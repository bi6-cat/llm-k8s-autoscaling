<!-- Mục đích: mục 3.6 của luận văn (Thiết kế đánh giá): ba lớp đánh giá, tải và kịch bản tải, ĐG1–ĐG3, chỉ số theo đề cương, quy tắc so sánh, điều kiện hợp lệ của lượt đo, kịch bản vận hành VH1–VH6 và cách chấm cảnh báo, kiểm chứng lý thuyết LT1–LT8. Người viết: Trình. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Số bảng tạm theo mục (Bảng 3.6a–3.6g) vì mục 3.2–3.4 chưa viết; đánh lại khi ghép chương. Hình 8 và Hình 17 của docs/chi-tiet/ chưa chèn: Hình 8 còn thời lượng cũ 20/25/25 phút, Hình 17 còn Argo CD trên VM thuê. -->
<!-- Thông điệp: (1) Mỗi chỉ tiêu có một phép thử định trước, thuộc một trong ba lớp (kiểm thử chức năng, kịch bản vận hành, phép đo trên VM thuê); mọi mức tải tính theo năng lực C của một replica. (2) Hai cấu hình chỉ được coi là khác nhau khi mọi lượt cùng chiều và vượt ngưỡng thực tiễn; một lượt chỉ được tính khi máy tạo tải và đường thu số liệu không là nút thắt. (3) Cảnh báo được chấm bằng log của máy tạo tải, độc lập với chính cảnh báo; kiểm chứng lý thuyết đặt dự đoán trước khi đo, ca nào không làm được thì ghi rõ. -->
<!-- Soát số: chưa · Soát văn phong: chưa · Người viết đọc lại: chưa -->
## 3.6. Thiết kế đánh giá

Đánh giá trả lời hai câu hỏi: nền tảng có đạt các chỉ tiêu ở mục 3.1 không, và để đạt thì phải đánh đổi những gì. Mỗi phép đo gắn với ít nhất một chỉ tiêu, và phép đo nào không phục vụ chỉ tiêu nào thì nhóm không làm. Cách tính từng chỉ số được viết thành mã có unit test trước phiên đo chính, nên không thể chỉnh theo kết quả.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §7 (câu hỏi "có đạt yêu cầu không, và đánh đổi những gì"; mỗi phép đo gắn với ít nhất một yêu cầu, không phục vụ yêu cầu nào thì không làm), §14.2 (analysis/metrics.py có unit test), §15 ("Chi tiết cách tính (chốt 15/11 khi viết analysis/metrics.py)"); docs/nhat-ky/van-hanh.md mục 18/11 và 19/11 (phiên V2 chạy 18–19/11, sau 15/11) -->

### 3.6.1. Ba lớp đánh giá

Nhóm chia việc đánh giá thành ba lớp theo chi phí và theo loại bằng chứng (Bảng 3.6a). Kiểm thử chức năng chạy nhanh và lặp lại được trong CI, nhưng không cho số hiệu năng. Kịch bản vận hành dựng một sự cố hoặc một thao tác có chủ đích rồi xem nền tảng phản ứng ra sao. Ba phép đo ĐG1–ĐG3 cần GPU thật cùng loại, nên chạy trên VM thuê trong một phiên đo liền.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §7 (bảng ba lớp: kiểm thử chức năng chạy lại trong CI nếu tự động hoá được; VH1–VH6; ĐG1–ĐG3 trên GPU thuê, phiên V2), §13 (VH: dựng sự cố có chủ đích); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 (toàn bộ ĐG1–ĐG3 trong một lần thuê liền) -->

**Bảng 3.6a.** Ba lớp đánh giá

| Lớp | Môi trường | Nội dung | Kết quả |
|---|---|---|---|
| Kiểm thử chức năng | Simulator, máy nhà | API, probe, graceful shutdown; bài kiểm thử cấu hình autoscaling; unit test quy tắc cảnh báo; danh sách kiểm tra bảo mật | Đạt hoặc không đạt; chạy lại trong CI nếu tự động hoá được |
| Kịch bản vận hành VH1–VH6 | Máy nhà và simulator trước; lặp lại trên VM thuê phần cần GPU thật | Mục 3.6.6 | Đạt hoặc không đạt, kèm số đo |
| Phép đo ĐG1–ĐG3 | VM thuê có 4 GPU cùng loại, phiên đo chính | Mục 3.6.3 | Số liệu cho chương 5 |
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §7 (bảng "Lớp / Ở đâu / Nội dung / Kết quả": API, probe, preStop, graceful shutdown; T1–T7; promtool test rules; checklist bảo mật); docs/chi-tiet/00-thong-so.md §2, §10.2 (N = 4 GPU cùng loại) -->

Số liệu hiệu năng chỉ lấy từ VM thuê. Máy nhà có một GPU 8 GB chia thành hai GPU replica bằng time-slicing, nên hai pod dùng chung nhân GPU và số đo của từng pod không độc lập. Các kiểm chứng lý thuyết ở mục 3.6.7 là ngoại lệ có chủ đích, vì chúng kiểm một quan hệ giữa các đại lượng chứ không báo cáo hiệu năng của nền tảng.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §18 ("Sao không làm luôn trên máy nhà cho rẻ?": GPU nhà 8 GB VRAM, time-slicing, các pod dùng chung nhân GPU nên số đo hiệu năng của từng pod không độc lập), §19 (ghi chú "Về số liệu ở nhà": LT1–LT8 kiểm chứng quan hệ, không báo cáo hiệu năng tuyệt đối); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 (không dùng số liệu máy nhà để kết luận) -->

### 3.6.2. Tải và kịch bản tải

