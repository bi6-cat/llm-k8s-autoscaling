# ADR-001: Các lựa chọn ban đầu của dự án

- **Trạng thái:** Đã chấp nhận ngày 30/09/2026. Còn 3 điểm chờ xác nhận (xem §6).
- **Người quyết định:** Nhóm. Ngân sách và nguồn GPU do nhóm chốt; các mục còn lại theo đề xuất trong phần thảo luận ngày 30/09/2026.
- **Liên quan:** [Bản mô tả chính](../mo-ta-chi-tiet-do-an.md), [06 – Môi trường và chi phí](../chi-tiet/06-moi-truong-chi-phi.md), [12 – Kế hoạch](../chi-tiet/12-ke-hoach.md)

## 1. Bối cảnh

Trước khi triển khai, cần chốt 25 lựa chọn về hạ tầng, model, autoscaling, thí nghiệm và quy trình. Có hai ràng buộc của nhóm:
1. Thuê GPU của **bên thứ ba**, ngân sách **100–200 USD**.
2. Cấu hình vừa với giá, nhưng **số liệu đo phải ổn định**.

## 2. Quyết định

| # | Nội dung | Lựa chọn | Lý do chính |
|---|---|---|---|
| D1 | Ngân sách | **100–200 USD**; nạp trước 150 USD, giữ 50 USD dự phòng | Nhóm chốt |
| D2 | Nguồn GPU | Marketplace bên thứ ba. **Chính: Vast.ai, chế độ VM**. **Dự phòng: TensorDock** (VM KVM) | Rẻ nhất trong số các nơi có VM thật (systemd, chạy được Kubernetes); Vast.ai công khai chỉ số của từng máy nên lọc được máy ổn định |
| D3 | Cấu hình | **1 VM × 4 RTX 4090 24 GB, thuê trọn máy, on-demand**. Dự phòng: 4 × RTX 3090 hoặc 4 × RTX A5000 | Vừa ngân sách; băng thông khoảng 1 TB/s; 24 GB đủ cho model 7B |
| D4 | Laptop | 2–3 laptop RTX 4060 cài Ubuntu (dual-boot), gộp thành k3s nhiều node | Demo autoscaling thật mà không tốn tiền (**cần xác nhận số laptop**) |
| D5 | Bản phân phối K8s | k3s cho cả hai tầng | Nhẹ; chỉnh được chu kỳ sync HPA và CPU manager |
| D6 | Model | Qwen2.5-7B-Instruct (cloud), Qwen2.5-1.5B-Instruct (laptop) | Apache-2.0; KV-cache nhỏ nên nhiều request đồng thời; cùng tokenizer |
| D7 | Phiên bản vLLM | Chốt bản ổn định mới nhất ở tuần T2, ghim theo digest | Tên metric và cờ không đổi giữa chừng |
| D8 | Đường đi request | Qua Traefik (có sẵn trong k3s) | Đúng kiến trúc; độ trễ thêm vào nhỏ và đo được |
| D9 | Mức cold start đo | **L0 và L2** | Trên một máy thuê không có ổ mạng tương đương để đo L1 một cách thực tế |
| D10 | Autoscaler | KEDA (Prometheus scaler) | Đã thiết kế sẵn; minh bạch |
| D11 | Chiến lược | A1–A3, cộng **A4 chỉ chạy ở KB3**. **Không có A1′** | GPU GeForce không có metric profiling của DCGM (`SM_ACTIVE`) |
| D12 | Chu kỳ sync HPA | 5 s cho ma trận chính; 15 s trong nghiên cứu độ nhạy (KB2 × A2) | Tách rõ ảnh hưởng của metric |
| D13 | Máy tạo tải | Tự viết (Python asyncio + httpx); đối chiếu với `vllm bench serve` / GuideLLM | Open-loop, λ(t) tuỳ ý |
| D14 | Nội dung tải | Prompt tổng hợp 256–1024 token, output cố định 256 | Kiểm soát biến |
| D15 | KB5 | Hình sin; trace thật chỉ làm thêm nếu còn thời gian | Kiểm soát biến |
| D16 | Quy mô | 75 lượt + 3 lượt (A4 × KB3) = **78 lượt**; thêm 12 lượt cho các ô trọng tâm nếu còn ngân sách | Vừa ngân sách |
| D17 | SLO | TTFT p95 ≤ 2 s, TPOT ≤ 100 ms; chỉnh tối đa 1 lần sau hiệu chỉnh (ghi ADR mới) | – |
| D18 | Tự động hoá hạ tầng | Script dùng **CLI chính thức `vastai`** (thuê/huỷ) + **Ansible** (cấu hình). Không dùng Terraform | Marketplace thao tác qua CLI/API là gọn nhất; phần Ansible dùng lại được cho mọi nhà cung cấp |
| D19 | GitOps | Argo CD | Có giao diện để demo |
| D20 | Lưu dữ liệu | Cloudflare R2 (hoặc Google Drive qua rclone) | Miễn phí cho vài GB, không tính phí tải ra |
| D21 | Stack Python | Python 3.12 + uv, httpx, pandas, pyarrow, matplotlib, kubernetes client | Phổ biến |
| D22 | Repo | Private trong lúc làm; public khi nộp | – |
| D23 | Ngôn ngữ | Luận văn tiếng Việt (**cần xác nhận quy định của trường**); code, commit, comment tiếng Anh | Sơ đồ được sinh bằng code nên đổi sang nhãn tiếng Anh được nếu cần |
| D24 | Lịch | T1 bắt đầu **thứ Hai 05/10/2026**; T16 kết thúc 24/01/2027; bảo vệ dự kiến cuối tháng 01/2027 (**cần xác nhận**) | Xong trước Tết Nguyên đán (06/02/2027) |
| D25 | Mở rộng | Không cam kết; nếu xong M3 sớm thì làm E6 | – |

