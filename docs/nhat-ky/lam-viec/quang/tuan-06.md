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
- **Links:** PR #33 (nhánh `docs/sync-after-v1`); `docs/chi-tiet/02-kien-thuc-nen.md`, `docs/diagrams/build_diagrams.py`, `docs/adr/004-*.md`, `docs/adr/005-*.md`.
- **Thesis:** §2 (kiến thức nền: KV-cache, giới hạn decode với số đo A4000), LT1, LT2; Hình 6, 9 cho chương 3 và phần kế hoạch.

## 2026-11-12 – Chốt phạm vi ADR-006 §3 và xác nhận của Trình

- **Task:** chung · **Environment:** none
- **Done:**
  1. Ghi quyết định vào ADR-006 §3.1, cập nhật chỉ mục ADR; bỏ khỏi bảng việc mở các mục "họp chốt §3" và "Trình review C7".
  2. Đồng bộ Thông số (F4, F7, danh sách đã bỏ), Bài toán §12.3 (thêm Hạn chế 10), Vận hành §8, Môi trường §3.7, Kế hoạch (TR1, nguyên tắc bí mật), bản bàn giao.
- **Decision:** tiêu chí của Quang: **hội đồng không nhìn thấy thì lược**.
  - Làm trước V2: Argo CD app `autoscaling`/`observability` (TR1; F3 Must, thấy trên giao diện Argo CD) và Alertmanager → Telegram (TR4; F6 Must, thấy trong demo).
  - Lược: Sealed Secrets, NetworkPolicy thường trực và rate limit (F7 chỉ là Should), Argo CD trên VM (F4 vẫn đạt bằng `make`), các lệnh `make burnin`/`capacity`/`analysis`. Việc đo ĐG1 → ADR-003 và biểu đồ chương 5 vẫn làm.
  - Trình đồng ý toàn bộ qua tin nhắn ngày 12/11, gồm cả truy vấn A1 (ADR-006 C7). PR #29 vẫn không có review trên GitHub.
- **Deviations:** F7 chỉ còn API key và mạng riêng; VH2 trên VM không qua Git. Cả hai đã ghi vào Hạn chế (Bài toán §12.3 mục 10).
- **Links:** PR #33; `docs/adr/006-chot-may-model-va-kich-ban-truoc-v2.md` §3.1.
- **Thesis:** §1 hoặc §3 (phạm vi và lý do lược), Hạn chế mục 10.

## 2026-11-13 – Tái cấu trúc repo theo môi trường và báo cáo kỹ thuật HTML

- **Task:** chung · **Environment:** sim (kind `llm-sim`); không đụng cluster nhà và VM
- **Done:**
  1. Chuyển repo sang `envs/{home,cloud,sim}/` (chạy ở đâu) + `common/` (chạy cái gì) + `ansible/`, bằng `git mv`; sửa mọi tham chiếu bằng một lượt thay theo bảng ánh xạ, rồi sửa tay phần còn lại (đường dẫn tương đối trong kustomization, `cd ../../..` của script, role Argo CD, test Python, regex của job docs trong CI).
  2. Gộp overlay `cloud` (7B) và `cloud-3b` thành một overlay `envs/cloud/serving` (3B); bỏ 7B.
  3. `make help` chia nhóm theo môi trường; sửa lỗi cũ: regex không khớp target có chữ số nên `vh5` không hiện. Các lệnh `burnin`/`capacity`/`analysis` in lệnh thay thế (ADR-006 §3.1).
  4. README gốc viết lại; thêm README cho `envs/home`, `envs/cloud`, `envs/sim`; CONTRIBUTING §1 mô tả cấu trúc mới; Hình 6 vẽ lại khối repo.
  5. Báo cáo kỹ thuật `docs/bao-cao/bao-cao-ky-thuat.html` (đăng artifact riêng tư): kiến trúc, số đo 08/11, mô phỏng ma trận V2, hướng nâng cấp (lý thuyết hàng đợi, A2 dự báo, JSQ).
  6. Viết lại báo cáo chi tiết hơn theo yêu cầu (17 mục): thuật ngữ, minh hoạ bài toán, một request đi qua hệ thống, GitOps, vòng autoscaling từng bước, tín hiệu scale, ba kịch bản tải, timeline tắt pod, chi phí quy ra USD, lộ trình nâng cấp, hỏi đáp khi bảo vệ. Thêm số đo mới trích từ `runs/dg1-v1-a4000/`: GPU util của GPU có pod = 100 % ở cả 5 mức λ (2–6 req/s), request đang chạy 12,1 / 39,6 / 51,6 / 63,6 / 63,4, KV-cache 4,3–22,8 %; request trung vị tại λ = 2: TTFT 0,18 s, E2E 6,14 s; tại C: TTFT 0,30 s, E2E 11,51 s.
