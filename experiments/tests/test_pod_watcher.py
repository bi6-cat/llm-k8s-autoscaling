"""Unit test cho ảnh chụp pod và PodWatcher (experiments/runner/collect.py), không cần cluster.

Khái niệm: Pod condition = một mục trong status.conditions của pod (PodScheduled, Ready…), kèm
    lastTransitionTime là lúc nó đổi trạng thái LẦN GẦN NHẤT. PodWatcher là luồng nền của runner, hỏi pod
    mỗi 5 s và giữ mốc đầu tiên của từng loại. Ở đây kubectl được thay bằng FakeKube trả kết quả dựng sẵn.
Mục đích: Kiểm rằng runner giữ được mốc thời gian và log của pod bị scale-down giữa lượt (pha cold start
    1, 2, 4, 8; GPU-giờ). JSON pod dựng tay theo đúng hình dạng API trả về (đối chiếu một pod simulator
    trên kind, Kubernetes v1.37.0, ngày 08/11): condition có lastTransitionTime chỉ tới giây; sau khi
    container restart thì PodReadyToStartContainers và Ready mang mốc của lần đổi mới nhất.
"""

from __future__ import annotations

import time
from datetime import datetime
from types import SimpleNamespace

from experiments.runner import collect
from experiments.runner.kube import KubeError


def U(stamp: str) -> float:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()


def pod_json(
    name: str,
    conds: dict[str, tuple[str, str]] | None = None,
    *,
    state: dict | None = None,
    deletion: str | None = None,
    grace: int = 180,
    restarts: int = 0,
    last_terminated: str | None = None,
    cname: str = "vllm",
) -> dict:
    """Một pod như `kubectl get pods -o json` trả về. conds: {loại: (status, lastTransitionTime)}."""
    meta = {"name": name, "creationTimestamp": "2026-11-08T10:00:00Z"}
    if deletion:
        meta |= {"deletionTimestamp": deletion, "deletionGracePeriodSeconds": grace}
    cs = {
        "name": cname,
        "ready": (conds or {}).get("Ready", ("False",))[0] == "True",
        "restartCount": restarts,
        "imageID": "docker.io/vllm/vllm-openai@sha256:abc",
        "state": state or {"waiting": {"reason": "ContainerCreating"}},
    }
    if last_terminated:
        cs["lastState"] = {"terminated": {"reason": last_terminated, "exitCode": 137}}
    return {
        "metadata": meta,
        "spec": {"nodeName": "llm-sim-worker"},
        "status": {
            "phase": "Running",
            "conditions": [
                {"type": t, "status": s, "lastTransitionTime": ts, "lastProbeTime": None}
                for t, (s, ts) in (conds or {}).items()
            ],
            "containerStatuses": [cs],
        },
    }


RUNNING = {"running": {"startedAt": "2026-11-08T10:00:07Z"}}
UP = {
    "PodScheduled": ("True", "2026-11-08T10:00:01Z"),
    "PodReadyToStartContainers": ("True", "2026-11-08T10:00:03Z"),
    "Initialized": ("True", "2026-11-08T10:00:03Z"),
    "ContainersReady": ("True", "2026-11-08T10:01:30Z"),
    "Ready": ("True", "2026-11-08T10:01:30Z"),
}


class FakeKube:
    """kubectl giả. `polls`: kết quả lần lượt của `get pods` (danh sách pod JSON, hoặc exception để raise);
    hết danh sách thì lặp lại phần tử cuối. `logs`: tên pod → kết quả lần lượt của `kubectl logs`
    (chuỗi = stdout, None = lỗi NotFound, exception = raise)."""

    def __init__(self, polls, logs=None):
        self.polls, self.logs, self.log_calls = list(polls), {k: list(v) for k, v in (logs or {}).items()}, []

    @staticmethod
    def _next(seq):
        return seq.pop(0) if len(seq) > 1 else seq[0]

    def get_json(self, *args):
        item = self._next(self.polls)
        if isinstance(item, Exception):
            raise item
        return {"items": item}

    def run(self, *args, stdin=None, timeout_s=None, check=True):
        assert args[0] == "logs" and "--timestamps" in args
        self.log_calls.append(args)
        out = self._next(self.logs.get(args[1], [None]))
        if isinstance(out, Exception):
            raise out
        if out is None:
            return SimpleNamespace(returncode=1, stdout="", stderr=f'pods "{args[1]}" not found')
        return SimpleNamespace(returncode=0, stdout=out, stderr="")


