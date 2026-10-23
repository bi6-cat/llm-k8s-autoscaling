# Nhật ký làm việc – Quang – Tuần 03 (19–25/10)

## 2026-10-23 – Làm bù W1: vLLM trên RTX 5060

- **Mã việc:** Q3 (chuẩn bị), rủi ro R23 · **Môi trường:** nhà (PC `zett-ubuntu-pc`, chạy bằng Docker)
- **Đã làm:**
  1. Kiểm tra PC theo `w1.md` §1–§2: RTX 5060, driver 595.99.02 bản open, compute_cap 12.0; Docker 29.1.3 có runtime `nvidia`; toolkit 1.20.1; container `nvidia/cuda:12.9.1-base` thấy GPU. Tất cả đã có sẵn, không cài gì thêm.
  2. Kéo `vllm/vllm-openai:v0.31.0-cu129` (28 phút 45 giây ở ~11 MB/s, 37,7 GB sau giải nén). Digest khớp giá trị tham chiếu trong `w1.md`. Image có `sm_120`, torch thấy `NVIDIA GeForce RTX 5060 (12, 0)`.
  3. Chạy vLLM bằng `-cu129`: chết sau 15 s.
  4. Chuyển sang `vllm/vllm-openai:v0.31.0` (bản CUDA 13 đã có sẵn trên máy dưới tag `latest`, digest trùng tag `v0.31.0` trên Docker Hub): khởi động được.
  5. Kiểm tra theo §3.4: health, `/v1/models`, streaming, metric, bucket TTFT, cờ, `vllm bench serve`.
  6. Thử `--shutdown-timeout 150` (§3.5), rồi chạy lại với `--shutdown-timeout 0` làm ca đối chứng (đồng thời đo khởi động khi đã có cache model).
- **Quyết định và lý do:** dùng `v0.31.0` (CUDA 13) cho lần thử, vì PC có driver 595 ≥ 580 và image đã có sẵn, không phải tải thêm ~30 GB. **Chưa đổi ghim trong repo**: `serving/base/kustomization.yaml` và `docs/phien-ban.md` vẫn ghi `-cu129`. Cần chọn giữa `v0.31.0` (laptop và VM phải có driver ≥ 580) và `v0.32.0-cu129` (chưa thử, chưa biết đã sửa lỗi chưa).
- **Kết quả và số đo:**
  - Khởi động lần đầu 486 s, trong đó tải và nạp model 327 s, `torch.compile` 10 s, capture CUDA graph 42 s + 38 s. Có cache model: 167 s (nạp weights 13 s, `torch.compile` 9,3 s, capture CUDA graph 42 s + 50 s, init engine 110 s).
  - `GPU KV cache size: 101,120 tokens`, `Maximum concurrency for 4,096 tokens per request: 24.69x`; KV-cache 2,7 GiB; model 2,98 GiB; VRAM 6864/8151 MiB với `--gpu-memory-utilization 0.85`.
  - Streaming: 67 dòng `data:`, usage 36 + 64 token, có `[DONE]`. Có `vllm:num_requests_running`, `vllm:num_requests_waiting`; bucket TTFT có `le="2.5"`; có cờ `--shutdown-timeout`, `--no-enable-prefix-caching`, `--api-key`.
  - `vllm bench serve` (random, input 512, output 256, `--ignore-eos`, c=8, 64 prompt): 64/64 thành công; TTFT trung bình 224 ms, p50 249 ms, p99 344 ms; TPOT p50 9,30 ms, p99 10,03 ms; output 782 tok/s (đỉnh 896). Chỉ để kiểm tra máy chạy hợp lý, không phải số liệu đánh giá.
  - Drain (`--shutdown-timeout 150`): SIGTERM khi stream 1000 token mới có 13 chunk; log `stopping engine client mode=drain timeout=150s`; stream nhận đủ 1000/1000 token, có `[DONE]` sau 8,6 s; container thoát sau 14,1 s.
  - Đối chứng (`--shutdown-timeout 0`): log `mode=abort timeout=0s`; stream cắt sau 10 chunk, không có `[DONE]`, curl exit 18.
