<!-- Mục đích: mục 5.3, autoscaling so với cấu hình tĩnh (ĐG2, Hình C1; Hình C4 sang Phụ lục E). Người viết: Trình. Nháp ngày 21/11/2026 từ gói dữ liệu V2 (runs/v2-vm/v2-dg2/, bảng ở analysis/figures/v2-dg2/) và analysis/dg2_a2.py; 24/11 cắt về ngân sách 3,5 trang (D96); Trình chưa đọc lại. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Thông điệp: (1) GPU utilization không dùng được làm tín hiệu scale vì bão hoà ngay ở tải thấp, còn tải đồng thời thì phân biệt được (TĐ1, 5.3.1); (2) chỉ ở tải thấp ổn định, A2 vừa giữ SLO vừa tiết kiệm GPU-giờ vượt ngưỡng (25% GPU-giờ của S4; TĐ2, 5.3.2); (3) khi tải tăng đột ngột, A2 thêm replica kịp N2a nhưng mất khoảng 20 điểm SLO attainment, vì hàng đợi dồn vào pod có sẵn trong lúc chờ cold start và Service chia đều request (TĐ2, 5.3.3). -->
<!-- Soát số: 27/11/2026 · Soát văn phong: kiem_van 27/11 · Người viết đọc lại: chưa -->
<!-- Đề mục theo Kế hoạch §11.1 và D101 (26/11): TĐ1 lên 5.3.1; scale-down (trước là 5.3.3) chuyển sang 5.5.1, ở đây chỉ dẫn chéo. Số hình, bảng theo chương (Bảng 5.2, Hình 5.2; trước 28/11 là số tạm theo mục 5.3a, 5.3b). Ý đã cắt khi rút gọn 24/11, dùng lại được cho Phụ lục E hoặc chương 6: Hình C4 (analysis/figures/v2-dg2/c4-tradeoff-cloud.svg, SLO attainment theo GPU-giờ); A1 bớt pod 308–315 s sau khi kịch bản tải kết thúc. Đã đưa lại thân bài 27/11 (bước 2b): A1 × KB1 tiết kiệm 9,4–10,3% (5.6.2), pod cũ 3,60–3,78 req/s và hàng đợi 370–400 → 38–80 (5.3.3), pha tăng dần và pha duy trì của KB3 (5.3.1, 5.3.2). -->

## 5.3. Autoscaling so với cấu hình tĩnh

Ma trận so sánh đặt A2 cạnh hai cấu hình tĩnh S1, S4 và cạnh A1 trên ba kịch bản tải của mục 3.6. Ma trận gồm 17 lượt trên 11 ô, chạy trong phiên đo trên 4 × RTX 4060 Ti (mục 5.1). Cả 17 lượt hợp lệ, đều bắt đầu khi image, model và compile cache đã có sẵn trên node (mục 3.4), và các lượt cùng số thứ tự lặp dùng chung một lịch gửi request.

<!-- nguồn: analysis/figures/v2-dg2/runs.csv (17 dòng, valid = True, capacity_rps 3,5 (mục 5.2), threshold 37, max_replicas 4); nhật ký Quang tuần 07 mục 18/11 (ĐG2 17/17 hợp lệ; C = 3,5, B\* = 46,3, threshold 37); Thông số §7 (KB1 0,5 C; đỉnh KB2, KB3 0,75 × N = 3,0 C), §8.1 (A1 target 70), §8.2 (ma trận 17 lượt, lịch gửi chung theo lần lặp, mọi lượt ở L2); runs.csv n_sent: A1-KB2-1 và A2-KB2-1 cùng 7.771 request, A1-KB1-2 và A2-KB1-2 cùng 1.326 -->

Theo quy tắc so sánh ở mục 3.6, hai cấu hình chỉ được coi là khác nhau khi mọi lượt cùng chiều và chênh lệch vượt ngưỡng thực tiễn. Ngưỡng là 5 điểm phần trăm SLO attainment, hoặc 10% GPU-giờ. Bảng 5.2 ghi kết quả từng ô; số của từng lượt và hình đặt SLO attainment theo GPU-giờ nằm ở Phụ lục E.

<!-- nguồn: Thông số §6 (ngưỡng thực tiễn 5 điểm phần trăm, 10% GPU-giờ; mọi lượt cùng chiều) -->

