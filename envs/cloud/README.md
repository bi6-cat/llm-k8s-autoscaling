# Chạy trên cloud (`envs/cloud`)

Môi trường đánh giá: một VM thuê theo giờ trên Vast.ai, dựng từ máy trắng, chạy toàn bộ phép đo trong **một lần thuê liền** (phiên V2, 14–15/11/2026), sao lưu dữ liệu lên R2 sau mỗi lượt, rồi trả máy. Mọi số đo của chương 5 lấy từ đây.

| | |
|---|---|
| Máy | Vast.ai chế độ VM, **4 × RTX A4000 16 GB**, verified, ngoài Trung Quốc, ≥ 20 vCPU (ADR-006 C2) |
| Model | Qwen2.5-3B-Instruct, 1 GPU mỗi pod, tối đa 4 pod (N = 4) |
| Cài đặt | Ansible dựng k3s; `make cloud-platform` cài nền bằng helm. **Không chạy Argo CD** (VM chỉ sống ~22 giờ, ADR-006 §3.1) |
| Chi phí | ≈ 0,6 USD/giờ cả máy; phiên V0+V1 ngày 08/11 tốn ≈ 1,5 USD |

## Trong thư mục này

| Đường dẫn | Là gì |
|---|---|
| `provision/vast.sh` | Mọi thao tác với Vast: tìm, thuê, đo máy, sinh inventory, cài nền, tunnel, chạy runner, trả máy. **Chỉ nơi này phụ thuộc nhà cung cấp** |
| `provision/probe.sh` | Chạy trên VM vừa thuê: GPU, PCIe, CPU, RAM, ổ, tải Hugging Face thật, Docker Hub → quyết định giữ hay trả máy |
| `provision/install-platform.sh` | Chạy trên VM: helm cài device plugin, kube-prometheus-stack (Alertmanager → Telegram), KEDA; apply rule, cảnh báo, dashboard, GPU exporter và vLLM |
| `provision/vh5.sh` | Kịch bản VH5: bấm giờ từng bước dựng lại từ máy trắng tới API trả lời |
| `provision/llm-runner.service` | systemd chạy runner trên VM, không phụ thuộc SSH của laptop |
| `serving/` | Overlay vLLM: model 3B, 3 lõi CPU riêng mỗi pod (QoS Guaranteed), cache model trên NVMe |
| `platform/kube-prometheus-stack-values.yaml` | Values riêng của cloud: nhãn `env=cloud` để tin Telegram ghi `[cloud]` |
| `experiments/matrix-dg1.yaml` | ĐG1: quét λ với 1 replica để tìm năng lực C |
| `experiments/matrix-v2.yaml` | Ma trận 17 lượt của V2. **Bản nháp**: C và threshold để trống, điền từ kết quả ĐG1 (ADR-003); runner từ chối chạy khi còn trống |
| `experiments/matrix-v1.yaml` | Ma trận 2 lượt đã chạy ở V1 (08/11), giữ để tái lập |
| `experiments/matrix-dg1-n2.yaml`, `matrix-try-n2.yaml` | Phiên thử code 16/11 trên máy 2 GPU (N = 2): ĐG1 rút gọn và 2 lượt autoscaling. Không dùng làm số liệu đánh giá |

## Trước phiên

```bash
cp .env.example .env    # điền VAST_VM_TEMPLATE, API key Vast, khoá R2, bot Telegram (runner và Alertmanager)
make backup-check       # thử R2: không lỗi nghĩa là khoá đúng
```

## Một phiên đầy đủ

| # | Lệnh | Làm gì | Ghi chú |
|---|---|---|---|
| 1 | `make find MODE=v2` | Liệt kê offer đạt tiêu chí, rẻ nhất trước | – |
| 2 | `make rent OFFER=<id> MODE=v2` | Thuê và chờ SSH được | **Tiền tính từ đây** |
| 3 | `make probe` | Đo máy thật | Mạng, ổ hoặc CPU không đạt thì `make release`, thử máy khác (tối đa 2 máy) |
| 4 | `make bootstrap` | Ansible: k3s, GPU, tải sẵn model + image | In tổng thời gian |
| 5 | `make cloud-platform` | Cài nền và vLLM 1 replica | Bước 4 + 5 đo 08/11: 12,5 phút từ máy trắng |
| 6 | `envs/cloud/provision/vast.sh tunnel` | (terminal riêng) cổng 16443 → API server | kubeconfig `llm-cloud` |
| 7 | `make run MATRIX=envs/cloud/experiments/matrix-dg1.yaml` | ĐG1 → `capacity.json` | Ghi C, B\*, threshold vào ADR-003 và `matrix-v2.yaml`, commit, push |
| 8 | `make run MATRIX=envs/cloud/experiments/matrix-v2.yaml` | Ma trận chính | Tự sao lưu R2 và nhắn Telegram sau mỗi lượt |
| 9 | `make ops-tests S=<vh2a…vh4> MATRIX=envs/cloud/experiments/matrix-v2.yaml RATE=2 CTX=llm-cloud` | Kịch bản vận hành dưới tải | RATE ≈ 0,5 C |
| 10 | `make backup-check && make release` | Xác nhận đủ dữ liệu trên R2 rồi trả máy | `release` tự chặn nếu R2 chưa đủ |

**Máy thuê qua giao diện web** (không có API key trên máy dev, hoặc offer chỉ thuê được trên web): thay bước 1–2 bằng `make attach HOST=<ip> PORT=<cổng SSH>`, lấy từ lệnh SSH mà Vast hiển thị. Lệnh thử SSH trước rồi mới ghi `.vast/target`; ngày 16/11 có 2 trong 3 máy thuê không lên SSH, gặp vậy thì huỷ máy và thuê offer khác. Các bước 3–9 giữ nguyên. Bước 10: `make release` không huỷ được máy gắn bằng `attach`; chạy `make backup-check`, huỷ máy trên trang Vast, rồi `envs/cloud/provision/vast.sh detach`.

Bước 2–5 trên VM vừa thuê gộp lại là kịch bản **VH5**: chạy `make vh5` ngay sau `make rent` để bấm giờ chính thức (N6 ≤ 30 phút; 08/11 đo được 12,5 phút).

Runner chạy bằng systemd trên VM và lấy đúng commit đang đứng, nên **commit và push trước** khi `make run`. Mất kết nối giữa chừng thì chạy lại đúng lệnh: runner đọc `progress.json` và chạy tiếp lượt dở.

## Nếu không có máy

Không có offer 4 × A4000 sáng 14/11 thì theo thứ tự (ADR-006 C2): (a) 4 × RTX 4090 VM, khoảng 2,4–2,7 USD/giờ, vẫn trong trần ngân sách; (b) máy 2 GPU với N = 2. Tìm bằng `GPU=RTX_4090 MAX_DPH=3 make find MODE=v2`.
