# Nhật ký làm việc – Quang – Tuần 06 (09–15/11/2026)

## 2026-11-09 – Đưa phần dọn dẹp 08/11 vào `main` sau khi PR #27 merge nhầm base

- **Task:** chung · **Environment:** none
- **Done:** rà công việc đầu tuần, phát hiện `main` thiếu 7 commit; tạo `chore/v2-prep-to-main` từ `origin/feat/v2-prep`, gộp `origin/main`; sửa mục nhánh và PR trong `viec-sap-lam.md`.
- **Results:** gộp không conflict. Trên bản gộp: pytest `experiments` 126 passed, `loadgen` 55 passed.
- **Incidents:** PR #27 có base `feat/v2-prep` (xếp chồng trên PR #26). PR #26 merge trước nên PR #27 merge vào nhánh `feat/v2-prep` và GitHub vẫn báo `MERGED`, trong khi `main` thiếu sửa UTIL của `capacity.py`, đồng bộ tài liệu, handoff mới. Cách tránh: trước khi merge PR dưới, đổi base PR trên về `main`, giống bài học PR #24/#25 của Trình.
- **Links:** nhánh `chore/v2-prep-to-main`; PR #26, #27.

## 2026-11-09 – Sửa truy vấn A1 thay Trình (TR2)

- **Task:** TR2 (Quang làm thay, đã ghi ở thư mục Trình) · **Environment:** none
- **Done:** chạy lại tín hiệu A1 trên `metrics.csv.gz` của lượt V1 `A1-KB3-1` với nhiều cửa sổ; đổi query sang `avg_over_time(…[15s])` trên từng GPU trước khi cộng; kiểm PromQL bằng `promtool test rules`.
- **Decision:** không dùng được "chỉ GPU của pod Ready" vì exporter không có label pod. So 4 phương án trên dữ liệu V1, chọn trung bình 15 s: hạ mẫu đơn lẻ mà trễ ít. `min_over_time` cũng hết kẹt nhưng một mẫu thấp đơn lẻ sẽ kéo tụt cả tín hiệu khi tải thật. Không so A1 với cấu hình cũ của 2 lượt V1, vì tín hiệu đã đổi.
- **Results:**
  - Tín hiệu lớn nhất sau tải (14:16 trở đi): gốc 100, avg 15 s 33,3, avg 30 s 16,7, avg 60 s 8,3, min 15 s 0. Với threshold 70, chỉ bản gốc cho desired = 2.
  - Mốc desired 2 / 3 / 4 so với gốc: avg 15 s trễ 10 / 5 / 20 s; avg 30 s trễ 20 / 10 / 20 s; avg 60 s trễ 40 / 20 / 25 s.
  - `promtool` (prom/prometheus v3.5.0, CI dùng 3.15.0): một mẫu 100 % trên một GPU → 33,33; 20 s sau → 0. pytest `experiments` đạt.
  - Chưa đo: chưa chạy query này với KEDA trên cluster nào; lần đầu sẽ là V2. Đây là phép tính lại trên một lượt, tức một lần xuất hiện của lỗi.
- **Deviations:** Thông số §8.1 đổi query. A1 phản ứng chậm hơn tối đa khoảng 20 s so với query cũ.
- **Links:** nhánh `fix/a1-transient-gpu-sample`; `autoscaling/eval/A1.yaml`.
- **Thesis:** §5 (LT6, GPU util là tín hiệu kém: phải làm mượt để tránh một mẫu nhiễu giữ replica).

## 2026-11-09 – Tự động hoá VM thuê, sao lưu R2, systemd, Telegram, kịch bản VH2–VH5

- **Task:** Q2, Q5, Q6, Q7 · **Environment:** sim (kind `llm-sim`); chưa chạy trên VM
- **Done:**
  1. `vast.sh`: bộ lọc v2 mặc định `RTX_A4000`, CPU ≥ 8 + 3N, RAM ≥ 24 GB/GPU, bỏ `inet_down`; thêm `probe`, `platform`, `runner-start`, `target`. `release` từ chối khi R2 chưa đủ dữ liệu.
  2. Role Ansible `cloud-prefetch`: tải model, kéo image chạy nền; bootstrap chờ cả hai xong. `make prefetch`, `make cloud-platform`.
  3. `experiments/runner/backup.py` (đẩy R2 sau mỗi lượt), `notify.py` (Telegram), `llm-runner.service`; `make run`, `make backup`, `make backup-check`.
  4. `experiments/ops/vh.py` (vh2a, vh2b, vh2c, vh3-delete, vh3-kill, vh3-drain, vh4), `infra/provision/vh5.sh`; `make ops-tests`, `make vh5`.
