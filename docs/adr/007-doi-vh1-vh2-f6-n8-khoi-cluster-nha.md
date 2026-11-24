# ADR-007: Dời VH1, VH2, F6 và N8 khỏi cluster nhà

- **Trạng thái:** Đã chấp nhận ngày 24/11/2026 (Trình quyết, Quang đọc ở PR).
- **Người quyết định:** Trình, theo quyền tự quyết phạm vi phần TR1–TR8; các việc thuộc phần của Quang (VH1, VH2) được nêu ở đầu PR.
- **Thay thế một phần:** [Thông số §5](../chi-tiet/00-thong-so.md#5-mức-độ-thành-công) dòng Must "VH1, VH2 ở nhà"; [Môi trường §13](../chi-tiet/05-moi-truong-danh-gia.md#13-kịch-bản-vận-hành-vh1vh6) cột "Ở đâu" của VH1, VH2.
- **Liên quan:** [Môi trường §16](../chi-tiet/05-moi-truong-danh-gia.md#16-trình-bày-kết-quả-và-bảng-nghiệm-thu) (bảng nghiệm thu 21/11), [Kế hoạch §5.1](../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công), [nhật ký Trình tuần 08](../nhat-ky/lam-viec/trinh/tuan-08.md) (24/11).

## 1. Bối cảnh

Bảng nghiệm thu điền ngày 21/11 từ dữ liệu phiên V2 còn bốn mục Must chưa xong và đều ghi là chờ cluster nhà:

| Mục | Phần còn thiếu ngày 24/11 | Đã có từ V2 hoặc simulator |
|---|---|---|
| VH1 (N4) | KB2-mini ở nhà chưa chạy | Pha `drop` của 3 lượt A2 × KB2 trên V2: N = 4, 0 lỗi |
| VH2 (F3, N4) | Vòng Git → Argo CD sync → `git revert` chưa chạy | Rolling update trên VM thuê, kích hoạt bằng annotation: ca 1 replica và ca mọi GPU có pod đều 0 lỗi (ca mọi GPU có pod: 371,6 s); ca kiểu web kẹt Pending đúng như phân tích |
| F6 | Chưa gửi tới Telegram thật | Alertmanager → Telegram kiểm với API giả trên simulator; 7 quy tắc có runbook và unit test |
| N8 | Người thứ hai dựng lại theo README: chưa đo | Phiên bản đã ghim |

Yêu cầu kubeconfig và share node của cluster nhà cho Trình đã chờ từ 21/10, tức 34 ngày. Mốc M4 là 29/11 và hạn nộp là khoảng 08/12.

## 2. Quyết định

| # | Mục | Quyết định |
|---|---|---|
| D1 | VH1 | Không chạy KB2-mini ở nhà. Bằng chứng scale-down an toàn cho Must lấy từ pha `drop` của 3 lượt A2 × KB2 trên V2 |
| D2 | VH2 | Phần qua Git chạy trên kind + simulator có cài Argo CD (phiên bản ghim theo [phien-ban.md](../phien-ban.md)). Application trên kind theo dõi một nhánh riêng của Trình, nên commit và `git revert` không đổi `main` hay cluster nhà. Ca 1 replica và ca mọi GPU có pod dùng kết quả đã đo trên V2 |
| D3 | F6 | Tin cảnh báo tới Telegram thật được kiểm trên kind + simulator, với bot Telegram thật; token chỉ nằm trong Secret cục bộ tạo từ `.env` |
| D4 | N8 | Trình dựng lại cluster kind + simulator từ đầu, chỉ theo README, có bấm giờ. [Thông số §4](../chi-tiet/00-thong-so.md#4-chỉ-tiêu-nghiệm-thu) N8 và Môi trường §13 VH5 đã cho phép cách này |
| D5 | Quyền cluster nhà | Bỏ yêu cầu kubeconfig và share node cho Trình |

## 3. Lý do

- **VH1:** cùng cơ chế với KB2-mini (preStop cộng graceful shutdown), nhưng đo trên 4 GPU thật thay vì 2 GPU replica chia time-slicing trên RTX 5060.
- **VH2:** vòng Git → Argo CD → `git revert` không phụ thuộc GPU, nên simulator kiểm được đúng phần F3 còn thiếu. Phần phụ thuộc GPU (ca 1 replica, `maxSurge: 0`, ca kẹt Pending) đã có số đo trên V2.
- **F6, N8:** không cần GPU, cũng không cần cluster nhà.
- Cả bốn việc thôi phụ thuộc vào lịch của Quang và vào quyền truy cập đã chờ 34 ngày. Làm trên kind cũng không làm Argo CD đổi cluster nhà.

**Phương án không chọn**
- Chờ Quang chạy VH1, VH2 ở nhà: đúng chữ Must cũ, nhưng tốn khoảng 1–2 giờ của Quang, và mốc M4 còn 5 ngày.
- Giữ chữ Must cũ và ghi F3 vào Hạn chế: F3 mất đúng phần lõi (cập nhật và rollback qua Git).

## 4. Hệ quả

- VH1 trong luận văn chỉ có dữ liệu GPU thuê. Mục 5.5 nói rõ đây là pha `drop` của ĐG2, không phải một lượt VH1 riêng.
- VH2 tách làm hai phần: vòng Git trên simulator (không có GPU, cold start của simulator ngắn hơn vLLM thật) và ràng buộc GPU trên V2 (không qua Git, vì VM thuê không dùng Argo CD, [ADR-006 §3.1](006-chot-may-model-va-kich-ban-truoc-v2.md#31-quyết-định-ngày-12112026)). Chưa có lần nào đi trọn vòng Git trên GPU thật; mục Hạn chế ghi điều này.
- Tin Telegram thật có ảnh chụp từ simulator, không phải từ một vi phạm SLO trên GPU.

## 5. Việc còn mở

| Việc | Người | Hạn |
|---|---|---|
| N8: dựng lại kind + simulator theo README, bấm giờ, sửa README nếu thiếu bước | Trình | Trước M4 (29/11) |
| F6: kích hoạt một cảnh báo thật trên kind, gửi qua bot thật, chụp tin | Trình | Trước M4 |
| VH2: cài Argo CD lên kind, chạy cập nhật rồi `git revert` dưới tải, đo lỗi và thời gian | Trình | Trước M4 |
| Cập nhật bảng nghiệm thu ([Môi trường §16](../chi-tiet/05-moi-truong-danh-gia.md#16-trình-bày-kết-quả-và-bảng-nghiệm-thu)) khi có kết quả | Trình | Cùng PR của từng việc |
