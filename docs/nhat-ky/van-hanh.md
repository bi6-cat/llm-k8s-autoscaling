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
- **Cập nhật 05/11 trưa (đọc `journalctl --list-boots` trên PC):** không phải k3s tự khởi động lại mà là **cả PC khởi động lại**. Lượt boot trước kết thúc bằng tắt máy bình thường (`systemd: Shutting down.`) lúc 19:32 ngày 04/11; lượt boot mới bắt đầu khoảng 02:01 ngày 05/11. Lúc boot, kernel đặt đồng hồ theo RTC là `02:01:25 UTC` (tức 09:01 giờ VN), lệch 7 giờ so với thực tế, rồi NTP chỉnh lại. Vì vậy giờ "01:25" ở trên (tính từ tuổi pod) không đáng tin; `creationTimestamp` của pod mới là 19:17 UTC ngày 04/11 (02:17 giờ VN), khoảng 16 phút sau khi boot. Chưa rõ ai tắt máy lúc 19:32. Giả thuyết cho chuyện RTC lệch đúng 7 giờ (chưa kiểm): PC dual-boot với Windows, Windows ghi RTC theo giờ địa phương.

## 2026-11-05 – Sự cố: PC nhà treo khi suspend, khởi động lại từ đầu

- **Môi trường:** nhà, PC `zett-ubuntu-pc` (node k3s duy nhất, vLLM đang giữ ~6,8 GB VRAM). Người xử lý: Quang (AI agent ra lệnh suspend theo yêu cầu).
- **Triệu chứng:** sau lệnh `systemctl suspend` lúc 03:16 ngày 05/11, máy không vào trạng thái ngủ. Sáng 11:17 máy chạy một **lượt boot mới** (`uptime` 39 phút lúc 11:57), không phải resume.
- **Bằng chứng (`journalctl -b -1`):** 03:16:42 `Reached target sleep.target`, `Starting nvidia-suspend.service`; sau đó không có dòng `PM: suspend entry`; log vẫn chạy (gsd-power 03:17:16, tailscaled báo mất mạng) và dừng ở 03:18:38. Lượt boot tiếp theo bắt đầu 11:17:54. So sánh: lần suspend 04/11 lúc 02:59 có vào được (`PM: suspend entry (deep)`, `nvidia-suspend` mất 3 phút 47 giây, đỉnh 2,4 GB RAM), resume 12:26 nhưng gnome-shell lỗi `gbm_surface_lock_front_buffer failed`, 1 phút sau máy boot lại.
- **Nguyên nhân (giả thuyết, chưa kiểm):** bước `nvidia-suspend` phải chép VRAM ra RAM; khi vLLM giữ gần hết VRAM thì bước này chậm hoặc treo.
- **Sau khi khởi động lại:** k3s tự lên (node IP Tailscale), mọi pod hệ thống `Running`, vLLM mới 1/1. Còn 5 pod vLLM cũ `Unknown`/`Completed` và pod `loadgen` `Unknown` từ các lượt boot trước, chưa dọn.
- **Bài học:** không suspend PC khi nó đang là node k3s chạy vLLM; muốn nghỉ thì tắt hẳn (`shutdown`), hoặc scale vLLM về 0 trước khi suspend. Việc PC khởi động lại nhiều lần (04/11 12:28, 19:26, 05/11 ~02:01, 11:17) và k3s lần nào cũng tự lên cho thấy drop-in "chờ Tailscale" (02/11) hoạt động, mục "Chưa kiểm" trong nhật ký Quang 02/11 coi như đã kiểm.

## 2026-11-06 – Dựng lại cluster nhà từ máy trắng sau khi cài lại hệ điều hành

- **Môi trường:** nhà, PC cài lại Ubuntu 26.04.1 lên NVMe (23:08 ngày 05/11), tên mới `zorsche-upc`, IP Tailscale mới `100.120.67.28`. Người làm: Quang và Claude Code (từ xa, Quang ngủ).
- **Các bước:** cài Ansible (ansible-core 2.21.6, `uv tool`), Tailscale 1.104.5 (apt); `ansible-playbook -i inventory/home.yaml site.yml`; helm/kubectl cho kube-prometheus-stack, device plugin, GPU exporter, KEDA, vLLM; chạy lại playbook với Argo CD.
- **Số đo:** k3s từ lúc chạy playbook tới node Ready: **29 s** (lần chạy thành công); kube-prometheus-stack 59 s; kéo image vLLM 9,0 GB: 4 phút 14 giây; pod vLLM đầu tiên Ready sau 400 s. Driver NVIDIA 595.99.02 và Container Toolkit 1.20.1 đã có sẵn sau khi cài lại hệ điều hành (Quang cài tay).
- **Lỗi gặp khi dựng lại:** umask 077 của shell lan sang Ansible làm khoá GPG kho NVIDIA không đọc được (`apt update` lỗi); Argo CD core thiếu AppProject `default`. Cả hai đã sửa trong repo (xem nhật ký tuần 05 của Quang).
- **Runbook đã dùng:** không có; theo README và `docs/huong-dan/w2.md`.
- **Bài học:** đường Ansible dựng lại được cluster nhanh, nhưng phần sau k3s (helm, Argo CD) vẫn còn bước tay cho tới khi App-of-Apps lên `main`. Đây chưa phải VH5 chính thức (người dựng là chính Quang, không bấm giờ trọn từ máy trắng).

## 2026-11-06 – Sự cố: PC hết RAM khi chạy 2 pod vLLM, treo nhiều giờ

- **Môi trường:** nhà, PC (RAM 15 GB, không swap), k3s một node, vLLM Qwen2.5-0.5B, time-slicing 2 GPU replica. Desktop GNOME, VS Code và Claude Code đang chạy.
- **Triệu chứng:** khoảng 05:08 scale vLLM lên 2 replica. Từ 05:15, `kubectl` báo `TLS handshake timeout`; load average 70–100; RAM khả dụng 0,36–0,64 GB; đọc đĩa 0,4–1,2 GB/s; IO pressure ~80 %. Lệnh `kubectl scale` về 1 không tới được API server suốt từ 05:19 tới khoảng 09:00. `sudo pkill -9` các tiến trình vLLM báo `Permission denied`, chưa rõ vì sao.
- **Nguyên nhân:** mỗi pod vLLM dùng ~3,4 GiB RAM; cộng desktop (~4–5 GB), k3s (~1,5 GB), giám sát (~1,2 GB), Argo CD (~0,5 GB) thì vượt RAM. Không có swap nên kernel bỏ page cache của code đang chạy rồi đọc lại liên tục (thrashing) thay vì OOM-kill. Không phải thiếu VRAM: 2 pod dùng ~6,5/8 GB.
- **Xử lý:** máy khởi động lại khoảng 10:19 (không rõ do người bấm hay tự treo rồi reset). Ngay sau khi lên, k3s lại tạo 2 pod vì Deployment vẫn lưu `replicas=2`; scale về 1 trong phút đầu, trước khi RAM cạn.
- **Số đo:** gián đoạn API server khoảng 5 giờ (05:15 → 10:19).
- **Runbook đã dùng:** không có.
- **Bài học:** ở nhà, RAM chứ không phải VRAM là giới hạn số replica. Trước khi chạy 2 pod: tắt desktop (chạy `multi-user.target`), hoặc thêm zram/swap để máy chậm thay vì treo, hoặc giảm thành phần giám sát; cân nhắc đặt `maxReplicaCount` của A2 ở nhà = 1 cho tới khi xong. Tạo pod mới trên node đang thiếu RAM có thể làm chính control-plane mất phản hồi: nên viết runbook "node hết RAM".

## 2026-11-06 – Test graceful shutdown ở nhà; sự cố: vLLM không dừng khi nhận SIGTERM

- **Môi trường:** nhà, PC (k3s một node, RTX 5060 chia 2 GPU replica), vLLM `v0.31.0`, Qwen2.5-0.5B, `--max-num-seqs 16`, `--max-model-len 2048`, 1 pod. Script `experiments/ops/graceful_shutdown.py`, client chạy trên PC gọi ClusterIP của Service. Người chạy: Quang (Claude hỗ trợ).
- **Các bước:** mỗi lần thử mở 48 stream `/v1/completions` × 1900 token (`ignore_eos`), chờ 16 stream đầu nhận token, `kubectl delete pod`, đếm stream ok / cut (đã nhận 200 nhưng thiếu `[DONE]` hoặc thiếu token) / rejected. 48 thay vì "khoảng 30" (Kiến trúc §8.3) để vẫn còn stream chạy lúc SIGTERM đến ở giây 20.
- **Số đo:**

  | Ca | preStop | `--shutdown-timeout` | grace | ok / cut / rejected | stream cuối xong | pod mất sau |
  |---|---|---|---|---|---|---|
  | Chính, lần 1–3 | 20 s | 150 | 180 s | 48/0/0 mỗi lần (144/144) | +23,1–23,3 s | +181,5 / 181,9 / 181,9 s |
  | Đối chứng 1 | không | 0 | 180 s | 48/0/0 | +23,1 s | +182,9 s |
  | Đối chứng 2 | không | 0 | 5 s | 0/48/0 (16 đang sinh, nhiều nhất 1432/1900 token; 32 đang xếp hàng) | cắt ở +5,5 s | +6,5 s |

  Mỗi lần thử của ca chính có 16 stream xong sau giây 20 (sau SIGTERM). RAM khả dụng thấp nhất 1,26 GB (20:14:17), lúc pod cũ còn kẹt và pod thay thế đang nạp model.
- **Sự cố:** ở mọi ca, sau SIGTERM vLLM log `[shutdown] … mode=drain timeout=150s` (hoặc `mode=abort timeout=0s`) và `send sigterm to process EngineCore`, nhưng **engine vẫn chạy**: 3–18 s sau vẫn `Running: 16 reqs` và còn nhận request từ hàng đợi (prompt throughput > 0), kể cả ở chế độ abort. API server vẫn trả `/health` 200 và **không tự thoát, kể cả sau mốc 150 s**; tiến trình chỉ dừng khi kubelet SIGKILL ở giây 180. Pod nhàn rỗi (scale về 0, không có request) cũng kẹt y hệt. Ở W1 (Docker, 1,5B, 1 stream) chế độ abort có cắt stream; chưa rõ vì sao lần này khác. Chưa tìm nguyên nhân gốc.
- **Kết luận:** request không bị cắt là **nhờ grace period 180 s giữ pod sống**, không phải nhờ drain của vLLM (đối chứng 1 cũng 0 lỗi; đối chứng 2 rút grace xuống 5 s thì cắt cả 48). Hệ quả: (1) request kéo dài quá ~160 s sau SIGTERM vẫn bị SIGKILL cắt; (2) mỗi lần tắt pod giữ GPU đủ 180 s: rolling update với `maxSurge: 0` chờ thêm 3 phút mỗi pod, scale-down tốn thêm 3 phút GPU-giờ; (3) ở nhà pod kẹt chồng với pod mới làm RAM xuống 1,26 GB.
- **Runbook đã dùng:** không.
- **Bài học / việc tiếp:** tìm nguyên nhân EngineCore bỏ qua SIGTERM (thử `kill -TERM` tay trong pod, xem tiến trình con, thử bản vLLM khác); kiểm lại trên VM thuê ở V0. Ghi vào phần hạn chế nếu không sửa được. Dữ liệu: `runs/graceful-20261106-2006*` trên PC (chưa đẩy R2).

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
- **Số đo** (RTX 5060, 1 replica, CONST, `max_tokens` 256, prompt 256–1024 từ; mỗi mức 120 s đo; bảng đầy đủ ở `experiments/capacity-home-1.5b.json`, trước 06/11 tên là `capacity-home.json`):

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