- **Decision:**
  - Sao lưu lỗi không dừng phiên: đo tiếp có giá trị hơn, lần sau đẩy bù, và `release` vẫn chặn. Phiên cloud không có đích sao lưu thì từ chối chạy, trừ khi có `--no-backup`.
  - systemd gửi SIGINT thay vì SIGTERM, để khối `finally` của lượt chạy.
  - Rollout trong VH2 kích hoạt bằng annotation, không qua Git, để lặp lại được trên VM chưa có Argo CD.
- **Results (kind, không có GPU; chỉ kiểm logic, không phải số đo hiệu năng):**
  - Runner `A2-CONST2-1` có sao lưu bằng rclone v1.71.2 (đích là thư mục cục bộ): `done`, 24 file, `check` đạt.
  - vh3-delete (2 req/s): 582 request, 0 lỗi, pod thay sau 10,1 s. vh2b (2 req/s): 831 request, 0 lỗi, rollout 3 pod 16,6 s.
  - vh4 (0,2 req/s, chặn 90 s): 1 → 3 replica, fallback sau 18,8 s (N6 ≤ 30 s), 68 request, 0 lỗi; gỡ chặn thì hết Fallback.
  - vh2a (0,2 req/s): xuất phát 1 replica, rollout 12,5 s, 87 request, 0 lỗi. vh3-drain (0,2 req/s): hồi phục 22,1 s, 68 request, 0 lỗi.
  - vh2c: báo không đạt, đúng dự đoán vì simulator không giới hạn GPU nên không kẹt. vh3-kill: báo không đạt, đúng dự đoán vì simulator không có tiến trình con. Hai đường đạt này **chưa kiểm được**.
  - pytest `experiments` 145 đạt; `ruff`, `yamllint` đạt; `ansible-playbook --syntax-check` đạt với inventory home và cloud; `shellcheck -S warning` sạch.
  - Khảo sát Vast 09/11 (lúc chiều tối, không qua `vast.sh`): chỉ 3 offer VM 4 GPU (4 × 5090 $2,404/giờ, độ tin cậy 95 %; 4 × 4090 $2,669/giờ, 99 %; 4 × 5090 $3,468/giờ, 95 %), vài phút sau chỉ còn offer $2,404. Không có offer VM 4 × A4000; có 1 offer 4 × A4000 không bật VM ($0,647/giờ, 28 vCPU).
  - **Chưa chạy:** `make bootstrap` với role mới, `make probe`, `make cloud-platform`, `make vh5`, `make run` với systemd, `release` có chặn: tất cả cần VM thuê. R2 và Telegram chưa thử với tài khoản thật vì máy chưa có `.env`. VH trên GPU thật chưa chạy.
- **Incidents:**
  - Lần chạy kind đầu cho 3 kết quả đạt oan do lỗi script: vh4 báo fallback 0,09 s vì tải đã đẩy lên max từ trước; vh2a không xuất phát từ 1 replica; vh3-drain đo hồi phục sau khi `drain` đã xong. Sửa: đòi Fallback=True và kiểm điều kiện đầu vào, thêm test, chạy lại với tải thấp.
  - vh3-drain lần hai mất toàn bộ kết quả vì pod máy tạo tải nằm chung node bị drain. Sửa: cordon node đó trước khi khởi động tải.
  - Ghi nhầm `huggingface_hub` 1.4.0 (đúng 2.4.0); `include_role` không truyền tag nên `--tags prefetch` không làm gì, đổi sang `import_role`. Đều phát hiện trước khi commit.
  - `make backup` sẽ đẩy cả `runs/vast-v2b-20261108/api-key.secret` lên R2. Sửa: loại `*.secret`, `*.bak`; kiểm bằng rclone thật.
  - Merge PR #28 bị bộ phân quyền của Claude Code chặn vì chưa có review; chưa merge, chờ Quang quyết.
- **Deviations:** VH2 qua annotation thay vì Git + Argo CD (Vận hành §5.3); ở nhà vẫn phải làm theo quy trình Git. Runner trên VM clone repo công khai thay vì chép từ laptop.
- **Links:** nhánh `feat/cloud-automation`, `feat/runner-backup-notify`, `feat/ops-scenarios`.
- **Thesis:** §4 (tự động hoá dựng VM, sao lưu, chạy không người trực), §5 VH2–VH5 (chỉ dùng số đo trên GPU thật), Hạn chế (ít máy VM 4 GPU trên Vast).
