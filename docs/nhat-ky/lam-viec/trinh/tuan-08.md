# Nhật ký làm việc – Trình – Tuần 08 (23–29/11/2026)

## 2026-11-23 – Luận văn: chốt bố cục

- **Task:** chung (luận văn) · **Environment:** none
- **Done:**
  1. Đọc lại các nguồn quyết định giá trị của luận văn: Bài toán §5–§9, §12–§13; ADR-002; Thông số §3–§5; Môi trường §7–§19; Kế hoạch §11–§12 và R21; nguồn tư liệu §2–§6 (bản trong PR #52).
  2. Đề xuất bố cục mới, rồi giao một agent độc lập soát với các nguồn đó. Agent trả 17 điểm (3 cao, 10 vừa, 4 thấp). Phiên chính kiểm lại các khẳng định chính với nguồn gốc (ADR-002 Q13, Bài toán §9, mô tả đồ án Phụ lục A, Kế hoạch §12.1, Môi trường §13, các cột của `runs.csv`). Áp 16 điểm, bác 1.
- **Decision:** D87: bố cục dựng quanh ba thông điệp và năm hướng giải của Bài toán §6, mỗi hướng giải đi qua đủ thiết kế, triển khai, đánh giá, kết luận. Giữ khung yêu cầu F/N và bảng nghiệm thu của ADR-002, không quay lại câu hỏi nghiên cứu và giả thuyết.
  - Ba thông điệp: (T1) scale theo tải đồng thời của vLLM, không theo GPU utilization; (T2) autoscaling tiết kiệm nhiều ở tải thấp ổn định, còn dưới tải tăng đột ngột có giới hạn với nguyên nhân đo được; (T3) nền tảng vận hành được.
  - Chương 4 gom từ 11 mục còn 7, mỗi mục đủ dày cho khung sáu bước (rủi ro R21). Chương 3 có mục 3.6 Thiết kế đánh giá, kèm các chỉ số của đề cương; chương 2 có mục Hàng đợi và năng lực phục vụ; chương 5 có mục 5.7 Hạn chế và bảng tổng hợp LT1–LT8.
  - Số trang: 4–5 / 8–10 / 10–12 / 16–20 / 12–14 / 2–3. Chương 5 nằm trong mức 12–15 trang của ADR-002 Q13.
  - Bỏ: giữ 11 mục ở chương 4 (mỏng); viết mỗi hướng giải thành một chương (lệch chuẩn trình bày, hội đồng khó theo); tách mục 4.1 theo người viết (không còn áp dụng, vì Trình viết toàn bộ bản base).
- **Results:** bản soát phát hiện các điểm có căn cứ:
  - thiếu bảng ánh xạ bảy mục tiêu của đề cương và thiếu các chỉ số P95/P99, throughput, token/GPU-giờ (`runs.csv` đã có đủ các cột này);
  - giá trị SLO được dùng ở 3.1 nhưng đến 3.5 mới định nghĩa;
  - scale-down được đặt ở hai chỗ;
  - chưa có chỗ cho ca đối chứng graceful shutdown và VH2c;
  - ba số trong thông điệp lệch nguồn: A1 ở KB1 dùng khoảng 90% GPU-giờ của S4, không phải "chỉ tiết kiệm 5–10%"; thời gian phản ứng 79,7–81,5 s; câu "mọi thay đổi đi qua Git" chỉ đúng ở cluster nhà, vì trên VM thuê nền tảng được cài bằng Helm.
- **Deviations:** mục 1.5 Đóng góp được nêu 2–3 số chính kèm dẫn chéo tới chương 5, lệch `quy-tac-viet.md` §2 (chương 1 không đặt số đo).
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts`.
- **Thesis:** toàn bộ bố cục; cần sửa theo Kế hoạch §11.1, `quy-tac-viet.md` §2 và §8, `nguon-tu-lieu.md` §2.
