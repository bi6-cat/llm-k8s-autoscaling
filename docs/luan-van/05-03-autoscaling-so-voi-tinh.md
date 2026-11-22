<!-- Mục đích: mục 5.3, autoscaling so với cấu hình tĩnh (ĐG2, Hình C1 và C4). Người viết: Trình. Nháp do agent soạn ngày 21/11/2026 từ gói dữ liệu V2 (runs/v2-vm/v2-dg2/, bảng ở analysis/figures/v2-dg2/) và analysis/dg2_a2.py; một agent khác đối chiếu từng số; Trình chưa đọc lại. -->
<!-- Số hình, bảng tạm theo mục (Bảng 5.3a, Hình 5.3a) vì 5.1–5.2 chưa có; đánh lại khi ghép chương. Dẫn chéo "(mục 3.x)" là chỗ giữ, điền khi các mục đó có. -->

## 5.3. Autoscaling so với cấu hình tĩnh

Mục này trả lời câu hỏi chính của đồ án: autoscaling theo tải đồng thời (A2) có giữ được SLO với ít GPU-giờ hơn cấu hình tĩnh hay không. Mục này so A2 với hai cấu hình tĩnh S1, S4 và với autoscaling theo GPU utilization (A1), trên ba kịch bản tải KB1–KB3 (mục 3.x). Mục 5.3.1 tổng hợp SLO attainment và GPU-giờ của cả ma trận. Mục 5.3.2 và 5.3.3 phân tích hành vi theo thời gian khi tải tăng và giảm. Mục 5.3.4 đối chiếu lựa chọn tín hiệu A2 với số đo của A1.

Ma trận ĐG2 gồm 17 lượt trên 11 ô, chạy trong phiên đo V2 (mục 5.1); cả 17 lượt đều hợp lệ. Mọi lượt chạy ở mức cold start L2. Các lượt có cùng số thứ tự lặp dùng chung lịch gửi request, nên S4, A1 và A2 ở cùng một lần lặp nhận đúng cùng một chuỗi request. Năng lực một replica đo ở ĐG1 là C = 3,5 req/s (mục 5.2), nên KB1 tương ứng 1,75 req/s và đỉnh của KB2, KB3 (3,0 C) là 10,5 req/s. A2 dùng threshold 37, bằng 0,8 B\* với B\* = 46,3; A1 dùng target 70%; cả hai giới hạn ở 1–4 replica.

<!-- nguồn: analysis/figures/v2-dg2/runs.csv (17 dòng, valid = True, capacity_rps 3,5, threshold 37, max_replicas 4); nhật ký Quang tuần 07 mục 18/11 (ĐG2 17/17 hợp lệ; C = 3,5, B\* = 46,3, threshold 37); Thông số §7 (KB1 0,5 C; đỉnh KB2, KB3 0,75 × N = 3,0 C), §8.1 (A1 target 70), §8.2 (ma trận 17 lượt, lịch gửi chung theo lần lặp, L2); runs.csv n_sent: A1-KB2-1 và A2-KB2-1 cùng 7.771 request, A1-KB1-2 và A2-KB1-2 cùng 1.326 -->

### 5.3.1. SLO attainment và GPU-giờ theo cấu hình

Bảng 5.3a liệt kê kết quả của từng ô; Hình 5.3a đặt hai đại lượng chính lên cùng một mặt phẳng. Theo quy tắc so sánh ở mục 3.x, hai cấu hình chỉ được coi là khác nhau khi mọi lượt cùng chiều và chênh lệch vượt ngưỡng thực tiễn: 5 điểm phần trăm SLO attainment, hoặc 10% GPU-giờ.

**Bảng 5.3a.** Kết quả ĐG2 theo ô (phiên đo V2, 4 × RTX 4060 Ti, model 3B). Ô có nhiều lượt ghi giá trị từng lượt, cách nhau bằng dấu chấm phẩy. SLO attainment và TTFT p95 tính trên các pha được chấm (KB1: `steady`; KB2: `pre`, `spike`, `drop`; KB3: `sustain`). Số request lỗi và GPU-giờ tính trên cả kịch bản. "–": không có request thành công để tính TTFT.