def test_snapshot_pods_keeps_validity_fields_and_adds_times():
    p = pod_json("vllm-a", UP, state=RUNNING, restarts=1, last_terminated="OOMKilled")
    [s] = collect.snapshot_pods(FakeKube([[p]]), "ns", "vllm")
    # Các trường checks.py đang dùng: giữ nguyên
    assert (s["name"], s["deleting"], s["restarts"]) == ("vllm-a", False, 1)
    assert s["last_terminated"] == ["OOMKilled"]
    assert s["image_ids"] == ["docker.io/vllm/vllm-openai@sha256:abc"]
    # Trường mới cho pha cold start
    assert s["node"] == "llm-sim-worker" and s["created"] == "2026-11-08T10:00:00Z"
    assert s["conditions"]["Ready"] == {"status": "True", "time": "2026-11-08T10:01:30Z", "reason": None}
    assert s["containers"] == [
        {
            "name": "vllm",
            "state": "running",
            "reason": None,
            "started_at": "2026-11-08T10:00:07Z",
            "finished_at": None,
            "ready": True,
            "restarts": 1,
        }
    ]
    assert s["init_containers"] == [] and s["deletion_timestamp"] is None


def test_pod_marks_maps_conditions_to_phases():
    p = pod_json("vllm-a", UP, state=RUNNING, deletion="2026-11-08T10:10:00Z", grace=180)
    [s] = collect.snapshot_pods(FakeKube([[p]]), "ns", "vllm")
    m = collect.pod_marks(s)
    assert m["created"] == U("2026-11-08T10:00:00Z")
    assert m["scheduled"] == U("2026-11-08T10:00:01Z")
    assert m["sandbox_ready"] == U("2026-11-08T10:00:03Z")
    assert m["container_started"] == U("2026-11-08T10:00:07Z")
    assert m["ready"] == U("2026-11-08T10:01:30Z")
    # deletionTimestamp = lúc nhận lệnh xoá + grace, nên lệnh xoá đến lúc 10:07:00
    assert m["delete_requested"] == U("2026-11-08T10:07:00Z")
    assert m["container_finished"] is None

    # Pod mới: chưa Ready (status False) thì không có mốc, dù condition có lastTransitionTime
    q = pod_json("vllm-b", {"PodScheduled": UP["PodScheduled"], "Ready": ("False", "2026-11-08T10:00:01Z")})
    [s] = collect.snapshot_pods(FakeKube([[q]]), "ns", "vllm")
    m = collect.pod_marks(s)
    assert m["scheduled"] == U("2026-11-08T10:00:01Z")
    assert m["ready"] is None and m["container_started"] is None and m["delete_requested"] is None

    # Container không tên "vllm": lấy container đầu tiên; container đã thoát có finished_at
    gone = {"terminated": {"startedAt": "2026-11-08T10:00:07Z", "finishedAt": "2026-11-08T10:09:40Z"}}
    r = pod_json("vllm-c", UP, state=gone, cname="server")
    [s] = collect.snapshot_pods(FakeKube([[r]]), "ns", "vllm")
    m = collect.pod_marks(s)
    assert m["container_started"] == U("2026-11-08T10:00:07Z")
    assert m["container_finished"] == U("2026-11-08T10:09:40Z")


