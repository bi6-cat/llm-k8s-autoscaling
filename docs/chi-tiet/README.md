# Tài liệu chuyên sâu

Mỗi tài liệu dưới đây đi sâu vào một mục lớn của [bản mô tả chính](../mo-ta-chi-tiet-do-an.md). Mục 15 (tài liệu tham khảo) và Phụ lục A (đối chiếu đề cương) không có tài liệu riêng.

Mọi tài liệu có cùng khung: **tóm tắt nhanh**, phần nội dung chi tiết, và **câu hỏi hội đồng có thể đặt ra** (kèm gợi ý trả lời) để chuẩn bị bảo vệ.

| # | Tài liệu | Nội dung chính | Hình mới |
|---|---|---|---|
| 1 | [Đặt vấn đề](01-dat-van-de.md) | VRAM và KV-cache, vì sao batching quan trọng, đặc điểm tải, lý thuyết hàng đợi, bối cảnh tự host, vì sao vận hành LLM trên GPU khó, phát biểu bài toán | Hình 10 |
| 2 | [Mục tiêu và yêu cầu hệ thống](02-muc-tieu-yeu-cau.md) | Yêu cầu chức năng F1–F7, chỉ tiêu nghiệm thu N1–N8, đối chiếu đề cương, ma trận truy vết, Must/Should/Could | – |
| 3 | [Phạm vi, giả định và hạn chế](03-pham-vi-gia-dinh.md) | Ranh giới hệ thống, 7 giả định kèm cách kiểm tra, hạn chế, điều kiện so sánh công bằng | – |
| 4 | [Kiến thức nền](04-kien-thuc-nen.md) | Prefill/decode, KV-cache, vLLM V1, thuật toán HPA, KEDA, metric DCGM, **SLO và burn rate, GitOps, rolling update**, giải pháp liên quan, thuật ngữ | Hình 11 |
| 5 | [Kiến trúc hệ thống](05-kien-truc-he-thong.md) | Cấu hình Deployment, lưu trữ model, Ingress, mô hình thời gian, **cold start 8 pha**, **graceful shutdown**, giám sát, GitOps | Hình 12, 13 |
| 6 | [Môi trường và chi phí](06-moi-truong-chi-phi.md) | Dựng k3s có GPU trên laptop; **Vast.ai chế độ VM, 4 × RTX 4090**; tiêu chí lọc máy, burn-in; dự toán 60–105 USD; đợt thuê liên tục ~37 giờ | – |
| 7 | [Thiết kế autoscaling](07-chien-luoc-autoscaling.md) | Phân tích A1–A4 (bão hoà, định luật Little, flapping), chọn target, YAML đầy đủ, cạm bẫy, bài kiểm thử, **cấu hình khuyến nghị** | Hình 14 |
| 8 | [**Vận hành nền tảng**](08-van-hanh.md) | SLI/SLO, cảnh báo theo burn rate, Alertmanager, **runbook**, **cập nhật khi hết GPU**, sự cố, dựng lại từ đầu, bảo mật tối thiểu, chi phí và năng lực | Hình 16 |
| 9 | [Kiểm thử và đánh giá](09-kiem-thu-danh-gia.md) | Ba lớp kiểm thử, đo năng lực, máy tạo tải, ba kịch bản tải, ma trận 28 lượt, cold start, **kịch bản vận hành VH1–VH6**, chỉ số, bảng nghiệm thu | Hình 15, 17 |
| 10 | [Phân công](10-phan-cong.md) | RACI theo 8 gói công việc, hợp đồng giao diện, quy trình làm việc, học chéo, minh chứng đóng góp | – |
| 11 | [Kế hoạch](11-ke-hoach.md) | Kế hoạch từng tuần, checklist các mốc, đường găng, lịch làm việc với GVHD, kế hoạch cắt giảm | – |
| 12 | [Rủi ro](12-rui-ro.md) | Sổ đăng ký 22 rủi ro, phân tích sâu các rủi ro đáng chú ý, ngưỡng ngân sách, runbook sự cố trong đợt đánh giá | – |
| 13 | [Sản phẩm bàn giao](13-san-pham-ban-giao.md) | Cấu trúc repo, Makefile, CI, dữ liệu, hướng dẫn tái lập và vận hành, dàn ý luận văn và slide, kịch bản demo | – |
| 14 | [Hướng mở rộng](14-huong-mo-rong.md) | 13 hướng, xếp hạng theo giá trị và công sức, cách viết mục "Hướng phát triển" | – |

**Lộ trình đọc gợi ý**
- *Để hiểu nền tảng:* 01 → 04 → 05 → 07 → 08.
- *Để bắt tay vào làm:* 06 → 05 → 07 → 08 → 11.
- *Để chuẩn bị đợt đánh giá:* 09 → 06 §5 → 12 §5.
- *Trước buổi bảo vệ:* đọc mục "Câu hỏi hội đồng" ở cuối mỗi tài liệu, nhất là 02 §10 và 08 §11.

**Ghi chú về số liệu:** mọi con số về thời gian, năng lực và chi phí trong bộ tài liệu là **ước lượng hoặc minh hoạ** dựa trên thông số phần cứng và hiểu biết chung. Chúng sẽ được thay bằng số đo thực tế của đồ án. Tên metric, cờ dòng lệnh và cách cài đặt có thể đổi theo phiên bản, nên luôn kiểm tra lại sau khi ghim phiên bản.

**Thay đổi so với bản 1.0:** đồ án chuyển trọng tâm sang xây dựng và vận hành (khoảng 70%), phần đánh giá giữ ở mức nghiệm thu (khoảng 30%). Lý do và danh sách thay đổi nằm ở [ADR-002](../adr/002-chuyen-trong-tam-sang-van-hanh.md).
