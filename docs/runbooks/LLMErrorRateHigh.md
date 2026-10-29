<!-- Mục đích: runbook cho cảnh báo LLMErrorRateHigh (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMErrorRateHigh

**Mức:** page · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** Trong 5 phút gần nhất, ≥ 1% request tới vLLM bị Traefik trả mã 5xx, kéo dài ít nhất 1 phút (SLO lỗi 99%, [Thông số §6](../chi-tiet/00-thong-so.md#6-slo)).

**Ảnh hưởng.** Người dùng nhận lỗi thay vì câu trả lời. Lỗi đo ở cửa vào nên gồm cả lúc không còn pod nào nhận request.

**Chẩn đoán nhanh (≤ 5 phút).**
1. Còn pod Ready nào không? Không còn pod Ready thì Traefik trả 503.
   ```bash
   kubectl -n llm-serving get pods
   kubectl -n llm-serving get endpointslices -l kubernetes.io/service-name=vllm   # có địa chỉ nào không
   ```
2. Mã lỗi là gì (Grafana, `sum by (code) (rate(traefik_service_requests_total{service=~"llm-serving-.*"}[5m]))`)?
   - 503: không có endpoint (mọi pod đều không Ready, hoặc đang rollout với 1 replica).
   - 502: pod chết hoặc đóng kết nối giữa chừng.
   - 500: lỗi trong vLLM, xem log.
3. Log vLLM và Traefik:
   ```bash
   kubectl -n llm-serving logs deploy/vllm --since=10m | grep -iE 'error|exception' | tail -20
   kubectl -n kube-system logs -l app.kubernetes.io/name=traefik --since=10m | tail -20
   ```

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Không còn pod Ready | Xem [LLMPodNotReady](LLMPodNotReady.md) hoặc [LLMPodCrashLooping](LLMPodCrashLooping.md) |
| Đang rollout với 1 replica | Tạm nâng `minReplicaCount` lên 2 trước khi cập nhật ([Vận hành §5](../chi-tiet/04-van-hanh.md#5-cập-nhật-phiên-bản-khi-gpu-đã-dùng-hết)) |
| Lỗi 500 sau khi đổi tham số hoặc phiên bản | Rollback bằng `git revert`, để Argo CD sync |
| Pod bị OOMKilled giữa chừng (502) | `kubectl describe pod` xem `Last State`; giảm `--max-num-seqs` hoặc `--max-model-len` |

**Leo thang.** Lỗi kéo dài 10 phút mà không rõ nguyên nhân thì gọi người thứ hai.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md`; bổ sung runbook nếu thiếu bước.