- **Decision:**
  - Giữ Kustomize base + overlay (base ở `common/`), không nhân đôi manifest theo môi trường.
  - Giữ nguyên tên lệnh `make` (ADR và nhật ký dùng chúng), chỉ nhóm lại trong `make help`.
  - Nhật ký, ADR, hướng dẫn W1/W2 giữ đường dẫn cũ (tư liệu); CI vẫn bỏ qua link tới đường dẫn cũ.
  - Báo cáo dùng số thật 08/11 + mô phỏng có nhãn cho ô chưa chạy (Quang chọn).
- **Results:**
  - 10 thư mục kustomize render **giống từng byte** trước và sau (kể cả `envs/cloud/serving` so với `serving/overlays/cloud-3b` cũ).
  - pytest `experiments` 146 passed (bằng `main`), `loadgen` 55 passed; ruff, yamllint, ansible syntax-check, shellcheck sạch; `make alerts-test` (promtool 3.15.0) 7 cảnh báo + 2 file rule đạt; `make dashboards-check` 3 dashboard đạt.
  - `make sim-up` trên kind mới: exit 0, A2 được tạo từ `envs/sim/autoscaling`. Runner `--dry-run` đọc được 5 ma trận ở chỗ mới; `matrix-v2.yaml` từ chối vì C và threshold còn trống (đúng thiết kế).
  - **Chưa chạy:** `make sim-test` (máy chưa có `hey`; tải binary bị chặn). Chưa thử `make home-up`, `make cloud-platform` với đường dẫn mới trên máy thật.
  - Mô phỏng hiệu chỉnh bằng 2 lượt V1: A2×KB2 spike 64,6 % so với thật 62,7 %; A1×KB3 ramp 79,9 % so với 88,6 %, sustain 99,8 % so với 99,9 %. Kết quả (5 seed): A1 tốn 86–93 % GPU-giờ của S4 ở mọi kịch bản; A2 KB1 0,20 GPU-giờ (= S1), KB2 SLO 71,9 %; A2 dự báo đưa KB3 từ 88,8 % lên 96,9 % (+4 % GPU-giờ) nhưng KB1 tốn gấp đôi.
  - Hàng đợi đỉnh ở pod cũ (A2×KB2) đo 1.041, công thức (λ − C) × timeout 120 s = 1.080.
- **Incidents:**
  - `git stash` / `stash pop` làm mất các rename trong index, khiến danh sách file của lượt thay thiếu file đã dời → `git add -A` rồi chạy lại.
  - Mẫu `observability/` trong lượt thay đầu có lookahead chặn mọi đường dẫn con → gần như không thay; phát hiện khi `make alerts-test` lỗi, sửa bằng lượt riêng.
  - Bốn script và role Argo CD tính gốc repo theo số tầng (`../..`), sai sau khi sâu thêm một tầng; không công cụ kiểm nào bắt được, tìm bằng grep.
  - Mô phỏng: lần đầu tính GPU-giờ cả phần sau khi lượt kết thúc (A1×KB1 > S4, vô lý) → giới hạn trong thời lượng lượt. Bản nháp báo cáo có chia pha cold start lần 2 không có trong log → bỏ, ghi "chưa tách".