## 3. Thay đổi thiết kế do thuê trên marketplace

1. **Máy tạo tải chạy trên cùng VM**, không có VM CPU riêng. Máy tạo tải là một pod có **lõi CPU riêng** (kubelet `cpu-manager-policy=static`, pod QoS Guaranteed). Các pod vLLM cũng có lõi riêng, nên hai bên không tranh CPU. Cách này loại bỏ hẳn độ trễ và dao động của mạng giữa máy tạo tải và cluster.
2. **Một đợt thuê liên tục khoảng 72 giờ trên cùng một máy**, thay cho nhiều phiên rời rạc. Mỗi khối của ma trận là một đoạn liên tiếp khoảng 15 giờ. Toàn bộ dữ liệu chính vì thế đến từ **cùng một phần cứng**.
3. **Burn-in bắt buộc** (khoảng 1 giờ) trước khi chốt máy. Đạt thì chạy luôn đợt chính trên máy đó; không đạt thì huỷ và thử máy khác.
4. **Metric GPU:** dùng `dcgm-exporter`. Nếu DCGM không chạy được trên GPU GeForce, chuyển sang `nvidia_gpu_exporter` (đọc qua `nvidia-smi`). Truy vấn của A1 phải đổi theo tên metric tương ứng.

## 4. Chọn máy trên Vast.ai

### 4.1. Tiêu chí lọc

| Tiêu chí | Ngưỡng | Vì sao |
|---|---|---|
| Chế độ VM | `vms_enabled=true` | Cần systemd để chạy k3s |
| Loại thuê | **On-demand** (không dùng interruptible) | Không bị thu hồi giữa chừng |
| Số GPU | 4, và **máy có đúng 4 GPU** (thuê trọn máy) | Không chia máy với người khác, giảm nhiễu |
| Loại máy | Datacenter / đã xác minh | Ổn định hơn máy cá nhân |
| Độ tin cậy | ≥ 99% | – |
| GPU | RTX 4090 (dự phòng: 3090, A5000) | Như D3 |
| CPU | ≥ 32 vCPU (nên ≥ 48) | 4 pod vLLM × 6 lõi riêng, máy tạo tải 4 lõi, hệ thống |
| RAM | ≥ 128 GB | 4 × 24 GiB cho vLLM, cộng giám sát và page cache |
| Ổ đĩa | ≥ 300 GB, tốc độ đọc ≥ 1.000 MB/s | Image, model, dữ liệu; nạp weights nhanh |
| PCIe | Gen4 trở lên với mỗi GPU | Không bị nghẽn khi nạp weights |
| Mạng | Tải xuống ≥ 500 Mbps | Tải image và model |
| Driver/CUDA | Hỗ trợ phiên bản CUDA của image vLLM đã ghim | Chạy được vLLM |
| Giá | **≤ 0,50 USD/GPU-giờ** | Vừa ngân sách, kể cả phần dự phòng |

