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

## 2026-11-23 – Merge PR #46, #52 của Quang; gộp xung đột nhật ký qua PR #58

- **Task:** chung · **Environment:** none
- **Done:**
  - Trình merge PR #46 (Q6, `vh3-delete` giữ pod thứ hai trước khi xoá) bằng merge commit: CI 6/6 xanh, đã Approve 21/11, không có commit sau lần duyệt.
  - Sau đó #52 chuyển sang `CONFLICTING`, vì #46 và #52 cùng thêm mục vào cuối `docs/nhat-ky/lam-viec/quang/tuan-07.md`.
  - Tạo nhánh `fix/tr8-pr52-sync-main` từ đầu nhánh #52 (`72e83f5`), merge `origin/main`, gộp nhật ký theo thứ tự ngày: hai mục 16/11 của #46 đặt trước tám mục 18–20/11 của #52. Mở PR #58; CI 6/6 xanh; merge. GitHub tự đánh dấu #52 là merged.
  - Merge `main` vào `docs/tr8-thesis-ch5-drafts`: không xung đột.
- **Decision:** D88. Không đẩy commit lên nhánh của Quang; dùng PR thay thế bằng merge commit để giữ nguyên 15 commit và tác giả. Bỏ: chờ Quang tự merge `main` vào nhánh (chặn thêm), squash (mất lịch sử, #52 không tự thành merged).
- **Results:** diff của #58 so với `main`: 11 file, +944 −16, khớp từng file với #52. Nhật ký sau gộp không còn marker; tập dòng khác rỗng bằng đúng hợp của hai phía (367 dòng). CI của `main` sau #46 (`adc80b1`) xanh.
- **Incidents:** lệnh `git switch -c` thất bại khi đang merge dở ("cannot switch branch while merging"), nên commit gộp được tạo trên HEAD tách rời trước rồi mới đặt tên nhánh. Không có gì bị đẩy lên sai nhánh.
- **Links:** PR #46, #52, #58 (merge commit `6482406`).
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
- **Links:** PR #59, merge commit `31a3ae5` (CI 6/6 xanh, MERGEABLE, không có review); sau đó merge `origin/main` vào `docs/tr8-thesis-ch5-drafts`, nhật ký tuần 08 gộp đúng thứ tự. `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§3 M4, M5; §5.1; §11.1; §11.4); `docs/chi-tiet/01`, `03`, `04`, `05` (phần đầu; 05 dòng F4); `docs/luan-van/quy-tac-viet.md`, `nguon-tu-lieu.md`, `README.md`, `03-05-giam-sat-slo-canh-bao.md`.
- **Thesis:** dàn ý toàn bộ; 1.4 (cách trình bày quy trình); Lời cam đoan (khai báo công cụ AI).

## 2026-11-23 – Luận văn: đo trang bằng dàn trang thử, chốt ngân sách từng mục chương 3

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Dàn trang thử bốn bản nháp chương 3 (3.1, 3.3, 3.5, 3.6) bằng pandoc 3.13 và Typst 0.15.1, theo hai khuôn A4 giãn 1,5 dòng: khuôn A Times New Roman 13 pt, lề 2/2/3/2 cm; khuôn B 14 pt, lề 3,5/3/3,5/2 cm. Bảng dùng cỡ chữ nhỏ hơn văn xuôi 1 pt, được ngắt qua trang, cột co theo nội dung.
  2. Ghi vào quy tắc viết: ngân sách theo trang (§1), thứ tự cắt khi vượt ngân sách (§3.1), quy tắc bảng (§6). Thêm ngân sách từng mục chương 3 vào Kế hoạch §11.1.
- **Decision:** Trình giao việc chọn độ dài, yêu cầu nội dung chuyên nghiệp, đúng trọng tâm 20/80 và câu nào cũng có giá trị.
  - Giữ tổng 55–65 trang (ADR-004 K12) và khoảng trang của từng chương. Ngân sách đổi đơn vị từ "300 chữ mỗi trang" sang **trang, gồm cả bảng và hình**.
  - Chương 3 lấy mức trên, 12 trang: mở đầu và kết chương 0,5 · 3.1 1,5 · 3.2 2 · 3.3 2,5 · 3.4 1,5 · 3.5 2 · 3.6 2. Mục 3.3 nhiều nhất vì mang TĐ1.
  - Không chọn nâng chương 3 lên 14–16 trang: phải lấy chỗ của chương 4 hoặc chương 2, trong khi gần một nửa số trang thừa là bảng.
  - Script dàn trang chỉ để trên máy, không đưa vào repo. Khi có khuôn .docx của trường thì đo lại bằng `--reference-doc` và Word.
- **Results:** số trang (mỗi mục dàn riêng, nên trang cuối lẻ tính tròn một trang):

  | Phần | Khuôn A | Khuôn B |
  |---|---|---|
  | 3.1 (1.181 chữ văn xuôi, 5 bảng) | 5 | 7 |
  | 3.3 (1.659 chữ, 3 bảng) | 5 | 6 |
  | 3.5 (1.464 chữ, 2 bảng) | 4 | 5 |
  | 3.6 (2.305 chữ, 7 bảng) | 10 | 13 |
  | Bốn mục ghép liền | 22 | 29 |
  | Chỉ văn xuôi của bốn mục (6.609 chữ) | 13 | 16 |

  Văn xuôi khoảng 510 chữ/trang (A) và 415 chữ/trang (B). Bảng trung bình 0,5–0,75 trang mỗi bảng. Bốn mục mới viết gấp 2,75–3,6 lần ngân sách 8 trang của chính chúng, và đã vượt 10–12 trang của cả sáu mục.
- **Incidents:** lần dàn đầu, bảng không ngắt qua trang (để lại trang gần trống) và cột chia đều, nên số trang bị đội; lần sửa thứ hai đếm số cột từ file Markdown, lệch vì có bảng trong comment. Cuối cùng giữ số cột Pandoc sinh ra, chỉ đổi độ rộng sang `auto`, và soát bằng ảnh trang trước khi lấy số.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §3.1, §6); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§11.1).
- **Thesis:** áp cho mọi mục; trước mắt là cắt 3.1, 3.3, 3.5, 3.6 về ngân sách, và viết 3.2, 3.4 theo ngân sách.