**Bảng 5.2.** Kết quả ĐG2 theo ô (phiên đo V2, 4 × RTX 4060 Ti, model 3B). Ô có nhiều lượt ghi khoảng từ thấp nhất tới cao nhất. SLO attainment và TTFT p95 tính trên các pha được chấm (KB1: pha ổn định; KB2: pha nền, tăng đột ngột và giảm; KB3: pha duy trì); request lỗi và GPU-giờ tính trên cả kịch bản. "–": không có request thành công.

| Ô | Số lượt | SLO attainment (%) | TTFT p95 (s) | Request lỗi | GPU-giờ | So với S4 (%) |
|---|---|---|---|---|---|---|
| S4 × KB1 | 1 | 100 | 0,22 | 0 | 0,80 | 100 |
| A1 × KB1 | 2 | 100 | 0,22–0,24 | 0 | 0,72 | 89,7–90,6 |
| A2 × KB1 | 2 | 100 | 0,32 | 0 | 0,20 | 25 |
| S1 × KB2 | 1 | 12,5 | 93,1 | 5.659 | 0,40 | 25 |
| S4 × KB2 | 1 | 100 | 0,38 | 0 | 1,60 | 100 |
| A1 × KB2 | 2 | 100 | 0,38–0,39 | 0 | 1,52–1,53 | 95,1–95,4 |
| A2 × KB2 | 3 | 79,4–80,7 | 73,3–79,0 | 37–93 | 1,15–1,20 | 71,8–75,2 |
| S1 × KB3 | 1 | 0,0 | – | 8.008 | 0,28 | 25 |
| S4 × KB3 | 1 | 100 | 0,40 | 0 | 1,13 | 100 |
| A1 × KB3 | 1 | 100 | 0,40 | 0 | 1,05 | 92,7 |
| A2 × KB3 | 2 | 100 | 0,40 | 0 | 1,04–1,05 | 91,7–92,3 |

<!-- nguồn: analysis/figures/v2-dg2/runs.csv, cột slo_attainment, ttft_p95_s, n_error, gpu_h, gpu_vs_baseline, scored_phases; cells.csv (n_runs); nhật ký Quang tuần 07 mục 18/11 (bảng 11 ô, cùng số sau khi làm tròn). Mọi lỗi là Timeout (cột error_types). Từng lượt: A1-KB1 0,24; 0,22 s, 89,7; 90,6%; A1-KB2 1,53; 1,52, 95,4; 95,1%, 0,39; 0,38 s; A2-KB2 79,8; 79,4; 80,7%, 79,0; 77,9; 73,3 s, 37; 82; 93 lỗi, 1,20; 1,15; 1,16, 75,2; 71,8; 72,2%; A2-KB3 1,04; 1,05, 91,7; 92,3% -->

Kết quả được đọc theo ba câu hỏi. Mục 5.3.1 xét tín hiệu scale, vì A1 scale theo GPU utilization chỉ giữ được SLO nhờ chạy gần như cấu hình tĩnh. Mục 5.3.2 xét tải ổn định, nơi autoscaling tiết kiệm GPU-giờ rõ nhất, còn mục 5.3.3 xét tải tăng đột ngột, nơi A2 phải đánh đổi SLO. Pha giảm tải của KB2 thuộc kịch bản scale-down an toàn nên được trình bày ở mục 5.5.1.

### 5.3.1. Tải đồng thời so với GPU utilization làm tín hiệu

Số đo xác nhận lý do nhóm không scale theo GPU utilization (mục 3.3). Chỉ số này đo tỷ lệ thời gian GPU có ít nhất một kernel đang chạy (mục 2.3). vLLM chạy kernel liên tục khi còn request, nên GPU utilization xấp xỉ xác suất có ít nhất một request trong hệ thống. Theo mô hình của phép kiểm LT6, xác suất này là $1 - e^{-L}$, với L là số request trung bình, và đã vượt 99% khi L lớn hơn 5. Ở cluster nhà, mô hình khớp số đo trong một sai số chuẩn ở cả 5 mức tải còn kiểm được. Trên máy 4060 Ti, mức tải thấp nhất của ĐG1 (0,57 C) đã có L = 16,4. GPU utilization vì vậy bằng 100% ở cả năm mức, từ 0,57 C tới 1,43 C, trong khi số request chờ tăng từ 0 lên 168.