Máy tạo tải (*load generator*) gửi request theo kiểu open-loop (mục 2.2), để quá tải hiện ra đúng trong số đo. Thời điểm gửi được sinh trước theo quá trình Poisson với tốc độ λ(t), không phụ thuộc vào phản hồi của nền tảng. Khi nền tảng chậm, tải vì thế không tự giảm theo như ở kiểu closed-loop.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §9 ("Open-loop và lịch gửi": closed-loop che mất quá tải; thời điểm gửi sinh trước theo λ(t), quá trình Poisson, độc lập với phản hồi); docs/chi-tiet/00-thong-so.md §7 (open-loop, Poisson); docs/luan-van/quy-tac-viet.md §4 (máy tạo tải, lần đầu ghi load generator) -->

Mọi cấu hình nhận đúng cùng một chuỗi request. Lịch gửi và độ dài prompt sinh từ một seed gắn với kịch bản và lần lặp. Prompt là văn bản tổng hợp dài 256–1024 token, phân phối đều. Output cố định 256 token và trả về dạng streaming, để request nào cũng có cùng lượng việc ở pha decode. Request chưa xong sau 120 s bị tính là lỗi.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §7 (bảng Request: seed theo (kịch bản, số thứ tự lượt); prompt tổng hợp 256–1024 token, phân phối đều; output cố định 256 token, max_tokens=256, ignore_eos=true; stream=true; timeout 120 s tính là lỗi); docs/chi-tiet/05-moi-truong-danh-gia.md §9 (mọi cấu hình nhận đúng cùng một chuỗi request), §14.2 (cột id: cùng kịch bản và cùng số thứ tự lượt thì cùng t_sched, cùng prompt), §18 (output cố định để lượng việc giữa các cấu hình như nhau); loadgen/prompts.py (mỗi từ đúng 1 token) -->

Ba kịch bản tải theo đề cương tái hiện ba lúc trong ngày: ban đêm, đầu giờ sáng và giờ cao điểm kéo dài (Bảng 3.6b). Mức tải tính theo bội số của C, năng lực một replica đo ở ĐG1. Khi đổi máy, nhóm chỉ cần đo lại C, không phải thiết kế lại kịch bản.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §10 ("Vì sao ba kịch bản này?": đúng ba kịch bản trong đề cương; ban đêm KB1, 9 giờ sáng KB2, giờ cao điểm kéo dài KB3); docs/chi-tiet/00-thong-so.md §7 (đơn vị C đo ở ĐG1); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 (máy khác thì đo lại ĐG1 trên máy mới) -->

**Bảng 3.6b.** Ba kịch bản tải. Tốc độ gửi λ(t) tính theo C; thời điểm tính bằng phút từ đầu kịch bản; số GPU N = 4

| Kịch bản | Tốc độ gửi λ(t) | Thời lượng | Pha được chấm | Dùng để kiểm |
|---|---|---|---|---|
| KB1. Thấp, ổn định | 0,5 C | 12 phút | Pha ổn định (phút 2–12) | SLO attainment và GPU-giờ khi tải thấp |
| KB2. Tăng đột ngột rồi giảm | 0,5 C tới phút 4; lên 3,0 C trong 30 s; giữ tới phút 14; về 0,5 C trong 30 s; giữ tới phút 24 | 24 phút | Pha nền (2–4), pha tăng đột ngột (4–14), pha giảm (14–24) | Thời gian phản ứng và hồi phục (pha tăng đột ngột); request lỗi khi scale-down (pha giảm) |
| KB3. Cao, kéo dài | Tăng dần từ 0,5 C lên 3,0 C trong 5 phút; giữ tới phút 17 | 17 phút | Pha tăng dần (0–5), pha duy trì (5–17) | SLO attainment ở pha duy trì; flapping; cảnh báo SLO |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §7 (bảng KB: KB1 0,5, 12 phút, steady [2, 12]; KB2 0,5 khi t < 4, lên 0,75 × N = 3,0 trong [4; 4,5], giữ tới 14, về 0,5 trong [14; 14,5], giữ tới 24, pre [2, 4], spike [4, 14], drop [14, 24]; KB3 tăng từ 0,5 lên 3,0 trong [0, 5], giữ tới 17, ramp [0, 5], sustain [5, 17]; cột "Kiểm chứng chủ yếu"; hai phút đầu của KB1, KB2 không tính); docs/luan-van/quy-tac-viet.md §4 (tên pha tiếng Việt) -->

Đỉnh của hai kịch bản tải cao được đặt ở 0,75 × N × C, với N = 4 là 3,0 C. Ở mức này, autoscaling cần đúng 4 replica với target ở mục 3.3. Ở 3,5 C sẽ cần 5 replica, vượt số GPU, và kết quả khi đó nói về việc thiếu GPU chứ không về autoscaling. Kịch bản tăng đột ngột giảm tải trở lại ở phút 14, để một lượt kiểm được cả scale-up lẫn scale-down. Bốn pha chính dài 10–12 phút, đủ hai cửa sổ chờ scale-down 300 s để thấy flapping. Pha giảm còn đủ dài để pod cuối cùng bị xoá, khoảng 8 phút sau khi tải giảm.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §10 (KB2 giảm tải trở lại để cùng một lượt kiểm cả scale-up lẫn scale-down; "Vì sao KB3 dừng ở 0,75 × N × C": target 0,8 × B\*, tải 3,5C cần ⌈3,5 ÷ 0,8⌉ = 5 replica, vượt 4 GPU, thiếu năng lực chứ không vì autoscaling kém; ở 3C HPA cần đúng 4 replica); docs/chi-tiet/00-thong-so.md §7 ("Giới hạn khi rút": pha steady, sustain ≥ 10 phút = hai cửa sổ scale-down 300 s; drop 10 phút, với N = 4 pod cuối bị xoá khoảng 8 phút sau khi tải giảm), §8.1 (A2 target 0,8 × B\*). Bốn pha chính: steady 10 phút, spike 10, drop 10, sustain 12 -->

