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

## 2026-11-23 – TR8: bản base mục 3.6 (thiết kế đánh giá)

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Trình (viết cùng agent, lượt tự chạy) viết bản base `docs/luan-van/03-06-thiet-ke-danh-gia.md` theo dàn ý ở Kế hoạch §11.1. Bản này có 7 tiểu mục và 7 bảng:
    - ba lớp đánh giá;
    - tải và kịch bản tải;
    - ĐG1–ĐG3;
    - chỉ số theo đề cương và quy tắc so sánh;
    - điều kiện hợp lệ của một lượt;
    - VH1–VH6 và cách chấm cảnh báo;
    - LT1–LT8.
  - Phần "Cách đo" của VH6 (mốc vi phạm, page giả, thời gian tới cảnh báo) được viết ở 3.6.6 theo dàn ý. Nhánh nháp chương 5 không bị sửa.
  - Mọi đoạn và bảng có số đều kèm comment nguồn: § của `docs/chi-tiet/`, mã nguồn `analysis/` và `experiments/runner/`, nhật ký vận hành.
- **Decision:**
  - Không chèn Hình 8 và Hình 17, vì Hình 8 còn thời lượng cũ 20/25/25 phút và Hình 17 còn Argo CD trên VM thuê. Bảng 3.6b và 3.6c dùng thay. Hai hình phải vẽ lại trước khi chèn.
  - Số bảng tạm là 3.6a–3.6g, vì mục 3.2–3.4 chưa viết.
  - ĐG3 viết "khi thêm một replica" thay cho "scale 1 → 2" của thiết kế. Lý do: ở V2, mức L0 được đo 0 → 1 vì containerd không xoá được image đang dùng (`van-hanh.md` 19/11), và LT4 ở nhà cũng đo 0 → 1. Mục 5.4 sẽ ghi lệch này; comment nguồn của 3.6 đã nhắc.
  - Phần LT không khẳng định mọi dự đoán đều tính trước khi đo. Theo `van-hanh.md`, dự đoán của LT4 được tính sau khi đã có số đo lần A, nên 3.6 ghi rằng chương 5 nêu rõ các ca như vậy.
  - Không ghi công cụ cụ thể của ĐG1 ở V2, vì chưa đối chiếu được.
- **Results:**
  - `kiem_van.py`: 2.305 chữ văn xuôi, 31 đoạn, 111 câu, 0 điểm cần xem.
  - lychee 0.24.2 (offline, kèm anchor): 0 lỗi. Pandoc ghép thử `docs/luan-van/[0-9]*.md` ra `.docx` được.
  - `/code-review high` báo 10 điểm. Từng điểm được đối chiếu với mã nguồn, git log và nhật ký, và cả 10 đã được sửa:
    - lý do bỏ S1 × KB1 ghi sai thành "autoscaling chạy 1 replica", trong khi A1 scale lên ở KB1 (đúng là A2);
    - "không thể chỉnh theo kết quả" nói quá, vì `analysis/dg2_a2.py` và `vh6_window.py` được thêm ngày 21/11, sau V2; chỉ `metrics.py` (sửa lần cuối 16/11) được chốt trước;
    - ĐG3 1 → 2 khác với cách đo L0 ở V2;
    - định nghĩa thời gian hồi phục SLO chưa khớp `metrics.slo_recovery_s`;
    - phân vị chỉ tính trên request thành công;
    - VH6: độ kịp chỉ chấm ở S1 × KB3;
    - lý do 10 phút của pha tăng đột ngột là cold start đo ngày 08/11, không phải flapping;
    - TTFT/TPOT ánh xạ sai sang P95/P99 của đề cương;
    - chỉ độ lệch lịch gửi, event loop và CPU được chấm theo từng tiến trình;
    - kiểm thử chức năng chỉ chạy trong CI ở phần tự động hoá được.
- **Deviations:** 2.305 chữ văn xuôi, vượt ngân sách chương 3 (10–12 trang cho 6 mục; 3.1 và 3.5 đã khoảng 2.650 chữ). Ba chỗ cắt được: đoạn quy ước tính (chuyển sang 5.1), chi tiết reset, làm ấm và cooldown (sang 4.7), đoạn ca đối chứng (sang 5.5).
- **Links:** PR #64; `docs/luan-van/03-06-thiet-ke-danh-gia.md`.
- **Thesis:** 3.6; dẫn chéo từ 3.1 (mục 3.6), 4.7 (runner kiểm tính hợp lệ), 5.1–5.5.
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

