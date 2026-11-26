<!-- Mục đích: mục 2.2 của luận văn (Hàng đợi và năng lực phục vụ): tải mở và tải đóng, định luật Little áp cho một replica vLLM, độ trễ theo mức sử dụng (M/M/1), năng lực dùng được C và B*, vì sao không chạy GPU sát giới hạn. Bản base lượt 1. Người viết: Trình. Viết ngày 27/11/2026 từ docs/chi-tiet/01-bai-toan-yeu-cau.md §3, docs/chi-tiet/03-kien-truc-autoscaling.md §10.2, phần lý thuyết của LT5 trong docs/nhat-ky/van-hanh.md và tài liệu trong tai-lieu.bib. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Hình đánh số theo chương: Hình 2.2 (độ trễ theo mức tải). -->
<!-- Ý không đưa vào, để chỗ khác: số đo LT5 (lệch Little ≤ 2% ở nhà, −5,8…+4,9% ở 24 cửa sổ V2) để mục 5.2 hoặc 5.3; công thức edge của cửa sổ hữu hạn và SE do lấy mẫu 5 s (van-hanh.md LT5) bỏ, chỉ người làm cần; cách chọn threshold 0,8 × B* để mục 3.3; mô hình M/G/∞ và util ≈ 1 − e^(−L) để mục 2.3 (LT6); mức ρ 0,7–0,85 của Bài toán §3 bỏ vì không có nguồn chung, chương 3 tự chọn hệ số. -->
<!-- Thông điệp: (1) Theo định luật Little, số request đang chạy cộng đang chờ trên một replica bằng tốc độ đến nhân thời gian lưu lại, nên tỷ lệ với tải khi chưa quá tải và tăng nhanh hơn tải khi đã quá tải. (2) Độ trễ tăng vọt khi gần giới hạn throughput, nên năng lực dùng được C nhỏ hơn throughput tối đa và hệ thống phải luôn giữ năng lực dư. -->
<!-- Soát số: chưa · Soát văn phong: kiem_van 27/11 · Người viết đọc lại: chưa -->
## 2.2. Hàng đợi và năng lực phục vụ

Một replica vLLM nhận request đến ngẫu nhiên, giữ mỗi request một khoảng thời gian rồi trả kết quả, nên có thể phân tích như một hàng đợi. Mục này dùng hai kết quả của lý thuyết hàng đợi. Định luật Little nối số request đồng thời với tốc độ đến. Đường cong độ trễ theo mức tải giải thích vì sao một replica không thể chạy sát throughput tối đa của nó.

**Tải mở và tải đóng.** Ký hiệu λ là tốc độ đến, tính bằng req/s. Request của nhiều người dùng đến độc lập với nhau. Mô hình thường dùng cho dòng request như vậy là quá trình Poisson: khoảng cách giữa hai request liên tiếp có phân phối mũ, và số request trong một khoảng thời gian dao động quanh giá trị trung bình. Ví dụ minh hoạ, với λ = 3 req/s, một cửa sổ 10 s có trung bình 30 request, với độ lệch chuẩn khoảng 5,5 request. Schroeder và cộng sự phân biệt hai cách sinh tải khi đánh giá hệ thống [@schroeder-open-closed]. Ở mô hình đóng, request mới chỉ được gửi khi một request cũ đã xong. Ở mô hình mở, request đến theo lịch riêng, không phụ thuộc lúc các request khác xong. Hai mô hình cho kết quả khác nhau nhiều trong thực tế.

<!-- nguồn: tóm tắt Schroeder và cộng sự, NSDI 2006 (mô hình đóng, mô hình mở; khác nhau nhiều trong thực tế); docs/chi-tiet/05-moi-truong-danh-gia.md §8 bước 6 (số request đến dao động Poisson); √30 ≈ 5,48 -->

Với mô hình đóng, hệ thống chậm đi thì tải tự giảm theo, và hàng đợi không bao giờ dài quá số người dùng ảo. Người dùng một dịch vụ LLM không chờ người khác xong mới gửi câu hỏi. Mô hình mở vì vậy gần với tải thật hơn, và mục 3.6 dùng mô hình này.

<!-- nguồn: tóm tắt Schroeder, Wierman, Harchol-Balter, NSDI 2006 (usenix.org/events/nsdi06/tech/schroeder.html, đọc 27/11/2026: closed system model, new job arrivals only triggered by job completions; open system model, new jobs arrive independently of job completions; vast difference in behavior between open and closed models in real-world settings); docs/chi-tiet/05-moi-truong-danh-gia.md §8 bước 6 (số request đến dao động Poisson); docs/mo-ta-chi-tiet-do-an.md tài liệu [19]. Tính minh hoạ: Poisson trung bình λt = 30, độ lệch chuẩn √30 ≈ 5,48. "Tải tự giảm, hàng đợi không dài ra" suy ra trực tiếp từ định nghĩa mô hình đóng: số request trong hệ thống không vượt số người dùng ảo -->

**Định luật Little.** Gọi L là số request trung bình có mặt trong hệ thống và W là thời gian trung bình mỗi request lưu lại trong đó. Với một hệ thống ở trạng thái dừng,

