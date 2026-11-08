"""Điều phối một lượt (7 bước của Môi trường §14.1) và cả phiên (vòng lặp + checkpoint).

Khái niệm:
    Phiên (session) = một lần chạy file ma trận; dữ liệu ở runs/<session>/.
    Lần thử (attempt) = một lần chạy một lượt; lượt không hợp lệ được chạy lại thành attempt-2, attempt-1
    vẫn giữ (Môi trường §17: dữ liệu lượt hỏng vẫn giữ lại).
Mục đích: Chạy không người trực. Một lượt lỗi (exception) thì ghi lại lỗi rồi sang lượt sau, không dừng cả
    phiên. Có khoá file (flock) để systemd hay người vận hành lỡ chạy hai runner cùng lúc thì runner thứ
    hai dừng ngay, không giẫm lên nhau trên cùng cluster.

Cấu trúc một lần thử: runs/<session>/<run_id>/attempt-<n>/
    metadata.json  requests.csv  loadgen.json  metrics.csv.gz  events.jsonl  alerts.jsonl
    pods_start.json  pods_end.json  pods_timeline.json  checks.json  logs/  warmup/  loadgen-main/
    (error.txt nếu lỗi)
"""

from __future__ import annotations

import fcntl
import json
import shutil
import subprocess
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from experiments.runner import checks, collect, configs
from experiments.runner.kube import Kube, Prometheus
from experiments.runner.loadjob import LoadJob, loadgen_args
from experiments.runner.matrix import Matrix, RunSpec
from experiments.runner.progress import Progress

# Thời lượng kịch bản (giây), theo Thông số §8 và loadgen/scenarios.py. CONST lấy từ `duration` của lượt.
SCENARIO_S = {"KB1": 12 * 60, "KB2": 24 * 60, "KB3": 17 * 60}


def log(msg: str) -> None:
    # In kèm giờ để đọc được trong `journalctl` khi chạy bằng systemd (v2).
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def git_state(repo_root: Path) -> dict[str, Any]:
    """Commit đang chạy và có sửa đổi chưa commit không (tái lập được, N8)."""

    def git(*a: str) -> str:
        proc = subprocess.run(["git", "-C", str(repo_root), *a], capture_output=True, text=True)
        return proc.stdout.strip()

    return {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))}


@dataclass
class Context:
    matrix: Matrix
    kube: Kube
    prom: Prometheus
    repo_root: Path
    runs_dir: Path


def wait_initial_state(ctx: Context, replicas: int) -> tuple[bool, str]:
    """Reset: chờ đúng `replicas` pod Ready, không pod nào đang xoá, hàng đợi vLLM trống.

    Trả (đạt hay không, mô tả). Không đạt sau reset_timeout_s thì lượt vẫn chạy nhưng bị đánh dấu không
    hợp lệ, để còn dữ liệu xem vì sao.
    """
    t = ctx.matrix.target
    queue = (
        f'(sum(vllm:num_requests_running{{namespace="{t.namespace}"}}) or vector(0)) + '
        f'(sum(vllm:num_requests_waiting{{namespace="{t.namespace}"}}) or vector(0))'
    )
    end = time.time() + ctx.matrix.timing.reset_timeout_s
    note = ""
    while time.time() < end:
        dep = ctx.kube.get_json(f"deployment/{t.deployment}", "-n", t.namespace)
        pods = collect.snapshot_pods(ctx.kube, t.namespace, t.deployment)
        alive = [p for p in pods if not p["deleting"]]
        ready = dep["status"].get("readyReplicas", 0)
        q = ctx.prom.scalar(queue)
        note = f"spec={dep['spec'].get('replicas')} ready={ready} pods={len(alive)}/{len(pods)} queue={q}"
        if (
            dep["spec"].get("replicas") == replicas
            and ready == replicas
            and len(pods) == replicas
            and (q or 0) == 0
        ):
            log(f"  trạng thái đầu đạt: {note}; chờ thêm {ctx.matrix.timing.settle_s:g} s")
            time.sleep(ctx.matrix.timing.settle_s)
            return True, note
        time.sleep(10)
    return False, f"quá {ctx.matrix.timing.reset_timeout_s:g} s: {note}"


