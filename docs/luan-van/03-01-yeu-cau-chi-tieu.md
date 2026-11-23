<!-- Mục đích: mục 3.1 của luận văn (Yêu cầu và chỉ tiêu nghiệm thu): truy vết bài toán tới yêu cầu, bảng mã định danh, yêu cầu chức năng F1–F7, giá trị SLO, chỉ tiêu N1–N8. Người viết: Trình. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Thông điệp: (1) Ba yêu cầu kéo nhau của bài toán được tách thành 7 yêu cầu chức năng và 8 chỉ tiêu nghiệm thu; mỗi cái có phép thử và mức ưu tiên, phần lớn chỉ tiêu có ngưỡng, nên chương 5 chủ yếu đối chiếu số đo với ngưỡng. (2) SLO: TTFT ≤ 2,5 s, TPOT ≤ 100 ms, 95% request đạt; cảnh báo và nghiệm thu dùng cùng một ngưỡng TTFT. (3) Ngưỡng nào cũng có lý do từ đặc điểm của nền tảng (cold start, tải tăng đột ngột), và được đặt trước phiên đo chính. -->
<!-- Soát số: chưa · Soát văn phong: chưa · Người viết đọc lại: chưa -->
## 3.1. Yêu cầu và chỉ tiêu nghiệm thu

Bài toán ở mục 1.2 gồm ba yêu cầu kéo nhau: chất lượng phục vụ, hiệu quả GPU và vận hành được hằng ngày. Phát biểu đó chưa đo được trực tiếp, nên nhóm tách nó thành bảy yêu cầu chức năng và tám chỉ tiêu nghiệm thu. Mỗi yêu cầu có một phép thử và một mức ưu tiên. Phần lớn chỉ tiêu có ngưỡng đặt từ trước, nên chương 5 nghiệm thu bằng cách đối chiếu số đo với ngưỡng. Vài chỉ tiêu chỉ báo cáo số đo, và mục 3.1.4 nêu lý do.
<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §6 (ba yêu cầu kéo nhau), §8 (mỗi yêu cầu có cách kiểm chứng); docs/chi-tiet/00-thong-so.md §3 (F1–F7), §4 (N1–N8: N2 tách N2a, N2b nhưng vẫn là một chỉ tiêu), §5 (mức Must, Should, Could) -->

### 3.1.1. Từ bài toán tới yêu cầu

Để giải bài toán, nền tảng phải làm được sáu điều, mỗi điều ứng với một nhóm yêu cầu (Bảng 3.1). Hai điều đầu là phục vụ qua API chuẩn và tự điều chỉnh số replica theo tải. Hai điều tiếp theo nhắm vào điểm khó riêng của LLM. Pod mới phải sẵn sàng nhanh, còn scale-down hay cập nhật phiên bản không được cắt request đang stream. Hai điều cuối thuộc về vận hành: biết khi nào có vấn đề và phải làm gì, dựng lại được từ đầu với chi phí biết trước.
<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §8 (sơ đồ "Bài toán vận hành LLM tự host" tách thành sáu nhánh, mỗi nhánh ứng với F/N) -->

**Bảng 3.1.** Truy vết từ việc nền tảng phải làm tới yêu cầu và các mục của luận văn

| Nền tảng phải làm được | Yêu cầu, chỉ tiêu | Thiết kế | Triển khai | Đánh giá |
|---|---|---|---|---|
| Phục vụ được, đúng chuẩn API | F1 | 3.2 | 4.2 | 5.6 |
| Tự điều chỉnh số replica theo tải, đúng tín hiệu | F2, N1, N2, N3 | 3.3, 3.4 | 4.3, 4.4 | 5.3, 5.4 |
| Có pod mới sẵn sàng nhanh | N5 | 3.4 | 4.4 | 5.4 |
| Thay đổi an toàn (scale-down, cập nhật) | F3, N4 | 3.2, 3.4 | 4.1, 4.5 | 5.3, 5.5 |
| Biết khi nào có vấn đề và phải làm gì | F5, F6, N7 | 3.5, 3.6 | 4.6 | 5.5, 5.6 |
| Dựng lại được, an toàn, biết chi phí | F4, F7, N6, N8 | 3.2, 3.3, 3.5 | 4.1, 4.3, 4.6 | 5.1, 5.5, 5.6 |
<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §8 (sáu nhánh và mã F/N), §10 (ma trận truy vết tới mục đánh giá); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (bảng "Truy vết yêu cầu → mục": cột thiết kế, triển khai, đánh giá của từng F/N) -->