- **Sự cố:**
  - `v0.31.0-cu129` không khởi động được: `OSError: libnvrtc.so.13: cannot open shared object file` → `Could not load .../torchcodec/libtorchcodec_image.so`. Nguyên nhân: image có `torchcodec 0.17.0` (bản build cho CUDA 13) trong khi chỉ có `libnvrtc.so.12`; vLLM import `torchcodec` ngay lúc khởi động (`vllm.multimodal.audio`). Đã kiểm chứng bằng `python3 -c 'import torchcodec.decoders'`: lỗi trên `-cu129`, chạy được trên `v0.31.0` (`torchcodec 0.17.0+cu130`). Cách xử lý: tạm dùng `v0.31.0`; chưa thử build lại image hay `v0.32.0-cu129`.
  - Ở ca đối chứng, engine bị kill ngay nhưng HTTP server dừng ở `Shutting down` và không tự thoát; Docker SIGKILL sau 160 s (exit 137). Ca drain không bị. Chưa rõ nguyên nhân, có thể do server chờ kết nối đang mở. Cần để ý ở W3: trong k8s thì `terminationGracePeriodSeconds` sẽ quyết định khi nào pod bị kill.
  - Model 1,5B trả lời câu hỏi tiếng Việt bằng tiếng Trung. Không ảnh hưởng việc đo; prompt của máy tạo tải nên dùng tiếng Anh.
- **Khác thiết kế:**
  - `w1.md` §1 và `docs/phien-ban.md` chọn `-cu129`, nhưng bản này hỏng. Thực tế chạy `v0.31.0` (CUDA 13).
  - Khi khởi động có cache, `torch.compile` vẫn mất 9,3 s và capture CUDA graph vẫn mất ~90 s, vì lệnh Docker chỉ mount `~/.cache/huggingface`, còn cache compile nằm ở `/root/.cache/vllm` không được giữ. Liên quan L2 (compile cache, Q4): manifest phải mount cả thư mục này.
  - Chưa làm phần còn lại của W1: laptop, kind + simulator, offer Vast, quota GCP.
- **Liên kết:** `docs/nhat-ky/tuan-01.md`, `docs/huong-dan/w1.md` §1–§3.
- **Dùng cho luận văn:** §4.3 (chọn image vLLM, lỗi `-cu129`); chương 5 phần cold start (486 s / 167 s và các pha); N4 graceful shutdown (bằng chứng drain và đối chứng trước khi lên k8s); LT2 (KV-cache 101.120 token trên 2,7 GiB ≈ 28 KB/token, khớp dự đoán 16/10). Nên chụp log `[shutdown] … mode=drain` và bảng kết quả `vllm bench`.

## 2026-10-23 – Chốt image vLLM `v0.31.0` (CUDA 13)

- **Mã việc:** Q3 · **Môi trường:** không
- **Đã làm:** đổi ghim image từ `v0.31.0-cu129` sang `vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3` ở `docs/phien-ban.md`; sửa yêu cầu driver thành ≥ 580 ở `w1.md`, `w2.md`, `.env.example`; thêm lỗi `libnvrtc.so.13` vào bảng lỗi của `w1.md`; sửa chữ trong hình 18; thêm một dòng vào ADR-004 §7. Điền driver 595.99.02, toolkit 1.20.1, Ubuntu 26.04.1 của PC vào `phien-ban.md`.
- **Quyết định và lý do:** chọn `v0.31.0` vì là bản duy nhất đã chạy thật trên 5060 và đã có trên PC. Bỏ `v0.32.0-cu129`: chưa thử, phải tải thêm ~30 GB trong khi ổ PC còn ~31 GB, và đổi minor version có thể đổi cờ hoặc metric đã kiểm tra.
- **Khác thiết kế:** yêu cầu driver tăng từ ≥ 575 lên ≥ 580 cho mọi máy GPU. Laptop và template VM Vast chưa kiểm tra. Ubuntu trên PC là 26.04.1 bản desktop, không phải 24.04 server như `phien-ban.md` ghi trước đây.
- **Sự cố:** chưa sửa được `serving/base/kustomization.yaml` vì file này chỉ có trên nhánh `temp/w2-scaffold`; sửa khi tách nhánh serving.
- **Liên kết:** `docs/phien-ban.md`, `docs/adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md` §7.
- **Dùng cho luận văn:** §4.3 (chọn và ghim image, vì sao ghim digest, lỗi đóng gói của image `-cu129`).

## 2026-10-23 – k3s trên PC bằng Ansible, GPU trong Kubernetes (W2 §3, §5)