def wait_replicas(ctx: Context, replicas: int, timeout_s: float) -> float | None:
    """Cooldown: chờ Deployment về `replicas` pod sẵn sàng. Trả số giây đã chờ, None nếu quá hạn."""
    t = ctx.matrix.target
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        dep = ctx.kube.get_json(f"deployment/{t.deployment}", "-n", t.namespace)
        if dep["spec"].get("replicas") == replicas and dep["status"].get("readyReplicas", 0) == replicas:
            return time.time() - t0
        time.sleep(10)
    return None


def run_one(ctx: Context, spec: RunSpec, attempt_dir: Path) -> str:
    """Chạy một lượt. Trả "done" (hợp lệ) hoặc "invalid". Exception = lỗi runner, phiên xử lý."""
    m, t = ctx.matrix, ctx.matrix.target
    attempt_dir.mkdir(parents=True, exist_ok=False)
    t_begin = time.time()
    meta: dict[str, Any] = {
        "session": m.session,
        "env": m.env,
        "run_id": spec.run_id,
        "attempt_dir": attempt_dir.name,
        "spec": asdict(spec),
        "shuffle_seed": m.shuffle_seed,  # seed xáo thứ tự lượt (Thông số §8.2); None = theo thứ tự file
        "timing": asdict(m.timing),
        "target": asdict(t),
        "git": git_state(ctx.repo_root),
        "t_begin": t_begin,
    }
    dep = ctx.kube.get_json(f"deployment/{t.deployment}", "-n", t.namespace)
    c0 = dep["spec"]["template"]["spec"]["containers"][0]
    meta["vllm"] = {"image": c0.get("image"), "args": c0.get("args")}
    node = ctx.kube.get_json("nodes")["items"]
    meta["nodes"] = [
        {
            "name": n["metadata"]["name"],
            "kubelet": n["status"]["nodeInfo"]["kubeletVersion"],
            "allocatable": n["status"].get("allocatable"),
        }
        for n in node
    ]

    # 1) Áp cấu hình (ScaledObject bị pause ở 1 replica)
    log(f"[{spec.run_id}] áp cấu hình {spec.config.id} ({spec.config.type})")
    so_name = configs.apply_config(ctx.kube, t, spec.config, ctx.repo_root)
    start_replicas = spec.config.replicas if spec.config.type == "static" else 1

    # 2) Reset
    log(f"[{spec.run_id}] reset về {start_replicas} replica")
    initial_ok, initial_note = wait_initial_state(ctx, start_replicas)
    if not initial_ok:
        log(f"  CẢNH BÁO: {initial_note}")
    pods_start = collect.snapshot_pods(ctx.kube, t.namespace, t.deployment)
    write_json(attempt_dir / "pods_start.json", pods_start)

    # Theo dõi pod suốt warm-up, pha chính và cooldown: pod do scale-up tạo ra thường bị xoá trước bước 6,
    # nên mốc thời gian và log của chúng phải thu trong lúc lượt đang chạy (collect.PodWatcher).
    watcher = collect.PodWatcher(ctx.kube, t.namespace, t.deployment, attempt_dir / "logs", since=t_begin)
    watcher.start()
    try:
        job = LoadJob(ctx.kube, t, ctx.repo_root)
        job.sync_code()

        # 3) Warm-up: CONST ở 0,3 C trong warmup_s, vẫn đang pause, không tính vào kết quả
        t_warm = time.time()
        if m.timing.warmup_s > 0:
            base = spec.capacity if spec.scenario != "CONST" else spec.rate
            rate = round(m.timing.warmup_fraction * float(base), 3)
            log(f"[{spec.run_id}] warm-up {rate:g} req/s × {m.timing.warmup_s:g} s")
            args = loadgen_args(
                "CONST",
                capacity=None,
                rate=rate,
                duration=m.timing.warmup_s,
                kb3_replicas=0,
                run_index=spec.repeat,
                url=t.service_url,
                model=t.model,
                out="/out/warmup",
                workers=t.loadgen_workers,
            )
            job.run(spec.run_id, "warmup", args, m.timing.warmup_s, attempt_dir / "warmup")

        # 4) Chạy kịch bản: bỏ pause ngay trước khi máy tạo tải bắt đầu
        duration = SCENARIO_S.get(spec.scenario) or float(spec.duration or 0)
        if so_name:
            configs.set_paused(ctx.kube, t.namespace, so_name, paused=False)
        log(f"[{spec.run_id}] chạy {spec.scenario} ({duration:g} s)")
        args = loadgen_args(
            spec.scenario,
            capacity=spec.capacity,
            rate=spec.rate,
            duration=spec.duration,
            kb3_replicas=spec.replicas_for_kb3,
            run_index=spec.repeat,
            url=t.service_url,
            model=t.model,
            out="/out/main",
            workers=t.loadgen_workers,
        )
        res = job.run(spec.run_id, "main", args, duration, attempt_dir / "loadgen-main")
        t_main0, t_main1 = res["started"], res["finished"]
        pods_end = collect.snapshot_pods(ctx.kube, t.namespace, t.deployment)
        write_json(attempt_dir / "pods_end.json", pods_end)
        main_out = attempt_dir / "loadgen-main" / "main"
        for f in ("requests.csv", "loadgen.json"):
            if (main_out / f).exists():
                shutil.copy2(main_out / f, attempt_dir / f)

        # 5) Cooldown: cấu hình autoscaling phải tự về 1 replica (scale-down chậm: 300 s rồi 1 pod/60 s)
        cooldown_s = None
        if so_name:
            log(f"[{spec.run_id}] cooldown: chờ về 1 replica (tối đa {m.timing.cooldown_max_s:g} s)")
            cooldown_s = wait_replicas(ctx, 1, m.timing.cooldown_max_s)
            configs.set_paused(ctx.kube, t.namespace, so_name, paused=True)  # giữ yên cho lượt sau
        t_end = time.time()
    finally:
        # Cả khi lượt lỗi giữa chừng: dừng luồng nền (không thì nó tiếp tục ghi vào lượt cũ), giữ dữ liệu
        timeline = watcher.stop()
        write_json(attempt_dir / "pods_timeline.json", timeline)

    # 6) Thu dữ liệu: từ trước warm-up 30 s tới hết cooldown
    log(f"[{spec.run_id}] thu dữ liệu")
    queries = collect.metric_queries(t.namespace, t.deployment)
    n_metric = collect.write_metrics(ctx.prom, queries, t_warm - 30, t_end, attempt_dir / "metrics.csv.gz")
    n_event = collect.write_events(ctx.kube, t.namespace, t_begin, attempt_dir / "events.jsonl")
    n_alert = collect.write_alerts(ctx.prom, t_main0, t_end, attempt_dir / "alerts.jsonl")
    # Log đã thu trong watcher.stop(). Thiếu log không loại lượt (Môi trường §17), nhưng mất số đo cold start.
    # Pod chưa từng chạy container (Pending vì hết GPU rồi bị scale-down) không có log nào để mất.
    no_log = [e["name"] for e in timeline["pods"] if e["log"] is None and e["marks"].get("container_started")]
    n_err, last_err = timeline["errors"], timeline["last_error"]
    if no_log or n_err:
        log(f"  CẢNH BÁO: thiếu log {no_log}; {n_err} lần hỏi pod lỗi ({last_err})")
    gaps = collect.scrape_gaps(
        ctx.prom,
        t.namespace,
        t_main0,
        t_main1,
        at_start=frozenset(p["name"] for p in pods_start),
        at_end=frozenset(p["name"] for p in pods_end if not p.get("deleting")),
    )
    sig = spec.config.signal
    signal = collect.signal_gap(ctx.prom, sig, t_main0, t_main1) if sig else None

    # 7) Kiểm hợp lệ
    lg = attempt_dir / "loadgen.json"
    lg_data = json.loads(lg.read_text(encoding="utf-8")) if lg.exists() else None
    result = checks.evaluate(
        loadgen_rc=res["rc"],
        loadgen_checks=lg_data["checks"] if lg_data else None,
        initial_ok=initial_ok,
        initial_note=initial_note,
        pods_start=pods_start,
        pods_end=pods_end,
        scrape_gaps=gaps,
        signal=signal,
    )
    write_json(attempt_dir / "checks.json", result)
    meta.update(
        {
            "t_warmup": t_warm,
            "t_main_start": t_main0,
            "t_main_end": t_main1,
            "t_end": t_end,
            "cooldown_s": cooldown_s,
            "counts": {
                "metric_rows": n_metric,
                "events": n_event,
                "alerts": n_alert,
                "pods_seen": len(timeline["pods"]),
                "pods_without_log": no_log,
                "pod_poll_errors": timeline["errors"],
            },
            "loadgen_summary": {k: lg_data.get(k) for k in ("n_planned", "n_done", "n_error")}
            if lg_data
            else None,
        }
    )
    write_json(attempt_dir / "metadata.json", meta)
    status = "done" if result["valid"] else "invalid"
    log(f"[{spec.run_id}] {status}" + ("" if result["valid"] else f": {'; '.join(result['reasons'])}"))
    return status


