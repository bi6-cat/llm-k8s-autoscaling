<!-- Mục đích: runbook cho cảnh báo LLMSLOBurnFast (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMSLOBurnFast

**Mức:** page · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** Trong cả 5 phút và 1 phút gần nhất, hơn 20% request phải chờ token đầu tiên lâu hơn 2,5 s (burn rate ≥ 4 so với SLO 95%, [Thông số §6](../chi-tiet/00-thong-so.md#6-slo)).

**Ảnh hưởng.** Khoảng một phần năm người dùng thấy trợ lý "đứng hình" vài giây trước khi trả lời.

**Chẩn đoán nhanh (≤ 5 phút).**
1. Dashboard *Autoscaling*: số replica mong muốn có lớn hơn số replica đang có không? Có pod đang khởi động không?
2. Số replica đã bằng max chưa? Nếu rồi, xem thêm [LLMAtMaxReplicas](LLMAtMaxReplicas.md).
3. Dashboard *Serving và GPU*: hàng đợi tăng ở mọi pod hay chỉ một pod? Có preemption không? Có GPU nào giảm xung hoặc quá nhiệt không?
4. Argo CD: có lần sync nào trong 30 phút gần đây không?

```bash
kubectl -n llm-serving get pods -o wide          # pod nào đang Ready, nằm trên node nào
kubectl -n llm-serving get hpa                   # TARGETS (metric/threshold), REPLICAS hiện tại
```

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Tải vừa tăng, pod mới đang cold start | Theo dõi. Cảnh báo tự tắt khi pod mới Ready và hàng đợi rút hết, thường trong vài phút. Nếu cold start > 3 phút: kiểm tra image đã có sẵn trên node chưa, model có nằm trên NVMe không |
| Đã chạy tối đa replica | Thắt giới hạn tốc độ ở Traefik để bảo vệ phần lớn người dùng; báo người dùng; đề xuất thêm GPU (Vận hành §9) |
| Một pod chậm bất thường | Xem GPU của pod đó (nhiệt độ, XID); xoá pod để nó chuyển đi |
| Ngay sau một lần cập nhật | Rollback bằng `git revert` rồi để Argo CD sync ([Vận hành §5](../chi-tiet/04-van-hanh.md#5-cập-nhật-phiên-bản-khi-gpu-đã-dùng-hết)) |
| KEDA đang lỗi | Autoscaling đã fallback; xử lý theo [KedaScalerErrors](KedaScalerErrors.md) |

**Leo thang.** Sau 15 phút chưa rõ nguyên nhân thì gọi người thứ hai.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` (thời điểm kêu, nguyên nhân, thời gian hồi phục); bổ sung runbook nếu thiếu bước.
