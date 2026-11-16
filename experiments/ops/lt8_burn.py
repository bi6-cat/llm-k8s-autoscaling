"""LT8: đo lúc cảnh báo LLMSLOBurnFast kêu theo tỷ lệ request xấu x, trên simulator (Môi trường §19).

Khái niệm:
    LLMSLOBurnFast (common/observability/alerts/llm.yaml) kêu khi tỷ lệ request có TTFT > 2,5 s vượt 20 %
    (burn rate 4 với SLO 95 %) trên CẢ cửa sổ 5 phút và 1 phút, đúng liên tục suốt `for: 1m`.
    Simulator llm-d-inference-sim v0.12.0 có endpoint POST /admin/config đổi độ trễ ngay lúc đang chạy (cấu
    hình mới thay nguyên tử, request đến sau dùng ngay; pkg/simulator/context.go ApplyConfigUpdate). TTFT
    của mỗi request lấy ngẫu nhiên theo phân phối chuẩn N(μ, σ) rồi cắt vào [0,3 μ; 1,7 μ], và simulator
    từ chối σ > 0,3 μ (pkg/common/utils.go RandomNormDuration, pkg/common/config.go). Chọn σ = 0,3 μ và μ
    sao cho P(TTFT > 2,5 s) = x, nên có đúng tỷ lệ xấu x mà không phải sửa manifest hay khởi động lại pod.
Mục đích: Thu dữ liệu thô cho LT8 (TR8), cũng là dữ liệu cho VH6. Mỗi lượt là một lần chạy máy tạo tải (Job
    trong cluster, tốc độ cố định), trong đó lần lượt bơm từng mức x:
        nền WARM s (TTFT 200 ms, x = 0) → bơm x trong INJECT s → về nền GAP s → mức kế tiếp … → nền TAIL s
    WARM và GAP ≥ 5 phút + dư, để lúc bơm, cửa sổ 5m chỉ chứa request tốt (đúng giả thiết của dự đoán).
    Ghi mốc bơm/gỡ (giờ thực và đồng hồ đơn điệu), requests.csv, và mẫu Prometheus thô (ALERTS, hai recording
    rule, bộ đếm histogram TTFT) tới ms. Phần tính toán nằm ở analysis/lt8_burn.py (có unit test); file này
    chỉ đo. KEDA bị tạm dừng ở 1 replica suốt phiên: LT8 kiểm cảnh báo chứ không kiểm scale, và pod mới
    sinh ra giữa chừng sẽ không mang độ trễ đã bơm.
Chạy (cluster dựng bằng make sim-up). Mặc định 3 mức × 3 lượt, mỗi lượt khoảng 38 phút; thứ tự mức xoay vòng
    theo lượt, nên mỗi mức đứng đầu, giữa, cuối đúng một lần:
    make sim-lt8
    Windows có kubectl trong WSL nhưng WSL không có uv: gọi thẳng python3 trong WSL (chỉ cần PyYAML):
    python3 -m experiments.ops.lt8_burn --matrix envs/sim/experiments/matrix.yaml --context kind-llm-sim
    uv run --project analysis python -m analysis.lt8_burn runs/sim/lt8-<giờ>     # bảng của LT8
Kết quả: runs/sim/lt8-<giờ>/rep<r>/: meta.json, timeline.json, prom.json, load/ (requests.csv, loadgen.json).
Tham khảo: Môi trường §19 (LT8), §13 (VH6); Kiến thức nền §5.2; Vận hành §3.3; Thông số §4 (N7), §6
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import NormalDist
from typing import Any

from experiments.ops.vh import SO_NAME, Ops
from experiments.runner import configs
from experiments.runner import matrix as matrix_mod
from experiments.runner.kube import Kube, KubeError, Prometheus
from experiments.runner.loadjob import LoadJob, loadgen_args

REPO = Path(__file__).resolve().parents[2]
SLO_TTFT_MS = 2500  # ngưỡng TTFT của SLO (Thông số §6), cũng là biên bucket le="2.5" mà recording rule đọc
SIGMA_RATIO = 0.3  # σ = 0,3 μ: mức lớn nhất simulator nhận
# Độ trễ nền = cờ --time-to-first-token của envs/sim/serving/patch-sim.yaml. Sửa file đó thì sửa cả đây.
BASE_LATENCY = {"time-to-first-token": "200ms", "time-to-first-token-std-dev": "0s"}
SIM_PORT = 8000  # --port của simulator (patch-sim.yaml)
POLL_S = 2
DETECT_SLACK_S = 30  # loadgen chạy thêm chừng này: mốc 0 của lịch bơm là lúc THẤY tải, trễ hơn t0 của loadgen
# loadgen đếm --duration theo đồng hồ đơn điệu, chạy nhanh k lần trên WSL2 (k ≤ 1,04 đã gặp), nên tự dừng sớm
# total·(1 − 1/k) giây thực (≈ 85 s ở k = 1,04, total = 2190 s). Nhân thêm 5 % để pha nền cuối vẫn đủ dài.
CLOCK_MARGIN = 1.05
# Chuỗi Prometheus lưu nguyên mẫu thô (mốc tới ms). Tên khoá là tên mà analysis/lt8_burn.py đọc.
SERIES = {
    "alerts": 'ALERTS{alertname="LLMSLOBurnFast"}',
    "r1": "llm:ttft_bad_ratio:rate1m",
    "r5": "llm:ttft_bad_ratio:rate5m",
    "count": 'vllm:time_to_first_token_seconds_count{namespace="llm-serving"}',
    "good": 'vllm:time_to_first_token_seconds_bucket{namespace="llm-serving", le="2.5"}',
}


def latency_for(x: float) -> tuple[int, int]:
    """(μ, σ) tính bằng ms để P(TTFT > 2,5 s) = x, với σ = 0,3 μ. Hàm thuần.

    P(TTFT > s) = 1 − Φ((s − μ)/σ) = x  ⇔  (s − μ)/(0,3 μ) = z, với z = Φ⁻¹(1 − x)  ⇔  μ = s / (1 + 0,3 z).
    σ làm tròn XUỐNG ms để không vượt 0,3 μ (simulator từ chối). Phải có 0,3 μ < s < 1,7 μ, nếu không mọi
    mẫu bị cắt về cùng một phía của ngưỡng và tỷ lệ xấu thành 0 hoặc 1, không còn là x.
    """
    if not 0 < x < 1:
        raise ValueError(f"x phải trong (0; 1), nhận {x}")
    z = NormalDist().inv_cdf(1 - x)
    if 1 + SIGMA_RATIO * z <= 0:
        raise ValueError(f"x = {x} quá gần 1 để đạt được với σ = {SIGMA_RATIO} μ")
    mu = round(SLO_TTFT_MS / (1 + SIGMA_RATIO * z))
    if not 0.3 * mu < SLO_TTFT_MS < 1.7 * mu:
        raise ValueError(f"x = {x}: μ = {mu} ms làm ngưỡng 2,5 s rơi ra ngoài [0,3 μ; 1,7 μ]")
    return mu, math.floor(SIGMA_RATIO * mu)


def plan(
    levels: list[float], warm_s: float, inject_s: float, gap_s: float, tail_s: float
) -> tuple[list[dict[str, float]], float]:
    """Lịch bơm của một lượt: [{x, start, end}] (giây, tính từ lúc thấy tải) và tổng thời lượng. Hàm thuần."""
    out, t = [], warm_s
    for i, x in enumerate(levels):
        out.append({"x": x, "start": t, "end": t + inject_s})
        t += inject_s + (gap_s if i < len(levels) - 1 else tail_s)
    return out, t


def rotate(levels: list[float], k: int) -> list[float]:
    """Xoay thứ tự mức theo lượt, để mức nào cũng có lúc đứng đầu, giữa, cuối. Hàm thuần."""
    k %= len(levels)
    return levels[k:] + levels[:k]


class Lt8:
    """Các thao tác trên cluster của một phiên LT8."""

    def __init__(self, kube: Kube, ops: Ops, prom: Prometheus) -> None:
        self.kube, self.ops, self.prom = kube, ops, prom
        self.timeline: list[dict[str, Any]] = []

    def mark(self, event: str, **data: Any) -> float:
        # Ghi cả hai đồng hồ của runner: giờ thực để ghép với Prometheus; đơn điệu để có k dự phòng khi không
        # đọc được đồng hồ trong pod loadgen (pod_clock). Chỉ đúng khi runner chung kernel với cluster.
        wall, mono = time.time(), time.monotonic()
        self.timeline.append({"event": event, "wall": wall, "mono": mono, **data})
        print(f"{datetime.now(UTC):%H:%M:%S} {event} {data or ''}", flush=True)
        return wall

    def set_latency(self, body: dict[str, str]) -> list[dict[str, Any]]:
        """POST /admin/config tới MỌI pod Ready (qua API server proxy). Trả `latencies` mà mỗi pod báo lại."""
        out = []
        for pod in self.ops.ready_names():
            path = f"/api/v1/namespaces/{self.ops.ns}/pods/{pod}:{SIM_PORT}/proxy/admin/config"
            # `kubectl create --raw -f -` = POST thân lấy từ stdin. Simulator trả 400 nếu giá trị sai.
            res = self.kube.run("create", "--raw", path, "-f", "-", stdin=json.dumps(body)).stdout
            lat = json.loads(res)["latencies"]
            out.append(
                {"pod": pod, "ttft": lat["time-to-first-token"], "sd": lat["time-to-first-token-std-dev"]}
            )
        return out

    def ttft_count(self) -> float:
        return self.prom.scalar(f"sum({SERIES['count']})") or 0.0

    def wait_quiet(self, settle_s: float = 12, timeout_s: float = 300) -> float:
        """Chờ bộ đếm TTFT đứng yên qua hơn hai lần scrape (5 s), rồi trả giá trị đó. Nếu không chờ, request
        cuối của lượt trước có thể được đếm muộn, và vòng chờ "thấy tải" của lượt sau tưởng tải đã tới."""
        prev, end = self.ttft_count(), time.time() + timeout_s
        while time.time() < end:
            time.sleep(settle_s)
            cur = self.ttft_count()
            if cur == prev:
                return cur
            prev = cur
        raise RuntimeError(f"bộ đếm TTFT vẫn tăng sau {timeout_s:.0f} s dù chưa có tải của lượt này")

    def pod_clock(self, job_name: str) -> dict[str, float] | None:
        """Giờ thực và đồng hồ đơn điệu đọc CÙNG LÚC trong pod loadgen, tức trên đúng kernel mà loadgen dùng
        cho perf_counter. Đọc ở đầu và cuối lượt thì có k của chính đồng hồ loadgen, đúng cả khi runner chạy
        trên máy khác kernel với cluster. Trên WSL2, k ≈ 1,02–1,04 và đổi theo lần VM khởi động (LT5), nên
        phải đo trong chính lượt đó. None nếu không đọc được (pod chưa chạy hoặc đã xong)."""
        try:
            pods = self.kube.get_json("pods", "-n", self.ops.ns, "-l", f"job-name={job_name}")["items"]
            pod = next(p["metadata"]["name"] for p in pods if p["status"].get("phase") == "Running")
            code = "import time; print(time.time(), time.monotonic())"
            out = self.kube.run("exec", pod, "-n", self.ops.ns, "--", "python", "-c", code).stdout.split()
            return {"wall": float(out[0]), "mono": float(out[1])}
        except (KubeError, StopIteration, ValueError, IndexError):
            return None

    def pod_state(self) -> dict[str, int]:
        """{UID pod simulator: tổng số lần restart}. So đầu và cuối lượt: pod bị thay (UID khác, restartCount
        của pod mới về 0) hay container restart đều làm mất độ trễ đã bơm và reset bộ đếm."""
        return {
            p["metadata"]["uid"]: sum(
                c.get("restartCount", 0) for c in p["status"].get("containerStatuses", [])
            )
            for p in self.ops.pods()
        }

    def pause_at_one(self, timeout_s: float = 900) -> None:
        """Tạm dừng KEDA ở 1 replica rồi chờ chỉ còn đúng 1 pod (pod thừa đã tắt hẳn), pod đó Ready."""
        configs.set_paused(self.kube, self.ops.ns, SO_NAME, True)
        end = time.time() + timeout_s
        while time.time() < end:
            if len(self.ops.pods()) == 1 and len(self.ops.ready_names()) == 1:
                return
            time.sleep(5)
        raise RuntimeError(f"sau {timeout_s:.0f} s vẫn chưa về đúng 1 pod Ready")

    def raw(self, start: float, end: float) -> dict[str, Any]:
        """Mẫu thô của các chuỗi trong SERIES: truy vấn range vector `expr[d]` tại `end` trả mọi mẫu đã lưu
        cùng mốc thật (không nội suy theo bước như query_range)."""
        d = math.ceil(end - start)
        return {k: self.prom.query(f"{e}[{d}s]", at=end) for k, e in SERIES.items()}


def run_rep(
    s: Lt8, job: LoadJob, target: Any, rep: int, levels: list[float], a: argparse.Namespace, out: Path
) -> dict[str, Any]:
    """Một lượt: chạy loadgen, bơm từng mức theo lịch, rồi lấy dữ liệu Prometheus. Trả meta của lượt."""
    sched, total = plan(levels, a.warm, a.inject, a.gap, a.tail)
    for item in sched:
        item["mu_ms"], item["sd_ms"] = latency_for(item["x"])
    s.timeline = []
    s.set_latency(BASE_LATENCY)  # phòng lượt trước dừng giữa chừng khi đang bơm
    pods0, c0 = s.pod_state(), s.wait_quiet()
    duration = math.ceil(total * CLOCK_MARGIN + DETECT_SLACK_S)
    args = loadgen_args(
        "CONST", capacity=None, rate=a.rate, duration=duration, kb3_replicas=1, run_index=rep,
        url=target.service_url, model=target.model, out="/out", workers=target.loadgen_workers,
    )  # fmt: skip
    # Request ngắn: 16 token × 50 ms ≈ 0,8 s, nên ở x = 0,6 (μ ≈ 2,7 s) mỗi request ≈ 3,5 s, tức chỉ ≈ 7
    # request đồng thời ở 2 req/s, dưới --max-num-seqs = 16: không phải xếp hàng, TTFT đúng bằng giá trị bơm.
    args += ["--max-tokens", str(a.max_tokens)]
    load: dict[str, Any] = {}

    def run_load() -> None:
        try:
            load.update(job.run("lt8", f"rep{rep}", args, duration, out / "load"))
        except Exception as e:  # noqa: BLE001 - ghi vào meta, vẫn giữ timeline và dữ liệu Prometheus
            load["error"] = f"{type(e).__name__}: {e}"[:300]

    t_start = s.mark("load_submitted", duration=duration)
    loader = threading.Thread(target=run_load, daemon=True)
    loader.start()
    # Mốc 0 của lịch = lần đầu Prometheus thấy bộ đếm TTFT tăng (pod loadgen cài thư viện ~1 phút rồi mới gửi)
    deadline = time.time() + 900
    while s.ttft_count() <= c0:
        if not loader.is_alive():
            raise RuntimeError(f"máy tạo tải dừng trước khi gửi: {load.get('error', load)}")
        if time.time() > deadline:
            raise RuntimeError("không thấy tải tới simulator sau 15 phút")
        time.sleep(POLL_S)
    t0 = s.mark("traffic_seen")
    job_name = f"loadgen-lt8-rep{rep}"  # tên LoadJob.run đặt: loadgen-<run_id>-<phase>
    clocks = [s.pod_clock(job_name)]

    for item in sched:
        time.sleep(max(0.0, t0 + item["start"] - time.time()))
        body = {
            "time-to-first-token": f"{item['mu_ms']}ms",
            "time-to-first-token-std-dev": f"{item['sd_ms']}ms",
        }
        # Mốc ghi SAU khi POST trả về, nên muộn hơn lúc độ trễ đổi tối đa post_s (ghi lại để chặn sai số).
        t_post = time.time()
        pods = s.set_latency(body)
        s.mark(
            "inject",
            x=item["x"],
            mu_ms=item["mu_ms"],
            sd_ms=item["sd_ms"],
            pods=pods,
            post_s=time.time() - t_post,
        )
        time.sleep(max(0.0, t0 + item["end"] - time.time()))
        t_post = time.time()
        pods = s.set_latency(BASE_LATENCY)
        s.mark("recover", x=item["x"], pods=pods, post_s=time.time() - t_post)
    clocks.append(s.pod_clock(job_name))  # loadgen còn chạy pha nền cuối (--tail), pod chưa xong

    loader.join()
    t_end = s.mark("load_done", **{k: v for k, v in load.items() if k != "pod"})
    # Chờ qua mốc cuối của cửa sổ truy vấn, để lấy được cả lần tính rule ngay sau khi tải dừng
    time.sleep(max(0.0, t_end + 30 - time.time()))
    (out / "prom.json").write_text(json.dumps(s.raw(t_start - 60, t_end + 30)), encoding="utf-8")
    # Một ảnh chụp duy nhất cho cả hai khoá. restartCount cộng theo từng UID: pod mới (UID không có lúc đầu)
    # tính trọn số restart của nó, nên pod bị thay không làm hiệu số âm hay che mất restart.
    pods1 = s.pod_state()
    first, last = s.timeline[0], s.timeline[-1]
    k_runner = (last["mono"] - first["mono"]) / (last["wall"] - first["wall"])
    k_pod = None
    if clocks[0] and clocks[1]:
        k_pod = (clocks[1]["mono"] - clocks[0]["mono"]) / (clocks[1]["wall"] - clocks[0]["wall"])
    meta = {
        "rep": rep,
        "levels": levels,
        "schedule": sched,
        "rate": a.rate,
        "max_tokens": a.max_tokens,
        "slo_ttft_s": SLO_TTFT_MS / 1000,
        "base_latency": BASE_LATENCY,
        # k > 1: đồng hồ đơn điệu của loadgen chạy nhanh hơn giờ thực; analysis đổi mốc loadgen bằng k.
        # Ưu tiên k đo trong pod; k của runner để đối chiếu (chung kernel thì hai số gần bằng nhau).
        "k_mono_per_wall": k_pod or k_runner,
        "k_source": "pod" if k_pod else "runner",
        "k_pod": k_pod,
        "k_runner": k_runner,
        "pod_clocks": clocks,
        "restarts": sum(n - pods0.get(uid, 0) for uid, n in pods1.items()),
        "pod_replaced": set(pods1) != set(pods0),
        "load": load,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "timeline.json").write_text(json.dumps(s.timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m experiments.ops.lt8_burn", description=__doc__.split("\n")[0])
    p.add_argument("--matrix", type=Path, required=True, help="Lấy target và Service Prometheus từ file này")
    p.add_argument("--context")
    p.add_argument("--levels", type=float, nargs="+", default=[0.1, 0.3, 0.6], help="Các mức x")
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--rate", type=float, default=2.0, help="Tải nền, req/s")
    p.add_argument("--max-tokens", type=int, default=16)
    # 330 s = cửa sổ 5m (300 s) + 30 s dư: lúc bơm, cửa sổ dài không còn request nào của mức trước
    p.add_argument("--warm", type=float, default=330, help="Giây nền trước lần bơm đầu")
    # 360 s: dự đoán firing muộn nhất là x = 0,3 ở khoảng 260 s + trễ scrape và tính rule (< 60 s)
    p.add_argument("--inject", type=float, default=360, help="Giây bơm mỗi mức")
    p.add_argument("--gap", type=float, default=330, help="Giây nền giữa hai lần bơm")
    p.add_argument("--tail", type=float, default=120, help="Giây nền sau lần bơm cuối (đủ thấy cảnh báo hết)")
    a = p.parse_args(argv)
    for x in a.levels:
        try:
            latency_for(x)
        except ValueError as e:
            p.error(str(e))

    try:
        m = matrix_mod.load(a.matrix)
    except matrix_mod.MatrixError as e:
        print(f"Lỗi file ma trận: {e}", file=sys.stderr)
        return 2
    # Recording rule (slo.yaml) chỉ đọc namespace llm-serving: ở namespace khác cảnh báo không bao giờ kêu
    if m.target.namespace != "llm-serving":
        print(
            f"LT8 cần target ở namespace llm-serving, file ma trận ghi {m.target.namespace}", file=sys.stderr
        )
        return 2
    kube = Kube(context=a.context, timeout_s=120)
    ops = Ops(kube, m.target, max_replicas=1)
    s = Lt8(kube, ops, Prometheus(kube, m.target.prometheus_service))
    session = REPO / "runs" / "sim" / f"lt8-{datetime.now(UTC):%Y%m%d-%H%M%S}"
    try:
        so = kube.get_json("scaledobject", SO_NAME, "-n", ops.ns)
    except KubeError as e:
        print(f"Không đọc được ScaledObject {SO_NAME}: {e}", file=sys.stderr)
        return 2
    paused_before = so["metadata"].get("annotations", {}).get(configs.PAUSE_ANNOTATION)
    failed = False
    try:
        configs.guard_argocd(kube)
        s.pause_at_one()
        job = LoadJob(kube, m.target, REPO)
        job.sync_code()
        for rep in range(1, a.reps + 1):
            out = session / f"rep{rep}"
            out.mkdir(parents=True)
            meta = run_rep(s, job, m.target, rep, rotate(list(a.levels), rep - 1), a, out)
            failed |= meta["load"].get("rc") != 0 or "error" in meta["load"]
            failed |= meta["restarts"] > 0 or meta["pod_replaced"]
    except (KubeError, RuntimeError, ValueError, KeyError, OSError) as e:  # ValueError gồm lỗi JSON
        print(f"Dừng: {e}", file=sys.stderr)
        failed = True
    finally:
        # Luôn trả cluster về như cũ, mỗi bước một try để bước trước lỗi không chặn bước sau:
        # (1) dừng máy tạo tải còn chạy (lượt dừng giữa chừng); (2) độ trễ nền; (3) bỏ tạm dừng KEDA nếu
        # trước phiên không tạm dừng. Bỏ tạm dừng sau cùng, khi đã hết tải, để KEDA không scale theo tải dở.
        kube.run(
            "delete", "job", "-n", ops.ns, "-l", "experiment/run=lt8", "--ignore-not-found", check=False
        )  # fmt: skip
        try:
            s.set_latency(BASE_LATENCY)
        except Exception as e:  # noqa: BLE001 - vẫn phải gỡ tạm dừng KEDA ở dưới
            print(f"Không đặt lại được độ trễ nền: {e}", file=sys.stderr)
        ann = (
            f"{configs.PAUSE_ANNOTATION}-"
            if paused_before is None
            else f"{configs.PAUSE_ANNOTATION}={paused_before}"
        )
        kube.run("annotate", "scaledobject", SO_NAME, "-n", ops.ns, ann, "--overwrite", check=False)
    print(f"Kết quả: {session}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
