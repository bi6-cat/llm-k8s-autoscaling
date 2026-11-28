<!-- Mục đích: runbook cho cảnh báo LLMPodPending (common/observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMPodPending

**Mức:** ticket · **Quy tắc:** [common/observability/alerts/llm.yaml](../../common/observability/alerts/llm.yaml)

**Ý nghĩa.** Một pod vLLM ở trạng thái Pending hơn 10 phút: chưa được xếp lên node nào, hoặc đã có node nhưng container chưa chạy (đang tải image, chờ volume).

**Ảnh hưởng.** Ít replica hơn mức HPA muốn. Người dùng chưa chắc bị ảnh hưởng; nếu kèm [LLMSLOBurnFast](LLMSLOBurnFast.md) thì có.

**Lưu ý.** Pending vài phút lúc rollout là bình thường. vLLM 0.31.0 không tự thoát khi nhận SIGTERM, nên pod cũ luôn giữ GPU đủ `terminationGracePeriodSeconds` (180 s) rồi mới bị kill, và pod mới chờ chừng ấy ([nhật ký vận hành](../nhat-ky/van-hanh.md), mục 06/11 và 16/11). Trên V2, rollout 4 pod với `maxSurge: 0` mất 371,6 s. Ở VH2c (`maxSurge: 1` khi hết GPU), pod mới Pending suốt 300 s rồi kịch bản khôi phục, chưa tới `for: 10m` nên cảnh báo không kêu. Ngược lại, ở PC nhà, một lần kéo lại image (gần 15 phút, xem bảng dưới) đủ làm cảnh báo kêu dù không có gì hỏng; khi đó chỉ cần chờ kéo xong.

**Chẩn đoán nhanh (≤ 5 phút).**
```bash
kubectl -n llm-serving get pods -o wide
kubectl -n llm-serving describe pod <pod> | sed -n '/Events:/,$p'     # đọc phần Events ở cuối
```
- `0/2 nodes are available: ... Insufficient nvidia.com/gpu`: không còn GPU trống.
- `Pulling image` kéo dài: đang tải image (khoảng 9–11 GB nén, khoảng 32 GB sau giải nén, nên ổ cần trống nhiều hơn cỡ tải về). Đo được: 2 phút 34 giây trên V2, 14 phút 52 giây ở PC nhà.
- `didn't match Pod's node affinity/selector`: node phù hợp đang tắt (ví dụ laptop).

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Hết GPU, đang có rollout | Rolling update bị kẹt; xem [Vận hành §5](../chi-tiet/04-van-hanh.md#5-cập-nhật-phiên-bản-khi-gpu-đã-dùng-hết) (`maxSurge: 0`, tạm nâng `minReplicaCount`) |
| Hết GPU, không có rollout | `maxReplicaCount` lớn hơn số GPU đang có: hạ max qua PR, hoặc bật lại node GPU |
| Pod cũ chưa trả GPU (đang terminating) | Chờ hết `terminationGracePeriodSeconds` (180 s; pod cũ luôn chờ đủ, xem Lưu ý). Quá 180 s mà pod cũ vẫn `Terminating` thì xem log của nó và trạng thái node |
| Đang tải image lâu | Kiểm tra mạng và dung lượng ổ trên node (`df -h`); lần sau tải trước image (`make prefetch` trên VM thuê) |
| Image không còn trên node sau khi vLLM ở 0 replica | Gặp ở PC nhà 16/11; nguyên nhân chưa xác định, nghi kubelet image GC (xoá image không còn container nào dùng khi đĩa vượt ngưỡng, mặc định 85 %; đĩa `/` đo được 80 % sau khi đã kéo lại). Giữ đĩa dưới ngưỡng GC (nhà đã nâng lên 95/90 %, `ansible/inventory/group_vars/home.yaml`); trước phiên đo, scale lên 1 pod và chờ Ready rồi mới chạy runner |
| Node phù hợp đang tắt | Bật node, hoặc chấp nhận và ghi lại |

**Leo thang.** Ticket. Nếu Pending kéo dài trong phiên đánh giá thì báo cả nhóm vì kết quả lượt đó không dùng được.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md`; bổ sung runbook nếu thiếu bước.