### 3.6.3. Ba phép đo trên VM thuê

Phép đo năng lực (ĐG1) tìm C, tốc độ request lớn nhất mà một replica phục vụ được trong khi vẫn đạt SLO. Nhóm cố định 1 replica rồi quét λ tăng dần, mỗi mức gồm 1 phút làm ấm và 4 phút đo, dày hơn quanh mức bắt đầu vi phạm. Năng lực C là mức λ lớn nhất còn ít nhất 95% request đạt SLO. Tại C, nhóm đọc B\*, số request đồng thời trung bình trên replica, để suy ra target của autoscaling (mục 3.3). Định luật Little cho một phép kiểm chéo: B\* phải gần bằng tốc độ đến thực tế nhân thời gian lưu lại trung bình của request. Hai vế lệch nhau quá 15% thì cách đo phải được xem lại.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §8 (mục đích: tìm C; cố định 1 replica S1; quét λ tăng dần, quét dày quanh điểm vi phạm; C = mức λ lớn nhất còn đạt SLO, đọc B\* tại C; kiểm bằng định luật Little với λ_thực, lệch hơn 15% thì xem lại cách đo; target A1, A2 suy ra từ đây); docs/chi-tiet/00-thong-so.md §8.3 (mỗi mức 1 phút làm ấm + 4 phút đo, bước 0,25 quanh điểm vi phạm), §8.1 (B\* = số request đồng thời trung bình trên một replica khi tải bằng C); experiments/runner/capacity.py (ATTAINMENT = 0.95; C = mức lớn nhất có slo_attainment ≥ 0,95 và lượt hợp lệ) -->

Phép đo autoscaling (ĐG2) so bốn cấu hình ở mục 3.3 trên ba kịch bản, tổng cộng 17 lượt (Bảng 3.6c). Một lượt là một lần chạy một cấu hình với một kịch bản tải. Hai cấu hình tĩnh là hai đầu của trade-off, một bên cấp thiếu với chi phí thấp nhất, một bên cấp theo đỉnh. Cấu hình scale theo GPU utilization là cách làm phổ biến, dùng làm đối chứng cho cấu hình vận hành chính thức.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §8.1 (S1 cấp thiếu, chi phí thấp nhất; S4 cấp theo đỉnh; A1 đối chứng, cách làm phổ biến; A2 cấu hình vận hành chính thức), §8.2 (17 lượt); docs/luan-van/quy-tac-viet.md §4 (lượt = một lần chạy một cấu hình với một kịch bản tải) -->

**Bảng 3.6c.** Số lượt của ma trận ĐG2 theo cấu hình và kịch bản. Dấu "–" là ô không chạy

| Cấu hình | KB1 | KB2 | KB3 | Cộng |
|---|---|---|---|---|
| S1 | – | 1 | 1 | 2 |
| S4 | 1 | 1 | 1 | 3 |
| A1 | 2 | 2 | 1 | 5 |
| A2 | 2 | 3 | 2 | 7 |
| Cộng | 5 | 7 | 5 | 17 |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §8.2 (ma trận ĐG2 17 lượt) -->

Số lượt dồn vào cấu hình vận hành và vào kịch bản tăng đột ngột, vì kịch bản này kiểm cả phản ứng lẫn scale-down. Ô cấu hình tĩnh một replica ở tải thấp bị bỏ, vì ở 0,5 C autoscaling cũng chỉ chạy 1 replica. Thứ tự lượt được xáo bằng một seed ghi lại, trong từng khối lần lặp. Mọi ô chạy lần thứ nhất trước rồi mới tới lần thứ hai và thứ ba, nên phiên đo bị cắt ngang chỉ mất lần lặp, không mất ô nào. Mọi lượt chạy ở mức cold start L2.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §11 (KB2 nhiều lượt nhất vì kiểm phản ứng và scale-down); docs/chi-tiet/00-thong-so.md §4 (N1, N3 chấm trên A2), §8.2 (bỏ S1 × KB1: ở 0,5C S1 và A2 cùng chạy 1 replica; xáo trộn bằng seed ghi lại trong từng khối lần lặp, 11 lượt lặp-1 rồi 5 lượt lặp-2 rồi 1 lượt lặp-3; phiên bị cắt ngang chỉ mất lần lặp; mọi lượt ở L2) -->

Hai lượt cùng kịch bản chỉ khác nhau ở cấu hình autoscaling. Toàn bộ phép đo chạy trên một máy trong một lần thuê liền, với image vLLM ghim theo digest và tham số vLLM giữ nguyên. Máy tạo tải chạy trên chính VM thuê với lõi CPU riêng, nên request không đi qua mạng bên ngoài. Runner là chương trình chạy tự động các lượt đánh giá. Trước mỗi lượt, runner đưa nền tảng về 1 replica (S4 là 4 replica), chờ hàng đợi trống rồi chờ thêm 60 s. Tiếp theo là 2 phút làm ấm ở 0,3 C, không tính vào kết quả. Hết kịch bản, runner chờ nền tảng về 1 replica trong tối đa 10 phút, để lượt sau không nhận pod đang khởi động hay request còn trong hàng đợi.
<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 (cùng máy: một lần thuê liền; cùng phiên bản và tham số: ghim digest, chỉ đổi cấu hình autoscaling giữa các lượt; trạng thái đầu giống nhau vì lượt trước có thể để lại pod đang khởi động hoặc hàng đợi); docs/chi-tiet/05-moi-truong-danh-gia.md §14.1 (Reset: 1 pod Ready, S4: 4 pod Ready, hàng đợi trống, chờ thêm 60 s; Warm-up 0,3C trong 2 phút, không tính; Cooldown chờ còn 1 replica, tối đa 10 phút), §18 (máy tạo tải nằm cùng VM với lõi CPU riêng, không có nhiễu mạng); docs/luan-van/quy-tac-viet.md §4 (runner) -->