<!-- nguồn: van-hanh.md LT6 (util ≈ P(N ≥ 1) = 1 − e^(−L), mô hình M/G/∞; ở nhà 5 mức có dự đoán < 0,999, |z| < 1, lớn nhất 0,91; V2: util 1,000 ở cả 5 mức 0,57–1,43 C, L thấp nhất 16,4, waiting 0 → 168; 1 − e^(−5) = 0,9933); docs/chi-tiet/02-kien-thuc-nen.md §4.4 -->

Về tín hiệu scale, LT6 coi một tín hiệu là phân biệt được khi giá trị nhỏ nhất của nó lúc quá tải vẫn lớn hơn giá trị lớn nhất lúc tải vừa. Trên dữ liệu đo năng lực của máy 4060 Ti, GPU utilization không đạt tiêu chí này. Tổng số request đang chạy và đang chờ, tín hiệu của A2, có khoảng hở 4,6 lần: 16,4 ở λ = 2 so với 75,9–232 khi quá tải. Mức dùng KV cache cũng tách được (3,9 lần), nhưng gần như đứng yên khi quá tải nặng thêm, từ 0,240 lên 0,241, vì vLLM chỉ cấp KV cache cho request đang chạy và số này bị chặn ở 64 (mục 5.2). Áp ngưỡng của hai cấu hình lên năm mức tải này, cấu hình theo GPU utilization đòi 2 replica ở mọi mức, kể cả 0,57 C. Cấu hình theo tải đồng thời giữ 1 replica ở λ = 2 và 3, bắt đầu đòi thêm replica từ λ = C (2 replica), rồi 3 và 7 replica ở λ = 4 và 5. Hai model ở cluster nhà cho cùng quy luật.

<!-- nguồn: van-hanh.md LT6 (tiêu chí khoảng hở = min(quá tải) ÷ max(vừa); bảng V2: util 1,000/1,000 không tách được, running + waiting 16,4 so với 75,9–232 (4,6×), KV-cache 0,062 so với 0,240–0,241 (3,9×); quyết định đầu tiên khi có 1 replica, V2 threshold A2 37: A1 đòi 2 ở cả 5 mức, A2 giữ 1 ở λ = 2; 3, đòi 2 ở λ = 3,5, 3 và 7 ở λ = 4; 5; ở nhà 1,5B và 0,5B cùng quy luật); Thông số §8.1 (A1 target 70), §9.3 (tolerance 10%: A1 thêm pod khi util > 77%) -->

Trong ma trận so sánh, hành vi này làm A1 chạy gần như cấu hình tĩnh. Ở tải thấp, 1 replica là đủ, nhưng A1 đã lên 4 replica sau 166–181 s. Ở tải này, cấu hình tĩnh 4 replica cho thấy vì sao: mỗi replica chỉ nhận khoảng 0,125 C mà GPU utilization trung bình vẫn là 93%. Trong pha ổn định, cấu hình này có trung bình 3,66–3,73 replica Ready nhưng dùng 97–98% GPU-giờ của cấu hình tĩnh 4 replica trong pha đó, vì pod giữ GPU từ lúc được xếp lịch, trước khi Ready. Ở kịch bản tăng đột ngột, nó đã có 4 replica trước lúc tải tăng, và ở cả hai kịch bản tải cao nó chỉ tiết kiệm 4,6–7,3% GPU-giờ so với cấu hình tĩnh. SLO attainment 100% của A1 vì vậy đến từ việc giữ gần đủ 4 replica. Ngược lại, ở cùng tải thấp, A2 giữ 1 replica và dùng 25% GPU-giờ của cấu hình tĩnh (mục 5.3.2).

