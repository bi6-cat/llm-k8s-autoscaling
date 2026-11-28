<!-- Mục đích: runbook cho cảnh báo LLMPodNotReady (common/observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMPodNotReady

**Mức:** page · **Quy tắc:** [common/observability/alerts/llm.yaml](../../common/observability/alerts/llm.yaml)

**Ý nghĩa.** Một pod vLLM ở phase `Running` (đã có node, container đã khởi động ít nhất một lần) hơn 15 phút mà readiness probe vẫn chưa đạt. 15 phút lâu hơn nhiều so với cold start đo được. Riêng đoạn từ lúc container chạy tới Ready: 155–162 s ở PC nhà. Cả quá trình từ lệnh scale tới Ready trên V2: 76–81 s khi image và model có sẵn (L2), 300–311 s khi phải kéo lại image và tải lại model (L0; phần kéo image nằm ở phase Pending). Vì vậy pod gần như chắc chắn bị treo. Pod Pending không tính ở đây mà thuộc [LLMPodPending](LLMPodPending.md).

**Lưu ý.** startupProbe cho container tối đa 10 phút (5 s × 120 lần), quá hạn thì kubelet restart container mà pod vẫn ở `Running`. Nên lúc cảnh báo kêu, container thường đã restart ít nhất một lần (cột `RESTARTS` ≥ 1), và log của lần treo đầu nằm ở `--previous`. Sau mỗi lần restart, kubelet chờ một khoảng backoff với lý do `CrashLoopBackOff`, nên [LLMPodCrashLooping](LLMPodCrashLooping.md) có thể kêu gần cùng lúc, kể cả khi mới restart một lần. Hai cảnh báo đó là cùng một sự cố.

**Ảnh hưởng.** Pod giữ một GPU mà không phục vụ request. Nếu đó là pod duy nhất thì Traefik trả 503 ([LLMErrorRateHigh](LLMErrorRateHigh.md)).

**Chẩn đoán nhanh (≤ 5 phút).**
```bash
kubectl -n llm-serving describe pod <pod> | sed -n '/Conditions:/,/Volumes:/p;/Events:/,$p'
kubectl -n llm-serving get pod <pod>              # cột RESTARTS: startupProbe đã restart container chưa
kubectl -n llm-serving logs <pod> --tail=50       # lần chạy hiện tại đang dừng ở bước nào
kubectl -n llm-serving logs <pod> --previous --tail=50   # lần chạy trước (bị startupProbe restart)
```
Các bước khởi động của vLLM theo thứ tự: tải/nạp weights → `torch.compile` → capture CUDA graph → khởi tạo engine → mở cổng 8000. Log dừng ở bước nào thì nghi bước đó.

**Xử lý.**

| Nguyên nhân | Hành động |
|---|---|
| Treo khi nạp model (đọc ổ chậm, model chưa có sẵn) | Kiểm tra đường dẫn model và ổ chứa; tải model trước |
| Thiếu `/dev/shm` hoặc VRAM | Xem log có `out of memory`/`shm`; sửa tham số qua PR |
| Sai tham số sau cập nhật | Rollback bằng `git revert`, để Argo CD sync |
| Readiness probe sai (đường dẫn, cổng) | So probe trong `common/serving/deployment.yaml` với cổng vLLM |
| Không rõ | Xoá pod để tạo lại (`kubectl delete pod <pod>`); nếu lặp lại thì không xoá nữa, giữ pod để điều tra |

**Leo thang.** Pod duy nhất không Ready (dịch vụ ngừng) thì gọi người thứ hai ngay.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` (bước khởi động bị treo, thời gian); bổ sung runbook nếu thiếu bước.