| Ô | Số lượt | SLO attainment (%) | TTFT p95 (s) | Request lỗi | GPU-giờ | GPU-giờ so với S4 (%) |
|---|---|---|---|---|---|---|
| S4 × KB1 | 1 | 100 | 0,22 | 0 | 0,80 | 100 |
| A1 × KB1 | 2 | 100; 100 | 0,24; 0,22 | 0; 0 | 0,72; 0,72 | 89,7; 90,6 |
| A2 × KB1 | 2 | 100; 100 | 0,32; 0,32 | 0; 0 | 0,20; 0,20 | 25; 25 |
| S1 × KB2 | 1 | 12,5 | 93,1 | 5.659 | 0,40 | 25 |
| S4 × KB2 | 1 | 100 | 0,38 | 0 | 1,60 | 100 |
| A1 × KB2 | 2 | 100; 100 | 0,39; 0,38 | 0; 0 | 1,53; 1,52 | 95,4; 95,1 |
| A2 × KB2 | 3 | 79,8; 79,4; 80,7 | 79,0; 77,9; 73,3 | 37; 82; 93 | 1,20; 1,15; 1,16 | 75,2; 71,8; 72,2 |
| S1 × KB3 | 1 | 0,0 | – | 8.008 | 0,28 | 25 |
| S4 × KB3 | 1 | 100 | 0,40 | 0 | 1,13 | 100 |
| A1 × KB3 | 1 | 100 | 0,40 | 0 | 1,05 | 92,7 |
| A2 × KB3 | 2 | 100; 100 | 0,40; 0,40 | 0; 0 | 1,04; 1,05 | 91,7; 92,3 |

<!-- nguồn: analysis/figures/v2-dg2/runs.csv, cột slo_attainment, ttft_p95_s, n_error, gpu_h, gpu_vs_baseline, scored_phases; cells.csv (n_runs); nhật ký Quang tuần 07 mục 18/11 (bảng 11 ô, cùng số sau khi làm tròn). Mọi lỗi là Timeout (cột error_types) -->

Kết quả cho thấy chỉ A2 vừa giữ SLO vừa tiết kiệm GPU-giờ rõ rệt, và chỉ ở tải thấp ổn định (KB1). Ở KB1, A2 giữ 1 replica suốt lượt và dùng 25% GPU-giờ của S4 ở cả hai lượt, với SLO attainment 100% như S4. Như vậy chỉ tiêu N3 (A2 dùng không quá 50% GPU-giờ của S4 ở KB1, SLO attainment kém không quá 5 điểm phần trăm) đạt, với mức chênh SLO là 0 điểm. Ở KB3, A1 và A2 đều dùng 91,7–92,7% GPU-giờ của S4. Mức tiết kiệm 7,3–8,3% này dưới ngưỡng 10%, nên ở KB3, cả A1 và A2 đều không khác S4 về GPU-giờ. Chỉ tiêu N1 (SLO attainment của A2 ≥ 95% ở KB1 pha `steady` và KB3 pha `sustain`) đạt, với 100% ở cả bốn lượt.

<!-- nguồn: runs.csv: A2-KB1-1/2 replicas_max 1, gpu_vs_baseline 0,25, slo_delta_vs_baseline_pp 0; A1-KB3-1 0,927411, A2-KB3-1/2 0,916557 và 0,922614; A2-KB1, A2-KB3 slo_attainment 1,0. Thông số §4 (N1, N3), §6 (ngưỡng thực tiễn) -->

![Hình 5.3a. SLO attainment theo GPU-giờ (phần trăm so với S4) của từng cấu hình ở ba kịch bản tải, phiên đo V2 (4 × RTX 4060 Ti, model 3B, C = 3,5 req/s). Điểm lớn là trung bình các lượt của một ô, chấm nhỏ là từng lượt; số lượt mỗi cấu hình ghi ở tiêu đề mỗi ô. Đường gạch ngang là mục tiêu 95% của chỉ tiêu N1.](../../analysis/figures/v2-dg2/c4-tradeoff-cloud.svg)