## 2026-11-24 – Luận văn: đo ba nháp chương 5, chốt ngân sách chương 5, cắt 5.3

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Đo ba nháp chương 5 bằng dàn trang thử (`.work/tools/do_trang/run.sh`, khuôn B: 14 pt, lề 3,5/3/3,5/2 cm): 5.3 = 8 trang, 5.5b (VH4, VH6) = 8, 5.6 = 8; tổng ba nháp gấp khoảng 4 lần phần ngân sách tương ứng.
  2. Chốt ngân sách chương 5 theo trang và ghi vào Kế hoạch §11.1 (đoạn Cân đối).
  3. Cắt 5.3 (`docs/luan-van/05-03-autoscaling-so-voi-tinh.md`) từ 3.500 xuống khoảng 830 chữ văn xuôi: bảng 11 ô ghi khoảng thấp nhất–cao nhất thay cho số từng lượt; bỏ đoạn mô tả lại kịch bản KB2 (đã có ở 3.6), tốc độ xử lý của pod cũ, chi tiết pha tăng dần và pha duy trì của KB3, thời điểm A1 bớt pod; viết lại theo quy-tac-viet §4 (tối đa 4 mã mỗi đoạn, tên pha tiếng Việt). Các ý đã cắt ghi trong comment đầu file kèm nguồn (`analysis/dg2_a2.py` phần 1–4).
- **Decision:** ngân sách chương 5 = 14 trang (mức trên của 12–14): 5.1 ≈ 1 · 5.2 ≈ 1,5 · 5.3 ≈ 4 · 5.4 ≈ 1,5 · 5.5 ≈ 3 (VH4 và VH6 khoảng 1,25) · 5.6 ≈ 2 · 5.7 ≈ 1. 5.3 tăng từ 3 lên 4 trang vì trả lời câu hỏi chính và hình diễn biến KB2 (518 × 619 pt) chiếm gần trọn một trang; hình SLO attainment theo GPU-giờ chuyển sang Phụ lục E. Phương án bỏ: giữ 5.3 = 3 trang (phải bỏ phân tích hàng đợi, là kết quả chính của mục); đo với hình trôi (lệch với cách đo của chương 3).
- **Results:** 5.3 sau khi cắt: 3,61 trang khuôn A, 3,96 trang khuôn B (ngân sách 4); `kiem_van.py` 0 điểm; lychee 59/59 OK. Không đổi số liệu so với nguồn; hai chỗ diễn đạt lại có tính từ nguồn: A1 × KB2 tiết kiệm 4,6–4,9% GPU-giờ (1 − 0,9537 và 1 − 0,9514), A1 lên 4 replica sau 166–181 s.
- **Deviations:** Kế hoạch §11.1 đổi ngân sách mục của chương 5 (5.1 1,5 → 1; 5.3 3 → 4); tổng chương 5 vẫn trong khoảng 12–14 trang.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.1.
- **Thesis:** §5.3; chương 2 (mục 2.4) phải định nghĩa flapping, vì 5.3 dùng thẳng thuật ngữ này. Còn cắt: 5.6 (8 → 2 trang), 5.5b (8 → 1,25 trang).

## 2026-11-24 – Luận văn: cắt nháp 5.6 về 2 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Cắt `docs/luan-van/05-06-bang-nghiem-thu.md` từ 8 trang (khuôn B) về ngân sách 2 trang: gộp hai bảng F1–F7 và N1–N8 thành một Bảng 5.6a 4 cột (yêu cầu/chỉ tiêu, mức, kết quả hoặc phần còn thiếu, kết luận); ngưỡng dẫn chéo sang Bảng 3.1, bảng đầy đủ kèm số từng lượt dành cho Phụ lục E; bỏ đoạn điều kiện đo (đã ở 5.1) và danh sách năm mức kết luận (đưa vào chú thích bảng).
  2. Viết lại văn xuôi theo quy-tac-viet §3–§5: khoảng giá trị kèm số lượt, tối đa 4 mã mỗi đoạn, mỗi đoạn có comment nguồn ngay sau. Ý đã cắt ghi trong comment đầu file kèm nguồn.
  3. Soát độc lập (`/code-review high`): 10 điểm, sửa cả 10 (phạm vi KB1, KB3 của N1; N2b không có ngưỡng ở Bảng 3.1 nên bỏ "dự kiến 5 phút"; thêm bằng chứng phần đã đạt của F1, F5, F7; đủ hai điều kiện của N3 và ba phần của N6; giải thích page ở A2 × KB3 không phải page giả; ghi số lượt; gọi mốc so sánh nhất quán là cấu hình tĩnh; sửa comment số cột và dẫn chéo sang file có trong repo).
- **Results:** 2.463 → 463 chữ văn xuôi, 2 → 1 bảng; đo 1,55 trang khuôn A, 1,95 trang khuôn B (ngân sách 2); `kiem_van.py` còn 1 điểm (đoạn mở mục 2 câu, mâu thuẫn §2 với §3.2 đã biết); lychee đạt. Không đổi số liệu so với nguồn; A2 × KB1 = 0,25 GPU-giờ của S4 đối chiếu lại `analysis/figures/v2-dg2/runs.csv`.
- **Deviations:** mục 5.6 chưa có bảng kiểm chứng LT1–LT8 như Kế hoạch §11.1; 5.6 đã dùng gần hết 2 trang, nên khi thêm bảng LT phải đưa bảng vào Phụ lục E hoặc lấy chỗ từ mục khác của chương 5.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR).
- **Thesis:** §5.6. Còn cắt: 5.5b (8 → 1,25 trang).

## 2026-11-24 – Luận văn: cắt nháp 5.5b (VH4, VH6) về 1,25 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Cắt `docs/luan-van/05-05b-vh4-vh6.md` từ 8 trang (khuôn B) về ngân sách 1,25 trang (D96): bỏ cả ba bảng (thời gian fallback ba lượt, SLO theo ba khoảng, mốc của 7 page), số từng lượt dành cho Phụ lục E; bỏ phần cách đo của VH6 (đã ở 3.6, PR #64), hai cấu hình quyết định fallback (để 4.3), chuỗi cảnh báo `KedaScalerErrors` trên simulator, danh sách cảnh báo khác và hai đoạn giới hạn.
  2. Viết lại văn xuôi theo quy-tac-viet §3–§4: câu đầu đoạn là kết luận, tối đa 4 mã mỗi đoạn, mã N chỉ ở câu so với chỉ tiêu, tên pha tiếng Việt. Ý đã cắt ghi trong comment đầu file kèm nguồn; giới hạn của VH4, VH6 và lỗ hổng "cảnh báo lỗi gửi tin đi qua chính đường đang hỏng" chuyển sang `nguon-tu-lieu.md` §6 cho mục 5.7 và 6.2.
  3. Soát độc lập (`/code-review high`): 10 điểm, sửa cả 10 (bỏ khẳng định "không tin nào tới Telegram", chỉ giữ "không có bằng chứng"; thêm số TPOT so sánh vì 5.3 không còn TPOT; "có cửa sổ 1 phút vi phạm SLO" để không mâu thuẫn với SLO attainment 100% của A2 × KB3; nêu đợt kêu sót từ lượt trước không chấm; mốc bắt đầu của thời gian fallback; "ở tải thấp" trong câu chủ đề; sửa dẫn chéo §3.5.5 và mục 4.3; ghi chi tiết cách chấm VH6 cho 3.6 hoặc Phụ lục E; ghi 300 s chờ scale-down là số tính từ cấu hình, chưa đo).
