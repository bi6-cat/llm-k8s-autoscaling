"""Thu dữ liệu của một lượt từ cluster, ghi vào thư mục lượt (Môi trường §14.2).

Khái niệm: Prometheus chỉ giữ dữ liệu vài ngày, event của Kubernetes chỉ giữ khoảng 1 giờ, log pod mất khi
    pod bị xoá. Vì vậy runner thu ngay sau mỗi lượt, khi mọi thứ còn đó.
Mục đích: Ghi các file:
    metrics.csv.gz   chuỗi Prometheus trong cửa sổ lượt, dạng dài: ts, name, labels (JSON), value.
                     (Thiết kế ghi metrics.parquet; v1 dùng CSV nén để không kéo thêm pyarrow. Bảng phân
                     tích (TR7) đọc được cả hai.)
    events.jsonl     event Kubernetes trong namespace từ lúc bắt đầu lượt (pod, HPA, ScaledObject)
    alerts.jsonl     cảnh báo firing trong cửa sổ lượt (chuỗi ALERTS), dữ liệu cho VH6
    pods_start.json, pods_end.json   ảnh chụp pod vLLM đầu và cuối lượt (cho kiểm hợp lệ)
    logs/<pod>.log   log vLLM (cho đọc log 8 pha cold start, TR5)
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from experiments.runner.kube import Kube, KubeError, Prometheus

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


def scrape_gaps(prom: Prometheus, ns: str, start: float, end: float) -> dict[str, float | None]:
    """Khoảng trống scrape lớn nhất của từng target vLLM trong cửa sổ lượt (Môi trường §17: ≤ 15 s).

    Dùng range selector `up{…}[Ns]` trong truy vấn tức thời: Prometheus trả MẪU GỐC kèm timestamp thật,
    khác query_range (luôn có giá trị ở mỗi bước nhờ lookback, nên không thấy được khoảng trống).
    """
    window = max(int(end - start), 1)
    res = prom.query(f'up{{namespace="{ns}"}}[{window}s]', at=end)
    return {
        s["metric"].get("pod", s["metric"].get("instance", "?")): max_scrape_gap(s["values"]) for s in res
    }


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


def snapshot_pods(kube: Kube, ns: str, deployment: str) -> list[dict[str, Any]]:
    """Tên, trạng thái, số lần restart, lý do kết thúc gần nhất của từng pod vLLM."""
    items = kube.get_json("pods", "-n", ns, "-l", f"app={deployment}")["items"]
    out = []
    for p in items:
        statuses = p["status"].get("containerStatuses", [])
        out.append(
            {
                "name": p["metadata"]["name"],
                "phase": p["status"].get("phase"),
                "deleting": "deletionTimestamp" in p["metadata"],
                "restarts": sum(c.get("restartCount", 0) for c in statuses),
                "last_terminated": [
                    c.get("lastState", {}).get("terminated", {}).get("reason")
                    for c in statuses
                    if c.get("lastState", {}).get("terminated")
                ],
                "image_ids": [c.get("imageID") for c in statuses],
            }
        )
    return out


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


def write_logs(kube: Kube, ns: str, pods: list[str], since_s: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for pod in pods:
        proc = kube.run(
            "logs", pod, "-n", ns, "--timestamps", f"--since={since_s}s", check=False, timeout_s=120
        )
        (out_dir / f"{pod}.log").write_text(
            proc.stdout if proc.returncode == 0 else proc.stderr, encoding="utf-8"
        )
