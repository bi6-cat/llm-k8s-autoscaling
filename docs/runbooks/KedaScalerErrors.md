<!-- Mục đích: runbook cho cảnh báo KedaScalerErrors (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# KedaScalerErrors

**Mức:** page · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** KEDA gặp ít nhất 3 lỗi trong 2 phút khi chạy PromQL của ScaledObject (`keda_scaler_detail_errors_total` tăng), kéo dài ít nhất 1 phút. Khi lỗi quá 3 lần liên tiếp (lần thứ 4, khoảng 20 s), ScaledObject vào chế độ **fallback**: giữ số replica cố định (`fallback.replicas`, hiện là 4) thay vì scale theo tải.

**Ảnh hưởng.** Autoscaling bị "mù". Người dùng thường chưa bị ảnh hưởng vì fallback giữ nhiều replica, nhưng hệ thống tốn GPU và không phản ứng nếu tải vượt mức fallback.

**Chẩn đoán nhanh (≤ 5 phút).**
1. Prometheus còn sống không?
   ```bash
   kubectl -n monitoring get pods -l app.kubernetes.io/name=prometheus
   ```
2. KEDA thấy lỗi gì?
   ```bash
   kubectl -n llm-serving describe scaledobject vllm-a2 | sed -n '/Conditions:/,$p'   # Ready, Fallback
   kubectl -n keda logs deploy/keda-operator --since=10m | grep -i error | tail -20
   ```
3. PromQL của trigger còn chạy được không? Chạy đúng câu `query` trong ScaledObject trên Grafana (Explore). KEDA báo lỗi khi câu sai cú pháp hoặc trả **nhiều** chuỗi (`returned multiple elements`, thường do thiếu `sum(…)`). Câu trả **rỗng** thì KEDA v2.21.0 không báo lỗi mà coi là 0 (`ignoreNullValues` mặc định `true`), nên không gây cảnh báo này, nhưng HPA đứng ở `minReplicaCount` dù có tải.
4. KEDA có tới được Prometheus không (NetworkPolicy, DNS `prometheus-operated.monitoring.svc`)?

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Prometheus sập hoặc đang khởi động lại | Xem log và `describe` pod Prometheus (thường OOM trên máy nhà 16 GB): tăng limit hoặc giảm retention |
| Mạng KEDA → Prometheus bị chặn | Kiểm tra NetworkPolicy vừa áp (kịch bản VH4 chặn có chủ đích, gỡ khi xong) |
| PromQL sai cú pháp hoặc trả nhiều chuỗi | Vừa sửa `query`? Sửa lại qua PR; tổng hợp bằng `sum(…)` để chỉ còn một chuỗi |
| Sai `serverAddress` | So với Service thật của Prometheus trong namespace `monitoring` |

**Leo thang.** Fallback chạy quá 30 phút mà chưa sửa được thì báo cả nhóm, vì trong lúc đó chi phí GPU cao hơn bình thường.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` (thời gian fallback, nguyên nhân); bổ sung runbook nếu thiếu bước.