- **Results:** 4.503 → 512 chữ văn xuôi (đếm của `kiem_van.py`), 3 → 0 bảng; đo 0,96 trang khuôn A, 1,25 trang khuôn B (ngân sách 1,25); `kiem_van.py` 0 điểm; lychee đạt. Không đổi số liệu so với nguồn.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/nguon-tu-lieu.md` §6.
- **Thesis:** §5.5 (VH4, VH6), §5.7, §6.2; Phụ lục E (bảng từng lượt, lấy từ commit `bc49ff6`). Việc đo và cắt ba nháp chương 5 đã xong.

## 2026-11-24 – Luận văn: bản base mục 5.4 Cold start (ĐG3, LT4)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/05-04-cold-start.md` từ 5 lượt hợp lệ của ĐG3 (`runs/v2-vm/dg3-v2-4060ti/{L0-1,L0-2,L2-1,L2-2,L2-3}`: `summary.txt`, `vllm_log.json`). Bảng 5.4a chia thời gian theo tám pha (mốc kubelet cho pha 1–4, mốc vLLM cho pha 4–8), ghi khoảng giá trị; số từng lượt để trong comment cho Phụ lục E. Câu mở mục ghi rõ L0 đo 0 → 1, L2 đo 1 → 2.
  2. Đọc thêm log vLLM của 9 pod mới trong ba lượt A2 × KB2 bằng `parse_vllm_log` để giải thích vì sao cold start trong ĐG2 (65–66 s) ngắn hơn ĐG3 L2.
  3. Soát độc lập (`/code-review high`): 10 điểm. Sửa 8 điểm ở 5.4: pha 4 tách được bằng mốc `container_started`, `api_server_start`, `engine_init_start`; dòng "nạp weights" của bảng đổi thành "khởi tạo model và nạp weights", thêm dòng con theo log vLLM; hạ mức chắc chắn của giải thích page cache; chỉ dùng tên L0/L2; câu định nghĩa cold start; tổng tính chính xác tới 0,1 s; sửa ghi chú thứ tự lượt; đổi GiB/GB. Hai điểm ngoài 5.4 cũng sửa: câu bước scale-down đầu ở 5.3 thêm "nhiều khả năng" (lượt 2 không khớp với cửa sổ 300 s), Kế hoạch §11.1 "14–16 trang" thành "tối đa 16 trang". Thêm hai dòng hạn chế vào `nguon-tu-lieu.md` §6.
- **Decision:** D97: tổng cold start lấy `ready_seen_unix − trigger_unix` (chính xác tới 0,1 s) thay cho `trigger_to_ready_s` nguyên giây, để bảng cộng đúng từng pha. N5 vì vậy đổi từ 25,4% thành 25,3% ở 5.4 và 5.6; số nguyên giây vẫn ghi trong comment nguồn. Phương án bỏ: giữ số nguyên giây, khi đó tỷ lệ và tổng các pha lệch nhau tới 0,7 s.
- **Results:**
  - Từ lệnh scale tới Ready: L2 75,7–80,8 s (3 lượt), L0 301–311 s (2 lượt). L2 bằng 25,3% L0 theo trung bình, 26,9% ở cặp lượt bất lợi nhất, nên N5 đạt.
  - L0: kéo image 9,04 GB mất 154–156 s (khoảng một nửa), tải model 54,2–56,8 s, torch.compile 18,0–20,2 s (L2: 1,2–1,3 s nhờ compile cache).
  - L2: pha khởi động tiến trình 42,6–43,0 s, chiếm 52,7–56,8%. Trong đó 28,3–28,7 s trôi qua trước dòng log đầu của vLLM. Tài liệu thiết kế ước tính 5–15 s cho pha này.
  - LT4: vLLM báo nạp 5,75 GiB weights mất 7,7–7,8 s ở L2 (khoảng 0,8 GB/s) và 0,99–1,14 s ở L0. Tốc độ đĩa của VM chưa đo, nên chưa kiểm được phần định lượng. Nạp weights chiếm không quá 10,3% cold start.
  - ĐG2 A2 × KB2: 9 pod mới nạp weights 1,01–1,04 s, phù hợp với page cache ấm; phần này giải thích khoảng 6,7 s trong khoảng chênh 10–16 s so với ĐG3.
  - Đo trang: 1,21 trang khuôn A, 1,49 trang khuôn B (ngân sách 1,5); 472 chữ văn xuôi; `kiem_van.py` 0 điểm; lychee `docs/luan-van/` đạt. 5.3 sau khi sửa: 3,99 trang B (ngân sách 4).