Hình 5.3a cho thấy KB2 là kịch bản duy nhất buộc phải đánh đổi. Ở KB2, A2 dùng 71,8–75,2% GPU-giờ của S4, tức tiết kiệm 24,8–28,2%. Đổi lại, SLO attainment chỉ còn 79,4–80,7%, kém S4 19,3–20,6 điểm phần trăm. Cả hai chênh lệch đều vượt ngưỡng ở mọi lượt, nên ở KB2, A2 khác S4 theo cả hai chiều. A1 đạt 100% ở KB2 nhưng dùng 95,1–95,4% GPU-giờ của S4, nên không khác S4 về GPU-giờ. Ở KB1, A1 tiết kiệm 10,3% và 9,4% ở hai lượt; một lượt dưới ngưỡng 10%, nên theo quy tắc trên A1 không khác S4 (mục 5.3.4 giải thích vì sao). Cuối cùng, S1 chỉ đạt 12,5% ở KB2 và 0% ở KB3, với 5.659 và 8.008 request timeout, nên tải ở đỉnh cần nhiều hơn một replica.

<!-- nguồn: runs.csv: A2-KB2-1/2/3 gpu_vs_baseline 0,752028; 0,717897; 0,722459, slo_delta_vs_baseline_pp −20,18; −20,56; −19,26; A1-KB2-1/2 0,953713; 0,9514; A1-KB1-1/2 0,897032; 0,906002; S1-KB2-1 slo 0,124719, n_error 5.659; S1-KB3-1 slo 0,0, n_error 8.008. Hình: analysis/figures/v2-dg2/c4-tradeoff-cloud.svg -->

### 5.3.2. Phản ứng khi tải tăng đột ngột (KB2)

Hình 5.3b xếp chồng diễn biến của S4, A1 và A2 trong lượt thứ nhất của KB2. Hai lượt còn lại của A2 cho cùng hình dạng (Phụ lục x). Ở KB2, tải đứng ở 0,5 C trong 4 phút đầu, tăng lên 3,0 C trong 30 s (từ giây 240 tới giây 270 của pha chính), giữ tới phút 14, rồi giảm về 0,5 C.

![Hình 5.3b. Diễn biến theo thời gian của lượt thứ nhất ở kịch bản KB2 cho S4, A1 và A2, cùng một lịch gửi request (phiên đo V2, C = 3,5 req/s). Từ trên xuống: tốc độ đến theo lịch (trung bình 30 s); số replica (nét liền: replica Ready; nét gạch: số replica HPA đặt); TTFT p95 trên cửa sổ trượt 30 s (thang log; request lỗi hoặc timeout tính là 120 s); tổng số request chờ trong hàng đợi vLLM của mọi pod. Nền xám đánh dấu pha pre và drop.](../../analysis/figures/v2-dg2/c1-kb2-cloud-r1.svg)

Hình 5.3b cho thấy A2 thêm replica kịp thời, nhưng hàng đợi dồn trong pod có sẵn giữ TTFT p95 trên ngưỡng SLO tới khoảng phút 11, trong khi S4 và A1 không có hàng đợi. Các đoạn dưới phân tích từng giai đoạn.

**Phát hiện tải và thêm replica.** Trong pha `pre`, A2 chạy 1 replica. Ở cả ba lượt, pod mới đầu tiên được tạo 14,7–16,4 s sau khi tải bắt đầu tăng. Pod đó Ready sau thêm 65–66 s; đây là thời gian cold start ở mức L2, tính từ lúc pod được tạo (mục 5.4 phân tích riêng cold start). Thời gian phản ứng vì vậy là 81,4 s, 81,5 s và 79,7 s. Chỉ tiêu N2a (replica mới đầu tiên Ready ≤ 2 phút) đạt, với khoảng dư nhỏ nhất 38,5 s. HPA đặt đủ 4 replica sau 30–36 s kể từ khi tải bắt đầu tăng.

<!-- nguồn: runs.csv A2-KB2-1/2/3: replicas_at_rise 1, detect_s 16,42; 15,53; 14,71, create_to_ready_s 65; 66; 65, react_s 81,42; 81,53; 79,71; phases.csv pha pre replicas_ready_mean 1,0. events.jsonl (SuccessfulRescale, tính trong analysis/dg2_a2.py §1): 4 replica lúc 271, 276, 270 s, tải tăng lúc 240 s. Thông số §4 (N2a), §7 (KB2) -->

