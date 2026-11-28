<!-- Mục đích: phần Mở đầu của luận văn (không đánh số), bản base lượt 1. Người viết: Trình. Viết ngày 27/11/2026 theo dàn ý ở docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (dòng Mở đầu, 1,5–2 trang) và docs/luan-van/quy-tac-viet.md §1 (mục 5 của thứ tự các phần), §2 (Mở đầu không có số đo, trích dẫn chi tiết, thuật ngữ chưa giải thích). Quy ước: docs/luan-van/README.md (file 00-00-mo-dau.md) -->
<!-- Thông điệp: (1) Ở mức người không chuyên: tự chạy LLM trên GPU thì tốn tiền theo giờ, còn tải thay đổi theo giờ, nên cần autoscaling; nhưng cách làm của web không áp nguyên được, và hệ thống còn phải vận hành được hằng ngày. (2) Đồ án ghép phần mềm mã nguồn mở thành một nền tảng như vậy, rồi đo nó trên máy thuê, nêu cả chỗ chưa đạt. (3) Luận văn gồm sáu chương, mỗi chương trả lời một câu hỏi. Thuật ngữ dùng lần đầu trong cả quyển ở đây (LLM, replica, request, autoscaling, GPU-giờ) được giải thích theo quy-tac-viet §4. -->
<!-- Soát số: không có số đo · Soát văn phong: kiem_van 27/11 · Người viết đọc lại: chưa -->
# Mở đầu {.unnumbered}

Nhiều tổ chức muốn dùng mô hình ngôn ngữ lớn (*large language model*, LLM) cho công việc nội bộ, như hỏi đáp tài liệu hay soạn thảo văn bản. Tổ chức không được gửi dữ liệu ra dịch vụ bên ngoài thì phải tự chạy một model mã nguồn mở trên máy chủ có GPU, của mình hoặc thuê theo giờ. GPU là phần cứng đắt nhất của hệ thống này, và bị tính tiền cả những giờ không có ai dùng. Lượng người dùng lại thay đổi theo giờ: đông vào giờ làm việc, gần như vắng hẳn ban đêm, có lúc tăng vọt trong vài phút.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §4 (bối cảnh giả định: doanh nghiệp tự host, GPU tính theo giờ), §2 (đặc điểm của tải thực tế: chu kỳ ngày đêm, đợt tăng đột ngột); mục 1.1 của luận văn (01-01) trình bày đầy đủ, ở đây chỉ dẫn dắt -->

Mỗi bản của model đang chạy gọi là một replica, và chiếm trọn một GPU. Giữ cố định một số replica thì phải chọn giữa hai điều không tốt. Giữ ít thì vào giờ cao điểm, mỗi câu hỏi người dùng gửi tới model (một request) phải chờ lâu mới có câu trả lời. Giữ đủ cho giờ cao điểm thì phần lớn thời gian số GPU đó chạy không mà vẫn tốn tiền. Cách giải quen thuộc là để hệ thống tự động điều chỉnh số replica theo tải (*autoscaling*), thêm khi đông người và bớt khi vắng.

Autoscaling đã thành thông lệ với ứng dụng web, nhưng LLM trên GPU có ba khác biệt khiến cách làm đó không áp nguyên được. Một replica mới cần hàng phút để khởi động, trong khi ứng dụng web chỉ cần vài giây. Chỉ số quen dùng để đo độ bận của GPU báo gần đầy ngay khi tải còn thấp, nên scale theo nó sẽ thêm GPU khi chưa cần. Mỗi câu trả lời được sinh và gửi dần về trong nhiều giây. Tắt một replica không đúng cách sẽ cắt ngang câu trả lời mà người dùng đang đọc.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §5 (cold start tính bằng phút, GPU utilization bão hoà sớm, request dài có streaming); quy-tac-viet §4 (replica: một bản sao pod vLLM, mỗi bản dùng 1 GPU; autoscaling: tự động điều chỉnh số replica theo tải); mục 1.1 (01-01), 2.3 (02-03) -->

Autoscaling mới giải quyết một nửa bài toán. Hệ thống còn phải để một nhóm nhỏ vận hành được hằng ngày. Cập nhật phiên bản không được làm gián đoạn người dùng. Khi chất lượng phục vụ giảm, người trực phải được báo kịp thời và có sẵn hướng dẫn xử lý. Khi một máy hỏng, toàn bộ hệ thống phải dựng lại được từ phần mô tả lưu trong kho mã. Vì vậy đồ án coi đây là một bài toán vận hành, với ba yêu cầu kéo nhau. Ba yêu cầu đó là người dùng không phải chờ lâu, hệ thống không giữ GPU thừa, và vận hành được hằng ngày.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §6 (phát biểu bài toán, ba yêu cầu kéo nhau); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (xương sống) -->

Đồ án xây dựng và vận hành một nền tảng như vậy từ các phần mềm mã nguồn mở phổ biến. Model chạy trên vLLM, phần mềm chuyên phục vụ LLM trên GPU. Kubernetes, nền tảng quản lý ứng dụng trên một cụm máy, giữ các replica và cấp cho mỗi replica một GPU. Nhóm cho hệ thống scale theo số request mà vLLM đang xử lý và đang chờ, thay cho độ bận của GPU. Thời gian khởi động được rút ngắn bằng cách chuẩn bị sẵn phần mềm và model trên máy. Trước khi tắt, mỗi replica có thời gian trả lời xong các request đang dở. Hệ thống có cảnh báo theo mục tiêu chất lượng, kèm hướng dẫn xử lý cho người trực. Các tệp mô tả hệ thống nằm trong Git, công cụ quản lý phiên bản mã nguồn, và cụm máy của nhóm tự cập nhật theo kho Git đó.