- **Incidents:** lần đo trang đầu chạy `run.sh` với biến thư mục rỗng, nên `cat` tạo file `all.md` rỗng ở gốc repo. File đã được xoá trước khi commit. Theo `trigger_unix`, thứ tự đo là L2-2 → L0-2 → L2-1 → L2-3 → L0-1, tức chỉ 2 trong 3 lượt L2 chạy sau L0-2; nhật ký Quang 19/11 ghi "ba lượt".
- **Deviations:** phép so với cluster nhà (LT4 16/11, model 0,5B) bỏ khỏi thân bài để giữ ngân sách. Ý này ghi trong comment đầu file, để dùng cho bảng LT1–LT8 (5.6) hoặc Phụ lục E.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-04-cold-start.md`; `nguon-tu-lieu.md` §6.
- **Thesis:** §5.4, §5.6 (N5, LT4), §5.7 (hạn chế ĐG3); Phụ lục E (số từng lượt trong comment đầu 5.4).

## 2026-11-24 – Luận văn: bản base mục 5.1 và 5.2 (môi trường đo, năng lực một replica)

- **Task:** TR8 · **Environment:** none
- **Done:** viết `05-01-moi-truong-dieu-kien-do.md` (phiên V2: phần cứng, phần mềm, tham số request, lý do đổi máy, thứ tự đo, điều kiện hợp lệ, chi phí) và `05-02-nang-luc-mot-replica.md` (ĐG1, Bảng 5.2a, LT1–LT3). Nguồn: `capacity.json`, `matrix-dg1-v2.yaml`, nhật ký Quang tuần 06–07, `van-hanh.md` LT1–LT3, log vLLM và `checks.json` của 22 lượt. Soát số độc lập trên cả hai file, sửa 10 điểm, rồi cắt lại về ngân sách.
- **Decision:** 5.1 chỉ nêu giá trị xấu nhất của các điều kiện hợp lệ, không lập bảng, vì bảng ngưỡng đã có ở 3.6. Chi phí thực tế V2 ghi là chưa có (chưa đối chiếu hoá đơn), so sánh chi phí dùng GPU-giờ theo giả định G1. Giả thuyết "C bám TPOT ở batch lớn" chỉ ghi ở mức "có thể": C ở hai máy chỉ biết với bước 0,5 req/s, nên tỷ lệ C thật nằm trong 1,13–1,43, và phiên A4000 chạy vLLM với 2 lõi CPU.
- **Results:**
  - ĐG1 (RTX 4060 Ti, model 3B): C = 3,5 req/s, B* = 46,3, threshold A2 = 37. Ở λ = 4: SLO attainment 28,5%, đang chờ TB 12,4.
  - LT1: TPOT với 1 request chậm hơn cận dưới weights ÷ băng thông khoảng một phần tư (nhà 8,68 so với 6,9 ms; A4000 17,2 so với 13,8 ms). V2 đo C cao hơn tỷ lệ băng thông thuần (2,893 req/s) 21,0%.
  - LT2: dự đoán 36.864 B/token, V2 đo 36.843 B/token (7,26 GiB cho 211.584 token), lệch 0,06%.
  - LT3: điểm gãy giữa λ = 3,5 và 4, lúc số request đang chạy chạm 64 (63,5 ở λ = 4). Throughput bão hoà suy ra từ TPOT p50 62,6 ms khoảng 4,0 req/s. TPOT p50 tăng 53,6% khi B tăng từ 16 lên 46.
  - Điều kiện hợp lệ, giá trị xấu nhất trên 22 lượt: send lag p99 5,98 ms, CPU máy tạo tải 43,6%, khoảng trống scrape 5,0 s.
  - Đo trang (khuôn B, ngân sách D96): 5.1 0,99 trang (1), 5.2 1,49 trang (1,5). `kiem_van.py`: 5.2 0 điểm; 5.1 1 điểm ngày tháng ở đoạn đầu, chủ ý theo quy-tac-viet §5. lychee hai file đạt.
- **Incidents:**
  - Soát số tìm ra: LT1 ghi "chậm khoảng 20%" trong khi số trong câu cho 25–26%; 5.1 viết `--max-num-seqs` như giới hạn request nhận vào, trong khi đó là giới hạn batch; LT2 viết "lệch dưới 0,1% như ở nhà", nhưng ở nhà vLLM làm tròn tới 0,1 GiB; comment đầu file nêu tên công cụ soát, trái quy-tac-viet §9; thiếu comment thông điệp (§2). Đã sửa cả năm điểm.
  - Hai lần lệnh Bash bị treo vì một lệnh `cat >` thừa chờ stdin. Đã dừng tác vụ và chạy lại.
- **Deviations:** băng thông 288 và 448 GB/s là thông số của NVIDIA, chưa có mục trong `tai-lieu.bib`; ghi trong comment nguồn, thêm khi ghép chương. Các file 5.3–5.6 trên nhánh vẫn dùng dạng comment cũ (nêu tên công cụ soát, thiếu comment thông điệp).
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-01-moi-truong-dieu-kien-do.md`, `docs/luan-van/05-02-nang-luc-mot-replica.md`.
- **Thesis:** §5.1, §5.2, §5.6 (bảng LT), §5.7 (C thô do bước 0,5; V2 không đo TPOT 1 request; giả thuyết LT1 chưa kiểm).

## 2026-11-24 – Luận văn: bản base đầy đủ mục 5.5 Kịch bản vận hành (VH1–VH6, graceful shutdown)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Gộp `05-05b-vh4-vh6.md` vào `05-05-kich-ban-van-hanh.md` (`git mv`), giữ nguyên chữ phần VH4, VH6, thêm đoạn mở mục, VH1 (dẫn chéo 5.3), VH2 kèm ca đối chứng VH2c, VH3, VH5 và tiểu mục 5.5.7 graceful shutdown kèm ca đối chứng grace 5 s. Số tiểu mục theo mã kịch bản (5.5.k = VHk).
  2. Số lấy từ `runs/v2-vm/ops-vh*/summary.json` và `timeline.json`, `experiments/ops/vh.py`, nhật ký Quang tuần 07 (16/11, 18/11, 19/11), `van-hanh.md` (06/11, 09/11, 16/11). Bản nháp do agent soạn; một lượt soát độc lập đối chiếu từng số với nguồn.
  3. Đo trang, cắt về ngân sách, soát văn bằng `kiem_van.py`, soát độc lập rồi sửa, đo lại.
- **Decision:** bỏ bảng kết quả VH2/VH3 (5 dòng) khỏi thân bài, vì với bảng mục 5.5 đo 3,93 trang khuôn B so với ngân sách 3 (D96). Số của bảng đã có trong văn xuôi hoặc comment nguồn, nên bảng chuyển sang Phụ lục E. Số request của VH2, VH3 là của cả lượt tải (1.200–2.400 s), không phải của khoảng rolling update, nên không đặt cạnh thời gian rollout. Kết quả drain trên simulator (22,1 s) bỏ khỏi thân bài vì chỉ kiểm logic script.
- **Results:**
  - VH2 (V2, 1,75 req/s): ca 1 replica rolling update 141 s, ca 4/4 GPU `maxSurge: 0` 372 s, ca đối chứng `maxSurge: 1` kẹt sau 300 s với 1 pod Pending; cả ba 0 lỗi (2.077 / 4.229 / 2.077 request cả lượt).
  - VH3: xoá pod khi có 2 pod, thay thế Ready sau 67,4 s, 0 lỗi / 1.351; kill tiến trình con: Ready lại sau 67,4 s nhưng 129 lỗi / 1.041 (117 lỗi kết nối).
  - VH5: 8 phút 22 giây từ VM trắng (bấm tay, 1 lần). Graceful shutdown ở nhà: 144/144 stream, ca grace 5 s cắt 48/48.
  - Đo trang: 2,41 trang khuôn A, 2,93 trang khuôn B (ngân sách 3); 1.171 chữ văn xuôi, không bảng. `kiem_van.py` 0 điểm; lychee `docs/luan-van/` 0 lỗi.