**SLO không đạt dù phản ứng kịp.** Trong pha `spike`, SLO attainment của A2 chỉ là 75,4%, 74,8% và 76,2%. Ba lượt có 37, 82 và 93 request lỗi, đều là timeout 120 s, và đều nằm trong pha này. TTFT p95 (cửa sổ trượt 30 s) chỉ trở lại dưới ngưỡng 2,5 s, và giữ được ít nhất 60 s, sau 426 s, 430 s và 409 s kể từ khi tải tăng. Chỉ tiêu N2b chỉ yêu cầu báo cáo thời gian hồi phục; con số đo được dài hơn mức dự kiến 5 phút.

<!-- nguồn: phases.csv A2-KB2-1/2/3 pha spike: slo_attainment 0,753792; 0,748413; 0,76192, n_error 37; 82; 93; runs.csv error_types Timeout, recovery_s 426; 430; 409; nhật ký Quang tuần 07 mục 19/11 (lỗi đều ở pha spike). Thông số §4 (N2b), §6 (SLO TTFT 2,5 s), §7 (timeout 120 s) -->

**Nguyên nhân: hàng đợi dồn vào pod có sẵn.** Trong khoảng 80 s chờ replica mới, mọi request đều vào pod duy nhất, trong khi tải đã gấp 3 lần năng lực C của pod. Hàng đợi trong vLLM của pod này lên tối đa 416, 425 và 428 request. Hàng đợi kéo dài 385–390 s và chỉ hết ở giây 642–654, tức 402–414 s sau khi tải bắt đầu tăng. Trong khi đó, ba pod mới có nhiều nhất 0–9 request chờ. Ở S4, bốn pod có 0 request chờ suốt lượt. A1 cũng gần như không có hàng đợi (tối đa 1 request), vì A1 đã chạy đủ 4 replica trước khi tải tăng (mục 5.3.4).

<!-- nguồn: nhật ký Quang tuần 07 mục 19/11 (hàng đợi pod cũ 416/425/428 trong khoảng 385–390 s, pod mới 0–9, S4 0 request chờ); kiểm lại trên runs/v2-vm/v2-dg2/{A2,S4,A1}-KB2-*/attempt-1/metrics.csv.gz (vllm_waiting theo pod; mẫu > 0 cuối cùng ở 649, 654, 642 s): analysis/dg2_a2.py §2; runs.csv A1-KB2-1/2 replicas_at_rise 4 -->

**Vì sao hàng đợi rút chậm.** Nhóm đếm số request mỗi pod nhận trong khoảng từ giây 360 tới giây 600, khi cả bốn pod đã Ready, theo access log của vLLM. Pod cũ nhận 24,3–25,7% số request mới, ngang với 23,3–26,1% của mỗi pod mới. Pod cũ xử lý 3,60–3,78 req/s, nhiều hơn mức 2,41–2,83 req/s của các pod mới, nhưng 69–75% số request nó xử lý xong chỉ để bù cho request mới đến. Vì vậy, trong 240 s đó, hàng đợi của pod cũ chỉ giảm từ 370–400 xuống 38–80 request. Số đo cho thấy Service của Kubernetes chia request mới đều cho các pod Ready, không xét hàng đợi trong từng pod, nên khoảng một phần tư request mới tiếp tục xếp sau hàng đợi cũ.

<!-- nguồn: runs/v2-vm/v2-dg2/A2-KB2-*/attempt-1/logs/vllm-*.log (dòng "POST /v1/chat/completions" theo pod; tổng cả lượt bằng đúng n_sent 7.771; 7.730; 7.846, tổng trong cửa sổ bằng số request gửi 2.498; 2.572; 2.517); pod cũ nhận 642; 650; 611, xử lý xong (Δ vllm_success_total) 908; 863; 880; hàng đợi 370→63, 379→80, 400→38 (metrics.csv.gz): analysis/dg2_a2.py §3; agent đối chiếu tính độc lập ra cùng số -->

