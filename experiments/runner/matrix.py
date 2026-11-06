"""Đọc file ma trận đánh giá (YAML) thành danh sách lượt cần chạy.

Khái niệm: File ma trận mô tả một phiên: cluster nào (namespace, Deployment, Service, Prometheus),
    các cấu hình scale (`configs`), và danh sách lượt (`runs`: cấu hình × kịch bản × số lần lặp).
    Mỗi lượt có một `run_id` cố định, sinh từ nội dung lượt, nên chạy lại phiên thì runner nhận ra
    lượt nào đã xong (progress.json) mà không cần đánh số tay.
Mục đích: Kiểm tra file ngay khi bắt đầu, báo lỗi rõ ràng, để không phát hiện lỗi chính tả ở lượt
    thứ 10 lúc 3 giờ sáng. Không gọi cluster: hàm thuần, có unit test.

Ví dụ một file: experiments/matrix-sim.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Kịch bản mà loadgen hiểu (loadgen/scenarios.py). CONST cần rate + duration; KB1–KB3 cần capacity.
SCENARIOS = ("KB1", "KB2", "KB3", "CONST")
# Hai loại cấu hình: static = cố định N replica, không có ScaledObject (S1, S4);
# scaledobject = KEDA tự scale theo file ScaledObject (A1, A2, A3, A4).
CONFIG_TYPES = ("static", "scaledobject")


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


@dataclass(frozen=True)
class RunSpec:
    """Một lượt: cấu hình × kịch bản × lần lặp."""

    run_id: str  # ví dụ "A2-KB2-1"; tên thư mục runs/<session>/<run_id>
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
    runs: list[RunSpec]


def _require(d: dict[str, Any], key: str, where: str) -> Any:
    if key not in d:
        raise MatrixError(f"{where}: thiếu trường `{key}`")
    return d[key]


def parse(data: dict[str, Any]) -> Matrix:
    """Kiểm tra và chuyển dict (đã đọc từ YAML) thành Matrix. Lỗi nào cũng báo kèm vị trí."""
    if not isinstance(data, dict):
        raise MatrixError("file ma trận phải là một map YAML")
    session = str(_require(data, "session", "gốc"))
    env = str(_require(data, "env", "gốc"))
    if env not in ("home", "sim", "cloud"):
        raise MatrixError(f"gốc: env `{env}` không hợp lệ (home | sim | cloud)")

    t = _require(data, "target", "gốc")
    target = Target(
        namespace=str(_require(t, "namespace", "target")),
        deployment=str(_require(t, "deployment", "target")),
        service_url=str(_require(t, "service_url", "target")),
        model=str(_require(t, "model", "target")),
        prometheus_service=str(_require(t, "prometheus_service", "target")),
        api_key_secret=t.get("api_key_secret"),
    )
    timing = Timing(**data.get("timing", {}))

    configs: dict[str, Config] = {}
    for cid, c in _require(data, "configs", "gốc").items():
        where = f"configs.{cid}"
        ctype = _require(c, "type", where)
        if ctype not in CONFIG_TYPES:
            raise MatrixError(f"{where}: type `{ctype}` không hợp lệ ({' | '.join(CONFIG_TYPES)})")
        if ctype == "scaledobject" and "file" not in c:
            raise MatrixError(f"{where}: cấu hình scaledobject cần `file`")
        configs[cid] = Config(
            id=cid,
            type=ctype,
            replicas=int(c.get("replicas", 1)),
            file=c.get("file"),
            overrides=dict(c.get("overrides", {})),
        )

    runs: list[RunSpec] = []
    defaults = data.get("defaults", {})
    for i, r in enumerate(_require(data, "runs", "gốc")):
        where = f"runs[{i}]"
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
        for rep in range(1, int(r.get("repeats", 1)) + 1):
            runs.append(
                RunSpec(
                    run_id=f"{cid}-{scenario}-{rep}",
                    config=configs[cid],
                    scenario=scenario,
                    repeat=rep,
                    capacity=r.get("capacity"),
                    rate=r.get("rate"),
                    duration=r.get("duration"),
                    replicas_for_kb3=int(r.get("kb3_replicas", 4)),
                )
            )
    ids = [x.run_id for x in runs]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        raise MatrixError(f"runs: trùng run_id {dup}; đổi `repeats` hoặc gộp các dòng trùng")
    return Matrix(session=session, env=env, target=target, timing=timing, runs=runs)


def load(path: Path) -> Matrix:
    with path.open(encoding="utf-8") as fh:
        return parse(yaml.safe_load(fh))
