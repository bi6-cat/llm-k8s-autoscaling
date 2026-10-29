# Nhật ký làm việc – Quang – Tuần 04 (26/10–01/11)

## 2026-10-29 – Tách Q1 thành PR riêng, sửa `make lint`

- **Mã việc:** Q1 · **Môi trường:** không (máy dev không GPU)
- **Đã làm:**
  1. Tạo nhánh `feat/home-k3s` tại commit cuối phần Ansible của `feat/serving` (`3cb962c`), merge `origin/main` vào (có TR4, TR5 của Trình).
  2. Sửa target `lint` trong `Makefile`: thư mục kustomize chưa có thì in "bỏ qua" thay vì lỗi.
  3. Cài `yamllint` 1.38.0 bằng `uv tool install`; chạy `make lint`.
- **Quyết định và lý do:**
  - Tách `feat/serving` (1.315 dòng) thành 2 PR xếp chồng: A = Q1 (ghim image, Ansible, `platform/gpu/`), B = Q3 (`serving/`), vì CONTRIBUTING §7 khuyên PR dưới 400 dòng và một PR một việc. A vẫn ~840 dòng, phần lớn là role Ansible lấy từ scaffold.
  - Merge `main` vào thay vì rebase: không phải force-push `feat/serving` đã có trên GitHub, và sửa `Makefile` trên bản đã có phần `observability` của TR4 nên không xung đột về sau.
  - In "bỏ qua" thay vì bỏ qua im lặng, để thấy rõ thư mục nào chưa được kiểm.
- **Kết quả và số đo:** trước khi sửa, `make lint` lỗi `must build at directory: not a valid directory` ở `autoscaling/official/overlays/*` và `platform/kube-prometheus-stack/extras` (trên `main` hỏng cả `serving/overlays/*`). Sau khi sửa: `yamllint -s .` sạch, `kubectl kustomize` đạt ở `platform/gpu/exporter` và `observability`, `ansible-playbook --syntax-check` đạt (ansible-core 2.16.3 trên máy dev, PC dùng 2.21.5), exit 0.
- **Khác thiết kế:** role `argocd-bootstrap` cần `platform/argocd/root-app-*.yaml` (TR1, chưa có), nên tới khi có TR1 phải chạy playbook với `-e argocd_enabled=false`.
- **Liên kết:** nhánh `feat/home-k3s`; `Makefile`.
- **Dùng cho luận văn:** §4.2 (quy trình PR, lint trước khi merge).