**Hai phần của vi phạm SLO.** Từ đó suy ra tín hiệu A2 không phải điểm nghẽn: HPA đã đặt đủ 4 replica chỉ sau 30–36 s. Trong số request không đạt SLO của pha `spike`, 42–44% được gửi trước khi pod mới đầu tiên Ready, tức trong lúc chờ cold start. 56–58% còn lại được gửi sau đó; phần lớn số này nhiều khả năng là request xếp sau hàng đợi cũ, vì các pod mới gần như không có hàng đợi.

<!-- nguồn: events.jsonl (4 replica sau 30–36 s, dg2_a2 phần 1); requests.csv A2-KB2-1/2/3, t_sched trong [240; 840) s, SLO như analysis/metrics.py (khớp phases.csv 0,7538; 0,7484; 0,7619): không đạt gửi trước lúc pod mới đầu tiên Ready (321,4; 321,5; 319,7 s) 635; 651; 647, sau đó 891; 895; 826 (dg2_a2 phần 5) -->

Nhóm nêu hai hướng khắc phục, cả hai chưa được kiểm chứng. Hướng thứ nhất là định tuyến theo tải của từng pod, ví dụ gửi request mới tới pod có ít request chờ nhất. Giả thuyết của nhóm là khi đó request mới không phải xếp sau hàng đợi cũ, còn pod cũ dùng toàn bộ năng lực để rút hàng đợi của mình, nên SLO hồi phục sớm hơn nhiều so với khoảng 7 phút đo được (chưa kiểm chứng). Hướng thứ hai là giữ tối thiểu 2 replica. Khi đó GPU-giờ ở KB1 tăng lên khoảng 50% của S4 (ước tính: 2 replica × 12 phút), đúng bằng giới hạn của N3. Chương 6 bàn tiếp hai hướng này.

<!-- nguồn: ước tính 2 × 12 phút = 0,40 GPU-giờ so với 0,80 của S4 × KB1 (runs.csv gpu_h); Thông số §4 (N3 ≤ 50%); nhật ký Quang tuần 07 mục 19/11 (hướng "routing theo hàng đợi" chưa thử) -->

### 5.3.3. Scale-down và độ ổn định của số replica

Khi tải giảm, A2 bớt replica từng bước mà không gây lỗi. Tải bắt đầu giảm ở giây 840. A2 bớt pod đầu tiên sau 190–299 s, rồi về 1 replica sau 369–420 s; các bước cách nhau 60–125 s. Nhịp này khớp với cấu hình scale-down: cửa sổ ổn định 300 s và bớt tối đa 1 pod mỗi 60 s (mục 3.x). Cả ba lượt về 1 replica trước khi pha `drop` kết thúc. Trong pha `drop`, ba lượt có 0 request lỗi trên 1.147, 1.166 và 1.245 request, và SLO attainment 100%. Như vậy, phần scale-down của chỉ tiêu N4 (0 request lỗi khi scale-down) đạt; phần rolling update được trình bày ở mục 5.5.

<!-- nguồn: events.jsonl A2-KB2-1/2/3 (dg2_a2 phần 1): 4→3 lúc 1139; 1030; 1068 s, 3→2 lúc 1200; 1155; 1148 s, 2→1 lúc 1260; 1215; 1209 s; tải giảm lúc 840 s (Thông số §7); phases.csv pha drop: n_sent 1.147; 1.166; 1.245, n_error 0, slo_attainment 1,0; runs.csv scale_downs 3. Thông số §9.3 (stabilizationWindowSeconds 300, 1 pod mỗi 60 s), §4 (N4) -->

Ở lượt 2 và lượt 3, bước bớt pod đầu tiên đến sớm hơn 300 s sau khi tải giảm. Khi đang có 4 replica, HPA đề xuất bớt pod nếu tổng số request đang chạy và đang chờ không quá 111 (3 × threshold 37). Cửa sổ ổn định tính từ đề xuất cao gần nhất, không tính từ lúc tải giảm. Mẫu cuối cùng có tổng trên 111 nằm ở giây 749 và 767 ở lượt 2 và lượt 3, tức trước khi tải giảm, còn ở lượt 1 là giây 839. Nhiều khả năng vì vậy cửa sổ 300 s của lượt 2 và lượt 3 đã bắt đầu từ cuối pha `spike`, khi hàng đợi đã rút hết.

