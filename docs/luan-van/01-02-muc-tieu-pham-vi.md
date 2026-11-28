<!-- Mục đích: mục 1.2 của luận văn (Mục tiêu, phạm vi và phương pháp), bản base lượt 1. Người viết: Trình. Viết ngày 27/11/2026 theo dàn ý ở docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 và nguồn ở docs/luan-van/nguon-tu-lieu.md §2 (dòng 1.2). Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md (§2.2: phương pháp và tổ chức thực hiện, chỉ điều đã thật sự diễn ra; §4: mã F/N chỉ dùng ở bảng ánh xạ của mục này, kèm tên ngắn) -->
<!-- Thông điệp: (1) Bảy mục tiêu của đề cương được giữ nguyên và cụ thể hoá thành yêu cầu và chỉ tiêu có phép thử; đồ án thêm các chỉ tiêu vận hành ngoài đề cương. (2) Phạm vi: autoscaling số replica trên nhóm GPU cố định, mỗi replica một GPU, một model; giả định chính là chi phí xấp xỉ GPU-giờ. (3) Làm theo vòng từ simulator, máy nhà tới VM thuê; mọi thay đổi qua PR và CI, quyết định ghi thành ADR. -->
<!-- Ý không đưa vào (cắt 28/11 theo D103 để chương 1 gần 4 trang; bản gốc trước khi rút gọn; chỗ nào trong bài đã viết gọn lại thì khôi phục bằng cách thay, không chèn thêm): đoạn yêu cầu ngoài đề cương “Bốn yêu cầu không có trong bảng là phần nhóm thêm ngoài đề cương, đều thuộc yêu cầu vận hành được hằng ngày của bài toán: bảo vệ tối thiểu, an toàn khi thay đổi, tự phục hồi, tái lập và chi phí. Đồ án đặt trọng tâm vào xây dựng và vận hành, theo kế hoạch chiếm khoảng 70% công việc, phù hợp với chuyên môn vận hành nền tảng của hai thành viên.”; đoạn môi trường “Nhóm làm theo vòng qua ba môi trường. Phần không cần GPU thật, như autoscaling, cảnh báo và triển khai qua Git, được dựng và thử trước trên simulator. Đây là một cluster Kubernetes không có GPU, chạy phần mềm giả lập API và metric của vLLM. Phần cần GPU được kiểm chức năng trên máy nhà, một PC có RTX 5060 8 GB được chia thành hai GPU replica để chạy hai replica model nhỏ. Trước phiên đo chính, nhóm thuê vài VM trong thời gian ngắn để thử quy trình, đo thử cold start và chạy thử các kịch bản vận hành.” (máy nhà và VM thuê đã có ở mục 3.2, Bảng 3.2); đoạn quy trình, hai câu đầu “Mọi thay đổi vào nhánh chính của kho mã đi qua pull request (PR) trên GitHub. Trước khi merge, CI chạy bằng GitHub Actions tự kiểm YAML, manifest Kubernetes, quy tắc cảnh báo kèm unit test, mã Python và link trong tài liệu.” -->
<!-- Soát số: chưa · Soát văn phong: kiem_van 28/11 · Người viết đọc lại: chưa -->
## 1.2. Mục tiêu, phạm vi và phương pháp

Mục tiêu tổng quát của đồ án là xây dựng và vận hành một nền tảng phục vụ LLM mã nguồn mở trên Kubernetes có GPU, rồi đánh giá nó so với cách cấp phát tài nguyên cố định. Nền tảng tự điều chỉnh số replica theo tải, được triển khai và cập nhật hoàn toàn bằng mã nguồn, có giám sát, cảnh báo theo SLO và quy trình xử lý sự cố. Nhóm giữ nguyên bảy mục tiêu cụ thể của đề cương và cụ thể hoá chúng thành bảy yêu cầu chức năng và tám chỉ tiêu nghiệm thu, mỗi cái có một phép thử định trước (mục 3.1). Bảng 1.1 ghi mỗi mục tiêu ứng với yêu cầu nào và được trình bày ở mục nào.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §8 (mục tiêu tổng quát; mỗi yêu cầu có cách kiểm chứng), §9 (bảy mục tiêu của đề cương giữ nguyên) -->

