# ADR-004: Điều kiện thực tế, phạm vi rút gọn, môi trường và kế hoạch đến hạn nộp

- **Trạng thái:** Đã chấp nhận ngày 08/10/2026. K13 được bổ sung ngày 15–16/10/2026 (xem §7).
- **Người quyết định:** Nhóm, dựa trên báo cáo review nội bộ ngày 08/10/2026 (§0, §7, §9; không lưu trong repo, các kết luận chính được ghi lại trong ADR này và ADR-005) và các thông tin nhóm đã xác nhận cùng ngày.
- **Thay thế một phần:** [ADR-001](001-cac-lua-chon-ban-dau.md) và [ADR-002](002-chuyen-trong-tam-sang-van-hanh.md) (chi tiết ở §4).
- **Liên quan:** [ADR-005](005-sua-thiet-ke-sau-review.md) (các sửa thiết kế kỹ thuật), [Thông số và chỉ tiêu](../chi-tiet/00-thong-so.md), [Môi trường và đánh giá](../chi-tiet/05-moi-truong-danh-gia.md), [Kế hoạch và quản lý](../chi-tiet/06-ke-hoach-quan-ly.md)

## 1. Bối cảnh

ADR-001 và ADR-002 được viết với ba giả định: có 16 tuần và bảo vệ cuối tháng 01/2027; có 2–3 laptop RTX 4060; và thuê Vast.ai một đợt liên tục khoảng 37 giờ. Ngày 08/10/2026 nhóm xác nhận điều kiện thật như sau:

| Hạng mục | Điều kiện thật |
|---|---|
| Thời gian | Hạn nộp luận văn khoảng **08/12/2026**, còn khoảng 8,7 tuần. Chưa có ngày bảo vệ |
| Quỹ giờ | Mỗi người 8–15 giờ/tuần (cả hai đều đang đi làm), tổng khoảng 135–270 người-giờ |
| Kinh nghiệm | Đã làm Prometheus/cảnh báo, K8s, CI/CD ở dự án cá nhân; chưa làm vLLM, GPU trên K8s, Argo CD |
| Máy nhà | 1 PC RTX 5060 8 GB (CPU 6 nhân/12 luồng, RAM 16 GB, bật 24/7, có Tailscale, mạng ~30 MB/s); có thể thêm 1 laptop RTX 4050 6 GB. Một thành viên chỉ có laptop không GPU, làm việc từ xa |
| Cloud | Đã có tài khoản Vast.ai và Cloudflare R2. GCP có 200 USD credit (Gmail cá nhân, free trial). Chỉ thuê được vào thứ Bảy, Chủ nhật |
| Tiền thật | Tối đa 150 USD. Đã nạp 800.000 VND (~30 USD) |
| Model | Không bắt buộc model cụ thể |
| Demo, phân công | Demo tính sau; phân công tạm bỏ |

Với điều kiện này, báo cáo review chấm phạm vi cũ trong tài liệu là **NO-GO (2/10)**. Có hai lý do chính: lịch cũ đặt đợt đo chính vào 04–05/12, quá sát hạn nộp (B1); và khối lượng việc cần 330–515 người-giờ, vượt xa quỹ giờ (B2).

## 2. Quyết định