## 2026-11-24 – Luận văn: cắt mục 3.6 về 2 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge `origin/main` vào nhánh `docs/tr8-thesis-3-6-base` để có ngân sách trang (PR #65, D94).
  2. Viết lại 3.6 theo thứ tự cắt của `quy-tac-viet.md` §3.1: bảy bảng còn một (Bảng 3.6a, ba kịch bản tải); ĐG, VH, LT, chỉ số, quy tắc so sánh, điều kiện hợp lệ và cách chấm cảnh báo viết thành văn xuôi ngắn, mỗi đoạn kèm comment nguồn.
  3. Ghi vào dòng 3.6 của `nguon-tu-lieu.md` từng ý đã chuyển ra và nơi chứa nó (`docs/chi-tiet/`, mục 4.7, chương 5, Phụ lục E).
  4. Chạy `/code-review high` trên diff, sửa 10/10 lỗi được báo, rồi cắt lại cho vừa 2 trang.
- **Decision:**
  - Bỏ bảng VH1–VH6 và LT1–LT8 khỏi thân bài: 3.6 chỉ cần nêu có phép thử nào và đạt khi nào; cách làm và kết quả từng VH, LT thuộc 5.2–5.5. Bảng ma trận 17 lượt, bảng chỉ số, bảng điều kiện hợp lệ cũng bỏ, vì dưới 3 cột thông tin riêng hoặc trùng văn xuôi (§6).
  - Không định nghĩa lại C, B\* và threshold 0,8 B\*, vì mục 3.3 đã định nghĩa; 3.6 chỉ dẫn chéo.
  - Giữ trong thân bài các định nghĩa mà 3.1 trỏ tới: KB, ĐG, VH, LT, page giả, pha ổn định của KB1 (D95).
  - Theo review: nêu rõ seed theo kịch bản và lần lặp, mọi lượt ĐG2 ở mức ấm, "đỉnh 3,0 C cần vừa đủ 4 replica" là ước tính của 3.3, thời gian tới cảnh báo chấm ở S1 × KB3, page giả chỉ chấm ở A2 × KB1 và A2 × KB3.
- **Results:** đo bằng dàn trang thử (khuôn A 13 pt, khuôn B 14 pt; đạt khi khuôn B ≤ 2 trang):

  | Bản | Chữ văn xuôi | Bảng | Khuôn A | Khuôn B |
  |---|---|---|---|---|
  | Base 23/11 | 2.305 | 7 | 10 | 13 |
  | Lần cắt 1 | khoảng 1.580 | 3 | 3,04 | 4,05 |
  | Lần cắt 2 | khoảng 900 | 2 | 2,00 | 2,76 |
  | Lần cắt 3 | khoảng 720 | 1 | 1,65 | 2,14 |
  | Sau review, cắt lại | 670 | 1 | 1,63 | 1,99 |

  `kiem_van.py`: 0 điểm cần xem (37 câu, trung bình 18,1 chữ/câu). `lychee --offline --include-fragments 'docs/luan-van/*.md'`: 0 lỗi.
- **Incidents:** sau khi sửa theo review, bản tăng lên 2,14 trang và một đoạn có 5 mã (quá 4, §4). Đã bỏ mã L2 ở câu ĐG2 (thay bằng "mức ấm, mục 3.4"), bỏ câu "hai lượt chỉ khác nhau ở cấu hình" (câu seed ở 3.6.1 đã nói), và rút các dòng cuối đoạn chỉ có 1–2 chữ.
- **Deviations:** ý "LT chạy được ở máy nhà và simulator" và ca đối chứng VH2 không còn trong 3.6; đã ghi nơi chứa ở `nguon-tu-lieu.md`. Chương 5.5 phải nhắc ca đối chứng khi trình bày VH2.
- **Links:** PR #64; `docs/luan-van/03-06-thiet-ke-danh-gia.md`, `docs/luan-van/nguon-tu-lieu.md`.
- **Thesis:** 3.6; dẫn chéo từ 3.1, 3.3; các ý chuyển ra đi vào 4.7, 5.1–5.5, Phụ lục E.