def check_signals(ctx: Context, specs: list[RunSpec]) -> None:
    """Hỏi thử Prometheus tín hiệu scale của các lượt sắp chạy, một lần trước lượt đầu tiên.

    Selector sai cú pháp thì Prometheus trả lỗi (KubeError), phiên dừng ngay, không đợi hết lượt đầu
    (khoảng 35 phút) mới lộ. Không có chuỗi nào (sai label, exporter chưa chạy, simulator không có GPU) thì
    chỉ cảnh báo: lượt đó sẽ bị đánh dấu invalid (checks.py), còn chạy hay dừng do người vận hành quyết.
    Đo luôn độ lệch đồng hồ giữa runner và Prometheus: kiểm tín hiệu tính mép cửa sổ theo đồng hồ runner
    (collect.signal_gap), nên lệch quá khoảng 10 s thì mọi lượt bị loại nhầm. Ngưỡng cảnh báo 5 s để còn dư.
    """
    sels = sorted({s.config.signal for s in specs if s.config.signal})
    if not sels:
        return
    # time() = giờ của Prometheus lúc tính truy vấn; bọc vector() vì prom.scalar đọc kết quả dạng series
    t0 = time.time()
    prom_now = ctx.prom.scalar("vector(time())")
    t1 = time.time()
    skew = None if prom_now is None else prom_now - (t0 + t1) / 2  # so với giữa hai mốc: trừ thời gian gọi
    log(f"đồng hồ Prometheus lệch runner: {'không đọc được' if skew is None else f'{skew:+.1f} s'}")
    if skew is not None and abs(skew) > 5:
        log("CẢNH BÁO: lệch quá 5 s; kiểm tín hiệu scale có thể loại nhầm lượt (đồng bộ NTP hai máy)")
    for sel in sels:
        n = ctx.prom.scalar(f"count({sel})")
        if n:
            log(f"tín hiệu scale {sel}: {n:g} chuỗi")
        else:
            log(f"CẢNH BÁO: tín hiệu scale {sel} hiện không có chuỗi nào; lượt dùng nó sẽ invalid")