- **Incidents:** soát độc lập báo 10 điểm, đều đã sửa. Nặng nhất: 5.5.7 khẳng định mỗi lần tắt pod giữ GPU tới 3 phút, trong khi VH2b trên V2 thay 4 pod (`maxSurge: 0`, pod mới phải chờ GPU của pod cũ) trong 371,6 s, khoảng 93 s mỗi pod, gần bằng cold start L2. Như vậy pod cũ trên V2 có lẽ đã thoát sau khoảng 15–20 s, khác với ở nhà. Câu đó giờ chỉ nói về máy nhà và nêu quan sát trên V2 như một suy luận chưa kiểm bằng log. Các điểm khác: rollout được kích hoạt bằng annotation trong pod template, không phải annotation của Deployment; làm tròn thời gian ≥ 100 s về số nguyên (sửa cả 104,5 → 104 s ở 5.6); câu lồng ", tức"; trộn số đo với suy luận trong một câu; đoạn mở mục dạng "Mục này…"; VH4 lặp điều kiện tải của đoạn mở; nhãn simulator cho drain; "mọi tiến trình" sửa thành tiến trình con.
- **Deviations:** SLO trong lúc rolling update (tiêu chí VH2 ở Môi trường §13) chưa tính: chưa có script tính SLO theo mốc của VH2 (`vh4_windows.py` chỉ nhận mốc của VH4). Cảnh báo trong các lượt VH2–VH4 không được lưu, nên vế "có cảnh báo" của VH2c và VH3 chưa kiểm được.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-05-kich-ban-van-hanh.md`, `docs/luan-van/05-06-bang-nghiem-thu.md`, `docs/luan-van/nguon-tu-lieu.md`.
- **Thesis:** §5.5; §5.7 (vh3-kill có lẽ chỉ 1 pod; hành vi SIGTERM của vLLM trên V2 khác ở nhà, chưa kiểm bằng log; không lưu cảnh báo trong VH2–VH4); §4.5 (VH2 trên VM kích hoạt qua annotation, không qua Git).

## 2026-11-24 – Luận văn: bản base mục 5.7 Hạn chế của phép đo và kết chương 5

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/05-07-han-che-phep-do.md` từ `nguon-tu-lieu.md` §6 (phần phép đo) và các chỗ ở 5.2, 5.4, 5.5, 5.6 dẫn "(mục 5.7)". Bản nháp do agent soạn; Trình chưa đọc lại.
  2. Đo trang, cắt về ngân sách, soát văn bằng `kiem_van.py`, soát độc lập rồi sửa, đo lại cả mục và cả chương 5.
- **Decision:** 5.7 chỉ nêu hạn chế chưa có ở mục khác: cỡ mẫu (1–3 lượt mỗi ô, 6/11 ô chỉ 1 lượt; hai kết luận chính vẫn giữ vì mọi lượt cùng chiều), bước tải ĐG1 0,5 thay vì 0,25, L0 đo từ 0 lên 1, LT1 chưa đo trên 4060 Ti, VH4 một lượt ở 0,5 C, VH6 chỉ chấm `LLMSLOBurnFast`, bản ghi thiếu của VH2–VH4, kịch bản vận hành chưa chạy ở nhà. Những ý mục khác đã nêu (máy 4060 Ti ở 5.1, page cache và tốc độ đĩa ở 5.4, Telegram ở 5.5.6) và các giới hạn nhỏ (metadata ghi commit khi tree dirty, không sao lưu R2, 2 lõi CPU ở phiên thử A4000) chuyển vào comment "Ý không đưa vào". Hạn chế của hệ thống để 6.2.
- **Results:**
  - 5.7: 405 chữ văn xuôi, không bảng; 0,75 trang khuôn A, 0,96 trang khuôn B (ngân sách 1, gồm kết chương). `kiem_van.py` 0 điểm; lychee 0 lỗi.
  - Cả chương 5 (05-01 tới 05-07, bỏ comment): 11,61 trang khuôn A, 13,68 trang khuôn B, trong ngân sách 14 trang (D96).
