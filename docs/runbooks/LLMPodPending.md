<!-- Mục đích: runbook cho cảnh báo LLMPodPending (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMPodPending

**Mức:** ticket · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** Một pod vLLM ở trạng thái Pending hơn 10 phút: chưa được xếp lên node nào, hoặc đã có node nhưng container chưa chạy (đang tải image, chờ volume).

**Ảnh hưởng.** Ít replica hơn mức HPA muốn. Người dùng chưa chắc bị ảnh hưởng; nếu kèm [LLMSLOBurnFast](LLMSLOBurnFast.md) thì có.

**Chẩn đoán nhanh (≤ 5 phút).**
```bash
kubectl -n llm-serving get pods -o wide
kubectl -n llm-serving describe pod <pod> | sed -n '/Events:/,$p'     # đọc phần Events ở cuối
```
- `0/2 nodes are available: ... Insufficient nvidia.com/gpu`: không còn GPU trống.
- `Pulling image` kéo dài: đang tải image (~30 GB).
- `didn't match Pod's node affinity/selector`: node phù hợp đang tắt (ví dụ laptop).

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Hết GPU, đang có rollout | Rolling update bị kẹt; xem [Vận hành §5](../chi-tiet/04-van-hanh.md#5-cập-nhật-phiên-bản-khi-gpu-đã-dùng-hết) (`maxSurge: 0`, tạm nâng `minReplicaCount`) |
| Hết GPU, không có rollout | `maxReplicaCount` lớn hơn số GPU đang có: hạ max qua PR, hoặc bật lại node GPU |
| Pod cũ chưa trả GPU (đang terminating) | Chờ hết `terminationGracePeriodSeconds`; nếu pod cũ treo thì xem log của nó |
| Đang tải image lâu | Kiểm tra mạng và dung lượng ổ trên node (`df -h`); lần sau tải trước image (`make prefetch`) |
| Node phù hợp đang tắt | Bật node, hoặc chấp nhận và ghi lại |

**Leo thang.** Ticket. Nếu Pending kéo dài trong phiên đánh giá thì báo cả nhóm vì kết quả lượt đó không dùng được.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md`; bổ sung runbook nếu thiếu bước.
