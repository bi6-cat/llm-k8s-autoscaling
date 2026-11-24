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
## 2026-11-24 – Luận văn: cắt mục 3.1 về 1,5 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge `origin/main` vào nhánh `docs/tr8-thesis-3-1-base` (PR #63) để có ngân sách trang (D94).
  2. Viết lại `03-01-yeu-cau-chi-tieu.md`: 5 bảng còn 1 (F1–F7 và N1–N8 gộp, mỗi dòng một cụm ngắn); bỏ 4 tiểu mục; giá trị SLO và lý do của ngưỡng viết thành văn xuôi.
  3. Ghi các ý đã cắt và nơi chứa chúng vào dòng 3.1 của `nguon-tu-lieu.md`, và vào comment nguồn của mục.
- **Decision:** bảng mã định danh đầy đủ (S, A, KB, ĐG, VH, LT, L, V, C, B\*, N) chuyển khỏi 3.1 sang danh mục mã định danh ở phần đầu quyển (quy-tac-viet §1 mục 4, §4). Thân bài 3.1 chỉ giữ bảng F/N và một câu dẫn tới mục 3.3–3.6, nơi từng mã được định nghĩa. Lý do: bảng mã tốn khoảng 0,8 trang (khuôn B), hơn nửa ngân sách 1,5 trang. Không chọn giữ bảng mã và bỏ bảng F/N, vì F/N là nội dung chính của mục. Ma trận truy vết (Bảng 3.1 cũ) bỏ khỏi thân bài; cột "Phép thử" của bảng F/N vẫn nối mỗi yêu cầu tới phép thử.
- **Results:** đo bằng dàn trang thử (pandoc + Typst, hai khuôn như mục 23/11):

  | Bản | Chữ văn xuôi | Bảng | Khuôn A | Khuôn B |
  |---|---|---|---|---|
  | Base (trước khi cắt) | 1.181 | 5 | 5 trang | 7 trang |
  | Lần thử 1 (giữ bảng mã gọn) | 580 | 2 | 2,43 | 3,25 |
  | Lần thử 2 (trước `/code-review`) | 344 | 1 | 1,16 | 1,49 |
  | Bản cuối (sau khi sửa theo review) | 314 | 1 | 1,17 | 1,44 |

  `kiem_van.py` 0 điểm; lychee `docs/luan-van/*.md` 0 lỗi. `/code-review high`: 10 điểm, sửa cả 10. Phần lớn do nén bảng làm mất điều kiện của chỉ tiêu (pha của N1, "so với S4" của N3, ca 1 replica của N4, điều kiện fallback của N6, mốc tính giờ của N2a). Ngoài ra: lý do ngưỡng TTFT bị đảo so với ADR-005 T3, câu chủ đề "mọi ngưỡng tính từ nền tảng" mâu thuẫn với mức 95% theo thông lệ, "tức …" lồng định nghĩa (quy-tac-viet §3.2). Bỏ lý do TPOT 100 ms (ghi ở `nguon-tu-lieu.md`) để giữ trong 1,5 trang.
- **Deviations:** quy-tac-viet §4 trước ghi "mã định danh định nghĩa ở chương 3, gom vào một bảng"; đã sửa thành: mỗi mã định nghĩa ở mục chương 3 dùng nó, bảng gom nằm ở danh mục đầu quyển. Kế hoạch §11.1 (dòng chương 3) bỏ "truy vết, bảng mã định danh" khỏi 3.1.
- **Links:** `docs/luan-van/03-01-yeu-cau-chi-tieu.md`, `docs/luan-van/nguon-tu-lieu.md` (dòng 3.1), `docs/luan-van/quy-tac-viet.md` §4, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.1; PR #63.
- **Thesis:** §3.1; danh mục mã định danh ở phần đầu quyển lấy từ bảng mã của bản base (commit `fbe651b`).
## 2026-11-24 – Luận văn: bản base mục 3.2 (Kiến trúc tổng thể)