| # | Nội dung | Quyết định |
|---|---|---|
| K1 | Lịch | Kế hoạch 9 tuần W1–W9 (08/10 → 06/12), nộp 07–08/12. **Đóng băng dữ liệu 15/11**, muộn nhất 22/11 |
| K2 | Phạm vi | Dùng phạm vi rút gọn của review §9.1, khoảng 169–251 người-giờ. Giữ đủ tên đề tài và bảy mục tiêu của đề cương |
| K3 | Môi trường phát triển | Máy nhà (PC 5060, cộng laptop 4050 nếu được) chỉ là **môi trường chức năng**: không dùng số liệu hiệu năng của nó. Phần lớn việc phát triển autoscaling, dashboard và runner chạy trên `llm-d-inference-sim` (cluster kind hoặc k3s) |
| K4 | Cloud chính | **Vast.ai chế độ VM, 4 × RTX 4090**, thuê on-demand; dự phòng 4 × 3090 hoặc A5000. Đo **toàn bộ ĐG1–ĐG3 trong một lần thuê liền** từ sáng thứ Bảy 07/11 tới sáng Chủ nhật 08/11 (khoảng 20–22 giờ), runner chạy qua đêm không cần người trực |
| K5 | Dự phòng cloud | (1) Cuối tuần 14–15/11 thuê máy khác và chạy lại **trọn bộ cấu hình** của kịch bản bị hỏng, kèm ĐG1. (2) GCP g2/L4 bằng credit nếu được duyệt quota; khi đó đo lại toàn bộ trên L4. Không trộn số liệu hai loại máy trong cùng một kịch bản |
| K6 | Hạn chọn cloud | Tìm offer Vast vào 10–11/10 và 17–18/10. Đạt khi có **≥ 3 offer 4 × 4090 chế độ VM, ≤ 0,50 USD/GPU-giờ, ở cả hai ngày** của ít nhất một cuối tuần, và phiên V0 dựng được k3s có GPU. **Quyết định chậm nhất 18/10/2026**; không đạt thì chuyển sang GCP |
| K7 | Ngân sách | **≤ 150 USD tiền thật** cho GPU thuê; ước tính 30–75 USD. Credit GCP chỉ dùng cho phương án dự phòng |
| K8 | Ma trận đánh giá | **17 lượt** (thay 28). ĐG3: L0 × 2, L2 × 3; bỏ KB2 × A2 ở L0 |
| K9 | Model | F1 viết lại thành "một model mở cỡ 3–8B". Khuyến nghị Qwen2.5-7B-Instruct trên GPU 24 GB; Qwen2.5-1.5B (hoặc 3B AWQ) ở nhà |
| K10 | Vận hành rút gọn | 3 dashboard; 6 cảnh báo, mỗi runbook khoảng nửa trang; chỉ gửi Telegram; Argo CD bản core với một App-of-Apps khoảng 4 app, **bỏ sync window** |
| K11 | Kịch bản cần người thứ hai hoặc nhiều node | VH5 "người thứ hai dựng lại" thực hiện qua Tailscale trên cluster nhà, hoặc trên cluster kind + simulator. Drain node, scale 1 → 3 và A4 làm trên simulator |
| K12 | Luận văn | 55–65 trang; dùng bộ tài liệu thiết kế làm bản nháp chương 1–3 |
| K13 | Phân công, demo | Tạm chưa phân công. Demo chốt sau; định hướng là video, cộng phần live nhỏ bằng simulator |
| K14 | Tài liệu | Gộp 14 tài liệu chuyên sâu thành 7 file, có một file [Thông số và chỉ tiêu](../chi-tiet/00-thong-so.md) làm nguồn sự thật duy nhất |

## 3. Lý do

- **Vast thay vì GCP làm phương án chính.** Nhóm ưu tiên Vast vì rẻ. Ở mức 0,30–0,50 USD/GPU-giờ, giá Vast thấp hơn GCP tính theo tiền thật. Ngược lại, GCP free trial chặn GPU, và quota GPU mặc định bằng 0, tài khoản cá nhân dễ bị từ chối.
- **Một lần thuê liền.** Mọi số liệu đến từ cùng một máy. Nhờ vậy giữ đúng quy tắc "cùng máy" khi so sánh các cấu hình, mà không phải chứng minh các phiên cuối tuần khác nhau so sánh được với nhau.
- **Phạm vi rút gọn.** Vừa với quỹ giờ khi mỗi người làm khoảng 12–15 giờ/tuần, và vẫn đo đủ các chỉ số mà đề cương yêu cầu.

## 4. Các mục bị thay thế

| Mục | Nội dung cũ | Nội dung mới |
|---|---|---|
| ADR-001 D1, ADR-002 Q10 | 100–200 USD; một đợt ~37 giờ, 60–105 USD, nạp trước 100 USD | K4, K7 |
| ADR-001 D2, D3 | Vast VM 4 × 4090; dự phòng TensorDock | K4, K5 (bỏ TensorDock; dự phòng là máy Vast khác hoặc GCP) |
| ADR-001 D4 | 2–3 laptop RTX 4060 | K3 |
| ADR-001 D6 | Qwen2.5-7B (cloud), 1.5B (laptop) | K9 |
| ADR-001 D18 | CLI `vastai` + Ansible; dự phòng TensorDock API | Giữ `vastai` + Ansible; bỏ TensorDock |
| ADR-001 D24, §6 | 16 tuần, T1 = 05/10, bảo vệ cuối 01/2027 | K1 |
| ADR-001 §3.2, §4.2 | Đợt liên tục; burn-in ~1 giờ, tối đa 3 máy | Lần thuê liền ~20–22 giờ (K4); burn-in rút gọn ~30 phút |
| ADR-001 §4.1 | Độ tin cậy ≥ 99% | ≥ 0,98, để đủ offer vào cuối tuần |
| ADR-002 Q6, Q8 | 28 lượt; KB2 × A2 ở L0 | K8 |
| ADR-002 Q12 | Phân công theo vai trò | K13 |
| ADR-002 Q13 | Chương 4: 22–28 trang; chương 5: 12–15 trang | K12 |
| ADR-002 Q14 | 14 tài liệu chuyên sâu | K14 |
| ADR-002 §6 | ADR-003 viết ở T9 | ADR-003 viết trong phiên V2, khoảng giờ thứ 3 |

