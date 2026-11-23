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

## 2026-11-23 – Luận văn: viết lại mục 3.5 thành mẫu văn

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết lại `docs/luan-van/03-05-giam-sat-slo-canh-bao.md` theo bố cục mới (Kế hoạch §11.1) và `quy-tac-viet.md`: tiêu đề "Thiết kế giám sát, cảnh báo và xử lý sự cố"; bốn tiểu mục SLI và dashboard, cảnh báo theo burn rate, danh sách cảnh báo và định tuyến, xử lý sự cố và vai trò người trực (mới, theo Vận hành §4, §6 và runbook `LLMSLOBurnFast`). Comment thông điệp và trạng thái soát ở đầu file.
  2. Đối chiếu lại số với `docs/chi-tiet/00-thong-so.md` §3, §4, §6; `04-van-hanh.md` §2.1, §2.2, §3.1–§3.5, §4, §6; `03-kien-truc-autoscaling.md` §13.4; `llm.yaml`, `slo.yaml`, `alertmanager-values.yaml`, `scaledobject-a2.yaml`, ba dashboard.
  3. Bản viết đầu còn 1.854 chữ văn xuôi, nên rút tiếp còn 1.367 chữ. Chạy `/code-review high`, sửa 10 điểm, bản cuối 1.464 chữ.
  4. Cập nhật `nguon-tu-lieu.md` (dòng 2.5, 3.3, 3.5, 4.6, 6.2) để ghi phần đã chuyển ra khỏi 3.5.
- **Decision:** Bản cũ có 2.407 chữ, trong khi trần của cả chương 3 (6 mục) là 3.000–3.600 chữ, nên chỉ giữ những gì phục vụ ba thông điệp của mục. Chuyển sang 4.6: bảng nguồn metric và chu kỳ scrape, retention, NaN khi không có traffic, chuyện chọn lại tín hiệu `KedaScalerErrors`, khuôn tin Telegram. Chuyển sang 6.2 (3.5 chỉ dẫn chéo): điểm yếu `LLMErrorRateHigh`, chưa có dead man's switch. Chuyển sang 3.1: cột giá trị SLO. Chuyển sang 2.5: định nghĩa SLI, SLO, burn rate, vai trò hai cửa sổ, vì sao không dùng ngưỡng p95. Bảng định tuyến chuyển thành văn xuôi. Thân bài không còn mã F/N. Giữ công thức ước tính thời gian báo (dự đoán LT8) ở 3.5.2, vì đó là lý do chọn cặp cửa sổ 5 phút và 1 phút. Giữ tên file để không phải sửa link. Chưa chèn Hình 7, vì hình còn lệch 6 điểm (nhật ký 18/11). Phương án bỏ: chỉ sửa lỗi văn phong của bản cũ (vượt xa ngân sách); cắt còn khoảng 600 chữ (mất phần ước tính và vai trò người trực mà bố cục yêu cầu).
- **Results:** `kiem_van.py`: bản cũ 50 điểm, bản mới 0 điểm (1.464 chữ, 19 đoạn, 71 câu, trung bình 20,6 chữ/câu). `lychee --offline --include-fragments` trên `docs/luan-van/*.md`: 0 lỗi. `pandoc … --citeproc` ra `.docx`: không lỗi, không cảnh báo trích dẫn.
- **Incidents:** `/code-review high` xác nhận 10 điểm, đã sửa cả 10:
  - câu "đã kiểm hai biên 2,5 s và 0,1 s trên `/metrics`" không có nguồn cho biên 0,1 s;
  - mất câu đánh đổi "cửa sổ ngắn nhạy hơn với đợt xấu ngắn", trong khi thông điệp nói "đợt chậm ngắn không page";
  - mất ý tin "đã hết" tới muộn tới 5 phút (`group_interval`);
  - câu "`KedaScalerErrors` page sau 1 phút" đánh giá thấp độ trễ;
  - mốc 20% của cảnh báo và của page giả đo từ hai nguồn khác nhau nhưng không nói ra;
  - câu "dashboard cho cùng một số" không đúng với panel TPOT và panel ngân sách lỗi;
  - con số 12 phút xuất hiện trước công thức dùng để tính nó;
  - các khái niệm 3.5 dùng thẳng chưa được giao cho chương 2;
  - phần chuyển sang 4.6 và 3.3 chưa được ghi lại ở nguồn tư liệu.