Phép đo cold start (ĐG3) so mức lạnh L0 với mức ấm L2 (mục 3.4) khi scale từ 1 lên 2 replica. Ở mức lạnh, nhóm xoá image vLLM, model và compile cache trên node trước mỗi lần đo. Ở mức ấm, các thứ này đã có sẵn trên node. Cả hai mức đều xoá page cache của hệ điều hành, vì lần nạp model thứ hai đọc từ RAM sẽ nhanh bất thường. Mỗi lần đo ghi mốc của tám pha cold start từ trạng thái pod, event và log vLLM, với 2 lần ở mức lạnh và 3 lần ở mức ấm. Nhóm không chạy riêng kịch bản tăng đột ngột ở mức lạnh. Ảnh hưởng của cold start lên thời gian phản ứng được suy ra từ tám pha này và các lượt của phép đo autoscaling.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §12 (bảng ĐG3: L0 crictl rmi image, xoá model và compile cache; L2 image pre-pull, model trên NVMe, compile cache đã làm ấm; drop_caches ở cả hai; scale 1 lên 2; mốc 8 pha từ pod conditions, event pull image, log vLLM; ảnh hưởng lên thời gian phản ứng suy ra từ 8 pha cộng lượt A2 × KB2 ở L2, không chạy KB2 × A2 ở L0, ADR-004 K8); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 (page cache: lần nạp thứ hai đọc từ RAM nên nhanh bất thường); docs/chi-tiet/00-thong-so.md §8.3 (L0 × 2, L2 × 3) -->

### 3.6.4. Chỉ số và quy tắc so sánh

Nhóm đo đủ các chỉ số mà đề cương yêu cầu, và thêm những chỉ số mà chỉ tiêu ở mục 3.1 cần (Bảng 3.6d). Đề cương ghi độ trễ P95/P99, TTFT, throughput, mức dùng tài nguyên và thời gian phản ứng của autoscaling. Với request streaming, độ trễ được đo bằng hai đại lượng TTFT và TPOT. Mức dùng tài nguyên được báo chủ yếu bằng GPU-giờ, vì đồ án quy ước chi phí tỷ lệ với số GPU-giờ cấp cho pod vLLM (mục 1.3).
<!-- nguồn: docs/mo-ta-chi-tiet-do-an.md Phụ lục A (đề cương: "P95/P99 Latency, TTFT, Throughput, Resource Utilization", "Autoscaling Response Time"; bổ sung TPOT, SLO attainment, tỷ lệ lỗi; resource utilization báo bằng GPU-giờ, token/GPU-giờ, GPU utilization trung bình, CPU/RAM của pod); docs/adr/002-chuyen-trong-tam-sang-van-hanh.md (vẫn đo đủ chỉ số đề cương yêu cầu); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.2 (G1: chi phí ≈ GPU-giờ cấp phát cho pod vLLM, là quy ước) -->

**Bảng 3.6d.** Chỉ số đánh giá. Thời điểm của từng request lấy từ log của máy tạo tải

| Nhóm | Chỉ số | Cách tính | Trong đề cương |
|---|---|---|---|
| Độ trễ | TTFT p50, p95, p99 | Từ lúc gửi tới lúc nhận chunk có nội dung đầu tiên | P95/P99, TTFT |
| | TPOT p50, p95 | Thời gian từ chunk đầu tới chunk cuối ÷ (số token output − 1) | Bổ sung |
| Chất lượng | SLO attainment | Số request đạt SLO ÷ số request đã gửi trong pha; request lỗi vẫn nằm ở mẫu số | Bổ sung |
| | Tỷ lệ lỗi | Số request lỗi HTTP, quá 120 s hoặc bị cắt stream ÷ số request đã gửi | Bổ sung |
| Tài nguyên | Throughput | Số token output mỗi giây | Throughput |
| | GPU-giờ, % so với S4 | Tổng thời gian các pod vLLM giữ GPU, gồm cả lúc cold start và lúc đang tắt | Mức dùng tài nguyên |
| | Token/GPU-giờ | Tổng token output ÷ GPU-giờ | Mức dùng tài nguyên |
| | GPU utilization, CPU và RAM của pod | Trung bình trên cửa sổ lượt | Mức dùng tài nguyên |
| Autoscaling | Thời gian phản ứng | Từ lúc tải tăng theo lịch tới lúc replica mới đầu tiên Ready; tách phần phát hiện và phần cold start | Thời gian phản ứng |
| | Thời gian hồi phục SLO | Từ lúc tải tăng tới khi TTFT p95 trên cửa sổ trượt 30 s không còn vượt ngưỡng và giữ được ít nhất 60 s | Thời gian phản ứng |
| | Số lần scale, flapping | Số lần số replica đổi; số lần đổi chiều trong vòng 5 phút | Bổ sung |
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §15 (bảng chỉ số: TTFT = t_first − t_send; TPOT = (t_last − t_first) ÷ (n_out − 1); SLO attainment, request lỗi vẫn ở mẫu số; tỷ lệ lỗi gồm HTTP, timeout, stream bị cắt; throughput token output mỗi giây; GPU-giờ tính cả cold start và drain; token/GPU-giờ; GPU util, CPU, RAM trung bình; thời gian phản ứng tách phát hiện và cold start; hồi phục SLO cửa sổ trượt 30 s, giữ ít nhất 60 s; flapping trong vòng 5 phút), §9 (t_first = chunk có nội dung đầu tiên); analysis/build_tables.py (cột n_sent, n_error, error_ratio, tokens_per_gpu_h, throughput_tok_s); docs/mo-ta-chi-tiet-do-an.md Phụ lục A (cột "Trong đề cương") -->

