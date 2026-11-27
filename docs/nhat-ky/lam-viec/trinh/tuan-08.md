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

## 2026-11-27 – Phụ lục A–C: manifest chính, quy tắc cảnh báo, runbook mẫu

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Viết `docs/luan-van/phu-luc/a-manifest-chinh.md`: trích Deployment vLLM, overlay VM thuê, ScaledObject A2, Application gốc của Argo CD, bảng tám Application con; mỗi đoạn ghi đường dẫn file và commit.
  - Viết `b-quy-tac-canh-bao.md`: quy tắc ghi `llm:ttft_bad_ratio:rate5m`, bảng bảy cảnh báo (mức, `for`, điều kiện), quy tắc `LLMSLOBurnFast` đầy đủ, unit test đầu tiên của nó kèm cách đọc bốn thời điểm kiểm.
  - Viết `c-runbook-mau.md`: runbook `LLMSLOBurnFast`, bỏ dẫn chiếu tới tài liệu thiết kế.
  - Thêm dòng `phu-luc/` vào bảng tổ chức file của `docs/luan-van/README.md`.
- **Decision:** Trình chọn mỗi phụ lục một file trong `phu-luc/`, đánh số theo chữ (A.1, Bảng A.1, Đoạn mã A.1), và ghi commit cạnh mỗi trích đoạn vì phụ lục không thuộc thân bài. Phụ lục A thêm Application gốc vì mục 4.1 dẫn tới nó. Lệnh pandoc trong README để phần 2 sửa, vì PR phần đầu quyển đang sửa cùng dòng.
- **Results:** kiem_van còn 1 điểm (đường dẫn `docs/runbooks/` ở Phụ lục C, giữ vì đó là chỗ người đọc tìm runbook); lychee 0 lỗi; pandoc ghép ba file không cảnh báo; `make alerts-test SHELL=bash` đạt (9 test case, 4 + 5 + 7 quy tắc).
- **Deviations:** threshold trong file ScaledObject là 24 (giá trị tạm), phiên V2 dùng 37 do runner ghi đè từ `matrix-v2.yaml`; Phụ lục A ghi rõ điều này.
- **Links:** `docs/luan-van/phu-luc/a-manifest-chinh.md`, `b-quy-tac-canh-bao.md`, `c-runbook-mau.md`; `docs/luan-van/README.md`.
- **Thesis:** Phụ lục A–C; dẫn từ mục 3.5, 4.1, 4.3, 4.6.

## 2026-11-27 – Phụ lục D–F: phiên bản, số từng lượt của V2, kế hoạch và phân công

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Viết `d-phien-ban.md`: hai bảng phiên bản (nền tảng và tầng phục vụ; công cụ kiểm tra) chép từ `docs/phien-ban.md`, bỏ dòng laptop chưa điền và các dòng thân bài không dẫn.
  - Viết `e-so-lieu-tung-luot.md`: 17 lượt ĐG2 (Bảng E.1) kèm Hình C4 (Hình E.1), phản ứng của A2 × KB2 (E.2), mốc vi phạm và page của 7 lượt (E.3), 8 pha cold start của 5 lượt ĐG3 (E.4), 6 kịch bản vận hành (E.5).
  - Viết `f-ke-hoach-phan-cong.md`: mốc M1–M5, điều chỉnh lịch 04/11, bảng Q1–Q8 và TR1–TR8 kèm giờ công ước lượng, người soát từng chương.
  - Sửa lệnh pandoc trong `docs/luan-van/README.md`: thêm `phu-luc/*.md` và thư mục `phu-luc/` vào `--resource-path` (dấu tách `;` trên Windows).
- **Decision:** Trình chọn ghi đường dẫn hình ở phụ lục tương đối với chính file (lychee và GitHub mở được), thêm `phu-luc/` vào `--resource-path` thay vì viết đường dẫn theo thư mục `docs/luan-van/` như các chương. Bảng nghiệm thu đầy đủ, bảng LT1–LT8 và các lượt chạy thử không đưa vào Phụ lục E.
- **Results:** soát số độc lập (agent Opus, khoảng 320 số): 1 lỗi xác nhận (lượt ĐG3 nào được đo lại), 6 điểm nghi vấn, đã sửa cả 7. `/code-review high`: 10 điểm, sửa 9 (gồm câu "người còn lại review PR" trái với quy tắc viết §2.2, dấu tách `--resource-path` trên Windows, "cửa sổ ổn định" không có ở scale-up, đợt page thứ 8 còn sót từ lượt trước); bỏ qua gợi ý ghim mọi trích đoạn theo một tag (để lúc gắn `v1.0`). lychee 0 lỗi; pandoc ghép toàn bộ `[0-9]*.md` + `phu-luc/*.md` nhúng được Hình E.1 (chỉ cảnh báo thiếu rsvg-convert). Chưa đo khuôn T (phụ lục không tính vào thân bài).
- **Deviations:** tên có dấu của Quang ở Phụ lục F suy từ tên Git; mã sinh viên, lớp chưa điền.
- **Links:** `docs/luan-van/phu-luc/d-phien-ban.md`, `e-so-lieu-tung-luot.md`, `f-ke-hoach-phan-cong.md`; `docs/luan-van/README.md`.
- **Thesis:** Phụ lục D–F; dẫn từ mục 1.2, 4.1, 5.3–5.6.