def run_session(ctx: Context, only: set[str] | None, max_attempts: int) -> dict[str, str]:
    """Chạy mọi lượt chưa xong. Trả {run_id: trạng thái cuối}."""
    sdir = ctx.runs_dir / ctx.matrix.session
    sdir.mkdir(parents=True, exist_ok=True)
    lock = (sdir / ".lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # NB: không chờ, có runner khác thì báo lỗi ngay
    except BlockingIOError as e:
        raise RuntimeError(f"đang có runner khác chạy phiên {ctx.matrix.session} ({sdir / '.lock'})") from e

    prog = Progress(sdir / "progress.json")
    # Lọc trước một lần (mỗi run_id chỉ có một dòng, progress chỉ đổi cho chính lượt vừa chạy, nên lọc
    # trước hay lọc trong vòng lặp là như nhau), để check_signals chỉ hỏi tín hiệu của lượt sẽ chạy thật.
    pending: list[RunSpec] = []
    for spec in ctx.matrix.runs:
        if only and spec.run_id not in only:
            continue
        if not prog.should_run(spec.run_id, max_attempts):
            log(f"[{spec.run_id}] bỏ qua: {prog.status(spec.run_id)} ({prog.attempts(spec.run_id)} lần thử)")
            continue
        pending.append(spec)
    check_signals(ctx, pending)
    for spec in pending:
        attempt_dir = sdir / spec.run_id / f"attempt-{prog.attempts(spec.run_id) + 1}"
        try:
            status, note = run_one(ctx, spec, attempt_dir), ""
        except KeyboardInterrupt:
            prog.record(spec.run_id, "error", attempt_dir.name, "bị ngắt bằng Ctrl+C")
            raise
        except Exception as e:  # noqa: BLE001 - chạy không người trực: ghi lỗi rồi sang lượt sau
            attempt_dir.mkdir(parents=True, exist_ok=True)
            (attempt_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            status, note = "error", f"{type(e).__name__}: {e}"[:300]
            log(f"[{spec.run_id}] LỖI: {note}")
        prog.record(spec.run_id, status, attempt_dir.name, note)
    return {s.run_id: prog.status(s.run_id) or "-" for s in ctx.matrix.runs}