Số liệu ở chương 5 tính theo ba quy ước chung. Phân vị tính trên toàn bộ request của pha, không lấy trung bình các p95 theo phút hay theo pod. Pha có dưới khoảng 200 request chỉ báo p95 kèm số mẫu. Độ trễ lấy từ log của máy tạo tải, chính xác tới từng request, còn histogram của Prometheus nội suy trong bucket nên chỉ dùng cho dashboard và cảnh báo. GPU-giờ của mỗi pod tính từ lúc pod được xếp lên node tới lúc runner thấy pod đã biến mất. Cách tính này hơi cao với cấu hình autoscaling, nên không thổi phồng mức tiết kiệm GPU.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §15 ("Hai nguyên tắc tính": phân vị trên tất cả request của pha, không trung bình p95 theo phút hay theo pod, pha dưới khoảng 200 request chỉ báo p95 kèm số mẫu; độ trễ từ log máy tạo tải, histogram Prometheus nội suy theo bucket chỉ dùng cho dashboard và cảnh báo; "Chi tiết cách tính": GPU-giờ mỗi pod từ mốc scheduled tới gone_at, cận trên, sai số ≤ 5 s mỗi pod, hơi cao cho cấu hình autoscaling nên kết luận "A2 tiết kiệm" không bị thổi phồng), §14.2 (gone_at = lần đầu thấy pod đã biến mất, đồng hồ runner) -->

Nhóm chỉ kết luận hai cấu hình khác nhau khi mọi lượt đều cùng chiều và chênh lệch vượt ngưỡng thực tiễn. Ngưỡng này là 5 điểm phần trăm với SLO attainment, 10% với GPU-giờ và 30 s với thời gian. Mỗi ô chỉ có 1–3 lượt, nên đồ án không dùng kiểm định thống kê, và quy tắc trên chỉ đủ để nhận ra các khác biệt lớn. Chênh lệch nhỏ hơn ngưỡng được ghi là không phân biệt được, còn kết quả nằm sát ngưỡng được ghi rõ là sát ngưỡng. Mỗi ô được báo bằng trung bình kèm min–max, và biểu đồ vẽ từng lượt thành một chấm.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §6 (ngưỡng thực tiễn: 5 điểm phần trăm SLO attainment, 10% GPU-giờ, 30 s thời gian; chỉ kết luận "khác nhau" khi mọi lượt cùng chiều và vượt ngưỡng); docs/chi-tiet/05-moi-truong-danh-gia.md §7 (chỉ kết luận về các khác biệt lớn, khác biệt nhỏ báo "không phân biệt được"), §16 (mỗi ô 1–3 lượt, trung bình kèm min–max, vẽ từng lượt thành chấm, sát ngưỡng ghi rõ); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 ("không phải một thiết kế thí nghiệm thống kê"); docs/adr/002-chuyen-trong-tam-sang-van-hanh.md (bỏ thiết kế thí nghiệm thống kê của bản 1.0) -->

### 3.6.5. Điều kiện hợp lệ của một lượt

Một lượt chỉ được tính khi máy tạo tải và đường thu số liệu không là nút thắt, và lượt bắt đầu từ đúng trạng thái đầu (Bảng 3.6e). Nếu máy tạo tải gửi trễ hay xử lý chậm, số đo sẽ phản ánh máy tạo tải chứ không phản ánh nền tảng. Runner tự kiểm các điều kiện này ở mọi lượt và ghi kết quả cùng dữ liệu của lượt (mục 4.7).
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §9 ("Tự kiểm tra ở mọi lượt"; không đạt thì lượt không hợp lệ), §14.1 (bước "Kiểm tra, sao lưu": ghi checks.json), §17; docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (3.6 nói tiêu chí và lý do, 4.7 nói runner kiểm thế nào) -->

**Bảng 3.6e.** Điều kiện hợp lệ của một lượt

| Kiểm tra | Ngưỡng | Vì sao |
|---|---|---|
| Lệch giữa lúc gửi thật và lúc gửi theo lịch | p99 < 50 ms | Tải thật phải đúng lịch open-loop |
| CPU của máy tạo tải | < 70% một lõi, theo cửa sổ 5 s; thời gian bị throttle < 0,1% thời gian lượt | Máy tạo tải còn dư năng lực, không thành nút thắt |
| Độ trễ event loop của máy tạo tải | p99 < 50 ms, không lần nào quá 500 ms | Event loop nghẽn thì mốc nhận chunk đầu bị ghi trễ, TTFT đo được cao hơn thật mà kiểm tra phía gửi không thấy |
| Chạy hết lịch | Mọi request trong lịch có đúng một dòng kết quả | Không mất mẫu |
| Khoảng trống scrape của Prometheus | ≤ 15 s giữa hai lần scrape thành công của một pod | Chuỗi số replica, hàng đợi và GPU đủ để phân tích |
| Tín hiệu scale của A1, A2 | Có mẫu suốt pha chính, không mất quá 15 s | KEDA coi truy vấn rỗng là 0 mà không báo lỗi, nên mất tín hiệu chỉ lộ ra ở kiểm tra này |
| Trạng thái của node và pod | Trạng thái đầu đúng; không có sự cố node, không có pod bị OOMKilled ngoài dự kiến | Mọi lượt bắt đầu từ cùng một điểm |
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §17 (bảng điều kiện hợp lệ: lệch gửi p99 < 50 ms ở từng tiến trình; CPU < 70% một lõi, cửa sổ 5 s, tiến trình bận nhất; throttle < 0,1%; event loop p99 < 50 ms và không lần nào quá 500 ms; chạy hết lịch; khoảng trống scrape ≤ 15 s giữa hai lần scrape thành công; tín hiệu scale có mẫu suốt pha chính, không mất quá 15 s, KEDA coi truy vấn rỗng là 0 mà không báo lỗi; không có sự cố node, OOMKilled ngoài dự kiến; trạng thái đầu đúng), §9 (event loop nghẽn thì t_first bị trễ mà kiểm tra phía gửi không phát hiện) -->