- **Mã việc:** Q1 · **Môi trường:** nhà (PC `zett-ubuntu-pc`)
- **Đã làm:**
  1. Tạo nhánh `feat/ansible-k3s`, lấy `infra/ansible/` và `platform/gpu/` từ nhánh `temp/w2-scaffold`.
  2. Sửa inventory theo máy thật: PC 192.168.0.100, user `zett`, `ansible_connection: local`; tên và IP Tailscale của PC vào `k3s_tls_sans`. Tạm bỏ laptop khỏi nhóm `k3s_agent`.
  3. Chạy `ansible-playbook -i inventory/home.yaml site.yml -e argocd_enabled=false` trên PC. Lần 1 lỗi ở task "Chờ node Ready"; sửa role; lần 2 đạt; sửa tiếp để idempotent; lần 4 `changed=0`.
  4. Kiểm tra cluster bằng kubeconfig `~/.kube/llm-home.yaml`, qua IP LAN, tên MagicDNS và IP Tailscale.
  5. Cài device plugin bằng Helm (chart `nvidia-device-plugin` 0.20.1, release `nvdp`, namespace `gpu`, values `platform/gpu/device-plugin-values.yaml`); áp DaemonSet GPU exporter; chạy pod thử xin 1 GPU.
- **Quyết định và lý do:**
  - Chạy Ansible ngay trên PC thay vì từ laptop như `w2.md` §3: PC đã đủ công cụ (ansible-core 2.21.5, helm, kubectl, argocd, vastai); laptop chưa kiểm tra driver ≥ 580 và PC chưa SSH được tới máy `quangnv3-d8-u` (lỗi host key).
  - Cluster một node (PC) tới W3: chỉ cần laptop khi chạy 2 replica (KB2-mini, VH2, VH3).
  - Chưa cài Argo CD (`argocd_enabled=false`): role áp `platform/argocd/root-app-home.yaml`, mà thư mục `platform/argocd/` chưa có trên `main` (phần TR1 của Trình).
  - Device plugin cài tạm bằng Helm, cùng chart, phiên bản, values và tên release như Application `gpu-device-plugin`, để Argo CD nhận quản lý sau. Chưa áp `podmonitor.yaml` vì CRD `PodMonitor` có cùng kube-prometheus-stack (TR3).
- **Kết quả và số đo:**
  - Ansible: lần đạt đầu tiên 23 s (k3s đã cài từ lần 1; lần 1 tới chỗ lỗi mất 84 s, gồm cài k3s). Lần chạy lại: `ok=23 changed=0 failed=0`.
  - Node `zett-ubuntu-pc` `Ready`, k3s `v1.36.5+k3s1`, containerd `2.3.4-k3s1.36`, nhãn `nvidia.com/gpu.present=true`, RuntimeClass `nvidia` có. `config.yaml`: `tls-san` gồm IP LAN, `zett-ubuntu-pc`, IP Tailscale; `horizontal-pod-autoscaler-sync-period=5s`.
  - `kubectl` gọi được qua `https://192.168.0.100:6443`, `https://zett-ubuntu-pc:6443` và IP Tailscale, không lỗi chứng chỉ.
  - Pod hệ thống chạy: coredns, local-path-provisioner, metrics-server, traefik, svclb-traefik.
  - Device plugin log `Registered device plugin for 'nvidia.com/gpu' with Kubelet`; node allocatable `nvidia.com/gpu: 1` (sau ~10 s). Pod thử (`runtimeClassName: nvidia`, limit `nvidia.com/gpu: 1`) in `GPU 0: NVIDIA GeForce RTX 5060`.
  - Exporter: `nvidia_smi_memory_total_bytes` 8,55e9, `memory_used_bytes` 6,4e8, `power_draw_watts` 8,77, `temperature_gpu` 44, `utilization_gpu_ratio` 0 (máy rảnh).
  - Swap đã tắt (trước đó 4 GB, đang dùng 2,2 GB); dòng swap trong `/etc/fstab` đã comment.
- **Sự cố:**
  - Task "Chờ node Ready" lỗi `error: no matching resources found` sau 0,16 s: `kubectl wait node --all` chạy khi kubelet chưa đăng ký node nên danh sách rỗng và lỗi ngay thay vì chờ; 4 s sau node đã Ready. Sửa: thêm `until/retries: 30/delay: 5`; làm tương tự cho kiểm tra RuntimeClass.
  - Playbook không idempotent: mỗi lần chạy có 3 task `changed` (fetch kubeconfig rồi sửa tại chỗ, nên file đã sửa luôn khác file gốc và bị chép đè). Sửa: `slurp` file gốc, thay chuỗi bằng `regex_replace` trong bộ nhớ, ghi một lần bằng `copy` (mode 0600).
  - Tự sửa nhật ký: mục "Chốt image" chèn nhầm làm dòng "Dùng cho luận văn" của mục "Làm bù W1" bị đẩy xuống cuối file; đã chuyển về đúng chỗ.