$$
L = \lambda W.
$$

Định luật đúng mà không cần giả định gì về phân phối của dòng đến, phân phối thời gian phục vụ hay thứ tự phục vụ [@little-law]. Ví dụ, nếu request đến với λ = 2 req/s và mỗi request lưu lại trung bình 10 s thì trong hệ thống luôn có trung bình 20 request.

<!-- nguồn: Little 1961 (metadata kiểm qua Crossref 27/11/2026). Ví dụ: 2 × 10 = 20 -->

Áp cho một replica vLLM, L là số request đang chạy cộng số request đang chờ, hai metric ở Bảng 2.1, còn W là thời gian từ khi request đến vLLM tới khi xong. Khi replica chưa quá tải, request vào batch ngay, và W gần bằng thời gian sinh hết câu trả lời. Thời gian này phụ thuộc độ dài câu trả lời và chỉ tăng chậm theo kích thước batch (mục 2.1.1). Do đó L tăng gần tỷ lệ với λ. Khi replica đã quá tải, W cộng thêm thời gian chờ trong hàng đợi và tăng theo tải, nên L tăng nhanh hơn λ. Tải đồng thời vì vậy đo được cả hai trạng thái: tỷ lệ với tải khi hệ thống còn đáp ứng được, và tăng vọt khi hệ thống bắt đầu không đáp ứng được. Mục 3.3 dựa trên tính chất này để chọn tín hiệu scale.

<!-- nguồn: Little 1961 (Operations Research 9(3):383–387, metadata kiểm qua Crossref 27/11/2026; L = λW cho hệ dừng, không phụ thuộc phân phối và thứ tự phục vụ); docs/chi-tiet/03-kien-truc-autoscaling.md §10.2 ("Cơ sở lý thuyết: định luật Little": số request trong hệ thống = tốc độ đến × thời gian lưu lại; chưa quá tải thì B tỷ lệ với λ; quá tải thì B tăng nhanh hơn λ); docs/nhat-ky/van-hanh.md LT5 (lý thuyết: A2 dùng chính L = Σ_pod (running + waiting)); 03-03 trên nhánh chương 3 (dẫn mục 2.2 cho định luật Little). Ví dụ: 2 × 10 = 20 -->

Định luật nói về giá trị trung bình trên một khoảng thời gian đủ dài. Trong một cửa sổ ngắn, ngay sau khi tải đổi, hoặc khi hàng đợi đang dài ra không ngừng, số request đo được lệch khỏi λW, vì một phần request đến trong cửa sổ chưa kịp rời đi. Khi kiểm định luật bằng số đo, cần chọn cửa sổ mà hệ thống ở trạng thái dừng.

<!-- nguồn: docs/nhat-ky/van-hanh.md LT5 (cửa sổ hữu hạn: L_client = λ_thực × W + edge; hệ dừng thì edge ≈ 0, hàng đợi đang tăng thì edge < 0), LT3 (λ = 8 ở nhà lệch 11% vì hàng đợi tăng liên tục, không ở trạng thái dừng); docs/chi-tiet/05-moi-truong-danh-gia.md §8 bước 6 -->

**Độ trễ theo mức sử dụng.** Gọi μ là throughput tối đa của một replica, tức số request mỗi giây mà nó xử lý được khi luôn có việc. Mức sử dụng là ρ = λ/μ. Với hàng đợi M/M/1, mô hình đơn giản nhất gồm dòng đến Poisson và một server có thời gian phục vụ phân phối mũ, thời gian trung bình một request lưu lại là [@harchol-balter-queueing]

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §3 (μ, λ, ρ = λ/μ, công thức M/M/1); Harchol-Balter 2013 -->

$$
W = \frac{1}{\mu - \lambda} = \frac{1/\mu}{1 - \rho}.
$$

Công thức cho thấy độ trễ không tăng đều theo tải. Ở ρ = 0,5, một request lưu lại gấp 2 lần thời gian phục vụ thuần 1/μ. Ở ρ = 0,8 là 5 lần, và ở ρ = 0,9 là 10 lần: thêm 10 điểm phần trăm tải làm độ trễ tăng gấp đôi. Khi λ ≥ μ, hàng đợi dài ra mãi, và hệ thống không tự hồi phục cho tới khi tải giảm.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §3 (μ, λ, ρ = λ/μ; M/M/1: W = 1/(μ − λ) = (1/μ)/(1 − ρ); ρ từ 0,8 lên 0,9 làm thời gian chờ tăng gấp đôi; λ > μ thì hàng đợi tăng mãi, không tự hồi phục cho tới khi tải giảm); Harchol-Balter 2013 (M/M/1). Tính: 1/(1 − 0,5) = 2; 1/(1 − 0,8) = 5; 1/(1 − 0,9) = 10 -->