<!-- nguồn: docs/chi-tiet/03-kien-truc-autoscaling.md (thành phần, tín hiệu A2 = running + waiting, L2, graceful shutdown, cảnh báo burn rate, GitOps với Argo CD); docs/chi-tiet/00-thong-so.md F4 (Argo CD ở cluster nhà; VM thuê dựng bằng make cloud-platform, helm; Sealed Secrets và Argo CD trên VM thuê đã lược), Kế hoạch §11.1 TĐ3 ("ở cluster nhà, mọi thành phần do Argo CD quản lý từ Git"); mục 3.2–3.5 của luận văn -->

Nhóm đánh giá nền tảng trên một VM thuê có bốn GPU. Máy tạo tải (*load generator*) sinh request theo ba mẫu tải điển hình: tải thấp ổn định, tải tăng đột ngột, và tải tăng dần rồi giữ ở mức cao. Với mỗi mẫu tải, nhóm so autoscaling với cách giữ cố định số replica theo hai thước đo. Thước đo thứ nhất là tỷ lệ request đạt mục tiêu độ trễ. Thước đo thứ hai là số GPU-giờ, bằng số GPU bị giữ nhân với thời gian giữ.

Nhóm cũng chạy các tình huống vận hành. Khi cập nhật phiên bản, xoá một replica đang phục vụ hay mất nguồn số liệu giám sát, nhóm kiểm xem có request nào bị rớt không. Nhóm còn đo thời gian dựng lại hệ thống từ máy trắng, và kiểm riêng xem cảnh báo có báo kịp khi chất lượng giảm và có báo giả hay không. Luận văn nêu cả những chỗ nền tảng chưa đạt mục tiêu, kèm nguyên nhân đo được và hướng sửa.

<!-- nguồn: docs/chi-tiet/00-thong-so.md (tải open-loop, Poisson với tốc độ λ(t); KB1 ổn định, KB2 tăng đột ngột, KB3 tăng dần rồi duy trì; S4 tĩnh, A2; VH2 cập nhật, VH3 xoá pod, VH4 mất Prometheus: N4, N6 tính theo request lỗi; VH5 dựng lại: N6 tính theo thời gian; VH6 cảnh báo: N7); quy-tac-viet §4 (GPU-giờ: số GPU bị giữ nhân thời gian giữ); mục 3.6, 5.1 (V2, 4 × RTX 4060 Ti); "bốn GPU" là cấu hình máy, không phải số đo -->

Ngoài phần Mở đầu, luận văn gồm sáu chương.

**Chương 1. Giới thiệu** phát biểu bài toán vận hành với ba yêu cầu kéo nhau. Chương này cũng đặt mục tiêu và phạm vi theo đề cương, mô tả cách nhóm tổ chức thực hiện, và tóm tắt các đóng góp chính kèm kết quả đo.

**Chương 2. Cơ sở lý thuyết và giải pháp liên quan** giải thích cách LLM sinh câu trả lời trên GPU và vì sao một replica không nên chạy sát giới hạn. Chương này cũng trình bày cách Kubernetes cấp GPU, cơ chế autoscaling, cách vận hành theo mục tiêu chất lượng và triển khai qua Git. Cuối chương so đồ án với các giải pháp liên quan.

**Chương 3. Yêu cầu và thiết kế** nêu hệ thống cần đáp ứng những gì, với chỉ tiêu nghiệm thu đo được, và thiết kế từng phần để đáp ứng. Mỗi lựa chọn thiết kế, từ tín hiệu scale tới cách cảnh báo, đi kèm lý do và phương án đã cân nhắc. Chương kết thúc bằng thiết kế cách đánh giá.

**Chương 4. Triển khai và vận hành** kể nhóm đã dựng từng phần thế nào, gặp sự cố gì, lệch thiết kế ở đâu và kiểm chứng ra sao. Cuối chương có bảng đối chiếu các khó khăn riêng của GPU và LLM với cách nhóm xử lý.

**Chương 5. Đánh giá** trình bày số đo trên VM thuê và so với chỉ tiêu của chương 3. Các phép đo gồm năng lực của một replica, autoscaling so với cấu hình cố định, thời gian khởi động và các tình huống vận hành. Chương này nêu rõ giới hạn của nền tảng khi tải tăng đột ngột, và các hạn chế của phép đo.

**Chương 6. Kết luận và hướng phát triển** rút ba kết luận từ kết quả đánh giá và nêu các hạn chế còn lại của hệ thống. Chương này đề xuất hướng làm tiếp, mỗi hướng xuất phát từ một phát hiện của chương 5.

Phụ lục chứa phần người muốn làm lại cần tra cứu. Đó là tệp cấu hình chính, quy tắc cảnh báo, hướng dẫn xử lý sự cố mẫu và phiên bản phần mềm. Phụ lục cũng có số liệu của từng lượt đo, kế hoạch và phân công.

<!-- nguồn: đoạn mở đầu của từng chương (01-00, 02-00, 03-00, 05-00, 06-00 trên nhánh docs/tr8-thesis-ch*); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (dòng từng chương, Phần cuối: Phụ lục A–F; kết chương 4 có bảng vấn đề riêng của GPU/LLM) -->
