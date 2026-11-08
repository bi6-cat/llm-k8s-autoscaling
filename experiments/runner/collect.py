"""Thu dữ liệu của một lượt từ cluster, ghi vào thư mục lượt (Môi trường §14.2).

Khái niệm: Prometheus chỉ giữ dữ liệu vài ngày, event của Kubernetes chỉ giữ khoảng 1 giờ, log pod mất khi
    pod bị xoá. Vì vậy runner thu ngay sau mỗi lượt, khi mọi thứ còn đó.
Mục đích: Ghi các file:
    metrics.csv.gz   chuỗi Prometheus trong cửa sổ lượt, dạng dài: ts, name, labels (JSON), value.
                     (Thiết kế ghi metrics.parquet; v1 dùng CSV nén để không kéo thêm pyarrow. Bảng phân
                     tích (TR7) đọc được cả hai.)
    events.jsonl     event Kubernetes trong namespace từ lúc bắt đầu lượt (pod, HPA, ScaledObject)
    alerts.jsonl     cảnh báo firing trong cửa sổ lượt (chuỗi ALERTS), dữ liệu cho VH6
    pods_start.json, pods_end.json   ảnh chụp pod vLLM sau reset và cuối pha chính (cho kiểm hợp lệ)
    pods_timeline.json   mọi pod vLLM từng xuất hiện từ reset tới hết cooldown, với mốc thời gian đầu
                     tiên của từng loại (PodWatcher): pha cold start 1, 2, 4, 8; GPU-giờ; N2a
    logs/<pod>.log   log vLLM có mốc kubelet (--timestamps), đọc bằng vllm_log.parse_vllm_log (pha cold
                     start, TR5). Có cả pod đã bị scale-down giữa lượt: PodWatcher thu log lúc pod đang tắt.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from experiments.runner.kube import Kube, KubeError, Prometheus

# Chu kỳ hỏi pod của PodWatcher. preStop 20 s (Thông số §9.2), nên pod đang tắt được thấy nhiều lần.
POD_POLL_S = 5.0

STEP_S = 5  # = chu kỳ scrape 5 s của vLLM, GPU, Traefik


def metric_queries(ns: str, deployment: str) -> dict[str, str]:
    """Các chuỗi cần cho bảng phân tích. Tên ngắn → biểu thức PromQL. Thiếu metric (ví dụ GPU trên kind)
    thì chuỗi đó rỗng, không lỗi."""
    sel = f'namespace="{ns}"'
    return {
        # Số replica: theo Deployment (spec), số đang chạy và số sẵn sàng phục vụ
        "replicas_spec": f'kube_deployment_spec_replicas{{{sel},deployment="{deployment}"}}',
        "replicas": f'kube_deployment_status_replicas{{{sel},deployment="{deployment}"}}',
        "replicas_ready": f'kube_deployment_status_replicas_ready{{{sel},deployment="{deployment}"}}',
        # Quyết định của HPA (KEDA tạo HPA tên keda-hpa-<ScaledObject>)
        "hpa_desired": f"kube_horizontalpodautoscaler_status_desired_replicas{{{sel}}}",
        # Tín hiệu của A2 và A3, theo từng pod
        "vllm_running": f"vllm:num_requests_running{{{sel}}}",
        "vllm_waiting": f"vllm:num_requests_waiting{{{sel}}}",
        "vllm_kv_cache": f"vllm:kv_cache_usage_perc{{{sel}}}",
        # Tín hiệu của A1 (GPU util, exporter nvidia-smi) và bộ nhớ GPU
        "gpu_util": "nvidia_smi_utilization_gpu_ratio",
        "gpu_mem_used": "nvidia_smi_memory_used_bytes",
        # CPU và RAM của từng container trong namespace (vLLM và máy tạo tải)
        "cpu_cores": "sum by (pod, container) "
        f'(rate(container_cpu_usage_seconds_total{{{sel},container!=""}}[1m]))',
        "mem_bytes": f'sum by (pod, container) (container_memory_working_set_bytes{{{sel},container!=""}})',
        # Tổng request thành công theo pod: thấy được tải có chia đều giữa các replica không
        "vllm_success_total": f"sum by (pod) (vllm:request_success_total{{{sel}}})",
    }


def write_metrics(prom: Prometheus, queries: dict[str, str], start: float, end: float, path: Path) -> int:
    """Ghi metrics.csv.gz. Trả số dòng đã ghi."""
    n = 0
    with gzip.open(path, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "name", "labels", "value"])
        for name, expr in queries.items():
            try:
                series = prom.query_range(expr, start, end, STEP_S)
            except KubeError as e:
                w.writerow([f"{start:.3f}", f"_error_{name}", "{}", str(e)[:200]])
                continue
            for s in series:
                labels = json.dumps(s["metric"], sort_keys=True, ensure_ascii=False)
                for ts, v in s["values"]:
                    w.writerow([ts, name, labels, v])
                    n += 1
    return n


def max_scrape_gap(samples: list[list[Any]], window: tuple[float, float] | None = None) -> float | None:
    """Khoảng trống lớn nhất (giây) giữa hai mẫu liên tiếp. samples = [[ts, "v"], …]. Hàm thuần.

    Có `window` = (start, end): chỉ xét mẫu trong [start, end] và tính cả hai mép (start → mẫu đầu, mẫu
    cuối → end). Nhờ vậy chuỗi tắt giữa chừng rồi không quay lại cũng lộ ra, và không có mẫu nào thì kết
    quả là cả cửa sổ (end − start). Không có mép thì hai trường hợp đó không có khoảng trống nào giữa hai
    mẫu.
    """
    ts = sorted(float(t) for t, _ in samples)
    if window is not None:
        start, end = window
        ts = [start, *(t for t in ts if start <= t <= end), end]
    if len(ts) < 2:
        return None
    return max(b - a for a, b in zip(ts, ts[1:], strict=False))


def scrape_gaps(
    prom: Prometheus,
    ns: str,
    start: float,
    end: float,
    *,
    at_start: frozenset[str] = frozenset(),
    at_end: frozenset[str] = frozenset(),
) -> dict[str, float | None]:
    """Khoảng trống scrape lớn nhất của từng pod vLLM trong cửa sổ lượt (Môi trường §17: ≤ 15 s).

    Dùng range selector `up{…}[Ns]` trong truy vấn tức thời: Prometheus trả MẪU GỐC kèm timestamp thật,
    khác query_range (luôn có giá trị ở mỗi bước nhờ lookback, nên không thấy được khoảng trống).

    Chỉ tính mẫu `up == 1`: mỗi lần scrape THẤT BẠI Prometheus vẫn ghi một mẫu `up = 0`, nên đếm mọi mẫu
    thì scrape lỗi liên tục cũng không để lại khoảng trống nào. Mép cửa sổ tính theo pod:
    - `at_start`: pod đã có từ đầu lượt (pods_start). Tính từ `start` tới lần scrape thành công đầu tiên.
    - `at_end`: pod còn sống, không đang bị xoá, ở cuối lượt (pods_end). Tính từ lần thành công cuối
      tới `end`.
    Pod mới do scale-up không có mép đầu: mẫu `up = 0` lúc cold start (chưa mở /metrics) không bị tính.
    Pod đang tắt không có mép cuối, vì lúc drain /metrics có thể đã ngừng trả lời. Pod sống suốt lượt mà
    không có lần thành công nào, hoặc không có chuỗi `up` nào, cho ra cả cửa sổ (end − start).
    Pod có từ đầu lượt mà bị xoá giữa lượt thì checks.py đã loại lượt ở tiêu chí 3.
    """
    window = max(math.ceil(end - start), 1)
    res = prom.query(f'up{{namespace="{ns}"}}[{window}s]', at=end)
    gaps: dict[str, float | None] = {}
    for s in res:
        pod = s["metric"].get("pod", s["metric"].get("instance", "?"))
        ok = [float(t) for t, v in s["values"] if float(v) == 1 and start <= float(t) <= end]
        edges = ([start] if pod in at_start else []) + ([end] if pod in at_end else [])
        gaps[pod] = max_scrape_gap([[t, "1"] for t in ok + edges])
    for pod in (at_start & at_end) - gaps.keys():  # sống suốt lượt mà Prometheus không có target nào
        gaps[pod] = end - start
    return gaps


def signal_gap(prom: Prometheus, selector: str, start: float, end: float) -> dict[str, Any]:
    """Tín hiệu scale có mẫu suốt [start, end] không (Môi trường §17: mất mẫu ≤ 15 s).

    Khác scrape_gaps ở hai điểm:
    - Gộp mẫu của MỌI chuỗi khớp selector (A1: mỗi GPU một chuỗi; A2: mỗi pod vLLM một chuỗi) rồi mới tìm
      khoảng trống, vì pod mới do scale-up có chuỗi bắt đầu giữa lượt, đó không phải mất mẫu. Vì gộp nên
      chỉ bắt được khi CẢ tín hiệu biến mất (exporter chết, chưa được scrape, sai label). Đó đúng là ca KEDA
      đọc rỗng thành 0 (Kiến trúc §13.4). Mất một chuỗi trong nhiều chuỗi thì không bắt được: với A1 khó
      xảy ra, vì exporter đọc mọi GPU trong một lần gọi nvidia-smi.
    - Tính cả hai mép cửa sổ (max_scrape_gap có `window`), vì exporter chết rồi không quay lại thì giữa
      các mẫu còn lại không có khoảng trống nào. Mép lấy theo đồng hồ của runner, nên runner và Prometheus
      lệch giờ quá khoảng 10 s (15 s trừ chu kỳ scrape 5 s) thì lượt bị loại nhầm. Trên VM thuê và kind,
      runner chạy cùng máy với Prometheus; ở nhà thì không, nên session.check_signals đo độ lệch đầu phiên.
    Truy vấn lỗi (Prometheus tạm mất, kubectl quá giờ) thì trả `error` thay vì raise, để lượt đã chạy xong
    vẫn ghi đủ checks.json và metadata.json; checks.py coi lượt đó là invalid vì không kiểm được.
    """
    rng = max(math.ceil(end - start), 1)  # làm tròn lên để range selector phủ hết [start, end]
    out: dict[str, Any] = {"selector": selector}
    try:
        res = prom.query(f"{selector}[{rng}s]", at=end)
    except KubeError as e:
        return {**out, "series": None, "samples": None, "max_gap_s": None, "error": str(e)[:300]}
    # Chỉ đếm mẫu trong pha chính: range làm tròn lên có thể lấy dư một mẫu ngay trước start
    inside = [v for s in res for v in s["values"] if start <= float(v[0]) <= end]
    return {
        **out,
        "series": len(res),
        "samples": len(inside),
        "max_gap_s": max_scrape_gap(inside, (start, end)),
    }


def _container_status(c: dict[str, Any]) -> dict[str, Any]:
    """Một phần tử của `containerStatuses` → trạng thái hiện tại của container đó."""
    state = c.get("state") or {}
    kind = next(iter(state), None)  # API chỉ đặt đúng một khoá: "waiting" | "running" | "terminated"
    st = state.get(kind) or {}
    return {
        "name": c.get("name"),
        "state": kind,
        # waiting: ContainerCreating, ErrImagePull, CrashLoopBackOff…; terminated: Completed, OOMKilled…
        "reason": st.get("reason"),
        "started_at": st.get("startedAt"),  # có khi running hoặc terminated
        "finished_at": st.get("finishedAt"),  # chỉ có khi terminated
        "ready": c.get("ready"),
        "restarts": c.get("restartCount", 0),
    }


def snapshot_pods(kube: Kube, ns: str, deployment: str) -> list[dict[str, Any]]:
    """Ảnh chụp từng pod vLLM: trạng thái để kiểm hợp lệ (restart, OOMKilled, đang xoá) và mốc thời gian
    cho pha cold start, GPU-giờ, N2a (Môi trường §12, §15).

    Mốc giữ nguyên chuỗi của API (RFC 3339, chỉ tới GIÂY); pod_marks đổi sang giây UNIX.
    - created: metadata.creationTimestamp, lúc ReplicaSet tạo pod = đầu pha 1.
    - conditions: {loại: {status, time, reason}}, `time` = lastTransitionTime. API chỉ giữ lần đổi GẦN
      NHẤT: Ready có thể đã lật True → False (pod đang tắt, probe trượt lúc quá tải) → True. Muốn lần
      True đầu tiên thì dùng PodWatcher.
    - deletion_timestamp: API đặt bằng lúc nhận lệnh xoá + deletion_grace_s (hạn chót trước khi kubelet
      gửi SIGKILL), không phải lúc nhận lệnh.
    """
    items = kube.get_json("pods", "-n", ns, "-l", f"app={deployment}")["items"]
    out = []
    for p in items:
        meta, spec, status = p["metadata"], p.get("spec", {}), p["status"]
        statuses = status.get("containerStatuses", [])
        out.append(
            {
                "name": meta["name"],
                "phase": status.get("phase"),
                "deleting": "deletionTimestamp" in meta,
                "restarts": sum(c.get("restartCount", 0) for c in statuses),
                "last_terminated": [
                    c.get("lastState", {}).get("terminated", {}).get("reason")
                    for c in statuses
                    if c.get("lastState", {}).get("terminated")
                ],
                "image_ids": [c.get("imageID") for c in statuses],
                "node": spec.get("nodeName"),  # None khi chưa xếp lịch (Pending vì hết GPU)
                "created": meta.get("creationTimestamp"),
                "deletion_timestamp": meta.get("deletionTimestamp"),
                "deletion_grace_s": meta.get("deletionGracePeriodSeconds"),
                "conditions": {
                    c["type"]: {
                        "status": c.get("status"),
                        "time": c.get("lastTransitionTime"),
                        "reason": c.get("reason"),
                    }
                    for c in status.get("conditions", [])
                },
                "containers": [_container_status(c) for c in statuses],
                "init_containers": [_container_status(c) for c in status.get("initContainerStatuses", [])],
            }
        )
    return out


def _unix(stamp: str | None) -> float | None:
    """Chuỗi RFC 3339 của API ("2026-11-08T09:43:01Z") → giây UNIX."""
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() if stamp else None


def pod_marks(pod: dict[str, Any], container: str = "vllm") -> dict[str, float | None]:
    """Mốc phía Kubernetes (giây UNIX) của một ảnh chụp snapshot_pods. Hàm thuần. None = chưa xảy ra.

    Gắn với 8 pha của Kiến trúc §7.2:
        created            ReplicaSet tạo pod: đầu pha 1
        scheduled          condition PodScheduled: hết pha 1 (từ đây pod giữ GPU, Kiến trúc §7.4)
        sandbox_ready      condition PodReadyToStartContainers (K8s ≥ 1.29): sandbox và mạng xong, trong pha 2
        initialized        condition Initialized: init container (nếu có) đã chạy xong
        container_started  container vLLM bắt đầu chạy: hết pha 3 (kéo image), đầu pha 4;
                           truyền vào vllm_log.phases(container_started=…)
        ready              condition Ready: hết pha 8; truyền vào vllm_log.phases(pod_ready=…)
        delete_requested   lúc nhận lệnh xoá (scale-down): đầu pha tắt (preStop rồi drain)
        container_finished container vLLM đã thoát (chỉ thấy nếu kịp chụp trước khi pod biến mất)
    Pha 3 lấy từ event Pulling/Pulled trong events.jsonl. Condition chỉ tính khi status "True". Container
    vLLM là container tên `container`; không có tên đó thì lấy container đầu tiên.
    """
    conds = pod.get("conditions", {})

    def cond(kind: str) -> float | None:
        c = conds.get(kind)
        return _unix(c["time"]) if c and c.get("status") == "True" else None

    cs = pod.get("containers", [])
    main = next((c for c in cs if c["name"] == container), cs[0] if cs else {})
    deletion, grace = _unix(pod.get("deletion_timestamp")), pod.get("deletion_grace_s")
    return {
        "created": _unix(pod.get("created")),
        "scheduled": cond("PodScheduled"),
        "sandbox_ready": cond("PodReadyToStartContainers"),
        "initialized": cond("Initialized"),
        "container_started": _unix(main.get("started_at")),
        "ready": cond("Ready"),
        "delete_requested": None if deletion is None else deletion - (grace or 0),
        "container_finished": _unix(main.get("finished_at")),
    }


def fetch_log(kube: Kube, ns: str, pod: str, since_s: int, path: Path) -> str | None:
    """Ghi log của một pod (kèm mốc kubelet) vào `path`. Trả None nếu được, mô tả lỗi nếu không.

    Lỗi thì KHÔNG đụng tới file: bản thu lần trước (pod đang tắt) vẫn còn nguyên. Ghi qua file tạm rồi đổi
    tên, để runner bị ngắt giữa lúc ghi không để lại log cụt.
    """
    try:
        proc = kube.run(
            "logs", pod, "-n", ns, "--timestamps", f"--since={since_s}s", check=False, timeout_s=120
        )
        if proc.returncode != 0:
            return (proc.stderr.strip() or f"kubectl logs → {proc.returncode}")[:300]
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(proc.stdout, encoding="utf-8")
        tmp.replace(path)
    # KubeError: quá thời gian; UnicodeError: log có byte không phải UTF-8; OSError: đĩa đầy, không ghi được
    except (KubeError, UnicodeError, OSError) as e:
        return _describe(e)
    return None


def _describe(e: Exception) -> str:
    """Mô tả lỗi ngắn gọn để ghi vào JSON. KubeError đã có sẵn lệnh và lý do nên không thêm tên lớp."""
    return (str(e) if isinstance(e, KubeError) else f"{type(e).__name__}: {e}")[:300]


# Mốc kết thúc lấy theo ảnh chụp MỚI NHẤT (None khi container đang chạy lại sau một lần crash), các mốc
# khác giữ giá trị đầu tiên. Nhờ vậy một lần crash rồi restart không bị ghi nhầm thành lúc pod tắt.
_LATEST_MARKS = frozenset({"container_finished"})


class PodWatcher:
    """Theo dõi pod vLLM suốt lượt bằng một luồng nền (thread), hỏi API mỗi `interval_s` giây.

    Vì sao cần: pods_start và pods_end chỉ chụp hai thời điểm. Pod do scale-up tạo ra, đúng loại pod có
    cold start cần đo, thường bị scale-down trong cooldown hoặc ngay trong pha chính (KB2, KB3). Pod bị
    xoá thì mất cả log lẫn mốc thời gian. Watcher:
    - ghi mọi pod từng xuất hiện kèm mốc ĐẦU TIÊN của từng loại trong pod_marks (Ready lần đầu, container
      chạy lần đầu…), vì API chỉ giữ lần đổi gần nhất; riêng `container_finished` lấy theo ảnh chụp mới
      nhất (_LATEST_MARKS). Cùng với đó là `last_seen` (lần cuối thấy pod) và `gone_at`
      (lần đầu thấy pod đã biến mất). Pod giữ GPU từ `scheduled` tới lúc biến mất, trong khoảng
      (last_seen, gone_at]: dùng cho GPU-giờ chính xác (Môi trường §15);
    - thu log của pod đang tắt ở MỖI lần hỏi, tới khi pod biến mất. Bản sau ghi đè bản trước nên còn cả
      log lúc drain (thoát êm, Kiến trúc §8). Pod đang tắt sống ít nhất 20 s (preStop), nên với chu kỳ
      5 s nó được thấy nhiều lần.
    Hỏi định kỳ thay vì `kubectl get --watch`: watch phải tự nối lại khi đứt và tự ghép từng bản cập nhật.
    Mốc của condition đã có lastTransitionTime nên hỏi định kỳ vẫn đúng tới giây (trừ khi condition lật
    hai lần trong một chu kỳ); chỉ thời điểm pod biến mất có sai số tới một chu kỳ. Chu kỳ thực = 5 s cộng
    thời gian của chính lần hỏi, gồm tải lại trọn log của pod đang tắt (log vLLM một lượt ước khoảng 1 MB
    mỗi pod, chủ yếu là access log của uvicorn: chưa đo trên vLLM thật).
    `first_seen`, `last_seen`, `gone_at` theo đồng hồ của runner; mốc trong `marks` theo đồng hồ API
    server. Trên kind và VM thuê, runner chạy cùng máy với cluster.
    Lỗi giữa chừng (kubectl lỗi hay quá giờ, JSON hỏng) chỉ được đếm vào `errors`, không dừng lượt.
    Giới hạn:
    - Pod có container restart trong lượt (`last.restarts` > `restarts_at_first_seen`): `kubectl logs`
      chỉ trả log của lần chạy hiện tại, còn `marks.container_started` là lần chạy đầu. Không dùng pod đó
      để tính pha cold start.
    - Cooldown xong khi Deployment còn 1 replica sẵn sàng, lúc đó pod cuối bị scale-down có thể vẫn đang
      tắt (kind 08/11: lệnh xoá 4 s trước khi dừng). Pod đó có `last.deleting` = true, `gone_at` = None,
      và log chỉ tới lúc dừng: đủ phần khởi động, thiếu phần drain cuối.
    - Kubelet xoay vòng log container khi quá 10 MiB (mặc định) và `kubectl logs` chỉ đọc file hiện tại,
      nên pod ghi rất nhiều log có thể mất phần khởi động. Lượt 25 phút còn xa ngưỡng này.
    """

    def __init__(
        self,
        kube: Kube,
        ns: str,
        deployment: str,
        log_dir: Path,
        *,
        since: float,
        interval_s: float = POD_POLL_S,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.kube, self.ns, self.deployment, self.log_dir = kube, ns, deployment, log_dir
        self.since, self.interval_s, self.clock = since, interval_s, clock  # since: mốc --since của log
        self.pods: dict[str, dict[str, Any]] = {}
        self.polls, self.errors, self.last_error = 0, 0, None
        self.started: float | None = None
        self._lock = threading.Lock()  # poll() của luồng nền và của stop() không chạy chồng nhau
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _log(self, name: str, source: str) -> None:
        """Thu log của một pod. `log_error` chỉ ghi khi CHƯA có bản nào: lần thu cuối của pod đang tắt hay
        trượt vì pod vừa biến mất giữa `get` và `logs`, khi đó bản thu trước vẫn là log đầy đủ."""
        ent, now = self.pods[name], self.clock()
        path = self.log_dir / f"{name}.log"
        err = fetch_log(self.kube, self.ns, name, int(now - self.since) + 60, path)
        if err is None:
            ent["log"] = {"file": f"{self.log_dir.name}/{path.name}", "source": source, "at": now}
            ent["log_error"] = None
        elif ent["log"] is None:
            ent["log_error"] = err

    def _record(self, e: Exception) -> None:
        """Đếm một lỗi. Chỉ gọi khi đang giữ lock, để luồng nền và stop() không đếm sót của nhau."""
        self.errors, self.last_error = self.errors + 1, _describe(e)

    def poll(self) -> None:
        """Một lần hỏi: cập nhật mọi pod đang thấy, đánh dấu pod đã biến mất, thu log pod đang tắt.
        Không raise: lỗi bất kỳ chỉ được đếm, vì luồng nền chết im lặng thì mất dữ liệu cả lượt."""
        with self._lock:
            self.polls += 1
            try:
                self._poll_locked(self.clock())
            except Exception as e:  # kubectl lỗi hay quá giờ, JSON hỏng, mốc thời gian sai định dạng…
                self._record(e)

    def _poll_locked(self, now: float) -> None:
        snap = snapshot_pods(self.kube, self.ns, self.deployment)  # lỗi ở đây: chưa đánh dấu pod nào mất
        names = set()
        for p in snap:
            names.add(p["name"])
            ent = self.pods.setdefault(
                p["name"],
                {
                    "name": p["name"],
                    "first_seen": now,
                    "restarts_at_first_seen": p["restarts"],
                    "marks": {},
                    "log": None,
                    "log_error": None,
                },
            )
            ent.update(last_seen=now, gone_at=None, last=p)
            for k, v in pod_marks(p).items():
                old = ent["marks"].get(k)
                ent["marks"][k] = v if k in _LATEST_MARKS or old is None else old
            if p["deleting"]:
                self._log(p["name"], "terminating")
        for name, ent in self.pods.items():
            if name not in names and ent["gone_at"] is None:
                ent["gone_at"] = now
                if ent["log"] is None and ent["log_error"] is None:
                    ent["log_error"] = "pod biến mất trước khi kịp thu log"

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_s):
            self.poll()

    def start(self) -> None:
        """Hỏi một lần ngay (bắt các pod có từ đầu), rồi chạy luồng nền."""
        self.started = self.clock()
        self.poll()
        self._thread = threading.Thread(target=self._loop, name="pod-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        """Dừng luồng nền, hỏi lần cuối, thu log mọi pod còn sống. Trả nội dung pods_timeline.json.

        Không raise, để lượt lỗi giữa chừng vẫn ghi được pods_timeline.json. Luồng nền chưa dừng sau
        `join` (một lần hỏi treo lâu) thì poll() dưới đây chờ nó qua lock; sau đó nó không hỏi thêm lần nào
        vì cờ dừng đã bật.
        """
        self._stop.set()
        hung = False
        if self._thread is not None:
            self._thread.join(timeout=600)  # một lần hỏi có thể chờ kubectl logs tới 120 s mỗi pod
            hung = self._thread.is_alive()
        self.poll()
        with self._lock:
            if hung:
                self._record(RuntimeError("luồng nền chưa dừng sau 600 s"))
            try:
                for name, ent in self.pods.items():
                    if ent["gone_at"] is None and not ent["last"]["deleting"]:
                        self._log(name, "end")  # pod đang tắt đã được thu ở poll() ngay trên
            except Exception as e:
                self._record(e)
            return self.timeline()

    def timeline(self) -> dict[str, Any]:
        return {
            "interval_s": self.interval_s,
            "started": self.started,
            "stopped": self.clock(),
            "polls": self.polls,
            "errors": self.errors,
            "last_error": self.last_error,
            "pods": sorted(self.pods.values(), key=lambda e: (e["first_seen"], e["name"])),
        }


def write_events(kube: Kube, ns: str, since: float, path: Path) -> int:
    """Event trong namespace có mốc thời gian ≥ since. Trả số event đã ghi."""
    items = kube.get_json("events", "-n", ns)["items"]
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for e in items:
            stamp = e.get("lastTimestamp") or e.get("eventTime") or e["metadata"].get("creationTimestamp")
            if not stamp:
                continue
            t = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
            if t < since:
                continue
            fh.write(
                json.dumps(
                    {
                        "time": stamp,
                        "type": e.get("type"),
                        "reason": e.get("reason"),
                        "object": f"{e['involvedObject'].get('kind')}/{e['involvedObject'].get('name')}",
                        "message": e.get("message"),
                        "count": e.get("count"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            n += 1
    return n


def write_alerts(prom: Prometheus, start: float, end: float, path: Path) -> int:
    series = prom.query_range('ALERTS{alertstate="firing"}', start, end, STEP_S)
    with path.open("w", encoding="utf-8") as fh:
        for s in series:
            fh.write(
                json.dumps(
                    {"labels": s["metric"], "first": s["values"][0][0], "last": s["values"][-1][0]},
                    ensure_ascii=False,
                )
                + "\n"
            )
    return len(series)