- **Khác thiết kế:** Ansible chạy trên PC (không từ laptop); chưa có laptop agent; Argo CD chưa cài; device plugin và exporter tạm áp tay, chưa qua Argo CD; chưa có PodMonitor.
- **Liên kết:** `infra/ansible/inventory/home.yaml`, `infra/ansible/inventory/group_vars/home.yaml`, `infra/ansible/roles/k3s-server/tasks/main.yml`, `platform/gpu/`.
- **Dùng cho luận văn:** §4.1 (dựng cluster nhà bằng Ansible, idempotent, tls-san cho Tailscale); §4.3 (GPU trong Kubernetes: RuntimeClass, device plugin, exporter thay cho GPU Operator). Nên chụp `kubectl get nodes -o wide` và output pod thử `nvidia-smi -L`.

## 2026-10-23 – vLLM chạy trong Kubernetes ở nhà (W2 §8)

- **Mã việc:** Q3 · **Môi trường:** nhà (PC, k3s một node)
- **Đã làm:**
  1. Tạo nhánh `feat/serving` (nối sau `feat/ansible-k3s`), lấy `serving/` từ `temp/w2-scaffold`; sửa ghim image ở `serving/base/kustomization.yaml` sang `v0.31.0@sha256:c1c9f6fd…`.
  2. Xoá hai image vLLM trong Docker (`-cu129` hỏng 37,7 GB và `v0.31.0` 32,3 GB) để lấy chỗ (ổ còn 22 GB → 87 GB). Quang đồng ý trước khi xoá.
  3. Kéo image vào containerd của k3s bằng `k3s crictl pull` theo digest. Hai lần đầu k3s tự thoát (xem `docs/nhat-ky/van-hanh.md`); lần ba đặt giới hạn ghi 80 MB/s thì xong; gỡ giới hạn sau đó.
  4. Tạo namespace `llm-serving` và Secret `vllm-api-key` (khoá ngẫu nhiên 48 ký tự hex, không lưu vào Git, không in ra). Chép cache model từ W1 (`~/hf-cache`, 2,9 GB) sang hostPath `/var/lib/llm-cache/hf`.
  5. `kubectl apply -k serving/overlays/home`: pod restart 3 lần; sửa `enableServiceLinks: false`; apply lại: Ready.
  6. Kiểm tra API qua Traefik (Ingress `llm.home`), khoá API, streaming; chạy `vllm bench` hai lần.
- **Quyết định và lý do:**
  - Apply tay bằng `kubectl` thay vì Argo CD: Argo CD chưa cài (TR1). Khi Argo CD lên, app `serving` sẽ nhận quản lý các tài nguyên này.
  - Chưa áp `PodMonitor` (thiếu CRD, chờ kube-prometheus-stack của Trình); `kubectl apply -k` báo lỗi cho riêng object này, các object khác vẫn tạo.
  - Chép sẵn cache model để khỏi tải lại; vì vậy số đo khởi động dưới đây là khởi động **có cache**, không phải L0.
- **Kết quả và số đo:**
  - Pod `vllm` 1/1 Running, 0 restart sau khi sửa. Container chạy → Ready: 155 s (04:52:38 → 04:55:13 UTC); nạp weights 10,9 s; `torch.compile` 1,41 s (W1 Docker 9–10 s, nhờ cache compile nằm trên hostPath qua `VLLM_CACHE_ROOT`); capture CUDA graph 44 s + 40 s; init engine 98,9 s.
  - `GPU KV cache size: 112,160 tokens`, `Maximum concurrency: 27.38x` (Docker W1: 101.120 / 24,69x). Chưa tìm hiểu vì sao cao hơn.
  - Qua Traefik: không khoá hoặc sai khoá → 401; đúng khoá → 200; `/health` không khoá → 200; streaming 25 dòng `data:`, có `[DONE]`, usage 36 + 22 token; gọi qua IP Tailscale → 200.
  - `vllm bench` (cùng tham số W1: random 512/256, c=8, 64 prompt), hai lần: 64/64 thành công; TTFT trung bình 255 / 249 ms, p50 295 / 295 ms, p99 541 / 503 ms; TPOT p50 9,72 / 9,69 ms; output 744 / 746 tok/s. So W1 Docker: TPOT +4 %, throughput −5 % (trong ±10 %); **TTFT p50 +18 %, p99 +46–57 %** (vượt ±10 %, lặp lại ổn định nên không do làm nóng). Chưa rõ nguyên nhân.
