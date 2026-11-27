<!-- Mục đích: phần Mở đầu của luận văn (không đánh số), bản base lượt 1. Người viết: Trình. Viết ngày 27/11/2026 theo dàn ý ở docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (dòng Mở đầu, 1,5–2 trang) và docs/luan-van/quy-tac-viet.md §1 (mục 5 của thứ tự các phần), §2 (Mở đầu không có số đo, trích dẫn chi tiết, thuật ngữ chưa giải thích). Quy ước: docs/luan-van/README.md (file 00-00-mo-dau.md) -->
<!-- Thông điệp: (1) Ở mức người không chuyên: tự chạy LLM trên GPU thì tốn tiền theo giờ, còn tải thay đổi theo giờ, nên cần tự thêm bớt GPU; nhưng cách làm của web không áp nguyên được, và hệ thống còn phải vận hành được hằng ngày. (2) Đồ án ghép phần mềm mã nguồn mở thành một nền tảng như vậy, rồi đo nó trên máy thuê, nêu cả chỗ chưa đạt. (3) Luận văn gồm sáu chương, mỗi chương trả lời một câu hỏi. -->
<!-- Soát số: không có số đo · Soát văn phong: kiem_van 27/11 · Người viết đọc lại: chưa -->
# Mở đầu {.unnumbered}

Nhiều tổ chức muốn dùng mô hình ngôn ngữ lớn (*large language model*, LLM) cho công việc nội bộ, như hỏi đáp tài liệu hay soạn thảo văn bản. Khi không được gửi dữ liệu tới dịch vụ của nhà cung cấp bên ngoài, tổ chức phải tự chạy một model mã nguồn mở trên máy chủ có GPU, của mình hoặc thuê theo giờ. GPU là phần cứng đắt nhất của hệ thống này, và bị tính tiền cả những giờ không có ai dùng. Lượng người dùng lại thay đổi theo giờ: đông vào giờ làm việc, gần như vắng hẳn ban đêm, có lúc tăng vọt trong vài phút.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §5, §6 (bối cảnh doanh nghiệp tự host, tải thay đổi theo giờ); mục 1.1 của luận văn (01-01) trình bày đầy đủ, ở đây chỉ dẫn dắt -->

Giữ cố định một số GPU thì phải chọn giữa hai điều không tốt. Giữ ít GPU thì vào giờ cao điểm người dùng phải chờ lâu mới nhận được câu trả lời. Giữ đủ GPU cho giờ cao điểm thì phần lớn thời gian số GPU đó chạy không mà vẫn tốn tiền. Cách giải quen thuộc là để hệ thống tự thêm bản chạy của model khi đông người và tự bớt khi vắng, gọi là autoscaling.

Autoscaling đã thành thông lệ với ứng dụng web, nhưng LLM trên GPU có ba khác biệt khiến cách làm đó không áp nguyên được. Một bản chạy mới cần hàng phút để khởi động, trong khi ứng dụng web chỉ cần vài giây. Chỉ số quen dùng để đo độ bận của GPU báo gần đầy ngay khi tải còn thấp, nên scale theo nó sẽ thêm GPU khi chưa cần. Mỗi câu trả lời được sinh và gửi dần về trong nhiều giây. Tắt một bản chạy không đúng cách sẽ cắt ngang câu trả lời mà người dùng đang đọc.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §5 (cold start tính bằng phút, GPU utilization bão hoà sớm, request dài có streaming); mục 1.1 (01-01), 2.3 (02-03) -->

Tự thêm bớt GPU mới giải quyết một nửa bài toán. Hệ thống còn phải để một nhóm nhỏ vận hành được hằng ngày. Cập nhật phiên bản không được làm gián đoạn người dùng. Khi chất lượng phục vụ giảm, người trực phải được báo kịp thời và có sẵn hướng dẫn xử lý. Khi một máy hỏng, toàn bộ hệ thống phải dựng lại được từ phần mô tả lưu trong kho mã. Vì vậy đồ án coi đây là một bài toán vận hành, trong đó ba yêu cầu kéo nhau: người dùng không phải chờ lâu, không giữ GPU thừa, và hệ thống vận hành được hằng ngày.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §6 (phát biểu bài toán, ba yêu cầu kéo nhau); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (xương sống) -->

Đồ án xây dựng và vận hành một nền tảng như vậy từ các phần mềm mã nguồn mở phổ biến. Model chạy trên vLLM, phần mềm chuyên phục vụ LLM trên GPU. Kubernetes, nền tảng quản lý ứng dụng trên một cụm máy, giữ các bản chạy và cấp cho mỗi bản một GPU. Nhóm cho hệ thống scale theo số request mà vLLM đang xử lý và đang chờ, thay cho độ bận của GPU. Thời gian khởi động được rút ngắn bằng cách chuẩn bị sẵn phần mềm và model trên máy. Trước khi tắt, mỗi bản chạy có thời gian trả lời xong các request đang dở. Hệ thống có cảnh báo theo mục tiêu chất lượng kèm hướng dẫn xử lý, và toàn bộ cấu hình được lưu trong Git để hệ thống tự áp theo.