Một replica vLLM khác M/M/1 ở hai điểm. Thứ nhất, nó giống một hệ có nhiều chỗ phục vụ song song, mỗi chỗ trong batch là một chỗ, và mỗi chỗ chậm đi một chút khi batch đông hơn. Throughput tối đa μ vì vậy chỉ đạt được khi batch đã đầy. Thứ hai, thời gian phục vụ phụ thuộc độ dài prompt và câu trả lời. Dù vậy, đường cong độ trễ vẫn có dạng "đầu gối" như Hình 2.2. Khi batch còn chỗ, request mới vào ngay và TTFT gần bằng thời gian prefill. Khi batch đã đầy, phần request dư vào hàng đợi, và TTFT tăng nhanh trong khi TPOT của các request đang chạy gần như đứng yên.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §3 (LLM serving khác M/M/1 ở hai điểm: μ tăng theo kích thước batch, thời gian phục vụ phụ thuộc độ dài; hình dạng đầu gối giữ nguyên); docs/nhat-ky/van-hanh.md LT3 (lý thuyết: quá điểm gãy TTFT tăng vọt trong khi TPOT đứng yên) -->

![Hình 2.2. TTFT p95 theo tốc độ request đến trên một replica (minh hoạ, vẽ từ mô hình hàng đợi đơn giản). Từ trái sang phải: vùng đạt SLO; vùng vi phạm SLO dù replica vẫn chạy, giữa năng lực dùng được C và throughput tối đa μ; vùng quá tải, hàng đợi tăng mãi.](../images/png/10-do-tre-theo-muc-tai.png)

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §3 (LLM serving khác M/M/1: μ tăng theo kích thước batch tới khi đầy, thời gian phục vụ phụ thuộc độ dài request; hình dạng đầu gối giữ nguyên; Hình 10 vẽ từ mô hình hàng đợi đơn giản để minh hoạ, đường cong thật đo ở bước đo năng lực); docs/images/png/10-do-tre-theo-muc-tai.png (C ≈ 2,1, μ = 2,4, minh hoạ); docs/nhat-ky/van-hanh.md LT3 (lý thuyết: throughput tăng gần tuyến tính rồi bão hoà ở điểm gãy; quá điểm gãy TTFT tăng vọt trong khi TPOT đứng yên); docs/chi-tiet/02-kien-thuc-nen.md §2.8 (num_requests_waiting bằng 0 khi chưa quá tải) -->

Hình 2.2 dẫn tới khái niệm năng lực dùng được của một replica, ký hiệu C: tốc độ đến lớn nhất mà replica vẫn đạt mục tiêu chất lượng phục vụ (mục 2.5). C luôn nhỏ hơn μ, vì gần μ thời gian chờ trong hàng đợi đã vượt ngưỡng TTFT cho phép. Số request đồng thời trung bình khi λ = C ký hiệu là B\*. Theo định luật Little, B\* bằng C nhân thời gian lưu lại tại mức tải đó. Như vậy B\* là mức tải đồng thời mà một replica gánh được mà chưa vi phạm chất lượng. Chương 3 suy ra threshold scale từ B\*, còn mục 5.2 đo C và B\* trên GPU của đồ án.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §3 ("năng lực dùng được C (tốc độ lớn nhất còn đạt SLO) luôn nhỏ hơn μ"); docs/luan-van/quy-tac-viet.md §4 (ký hiệu: C = năng lực một replica, req/s; B* = số request đồng thời ở mức năng lực; λ = tốc độ đến); docs/chi-tiet/05-moi-truong-danh-gia.md §8 bước 6 (B* ≈ λ_thực × E2E tại C); 05-02 trên nhánh chương 5 (C, B*, threshold A2 suy từ B*) -->

Từ hai kết quả trên, hệ thống phục vụ không thể cho mỗi replica chạy sát μ, kể cả khi tải trung bình biết trước. Lý do thứ nhất là đầu gối của đường cong: chỉ thêm một phần nhỏ tải là độ trễ vượt ngưỡng. Lý do thứ hai là dòng đến dao động, nên tải trung bình dưới C vẫn có những đợt ngắn vượt C. Lý do thứ ba là thêm năng lực không có ngay, vì replica mới phải nạp weights lên GPU trước khi phục vụ được. Vì vậy phải luôn giữ một phần năng lực dư. Câu hỏi còn lại là giữ dư bao nhiêu và vào lúc nào, và autoscaling (mục 2.4) là cách điều chỉnh lượng dư đó theo tải. Mức sử dụng ρ ở đây là tỷ lệ giữa tốc độ đến và throughput tối đa. Nó khác chỉ số GPU utilization mà công cụ giám sát GPU báo, và mục 2.3 cho thấy chỉ số này đạt gần 100% khi ρ còn thấp.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §3 ("Hệ quả thực tế": phải luôn có dư năng lực; dư bao nhiêu và vào lúc nào; autoscaling điều chỉnh lượng dư theo thời gian), §5.2 (cold start tính bằng phút, nạp weights); docs/nhat-ky/van-hanh.md LT6 (lý thuyết: GPU util là tỷ lệ thời gian có kernel chạy; util ≈ 1 − e^(−L), bão hoà khi L mới bằng khoảng 1/6 B*), LT3 (GPU util 89% ở λ = 1, 100% từ λ = 2 ở nhà) -->
