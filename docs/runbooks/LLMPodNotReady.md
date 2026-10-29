<!-- Mục đích: runbook cho cảnh báo LLMPodNotReady (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMPodNotReady

**Mức:** page · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** Một pod vLLM đã Running (container đang chạy) hơn 15 phút mà readiness probe vẫn chưa đạt. 15 phút lâu hơn nhiều so với cold start bình thường (vài phút), nên pod gần như chắc chắn bị treo. Pod Pending không tính ở đây mà thuộc [LLMPodPending](LLMPodPending.md).

**Ảnh hưởng.** Pod giữ một GPU mà không phục vụ request. Nếu đó là pod duy nhất thì Traefik trả 503 ([LLMErrorRateHigh](LLMErrorRateHigh.md)).

**Chẩn đoán nhanh (≤ 5 phút).**
```bash
kubectl -n llm-serving describe pod <pod> | sed -n '/Conditions:/,/Volumes:/p;/Events:/,$p'
kubectl -n llm-serving logs <pod> --tail=50       # vLLM đang dừng ở bước nào
```
Các bước khởi động của vLLM theo thứ tự: tải/nạp weights → `torch.compile` → capture CUDA graph → khởi tạo engine → mở cổng 8000. Log dừng ở bước nào thì nghi bước đó.

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Treo khi nạp model (đọc ổ chậm, model chưa có sẵn) | Kiểm tra đường dẫn model và ổ chứa; tải model trước |
| Thiếu `/dev/shm` hoặc VRAM | Xem log có `out of memory`/`shm`; sửa tham số qua PR |
| Sai tham số sau cập nhật | Rollback bằng `git revert`, để Argo CD sync |
| Readiness probe sai (đường dẫn, cổng) | So probe trong `serving/base/deployment.yaml` với cổng vLLM |
| Không rõ | Xoá pod để tạo lại (`kubectl delete pod <pod>`); nếu lặp lại thì không xoá nữa, giữ pod để điều tra |

**Leo thang.** Pod duy nhất không Ready (dịch vụ ngừng) thì gọi người thứ hai ngay.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` (bước khởi động bị treo, thời gian); bổ sung runbook nếu thiếu bước.