- **Task:** TR8 · **Environment:** none
- **Done:** viết `docs/luan-van/03-02-kien-truc-tong-the.md` theo bố cục 3.2 (ba luồng: request, autoscaling, thay đổi qua Git; hai tầng môi trường dùng chung base Kustomize; bảo vệ tối thiểu). Đối chiếu từng khẳng định với Kiến trúc §1–§5, §18; Môi trường §1, §2.7; Thông số §3, §9, §10; Vận hành §7–§8; ADR-006 §3, §3.1; `envs/home/argocd/apps/`, `Makefile`, `docs/phien-ban.md`. Thêm `argocd-cluster-bootstrapping` (Argo CD v3.5.4) vào `tai-lieu.bib`. Đo trang, cắt, chạy `/code-review high`, sửa, đo lại.
- **Decision:** chèn tạm hình kiến trúc hiện có (Hình 2 của `docs/chi-tiet/`) làm Hình 3.2a để đo trang có tính hình; hình phải vẽ lại trước khi ghép, vì còn ghi giới hạn tốc độ ở Traefik và chưa có Argo CD. Không chèn Hình 6 (còn A4000, A3/A4): Bảng 3.2a thay cho nó. Giữ cách gọi "hai tầng" của Môi trường §1, bảng vẫn tách ba cột (simulator, máy nhà, VM thuê).
- **Results:** bản đầu khoảng 900 chữ (đếm thô bằng `wc`, gồm tiêu đề và chú thích), bản cuối 505 chữ văn xuôi (kiem_van), 1 bảng, 1 hình. Dàn trang thử có chèn hình: bản đầu 2,87 trang (khuôn B), bản cuối 1,65 trang (khuôn A), 1,98 trang (khuôn B). kiem_van 0 điểm; lychee 0 lỗi.
- **Incidents:** `/code-review high` báo 10 điểm, sửa cả 10: đếm sai số lớp bảo vệ còn giữ (là ba lớp, gồm ghim phiên bản, không phải hai); lý do lược bảo mật viết lệch ADR-006 §3.1; thiếu GPU replica ở máy nhà; `make bootstrap` là Ansible, không phải Helm; "ba môi trường" lệch "hai tầng" của nguồn; thiếu điều kiện self-heal; nói quá về simulator; chú thích hình sai khuôn README; ô tiêu đề bảng trống; "Ba đánh giá" chưa được định nghĩa. Script đo `run.sh` dừng khi `31.md` rỗng (`grep` trả mã 1 dưới `set -e`), nên mục 3.2 được đo ở vị trí của `31.md`.
- **Links:** `docs/luan-van/03-02-kien-truc-tong-the.md`, `docs/luan-van/tai-lieu.bib`.
- **Thesis:** §3.2. Việc kéo theo: chương 2 định nghĩa Kustomize base/overlay, App-of-Apps, k3s, time-slicing, external metric; tên đầy đủ Qwen2.5-0.5B/3B-Instruct xuất hiện lần đầu trước 3.2; mục 6.2 nhận ba lớp bảo vệ bị lược.
## 2026-11-24 – Luận văn: bản base mục 3.3 (thiết kế autoscaling) và cắt về 2,5 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Bản base 3.3 (commit `28be408`, 23/11): ba tiểu mục tín hiệu, threshold và hành vi, mất tín hiệu; mỗi đoạn có comment nguồn trỏ về `docs/chi-tiet/`, manifest và tài liệu KEDA 2.21.
  2. Merge `origin/main` (có PR #65, ngân sách trang D94), rồi cắt theo thứ tự quy-tac-viet §3.1: Bảng tín hiệu không chọn còn hai câu (TTFT p95, KV cache); bỏ A3/A4, tolerance, ví dụ 3 B\*; gộp 4 tiểu mục thành 3; Bảng 3.3a bỏ cột "Vai trò", Bảng 3.3b bỏ dòng max, scale-up, tolerance.
  3. `/code-review high` báo 10 điểm, sửa 9 (dưới); điểm "vượt ngân sách" không sửa vì reviewer ước theo chữ, còn số đo dàn trang thử đã đạt.
- **Decision:** ý bị cắt chuyển chỗ: exporter GPU không có label pod sang 4.3; cảnh báo `KedaScalerErrors` sang 3.5; Deployment không đặt `replicas` (Argo CD và HPA) sang 3.2; giới hạn "threshold gắn với phân phối độ dài request" sang mục Hạn chế. Comment nguồn của 3.3 ghi lại từng chỗ và § gốc.
- **Results:** đo bằng `.work/tools/do_trang/run.sh` (citation thay tạm bằng `[1]` vì Typst không có nhãn):

  | Bản | Văn xuôi | Bảng | Khuôn A (13 pt) | Khuôn B (14 pt) |
  |---|---|---|---|---|
  | Base 23/11 | 1.715 chữ | 3 | 5 trang | 6 trang |
  | Sau cắt | 809 chữ | 2 | 1,9 trang | 2,5 trang |

  Trang lẻ ước từ toạ độ dòng chữ thấp nhất trên trang cuối. `kiem_van.py` 0 điểm; lychee 0 lỗi.
- **Incidents:** review phát hiện bản base viết sai cơ chế mất metric: văn cũ nói "giữ mặc định ignoreNullValues", nhưng truy vấn của A1 và A2 kết thúc bằng `or vector(0)` nên không bao giờ rỗng; sửa theo manifest. Các điểm khác đã sửa: thời gian phát hiện 10–25 s (Kiến trúc §6, bảng thứ hai, gồm chờ vượt tolerance) thay cho "tối đa 10 s"; lý do loại TTFT p95 theo Kiến trúc §10.5 (prefill, cửa sổ `rate()` 1 phút) thay cho "giảm ngay sau scale-up", vốn mâu thuẫn với đoạn hàng đợi ở pod cũ; KV cache ghi là dự đoán, chưa kiểm chứng; A1 cộng mọi GPU của node chứ không cộng theo pod; `--max-num-seqs` 64 ghi rõ là máy cloud (nhà 16); fallback ghi "khoảng 20 s theo thiết kế", số đo V2 16,8 s để chương 5; công thức trần đổi sang `$…$` theo README.
- **Links:** `docs/luan-van/03-03-thiet-ke-autoscaling.md`; nhánh `docs/tr8-thesis-3-3-base`.
- **Thesis:** §3.3; Hình 4 (vòng lặp autoscaling) còn ghi model 7–8B và sync 15 s, vẽ lại trước khi chèn.
## 2026-11-24 – Luận văn: bản base mục 3.4 (Cold start và thay đổi an toàn)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Đọc Kiến trúc §3.1, §7, §8; Vận hành §5; Thông số §9.2–§9.3; ADR-005 T1, T2; ADR-006 C8; quy tắc viết §2–§6.
  2. Viết `docs/luan-van/03-04-cold-start-thay-doi-an-toan.md`, ba tiểu mục: rút ngắn cold start (L0, L2), graceful shutdown cho request streaming, rolling update khi mọi GPU đều có pod. Mỗi đoạn có comment nguồn kèm §.
  3. Đối chiếu hai khẳng định với upstream ở phiên bản ghim: trang Pod Lifecycle của Kubernetes (nhánh `release-1.36`, khớp k3s v1.36.5) cho việc gỡ khỏi EndpointSlice chạy song song với preStop, grace period gồm cả preStop; `VllmConfig.shutdown_timeout` trong vLLM v0.31.0 (`vllm/config/vllm.py`, mặc định 0) cho mô tả của cờ `--shutdown-timeout`. Thêm hai mục vào `tai-lieu.bib`.
  4. Đo trang, cắt ba lần về ngân sách; `kiem_van.py`, lychee; `/code-review high`.
- **Decision:**
  - Bỏ bảng L0/L2 ba dòng, viết thành hai câu: bảng chiếm khoảng 0,3 trang, văn xuôi nói cùng ý trong khoảng 40 chữ.
  - Không chèn hình (Hình 12, 13, 16 của tài liệu thiết kế) để giữ ngân sách 1,5 trang. Hình 13 còn vẽ pha "drain" mà vLLM v0.31.0 không làm, phải sửa trước khi dùng ở 4.5.
  - Điểm lệch của `--shutdown-timeout` chỉ nêu một câu kèm dẫn chéo tới 4.5, vì người đọc thiết kế cần biết grace period mới là thứ giữ request; số đo để 4.5 và 5.5.
  - Bỏ khỏi thân bài, ghi trong comment nơi nên đặt: mức L1, `--enforce-eager`, startup probe 10 phút, sync window, `kubectl rollout undo`.
- **Results:** dàn thử 24/11: 1,15 trang (khuôn A), 1,49 trang (khuôn B), ngân sách 1,5; khoảng 550 chữ văn xuôi, không bảng, không hình. Lần viết đầu 2,31 trang (B). `kiem_van.py` 0 điểm; lychee 0 lỗi. `/code-review high` báo 10 điểm, sửa 9: đếm pha sai (KV cache và CUDA graph cùng pha 7 với compile), thiếu bước nạp weights, rollback phải giữ `minReplicaCount` 2, pod giữ GPU đủ 180 s chứ không phải "tới 180 s", thiếu trích dẫn, số replica tối thiểu khác nhau theo môi trường, thuật ngữ warm pool, ngoặc `{}` trong bib, thiếu nhật ký. Không sửa điểm "đoạn mở mục 3 câu": quy tắc viết §2 cho 1–2 câu, nhưng §3.2 và `kiem_van.py` đòi đoạn 3–7 câu; giữ 3 câu như mục 3.2.
- **Links:** `docs/luan-van/03-04-cold-start-thay-doi-an-toan.md`, `docs/luan-van/tai-lieu.bib`.
- **Thesis:** §3.4. Việc kéo theo: chương 2 định nghĩa probe, EndpointSlice, preStop, SIGTERM/SIGKILL, grace period, torch.compile, CUDA graph, maxSurge/maxUnavailable; 4.5 nhận chi tiết điểm lệch của `--shutdown-timeout`; 5.3 tính phần GPU-giờ do grace 180 s.
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

## 2026-11-25 – Luận văn: gom chương 3 vào một nhánh, đổi đề mục theo dàn ý mới (bước 1)

- **Task:** TR8 · **Environment:** none
- **Done:** tạo nhánh `docs/tr8-thesis-ch3` từ `origin/main`; merge 6 nhánh mục (#63 3.1, #67 3.2, #66 3.3, #68 3.4, #62 3.5, #64 3.6), giữ lịch sử và các mục nhật ký 23–24/11 vốn chỉ nằm trên các nhánh đó. Đổi đề mục theo Kế hoạch §11.1: 3.2.3 "Bảo vệ tối thiểu" thành đoạn cuối của 3.2.1 "Thành phần và ba luồng"; 3.4.3 gộp vào 3.4.2 "Tắt pod và cập nhật không rớt request"; 3.5.2 gộp vào 3.5.1 "SLI và cảnh báo theo burn rate", 3.5.3 thành 3.5.2 "Định tuyến cảnh báo, runbook và người trực"; 3.6.2, 3.6.3 đổi tên. Khôi phục phần lõi đã cắt ngày 24/11 ở 3.3 (ba câu hỏi thiết kế, bảng tín hiệu không chọn, điểm yếu của tín hiệu A2, lý do hệ số 0,8, dòng max = N, lý do timeout 1 s, dẫn chéo `KedaScalerErrors`, lấy từ bản base 28be408) và 3.4 (bảng L0/L2 ba dòng, lý do không đo L1, không dùng `--enforce-eager`, startup probe 10 phút, không dùng sync window). Thêm `03-00-yeu-cau-thiet-ke.md`: tiêu đề chương và đoạn mở nêu các lựa chọn thiết kế chính (quy tắc viết §2).
- **Decision:** D118. Gom bằng merge thay vì chép file, để giữ nhật ký của từng PR mục. Xung đột Kế hoạch §11.1 lấy bản main (dàn ý mới); `tai-lieu.bib` giữ cả hai mục; `nguon-tu-lieu.md` giữ dòng mới của cả hai phía, dòng 4.6.x theo đề mục của main. Khôi phục có chọn lọc: chỉ lý do thiết kế và phương án bỏ, không khôi phục phần đã có chỗ ở chương 4, 5 hay phụ lục. Câu "triển khai qua Git chỉ được kiểm ở cluster nhà" ở 3.2 chưa sửa, chờ PR #75 và #78 được duyệt (ghi comment trong file).
- **Results:** văn xuôi theo `kiem_van.py`: 03-00 153 chữ, 3.2 522, 3.3 998 (trước 24/11 cắt còn ≈ 830), 3.4 668, 3.5 681, 3.6 670; 0 điểm cần xem ở cả 6 file đã sửa. `lychee --offline --include-fragments 'docs/luan-van/*.md'`: 0 lỗi. Chưa đo trang khuôn T.
- **Incidents:** khi chèn comment "Chờ PR #75" vào giữa đoạn cuối 3.2.2, phần sau comment bị tách khỏi đoạn; đã đưa comment xuống sau đoạn.
- **Deviations:** 3.2 (522 chữ) và 3.4 (668 chữ) dưới mức 1.000 chữ mà quy tắc viết §2 đặt cho việc chia cấp 3; vẫn giữ hai tiểu mục theo dàn ý §11.1, xem lại khi đo khuôn T ở bước 2.
- **Links:** nhánh `docs/tr8-thesis-ch3` (chưa PR); `docs/luan-van/03-00-yeu-cau-thiet-ke.md`, `03-02`…`03-06`.
- **Thesis:** chương 3. Còn lại cho bước 2: khôi phục phần lõi 3.1, 3.5, 3.6; kết chương; đánh lại số bảng; đo khuôn T (13–15 tr); `/code-review high`; PR; đóng #62–#64, #66–#68.