**Bảng 1.1.** Bảy mục tiêu của đề cương, yêu cầu tương ứng và mục trình bày

| Mục tiêu của đề cương | Yêu cầu, chỉ tiêu | Thiết kế, triển khai | Đánh giá |
|---|---|---|---|
| 1. Triển khai LLM mã nguồn mở bằng vLLM trên Kubernetes | F1 API có streaming; F3 triển khai qua Git; F4 dựng từ máy trắng | 3.2; 4.1, 4.2, 4.5 | 5.5, 5.6 |
| 2. Cấu hình GPU cho suy luận | F1; N5 cold start | 3.2, 3.4; 4.2, 4.4 | 5.4, 5.6 |
| 3. Autoscaling theo metric tải hoặc request | F2 tự điều chỉnh replica; N2 tốc độ phản ứng; N3 hiệu quả GPU | 3.3, 3.4; 4.3, 4.4 | 5.3, 5.4 |
| 4. Giám sát metric phục vụ và GPU | F5 dashboard; F6 cảnh báo; N7 quan sát được | 3.5, 3.6; 4.6 | 5.5, 5.6 |
| 5. Thử nghiệm với nhiều mẫu tải | N1 tỷ lệ request đạt SLO; N2; N3 | 3.6; 4.7 | 5.3 |
| 6. So sánh với cấu hình tài nguyên cố định | N1; N3 | 3.6; 4.7 | 5.3 |
| 7. Đánh giá đánh đổi giữa hiệu năng và tài nguyên | N3 | 3.6 | 5.3, 5.6 |

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §9 (bảng: mục tiêu → F/N → bằng chứng); docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (bảng "Truy vết yêu cầu → mục"); tên ngắn của F/N theo Bảng 5.6a trên nhánh docs/tr8-thesis-ch5-drafts (05-06). N2 gồm N2a phản ứng và N2b hồi phục -->

Bốn yêu cầu không có trong bảng (bảo vệ tối thiểu, an toàn khi thay đổi, tự phục hồi, tái lập và chi phí) là phần nhóm thêm ngoài đề cương, đều thuộc yêu cầu vận hành được hằng ngày của bài toán.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §8 (sơ đồ sáu việc: F7, N4, N6, N8 thuộc "thay đổi an toàn" và "dựng lại được, an toàn, biết chi phí"; tỷ trọng dự kiến 70/30), §9 (bảng không có F7, N4, N6, N8); docs/adr/002-chuyen-trong-tam-sang-van-hanh.md §1 (khoảng 70% cài đặt và vận hành, đúng chuyên môn Platform, DevOps/SRE của hai thành viên), §2 Q2 (bài toán vận hành) -->

Phạm vi của đồ án là autoscaling số replica cho một model trên một nhóm GPU cố định, mỗi replica dùng trọn một GPU, tối đa 4 replica. Ngoài phạm vi là thêm bớt máy theo tải, chia một model qua nhiều GPU, định tuyến request theo trạng thái của từng replica, phục vụ nhiều model và tắt hẳn mọi replica khi không có tải (*scale-to-zero*). Scale-to-zero bị loại vì cold start tính bằng phút không hợp với dịch vụ người dùng ngồi chờ trả lời. Đồ án không đề xuất thuật toán autoscaling mới, không cải tiến hiệu năng của bản thân vLLM và không kiểm định giả thuyết thống kê. Mỗi cấu hình chỉ chạy 1–3 lượt, đủ để nghiệm thu và thấy các khác biệt lớn.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §11 (không phải mục tiêu), §12.1 (ranh giới hệ thống: trong/ngoài, lý do loại scale-to-zero), §12.3 mục 2 (tối đa 4 replica) -->

Giả định quan trọng nhất là chi phí xấp xỉ bằng số GPU-giờ cấp cho các replica. Giả định này đúng khi GPU được thuê theo mức dùng, hoặc thuộc một cluster dùng chung nơi GPU được giải phóng sẽ chạy việc khác. Trên một nhóm GPU dành riêng, bớt replica không làm giảm tiền, và kết quả về hiệu quả chỉ còn nói về số GPU giải phóng được.

