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
