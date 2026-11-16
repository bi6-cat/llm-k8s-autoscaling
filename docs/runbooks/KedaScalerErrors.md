<!-- Mục đích: runbook cho cảnh báo KedaScalerErrors (common/observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# KedaScalerErrors

**Mức:** page · **Quy tắc:** [common/observability/alerts/llm.yaml](../../common/observability/alerts/llm.yaml)

**Ý nghĩa.** ScaledObject có condition `Fallback=True` hoặc `Ready` khác `True` liên tục ít nhất 1 phút, và không ở trạng thái `Paused`. kube-state-metrics đọc các condition này thành metric `kube_scaledobject_status_condition` ([common/platform/kube-state-metrics-values.yaml](../../common/platform/kube-state-metrics-values.yaml)).
- `Fallback=True`: KEDA lỗi quá 3 lần liên tiếp khi chạy PromQL của trigger (lần thứ 4, khoảng 20 s), nên giữ số replica cố định (`fallback.replicas`, bằng `maxReplicaCount`) thay vì scale theo tải. Đây là ca thường gặp.
- `Ready=False`: KEDA không đọc hoặc không scale được Deployment đích. `Ready=Unknown`: trigger lỗi khi đang có tải, và chưa tới ngưỡng fallback.

Cảnh báo không dựa vào bộ đếm lỗi của KEDA. Lý do: khi đã fallback, KEDA v2.21.0 không đếm lỗi nữa, nên `keda_scaler_detail_errors_total` đứng yên dù sự cố vẫn còn.

**Ảnh hưởng.** Autoscaling bị "mù". Người dùng thường chưa bị ảnh hưởng vì fallback giữ nhiều replica, nhưng hệ thống tốn GPU và không phản ứng nếu tải vượt mức fallback.

**Chẩn đoán nhanh (≤ 5 phút).**
1. Condition nào đang bật?
   ```bash
   kubectl -n llm-serving describe scaledobject vllm-a2 | sed -n '/Conditions:/,$p'   # Ready, Fallback, Paused
   ```
2. Prometheus còn sống không?
   ```bash
   kubectl -n monitoring get pods -l app.kubernetes.io/name=prometheus
   ```
3. KEDA thấy lỗi gì? Xem log, và mã lỗi của các request KEDA gửi tới Prometheus (Grafana, dashboard "LLM / Autoscaling", panel "KEDA: request lỗi và fallback", hoặc Explore):
   ```bash
   kubectl -n keda logs deploy/keda-operator --since=10m | grep -i error | tail -20
   ```
   ```promql
   sum by (scaled_resource, status_code) (rate(keda_scaler_http_requests_total{status_code!~"2.."}[2m]))
   ```
   `status_code="error"`: không kết nối được (mạng, DNS, quá timeout 1 s). `4xx`: PromQL sai cú pháp. `5xx`: Prometheus quá tải. Không có lỗi HTTP nào mà vẫn fallback: PromQL chạy được nhưng kết quả sai dạng (xem bước 4).
4. PromQL của trigger còn chạy được không? Chạy đúng câu `query` trong ScaledObject trên Grafana (Explore). KEDA báo lỗi khi câu sai cú pháp hoặc trả **nhiều** chuỗi (`returned multiple elements`, thường do thiếu `sum(…)`). Câu trả **rỗng** thì KEDA v2.21.0 không báo lỗi mà coi là 0 (`ignoreNullValues` mặc định `true`), nên không gây cảnh báo này, nhưng HPA đứng ở `minReplicaCount` dù có tải.
5. KEDA có tới được Prometheus không (NetworkPolicy, DNS `prometheus-operated.monitoring.svc`)?

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Prometheus vừa khởi động lại (OOM) | Xem log và `describe` pod Prometheus (thường OOM trên máy nhà 16 GB): tăng limit hoặc giảm retention |
| Mạng KEDA → Prometheus bị chặn | Kiểm tra NetworkPolicy vừa áp (kịch bản VH4 chặn có chủ đích, gỡ khi xong) |
| PromQL sai cú pháp hoặc trả nhiều chuỗi | Vừa sửa `query`? Sửa lại qua PR; tổng hợp bằng `sum(…)` để chỉ còn một chuỗi |
| Sai `serverAddress` | So với Service thật của Prometheus trong namespace `monitoring` |
| `Ready=False`, không có fallback | Xem `Reason`/`Message` của condition `Ready`: thường là Deployment `vllm` bị xoá hoặc đổi tên (`ErrorGettingCurrentReplicas`) |

Khi KEDA hỏi lại được, condition `Fallback` về `False` ngay ở lần hỏi thành công đầu tiên. Cảnh báo hết sau khoảng 30 s (một lần scrape kube-state-metrics và một chu kỳ tính rule; khi hết thì không chờ `for:`). Tin "đã hết" tới Telegram chậm hơn, tới 5 phút (`group_interval` của Alertmanager). Đo trên kind 15/11: `Fallback=False` sau ≤ 12 s, Alertmanager hết cảnh báo sau ≤ 28 s, tin "đã hết" sau 273 s.

**Giới hạn.** Có ba ca cảnh báo này không kêu được, nên đừng coi "không có cảnh báo" là "KEDA ổn":
- **Thiếu metric.** Môi trường chưa nạp `kube-state-metrics-values.yaml`, hoặc kube-state-metrics mất quyền đọc ScaledObject: rule không có dữ liệu nên im lặng. Sau mỗi lần dựng môi trường, chạy PromQL `kube_scaledobject_status_condition{namespace="llm-serving"}`: mỗi ScaledObject phải có 5 chuỗi (Ready, Active, Fallback, Paused, HPAActive).
- **Prometheus sập hẳn.** Prometheus vừa là nơi KEDA hỏi vừa là nơi tính rule, nên không còn ai tính cảnh báo. Prometheus khởi động lại thì rule chạy lại và kêu nếu KEDA vẫn đang fallback.
- **keda-operator sập.** Không còn ai cập nhật condition, nên `Ready` và `Fallback` giữ giá trị cuối (thường là bình thường). Kiểm bằng `kubectl -n keda get pods`.

**Leo thang.** Fallback chạy quá 30 phút mà chưa sửa được thì báo cả nhóm, vì trong lúc đó chi phí GPU cao hơn bình thường.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` (thời gian fallback, nguyên nhân); bổ sung runbook nếu thiếu bước.
