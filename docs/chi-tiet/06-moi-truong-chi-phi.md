# 6. Môi trường triển khai và dự toán chi phí: tài liệu chuyên sâu

> Thuộc [Mục 6 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#6-môi-trường-triển-khai-và-dự-toán-chi-phí) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- **Tầng 1 (laptop RTX 4060):** hướng dẫn từng bước dựng k3s có GPU, gộp nhiều laptop thành một cluster, và những lưu ý riêng cho laptop.
- **Tầng 2 (GPU thuê):** thuê **Vast.ai chế độ VM, 4 × RTX 4090, thuê trọn máy** (dự phòng TensorDock); tiêu chí lọc máy; burn-in; phân bổ CPU riêng cho vLLM và máy tạo tải trên cùng VM; tự động thuê và huỷ.
- **Chi phí:** dự toán khoảng **60–105 USD** (trong ngân sách 100–200 USD), tín dụng trả trước làm giới hạn cứng, và **một đợt thuê liên tục khoảng 37 giờ trên cùng một máy** để số liệu ổn định.
- Phần lớn công việc vận hành (cảnh báo, runbook, rolling update, drain node) được làm và kiểm thử trên **cluster laptop**, nên không tốn tiền thuê GPU.

> Các lệnh dưới đây là **khung tham khảo**. Tên gói, cờ và đường dẫn có thể thay đổi theo phiên bản, nên luôn đối chiếu với tài liệu chính thức của k3s, NVIDIA và nhà cung cấp tại thời điểm cài đặt.

---

## 1. Hai tầng, cùng một bộ manifest

![Hình 6 – Hai tầng môi trường](../images/06-moi-truong-trien-khai.svg)

*Hình 6 (tài liệu chính). Hai tầng môi trường.*

| | Tầng 1: Laptop | Tầng 2: GPU thuê |
|---|---|---|
| Mục đích | Phát triển; kiểm thử chức năng; kịch bản vận hành (drain node, rolling update, cảnh báo); demo khi bảo vệ | Đo năng lực, đánh giá autoscaling, cold start, kịch bản vận hành trên GPU thật |
| GPU | RTX 4060 Laptop 8 GB (mỗi máy 1 GPU) | 4 × RTX 4090 24 GB (Vast.ai, chế độ VM) |
| Model | Qwen2.5-1.5B-Instruct (hoặc 3B AWQ) | Qwen2.5-7B-Instruct |
| Chi phí | ≈ 0 (tiền điện) | Theo giờ |
| Số liệu dùng trong chương đánh giá? | Chỉ kết quả đạt/không đạt của kịch bản vận hành | **Có** |

---

## 2. Tầng 1: laptop RTX 4060

### 2.1. Chuẩn bị máy

- **Hệ điều hành:** Ubuntu 22.04 hoặc 24.04, cài trực tiếp (dual-boot). WSL2 không phù hợp để dựng Kubernetes có GPU và có nhiều node.
- **Laptop có hai GPU (Optimus):** đảm bảo GPU NVIDIA đang hoạt động (`prime-select nvidia` hoặc `on-demand`), và kiểm tra bằng `nvidia-smi`.
- **Điện và nhiệt:** luôn cắm sạc, tắt chế độ ngủ, đặt ở nơi thoáng. Theo dõi nhiệt độ và xung nhịp GPU (có panel trong dashboard GPU).
- **Mạng LAN:** đặt IP cố định (giữ DHCP trên router), và mở các cổng k3s cần: 6443/tcp (API), 8472/udp (flannel VXLAN), 10250/tcp (kubelet).

### 2.2. Driver và container toolkit

```bash
# Driver NVIDIA (chọn nhánh driver được khuyến nghị cho GPU)
sudo ubuntu-drivers install
nvidia-smi                                  # phải thấy RTX 4060 và phiên bản CUDA

# NVIDIA Container Toolkit (theo hướng dẫn chính thức của NVIDIA)
sudo apt-get install -y nvidia-container-toolkit
```

### 2.3. Cài k3s

```bash
# Máy chủ (laptop 1): giảm chu kỳ sync HPA xuống 5 s để phát hiện tải nhanh hơn
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.xx.y+k3s1 sh -s - server \
  --kube-controller-manager-arg=horizontal-pod-autoscaler-sync-period=5s \
  --write-kubeconfig-mode=644

sudo cat /var/lib/rancher/k3s/server/node-token     # token để máy khác join

# Máy agent (laptop 2, 3)
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.xx.y+k3s1 \
  K3S_URL=https://<ip-laptop-1>:6443 K3S_TOKEN=<token> sh -
```

Khi có sẵn NVIDIA container toolkit, k3s thường tự phát hiện `nvidia-container-runtime` và tạo RuntimeClass `nvidia`. Kiểm tra bằng `kubectl get runtimeclass`.

### 2.4. Cho Kubernetes thấy GPU

Hai cách, chọn một:
- **GPU Operator** với `driver.enabled=false` (driver đã cài sẵn). Nếu dùng toolkit của Operator, phải trỏ tới containerd của k3s (config và socket nằm dưới `/var/lib/rancher/k3s/…` và `/run/k3s/containerd/…`) theo hướng dẫn "GPU Operator với k3s".
- **Chỉ cài NVIDIA device plugin** (Helm) với `runtimeClassName: nvidia`, rồi cài riêng DCGM exporter. Cách này gọn hơn cho laptop.

Kiểm tra:

```bash
kubectl describe node <laptop> | grep -A2 "nvidia.com/gpu"    # Capacity: nvidia.com/gpu: 1
kubectl run gpu-test --rm -it --restart=Never \
  --image=nvidia/cuda:12.4.1-base-ubuntu22.04 \
  --overrides='{"spec":{"runtimeClassName":"nvidia","containers":[{"name":"t","image":"nvidia/cuda:12.4.1-base-ubuntu22.04","command":["nvidia-smi"],"resources":{"limits":{"nvidia.com/gpu":1}}}]}}'
```

GPU dòng consumer (RTX) không nằm trong danh sách hỗ trợ chính thức của GPU Operator, nhưng thường vẫn chạy được. Metric profiling (`DCGM_FI_PROF_*`) có thể không có trên laptop.

### 2.5. vLLM trên 8 GB VRAM

Overlay `laptop` gợi ý:
- `--model Qwen/Qwen2.5-1.5B-Instruct` (khoảng 3 GB), `--max-model-len 4096`, `--gpu-memory-utilization 0.85`, `--max-num-seqs 32`.
- Nếu thiếu VRAM: dùng model lượng tử hoá AWQ, hoặc thêm `--enforce-eager` (bỏ CUDA graph để tiết kiệm bộ nhớ).
- `requests.cpu: 2`, `memory: 8Gi`.

### 2.6. Không có GPU vẫn phát triển được

`llm-d-inference-sim` giả lập API và metric của vLLM, cho phép cấu hình TTFT và ITL giả. Công cụ này chạy được trên cluster `kind` hoặc k3s không có GPU. Dùng nó để:
- Viết và kiểm thử ScaledObject A1, A2 (A1 cần GPU thật, hoặc giả lập metric DCGM).
- Viết dashboard, quy tắc cảnh báo và runner đánh giá.
- Kiểm thử máy tạo tải ở tốc độ cao mà không tốn GPU.

---

## 3. Tầng 2: GPU thuê trên marketplace

> Lựa chọn đã chốt: [ADR-001](../adr/001-cac-lua-chon-ban-dau.md). Thuê **Vast.ai ở chế độ VM**, **4 × RTX 4090, thuê trọn máy, on-demand**. Dự phòng là TensorDock. Ngân sách 100–200 USD.

### 3.1. Chọn loại GPU

| GPU | VRAM | Băng thông | Decode tối đa với 7B BF16 | Nhận xét |
|---|---|---|---|---|
| **RTX 4090** | 24 GB | ~1.008 GB/s | ~66 token/s | **Lựa chọn chính**: nhanh; khoảng 0,3–0,55 USD/GPU-giờ trên marketplace |
| RTX 3090 | 24 GB | ~936 GB/s | ~61 token/s | Dự phòng rẻ hơn; Ampere, có BF16 |
| RTX A5000 | 24 GB | ~768 GB/s | ~50 token/s | Dự phòng; card workstation, nhiệt độ và xung nhịp ổn định hơn |
| A10 / L4 | 24 GB | 600 / 300 GB/s | ~40 / ~20 token/s | Chủ yếu có trên hyperscaler, giá vượt ngân sách |
| A100 / H100 | 40–80 GB | 1,5–3,3 TB/s | 100+ token/s | Dư thừa cho 7B, đắt |

**Hệ quả của việc dùng GPU GeForce:**
- Không có metric profiling của DCGM (`DCGM_FI_PROF_*`), nên bỏ A1′.
- DCGM có thể không hỗ trợ đầy đủ. Nếu vậy, chuyển sang `nvidia_gpu_exporter` (đọc qua `nvidia-smi`).
- Kết luận định lượng gắn với GPU consumer. Điều này được ghi vào phần hạn chế.

### 3.2. Chọn nền tảng

| Nền tảng | Chạy được K8s? | Ưu | Nhược |
|---|---|---|---|
| **Vast.ai, chế độ VM** | **Có**: VM KVM, có systemd | Rẻ; nhiều máy; **hiển thị chỉ số từng máy** (độ tin cậy, tốc độ ổ, PCIe, mạng) để lọc | Ít máy hỗ trợ VM hơn máy container; khởi tạo chậm hơn; chỉ truy cập qua SSH |
| Vast.ai, chế độ container (mặc định) | **Không**: không có systemd, không chạy container lồng được | Rẻ, nhiều máy | Chỉ dùng để thử vLLM đơn lẻ |
| **TensorDock** | **Có**: VM KVM, root, GPU passthrough riêng | Máy chủ EPYC, NVMe; 1–8 GPU/VM; khoảng 0,37 USD/GPU-giờ | Máy 4 × 4090 thường khan hiếm; **hết tiền thì VM bị xoá** |
| RunPod Pods | Không (container) | Dễ dùng | Không phù hợp |
| Hyperscaler (AWS, GCP) | Có | Rất ổn định | 4 GPU cỡ 4–6 USD/giờ, vượt ngân sách; phải xin quota |

**Lý do chọn Vast.ai làm chính:** marketplace lớn nên dễ tìm được máy 4 GPU hỗ trợ VM, và **chỉ số công khai của từng máy** cho phép lọc máy ổn định trước khi thuê. TensorDock làm dự phòng.

### 3.3. Tiêu chí lọc máy

Bảng đầy đủ nằm ở [ADR-001 §4.1](../adr/001-cac-lua-chon-ban-dau.md#41-tiêu-chí-lọc). Tóm tắt: `vms_enabled=true`; on-demand; **máy có đúng 4 GPU và thuê cả 4**; máy datacenter đã xác minh; độ tin cậy ≥ 99%; ≥ 32 vCPU (nên ≥ 48); RAM ≥ 128 GB; ổ ≥ 300 GB, đọc ≥ 1 GB/s; PCIe Gen4; mạng ≥ 500 Mbps; **≤ 0,50 USD/GPU-giờ**.

```bash
pip install vastai && vastai set api-key <KEY>
vastai search offers \
  'num_gpus=4 gpu_name=RTX_4090 vms_enabled=true rentable=true reliability>0.99 cpu_ram>=128 disk_space>=300 inet_down>=500' \
  -o 'dph'                     # kiểm tra tên trường bằng: vastai search offers --help
```

**Vì sao thuê trọn máy:** không ai khác dùng chung CPU, RAM, PCIe hay ổ đĩa của máy. Đây là nguồn nhiễu lớn nhất trên marketplace.

### 3.4. Burn-in trước khi chốt máy

Làm ngay sau khi thuê, mất khoảng 1 giờ. **Đạt thì giữ máy và chạy luôn đợt chính.**

```bash
nvidia-smi -q | grep -iE "product name|link|power limit|clocks|driver|cuda"   # ghi vào burnin.json
fio --name=seqread --rw=read --bs=1M --size=8G --filename=/data/fio.tmp --direct=1   # yêu cầu ≥ 1 GB/s
# Chạy vLLM bằng Docker trên từng GPU, mỗi GPU 5 phút ở cùng λ:
for g in 0 1 2 3; do
  docker run --rm --gpus "device=$g" … vllm/vllm-openai@sha256:… --model /models/Qwen2.5-7B-Instruct &
  vllm bench serve … --request-rate 1.5 --num-prompts 450   # ghi TTFT p95, token/s
done
nvidia-smi -q -d PERFORMANCE,TEMPERATURE    # không có lý do throttle; nhiệt < 83 °C
```

| Kiểm tra | Ngưỡng đạt |
|---|---|
| Chênh lệch TTFT p95 và token/s giữa 4 GPU | ≤ 5% |
| Trôi sau 30 phút (chạy lại GPU 0) | ≤ 5% |
| Tốc độ đọc ổ | ≥ 1 GB/s |
| Throttle / nhiệt độ | Không có / < 83 °C |
| PCIe | Gen4 trở lên, đúng độ rộng khe cắm (thường x16) |

**Không đạt** thì huỷ ngay (mất khoảng 1 giờ tiền thuê) và thử máy tiếp theo, tối đa 3 máy.

### 3.5. Cấu hình k3s và phân bổ CPU trên VM thuê

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.xx.y+k3s1 sh -s - server \
  --kube-controller-manager-arg=horizontal-pod-autoscaler-sync-period=5s \
  --kubelet-arg=cpu-manager-policy=static \
  --kubelet-arg=reserved-cpus=0-3 \
  --write-kubeconfig-mode=644
```

Với `cpu-manager-policy=static`, pod có QoS **Guaranteed** (requests = limits, CPU là số nguyên) được cấp **lõi CPU riêng**, không bị pod khác chen vào. Ví dụ với máy 48 vCPU:

| Nhóm | Lõi CPU | Ghi chú |
|---|---|---|
| Hệ thống, k3s (`reserved-cpus`) | 0–3 | Không cấp riêng cho pod nào |
| 4 pod vLLM | 4 × 6 lõi riêng | `requests = limits: cpu 6, memory 24Gi, nvidia.com/gpu 1` |
| Pod máy tạo tải | 4 lõi riêng | `cpu 4, memory 4Gi` |
| Các pod còn lại (Prometheus, Grafana, KEDA, Argo CD, Traefik) | Vùng CPU dùng chung | Không đòi lõi riêng |

Nếu máy chỉ có 32 vCPU: dùng 5 lõi cho mỗi pod vLLM và 3 lõi cho máy tạo tải.

### 3.6. Máy tạo tải chạy cùng VM

- Trên marketplace khó thuê được một máy CPU riêng nằm cùng datacenter. Nhóm vì thế đặt máy tạo tải **trong chính cluster**, dưới dạng pod Guaranteed có lõi riêng, và gửi request qua Traefik. Độ trễ mạng gần như bằng 0 và không dao động.
- **Kiểm chứng trong mỗi lượt:**
  - CPU của pod máy tạo tải < 70%, và **không bị giới hạn CPU** (đọc `nr_throttled` trong `cpu.stat` của cgroup).
  - Độ lệch lịch gửi p99 < 50 ms.
- Runner đánh giá chạy trên host (ngoài cluster), dùng `kubectl` và API của Prometheus. Runner tốn rất ít CPU.

### 3.7. Tự động hoá thuê và huỷ

```text
make find                → vastai search offers (tiêu chí §3.3), in ra 5 máy rẻ nhất
make rent OFFER=<id>     → vastai create instance (template VM Ubuntu 22.04), chờ SSH, ghi instance id
make burnin              → Ansible chạy các bước §3.4, xuất burnin.json; không đạt thì dừng
make bootstrap           → Ansible: chrony, NVMe, k3s (tham số §3.5), GPU (device plugin/Operator), Argo CD, root-app
                           (in ra thời gian từng bước; dùng cho kịch bản VH5)
make prefetch            → Job tải model, DaemonSet pre-pull image
make capacity            → đo năng lực một replica, sinh capacity.json
make run MATRIX=…        → chạy ma trận đánh giá autoscaling
make ops-tests           → chạy các kịch bản vận hành tự động hoá được (VH2–VH4, VH6)
make backup              → rclone lên R2, kiểm tra checksum
make release             → huỷ instance (từ chối chạy nếu backup chưa xong)
```

- Chỉ phần `find/rent/release` phụ thuộc Vast.ai. Muốn chuyển sang TensorDock thì chỉ viết lại ba lệnh này bằng API của họ; toàn bộ Ansible trở đi giữ nguyên.
- **Đồng bộ giờ:** tất cả chạy trên cùng một máy nên không lo lệch đồng hồ. Vẫn cài chrony để timestamp đúng giờ UTC.

### 3.8. Sao lưu dữ liệu

- Runner đẩy `runs/<run-id>/` lên **Cloudflare R2** ngay sau mỗi lượt (`rclone copy` kèm checksum). Nếu không dùng R2 thì dùng Google Drive qua rclone.
- `make release` kiểm tra xem mọi lượt đã được sao lưu chưa; nếu chưa thì **từ chối huỷ instance**.

---

## 4. Chi phí

### 4.1. Công thức

$$
\text{Chi phí} = \sum_{\text{đợt}} h \times n_{\text{GPU}} \times p_{\text{GPU}} \;+\; \text{lưu trữ (GB × thời gian)} \;+\; \text{băng thông tải về}
$$

Trên Vast.ai, giá hiển thị cho mỗi máy thường đã gồm CPU và RAM. **Ổ đĩa tính tiền riêng**, kể cả khi instance đang dừng. Một số máy tính thêm phí băng thông (với khoảng 50 GB image và model thì không đáng kể).

### 4.2. Dự toán

| Hạng mục | Tuần | Số giờ | Số GPU | GPU-giờ |
|---|---|---|---|---|
| Chạy thử script trên VM 1 GPU giá rẻ | T8 | 4 | 1 | 4 |
| Máy ứng viên trượt burn-in (tối đa 2) | T9 | 2 | 4 | 8 |
| Đợt chính: burn-in, dựng từ máy trắng (đo thời gian cho VH5), prefetch | T9 | 4 | 4 | 16 |
| Đo năng lực, chốt SLO và threshold | T9 | 4 | 4 | 16 |
| Cold start L0/L2 (3 lần mỗi mức) và KB2 × A2 ở L0 (2 lượt) | T9 | 3 | 4 | 12 |
| Ma trận autoscaling (28 lượt × ~35 phút) | T9 | 17 | 4 | 68 |
| Kịch bản vận hành trên GPU thật (rolling update, xoá pod, mất Prometheus, cảnh báo) | T9 | 4 | 4 | 16 |
| Chạy lại lượt hỏng, sao lưu, huỷ máy | T9 | 5 | 4 | 20 |
| **Cộng (theo kế hoạch)** | | **43** | | **≈ 160** |
| Đợt dự phòng: lượt bổ sung hoặc làm lại (chỉ khi cần) | T11 | ≤ 8 | 4 | ≤ 32 |

| Giá RTX 4090 (USD/GPU-giờ) | Theo kế hoạch | Kể cả đợt dự phòng |
|---|---|---|
| 0,35 | ~56 USD | ~67 USD |
| 0,45 | ~72 USD | ~86 USD |
| 0,50 (mức trần khi lọc máy) | ~80 USD | ~96 USD |

Cộng thêm ổ đĩa và băng thông khoảng 5–10 USD, **tổng khoảng 60–105 USD**, chỉ bằng khoảng một nửa dự toán của bản mô tả 1.0 (105–170 USD). Phần tiết kiệm đến từ việc ma trận đánh giá nhỏ hơn (28 lượt thay vì 78) và các kịch bản vận hành chủ yếu chạy trên laptop. Nếu dùng RTX 3090 (thường rẻ hơn khoảng một nửa), chi phí chỉ còn khoảng 35–55 USD.

### 4.3. Kiểm soát chi phí

1. **Tín dụng trả trước là giới hạn cứng.** Nạp trước 100 USD; chỉ nạp thêm khi thật cần, tổng không quá 150 USD.
2. **Không để số dư về 0.** Khi hết tiền, instance có thể bị dừng hoặc **xoá** (TensorDock ghi rõ là xoá). Runner kiểm tra số dư mỗi giờ (`vastai show user`) và báo động khi còn dưới 30 USD.
3. **Không phát triển trên máy thuê.** Mọi thứ phải chạy ổn trên laptop (mốc M2) và qua lần chạy thử 1 GPU.
4. **Huỷ ngay khi xong đợt.** Không để instance ở trạng thái dừng lâu ngày, vì ổ đĩa vẫn tính tiền và khi bật lại chưa chắc GPU còn trống.
5. **Báo động tự động:** runner gửi thông báo (webhook Telegram/Discord) khi xong mỗi nhóm lượt, khi có lượt không hợp lệ, hoặc khi số dư thấp.

---

## 5. Lịch sử dụng GPU thuê

| Đợt | Tuần | Thời lượng | Nội dung | Điều kiện bắt đầu |
|---|---|---|---|---|
| Chạy thử | T8 | ~4 giờ, 1 GPU | Kiểm tra `make rent/bootstrap` trên VM của Vast.ai, GPU trong k3s, Argo CD, cảnh báo, runner chạy 1 lượt | Nền tảng trên laptop gần đạt M2 |
| **Đợt chính** | T9 (ví dụ thứ Sáu 04/12 đến thứ Bảy 05/12/2026) | ~37 giờ **liên tục, trên cùng một máy** | Burn-in → dựng từ máy trắng → đo năng lực → cold start → ma trận → kịch bản vận hành → chạy lại → sao lưu → huỷ | M2 đạt; file ma trận đã review; số dư ≥ 100 USD; webhook đã thử |
| Dự phòng | T11 | ≤ 8 giờ | Lượt bổ sung, hoặc làm lại nếu đợt chính hỏng | Chỉ khi cần |

Tiến trình trong đợt chính (tính theo giờ kể từ lúc thuê):

```text
0–1    burn-in (đạt → tiếp tục)                 │ 11–28  ma trận autoscaling: 28 lượt, thứ tự xáo trộn
1–4    bootstrap từ máy trắng (đo VH5), prefetch │ 28–32  kịch bản vận hành: VH2 rolling update, VH3 xoá pod,
4–8    đo năng lực → chốt C, SLO, threshold      │        VH4 mất Prometheus, VH6 kiểm tra cảnh báo
       (cả nhóm online, ghi ADR-003)            │ 32–36  chạy lại lượt hỏng
8–11   cold start L0/L2; KB2 × A2 ở L0           │ 36–37  sao lưu, kiểm tra, huỷ instance
```

- **Giữa đợt** (khoảng giờ 20), runner tự chạy lại một mức tải 3 phút để kiểm tra năng lực không bị trôi. Nếu lệch hơn 10%, runner tạm dừng và báo động.
- **Chia ca theo dõi:** Trình và Quang thay phiên xem cảnh báo. Runner tự chạy; con người chỉ can thiệp khi có báo động. Đây cũng là dịp chạy thử chính quy trình trực và runbook của nền tảng.

---

## 6. Checklist

**Trước khi thuê:** M2 đạt; đã chạy thử trên VM 1 GPU; file ma trận đánh giá đã review; số dư ≥ 100 USD; webhook báo động hoạt động; lịch trực đã thống nhất.

**Sau burn-in:** `burnin.json` đạt mọi ngưỡng; ghi mã máy, GPU, CPU, RAM, PCIe và driver vào `metadata.json`.

**Trước khi huỷ:** mọi lượt đã sao lưu, checksum khớp; đã xuất snapshot Prometheus nếu cần; đã ghi nhật ký đợt (giờ bắt đầu và kết thúc, sự cố, chi phí thực tế).

---

## 7. Câu hỏi hội đồng có thể đặt ra

**Sao không làm luôn trên laptop cho rẻ?**
Laptop chỉ chạy được model khoảng 1,5B, GPU hay giảm xung vì nhiệt, và VRAM 8 GB không đại diện cho môi trường production. Laptop phù hợp để phát triển, kiểm thử các kịch bản vận hành và demo. Số liệu hiệu năng phải đo trên GPU 24 GB.

**Marketplace như Vast.ai có đủ tin cậy cho việc đánh giá không?**
Có, với năm biện pháp:
1. Chỉ thuê máy chế độ VM, datacenter, độ tin cậy ≥ 99%, và **thuê trọn máy** (không chia với ai).
2. **Burn-in** trước khi chốt: 4 GPU chênh nhau ≤ 5%, trôi ≤ 5%.
3. **Toàn bộ dữ liệu chính từ một đợt liên tục trên cùng một máy.**
4. Máy tạo tải nằm cùng VM với lõi CPU riêng, nên không có nhiễu mạng.
5. Xáo trộn thứ tự các lượt, và chạy lại nhanh một mức tải giữa đợt để chắc năng lực không bị trôi (xem [03 §5](03-pham-vi-gia-dinh.md#5-điều-kiện-để-so-sánh-công-bằng)).

**Vì sao dùng RTX 4090 mà không dùng GPU datacenter?**
Vì ngân sách. RTX 4090 có 24 GB VRAM và băng thông khoảng 1 TB/s, đủ để phục vụ model 7B một cách thực tế. Các cơ chế mà đồ án xử lý (metric bão hoà, cold start, scale-down, cập nhật khi hết GPU) không phụ thuộc dòng GPU. Kết luận định lượng gắn với RTX 4090 được ghi vào phần hạn chế.

**Hết ngân sách giữa chừng thì sao?**
Dự toán mới chỉ dùng khoảng một nửa ngân sách, nên khả năng này thấp. Nếu vẫn xảy ra, cắt giảm theo thứ tự Must/Should/Could ở [02 §9](02-muc-tieu-yeu-cau.md#9-mức-độ-thành-công).