- **Links:** nhánh `docs/tr8-thesis-3-5-sample`; `docs/luan-van/03-05-giam-sat-slo-canh-bao.md`, `docs/luan-van/nguon-tu-lieu.md`.
- **Thesis:** §3.5 (mẫu văn, chờ Trình duyệt trước khi viết các mục khác của chương 3).
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

## 2026-11-24 – Luận văn: cắt mục 3.5 (mẫu văn) về 2 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge `origin/main` vào nhánh `docs/tr8-thesis-3-5-sample` (PR #62) để có ngân sách trang và thứ tự cắt trong `quy-tac-viet.md`.
  2. Cắt `03-05-giam-sat-slo-canh-bao.md` theo thứ tự §3.1: bảng SLI thành văn xuôi; gộp 3.5.3 và 3.5.4; bảng cảnh báo bỏ cột "Lý do", còn lại hai lý do không hiển nhiên ở văn xuôi; công thức thời gian báo đưa vào câu. Những ý đã bỏ được ghi ở comment đầu file, kèm nơi còn giữ chúng (`docs/chi-tiet/04-van-hanh.md` §2.1, §3.2, §3.5, §4; mục 3.3; mục 4.6; mục 6.2; chương 5).
  3. Đo sau mỗi lượt cắt bằng dàn trang thử, rồi xem ảnh trang cuối để biết dòng nào bị tràn.
  4. Chạy `/code-review high`: 10 điểm, sửa 8.
- **Decision:**
  - Bỏ cột "Lý do" thay vì cắt thêm văn xuôi. Đo riêng bảng: 5 cột chiếm 0,61 trang (khuôn B), 4 cột 0,33 trang.
  - Định nghĩa page/ticket đặt trong chú thích Bảng 3.5a, vì dàn ý chương 2 ở Kế hoạch §11.1 chưa có hai thuật ngữ này.
  - Hai điểm yếu đã biết chuyển sang mục 6.2 (Hạn chế): một đợt lỗi 503 ngắn vẫn gây page, và `Watchdog` chưa được nối ra ngoài. Mục 6.2 phải nhắc lại hai điểm này.
  - Bỏ ý "mất metric nguồn thì kết quả là 0", vì mục 3.3 (PR #66) đã trình bày đúng cơ chế `or vector(0)`.
- **Results:** văn xuôi giảm từ 1.523 xuống khoảng 700 chữ; số bảng từ 2 xuống 1. Đo được 1,62 trang (khuôn A, 13 pt) và 1,97 trang (khuôn B, 14 pt), trước khi cắt là 3,63 và 4,88. Phần trang lẻ = (y thấp nhất trên trang cuối − lề trên) ÷ chiều cao vùng in. Cách đo cho lại đúng số của 3.3 ở vòng trước: 1,90 và 2,52. `kiem_van.py` báo 0 điểm; lychee không báo lỗi ở `docs/luan-van/`.
- **Incidents:**
  - Code review ra 10 điểm, 8 điểm đã sửa:
    - văn bản chưa nói TPOT vẫn được xét khi nghiệm thu;
    - con số 12 phút xuất hiện trước khi nêu ngưỡng;
    - lý do rút cửa sổ lệch với tài liệu nguồn (lượt đánh giá 12–24 phút);
    - thiếu lưu ý về 20 s trễ scrape và tính rule;
    - sau bảng không có câu nhận xét (quy-tac-viet §6);
    - thiếu ánh xạ 7 quy tắc ↔ 6 cảnh báo;
    - page/ticket chưa được định nghĩa;
    - header dẫn mã quyết định riêng và nguồn tên dashboard sai.

    Hai điểm còn lại không cần sửa: ý "mất metric thành 0" đã có ở 3.3; nhật ký được ghi ở mục này.
- **Links:** PR #62; `docs/luan-van/03-05-giam-sat-slo-canh-bao.md`.
- **Thesis:** §3.5. Mục 6.2 phải có hai điểm yếu nêu trên. Hình 7 (vòng vận hành, PR #60) mà chèn vào 3.5.3 thì phải bỏ bớt câu ở đoạn tự xử lý sự cố.
