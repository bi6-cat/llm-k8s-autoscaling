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