def test_watcher_keeps_first_ready_and_log_of_scaled_down_pod(tmp_path):
    old = pod_json("vllm-old", UP, state=RUNNING)
    new_pending = pod_json("vllm-new", {"PodScheduled": ("True", "2026-11-08T10:05:01Z")})
    new_ready = pod_json(
        "vllm-new",
        {"PodScheduled": ("True", "2026-11-08T10:05:01Z"), "Ready": ("True", "2026-11-08T10:06:00Z")},
        state={"running": {"startedAt": "2026-11-08T10:05:08Z"}},
    )
    # Scale-down: pod đang tắt chuyển Ready=False với mốc MỚI; mốc Ready lần đầu phải được giữ
    new_term = pod_json(
        "vllm-new",
        {"PodScheduled": ("True", "2026-11-08T10:05:01Z"), "Ready": ("False", "2026-11-08T10:20:00Z")},
        state={"running": {"startedAt": "2026-11-08T10:05:08Z"}},
        deletion="2026-11-08T10:23:00Z",
    )
    kube = FakeKube(
        polls=[
            [old, new_pending],
            [old, new_ready],
            [old, new_term],
            [old, new_term],
            [old, new_term],
            [old],  # pod đã biến mất
            [old],  # lần hỏi cuối trong stop()
        ],
        # Lần thu thứ 3 lỗi vì pod vừa biến mất giữa `get` và `logs`: bản thu trước phải còn nguyên
        logs={"vllm-new": ["dòng khởi động\n", "dòng khởi động\ndòng drain\n", None], "vllm-old": ["cũ\n"]},
    )
    clock = SimpleNamespace(t=1000.0)
    w = collect.PodWatcher(kube, "ns", "vllm", tmp_path / "logs", since=900.0, clock=lambda: clock.t)
    for _ in range(6):
        w.poll()
        clock.t += 5
    tl = w.stop()

    assert tl["polls"] == 7 and tl["errors"] == 0
    assert [e["name"] for e in tl["pods"]] == ["vllm-new", "vllm-old"]  # cùng first_seen: theo tên
    new = next(e for e in tl["pods"] if e["name"] == "vllm-new")
    assert new["marks"]["ready"] == U("2026-11-08T10:06:00Z")  # lần True đầu, không phải 10:20 (False)
    assert new["marks"]["container_started"] == U("2026-11-08T10:05:08Z")
    assert new["marks"]["delete_requested"] == U("2026-11-08T10:20:00Z")
    assert new["last"]["conditions"]["Ready"]["status"] == "False"  # ảnh chụp cuối vẫn đúng như API
    assert (new["first_seen"], new["last_seen"], new["gone_at"]) == (1000, 1020, 1025)
    assert new["restarts_at_first_seen"] == 0 and new["last"]["restarts"] == 0  # không restart: dùng được
    assert new["log"] == {"file": "logs/vllm-new.log", "source": "terminating", "at": 1015}
    assert new["log_error"] is None
    assert (tmp_path / "logs" / "vllm-new.log").read_text(encoding="utf-8") == "dòng khởi động\ndòng drain\n"
    assert not list((tmp_path / "logs").glob("*.tmp"))
    # --since phủ từ `since` tới lúc thu, cộng 60 s dư
    assert "--since=170s" in kube.log_calls[0]

    old_e = next(e for e in tl["pods"] if e["name"] == "vllm-old")
    assert old_e["gone_at"] is None and old_e["log"]["source"] == "end"
    assert (tmp_path / "logs" / "vllm-old.log").read_text(encoding="utf-8") == "cũ\n"


