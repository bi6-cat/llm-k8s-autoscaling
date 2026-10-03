# ADR-002: Chuyển trọng tâm đồ án sang xây dựng và vận hành

- **Trạng thái:** Đã chấp nhận ngày 04/10/2026.
- **Người quyết định:** Nhóm.
- **Thay thế một phần:** [ADR-001](001-cac-lua-chon-ban-dau.md), các mục D1, D11, D12, D15, D16 và §3.2 (chi tiết ở §4).
- **Liên quan:** [Bản mô tả chính](../mo-ta-chi-tiet-do-an.md) (phiên bản 2.0), [02 – Mục tiêu và yêu cầu](../chi-tiet/02-muc-tieu-yeu-cau.md), [08 – Vận hành](../chi-tiet/08-van-hanh.md), [09 – Kiểm thử và đánh giá](../chi-tiet/09-kiem-thu-danh-gia.md)

## 1. Bối cảnh

Bản mô tả 1.0 (26/09/2026) dựng đồ án quanh ba câu hỏi nghiên cứu (RQ1–RQ3) và ba giả thuyết. Phần đánh giá được thiết kế như một nghiên cứu thực nghiệm: ma trận 78 lượt chạy, thiết kế khối ngẫu nhiên, so sánh cặp, khoảng tin cậy 95%, bootstrap, kế hoạch phân tích đăng ký trước. Chương "Thí nghiệm và đánh giá" là chương dài nhất của luận văn (18–25 trang), còn chương "Triển khai" chỉ 10–12 trang.

Nhóm muốn đồ án nghiêng về **cài đặt và vận hành (khoảng 70%)**, đúng chuyên môn của hai thành viên (Platform, DevOps/SRE/Cloud). Chỉ cần một bài toán đủ thuyết phục.

Có hai ràng buộc:
1. **Tên đề tài đã đăng ký, không đổi được:** *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling*. Vì vậy vẫn phải có phần đánh giá.
2. **Đề cương đã nộp** có bảy mục tiêu, ba kịch bản tải, so sánh tĩnh với autoscaling, và các chỉ số P95/P99, TTFT, throughput, resource utilization, autoscaling response time. Câu hỏi nghiên cứu và giả thuyết **không có trong đề cương**; đó là phần nhóm thêm vào ở bản 1.0 (Phụ lục A, dòng "(chưa có)").

## 2. Quyết định

| # | Nội dung | Bản 1.0 | Bản 2.0 |
|---|---|---|---|
| Q1 | Khung đồ án | RQ1–RQ3, giả thuyết H1–H3, quy tắc kết luận | **Yêu cầu chức năng F1–F7 và chỉ tiêu nghiệm thu N1–N8**; kết quả là bảng nghiệm thu |
| Q2 | Bài toán | Tối thiểu GPU-giờ với ràng buộc SLO | **Bài toán vận hành**: doanh nghiệp tự host LLM, giữ chất lượng với ít GPU nhất, và vận hành được hằng ngày |
| Q3 | Phần vận hành | Rải rác, đóng vai "hạ tầng cho thí nghiệm" | Tài liệu riêng ([08](../chi-tiet/08-van-hanh.md)): SLO, cảnh báo theo burn rate, runbook, cập nhật khi hết GPU, sự cố, dựng lại, bảo mật tối thiểu, chi phí |
| Q4 | Kịch bản tải | 5 (KB1–KB5) | **3 theo đề cương**: KB1 thấp ổn định, KB2 tăng đột ngột (rồi giảm lại để kiểm tra scale-down), KB3 cao kéo dài |
| Q5 | Cấu hình đánh giá | S1, S4, A1, A2, A3, cộng A4 ở KB3 | **S1, S4, A1, A2**. A3 là tuỳ chọn (Could). A4 chỉ dùng trên laptop để minh hoạ flapping |
| Q6 | Số lượt | 78 (3 lượt mỗi ô, 3 khối) | **28** (KB2: 3 lượt; KB1, KB3: 2 lượt) |
| Q7 | Thống kê | Khoảng tin cậy, bootstrap, so sánh cặp theo khối, `PLAN.md` | Trung bình kèm min–max; vẽ từng lượt; chỉ kết luận khác biệt khi mọi lượt cùng chiều và vượt ngưỡng thực tiễn |
| Q8 | Cold start | 5 lần mỗi mức; KB2 × A2 ở L0 và L2, mỗi mức 3 lượt | 3 lần mỗi mức; KB2 × A2 ở L0, 2 lượt (L2 lấy từ ma trận) |
| Q9 | Kịch bản vận hành | Chỉ có KB4 (scale-down) | **VH1–VH6**: scale-down, rolling update khi hết GPU, sự cố pod/node, mất Prometheus, dựng lại từ máy trắng, cảnh báo đúng và không báo giả |
| Q10 | Đợt thuê GPU | ~72 giờ, 105–170 USD | **~37 giờ, 60–105 USD**; nạp trước 100 USD |
| Q11 | Cấu hình autoscaling trong Git | Nằm ngoài Argo CD | A2 nằm trong Git (Argo CD quản lý); runner tắt auto-sync khi đánh giá |
| Q12 | Phân công | Quang: IaC, giám sát, sinh tải, runner, thống kê | Quang (DevOps/SRE/Cloud): hạ tầng cloud và cluster, IaC, GitOps, giám sát, SLO, cảnh báo, runbook, khôi phục, chi phí, công cụ đánh giá. Trình (Platform): GPU, vLLM, autoscaling, cold start, rolling update, bảo mật tối thiểu |
| Q13 | Luận văn | Chương 4 "Triển khai" 10–12 trang; chương 5 18–25 trang | **Chương 4 "Triển khai và vận hành" 22–28 trang**; chương 5 "Đánh giá" 12–15 trang |
| Q14 | Đánh số tài liệu | 15 tài liệu chuyên sâu | 14 tài liệu: thêm 08 – Vận hành; gộp ba tài liệu thí nghiệm, chỉ số, phân tích thành 09 – Kiểm thử và đánh giá |

