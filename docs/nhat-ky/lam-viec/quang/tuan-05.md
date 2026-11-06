# Nhật ký làm việc – Quang – Tuần 05 (02–08/11)

## 2026-11-02 – Sửa k3s crash liên tục sau khi router đổi dải IP

- **Mã việc:** Q1 · **Môi trường:** nhà (làm từ xa qua Tailscale + SSH, không có mặt cạnh máy)
- **Đã làm:**
  1. Kiểm kết nối từ máy dev: `tailscale ping` tới PC đạt (đi qua DERP Singapore, 95–140 ms, chưa nối thẳng); cổng 22 mở, cổng 6443 `connection refused`.
  2. SSH vào PC: GPU bình thường (RTX 5060, driver 595.99.02, 237/8151 MiB, 42 °C), nhưng `systemctl show k3s` báo `NRestarts=1087` sau 4 giờ máy chạy.
  3. Đọc `journalctl -u k3s`: `node IP: "192.168.0.100" not found in the host's network interfaces` rồi `Shutdown request received: failed to start networking: ... failed to find interface with specified node ip`. `ip -4 addr`: `eno1` giờ là `192.168.10.42/24`, gateway `192.168.10.1`.
  4. Sửa `ansible_host` trong `infra/ansible/inventory/home.yaml` thành `192.168.10.42`; `make lint` đạt. Chuyển commit sang PC bằng `git bundle` qua SSH (máy dev chưa push được lên GitHub), fast-forward `feat/serving` trên PC.
  5. Chạy `ansible-playbook -i inventory/home.yaml site.yml -e argocd_enabled=false`, trước ở `--check --diff` (chỉ đổi `node-ip`, `tls-san` trong `/etc/rancher/k3s/config.yaml` và `server:` trong kubeconfig), sau chạy thật: `changed=3`, `failed=0`.
  6. k3s vẫn restart (thêm 2 lần trong 30 s), cùng thông báo lỗi. Đối tượng Node trong datastore còn IP cũ; bộ điều khiển NetworkPolicy (kube-router) đọc IP từ đó và tắt k3s trước khi kubelet kịp ghi IP mới. Tạo tạm `/etc/rancher/k3s/config.yaml.d/99-tam-go-ket-ip.yaml` với `disable-network-policy: true`, restart: Node nhận `InternalIP=192.168.10.42` và các annotation `k3s.io/internal-ip`, `flannel.alpha.coreos.com/public-ip` đổi theo. Xoá file tạm, restart lại với cấu hình gốc.
  7. Dọn pod kẹt do 1087 lần restart để lại: `metrics-server`, `local-path-provisioner` (`CreateContainerError: failed to reserve container name`, từ ~5 giờ trước), `coredns`, `traefik` (sandbox cũ 45 giờ, readiness 503), một pod vLLM `Unknown` và pod vLLM `CrashLoopBackOff` (lỗi DNS khi CoreDNS chưa lên). Xoá pod để Deployment tạo lại.
  8. Chép kubeconfig về máy dev (`~/.kube/llm-home.yaml`, `server:` đổi thành IP Tailscale của PC); `kubectl get nodes` từ máy dev đạt.
- **Quyết định và lý do:**
  - Dùng IP DHCP hiện tại thay vì đặt IP tĩnh trên PC: đang ở xa, cấu hình mạng sai thì mất cả Tailscale, không vào lại được. DHCP reservation trên router để làm khi có mặt ở nhà.
  - Sửa qua Ansible (Git) chứ không sửa tay `config.yaml`, theo quy tắc trong file. Riêng bước gỡ kẹt dùng file trong `config.yaml.d/` (k3s đọc thêm thư mục này) để không đụng file Ansible quản lý, và xoá ngay sau đó.
  - Xoá pod thay vì restart toàn bộ: Deployment tự tạo lại, ít ảnh hưởng hơn.
- **Kết quả và số đo:**
  - Sau khi xoá file tạm và restart lúc 14:37:57: `NRestarts=0` sau 60 s; node `Ready`, `INTERNAL-IP 192.168.10.42`; `nvidia.com/gpu` allocatable = 1.
  - Mọi pod `Running` (device plugin, GPU exporter, CoreDNS, Traefik, metrics-server, local-path, vLLM 1/1).
  - vLLM: `/v1/models` trả `qwen2.5-1.5b`; một lần `/v1/chat/completions` (`max_tokens` 32, qua `port-forward`) HTTP 200 trong 0,127 s; VRAM 6783/8151 MiB. Không đo thời gian khởi động lại của vLLM.
- **Sự cố:** IP LAN của PC đổi (router đổi dải từ `192.168.0.0/24` sang `192.168.10.0/24`, chưa rõ vì sao) → `node-ip` ghim trong cấu hình k3s không còn trên máy → k3s tự tắt, systemd bật lại, lặp 1087 lần → chạy lại Ansible với IP mới, tạm tắt NetworkPolicy một lần để Node nhận IP mới. Rủi ro này đã ghi ở nhật ký chung tuần 01 ("chưa kiểm tra là IP tĩnh hay DHCP reservation").
- **Khác thiết kế:** cluster vẫn dựa vào IP LAN do DHCP cấp, chưa có reservation. Chạy playbook với `-e argocd_enabled=false` vì chưa có `platform/argocd/root-app-*.yaml` (TR1).
- **Còn phải làm:** đặt DHCP reservation trên router (cần có mặt ở nhà); viết runbook "node đổi IP"; đổi mật khẩu SSH của `zett` và chuyển sang đăng nhập bằng khoá (mật khẩu hiện tại yếu, đã lộ trong phiên chat với AI agent).
- **Liên kết:** commit `baed4bb` (nhánh `feat/home-k3s`); `infra/ansible/inventory/home.yaml`; `docs/nhat-ky/van-hanh.md` (nhánh `feat/serving`).
- **Dùng cho luận văn:** §4.1 (hạ tầng nhà, phụ thuộc IP LAN), chương 5 hoặc §3.5 phần rủi ro vận hành: ví dụ thật về một cấu hình ghim cứng gây crash-loop và cách gỡ. Hình nên có: đoạn log `Shutdown request received` và `NRestarts=1087`.