def test_watcher_reports_pod_that_vanished_unlogged_and_kubectl_errors(tmp_path):
    a = pod_json("vllm-a", UP, state=RUNNING)
    b = pod_json("vllm-b", {"PodScheduled": ("True", "2026-11-08T10:05:01Z")})
    kube = FakeKube(
        polls=[[a, b], KubeError("quá 60 s: kubectl get pods"), [a], [a]],
        logs={"vllm-a": [KubeError("quá 120 s: kubectl logs")]},
    )
    clock = SimpleNamespace(t=0.0)
    w = collect.PodWatcher(kube, "ns", "vllm", tmp_path / "logs", since=0.0, clock=lambda: clock.t)
    w.poll()
    clock.t = 5
    w.poll()  # lỗi: không được coi là mọi pod đã biến mất
    assert w.pods["vllm-b"]["gone_at"] is None
    clock.t = 10
    w.poll()  # pod b bị xoá nhanh hơn một chu kỳ (không thấy lúc đang tắt)
    tl = w.stop()

    b_e = next(e for e in tl["pods"] if e["name"] == "vllm-b")
    assert b_e["gone_at"] == 10 and b_e["log"] is None and "biến mất" in b_e["log_error"]
    a_e = next(e for e in tl["pods"] if e["name"] == "vllm-a")
    assert a_e["log"] is None and a_e["log_error"].startswith("quá 120 s")
    assert tl["errors"] == 1 and tl["last_error"].startswith("quá 60 s")
    assert not (tmp_path / "logs" / "vllm-a.log").exists()


def test_watcher_end_mark_follows_latest_snapshot_and_bad_input_is_counted(tmp_path):
    crashed = {"terminated": {"startedAt": "2026-11-08T10:00:07Z", "finishedAt": "2026-11-08T10:03:00Z"}}
    rerun = {"running": {"startedAt": "2026-11-08T10:03:05Z"}}
    final = {"terminated": {"startedAt": "2026-11-08T10:03:05Z", "finishedAt": "2026-11-08T10:09:40Z"}}
    bad = pod_json("vllm-b", UP, state=RUNNING)
    bad["metadata"]["creationTimestamp"] = "không phải giờ"
    kube = FakeKube(
        polls=[
            [pod_json("vllm-a", UP, state=crashed)],
            [pod_json("vllm-a", UP, state=rerun, restarts=1)],
            [pod_json("vllm-a", UP, state=final, restarts=1, deletion="2026-11-08T10:12:00Z")],
            [pod_json("vllm-a", UP, state=final, restarts=1, deletion="2026-11-08T10:12:00Z"), bad],
        ],
        # Log có byte không phải UTF-8: subprocess (text=True) raise UnicodeDecodeError, không phải KubeError
        logs={"vllm-a": [UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")]},
    )
    w = collect.PodWatcher(kube, "ns", "vllm", tmp_path / "logs", since=0.0, clock=lambda: 0.0)
    w.poll()
    assert w.pods["vllm-a"]["marks"]["container_finished"] == U("2026-11-08T10:03:00Z")
    w.poll()  # chạy lại sau crash: mốc kết thúc trở về None, mốc bắt đầu vẫn là lần đầu
    m = w.pods["vllm-a"]["marks"]
    assert m["container_finished"] is None and m["container_started"] == U("2026-11-08T10:00:07Z")
    w.poll()  # thoát thật lúc scale-down
    assert w.pods["vllm-a"]["marks"]["container_finished"] == U("2026-11-08T10:09:40Z")
    a = w.pods["vllm-a"]
    assert a["restarts_at_first_seen"] == 0 and a["last"]["restarts"] == 1  # đã restart: không dùng cho pha
    assert a["log"] is None and a["log_error"].startswith("UnicodeDecodeError")
    tl = w.stop()  # lần hỏi cuối gặp mốc sai định dạng: chỉ đếm lỗi, stop() vẫn trả timeline
    assert tl["errors"] == 1 and tl["last_error"].startswith("ValueError")


def test_watcher_thread_polls_until_stopped(tmp_path):
    kube = FakeKube(polls=[[pod_json("vllm-a", UP, state=RUNNING)]], logs={"vllm-a": ["x\n"]})
    w = collect.PodWatcher(kube, "ns", "vllm", tmp_path / "logs", since=time.time(), interval_s=0.01)
    w.start()
    deadline = time.time() + 5
    while w.polls < 3 and time.time() < deadline:
        time.sleep(0.01)
    tl = w.stop()
    assert tl["polls"] >= 4  # lần đầu trong start(), ≥ 2 lần của luồng nền, lần cuối trong stop()
    assert not w._thread.is_alive()
    assert tl["pods"][0]["log"]["source"] == "end" and tl["started"] <= tl["stopped"]
