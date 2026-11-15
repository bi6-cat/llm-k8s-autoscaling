# Nhật ký làm việc – Trình – Tuần 06 (09–15/11/2026)

## 2026-11-09 – TR2: truy vấn A1 đã sửa (Quang làm thay)

> Mục này do **Quang** ghi vào thư mục của Trình để Trình biết việc đã xong và không làm lại. Trình không tham gia lần sửa này; **Trình cần review**, vì đây là phần TR2 của Trình.

- **Task:** TR2 (Quang làm thay) · **Environment:** none (chưa chạy trên cluster)
- **Done:** đổi query trong `autoscaling/eval/A1.yaml` thành `(sum(avg_over_time(nvidia_smi_utilization_gpu_ratio[15s])) * 100) or vector(0)`; sửa Thông số §8.1, Kiến trúc §13; thêm test.
- **Decision:** handoff ghi "chỉ tính GPU của pod Ready", nhưng exporter không có label pod nên không lọc được. Chọn trung bình 15 s trên từng GPU; chưa chuyển sang dcgm-exporter vì chưa kiểm được trên máy thuê trước V2. Việc này đổi tín hiệu của A1 so với thiết kế, nên cần Trình xem lại.
- **Results:** xem nhật ký Quang tuần 06.
- **Links:** nhánh `fix/a1-transient-gpu-sample`; nhật ký Quang [tuần 06](../quang/tuan-06.md).

## 2026-11-09 – TR5: merge PR #25 (ghi bù ngày 15/11)

- **Task:** TR5 · **Environment:** none (GitHub)
- **Done:** merge PR #25 (`PodWatcher`, dòng thời gian pod, log pod bị scale-down) vào `main` lúc 00:02 ngày 09/11 (giờ Việt Nam), merge commit `4148f0e`.
- **Results:** CI 6/6 check xanh (run 42502810813) trước khi merge.
- **Links:** PR #25; mục 2026-11-08 ở [tuần 05](tuan-05.md).

## 2026-11-12 – chung: đồng ý ADR-006 C7 và §3.1 (ghi bù ngày 15/11)