<!-- nguồn: metrics.csv.gz A2-KB2-1/2/3 (vllm_running + vllm_waiting cộng mọi pod): mẫu > 111 cuối ở 839; 749; 767 s; ở [700; 840) s, 50%, 82%, 75% số mẫu ≤ 111 (dg2_a2 phần 4); quy tắc HPA với AverageValue và dung sai 10%: mục 2.x, LT7 -->

Không lượt nào trong 17 lượt có flapping, tức đổi chiều số replica trong vòng 5 phút. Điểm đáng chú ý là A2 × KB3. Trong pha `sustain`, tổng số request đang chạy và đang chờ dao động 64–152, trung bình 101,1 và 106,1 ở hai lượt; 65–74% số mẫu không quá 111, tức HPA đề xuất từ 3 replica trở xuống. Nếu bớt xuống 3 replica, mỗi pod sẽ chạy đúng ở năng lực C, với khoảng 46 request đồng thời mỗi pod (ước tính theo B\* của ĐG1), vượt threshold 37. Từ đó suy ra số replica sẽ dao động giữa 3 và 4 nếu HPA làm theo từng đề xuất. Trong pha này, hai mẫu liên tiếp có tổng trên 111 cách nhau nhiều nhất 120 s và 95 s, ngắn hơn cửa sổ ổn định 300 s. Vì cửa sổ này giữ số replica ở mức cao nhất trong các đề xuất gần đây, A2 giữ 4 replica suốt pha `sustain`.

<!-- nguồn: runs.csv flaps = 0 ở cả 17 lượt; metrics.csv.gz A2-KB3-1/2 (vllm_running + vllm_waiting cộng mọi pod, [300; 1020) s): min 64, 75, max 142, 152, trung bình 101,1; 106,1, tỷ lệ mẫu ≤ 111: 74%, 65%, khoảng cách lớn nhất giữa hai mẫu > 111: 120 s, 95 s (dg2_a2 phần 4); phases.csv A2-KB3 pha sustain replicas_ready_mean 4,0; nhật ký Quang tuần 07 mục 18/11 (B\* = 46,3 ở λ = 3,5). Thuật toán HPA và cửa sổ ổn định: mục 2.x, LT7 -->

Hệ quả là ở KB3, A2 chỉ tiết kiệm GPU-giờ trong pha `ramp`, nơi trung bình chỉ có 2,1 và 2,2 replica Ready. Pha `ramp` không được chấm SLO. Trong pha này, SLO attainment của A2 là 84,1% và 79,9%, còn A1 đạt 100%. Nhiều khả năng vì A1 tạo pod thứ hai ngay ở giây 20, còn A2 ở giây 65 và 70, trong khi tải bắt đầu vượt năng lực một pod từ khoảng giây 60.

<!-- nguồn: phases.csv: A2-KB3 pha ramp replicas_ready_mean 2,060272; 2,162116, slo 0,84136; 0,798886; A1-KB3-1 ramp slo 1,0; events.jsonl: A1-KB3-1 lên 2 replica lúc 20 s, A2-KB3-1/2 lúc 65; 70 s (dg2_a2 phần 1); Thông số §7 (KB3 tăng từ 0,5 C lên 3,0 C trong 5 phút: vượt 1,0 C ở khoảng 60 s nếu tăng tuyến tính) -->

### 5.3.4. Vì sao không dùng GPU utilization làm tín hiệu

A1 là cấu hình đối chứng, đại diện cho cách làm phổ biến: scale theo GPU utilization với target 70%. Số đo xác nhận lý do nhóm không chọn tín hiệu này (mục 3.x). Ở KB1, tải chỉ bằng 0,5 C, đủ cho 1 replica. Dù vậy, ở cả hai lượt, A1 thêm pod ở giây 15, 91–100 và 166–181, rồi giữ 4 replica tới hết tải. Kết quả là A1 dùng 89,7–90,6% GPU-giờ của S4, so với 25% của A2, trong khi SLO attainment của cả ba cấu hình đều là 100%.