Máy tạo tải chia lịch cho nhiều tiến trình, nên các ngưỡng của nó được chấm riêng ở từng tiến trình rồi lấy tiến trình tệ nhất. Nếu gộp mẫu, một tiến trình nghẽn sẽ bị các tiến trình rảnh che đi. Lượt không đạt bị đánh dấu không hợp lệ kèm lý do và được chạy lại ở cuối phiên đo. Dữ liệu của lượt hỏng vẫn được giữ lại.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §9 (chia lịch cho k tiến trình; lệch lịch, event loop, CPU chấm riêng từng tiến trình rồi lấy tiến trình tệ nhất, gộp mẫu thì tiến trình nghẽn bị "pha loãng"), §17 (lượt không đạt đánh dấu invalid kèm lý do, chạy lại ở cuối phiên V2; dữ liệu lượt hỏng vẫn được giữ lại) -->

### 3.6.6. Kịch bản vận hành và cách chấm cảnh báo

Sáu kịch bản vận hành kiểm những thao tác và sự cố mà người vận hành thường gặp (Bảng 3.6f). Mỗi kịch bản có tiêu chí đạt định trước. Phần không cần GPU thật chạy trước ở máy nhà hoặc simulator, phần cần GPU thật được lặp lại trên VM thuê.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §7 (VH: máy nhà và simulator trước, lặp lại trên GPU thuê những gì cần GPU thật), §13 (bảng VH1–VH6, cột "Tiêu chí đạt") -->

**Bảng 3.6f.** Sáu kịch bản vận hành

| Mã | Kịch bản | Cách làm | Tiêu chí đạt | Môi trường |
|---|---|---|---|---|
| VH1 | Scale-down an toàn | Tải giảm đột ngột khi đang có nhiều replica; đếm request lỗi hoặc bị cắt stream trong lúc scale-down | 0 request lỗi | VM thuê (pha giảm của kịch bản tăng đột ngột); máy nhà |
| VH2 | Cập nhật phiên bản | Đổi tham số hoặc image. (a) Từ 1 replica: nâng số replica tối thiểu lên 2 trước khi cập nhật. (b) Mọi GPU đều có pod: thay từng pod một, không thêm pod mới trước. (c) Đối chứng: cập nhật kiểu web service, thêm pod mới trước khi bớt pod cũ. Sau đó rollback qua Git | (a), (b) xong với 0 request lỗi; (c) kẹt và `LLMPodPending` kêu | Máy nhà (qua Git); VM thuê |
| VH3 | Sự cố pod và node | Khi đang có tải: xoá pod; kill tiến trình vLLM; drain một node | Pod mới tự Ready; xoá pod thì 0 lỗi; kill chỉ làm lỗi các request đang chạy trên pod đó; có cảnh báo tương ứng | Máy nhà, VM thuê; drain trên simulator |
| VH4 | Mất nguồn metric | Khi đang có tải, chặn KEDA đọc Prometheus bằng NetworkPolicy trong 5 phút rồi gỡ | KEDA chuyển sang fallback (số replica tối đa) trong ≤ 30 s; SLO không bị ảnh hưởng; gỡ chặn thì trở lại bình thường | Máy nhà, VM thuê |
| VH5 | Dựng lại từ máy trắng | Dựng VM trắng bằng các lệnh `make`; người thứ hai dựng cluster nhà, hoặc kind với simulator, chỉ theo README | VM trắng: ≤ 30 phút. Người thứ hai: < 1 giờ | VM thuê, máy nhà |
| VH6 | Cảnh báo đúng, không báo giả | Ghi cảnh báo trong mọi lượt ĐG2, so với mốc vi phạm theo log máy tạo tải | Cảnh báo SLO kêu ≤ 5 phút sau vi phạm; không có page giả | Mọi lượt ĐG2; máy nhà |
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §13 (bảng VH1–VH6: ở đâu, cách làm, tiêu chí đạt; VH1 nhà KB2-mini, GPU thuê pha drop của KB2; VH2 qua PR → Argo CD, (a) ca 1 replica nâng minReplicaCount lên 2, (b) mọi GPU đều có pod, maxSurge: 0, (c) phương án kiểu web bị kẹt và LLMPodPending kêu, rollback bằng git revert; VH3 drain ở nhà 2 node hoặc simulator; VH4 NetworkPolicy chặn KEDA → Prometheus, gỡ sau 5 phút; VH5 make bootstrap prefetch trên VM trắng, người thứ hai theo README); docs/chi-tiet/00-thong-so.md §4 (N6: fallback ≤ 30 s, dựng lại từ VM trắng ≤ 30 phút; N7: ≤ 5 phút, không có page giả; N8: < 1 giờ) -->