- **Incidents:** bản đầu dài 703 chữ (2 trang); cắt ba lần. Soát độc lập báo 10 điểm, đều đã sửa. Các điểm chính: bỏ sót giới hạn VH4, VH6 mà 05-05 hẹn đưa vào 5.7; kết chương chỉ nêu Service chia đều là nguyên nhân KB2, bỏ cold start mà 5.3 nêu ngang hàng; "cảnh báo kêu ở mọi lượt vi phạm" thiếu phạm vi "17 lượt so sánh cấu hình"; giải thích sai nguyên nhân C thô (do bước 0,5, không do mỗi mức 1 lượt); "LT1 chưa kiểm" mâu thuẫn 5.2 (đã kiểm ở nhà và A4000); câu mở "mọi số đo từ một phiên" sai vì chương có số ở nhà và simulator; "khâu gửi tin chưa kiểm" mâu thuẫn 5.5.6 (đã kiểm trên simulator).
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-07-han-che-phep-do.md`.
- **Thesis:** §5.7, kết chương 5; §6.2 nhận phần hạn chế của hệ thống (ghi trong comment đầu file).

## 2026-11-24 – Luận văn: chuẩn hoá comment đầu các file chương 5, kết thúc lượt tự chạy 4 giờ

- **Task:** TR8 · **Environment:** none
- **Done:** Lượt tự chạy 08:33 xong 7 vòng: cắt 5.3, 5.5b, 5.6 về ngân sách D96; viết base 5.1, 5.2, 5.4, 5.5, 5.7. Vòng 8 hết quota giữa lúc chuẩn hoá comment đầu file 5.3–5.7, để lại phần sửa chưa commit; script thoát mà không ghi dòng dừng. Phiên sau soát và commit phần đó: bỏ tên công cụ soát, thêm `<!-- Thông điệp -->` (5.3, 5.4, 5.6), đưa dòng soát về dạng `Soát số · Soát văn phong · Người viết đọc lại`, đổi câu mở 5.3 và 5.6 khỏi dạng "Mục này…" (quy-tac-viet §2).
- **Results:** đo lại khuôn B: 5.3 = 3,99 trang (bản trước khi sửa cũng 3,99; ngân sách 4), 5.6 = 1,95 trang (ngân sách 2). kiem_van còn 1 điểm ở đoạn mở 5.6 (2 câu), có từ trước, do mâu thuẫn quy-tac-viet §2 (đoạn mở 1–2 câu) với §3.2 (đoạn 3–7 câu), chưa sửa.
- **Links:** `docs/luan-van/05-03-…`, `05-04-…`, `05-06-…`, `05-07-…`; tổng kết lượt `.work/auto/runs/20261124-0833/` (cục bộ).
## 2026-11-24 – Luận văn: bỏ ngân sách trang từng mục, sửa dàn ý và quy tắc đề mục

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Ghép một bản đọc liền mạch (cục bộ, không commit) từ `main` và 8 nhánh luận văn chưa merge, có khung cho các mục chưa viết, rồi đo số trang từng mục theo khuôn B: đã có 28,4 trang base (chương 3: 11,5; 4.3: 3,05; chương 5: 13,8).
  2. Trình đọc bản ghép và nêu hai vấn đề: (a) độ dài không nên ép theo ngân sách, miễn nội dung có giá trị; (b) đề mục con nhiều mà mỗi mục ngắn, nhìn rời rạc, thiếu chuyên nghiệp.
  3. Đo độ dài từng đề mục của bản base và tìm quy định độ dài của các trường khác; so với một luận văn thạc sĩ cùng chủ đề.
  4. Sửa dàn ý ở Kế hoạch §11.1 (bảng đề mục, đoạn **Độ dài** thay đoạn "Cân đối", lộ trình, lý do), quy tắc viết §1, §2, §2.1, §3.1, §8, §10, nguồn tư liệu §2, ADR-004 K12 và §7.
- **Decision:** Trình đồng ý cả bốn điểm của đề xuất:
  - Độ dài theo nội dung lõi; định hướng 70–90 trang thân bài theo khuôn B, trần 100; bỏ ngân sách trang từng mục. Khoảng theo chương: 1: 5–6 · 2: 12–15 · 3: 15–18 · 4: 22–26 · 5: 16–20 · 6: 3–4. Không chọn giữ 55–65 trang, vì đó là con số nhóm tự đặt ở ADR-004 khi rút gọn phạm vi, không phải quy định của trường, và bản base viết theo ngân sách đó đã mất phần lý do.
  - Quy tắc đề mục: chỉ đặt tiêu đề khi nội dung dài từ khoảng 1 trang; mục dưới 2,5 trang không chia cấp 3; tiêu đề nói nội dung, không nói bước của khung hay mã kịch bản. Chương 1 gộp 6 mục còn 4; 5.3 đưa TĐ1 lên tiểu mục đầu; 5.5 gom 7 tiểu mục theo mã VH thành 3 theo chỉ tiêu N4, N6, N7; scale-down chuyển từ 5.3 sang 5.5.1.
  - Mỗi chương một PR, thay cho các PR từng mục (#62–#64, #66–#69); mốc M4 (29/11) là đủ mục theo dàn ý mới; phần lõi đã cắt ở chương 3, 5 được khôi phục tới trước hạn nộp.
- **Results:**
  - Bản base viết theo ngân sách cũ: phần lớn tiểu mục cấp 3 chỉ có 55–300 chữ (⅛–⅔ trang), ví dụ 3.2.3: 72 chữ, 5.5.1: 55, 5.5.5: 54; tiểu mục TĐ1 ở chương 5 (5.3.4) chỉ 110 chữ. Trước khi cắt, 5.3 có 3.500 chữ, sau khi cắt còn 830.
  - Quy định của các trường khác: ĐH KHTN TP.HCM 50–100 trang; một trường CNTT và Truyền thông 60–80 trang không kể phụ lục, mỗi nhóm tiểu mục ít nhất hai tiểu mục; Khoa CNTT ĐH Kinh tế Quốc dân tối thiểu 50 trang. Chưa tìm thấy quy định công khai của PTIT. Luận văn thạc sĩ Aalto về autoscaling Kubernetes: 54 trang thân bài, mục cấp 2 trung bình 2,5–3 trang.
  - Khuôn ảnh hưởng tới số trang: cả chương 5 (bản base ngày 24/11) đo 11,61 trang khuôn A (13 pt) và 13,68 trang khuôn B (14 pt), B dài hơn khoảng 18%.
  - `lychee --offline --include-fragments` trên `docs/**/*.md` và `*.md`: 719 link, 0 lỗi.
  - `/code-review high` trên diff: 9 điểm (2 quan trọng: tên 4.3.2 trái quy tắc mới; quy tắc 1 trang chưa miễn cho "Kết chương", "Cấu trúc luận văn"), đã sửa cả 9.
- **Deviations:** dàn ý ngày 23/11 (PR #59) và ngân sách trang ngày 23/11 (PR #65) được thay sau một ngày; các bản base 3.1–3.6, 4.3 và chương 5 sẽ phải sửa đề mục.
- **Links:** `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§3 M4, §11.1); `docs/luan-van/quy-tac-viet.md`; `docs/luan-van/nguon-tu-lieu.md`; `docs/luan-van/README.md`; `docs/adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md`.
- **Thesis:** áp cho toàn bộ luận văn; căn cứ về độ dài có thể nêu ngắn khi trả lời hội đồng.

## 2026-11-24 – Luận văn: chọn khuôn trình bày từ hai đồ án mẫu của khoa

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. GVHD gửi hai đồ án tốt nghiệp năm 2025 của Khoa Công nghệ Thông tin 1 làm mẫu: một đồ án chương trình tiên tiến viết tiếng Anh (.docx) và một đồ án hệ chính quy viết tiếng Việt (.pdf). Nhóm thuộc hệ chính quy nên luận văn viết tiếng Việt. Trình dặn hai mẫu chỉ là căn cứ tham khảo vì đề tài khác, không áp dập khuôn.
  2. Trích định dạng và cấu trúc: file .docx đọc style, section, mục lục bằng python-docx và pandoc; file .pdf đo vị trí từng ký tự bằng pdfplumber (khổ giấy, lề, cỡ chữ, khoảng dòng, thụt đầu dòng, vị trí chú thích, đầu trang, chân trang).
  3. Đo số trang bằng Word (COM, trên bản sao, không lưu): áp khuôn B, khuôn của mẫu tiếng Anh và khuôn T đề xuất lên bản đọc gộp ngày 24/11; áp khuôn của mẫu tiếng Anh lên chính file mẫu để kiểm tra cách giả lập.
  4. Ghi khuôn T vào quy tắc viết §1, §2; sửa Kế hoạch (dòng tóm tắt đầu file, §11.1: cột "Trang", đoạn **Phần đầu**, đoạn **Độ dài**, lý do thay đổi), nhật ký thay đổi của ADR-004 (K12) và README luận văn.
- **Decision:**
  - Khuôn T: A4; lề trên 2,5 cm, dưới 2,5 cm, trái 3 cm, phải 2 cm; Times New Roman 13 pt, giãn dòng 1,15, cách sau đoạn 6 pt, thụt đầu dòng 1,27 cm; chương 16 pt đậm căn giữa, sang trang mới; đầu trang và chân trang theo mẫu tiếng Việt. Ba chỗ khác mẫu: khổ A4 thay Letter (mẫu tiếng Việt dùng Letter, có lẽ do mặc định của Word); tên bảng đặt trên bảng theo IEEE và thông lệ tiếng Việt (hai mẫu đặt dưới); giữ cách đánh số `3.4.1.` và "Hình 3.1." vì hai mẫu không thống nhất với nhau.
  - Phần đầu quyển theo hai mẫu (bìa, Lời cảm ơn, hai trang nhận xét, mục lục và ba danh mục), giữ Lời cam đoan (chỗ khai báo dùng công cụ AI) và Tóm tắt 1 trang dù hai mẫu không có; bỏ *Abstract* và trang nhiệm vụ đồ án; không có phần "Mở đầu" riêng vì lặp chương 1.
  - Độ dài đổi đơn vị sang khuôn T, đo bằng Word: định hướng 60–75 trang thân bài, trần 85, cùng nội dung với mốc 70–90 trang, trần 100 theo khuôn B. Không tăng độ dài theo mẫu: phần dài của hai mẫu là sơ đồ và đặc tả use case, đề tài này không có.
  - Không dùng nguyên khuôn của mẫu tiếng Anh (dòng đơn, lề trên 1,5 cm) vì thuộc chương trình khác và lề trên quá hẹp.
  - Việc soát văn phong theo luận văn mẫu thu hẹp lại: không khảo sát thêm 4–6 luận văn bên ngoài trước M4. Hai mẫu cho biết mức GVHD chấp nhận, và văn của chúng không chặt hơn quy tắc hiện có, nên quy tắc văn phong giữ nguyên.
