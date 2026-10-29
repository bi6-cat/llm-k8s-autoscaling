<!-- Mục đích: runbook cho cảnh báo LLMAtMaxReplicas (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMAtMaxReplicas

**Mức:** ticket · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** HPA do KEDA tạo (`keda-hpa-vllm-<id>`) đã chạy bằng `maxReplicaCount` suốt 15 phút, mà vẫn có request nằm trong hàng đợi của vLLM. Autoscaling đã hết dư địa.

**Ảnh hưởng.** Chưa chắc người dùng đã bị ảnh hưởng, nhưng nếu tải tăng thêm thì không còn replica để đỡ. Nếu đồng thời có [LLMSLOBurnFast](LLMSLOBurnFast.md) thì người dùng đang phải chờ.

**Chẩn đoán nhanh (≤ 5 phút).**
1. Dashboard *Autoscaling*: metric so với `threshold × replicas`. Metric vượt xa thì đang thiếu năng lực thật.
2. So đỉnh tải với năng lực C của một replica (ĐG1, `capacity-*.json`): tải hiện tại ≈ bao nhiêu C?
3. `maxReplicaCount` có bằng số GPU không? Nhỏ hơn thì còn GPU trống, có thể nâng max.
   ```bash
   kubectl -n llm-serving get scaledobject -o wide       # MIN, MAX, trạng thái
   kubectl get nodes -o custom-columns=NODE:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu
   ```

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Tải thật vượt năng lực toàn cụm | Thắt giới hạn tốc độ ở Traefik nếu SLO đang bị vi phạm; đề xuất thêm GPU (Vận hành §9) |
| `maxReplicaCount` < số GPU | Nâng max trong `autoscaling/official/overlays/<env>/` qua PR, không sửa tay trên cluster |
| Đang chạy fallback của KEDA (giữ max) | Không phải tải thật; xử lý theo [KedaScalerErrors](KedaScalerErrors.md) |
| Tải giả (vòng lặp từ một client) | Tìm client trong log Traefik, chặn hoặc giới hạn |

**Leo thang.** Ticket: xử lý trong giờ làm việc. Nếu kèm page SLO thì làm theo runbook của page đó.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` đỉnh tải và số replica; nếu lặp lại thì đưa vào phần năng lực của luận văn.