Hai phép thử có thêm ca đối chứng, làm sai có chủ đích để thấy đúng lỗi mà thiết kế tránh. Ca (c) của kịch bản cập nhật cho thấy cách cập nhật quen thuộc của web service bị kẹt khi mọi GPU đã có pod. Phép thử graceful shutdown ở máy nhà có thêm ca rút thời gian chờ tắt pod còn 5 s, để thấy request đang stream bị cắt khi pod không được chờ đủ lâu.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §13 (VH2 (c): thử phương án kiểu web để thấy bị kẹt); docs/nhat-ky/van-hanh.md mục 06/11 (graceful shutdown: đối chứng rút grace xuống 5 s thì cắt cả 48 request); docs/chi-tiet/06-ke-hoach-quan-ly.md §8 (không cắt các ca đối chứng: ca đối chứng của graceful shutdown và VH2c) -->

Cảnh báo được chấm bằng log của máy tạo tải, một nguồn độc lập với chính cảnh báo. Kịch bản VH6 không cần lượt riêng, vì trong mỗi lượt ĐG2, runner ghi các cảnh báo đang kêu mỗi 5 s, từ 30 s trước lúc làm ấm tới hết lượt. Mốc SLO bắt đầu bị vi phạm là thời điểm đầu tiên mà hơn 20% request gửi trong 1 phút trước đó là request xấu. Request xấu gồm request không đạt SLO và request lỗi. Ngưỡng và cửa sổ này trùng với ngưỡng và cửa sổ ngắn của `LLMSLOBurnFast` (mục 3.5). Điểm khác là mốc vi phạm đếm từng request ở phía client, còn cảnh báo chỉ đọc histogram TTFT ở phía server. Thời gian tới cảnh báo tính từ mốc vi phạm tới lúc cảnh báo chuyển sang firing, chưa gồm 30 s Alertmanager chờ để gom nhóm.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §13 (VH6 ghi lại trong mọi lượt ĐG2; so thời điểm vi phạm từ log client với thời điểm firing qua ALERTS), §14.2 (alerts.jsonl: cảnh báo firing từ 30 s trước warm-up tới hết cooldown), §15 ("Chi tiết cách tính", N7: mốc vi phạm = mốc đầu tiên mà tỷ lệ request xấu trong 1 phút trước đó theo log client vượt 20 %, chỉ xét khi cửa sổ đã đủ 1 phút; cùng ngưỡng và cửa sổ ngắn của LLMSLOBurnFast; thời gian tới cảnh báo = firing − vi phạm; mốc firing lấy từ chuỗi ALERTS, chưa gồm group_wait 30 s của Alertmanager); experiments/runner/collect.py (query_range ALERTS{alertstate="firing"}, bước 5 s); analysis/metrics.py (_bad_fraction: request xấu gồm cả lỗi; slo_violation_start); common/observability/alerts/llm.yaml (LLMSLOBurnFast: rate5m > 4 × 0,05 và rate1m > 4 × 0,05); common/observability/rules/slo.yaml (tỷ lệ xấu chỉ từ histogram TTFT) -->

Một page bị tính là page giả nếu tỷ lệ request xấu theo log máy tạo tải, trong 5 phút trước lúc kêu, dưới 20%. Cửa sổ 5 phút này bằng cửa sổ dài của cảnh báo. Cửa sổ không có request nào cũng tính là page giả, vì không có bằng chứng người dùng bị ảnh hưởng. Mỗi đợt kêu được chấm riêng, vì đợt sau có thể là page giả dù đợt đầu đúng. Đợt đã kêu từ trước pha chính thì không được chấm. Chỉ tiêu không có page giả chỉ chấm trên các lượt A2 ở tải thấp và tải cao kéo dài, nơi nhóm không cố ý gây sự cố.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (N7: page giả = page trong khi tỷ lệ request xấu theo log client, trên cùng cửa sổ, < 20%; không có page giả khi A2 chạy KB1 và KB3); docs/chi-tiet/05-moi-truong-danh-gia.md §15 (page giả chấm cho từng đợt kêu trên cửa sổ dài 5 phút kết thúc lúc firing; đợt đã kêu từ trước t0 không đếm); analysis/metrics.py (classify_alerts: cửa sổ không có request cũng tính là page giả; mỗi đợt chấm riêng; định nghĩa chỉ có nghĩa ở lượt không cố ý gây sự cố, ở VH4 KedaScalerErrors kêu đúng dù người dùng chưa bị ảnh hưởng) -->

Các lượt đánh giá gọi thẳng Service của vLLM, không qua Traefik, nên tỷ lệ 5xx đo ở Traefik không có dữ liệu. Route riêng qua Traefik cho máy tạo tải đã bị lược cùng giới hạn tốc độ, còn simulator và VM thuê không có Ingress. Kịch bản VH6 vì vậy chỉ kiểm được `LLMSLOBurnFast`, còn `LLMErrorRateHigh` chỉ được kiểm bằng unit test.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §13 ("Giới hạn của VH6": runner gọi thẳng Service vllm.llm-serving.svc:8000 ở mọi môi trường, simulator và VM thuê không có Ingress, llm:error_ratio:rate5m không có dữ liệu, VH6 chỉ kiểm được LLMSLOBurnFast, LLMErrorRateHigh mới được kiểm bằng unit test); docs/chi-tiet/00-thong-so.md §7 (dòng "Đường đi", sửa 21/11: route riêng qua Traefik đã lược cùng rate limit, ADR-006 §3.1) -->

### 3.6.7. Kiểm chứng lý thuyết