- **Task:** chung (TR2, TR4) · **Environment:** none
- **Decision:** Trình đồng ý qua tin nhắn với Quang:
  1. C7: A1 dùng `sum(avg_over_time(nvidia_smi_utilization_gpu_ratio[15s])) * 100`, do Quang làm thay phần TR2 (PR #29).
  2. ADR-006 §3.1: lược Sealed Secrets, NetworkPolicy thường trực, rate limit. Alertmanager → Telegram (TR4) và Argo CD app `autoscaling`/`observability` (TR1) làm trước V2.
- **Links:** [ADR-006 §3.1](../../../adr/006-chot-may-model-va-kich-ban-truoc-v2.md#31-quyết-định-ngày-12112026).

## 2026-11-15 – TR4: Alertmanager → Telegram (việc 6a)

- **Task:** TR4 · **Environment:** sim (kind `llm-sim`, kube-prometheus-stack 92.1.1, Alertmanager v0.34.1)
- **Done:**
  1. Đối chiếu mã nguồn upstream ở phiên bản ghim: Alertmanager v0.34.1 có `bot_token_file`, `chat_id_file` và chỉ đọc hai file này lúc gửi tin; Prometheus Operator v0.94.1 nhận `chat_id_file` khi Alertmanager ≥ 0.31.
  2. `common/platform/alertmanager-values.yaml`: định tuyến page/ticket/null, template `telegram.llm.message`, mount Secret `alertmanager-telegram` với `optional: true`.
  3. `common/platform/alertmanager-secret.sh` cùng `make alertmanager-secret`: tạo Secret từ `.env` qua stdin.
  4. `make sim-up`, `vast.sh platform` và `install-platform.sh`: thêm values Alertmanager và áp `common/observability/`. Trước đó phần này chưa được áp ở môi trường nào.
  5. Nhãn `externalLabels: {env: sim|cloud}`, tạo file mới `envs/cloud/platform/kube-prometheus-stack-values.yaml`.
  6. `make alertmanager-check` (amtool 0.34.1) thêm vào job CI `alerts`.
  7. Sửa Vận hành §3.4, Thông số §9.4, `phien-ban.md`.
- **Decision:** D48–D52.
  - Định tuyến đặt ở file values riêng, để PR không làm Argo CD đổi cluster nhà; nhà bật ở việc 6b.
  - Token và chat id đọc từ file trong Secret mount `optional`. Không chọn `alertmanagerSpec.secrets` (thiếu Secret thì pod kẹt), AlertmanagerConfig CRD hay `chat_id` trong Git.
  - Gốc route là `null`. Chỉ page, ticket và critical của chart tới Telegram.
  - Script Secret dùng chung cho 3 môi trường.
  - amtool chạy trong CI.
- **Results:**
  - `helm template` chart 92.1.1 với values của nhóm: 134 cảnh báo của chart (32 critical, 93 warning, 7 info, 2 none). Secret cấu hình có đủ route và receiver; object Alertmanager có volume `optional`.
  - kind, chưa có Secret: pod Alertmanager 2/2 Running, `Reconciled=True`, cấu hình đã nạp có `chat_id_file`, log không có lỗi.
  - Script Secret: không đối số → exit 2; `.env` thiếu biến → exit 0, có cảnh báo; token hoặc chat id sai dạng → exit 1; đúng → Secret được tạo, file có trong pod sau 30 s mà không khởi động lại pod.
  - Telegram API giả (`tg-mock` ở scratchpad, `api_url` chỉ đặt trong values thử), cảnh báo bắn bằng `amtool alert add`:
    - `page` gồm 2 pod → 1 tin;
    - `ticket` → 1 tin;
    - `critical` → receiver ticket;
    - `warning` → không gửi;
    - `chat_id` đọc đúng từ file, `parse_mode=HTML`;
    - cho cảnh báo hết: page gửi "✅ … đã hết" sau khoảng 5 phút (`group_interval`); ticket không gửi.
  - `make alertmanager-check`: đạt. Bắt được 3 lỗi cố ý: bỏ `| html`, nhánh "đã hết" có `<`, bỏ giới hạn 8 dòng.
  - `make alerts-test dashboards-check`, `yamllint -s .`, `actionlint`, `shellcheck`, `lychee` (như CI): đạt.
  - **Chưa thử với Telegram thật:** máy này chưa có `.env` và bot Alertmanager.
- **Incidents:**
  - amtool.exe trên Windows không nhận glob `/tmp/…/*.tmpl` → chạy amtool trong thư mục tạm với đường dẫn tương đối.
  - Fixture ban đầu thử escape bằng `<b>…</b>`, mà đây là thẻ hợp lệ, nên phép thử ngược vẫn đạt → đổi sang `< 75 & > 2,5 s`.
  - make.exe bản ezwinports đổi mã chữ có dấu trong recipe, nên `grep '^• …'` không khớp → dùng mẫu grep chỉ có ASCII.
  - `AlertmanagerClusterCrashlooping` (critical) kêu trên kind: container restarts=0, nhưng `process_start_time_seconds` có 16 giá trị trong 15 phút, lệch tới 75 s (nghi do đồng hồ WSL) → tắt riêng rule này trên sim.
  - `/code-review high`: 10 điểm, sửa cả 10 (nhãn env, giới hạn độ dài tin, nhà chờ 6b, biến môi trường ưu tiên hơn `.env`, render cả nhánh resolved, subshell `cd`, nhật ký, Thông số §9.4, comment CI, comment về cách Helm gộp values).
  - PR vượt 400 dòng → tách phần metric KEDA sang PR sau.
- **Deviations:**
  - Vận hành §3.4 cũ đặt gốc route là `ticket` và có inhibit `LLMSLOBurnFast` → `LLMSLOBurnSlow`. Giờ gốc là `null` (tránh spam). Bỏ inhibit vì `LLMSLOBurnSlow` chưa có, nên giữ inhibit mặc định của chart. Đã sửa §3.4 theo cấu hình thật.
  - Ở nhà chưa bật.
- **Links:** nhánh `feat/tr4-alertmanager-telegram`; `common/platform/alertmanager-values.yaml`, `common/platform/alertmanager-secret.sh`, `Makefile` (`alertmanager-check`, `sim-up`), `envs/cloud/provision/`.
- **Thesis:** §4 (vận hành: đường cảnh báo Prometheus → Alertmanager → Telegram, lý do chỉ đẩy page/ticket); hình: ảnh chụp tin Telegram thật (`[cloud] 🔥 …`, rồi `✅ … đã hết`), chụp khi có bot.