Mỗi yêu cầu được kiểm bằng một trong ba loại phép thử. Loại thứ nhất là kiểm thử chức năng trên simulator hoặc máy nhà. Loại thứ hai là kịch bản vận hành, dựng sự cố hoặc thao tác có chủ đích rồi xem nền tảng phản ứng ra sao. Loại thứ ba là phép đo trên VM thuê có GPU giống nhau. Yêu cầu nào cũng có một trong ba mức ưu tiên. Mức Must là điều kiện đủ để bảo vệ, mức Should làm đồ án tốt hơn, mức Could chỉ làm khi còn thời gian. Khi chậm tiến độ, nhóm cắt từ mức Could trở lên.
<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §8 (cách kiểm chứng: bài kiểm thử ở nhà hoặc simulator, VH1–VH6, ĐG1–ĐG3 trên GPU thuê); docs/chi-tiet/05-moi-truong-danh-gia.md §7 (ba loại đánh giá), §13 (VH: dựng có chủ đích); docs/chi-tiet/00-thong-so.md §5 (Must = đủ điều kiện bảo vệ, Should = đồ án tốt, Could = xuất sắc; cắt từ dưới lên) -->

### 3.1.2. Mã định danh

Yêu cầu và chỉ tiêu dẫn tới cấu hình, kịch bản tải và phép thử bằng mã ngắn. Bảng 3.2 định nghĩa các mã này một lần cho cả luận văn. Các mục ghi ở cột cuối mô tả chi tiết từng nhóm mã.
<!-- nguồn: docs/luan-van/quy-tac-viet.md §4 (mã định danh định nghĩa ở chương 3, gom vào một bảng) -->

**Bảng 3.2.** Mã định danh và ký hiệu dùng trong luận văn

| Mã | Nghĩa | Chi tiết |
|---|---|---|
| F1–F7, N1–N8 | Yêu cầu chức năng; chỉ tiêu nghiệm thu | 3.1 |
| S1, S4 | Cấu hình tĩnh, luôn chạy 1 replica hoặc N replica | 3.3 |
| A1 | Autoscaling theo GPU utilization, target 70%; cấu hình đối chứng theo cách làm phổ biến | 3.3 |
| A2 | Autoscaling theo tải đồng thời của vLLM (request đang xử lý cộng đang chờ); cấu hình vận hành chính thức | 3.3 |
| A3, A4 | Cấu hình phụ theo mức dùng KV cache (A3) và chỉ theo request đang chờ (A4); không chạy trong ĐG2, chỉ dùng khi so sánh tín hiệu và khi thử trên simulator | 3.3 |
| KB1 | Tải thấp, ổn định: 0,5 C trong 12 phút; phân tích pha ổn định (phút 2–12) | 3.6 |
| KB2 | Tải tăng đột ngột: 0,5 C tới phút 4, lên 3,0 C trong 30 giây, giữ tới phút 14, rồi về 0,5 C; 24 phút; pha nền, pha tăng đột ngột, pha giảm | 3.6 |
| KB3 | Tải cao, kéo dài: tăng dần từ 0,5 C lên 3,0 C trong 5 phút rồi giữ tới phút 17; pha tăng dần, pha duy trì | 3.6 |
| ĐG1, ĐG2, ĐG3 | Ba đánh giá trên VM thuê: năng lực một replica; autoscaling so với cấu hình tĩnh (17 lượt); cold start | 3.6 |
| VH1–VH6 | Sáu kịch bản vận hành: scale-down; cập nhật phiên bản; sự cố pod và node; mất nguồn metric; dựng lại từ máy trắng; cảnh báo đúng, không báo giả | 3.6 |
| LT1–LT8 | Tám kiểm chứng lý thuyết: dự đoán bằng công thức trước khi đo, rồi so với số đo | 3.6 |
| L0, L2 | Mức cold start. L0: tải image và model từ Internet mỗi lần tạo pod. L2: kéo sẵn image, đặt model trên NVMe cục bộ, giữ compile cache | 3.4 |
| V0, V1, V2 | Các phiên đo trên VM thuê; V0, V1 là phiên chạy thử, V2 là phiên đo chính | 5.1 |
| C, B\*, N | Ký hiệu. C: năng lực một replica, tốc độ request lớn nhất mà vẫn đạt SLO (req/s). B\*: số request đồng thời trên một replica khi tải bằng C. N: số GPU (N = 4) | 3.3 |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §7 (KB1–KB3: λ/C, thời lượng, pha; KB2 đỉnh 0,75 × N = 3,0 khi N = 4, lên trong [4; 4,5], giữ tới 14, về 0,5 trong [14; 14,5]; KB3 ramp [0, 5], sustain [5, 17]; C = tốc độ request lớn nhất vẫn đạt SLO), §8.1 (S1, S4, A1 target 70, A2 running + waiting là cấu hình vận hành chính thức, A3 KV-cache, A4 chỉ hàng đợi; B\*), §8.2 (17 lượt), §8.3 (ĐG1–ĐG3); docs/nhat-ky/van-hanh.md (LT6: A3, A4 xuất hiện như tín hiệu được so sánh); docs/nhat-ky/lam-viec/trinh/tuan-05.md mục 07/11 TR2 (autoscaling/eval/A3.yaml, A4.yaml cho runner, kiểm trên kind); docs/chi-tiet/00-thong-so.md §8.2 (ma trận ĐG2 chỉ có S1, S4, A1, A2); docs/chi-tiet/05-moi-truong-danh-gia.md §6.1 (V0 smoke, V1 phát triển, V2 đợt chính), §13 (VH1–VH6), §19 (LT1–LT8: dự đoán tính trước khi đo); docs/chi-tiet/03-kien-truc-autoscaling.md §7.1 (L0, L2); docs/luan-van/quy-tac-viet.md §4 (ký hiệu C, B\*, N; tên pha tiếng Việt) -->