<!-- nguồn: docs/chi-tiet/01-bai-toan-yeu-cau.md §12.2 (G1: chi phí ≈ GPU-giờ, vì sao hợp lý, không kiểm chứng bằng thực nghiệm, nếu sai thì sao; G2–G7 về máy, tải, phiên bản thuộc điều kiện đo ở mục 3.6) -->

Nhóm làm theo vòng qua ba môi trường (mục 3.2). Autoscaling, cảnh báo và triển khai qua Git được thử trước trên simulator, một cluster Kubernetes không có GPU, chạy phần mềm giả lập API và metric của vLLM. Phần cần GPU được kiểm chức năng trên một PC ở nhà. Nhóm còn thuê vài VM ngắn hạn để thử quy trình, cold start và các kịch bản vận hành. Số đo hiệu năng dùng để kết luận chỉ lấy từ phiên đo chính trên một VM thuê có 4 × RTX 4060 Ti, với model Qwen2.5-3B-Instruct.

<!-- nguồn: docs/chi-tiet/05-moi-truong-danh-gia.md (dòng 6: tầng 1 máy nhà và simulator, PC RTX 5060 8 GB time-slicing 2 GPU replica, model 0,5B, llm-d-inference-sim; dòng 650: số đo hiệu năng không lấy ở máy nhà); 05-01 trên nhánh docs/tr8-thesis-ch5-drafts (máy V2 thực tế 4 × RTX 4060 Ti 16 GB); docs/luan-van/nguon-tu-lieu.md §3 (số đo V2: VM 4 × RTX 4060 Ti 16 GB, Qwen2.5-3B); các phiên thử trước V2: docs/nhat-ky/van-hanh.md mục 08/11 (2 × RTX 5060 Ti; 4 × RTX A4000, V0+V1) và 16/11 (2 × RTX 4000 Ada, chạy thử VH2a, VH3, VH4) -->

Kế hoạch chia theo tuần với năm mốc. Dữ liệu của phiên đo chính được đóng băng trước khi viết chương đánh giá, và phép thử bổ sung sau đó chạy trên simulator. Hai thành viên chia việc theo tính năng: một người phụ trách phần chạy trên GPU, người kia phụ trách autoscaling, giám sát và đánh giá.

<!-- nguồn: docs/chi-tiet/06-ke-hoach-quan-ly.md §1 (lịch, mốc M1–M5, đóng băng dữ liệu 22/11), §5.1 (hai người cùng vai trò, chia theo tính năng dọc: "chạy được trên GPU" Q1–Q8, phần autoscaling, giám sát và đo TR1–TR8); phép thử sau đóng băng trên kind: VH2 qua Git (PR #78), N8 dựng lại (PR #76) -->

Mọi thay đổi vào nhánh chính của kho mã đi qua pull request (PR) trên GitHub, và CI tự kiểm manifest, quy tắc cảnh báo, mã và tài liệu trước khi merge. Các quyết định lớn được ghi thành bản ghi quyết định kiến trúc (*architecture decision record*, ADR), kèm các phương án đã cân nhắc và lý do chọn. Kịch bản vận hành, sự cố và lần thuê máy được ghi vào nhật ký vận hành, nguồn của các sự kiện và số liệu ở chương 4 và 5. Kế hoạch và phân công chi tiết nằm ở Phụ lục F.

<!-- nguồn: .github/workflows/ci.yaml (job yaml: yamllint, actionlint; manifests: kustomize build + kubeconform; alerts: make alerts-test, alertmanager-check, dashboards-check; python: pytest, ruff; docs: lychee); CONTRIBUTING.md §7; docs/adr/ (ADR-001, 002, 004, 005, 006 trên main); docs/chi-tiet/06-ke-hoach-quan-ly.md §7 (nhật ký quyết định, nhật ký vận hành); docs/luan-van/quy-tac-viet.md §2.2 (chỉ mô tả quy trình đã diễn ra: không viết review chéo mọi thay đổi, không viết họp hằng tuần vì chỉ có biên bản tuần 01 và 05) -->
