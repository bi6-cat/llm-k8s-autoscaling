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

## Kiểm chứng lý thuyết LT1–LT4 (Quang, Q8)

Theo mẫu ở [Môi trường §19](../chi-tiet/05-moi-truong-danh-gia.md#19-kiểm-chứng-lý-thuyết-lt1lt8): lý thuyết → dự đoán (tính trước khi đo) → số đo → lệch → giải thích. Thông số model lấy từ `config.json` của `Qwen/Qwen2.5-1.5B-Instruct@989aa798…` (đúng revision đã ghim): 28 lớp, hidden 1536, 12 attention head, **2 KV head**, head_dim 1536 ÷ 12 = 128, BF16 (2 byte), `tie_word_embeddings: true`.

### LT2 – Dung lượng KV-cache (cập nhật 29/10/2026)

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
- **Còn phải đo (cần PC):** tách 0,85 × 8151 MiB thành weights / activation / CUDA graph / KV từ log khởi động; `vllm:kv_cache_usage_perc` lúc tải cao (ĐG1-mini).

### LT1 – Decode bị giới hạn bởi băng thông bộ nhớ (dự đoán 29/10/2026, chưa đo)

- **Lý thuyết** ([Kiến thức nền §1.5](../chi-tiet/02-kien-thuc-nen.md#15-giới-hạn-trên-của-tốc-độ-decode-theo-gpu)): mỗi bước decode phải đọc toàn bộ weights từ VRAM một lần, nên với batch nhỏ, TPOT ≳ kích thước weights ÷ băng thông bộ nhớ.
- **Dự đoán:**
  - Kích thước weights: file `model.safetensors` ở revision đã ghim nặng 3.087.467.144 B (≈ 3,09 GB), khớp với số tham số tính từ `config.json` (≈ 1,544 tỷ × 2 B). Phần KV-cache phải đọc thêm khi batch = 1 với ~770 token chỉ ≈ 22 MB, bỏ qua được.
  - RTX 5060, ~448 GB/s (thông số hãng, **chưa kiểm** bằng `nvidia-smi -q` trên PC): TPOT ≥ 3,09 ÷ 448 ≈ **6,9 ms/token** (≤ ~145 token/s). Thực tế thường chậm hơn 20–40 % ([Kiến thức nền §1.5](../chi-tiet/02-kien-thuc-nen.md#15-giới-hạn-trên-của-tốc-độ-decode-theo-gpu)) → khoảng **8,3–9,6 ms**.
  - RTX 4050 Laptop, ~192 GB/s: TPOT ≥ **16,1 ms/token**; tỷ lệ TPOT 4050 ÷ 5060 ≈ 448 ÷ 192 ≈ **2,3**.
- **Số đo:** chưa đo. Cần TPOT ở batch = 1, 20 lần mỗi máy (`vllm bench serve --max-concurrency 1 --num-prompts 20`, random 512/256, `--ignore-eos`).
- **Số tham khảo, không phải số đo LT1:** `vllm bench` ở **c = 8** (23/10) cho TPOT p50 9,30 ms (Docker) và 9,69–9,72 ms (k3s), nằm trong khoảng 8,3–9,6 ms đã dự đoán cho batch = 1. Ở c = 8, mỗi bước đọc thêm KV của 8 request (~0,15 GB), nên TPOT batch = 1 được kỳ vọng thấp hơn một chút; phải đo mới kết luận được.
