# Nhật ký vận hành

Mỗi kịch bản VH, mỗi sự cố thật và mỗi phiên thuê có một mục: ngày, môi trường, các bước, số đo, runbook đã dùng, chi phí, bài học ([Kế hoạch §10.6](../chi-tiet/06-ke-hoach-quan-ly.md#106-dữ-liệu-đánh-giá-và-nhật-ký-vận-hành)).

## 2026-10-23 – Sự cố: k3s tự thoát khi kéo image vLLM

- **Môi trường:** nhà, PC `zett-ubuntu-pc` (k3s server một node, `v1.36.5+k3s1`, datastore SQLite). Người xử lý: Quang.
- **Triệu chứng:** `k3s crictl pull` image `vllm/vllm-openai:v0.31.0` (~11 GB nén, ~32 GB giải nén) đứt với `error reading from server: EOF`; socket containerd `connection refused`. Hai lần: 11:25:09 (sau 20 phút kéo) và 11:35:52 (sau ~10 phút).
- **Nguyên nhân:** log k3s báo liên tục `Slow SQL` (79 lần trong lần thứ hai), rồi `level=fatal msg="Transaction commit failed: sql: transaction has already been committed or rolled back"` → tiến trình k3s thoát (exit 1), containerd chạy trong k3s nên việc kéo image chết theo. Ổ hệ thống là SSD SATA Colorful SL500 256 GB (`/dev/sda`); giải nén image ghi dồn dập làm ổ nghẽn, SQLite của k3s trên cùng ổ commit không kịp. Không phải thiếu RAM (dmesg không có OOM).
- **Xử lý:** systemd tự khởi động lại k3s mỗi lần (node Ready lại sau < 30 s). Đặt tạm giới hạn ghi cho k3s: `systemctl set-property --runtime k3s.service IOWriteBandwidthMax="/dev/sda 80M"`, kéo lại: xong sau 2 phút 34 giây, 29 lần `Slow SQL` nhưng không `fatal`. Gỡ giới hạn: xoá drop-in trong `/run/systemd/system.control/k3s.service.d/` và ghi `8:0 wbps=max` vào `/sys/fs/cgroup/system.slice/k3s.service/io.max` (chỉ `daemon-reload` thì giới hạn vẫn còn trong cgroup).
- **Số đo:** `NRestarts=2`; tổng thời gian kéo khoảng 33 phút qua ba lần (các lớp đã tải được giữ lại giữa các lần).
- **Runbook đã dùng:** chưa có runbook cho tình huống này.
- **Bài học:** ổ hệ thống của PC là điểm yếu: mọi đợt ghi lớn (kéo image, ghi cache model) có thể làm control-plane chết. Khi kéo image lớn lên node server, giới hạn ghi trước. Hướng lâu dài (chưa quyết): đưa `/var/lib/rancher` hoặc cache model sang NVMe (hiện chứa Windows và phân vùng dữ liệu NTFS), hoặc dùng datastore khác cho k3s. Liên quan rủi ro ở VH5 (dựng lại) và cold start L0 (kéo image trên máy mới).

## 2026-11-02 – Sự cố: k3s crash liên tục sau khi IP LAN của PC đổi

- **Môi trường:** nhà, PC `zett-ubuntu-pc` (k3s server một node, `v1.36.5+k3s1`). Xử lý từ xa qua Tailscale + SSH. Người xử lý: Quang.
- **Triệu chứng:** máy dev gọi cổng 6443 qua Tailscale bị `connection refused`; trên PC, `systemctl show k3s` báo `NRestarts=1087` sau 4 giờ máy chạy; kubectl không kết nối được.
- **Nguyên nhân:** router đổi dải mạng nhà, PC nhận IP DHCP mới `192.168.10.42` thay cho `192.168.0.100`. `/etc/rancher/k3s/config.yaml` (Ansible sinh) vẫn ghim `node-ip: 192.168.0.100`; k3s báo `failed to start networking: unable to initialize network policy controller: error getting node subnet: failed to find interface with specified node ip` rồi tự tắt. Sau khi sửa `node-ip`, lỗi vẫn còn vì đối tượng Node trong datastore giữ IP cũ và bộ điều khiển NetworkPolicy đọc IP từ đó.
- **Xử lý:** sửa `ansible_host` trong inventory, chạy lại playbook (`-e argocd_enabled=false`). Tạm thêm `disable-network-policy: true` qua `/etc/rancher/k3s/config.yaml.d/`, restart để Node nhận IP mới, xoá file tạm, restart lại. Xoá các pod kẹt (CoreDNS, Traefik, metrics-server, local-path-provisioner, vLLM) để Deployment tạo lại.
- **Số đo:** sau khi sửa, `NRestarts=0` sau 60 s; node `Ready` với `INTERNAL-IP 192.168.10.42`; vLLM `/v1/models` và một lần chat HTTP 200. Không đo tổng thời gian gián đoạn (không biết IP đổi lúc nào).
- **Runbook đã dùng:** chưa có runbook cho tình huống này.
- **Bài học:** cluster nhà phụ thuộc IP LAN do DHCP cấp; phải đặt DHCP reservation trên router (việc cần có mặt ở nhà). Đổi `node-ip` trên node đã đăng ký thì ngoài sửa cấu hình còn phải gỡ kẹt NetworkPolicy một lần. Nên viết runbook "node đổi IP" cho cả cluster nhà và VM thuê.
- **Theo dõi (cùng ngày):** PC ở chung cư, không đặt reservation được, nên chuyển k3s nhà sang IP Tailscale (`node-ip`, `flannel-iface: tailscale0`, k3s chờ `tailscaled`); node `INTERNAL-IP 100.73.95.48`, MTU pod 1230. Chi tiết ở nhật ký tuần 05 của Quang. Chưa thử khởi động lại PC.

## 2026-11-05 – Sự cố: k3s nhà tự khởi động lại, pod vLLM bị thay (chưa rõ nguyên nhân)

- **Phát hiện:** lúc khoảng 02:20 ngày 05/11, khi chuẩn bị đo, thấy pod vLLM cũ `Completed` và một pod mới `Running` được 53 phút (tạo khoảng 01:25).
- **Bằng chứng (event Kubernetes):** cùng thời điểm có `ApplyingManifest addon/traefik`, `NodePasswordValidationComplete`, CoreDNS và metrics-server báo readiness lỗi, device plugin `Started` → k3s server đã khởi động lại. Pod cũ bị `UnexpectedAdmissionError: Allocate failed due to no healthy devices present` (kubelet khởi động lại kiểm lại pod trước khi device plugin đăng ký GPU), Deployment tạo pod thay thế; pod mới chạy bình thường sau ~2 phút (startup probe).
- **Node:** không chuyển `NotReady` (`lastTransitionTime` vẫn 23/10), tức là k3s khởi động lại nhanh, không phải mất điện lâu.
- **Chưa làm:** chưa đọc `journalctl -u k3s` vì máy dev chưa có host key SSH của IP Tailscale của PC (không tự chấp nhận host key lạ). Cần Quang kiểm khi có mặt: `journalctl -u k3s --since "2026-11-05 01:00"`, `systemctl show k3s -p NRestarts`.
- **Ảnh hưởng:** không mất dữ liệu đo (lúc đó chưa đo). Cho thấy nếu k3s khởi động lại giữa phiên đánh giá thì pod vLLM bị thay và phải cold start lại; runner cần phát hiện (pod đổi tên giữa lượt) và đánh dấu lượt không hợp lệ.

## Kiểm chứng lý thuyết LT1–LT4 (Quang, Q8)

Theo mẫu ở [Môi trường §19](../chi-tiet/05-moi-truong-danh-gia.md#19-kiểm-chứng-lý-thuyết-lt1lt8): lý thuyết → dự đoán (tính trước khi đo) → số đo → lệch → giải thích. Thông số model lấy từ `config.json` của `Qwen/Qwen2.5-1.5B-Instruct@989aa798…` (đúng revision đã ghim): 28 lớp, hidden 1536, 12 attention head, **2 KV head**, head_dim 1536 ÷ 12 = 128, BF16 (2 byte), `tie_word_embeddings: true`.

### LT2 – Dung lượng KV-cache (cập nhật 29/10 và 05/11/2026)

- **Lý thuyết** ([Kiến thức nền §1.3–§1.4](../chi-tiet/02-kien-thuc-nen.md#13-kv-cache)): mỗi token lưu một vector K và một vector V ở mỗi lớp, cho mỗi KV head → byte/token = 2 (K, V) × số lớp × số KV head × head_dim × số byte mỗi phần tử.
- **Dự đoán:** 2 × 28 × 2 × 128 × 2 B = **28.672 B/token** (28 KiB). Với `--max-model-len=4096`, một request đầy cần 4096 × 28 KiB = 112 MiB, nên số request đồng thời tối đa = số token KV ÷ 4096.
- **Số đo:**

  | Lần chạy | KV-cache vLLM báo | Số token KV | B/token suy ra | "Maximum concurrency" | Token ÷ 4096 |
  |---|---|---|---|---|---|
  | W1, Docker, 23/10 | 2,7 GiB | 101.120 | 2,7 × 2³⁰ ÷ 101.120 ≈ 28.670 | 24,69x | 24,69 |
  | k3s, 23/10 | chưa đọc dòng này trong log | 112.160 | – | 27,38x | 27,38 |

- **Lệch:** 28.670 so với 28.672 B/token, dưới 0,01 % (vLLM in dung lượng làm tròn tới 0,1 GiB nên không so chính xác hơn được). "Maximum concurrency" đúng bằng số token ÷ 4096 ở cả hai lần. Công thức khớp.
- **Giải thích:** vLLM chia KV-cache theo đúng công thức trên (block KV có kích thước cố định theo token), nên số token chỉ phụ thuộc phần VRAM còn lại sau weights và bộ nhớ tạm. Model dùng GQA (2 KV head cho 12 attention head), nên KV nhỏ hơn 6 lần so với khi mỗi attention head có KV riêng: đây là lý do model 1,5B chứa được ~100 nghìn token trên một GPU 8 GB.
- **Điểm chưa giải thích được:** cùng `--gpu-memory-utilization=0.85`, trên k3s có thêm 11.040 token (≈ 0,30 GiB). Giả thuyết, **chưa kiểm chứng:** lúc chạy W1 desktop đang chiếm ~610 MiB VRAM, và vLLM tính cả bộ nhớ của tiến trình khác vào ngân sách 0,85. Cần đọc `nvidia-smi` và các dòng memory profiling trong `kubectl logs` của pod.
- **KV-cache lúc tải cao (ĐG1-mini, 05/11/2026):** khi số request chạy cùng lúc chạm `max-num-seqs` = 32 (λ = 7–8 req/s), `vllm:kv_cache_usage_perc` trung bình **23 %**. Dự đoán: mỗi request giữ ≈ 670 token prompt (256–1024 từ, trung bình 640, cộng 8 token đầu và chat template) + trung bình ≈ 128 token đang sinh ≈ 800 token → 32 × 800 ≈ 25.600 token ≈ **25 %** của 101.120 token. Lệch 2 điểm phần trăm. Kết luận: ở nhà, giới hạn số request đồng thời là `max-num-seqs`, không phải bộ nhớ KV (còn ~75 % trống). Hệ quả cho A3: KV-cache không bao giờ cao ở cấu hình này nên không hợp làm tín hiệu scale ở nhà.
- **Còn phải đo (cần PC):** tách 0,85 × 8151 MiB thành weights / activation / CUDA graph / KV từ log khởi động.

### LT1 – Decode bị giới hạn bởi băng thông bộ nhớ (dự đoán 29/10/2026, đo 5060 ngày 04/11/2026)

- **Lý thuyết** ([Kiến thức nền §1.5](../chi-tiet/02-kien-thuc-nen.md#15-giới-hạn-trên-của-tốc-độ-decode-theo-gpu)): mỗi bước decode phải đọc toàn bộ weights từ VRAM một lần, nên với batch nhỏ, TPOT ≳ kích thước weights ÷ băng thông bộ nhớ.
- **Dự đoán:**
  - Kích thước weights: file `model.safetensors` ở revision đã ghim nặng 3.087.467.144 B (≈ 3,09 GB), khớp với số tham số tính từ `config.json` (≈ 1,544 tỷ × 2 B). Phần KV-cache phải đọc thêm khi batch = 1 với ~770 token chỉ ≈ 22 MB, bỏ qua được.
  - RTX 5060, ~448 GB/s (thông số hãng, **chưa kiểm** bằng `nvidia-smi -q` trên PC): TPOT ≥ 3,09 ÷ 448 ≈ **6,9 ms/token** (≤ ~145 token/s). Thực tế thường chậm hơn 20–40 % ([Kiến thức nền §1.5](../chi-tiet/02-kien-thuc-nen.md#15-giới-hạn-trên-của-tốc-độ-decode-theo-gpu)) → khoảng **8,3–9,6 ms**.
  - RTX 4050 Laptop, ~192 GB/s: TPOT ≥ **16,1 ms/token**; tỷ lệ TPOT 4050 ÷ 5060 ≈ 448 ÷ 192 ≈ **2,3**.
- **Kiểm thông số:** `nvidia-smi` trong pod vLLM: RTX 5060, `clocks.max.memory` 14.001 MHz → GDDR7 28 Gbps/chân; bus 128 bit (theo thông số hãng, `nvidia-smi` không in) → **448 GB/s**, khớp số dùng để dự đoán.
- **Số đo (RTX 5060, 04/11/2026, cluster nhà):** `vllm bench serve` chạy trong pod vLLM, `--max-concurrency 1 --num-prompts 20`, random input 512 / output 256, `--ignore-eos`, `--seed 1`. 20/20 thành công. **TPOT p50 8,68 ms, p95 8,69 ms, p99 8,69 ms**; ITL p50 8,68 ms, p99 8,96 ms; TTFT p50 48 ms; 112,9 token/s.
- **So với dự đoán:** nằm trong khoảng 8,3–9,6 ms, cao hơn cận dưới 6,9 ms là 26 %. Băng thông hiệu dụng ≈ 3,087 GB ÷ 8,68 ms ≈ **356 GB/s ≈ 79 %** của 448 GB/s. Phần lệch phù hợp với overhead đã nêu ở Kiến thức nền §1.5 (kernel không đạt băng thông đỉnh, thời gian lấy mẫu token, lập lịch của vLLM giữa hai bước). TPOT gần như không dao động (p50 = p99), đúng với decode bị giới hạn bởi một đại lượng cố định là lượng byte phải đọc mỗi bước.
- **So với c = 8 (23/10):** 9,30–9,72 ms ở c = 8 so với 8,68 ms ở c = 1: tăng 7–12 % khi batch tăng 8 lần, đúng hướng LT3 (batch nhỏ gần như không làm chậm từng token).
- **Còn thiếu:** đo trên 4050 (laptop chưa vào cluster) để kiểm tỷ lệ ≈ 2,3.

### LT3 – Continuous batching (đo 05/11/2026 từ ĐG1-mini)

- **Lý thuyết** ([Kiến thức nền §2.2](../chi-tiet/02-kien-thuc-nen.md#22-continuous-batching)): vLLM ghép mọi request đang chạy vào cùng một bước decode. Khi batch còn nhỏ, mỗi bước vẫn chủ yếu là đọc weights (LT1), nên thêm request gần như không làm chậm từng token; throughput tăng gần tuyến tính theo số request đồng thời rồi bão hoà ở một điểm gãy.
- **Dự đoán:** throughput tăng gần tuyến tính đến gần B\*; điểm gãy nằm gần B\*.
- **Số đo** (RTX 5060, 1 replica, CONST, `max_tokens` 256, prompt 256–1024 từ; mỗi mức 120 s đo; bảng đầy đủ ở `experiments/capacity-home.json`):

| λ (req/s) | B (request trong hệ thống) | TPOT p50 | TTFT p95 | waiting TB | Throughput ra (≈ λ × 256) |
|---|---|---|---|---|---|
| 1 | 2,0 | 8,9 ms | 0,10 s | 0 | ≈ 256 tok/s |
| 2 | 5,3 | 9,8 ms | 0,12 s | 0 | ≈ 512 tok/s |
| 4 | 13,9 | 12,4 ms | 0,16 s | 0 | ≈ 1.024 tok/s |
| 6 | 27,1 | 16,7 ms | 1,35 s | 1,2 | ≈ 1.536 tok/s |
| 7 | 54,1 | 18,1 ms | 5,28 s | 21,8 | bão hoà ≈ 32 ÷ 18,1 ms ≈ 1.770 tok/s ≈ 6,9 req/s |
| 8 | 124,4 | 18,1 ms | 21,4 s | 92,1 | bão hoà (hàng đợi tăng liên tục) |

- **So với dự đoán:**
  - Throughput tăng tuyến tính tới λ = 6 (mọi request được phục vụ, không xếp hàng) rồi bão hoà ở ≈ 6,9 req/s. **Điểm gãy** giữa λ = 6 và 7, đúng tại B\* ≈ 27: ngay khi số request chạy chạm `max-num-seqs` = 32, phần dư vào hàng đợi, TTFT tăng vọt (1,35 → 5,28 s) trong khi TPOT đứng yên ở 18,1 ms.
  - "Gần như không làm chậm" chỉ đúng khi batch nhỏ: B 2 → 5 làm TPOT tăng 10 %; B 14 tăng 39 %; B 27 tăng 88 %. Lý do có thể: prompt dài (≈ 260–1.030 token) được prefill xen giữa các bước decode, và mỗi bước phải đọc thêm KV của mọi request. Chưa tách được hai phần này.
  - Điểm gãy ở nhà do `max-num-seqs` quyết định, không phải bộ nhớ (KV-cache chỉ 23 %, xem LT2). Trên 4090 với `max-num-seqs` 64 và model 7B thì có thể khác.
- **Định luật Little (dữ liệu cho LT5 của Trình):** B đo phía client so với λ\_thực × E2E trung bình, với λ\_thực = số request gửi trong cửa sổ ÷ 120 s: lệch **≤ 2 %** ở λ = 1–7. Phải dùng λ\_thực, không dùng λ danh định: ở λ = 1 chỉ có 102 request trong 120 s (0,85 req/s, dao động Poisson), dùng λ danh định thì lệch 16 %. Ở λ = 8 lệch 11 % (124 so với 140) vì hàng đợi tăng liên tục, hệ thống không ở trạng thái dừng nên định luật không áp được cho cửa sổ ngắn.
- **GPU util (dữ liệu cho LT6 của Trình):** 89 % ở λ = 1, 100 % từ λ = 2 tới 8, trong khi `waiting` đi từ 0 lên 92. GPU util không phân biệt được tải vừa với quá tải, đúng dự đoán của LT6.

