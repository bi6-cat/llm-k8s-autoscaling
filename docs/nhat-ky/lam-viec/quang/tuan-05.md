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