- **Deviations:** CONTRIBUTING §1 đổi từ chia theo thành phần sang chia theo môi trường; overlay 7B mà ADR-006 C3 ghi "giữ tham khảo" đã xoá (còn trong lịch sử Git).
- **Links:** nhánh `refactor/split-home-cloud`; `CONTRIBUTING.md`, `envs/*/README.md`, `docs/bao-cao/`.
- **Thesis:** §3–§4 (cấu trúc repo, ba môi trường); §5 (mô phỏng có hiệu chỉnh, chỉ dùng làm ước lượng); Hướng phát triển (lý thuyết hàng đợi, autoscaling dự báo, JSQ).

## 2026-11-13 – Tờ trình nâng cấp V3 trên cloud (chờ duyệt)

- **Task:** chung · **Environment:** none (mô phỏng trên laptop)
- **Done:**
  1. Quang quyết định từ nay chỉ tập trung cloud và yêu cầu nghiên cứu nâng cấp để có thêm phần làm và demo. Nghiên cứu hệ sinh thái: Gateway API Inference Extension (endpoint picker, nay ở llm-d), vLLM production-stack router, NVIDIA Dynamo SLA planner, AIBrix, sleep mode của vLLM, Run:ai streamer, bài MLSys 2026 "Breaking the Ice" về cold start, trace Azure 2024 và BurstGPT. Kiểm mã nguồn vLLM v0.31.0: có `max_num_queued_reqs` (quá giới hạn trả 503).
  2. Phân rã cold start 152 s (log 08/11): lập lịch + probe 9 s, import Python + khởi tạo engine 77 s, nạp weights 11 s, torch.compile 27 s, CUDA graph + KV-cache + warmup 28 s → tăng tốc nạp model gần như không rút được cold start.
  3. Mở rộng mô phỏng (`docs/bao-cao/de-xuat-v3/mo_phong_v3.py`): chặn quá tải mỗi pod, pool pod ngủ sẵn, dự báo bằng hồi quy 120 s + ngưỡng chết, kịch bản quá tải (đỉnh 4 C và 5 C).
  4. Viết tờ trình 9 hạng mục Đ1–Đ9 (`docs/bao-cao/de-xuat-v3/to-trinh.html`, đăng artifact riêng tư), kèm lịch 14–22/11, ma trận V3, chi phí, rủi ro, kịch bản demo 10 phút.
- **Decision:** (đề xuất, **chưa duyệt**) giữ nguyên V2; thêm phiên V3 20/11 (~8 giờ, ≈ 5 USD) và ADR-007; bắt buộc Đ1 gateway LeastRequest, Đ2 A3 = A2 + `predict_linear`, Đ3 `--max-num-queued-reqs=75` (định lý Little: 64 + C × 2,5 s), Đ7 Argo CD + Telegram + dashboard demo trên cloud, Đ9 V3 + demo. Loại: pool pod ngủ sẵn (KB2 chỉ 71,9 → 74,7 %, KB1 tốn gấp đôi), Run:ai streamer, KServe, endpoint picker đầy đủ, rate limit theo token.
- **Results:** mô phỏng, 5 seed mỗi biến thể (không phải số đo):
  - KB2 đạt SLO: A2 71,9 %; + gateway (JSQ) 83,5 %; A3 79,7 % (dao động 71–100 %); A3 + gateway 88,4 %; A3 + gateway + chặn 75 là 94,0 % (từ chối 3,6 %), GPU-giờ 1,41 so với S4 1,60.
  - KB3: A2 88,8 % → A3 96,2 % → đủ ba nâng cấp 98,8 %. KB1 GPU-giờ: A2 0,20, A3 0,31, A3 + gateway 0,40.
  - Quá tải đỉnh 5 C: S4 18,7 % → 78,2 % khi chặn 75; chặn 68 thì phần được nhận đạt ~100 %, từ chối 10–18 %.
- **Incidents:** mô phỏng "dự báo" của báo cáo kỹ thuật bản 2 có lỗi: giá trị đã ngoại suy bị ghi vào lịch sử metric (vòng phản hồi). Sửa xong: KB3 96,9 → 96,2 %, KB2 80,9 → 79,7 %, KB1 0,40 → 0,31 GPU-giờ; kết luận không đổi. **Chưa** cập nhật báo cáo kỹ thuật.
- **Links:** nhánh `refactor/split-home-cloud`; `docs/bao-cao/de-xuat-v3/`.
- **Thesis:** §5 (phân rã cold start), Hướng phát triển (gateway, autoscaling dự báo, admission control, goodput); nếu V3 chạy thì thành mục §5.x "Cải tiến".

