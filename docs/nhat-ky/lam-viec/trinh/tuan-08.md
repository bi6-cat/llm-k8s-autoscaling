# Nhật ký làm việc – Trình – Tuần 08 (23–29/11/2026)

## 2026-11-23 – Luận văn: đưa bố cục mới vào Kế hoạch §11.1 và quy tắc viết

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Thay dàn ý ở Kế hoạch §11.1 bằng bố cục chốt ngày 23/11: xương sống gồm ba thông điệp TĐ1–TĐ3 và năm hướng giải HG1–HG5; chương 4 gom 11 mục còn 7; thêm 1.4 Phương pháp và tổ chức thực hiện, 2.2 Hàng đợi và năng lực phục vụ, 3.6 Thiết kế đánh giá, 5.7 Hạn chế của phép đo, Phụ lục F; bảng truy vết yêu cầu → mục; người viết và lộ trình. Sửa §5.1 (câu phân công, bảng luận văn theo số mục mới) và tiêu chí M4, M5 cho khớp.
  2. `quy-tac-viet.md`: gộp quy tắc văn phong (giọng văn, người đọc, 20/80, mật độ gọn, câu và đoạn, cụm sáo và dấu hiệu văn do máy sinh, mã định danh, làm tròn số); thêm §2.2 trình bày quy trình và con người; §8 viết lại theo cách làm bản base, bảng ranh giới theo số mục mới; §9 khai báo công cụ AI một lần ở Lời cam đoan; cập nhật checklist.
  3. `nguon-tu-lieu.md`: đánh lại số mục ở §1, §2 theo dàn ý mới, bỏ cột người viết; sửa hai chỗ đã cũ (bảng và hình C1–C4 của V2 đã có ở `analysis/figures/v2-dg2/` từ PR #52).
  4. `docs/luan-van/README.md`: dòng người viết; bỏ quy ước tách file `a`, `b` theo người viết.
  5. Chạy `/code-review high` trên nhánh: 10 điểm, sửa cả 10 (Results).
- **Decision:** (D89)
  - Số của TĐ1–TĐ3 được đối chiếu với `analysis/figures/v2-dg2/runs.csv` trước khi ghi vào Kế hoạch. Thời gian phản ứng A2 × KB2 ghi 79,7–81,5 s theo cột `react_s` (79,71; 81,42; 81,53 s), thay cho 80–82 s đã làm tròn trong nhật ký Quang 18–19/11; dòng đó ở `nguon-tu-lieu.md` §3 cũng sửa theo. Chi tiết "A1 thêm replica từ giây 15, lên 4 replica trong 3 phút đầu" không đưa vào Kế hoạch, vì bảng đã commit không có cột để đối chiếu; TĐ1 chỉ giữ số kiểm được (A1 dùng 89,7–90,6% GPU-giờ của S4, A2 dùng 25%).
  - Kế hoạch không dẫn ADR-002 Q13 cho số trang chương 4, 5, vì Q13 đã được ADR-004 K12 thay; chỉ dẫn K12 (55–65 trang).
  - Bỏ cột "Người" ở `nguon-tu-lieu.md` §2: từ 22/11 Trình viết bản base toàn bộ, nên cột người viết không còn đúng; người soát kỹ từng mục lấy theo Kế hoạch §5.1.
  - Chưa đưa công cụ kiểm văn phong vào repo: để PR riêng có test, nên quy tắc viết chưa nhắc tới công cụ đó.
  - Kế hoạch §11.2 (slide) không dẫn số mục luận văn nên giữ nguyên.
  - Nhãn của dàn ý đổi thành TĐ1–TĐ3 (thông điệp) và HG1–HG5 (hướng giải), vì T1–T7 đã là bộ test autoscaling (Thông số F2) và P1–P7 đã là sản phẩm bàn giao (Kế hoạch §10.1). Hai nhãn chỉ dùng trong dàn ý, không vào thân bài (`quy-tac-viet.md` §4).
  - M4 (29/11) đổi thành bản base lượt 1 (mọi mục có mặt, khoảng 60% ngân sách chữ) gửi Quang review; tiêu chí "hai thành viên đã review chéo toàn bộ" chuyển sang M5 thành "Quang đã review toàn bộ bản base". Lý do: Trình viết base, Quang review sau khi base xong, nên tiêu chí cũ không đạt được đúng hạn.
  - Bản nháp `03-04-giam-sat-slo-canh-bao.md` đổi tên thành `03-05-…` ngay trong PR này, đánh lại tiêu đề, số bảng tạm và dẫn chéo theo số mục mới (nội dung giữ nguyên), để không còn hai mục 3.4 khi ghép thử.
- **Results:**
  - lychee 0.24.2 (offline, kèm anchor, bỏ qua đường dẫn cũ như job `docs`): 0 lỗi.
  - `/code-review high` báo 10 điểm, đã kiểm lại từng điểm với file và sửa cả 10:
    - §5.1 (đoạn và bảng luận văn) còn số mục cũ;
    - mã P và T trùng mã đã có;
    - tiêu chí M4 mâu thuẫn với lộ trình;
    - "7 lượt có vi phạm SLO" chưa nói rõ cách đếm: `runs.csv` có 7 lượt có `slo_violation_s`, trong đó A2 × KB3 (2 lượt) vẫn đạt SLO attainment 100% trên cả lượt;
    - quy tắc mã F/N mâu thuẫn với §5 và mục 1.3;
    - cộng khoảng trang chỉ được 52–64 (đã ghi cách đạt 55);
    - LT ở 5.2 lệch §11.1;
    - bản nháp 3.4 chưa đổi số;
    - dòng F4 ở Môi trường §16 ghi "bằng `make`" trong khi nhật ký Quang 18/11 cho thấy chạy tay từng lệnh;
    - phần đầu các tài liệu thiết kế 01, 03, 04, 05 còn dẫn số mục cũ.
- **Deviations:** phần "thay đổi so với dàn ý trước" ở Kế hoạch §11.1 chỉ giữ 6 ý chính, không chép đủ 8 ý của bản nháp bố cục.
- **Links:** `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§3 M4, M5; §5.1; §11.1; §11.4); `docs/chi-tiet/01`, `03`, `04`, `05` (phần đầu; 05 dòng F4); `docs/luan-van/quy-tac-viet.md`, `nguon-tu-lieu.md`, `README.md`, `03-05-giam-sat-slo-canh-bao.md`.
- **Thesis:** dàn ý toàn bộ; 1.4 (cách trình bày quy trình); Lời cam đoan (khai báo công cụ AI).

## 2026-11-23 – TR8: bản base mục 3.1 (yêu cầu và chỉ tiêu nghiệm thu)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Đọc Kế hoạch §11.1 (dàn ý 3.1), `quy-tac-viet.md` §2–§5, §10, Thông số §3–§8, Bài toán §6, §8–§12, ADR-005 T3, ADR-006 §3.1, Môi trường §6.1, §13, §19, Kiến trúc §7.1.
  2. Viết `docs/luan-van/03-01-yeu-cau-chi-tieu.md`: 4 tiểu mục (từ bài toán tới yêu cầu; mã định danh; yêu cầu chức năng; SLO và chỉ tiêu), 5 bảng (truy vết, mã định danh, F1–F7, SLO, N1–N8), comment nguồn sau mỗi đoạn và bảng. Agent viết nháp; Trình chưa đọc lại.
  3. Kiểm: `kiem_van.py` lần đầu 5 điểm (một cụm "việc … việc", 3 đoạn 2 câu, 1 câu 42 chữ), sửa còn 0; lychee 0 lỗi; pandoc ghép được.
  4. `/code-review high`: 10 điểm, sửa cả 10. Chính: ngưỡng 99% không 5xx ở Traefik không có số trong lượt đánh giá (thêm ghi chú vào bảng); câu "mỗi chỉ tiêu có một ngưỡng" sai vì N2b và phần KB2 của N1, N3 chỉ báo cáo; comment nguồn ghi V2 ngày 14–15/11 (kế hoạch) trong khi V2 thật chạy 18–19/11; lý do ngưỡng 30 phút dựng lại tính theo model 7B (khoảng 15 GB) nên thân bài nói rõ; KB2 giữ đỉnh tới phút 14 chứ không "giữ 10 phút"; VH2 cũng chạy trên VM (bằng annotation); "co giãn" thay bằng "tự điều chỉnh số replica"; vai trò A3, A4.
- **Decision:** đặt bảng mã định danh ngay sau bảng truy vết (3.1.2), trước bảng F/N, vì các bảng F/N dùng mã KB, ĐG, VH; bố cục ghi bảng mã ở cuối nhưng không quy định thứ tự. Bảng của 3.1 đánh số chính thức 3.1–3.5 (không dùng số tạm), vì 3.1 là mục đầu chương 3.
- **Results:** 1.181 chữ văn xuôi, 19 đoạn, 62 câu, trung bình 19,0 chữ/câu; kiem_van 0 điểm. `git log -L` trên `00-thong-so.md`: mọi dòng ngưỡng N1–N8, TPOT, 95%, 99% không đổi từ 08/10; dòng TTFT chỉ đổi ghi chú ngày 10/11, giá trị 2,5 s giữ nguyên.
- **Incidents:** câu nháp "histogram TTFT không có biên 2 s" không có nguồn trong repo (ADR-005 T3 chỉ nói ngưỡng 2 s lệch bucket 2,5 của recording rule); thử tìm danh sách bucket trong `vllm/v1/metrics/loggers.py` v0.31.0 thì thấy bucket sinh từ hàm `histogram_buckets()`, chưa đọc tiếp; đã viết lại câu theo đúng ADR-005 T3.
- **Deviations:** mục 3.1 vượt ngân sách lượt 1 (chương 3 lượt 1 khoảng 2.000 chữ, 3.5 đã 1.464 chữ). Chỗ cắt được nếu cần: đoạn lý do ngưỡng chất lượng và thời gian (khoảng 250 chữ) chuyển xuống phụ lục; bảng mã định danh chuyển sang danh mục mã ở phần đầu quyển. `00-thong-so.md` vẫn gắn nhãn "tạm" cho TTFT 2,5 s và N2b vì ADR-003 chưa viết; thân bài 3.1 không nhắc ADR, comment nguồn ghi rõ.
- **Links:** `docs/luan-van/03-01-yeu-cau-chi-tieu.md`, `docs/luan-van/nguon-tu-lieu.md` (dòng 3.1).
- **Thesis:** §3.1; danh mục mã định danh ở phần đầu quyển lấy từ Bảng 3.2.