## 3. Lý do

- **Đúng đề cương và đúng tên đề tài.** Bảy mục tiêu của đề cương giữ nguyên; bốn trong số đó (triển khai vLLM, cấu hình GPU, autoscaling, giám sát) vốn là việc xây dựng và vận hành. Chữ "Evaluation" được đáp ứng bằng phần đánh giá kiểu nghiệm thu, vẫn đo đủ các chỉ số đề cương yêu cầu.
- **Đúng chuyên môn của nhóm**, và sát công việc thật ở FCI và VCS.
- **Vẫn có chiều sâu kỹ thuật.** Mỗi phần cài đặt gắn với một vấn đề riêng của GPU và LLM (tín hiệu scale, cold start, scale-down với request streaming, rolling update khi hết GPU, Argo CD và HPA), và đều có số đo kèm theo.
- **Rẻ hơn và ít rủi ro hơn.** Ma trận nhỏ hơn gần ba lần; phần lớn kịch bản vận hành chạy được trên laptop.

## 4. Các mục của ADR-001 bị thay thế

| Mục ADR-001 | Nội dung cũ | Nội dung mới |
|---|---|---|
| D1 | Nạp trước 150 USD | Nạp trước 100 USD; tổng không quá 150 USD |
| D11 | A1–A3, cộng A4 ở KB3 | S1, S4, A1, A2; A3 tuỳ chọn; A4 chỉ trên laptop |
| D12 | Sync HPA 5 s; nghiên cứu độ nhạy với 15 s | Sync HPA 5 s; nghiên cứu độ nhạy chuyển sang hướng mở rộng E13 |
| D15 | KB5 hình sin, trace thật nếu còn thời gian | Không có KB5; trace thật chuyển sang hướng mở rộng E13 |
| D16 | 78 lượt (+12 nếu còn ngân sách) | 28 lượt (+6 lượt A3 nếu còn thời gian) |
| §3.2 | Một đợt liên tục ~72 giờ, mỗi khối ~15 giờ | Một đợt liên tục ~37 giờ, không chia khối; thứ tự các lượt được xáo trộn |
| §5 | Chi phí 105–165 USD | Chi phí 60–105 USD |

Các mục còn lại của ADR-001 (nhà cung cấp, cấu hình máy, model, SLO sơ bộ, IaC, GitOps, lịch…) giữ nguyên.

## 5. Hệ quả

**Tích cực**
- Luận văn có một chương chính đúng sở trường của nhóm (chương 4), và một bảng nghiệm thu dễ trình bày trước hội đồng.
- Chi phí thuê GPU còn khoảng một nửa; đợt thuê ngắn hơn nên ít rủi ro máy hỏng giữa chừng.
- Bộ vận hành (cảnh báo, runbook, quy trình) dùng lại được ngay trong công việc thật.

**Tiêu cực và cách giảm**
- **Kết luận về metric scale yếu hơn về mặt thống kê** (2–3 lượt, không có khoảng tin cậy). Ghi thành hạn chế; các khác biệt cần thấy đều lớn; đánh giá chặt hơn là hướng mở rộng E13.
- **Rủi ro hội đồng cho rằng đồ án thiên về cài đặt.** Giảm bằng cách trình bày theo cặp vấn đề → cách xử lý → số đo, và hỏi GVHD sớm ở buổi T6, T8 ([12 – R21](../chi-tiet/12-rui-ro.md#2-sổ-đăng-ký-rủi-ro)).
- **Phạm vi vận hành dễ phình to.** Giảm bằng tiêu chí vào/ra phạm vi và Must/Should/Could ([02 §9](../chi-tiet/02-muc-tieu-yeu-cau.md#9-mức-độ-thành-công)).

## 6. Việc tiếp theo

- Gửi GVHD bản mô tả 2.0 cùng ADR này ở buổi T1, xin xác nhận hướng đi.
- **ADR-003** (trong đợt thuê chính, T9) sẽ ghi kết quả đo năng lực và các giá trị chốt: C, B\*, ngưỡng SLO (trùng biên bucket của histogram TTFT), threshold của A1 và A2, các chỉ tiêu N1–N8 cuối cùng.
