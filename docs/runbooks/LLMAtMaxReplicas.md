<!-- Mục đích: runbook cho cảnh báo LLMAtMaxReplicas (common/observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMAtMaxReplicas

**Mức:** ticket · **Quy tắc:** [common/observability/alerts/llm.yaml](../../common/observability/alerts/llm.yaml)

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
| Tải thật vượt năng lực toàn cụm | Báo người dùng; đề xuất thêm GPU (Vận hành §9). Không có giới hạn tốc độ ở Traefik để thắt: lớp này đã lược ngày 12/11 ([Vận hành §8](../chi-tiet/04-van-hanh.md#8-bảo-mật-tối-thiểu)) |
| `maxReplicaCount` < số GPU | Nâng max trong `common/autoscaling/a2/` (hoặc overlay `envs/<env>/autoscaling/`) qua PR, không sửa tay trên cluster |
| Đang chạy fallback của KEDA (giữ max) | Không phải tải thật; xử lý theo [KedaScalerErrors](KedaScalerErrors.md) |
| Tải giả (vòng lặp từ một client) | Tìm client trong log Traefik, chặn hoặc giới hạn |

**Leo thang.** Ticket: xử lý trong giờ làm việc. Nếu kèm page SLO thì làm theo runbook của page đó.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` đỉnh tải và số replica; nếu lặp lại thì đưa vào phần năng lực của luận văn.