Một ô của ma trận đánh giá viết theo dạng cấu hình × kịch bản. Ví dụ, A2 × KB2 là lượt chạy cấu hình A2 với kịch bản tải tăng đột ngột. Mọi mức tải tính theo năng lực C đo ở ĐG1, nên khi phải đổi máy chỉ cần đo lại C, không phải thiết kế lại kịch bản.
<!-- nguồn: docs/luan-van/quy-tac-viet.md §4 (ô ma trận viết "A2 × KB2"); docs/chi-tiet/00-thong-so.md §7 (đơn vị C đo ở ĐG1; λ(t)/C; đỉnh KB2 theo N để chạy được cả máy 2 GPU); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.5 (đổi sang máy khác thì đo lại ĐG1 trên máy mới) -->

### 3.1.3. Yêu cầu chức năng

Bảy yêu cầu chức năng mô tả những gì nền tảng phải làm được (Bảng 3.3). Sáu yêu cầu đầu ở mức Must. Yêu cầu về bảo vệ ở mức Should và đã được thu hẹp trong lúc làm.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §3 (cột Mức), §5 (F1–F6 là Must, F7 là Should) -->

**Bảng 3.3.** Yêu cầu chức năng

| Mã | Yêu cầu | Phép thử | Mức |
|---|---|---|---|
| F1 | Phục vụ một model mở cỡ 3–8B qua API tương thích OpenAI (`/v1/chat/completions`), có streaming | Gọi API có streaming; chạy được ĐG1–ĐG3 | Must |
| F2 | Tự điều chỉnh số replica trong khoảng [1, N] theo tải | Kiểm thử chức năng trên simulator và máy nhà; ĐG2 | Must |
| F3 | Triển khai, cập nhật và rollback qua Git, không thao tác tay trên cluster | VH2 | Must |
| F4 | Dựng toàn bộ nền tảng từ máy trắng bằng vài lệnh `make` | VH5 | Must |
| F5 | Ba dashboard: phục vụ và GPU; autoscaling; SLO và chi phí | Dùng trong mọi lượt đo; ảnh chụp | Must (phần chi phí: Should) |
| F6 | Sáu cảnh báo theo SLO và sức khoẻ nền tảng, gửi tới Telegram; mỗi cảnh báo có runbook | VH6 | Must |
| F7 | Bảo vệ tối thiểu: API key, API không mở ra Internet | Danh sách kiểm tra bảo mật | Should |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §3 (F1–F7, cột "Cách kiểm chứng"; F2 kiểm bằng bài kiểm thử T1–T7 và ĐG2; F7 sửa 12/11), §5 (dashboard chi phí ở mức Should); docs/chi-tiet/05-moi-truong-danh-gia.md §7 (bài kiểm thử T1–T7 chạy trên simulator và máy nhà) -->