## 2026-11-02 – Chuyển k3s nhà sang IP Tailscale

- **Mã việc:** Q1 · **Môi trường:** nhà (từ xa qua Tailscale + SSH)
- **Đã làm:**
  1. Ansible nhóm `home`: `node_ip` lấy từ fact `tailscale0` (`100.73.95.48`), thêm `flannel_iface: tailscale0` (template server và agent ghi `flannel-iface`); `kubeconfig_server` dùng `node_ip` của server; bỏ IP Tailscale khỏi `k3s_tls_sans` (template đã thêm `node_ip`); `ansible_host` của PC đổi thành IP Tailscale. Nhóm `cloud` giữ nguyên (`flannel_iface` rỗng).
  2. Thêm drop-in systemd `10-cho-tailscale.conf` cho `k3s` và `k3s-agent`: `After/Wants=tailscaled.service`, `ExecStartPre` chờ tối đa 60 s tới khi `tailscale0` có IPv4. Task restart k3s chạy cả khi drop-in đổi, kèm `daemon_reload`.
  3. `make lint` đạt; chuyển sang PC bằng `git bundle`; `--check --diff` (chỉ đổi `node-ip`, `flannel-iface`, `tls-san`, drop-in, `server:` của kubeconfig), rồi chạy thật với file tạm `disable-network-policy: true` trong `config.yaml.d/` đặt trước (cùng cách gỡ kẹt như mục trên), xoá file tạm, restart.
  4. `rollout restart` CoreDNS, Traefik, metrics-server, local-path, DaemonSet trong `gpu`, vLLM để pod nhận MTU mới.
- **Quyết định và lý do:** PC ở chung cư, không quản lý được router nên không đặt DHCP reservation được; IP tĩnh trên PC có thể trùng IP máy khác hoặc hỏng khi toà nhà đổi dải, và cấu hình sai thì mất cả Tailscale. IP Tailscale gắn với máy, không phụ thuộc router. Bỏ phương án dummy interface (IP giả cố định): không dùng được khi laptop vào cluster.
- **Kết quả và số đo:**
  - Node `Ready`, `INTERNAL-IP 100.73.95.48`; annotation `flannel.alpha.coreos.com/public-ip` = `100.73.95.48`; `NRestarts=0` sau 60 s.
  - `/run/flannel/subnet.env`: `FLANNEL_MTU=1230` (MTU `tailscale0` 1280 trừ 50 B VXLAN); `eth0` trong pod vLLM: 1230.
  - Mọi pod `Running`; DNS trong pod phân giải được `huggingface.co` và `kubernetes.default`; chat qua `port-forward` HTTP 200 (0,127 s); Ingress `llm.home` qua `http://100.73.95.48` HTTP 200; `kubectl` từ máy dev đạt.
  - Khoá Tailscale của PC hết hạn 21/04/2027 (sau hạn nộp).
- **Khác thiết kế:** thiết kế cũ cố ý không dùng card Tailscale cho k3s. Giờ cluster nhà phụ thuộc `tailscaled`; MTU pod 1230 thay vì ~1450. Khi laptop vào cluster, lưu lượng giữa node đi qua Tailscale (cùng LAN thì thường nối thẳng, chưa đo).
- **Chưa kiểm:** chưa khởi động lại PC để thử drop-in chờ Tailscale (đang ở xa, PC không lên lại thì không xử lý được); làm khi có mặt ở nhà.
- **Còn phải làm:** tắt key expiry của PC trên trang admin Tailscale; đổi mật khẩu SSH, chuyển sang khoá.
- **Liên kết:** commit `c0beb4c` (nhánh `feat/home-k3s`); `infra/ansible/inventory/group_vars/home.yaml`, `roles/k3s-server`, `roles/k3s-agent`.
- **Dùng cho luận văn:** §4.1 (mạng của cluster nhà: vì sao dùng Tailscale), §3.6 Môi trường (ràng buộc mạng chung cư). Có thể làm hình: sơ đồ PC – Tailscale – máy dev/Trình.

## 2026-11-04 – Rà tiến độ, tích checklist mốc, dời V2 sang 14–15/11

