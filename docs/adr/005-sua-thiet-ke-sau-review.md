# ADR-005: Sửa thiết kế kỹ thuật sau review 08/10/2026

- **Trạng thái:** Đã chấp nhận ngày 08/10/2026. Các điểm đánh dấu *cần kiểm chứng* phải được thử trên phiên bản vLLM, KEDA và Traefik đã ghim.
- **Người quyết định:** Nhóm, theo báo cáo review nội bộ ngày 08/10/2026, §12 (không lưu trong repo; mã ISSUE trong ngoặc ở cột "Vấn đề" là mã của báo cáo đó).
- **Liên quan:** [ADR-004](004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md), [Kiến trúc và autoscaling](../chi-tiet/03-kien-truc-autoscaling.md), [Vận hành](../chi-tiet/04-van-hanh.md), [Thông số và chỉ tiêu](../chi-tiet/00-thong-so.md)

## 1. Bối cảnh

Review phát hiện hai lỗi thiết kế làm hỏng thẳng N4 (0 request lỗi khi scale-down và khi cập nhật), cùng một số điểm thiết kế mà khi chạy thật sẽ không đo được hoặc đo sai. ADR này ghi lại cách sửa.

## 2. Quyết định

| # | Vấn đề (ISSUE) | Quyết định | Cần kiểm chứng |
|---|---|---|---|
| T1 | vLLM mặc định **huỷ** request đang chạy khi nhận SIGTERM (`--shutdown-timeout` mặc định 0) (B6) | Thêm `--shutdown-timeout=150` cho vLLM. Ràng buộc: preStop 20 s + 150 s < `terminationGracePeriodSeconds` 180 s | Cờ có trong bản đã ghim (`vllm serve --help`); vLLM có làm nốt cả request đang `waiting` không. Kiểm bằng 30 stream dài rồi `kubectl delete pod`, đếm lỗi phía client |
| T2 | `maxSurge: 0, maxUnavailable: 1` làm mất dịch vụ khi chỉ có 1 replica (B7) | Giữ `maxSurge: 0, maxUnavailable: 1`, nhưng quy trình cập nhật thêm bước đầu: nếu đang có 1 replica thì **tạm nâng `minReplicaCount` lên 2** (một PR riêng), chờ 2 pod Ready rồi mới đổi phiên bản, xong thì hạ về 1. **Bỏ sync window** của Argo CD, vì nó đẩy việc cập nhật đúng vào lúc chỉ có 1 replica. VH2 thêm ca 1 replica | – |
| T3 | Ngưỡng TTFT 2 s trong khi recording rule dùng bucket 2,5 (m1) | Chỉ dùng **một ngưỡng TTFT, trùng một biên bucket có thật**, cho cả cảnh báo (N7) lẫn nghiệm thu (N1). Giá trị tạm là **2,5 s**, chốt ở ADR-003 | Danh sách bucket trong `/metrics` của bản đã ghim |
| T4 | Hai nơi khác nhau ghi chỗ kiểm API key (m11) | Kiểm API key bằng `--api-key` của vLLM; Traefik chỉ giới hạn tốc độ | – |
| T5 | Giới hạn 2 req/s mỗi khoá sẽ chặn máy tạo tải (m6) | Máy tạo tải đi qua một route riêng của Traefik (ví dụ host nội bộ `llm-eval`, chỉ truy cập được trong cluster), gắn middleware có giới hạn cao | Cấu hình route trong Traefik đã ghim |
| T6 | Cách gây sự cố "scale Prometheus về 0" sẽ bị Operator và Argo CD hoàn tác (m7) | VH4 và bài T4 gây sự cố bằng **NetworkPolicy chặn KEDA → Prometheus**. Cách thay thế: tạm dừng sync app `monitoring`, rồi patch `spec.replicas: 0` của CR `Prometheus` | NetworkPolicy có được thực thi trên k3s |
| T7 | App `autoscaling` trỏ cả thư mục; không có bước dọn sau đánh giá (m8) | App chỉ trỏ tới `autoscaling/official/`. Runner xoá mọi ScaledObject khác A2 trước khi bật lại auto-sync | – |
| T8 | Không có cách thu cảnh báo cho VH6/N7 (m9) | Runner truy vấn chuỗi `ALERTS{alertstate="firing"}` trong cửa sổ của lượt, rồi ghi ra `alerts.jsonl` | – |
| T9 | Ở nhà, metric GPU không có label pod; RTX 5060 còn chạy màn hình (m10) | Ở nhà và trên GPU GeForce: A1 dùng `sum(nvidia_smi_utilization_gpu_ratio) * 100`, chạy Ubuntu không giao diện đồ hoạ. DCGM chỉ dùng nếu chạy được | DCGM trên RTX 4090/5060 |
| T10 | N2 "hồi phục SLO ≤ 5 phút" khó đạt vì backlog kẹt ở pod cũ (M2) | Tách N2 thành **N2a** (replica mới Ready ≤ 2 phút; Must) và **N2b** (thời gian hồi phục SLO; báo cáo, ngưỡng chốt ở ADR-003) | Đo thử KB2-mini ở nhà trong W3 |
| T11 | KB3 3,5C sát trần năng lực; N1 tính cả pha ramp (M3) | KB3 đặt λ = 0,75 × N × C (= 3C khi N = 4). N1 ở KB3 chỉ tính trên pha `sustain` | – |
| T12 | N3 không đạt được theo định nghĩa nếu chỉ có 2 GPU (M4) | Giữ N3 cho N = 4. Nếu phải chạy với N = 2 thì viết lại N3 theo N ở ADR-003, ví dụ GPU-giờ của A2 ≤ (1/N + 0,15) × GPU-giờ của S_N | – |
| T13 | Chưa có target tạm trước khi có B\* (M9) | Chạy ĐG1-mini ở nhà (30 phút, GPU yếu nhất), sinh `capacity-home.json`; ghi vào ADR-003a "giá trị tạm cho môi trường nhà" | – |
| T14 | N7 "không page khi khoẻ" có thể trượt dù cảnh báo đúng (M10) | "Page giả" = page trong khi tỷ lệ request xấu theo log client trên cùng cửa sổ < 20% | – |
| T15 | N6 chưa định nghĩa "VM trắng" (M6) | VM trắng = VM Ubuntu từ template của Vast, có sẵn driver NVIDIA, chưa có image, model hay cluster | Template Vast có driver |
| T16 | Tolerance 10% và scale-up không có cửa sổ chờ có thể gây scale giả ở KB1 (m13) | Giữ cấu hình; ghi nhận trong phân tích. Nếu đo thấy thì thử `scaleUp.stabilizationWindowSeconds: 15` và ghi ADR mới | – |
| T17 | "Resource utilization" mới chỉ có GPU-giờ (m14) | Bảng mỗi lượt có thêm GPU util trung bình, CPU và RAM của pod | – |
| T18 | Máy tạo tải chỉ tự kiểm phía gửi (m15) | Đo thêm độ trễ event loop; đối chiếu TTFT phía client với histogram phía server | – |

## 3. Hệ quả

- N4 đo được và có thể đạt. Đổi lại, quy trình cập nhật thêm một bước khi tải thấp.
- Cảnh báo và nghiệm thu dùng chung một ngưỡng TTFT, nên VH6 và N1 đối chiếu được với nhau.
- Một số giá trị (bucket, tên cờ, tên metric) phụ thuộc phiên bản, phải kiểm lại ngay khi ghim phiên bản ở W2.
