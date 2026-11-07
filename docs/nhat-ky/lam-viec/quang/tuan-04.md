# Nhật ký làm việc – Quang – Tuần 04 (26/10–01/11)

## 2026-10-28 – Demo k3s một node trong Docker (chuẩn bị phỏng vấn)

- **Mã việc:** chung · **Môi trường:** không (máy dev, không GPU, không phải cluster nhà)
- **Đã làm:** chạy `rancher/k3s:v1.31.4-k3s1` trong container Docker privileged; deploy nginx 2 replica + Service + Ingress; gọi qua Traefik; xoá pod để xem tự phục hồi; scale 2 → 4; rolling update nginx:1.27 → 1.27-alpine.
- **Kết quả và số đo:** node Ready sau vài giây; Ingress trả HTTP 200; pod bị xoá được tạo lại sau ~8 s; rolling update xong 4/4, `rollout history` có 2 revision.
- **Sự cố:** lần đầu `kubectl apply -f -` qua `docker exec` thiếu cờ `-i` nên YAML không vào → thêm `-i`.
- **Khác thiết kế:** đây không phải playbook Ansible `infra/ansible`, chưa chạy trên PC 5060 / laptop 4050, chưa có GPU, Argo CD, Prometheus. k3s của đồ án đã chạy riêng trên PC từ 23/10 ([tuần 03](tuan-03.md)), demo này tách biệt với cluster đó.

## 2026-10-28 – Lab Argo CD trên k3s demo

- **Mã việc:** chung · **Môi trường:** không (cluster k3s trong Docker trên máy dev, không GPU)
- **Đã làm:** cài Argo CD v3.5.4 (`install.yaml`, có UI) vào k3s-demo; dựng git server (`git daemon`) chạy trong cluster; tạo Application `hello` với `automated.prune` + `selfHeal`; tạo `lab/argocd/` (manifest, README, 7 bài tập).
- **Quyết định và lý do:** git server trong cluster thay vì `git daemon` trên host, vì host lắng nghe 0.0.0.0 bị chặn và không muốn mở cổng ra mạng; không đẩy lên GitHub của dự án để khỏi lẫn với nhánh `main`.
- **Kết quả và số đo:** Application `Synced/Healthy`; sửa replicas 2→3 trong Git, sau refresh cluster có 3/3 pod (~12 s); `kubectl scale --replicas=1` bị Argo CD sửa về 3 trong ~12 s; UI trả HTTP 200.
- **Sự cố:** `alpine/git` không có `git daemon` → thêm `apk add git-daemon`. Application báo lỗi `connection refused` do cache lúc git server chưa lên → `refresh=hard`.
- **Khác thiết kế:** dùng `install.yaml` (có UI) thay vì `core-install.yaml` của role `argocd-bootstrap`, vì chạy lab local. Chưa chạy `root-app-home.yaml` thật.
- **Liên kết:** `lab/argocd/`.

## 2026-10-29 – Rà tiến độ dự án và lập danh sách việc sắp làm

- **Mã việc:** chung · **Môi trường:** không
- **Đã làm:** đối chiếu Kế hoạch §2, §3, §5.1 với `main`, các nhánh chưa merge và nhật ký cá nhân của hai người; tạo nhánh `docs/quang-w4-backlog` với `viec-sap-lam.md`.
- **Kết quả và số đo:**
  - M1 (18/10) chưa đạt: chưa có Argo CD, Prometheus, simulator, CI, V0; chưa chốt cloud. V1 (31/10–01/11) chưa có runner.
  - `main` có TR4 (cảnh báo, runbook) và TR5 (máy tạo tải), chưa chạy trên cluster.
  - Phần Quang: Q1, Q3 khoảng 70 % (k3s, GPU, vLLM chạy ở nhà từ 23/10) nhưng nằm trên `origin/feat/serving`, chưa mở PR; merge thử với `main` không xung đột. Q2, Q4, Q5, Q8 mới bắt đầu; Q6, Q7 chưa làm. Phần trăm là ước lượng theo đầu việc, không phải giờ đã dùng.
- **Quyết định và lý do:** P0 tuần này là merge `feat/serving` (Trình cần manifest trên `main` để làm Argo CD), chốt cloud và số phận V1/V2 với Trình, test graceful shutdown trong k8s, viết LT1–LT2 từ số đã có. Runner (Q6) dời sang W5 vì là đường găng của V2.
- **Sự cố:** mục 28/10 của tuần này (nhánh `feat/argocd-lab`) ghi "phần k3s của đồ án chưa chạy thật", mâu thuẫn với nhật ký tuần 03; đã sửa khi gom nhật ký tuần 04 về nhánh `docs/quang-w4`.
- **Liên kết:** `docs/nhat-ky/lam-viec/quang/viec-sap-lam.md`.
- **Dùng cho luận văn:** phần quản lý dự án (độ trễ so với kế hoạch, cách xử lý theo Kế hoạch §8).

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