- **Mã việc:** chung · **Môi trường:** không (máy dev, chỉ đọc cluster nhà bằng `kubectl`)
- **Đã làm:**
  1. `git fetch --all`: `origin/main` đã có PR #3 (TR4), #4 (TR5), #5 (TR1 CI). Liệt kê PR qua API công khai của GitHub vì `gh` chưa đăng nhập: 5 PR, đều đã merge, không có PR nào của phần Quang.
  2. Đọc trạng thái cluster nhà: 1 node `Ready`; namespace chỉ có `gpu`, `kube-system`, `llm-serving`; pod vLLM `Running` 32 giờ. Chưa có `monitoring`, `keda`, `argocd`.
  3. Kiểm CI: lượt chạy trên `main` ngày 02/11 đạt cả 6 job (`yaml`, `manifests`, `alerts`, `python` 3.11 và 3.15, `docs`).
  4. Tích [Kế hoạch §3](../../../chi-tiet/06-ke-hoach-quan-ly.md#3-checklist-các-mốc): M1 đạt 2/7 (vLLM trên GPU nhà, CI xanh), M2 đạt 0/8; mục làm một phần có ghi chú *(04/11: …)*.
  5. Ghi quyết định dời V2 vào Kế hoạch §1, §1.1 (mới), §2, §4 và Môi trường §6; nhật ký chung [tuần 05](../../tuan-05.md).
  6. Làm trang web tóm tắt tiến độ (artifact riêng tư trên claude.ai).
- **Quyết định và lý do:** dời V2 sang 14–15/11 vì runner, Prometheus, KEDA chưa có thì V2 không ra số liệu. Làm local trước (kind + simulator, rồi cluster nhà), vì miễn phí và sửa lỗi nhanh. Chọn cloud để sau nhưng phải xong trước phiên V0+V1. Chỉ tích ô khi mục đạt trọn, để checklist không đẹp hơn thực tế.
- **Sự cố:** merge `origin/main` vào `docs/quang-w4` xung đột ở `Makefile` (nhánh này mang `Makefile` của `feat/home-k3s`). Không cần merge cho việc sửa tài liệu nên huỷ merge; xung đột sẽ giải khi PR A vào `main`.
- **Khác thiết kế:** mất phiên dự phòng V3; đóng băng dữ liệu 22/11 thay vì 15/11.
- **Liên kết:** `docs/chi-tiet/06-ke-hoach-quan-ly.md`, `docs/chi-tiet/05-moi-truong-danh-gia.md`, `docs/nhat-ky/tuan-05.md`.
- **Dùng cho luận văn:** §1 hoặc phụ lục quản lý dự án: ví dụ áp dụng kế hoạch dự phòng (§8) khi trễ mốc.

## 2026-11-04 – Vòng autoscaling chạy local trên kind: simulator, Prometheus, KEDA, A2, máy tạo tải

- **Mã việc:** Q3 (overlay `sim`), thử chéo TR2, TR3, TR5 · **Môi trường:** simulator (kind trên máy dev Linux, 12 lõi, 15 GB RAM)
- **Đã làm:**
  1. Kéo image `llm-d-inference-sim:v0.12.0`, đọc `--help` để đối chiếu cờ với bản nháp `serving/overlays/sim`. Lấy digest bằng `docker image inspect`.
  2. Sửa `serving/overlays/sim`: ghim image theo digest qua `images:` của kustomization (bản cũ ghi tag thẳng trong patch, trái CONTRIBUTING §2); bỏ cờ `--force-dummy-tokenizer` (deprecated ở v0.12.0); viết lại comment. Ghi digest vào `docs/phien-ban.md`.
  3. Dựng môi trường thử bằng file nháp của `temp/w2-scaffold` chép ra thư mục tạm (không commit, vì `infra/kind`, `platform/*`, `autoscaling/` là phần TR2, TR3 của Trình đang làm ở `feat/tr2-sim`): kind 3 node (`kind-config.yaml`, HPA sync 5 s), kube-prometheus-stack 92.1.1, KEDA 2.21.0, ScaledObject A2 overlay `sim` (max 3, threshold 10), theo đúng các bước của `make sim-up` trong scaffold.
  4. Cài `uv` 0.13.7 bằng `pipx`; `pytest` của `loadgen`: 41 passed trên Python 3.14 (Linux).
  5. Lượt 1: máy tạo tải chạy trên máy dev, gọi qua `kubectl port-forward svc/vllm`. Lượt 2: máy tạo tải chạy trong pod `python:3.12-slim` (CPU 1, RAM 512 Mi, request = limit) trong namespace `llm-serving`, gọi `http://vllm.llm-serving.svc:8000`.
- **Quyết định và lý do:**
  - Không commit môi trường thử, chỉ commit phần thuộc Q3, để không làm trùng và xung đột với nhánh chưa push của Trình. Kết quả dưới đây vẫn dùng được làm bằng chứng cho mục M1 "A2 scale 1 → 3 trên simulator".
  - Chọn tải CONST 2 req/s, `max_tokens` 256 để dự đoán trước được: mỗi request ≈ 0,2 + 256 × 0,05 = 13 s, theo định luật Little số request đồng thời L = λW ≈ 26, A2 tính desired = ⌈26 / 10⌉ = 3.
- **Kết quả và số đo:**
  - Simulator: `/v1/models` trả `qwen2.5-1.5b`, `max_model_len` 4096; streaming có chunk `usage` cuối cùng khi gửi `stream_options.include_usage`; `ignore_eos` cho đúng 256 token. Prometheus scrape target `llm-serving/vllm` mỗi 5 s, metric có nhãn `namespace`, `pod`, `model_name`.
  - **Lượt 2 (trong cluster, CONST 2 req/s × 180 s):** 357/357 request, 0 lỗi; tự kiểm tra hợp lệ (lệch lịch p99 1,4 ms; CPU tối đa 9 % một lõi; không bị throttle). HPA quyết định 3 replica ở giây 16, 3 pod Ready ở giây 32. Giá trị trung bình mỗi pod ở trạng thái ổn định 7–11 (dự đoán 26 / 3 ≈ 8,7). TTFT p99 của request gửi trong 30 s đầu: 19,3 s (xếp hàng trên 1 pod trước khi scale xong); request gửi từ giây 60: TTFT p99 0,205 s (= độ trễ giả 200 ms). E2E p50 13,2 s.
  - **Scale-down:** metric về 0, khoảng 5 phút sau HPA giảm 3 → 2, 60 s sau giảm 2 → 1, đúng `stabilizationWindowSeconds: 300` và chính sách 1 pod/60 s của A2.
- **Sự cố:**
  - Lượt 1 (qua `port-forward`): cả 357 request vào **một** pod (Prometheus: `increase(vllm:request_success_total[15m])` chỉ có pod đầu tiên), dù HPA đã lên 3 replica; TTFT p50 47 s, 5 request timeout ở 120 s. Nguyên nhân: `kubectl port-forward svc/…` chọn một pod của Service lúc bắt đầu rồi chỉ chuyển tới pod đó, không cân bằng tải. Cách sửa: chạy máy tạo tải trong cluster, gọi Service. Đúng với thiết kế Môi trường §3.6 (máy tạo tải là pod trong cluster); không đo bằng `port-forward`.
  - Request timeout giữa luồng vẫn ghi `status=200` trong `requests.csv` (header 200 đã về trước khi bị cắt), lỗi nằm ở cột `error`. Khi phân tích phải lọc theo `error`, không theo `status`. Báo Trình (TR5, TR7).
  - `kind load docker-image python:3.12-slim` lỗi `content digest … not found` (image nhiều kiến trúc); pod vẫn tự kéo image từ Docker Hub nên không ảnh hưởng.
- **Khác thiết kế:**
  - KEDA cảnh báo khi áp A2: `pollingInterval` không ảnh hưởng tới scale khi `minReplicaCount ≥ 1`. Khi đó HPA hỏi metric server của KEDA mỗi chu kỳ sync (5 s trên kind và k3s), KEDA truy vấn Prometheus ngay lúc đó. Comment "KEDA hỏi Prometheus mỗi 5 s" trong A2 của scaffold chưa đúng; báo Trình sửa ở `feat/tr2-sim`.
  - Pod máy tạo tải lần này cài `httpx` bằng `pip` lúc chạy, chưa có image riêng ghim digest (còn thiếu của TR5).
- **Liên kết:** `serving/overlays/sim/`, `docs/phien-ban.md` (nhánh `feat/serving-sim`).
- **Dùng cho luận văn:** §4.4 (autoscaling trên simulator), §5 (kiểm chứng định luật Little: L dự đoán 26, đo ≈ 3 × 8,7); bài học "port-forward không cân bằng tải" cho phần phương pháp đo. Hình nên có: chuỗi thời gian replica và giá trị metric của lượt 2 (đã lưu tạm, cần vẽ lại từ Prometheus khi có runner).

## 2026-11-05 – LT1 trên RTX 5060, ĐG1-mini ở nhà, `capacity-home.json` tạm

- **Mã việc:** Q8 (LT1, LT2, LT3), Q6 (ĐG1-mini) · **Môi trường:** nhà (từ xa qua Tailscale, `kubectl`)
- **Đã làm:**
  1. Thấy pod vLLM bị thay khoảng 01:25 do k3s tự khởi động lại; ghi sự cố vào `docs/nhat-ky/van-hanh.md`, chưa rõ nguyên nhân.
  2. LT1: `vllm bench serve` chạy trong pod vLLM (API key lấy từ biến môi trường của pod, không in ra), `--max-concurrency 1 --num-prompts 20`, random 512/256, `--ignore-eos`, `--seed 1`; kiểm thông số bộ nhớ bằng `nvidia-smi`.
  3. ĐG1-mini: tạo pod `loadgen` (`python:3.12-slim` ghim digest, CPU 1 / RAM 512 Mi request = limit, `LOADGEN_API_KEY` lấy từ Secret `vllm-api-key`), chép `loadgen/` và script tạm `dg1_mini.py` vào pod. Script quét λ = 1, 2, … req/s ở chế độ CONST, mỗi mức 60 s làm ấm + 120 s đo, lấy mẫu `vllm:num_requests_running|waiting`, `vllm:kv_cache_usage_perc` và GPU exporter mỗi 2 s; dừng khi TTFT p95 > 7,5 s hoặc hàng đợi trung bình > 32.
  4. Ghi `experiments/capacity-home.json`; ghi LT1, LT2 (KV lúc tải cao), LT3 vào `van-hanh.md`; cập nhật ghi chú checklist Kế hoạch §3. Dữ liệu thô ở `runs/dg1-mini-home-20261105/` (gitignore, chỉ trên máy dev).
- **Quyết định và lý do:**
  - Gọi vLLM qua Service từ pod trong cluster, vì đã thấy `port-forward` chỉ nối một pod (mục 04/11). Với 1 replica thì không lệch, nhưng giữ cùng cách đo cho mọi phép.
  - Mỗi mức đo 120 s thay vì 4 phút, bước λ = 1 thay vì 0,25 quanh điểm gãy, để ĐG1-mini nằm trong ~30 phút như Thông số §8.3. Số liệu chỉ là target tạm.
  - C chọn = 6 req/s: mức lớn nhất có SLO attainment ≥ 95 % (100 %, TTFT p95 1,35 s). λ = 7 chỉ đạt 28 %.
  - Threshold A2 tạm = 0,8 × B\* = 0,8 × 26,8 ≈ 21 (Kiến trúc §11).
- **Kết quả và số đo:**
  - LT1: TPOT p50 8,68 ms, p99 8,69 ms (dự đoán 8,3–9,6 ms; cận dưới 6,9 ms); băng thông hiệu dụng ≈ 356 GB/s ≈ 79 % của 448 GB/s (`clocks.max.memory` 14.001 MHz, GDDR7, bus 128 bit theo thông số hãng).
  - ĐG1-mini (đã dừng sau λ = 8 vì hàng đợi > 32): C = 6 req/s; B\* = 26,8; GPU util tại C 100 %; KV-cache tại C 19 %. TPOT p50 tăng từ 8,9 ms (λ = 1) lên 18,1 ms rồi đứng yên khi số request chạy chạm `max-num-seqs` = 32. 0 lỗi HTTP ở mọi mức. Little (với λ thực trong cửa sổ): lệch ≤ 2 % ở λ = 1–7.
  - Máy tạo tải tự kiểm tra: lệch lịch p99 ≤ 2,3 ms, CPU ≤ 17,4 % một lõi ở mọi mức.
- **Sự cố:**
  - Script lần đầu tính `n_meas = 0`: `requests.csv` ghi thời gian **tương đối** (giây từ đầu lượt), còn mẫu metric ghi giờ Unix; trừ nhầm hai loại. Sửa hàm thống kê và tính lại từ dữ liệu thô (không phải chạy lại). Hệ quả phụ: điều kiện dừng theo TTFT không chạy (NaN), lượt quét dừng nhờ điều kiện hàng đợi.
  - Máy tạo tải đánh dấu lượt λ = 6 và λ = 8 **không hợp lệ** vì cgroup throttle đúng 1 chu kỳ (4,4 ms và 1,4 ms trên ~1.800–2.000 chu kỳ). Nghi do luồng lấy mẫu của script chạy chung pod, chung giới hạn 1 lõi. Ảnh hưởng tới số đo không đáng kể (lệch lịch p99 2,1 ms) nhưng vẫn ghi là không hợp lệ.
  - Không SSH được vào PC: máy dev chưa có host key cho IP Tailscale; không tự chấp nhận.
- **Khác thiết kế:**
  - ĐG1-mini rút gọn (bước 1 req/s, 120 s đo) như trên. Cần đo lại λ = 5,75–7 bước 0,25, với luồng lấy mẫu ở ngoài pod máy tạo tải hoặc pod 2 lõi.
  - Tiêu chí `throttle_ok` (`nr_throttled == 0`) rất chặt: 1 chu kỳ 4 ms cũng loại cả lượt. Đề xuất Trình xem có nên đặt ngưỡng theo `throttled_usec` (ví dụ < 0,1 % thời gian lượt), cần chốt ở Môi trường §17.
  - Script `dg1_mini.py` là script tạm (chưa có test), giữ ở `runs/` trên máy dev; runner Q6 sẽ thay.
- **Liên kết:** `experiments/capacity-home.json`, `docs/nhat-ky/van-hanh.md` (LT1, LT2, LT3, sự cố 05/11), `docs/chi-tiet/06-ke-hoach-quan-ly.md` §3 (nhánh `feat/serving-sim`).
- **Dùng cho luận văn:** chương 5 mục kiểm chứng lý thuyết (LT1 trọn mẫu, LT3 bảng và đường cong, LT2 phần KV lúc tải cao); dữ liệu cho LT5, LT6 của Trình; §4.11 năng lực (minh hoạ quy trình ĐG1 trên GPU nhà). Hình nên có: TTFT p95 và TPOT p50 theo λ, B theo λ (có thể vẽ từ `curves` trong `capacity-home.json`).

## 2026-11-05 – Cập nhật trang tiến độ, tìm ra PC treo khi suspend

- **Mã việc:** chung, Q1 · **Môi trường:** nhà (đọc log trên PC, `kubectl`)
- **Đã làm:**
  1. Cập nhật trang web tiến độ (artifact riêng tư trên claude.ai) từ bản 04/11: thêm bảng "thay đổi so với 04/11", trạng thái vòng autoscaling trên kind, C = 6 req/s, LT1–LT3, việc tiếp theo.
  2. Kiểm cluster nhà: vLLM 1/1 sau lượt boot 11:17; còn 5 pod vLLM cũ và pod `loadgen` ở `Unknown`/`Completed`.
  3. Đọc `journalctl --list-boots`, `journalctl -b -1`, `-b -2`, `-b -4` để xem các lượt boot kết thúc thế nào.
- **Kết quả và số đo:**
  - Lệnh suspend 03:16 treo ở `nvidia-suspend`, máy boot lại 11:17. Ghi ở `van-hanh.md`.
  - Vụ "k3s tự khởi động lại 05/11" thực ra là PC tắt bình thường lúc 19:32 ngày 04/11 rồi bật lại khoảng 02:01; RTC lúc boot lệch 7 giờ. Đã bổ sung vào mục sự cố đó trong `van-hanh.md`.
  - k3s tự lên sau mỗi lượt boot, tức drop-in chờ Tailscale (mục 02/11) đã chạy thật.
- **Quyết định và lý do:** không suspend PC khi đang chạy vLLM; chưa dọn pod `Unknown` (chờ Quang đồng ý thao tác trên cluster).
- **Liên kết:** `docs/nhat-ky/van-hanh.md`.
- **Dùng cho luận văn:** §3.6 hoặc chương 5 phần hạn chế của môi trường nhà (máy cá nhân, dual-boot, nguồn điện, suspend).

## 2026-11-05 – Thử xin quota GPU trên GCP: không đủ điều kiện

- **Mã việc:** Q2 · **Môi trường:** GCP (console)
- **Đã làm:** xin quota Compute Engine `GPUs (all regions)` = 2 và `NVIDIA L4 GPUs` ở `asia-southeast1` = 2.
- **Kết quả:** cả hai bị chặn ngay trong form: "Enter a new quota value between 0 and 0. Based on your service usage history, you are not eligible for a quota increase at this time", gợi ý liên hệ Sales. Không gửi được yêu cầu.
- **Quyết định và lý do:** chưa quyết. Đề xuất coi Vast là phương án cloud duy nhất cho V0+V1 và V2, vì GCP cần lịch sử dùng mới được xin GPU mà không còn thời gian trước 11/11. Cần chốt K6 trong ADR-004.
- **Dùng cho luận văn:** phần hạn chế, lý do chọn nền tảng thuê GPU (§3.2 Môi trường).

## 2026-11-06 – Bỏ laptop 4050, chia RTX 5060 thành 3 GPU replica bằng time-slicing

- **Mã việc:** Q1, Q3 · **Môi trường:** không (chỉ sửa code và tài liệu; chưa áp lên cluster nhà)
- **Đã làm:**
  1. Rà các việc cần laptop 4050: KB2-mini 1 → 2, VH1, VH2 (ca 1 replica cần tạm 2 pod), VH3 drain node, LT1 điểm thứ hai.
  2. Thêm `platform/gpu/device-plugin-values-home.yaml`: time-slicing, `nvidia.com/gpu` × 3 replica, `renameByDefault: false`, `failRequestsGreaterThanOne: true`. Để file riêng, cài chồng sau file chung, vì máy thuê dùng chung `device-plugin-values.yaml` mà không được chia GPU.
  3. Overlay `home`: đổi model sang `Qwen/Qwen2.5-0.5B-Instruct@7ae55760…75` (`qwen2.5-0.5b`), `--max-model-len` 2048, `--max-num-seqs` 16, `--gpu-memory-utilization` 0,25; RAM request 2Gi, limit 4Gi; `/dev/shm` 512Mi.
  4. Sửa tài liệu cho khớp: Thông số §9.1, §9.2, §10.1; Môi trường (tóm tắt, bảng tầng, Kế hoạch Z, §18); Kế hoạch §5.1; ADR-004 §7 (dòng 06/11); `phien-ban.md`; w2.md §5; `viec-sap-lam.md`.
- **Quyết định và lý do:** chia một card thay vì gắn laptop. Laptop còn là máy làm việc, driver và SSH chưa sẵn, và hai GPU khác loại cũng không cho số đo so sánh được. Ở nhà chỉ kiểm chức năng; mọi số đo hiệu năng lấy trên máy thuê. Chọn 0,5B vì 1,5B (~3,1 GB) chỉ vừa 1 pod trên 8 GB. VRAM chia tay qua `--gpu-memory-utilization`, vì time-slicing không cô lập VRAM: 0,25 × 8 GB ≈ 2 GB/pod, 3 pod ≈ 6 GB, chừa ~1,2 GB mà màn hình đang dùng (đo `nvidia-smi` 06/11: 1166 MiB). Drain node (VH3) chuyển sang kind nhiều node, vì time-slicing vẫn chỉ có 1 node.
- **Kết quả và số đo:** `helm template` chart `nvidia-device-plugin` 0.20.1 với hai file values: ra ConfigMap `time-slicing` và sidecar `config-manager` có `DEFAULT_CONFIG=time-slicing`. `uvx yamllint==1.38.0 -s .` sạch; `kubectl kustomize` cả 3 overlay `home`, `cloud`, `sim` build được. **Chưa chạy trên cluster:** máy dùng hôm nay không có k3s và Tailscale. Chưa đo RAM thực của pod 0,5B; chưa biết vLLM có lỗi thiếu VRAM khi 2–3 pod cùng khởi động không.
- **Khác thiết kế:** model nhà 1,5B → 0,5B; nhà có 3 GPU replica thay vì 1–2 GPU thật; VH3 drain node chỉ làm trên simulator. LT1–LT3 và `experiments/capacity-home.json` là số đo của 1,5B trước ngày đổi, nên ngưỡng A2 ở nhà phải đo lại. A1 (theo GPU util của cả card) không có nghĩa ở nhà khi có > 1 pod.
- **Liên kết:** nhánh `feat/home-timeslicing`; `platform/gpu/device-plugin-values-home.yaml`, `serving/overlays/home/patch-vllm.yaml`, ADR-004 §7.
- **Dùng cho luận văn:** §4.1 (môi trường nhà, GPU sharing bằng time-slicing), phần hạn chế (nhà không cô lập GPU nên không đo hiệu năng).

## 2026-11-06 – Dựng lại cluster nhà sau khi cài lại hệ điều hành; chạy thử M1

- **Mã việc:** Q1, Q3 (kèm phần nháp của TR1, TR2, TR3 để Trình review) · **Môi trường:** nhà (PC), simulator (kind trên PC)
- **Đã làm:**
  1. Quang cài lại Ubuntu 26.04.1 lên NVMe lúc 23:08 ngày 05/11 (ổ cũ SATA `sda5` còn nguyên). Mount `sda5` chỉ đọc: repo cũ sạch, không có commit chưa push; chép `runs/` (dữ liệu thô ĐG1-mini 05/11 và lượt A2 04/11, 632 KB) về repo mới. Không chép cache model 1,5B (3 GB) vì nhà đã chuyển sang 0,5B.
  2. Lấy từ `temp/w2-scaffold` các file nháp còn thiếu: kind config, values kube-prometheus-stack và KEDA, ScaledObject A2, App-of-Apps nhà. Commit từng nhóm trên nhánh `feat/m1-home-rebuild`; thêm values time-slicing vào Application `gpu-device-plugin`.
  3. Kind: `make sim-up` 188 s; bài T2/T3 với Job 25 vòng curl gọi Service.
  4. Cài Tailscale 1.104.5 từ kho apt có ký số (script cài bị auto mode chặn); IP mới `100.120.67.28`, tên `zorsche-upc`. Sửa inventory.
  5. Ansible dựng k3s, rồi bằng helm/kubectl: kube-prometheus-stack, device plugin (time-slicing), GPU exporter, KEDA, PodMonitor Traefik, vLLM overlay `home`. Chạy lại playbook với `argocd_enabled` để cài Argo CD core và Application gốc.
- **Kết quả và số đo:**
  - T2/T3 trên kind (threshold 10, max 3): HPA quyết định 3 replica ở t = 17 s, 3 pod Ready ở t = 27 s; metric mỗi pod 6,3–10,3 khi có tải; hết tải ở t ≈ 200 s, giảm 3 → 2 ở t = 487 s, 2 → 1 ở t = 548 s (đúng window 300 s và 1 pod/60 s).
  - Ansible: lần 1 lỗi sau 53 s (xem Sự cố), lần 2 dựng xong k3s `v1.36.5+k3s1` trong **29 s**, node Ready trên IP Tailscale, có RuntimeClass `nvidia`. kube-prometheus-stack 59 s. Node báo `nvidia.com/gpu` = 3, sau đó sửa về 2.
  - Prometheus scrape được GPU exporter, Traefik, vLLM (5 s) và các thành phần cluster. Qua Ingress `llm.home`: 3/3 request HTTP 200, TTFB 0,06–0,11 s; Traefik đếm đúng 3 request mã 200.
  - vLLM 0,5B: không có key → 401, có key → stream được. Image `v0.31.0` 9,0 GB kéo trong 4 phút 14 giây. Với `gpu-memory-utilization` 0,40: 3186 MiB VRAM, KV-cache 1,81 GiB (158.448 token, đồng thời tối đa 77× ở 2048 token), RAM pod ~3,3–3,4 GiB. Cold start 400 s (tạo pod 21:42:03 → Ready 21:48:43 UTC) dù image, model và compile cache đã có; riêng `init engine` 354 s, chậm hơn nhiều so với 155 s của 1,5B trước đây, chưa rõ vì sao.
  - Argo CD core chạy; Application gốc báo `platform/argocd/apps/home: app path does not exist` vì thư mục chưa có trên `main`. Đúng dự kiến: sẽ tự sync sau khi merge chuỗi PR.
- **Sự cố:**
  - Ansible lần 1 lỗi `Failed to update apt cache`: mình đặt `umask 077` trong shell để tạo file mật khẩu, umask lan sang Ansible nên khoá GPG kho NVIDIA và `/etc/sysctl.d/90-k8s.conf` có quyền 600, `apt` (user `_apt`) không đọc được. Sửa về 644, chạy lại. Bài học: chỉ đặt umask trong subshell.
  - Argo CD core không có argocd-server nên không có AppProject `default`: Application gốc bị từ chối. Thêm `platform/argocd/project-default.yaml`, role `argocd-bootstrap` áp trước Application gốc.
  - Secret API key tạo bằng `--from-file` dính ký tự xuống dòng; tạo lại bằng `--from-literal`. Key mới cất ở `~/.config/llm-k8s/vllm-api-key` (ngoài repo).
  - `gpu-memory-utilization` 0,25 không đủ: sau ~45 phút vLLM thoát với `No available memory for the cache blocks`. Lần đó capture CUDA graph mất 30 s/graph vì máy quá tải (hai pod cùng giải nén image, load average tới 241); lần sau chỉ 1 s.
  - Pod vLLM bị xoá khi đang kéo image kẹt `Terminating` cho tới khi kéo xong (> 5 phút, quá grace period 180 s). Liên quan việc Q5 "pod đang khởi tạo không thoát khi nhận SIGTERM".
  - **Scale lên 2 pod làm PC hết RAM** (chi tiết ở `van-hanh.md`): máy treo nhiều giờ, khởi động lại khoảng 10:19. Sau khi lên lại, Deployment vẫn lưu 2 replica nên 2 pod lại cùng khởi động; scale về 1 ngay.
- **Quyết định và lý do:** giữ IP Tailscale mới thay vì đổi về `100.73.95.48`: cluster mới có chứng chỉ mới nên Trình đằng nào cũng cần kubeconfig mới, còn đổi IP sau khi k3s chạy có thể gây crash loop như 02/11. Time-slicing 2 replica thay vì 3, `gpu-memory-utilization` 0,40, RAM request 3,5Gi/limit 5Gi, theo số đo. Không push theo dặn của Quang; Argo CD trỏ `main` như thiết kế.
- **Khác thiết kế:** nhà chỉ 2 GPU replica và tạm thời chỉ chạy được 1 pod vLLM (RAM). Các thành phần đang cài bằng helm/kubectl, chưa qua Argo CD.
- **Liên kết:** nhánh `feat/m1-home-rebuild` (chồng trên `feat/home-timeslicing`); `platform/argocd/project-default.yaml`, `infra/ansible/roles/argocd-bootstrap/tasks/main.yml`, `serving/overlays/home/patch-vllm.yaml`, `platform/gpu/device-plugin-values-home.yaml`; log Ansible `~/k3s-rebuild-*.log` trên PC.
- **Dùng cho luận văn:** §4.1 (dựng lại từ máy trắng bằng Ansible: 29 s cho k3s; tiền đề cho VH5/N8), §4.2 (bẫy Argo CD core thiếu AppProject), §5 hạn chế (GPU sharing ở nhà giới hạn bởi RAM, không phải VRAM), T2/T3 trên simulator.

## 2026-11-06 – Chạy được 2 pod vLLM chung một RTX 5060

- **Mã việc:** Q1, Q3 · **Môi trường:** nhà (PC)
- **Đã làm:** sau khi PC khởi động lại (10:19), chạy watchdog RAM bằng root: mỗi 2 s đọc `MemAvailable`, dưới 700 MB thì `k3s crictl stop` container vLLM mới nhất rồi scale về 1. Scale vLLM lên 2 lúc 10:45:45. Gửi 40 request song song qua Service.
- **Kết quả và số đo:** pod thứ hai Ready sau ~141 s; watchdog không phải ra tay. RAM khả dụng 5182 MB trước khi scale → ~1,7–1,9 GB khi có 2 pod; VRAM 2,6 → 5,7 GB/8 GB; load average ≤ 1,0. 40/40 request HTTP 200; Prometheus `vllm:request_success_total`: 26 và 14 request ở hai pod (kube-proxy chọn ngẫu nhiên). RAM mỗi pod ~3,7 GiB khi rảnh.
- **Sự cố:** đêm qua `sudo pkill -9` vLLM báo `Permission denied` vì container chạy dưới profile AppArmor `cri-containerd`, chặn tín hiệu từ ngoài kể cả root; phải dừng qua containerd (`crictl stop`).
- **Quyết định và lý do:** giữ 2 GPU replica. Hai pod chạy được nếu RAM khả dụng trước khi scale ≥ ~5 GB; dư sau đó chỉ ~1,7 GB nên vẫn cần kiểm `free -m` và nên chạy watchdog. Khác với lần treo đêm qua chủ yếu ở RAM khả dụng lúc bắt đầu (~3 GB so với ~5,2 GB).
- **Dùng cho luận văn:** §4.1 (GPU sharing bằng time-slicing: 2 replica trên 1 GPU 8 GB, cân bằng tải qua Service), §5 hạn chế (mỗi replica tốn ~3,5 GiB RAM cố định, RAM hết trước VRAM).

## 2026-11-06 – Merge chuỗi PR #7–#11, Argo CD tiếp quản cluster nhà

- **Task:** Q1, Q3; TR1 (nháp) · **Environment:** home
- **Done:** tạo 5 PR xếp chồng (#7–#11). Quang tự review và merge từng PR (merge commit), mỗi lần đổi base PR kế tiếp sang `main` rồi bỏ draft. Sau #11, refresh Application `root-home`.
- **Results:** #7–#11 vào `main` từ 11:23 đến 11:46 (giờ Việt Nam). Khoảng 1 phút sau #11, Argo CD core trên PC tạo đủ Application con; cả 7 (`root-home`, `gpu-device-plugin`, `gpu-exporter`, `monitoring`, `monitoring-extras`, `keda`, `serving`) đều `Synced`/`Healthy`, tiếp quản các thành phần trước đó cài bằng helm/kubectl mà không xoá gì. Deployment `vllm` vẫn 0 replica (manifest không có `replicas`, Argo CD không đụng số pod). Tích 3 mục M1: Argo CD, Prometheus, A2 trên kind.
- **Incidents:** CI không chạy trên cả 5 PR: "The job was not started because your account is locked due to a billing issue". Code đã kiểm trên máy trước khi merge: `yamllint`, `kustomize` 9 thư mục, Ansible syntax-check, `pytest` 41/41, lychee 498 link 0 lỗi. Chưa chạy `kubeconform` và `promtool` trên máy. Push lần đầu lỗi vì máy mới chưa cấu hình credential cho Git, sửa bằng `gh auth setup-git`.
- **Decision:** giữ trunk-based theo CONTRIBUTING §7 (PR thẳng vào `main`, Argo CD đọc `main`); nhánh `dev` cũ (đi sau `main` 74 commit) không dùng. Từ nay không `helm upgrade` cluster nhà, mọi thay đổi qua Git.
- **Links:** PR #7–#11; `docs/chi-tiet/06-ke-hoach-quan-ly.md` §3.
- **Thesis:** §4.2 GitOps (App-of-Apps tiếp quản thành phần cài tay; bẫy AppProject của bản core).

## 2026-11-06 – Runner v1: chạy được phiên sim-smoke trên kind, không cần can thiệp tay

- **Task:** Q6 · **Environment:** sim (kind)
- **Done:**
  1. Tạo package `experiments/` (uv, pyproject + uv.lock riêng như `loadgen/`) với runner `python -m experiments.runner`: đọc file ma trận YAML → với mỗi lượt: áp cấu hình (static hoặc ScaledObject đang pause), reset về trạng thái đầu, warm-up 0,3 × tốc độ, unpause rồi chạy phase chính, cooldown về 1 replica, thu dữ liệu, kiểm điều kiện hợp lệ, ghi `progress.json`.
  2. Máy tạo tải chạy trong cluster dưới dạng Job (image `python:3.12-slim` ghim digest, code loadgen qua ConfigMap, dependency ghim từ `loadgen/uv.lock`); runner chờ file `DONE` rồi `kubectl cp` kết quả ra.
  3. Prometheus truy vấn qua API server proxy (`kubectl get --raw`), không cần port-forward.
  4. 24 unit test cho các hàm thuần; CI chạy pytest/ruff cho `experiments/`.
  5. `make sim-up` (175 s), chạy phiên `experiments/matrix-sim.yaml`: S1 (static 1 replica) và A2 (threshold 10, max 3), mỗi lượt CONST 2 req/s.
- **Decision:** dùng annotation `autoscaling.keda.sh/paused-replicas` để giữ 1 replica suốt reset/warm-up, chỉ bỏ pause khi phase chính bắt đầu, nên warm-up không kích scale-up. Runner dừng ngay nếu Application Argo CD `autoscaling` đang auto-sync (Argo CD sẽ ghi đè ScaledObject runner áp). Một lượt lỗi thì ghi `error.txt` rồi chạy tiếp lượt sau; chạy lại phiên thì bỏ qua lượt `done`, tối đa 2 lần thử.
- **Results:**
  - Cả phiên 12:06:57 → 12:21:57 (15 phút), `S1-CONST-1=done`, `A2-CONST-1=done`, không phải can thiệp tay.
  - S1: 226 request trong 120 s; máy tạo tải lệch lịch p99 2,0 ms, CPU tối đa 5,4 %, không bị throttle; khoảng trống scrape tối đa 5 s.
  - A2: 357 request trong 180 s; replicas 1 → 3 khoảng 30 s sau khi phase chính bắt đầu (độ phân giải 5 s); hết tải rồi 3 → 2 sau ~315 s, 2 → 1 khoảng 60 s sau đó (đúng window 300 s, 1 pod/60 s); cả 3 pod scrape đều 5 s. Pod có từ đầu lượt còn nguyên, không restart.
  - Mỗi lượt sinh khoảng 150 KB dữ liệu (`metadata.json`, `requests.csv`, `metrics.csv.gz`, `checks.json`, events, logs).
- **Deviations:** metric lưu `metrics.csv.gz` thay vì `metrics.parquet` (Môi trường §17) để không thêm pandas/pyarrow; đổi khi phân tích cần. Chưa có upload R2, systemd, Grafana annotation (để runner v2).
- **Links:** nhánh `feat/runner`; `experiments/runner/`, `experiments/matrix-sim.yaml`, `experiments/tests/test_runner.py`, `.github/workflows/ci.yaml`.
- **Thesis:** §3 (thiết kế runner: các bước một lượt, tiêu chí hợp lệ), §4.3 (quy trình đo tự động, tái lập được), T2/T3 trên simulator lần 2 qua runner.