Trước phiên đo chính, nhóm lược ba hạng mục mức Should chạy ngầm, không có gì để trình diễn. Đó là giới hạn tốc độ, NetworkPolicy thường trực và bí mật mã hoá trong Git. Yêu cầu bảo vệ vì vậy chỉ còn API key và việc không mở API ra Internet. VM thuê cũng cài các thành phần nền bằng Helm thay cho Argo CD, vì VM bị huỷ sau phiên đo. Trên VM, kịch bản cập nhật phiên bản kích hoạt bằng annotation thay cho Git. Phần cập nhật và rollback qua Git do đó được kiểm ở cluster nhà, nơi Argo CD quản lý mọi thành phần. Mục 6.2 ghi lại các hạng mục đã lược.
<!-- nguồn: docs/adr/006-chot-may-model-va-kich-ban-truoc-v2.md §3.1 (lược Sealed Secrets, NetworkPolicy thường trực, rate limit vì "chạy ngầm, không có gì để trình diễn"; vẫn có API key, API không mở ra Internet; lược Argo CD trên VM thuê vì VM bị huỷ sau V2, VH5 dựng bằng make bootstrap + make cloud-platform; ở nhà làm app autoscaling và observability trên Argo CD trước V2 để mọi thành phần Synced); docs/chi-tiet/01-bai-toan-yeu-cau.md §12.3 mục 10 (trên VM cập nhật bằng annotation, ở nhà qua Git và Argo CD); docs/chi-tiet/05-moi-truong-danh-gia.md §13 (VH2 ở nhà là Must, trên GPU thuê là Should); docs/nhat-ky/van-hanh.md mục 19/11 (VH2 trên VM N = 4) -->

### 3.1.4. SLO và chỉ tiêu nghiệm thu

SLO của dịch vụ đặt trên hai độ trễ người dùng cảm nhận được, TTFT và TPOT, và trên tỷ lệ request lỗi. Một request chỉ được tính là đạt SLO khi cả hai độ trễ đều đạt và request không lỗi. Mục tiêu chính là 95% request đạt SLO, với TTFT không quá 2,5 s (Bảng 3.4).
<!-- nguồn: docs/chi-tiet/00-thong-so.md §6 (bảng SLO) -->

**Bảng 3.4.** Giá trị SLO

| Đại lượng | Giá trị | Ghi chú |
|---|---|---|
| TTFT | ≤ 2,5 s | Trùng biên bucket `le="2.5"` của histogram `vllm:time_to_first_token_seconds` |
| TPOT | ≤ 100 ms | Ít nhất 10 token/s |
| Request đạt SLO | TTFT và TPOT đều đạt, request không lỗi | Lỗi gồm lỗi HTTP, quá thời gian chờ 120 s, stream bị cắt trước khi trả `usage` |
| SLO attainment mục tiêu | 95% request đạt SLO | Ngân sách lỗi 5% |
| Request không trả mã 5xx | 99% | Đo ở Traefik; các lượt đánh giá gọi thẳng Service của vLLM nên không có số này (mục 3.6) |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §6 (TTFT ≤ 2,5 s trùng bucket le="2.5" của v0.31.0, đã kiểm 23/10; TPOT ≤ 100 ms tương đương ít nhất 10 token/s; lỗi gồm lỗi HTTP, timeout, stream bị cắt không có usage; 95%, ngân sách lỗi 5%; 99% không 5xx đo ở Traefik), §7 (timeout 120 s, stream_options.include_usage=true; sửa 21/11: lượt đánh giá gọi thẳng Service, tỷ lệ 5xx ở Traefik không có dữ liệu); docs/chi-tiet/05-moi-truong-danh-gia.md §13 (giới hạn của VH6) -->