Ví dụ tìm bằng CLI (kiểm tra lại tên trường bằng `vastai search offers --help`):

```bash
vastai search offers \
  'num_gpus=4 gpu_name=RTX_4090 vms_enabled=true rentable=true reliability>0.99 cpu_ram>=128 disk_space>=300 inet_down>=500' \
  -o 'dph'
```

### 4.2. Burn-in (khoảng 1 giờ, làm ngay trên máy vừa thuê)

1. `nvidia-smi -q`: ghi lại PCIe gen/width, power limit, xung nhịp, driver, CUDA.
2. Ổ đĩa: `fio` đọc tuần tự, yêu cầu ≥ 1 GB/s.
3. Mạng: tải thử model Qwen2.5-7B từ Hugging Face; ghi lại tốc độ.
4. **Chạy vLLM bằng Docker lần lượt trên từng GPU** (4 lần), mỗi lần `vllm bench serve` ở cùng λ trong 5 phút. Yêu cầu TTFT p95 và token/s **chênh nhau không quá 5%** giữa 4 GPU.
5. Chạy lại bước 4 trên GPU 0 sau 30 phút. Yêu cầu **trôi không quá 5%**.
6. Khi chạy tải: nhiệt độ dưới 83 °C, và `nvidia-smi -q -d PERFORMANCE` không báo giảm xung (throttle).

Máy **đạt** thì giữ và bắt đầu đợt chính ngay. **Không đạt** thì huỷ và thử máy tiếp theo (tối đa 3 máy).

## 5. Hệ quả

**Tích cực**
- Chi phí dự kiến khoảng **105–165 USD** (xem [06 §4](../chi-tiet/06-moi-truong-chi-phi.md#4-chi-phí)), vừa ngân sách.
- Dữ liệu chính đến từ **cùng một máy**; không có độ trễ mạng giữa máy tạo tải và cluster; có burn-in trước khi chạy. Cả ba đều giúp số liệu ổn định.
- Tín dụng trả trước đóng vai trò **giới hạn chi tiêu cứng**.

**Tiêu cực và việc phải làm**
- Pipeline phải **thật ổn định trên laptop** (mốc M2) trước đợt thuê chính, vì đợt này chạy liên tục.
- Cần một lần chạy thử trên **VM 1 GPU giá rẻ** (tuần T8, khoảng 4 giờ) để kiểm tra script dựng cluster trên Vast.ai.
- Khi tín dụng về 0, nền tảng có thể dừng hoặc **xoá** instance (TensorDock ghi rõ là xoá). Phải giữ số dư dư ra và có cảnh báo.
- GPU GeForce có thể giảm xung vì nhiệt, nên phải theo dõi xung nhịp và nhiệt độ trong suốt đợt chạy.
- Kết quả gắn với GPU dòng consumer (RTX 4090). Điều này được ghi vào phần hạn chế ([03](../chi-tiet/03-pham-vi-gia-dinh.md)).

## 6. Điểm chờ xác nhận

| Điểm | Giá trị đang giả định | Ảnh hưởng nếu khác |
|---|---|---|
| Số laptop RTX 4060 cài được Ubuntu | 2–3 | Nếu chỉ có 1: demo scale bằng simulator; phần còn lại không đổi |
| Ngôn ngữ luận văn theo quy định trường | Tiếng Việt | Nếu phải viết tiếng Anh: sinh lại sơ đồ với nhãn tiếng Anh |
| Ngày bắt đầu T1 và ngày bảo vệ | 05/10/2026 và cuối tháng 01/2027 | Quy đổi lại bảng lịch trong [12](../chi-tiet/12-ke-hoach.md) |

## 7. Nguồn tham khảo

- Vast.ai – Virtual Machines: https://docs.vast.ai/guides/instances/virtual-machines
- Vast.ai – thông báo hỗ trợ VM: https://vast.ai/article/announcing-virtual-machine-rental-on-vast-ai
- Vast.ai – giá RTX 4090: https://vast.ai/pricing/gpu/RTX-4090
- TensorDock – RTX 4090 (VM KVM, 1–8 GPU, trả trước): https://www.tensordock.com/gpu-4090.html