Tám kiểm chứng lý thuyết dùng kiến thức ở chương 2 và mục 3.4 để dự đoán hành vi của nền tảng trên đúng phần cứng của nhóm (Bảng 3.6g). Dự đoán sau đó được so với số đo. Theo thiết kế, dự đoán được tính trước khi đo, và kiểm chứng nào chỉ tính được dự đoán sau khi đã có số đo thì chương 5 ghi rõ. Số đo lấy từ dữ liệu mà nền tảng đã có sẵn, gồm Prometheus, log vLLM, event Kubernetes và log máy tạo tải, nên không cần thuê thêm máy. Lệch lớn so với dự đoán vẫn là một kết quả nếu giải thích được nguyên nhân.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §19 (mục đích: dùng lý thuyết dự đoán hành vi trên đúng phần cứng, đo để kiểm chứng, giải thích chỗ lệch; mẫu lý thuyết → dự đoán → số đo → giải thích; dự đoán tính trước khi đo; nguyên tắc chọn: số liệu lấy từ Prometheus, log vLLM, event Kubernetes, requests.csv, không cần thuê máy; lệch lớn không phải thất bại); docs/nhat-ky/van-hanh.md mục LT4 (dự đoán tính ngày 16/11, sau khi đã có số đo lần A, nên không phải dự đoán mù) -->

**Bảng 3.6g.** Tám kiểm chứng lý thuyết LT1–LT8

| Mã | Lý thuyết | Dự đoán | Số đo đối chiếu | Môi trường | Báo cáo ở |
|---|---|---|---|---|---|
| LT1 | Decode bị giới hạn bởi băng thông bộ nhớ (mục 2.1) | TPOT không nhỏ hơn dung lượng weights ÷ băng thông bộ nhớ của GPU | TPOT khi chỉ có 1 request | Máy nhà, VM thuê | 5.2 |
| LT2 | Dung lượng KV cache (mục 2.1) | Số token KV và số request đồng thời tối đa, tính từ cấu hình model và VRAM còn lại | Số block KV vLLM in khi khởi động; mức dùng KV cache lúc tải cao | Máy nhà | 5.2 |
| LT3 | Continuous batching (mục 2.1) | Throughput tăng gần tuyến tính theo số request đồng thời rồi bão hoà, điểm gãy gần B\* | Throughput và TPOT theo mức tải của phép đo năng lực | Máy nhà, VM thuê | 5.2 |
| LT4 | Phân rã cold start (mục 3.4) | Thời gian nạp weights ≈ dung lượng model ÷ tốc độ đọc đĩa; pha dài nhất ở mức lạnh và ở mức ấm | Mốc tám pha khi scale từ 1 lên 2 replica | Máy nhà, VM thuê | 5.4 |
| LT5 | Định luật Little (mục 2.2) | Số request trung bình trong hệ thống ≈ λ × thời gian lưu lại trung bình, lệch < 15% | Số request đang chạy và đang chờ từ Prometheus; log máy tạo tải của mọi lượt | Máy nhà, simulator, VM thuê | 5.3 |
| LT6 | GPU utilization bão hoà (mục 2.3) | GPU utilization gần 100% ngay từ tải vừa, trong khi số request chờ chênh nhau nhiều lần giữa tải vừa và quá tải | GPU utilization và số request chờ theo mức tải | Máy nhà, VM thuê | 5.3 |
| LT7 | Thuật toán HPA (mục 2.4) | Số replica = ⌈tổng metric ÷ target⌉; quyết định scale sau không quá khoảng 15 s | Mốc event và trạng thái HPA trong bài kiểm thử trên simulator, 5 lần | Simulator | 5.3 |
| LT8 | Cảnh báo theo burn rate (mục 2.5) | Cảnh báo SLO kêu khi tỷ lệ request xấu vượt 20%, sau thời gian chờ của quy tắc cộng thời gian để cửa sổ 5 phút vượt ngưỡng; dưới 20% thì không kêu | Thời điểm firing khi tỷ lệ request xấu là 10%, 30% và 60% | Simulator | 5.5 |
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §19 (bảng LT1–LT8: lý thuyết, dự đoán, lấy số đo, ở đâu; LT1 TPOT ≳ weights ÷ băng thông, batch = 1, V2: TPOT ở mức λ thấp nhất của ĐG1; LT2 dòng "Maximum concurrency", số block KV, vllm:kv_cache_usage_perc; LT3 điểm gãy gần B\*, dữ liệu ĐG1-mini, + V2 từ ĐG1; LT4 nạp weights ≈ dung lượng ÷ tốc độ đọc đĩa, pha lớn nhất ở L0 và L2, 8 pha khi scale 1 → 2, + V2 từ ĐG3; LT5 running + waiting ≈ λ × E2E, lệch < 15%, mọi lượt, nhà, simulator, V2; LT6 + V2 từ A1; LT7 desired = ⌈tổng metric ÷ target⌉, scrape 5 s + polling 5 s + HPA 5 s, quyết định sau ≤ ~15 s, bài T2 trên simulator 5 lần; LT8 kêu khi x > 20% sau khoảng for + thời gian để cửa sổ 5m vượt ngưỡng, x = 10%, 30%, 60% trên simulator); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (dàn ý chương 5: 5.2 có LT1–LT3, LT còn lại đặt ở mục có khẳng định tương ứng) -->

Các kiểm chứng về model và GPU chạy ở máy nhà, và dùng thêm số của phép đo năng lực và phép đo cold start trên VM thuê khi có. Hai kiểm chứng về thuật toán HPA và cảnh báo không phụ thuộc GPU, nên chạy trên simulator. Trên simulator, nhóm đổi được TTFT giả lập trong lúc chạy để tạo đúng tỷ lệ request xấu mà kiểm chứng về cảnh báo cần.
<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md §19 (cột "Ở đâu": LT1–LT4 nhà, + V2 từ ĐG1, ĐG3; LT7, LT8 simulator); docs/nhat-ky/van-hanh.md mục LT8 (16/11: đổi TTFT của simulator lúc chạy qua POST /admin/config để có tỷ lệ xấu x) -->
