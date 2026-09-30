# Tài liệu chuyên sâu

Mỗi tài liệu dưới đây đi sâu vào một mục lớn của [bản mô tả chính](../mo-ta-chi-tiet-do-an.md). Mục 16 (tài liệu tham khảo) và Phụ lục A (đối chiếu đề cương) không có tài liệu riêng.

Mọi tài liệu có cùng khung: **tóm tắt nhanh**, phần nội dung chi tiết, và **câu hỏi hội đồng có thể đặt ra** (kèm gợi ý trả lời) để chuẩn bị bảo vệ.

| # | Tài liệu | Nội dung chính | Hình mới |
|---|---|---|---|
| 1 | [Đặt vấn đề](01-dat-van-de.md) | VRAM và KV-cache, vì sao batching quan trọng, đặc điểm tải, lý thuyết hàng đợi, ví dụ chi phí, phát biểu bài toán | Hình 10 |
| 2 | [Mục tiêu và câu hỏi nghiên cứu](02-muc-tieu-cau-hoi-nghien-cuu.md) | Mục tiêu SMART, biến và quy tắc kết luận cho từng RQ, ma trận truy vết, Must/Should/Could | – |
| 3 | [Phạm vi, giả định và giới hạn](03-pham-vi-gia-dinh.md) | Ranh giới hệ thống, 8 giả định kèm cách kiểm chứng, các mối đe doạ tính hợp lệ | – |
| 4 | [Kiến thức nền](04-kien-thuc-nen.md) | Prefill/decode, công thức KV-cache, băng thông GPU, vLLM V1, thuật toán HPA, cơ chế KEDA, metric DCGM, nghiên cứu liên quan, thuật ngữ | Hình 11 |
| 5 | [Kiến trúc hệ thống](05-kien-truc-he-thong.md) | Cấu hình Deployment, lưu trữ model, Ingress, mô hình thời gian, **cold start 8 pha**, **graceful shutdown**, giám sát, GitOps | Hình 12, 13 |
| 6 | [Môi trường và chi phí](06-moi-truong-chi-phi.md) | Dựng k3s có GPU trên laptop; **Vast.ai chế độ VM, 4 × RTX 4090**; tiêu chí lọc máy, burn-in, CPU riêng cho máy tạo tải; dự toán 105–170 USD; đợt thuê liên tục ~72 giờ | – |
| 7 | [Chiến lược autoscaling](07-chien-luoc-autoscaling.md) | Phân tích A1–A4 (bão hoà, định luật Little, flapping), chọn target, YAML đầy đủ, cạm bẫy, bài kiểm thử | Hình 14 |
| 8 | [Thiết kế thí nghiệm](08-thiet-ke-thi-nghiem.md) | Hiệu chỉnh, SLO, Poisson không thuần nhất, máy tạo tải open-loop, thiết kế khối, máy trạng thái của runner, tiêu chí hợp lệ | Hình 15 |
| 9 | [Chỉ số đánh giá](09-chi-so-danh-gia.md) | Định nghĩa và công thức từng chỉ số, phân vị và cỡ mẫu, thời gian hồi phục, lược đồ dữ liệu, thư viện PromQL | Hình 16 |
| 10 | [Phân tích kết quả](10-phan-tich-ket-qua.md) | Pipeline phân tích, kế hoạch đăng ký trước, so sánh cặp, bootstrap, đặc tả biểu đồ C1–C8, khung chương 5 | – |
| 11 | [Phân công](11-phan-cong.md) | RACI chi tiết, hợp đồng giao diện, quy trình làm việc, học chéo, minh chứng đóng góp | – |
| 12 | [Kế hoạch](12-ke-hoach.md) | Kế hoạch từng tuần, checklist các mốc, đường găng, lịch làm việc với GVHD, kế hoạch cắt giảm | – |
| 13 | [Rủi ro](13-rui-ro.md) | Sổ đăng ký 16 rủi ro, phân tích sâu các rủi ro ưu tiên cao, ngưỡng ngân sách, runbook sự cố | – |
| 14 | [Sản phẩm bàn giao](14-san-pham-ban-giao.md) | Cấu trúc repo, Makefile, CI, bộ dữ liệu, hướng dẫn tái lập, dàn ý luận văn và slide, kịch bản demo | – |
| 15 | [Hướng mở rộng](15-huong-mo-rong.md) | 11 hướng, xếp hạng theo giá trị và công sức, cách viết mục "Hướng phát triển" | – |

**Lộ trình đọc gợi ý**
- *Để hiểu nền tảng:* 01 → 04 → 05 → 07.
- *Để bắt tay vào làm:* 06 → 05 → 07 → 08 → 12.
- *Trước buổi bảo vệ:* đọc mục "Câu hỏi hội đồng" ở cuối mỗi tài liệu, cùng với 03 §5 và 10 §4.

**Ghi chú về số liệu:** mọi con số về thời gian, năng lực và chi phí trong bộ tài liệu là **ước lượng hoặc minh hoạ** dựa trên thông số phần cứng và hiểu biết chung. Chúng sẽ được thay bằng số đo thực tế của đồ án. Tên metric, cờ dòng lệnh và cách cài đặt có thể đổi theo phiên bản, nên luôn kiểm tra lại sau khi ghim phiên bản.