- **Sự cố:**
  - Pod restart liên tục, log `ValueError: VLLM_PORT 'tcp://10.43.53.99:8000' appears to be a URI`: Service tên `vllm` khiến Kubernetes gắn biến kiểu Docker link `VLLM_PORT=tcp://…` vào pod, trùng tên biến cấu hình của vLLM; engine chết cuối giai đoạn khởi tạo (~2,5 phút mỗi lần). Sửa: `enableServiceLinks: false` ở `serving/base/deployment.yaml`.
  - Khi rollout bản sửa, pod mới chờ ~3 phút mới được xếp lịch: `maxSurge: 0` nên phải chờ pod cũ trả GPU, mà pod cũ đang dở khởi tạo không thoát khi nhận SIGTERM, bị kill sau đủ `terminationGracePeriodSeconds: 180`. Giống hiện tượng "không tự thoát" ở ca đối chứng W1. Cần xem ở Q5 (W3).
  - k3s tự thoát hai lần khi kéo image: ghi ở `docs/nhat-ky/van-hanh.md`.
- **Khác thiết kế:** triển khai bằng `kubectl apply` (chưa qua Argo CD); thiếu PodMonitor; thêm `enableServiceLinks: false` (thiết kế chưa có); image được kéo trước bằng `crictl` thay vì để kubelet kéo.
- **Liên kết:** `serving/base/deployment.yaml`, `serving/base/kustomization.yaml`, `docs/huong-dan/w2.md` §13, `docs/nhat-ky/van-hanh.md`.
- **Dùng cho luận văn:** §4.3 (Deployment vLLM, probe, cache trên hostPath, bẫy `VLLM_PORT`); §4.5 hoặc chương 5 cold start (155 s có cache, compile cache rút `torch.compile` từ ~10 s xuống 1,4 s); §4.9 vận hành (sự cố k3s và ổ SATA). Nên chụp output 401/200 và bảng `vllm bench` so với W1.

## 2026-10-23 – Đo ổ hệ thống của PC sau sự cố k3s

- **Mã việc:** Q1 · **Môi trường:** nhà (PC, `/dev/sda` Colorful SL500 256 GB SATA, k3s và vLLM đang chạy)
- **Đã làm:** đọc SMART (`smartctl -H -A`); đo bằng `fio` trong `/var/lib/rancher`: fsync kiểu etcd (`--fdatasync=1 --bs=2300 --size=22m`) khi ổ rảnh, ghi tuần tự 4 GB `--direct=1` cùng lúc với fsync; chạy `fstrim -v /` rồi đo lại (ghi 2 GB, fsync rảnh).
- **Kết quả và số đo:**
  - SMART `PASSED`; Reallocated, Pending, Uncorrectable, Erase fail, CRC đều 0; Power_On_Hours 6262. Ổ không hỏng.
  - fsync khi rảnh: p50 0,95 ms, p99 110 ms (sau TRIM: p99 60 ms). Khuyến nghị cho etcd/k3s: p99 < 10 ms.
  - Ghi tuần tự kéo dài: 35 MB/s (4 GB trong 116 s); sau TRIM 33 MB/s (2 GB trong 62 s).
  - fsync khi đang ghi tuần tự: p50 192 ms, p99 7,1 s, max 7,2 s. Khớp với sự cố k3s ("Slow SQL" rồi thoát).
  - `fstrim` giải phóng 47,1 GiB nhưng không cải thiện tốc độ ghi; `fstrim.timer` vẫn bật (hằng tuần).
  - k3s không restart trong lúc đo (`NRestarts=2` như trước).
- **Quyết định và lý do:** chưa đổi gì. Ổ chỉ là vấn đề khi ghi lớn kéo dài; đọc model vẫn nhanh (nạp 2,98 GiB weights trong ~11 s). Các phương án (giới hạn ghi cố định cho k3s, chuyển dữ liệu sang NVMe) chờ Quang quyết.
- **Dùng cho luận văn:** §3.6/§5 môi trường (hạn chế phần cứng nhà, vì sao số liệu chính thức đo trên máy thuê); mục "Hạn chế".
