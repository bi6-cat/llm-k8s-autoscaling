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

## 2026-10-29 – LT2 có kết quả, LT1 có dự đoán (Q8)

- **Mã việc:** Q8 · **Môi trường:** không (máy dev không GPU; dùng số đo ngày 23/10)
- **Đã làm:** tải `config.json` và đọc kích thước `model.safetensors` của Qwen2.5-1.5B-Instruct ở revision đã ghim; tính byte/token của KV-cache và kích thước weights; viết LT2 và phần dự đoán của LT1 vào `docs/nhat-ky/van-hanh.md`.
- **Quyết định và lý do:** không dùng TPOT ở c = 8 (đã có) làm số đo LT1, vì Môi trường §19 yêu cầu batch = 1; chỉ ghi là số tham khảo. Đặt các mục LT vào nhánh `docs/lt1-lt2` nối sau `feat/serving`, vì `van-hanh.md` chỉ có ở đó.
- **Kết quả và số đo:**
  - LT2: dự đoán 28.672 B/token; đo (W1) 2,7 GiB ÷ 101.120 token ≈ 28.670 B/token, lệch < 0,01 %. "Maximum concurrency" = số token ÷ 4096 ở cả W1 (24,69x) và k3s (27,38x).
  - LT1: weights 3.087.467.144 B → TPOT ≥ 6,9 ms trên 5060 (448 GB/s, chưa kiểm), ≥ 16,1 ms trên 4050 (192 GB/s); thực tế dự kiến 8,3–9,6 ms trên 5060. Chưa đo batch = 1.
- **Còn phải làm (cần PC):** LT1 batch = 1 × 20 lần; kiểm băng thông bằng `nvidia-smi -q`; tách bộ nhớ từ log khởi động; giải thích +11.040 token KV trên k3s (giả thuyết: VRAM của desktop lúc chạy W1). LT1 trên 4050 cần laptop vào cluster.
- **Liên kết:** nhánh `docs/lt1-lt2`; `docs/nhat-ky/van-hanh.md`.
- **Dùng cho luận văn:** chương 5, mục kiểm chứng lý thuyết (LT2 trọn mẫu, LT1 phần dự đoán); chương 2 phần GQA và KV-cache. Nên có bảng LT2 như trong `van-hanh.md`.
