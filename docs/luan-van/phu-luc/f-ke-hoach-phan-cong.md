<!-- Mục đích: Phụ lục F, kế hoạch, mốc và phân công của nhóm (quy tắc viết §2: bảng kế hoạch và phân công kèm tên thành viên), mà mục 1.2 dẫn tới. Người viết: Trình. -->
<!-- Tóm từ docs/chi-tiet/06-ke-hoach-quan-ly.md §1, §1.1, §5, §5.1 trên main (commit 71368c0, 24/11/2026). Tên có dấu của Quang suy từ tên Git "Nguyen Ngoc Quang"; mã sinh viên, lớp chưa điền: cần Trình và Quang soát theo mẫu của trường. Rút gọn 28/11 (bản nộp: phụ lục F 3 tr, đích ≤ 1,5 tr): F.2 bỏ câu về PR và CI (đã có ở 1.2) và ví dụ việc cạnh máy nhà (cài hệ điều hành và driver, khởi động lại máy). Bảng F.1 chỉ giữ tiêu chí chính của mốc (bỏ phiên thử V0 và chốt nhà cung cấp cloud ở M1, ADR-003 ở M3, sao lưu ở M3); bỏ chi tiết phiên dự phòng V3 bị bỏ, lịch V2 cũ 07–08/11 → 14–15/11 và hạn nộp 07–08/12 trong văn xuôi; tra ở Kế hoạch §1, §1.1. Không đưa vào: bảng việc theo tuần W2–W5 của §5.1 (kế hoạch, nhiều việc đã đổi), cột gói WP của từng mã, Hình 9 (vẽ lịch trước điều chỉnh 04/11). -->

# Phụ lục F. Kế hoạch và phân công {.unnumbered}

## F.1. Lịch và mốc

Đồ án làm trong khoảng 9 tuần và có 5 mốc (Bảng F.1). Lịch được điều chỉnh một lần lớn ngày 04/11/2026, khi M1 mới đạt 2/7 mục và M2 chưa đạt mục nào. Nhóm làm trên kind và cluster nhà trước, gộp hai phiên thử V0 và V1, dời phiên đo chính V2 và giữ nguyên ngày đóng băng dữ liệu. V2 diễn ra ngày 18–19/11, trước ngày đóng băng.
<!-- nguồn: 06-ke-hoach-quan-ly.md §1 (bảng tuần W1–W9, bảng mốc; M3 ghi "~~15/11~~ 22/11 (không lùi thêm)"), §1.1 (04/11: M1 2/7, M2 0/8; V0+V1 gộp; V2 dời sang 14–15/11; đóng băng 22/11); nhật ký Quang tuần 07 mục 18/11 và 19/11 (phiên V2) -->

**Bảng F.1.** Các mốc của đồ án

| Mốc | Ngày | Tiêu chí chính |
|----|------|--------------------|
| M1 | 18/10 | Nền tảng tối thiểu chạy ở nhà qua Argo CD |
| M2 | 01/11 | Vận hành thử đạt; runner chạy được trên VM thuê |
| M3 | 22/11 | Dữ liệu đánh giá đầy đủ, đóng băng |
| M4 | 29/11 | Bản thảo đủ 6 chương |
| M5 | 07–08/12 | Nộp luận văn; tag `v1.0` |
<!-- nguồn: 06-ke-hoach-quan-ly.md §1 bảng mốc, cột tiêu chí rút gọn -->

## F.2. Phân công theo tính năng

Hai thành viên cùng vai trò DevOps/SRE và chia việc theo tính năng dọc, chốt ngày 15/10/2026. Người sở hữu một tính năng làm trọn tính năng đó, từ thiết kế, code, kiểm thử, giám sát, runbook tới mục luận văn tương ứng. Việc phải có mặt cạnh máy nhà do Nguyễn Ngọc Quang làm. Bảng F.2 ghi giờ công ước lượng theo kế hoạch, chưa tính phần viết luận văn và ca trực phiên V2 của cả hai người.
<!-- nguồn: 06-ke-hoach-quan-ly.md §5 (phân công chốt 15/10/2026), §5.1 Nguyên tắc (tính năng dọc; việc cạnh máy do Quang, 3–5 giờ cả dự án) và "Việc chung" (trực V2 cả hai) -->

**Bảng F.2.** Phân công tính năng và giờ công ước lượng

