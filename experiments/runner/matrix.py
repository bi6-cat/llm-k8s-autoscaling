"""Đọc file ma trận đánh giá (YAML) thành danh sách lượt cần chạy.

Khái niệm: File ma trận mô tả một phiên: cluster nào (namespace, Deployment, Service, Prometheus),
    các cấu hình scale (`configs`), và danh sách lượt (`runs`: cấu hình × kịch bản × số lần lặp).
    Mỗi lượt có một `run_id` cố định, sinh từ nội dung lượt, nên chạy lại phiên thì runner nhận ra
    lượt nào đã xong (progress.json) mà không cần đánh số tay.
    `shuffle_seed` (tuỳ chọn) xáo thứ tự lượt theo seed (Thông số §8.2), để thứ tự chạy không trùng với
    thứ tự cấu hình: nếu không, thứ gì trôi theo thời gian (nhiệt GPU, trạng thái node) bị tính nhầm
    thành khác biệt giữa các cấu hình. Xáo trong từng khối lần lặp: mọi lượt lặp-1 chạy trước (mỗi ô
    cấu hình × kịch bản một lượt), rồi mới tới lặp-2…, nên phiên bị cắt ngang chỉ mất lần lặp, không mất
    ô nào. Các lượt cùng lần lặp dùng chung lịch gửi và chạy gần nhau, nên so sánh cặp ít bị trôi hơn.
Mục đích: Kiểm tra file ngay khi bắt đầu, báo lỗi rõ ràng, để không phát hiện lỗi chính tả ở lượt
    thứ 10 lúc 3 giờ sáng. Không gọi cluster: hàm thuần, có unit test.
    - Số phải dương và hữu hạn: bắt cả giá trị `null` chưa điền trong file nháp (như matrix-v2.yaml
      trước ADR-003) và `.nan`, `.inf` của YAML.
    - Khoá lạ bị từ chối: gõ nhầm `shufle_seed` hay `repeat` thì báo lỗi, thay vì lặng lẽ bỏ xáo hay bỏ
      lặp. Riêng khoá gốc bắt đầu bằng `x-` được bỏ qua: chỗ đặt YAML anchor (`x-adr003` trong
      matrix-v2.yaml).
    - `signal` của cấu hình phải là selector của một chuỗi, không phải biểu thức (xem SELECTOR_RE).

Ví dụ một file: experiments/matrix-sim.yaml.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

# Kịch bản mà loadgen hiểu (loadgen/scenarios.py). CONST cần rate + duration; KB1–KB3 cần capacity.
SCENARIOS = ("KB1", "KB2", "KB3", "CONST")
# Hai loại cấu hình: static = cố định N replica, không có ScaledObject (S1, S4);
# scaledobject = KEDA tự scale theo file ScaledObject (A1, A2, A3, A4).
CONFIG_TYPES = ("static", "scaledobject")
# Selector PromQL của một chuỗi: tên metric, tuỳ chọn kèm `{label…}`, ví dụ
# `vllm:num_requests_running{namespace="llm-serving"}`. Không nhận biểu thức (`sum(…)`, `rate(…)`): runner
# đọc mẫu gốc bằng range selector `<signal>[Ns]` (collect.signal_gap), mà Prometheus chỉ cho đặt `[Ns]`
# ngay sau một selector.
SELECTOR_RE = re.compile(r"[A-Za-z_:][A-Za-z0-9_:]*(\{[^{}]*\})?")
# CPU kiểu Kubernetes ở dạng thường dùng: số lõi ("2", "1.5") hoặc millicore ("500m"). Chặt hơn cú pháp
# quantity đầy đủ của Kubernetes (không nhận "+3", "1e1"), để giá trị lạ bị từ chối ngay lúc đọc ma trận
# thay vì lỗi ở `kubectl apply` Job giữa phiên.
CPU_RE = re.compile(r"\d+(\.\d+)?m?")


class MatrixError(ValueError):
    """File ma trận sai cấu trúc hoặc thiếu trường."""


@dataclass(frozen=True)
class Target:
    """Cluster và các thành phần mà runner điều khiển."""

    namespace: str  # namespace của vLLM, ScaledObject và Job máy tạo tải
    deployment: str  # Deployment vLLM (nhãn app=<deployment>)
    service_url: str  # địa chỉ vLLM nhìn từ TRONG cluster (máy tạo tải chạy trong pod)
    model: str  # --served-model-name của vLLM
    prometheus_service: str  # "<namespace>/<service>:<port>", truy vấn qua API server proxy
    api_key_secret: str | None  # Secret chứa API key (key `key`); None nếu server không cần key
    # CPU của pod máy tạo tải (request = limit), kiểu Kubernetes: "2", "500m". 1 lõi đủ ở vài req/s; tốc độ
    # cao hơn thì tăng lên để cgroup không throttle (ĐG1-mini 05/11 bị loại 2 mức λ vì throttle ở 1 lõi) và
    # để có thêm tiến trình gửi tải (loadgen_workers).
    loadgen_cpu: str = "1"

    @property
    def loadgen_workers(self) -> int:
        """Số tiến trình gửi tải (`loadgen --workers`): một tiến trình mỗi lõi nguyên, ít nhất 1.

        Mỗi tiến trình là một event loop, dùng tối đa một lõi (loadgen/workers.py); tiến trình cha chỉ chờ
        và ghi CSV (vài chục dòng/s), gần như không tốn CPU. Ném ValueError nếu `loadgen_cpu` sai dạng.
        """
        cpu = self.loadgen_cpu
        if not CPU_RE.fullmatch(cpu):
            raise ValueError(f'cần dạng "2", "1.5" hoặc "500m", gặp {cpu!r}')
        cores = float(cpu[:-1]) / 1000 if cpu.endswith("m") else float(cpu)
        if cores <= 0:
            raise ValueError("phải > 0")
        return max(1, int(cores))


@dataclass(frozen=True)
class Config:
    """Một cấu hình scale."""

    id: str  # S1, S4, A2…
    type: str  # static | scaledobject
    replicas: int = 1  # static: số replica cố định
    file: str | None = None  # scaledobject: đường dẫn file ScaledObject (từ gốc repo)
    # scaledobject: giá trị ghi đè lúc áp (threshold, max_replicas), vì cùng một file A2 dùng cho kind,
    # nhà và VM với threshold khác nhau (threshold = 0,8 × B*, Thông số §9.3).
    overrides: dict[str, Any] = field(default_factory=dict)
    # scaledobject, tuỳ chọn: selector của chuỗi mà trigger đọc (A1: `nvidia_smi_utilization_gpu_ratio`).
    # Chuỗi này mất mẫu quá 15 s trong pha chính thì lượt bị đánh dấu invalid (Môi trường §17), vì KEDA coi
    # truy vấn rỗng là 0 mà không báo lỗi: mất exporter thì cấu hình đứng ở 1 replica (Kiến trúc §13.4).
    signal: str | None = None


@dataclass(frozen=True)
class RunSpec:
    """Một lượt: cấu hình × kịch bản × lần lặp."""

    run_id: str  # ví dụ "A2-KB2-1", "S1-CONST4-1" (CONST kèm tốc độ); tên thư mục runs/<session>/<run_id>
    config: Config
    scenario: str
    repeat: int  # lần lặp thứ mấy (1, 2…); cũng là --run-index của loadgen (cùng lịch)
    capacity: float | None  # C (req/s) cho KB1–KB3
    rate: float | None  # CONST: req/s
    duration: float | None  # CONST: giây
    replicas_for_kb3: int  # N trong đỉnh 0,75 × N × C của KB3


@dataclass(frozen=True)
class Timing:
    """Các khoảng chờ của một lượt (giây). Mặc định theo Môi trường §14.1; kind dùng giá trị ngắn hơn."""

    settle_s: float = 60  # reset: chờ thêm sau khi hệ thống đã yên
    warmup_s: float = 120  # warm-up 0,3 C, không tính vào kết quả
    warmup_fraction: float = 0.3  # tốc độ warm-up = 0,3 × C (hoặc 0,3 × rate với CONST)
    cooldown_max_s: float = 600  # cooldown: chờ về 1 replica tối đa 10 phút
    reset_timeout_s: float = 900  # reset: tối đa 15 phút để đạt trạng thái đầu (cold start vài phút)


@dataclass(frozen=True)
class Matrix:
    session: str  # tên phiên; thư mục runs/<session>/
    env: str  # home | sim | cloud (CONTRIBUTING §1)
    target: Target
    timing: Timing
    runs: list[RunSpec]  # theo thứ tự sẽ chạy (đã xáo nếu có shuffle_seed)
    shuffle_seed: int | None = None


# Khoá hợp lệ ở từng cấp của file. `defaults` dùng chung tập khoá với một dòng `runs`.
ROOT_KEYS = {"session", "env", "shuffle_seed", "target", "timing", "configs", "defaults", "runs"}
TARGET_KEYS = {f.name for f in fields(Target)}
TIMING_KEYS = {f.name for f in fields(Timing)}
CONFIG_KEYS = {"type", "replicas", "file", "overrides", "signal"}
OVERRIDE_KEYS = {"threshold", "max_replicas", "min_replicas"}
RUN_KEYS = {"config", "scenario", "capacity", "rate", "duration", "kb3_replicas", "repeats"}


def _require(d: dict[str, Any], key: str, where: str) -> Any:
    if key not in d:
        raise MatrixError(f"{where}: thiếu trường `{key}`")
    return d[key]


def _check_keys(d: Any, allowed: set[str], where: str) -> None:
    """Báo lỗi nếu `d` không phải map hoặc có khoá ngoài `allowed` (thường là gõ nhầm tên khoá)."""
    if not isinstance(d, dict):
        raise MatrixError(f"{where}: phải là một map YAML, gặp {d!r}")
    extra = sorted(str(k) for k in d if k not in allowed)
    if extra:
        raise MatrixError(f"{where}: khoá không hợp lệ {extra}; hợp lệ: {', '.join(sorted(allowed))}")


def _positive(value: Any, where: str, key: str, integer: bool = False) -> Any:
    """Trả lại `value` nếu là số dương hữu hạn (số nguyên khi integer=True), nếu không thì báo lỗi.

    bool bị loại riêng vì trong Python `True` cũng là int (bằng 1). NaN bị loại riêng vì `nan <= 0` là
    False, nên lọt qua phép so sánh.
    """
    is_num = isinstance(value, int) if integer else isinstance(value, (int, float))
    if not is_num or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        kind = "số nguyên dương" if integer else "số dương hữu hạn"
        hint = " (viết số, không đặt trong ngoặc kép)" if isinstance(value, str) else ""
        raise MatrixError(f"{where}: `{key}` phải là {kind}, gặp {value!r}{hint}")
    return value


def _shuffle_key(seed: int, run_id: str) -> str:
    """Khoá sắp xếp khi xáo: sha256 của "<seed>:<run_id>".

    Không dùng random.shuffle: Python chỉ cam kết giữ nguyên dãy của random() qua các phiên bản, không cam
    kết với shuffle. Với khoá băm, thứ tự chỉ phụ thuộc seed và tập run_id (không phụ thuộc thứ tự dòng
    trong file hay bản Python), và thêm một lượt mới không đảo thứ tự tương đối của các lượt cũ.
    """
    return hashlib.sha256(f"{seed}:{run_id}".encode()).hexdigest()


def parse(data: dict[str, Any]) -> Matrix:
    """Kiểm tra và chuyển dict (đã đọc từ YAML) thành Matrix. Lỗi nào cũng báo kèm vị trí."""
    if not isinstance(data, dict):
        raise MatrixError("file ma trận phải là một map YAML")
    _check_keys({k: v for k, v in data.items() if not str(k).startswith("x-")}, ROOT_KEYS, "gốc")
    session = str(_require(data, "session", "gốc"))
    env = str(_require(data, "env", "gốc"))
    if env not in ("home", "sim", "cloud"):
        raise MatrixError(f"gốc: env `{env}` không hợp lệ (home | sim | cloud)")

    t = _require(data, "target", "gốc")
    _check_keys(t, TARGET_KEYS, "target")
    target = Target(
        namespace=str(_require(t, "namespace", "target")),
        deployment=str(_require(t, "deployment", "target")),
        service_url=str(_require(t, "service_url", "target")),
        model=str(_require(t, "model", "target")),
        prometheus_service=str(_require(t, "prometheus_service", "target")),
        api_key_secret=t.get("api_key_secret"),
        loadgen_cpu=str(t.get("loadgen_cpu", "1")),
    )
    try:
        target.loadgen_workers  # noqa: B018 (chỉ để kiểm loadgen_cpu đúng dạng ngay lúc đọc ma trận)
    except ValueError as e:
        raise MatrixError(f"target: loadgen_cpu {target.loadgen_cpu!r} không hợp lệ ({e})") from None
    _check_keys(data.get("timing", {}), TIMING_KEYS, "timing")
    timing = Timing(**data.get("timing", {}))

    configs: dict[str, Config] = {}
    for cid, c in _require(data, "configs", "gốc").items():
        where = f"configs.{cid}"
        _check_keys(c, CONFIG_KEYS, where)
        ctype = _require(c, "type", where)
        if ctype not in CONFIG_TYPES:
            raise MatrixError(f"{where}: type `{ctype}` không hợp lệ ({' | '.join(CONFIG_TYPES)})")
        if ctype == "scaledobject" and "file" not in c:
            raise MatrixError(f"{where}: cấu hình scaledobject cần `file`")
        _check_keys(c.get("overrides", {}), OVERRIDE_KEYS, f"{where}.overrides")
        overrides = dict(c.get("overrides", {}))
        # Kiểm ngay ở đây: threshold sai (ví dụ `null` chưa điền) chỉ lộ ra khi KEDA từ chối ScaledObject,
        # tức sau khi lượt đã reset xong.
        if "threshold" in overrides:
            _positive(overrides["threshold"], f"{where}.overrides", "threshold")
        for key in ("max_replicas", "min_replicas"):
            if key in overrides:
                _positive(overrides[key], f"{where}.overrides", key, integer=True)
        if overrides.get("min_replicas", 1) > overrides.get("max_replicas", math.inf):
            raise MatrixError(f"{where}.overrides: `min_replicas` lớn hơn `max_replicas`")
        signal = c.get("signal")
        if signal is not None:
            # Cấu hình tĩnh không có tín hiệu nào để kiểm: khoá này ở đó là đặt nhầm chỗ
            if ctype != "scaledobject":
                raise MatrixError(f"{where}: `signal` chỉ dùng cho cấu hình scaledobject")
            if not isinstance(signal, str) or not SELECTOR_RE.fullmatch(signal):
                raise MatrixError(
                    f"{where}: `signal` phải là selector của một chuỗi (tên metric, tuỳ chọn kèm "
                    f"{{label…}}), không phải biểu thức; gặp {signal!r}"
                )
        configs[cid] = Config(
            id=cid,
            type=ctype,
            replicas=_positive(c.get("replicas", 1), where, "replicas", integer=True),
            file=c.get("file"),
            overrides=overrides,
            signal=signal,
        )

    runs: list[RunSpec] = []
    defaults = data.get("defaults", {})
    _check_keys(defaults, RUN_KEYS, "defaults")
    for i, r in enumerate(_require(data, "runs", "gốc")):
        where = f"runs[{i}]"
        _check_keys(r, RUN_KEYS, where)
        r = {**defaults, **r}  # giá trị riêng của lượt ghi đè defaults
        cid = _require(r, "config", where)
        if cid not in configs:
            raise MatrixError(f"{where}: cấu hình `{cid}` chưa khai báo trong configs")
        scenario = _require(r, "scenario", where)
        if scenario not in SCENARIOS:
            raise MatrixError(f"{where}: kịch bản `{scenario}` không hợp lệ ({' | '.join(SCENARIOS)})")
        if scenario == "CONST" and ("rate" not in r or "duration" not in r):
            raise MatrixError(f"{where}: CONST cần `rate` và `duration`")
        if scenario != "CONST" and "capacity" not in r:
            raise MatrixError(f"{where}: {scenario} cần `capacity` (C, req/s)")
        if scenario == "CONST":
            _positive(r["rate"], where, "rate")
            _positive(r["duration"], where, "duration")
        else:
            _positive(r["capacity"], where, "capacity")
        kb3 = _positive(r.get("kb3_replicas", 4), where, "kb3_replicas", integer=True)
        repeats = _positive(r.get("repeats", 1), where, "repeats", integer=True)
        # CONST ghi kèm tốc độ vào tên, để một phiên quét nhiều mức λ (ĐG1) không trùng run_id
        label = f"CONST{float(r['rate']):g}" if scenario == "CONST" else scenario
        for rep in range(1, repeats + 1):
            runs.append(
                RunSpec(
                    run_id=f"{cid}-{label}-{rep}",
                    config=configs[cid],
                    scenario=scenario,
                    repeat=rep,
                    capacity=r.get("capacity"),
                    rate=r.get("rate"),
                    duration=r.get("duration"),
                    replicas_for_kb3=kb3,
                )
            )
    ids = [x.run_id for x in runs]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        raise MatrixError(f"runs: trùng run_id {dup}; đổi `repeats` hoặc gộp các dòng trùng")
    seed = data.get("shuffle_seed")
    if seed is not None:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise MatrixError(f"gốc: `shuffle_seed` phải là số nguyên, gặp {seed!r}")
        # Khoá (lần lặp, băm): xáo trong từng khối lần lặp, mọi lượt lặp-1 chạy trước (docstring đầu file)
        runs.sort(key=lambda x: (x.repeat, _shuffle_key(seed, x.run_id)))
    return Matrix(session=session, env=env, target=target, timing=timing, runs=runs, shuffle_seed=seed)


def load(path: Path) -> Matrix:
    with path.open(encoding="utf-8") as fh:
        return parse(yaml.safe_load(fh))
