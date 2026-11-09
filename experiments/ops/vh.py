"""Kịch bản vận hành VH2, VH3, VH4 chạy dưới tải thật, chấm đạt/không đạt (Môi trường §13).

Khái niệm: Mỗi kịch bản gây một thay đổi hoặc sự cố trong khi máy tạo tải đang gửi đều, rồi đếm request lỗi
    và đo thời gian hệ thống trở lại bình thường:
    - vh2a: cập nhật khi có 1 replica, làm theo quy trình: nâng minReplicaCount lên 2, chờ, cập nhật, hạ về 1.
    - vh2b: cập nhật với `maxSurge: 0` khi mọi GPU đều có pod.
    - vh2c: đối chứng kiểu web (`maxSurge: 1`) khi hết GPU: mong đợi rollout KẸT, pod mới Pending.
    - vh3-delete: `kubectl delete pod`: graceful shutdown, mong đợi 0 lỗi.
    - vh3-kill: `kill -9` tiến trình con của vLLM: mong đợi container restart, chỉ lỗi request trên pod đó.
    - vh3-drain: `kubectl drain` một node (cần ≥ 2 node, nên chỉ ở nhà hoặc simulator).
    - vh4: NetworkPolicy chặn KEDA → Prometheus: mong đợi fallback lên max trong ≤ 30 s (N6), gỡ chặn thì hết.
Mục đích: Lặp lại được trên kind, nhà và VM thuê bằng một lệnh; kết quả ghi vào runs/ làm số liệu cho nhật ký
    vận hành. Rolling update ở đây kích hoạt bằng cách đổi annotation của pod template (một thay đổi vô hại
    nhưng vẫn thay toàn bộ pod), không qua Git. Vì vậy script từ chối chạy khi Argo CD đang tự sync, và
    VH2 qua Git + Argo CD ở nhà vẫn phải làm theo Vận hành §5.3.

Chạy (KUBECONFIG/--context trỏ đúng cluster):
    uv run --project experiments python -m experiments.ops.vh vh3-delete \\
        --matrix experiments/matrix-sim.yaml --rate 2 --context kind-llm-sim
Kết quả: runs/ops-<kịch bản>-<thời điểm>/: summary.json, timeline.json, load/ (requests.csv của máy tạo tải).
Mã thoát 0 = đạt, 1 = không đạt, 2 = không chạy được.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from experiments.runner import configs
from experiments.runner import matrix as matrix_mod
from experiments.runner.kube import Kube, KubeError
from experiments.runner.loadjob import LoadJob, loadgen_args
from experiments.runner.matrix import Target

REPO = Path(__file__).resolve().parents[2]
A2_FILE = "autoscaling/official/base/scaledobject-a2.yaml"
BLOCK_FILE = REPO / "autoscaling" / "tests" / "t4-block-keda-to-prometheus.yaml"
SO_NAME = "vllm-a2"
LEAD_S = 60  # gửi tải 60 s trước khi gây sự cố, để có nền "trước sự cố" so sánh
FALLBACK_LIMIT_S = 30  # N6: mất Prometheus thì fallback lên max trong ≤ 30 s
POLL_S = 5
# Thời lượng tải mặc định (giây), đủ cho kịch bản trên VM: drain 180 s + cold start ~2 phút mỗi pod.
# Rollout 4 pod khoảng 20 phút; vh2c chờ kẹt 5 phút rồi khôi phục; vh4 chặn 5 phút rồi chờ tín hiệu.
DEFAULT_DURATION_S = {
    "vh2a": 1200,
    "vh2b": 2400,
    "vh2c": 3000,
    "vh3-delete": 780,
    "vh3-kill": 600,
    "vh3-drain": 900,
    "vh4": 720,
}


def analyze_requests(rows: Iterable[dict[str, str]]) -> dict[str, Any]:
    """Đếm kết quả từ requests.csv. Hàm thuần. Lọc theo cột `error` chứ không theo `status`: stream bị cắt
    giữa chừng vẫn có status 200 (loadgen/sender.py)."""
    total, errors = 0, Counter()
    for r in rows:
        total += 1
        if r.get("error"):
            errors[r["error"]] += 1
    return {"requests": total, "errors": sum(errors.values()), "by_error": dict(errors)}


def grade(scenario: str, load: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    """Trả danh sách lý do KHÔNG đạt; rỗng = đạt (tiêu chí ở Môi trường §13). Hàm thuần."""
    why: list[str] = []
    if load.get("requests", 0) == 0:
        why.append("không có request nào: không kết luận được")
    zero_errors = scenario in ("vh2a", "vh2b", "vh3-delete", "vh3-drain", "vh4")
    if zero_errors and load.get("errors"):
        why.append(f"có {load['errors']} request lỗi: {load['by_error']}")
    if not facts.get("recovered", False):
        why.append("hệ thống không trở lại đủ replica Ready")
    if scenario == "vh2c" and not facts.get("rollout_stuck"):
        why.append("rollout kiểu web không bị kẹt như phân tích")
    if scenario == "vh3-kill" and not facts.get("restarted"):
        why.append("container không restart: lệnh kill không có tác dụng trên cluster này")
    if scenario == "vh4":
        t = facts.get("fallback_s")
        if t is None:
            why.append("KEDA không fallback lên max")
        elif t > FALLBACK_LIMIT_S:
            why.append(f"fallback sau {t:.0f} s, quá {FALLBACK_LIMIT_S} s (N6)")
        if not facts.get("unblocked_ok"):
            why.append("sau khi gỡ chặn, tín hiệu scale không hoạt động lại")
    return why


@dataclass
class Ops:
    kube: Kube
    target: Target
    max_replicas: int
    timeline: list[dict[str, Any]] = field(default_factory=list)

    def mark(self, event: str, **data: Any) -> float:
        now = time.time()
        self.timeline.append({"t": now, "event": event, **data})
        print(f"{datetime.now(UTC):%H:%M:%S} {event} {data or ''}", flush=True)
        return now

    @property
    def ns(self) -> str:
        return self.target.namespace

    def pods(self) -> list[dict[str, Any]]:
        sel = f"app={self.target.deployment}"
        return self.kube.get_json("pods", "-n", self.ns, "-l", sel)["items"]

    def ready_names(self) -> list[str]:
        out = []
        for p in self.pods():
            if p["metadata"].get("deletionTimestamp"):
                continue  # pod đang tắt vẫn có thể báo Ready=True trong lúc chờ preStop
            conds = p["status"].get("conditions", [])
            if any(c["type"] == "Ready" and c["status"] == "True" for c in conds):
                out.append(p["metadata"]["name"])
        return out

    def wait_ready(self, n: int, timeout_s: float, exclude: set[str] | None = None) -> float | None:
        """Chờ tới khi có ít nhất n pod Ready (không tính `exclude`). Trả số giây đã chờ, None nếu hết giờ."""
        start = time.time()
        while time.time() - start < timeout_s:
            if len(set(self.ready_names()) - (exclude or set())) >= n:
                return time.time() - start
            time.sleep(POLL_S)
        return None

    def scale_min(self, n: int) -> None:
        patch = {"spec": {"minReplicaCount": n}}
        self.kube.run(
            "patch", "scaledobject", SO_NAME, "-n", self.ns, "--type=merge", "-p", json.dumps(patch)
        )

    def trigger_rollout(self, stamp: str) -> None:
        """Đổi annotation trên pod template: Deployment coi là phiên bản mới và thay toàn bộ pod."""
        patch = {"spec": {"template": {"metadata": {"annotations": {"experiment/ops-rollout": stamp}}}}}
        self.kube.run(
            "patch", "deploy", self.target.deployment, "-n", self.ns, "--type=merge", "-p", json.dumps(patch)
        )

    def set_strategy(self, max_surge: int, max_unavailable: int) -> None:
        patch = {
            "spec": {
                "strategy": {"rollingUpdate": {"maxSurge": max_surge, "maxUnavailable": max_unavailable}}
            }
        }
        self.kube.run(
            "patch", "deploy", self.target.deployment, "-n", self.ns, "--type=merge", "-p", json.dumps(patch)
        )

    def wait_rollout(self, timeout_s: float) -> bool:
        proc = self.kube.run(
            "rollout", "status", f"deploy/{self.target.deployment}", "-n", self.ns,
            f"--timeout={int(timeout_s)}s", timeout_s=timeout_s + 30, check=False,
        )  # fmt: skip
        return proc.returncode == 0


# ── Từng kịch bản: trả facts để grade() chấm ────────────────────────────────────


def vh2a(o: Ops) -> dict[str, Any]:
    o.scale_min(2)
    o.mark("min_replicas_2")
    second = o.wait_ready(2, 900)
    o.mark("two_ready", waited_s=second)
    t0 = o.mark("rollout_start")
    o.trigger_rollout(str(int(t0)))
    ok = o.wait_rollout(1800)
    o.mark("rollout_end", ok=ok, seconds=time.time() - t0)
    o.scale_min(1)
    o.mark("min_replicas_1")
    return {"recovered": ok and second is not None, "rollout_s": time.time() - t0}


def vh2b(o: Ops) -> dict[str, Any]:
    o.scale_min(o.max_replicas)
    o.mark("all_gpus_filling", replicas=o.max_replicas)
    full = o.wait_ready(o.max_replicas, 1200)
    t0 = o.mark("rollout_start", waited_s=full)
    o.trigger_rollout(str(int(t0)))
    ok = o.wait_rollout(1800)
    secs = time.time() - t0
    o.mark("rollout_end", ok=ok, seconds=secs)
    o.scale_min(1)
    return {"recovered": ok and full is not None, "rollout_s": secs}


def vh2c(o: Ops, stuck_after_s: float = 300) -> dict[str, Any]:
    """Đối chứng: maxSurge 1 khi mọi GPU có pod → pod mới Pending, rollout không tiến. Luôn khôi phục."""
    o.scale_min(o.max_replicas)
    full = o.wait_ready(o.max_replicas, 1200)
    o.set_strategy(1, 0)
    try:
        t0 = o.mark("rollout_start", waited_s=full)
        o.trigger_rollout(str(int(t0)))
        finished = o.wait_rollout(stuck_after_s)
        pending = [p["metadata"]["name"] for p in o.pods() if p["status"].get("phase") == "Pending"]
        o.mark("after_wait", rollout_finished=finished, pending=pending)
        stuck = not finished and bool(pending)
    finally:
        # Trả chiến lược thiết kế; rollout dở sẽ tự hoàn tất với maxSurge 0
        o.set_strategy(0, 1)
    ok = o.wait_rollout(1800)
    o.mark("restored", ok=ok)
    o.scale_min(1)
    return {"recovered": ok, "rollout_stuck": stuck, "pending_pods": pending}


def vh3_delete(o: Ops) -> dict[str, Any]:
    before = o.ready_names()
    if not before:
        raise RuntimeError("không có pod Ready để xoá")
    t0 = o.mark("delete", pod=before[0])
    # --wait=false: lệnh trả về ngay, không phải chờ pod tắt hết grace period
    o.kube.run("delete", "pod", before[0], "-n", o.ns, "--wait=false")
    back = o.wait_ready(len(before), 900, exclude={before[0]})
    o.mark("replaced", seconds=back)
    return {"recovered": back is not None, "replace_s": back, "t_action": t0}


def vh3_kill(o: Ops) -> dict[str, Any]:
    """Giết mọi tiến trình con trong container. Lưu ý: trong PID namespace, PID 1 bỏ qua cả SIGKILL gửi từ bên
    trong, nên không `kill -9 1` được. vLLM chạy engine ở tiến trình con; simulator chỉ có một tiến trình nên
    lệnh không có tác dụng và kịch bản báo không đạt, đúng là chưa kiểm được."""
    pod = o.ready_names()[0]
    before = o.kube.get_json("pod", pod, "-n", o.ns)["status"]["containerStatuses"][0]["restartCount"]
    # /proc/[0-9]*: mọi tiến trình; bỏ PID 1 và chính shell ($$); ${p##*/} = phần sau dấu / cuối, tức PID.
    script = (
        'for p in /proc/[0-9]*; do n=${p##*/}; [ "$n" = 1 ] || [ "$n" = "$$" ] || kill -9 "$n"; done'
        " 2>/dev/null"
    )
    t0 = o.mark("kill", pod=pod, restarts_before=before)
    o.kube.run("exec", pod, "-n", o.ns, "--", "sh", "-c", script, check=False)
    deadline = t0 + 900
    restarted, status = False, None
    while time.time() < deadline:
        status = o.kube.get_json("pod", pod, "-n", o.ns)["status"]["containerStatuses"][0]
        if status["restartCount"] > before:
            restarted = True
            if status.get("ready"):
                break
        elif time.time() - t0 > 180:
            break  # sau 3 phút không restart: lệnh kill không có tác dụng
        time.sleep(POLL_S)
    secs = time.time() - t0
    o.mark("after_kill", restarted=restarted, ready=bool(status and status.get("ready")), seconds=secs)
    return {"recovered": bool(status and status.get("ready")), "restarted": restarted, "recover_s": secs}


def vh3_drain(o: Ops) -> dict[str, Any]:
    nodes = o.kube.get_json("nodes")["items"]
    if len(nodes) < 2:
        raise RuntimeError("chỉ có 1 node: drain sẽ tắt cả Prometheus và KEDA; chạy VH3 drain ở simulator")
    pods = o.pods()
    node = pods[0]["spec"]["nodeName"]
    want = len(o.ready_names())
    t0 = o.mark("drain", node=node)
    try:
        # --ignore-daemonsets: DaemonSet (exporter) không chuyển đi được. --delete-emptydir-data: cho phép xoá
        # pod có emptyDir. Timeout 600 s vì grace period của vLLM là 180 s.
        o.kube.run(
            "drain", node, "--ignore-daemonsets", "--delete-emptydir-data", "--timeout=600s", timeout_s=660
        )
        back = o.wait_ready(want, 900)
        o.mark("drained", seconds=back)
    finally:
        o.kube.run("uncordon", node)  # luôn trả node về, kể cả khi drain lỗi
    return {"recovered": back is not None, "recover_s": back, "t_action": t0}


def vh4(o: Ops, block_s: float = 300) -> dict[str, Any]:
    t0 = o.mark("block_prometheus")
    fallback_s = None
    try:
        o.kube.run("apply", "-f", str(BLOCK_FILE))
        while time.time() - t0 < block_s:
            hpa = o.kube.get_json("deploy", o.target.deployment, "-n", o.ns)["spec"]["replicas"]
            if fallback_s is None and hpa >= o.max_replicas:
                fallback_s = time.time() - t0
                o.mark("fallback_reached", seconds=fallback_s)
            time.sleep(1)
    finally:
        o.kube.run("delete", "-f", str(BLOCK_FILE), "--ignore-not-found", check=False)  # luôn gỡ chặn
    o.mark("unblocked")
    # Gỡ chặn rồi: ScaledObject phải hết báo Fallback, tức KEDA lại đọc được Prometheus
    unblocked_ok = False
    end = time.time() + 120
    while time.time() < end:
        so = o.kube.get_json("scaledobject", SO_NAME, "-n", o.ns)
        conds = {c["type"]: c["status"] for c in so["status"].get("conditions", [])}
        if conds.get("Fallback") != "True":
            unblocked_ok = True
            break
        time.sleep(POLL_S)
    o.mark("signal_back", ok=unblocked_ok)
    back = o.wait_ready(1, 600)
    return {"recovered": back is not None, "fallback_s": fallback_s, "unblocked_ok": unblocked_ok}


SCENARIOS = {
    "vh2a": vh2a,
    "vh2b": vh2b,
    "vh2c": vh2c,
    "vh3-delete": vh3_delete,
    "vh3-kill": vh3_kill,
    "vh3-drain": vh3_drain,
    "vh4": vh4,
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m experiments.ops.vh", description=__doc__.split("\n")[0])
    p.add_argument("scenario", choices=sorted(SCENARIOS))
    p.add_argument("--matrix", type=Path, required=True, help="Lấy target và max replica của A2 từ file này")
    p.add_argument("--rate", type=float, required=True, help="Tải nền, req/s (nên khoảng 0,5 C)")
    p.add_argument("--duration", type=float, help="Thời lượng tải, giây (mặc định theo kịch bản)")
    p.add_argument("--block-s", type=float, default=300, help="vh4: thời gian chặn Prometheus, giây")
    p.add_argument("--context")
    p.add_argument("--max-replicas", type=int, help="Mặc định: max_replicas của A2 trong ma trận")
    a = p.parse_args(argv)

    try:
        m = matrix_mod.load(a.matrix)
    except matrix_mod.MatrixError as e:
        print(f"Lỗi file ma trận: {e}", file=sys.stderr)
        return 2
    a2 = next((r.config for r in m.runs if r.config.id == "A2"), None)
    if a2 is None:
        print("Ma trận không có cấu hình A2", file=sys.stderr)
        return 2
    max_replicas = a.max_replicas or int(a2.overrides.get("max_replicas", 1))

    duration = a.duration or DEFAULT_DURATION_S[a.scenario]
    kube = Kube(context=a.context, timeout_s=120)
    target = m.target
    out = REPO / "runs" / f"ops-{a.scenario}-{datetime.now(UTC):%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    ops = Ops(kube, target, max_replicas)
    try:
        configs.guard_argocd(kube)  # thay đổi ở đây sẽ bị Argo CD selfHeal hoàn tác giữa chừng
        doc = yaml.safe_load((REPO / A2_FILE).read_text(encoding="utf-8"))
        so = configs.render_scaledobject(doc, a2.overrides, paused=False)
        so["metadata"]["namespace"] = target.namespace
        kube.apply(yaml.safe_dump(so, sort_keys=False))
    except KubeError as e:
        print(f"Không chuẩn bị được cluster: {e}", file=sys.stderr)
        return 2

    # Máy tạo tải chạy trong pod (đi qua Service như client thật), ở luồng nền vì LoadJob.run chờ tới khi xong
    job = LoadJob(kube, target, REPO)
    job.sync_code()
    args = loadgen_args(
        "CONST", capacity=None, rate=a.rate, duration=duration, kb3_replicas=max_replicas, run_index=1,
        url=target.service_url, model=target.model, out="/out", workers=target.loadgen_workers,
    )  # fmt: skip
    load_result: dict[str, Any] = {}

    def run_load() -> None:
        try:
            load_result.update(job.run(a.scenario.replace("-", ""), "ops", args, duration, out / "load"))
        except Exception as e:  # noqa: BLE001 - báo trong summary, không làm mất timeline
            load_result["error"] = f"{type(e).__name__}: {e}"[:300]

    loader = threading.Thread(target=run_load, daemon=True)
    loader.start()
    ops.mark("load_started", rate=a.rate)
    time.sleep(LEAD_S + 60)  # 60 s cho pod máy tạo tải cài thư viện, LEAD_S để có tải nền

    facts: dict[str, Any] = {}
    error = None
    try:
        facts = vh4(ops, a.block_s) if a.scenario == "vh4" else SCENARIOS[a.scenario](ops)
    except Exception as e:  # noqa: BLE001 - vẫn phải chờ tải xong để ghi kết quả
        error = f"{type(e).__name__}: {e}"[:500]
        ops.mark("scenario_error", error=error)

    # Máy tạo tải chỉ ghi kết quả khi chạy xong lịch, nên phải chờ trọn --duration kể cả khi kịch bản xong
    # sớm. Vì vậy mặc định của --duration đặt riêng cho từng kịch bản (DEFAULT_DURATION_S).
    loader.join()
    requests_csv = out / "load" / "requests.csv"
    load = {"requests": 0, "errors": 0, "by_error": {}}
    if requests_csv.exists():
        with requests_csv.open(encoding="utf-8") as fh:
            load = analyze_requests(csv.DictReader(fh))

    reasons = grade(a.scenario, load, facts)
    if error:
        reasons.insert(0, error)
    if load_result.get("error"):
        reasons.insert(0, f"máy tạo tải lỗi: {load_result['error']}")
    summary = {
        "scenario": a.scenario,
        "passed": not reasons,
        "reasons": reasons,
        "load": load,
        "facts": facts,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "timeline.json").write_text(
        json.dumps(ops.timeline, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Kết quả: {out}")
    return 0 if not reasons else 1


if __name__ == "__main__":
    sys.exit(main())