<!-- nguồn: docs/chi-tiet/03-kien-truc-thiet-ke.md (thành phần, tín hiệu A2 = running + waiting, L2, graceful shutdown, cảnh báo burn rate, GitOps với Argo CD); mục 3.2–3.5 của luận văn -->

Nhóm đánh giá nền tảng trên một máy thuê có bốn GPU. Máy tạo tải phát lại ba mẫu tải giống người dùng thật: tải thấp ổn định, tải tăng đột ngột, và tải tăng dần rồi giữ ở mức cao. Với mỗi mẫu tải, nhóm so autoscaling với cách giữ cố định số GPU theo hai thước đo, là tỷ lệ request đạt mục tiêu độ trễ và số GPU-giờ bị giữ. Nhóm cũng chạy các tình huống vận hành như cập nhật phiên bản, xoá một bản chạy đang phục vụ, mất nguồn số liệu giám sát và dựng lại hệ thống từ máy trắng. Ở mỗi tình huống, nhóm kiểm xem có request nào bị rớt và cảnh báo có báo đúng lúc không. Luận văn nêu cả những chỗ nền tảng chưa đạt mục tiêu, kèm nguyên nhân đo được và hướng sửa.

<!-- nguồn: docs/chi-tiet/00-thong-so.md (KB1 ổn định, KB2 tăng đột ngột, KB3 tăng dần rồi duy trì; S4 tĩnh, A2; VH2–VH5); mục 3.6, 5.1 (V2, 4 × RTX 4060 Ti); "bốn GPU" là cấu hình máy, không phải số đo -->

Ngoài phần Mở đầu, luận văn gồm sáu chương.

**Chương 1. Giới thiệu** phát biểu bài toán vận hành với ba yêu cầu kéo nhau. Chương này cũng đặt mục tiêu và phạm vi theo đề cương, mô tả cách nhóm tổ chức thực hiện, và tóm tắt các đóng góp chính kèm kết quả đo.

**Chương 2. Cơ sở lý thuyết và giải pháp liên quan** giải thích cách LLM sinh câu trả lời trên GPU, vì sao một bản chạy không nên chạy sát giới hạn, và cách Kubernetes cấp GPU và tự scale. Phần sau của chương trình bày cách vận hành theo mục tiêu chất lượng và triển khai qua Git, rồi so đồ án với các giải pháp liên quan.

**Chương 3. Yêu cầu và thiết kế** nêu hệ thống cần đáp ứng những gì, với chỉ tiêu nghiệm thu đo được, và thiết kế từng phần để đáp ứng. Mỗi lựa chọn thiết kế, từ tín hiệu scale tới cách cảnh báo, đi kèm lý do và phương án đã cân nhắc. Chương kết thúc bằng thiết kế cách đánh giá.

**Chương 4. Triển khai và vận hành** kể nhóm đã dựng từng phần thế nào, gặp sự cố gì, lệch thiết kế ở đâu và kiểm chứng ra sao. Cuối chương có bảng đối chiếu các khó khăn riêng của GPU và LLM với cách nhóm xử lý.

**Chương 5. Đánh giá** trình bày số đo trên máy thuê và so với chỉ tiêu của chương 3, gồm năng lực của một bản chạy, autoscaling so với cấu hình cố định, thời gian khởi động và các tình huống vận hành. Chương này nêu rõ giới hạn của nền tảng khi tải tăng đột ngột và các hạn chế của phép đo.

**Chương 6. Kết luận và hướng phát triển** rút ba kết luận từ kết quả đánh giá, nêu các hạn chế còn lại của hệ thống, và đề xuất hướng làm tiếp, mỗi hướng xuất phát từ một phát hiện của chương 5.

Phụ lục chứa phần người muốn làm lại cần tra cứu: tệp cấu hình chính, quy tắc cảnh báo, hướng dẫn xử lý sự cố mẫu, phiên bản phần mềm, số liệu từng lượt đo, kế hoạch và phân công.

<!-- nguồn: đoạn mở đầu của từng chương (01-00, 02-00, 03-00, 05-00, 06-00 trên nhánh docs/tr8-thesis-ch*); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (dòng từng chương, Phần cuối: Phụ lục A–F; kết chương 4 có bảng vấn đề riêng của GPU/LLM) -->