Các mục còn lại của ADR-001 và ADR-002 giữ nguyên.

## 5. Hệ quả

**Tích cực**
- Có lịch khả thi với hạn nộp, còn 2–3 tuần để viết sau khi đóng băng dữ liệu.
- Chi phí tiền thật dự kiến chỉ bằng khoảng một nửa trần.

**Tiêu cực và cách giảm**
- **Đường găng gần như không có độ dư.** Mỗi tuần có điểm dừng và phương án cắt giảm ([Kế hoạch](../chi-tiet/06-ke-hoach-quan-ly.md#2-kế-hoạch-từng-tuần)).
- **Phụ thuộc vào việc có máy 4 × 4090 chế độ VM vào cuối tuần.** Chưa kiểm chứng; trang giá Vast ngày 08/10 hiện "No current offers". Giảm bằng tiêu chí K6 và hạn 18/10.
- **Máy nhà chỉ có 1–2 GPU khác loại.** Không đo hiệu năng ở nhà; dùng simulator cho các kịch bản nhiều replica.
- **RTX 5060 (sm_120) chưa chắc chạy được image vLLM chính thức.** Thử trong W1; nếu hỏng thì dùng laptop 4050 hoặc thuê 1 GPU.
- **Ít lượt mỗi ô hơn** (1–3 lượt). Chỉ đủ thấy các khác biệt lớn; điều này được ghi thành hạn chế.

## 6. Việc còn mở

| Việc | Hạn |
|---|---|
| ~~Gửi GVHD email 1 trang và xin xác nhận~~ (không cần, xem §7) | – |
| Kết quả chạy thử vLLM trên RTX 5060 | W1–W2 |
| Kết quả tìm offer Vast; chốt Vast hay GCP | 18/10 |
| 800.000 VND đã nạp vào Vast hay GCP? Nếu là GCP thì Vast cần nạp thêm ~70 USD; nếu là Vast thì nạp thêm ~40–50 USD trước 06/11 | 18/10 |
| ~~Phân công và cách ghi đóng góp cá nhân trong luận văn~~ (xong 15/10, xem §7) | Trước khi viết (W5) |
| Hình thức demo | Trước W7 |
| ADR-003: kết quả đo năng lực và các giá trị chốt | Trong phiên V2 (07/11) |

## 7. Cập nhật sau ngày 08/10/2026

| Ngày | Mục | Nội dung |
|---|---|---|
| 15/10/2026 | K13, §6 | **Đã phân công** theo tính năng dọc: Quang Q1–Q8 (hạ tầng, serving, vòng đời pod, runner, năng lực), Trình TR1–TR8 (GitOps, autoscaling, giám sát, cảnh báo, máy tạo tải, phân tích). Đóng góp cá nhân ghi trong `docs/nhat-ky/lam-viec/<người>/`. Chi tiết: [Kế hoạch §5.1](../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công) |
| 15/10/2026 | §6 | GVHD không yêu cầu duyệt chi tiết phạm vi; nhóm coi phạm vi rút gọn là đã chốt, chỉ báo cáo tiến độ theo các buổi ở [Kế hoạch §7](../chi-tiet/06-ke-hoach-quan-ly.md#7-quy-trình-làm-việc-và-nhịp-với-gvhd) |
| 16/10/2026 | K3 | Ngoại lệ có chủ đích cho "không dùng số liệu hiệu năng ở nhà": kiểm chứng lý thuyết LT1–LT8 dùng số đo ở nhà để kiểm tra **công thức**, không báo cáo hiệu năng của nền tảng ([Môi trường §19](../chi-tiet/05-moi-truong-danh-gia.md#19-kiểm-chứng-lý-thuyết-lt1lt8)) |
| 16/10/2026 | K8 | Khi phải cắt phạm vi, **không cắt ca đối chứng** (A1, L0) mà giảm số lượt lặp ([Kế hoạch §8](../chi-tiet/06-ke-hoach-quan-ly.md#8-dự-phòng-và-cắt-giảm-phạm-vi)) |
