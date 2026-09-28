# 6. Môi trường triển khai và dự toán chi phí: tài liệu chuyên sâu

> Thuộc [Mục 6 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#6-môi-trường-triển-khai-và-dự-toán-chi-phí) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- **Tầng 1 (laptop RTX 4060):** hướng dẫn từng bước dựng k3s có GPU, gộp nhiều laptop thành một cluster, và những lưu ý riêng cho laptop.
- **Tầng 2 (GPU thuê):** chọn loại GPU theo băng thông; checklist chọn nhà cung cấp; bài thử nghiệm 1 giờ trước khi chốt; cấu hình VM; tự động dựng và huỷ.
- **Chi phí:** công thức, bảng dự toán theo 3 mức giá (khoảng 80–300 USD), các biện pháp kiểm soát chi phí, và lịch các phiên thuê GPU.

> Các lệnh dưới đây là **khung tham khảo**. Tên gói, cờ và đường dẫn có thể thay đổi theo phiên bản, nên luôn đối chiếu với tài liệu chính thức của k3s, NVIDIA và nhà cung cấp tại thời điểm cài đặt.

---

## 1. Hai tầng, cùng một bộ manifest

![Hình 6 – Hai tầng môi trường](../images/06-moi-truong-trien-khai.svg)

*Hình 6 (tài liệu chính). Hai tầng môi trường.*

| | Tầng 1: Laptop | Tầng 2: GPU thuê |
|---|---|---|
| Mục đích | Phát triển, pilot, demo khi bảo vệ | Hiệu chỉnh, ma trận thí nghiệm, đo cold start |
| GPU | RTX 4060 Laptop 8 GB (mỗi máy 1 GPU) | 4 × GPU 24 GB |
| Model | Qwen2.5-1.5B-Instruct (hoặc 3B AWQ) | Qwen2.5-7B-Instruct |
| Chi phí | ≈ 0 (tiền điện) | Theo giờ |
| Số liệu dùng để kết luận? | **Không** (chỉ dùng để so xu hướng) | **Có** |

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
- Viết và kiểm thử ScaledObject A1–A3 (A1 cần GPU thật, hoặc giả lập metric DCGM).
- Viết dashboard và bộ export dữ liệu của runner.
- Kiểm thử máy tạo tải ở tốc độ cao mà không tốn GPU.

---

## 3. Tầng 2: GPU thuê theo giờ

### 3.1. Chọn loại GPU

| GPU | VRAM | Băng thông | Decode tối đa với 7B BF16 | Nhận xét |
|---|---|---|---|---|
| L4 | 24 GB | ~300 GB/s | ~20 token/s | Rẻ, tiết kiệm điện, **decode chậm** |
| A10 / A10G | 24 GB | ~600 GB/s | ~40 token/s | Cân bằng, phổ biến trên cloud |
| RTX A5000 | 24 GB | ~768 GB/s | ~50 token/s | Hay có ở các nhà cung cấp GPU nhỏ |
| RTX 4090 | 24 GB | ~1.008 GB/s | ~66 token/s | Nhanh, rẻ, nhưng hiếm ở dạng VM 4 GPU |
| L40S | 48 GB | ~864 GB/s | ~57 token/s | Dư VRAM; đắt hơn |
| A100 40/80 GB | 40/80 GB | 1,5–2 TB/s | 100+ token/s | Mạnh nhưng đắt; dư thừa cho 7B |

**Khuyến nghị:** A10, RTX A5000 hoặc RTX 4090, **cả 4 GPU trong cùng một VM**. Tránh trộn nhiều loại GPU trong cùng một thí nghiệm.

### 3.2. Checklist chọn nhà cung cấp

**Bắt buộc**
- [ ] Cho thuê **VM** có quyền root, systemd và nạp được kernel module (không phải chỉ container).
- [ ] Có loại VM **4 GPU** (hoặc 2 × 2 GPU cùng mạng riêng).
- [ ] Tính tiền theo giờ hoặc phút, **dừng và xoá được bất kỳ lúc nào**.
- [ ] Có ổ **NVMe cục bộ** từ 300 GB trở lên.
- [ ] Có VM CPU nhỏ **cùng region** để chạy máy tạo tải.

**Nên có**
- [ ] Có Terraform provider hoặc API/CLI để tự động hoá.
- [ ] Image có sẵn driver NVIDIA.
- [ ] Băng thông Internet tốt (tải image và model).
- [ ] Không bị thu hồi máy giữa chừng (tránh loại spot/preemptible cho phiên chạy ma trận).
- [ ] Có cảnh báo ngân sách.

**Danh sách để khảo sát** (giá và tình trạng còn máy thay đổi liên tục, cần kiểm tra lại): Lambda, TensorDock, DataCrunch, Hyperstack, Vultr; GCP (L4/A100), AWS (g5/g6), Azure; trong nước: FPT Cloud / FPT AI Factory, Viettel Cloud.

### 3.3. Bài thử nghiệm 1 giờ trước khi chốt

```bash
# 1. Phần cứng
nvidia-smi; nproc; free -g; lsblk; df -h
# 2. Quyền và kernel module
sudo whoami; lsmod | grep nvidia
# 3. Container có dùng GPU không
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi   # hoặc nerdctl/ctr
# 4. Mạng: tốc độ tải (image, model)
curl -o /dev/null -w "%{speed_download}\n" https://huggingface.co/…/model-00001-of-00004.safetensors
# 5. Cài k3s, rồi chạy thử pod nvidia-smi (như §2.4)
# 6. RTT từ VM CPU sang VM GPU
ping -c 20 <ip-noi-bo-vm-gpu>
```

Ghi kết quả vào `docs/nhat-ky/nha-cung-cap-<ten>.md` để so sánh các nhà cung cấp.

### 3.4. Cấu hình VM

| Tài nguyên | VM GPU | VM CPU (máy tạo tải + runner) |
|---|---|---|
| vCPU | ≥ 32 (4 pod × 4–6 vCPU, cộng hệ thống và Prometheus) | 4–8 |
| RAM | ≥ 128 GB (4 × 24 Gi request, cộng page cache cho weights) | 8–16 GB |
| Ổ | NVMe ≥ 300 GB: image ~20 GB, model ~15 GB, compile cache, Prometheus ~20 GB, dữ liệu | 50 GB |
| Mạng | Mạng riêng với VM CPU | Cùng region; RTT < 5 ms |

### 3.5. Tự động dựng và huỷ

```text
make up         → Terraform: tạo VM GPU + VM CPU, mạng riêng, firewall
make bootstrap  → Ansible: driver (nếu thiếu), toolkit, k3s, chrony, mount NVMe;
                  cài Argo CD và áp root-app (overlay cloud)
make prefetch   → Job tải model về NVMe, DaemonSet pre-pull image
make calibrate  → runner chạy bước hiệu chỉnh
make run MATRIX=experiments/matrix-session-1.yaml
make backup     → rclone đẩy runs/ lên object storage, kiểm tra checksum
make down       → terraform destroy (chỉ chạy sau khi backup báo OK)
```

- **Mục tiêu:** từ `make up` tới khi cluster sẵn sàng chạy thí nghiệm mất **dưới 30 phút**.
- Nếu nhà cung cấp không có Terraform provider, thay bằng script gọi CLI/API của họ. Các bước Ansible trở đi giữ nguyên.
- **Đồng bộ giờ:** cài chrony trên mọi máy, và kiểm tra độ lệch trước mỗi phiên (yêu cầu dưới 50 ms).

### 3.6. Sao lưu dữ liệu

- Runner đẩy thư mục `runs/<run-id>/` lên object storage **ngay sau mỗi lượt**, bằng `rclone copy` kèm kiểm tra checksum.
- Nếu không có object storage, dùng `rsync` về laptop qua SSH, hoặc lưu lên Google Drive qua rclone.
- `make down` kiểm tra xem mọi lượt đã được sao lưu chưa; nếu chưa thì **từ chối huỷ VM**.

---

## 4. Chi phí

### 4.1. Công thức

$$
\text{Chi phí} = \sum_{\text{phiên}} \Big( h \times (n_{\text{GPU}} \times p_{\text{GPU}} + p_{\text{VM CPU}}) \Big) + \text{lưu trữ} + \text{truyền dữ liệu ra ngoài}
$$

Trong đó h là số giờ bật máy của phiên, n_GPU là số GPU của VM, p_GPU là giá mỗi GPU-giờ, và p_VM CPU là giá mỗi giờ của VM CPU.

### 4.2. Dự toán

| Hạng mục | Giờ bật cluster (đầy đủ) | Giờ bật cluster (rút gọn) |
|---|---|---|
| Thử nhà cung cấp | 2 | 2 |
| Dựng và sửa cấu hình lần đầu | 6 | 6 |
| Hiệu chỉnh và kiểm tra C | 6 | 6 |
| Thí nghiệm cold start | 6 | 4 |
| Ma trận chính | 44 (75 lượt) | 26 (khoảng 55 lượt) |
| Chạy lại (~30% ma trận) | 13 | 8 |
| Dự phòng sửa lỗi | 7 | 4 |
| **Tổng** | **84 giờ → 336 GPU-giờ** | **56 giờ → 224 GPU-giờ** |

| Mức giá (USD/GPU-giờ) | Bản đầy đủ | Bản rút gọn |
|---|---|---|
| 0,35 (rẻ, GPU consumer) | ~118 USD | ~78 USD |
| 0,60 (trung bình) | ~202 USD | ~134 USD |
| 0,90 (đắt) | ~302 USD | ~202 USD |

Cộng thêm VM CPU (khoảng 0,05 USD/giờ × 84 giờ ≈ 4 USD) và lưu trữ (không đáng kể).

### 4.3. Kiểm soát chi phí

1. **Không phát triển trên cloud.** Mọi thứ phải chạy ổn trên laptop trước (mốc M2).
2. **Công tắc tự huỷ.** Mỗi phiên, VM tự tắt sau X giờ (`sudo shutdown -h +600`) phòng khi quên.
3. **Cảnh báo ngân sách** ở mức 50%, 80% và 100% dự toán.
4. **Chạy qua đêm không người trực.** Runner chạy trọn một khối, tự sao lưu, và gửi thông báo khi xong hoặc khi có lỗi.
5. **Huỷ ngay sau mỗi phiên.** Nếu nhà cung cấp vẫn tính tiền ổ đĩa khi VM tắt, so sánh chi phí giữ ổ với chi phí tải lại model và image (khoảng 15 phút).
6. **Tận dụng credit:** chương trình sinh viên của các cloud lớn, hoặc hỗ trợ nội bộ từ nơi làm việc.

---

## 5. Lịch các phiên thuê GPU

| Phiên | Tuần | Thời lượng | Nội dung | Điều kiện để bắt đầu |
|---|---|---|---|---|
| S0 | T7–T8 | 2 giờ | Thử 1–2 nhà cung cấp | Checklist §3.2 |
| S1 | T8 | 8 giờ | Dựng cluster bằng IaC, sửa lỗi, pilot 3 lượt | Mốc M2 đạt |
| S2 | T9 | 10 giờ | Hiệu chỉnh C, đo cold start L0/L1/L2 | S1 ổn định |
| S3 | T10 | ~15 giờ (qua đêm) | Khối 1 của ma trận (25 lượt) | C đã chốt |
| S4 | T11 | ~15 giờ | Khối 2 + KB2 × A2 ở L0/L2 | – |
| S5 | T11–T12 | ~15 giờ | Khối 3 | – |
| S6 | T12 | ~10 giờ | Chạy lại lượt hỏng, thêm lần cho các ô trọng tâm | Kết quả kiểm tra hợp lệ |

---

## 6. Checklist mỗi phiên

**Trước khi bật máy:** matrix file đã review; runner đã thử trên laptop; ngân sách còn đủ; mọi người biết lịch.

**Sau khi dựng xong:** `nvidia-smi` thấy đủ 4 GPU; `kubectl get nodes` Ready; dashboard có dữ liệu; kiểm tra nhanh C (lệch dưới 10% so với lần hiệu chỉnh); chrony lệch dưới 50 ms; RTT dưới 5 ms.

**Trước khi huỷ:** mọi lượt đã sao lưu, checksum OK; đã xuất snapshot Prometheus nếu cần; đã ghi nhật ký phiên (giờ bắt đầu và kết thúc, sự cố, chi phí thực tế).

---

## 7. Câu hỏi hội đồng có thể đặt ra

**Sao không làm luôn trên laptop cho rẻ?**
Laptop chỉ chạy được model khoảng 1,5B, GPU hay giảm xung vì nhiệt, và VRAM 8 GB không đại diện cho môi trường production. Laptop phù hợp để phát triển và demo; kết luận phải dựa trên GPU datacenter.

**Kết quả trên VM thuê có ổn định không?**
Có rủi ro (máy dùng chung). Nhóm giảm thiểu bằng cách kiểm tra nhanh C ở đầu mỗi phiên, so sánh cặp trong cùng phiên, và xáo trộn thứ tự lượt chạy (xem [08 §8](08-thiet-ke-thi-nghiem.md#8-ma-trận-thứ-tự-và-khối)).

**Hết ngân sách giữa chừng thì sao?**
Có phương án rút gọn đã tính sẵn. Thứ tự ưu tiên cắt giảm theo Must/Should/Could ở [02 §7](02-muc-tieu-cau-hoi-nghien-cuu.md#7-mức-độ-thành-công).