Ngưỡng TPOT 100 ms cho ít nhất 10 token/s, nhanh hơn tốc độ đọc của người dùng. Bản thiết kế đầu đặt ngưỡng TTFT 2 s cho nghiệm thu, trong khi quy tắc tính tỷ lệ request xấu cho cảnh báo dùng biên bucket 2,5 s. Hai ngưỡng lệch nhau sẽ cho hai kết luận khác nhau về cùng một khoảng thời gian, nên nhóm giữ một ngưỡng 2,5 s cho cả cảnh báo và nghiệm thu. Ngưỡng này trùng một biên bucket có thật của histogram TTFT trong bản vLLM đã ghim (mục 3.5).
<!-- nguồn: docs/chi-tiet/00-thong-so.md §6 (TPOT nhanh hơn tốc độ đọc; TTFT phải trùng biên bucket có thật, cảnh báo và nghiệm thu dùng cùng ngưỡng); docs/adr/005-sua-thiet-ke-sau-review.md T3 (ngưỡng TTFT 2 s trong khi recording rule dùng bucket 2,5; chốt một ngưỡng trùng biên bucket cho cả N7 lẫn N1); common/observability/rules/slo.yaml (le="2.5") -->

Tám chỉ tiêu nghiệm thu đặt ngưỡng cho chất lượng, tốc độ phản ứng, hiệu quả GPU và độ an toàn khi vận hành (Bảng 3.5). Nhiều chỉ tiêu chỉ áp cho một pha của kịch bản tải, vì mỗi pha kiểm một hành vi khác nhau của nền tảng. Các chỉ tiêu mức Must gồm SLO attainment ở tải thấp và tải cao kéo dài, thời gian có replica mới, không rớt request khi thay đổi, và khả năng tự phục hồi.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (N1–N8), §7 (cột "Kiểm chứng chủ yếu" theo pha) -->

**Bảng 3.5.** Chỉ tiêu nghiệm thu

| Mã | Chỉ tiêu | Phép thử | Mức |
|---|---|---|---|
| N1 | Với A2: SLO attainment ≥ 95% ở pha ổn định của KB1 và pha duy trì của KB3. Ở KB2 chỉ báo cáo | ĐG2 | Must |
| N2a | Ở KB2, mức cold start L2: từ lúc tải tăng tới khi replica mới đầu tiên Ready ≤ 2 phút | ĐG2 | Must |
| N2b | Ở KB2: thời gian hồi phục SLO, chỉ báo cáo | ĐG2 | Should |
| N3 | Ở KB1: A2 dùng ≤ 50% GPU-giờ của S4, SLO attainment kém S4 không quá 5 điểm phần trăm. Ở KB2: báo cáo mức tiết kiệm và cái giá về SLO | ĐG2 | Should |
| N4 | 0 request lỗi do scale-down (pha giảm của KB2, VH1) và do cập nhật phiên bản (VH2, gồm ca chỉ có 1 replica) | ĐG2, VH1, VH2 | Must |
| N5 | Cold start ở mức L2 ≤ 50% so với L0 | ĐG3 | Should |
| N6 | Pod hỏng được thay tự động; mất Prometheus thì KEDA chuyển sang fallback (số replica tối đa) trong ≤ 30 s; dựng lại từ VM trắng ≤ 30 phút | VH3, VH4, VH5 | Must |
| N7 | Cảnh báo SLO kích hoạt ≤ 5 phút sau khi SLO bị vi phạm thật (S1 × KB3); không có page giả khi A2 chạy KB1 và KB3 | VH6 | Should |
| N8 | Mọi phiên bản được ghim; người thứ hai dựng lại cluster nhà, hoặc cluster kind với simulator, theo README trong < 1 giờ; tiền thuê GPU ≤ 150 USD | VH5, sổ chi phí | Should |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (N1–N8, cột "Đo bằng" và "Mức"; VM trắng = VM Ubuntu từ template của Vast, có sẵn driver NVIDIA, chưa có image, model hay cluster), §5 (Must: N1, N2a, N4, N6; Should: N2b, N3, N5, N7, N8) -->

Hai khái niệm trong bảng cần nói rõ thêm. VM trắng ở chỉ tiêu dựng lại là VM Ubuntu có sẵn driver NVIDIA, chưa có image, model hay cluster. Page giả và cách chấm cảnh báo được định nghĩa ở mục 3.6, cùng với các phép thử khác.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (N6: định nghĩa VM trắng; N7: định nghĩa page giả); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (3.6: cách chấm cảnh báo, định nghĩa page giả) -->

