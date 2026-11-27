<!-- Mục đích: Phụ lục C, runbook mẫu cho cảnh báo LLMSLOBurnFast, mà mục 3.5 và 4.6 dẫn tới. Người viết: Trình. -->
<!-- Chép từ docs/runbooks/LLMSLOBurnFast.md trên main (commit caf6a19, 21/11/2026), đổi link tương đối thành tên file, bỏ dẫn chiếu tới tài liệu thiết kế (Thông số §6, Vận hành §5, §8, §9) vì người đọc luận văn không có các tài liệu đó, bỏ ngày lược rate limit (12/11/2026); các ý khác giữ nguyên. Sửa runbook thì cập nhật bản ở đây. Số dòng của bảy runbook đếm bằng wc -l ngày 27/11/2026. -->

# Phụ lục C. Runbook mẫu {.unnumbered}

Mỗi cảnh báo trong Bảng B.1 có một runbook cùng tên trong thư mục `docs/runbooks/` của repository, dài 29–53 dòng. Đường dẫn runbook nằm trong annotation `runbook_url` của quy tắc, nên tin cảnh báo gửi qua Telegram có sẵn link tới runbook. Mọi runbook theo cùng một khung: mức và quy tắc, ý nghĩa, ảnh hưởng tới người dùng, chẩn đoán nhanh trong 5 phút, bảng nguyên nhân và hành động, khi nào leo thang, ghi gì sau sự cố. Phần dưới đây là runbook của `LLMSLOBurnFast` (commit `caf6a19`), chép lại nội dung, chỉ bỏ các dẫn chiếu tới tài liệu thiết kế nội bộ.
<!-- nguồn: wc -l docs/runbooks/*.md (29–53 dòng, 27/11/2026); annotation runbook_url trong common/observability/alerts/llm.yaml -->

## C.1. Runbook `LLMSLOBurnFast`

**Mức:** page. **Quy tắc:** `common/observability/alerts/llm.yaml`.

**Ý nghĩa.** Trong cả 5 phút và 1 phút gần nhất, hơn 20% request phải chờ token đầu tiên lâu hơn 2,5 s (burn rate ≥ 4 so với SLO 95%).
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md; docs/chi-tiet/00-thong-so.md §6 -->

**Ảnh hưởng.** Khoảng một phần năm người dùng thấy trợ lý "đứng hình" vài giây trước khi trả lời.
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md -->

**Chẩn đoán nhanh (≤ 5 phút).**
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md, phần chẩn đoán -->

1. Dashboard *Autoscaling*: số replica mong muốn có lớn hơn số replica đang có không? Có pod đang khởi động không?
2. Số replica đã bằng max chưa? Nếu rồi, xem thêm runbook `LLMAtMaxReplicas`.
3. Dashboard *Serving và GPU*: hàng đợi tăng ở mọi pod hay chỉ một pod? Có preemption không? Có GPU nào giảm xung hoặc quá nhiệt không?
4. Argo CD: có lần sync nào trong 30 phút gần đây không?
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md -->

```bash
kubectl -n llm-serving get pods -o wide          # pod nào đang Ready, nằm trên node nào
kubectl -n llm-serving get hpa                   # TARGETS (metric/threshold), REPLICAS hiện tại
```

**Xử lý.** Bảng C.1 ghép từng nguyên nhân thường gặp với hành động tương ứng.
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md, bảng Xử lý -->

**Bảng C.1.** Nguyên nhân và hành động trong runbook `LLMSLOBurnFast`

| Nguyên nhân | Hành động |
|---|---|
| Tải vừa tăng, pod mới đang cold start | Theo dõi. Cảnh báo tự tắt khi pod mới Ready và hàng đợi rút hết, thường trong vài phút. Nếu cold start > 3 phút: kiểm tra image đã có sẵn trên node chưa, model có nằm trên NVMe không |
| Đã chạy tối đa replica | Báo người dùng; đề xuất thêm GPU. Không có giới hạn tốc độ ở Traefik để cắt bớt tải, vì lớp này đã được lược khỏi thiết kế |
| Một pod chậm bất thường | Xem GPU của pod đó (nhiệt độ, XID); xoá pod để nó chuyển đi |
| Ngay sau một lần cập nhật | Rollback bằng `git revert` rồi để Argo CD sync |
| KEDA đang lỗi | Autoscaling đã fallback; xử lý theo runbook `KedaScalerErrors` |
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md, commit caf6a19 -->

**Leo thang.** Sau 15 phút chưa rõ nguyên nhân thì gọi người thứ hai.
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md -->

**Sau sự cố.** Ghi vào nhật ký vận hành của repository (thời điểm kêu, nguyên nhân, thời gian hồi phục); bổ sung runbook nếu thiếu bước.
<!-- nguồn: docs/runbooks/LLMSLOBurnFast.md -->