<!-- nguồn: events.jsonl A1-KB1-1/2 (dg2_a2 phần 1): lên 2, 3, 4 replica lúc 15/15, 100/91, 181/166 s; runs.csv A1-KB1 replicas_max 4, scale_downs 0; runs.csv S4-KB1-1 gpu_util_mean 0,931024, capacity_rps 3,5 (0,5 C ÷ 4 replica = 0,125 C); Thông số §8.1 (A1 target 70), §9.3 (tolerance 10%: A1 thêm pod khi util > 70 × 1,1 = 77%); van-hanh.md LT6 (A1 thêm pod khi util mỗi pod > 77%; V2: util không tách được, A2 hở 4,6×); runs.csv A1-KB2-1/2 replicas_at_rise 4; gpu_vs_baseline A1-KB2-1/2 0,953713; 0,9514, A1-KB3-1 0,927411 (tiết kiệm 4,6–7,3%); A2 replicas_max 1 (KB1), 4 (KB2, KB3); events.jsonl A2-KB2 về 1 replica; pha steady (120–720 s) của A1-KB1: trung bình 3,66 và 3,73 replica Ready, GPU-giây 97–98% của S4 (van-hanh.md LT6, phần kiểm 21/11) -->

Phản ứng sớm của A1 có lợi khi tải tăng dần. Ở pha tăng dần của kịch bản tải cao kéo dài, cấu hình này lên 2 replica ở giây thứ 20, còn A2 ở giây 65 và 70, vì nó chỉ thêm replica khi tải đồng thời vượt threshold. SLO attainment của pha này là 100% với A1, so với 84,1% và 79,9% với A2 (2 lượt). Pha tăng dần không nằm trong phần được chấm của kịch bản này (mục 3.6), nên Bảng 5.2 không phản ánh khác biệt đó. Dù vậy, hai lượt này cho thấy điểm yếu ở mục 5.3.3 cũng xuất hiện khi tải tăng dần, nếu tải tăng nhanh hơn tốc độ có thêm replica Ready.

<!-- nguồn: pha tăng dần KB3: phases.csv pha ramp (0–300 s) slo_attainment A1-KB3-1 1,0, A2-KB3-1/2 0,84136; 0,798886, replicas_ready_mean 2,26 / 2,06; 2,16, ttft_p95_s A2 7,78; 12,59; scored_phases KB3 = sustain; dg2_a2 phần 1: A1-KB3-1 lên 2 replica lúc 20 s, A2-KB3-1/2 lúc 65; 70 s -->

### 5.3.2. Tải ổn định: tiết kiệm GPU-giờ mà vẫn đạt SLO

Chỉ ở tải thấp ổn định, autoscaling vừa giữ SLO vừa tiết kiệm GPU-giờ vượt ngưỡng. Ở kịch bản này, A2 giữ 1 replica và chỉ dùng 25% GPU-giờ của cấu hình tĩnh 4 replica, trong khi SLO attainment vẫn là 100%. Mức này đạt chỉ tiêu N3 (không quá 50%), và chỉ tiêu N1 (ít nhất 95% ở tải ổn định) cũng đạt ở cả bốn lượt. Cũng ở tải thấp, A1 dùng 89,7–90,6% GPU-giờ của cấu hình tĩnh. Chỉ một trong hai lượt tiết kiệm vượt ngưỡng 10%, nên theo quy tắc so sánh, nó vẫn ngang cấu hình tĩnh ở tải thấp.

<!-- nguồn: runs.csv: A2-KB1-1/2 replicas_max 1, gpu_vs_baseline 0,25, slo_delta_vs_baseline_pp 0; A1-KB3-1 0,927411, A2-KB3-1/2 0,916557 và 0,922614; A2-KB1, A2-KB3 slo_attainment 1,0 (N1 chấm pha steady của KB1, sustain của KB3); S1-KB2-1 slo 0,124719, n_error 5.659; S1-KB3-1 slo 0,0, n_error 8.008. Thông số §4 (N1 ≥ 95%, N3 ≤ 50% và kém không quá 5 điểm); A1-KB1-1/2 gpu_vs_baseline 0,897 và 0,906 (tiết kiệm 10,3% và 9,4%) -->