## 2026-11-13 – Tờ trình V3 bản 2: đánh giá lại trên tải thật BurstGPT

- **Task:** chung · **Environment:** none (mô phỏng trên laptop)
- **Done:**
  1. Quang nhận xét bản 1 "đơn giản nhưng hiệu quả có vẻ không sát thực tế", hỏi đỉnh tải lên rồi xuống ngay thì sao, và yêu cầu ưu tiên chất lượng, bỏ phần hội đồng không thấy được.
  2. Tải trace BurstGPT_1 (HPMLL, CC-BY-4.0; 61 ngày, 1,43 triệu request). Trace Azure 2024 không tải được (blob bị chặn DNS). Viết `chuan_bi_trace.py`: thống kê độ dài đỉnh, chọn 8 cửa sổ 30 phút train (ngày 0–39), 8 test (ngày 40–60), 2 ngày trọn (41, 59); chỉ lấy nhịp thời gian, co để phút bận nhất = 0,9 × 4 × C.
  3. Viết `mo_phong_thuc_te.py` (kế thừa tham số hiệu chỉnh của `mo_phong_v3.py`): client thử lại 2 lần như SDK OpenAI, kịch bản KB-ngắn (3 C trong 60 s, ba lần), planner P (chặn 75 + cộng nhu cầu bị chặn theo định lý Little + tham số τ, hold, huỷ pod chưa Ready), biến thể cold start 60 s và 15 s, quét ngưỡng để vẽ đường đánh đổi.
  4. Tìm hiểu ngoài thực tế: NVIDIA Dynamo Snapshot, Cerebrium (cuda-checkpoint + CRIU khôi phục vLLM trong vài giây), llm-d WVA (planner xuất `wva_desired_replicas` cho KEDA).
  5. Viết lại tờ trình (`to-trinh.html`, đăng lại cùng link): 5 hạng mục Đ1 gateway, Đ2 chặn + báo lại cho autoscaler, Đ3 snapshot (khó, điểm dừng 18/11 20:00), Đ3b rút cold start rẻ, Đ4 trace trong loadgen, Đ5 lớp demo.
- **Decision:** (đề xuất, **chưa duyệt**) bỏ A3 `predict_linear`, bỏ kho model R2, gộp chi phí theo token vào dashboard. Chọn tham số planner trên train theo luật "rẻ nhất trong các bộ có SLO cách tốt nhất ≤ 1 điểm": τ = 0, hold = 300 s, không huỷ pod.
- **Results:** (BurstGPT là dữ liệu thật; mọi % SLO, GPU-giờ là **mô phỏng**, 5 seed)
  - Độ dài đỉnh (vượt 2 × nền 10 phút): < 2 phút chiếm 83,8 % số đỉnh nhưng 5,3 % tải dư; ≥ 15 phút chiếm 3,6 % số đỉnh, 73,6 % tải dư. Train: đỉnh đã kéo dài 90 s thì 52 % khả năng còn đủ lâu cho pod mới (cold 110 s); test cao hơn (68 %), phân bố thay đổi theo thời gian.
  - Train (cold 110 s): τ 0 → 30 s: SLO 90,5 → 84,3 %, GPU 94,4 → 84,6 %; hold 120 s: 86,8 % và GPU 98,0 % (tắt bật liên tục); huỷ pod: 83,9 %.
  - Test (8 cửa sổ, SLO / GPU % của S4): A2 80,7/87; A2 + gateway 82,7/89; A3 + gateway 88,0/90; P 90,3/89 (bị chặn 6 %); P cold 60 s 93,9/88; P cold 15 s 97,9/88.
  - Trọn ngày: A2 92,3 % / 42 %; P 95,7 / 43; P cold 15 s 99,2 / 41. KB-ngắn: A2 71,7 %, P 77,1 %, P cold 15 s 95,7 %.
  - Chặn mà không báo lại cho autoscaler: KB2 77,5 % (thấp hơn A2 + gateway 82,0 %), vì request bị chặn biến mất khỏi metric hàng đợi.