Các ngưỡng chất lượng chỉ áp cho phần tải mà một hệ thống có cold start đáp ứng được. Mức 95% là mức SLO phổ biến cho dịch vụ nội bộ. Nhóm không áp mức này cho kịch bản tải tăng gấp 6 lần trong 30 giây, vì khi đó hệ thống nào có cold start cũng vi phạm SLO trong vài phút. Với tải cao kéo dài, chỉ pha duy trì được tính, vì trong pha tăng dần pod đầu tiên chắc chắn quá tải trong lúc chờ replica mới. Thời gian hồi phục sau tải tăng đột ngột chỉ được báo cáo. Request đã dồn trong hàng đợi của pod cũ không chuyển được sang pod mới. Vì vậy thời gian này phụ thuộc nhiều vào mức quá tải trước đó, và mức dự kiến 5 phút không được dùng để chấm đạt hay không.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (mục "Vì sao chọn các ngưỡng này": 95% phổ biến cho dịch vụ nội bộ; không áp cho KB2 vì tải tăng gấp 6 lần trong 30 giây; KB3 chỉ tính sustain; N2b chỉ báo cáo, ngưỡng dự kiến ≤ 5 phút là tạm), §7 (KB2 từ 0,5 lên 3,0 trong [4; 4,5]) -->

Các ngưỡng thời gian và tài nguyên tính từ đặc điểm của chính nền tảng. Ngưỡng 2 phút cho replica mới đầu tiên gồm cold start ở mức L2, dự kiến 0,5–1,5 phút, cộng khoảng 10 giây để phát hiện tải tăng. Ngưỡng 50% GPU-giờ dựa trên việc ở 0,5 C, autoscaling chỉ cần 1 trong 4 GPU. Phần chênh so với 25% chừa cho thời gian GPU bị giữ lúc khởi động và lúc chờ ổn định. Ngưỡng 30 phút để dựng lại được đặt khi nhóm còn dự kiến dùng model 7B, đủ để cài k3s, các thành phần nền và tải khoảng 15 GB weights. Model 3B dùng khi đo chỉ khoảng 6 GB, nên nhóm giữ nguyên ngưỡng này.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (mục "Vì sao chọn các ngưỡng này": 2 phút = cold start L2 dự kiến 0,5–1,5 phút cộng khoảng 10 giây phát hiện; 50% vì ở 0,5C chỉ cần 1 trong 4 GPU, chừa chỗ cho thời gian giữ GPU lúc khởi động và chờ ổn định; 30 phút đủ cài k3s, GPU, Argo CD và tải model khoảng 15 GB). docs/adr/006-chot-may-model-va-kich-ban-truoc-v2.md §1 (ADR-004 ngày 08/10 giả định model 7B), C3 (đổi sang Qwen2.5-3B); docs/chi-tiet/02-kien-thuc-nen.md §1.5 (model 3B ≈ 6,17 GB ở BF16); trên VM thuê các thành phần nền cài bằng helm, không bằng Argo CD (ADR-006 §3.1), nên câu văn ghi "các thành phần nền" -->

Mọi ngưỡng ở Bảng 3.4 và Bảng 3.5 được đặt trước phiên đo chính và giữ nguyên sau khi có kết quả. Chỉ tiêu nào không đạt sẽ được báo cáo là không đạt, kèm nguyên nhân đo được (chương 5). Quy tắc để kết luận hai cấu hình khác nhau, và điều kiện để một lượt đo hợp lệ, nằm ở mục 3.6.
<!-- nguồn: git log -L của docs/chi-tiet/00-thong-so.md (các dòng N1, N2a, N2b, N3, N4, N5, N6, N7, N8, TPOT, mục tiêu 95%, tỷ lệ lỗi 99% không đổi từ commit 8dde92c ngày 08/10; dòng TTFT chỉ đổi phần ghi chú ở acfa7c8 ngày 10/11, giá trị 2,5 s giữ nguyên); docs/nhat-ky/van-hanh.md mục 18/11 và 19/11 (phiên V2 thật chạy 18–19/11). Ghi chú: 00-thong-so.md vẫn gắn nhãn "tạm" cho TTFT 2,5 s và N2b, chờ ADR-003; ADR-003 chưa viết (docs/luan-van/nguon-tu-lieu.md §4), các giá trị tạm được dùng nguyên trong V2; docs/chi-tiet/00-thong-so.md §1 (không chỉnh sau khi đã thấy kết quả), §6 (ngưỡng thực tiễn khi so sánh hai cấu hình) -->