<!-- nguồn: events.jsonl A1-KB1-1/2 (dg2_a2 phần 1): lên 2, 3, 4 replica lúc 15/15, 100/91, 181/166 s; runs.csv A1-KB1 replicas_max 4, scale_downs 0, gpu_vs_baseline 0,897032; 0,906002; A2-KB1 0,25; slo 1,0 ở cả 5 lượt KB1. Thông số §8.1 (A1 target 70); van-hanh.md LT6 (kết quả V2 21/11) -->

Nguyên nhân là GPU utilization đo tỷ lệ thời gian GPU có ít nhất một kernel đang chạy, không đo phần năng lực đang dùng (mục 2.x). Vì vậy chỉ số này bão hoà ngay ở tải thấp. Ở S4 × KB1, mỗi replica chỉ nhận khoảng 0,125 C, nhưng GPU utilization trung bình của bốn GPU vẫn là 93%. Mức này cao hơn ngưỡng 77% mà trên đó A1 thêm pod (target 70% cộng dung sai 10%). Phép kiểm LT6 cũng cho kết quả tương tự trên dữ liệu ĐG1 của V2: GPU utilization không tách được tải vừa khỏi quá tải, còn tín hiệu A2 có khoảng hở 4,6 lần giữa hai nhóm. Ngoài ra, A1 không bớt pod lần nào khi còn tải. Ở cả năm lượt A1, pod chỉ bắt đầu được bớt 308–315 s sau khi kịch bản tải kết thúc và máy tạo tải đã dừng.

<!-- nguồn: runs.csv S4-KB1-1 gpu_util_mean 0,931024, capacity_rps 3,5 (0,5 C ÷ 4 replica = 0,125 C); Thông số §9.3 (tolerance 10%); van-hanh.md LT6 (A1 thêm pod khi util mỗi pod > 77%; V2: util không tách được, A2 hở 4,6×); events.jsonl A1 (dg2_a2 phần 1): 4→3 lúc 1028; 1029 s (kết thúc 720 s), 1751; 1755 s (kết thúc 1440 s), 1335 s (kết thúc 1020 s); runs.csv A1 scale_downs 0 ở cả 5 lượt -->

Như vậy, SLO attainment 100% của A1 không đến từ việc A1 theo được tải. Ở KB2, A1 đã chạy đủ 4 replica từ trước khi tải tăng, như S4. Ở pha `ramp` của KB3, A1 thêm pod thứ hai khi tải mới khoảng 0,67 C. Đổi lại, ở KB2 và KB3, A1 chỉ tiết kiệm 4,6–7,3% GPU-giờ so với S4. Ngược lại, số replica của A2 đi theo tải: 1 replica ở KB1, 4 replica ở đỉnh KB2 và KB3, rồi về 1 replica trong pha `drop` của KB2.

<!-- nguồn: runs.csv A1-KB2-1/2 replicas_at_rise 4; events.jsonl A1-KB3-1 lên 2 replica lúc 20 s (dg2_a2 phần 1), tải lúc đó 0,5 + 2,5 × 20/300 ≈ 0,67 C nếu tăng tuyến tính (Thông số §7); gpu_vs_baseline A1-KB2-1/2 0,953713; 0,9514, A1-KB3-1 0,927411 (tiết kiệm 4,6–7,3%); A2 replicas_max 1 (KB1), 4 (KB2, KB3); events.jsonl A2-KB2 về 1 replica (dg2_a2 phần 1) -->

Tổng hợp lại, A2 đạt các chỉ tiêu ở tải ổn định (N1, N3), và ở KB1 dùng ít hơn S4 75% GPU-giờ. Điểm yếu của A2 là tải tăng đột ngột. A2 phản ứng kịp theo N2a, nhưng hàng đợi dồn trong lúc chờ cold start, cộng với việc request mới vẫn được chia đều cho pod có hàng đợi, làm SLO attainment ở KB2 chỉ còn khoảng 80%. Cold start chiếm 65–66 s trong khoảng 80 s phản ứng; mục 5.4 phân tích riêng thời gian này.

<!-- nguồn: runs.csv A2-KB1 gpu_vs_baseline 0,25; A2-KB2 slo_attainment 0,798–0,807, create_to_ready_s 65–66 trong react_s 79,7–81,5 -->