- **Incidents:** lần đầu co trace theo token ra (request BurstGPT trung vị 34 token) cho cửa sổ tới 44 req/s, vượt phạm vi hiệu chỉnh → đổi sang co theo số request, giữ kích thước request của bộ đo. Lỗi trùng tên biến `mt` trong nhánh A3 làm vỡ lượt chạy đầu; sửa và chạy lại. Bản nháp tờ trình so 71,0 % (cả lượt) với 62,7 % (pha spike) → sửa trước khi đăng.
- **Deviations:** tờ trình bản 1 cùng ngày bị thay toàn bộ. Báo cáo kỹ thuật bản 2 **chưa** cập nhật theo kết quả mới. Chưa kiểm cờ `--max-num-queued-reqs` đếm hàng chờ hay tổng, chưa kiểm tên metric 429 của Envoy.
- **Links:** nhánh `refactor/split-home-cloud` (chưa commit); `docs/bao-cao/de-xuat-v3/chuan_bi_trace.py`, `mo_phong_thuc_te.py`, `cua-so-trace.json`, `ket-qua-thuc-te.json`, `to-trinh.html`.
- **Thesis:** §5 (đánh giá trên trace thật, đường đánh đổi SLO–GPU, đỉnh ngắn hơn cold start), Hạn chế (mô phỏng, chỉ lấy nhịp trace), Hướng phát triển (dự báo bằng mô hình học trên BurstGPT); nếu Đ3 chạy thì thành mục riêng về snapshot.

## 2026-11-13 – Bốn hướng nâng cấp bài toán; quét cửa sổ scale-down theo ski-rental