| Mã | Tính năng | Người-giờ |
|----|------------------------------------|--------|
| | **Nguyễn Ngọc Quang: chạy được trên GPU** | **61–89** |
| Q1 | Hạ tầng nhà: Ansible cho k3s, NVIDIA, device plugin, GPU exporter | 9–12 |
| Q2 | Cloud: script thuê máy Vast.ai, Ansible cho VM, overlay `cloud`, `make bootstrap`; phiên V0 | 5–8 |
| Q3 | Tầng phục vụ vLLM: Deployment, probe, preStop, lưu trữ model, overlay `home`, ghim digest | 12–18 |
| Q4 | Cold start: mức L2 (tải sẵn image, compile cache), đo 8 pha, L0 và L2 trên V2 | 8–12 |
| Q5 | Vòng đời pod an toàn: graceful shutdown, rolling update, VH1–VH3 | 8–12 |
| Q6 | Runner và ĐG1, ADR-003 | 12–16 |
| Q7 | VH5 trên VM (dựng lại từ máy trắng), sổ chi phí | 3–5 |
| Q8 | Kiểm chứng lý thuyết LT1–LT4 | 4–6 |
| | **Trần Đức Trình: tự scale và đo được** | **66–95** |
| TR1 | GitOps và CI: Argo CD, App-of-Apps, CI | 12–18 |
| TR2 | Simulator và autoscaling: kind với simulator, ScaledObject A1–A4, `behavior`, test T1–T7 | 8–12 |
| TR3 | Giám sát và SLO: kube-prometheus-stack, PodMonitor, quy tắc ghi, 3 dashboard | 9–13 |
| TR4 | Cảnh báo: quy tắc cảnh báo và unit test, Alertmanager tới Telegram, runbook | 10–14 |
| TR5 | Máy tạo tải, bộ đọc log 8 pha cold start | 8–11 |
| TR6 | VH4, VH6, bảo mật tối thiểu (API key, NetworkPolicy) | 5–8 |
| TR7 | Phân tích: script dựng bảng, biểu đồ, số liệu cho bảng nghiệm thu | 8–12 |
| TR8 | Kiểm chứng lý thuyết LT5–LT8 | 6–7 |
<!-- nguồn: 06-ke-hoach-quan-ly.md §5.1 hai bảng Quang (Cộng 61–89) và Trình (Cộng 66–95); TR1 bỏ Sealed Secrets (lược 12/11, ADR-006 §3.1), TR6 bỏ rate limit (lược 12/11, Phụ lục C comment đầu file) nên không ghi; Q2 "vast.sh" ghi thành "script thuê máy Vast.ai"; "6 cảnh báo, 6 runbook" của TR4 không ghi số vì nay có 7 cảnh báo (Phụ lục B, C) -->

## F.3. Phân công viết luận văn

Từ 22/11/2026, Trần Đức Trình viết bản đầu của toàn bộ luận văn từ nhật ký làm việc của cả hai người, tài liệu thiết kế và dữ liệu đo. Nguyễn Ngọc Quang review toàn bộ, sửa và cập nhật số. Mỗi mục do người sở hữu tính năng tương ứng soát sự kiện và số liệu (Bảng F.3).
<!-- nguồn: 06-ke-hoach-quan-ly.md §5.1 đoạn "Luận văn" (từ 22/11/2026) và bảng theo chương -->

**Bảng F.3.** Người soát sự kiện và số liệu của từng chương

| Chương | Nguyễn Ngọc Quang | Trần Đức Trình |
|------|---------|---------|
| Mở đầu | Cùng soát | Cùng soát |
| 1. Giới thiệu | Toàn chương | – |
| 2. Cơ sở lý thuyết | 2.1, 2.3 | 2.2, 2.4–2.6 |
| 3. Yêu cầu và thiết kế | 3.2, 3.4, 3.6 (ĐG1, ĐG3, VH1–VH3, VH5) | 3.1, 3.3, 3.5, 3.6 (ĐG2, VH4, VH6, tính hợp lệ) |
| 4. Triển khai và vận hành | 4.1 (hạ tầng, dựng lại), 4.2, 4.4, 4.5, 4.7 (runner) | 4.1 (GitOps, CI, bí mật, bảo mật), 4.3, 4.6, 4.7 (máy tạo tải, phân tích) |
| 5. Đánh giá | 5.1, 5.2, 5.4, 5.5 (VH1–VH3, VH5, graceful shutdown), 5.7 | 5.3, 5.5 (VH4, VH6), 5.6, 5.7 |
| 6. Kết luận | – | Toàn chương |
| Ghép và định dạng | Slide, video demo | Luận văn (khuôn trình bày, hình, tài liệu tham khảo) |
<!-- nguồn: 06-ke-hoach-quan-ly.md §5.1 bảng "Chương | Quang | Trình" -->