- **Results:**
  - Mẫu tiếng Việt: 125 trang, khổ Letter; Times New Roman 13 pt; khoảng dòng trung vị 17,5 pt (khoảng 1,17 lần dòng đơn), thêm 7,5 pt giữa hai đoạn; thụt đầu dòng 1,27 cm; lề trái 3 cm, phải 2 cm; chú thích hình và bảng 13 pt nghiêng, căn giữa, đặt dưới; 8 chương, chương 2–7 kết bằng mục "Kết luận"; trung vị 521 chữ trên trang chỉ có chữ. Thân bài 113 trang, trong đó chương phân tích và thiết kế 65 trang.
  - Mẫu tiếng Anh: 89 trang, A4, 13 pt dòng đơn, cách 6 pt trước và sau đoạn, lề trên/dưới/trái/phải 1,5/1,7/3,5/2 cm; 5 chương, thân bài 74 trang, chương phân tích và thiết kế 42 trang; 55 ảnh, 35 bảng.
  - Kiểm cách giả lập: áp khuôn của mẫu tiếng Anh lên chính file đó, vị trí các chương lệch bản gốc không quá 0,6 trang trên 89 trang.
  - Bản đọc gộp, chương 1–6 (gồm cả khung chưa viết): khuôn B 41,24 trang, khuôn T 27,67 trang; B dài gấp 1,49 lần T (từng chương 1,41–1,57). Mục 3.1–3.5: Typst cho 9,54 trang khuôn B, Word cho 11,97 trang (Typst thấp hơn khoảng 20%). Suy ra 1 trang khuôn B cũ bằng khoảng 0,85 trang khuôn T.
  - `lychee --offline --include-fragments` trên 4 file đã sửa: 94 link, 0 lỗi.
  - `/code-review high` trên diff: 6 điểm (2 quan trọng: khoảng trang chương 4 và 5 không khớp quy tắc nhân 0,85 rồi làm tròn, nay là 19–22 và 14–17, cộng 63–75 trang; số chữ mỗi trang chỗ ghi 450, chỗ ghi 500), đã sửa cả 6.
- **Incidents:** script Word lần đầu lỗi ở lệnh `Quit(0)` (COM trong PowerShell đòi tham số `[ref]`) và để lại một tiến trình Word chạy ngầm; số liệu của cả 6 lượt đo đã ghi đủ, tiến trình được tắt. Lần chạy sau, PowerShell trải phẳng mảng một phần tử nên đường dẫn file sai; sửa bằng `,@(...)`.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §2); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§11.1); `docs/adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md`; `docs/luan-van/README.md`.
- **Thesis:** bước định dạng (file `--reference-doc` theo khuôn T); căn cứ về độ dài khi hội đồng hỏi.

## 2026-11-24 – Luận văn: thêm phần Mở đầu, bỏ trang Lời cam đoan

- **Task:** TR8 · **Environment:** none
- **Done:** thêm phần Mở đầu vào thứ tự các phần của quyển (quy tắc viết §1) và vào bảng "mỗi chương nói gì" (§2); thêm dòng Mở đầu vào bảng dàn ý, bỏ mục 1.4 "Cấu trúc luận văn" khỏi chương 1 (Kế hoạch §11.1); cập nhật bảng nguồn tư liệu cho Mở đầu và chương 1. Bỏ trang Lời cam đoan khỏi phần đầu quyển; chuyển khai báo dùng công cụ AI sang đoạn cuối của Mở đầu (quy tắc viết §1, §3.5, §9; Kế hoạch §11.1).
- **Decision:**
  - Trình đề nghị giữ phần Mở đầu để dẫn dắt và mô tả nhanh từng chương, thay cho lựa chọn "không có Mở đầu" ở mục trước. Lý do: đây là thông lệ của đồ án hệ chính quy, mẫu tiếng Việt của khoa có phần này, và hội đồng đọc nó trước để nắm bức tranh chung. Để không lặp với chương 1, hai phần chia vai trò: Mở đầu (không đánh số, 1,5–2 trang) dẫn dắt ở mức người không chuyên và mô tả ngắn từng chương, không có số đo hay chi tiết kỹ thuật; chương 1 giữ bối cảnh, mục tiêu, phạm vi, phương pháp và đóng góp kèm số, còn 3–4 trang. Tóm tắt vẫn giữ vì nêu kết quả kèm số.
  - Trình đề nghị bỏ trang Lời cam đoan vì hai mẫu không có. Lời khai báo dùng công cụ AI vẫn giữ, vì dự án dùng công cụ AI cho cả viết mã, phân tích số liệu và soạn văn bản. Khai báo đặt ở đoạn cuối của Mở đầu: hội đồng đọc phần này trước, nên khai báo không bị khuất như khi để ở phụ lục, và chương 1–6 vẫn không nhắc tới công cụ AI. Nếu GVHD hoặc khoa quy định chỗ khai báo khác thì chuyển sang đó.
- **Results:**
  - Cộng các khoảng trang của chương 1–6 trong bảng dàn ý được 62–74 trang; định hướng chung giữ 60–75 trang thân bài khuôn T, trần 85. Mở đầu (1,5–2 trang) không tính vào thân bài.
  - `/code-review high` trên diff: 6 điểm nhỏ (Mở đầu chưa rõ có tính vào thân bài không, chưa có tên file nên lệnh ghép có thể bỏ sót, chưa có trong thứ tự viết và bảng phân công, ý lý do cũ mâu thuẫn, §3.5 chưa ghi ngoại lệ cho đoạn khai báo), đã sửa cả 6.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §2, §3.5, §9); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§5.1, §11.1); `docs/luan-van/nguon-tu-lieu.md`; `docs/luan-van/README.md` (tên file `00-00-mo-dau.md`).
- **Thesis:** phần Mở đầu; mục 1.4 cũ không còn.

## 2026-11-24 – Luận văn: bỏ trang Tóm tắt và đoạn khai báo dùng công cụ AI

