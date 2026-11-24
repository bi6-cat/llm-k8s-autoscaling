"""Kịch bản vận hành VH2, VH3, VH4 chạy dưới tải thật, chấm đạt/không đạt (Môi trường §13).

Khái niệm: Mỗi kịch bản gây một thay đổi hoặc sự cố trong khi máy tạo tải đang gửi đều, rồi đếm request lỗi
    và đo thời gian hệ thống trở lại bình thường:
    - vh2a: cập nhật khi có 1 replica, làm theo quy trình: nâng minReplicaCount lên 2, chờ, cập nhật, hạ về 1.
    - vh2b: cập nhật với `maxSurge: 0` khi mọi GPU đều có pod.
    - vh2c: đối chứng kiểu web (`maxSurge: 1`) khi hết GPU: mong đợi rollout KẸT, pod mới Pending.
    - vh3-delete: `kubectl delete pod` khi còn pod khác phục vụ (tự nâng min lên 2 nếu chỉ có 1 pod):
      graceful shutdown, mong đợi 0 lỗi.
    - vh3-kill: `kill -9` tiến trình con của vLLM: mong đợi container restart, chỉ lỗi request trên pod đó.
    - vh3-drain: `kubectl drain` một node (cần ≥ 2 node, nên chỉ ở nhà hoặc simulator).
    - vh4: NetworkPolicy chặn KEDA → Prometheus: mong đợi fallback lên max trong ≤ 30 s (N6), gỡ chặn thì hết.
    - vh2-git: như vh2a nhưng mọi thay đổi đi qua Git (ADR-007 D2, Vận hành §5.3, §5.4), chỉ trên kind có
      Argo CD (make sim-argocd): commit nâng min lên 2 → commit đổi tham số simulator → `git revert` commit
      đó → `git revert` commit nâng min. Mỗi commit push lên nhánh mà Argo CD theo dõi; script chờ Argo CD
      tự sync (không bấm refresh), nên thời gian đo gồm cả chu kỳ đọc Git của Argo CD.
Mục đích: Lặp lại được trên kind, nhà và VM thuê bằng một lệnh; kết quả ghi vào runs/ làm số liệu cho nhật ký
    vận hành. Rolling update ở vh2a–vh2c kích hoạt bằng cách đổi annotation của pod template (một thay đổi
    vô hại nhưng vẫn thay toàn bộ pod), không qua Git. Vì vậy các kịch bản đó từ chối chạy khi Argo CD đang
    tự sync; riêng vh2-git thì ngược lại, đòi Argo CD đang tự sync từ đúng nhánh đã cho.

Chạy (KUBECONFIG/--context trỏ đúng cluster):
    uv run --project experiments python -m experiments.ops.vh vh3-delete \\
        --matrix envs/sim/experiments/matrix.yaml --rate 2 --context kind-llm-sim
    vh2-git cần thêm một git worktree đang ở nhánh mà Argo CD theo dõi (không phải main), sạch, push được:
    ... vh2-git --matrix envs/sim/experiments/matrix.yaml --rate 0.5 --context kind-llm-sim \\
        --git-worktree <thư mục> --git-branch <nhánh>
Kết quả: runs/ops-<kịch bản>-<thời điểm>/: summary.json, timeline.json, load/ (requests.csv của máy tạo tải).
Mã thoát 0 = đạt, 1 = không đạt, 2 = không chạy được.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import threading
import time
from collections import Counter
from collections.abc import Callable, Iterable
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
A2_FILE = "common/autoscaling/a2/scaledobject-a2.yaml"
BLOCK_FILE = REPO / "common" / "autoscaling" / "tests" / "block-keda-to-prometheus.yaml"
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
    # 4 commit, mỗi commit chờ Argo CD đọc Git (vài phút) + 2 rolling update 2 pod của simulator
    "vh2-git": 1800,
}
# vh2-git: hai file mà các commit thử sửa, tính từ gốc worktree; tham số đổi là TTFT giả của simulator
SIM_A2_KUSTOMIZATION = "envs/sim/autoscaling/kustomization.yaml"
SIM_SERVING_PATCH = "envs/sim/serving/patch-sim.yaml"
VH2_GIT_TTFT_MS = 300  # Git đang có 200 ms (patch-sim.yaml); 300 ms đủ khác để thấy bản mới trên TTFT


def with_min_replicas(text: str, n: int) -> str:
    """Thêm thao tác đặt `minReplicaCount` vào JSON patch inline của overlay A2 bản sim. Hàm thuần, có unit
    test. Chèn ngay trước thao tác đổi maxReplicaCount, nên `git revert` commit này trả file về y như cũ."""
    anchor = "      - op: replace\n        path: /spec/maxReplicaCount\n"
    if text.count(anchor) != 1:
        raise ValueError(f"{SIM_A2_KUSTOMIZATION}: không thấy đúng một thao tác đổi maxReplicaCount")
    op = f"      - op: replace\n        path: /spec/minReplicaCount\n        value: {n}\n"
    return text.replace(anchor, op + anchor)


def with_ttft(text: str, ms: int) -> str:
    """Đổi cờ `--time-to-first-token` của simulator thành `ms`. Hàm thuần, có unit test."""
    new, count = re.subn(r"--time-to-first-token=\d+ms", f"--time-to-first-token={ms}ms", text)
    if count != 1:
        raise ValueError(f"{SIM_SERVING_PATCH}: có {count} cờ --time-to-first-token, cần đúng 1")
    return new


@dataclass
class GitTarget:
    """Worktree đang ở nhánh mà Argo CD theo dõi. Mỗi thay đổi = một commit rồi push, như PR đã merge."""

    worktree: Path
    branch: str
    # Chạy trong WSL (nơi có kubectl của kind) thì truyền `git.exe`: git của Windows push bằng credential sẵn
    # có trên Windows. Lệnh chạy với cwd = worktree (không dùng -C), vì WSL tự đổi cwd /mnt/d/... sang D:\...
    # cho chương trình Windows, còn một đường dẫn truyền qua tham số thì không được đổi.
    git_cmd: str = "git"

    def git(self, *args: str) -> str:
        proc = subprocess.run(
            [self.git_cmd, *args], cwd=self.worktree, capture_output=True, text=True, timeout=120, check=False
        )
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.strip()[:300]}")
        return proc.stdout.strip()

    def check(self) -> None:
        """Từ chối nhánh main (Argo CD nhà đọc main) và worktree bẩn (commit thử sẽ kéo theo thứ khác)."""
        if self.branch == "main":
            raise RuntimeError("vh2-git không chạy trên main: dùng một nhánh thử riêng")
        current = self.git("rev-parse", "--abbrev-ref", "HEAD")
        if current != self.branch:
            raise RuntimeError(f"worktree đang ở nhánh {current}, không phải {self.branch}")
        if self.git("status", "--porcelain"):
            raise RuntimeError(f"worktree {self.worktree} còn thay đổi chưa commit")
        # Phải trùng nhánh trên origin: commit chưa push sẽ bị push và áp cùng lượt; origin đi trước thì push
        # bị từ chối giữa lượt
        self.git("fetch", "-q", "origin", self.branch)
        if self.git("rev-parse", "HEAD") != self.git("rev-parse", f"origin/{self.branch}"):
            raise RuntimeError(f"worktree không trùng origin/{self.branch}: pull hoặc push trước")

    def commit_push(self, rel: str, edit: Callable[[str], str], message: str) -> str:
        path = self.worktree / rel
        # bytes thay vì text: Python trên Windows ghi CRLF khi dùng write_text
        path.write_bytes(edit(path.read_bytes().decode("utf-8")).encode("utf-8"))
        self.git("add", rel)
        self.git("commit", "-q", "-m", message)
        self.git("push", "-q", "origin", self.branch)
        return self.git("rev-parse", "HEAD")

    def revert_push(self, sha: str) -> str:
        """Rollback đúng như Vận hành §5.4: `git revert` commit cần bỏ, rồi push."""
        self.git("revert", "--no-edit", sha)
        self.git("push", "-q", "origin", self.branch)
        return self.git("rev-parse", "HEAD")


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
    zero_errors = scenario in ("vh2a", "vh2b", "vh2-git", "vh3-delete", "vh3-drain", "vh4")
    if zero_errors and load.get("errors"):
        why.append(f"có {load['errors']} request lỗi: {load['by_error']}")
    if not facts.get("recovered", False):
        why.append("hệ thống không trở lại đủ replica Ready")
    if scenario == "vh2-git":
        unsynced = [k for k, v in facts.get("phases", {}).items() if v.get("sync_s") is None]
        if unsynced:
            why.append(f"Argo CD không sync commit của bước: {', '.join(unsynced)}")
        if not facts.get("new_version_seen") or not facts.get("old_version_back"):
            why.append("không thấy tham số mới sau cập nhật, hoặc tham số cũ sau rollback")
        if not facts.get("finished_under_load"):
            why.append("kịch bản xong sau khi máy tạo tải đã ngừng: tăng --duration")
    if scenario in ("vh2a", "vh2-git") and facts.get("replicas_before") != 1:
        why.append(f"ca 1 replica nhưng trước khi làm có {facts.get('replicas_before')} replica: giảm --rate")
    if scenario == "vh3-delete" and facts.get("ready_before", 2) < 2:
        why.append("chỉ có 1 pod Ready lúc xoá: lỗi request là do không còn pod nào, không kết luận được")
    if scenario == "vh2c" and not facts.get("rollout_stuck"):
        why.append("rollout kiểu web không bị kẹt như phân tích")
    if scenario == "vh3-kill" and not facts.get("restarted"):
        why.append("container không restart: lệnh kill không có tác dụng trên cluster này")
    if scenario == "vh4":
        t = facts.get("fallback_s")
        if facts.get("replicas_before", 0) >= facts.get("max_replicas", 0):
            why.append("đã ở max replica trước khi chặn nên không đo được fallback: giảm --rate")
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

    def spec_replicas(self) -> int:
        return self.kube.get_json("deploy", self.target.deployment, "-n", self.ns)["spec"]["replicas"]

    def fallback_active(self) -> bool:
        """KEDA đang dùng fallback: condition Fallback của ScaledObject là True (Kiến trúc §13)."""
        so = self.kube.get_json("scaledobject", SO_NAME, "-n", self.ns)
        return any(
            c["type"] == "Fallback" and c["status"] == "True" for c in so["status"].get("conditions", [])
        )

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

    def wait_synced(self, app: str, sha: str, timeout_s: float) -> float | None:
        """Chờ Argo CD sync xong commit `sha` cho Application `app`: lần sync gần nhất là của commit đó và đã
        Succeeded. Trả số giây đã chờ, None nếu hết giờ."""
        start = time.time()
        while time.time() - start < timeout_s:
            st = self.kube.get_json("application", app, "-n", "argocd").get("status", {})
            op = st.get("operationState", {})
            if op.get("syncResult", {}).get("revision") == sha and op.get("phase") == "Succeeded":
                return time.time() - start
            time.sleep(POLL_S)
        return None

    def container_args(self) -> list[str]:
        return self.kube.get_json("deploy", self.target.deployment, "-n", self.ns)["spec"]["template"][
            "spec"
        ]["containers"][0].get("args", [])

    def wait_rollout(self, timeout_s: float) -> bool:
        proc = self.kube.run(
            "rollout", "status", f"deploy/{self.target.deployment}", "-n", self.ns,
            f"--timeout={int(timeout_s)}s", timeout_s=timeout_s + 30, check=False,
        )  # fmt: skip
        return proc.returncode == 0


# ── Từng kịch bản: trả facts để grade() chấm ────────────────────────────────────


def vh2a(o: Ops) -> dict[str, Any]:
    before = o.spec_replicas()  # phải là 1, nếu không thì đây không phải ca cần bước nâng min (grade kiểm)
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
    return {"recovered": ok and second is not None, "rollout_s": time.time() - t0, "replicas_before": before}


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


def vh2_git(o: Ops, git: GitTarget, load_until: float, sync_timeout_s: float = 900) -> dict[str, Any]:
    """vh2a qua Git: 4 commit trên nhánh Argo CD theo dõi. Mỗi bước ghi `sync_s` (giây từ lúc push xong tới
    lúc Argo CD sync xong commit đó, tức độ trễ của Argo CD) và `total_s` (từ trước khi commit tới lúc bước
    hoàn tất: 2 pod Ready, rollout xong, hoặc chỉ sync). `load_until`: mốc sớm nhất máy tạo tải ngừng gửi;
    kịch bản xong sau mốc này thì phần cuối không có tải, nên không chấm là đạt."""
    before = o.spec_replicas()
    phases: dict[str, dict[str, Any]] = {}

    def step(name: str, app: str, push: Callable[[], str]) -> float:
        t0 = o.mark(f"{name}_push")
        sha = push()
        phases[name] = {"sha": sha, "sync_s": None}  # ghi ngay để phần dọn dẹp biết commit nào đã push
        o.mark(f"{name}_pushed", sha=sha[:12])
        phases[name]["sync_s"] = o.wait_synced(app, sha, sync_timeout_s)
        o.mark(f"{name}_synced", sync_s=phases[name]["sync_s"])
        return t0

    def finish(name: str, t0: float, ok: bool) -> None:
        phases[name].update(ok=ok, total_s=time.time() - t0)
        o.mark(f"{name}_done", ok=ok, total_s=phases[name]["total_s"])

    ttft_new = f"--time-to-first-token={VH2_GIT_TTFT_MS}ms"
    # Giá trị đang chạy trước khi cập nhật: rollback phải trả về đúng giá trị này, không chỉ "khác 300 ms"
    ttft_old = next((x for x in o.container_args() if x.startswith("--time-to-first-token=")), None)
    new_seen = old_back = False
    try:
        # Bước 0 của Vận hành §5.3: đang 1 replica thì nâng min lên 2 trước, để rolling update luôn còn 1 pod
        t0 = step("min2", "autoscaling", lambda: git.commit_push(
            SIM_A2_KUSTOMIZATION, lambda t: with_min_replicas(t, 2),
            "test: raise sim A2 min replicas to 2 (VH2)",
        ))  # fmt: skip
        finish("min2", t0, o.wait_ready(2, 900) is not None)
        t0 = step("update", "serving", lambda: git.commit_push(
            SIM_SERVING_PATCH, lambda t: with_ttft(t, VH2_GIT_TTFT_MS),
            f"test: set sim time to first token to {VH2_GIT_TTFT_MS} ms (VH2)",
        ))  # fmt: skip
        finish("update", t0, o.wait_rollout(1800))
        new_seen = ttft_new in o.container_args()
        # Rollback là `git revert`, không phải `kubectl rollout undo` (Vận hành §5.4)
        t0 = step("rollback", "serving", lambda: git.revert_push(phases["update"]["sha"]))
        finish("rollback", t0, o.wait_rollout(1800))
        args = o.container_args()
        old_back = ttft_old is not None and ttft_old in args and ttft_new not in args
        t0 = step("min1", "autoscaling", lambda: git.revert_push(phases["min2"]["sha"]))
        finish("min1", t0, phases["min1"]["sync_s"] is not None)
    finally:
        # Lỗi giữa chừng: revert các commit đã push mà chưa được revert (mới trước, cũ sau), để nhánh và
        # cluster về như trước lượt; nếu không, lượt sau bắt đầu ở min 2 hoặc TTFT mới. Lỗi ở đây chỉ ghi lại.
        for revert_step, pushed in (("rollback", "update"), ("min1", "min2")):
            if pushed in phases and revert_step not in phases:
                try:
                    git.revert_push(phases[pushed]["sha"])
                    o.mark("cleanup_revert", step=pushed)
                except Exception as e:  # noqa: BLE001 - không che lỗi gốc của kịch bản
                    o.mark("cleanup_failed", step=pushed, error=str(e)[:200])
    return {
        "recovered": all(p.get("ok") for p in phases.values()),
        "replicas_before": before,
        "new_version_seen": new_seen,
        "old_version_back": old_back,
        "finished_under_load": time.time() < load_until,
        "phases": phases,
    }


def same_repo(a: str, b: str) -> bool:
    """Hai URL có trỏ cùng một repo không (bỏ qua `.git`, dấu `/` cuối, hoa thường). Hàm thuần."""
    x, y = (u.strip().rstrip("/").removesuffix(".git").lower() for u in (a, b))
    return x == y


def argocd_problem(app: dict[str, Any], branch: str, origin: str) -> str | None:
    """Application có đang tự sync từ đúng repo `origin`, nhánh `branch` không; trả lý do nếu không. Hàm
    thuần, có unit test. Sai repo thì push vẫn thành công nhưng Argo CD không bao giờ thấy commit."""
    name = app.get("metadata", {}).get("name", "?")
    src = app.get("spec", {}).get("source", {})
    if not same_repo(src.get("repoURL", ""), origin):
        return f"Application {name} đọc repo {src.get('repoURL')}, còn worktree push lên {origin}"
    rev = src.get("targetRevision")
    if rev != branch:
        return (
            f"Application {name} theo dõi '{rev}', không phải '{branch}': make sim-argocd ARGOCD_REV={branch}"
        )
    if not configs.autosync_enabled(app):
        return f"Application {name} không bật auto-sync"
    return None


def vh3_delete(o: Ops) -> dict[str, Any]:
    """Xoá một pod trong khi còn pod khác phục vụ. Tiêu chí 0 request lỗi (grade) chỉ có nghĩa khi vẫn còn
    ít nhất một pod Ready sau khi xoá: Service bỏ pod đang tắt khỏi danh sách endpoint ngay, nên nếu đó là
    pod duy nhất thì mọi request mới lỗi kết nối cho tới khi pod thay thế Ready (cả một lần cold start).
    Đo 16/11 trên máy thuê 2 GPU, tải 0,5 C nên A2 giữ 1 pod: xoá pod đó → 61 s không có pod, 90 request lỗi.
    Vì vậy khi chỉ có 1 pod Ready thì nâng min lên 2 trước, như vh2a, và luôn trả min về 1 sau đó."""
    before = o.ready_names()
    if not before:
        raise RuntimeError("không có pod Ready để xoá")
    raised = len(before) < 2
    try:
        if raised:
            if o.max_replicas < 2:
                raise RuntimeError("cần ≥ 2 pod để xoá một pod mà không mất dịch vụ, nhưng max replica là 1")
            o.scale_min(2)
            o.mark("min_replicas_2")
            second = o.wait_ready(2, 900)
            o.mark("two_ready", waited_s=second)
            if second is None:
                raise RuntimeError("không lên được 2 pod Ready trong 900 s")
            before = o.ready_names()
        t0 = o.mark("delete", pod=before[0], ready_before=len(before))
        # --wait=false: lệnh trả về ngay, không phải chờ pod tắt hết grace period
        o.kube.run("delete", "pod", before[0], "-n", o.ns, "--wait=false")
        back = o.wait_ready(len(before), 900, exclude={before[0]})
        o.mark("replaced", seconds=back)
    finally:
        if raised:
            o.scale_min(1)  # kể cả khi lỗi giữa chừng: không để cluster kẹt ở min 2
            o.mark("min_replicas_1")
    return {"recovered": back is not None, "replace_s": back, "t_action": t0, "ready_before": len(before)}


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


def pick_drain_node(o: Ops) -> str:
    """Node sẽ drain: node đang có pod vLLM. Cần ≥ 2 node, vì drain còn đuổi cả Prometheus và KEDA."""
    if len(o.kube.get_json("nodes")["items"]) < 2:
        raise RuntimeError("chỉ có 1 node: drain sẽ tắt cả Prometheus và KEDA; chạy VH3 drain ở simulator")
    return o.pods()[0]["spec"]["nodeName"]


def vh3_drain(o: Ops, node: str) -> dict[str, Any]:
    want = len(o.ready_names())
    t0 = o.mark("drain", node=node)
    # --ignore-daemonsets: DaemonSet (exporter) không chuyển đi được. --delete-emptydir-data: cho phép xoá
    # pod có emptyDir. Timeout 600 s vì grace period của vLLM là 180 s.
    o.kube.run(
        "drain", node, "--ignore-daemonsets", "--delete-emptydir-data", "--timeout=600s", timeout_s=660
    )
    # `drain` chỉ trả về khi pod cũ đã đi hết; đo từ lúc bắt đầu drain tới khi đủ pod Ready lại
    back = o.wait_ready(want, 900)
    recover_s = time.time() - t0 if back is not None else None
    o.mark("drained", seconds=recover_s)
    return {"recovered": back is not None, "recover_s": recover_s, "t_action": t0}


def vh4(o: Ops, block_s: float = 300) -> dict[str, Any]:
    before = o.spec_replicas()
    t0 = o.mark("block_prometheus", replicas_before=before)
    fallback_s = None
    try:
        o.kube.run("apply", "-f", str(BLOCK_FILE))
        while time.time() - t0 < block_s:
            # Cần CẢ HAI: chỉ xem replica thì tải cao đã đẩy lên max cũng bị tính nhầm là fallback (09/11)
            if fallback_s is None and o.fallback_active() and o.spec_replicas() >= o.max_replicas:
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
        if not o.fallback_active():
            unblocked_ok = True
            break
        time.sleep(POLL_S)
    o.mark("signal_back", ok=unblocked_ok)
    back = o.wait_ready(1, 600)
    return {
        "recovered": back is not None,
        "fallback_s": fallback_s,
        "unblocked_ok": unblocked_ok,
        "replicas_before": before,
        "max_replicas": o.max_replicas,
    }


SCENARIOS = {
    "vh2a": vh2a,
    "vh2b": vh2b,
    "vh2c": vh2c,
    "vh2-git": vh2_git,  # gọi riêng trong main vì cần worktree
    "vh3-delete": vh3_delete,
    "vh3-kill": vh3_kill,
    "vh3-drain": vh3_drain,  # gọi riêng trong main vì cần node đã cordon trước khi có tải
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
    p.add_argument("--git-worktree", type=Path, help="vh2-git: worktree ở nhánh Argo CD theo dõi")
    p.add_argument("--git-branch", help="vh2-git: tên nhánh đó (trùng ARGOCD_REV của make sim-argocd)")
    p.add_argument("--git-cmd", default="git", help="vh2-git: lệnh git; trong WSL dùng git.exe của Windows")
    a = p.parse_args(argv)
    git = None
    if a.scenario == "vh2-git":
        if not (a.git_worktree and a.git_branch):
            print("vh2-git cần --git-worktree và --git-branch", file=sys.stderr)
            return 2
        git = GitTarget(a.git_worktree, a.git_branch, a.git_cmd)

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
        if git:
            # Ngược với các kịch bản khác: A2 và simulator do Argo CD áp từ nhánh thử, script không áp gì
            git.check()
            origin = git.git("remote", "get-url", "origin")
            for name in ("serving", "autoscaling"):
                problem = argocd_problem(
                    kube.get_json("application", name, "-n", "argocd"), git.branch, origin
                )
                if problem:
                    raise RuntimeError(problem)
            so = kube.get_json("scaledobject", SO_NAME, "-n", target.namespace)
            # KEDA có hai annotation tạm dừng: giữ số replica cố định, hoặc dừng hẳn
            paused = {configs.PAUSE_ANNOTATION, "autoscaling.keda.sh/paused"} & set(
                so["metadata"].get("annotations", {})
            )
            if paused:
                raise RuntimeError(f"ScaledObject {SO_NAME} đang tạm dừng: gỡ annotation {', '.join(paused)}")
        else:
            configs.guard_argocd(kube)  # thay đổi ở đây sẽ bị Argo CD selfHeal hoàn tác giữa chừng
            doc = yaml.safe_load((REPO / A2_FILE).read_text(encoding="utf-8"))
            so = configs.render_scaledobject(doc, a2.overrides, paused=False)
            so["metadata"]["namespace"] = target.namespace
            kube.apply(yaml.safe_dump(so, sort_keys=False))
    except (KubeError, RuntimeError, OSError, subprocess.TimeoutExpired) as e:  # OSError: không có lệnh git
        print(f"Không chuẩn bị được cluster: {e}", file=sys.stderr)
        return 2

    # vh2a, vh4 cần bắt đầu từ 1 replica; lượt trước có thể còn nhiều replica vì cửa sổ scale-down 300 s.
    if a.scenario in ("vh2a", "vh2-git", "vh4"):
        end = time.time() + 900
        while ops.spec_replicas() > 1 and time.time() < end:
            time.sleep(POLL_S)
        ops.mark("settled", replicas=ops.spec_replicas())

    # vh3-drain: cordon node sẽ drain TRƯỚC khi có tải, để pod máy tạo tải không xếp vào đó. Nếu không, drain
    # đuổi luôn máy tạo tải và mất toàn bộ kết quả (gặp 09/11: lần đầu đạt chỉ vì tình cờ khác node).
    drain_node = None
    if a.scenario == "vh3-drain":
        try:
            drain_node = pick_drain_node(ops)
        except RuntimeError as e:
            print(f"Không chạy được: {e}", file=sys.stderr)
            return 2
        kube.run("cordon", drain_node)

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
    load_t0 = ops.mark("load_started", rate=a.rate)
    time.sleep(LEAD_S + 60)  # 60 s cho pod máy tạo tải cài thư viện, LEAD_S để có tải nền

    facts: dict[str, Any] = {}
    error = None
    try:
        if a.scenario == "vh3-drain":
            facts = vh3_drain(ops, drain_node)
        elif a.scenario == "vh4":
            facts = vh4(ops, a.block_s)
        elif git:
            # Máy tạo tải bắt đầu gửi sau mốc load_started (pod còn phải cài thư viện), nên mốc này + duration
            # là lúc sớm nhất nó ngừng
            facts = vh2_git(ops, git, load_t0 + duration)
        else:
            facts = SCENARIOS[a.scenario](ops)
    except Exception as e:  # noqa: BLE001 - vẫn phải chờ tải xong để ghi kết quả
        error = f"{type(e).__name__}: {e}"[:500]
        ops.mark("scenario_error", error=error)
    finally:
        if drain_node:
            kube.run("uncordon", drain_node, check=False)  # luôn trả node về, kể cả khi drain lỗi

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