Ở kịch bản tải cao kéo dài, cả hai cấu hình autoscaling dùng 91,7–92,7% GPU-giờ của S4, tiết kiệm dưới ngưỡng 10%. A2 không tiết kiệm được dù trong pha duy trì, tải thường chỉ cần 3 replica. Tín hiệu của A2 trung bình 101–106 request, và ở 65–74% số mẫu nó không vượt 111, mức ứng với 3 replica theo threshold 37. Tuy vậy, các mẫu vượt 111 cách nhau nhiều nhất 95–120 s, ngắn hơn cửa sổ ổn định 300 s của scale-down. HPA chỉ bớt replica khi mọi đề xuất trong cửa sổ đều thấp hơn số hiện có, nên A2 giữ 4 replica suốt 12 phút của pha. Đây là cái giá của cửa sổ ổn định, vốn được đặt để một đợt giảm tải ngắn không bắt hệ thống chịu cold start lần nữa (mục 3.3).

<!-- nguồn: dg2_a2 phần 4 (A2-KB3-1/2, pha sustain 300–1020 s, 144 mẫu mỗi lượt): tín hiệu running + waiting trung bình 101,1 và 106,1, tỷ lệ mẫu ≤ 111 (= 3 × 37) 74% và 65%, khoảng cách lớn nhất giữa hai mẫu > 111 là 120 s và 95 s; replicas_ready_mean pha sustain 4,0 (phases.csv); Thông số §9.3 (scaleDown stabilizationWindowSeconds 300, metricType AverageValue: desired = ⌈tổng ÷ target⌉); hành vi cửa sổ ổn định của HPA: lấy đề xuất lớn nhất trong cửa sổ (Kiến thức nền, mục 2.x); lý do đặt cửa sổ: 03-03 trên nhánh docs/tr8-thesis-ch3 (PR #80) đoạn Bảng 3.5, Kiến trúc §12 -->

### 5.3.3. Tải tăng đột ngột: vì sao SLO chỉ đạt khoảng 80%

Kịch bản tăng đột ngột là nơi duy nhất buộc phải đánh đổi. Ở đây A2 tiết kiệm 24,8–28,2% GPU-giờ, nhưng SLO attainment kém S4 19,3–20,6 điểm phần trăm, cả hai vượt ngưỡng ở mọi lượt. A1 giữ 100% nhưng chỉ tiết kiệm 4,6–4,9% GPU-giờ, nên không khác cấu hình tĩnh.

<!-- nguồn: runs.csv: A2-KB2-1/2/3 gpu_vs_baseline 0,752028; 0,717897; 0,722459, slo_delta_vs_baseline_pp −20,18; −20,56; −19,26; A1-KB2-1/2 slo 1,0, gpu_vs_baseline 0,953713; 0,9514 (tiết kiệm 4,6–4,9%). S1 (12,5% ở KB2, 0% ở KB3) chỉ còn trong bảng -->

Autoscaling thêm replica kịp thời nhưng vẫn không giữ được SLO. Pod mới đầu tiên được tạo 14,7–16,4 s sau khi tải bắt đầu tăng và Ready sau thêm 65–66 s cold start (mục 5.4). Thời gian phản ứng 79,7–81,5 s (3 lượt) đạt chỉ tiêu N2a (không quá 2 phút). Đúng như LT7 dự đoán, phần lớn khoảng này là cold start, vì HPA đã đặt đủ 4 replica chỉ sau 30–36 s. Dù vậy, SLO attainment của pha tăng đột ngột chỉ là 74,8–76,2%, với 37–93 request timeout mỗi lượt. TTFT p95 chỉ trở lại dưới ngưỡng 2,5 s sau 409–430 s (6,8–7,2 phút), dài hơn mức dự kiến 5 phút của N2b (Hình 5.2 vẽ lượt thứ nhất).

<!-- nguồn: runs.csv A2-KB2-1/2/3: replicas_at_rise 1, detect_s 16,42; 15,53; 14,71, create_to_ready_s 65; 66; 65, react_s 81,42; 81,53; 79,71 (khoảng dư nhỏ nhất 38,5 s), recovery_s 426; 430; 409, error_types Timeout; events.jsonl (SuccessfulRescale, analysis/dg2_a2.py phần 1): 4 replica lúc 271, 276, 270 s, tải tăng lúc 240 s; phases.csv pha spike: slo_attainment 0,753792; 0,748413; 0,76192, n_error 37; 82; 93; nhật ký Quang tuần 07 mục 19/11 (lỗi đều ở pha spike). van-hanh.md LT7 (HPA quyết định < 11 s; phần lớn N2a là cold start). Thông số §4 (N2a, N2b), §6 (SLO TTFT 2,5 s), §7 (timeout 120 s) -->

![Hình 5.2. Lượt thứ nhất của KB2 cho S4, A1 và A2, cùng lịch gửi request (phiên đo V2). Từ trên xuống: tốc độ đến, số replica (liền: Ready; gạch: HPA đặt), TTFT p95 trượt 30 s (thang log, request lỗi tính 120 s), số request chờ trong vLLM.](../../analysis/figures/v2-dg2/c1-kb2-cloud-r1.svg)

Hình 5.2 cho thấy nguyên nhân là hàng đợi dồn vào pod có sẵn. Hai lượt còn lại của A2 cho cùng hình dạng. Trong khoảng 80 s chờ replica mới, mọi request vào pod duy nhất trong khi tải đã gấp 3 lần năng lực của nó. Hàng đợi trong vLLM của pod này lên 416–428 request và chỉ hết sau 402–414 s. Ba pod mới có nhiều nhất 9 request chờ, cấu hình tĩnh không có request chờ nào.

<!-- nguồn: nhật ký Quang tuần 07 mục 19/11 (hàng đợi pod cũ 416/425/428 trong khoảng 385–390 s, pod mới 0–9, S4 0 request chờ); kiểm lại trên runs/v2-vm/v2-dg2/{A2,S4}-KB2-*/attempt-1/metrics.csv.gz (vllm_waiting theo pod; mẫu > 0 cuối cùng ở 649, 654, 642 s, tức 409, 414, 402 s sau lúc tải tăng 240 s): analysis/dg2_a2.py phần 2 -->

Hàng đợi rút chậm vì Service của Kubernetes chia request mới đều cho các pod Ready, không xét hàng đợi trong từng pod. Từ giây 360 tới giây 600, khi cả bốn pod đã Ready, pod cũ vẫn nhận 24,3–25,7% số request mới, nên 69–75% số request nó xử lý xong chỉ bù cho request mới đến. Pod này xử lý xong 3,60–3,78 req/s, nhanh hơn 2,41–2,83 req/s của mỗi pod mới, nhiều khả năng vì nó luôn có request chờ để lấp đầy batch. Dù vậy, hàng đợi của nó chỉ giảm từ 370–400 xuống 38–80 request trong 240 s đó. Trong số request không đạt SLO của pha tăng đột ngột, 42–44% được gửi trước khi pod mới đầu tiên Ready; phần lớn số còn lại nhiều khả năng xếp sau hàng đợi cũ. Như vậy, điểm nghẽn ở kịch bản này nằm ở cold start và cách chia request, không nằm ở tín hiệu scale. Chương 6 bàn hai hướng chưa kiểm chứng: định tuyến tới pod ít request chờ nhất, hoặc nâng số replica tối thiểu trong những khung giờ biết trước có tải tăng đột ngột.

<!-- nguồn: access log runs/v2-vm/v2-dg2/A2-KB2-*/attempt-1/logs/vllm-*.log (dòng "POST /v1/chat/completions" theo pod; tổng cả lượt bằng đúng n_sent 7.771; 7.730; 7.846, tổng trong cửa sổ bằng số request gửi 2.498; 2.572; 2.517); pod cũ nhận 642; 650; 611, xử lý xong (Δ vllm_success_total) 908; 863; 880, tức 3,60–3,78 req/s so với 2,41–2,83 req/s của pod mới: dg2_a2 phần 3; requests.csv, t_sched trong [240; 840) s, SLO như analysis/metrics.py (khớp phases.csv): không đạt gửi trước lúc pod mới đầu tiên Ready (321,4; 321,5; 319,7 s) 635; 651; 647, sau đó 891; 895; 826 (dg2_a2 phần 5) -->

<!-- nguồn: chi phí nếu giữ 2 replica suốt lượt, cận trên của hướng nâng số replica tối thiểu theo khung giờ (để chương 6; 5.6.2 dùng cùng cách diễn đạt): ước tính 2 replica × 12 phút = 0,40 GPU-giờ so với 0,80 của S4 × KB1 (runs.csv gpu_h); Thông số §4 (N3 ≤ 50%); nhật ký Quang tuần 07 mục 19/11 (hướng "routing theo hàng đợi" chưa thử) -->
