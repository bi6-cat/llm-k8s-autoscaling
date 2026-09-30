# 5. Kiến trúc hệ thống: tài liệu chuyên sâu

> Thuộc [Mục 5 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#5-kiến-trúc-hệ-thống) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Năm nguyên tắc thiết kế: **đơn giản và minh bạch, tái lập được, đo được mọi thứ, kiểm soát biến, an toàn khi scale**.
- Chi tiết tầng serving: cấu hình Deployment vLLM, lưu trữ model, Service, Ingress (Traefik hoặc Envoy Gateway, **không dùng ingress-nginx vì đã ngừng bảo trì**).
- Hai vòng đời quan trọng nhất của pod: **cold start 8 pha** (Hình 12) và **graceful shutdown** (Hình 13).
- Kiến trúc giám sát (PodMonitor, chu kỳ scrape, recording rule) và GitOps, kèm hai cạm bẫy hay gặp: **Argo CD tranh quyền `replicas` với HPA**, và **ServiceMonitor không được Prometheus nhận** vì thiếu label.

---

## 1. Nguyên tắc thiết kế

| Nguyên tắc | Cụ thể hoá |
|---|---|
| **Đơn giản, minh bạch** | Dùng Deployment và KEDA thay vì một framework serving nhiều tầng. Mọi quyết định scale đều truy được về một câu PromQL |
| **Tái lập được** | Mọi thứ nằm trong Git: IaC dựng máy, Argo CD dựng nền tảng, runner chạy thí nghiệm. Không có bước làm tay |
| **Đo được mọi thứ** | Mỗi pha của request, của cold start và của lần scale đều có timestamp |
| **Kiểm soát biến** | Giữa các cấu hình chỉ khác **một** thứ (metric hoặc số replica); mọi tham số khác được ghim |
| **An toàn khi scale** | Có probe đúng, có preStop, grace period đủ dài, và không để request bị cắt |

---

## 2. Tổng quan và namespace

![Hình 2 – Kiến trúc tổng thể](../images/02-kien-truc-tong-the.svg)

*Hình 2 (tài liệu chính). Kiến trúc tổng thể.*

| Namespace | Thành phần | Ghi chú |
|---|---|---|
| `llm-serving` | Deployment `vllm`, Service, PVC `model-cache`, PodMonitor, ScaledObject | Workload chính |
| `keda` | KEDA operator, metrics API server, admission webhook | Helm chart `kedacore/keda` |
| `monitoring` | Prometheus Operator, Prometheus, Grafana, kube-state-metrics, node-exporter | Helm chart `kube-prometheus-stack` |
| `gpu-operator` | Device plugin, GFD, DCGM exporter (và toolkit nếu cần) | Helm chart `nvidia/gpu-operator` |
| `argocd` | Argo CD | Nền của GitOps |
| `kube-system` | Traefik (có sẵn trong k3s), CoreDNS… | – |

**Bảng phiên bản** (điền và ghim khi triển khai, rồi ghi vào `metadata.json`):

| Thành phần | Phiên bản | Cách ghim |
|---|---|---|
| k3s | `v1.xx.y+k3s1` | Biến `INSTALL_K3S_VERSION` |
| NVIDIA driver | `5xx.yy` | Gói hệ điều hành hoặc image VM |
| GPU Operator | `vXX.Y.Z` | Phiên bản Helm chart |
| vLLM | `vllm/vllm-openai@sha256:…` | **Digest** thay vì tag |
| Model | `Qwen/Qwen2.5-7B-Instruct@<commit>` | Revision trên Hugging Face |
| KEDA, kube-prometheus-stack, Argo CD | Phiên bản chart | `Chart.yaml` / Argo Application |

---

## 3. Tầng serving

### 3.1. Deployment vLLM: giải thích từng lựa chọn

| Trường | Giá trị | Vì sao |
|---|---|---|
| `replicas` | **Bỏ trống trong manifest** | Để HPA quản lý; nếu đặt thì Argo CD sẽ "sửa lại" (xem §10.3) |
| `resources.limits.nvidia.com/gpu` | 1 | Mỗi replica dùng 1 GPU |
| `resources.requests.cpu` | 4–6 | API server cần CPU để tokenize và stream (xem [04 §3.6](04-kien-thuc-nen.md#36-kiến-trúc-tiến-trình-của-vllm-v1)) |
| QoS **Guaranteed** (requests = limits, CPU nguyên) | cpu 6, memory 24Gi | Với kubelet `cpu-manager-policy=static`, pod nhận **lõi CPU riêng**, không tranh với máy tạo tải chạy cùng VM ([06 §3.5](06-moi-truong-chi-phi.md#35-cấu-hình-k3s-và-phân-bổ-cpu-trên-vm-thuê)) |
| `resources.requests/limits.memory` | 24–32 Gi | Nạp weights qua RAM; nếu giới hạn quá thấp sẽ bị OOM lúc khởi động |
| `/dev/shm` | `emptyDir: {medium: Memory}` 8 Gi | PyTorch và NCCL dùng shared memory; mặc định chỉ có 64 MiB |
| `startupProbe` | `/health`, chu kỳ 5 s, tối đa 120 lần thử | Cho phép cold start tới 10 phút mà không bị kill |
| `readinessProbe` | `/health`, chu kỳ 5 s | Quyết định lúc nào pod nhận traffic |
| `livenessProbe` | `/health`, chu kỳ 10 s, `failureThreshold: 6` | Rộng tay để tránh kill nhầm khi pod đang rất tải |
| `preStop` | `sleep 20` | Chờ Endpoints cập nhật (xem §8) |
| `terminationGracePeriodSeconds` | 180 | Lớn hơn preStop cộng request dài nhất |
| `imagePullPolicy` | `IfNotPresent` | Để pre-pull có tác dụng |
| env `HF_HOME`, `VLLM_CACHE_ROOT` | Trỏ vào volume | Giữ lại cache model và compile cache (mức L2) |
| args | `--no-enable-prefix-caching` | Kiểm soát biến (xem [04 §3.4](04-kien-thuc-nen.md#34-prefix-caching)) |

### 3.2. Lưu trữ model: các phương án

| Phương án | Mô tả | Ưu điểm | Nhược điểm | Mức |
|---|---|---|---|---|
| Tải từ Hugging Face mỗi lần | `--model Qwen/...`, không mount gì | Đơn giản | Chậm, phụ thuộc mạng, dễ bị giới hạn tốc độ | L0 |
| PVC dùng chung (NFS, RWX) | Một bản model, mọi pod mount chung | Tải một lần | Đọc qua mạng chậm; NFS là điểm nghẽn khi nhiều pod cùng nạp | L1 |
| **NVMe cục bộ** (hostPath hoặc local PV) | Model nằm sẵn trên ổ của node | **Nạp nhanh nhất** | Phải chép lên từng node trước (Job hoặc DaemonSet) | L2 |
| Đóng model vào image | Image chứa luôn weights | Một artifact duy nhất | Image khoảng 25 GB, pull rất lâu | Không khuyến nghị |
| Stream từ object storage | `--load-format runai_streamer` | Không cần ổ cục bộ | Phụ thuộc băng thông object storage | Hướng mở rộng |

**Khuyến nghị:** trên laptop, dùng PVC cho đơn giản. Trên máy thuê (một node), dùng L2: một Job `model-prefetch` tải model về `/mnt/nvme/models`, rồi Deployment mount `hostPath` ở chế độ chỉ đọc. Đồ án chỉ đo L0 và L2 (ADR-001), vì trên một máy thuê không có ổ mạng tương đương để đo L1 một cách thực tế.

### 3.3. Service và cân bằng tải

- Service kiểu `ClusterIP`. kube-proxy (chế độ iptables) chọn endpoint **gần như ngẫu nhiên, đều nhau**, không biết pod nào đang có hàng đợi dài.
- Hệ quả: khi các request dài ngắn khác nhau, có lúc một pod bị dồn nhiều request dài trong khi pod khác rảnh. Năng lực thực tế vì thế thấp hơn N × C một chút.
- Trong đồ án, round-robin được **giữ nguyên cho mọi cấu hình** để so sánh công bằng. Nhóm theo dõi độ lệch `num_requests_running` giữa các pod để lượng hoá hiện tượng này.
- Có thể thay bằng Envoy Gateway với thuật toán `LEAST_REQUEST`, hoặc định tuyến nhận biết LLM. Đây là hướng mở rộng ([15 – E1](15-huong-mo-rong.md#e1-định-tuyến-có-nhận-biết-llm)).

### 3.4. Ingress / Gateway

- **ingress-nginx** đã được Kubernetes cho **ngừng bảo trì từ tháng 3/2026**, nên không nên dùng cho hệ thống mới.
- **Traefik** có sẵn trong k3s và hỗ trợ SSE streaming tốt. Nhóm khuyến nghị Traefik cho đơn giản. Envoy Gateway (Gateway API) là lựa chọn thay thế nếu muốn dùng `LEAST_REQUEST`.
- Với streaming dài, cần kiểm tra **timeout** của entrypoint và route để stream không bị cắt giữa chừng, và kiểm tra rằng proxy không gom (buffer) response lại.
- **Trong thí nghiệm**, có thể cho máy tạo tải gọi thẳng Service qua NodePort để loại bỏ Ingress khỏi danh sách biến. Nếu làm vậy, phải ghi rõ trong phần phương pháp.

### 3.5. Bảo mật tối thiểu

- Không mở API ra Internet; chỉ máy tạo tải (cùng mạng riêng) được gọi.
- Có thể bật `--api-key` hoặc xác thực ở Gateway.
- Tách namespace; NetworkPolicy cho `llm-serving` là tuỳ chọn.

---

## 4. Mẫu manifest (Kustomize)

```text
serving/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml      # không có trường replicas
│   ├── service.yaml
│   ├── podmonitor.yaml
│   └── model-prefetch-job.yaml
└── overlays/
    ├── laptop/              # model 1,5B, max-model-len 4096, gpu-mem 0.85, requests nhỏ
    └── cloud/               # model 7–8B, args đầy đủ, hostPath NVMe
```

Ví dụ patch trong overlay `cloud`:

```yaml
# serving/overlays/cloud/patch-args.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm
spec:
  template:
    spec:
      containers:
        - name: vllm
          args:
            - --model=/models/Qwen2.5-7B-Instruct
            - --served-model-name=qwen2.5-7b
            - --max-model-len=8192
            - --max-num-seqs=64
            - --gpu-memory-utilization=0.90
            - --no-enable-prefix-caching
          env:
            - {name: VLLM_CACHE_ROOT, value: /cache/vllm}
          volumeMounts:
            - {name: models, mountPath: /models, readOnly: true}
            - {name: vllm-cache, mountPath: /cache/vllm}
      volumes:
        - name: models
          hostPath: {path: /mnt/nvme/models, type: Directory}
        - name: vllm-cache
          hostPath: {path: /mnt/nvme/vllm-cache, type: DirectoryOrCreate}
```

---

## 5. Luồng một request

![Hình 3 – Vòng đời request](../images/03-vong-doi-request.svg)

*Hình 3 (tài liệu chính). Vòng đời một request và các metric độ trễ.*

| Bước | Diễn ra ở đâu | Thời gian | Có trong TTFT phía client? |
|---|---|---|---|
| Gửi HTTP, TCP | Pod máy tạo tải → Traefik | < 1 ms (cùng VM, dùng keep-alive) | Có |
| Chuyển tiếp qua Gateway, kube-proxy | Traefik → Service → pod | < 1 ms | Có |
| Parse JSON, tokenize | API server (CPU) | 1–10 ms tuỳ độ dài prompt | Có |
| **Chờ trong hàng đợi** | Scheduler | 0 → **vài giây** khi quá tải | Có (**thành phần biến động mạnh nhất**) |
| Prefill | GPU | ~50–300 ms (prompt 256–1024 token) | Có |
| Detokenize, gửi chunk SSE đầu tiên | API server → client | < 5 ms | Có |
| Các bước decode tiếp theo | GPU, chung batch | ~25–80 ms mỗi token | Không (thuộc TPOT) |

Định dạng stream mà máy tạo tải nhận được:

```text
data: {"id":"…","choices":[{"delta":{"content":"Xin"}}],…}
data: {"id":"…","choices":[{"delta":{"content":" chào"}}],…}
…
data: {"id":"…","choices":[],"usage":{"prompt_tokens":512,"completion_tokens":256,…}}
data: [DONE]
```

Để nhận được phần `usage` ở cuối stream, request phải gửi kèm `"stream_options": {"include_usage": true}`. Một chunk có thể chứa nhiều token, nên phải lấy số token từ `usage` (xem [09 §3.2](09-chi-so-danh-gia.md#32-tpot-và-itl)).

---

## 6. Vòng lặp autoscaling và mô hình thời gian

![Hình 4 – Vòng lặp autoscaling](../images/04-vong-lap-autoscaling.svg)

*Hình 4 (tài liệu chính). Vòng lặp autoscaling.*

Mô hình thời gian đã hiệu chỉnh theo đúng cơ chế KEDA/HPA (xem [04 §4.3](04-kien-thuc-nen.md#43-keda)):

| Thành phần | Mặc định | Sau khi chỉnh | Cách chỉnh |
|---|---|---|---|
| Chu kỳ scrape metric vLLM | 30 s (kube-prometheus-stack) | 5 s | `PodMonitor.podMetricsEndpoints[].interval` |
| Chu kỳ thu metric DCGM | có thể 30 s | 5 s | Biến môi trường collect interval của DCGM exporter |
| Chu kỳ sync HPA (KEDA truy vấn khi HPA hỏi) | 15 s | 5 s | k3s: `--kube-controller-manager-arg=horizontal-pod-autoscaler-sync-period=5s` |
| Thời gian chạy PromQL | < 1 s | < 1 s | – |
| **Tổng độ trễ phát hiện (xấu nhất)** | **≈ 45 s** | **≈ 10 s** | – |
| Cold start | 1–8 phút | 0,5–1,5 phút (L2) | §7 |

Metric A2 và A3 là **gauge**, lấy giá trị tức thời, nên không có độ trễ do cửa sổ `rate()` hay `histogram_quantile()`. Đây là một ưu điểm nữa của metric tầng ứng dụng so với metric tính từ histogram.

---

## 7. Cold start chi tiết

![Hình 12 – Tám pha cold start](../images/12-cold-start-chi-tiet.svg)

*Hình 12. Tám pha khởi động một pod vLLM và khả năng tối ưu từng pha.*

### 7.1. Từng pha

**Pha 1. Scheduling (≈ 1–2 s).** HPA tăng `spec.replicas`, ReplicaSet tạo Pod mới ở trạng thái Pending. kube-scheduler lọc các node còn `nvidia.com/gpu` trống và đủ CPU/RAM, sau đó gán pod vào một node. **Từ thời điểm này GPU bị giữ.** Nếu hết GPU, pod nằm Pending mãi. Vì vậy `maxReplicas` phải bằng đúng số GPU có sẵn.

**Pha 2. Chuẩn bị pod (≈ 2–5 s).** Kubelet tạo sandbox, CNI cấp IP, mount volume (NFS mount qua mạng nên chậm hơn), gọi device plugin để chọn GPU cụ thể. NVIDIA toolkit đưa file thiết bị và thư viện driver vào container.

**Pha 3. Pull image (≈ 60–180 s, hoặc 0 s).** Image `vllm-openai` cỡ ~10 GB vì chứa CUDA, PyTorch và các kernel. Thời gian gồm **tải về** và **giải nén** từng layer; giải nén tốn CPU và nhiều khi chậm hơn cả tải. Nếu node đã có image và `IfNotPresent` thì mất 0 s. Kubelet ghi event dạng `Successfully pulled image … in 1m23s`.

**Pha 4. Khởi động tiến trình (≈ 5–15 s).** Chạy `vllm serve`: import `torch`/`vllm` (nặng), đọc tham số, khởi tạo CUDA context, tạo tiến trình EngineCore.

**Pha 5. Tải model (≈ 150 s, hoặc 0 s).** Chỉ xảy ra khi `--model` là tên repo trên Hugging Face và chưa có cache. Qwen2.5-7B gồm khoảng 15 GB file safetensors (4 shard); ở 100 MB/s mất khoảng 150 s.

**Pha 6. Nạp weights vào GPU (≈ 10–60 s).** Đọc file từ đĩa lên RAM, rồi copy qua PCIe vào VRAM. Tốc độ phụ thuộc chủ yếu vào ổ đĩa: NVMe cục bộ (2–3 GB/s) mất khoảng 10 s; NFS (100–300 MB/s) mất 50–150 s. Log có dòng `Loading weights took … seconds` và `Model loading took … GiB and … seconds`.

**Pha 7. Compile, KV-cache, CUDA graph (≈ 20–60 s).** Gồm ba việc nối tiếp:
- (a) Chạy thử một lượt forward để **đo bộ nhớ**. Trong lượt chạy thử đó, **torch.compile** biên dịch model; kết quả được lưu vào `$VLLM_CACHE_ROOT/torch_compile_cache`.
- (b) **Cấp phát KV-cache** bằng phần VRAM còn lại. Log: `GPU KV cache size: … tokens`.
- (c) **Capture CUDA graph** cho nhiều kích thước batch. Log: `Graph capturing finished in … secs`.

Cả pha có một dòng tổng: `init engine (profile, create kv cache, warmup model) took … seconds`. Câu chữ có thể khác theo phiên bản, nên runner cần có bộ phân tích log dễ chỉnh.

**Pha 8. Probe → Ready → Endpoints (≈ 5–10 s).** API server chỉ mở cổng 8000 sau khi engine sẵn sàng; trước đó probe bị từ chối kết nối. Probe thành công thì condition `Ready=True`, EndpointSlice thêm IP của pod, và kube-proxy/Traefik cập nhật. Với `periodSeconds: 5`, có thể mất thêm tối đa 5 s chỉ để chờ lần probe kế tiếp.

### 7.2. Tối ưu theo mức

| Pha | L0 | L1 (model trên PVC) | L2 (tối ưu đầy đủ) | Cách làm cho L2 |
|---|---|---|---|---|
| 3 Pull image | ✓ | ✓ | **0 s** | DaemonSet pre-pull, hoặc image VM đã có sẵn; `IfNotPresent` |
| 5 Tải model | ✓ | **0 s** | **0 s** | Job prefetch tải về NVMe |
| 6 Nạp weights | nhanh | chậm (đọc qua mạng) | nhanh | hostPath trên NVMe |
| 7a Compile | đầy đủ | đầy đủ | **nhanh** | `VLLM_CACHE_ROOT` trên volume bền |
| 7b–c KV, graph | ✓ | ✓ | ✓ | Không tránh được (`--enforce-eager` bỏ được graph nhưng làm ITL tăng) |
| 8 Probe | ✓ | ✓ | ✓ | Có thể giảm `periodSeconds` xuống 2 s |

DaemonSet pre-pull tối giản:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata: {name: prepull-vllm, namespace: llm-serving}
spec:
  selector: {matchLabels: {app: prepull-vllm}}
  template:
    metadata: {labels: {app: prepull-vllm}}
    spec:
      nodeSelector: {nvidia.com/gpu.present: "true"}
      initContainers:
        - name: pull
          image: vllm/vllm-openai@sha256:…     # đúng digest của Deployment
          command: ["true"]
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.9
```

### 7.3. Cạm bẫy khi đo

1. **Page cache.** Lần nạp thứ hai trên cùng node đọc weights từ RAM nên nhanh bất thường. Khi đo mức "node lạnh", chạy `sync; echo 3 > /proc/sys/vm/drop_caches` trên node trước mỗi lần đo.
2. **Chỉ pull image một lần trên một node.** Với phương án A (1 VM), chỉ pod đầu tiên phải pull. Muốn đo L0 đúng, phải `crictl rmi <image>` trước mỗi lần đo.
3. **Compile cache mất hiệu lực** khi đổi phiên bản vLLM hoặc tham số (`max-model-len`…). Sau khi đổi, lần đầu sẽ compile lại, nên cần "làm ấm" cache trước khi đo L2.
4. **Pod giữ GPU từ pha 1**, nên GPU-giờ được tính cả trong lúc cold start.

---

## 8. Scale-down và graceful shutdown

![Hình 13 – Graceful shutdown](../images/13-graceful-shutdown.svg)

*Hình 13. Không có preStop, request đến trong lúc Endpoints chưa cập nhật sẽ lỗi. Có preStop, request đó vẫn được phục vụ.*

### 8.1. Trình tự khi một pod bị xoá

1. HPA giảm `replicas`. ReplicaSet chọn pod để xoá, ưu tiên theo thứ tự: pod chưa được gán node, pod chưa Ready, rồi đến các tiêu chí khác. Có thể điều chỉnh bằng annotation `controller.kubernetes.io/pod-deletion-cost`.
2. Pod được đánh dấu **Terminating**. Kể từ đây, **hai việc chạy song song**:
   - Controller EndpointSlice gỡ pod khỏi Service. kube-proxy và Traefik nhận thay đổi sau khoảng 1–5 s.
   - Kubelet chạy **preStop** (ví dụ `sleep 20`), rồi gửi **SIGTERM**.
3. vLLM (uvicorn) nhận SIGTERM: ngừng nhận kết nối mới và làm nốt request đang chạy.
4. Nếu quá `terminationGracePeriodSeconds` (tính từ bước 2, **gồm cả thời gian preStop**) mà tiến trình chưa thoát, kubelet gửi **SIGKILL** và request dở dang bị cắt.

### 8.2. Chọn tham số

- `preStop sleep` bằng 15–20 s: lớn hơn thời gian lan truyền thay đổi Endpoints.
- `terminationGracePeriodSeconds` ≥ preStop + (thời gian chờ tối đa + thời gian sinh output dài nhất). Với output 256 token và TPOT 100 ms, riêng phần sinh đã là 26 s. Chọn 180 s để có biên an toàn.
- **Cần kiểm chứng bằng thực nghiệm** (KB4): vLLM có thực sự chờ hết các stream đang mở trước khi thoát không, và số lỗi trong cửa sổ scale-down có bằng 0 không. Nếu có lỗi, đó là một phát hiện, và là cơ sở đề xuất giải pháp như tăng thời gian preStop hoặc chủ động gỡ pod khỏi Service trước.

---

## 9. Kiến trúc giám sát

### 9.1. Thu thập

```yaml
# PodMonitor cho vLLM: scrape mỗi 5 s
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: vllm
  namespace: llm-serving
  labels: {release: kube-prometheus-stack}   # BẮT BUỘC nếu Prometheus chọn theo label release
spec:
  selector: {matchLabels: {app: vllm}}
  podMetricsEndpoints:
    - port: http
      path: /metrics
      interval: 5s
```

> **Cạm bẫy:** mặc định, `kube-prometheus-stack` chỉ nhận ServiceMonitor/PodMonitor có label `release: <tên-release>`. Có hai cách xử lý: thêm label như trên, hoặc đặt `prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false` (và tương tự cho ServiceMonitor).

Với DCGM exporter, trong values của GPU Operator:
- Bật `serviceMonitor` (interval 5 s).
- Đặt chu kỳ thu metric về 5000 ms.
- RTX 4090 là GPU GeForce: DCGM có thể không hỗ trợ đầy đủ, và **không có** metric profiling (`DCGM_FI_PROF_*`). Nếu `dcgm-exporter` không chạy, dùng `nvidia_gpu_exporter` (đọc qua `nvidia-smi`, metric kiểu `nvidia_smi_utilization_gpu_ratio`) và đổi truy vấn của A1 theo.

### 9.2. Recording rule (tính sẵn cho dashboard và autoscaling)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata: {name: vllm-rules, namespace: monitoring, labels: {release: kube-prometheus-stack}}
spec:
  groups:
    - name: vllm.rules
      interval: 5s
      rules:
        - record: llm:concurrency:sum
          expr: sum(vllm:num_requests_running{namespace="llm-serving"}) + sum(vllm:num_requests_waiting{namespace="llm-serving"})
        - record: llm:kv_usage:sum
          expr: sum(vllm:kv_cache_usage_perc{namespace="llm-serving"})
        - record: llm:ttft_p95:1m
          expr: histogram_quantile(0.95, sum by (le) (rate(vllm:time_to_first_token_seconds_bucket{namespace="llm-serving"}[1m])))
        - record: llm:gen_tokens:rate1m
          expr: sum(rate(vllm:generation_tokens_total{namespace="llm-serving"}[1m]))
```

ScaledObject **nên dùng biểu thức gốc** thay vì recording rule. Recording rule được tính theo chu kỳ riêng, nên sẽ cộng thêm một khoảng trễ vào quá trình phát hiện.

### 9.3. Dashboard

| Dashboard | Panel chính |
|---|---|
| Serving | RPS; TTFT/ITL p50 và p95; running, waiting theo từng pod; KV-cache; token/s; preemption |
| GPU | GPU_UTIL, SM_ACTIVE, DRAM_ACTIVE; VRAM; công suất; nhiệt độ và xung nhịp |
| Autoscaling | desired so với current replicas; metric so với target (vẽ `threshold × replicas`); pod theo trạng thái (Pending, ContainerCreating, Running-not-ready, Ready) |
| Thí nghiệm | Annotation các pha KB; λ(t) theo lịch so với thực tế; độ lệch lịch gửi của máy tạo tải; lỗi |

### 9.4. Lưu trữ

- Retention khoảng 15 ngày; dữ liệu mỗi lượt chạy được runner xuất riêng (xem [09](09-chi-so-danh-gia.md#7-lược-đồ-dữ-liệu)).
- Lượng series ít (4 pod, vài chục metric), nên chỉ cần khoảng 10–20 GB ổ cho Prometheus.

---

## 10. GitOps và quản lý cấu hình

### 10.1. Mô hình App-of-Apps

```text
argocd/
├── root-app.yaml            # Application trỏ vào thư mục apps/
└── apps/
    ├── gpu-operator.yaml    # Helm chart + values theo môi trường
    ├── monitoring.yaml
    ├── keda.yaml
    └── serving.yaml         # Kustomize overlay laptop|cloud
```

### 10.2. Autoscaling nằm ngoài Argo CD

Cấu hình autoscaling **thay đổi theo từng lượt chạy**, nên runner áp nó trực tiếp bằng `kubectl apply` từ thư mục `autoscaling/`. Argo CD **không quản lý** thư mục này. Nhờ vậy việc đổi cấu hình diễn ra ngay lập tức, không phải chờ Git sync.

### 10.3. Cạm bẫy: Argo CD và HPA tranh nhau `replicas`

Nếu Deployment trong Git có trường `replicas: 1` và Argo CD bật self-heal, thì mỗi khi HPA scale lên 3, Argo CD thấy trạng thái lệch với Git và **đặt lại về 1**. Kết quả là số replica dao động loạn.

Hai cách xử lý:
1. **Bỏ trường `replicas`** khỏi manifest. Nhóm khuyến nghị cách này.
2. Hoặc cấu hình Argo CD bỏ qua trường đó:

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers: [/spec/replicas]
```

---

## 11. Câu hỏi hội đồng có thể đặt ra

**Vì sao không dùng KServe cho "chuẩn"?**
KServe thêm nhiều tầng (Knative, activator, CRD riêng). Các tầng này làm khó kiểm soát biến và khó tách thời gian phản ứng thành từng thành phần. Deployment cộng KEDA là tối giản, và kết quả vẫn áp dụng được cho KServe ở chế độ raw deployment.

**Vì sao liveness probe để rộng tay như vậy?**
Khi pod rất tải, `/health` có thể trả chậm. Liveness quá gắt sẽ **kill một pod đang làm việc** ngay lúc cần nó nhất, gây thêm một lần cold start.

**Sao không cho mọi pod đọc chung model qua NFS cho gọn?**
Hoàn toàn được (mức L1), và đây là cách phổ biến trong cluster nhiều node. Nhưng nạp 15 GB qua mạng chậm hơn NVMe nhiều. Trên một máy thuê, nhóm không có ổ mạng tương đương để đo L1, nên chỉ so L0 với L2.