### LT4 – Phân rã cold start (đo 16/11/2026 ở nhà, Qwen2.5-0.5B)

- **Lý thuyết** ([Kiến trúc §7](../chi-tiet/03-kien-truc-autoscaling.md#7-cold-start-chi-tiết)): thời gian nạp weights ≈ dung lượng checkpoint ÷ tốc độ đọc đĩa; nếu file đã nằm trong page cache thì gần bằng tốc độ chép RAM.
- **Dự đoán** (tính ngày 16/11, **sau** khi đã có số đo lần A, nên không phải dự đoán mù): checkpoint 0,92 GiB = 988 MB. `fio` đọc tuần tự trên phân vùng NVMe chứa `/var/lib/llm-cache`: 367 MB/s (direct, 1 MiB, QD1) và 1.202 MB/s (buffered, 128 KiB, có readahead) → nạp nguội **0,8–2,7 s**; nạp ấm dưới 1 s.
- **Số đo** (bộ đọc `experiments.runner.vllm_log`, mốc container lấy từ pod status):

  | Pha | A: page cache nguội (12:58, sau boot) | B: page cache ấm (13:10, thay pod) |
  |---|---|---|
  | Kéo image | 892 s (image không còn trên node) | 0 s (đã có) |
  | Container chạy → dòng log đầu (import) | 18,9 s | 16,2 s |
  | Tải weights từ Hugging Face | 0 s (đã có trên đĩa) | 0 s |
  | Nạp model (`p6_load_weights`); riêng "Loading weights took" | 16,2 s; **11,67 s** | 7,6 s; **3,08 s** |
  | Khởi tạo engine (`p7_engine_init`) | 106,9 s | 108,8 s |
  | – trong đó chụp CUDA graph lúc profiling | 97 s | 100 s |
  | – trong đó `torch.compile` (cache ấm) | 0,90 s | 0,87 s |
  | – cấp KV-cache; chụp CUDA graph thật | 3,1 s; 1 s | 3,0 s; 1 s |
  | Engine xong → server mở cổng | 5,6 s | 5,5 s |
  | Container chạy → pod Ready | 162 s | 155 s |

- **Lệch:** nạp weights nguội 11,67 s ứng với 85 MB/s, chậm hơn dự đoán 4–14 lần. Nạp ấm 3,08 s ứng với 321 MB/s, cũng chậm hơn dự đoán.
- **Giải thích (chưa kiểm chứng):** lúc đo máy thiếu RAM (vLLM báo `Available RAM: 1.93 GiB` ở lần A, `2.59 GiB` ở lần B; hệ thống đang swap 2,6–2,9 GB), nên page cache bị thu hồi liên tục; và "Loading weights took" gồm cả việc chép tensor lên GPU, không chỉ đọc đĩa. Chưa tách được hai phần này.
- **Pha chi phối:** không phải nạp weights. Ở cả hai lần, chụp CUDA graph lúc profiling (để đo bộ nhớ CUDA graph) chiếm ≈ 100 s trên ≈ 160 s, tức 60–64 %; lần chụp thật ngay sau đó chỉ 1 s. Chưa rõ vì sao lần chụp lúc profiling chậm tới 28–48 s mỗi bước. Với model 0,5B, cold start khi image và weights đã có gần như không phụ thuộc đĩa.
- **Giới hạn của phép đo:** mỗi ca 1 mẫu; ca nguội không dùng `drop_caches` (không có sudo trong phiên) mà lấy lần khởi động đầu sau khi boot; đo 0 → 1 và thay pod, không phải scale 1 → 2 như Môi trường §19. Cần đo lại trên V2 (ĐG3) với model 3B.

## Kiểm chứng lý thuyết LT5–LT8 (Trình, TR8)

Cùng mẫu với LT1–LT4. Đủ LT5–LT8; LT5, LT6 đã thêm dữ liệu V2 ngày 21/11.

### LT5 – Định luật Little (phân tích 16/11/2026 trên dữ liệu đã đo)

Thêm dữ liệu V2 ngày 21/11 (giữ tên mục để link tới mục không đổi).

- **Lý thuyết** ([Kiến trúc §10.2](../chi-tiet/03-kien-truc-autoscaling.md#102-a2-số-request-đồng-thời-running--waiting)): ở trạng thái dừng, L = λ × W. A2 dùng chính L = Σ_pod (`running` + `waiting`). Trên một cửa sổ hữu hạn dài T, đẳng thức sau đúng tuyệt đối: L_client = λ\_thực × W + edge, với edge = (vào − tràn) ÷ T. "Vào" là thời gian mà các request gửi trước cửa sổ còn nằm lại trong cửa sổ; "tràn" là thời gian mà các request gửi trong cửa sổ còn nằm lại sau cửa sổ. Khi hệ dừng thì edge ≈ 0; khi hàng đợi đang tăng thì edge < 0.
- **Dự đoán** (ghi trước khi chạy script trên dữ liệu simulator; dữ liệu nhà đo từ 05–06/11, nhưng Little không có tham số tự do, nên không có gì để chỉnh cho khớp số đo):
  - Mọi cửa sổ dừng: L_server ≈ λ\_thực × W, lệch < 15 %. Lệch còn lại do lấy mẫu 5 s. Theo M/G/∞ (chưa xếp hàng), SE = √((λ ÷ n) × Σ_k (W − 5|k|)+). Ở nhà, W < 5 s và có 24 mẫu, nên SE ≈ √(L ÷ 24), tức 14 % khi L = 2. Ở simulator pha `pre` (W ≈ 13 s), SE ≈ 13 %.
  - Simulator (`patch-sim.yaml`: TTFT 200 ms, ITL 50 ms, 256 token): W = 0,2 + 255 × 0,05 = 12,95 s. Từ đó `pre` (λ 0,5) cho L ≈ 6,5; `spike` của A2 (λ trung bình ≈ 2,21) cho L ≈ 28,6; `drop` có edge dương nhỏ, vì request của `spike` còn trong hệ thống ở mép đầu.
  - Cửa sổ quá tải (λ\_thực > năng lực) thì L < λW. Lượt có request lỗi thì không áp được định luật, vì không biết lúc request lỗi rời server.
- **Cách đo:** `analysis/lt5_little.py`, bảng mỗi cửa sổ một dòng ở `analysis/figures/lt5-little.csv`. Lệnh: `uv run --project analysis python -m analysis.lt5_little envs/home/experiments/capacity-1.5b.json envs/home/experiments/capacity.json runs/sim/mp-final-w2@1.0162 runs/sim/tr7-kb2-sim-2@1.033 runs/dg1-v2-4060ti runs/v2-vm/v2-dg2 --out analysis/figures/lt5-little.csv`.
  - V2 (18–19/11, VM 4 × RTX 4060 Ti, Qwen2.5-3B) dùng dữ liệu thô của runner, không dùng bản tóm tắt `capacity.json`: ĐG1 (`dg1-v2-4060ti`, 1 replica, mỗi mức một cửa sổ `steady` 300 s, gồm cả 60 s đầu mà `capacity.json` bỏ) và ĐG2 (`v2-dg2`, 17 lượt A1, A2, S1, S4 × KB1–KB3, 1–4 replica). V2 chạy trên Linux thật nên k = 1 (kiểm ở phần "Hệ quả").
  - File capacity ở nhà chỉ có bản tóm tắt mỗi mức λ (dữ liệu thô nằm trên máy Quang), nên chỉ tính lại được λ\_thực = n\_measured ÷ 120 s và so B_server, B_client với λ\_thực × W.
  - Lượt runner trên simulator có đủ dữ liệu thô. Script tách thêm L_client_sampled, là số request client đang chờ đúng tại các mốc mẫu của Prometheus. Nhờ vậy lệch của server tách được thành hai phần: phần do lấy mẫu (L_client_sampled − L_client) và phần do định nghĩa (L_server − L_client_sampled).
  - Hậu tố `@k` là tốc độ đồng hồ của máy tạo tải (xem giải thích 3).
- **Số đo** (lệch = L ÷ (λ\_thực × W) − 1):

  | Dữ liệu | Cửa sổ | λ\_thực (req/s) | W (s) | λ\_thực × W | L_client (edge) | L_server | lệch server |
  |---|---|---|---|---|---|---|---|
  | Nhà, 1,5B, 7 mức dừng (λ 1–7) | 120 s | 0,85–6,79 | 2,37–7,92 | 2,0–53,8 | lệch −0,6…+0,6 % | | −1,2…+4,5 % |
  | Nhà, 1,5B, λ = 8 (quá tải) | 120 s | 7,52 | 18,57 | 139,6 | 124,4 (−10,9 %) | 124,0 | −11,2 % |
  | Nhà, 0,5B, 7 mức dừng (λ 2–12,5) | 120 s | 2,03–12,36 | 0,92–2,23 | 1,9–27,6 | lệch −0,3…+1,1 % | | −4,4…+14,3 % |
  | Nhà, 0,5B, λ = 13; 13,5; 14 (quá tải) | 120 s | 12,96–14,13 | 5,5–14,9 | 72–211 | −4,4; −7,1; −12,7 % | | −5,1; −10,4; −13,7 % |
  | Sim S1-CONST2-1 (λ 2 > năng lực 1,24) | 60 s từ hệ rỗng | 1,93 | 29,71 | 57,37 | 37,88 (edge −19,49) | 37,00 | −35,5 % |
  | Sim A2-KB2-1 `pre` | 120 s | 0,551 | 12,74 | 7,02 | 7,06 (+0,04) | 7,17 | +2,1 % |
  | Sim A2-KB2-1 `spike` (scale 1 → 3) | 600 s | 2,204 | 12,79 | 28,18 | 27,92 (−0,26) | 27,92 | −0,9 % |
  | Sim A2-KB2-1 `drop` (scale 3 → 1) | 600 s | 0,623 | 12,74 | 7,94 | 8,15 (+0,21) | 8,30 | +4,6 % |
  | Sim S1-KB2-1 `pre` (lượt không hợp lệ) | 120 s | 0,551 | 12,73 | 7,01 | 7,05 (+0,04) | 6,96 | −0,8 % |
  | Sim S1-KB2-1 `spike`, `drop` (có request lỗi) | | | | | | | không áp được |
  | V2 ĐG1, 3B, 3 mức dừng (λ 2–3,5; 1 replica) | 300 s | 1,94–3,47 | 8,45–12,97 | 16,4–45,0 | lệch −1,5…−0,9 % | | −3,5…−1,0 % |
  | V2 ĐG1, λ = 4; 5 (quá tải) | 300 s | 4,00; 4,94 | 18,5; 51,4 | 74,1; 253,7 | 71,0 (−4,2 %); 202,1 (edge −51,7; −20,4 %) | 69,2; 199,4 | −6,6; −21,4 % |
  | V2 ĐG2, 24 cửa sổ chưa xếp hàng (A1, A2, S1, S4 × KB1–KB3; 1–4 replica) | 120–720 s | 1,69–10,72 | 6,63–10,02 | 11,2–107,3 | lệch −3,8…+5,3 % | | −5,8…+4,9 % |
  | V2 ĐG2, A2-KB3-1, -2 `ramp` (có hàng đợi, waiting 6,0; 10,8) | 300 s | 5,88; 5,98 | 12,42; 13,00 | 73,1; 77,8 | 71,2 (edge −1,84); 76,2 (−1,60) | 69,7; 75,6 | −4,6; −2,8 % |
  | V2 ĐG2, 10 cửa sổ pha có request lỗi (A2-KB2 `spike`, `drop`; S1-KB2; S1-KB3) | | | | | | | không áp được |

  Sim dùng k = 1,033 cho phiên `tr7-kb2-sim-2` và 1,0162 cho `mp-final-w2` (giải thích 3). V2 dùng k = 1.

- **So với dự đoán:**
  - Ở cả **18/18 cửa sổ dừng**, L_server lệch λ\_thực × W từ −4,4 % đến +14,3 %, tức đều dưới 15 %. Phía client lệch từ −0,9 % đến +2,6 %. Hai trong 18 cửa sổ thuộc lượt mà runner đánh dấu không hợp lệ: 1,5B λ = 6 (máy tạo tải bị cgroup throttle 4,4 ms) và S1-KB2-1 (pod restart một lần trong lượt). Hai cửa sổ này lệch −1,2 % và −0,8 %; bỏ chúng thì khoảng lệch không đổi.
  - Lệch lớn nhất (+14,3 %, 0,5B λ = 2, L = 1,86) chỉ bằng 1,0 SE do lấy mẫu. Ở 14 cửa sổ chưa xếp hàng, z = (L_server − λW) ÷ SE nằm trong [−0,76; +0,96], trung bình +0,20, nên không thấy thiên lệch có hệ thống.
  - Simulator: λ\_thực × W khớp dự đoán tiên nghiệm trong khoảng −1,5 % (`spike` A2: 28,18 so với 28,6). Ở `pre`, λW = 7,0 so với dự đoán 6,5, vì λ\_thực = 0,55 thay vì 0,5: 64 request trong 120 s, dao động Poisson (SD ±13 %) cộng phần hiệu chỉnh đồng hồ. W ở `pre` đo theo đồng hồ của máy tạo tải là 13,16 s, dài hơn cấu hình 1,6 % (TPOT 50,7–50,8 ms thay vì 50 ms; chưa tách nguyên nhân). Simulator hẹn giờ bằng đồng hồ đơn điệu, nên phần chênh này không phải do k.
  - **V2 (thêm 21/11, sau khi đã ghi dự đoán ở trên):** ở cả **27/27 cửa sổ chưa xếp hàng** (3 của ĐG1, 24 của ĐG2), L_server lệch λ\_thực × W từ −5,8 % đến +4,9 %; phía client lệch từ −3,8 % đến +5,3 %. z nằm trong [−2,35; +1,57], trung bình −0,42. Ba cửa sổ có |z| > 2 đều rơi vào lúc tải đang đổi: pha `ramp` của A1-KB3-1 và S4-KB3-1, pha `spike` của S4-KB2-1. Ở các cửa sổ đó edge âm (−0,7 đến −1,8), nên phía client cũng lệch âm (−0,7 đến −3,8 %). Tách lệch của 27 cửa sổ thành hai phần: phần lấy mẫu trung bình −0,5 % (−3,4…+1,7 %), phần định nghĩa trung bình −0,3 % (−3,8…+3,0 %), nên không thấy thiên lệch có hệ thống. Cả 53 dòng V2 đều thuộc lượt hợp lệ.
- **Giải thích:**
  1. **Quá tải** (1,5B λ = 8; 0,5B λ ≥ 13): lệch âm 5–14 %, và phía client lệch gần bằng phía server, nên đây không phải lỗi đo của Prometheus. Hệ không dừng: request gửi cuối cửa sổ còn nằm trong hàng đợi sau khi cửa sổ đóng (tràn > vào). Lượt simulator S1-CONST2-1 cho thấy rõ bằng số: edge = −19,5 trên λW = 57,4, nên L_client = 37,9 (−34 %), còn L_server chỉ lệch L_client −2,3 %. Đẳng thức có edge vẫn đúng tuyệt đối; chỉ phép xấp xỉ L ≈ λW là không dùng được. Trên V2, ĐG1 λ = 5 (1,43 C, waiting trung bình 137) cho cùng hình ảnh: edge = −51,7 trên λW = 253,7, L_client lệch −20,4 %, L_server lệch L_client chỉ −1,3 %. Đây là cửa sổ V2 duy nhất nằm ngoài dải ±15 %.
  2. **Nhiều replica:** ở `spike` và `drop` của A2, tổng running + waiting của mọi pod khớp log client trong 5 %, kể cả khi số pod đổi 1 → 3 → 1 (theo series của pod; pod bị xoá thì series của nó dừng lại). Vậy metric của A2 đo đúng lượng việc của cả hệ thống. V2 kiểm lại điều này trên 4 GPU thật: 13 cửa sổ có trung bình ≥ 3,99 replica Ready (mọi pha của S4, A1-KB2 `spike` và `drop`, A1-KB3 và A2-KB3 `sustain`) lệch −5,8…+4,9 %, kể cả khi λ\_thực × W tới 107. Lệch −5,8 % là pha `ramp` của S4-KB3, lúc tải đang tăng (edge −1,8; phía client −3,8 %).
  3. **Đồng hồ của simulator.** Lần chạy đầu (k = 1), pha `drop` của A2 lệch −11,9 % (L_server 6,99 so với L_client_sampled 8,24). Phần lệch dồn vào 30 s đầu pha (846–871 s): client có 20–33 request đang chờ, còn server chỉ đếm 7–22. Nguyên nhân: loadgen ghi mốc request bằng `perf_counter` (đồng hồ đơn điệu) cộng `t0_unix` (`loadgen/sender.py`), còn Prometheus đóng dấu mẫu bằng giờ thực, và trong VM WSL2 đồng hồ đơn điệu chạy nhanh hơn giờ thực k lần. Các bằng chứng:
     - Độ trễ khớp nhất giữa chuỗi server và chuỗi client tăng dần theo thời gian: −1, −6, −11 s ở các đoạn có tâm 120, 370, 670 s. Đây chỉ là bằng chứng về chiều lệch. Độ dốc suy ra (≈ 1,8 %) là ước lượng thô, vì độ trễ được dò trên số request đang chạy (vốn nhiễu) và lấy trung bình cả đoạn, nên không dùng để chọn k.
     - Runner (giờ thực) thấy loadgen xong lúc t0 + 1419,4 s, trong khi loadgen tự đo được `wall_s` = 1451,6 s. Vậy k ≥ 1,022 (cộng trừ 1 s cho lệch giờ giữa pod và runner). Runner hỏi file DONE theo vòng `kubectl get` + `kubectl exec` + ngủ 10 s, nên thấy DONE muộn nhất khoảng 20 s (dư 5 s cho mỗi lần gọi kubectl), tức k ≤ 1,038 (A2). Với S1, chạy cùng buổi sáng, k ∈ [1,028; 1,044]. Mtime của các file kết quả không giúp gì thêm: đó là lúc `kubectl cp` giải nén, sau `t_main_end` 22 ms.
     - Bản ghi chỉnh giờ của journal trong lượt LT7 cho k = 1,0188 vào chiều 16/11, sau khi VM khởi động lại lúc khoảng 16:17. Ngày 07/11 là 1,0162. Vậy k đổi sau mỗi lần VM khởi động.

     Dùng k = 1,033 (giữa cận chung [1,028; 1,038] của hai lượt) thì `drop` chỉ còn lệch +4,6 %. Với mọi k trong cận chung, lệch nằm trong +2,2…+7,4 %; trong cận riêng của A2 thì −0,5…+7,4 %. Cận lấy từ mốc của runner, không dùng dữ liệu Prometheus, nên không phải lập luận vòng. λ × W không phụ thuộc k: W ngắn đi k lần, còn λ tăng đúng k lần.
  4. **Có request lỗi** (S1-KB2 `spike`, `drop`): L_server gấp 2–3 lần L_client, vì L_client không tính các request lỗi (timeout, bị từ chối kết nối): chúng không có mốc rời hệ thống. Script đánh dấu `applicable = False`. Trên V2, S1-KB2-1 `spike` có 5.468/6.198 request lỗi và L_server gấp 13,6 lần L_client (1.033 so với 75,8). Ngược lại, A2-KB2 `spike` chỉ có 37–93/6.145–6.198 request lỗi (0,6–1,5 %), nên L_server vẫn chỉ lệch +2,4…+7,0 %. Script vẫn bỏ các cửa sổ này theo đúng quy tắc.
- **Hệ quả:**
  - Prometheus đo đúng L, và L tỷ lệ với λ theo đúng W đo được ở trạng thái dừng. Đây là cơ sở để đặt threshold A2 theo B\* lấy từ ĐG1.
  - Phần kiểm Little trong `experiments/runner/capacity.py` (Môi trường §8 bước 6) trước đây dùng λ danh định, nên báo nhầm ở mức λ thấp: 0,5B λ = 2 lệch 15,7 % và ra `little_ok = False`, trong khi dùng λ\_thực chỉ lệch 14,3 %. Trình đã sửa sang λ\_thực, đếm trên cùng tập request thành công với W, và thêm hai trường `lambda_real_rps`, `window_s` (`lt5_little.py` đọc hai trường này khi có, ví dụ ĐG1 trên V2 đo 240 s mỗi mức). Hai file `capacity*.json` đã có giữ giá trị cũ, vì không có dữ liệu thô trên máy này để tính lại.
  - Ngưỡng 15 % là chặt khi B nhỏ: với 24 mẫu, SE ≈ 1 ÷ √(24 B), tức 14 % ở B = 2. ĐG1 trên V2 đo 4 phút mỗi mức (48 mẫu) thì SE còn 10 % ở B = 2.
  - Trên simulator trong WSL2, mọi phép so mốc client với Prometheus hoặc mốc pod đều lệch (k − 1) × t. Ví dụ, thời điểm tải tăng của KB2 (t = 240 s) thật ra sớm hơn khoảng 8 s so với `t0_unix + 240`, nên N2a do `build_tables` tính trên simulator ngắn đi khoảng 8 s. Cuối lượt 24 phút, lệch tới khoảng 45 s. V2 chạy trên Linux thật nên không bị: đã kiểm 21/11, cận k của cả 22 lượt V2 (5 ĐG1, 17 ĐG2) đều chứa 1, giao của chúng là [0,9973; 1,0076]. Cách sửa gốc là để loadgen ghi thêm giờ thực lúc kết thúc; chưa làm.
- **Hình** ([lt5-little.svg](../../analysis/figures/lt5-little.svg), vẽ 18/11 từ `lt5-little.csv` bằng `analysis/lt_charts.py --lt5`): ô trái là L_server theo λ\_thực × W (thang log, đường y = x, dải ±15 %); ô phải là độ lệch, kèm thanh ±1 SE do lấy mẫu ở các cửa sổ chưa xếp hàng. Hình có 23 cửa sổ: 18 cửa sổ dừng và 5 cửa sổ quá tải của bảng trên. Bỏ 3 cửa sổ có request lỗi, và cửa sổ `main` của A2-KB2-1 vì nó chồng lên `pre`, `spike`, `drop`. Chấm rỗng là 9 cửa sổ có hàng đợi (waiting trung bình ≥ 1): 5 cửa sổ quá tải, cộng 4 cửa sổ mà bảng trên xếp vào nhóm dừng nhưng đã có hàng đợi (1,5B λ = 6, 7; 0,5B λ = 12; 12,5). 22/23 cửa sổ nằm trong dải. Chỉ cửa sổ `steady` của S1-CONST2-1 trên simulator (`mp-final-w2`) nằm ngoài dải (−35,5 %, giải thích 1).
  - Vẽ lại 21/11, thêm V2 (màu thứ 4): **54 cửa sổ** = 23 cửa sổ trên + 31 cửa sổ V2. Bỏ 18 cửa sổ có request lỗi (3 cũ, 15 V2) và 8 cửa sổ `main` (1 cũ, 7 V2; KB3 cũng có `main` chồng lên `ramp`, `sustain`). 52/54 cửa sổ nằm trong dải; hai cửa sổ ngoài dải đều là quá tải: S1-CONST2-1 trên simulator và S1-CONST5-1 của ĐG1 V2 (−21,4 %, giải thích 1).

### LT6 – GPU utilization bão hoà (phân tích 16/11/2026 trên dữ liệu đã đo)

Thêm dữ liệu V2 ngày 21/11 (giữ tên mục để link tới mục không đổi).

- **Lý thuyết** ([Kiến thức nền §4.4](../chi-tiet/02-kien-thuc-nen.md#44-vì-sao-gpu_util-bão-hoà)): GPU util là tỷ lệ thời gian có ít nhất một kernel chạy, không phải phần năng lực GPU đang dùng. vLLM chạy kernel liên tục khi còn ít nhất một request, nên util ≈ P(N ≥ 1), với N là số request trong hệ thống. Khi chưa xếp hàng, mỗi request được phục vụ gần như độc lập với số request khác (LT3), nên hệ gần với hàng đợi M/G/∞: N có phân phối Poisson với trung bình L (LT5), và util ≈ 1 − e^(−L).
- **Dự đoán:**
  - Định tính (Môi trường §19, ghi trước khi đo): util ≈ 100 % ngay từ tải vừa, trong khi `waiting` chênh nhau nhiều lần giữa tải vừa và quá tải.
  - Định lượng: util = 1 − e^(−L), tức 86 % ở L = 2 và 99 % ở L = 4,6. Như vậy util bão hoà khi L mới bằng khoảng 1/6 B\* (B\* = 27–28 ở cả hai model). Công thức này Trình thêm lúc phân tích, sau khi đã thấy bản tóm tắt "89 % ở λ = 1, 100 % từ λ = 2" ở LT3. Nó không có tham số tự do, nên không chỉnh được cho khớp số đo.
  - Tiêu chí "phân biệt được": có một ngưỡng tách được nhóm tải vừa (0,3 C ≤ λ ≤ 0,7 C) khỏi nhóm quá tải (λ > C, SLO không đạt), tức max(tín hiệu ở tải vừa) < min(tín hiệu ở quá tải). Kiểm cả bốn tín hiệu của Kiến trúc §10: A1 util, A2 running + waiting, A3 KV-cache, A4 waiting.
- **Cách đo:** `analysis/lt6_gpu_util.py`, mỗi mức λ một dòng ở `analysis/figures/lt6-gpu-util.csv`. Lệnh: `uv run --project analysis python -m analysis.lt6_gpu_util envs/home/experiments/capacity-1.5b.json envs/home/experiments/capacity.json runs/dg1-v2-4060ti/capacity.json --out analysis/figures/lt6-gpu-util.csv`.
  - V2 (thêm 21/11): ĐG1 trên VM 4 × RTX 4060 Ti, Qwen2.5-3B, 1 replica, C = 3,5, λ = 2; 3; 3,5; 4; 5 (0,57–1,43 C), mỗi mức đo 240 s (48 mẫu). Phần `curves` của `runs/dg1-v2-4060ti/capacity.json` trùng bản `envs/cloud/experiments/capacity.json` của PR #52 (hai bản chỉ khác `status`, `note`), nên chạy lại bằng file trong `envs/` cho cùng CSV. Từ 21/11, CSV của LT5, LT6 có thêm cột `session` (trường `session` trong JSON hoặc tên phiên runner; file cũ không ghi session thì là tên file). Script gom phép kiểm, còn hình tô màu, theo cặp (env, session), vì các file ĐG1 ở nhà (0,5B), trên V1 (A4000) và trên V2 cùng tên `capacity.json`. Trước đó script gom theo tên file, và lần chạy đầu ngày 21/11 đã gộp nhầm V2 với 0,5B ở nhà.
  - Dữ liệu là ĐG1-mini ở nhà (RTX 5060, 1 replica, các bậc λ, mỗi bậc đo 120 s). util và `waiting` là trung bình của 24 mẫu Prometheus cách nhau 5 s, do runner tính sẵn (`nvidia_smi_utilization_gpu_ratio`, `vllm:num_requests_waiting`).
  - L lấy B_client: trung bình theo thời gian phía client, không có sai số lấy mẫu.
  - z = (đo − dự đoán) ÷ SE, với SE = √(p(1 − p) ÷ n) nếu các mẫu độc lập; n = 24 ở nhà (120 s), 48 ở V2 (240 s). Thực tế các mẫu có tương quan, vì chu kỳ bận trung bình (e^L − 1) ÷ λ ở 1,5B λ = 1 là 7,5 s, dài hơn bước 5 s, nên SE thật có thể lớn hơn.
- **Số đo, util so với mô hình** (10 mức chưa xếp hàng):

  | Model | λ ÷ C | L | util đo | 1 − e^(−L) | z |
  |---|---|---|---|---|---|
  | 1,5B | 0,17 | 2,0 | 0,895 | 0,865 | +0,4 |
  | 1,5B | 0,33 | 5,3 | 1,000 | 0,995 | +0,3 |
  | 0,5B | 0,16 | 1,9 | 0,780 | 0,844 | −0,9 |
  | 0,5B | 0,32 | 4,1 | 0,958 | 0,983 | −0,9 |
  | 0,5B | 0,48 | 6,1 | 1,000 | 0,998 | +0,2 |
  | 5 mức còn lại | 0,50–0,83 | 8,7–17,8 | 1,000 | ≥ 0,9998 | |
  | 3B (V2), 3 mức | 0,57–1,00 | 16,4–46,7 | 1,000 | > 0,99999 | |

  V2 không có mức nào dưới 0,57 C, nên không thêm điểm nào kiểm được phần cong của 1 − e^(−L): ở mức thấp nhất L đã là 16,4.

- **Số đo, tách tải vừa khỏi quá tải** (khoảng hở = min(quá tải) ÷ max(vừa); lớn hơn 1 thì tách được):

  | Tín hiệu (cấu hình) | 1,5B vừa (λ 2–4) | 1,5B quá tải (λ 7–8) | Khoảng hở | 0,5B vừa (λ 4–8) | 0,5B quá tải (λ 13–14) | Khoảng hở |
  |---|---|---|---|---|---|---|
  | GPU util (A1) | 1,000 | 1,000 | 1,00: **không tách được** | 0,958–1,000 | 0,9996–1,000 | 0,9996: **không tách được** |
  | running + waiting (A2) | 5,3–13,7 | 53,7–124 | 3,9× | 4,3–8,8 | 68–182 | 7,7× |
  | KV-cache (A3) | 0,039–0,099 | 0,228–0,231 | 2,3× | 0,022–0,045 | 0,084–0,085 | 1,9× |
  | waiting (A4) | 0 | 21,8–92,1 | ∞ | 0–0,08 | 52–166 | 630× |

  Bỏ hai mức mà máy tạo tải đánh dấu không hợp lệ (1,5B λ = 6 và 8; script in thêm dòng "chỉ mức hợp lệ") thì cả bốn kết luận và bốn khoảng hở không đổi.

  V2 (3B, C = 3,5; cả 5 mức hợp lệ; dải vừa chỉ có một mức):

  | Tín hiệu (cấu hình) | 3B vừa (λ 2) | 3B quá tải (λ 4–5) | Khoảng hở |
  |---|---|---|---|
  | GPU util (A1) | 1,000 | 1,000 | 1,00: **không tách được** |
  | running + waiting (A2) | 16,4 | 75,9–232 | 4,6× |
  | KV-cache (A3) | 0,062 | 0,240–0,241 | 3,9× |
  | waiting (A4) | 0 | 12,4–168 | ∞ |
- **Số đo, quyết định đầu tiên khi đang có 1 replica** (threshold ở nhà: A1 70 %; A2 21 với 1,5B, 23 với 0,5B):
  - A1 đòi 2 replica ở **cả 18 mức**, từ 0,16 C tới quá tải, vì util ≥ 0,78, tức vượt 77 % = 70 % × 1,1. Ở nhà, exporter chỉ thấy 1 GPU vật lý, nên A1 không lên quá 2.
  - A2 giữ 1 replica khi λ < C, đòi 2 ở λ = C, và 3, 6 ở 1,5B λ = 7, 8; 3, 6, 8 ở 0,5B λ = 13; 13,5; 14.
  - V2 (threshold A2 = 37): A1 đòi 2 replica ở cả 5 mức (util 1,000). A2 giữ 1 ở λ = 2; 3, đòi 2 ở λ = C = 3,5, và 3, 7 ở λ = 4; 5. Cùng quy luật với ở nhà.
- **So với dự đoán:**
  - Định tính đúng. util = 1,000 từ 0,33 C (1,5B) và 0,48 C (0,5B) cho tới quá tải, trong khi `waiting` tăng từ 0 lên 92 và 166. Ở cả hai model, util không tách được tải vừa khỏi quá tải; ở 0,5B, mức quá tải λ = 14 còn có util thấp hơn mức vừa (0,9996 so với 1,000). Ba tín hiệu còn lại đều tách được.
  - Định lượng: ở 5 mức có dự đoán < 0,999, 1 − e^(−L) khớp util đo với |z| < 1 (lớn nhất 0,91). Ở 5 mức chưa xếp hàng còn lại, dự đoán ≥ 0,9998 và số đo là 1,000. Hai mức có |z| lớn nhất cùng thuộc 0,5B và cùng âm (z = −0,86 và −0,91, lệch −0,064 và −0,024), nhưng mỗi mức chưa tới 1 SE, nên chưa kết luận được có lệch hệ thống.
  - V2 (thêm 21/11): util = 1,000 ở cả 5 mức, từ 0,57 C tới 1,43 C, trong khi `waiting` tăng từ 0 lên 168. util lại không tách được tải vừa khỏi quá tải; ba tín hiệu còn lại tách được (A2 4,6×, A3 3,9×, A4 ∞). KV-cache lại đứng yên khi quá tải nặng thêm (0,240 → 0,241 trong khi `waiting` tăng 13,5×), đúng như giải thích 2: `max-num-seqs` = 64 chặn số request chạy.
- **Giải thích:**
  1. **Vì sao bão hoà sớm:** P(N = 0) = e^(−L) giảm theo hàm mũ. Ở 0,33 C (1,5B), L = 5,3, nên GPU chỉ rảnh khoảng 0,5 % thời gian, dù batch trung bình mới bằng 1/5 B\*. util đo "có việc hay không", không đo "bao nhiêu việc".
  2. **KV-cache tách được nhưng không theo được quá tải:** khoảng hở chỉ 1,9–2,3×, và KV đứng yên khi quá tải nặng thêm (0,228 → 0,231 trong khi `waiting` tăng 4×; 0,5B: 0,084 → 0,085). Lý do: vLLM chỉ cấp KV cho request đang chạy, mà số request chạy bị `max-num-seqs` chặn; request trong hàng đợi chưa chiếm KV (LT3: điểm gãy ở nhà do `max-num-seqs`, không do bộ nhớ). A3 vì vậy không biết quá tải nặng tới đâu.
  3. **Hệ quả của mô hình cho A1 (dự đoán, chưa đo):**
     - HPA (threshold 70 %, tolerance 10 %) giữ nguyên số replica khi util mỗi pod nằm trong [63 %; 77 %], tức L mỗi pod trong [0,99; 1,47]. A2 giữ nguyên ở L mỗi pod trong [0,9; 1,1] × threshold, tức 18,9–23,1 với threshold 21.
     - Nếu mỗi pod chạy trên một GPU và Service chia request ngẫu nhiên, mỗi pod là một M/G/∞ với L ÷ N. Khi đó A1 dừng ở L mỗi pod 1,25–1,47, còn A2 dừng ở L mỗi pod cỡ threshold. Ở tổng L = 30–100, nếu không kẹp max, A1 cần 23–71 replica so với 2–5 của A2 (gấp 11–14 lần).
     - Với cùng tải này trên node 4 GPU: A1 lên 3 replica ở 0,32 C (0,5B), lên đủ 4 từ 0,33 C (1,5B) và 0,48 C (0,5B). A2 ở 1 replica cho tới 0,83 C (cột `a1_replicas`, `a2_replicas`).
     - Với N = 4, A1 lên đủ 4 replica khi tổng L > 4,4 (= 3 × 1,47). Nó chỉ bớt pod khi ⌈4 × util ÷ 0,7⌉ ≤ 3, tức util mỗi pod ≤ 52,5 %, hay tổng L ≤ 3,0.
- **Hệ quả:**
  - Con số này lượng hoá dự đoán "A1 gần như Static-4" của [Kiến trúc §10.1](../chi-tiet/03-kien-truc-autoscaling.md#101-a1-gpu-utilization). Nó cũng khớp với V1 (08/11), khi A1 lên 2 replica lúc tải mới khoảng 0,5 C ([log phiên của Quang §13](lam-viec/quang/phien-2026-11-08-a4000.md#13-v1-runner-chạy-2-lượt-đg2-có-keda)).
  - Dự đoán kiểm được ở V2: A1 × KB1 (0,5 C) giữ max replica suốt pha `steady`, nên GPU-giờ của A1 gần bằng S4, nếu L ở 0,5 C trên V2 lớn hơn 4,4 (ở nhà L ở 0,5 C là 8,7, với B\* = 26,8; ở V1, B\* = 52,5).
    - **Kết quả (kiểm 21/11 trên ĐG2 V2, `analysis/figures/v2-dg2/`):** điều kiện thoả, vì L ở KB1 (λ\_thực 1,69–1,84 req/s) là 11,3–12,0 (LT5), lớn hơn 4,4. Ở cả 2 lượt A1-KB1, A1 tạo thêm pod lúc t = 15 s, 91–100 s và 166–181 s; đủ 4 replica Ready lúc t = 246 s và 231 s; rồi giữ 4 tới hết tải (720 s), với 3 lần scale up và 0 lần scale down. Trong pha `steady` (120–720 s), A1 có trung bình 3,66 và 3,73 replica Ready, tức GPU-giây bằng 97–98 % của S4; tính cả lượt là 90–91 % (`gpu_vs_baseline`). Cùng tải, A2 giữ 1 replica (25 % của S4), và SLO của cả ba cấu hình đều đạt 100 %. Dự đoán đúng. Phần hụt so với "suốt pha" chỉ là 111–126 s đầu pha, khi pod thứ 2–4 còn đang khởi động.
- **Lệch so với thiết kế:** Môi trường §19 ghi "một lượt tải tăng dần (0,3 → 1,5 C) ở nhà, đọc từ Prometheus". Trình chưa có quyền vào cluster nhà, nên dùng các bậc λ của ĐG1-mini đã có (0,16–1,33 C với 1,5B, 0,16–1,12 C với 0,5B, mỗi bậc 120 s) và các trung bình mà runner đã tính từ Prometheus. Dữ liệu này đủ cho tiêu chí, vì mỗi nhóm có ít nhất 2 mức đo ở mỗi model.
- **Hình** ([lt6-gpu-util.svg](../../analysis/figures/lt6-gpu-util.svg), vẽ 18/11 từ `lt6-gpu-util.csv` bằng `analysis/lt_charts.py --lt6`): trục hoành λ ÷ C, dải nền là tải vừa. Ô trái là util đo, kèm vạch dự đoán 1 − e^(−L) và mức 77 % mà trên đó A1 thêm pod. Ô phải là running + waiting (thang log), kèm threshold A2 (21; 23). Tiêu đề mỗi ô ghi kết luận tách được hay không, tính bằng cùng hàm `separation` với bảng trên: util không tách được; A2 có khoảng hở 3,9× (1,5B) và 7,7× (0,5B). Vẽ lại 21/11, thêm V2 (màu thứ 4, threshold A2 37): util vẫn không tách được; A2 thêm khoảng hở 4,6× (3B).
- **Còn thiếu:** phần V2 từ lượt A1: so tổng util theo node với số pod đang có request, trên dữ liệu thô (PR sau).

### LT7 – Thuật toán HPA và trễ phản ứng (đo 16/11/2026 trên simulator)

- **Lý thuyết** ([Kiến thức nền §3.1](../chi-tiet/02-kien-thuc-nen.md#31-thuật-toán-hpa)): với metric External kiểu `AverageValue`, HPA giữ nguyên số replica nếu tổng ÷ (target × số replica) nằm trong [0,9; 1,1], ngược lại desired = ⌈tổng ÷ target⌉, rồi kẹp vào [min, max]. Trễ quyết định gồm thời gian chờ lần scrape kế tiếp và thời gian chờ lần sync HPA kế tiếp.
- **Dự đoán:**
  - Threshold 10, max 3: C = 5, 15, 25, 35 request đồng thời → 1, 2, 3, 3 replica (⌈3,5⌉ = 4 bị kẹp ở max).
  - Môi trường §19 ghi ≤ ~15 s (scrape 5 s + polling 5 s + sync 5 s). Trước khi đo, Trình sửa lại thành < 10 s: khi `minReplicaCount` ≥ 1, KEDA chạy câu PromQL ngay lúc HPA hỏi, nên `pollingInterval` không nằm trên đường này (KEDA v2.21.0 in cảnh báo này khi áp ScaledObject).
- **Cách đo:** `make sim-lt7` (`envs/sim/tests/lt7-hpa.sh`), kind trong WSL2, Kubernetes v1.37.0, KEDA v2.21.0. Mỗi lượt reset về 1 replica bằng `paused-replicas` (KEDA tạo HPA mới), rồi bơm C request đồng thời trong 60 s bằng hey. Các mốc lấy được: lúc hey bắt đầu (ms), mẫu Prometheus thô (ms), dòng "Successfully rescaled" trong log kube-controller-manager (µs), mốc của pod (giây). Giờ thực của WSL2 bị kéo lùi 0,5–1,3 s khoảng mỗi 32 s, nên mọi mốc được đổi sang đồng hồ đơn điệu nhờ các dòng "Clock change detected" trong journal. Bảng tính bằng `analysis/lt7_hpa.py`, mỗi lượt một dòng ở `analysis/figures/lt7-hpa.csv` (phiên 2).
- **Số đo, số replica:** 24/24 lượt (2 phiên × 4 mức × 3 lần) đúng dự đoán. C = 5 thì không đổi; 15 → 2; 25 → 3; 35 → 3. Mỗi lượt có scale thì scale đúng một lần, không lên thêm, không dao động trong 60 s. Cuối mỗi lượt, metric HPA thấy nhân số replica bằng C (15,0; 25,0; 35,0).
- **Số đo, trễ** (phiên 2, có lệch pha ngẫu nhiên, 7 lượt scale-up; giây, theo đồng hồ đơn điệu):

  | Chặng | Dự đoán | min | TB | max |
  |---|---|---|---|---|
  | tải tới → lần scrape đầu thấy tải | [0; 5) | 0,88 | 3,29 | 5,02 |
  | scrape → KEDA thấy mẫu (giây tròn kế tiếp) | không có trong dự đoán | 0,45 | 0,60 | 0,79 |
  | KEDA thấy mẫu → HPA đổi replica | [0; 5) + thời gian xử lý | 0,11 | 3,02 | 4,76 |
  | **tải tới → HPA đổi replica** | **< 10** | **3,61** | **6,91** | **10,21** |
  | HPA đổi → pod mới Ready (±1 s) | ≈ 5 (một chu kỳ startupProbe) | 5 | 5,98 | 7 |

  Ở cả 18 lượt có scale-up của hai phiên, pod mới được tạo ngay trong giây HPA đổi replica. Phiên 1 (8 lượt, chưa lệch pha) nằm trong cùng các cận, với thời gian quyết định 3,11–8,83 s. 7 mẫu T2 trước đó (`make sim-test`, 01/11–07/11, đo theo đồng hồ đơn điệu, tới giây) là 1, 6, 8, 8, 9, 4, 5 s.
- **Lệch và giải thích:**
  - 10,21 s vượt dự đoán < 10 s. Nguyên nhân là một chặng không có trong dự đoán: KEDA hỏi Prometheus với `time=` làm tròn xuống giây (`time.Now().UTC().Format(time.RFC3339)`, `pkg/scalers/prometheus_scaler.go:224` ở v2.21.0). Vì thế mẫu scrape lúc x,138 s chỉ được thấy từ giây x + 1, và cận trên đúng là 5 + 1 + 5 = 11 s. Chặng này lộ ra ở lượt đo thử đầu tiên: từ scrape tới lúc HPA đổi replica mất 5,29 s, dài hơn một chu kỳ sync. Ở cả 15 lượt tính được, chặng "KEDA thấy mẫu → HPA đổi replica" đều dưới 5 s (lớn nhất 4,81 s).
  - Thời gian xử lý trong chu kỳ sync rất nhỏ. KEDA trả metric trung bình trong 4,2 ms (199 lần, theo metric gRPC của keda-operator). Mỗi lần HPA xử lý mất trung bình 20 ms, và 37 ms khi có scale-up (`horizontal_pod_autoscaler_controller_reconciliation_duration_seconds`, cộng dồn từ 16:18 tới 16:53). HPA hẹn lần sync kế tiếp 5 s kể từ lúc lần trước xử lý xong (`AddRateLimited`, `horizontal.go` ở v1.37.0).
  - d_scrape = 5,02 s, lớn hơn chu kỳ scrape: lần scrape lúc +0,015 s chưa thấy request nào, vì request đầu tiên cần vài chục ms mới qua được port-forward. Lần scrape kế tiếp, lúc +5,016 s, mới thấy đủ 25.
  - Phiên 1 chưa có lệch pha. Reset tạo HPA mới, HPA sync ngay khi được tạo, và script bơm tải sau reset một khoảng gần như cố định, nên thời gian quyết định chỉ rơi vào hai cụm, quanh 3–4 s hoặc 8–9 s. Phiên 2 thêm một khoảng chờ ngẫu nhiên trong [0; 5) s trước khi bơm tải.
  - Nếu đo bằng giờ thực thì những lượt có bước lùi đồng hồ sai tới 1,3 s (ví dụ phiên 2, C = 25 lần 2: ngắn đi 0,90 s). Sau khi đổi sang đồng hồ đơn điệu, khoảng cách giữa hai lần scrape liền nhau chỉ lệch tối đa 2 ms so với 5 s; theo giờ thực thì lệch tới 1301 ms. Có 3/18 lượt scale-up có mốc rơi đúng vào khoảng giờ thực bị lặp lại ngay sau một bước lùi, không đổi chắc chắn được, nên không tính vào bảng trễ.
- **Hệ quả cho V2:** trên cloud (k3s, cùng scrape 5 s, sync 5 s, KEDA v2.21.0), HPA quyết định trong < 11 s sau khi tải tăng. Phần lớn thời gian của N2a (≤ 180 s) vì vậy là cold start của pod vLLM, không phải độ trễ của autoscaler.

### LT8 – Cảnh báo theo burn rate (đo 16/11/2026 trên simulator)

- **Lý thuyết** ([Kiến thức nền §5.2](../chi-tiet/02-kien-thuc-nen.md#52-cảnh-báo-theo-tốc-độ-tiêu-hao-burn-rate)): `LLMSLOBurnFast` chuyển sang pending khi tỷ lệ request có TTFT > 2,5 s vượt θ = 4 × 5 % = 0,2 trên **cả** cửa sổ 5 phút và 1 phút (`llm:ttft_bad_ratio:rate5m`, `:rate1m`), và sang firing nếu điều kiện đúng liên tục suốt `for: 1m`. Sau bước nhảy từ 0 lên tỷ lệ xấu x, với λ không đổi và ít nhất 5 phút nền sạch trước đó, tỷ lệ trên cửa sổ w là r_w(τ) = x · min(τ, w) / w.
- **Dự đoán** (công thức và giả thiết ở docstring `analysis/lt8_burn.py`):
  - x ≤ 0,2: r_5m không bao giờ vượt θ, nên cảnh báo không kêu dù lỗi kéo dài bao lâu.
  - x > 0,2: điều kiện đúng sau θ · 300 / x (cửa sổ 5m là chặng chậm), firing sau θ · 300 / x + 60 s. x = 0,3 → 200 s và 260 s; x = 0,6 → 100 s và 160 s.
  - Sau khi gỡ lỗi, điều kiện sai khi cửa sổ **ngắn** xuống dưới θ: 60 · (1 − θ / x) = 20 s (x = 0,3) và 40 s (x = 0,6). Nếu chỉ có cửa sổ 5m thì cảnh báo còn kêu tới 300 · (1 − θ / x) = 100 s và 200 s.
  - N7 tính từ lúc SLO bị vi phạm thật theo log client (cửa sổ 1 phút vượt θ, sau θ · 60 / x) tới lúc firing: θ · 240 / x + 60 s = 220 s (x = 0,3) và 140 s (x = 0,6). Mốc này luôn < 300 s khi x > θ, nhưng tiến tới 300 s khi x → 0,2.
  - Các trễ không có trong công thức, dự kiến tổng dưới khoảng 30 s: request xấu chỉ được đếm khi có token đầu (khoảng μ, 2–3 s, sau khi gửi); chờ lần scrape kế tiếp (≤ 5 s); recording rule và alerting rule tính ở hai nhóm riêng, mỗi nhóm 15 s, nên mọi mốc chỉ chính xác tới 15 s.
- **Cách đo:** `make sim-lt8` (`experiments/ops/lt8_burn.py`), kind trong WSL2, simulator llm-d-inference-sim v0.12.0, KEDA tạm dừng ở 1 replica (LT8 kiểm cảnh báo, không kiểm scale). Máy tạo tải chạy thành Job trong cluster, tốc độ cố định 2 req/s. Tỷ lệ xấu x được tạo bằng cách đổi TTFT của simulator ngay lúc chạy (`POST /admin/config`): TTFT ~ N(μ, σ = 0,3 μ), μ chọn để P(TTFT > 2,5 s) = x, nên x = 0,1/0,3/0,6 ứng với μ = 1806/2160/2706 ms (D64). Mỗi lượt: nền 330 s (TTFT 200 ms) → bơm một mức 360 s → nền 330 s → mức kế tiếp … → nền cuối. 3 mức × 3 lượt, thứ tự mức xoay vòng nên mỗi mức đứng đầu, giữa, cuối đúng một lần. Ghi lại mốc bơm và gỡ, `requests.csv`, và mẫu Prometheus thô (`ALERTS`, hai recording rule, bộ đếm histogram TTFT). Bảng tính bằng `analysis/lt8_burn.py`, mỗi lần bơm một dòng ở `analysis/figures/lt8-burn.csv` (phiên `runs/sim/lt8-20261116-131116`).
- **Số đo:** 9/9 lần bơm hợp lệ (nền sạch trước mỗi lần bơm 322–331 s, 0 restart, 0 request lỗi). Giá trị dạng min–max (TB), dự đoán trong ngoặc; thời gian tính từ lúc bơm, riêng cột "điều kiện sai" tính từ lúc gỡ (giây).

  | x | x client | x server | điều kiện đúng | firing | điều kiện sai | N7: vi phạm → firing | page giả |
  |---|---|---|---|---|---|---|---|
  | 0,1 | 0,095–0,131 (0,100) | 0,097–0,126 | không lần nào (không) | không kêu, 0 lần pending (không) | – | – | 0 |
  | 0,3 | 0,303–0,324 (0,300) | 0,300–0,315 | 183–220, TB 201 (200) | 249–286, TB 267 (260) | 21–34, TB 27 (20) | 215–242, TB 233 (220) | 0 |
  | 0,6 | 0,581–0,620 (0,600) | 0,572–0,612 | 108–125, TB 116 (100) | 173–190, TB 181 (160) | 48–55, TB 52 (40) | 159–163, TB 161 (140) | 0 |

  - Ở cả 6 lần có cảnh báo: pending → firing đúng 60,0 s, cảnh báo kêu đúng một đợt, không lần nào pending rồi bị đặt lại. Từ lúc điều kiện đúng (nhóm recording rule) tới lúc pending (nhóm cảnh báo) luôn là 5,5 s.
  - Mọi lần x > 0,2 đều đạt N7 (≤ 300 s), với khoảng dư nhỏ nhất 58 s (x = 0,3).
- **Lệch và giải thích:**
  - Lý thuyết đúng về mặt định tính: dưới θ thì im lặng, trên θ thì kêu, và x càng lớn thì kêu càng sớm, hết càng muộn. Hết cảnh báo đúng là nhờ cửa sổ 1 phút: 27 s và 52 s, so với 100 s và 200 s nếu chỉ dùng cửa sổ 5m.
  - Firing muộn hơn dự đoán trung bình 6 s (x = 0,3) và 21 s (x = 0,6). Phần trễ dương này khớp với các trễ không có trong công thức: token đầu của request xấu ra sau khoảng μ (2,2–2,7 s), chờ scrape (≤ 5 s), mốc chỉ thấy được ở lần tính rule kế tiếp (≤ 15 s). Hết cảnh báo cũng muộn hơn 7–12 s trung bình, vì cùng lý do.
  - Ở x = 0,3 có một lần kêu **sớm** hơn dự đoán 11 s. Lần đó x client = 0,324, nên θ · 300 / 0,324 = 185 s, khớp mốc điều kiện đúng đo được (183 s). Ở x = 0,3, r_5m tăng chậm (x / 300 = 0,001 mỗi giây), nên nhiễu thống kê của r_5m (độ lệch chuẩn khoảng 0,016 với khoảng 600 request trong cửa sổ) làm lúc vượt θ xê dịch cỡ ±16 s. Ở x = 0,6 con số này chỉ khoảng ±8 s, nên ở đó cả 3 lần đều muộn.
  - x server thấp hơn x client ở 8/9 lần, tối đa 0,009: server chỉ đếm request đã có token đầu trước lúc gỡ, nên hụt vài request xấu gửi ngay trước đó.
  - Mốc vi phạm theo log client (24–44 s và 14–27 s, dự đoán 40 s và 20 s) dao động mạnh hơn, vì cửa sổ 1 phút chỉ có khoảng 120 request.
- **Hệ quả cho V2 (VH6):** mức 5 phút của N7 vừa khít với cửa sổ 5m. Theo công thức, cộng thêm khoảng 30 s trễ như đo ở trên, N7 chỉ chắc giữ được khi x ≳ 0,23 (θ · 240 / x + 60 + 30 = 300 ⇔ x ≈ 0,229; tính từ công thức, chưa đo). Với x trong khoảng 0,2–0,23, thời gian từ lúc vi phạm tới page có thể vượt 5 phút. Đó là đánh đổi có chủ đích của burn rate 4: đổi lấy việc không page khi lỗi dưới 20 %.

## 2026-11-08 – Phiên thử VM Vast đầu tiên (2 × RTX 5060 Ti): bootstrap, mạng, cold start 3B

- **Máy:** Vast VM 2 × RTX 5060 Ti 16 GB, **unverified**, host đặt ở Trung Quốc (thuê qua web UI, không qua `vast.sh`); Xeon E5-2683 v4, VM nhận 30 vCPU, 61 GB RAM (quảng cáo 80 GB), ổ 130 GB; driver ban đầu 580.95, Max CUDA 13.0.
- **Bootstrap:** inventory viết tay theo mẫu `vast.sh inventory`; `ansible-playbook site.yml` xong trong **239 s**, 0 lỗi. Device plugin 0.20.1 (helm) → node `nvidia.com/gpu: 2`; pod `nvidia-smi` chạy được. `fio` đọc tuần tự 2918 MiB/s (có thể nhờ cache của host).
- **Mạng:** `registry-1.docker.io` bị reset kết nối; `ghcr.io`, `quay.io`, `registry.k8s.io`, Hugging Face, GitHub thông. Sửa bằng registry mirror `mirror.gcr.io` (có đúng digest vLLM đã ghim). Trần băng thông thực **~8 MB/s** dù quảng cáo 885 Mbps: HF 1 kết nối 5 MB/s, 16 kết nối 8 MB/s, ModelScope 7 MB/s, `mirror.gcr.io` 8 MB/s; DaoCloud lỗi xác thực. Kéo image vLLM 9,04 GB mất **24 phút 22 giây**; tải model 3B (5,75 GiB) mất **690 s**.
- **Sự cố 1 – SSH tunnel tới API server đứt khi nhận phản hồi lớn** (tải OpenAPI ~2,8 MB) → dùng `helm --disable-openapi-validation`, `kubectl --validate=false`, và chạy lệnh dài ngay trên VM (`k3s kubectl`), mỗi lần kiểm là một phiên SSH ngắn.
- **Sự cố 2 – NVML mismatch:** `unattended-upgrades` nâng cả hệ thống (~260 gói, ~55 phút), gồm thư viện driver 580.95 → 580.178 khi module kernel 580.95 vẫn nạp → mọi container GPU lỗi `failed to initialize NVML: Driver/library version mismatch` (pod vLLM `StartError`). Chờ nâng cấp xong rồi reboot (VM lên lại sau ~35 s, driver 580.178), tắt `unattended-upgrades` và timer apt, `apt-mark hold` 21 gói driver. Lỗi của Claude: reboot khi `unattended-upgrade` còn giữ khoá dpkg (mẫu `pgrep` sai); sau reboot `dpkg --audit` sạch.
- **Sự cố 3 – `hf_xet` treo** ở 1,71 / 3,97 GB khi kết nối đứt, không tự nối lại → tải lại bằng HTTP (`HF_HUB_DISABLE_XET=1`), phần đã tải bằng xet không dùng lại được.
- **Cold start vLLM 0.31.0, Qwen2.5-3B, 1 GPU, 3 CPU** (image, model đã có trên ổ; tính từ lúc tạo pod tới Ready):

  | Lần | Cấu hình | Ready | Ghi chú |
  |---|---|---|---|
  | 1 | gốc, compile lần đầu | 412 s | nạp weights 12 s, compile 32 s, CUDA graph capture 127 + 121 s |
  | 2 | gốc, có compile cache | 363 s | compile 1,6 s, capture 131 + 120 s |
  | 3 | gốc, 8 CPU | 360 s | CPU nhiều hơn không giúp |
  | 4–5 | `cudagraph_mode: PIECEWISE`, capture [1, 2, 4, 8, 16, 32, 64] | 262 s / 231 s | capture 55 + 2 s; còn ~70 s không có log sau capture đầu |
  | 6 | thêm `--no-enable-flashinfer-autotune` | 231 s | không đổi |
  | 7 | thêm `VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0` | 272 s | mất compile cache, không giúp |
  | 8 | gốc (đo lại trước benchmark) | 377 s | |

- **Benchmark** (`vllm bench serve`, input 512, output 256, `--ignore-eos`, seed 1; trong pod):

  | Đồng thời | TPOT TB gốc | TPOT TB PIECEWISE | Throughput gốc | Throughput PIECEWISE |
  |---|---|---|---|---|
  | 1 | 15,9 ms | 23,0 ms | 62 tok/s | 26 tok/s |
  | 16 | 18,8 ms | 24,8 ms | 747 tok/s | 584 tok/s |
  | 32 | 22,2 ms | 29,4 ms | 1195 tok/s | 953 tok/s |

  Lượt PIECEWISE ở đồng thời 1 không làm nóng trước (một request đầu TTFT 82 s), các mức còn lại có làm nóng ở lượt gốc. Kết luận: **giữ cấu hình gốc**; PIECEWISE nhanh hơn ~2 phút lúc khởi động nhưng chậm hơn 20–45%. Nghi CPU đơn luồng yếu (E5 đời 2016) làm chậm cả capture lẫn chế độ PIECEWISE.
- **API:** gọi được `/v1/chat/completions` với khoá, không khoá → 401. KV cache 208.000 token, Maximum concurrency 25,4 × ở 8192 token.
- **Chưa làm:** Prometheus, KEDA, runner, `make bootstrap` trọn bằng `vast.sh`; chưa đo chi phí thực tế của phiên (xem trên console Vast).

## 2026-11-08 – VM Vast thứ hai (4 × RTX A4000): bootstrap trọn, cold start 3B, scale 1 → 4

- **Chọn máy:** 2 VM ứng viên, chạy cùng một script kiểm tra nhanh (GPU, PCIe, CPU, RAM, ổ, tải HF thật, Docker Hub). Máy thứ nhất mở cổng SSH nhưng timeout lúc banner exchange cả 2 lần → huỷ. Giữ máy thứ hai.
- **Máy:** Vast VM 4 × RTX A4000 16 GB, PCIe Gen3 x16 cả 4 GPU, driver 580.95.05 (CUDA 13.0); Xeon E5-2620 v4 2,1 GHz, 15 vCPU, 98 GB RAM, ổ 126 GB (ghi 599 MB/s); đặt ở Séc. Docker Hub thông trực tiếp; tải từ Hugging Face 1 kết nối **93,9 MB/s**.
- **Thời gian dựng (UTC, từ lúc VM boot ~12:34):**

  | Bước | Thời gian | Máy 08/11 trước (2 × 5060 Ti) |
  |---|---|---|
  | Tải model 3B (5,8 GB, `HF_HUB_DISABLE_XET=1`), chạy song song bootstrap | 27 s | 690 s |
  | `ansible-playbook site.yml` (ok=30, changed=12, failed=0) | 164 s | 239 s |
  | Kéo image vLLM 9,04 GB qua `mirror.gcr.io`, bắt đầu ngay khi k3s lên | 413 s | 24 min 22 s |
  | Cài nền trên VM bằng helm: device plugin, kube-prometheus-stack, KEDA, GPU exporter (song song kéo image) | 236 s | cài tay |

  Từ lúc bắt đầu bootstrap tới pod vLLM đầu tiên Ready: 12:40:56 → 12:53:17 ≈ **12,5 phút** (N6 ≤ 30 phút: đạt trên máy này, chưa tính thời gian thuê và chờ VM boot).
- **Sự cố 1 – task Ansible "Chờ lượt nâng cấp" kẹt:** `pgrep -f '/usr/bin/unattended-upgrade'` khớp chính dòng lệnh của shell đang chạy task, nên luôn thấy "đang chạy". Thực tế `unattended-upgrade` đã tự dừng lúc 12:36:54 (lỗi 404 khi tải gói, 0 gói được nâng, driver nguyên). Sửa mẫu thành `'[/]usr/bin/unattended-upgrade'`, chạy lại playbook.
- **Sự cố 2 – GPU exporter lỗi `namespaces "gpu" not found`:** ở nhà Argo CD tạo namespace; khi cài tay phải tạo trước.
- **CPU:** 15 vCPU − `reserved-cpus=0-3` = 11 lõi allocatable < 4 pod × 3 lõi. Dùng overlay tạm (không commit) hạ request/limit vLLM xuống **2 lõi**/pod.
- **Cold start vLLM 0.31.0, Qwen2.5-3B, 1 GPU, 2 CPU** (image và model có sẵn; từ lúc tạo pod tới Ready):

  | Lần | Điều kiện | Ready | Chi tiết |
  |---|---|---|---|
  | 1 | chưa có compile cache | 152 s | import Python ~39 s, init ~31 s, nạp weights 11 s, compile 27,4 s, CUDA graph capture 4 + 4 s |
  | 2 | có compile cache | 108 s | compile 2,0 s, capture 4 + 4 s |
  | 3 | scale 1 → 4, 3 pod khởi động đồng thời | 117 / 121 / 122 s | |

  Capture CUDA graph ở máy trước mất 127 + 121 s, ở máy này 4 + 4 s, dù cả hai đều là Xeon E5 v4 đời 2016. Giả thuyết "CPU yếu làm chậm capture" (ghi ở mục trước) **không đúng** cho máy này; nguyên nhân ở máy trước chưa rõ.
  KV cache 7,28 GiB = 211.936 token (Maximum concurrency 25,87× ở 8192 token); VRAM mỗi GPU khi chạy 14.416 MiB.
- **Benchmark** (`vllm bench serve`, cùng tham số mục trước, thêm mức 64; trong 1 pod, 2 CPU):

  | Đồng thời | TPOT TB | P99 TPOT | TTFT TB | P99 TTFT | Throughput |
  |---|---|---|---|---|---|
  | 1 | 17,2 ms | 17,3 ms | 97 ms | 104 ms | 57 tok/s |
  | 16 | 21,3 ms | 23,2 ms | 632 ms | 1014 ms | 675 tok/s |
  | 32 | 25,1 ms | 27,9 ms | 892 ms | 1977 ms | 1121 tok/s |
  | 64 | 36,2 ms | 40,4 ms | 1243 ms | 3980 ms | 1562 tok/s |

  Chậm hơn máy 5060 Ti 6–13 % (cùng ~448 GB/s). Chưa tách được do kiến trúc GPU hay do 2 CPU thay vì 3.
- **Chưa làm:** ĐG1 (đo C), runner, A1–A3; so 2 CPU với 3 CPU; chi phí thực tế của phiên.

## 2026-11-08 – ĐG1 thử và V1 trên VM 4 × RTX A4000

- **Runner** chạy từ laptop qua SSH tunnel tới API server (tunnel máy này chịu được 7 MB OpenAPI). Chi tiết từng bước: [phien-2026-11-08-a4000.md](lam-viec/quang/phien-2026-11-08-a4000.md).
- **ĐG1 thử** (`experiments/matrix-dg1-v1.yaml`, S1, CONST, mỗi mức 300 s, đo 240 s): λ = 2 / 4 / 4,5 / 5 / 6 → SLO 100 / 100 / 99,1 / 6,3 / 0 %. **C = 4,5 req/s, B\* = 52,5, ngưỡng A2 = 42**, KV\* 18,5 %. Giới hạn là hàng đợi (`max-num-seqs` 64), TPOT p95 ~53 ms. Little khớp trong 1 % ở các mức ổn định. Dừng sớm 2 lần (bỏ 8, 10, 5,5), tiết kiệm ~22 phút. Lỗi đo: `UTIL_star` = 0,25 do `capacity.py` lấy trung bình trên cả 4 GPU của node.
- **V1** (`experiments/matrix-v1.yaml`: A1 × KB3, A2 × KB2, C = 4,5, N = 4): runner chạy 2 lượt liền, không can thiệp, 60 phút. Cả hai `invalid` vì máy tạo tải 2 lõi vượt ngưỡng CPU 70 % (72,8 % và 74,9 %); lịch gửi vẫn chính xác.
  - A1 × KB3: SLO `ramp` 88,6 %, `sustain` 99,9 %; scale 1→2→3→4 mỗi 120 s; sau tải **kẹt ở 2 replica**: một mẫu GPU util 100 % của pod đang tắt + truy vấn `sum` mọi GPU của node + cửa sổ 300 s → runner phải ép về 1.
  - A2 × KB2: SLO `pre` 100 %, `spike` **62,7 %** (855 timeout), `drop` 100 %; desired lên 4 sau 43 s, đủ 4 Ready sau ~2 phút 43 giây; scale-down 4→3→2→1 đúng 300 s + 60 s/pod. Hàng đợi 1.028 request **ghim ở pod cũ**, 3 pod mới không có request chờ; xả hết sau ~9 phút.
- **Chi phí:** giá máy (Vast, Price Breakdown) **$0,611/giờ** = GPU on-demand $0,587 + ổ 130 GB $0,025 ($14,66/ngày). Thời gian thuê ~12:30 → ~15:00 UTC ≈ 2,5 giờ → **≈ $1,5** (ước tính theo giờ, chưa đối chiếu hoá đơn). Nếu V2 (~20–22 giờ) chạy trên máy cùng giá: ≈ $12–13,5; nhưng máy này chỉ 15 vCPU, không đủ cho máy tạo tải 3 lõi (lượt invalid).

## 2026-11-09 – Chạy thử script VH2–VH4 trên simulator (kind)

- **Môi trường:** kind `llm-sim`, 3 node, `llm-d-inference-sim`, không có GPU. Chỉ kiểm logic script; **không phải kết quả VH chính thức**.
- **Số đo:** vh4 fallback 18,8 s; vh3-drain hồi phục 22,1 s; vh3-delete pod thay 10,1 s; vh2a rollout 12,5 s; vh2b rollout 16,6 s. Cả năm ca 0 request lỗi.
- **Chưa kiểm:** vh2c (simulator không giới hạn GPU nên không kẹt), vh3-kill (simulator không có tiến trình con).
- **Chi phí:** không thuê máy.
- **Chi tiết:** [nhật ký Quang tuần 06](lam-viec/quang/tuan-06.md).

## 2026-11-16 – Cluster nhà: Argo CD mất đồng bộ sau refactor, image vLLM bị mất, LT4

- **Môi trường:** PC nhà (RTX 5060, 2 GPU replica time-slicing), Qwen2.5-0.5B, vLLM 0.31.0. Không thuê máy.
- **Sự cố 1 – Argo CD `Unknown`:** cả 7 Application Sync `Unknown` vì `root-home` còn trỏ đường dẫn cũ `platform/argocd/apps/home` (đổi ở PR #34). Sửa: `kubectl apply -f envs/home/argocd/root-app.yaml`; dưới 3 phút cả 7 app `Synced`/`Healthy`. Sau đó áp tiếp bản root-app của PR #39 (thêm `ignoreDifferences`), cluster không đổi gì khác.
- **Sự cố 2 – image vLLM không còn trên node:** scale 0 → 1 phải kéo lại image, mất 14 phút 52 giây; runner hết 900 s chờ, lượt đầu invalid (123/357 request lỗi kết nối trong 68 s đầu). Nguyên nhân mất image chưa xác định; nghi kubelet image GC (đĩa `/` 80 %, ngưỡng mặc định 85 %, vLLM đang ở 0 replica nên image không được giữ). **Hệ quả vận hành:** trước một phiên ở nhà, scale lên 1 pod và chờ Ready trước khi chạy runner; giữ đĩa dưới 85 %.
- **Số đo:** lượt runner hợp lệ (S1, 2 req/s × 180 s): 357 request, 0 lỗi, TTFT p50 30 ms / p95 40 ms, TPOT p50 3,7 ms. Cold start khi image đã có: 155–162 s từ lúc container chạy tới Ready (bảng ở mục LT4).
- **Quan sát:** thay pod thì hai pod cùng tồn tại khoảng 3 phút (pod cũ ở `Terminating` tới hết grace period 180 s, tức không thoát khi nhận SIGTERM, giống 06/11); RAM khả dụng còn 2,7 GB, swap 4,3 GB, không OOM. Một pod dùng 3.644 Mi RAM.
- **Chưa làm:** VH1–VH4 trên GPU nhà (cần 2 replica dưới tải, RAM không đủ khi desktop đang mở); kiểm sau merge của PR #39.
- **Trạng thái cuối:** vLLM 0 replica, 7 app `Synced`/`Healthy`, không có ScaledObject.
- **Chi phí:** không thuê máy.
- **Chi tiết:** [nhật ký Quang tuần 07](lam-viec/quang/tuan-07.md).

## 2026-11-16 – Máy thuê: 4 máy thử, phiên thử code trên 2 × RTX 4000 Ada (N = 2)

- **Môi trường:** Vast, chế độ VM, thuê qua giao diện web. Không phải phiên đo chính thức; không sao lưu R2 (PC chưa có `.env`).
- **Máy 1 (4 × RTX 5060 Ti, Trung Quốc):** SSH được, nhưng Docker Hub, `huggingface.co`, `github.com`, `get.k3s.io`, PyPI bị chặn; chưa cài gì, đã tắt.
- **Máy 2 và 3 (2 GPU):** không lên SSH (một máy mở cổng nhưng không trả banner, một máy timeout TCP); đã tắt.
- **Máy 4 (2 × RTX 4000 Ada 20 GB, Hungary, 11 vCPU, 49 GB RAM):** `probe` đạt trừ CPU (11 < 14). `bootstrap` 9 phút 12 giây, `cloud-platform` 99 s, vLLM 3B Ready sau 90 s; từ máy trắng tới vLLM Ready 12 phút 54 giây.
- **Số đo:** ĐG1 rút gọn (4 mức, 180 s đo mỗi mức): C = 5,0 req/s (sơ bộ), B\* = 48,9, threshold A2 = 39. Cold start 3B: nạp weights 1,48 s, `torch.compile` 17,2 s, chụp CUDA graph lúc profiling 2 s.
- **Kết quả các lượt autoscaling và VH trên máy này:** xem các mục sau trong [nhật ký Quang tuần 07](lam-viec/quang/tuan-07.md).
- **Chi phí:** chưa ghi (máy thuê qua web, offer cùng loại ở Hungary lúc tra là 0,455 USD/giờ; số thực lấy từ trang Vast khi trả máy).


## 2026-11-16 – VH3, VH4, VH2a chạy thử trên máy thuê 2 × RTX 4000 Ada (N = 2)

Chạy bằng `experiments.ops.vh`, tải CONST 2,5 req/s, A2 threshold 39, Qwen2.5-3B. Mục đích là kiểm script trên GPU thật, chưa phải số chính thức.

| Kịch bản | Chấm | Request / lỗi | Số đo |
|---|---|---|---|
| vh3-delete | không đạt | 1.942 / 90 | pod thay thế Ready sau 61,3 s |
| vh3-kill | đạt | 1.481 / 168 | container restart, Ready lại sau 69,4 s |
| vh4 | đạt | 1.771 / 0 | fallback sau 17,2 s kể từ lúc chặn Prometheus |
| vh2a | đạt | 2.948 / 0 | rolling update 2 pod: 181,6 s |

- **vh3-delete không đạt vì điều kiện chạy, không phải vì hệ thống:** tải thấp nên chỉ có 1 pod; xoá pod duy nhất thì 61 s không có ai phục vụ. Lần chính thức phải có ≥ 2 pod Ready trước khi xoá.
- **vh2a:** thời gian rolling update gần bằng grace period 180 s, do vLLM không dừng khi nhận SIGTERM (xem mục 06/11).
- Chưa chạy: vh2b, vh2c, vh3-drain (drain cần ≥ 2 node).

## 2026-11-18 – V2 trên VM 4 × RTX 4060 Ti: dựng cluster, ĐG1 chính thức, bắt đầu ma trận

- **Môi trường:** Vast, chế độ VM, thuê qua giao diện web, Canada; 4 × RTX 4060 Ti 16 GB, 61 vCPU, 197 GB RAM; Qwen2.5-3B, vLLM 0.31.0, N = 4.
- **Máy bỏ:** 4 × RTX 4090 (1,5 USD/giờ): cổng SSH timeout khoảng 15 phút, không cài được gì.
- **Dựng:** `bootstrap` 5 phút 8 giây (0 failed), `cloud-platform` 82 s, vLLM Ready sau 90 s; từ máy trắng tới vLLM Ready 8 phút 22 giây.
- **ĐG1:** 5 mức λ, đều hợp lệ → C = 3,5 req/s, B\* = 46,3, threshold A2 = 37. Bảng ở [nhật ký Quang tuần 07](lam-viec/quang/tuan-07.md).
- **Ma trận ĐG2:** 17 lượt chạy bằng runner trong tmux trên VM, `--no-backup`, 16:30 → 23:44; **17/17 hợp lệ**. A2 × KB2 chỉ đạt SLO khoảng 80 % (phản ứng 80–82 s); các ô khác của A1, A2, S4 đạt 100 %. Bảng ở [nhật ký Quang tuần 07](lam-viec/quang/tuan-07.md).
- **Chi phí:** 1,5 USD/giờ cả máy (Quang báo theo trang Vast). Ước tính: ĐG1 + ma trận khoảng 9–10 giờ ≈ 14–15 USD; cộng ĐG3, VH trong cùng lần thuê. Số thực ghi khi trả máy.

## 2026-11-19 – V2: ĐG3, VH2–VH4 trên N = 4, trả máy

- **ĐG3:** L2 = 76 / 76 / 81 s, L0 = 311 / 300 s (L0 đo 0 → 1 vì containerd không xoá được image đang dùng). 3 lượt đầu hỏng do lỗi `wait_count` trong `dg3.sh`, đã sửa và đo lại.
- **VH (1,75 req/s):** vh2a, vh2b (371,6 s), vh2c (kẹt có pod Pending), vh3-delete (67,4 s, 0 lỗi), vh4 (fallback 16,8 s) đạt, 0 lỗi. vh3-kill: restart 67,4 s nhưng 129 lỗi, khả năng cao do chỉ có 1 pod lúc kill.
- **Trả máy:** VM `poweroff` 02:05 ngày 19/11 sau khi kiểm sha256 mọi file; Quang xoá instance trên Vast ngày 19/11. Chi phí thực tế: chưa có.
- Chi tiết ở [nhật ký Quang tuần 07](lam-viec/quang/tuan-07.md).

## 2026-11-24 – kind `llm-sim`: thêm rồi gỡ Argo CD (chuẩn bị VH2 qua Git)

- **Môi trường:** kind `llm-sim` trên laptop của Trình (WSL2), không đụng cluster nhà hay máy thuê.
- **Thao tác:** `make sim-argocd` (Argo CD core `v3.5.4`, app `serving`, `autoscaling` theo `main`) 142 s tới `Synced Healthy`; self-heal đưa sửa tay về Git sau 2 s; gỡ theo `envs/sim/README.md` 13 s. Simulator và A2 chạy suốt, không tạo lại pod.
- **Trạng thái sau:** không còn Argo CD trên kind. VH2 (commit, sync, `git revert` dưới tải) làm ở bước sau. Chi tiết ở [nhật ký Trình tuần 08](lam-viec/trinh/tuan-08.md).