- **Task:** chung · **Environment:** sim
- **Done:** Viết trang `cac-huong-nang-cap.html` (4 hướng: ngưỡng từ Little's law, cửa sổ scale-down theo ski-rental, planner hybrid dự báo chu kỳ ngày, định tuyến LeastRequest) để duyệt trước khi sửa tờ trình V3. Viết `mo_phong_cua_so.py` quét H ∈ {0, 60, 120, 180, 300, 450, 600, 900} s × cold start {110, 60, 15} s, planner thuần (adm=None, τ=0, không huỷ pod), 8 cửa sổ test × 3 seed + 2 ngày trọn; kết quả `ket-qua-cua-so.json`.
- **Decision:** Khung luận văn "lồng nhau": Mô hình → Chính sách → Đánh giá, trong đó ma trận V2/V3 đo trên cụm là lớp Đánh giá và nguồn hiệu chỉnh; mô phỏng chỉ quét ô không có tiền chạy. Loại Đ2 "chặn 429 + báo lại autoscaler" khỏi tờ trình (là lớp bảo vệ cuối, không phải đóng góp; với người dùng là lỗi). Loại A3 `predict_linear`. Bài đỉnh ngắn ghi thành giới hạn, không giải. Hướng 3 chỉ đưa vào V3 nếu mô phỏng cho ≥ 2 điểm SLO hoặc ≥ 3 điểm GPU-giờ trên 2 ngày test.
- **Results:** (mô phỏng) GPU-giờ thấp nhất ở H = 180 s với cả ba cold start (test 87,3 / 86,8 / 85,3 %), đúng bằng grace 180 s; H = 0: SLO 66,8 %, GPU 95,4 %, 12 lần bật mỗi cửa sổ. 180–600 s GPU gần phẳng (± 1,5 điểm) trong khi SLO cold 110 tăng 80,1 → 84,4 %; quá 600 s ngày trọn tốn thêm (43,8 → 46,2 %). Cold start ngắn làm H ít nhạy: chênh SLO 180↔600 s là 4,3 / 2,8 / 1,1 điểm cho cold 110 / 60 / 15. Mặc định 300 s nằm trong vùng tối ưu.
- **Incidents:** Chạy đầu bị người dùng dừng khi mình định tra web; viết từ kiến thức sẵn, chưa kiểm lại nguồn trực tuyến. Số "hold 120 s → GPU 98 %" ở lưới train hôm trước không lặp lại trong quét thuần (87,5 %): lưới train có kèm chặn 429 và τ, không tách riêng hiệu ứng H; dùng số quét mới.
- **Deviations:** Cận dưới của cửa sổ scale-down đến từ grace period, không từ cold start như mình đoán ban đầu; đã sửa lý luận trên trang.
- **Links:** `docs/bao-cao/de-xuat-v3/cac-huong-nang-cap.html`, `mo_phong_cua_so.py`, `ket-qua-cua-so.json` (chưa commit).
- **Thesis:** chương Chính sách, mục cửa sổ scale-down (hình SLO theo H, bảng H); phần giới hạn phương pháp (đỉnh ngắn).

## 2026-11-13 – Hướng 1 (quét ngưỡng × cold start) và hướng 3 (dự báo Holt-Winters): kết quả

- **Task:** chung · **Environment:** sim
- **Done:** `mo_phong_nguong.py` quét thr ∈ {16…64} × cold {110, 60, 15} s, planner thuần H = 300 (→ `ket-qua-nguong.json`). Thêm hook `_pro` vào `mo_phong_thuc_te.simulate` (chuỗi proactive chỉ được nâng desired). `du_bao_mua_vu.py`: Holt-Winters cộng tính khung 10 phút trên BurstGPT ngày 0–39 (chọn α, γ trên ngày 30–39), dự báo ngày 41 và 59, mô phỏng hybrid vs A2+G (→ `ket-qua-du-bao.json`). Cập nhật `cac-huong-nang-cap.html` bản 5.
- **Decision:** Hướng 3 không đưa vào V3 (không đạt ngưỡng ≥ 2 điểm SLO hoặc ≥ 3 điểm GPU-giờ); viết thành kết luận âm có phương pháp. Hướng 1 giữ: công thức thr ≈ 74 − 0,5·(cold + 12) khớp dữ liệu.
- **Results:** (mô phỏng) Cùng SLO ≈ 90 % trên test: cold 110 cần thr 16 (GPU 92,5 %), cold 15 cần thr 64 (GPU 79,2 %); ngày trọn cùng SLO ≈ 96,5 %: 55,3 → 36,8 % GPU. Ngưỡng tĩnh không tối ưu cho cả hai loại tải: hạ 42 → 16 trên test +9,8 SLO / +3,8 GPU, trên ngày trọn +4,5 SLO / +12,8 GPU. Holt-Winters dự báo gần phẳng (1,6–2,1 và 3,7–4,3 req/s) trong khi tải thật theo giờ 0 → 10,7 req/s; WAPE 108 % / 140 %; nền ≈ 0,4 C nên proactive = 1 pod mọi khung; hybrid 92,5 % / 42,6 % so với A2+G 92,4 % / 42,7 % (cold 110).
- **Incidents:** `python3 -I` bỏ thư mục script khỏi `sys.path` → `ModuleNotFoundError: mo_phong_thuc_te`; sửa bằng `sys.path.insert(0, dirname(__file__))`. MAPE vô nghĩa (hàng trăm %) vì nhiều khung đêm gần 0; chuyển sang WAPE.
- **Deviations:** Ban đầu kỳ vọng hướng 3 có lợi ở ramp buổi sáng; dữ liệu cho thấy BurstGPT không có nhịp ngày đủ mạnh ở quy mô 4 GPU. Chưa kiểm định lượng độ mạnh chu kỳ trên 61 ngày và chưa chạy ở quy mô nền 2–3 pod (việc tiếp theo, ~1 giờ).
- **Links:** `docs/bao-cao/de-xuat-v3/{mo_phong_nguong.py, du_bao_mua_vu.py, ket-qua-nguong.json, ket-qua-du-bao.json, cac-huong-nang-cap.html, mo_phong_thuc_te.py}` (chưa commit). Dừng phiên 00:00 theo yêu cầu.
- **Thesis:** chương Chính sách: mục ngưỡng (hình ba frontier, bảng SLO mục tiêu → ngưỡng); mục proactive: kết luận âm và điều kiện có lợi.

## 2026-11-14 – Hướng 3 xong (độ mạnh chu kỳ, cận oracle); chuẩn bị đo TPOT trên 5060 Ti cho hướng 1

- **Task:** chung · **Environment:** sim (máy thuê 4 × 5060 Ti chưa vào được)
- **Done:** `do_chu_ky.py` đo độ mạnh mùa vụ của BurstGPT (60 ngày, theo giờ). `du_bao_quy_mo.py` so A2+G / hybrid Holt-Winters / hybrid oracle (biết trước λ trung bình 10 phút tới) ở 4 GPU và 16 GPU (tải ×4), cold 110 / 15 s, 2 ngày test × 2 seed. Sửa `mo_phong_thuc_te.simulate` nhận `_N` theo job (Python 3.14 dùng forkserver nên worker không kế thừa biến module đã đổi). Viết `do_tpot.py` (closed-loop, n ∈ {1…96}, đo TTFT/TPOT/throughput, fit a + b·n, suy sức chứa). Cập nhật `cac-huong-nang-cap.html` bản 6.
- **Decision:** Kết luận hướng 3 chốt bằng cận trên oracle thay vì chỉ một bộ dự báo: kết luận âm không phụ thuộc chất lượng Holt-Winters.
- **Results:** (mô phỏng) F_s chu kỳ 24 h = 0,05, tuần = 0,15; ACF 1 h = 0,70, 24 h = 0,07; hình dạng trung bình 07:00 thấp hơn 14:00 ~13 lần nhưng CV theo giờ 1,4–5. Oracle: 4 GPU cold 110 s 92,4 → 95,2 % SLO, 42,7 → 41,4 % GPU; 16 GPU 92,9 → 94,0 %, 35,2 → 33,7 %. Holt-Winters: 4 GPU không đổi; 16 GPU +0,2 SLO nhưng +4,2 điểm GPU. Cold 110 → 15 s lợi hơn oracle 2–3 lần.
- **Incidents:** SSH tới máy thuê timeout (cả trong và ngoài sandbox, Internet của máy nhà vẫn bình thường); chưa đo được TPOT trên 5060 Ti.
- **Links:** `docs/bao-cao/de-xuat-v3/{do_chu_ky.py, du_bao_quy_mo.py, do_tpot.py, ket-qua-chu-ky.json, ket-qua-du-bao-quy-mo.json}` (chưa commit).
- **Thesis:** chương Chính sách, mục proactive: bảng oracle; chương Mô hình: TPOT(n) trên hai loại GPU (khi đo xong).

## 2026-11-15 – Commit phần V3, tách 3 PR xếp chồng, sửa CI link

- **Task:** chung · **Environment:** none
- **Done:** Commit phần việc 13–14/11 thành 5 commit nhỏ. Tách nhánh `refactor/split-home-cloud` (gộp 3 việc, 147 file) thành 3 PR xếp chồng: #34 refactor → `main`, #35 báo cáo kỹ thuật → #34, #36 V3 → #35. `make lint` đạt (yamllint chạy qua `uvx`).
- **Incidents:** Job `docs` (lychee) của cả 3 PR lỗi. (1) `03-kien-truc-autoscaling.md` link tới ADR-006 §3.1, nhưng 5 commit thêm §3.1 nằm trên `docs/sync-after-v1` được push **sau khi** PR #33 đã merge nên chưa vào `main` → merge nhánh đó vào #34 (không conflict), truyền lên #35, #36 bằng merge; conflict ở `tuan-06.md` và `viec-sap-lam.md` (cả hai bên cùng thêm mục cuối file) → giữ cả hai, mục 12/11 đứng trước 13/11. (2) README ở #34 link tới `docs/bao-cao/`, thư mục chỉ có ở #35 → chuyển link sang #35. Sau khi sửa, CI của cả 3 PR đều đạt.
- **Decision:** Dùng merge thay cho rebase để không phải force-push nhánh đã có PR. Khi merge, giữ merge commit (không squash) và merge theo thứ tự #34 → #35 → #36.
- **Links:** PR #34, #35, #36.
