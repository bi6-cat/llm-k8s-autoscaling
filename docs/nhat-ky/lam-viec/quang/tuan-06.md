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

## 2026-11-10 – ADR-006 và đồng bộ tài liệu thiết kế sau V0+V1

- **Task:** chung · **Environment:** none
- **Done:** (ghi bù ngày 12/11 theo lịch sử commit, phiên 10/11 chưa ghi nhật ký)
  1. Viết ADR-006: gom các quyết định 04–09/11 (chỉ còn Vast VM, 4 × RTX A4000 ≥ 20 vCPU, model 3B, N = 4, kịch bản 12/24/17 phút, KEDA `timeout` 1000 ms, truy vấn A1 mới, tạm chấp nhận grace 180 s) và bảng các hạng mục thiết kế chưa có trong repo; thêm `docs/adr/README.md`.
  2. Đồng bộ Thông số, Bài toán, mô tả tổng; Môi trường, Kế hoạch (theo CI thật); Kiến trúc, Vận hành (hành vi tắt pod đã đo, trạng thái repo).
  3. `.gitignore` bỏ cache của ruff và pytest.
- **Decision:** ghi một ADR gom thay vì sửa ADR-004/005 (quy tắc không sửa ADR cũ). ADR-003 vẫn để dành cho kết quả ĐG1 trong V2.
- **Links:** nhánh `docs/sync-after-v1`; commit `d6a0ef0`, `4be2338`, `acfa7c8`, `18dc033`, `7c94846`.
- **Thesis:** §3–§4 (thiết kế theo điều kiện thực tế), Hạn chế (A4000 + 3B thay 4090 + 7B; grace 180 s).

## 2026-11-12 – Đồng bộ nốt tài liệu với ADR-006

- **Task:** chung · **Environment:** none
- **Done:**
  1. Rà mọi file `.md` còn ghi giá trị trước ADR-006 (4090, 7B, GCP, V3, 20/25/25, đỉnh 3,0 C, query A1 cũ). Phần lớn chỗ còn lại là ghi chú lịch sử hợp lệ, giữ nguyên.
  2. Dòng trạng thái ADR-004 (K4, K5, K6, K9) và ADR-005 (T1) ghi bị ADR-006 thay.
  3. Bỏ V3 khỏi Môi trường §17 và Kế hoạch §8, §9 (dự phòng, rủi ro R4, ngưỡng ngân sách, runbook phiên): máy hỏng thì thuê máy Vast khác ngay trong 14–15/11.
  4. Kiến thức nền §1.3–§1.5: thêm Qwen2.5-3B và RTX A4000, kèm số đo 08/11.
  5. Vẽ lại Hình 6 (A4000, 3B, nhà 0,5B time-slicing, bỏ laptop 4050, cloud qua `make cloud-platform`) và Hình 9 (V0+V1 gộp 08/11, V2 14–15/11, bỏ V3, M3 22/11); xuất lại SVG và PNG 2x.
  6. W1, W2: thêm ghi chú đầu file rằng phần máy thuê đã lỗi thời, không viết lại.
  7. `viec-sap-lam.md`: đánh dấu PR #28–#32 đã merge 09/11, thêm việc họp chốt ADR-006 §3.
  8. Theo quyết định của Quang: đổi ví dụ 7B sang 3B trên A4000 ở Bài toán §1.2–§1.3, §2 và Kiến trúc pha 5, L1; Hình 12 pha 5 (≈ 30–60 s, ~6 GB). Dùng số đo 08/11: KV-cache 7,28 GiB, TPOT 17,2 ms (1 request) / 25,1 ms (32 request, 1.121 token/s), tải model 27 s.
  9. Ghi đề xuất của Quang cho ADR-006 §3 vào `viec-sap-lam.md` (làm trước V2: Argo CD app `autoscaling`/`observability`, Telegram cho Alertmanager); chưa chốt, chờ họp với Trình.
- **Decision:** Ví dụ trong Bài toán dùng số thật của 3B/A4000 thay vì 7B/24 GB: lộ ra giới hạn thật trên máy V2 là `--max-num-seqs` 64 chứ không phải KV-cache (đủ ~210 request). W1, W2 là hướng dẫn của tuần đã qua nên giữ làm tư liệu, chỉ gắn ghi chú. Hình 18, 19 (trạng thái dự kiến W1, W2) giữ nguyên vì cùng lý do. Hình 9 giữ các thanh W1–W4 theo kế hoạch gốc, chỉ thêm dòng việc bổ sung 04/11, vì đây là hình kế hoạch chứ không phải tiến độ thực tế.
- **Results:**
  - KV-cache 3B: vLLM báo 7,28 GiB = 211.936 token → ≈ 36.880 B/token; công thức 2 × 36 lớp × 2 KV head × 128 × 2 B = 36.864 B, lệch < 0,1 %.
  - TPOT 3B trên A4000 ở 1 request: 17,2 ms; cận dưới lý thuyết 6,17 GB ÷ 448 GB/s ≈ 13,8 ms → băng thông hiệu dụng ≈ 359 GB/s ≈ 80 % (1,5B trên 5060: 79 %). Đây là tính lại từ số đo 08/11, không đo mới.
  - `build_diagrams.py` chạy lại trên code cũ không đổi SVG nào (sinh hình ổn định); sau khi sửa chỉ Hình 6, 9 đổi.
- **Incidents:** bản nháp ngân sách VRAM ghi 14.416 MiB = 14,4 GiB; đúng là ≈ 14,1 GiB (14,4 GiB là mức 0,90 cho phép). Sửa trước khi commit. Nhãn M3 và M5 ở Hình 9 đè nhau sau khi dời M3 sang 22/11; sửa bằng căn phải.
- **Links:** nhánh `docs/sync-after-v1` (chưa push); `docs/chi-tiet/02-kien-thuc-nen.md`, `docs/diagrams/build_diagrams.py`, `docs/adr/004-*.md`, `docs/adr/005-*.md`.
- **Thesis:** §2 (kiến thức nền: KV-cache, giới hạn decode với số đo A4000), LT1, LT2; Hình 6, 9 cho chương 3 và phần kế hoạch.
