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