- **Task:** TR8 · **Environment:** none
- **Done:** bỏ trang Tóm tắt khỏi phần đầu quyển và khỏi thứ tự viết; bỏ đoạn khai báo dùng công cụ AI ở cuối Mở đầu (quy tắc viết §1, §3.5, §9; Kế hoạch §5.1, §11.1). Sửa dòng Mở đầu ở bảng §5.1 thành "cùng soát".
- **Decision:**
  - Trình chọn bỏ trang Tóm tắt vì hai mẫu không có. Khi đã có Mở đầu, Tóm tắt thành phần tóm lược thứ ba cùng với Mở đầu và mục 1.3; 2–3 kết quả chính kèm số vẫn nằm ở mục 1.3.
  - Trình chọn không đưa đoạn khai báo dùng công cụ AI vào luận văn: hai mẫu không có, và nhóm chưa thấy quy định nào của trường. Câu mẫu giữ ở quy tắc viết §9, để thêm vào cuối Mở đầu nếu GVHD hoặc khoa yêu cầu.
  - Bảng §5.1 ghi người sở hữu tính năng để soát nội dung, còn bản base của mọi phần do Trình viết (từ 22/11). Dòng Mở đầu ghi ở PR #72 là "Quang, toàn phần", nay sửa thành cả hai cùng soát, vì Mở đầu tóm lược mọi chương.
- **Results:** `/code-review high` trên diff: 5 điểm nhỏ (§3.5 và §9 nói khác nhau về chỗ ghi việc dùng AI; quy tắc "kết quả cụ thể có số" của Tóm tắt chưa chuyển sang mục 1.3; §1 chưa ghi chỗ đặt đoạn khai báo nếu được yêu cầu; "khuôn T" ở §5.1 chưa có link; thiếu dòng Thesis), đã sửa cả 5.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §3.5, §9); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§5.1, §11.1).
- **Thesis:** phần đầu quyển (không có Tóm tắt, không có Lời cam đoan); Mở đầu; mục 1.3 Đóng góp.

## 2026-11-26 – Luận văn: chương 5 bước 1, merge main và đổi đề mục theo D101

- **Task:** TR8 · **Environment:** none
- **Done:** trên nhánh `docs/tr8-thesis-ch5-drafts`: merge `origin/main` (xung đột ở Kế hoạch §11.1 lấy bản main, đoạn "Độ dài" thay "Cân đối"; xung đột ở `nguon-tu-lieu.md` lấy bản main theo đề mục mới, giữ lại con trỏ tới bảng từng lượt VH4, VH6 ở commit `bc49ff6`). Đổi đề mục 5.3: TĐ1 (GPU utilization so với tải đồng thời) lên 5.3.1, tải ổn định 5.3.2, tải tăng đột ngột 5.3.3; Bảng 5.3a ở đoạn dẫn. 5.5 gom 7 tiểu mục thành 3 theo N4 (VH1 kèm pha giảm tải KB2 chuyển từ 5.3, VH2, graceful shutdown), N6 (VH3, VH4, VH5), N7 (VH6). Thêm `05-00-danh-gia.md` với đoạn mở chương kèm số chính. Sửa dẫn chéo §5.5.x trong comment của 5.7.
- **Decision:** D124: bảng 5.3a đặt trước 5.3.1 vì phục vụ cả ba tiểu mục; tiêu đề 5.5.x không mang mã VH (quy-tac-viet §2), mã nằm trong câu chủ đề.
- **Results:** `kiem_van.py` 0 điểm cần xem ở 05-00, 05-02 tới 05-07; 05-01 còn 1 điểm "ngày tháng §5" có chủ ý (ngày phiên đo nêu một lần ở 5.1). lychee trên `docs/luan-van/*.md`: 0 lỗi. Chưa đo số trang (để bước 2, sau khi khôi phục phần lõi).
- **Deviations:** nội dung 5.5 chưa theo ADR-007 (PR #75: VH1 lấy từ V2, VH2 qua Git trên kind ở PR #78, N8 ở PR #76), vì các PR đó chưa merge; sửa ở bước 2.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts`; `docs/luan-van/05-00-danh-gia.md`, `05-03-autoscaling-so-voi-tinh.md`, `05-05-kich-ban-van-hanh.md`.
- **Thesis:** chương 5.

## 2026-11-27 – Luận văn: chương 5 bước 2a, đưa ADR-007, VH2 qua Git và N8 vào 5.5–5.7

- **Task:** TR8 · **Environment:** none
- **Done:** trên nhánh `docs/tr8-thesis-ch5-drafts`, sửa 5.5 theo ADR-007 (PR #75): đoạn mở mục nêu phần nào chạy trên simulator và vì sao; 5.5.1 ghi VH1 lấy từ pha giảm tải của 3 lượt A2 × KB2, không phải lượt riêng; thêm vế chưa có bằng chứng `LLMPodPending` kêu ở ca kẹt Pending (`for: 10m` so với khoảng 300 s chờ); thêm đoạn kết quả vòng Git trên simulator (PR #78), phần cách làm dẫn sang 4.5 để không lặp; thời gian pod cũ giữ GPU trên V2 ghi "chưa đo". 5.5.2 thêm N8 trên simulator (PR #76). 5.5.3 nêu rõ LT8 và VH6 cùng mốc tính. 5.6: dòng F3, N8 và đoạn "phần còn thiếu" theo kết quả mới. 5.7: thêm đoạn hạn chế của phép đo trên simulator (không cold start, commit không qua PR và CI, người dựng lại đã quen hệ thống).
- **Decision:** D125: bằng chứng VH1 chỉ gồm 3 lượt A2 × KB2. Hai lượt A1 × KB2 giữ 4 replica suốt pha giảm (`scale_downs` 0), nên không kiểm được scale-down. F3 chuyển sang "Đạt" (vòng Git kiểm trên simulator theo ADR-007 D2), N8 sang "Đạt một phần" (còn thiếu chi phí).
- **Results:** `analysis/figures/v2-dg2/runs.csv`: 5 lượt KB2 của A1, A2; chỉ 3 lượt A2 có `scale_downs` = 3. Đo khuôn T bằng Word (pandoc → `do_trang_word_T.ps1`): chương 5 = 11,3 tr (5.1 0,8; 5.2 1,0; 5.3 2,1; 5.4 1,1; 5.5 3,0; 5.6 1,9; 5.7 + kết chương 1,0), chưa tính Hình 5.3b, dưới định hướng 14–17 tr. `kiem_van.py` 0 điểm cần xem ở 05-05, 05-06, 05-07. lychee `docs/luan-van/*.md` 0 lỗi.
- **Deviations:** số và khẳng định trong các đoạn sửa dẫn từ nhánh của PR #75, #76, #78 (chưa merge); phần sửa chưa qua soát số độc lập (để bước 3).
- **Links:** `docs/luan-van/05-05-kich-ban-van-hanh.md`, `05-06-bang-nghiem-thu.md`, `05-07-han-che-phep-do.md`.
- **Thesis:** 5.5, 5.6, 5.7.
