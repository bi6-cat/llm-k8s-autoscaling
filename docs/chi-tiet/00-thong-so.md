# Thông số và chỉ tiêu (nguồn sự thật duy nhất)

> Thuộc [bộ tài liệu đồ án](../mo-ta-chi-tiet-do-an.md#bộ-tài-liệu) · Quyết định liên quan: [ADR-004](../adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md), [ADR-005](../adr/005-sua-thiet-ke-sau-review.md)

**Tóm tắt nhanh**
- Mọi yêu cầu (F1–F7), chỉ tiêu (N1–N8), SLO, kịch bản tải (KB1–KB3), cấu hình đánh giá, tham số triển khai, cấu hình máy và ngân sách được **định nghĩa ở đúng một chỗ: tài liệu này**.
- Các tài liệu khác chỉ giải thích và link về đây, không chép lại giá trị.
- Các giá trị đánh dấu *tạm* sẽ được chốt **một lần** ở ADR-003, sau bước đo năng lực trong phiên V2, trước khi chạy ma trận. Không chỉnh sau khi đã thấy kết quả.

---

## 1. Quy tắc dùng

- Đổi một giá trị thì sửa **ở đây**, qua PR. Nếu đó là một quyết định (không phải sửa lỗi chính tả), ghi thêm ADR.
- Lịch, các phiên thuê GPU và dự toán chi phí theo phiên **không** nằm ở đây. Lịch nằm ở [Kế hoạch](06-ke-hoach-quan-ly.md#1-lịch-và-mốc); các phiên thuê nằm ở [Môi trường và đánh giá](05-moi-truong-danh-gia.md#6-các-phiên-thuê-gpu).
- Nhãn dùng trong bảng: **tạm** = chốt ở ADR-003; **cần kiểm chứng** = phụ thuộc phiên bản phần mềm hoặc nguồn ngoài.

---

## 2. Điều kiện thực hiện

| Hạng mục | Giá trị |
|---|---|
| Hạn nộp luận văn | ~**08/12/2026**. Ngày bảo vệ: chưa có |
| Quỹ giờ | 2 người × 8–15 giờ/tuần, tổng ~135–270 người-giờ đến hạn nộp |
| Phân công | Tạm chưa phân công ([ADR-004](../adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md) K13) |
| Máy nhà | Xem [§10.1](#101-máy-nhà) |
| Cloud | Chính: Vast.ai chế độ VM, 4 × RTX 4090. Dự phòng: máy Vast khác, rồi GCP g2/L4 ([§10.2](#102-gpu-thuê)) |
| Tiền | Xem [§11](#11-ngân-sách) |
| Demo khi bảo vệ | Chốt sau; định hướng là video, cộng phần live nhỏ bằng simulator |

---

## 3. Yêu cầu chức năng

| # | Yêu cầu | Thành phần đáp ứng | Cách kiểm chứng | Mức |
|---|---|---|---|---|
| **F1** | Phục vụ **một model mở cỡ 3–8B** qua API tương thích OpenAI (`/v1/chat/completions`), có streaming | vLLM, Traefik | Gọi API có streaming; chạy được ĐG1–ĐG3 | Must |
| **F2** | Tự điều chỉnh số replica trong khoảng [1, N] theo tải (N = số GPU) | KEDA + HPA, cấu hình A2 | Bài kiểm thử T1–T7; ĐG2 | Must |
| **F3** | Triển khai, cập nhật và rollback qua Git, không thao tác tay trên cluster | Argo CD (bản core, một App-of-Apps), Kustomize | VH2: cập nhật và rollback bằng `git revert` | Must |
| **F4** | Dựng toàn bộ từ máy trắng bằng vài lệnh `make` | Ansible; script `vastai`; Argo CD | VH5 | Must |
| **F5** | **3 dashboard**: Serving + GPU; Autoscaling; SLO + chi phí | Prometheus, Grafana | Kiểm tra trong mọi lượt; ảnh chụp đưa vào luận văn | Must |
| **F6** | **6 cảnh báo** theo SLO và sức khoẻ nền tảng, gửi tới Telegram; **mỗi cảnh báo có runbook** | Alertmanager, `docs/runbooks/` | VH6 | Must |
| **F7** | Bảo vệ tối thiểu: API key, giới hạn tốc độ, một NetworkPolicy, bí mật mã hoá trong Git | `--api-key` của vLLM, Traefik `rateLimit`, NetworkPolicy, Sealed Secrets | Checklist ở [Vận hành](04-van-hanh.md#8-bảo-mật-tối-thiểu) | Should |

Danh sách 6 cảnh báo nằm ở [Vận hành §3.2](04-van-hanh.md#32-danh-sách-cảnh-báo).

---

## 4. Chỉ tiêu nghiệm thu

| # | Nhóm | Chỉ tiêu | Đo bằng | Mức |
|---|---|---|---|---|
| **N1** | Chất lượng phục vụ | Với A2: **SLO attainment ≥ 95%** ở KB1 (pha `steady`) và KB3 (**chỉ pha `sustain`**). Ở KB2 chỉ báo cáo | ĐG2 | Must |
| **N2a** | Tốc độ phản ứng | Ở KB2, mức cold start L2: từ lúc tải tăng đến khi replica mới đầu tiên Ready **≤ 2 phút** | ĐG2 | Must |
| **N2b** | Hồi phục | Ở KB2: thời gian hồi phục SLO. Chỉ báo cáo; ngưỡng (dự kiến ≤ 5 phút) *tạm*, chốt ở ADR-003 | ĐG2 | Should |
| **N3** | Hiệu quả GPU | Ở KB1: A2 dùng **≤ 50% GPU-giờ** của S4, SLO attainment kém S4 **không quá 5 điểm phần trăm**. Ở KB2: báo cáo mức tiết kiệm và cái giá về SLO. Nếu phải chạy với N = 2 thì viết lại theo N ở ADR-003 | ĐG2 | Should |
| **N4** | An toàn khi thay đổi | **0 request lỗi** do scale-down (pha `drop` của KB2, VH1) và do cập nhật phiên bản (VH2, gồm ca chỉ có 1 replica) | ĐG2, VH1, VH2 | Must |
| **N5** | Cold start | Cold start ở mức L2 **≤ 50%** so với L0 | ĐG3 | Should |
| **N6** | Tự phục hồi và khôi phục | Pod hỏng được thay tự động; mất Prometheus thì KEDA chuyển sang fallback (max replica) trong **≤ 30 s**; **dựng lại từ VM trắng ≤ 30 phút**. VM trắng = VM Ubuntu từ template của Vast, có sẵn driver NVIDIA, chưa có image, model hay cluster | VH3, VH4, VH5 | Must |
| **N7** | Quan sát được | Cảnh báo SLO kích hoạt **≤ 5 phút** sau khi SLO bị vi phạm thật (S1 × KB3); **không có page giả** khi A2 chạy KB1 và KB3. Page giả = page trong khi tỷ lệ request xấu theo log client, trên cùng cửa sổ, **< 20%** | VH6 | Should |
| **N8** | Tái lập và chi phí | Mọi phiên bản được ghim; người thứ hai dựng lại cluster nhà (qua Tailscale) hoặc cluster kind + simulator theo README trong **< 1 giờ**; tiền thật thuê GPU **≤ 150 USD** | VH5, sổ chi phí | Should |

**Vì sao chọn các ngưỡng này**
- **95% (N1):** mức SLO phổ biến cho dịch vụ nội bộ. Không áp cho KB2, vì khi tải tăng gấp 6 lần trong 30 giây thì hệ thống nào có cold start cũng vi phạm SLO vài phút. Ở KB3 chỉ tính pha `sustain`, vì trong pha `ramp` pod đầu tiên chắc chắn quá tải trong lúc chờ cold start.
- **2 phút (N2a):** cold start ở mức L2 dự kiến 0,5–1,5 phút, cộng khoảng 10 giây phát hiện.
- **N2b chỉ báo cáo:** request dồn sẵn trong hàng đợi của pod cũ không chuyển được sang pod mới, nên thời gian hồi phục phụ thuộc nhiều vào mức quá tải trước đó.
- **50% (N3):** ở 0,5C, autoscaling chỉ cần 1 trong 4 GPU. Ngưỡng 50% chừa chỗ cho thời gian GPU bị giữ lúc khởi động và lúc chờ ổn định.
- **30 phút (N6):** đủ để cài k3s, GPU, Argo CD và tải model khoảng 15 GB.

---

## 5. Mức độ thành công

| Mức | Nội dung | Ý nghĩa |
|---|---|---|
| **Must** | F1–F6 (F3–F6 ở bản rút gọn); N1, N2a, N4, N6; ĐG1; ĐG2 17 lượt; VH1, VH2 ở nhà (gồm ca 1 replica), VH4, VH5 | Đủ điều kiện bảo vệ |
| **Should** | F7; N2b, N3, N5, N7, N8; ĐG3; VH2 trên GPU thuê, VH3, VH6; dashboard chi phí | Đồ án tốt |
| **Could** | A3 (KV-cache); A4 (flapping) trên simulator; cảnh báo phụ (`LLMSLOBurnSlow`, `LLMPreemptions`, `GPUTemperatureHigh`, `GPUXidError`); `gitleaks`; trigger theo TTFT (E6); `pod-deletion-cost` (E11); warm pool | Đồ án xuất sắc |

Nếu chậm tiến độ thì cắt từ dưới lên theo thứ tự trên ([Kế hoạch §8](06-ke-hoach-quan-ly.md#8-dự-phòng-và-cắt-giảm-phạm-vi)).

**Đã bỏ khỏi phạm vi** ([ADR-004](../adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md)): sync window của Argo CD; burn-in đầy đủ 1 giờ và kiểm tra trôi sau 30 phút; KB2 × A2 ở L0; quy trình vận hành định kỳ trong phần bàn giao (chỉ mô tả trong luận văn); demo trực tiếp trên cluster laptop; TensorDock.

---

## 6. SLO

| Đại lượng | Giá trị | Ghi chú |
|---|---|---|
| TTFT | **≤ 2,5 s** (*tạm*) | Phải **trùng một biên bucket có thật** của histogram `vllm:time_to_first_token_seconds` trong bản đã ghim (*cần kiểm chứng*). Cảnh báo và nghiệm thu dùng **cùng** ngưỡng này |
| TPOT | **≤ 100 ms** | Tương đương ít nhất 10 token/s, nhanh hơn tốc độ đọc |
| Request đạt SLO | TTFT và TPOT đều đạt, và request không lỗi | Lỗi gồm lỗi HTTP, timeout, stream bị cắt (không có `usage`) |
| Mục tiêu SLO attainment | **95%** request đạt SLO | Ngân sách lỗi 5% |
| Tỷ lệ lỗi | **99%** request không trả 5xx | Đo ở Traefik |
| Ngưỡng thực tiễn khi so sánh hai cấu hình | 5 điểm phần trăm SLO attainment; 10% GPU-giờ; 30 s thời gian | Chỉ kết luận "khác nhau" khi mọi lượt cùng chiều và vượt ngưỡng |

---

## 7. Kịch bản tải

Đơn vị **C** là năng lực một replica: tốc độ request lớn nhất mà vẫn đạt SLO, đo ở ĐG1. t tính bằng phút.

| KB | λ(t) / C | Thời lượng | Các pha khi phân tích | Kiểm chứng chủ yếu |
|---|---|---|---|---|
| **KB1** Thấp, ổn định | 0,5 | 20 phút | `steady` [2, 20] | N1, N3 |
| **KB2** Tăng đột ngột rồi giảm | 0,5 khi t < 5; lên 3,0 trong [5; 5,5]; giữ tới 15; về 0,5 trong [15; 15,5]; giữ tới 25 | 25 phút | `pre` [2, 5] · `spike` [5, 15] · `drop` [15, 25] | N2a, N2b (pha `spike`); N4 (pha `drop`); N3 |
| **KB3** Cao, kéo dài | tăng từ 0,5 lên **0,75 × N** (= 3,0 khi N = 4) trong [0, 5]; giữ tới 25 | 25 phút | `ramp` [0, 5] · `sustain` [5, 25] | N1 (pha `sustain`); không flapping; N7 |

Hai phút đầu của KB1 và KB2 là thời gian ổn định, không tính.

**Request**

| Thuộc tính | Giá trị |
|---|---|
| Sinh tải | Open-loop, Poisson với tốc độ λ(t); lịch gửi và độ dài prompt sinh từ seed theo (kịch bản, số thứ tự lượt) |
| Prompt | Văn bản tổng hợp, mỗi request khác nhau; độ dài phân phối đều **256–1024 token** |
| Output | **Cố định 256 token** (`max_tokens=256`, `ignore_eos=true`) |
| Streaming | `stream=true`, `stream_options.include_usage=true` |
| Timeout | 120 s; quá hạn tính là lỗi |
| Đường đi | Qua Traefik bằng **route riêng cho máy tạo tải** (chỉ truy cập được trong cluster) với giới hạn tốc độ cao; khoá API vẫn được vLLM kiểm ([ADR-005](../adr/005-sua-thiet-ke-sau-review.md) T5) |

---

## 8. Cấu hình và ma trận đánh giá

### 8.1. Các cấu hình

| Mã | Tên | Tín hiệu (PromQL, tổng toàn Deployment) | Target mỗi replica | Vai trò | Chạy ở đâu |
|---|---|---|---|---|---|
| **S1** | Static-1 | – (cố định 1 replica) | – | Cấp thiếu: chi phí thấp nhất | GPU thuê |
| **S4** | Static-4 (S_N) | – (cố định N replica) | – | Cấp theo đỉnh: hiệu năng tốt nhất | GPU thuê |
| **A1** | GPU utilization | `sum(DCGM_FI_DEV_GPU_UTIL{…})`, hoặc `sum(nvidia_smi_utilization_gpu_ratio) * 100` trên GPU GeForce | **70** (%) | Đối chứng: cách làm phổ biến | GPU thuê, nhà |
| **A2** | Tải đồng thời | `sum(vllm:num_requests_running) + sum(vllm:num_requests_waiting)` | **0,8 × B\*** (*tạm*; minh hoạ: 24) | **Cấu hình vận hành chính thức** | GPU thuê, nhà, simulator |
| A3 | KV-cache | `sum(vllm:kv_cache_usage_perc)` | 0,8 × KV\* | Could | – |
| A4 | Chỉ hàng đợi | `sum(vllm:num_requests_waiting)` | 5 | Minh hoạ flapping | Simulator |

B\* và KV\* là số request đồng thời trung bình và mức KV-cache trên một replica khi tải bằng C (ĐG1). Ở nhà, target tạm lấy từ ĐG1-mini trên GPU yếu nhất (`capacity-home.json`).

### 8.2. Ma trận ĐG2 (17 lượt)

| Cấu hình \ Kịch bản | KB1 | KB2 | KB3 | Cộng |
|---|---|---|---|---|
| S1 | – | 1 | 1 | 2 |
| S4 | 1 | 1 | 1 | 3 |
| A1 | 2 | 2 | 1 | 5 |
| A2 | 2 | 3 | 2 | 7 |
| **Cộng** | 5 | 7 | 5 | **17** |

- Bỏ S1 × KB1: ở 0,5C, S1 và A2 cùng chạy 1 replica, nên S1 không thêm thông tin.
- Thứ tự lượt được xáo trộn bằng seed ghi lại. Mọi lượt chạy ở mức cold start L2. Mỗi lượt khoảng 35 phút, kể cả reset, warm-up và cooldown.
- Could: thêm A3 × KB1–KB3, mỗi ô 2 lượt.

### 8.3. ĐG1 và ĐG3

| Phép đo | Thiết lập |
|---|---|
| **ĐG1** đo năng lực | 1 replica; quét λ ∈ {0,5; 1,0; 1,5; …} req/s, mỗi mức 1 phút làm ấm + 4 phút đo, bước 0,25 quanh điểm vi phạm; khoảng 2 giờ |
| **ĐG1-mini** ở nhà | Như ĐG1 trên GPU yếu nhất, khoảng 30 phút; chỉ để lấy target tạm |
| **ĐG3** cold start | Scale từ 1 lên 2 replica; **L0 × 2, L2 × 3** |

---

## 9. Tham số triển khai

### 9.1. vLLM

| Tham số | Cloud (GPU 24 GB) | Nhà (GPU 6–8 GB) |
|---|---|---|
| Model | `Qwen/Qwen2.5-7B-Instruct` (revision ghim) | `Qwen/Qwen2.5-1.5B-Instruct` (hoặc bản 3B AWQ) |
| `--served-model-name` | `qwen2.5-7b` | `qwen2.5-1.5b` |
| `--max-model-len` | 8192 | 4096 |
| `--max-num-seqs` | 64 | 32 |
| `--gpu-memory-utilization` | 0,90 | 0,85 (0,80 nếu GPU còn chạy màn hình) |
| `--max-num-batched-tokens` | Mặc định, ghi lại giá trị | như cloud |
| Prefix caching | **Tắt** khi đánh giá (`--no-enable-prefix-caching`); bật khi vận hành thật | như cloud |
| `--shutdown-timeout` | **150** (s) (*cần kiểm chứng* tên cờ trên bản ghim) | như cloud |
| `--api-key` | Lấy từ Secret | như cloud |
| Image | `vllm/vllm-openai@sha256:…`, ghim theo digest | như cloud (*cần kiểm chứng* trên RTX 5060, sm_120) |

### 9.2. Deployment vLLM

| Trường | Giá trị |
|---|---|
| `replicas` | **Không đặt** (HPA quản lý) |
| GPU | `nvidia.com/gpu: 1` mỗi pod |
| CPU, RAM | Cloud: requests = limits, `cpu: 6`, `memory: 24Gi` (QoS Guaranteed). Nhà: request `cpu: 2`, `memory: 4–6Gi`; limit `memory: 8Gi` |
| `/dev/shm` | `emptyDir: {medium: Memory, sizeLimit: 8Gi}` |
| `startupProbe` | `/health`, chu kỳ 5 s, `failureThreshold: 120` (tối đa 10 phút) |
| `readinessProbe` | `/health`, chu kỳ 5 s |
| `livenessProbe` | `/health`, chu kỳ 10 s, `failureThreshold: 6` |
| `preStop` | `sleep 20` |
| `terminationGracePeriodSeconds` | **180** (phải > preStop + `--shutdown-timeout`) |
| `strategy` | `RollingUpdate`, `maxSurge: 0`, `maxUnavailable: 1`; khi chỉ có 1 replica thì nâng `minReplicaCount` lên 2 trước khi cập nhật |
| `progressDeadlineSeconds` | 900 |
| `imagePullPolicy` | `IfNotPresent` |
| Lưu model | Cloud: hostPath trên NVMe (`/mnt/nvme/models`), compile cache ở `/mnt/nvme/vllm-cache`. Nhà: PVC `model-cache` (local-path) |

### 9.3. KEDA và HPA

| Tham số | Giá trị |
|---|---|
| `minReplicaCount` / `maxReplicaCount` | 1 / **N = 4** (bằng số GPU và bằng S4). Ở nhà: số GPU có thật (1–2). Simulator: 3 |
| `metricType` | `AverageValue` cho mọi trigger (desired = ⌈tổng ÷ target⌉) |
| `pollingInterval` | 5 s |
| Chu kỳ sync HPA | **5 s** (k3s: `--kube-controller-manager-arg=horizontal-pod-autoscaler-sync-period=5s`) |
| scaleUp | Mặc định của HPA: cửa sổ 0; tăng 100% hoặc thêm 4 pod mỗi 15 s |
| scaleDown | `stabilizationWindowSeconds: 300`; 1 pod mỗi 60 s |
| tolerance | 10% (mặc định) |
| `fallback` | `failureThreshold: 3`, `replicas` = max |
| Target | Theo [§8.1](#81-các-cấu-hình) |

### 9.4. Giám sát

| Tham số | Giá trị |
|---|---|
| Chu kỳ scrape vLLM, Traefik | 5 s |
| Chu kỳ thu metric GPU (DCGM hoặc `nvidia_gpu_exporter`) | 5 s |
| Retention Prometheus | Cloud: 15 ngày. Nhà: 3 ngày (RAM 16 GB) |
| Số dashboard / số cảnh báo | 3 / 6 ([F5](#3-yêu-cầu-chức-năng), [F6](#3-yêu-cầu-chức-năng)) |

---

## 10. Máy và môi trường

### 10.1. Máy nhà

| Máy | Cấu hình | Vai trò |
|---|---|---|
| PC | RTX 5060 8 GB (Blackwell, sm_120); CPU 6 nhân/12 luồng; RAM 16 GB; ổ trống 100–200 GB; bật 24/7; Tailscale; mạng ~30 MB/s | Node chủ k3s có GPU |
| Laptop (nếu được) | RTX 4050 Laptop 6 GB (Ada, sm_89); RAM 16 GB | Node agent có GPU |
| Laptop không GPU | – | kind/k3d + `llm-d-inference-sim`; truy cập cluster nhà qua Tailscale |

Máy nhà là **môi trường chức năng**: không dùng số liệu hiệu năng của nó trong chương đánh giá.

### 10.2. GPU thuê

**Chính: Vast.ai chế độ VM, 4 × RTX 4090 24 GB.** Tiêu chí lọc máy:

| Tiêu chí | Ngưỡng |
|---|---|
| Chế độ | VM (`vms_enabled=true`), on-demand |
| GPU | Máy có **đúng 4** RTX 4090, thuê cả 4 (dự phòng: 4 × RTX 3090 hoặc A5000) |
| Độ tin cậy | ≥ 0,98 |
| CPU / RAM | ≥ 32 vCPU (nên ≥ 48) / ≥ 128 GB |
| Ổ đĩa | ≥ 300 GB, đọc tuần tự ≥ 1 GB/s |
| PCIe / mạng | Gen4 trở lên / tải xuống ≥ 500 Mbps |
| Giá | **≤ 0,50 USD/GPU-giờ** |

**Dự phòng cuối:** GCP g2-standard-48 (4 × L4) bằng credit, chạy k3s trên Compute Engine ([Môi trường §5](05-moi-truong-danh-gia.md#5-dự-phòng-gcp-và-kế-hoạch-z)).

---

## 11. Ngân sách

| Hạng mục | Giá trị |
|---|---|
| Trần tiền thật cho GPU thuê | **≤ 150 USD** |
| Dự toán (phương án Vast) | ~30–75 USD ([các phiên thuê](05-moi-truong-danh-gia.md#6-các-phiên-thuê-gpu)) |
| Đã nạp | 800.000 VND (~30 USD, tỷ giá ~26.000 VND/USD). <!-- TODO(review:§0.3): chưa rõ nạp vào Vast hay GCP --> |
| Credit GCP | 200 USD, hết hạn khoảng 01/2027; **chỉ** dùng cho phương án dự phòng |
| Số dư tối thiểu trước phiên V2 | ≥ 1,3 × chi phí dự kiến của V2; runner báo động khi số dư < 30 USD |
