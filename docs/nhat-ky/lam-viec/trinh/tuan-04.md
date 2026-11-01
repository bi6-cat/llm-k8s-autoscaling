# Nhật ký làm việc – Trình – Tuần 04 (26/10–01/11/2026)

## 2026-11-01 – Chạy được yamllint và `make alerts-test` trên máy Windows

- **Mã việc:** chung (công cụ kiểm tra cục bộ) · **Môi trường:** không (máy cá nhân Windows 11 + Git Bash)
- **Đã làm:**
  1. Đổi `core.autocrlf` của bản clone từ `true` (mặc định của Git for Windows) sang `input`, rồi làm mới index và checkout lại (`git rm -r --cached -q .` + `git reset --hard -q`, khi cây đang sạch). File trên đĩa giờ là LF như trong Git.
  2. Cài GNU make 4.4.1 (winget, gói `ezwinports.make`) và yamllint 1.38.0 (`uv tool install`); chép promtool 3.13.4 (bản zip đã kiểm sha256 ngày 25/10) vào `~/.local/bin`.
- **Quyết định và lý do:**
  - `input` thay vì `false`: file CRLF lỡ tạo trên Windows vẫn được đổi thành LF khi commit. Đặt trong cấu hình của bản clone, không thêm `.gitattributes` vì đó là file chung.
  - Chạy chính Makefile (`make alerts-test`) thay vì gõ tay các lệnh tương đương, để không bị lệch khi recipe thay đổi. Truyền `SHELL=bash` vì Makefile đặt `SHELL := /bin/bash` (đường dẫn kiểu Linux), và chạy trong Git Bash để có `sed`, `tail`, `mktemp`. Chưa thử chạy khi không có `SHELL=bash`.
- **Kết quả và số đo:**
  - `yamllint -s observability .yamllint.yaml`: đạt. Trước khi đổi: lỗi `new-lines` ở cả 6 file; riêng `observability/alerts/llm.yaml` có 151 ký tự CR.
  - `make alerts-test SHELL=bash PROMTOOL=promtool` (trong Git Bash): `promtool check rules` và `promtool test rules` đều SUCCESS.
  - `uv run --project loadgen pytest loadgen`: 41 passed; `ruff check` và `ruff format --check`: đạt.
- **Sự cố:**
  - `git checkout-index --force --all` không ghi lại file nào: Git bỏ qua file có stat khớp index, kể cả khi có `--force`. Phải làm mới index như bước 1.
  - Chạy thẳng `promtool test rules observability/alerts/tests/llm-test.yaml` báo `field kind not found in type rulefmt.RuleGroups`, vì rule lưu dạng CRD `PrometheusRule`. Recipe `make alerts-test` tách phần `spec:` trước khi gọi promtool.
- **Còn thiếu:** `make lint` trọn vẹn (cần `ansible-playbook` và các thư mục chỉ có trong scaffold) và `make sim-*` (cần kind, Docker) vẫn chưa chạy được trên máy này. Hướng xử lý: CI (TR1) và WSL2.
- **Liên kết:** sự cố CRLF đã ghi trong mục TR4 của `tuan-03.md`.
