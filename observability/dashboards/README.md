<!-- Mục đích: cách 3 dashboard Grafana (F5) được nạp, xem, sửa và kiểm. Tham khảo: Kiến trúc §17.3, Vận hành §4, §9 -->
# Dashboard Grafana

Ba dashboard của yêu cầu F5 ([Thông số §3](../../docs/chi-tiet/00-thong-so.md#3-yêu-cầu-chức-năng)), panel theo [Kiến trúc §17.3](../../docs/chi-tiet/03-kien-truc-autoscaling.md#173-dashboard):

| File | uid | Tiêu đề | Trả lời câu hỏi |
|---|---|---|---|
| `serving-gpu.json` | `llm-serving-gpu` | LLM / Serving và GPU | vLLM phục vụ thế nào (RPS, TTFT, ITL, hàng đợi, KV-cache theo từng pod), GPU đang làm gì (util, VRAM, công suất, nhiệt độ, xung nhịp) |
| `autoscaling.json` | `llm-autoscaling` | LLM / Autoscaling | HPA muốn bao nhiêu replica và đang có bao nhiêu; tín hiệu so với target × replica; pod đang ở trạng thái nào (chờ GPU, kéo image, nạp model, Ready, đang tắt); cold start từng pod; KEDA đọc được gì |
| `slo-cost.json` | `llm-slo-cost` | LLM / SLO và chi phí | TTFT, TPOT, 5xx so với SLO; burn rate; ngân sách lỗi còn lại; cảnh báo đã kêu; GPU-giờ, chi phí, chi phí trên 1 triệu token, thời gian ở mức max replica |

Hai dashboard đầu dùng khi chẩn đoán theo runbook ([Vận hành §4.2](../../docs/chi-tiet/04-van-hanh.md#42-ví-dụ-llmsloburnfast)). Dashboard thứ ba dùng để xem lại một lượt đánh giá: chọn khoảng thời gian bằng đúng lượt đó, các ô "trong khoảng đang xem" sẽ tính cho lượt ấy.

Mỗi panel có phần mô tả (biểu tượng ⓘ cạnh tiêu đề) giải thích metric, cách đọc và ngưỡng đang vẽ. JSON không có chỗ cho comment, nên phần giải thích nằm ở đó.

## Nạp vào Grafana

`observability/kustomization.yaml` biến mỗi file JSON thành một ConfigMap có label `grafana_dashboard: "1"` trong namespace `monitoring`. Sidecar của Grafana (values của kube-prometheus-stack) thấy ConfigMap đó và nạp dashboard, không cần import tay:

```bash
kubectl --context kind-llm-sim apply -k observability     # simulator; ở nhà thì Argo CD áp (khi có App)
kubectl --context kind-llm-sim -n monitoring port-forward svc/kps-grafana 3000:80
# http://localhost:3000, đăng nhập bằng Secret grafana-admin; tìm theo tag llm-k8s-autoscaling
```

Dashboard nạp từ ConfigMap là *provisioned*: sửa trên giao diện thì không lưu đè được vào file, và lần nạp lại sẽ xoá thay đổi. Muốn giữ thay đổi thì đưa nó về JSON trong Git.

## Sửa một dashboard

1. Sửa trên Grafana, rồi **Export → Export as JSON**, *không* bật "Export for sharing externally" (bật thì Grafana thay datasource bằng `${DS_…}` và thêm `__inputs`).
2. Dán vào file, **xoá trường `id`** ở gốc, giữ nguyên `uid` (CONTRIBUTING §4). Muốn diff gọn thì chỉ chép phần panel vừa sửa.
3. `make dashboards-check` (Windows: `make dashboards-check SHELL=bash`), rồi áp lại như trên.

Quy ước chung của cả ba dashboard:

- **Datasource là biến `${datasource}`**, không ghi uid cố định, để một file chạy được ở home, cloud và sim. `make dashboards-check` báo lỗi nếu có panel trỏ thẳng tới một datasource.
- **Tag `llm-k8s-autoscaling`**, tiêu đề bắt đầu bằng `LLM /`. Thanh liên kết ở đầu mỗi dashboard mở hai dashboard còn lại và giữ nguyên khoảng thời gian đang xem.
- Ngưỡng vẽ trên panel (TTFT 2,5 s, TPOT 100 ms, 83 °C, target 70 % của A1) lấy từ `docs/chi-tiet/00-thong-so.md`. Đổi ngưỡng ở đó thì sửa cả ở đây.
- Truy vấn dùng tên metric của các bản đã ghim: vLLM v0.31.0 (đối chiếu `vllm/v1/metrics/loggers.py`), nvidia_gpu_exporter 1.15.1, KEDA 2.21.0, kube-state-metrics của chart kube-prometheus-stack 92.1.1.

## Annotation

Mỗi dashboard có ba lớp annotation (bật, tắt ở đầu trang):

| Lớp | Nguồn | Hiện gì |
|---|---|---|
| Annotations & Alerts | Grafana | Annotation người dùng tự thêm |
| Pha kịch bản (runner) | Grafana, lọc tag `llm-run` | Ranh giới các pha của kịch bản tải (`steady`, `spike`, `drop`…) |
| Cảnh báo LLM đang bật | Prometheus, chuỗi `ALERTS` | Khoảng thời gian mỗi cảnh báo `LLM…`, `Keda…` ở trạng thái firing |

Runner gửi annotation pha qua HTTP API của Grafana, mỗi pha một vùng (`time` và `timeEnd` tính bằng mili giây):

```json
POST /api/annotations
{"time": 1762500000000, "timeEnd": 1762500600000, "tags": ["llm-run", "<run_id>", "<pha>"], "text": "<run_id>: <pha>"}
```

Tag `llm-run` là điểm hẹn giữa runner và dashboard. Đổi tag thì sửa cả hai phía.

## Thiếu dữ liệu ở môi trường nào

| Panel | Cần | sim (kind) | home | cloud |
|---|---|---|---|---|
| Hàng GPU (Serving và GPU) | nvidia_gpu_exporter | Trống (không có GPU) | Có | Có |
| Preemption | `vllm:num_preemptions_total` | Trống (simulator không xuất) | Có | Có |
| Hàng KEDA (Autoscaling) | Prometheus thu metric của KEDA operator | Trống | Trống | Trống |
| Không lỗi 5xx, ngân sách lỗi 5xx | Traefik và PodMonitor của nó | Trống (kind không có Traefik) | Có | Có |

"No data" ở các ô trên là đúng. Hàng KEDA sẽ có số khi thêm việc thu metric của KEDA operator (chưa làm). Ở chỗ khác mà thấy "No data" thì kiểm tra target trong Prometheus (`/targets`) và tên metric.

**Lưu ý khi đọc trên simulator.** TTFT mà simulator báo **không gồm thời gian chờ hàng đợi**: lượt tải 25 request đồng thời ngày 07/11 cho TTFT p95 0,24 s trong khi thời gian chờ hàng đợi p95 là 4,7 s. vLLM thật thì tính TTFT từ lúc request tới, nên gồm cả thời gian chờ. Vì vậy trên kind, quá tải không làm các panel TTFT, burn rate hay cảnh báo `LLMSLOBurnFast` thay đổi. Hãy xem panel thời gian chờ hàng đợi. Simulator đặt lý do kết thúc vào nhãn `finish_reason`; overlay `sim` đổi tên nhãn này thành `finished_reason` lúc scrape (`serving/overlays/sim/patch-podmonitor-sim.yaml`) cho giống vLLM.
