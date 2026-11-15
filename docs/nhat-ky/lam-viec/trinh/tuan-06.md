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

## 2026-11-15 – TR4: `KedaScalerErrors` không thể kêu (đang sửa, chưa mở PR)

- **Task:** TR4 · **Environment:** sim (kind `llm-sim`, KEDA 2.21.0)
- **Done:**
  1. Thử chuỗi thật (NetworkPolicy T4 → KEDA lỗi → `KedaScalerErrors` → Alertmanager → Telegram giả) và phát hiện Prometheus không có metric `keda_*` nào: `common/platform/keda-values.yaml` chưa bật `prometheus.operator.enabled` và `podMonitor.enabled` (chart mặc định tắt), dù comment trong `alerts/llm.yaml` ghi là cần.
  2. Thêm `common/platform/keda-metrics-values.yaml` (lớp values thứ hai) cho `sim-up` và `install-platform.sh` (D53).
- **Results:**
  - Sau khi thêm: PodMonitor `keda/keda-operator` được tạo, target `up=1`.
  - Áp NetworkPolicy T4 (ScaledObject đã bỏ pause): fallback 1 → 3 replica sau khoảng 28 s. Sau khoảng 4 phút, `numberOfFailures` lên 56–67, nhưng `keda_scaler_detail_errors_total` = 1 và `keda_scaled_object_errors_total` = 5, nên `increase(...[2m]) >= 3` không bao giờ đúng. **Rule sai cả về tín hiệu, không chỉ thiếu metric.**
  - Mã nguồn KEDA v2.21.0 (`pkg/scaling/scale_handler.go`): bộ đếm ghi theo `result.record.ScalerError`, mà khi fallback đang bật thì `processMetricsWithFallback` trả giá trị fallback. Giả thuyết: lúc đó lỗi không còn được đếm. Chưa đọc `pkg/fallback/fallback.go` để xác nhận.
  - Metric `keda_*` có trên kind: `keda_scaled_object_errors_total`, `keda_scaler_detail_errors_total`, `keda_scaler_active`, `keda_scaler_metrics_value`, `keda_scaler_metrics_latency_seconds`, `keda_scaler_http_requests_total`, `keda_scaler_http_request_duration_seconds_*`, `keda_scaled_object_paused`, `keda_internal_*`, `keda_build_info`.
- **Incidents:**
  - 2 lần đầu T4 không gây lỗi KEDA nào: ScaledObject `vllm-a2` đang `Paused=True` (annotation `paused-replicas: 1` do runner đặt sau lượt cuối, `session.py:236`), nên không có HPA và KEDA không hỏi Prometheus. Gỡ annotation thì HPA có lại và T4 chạy đúng.
  - Image Prometheus không có `wget` → dùng `promtool query instant` trong pod. NetworkPolicy T4 chặn cả proxy của API server tới Prometheus.
  - `kubectl debug` vào pod keda-operator không chạy được vì `runAsNonRoot`.
  - `pkill -f chain-test.sh` tự giết chính lệnh đang chạy.
  - `/code-review high` trên diff: 7 điểm, chưa sửa. Sẽ sửa cùng rule mới: comment trong `llm.yaml` ghi rõ môi trường; header `install-platform.sh`; `phien-ban.md` thêm `install-platform.sh` ở dòng kps và KEDA; điều kiện tiên quyết cho T4 là phải có PodMonitor `keda-operator`. Ở nhà và gộp 2 file values KEDA: làm ở 6b.
- **Links:** nhánh `fix/tr4-keda-metrics` (chỉ commit ở máy, chưa push), xếp chồng trên PR #37; script thử ở `.work/tools/alertmanager-test/`.
- **Thesis:** §4 hoặc §5, bài học "unit test đạt mà cảnh báo vẫn chết": unit test chỉ kiểm biểu thức với dữ liệu tự bơm, không kiểm metric có thật và hành vi của exporter.

## 2026-11-15 – TR4: merge PR #37 (Alertmanager → Telegram)

- **Task:** TR4 · **Environment:** none (GitHub)
- **Done:** merge PR #37 vào `main` lúc 17:29 (giờ Việt Nam), merge commit `839c5e5`; xoá nhánh `feat/tr4-alertmanager-telegram` trên remote.
- **Results:** đủ 5 điều kiện merge (D35): CI 6/6 xanh (run 43703913364, job `alerts` chạy `make alertmanager-check` trên Linux và in đủ 3 tin mẫu); `/code-review high` đã sửa 10/10; `MERGEABLE`/`CLEAN`, không có review hay bình luận; không file nào mà Application ở nhà đọc bị đổi; base là `main`.
- **Links:** PR #37.

## 2026-11-15 – TR4: `KedaScalerErrors` đọc condition `Fallback` của ScaledObject

- **Task:** TR4 · **Environment:** sim (kind `llm-sim`, KEDA 2.21.0, kube-prometheus-stack 92.1.1)
- **Done:**
  1. Đọc mã nguồn KEDA v2.21.0 để xác nhận giả thuyết ở mục trước: `pkg/fallback/fallback.go` `GetMetricsWithFallback` trả giá trị fallback với `err = nil` khi `numberOfFailures > failureThreshold`; `pkg/scaling/scale_handler.go` gọi `RecordScalerError(..., err)` bằng lỗi **sau** khi xử lý fallback; `pkg/metricscollector/prommetrics.go` chỉ tăng bộ đếm khi `err != nil`. Kết luận: `keda_scaler_detail_errors_total` và `keda_scaled_object_errors_total` chỉ tăng ở vài lần lỗi đầu rồi đứng yên suốt thời gian fallback. Rule đếm lỗi kiểu nào cũng sai: `increase(...) >= 1` cũng tự hết sau 2 phút trong khi vẫn fallback.
  2. Đọc thêm `pkg/scaling/executor/scale_scaledobjects.go`: khi có `fallback`, lỗi dưới ngưỡng lúc không active **không** làm `Ready=False`; `Ready=Unknown` khi trigger lỗi lúc active; `Ready=False` khi không đọc hoặc không scale được Deployment đích.
  3. Thêm `common/platform/kube-state-metrics-values.yaml` (lớp values kps): kube-state-metrics custom resource state đọc `status.conditions` của ScaledObject thành `kube_scaledobject_status_condition{namespace, scaledobject, condition}`, kèm quyền `list/watch` `scaledobjects.keda.sh`. Nạp ở `sim-up` bước 4, `install-platform.sh`, `vast.sh platform`.
  4. Viết lại rule: `(Fallback == 1 or Ready == 0) unless Paused == 1`, `for: 1m`. Unit test 4 ScaledObject: chuyển `Ready=Unknown` → `Fallback=True` (kiểm cảnh báo liền mạch, không đặt lại `for:`), `Ready=False`, đang pause với Fallback cũ, mới tạo.
  5. Panel "Lỗi scaler trong 2 phút" (dashboard autoscaling) mắc cùng lỗi → đổi thành "KEDA: request lỗi và fallback": `keda_scaler_http_requests_total{status_code!~"2.."}` theo mã (trục trái) và condition Fallback (trục phải).
  6. `/code-review high` trên phần chưa commit: 7 điểm, đều đã xử lý. Điểm "thiếu metric thì rule im lặng" chỉ ghi thành giới hạn (comment rule, runbook mục "Giới hạn", lệnh kiểm metric có mặt), chưa thêm cảnh báo `absent()`; Prometheus hoặc keda-operator sập cũng ghi vào giới hạn; summary bao cả ca `Ready=False`; runbook sửa thời gian hết cảnh báo theo số đo.
  7. Sửa runbook, Vận hành §3.2 và §4.3, w2.md (điều kiện để T4 kích cảnh báo), comment của `keda-metrics-values.yaml`, Makefile, `install-platform.sh` (header), `phien-ban.md` (thêm `install-platform.sh`, KSM v2.20.0). Gồm 4 điểm review còn lại của mục trước.
- **Decision:** Trình chọn tín hiệu condition qua kube-state-metrics (D54). Bỏ `keda_scaler_http_requests_total` làm tín hiệu cảnh báo: metric này vẫn đếm khi fallback, nhưng bỏ sót ca PromQL trả nhiều chuỗi (HTTP 200) và ca scaler không dựng được; giữ nó cho chẩn đoán. Không sửa `kube-prometheus-stack-values.yaml` vì Argo CD ở nhà đọc file đó (điều kiện merge 4).
- **Results:**
  - KSM v2.20.0 với `--resources=<danh sách có sẵn>` vẫn thu custom resource (log: `Active resources … keda.sh/v1alpha1, Resource=scaledobjects`); collector có sẵn vẫn chạy (`kube_pod_info` 26 chuỗi). Nhãn `namespace` giữ nguyên trong Prometheus (`namespace="llm-serving"`).
  - Kiểm đột biến unit test: bỏ pha `Ready=Unknown` hoặc bỏ vế `unless Paused` thì test đỏ.
  - Chuỗi thật trên kind. Cách làm: kps nâng cấp thêm một lớp values thử (chỉ ở máy Trình) trỏ `api_url` của hai receiver Telegram sang `tg-mock`, một HTTP server trong namespace `monitoring` ghi log mọi request; ScaledObject `vllm-a2` không pause; áp `common/autoscaling/tests/block-keda-to-prometheus.yaml`; cứ 10–15 s đọc condition (`kubectl get scaledobject -o jsonpath`), số cảnh báo trong Alertmanager (`amtool alert query`) và log `tg-mock`; gỡ policy khi có tin "đang kêu". Kết quả: áp policy 10:52:22 UTC → `Fallback=True`, replica 1 → 3 lúc +18 s → cảnh báo vào Alertmanager lúc +97 s → tin "đang kêu" tới `tg-mock` lúc +130 s (thêm `group_wait` 30 s). Trong 2 phút chặn: `keda_scaler_http_requests_total{status_code="error"}` 140 → 190, `keda_scaler_detail_errors_total` 1 → 2. Gỡ policy → `Fallback=False` sau ≤ 12 s, Alertmanager hết cảnh báo sau ≤ 28 s, tin "đã hết" tới `tg-mock` sau 273 s (chờ `group_interval` 5 phút). Hai tin có đủ nhãn `[sim]`, summary, description và link runbook.
  - `make alerts-test`, `make dashboards-check`, `yamllint -s .`, `shellcheck` (2 script cloud), lychee (0 lỗi), kubeconform `common/observability` (6/6) đều đạt.
- **Deviations:** Vận hành §3.2 đổi điều kiện của `KedaScalerErrors` từ "≥ 3 lỗi trong 2 phút" sang condition `Fallback`/`Ready`.
- **Links:** nhánh `fix/tr4-keda-metrics`; `common/platform/kube-state-metrics-values.yaml`, `common/observability/alerts/llm.yaml`, `docs/runbooks/KedaScalerErrors.md`.
- **Thesis:** §4 (giám sát autoscaling), bài học "unit test đạt mà cảnh báo vẫn chết" kèm dòng thời gian T4 ở trên; nên chụp panel "KEDA: request lỗi và fallback" trong một lượt T4.

## 2026-11-15 – TR4: merge PR #38 (`KedaScalerErrors` đọc condition Fallback)

- **Task:** TR4 · **Environment:** none (GitHub)
- **Done:** merge PR #38 vào `main` lúc 18:04 (giờ Việt Nam), merge commit `02fdd42`; xoá nhánh `fix/tr4-keda-metrics`. Trước khi mở PR, Trình gộp commit WIP (chưa push) với phần sửa thành một commit `15df7bc`.
- **Results:** đủ 5 điều kiện merge (D35): CI 6/6 xanh (run 43707072307); kiểm cục bộ và `/code-review high` (7/7 đã xử lý); `MERGEABLE`/`CLEAN`, không có review hay bình luận; Application ở nhà không đọc file nào bị đổi (`kube-prometheus-stack-values.yaml`, `keda-values.yaml` giữ nguyên); base là `main`.
- **Links:** PR #38.

## 2026-11-15 – TR1: Argo CD app `autoscaling` và `observability` ở nhà (việc 6b, PR chờ kiểm ở nhà)

- **Task:** TR1 (kèm TR4) · **Environment:** sim (kind `llm-sim`, Argo CD core v3.5.4 cài tạm), none (GitHub)
- **Done:**
  1. Thêm overlay `envs/home/autoscaling/` (A2: max 2, fallback 2, threshold 23), Application `autoscaling` (trỏ overlay) và `observability` (trỏ `common/observability`).
  2. App `monitoring` nạp thêm `alertmanager-values.yaml` và `kube-state-metrics-values.yaml`; app `keda` nạp thêm `keda-metrics-values.yaml`, cùng thứ tự với `make sim-up` và `install-platform.sh`. Prometheus ở nhà thêm `externalLabels: {env: home}`.
  3. Root-app: `ignoreDifferences` cho `/spec/syncPolicy/automated` của app `autoscaling` cùng `RespectIgnoreDifferences=true`; cộng 2 trường Argo CD tự ghi (`refresh`, `/operation`) theo mẫu upstream `cluster-bootstrapping.md` v3.5.4.
  4. Thêm `make home-eval-begin` (tắt auto-sync của A2) và `make home-eval-end` (xoá ScaledObject khác A2, chép khối `automated` từ Git bằng yq). `guard_argocd` của runner đổi sang `autosync_enabled()`, theo đúng `SyncPolicy.IsAutomatedSyncEnabled` của v3.5.4; thêm 6 ca unit test.
  5. Sửa README nhà (phiên đánh giá, các bước làm một lần), Kiến trúc §18.1–§18.2, Môi trường §14.1, Vận hành §3.4, Thông số §8.1 và §9.3, cùng các comment còn ghi "việc 6b".
  6. Thử trên kind: cài Argo CD core v3.5.4 giống role `argocd-bootstrap`. Đẩy một nhánh tạm `test/tr1-argocd-kind`, chỉ khác ở chỗ 2 app mới trỏ vào chính nhánh đó; root thử là root thật, cộng `directory.include` để chỉ lấy 2 app này. Thử xong thì xoá nhánh tạm, gỡ Argo CD, chạy `make sim-up` (không có values thử).
  7. `/code-review high`: 9 điểm. Sửa 7, ghi nhật ký này là điểm thứ 8. Giữ nguyên điểm còn lại (mục `/operation` áp cho mọi app con): đó là mẫu của upstream, và ca xấu nhất chỉ là một lần sync lặp lại.
- **Decision:** Trình chọn mẫu `ignoreDifferences` của upstream, chỉ mở cho app `autoscaling` (D55). Các phương án bỏ: bỏ qua `automated` của mọi app con (Git không còn ép được các app khác); tắt auto-sync của root mỗi lần đánh giá (2 bước, dễ quên bật lại); annotation `skip-reconcile` (`guard_argocd` không hiểu). Thông số A2 ở nhà lấy từ `capacity.json`, 0,8 × 28,4 ≈ 23; `home-eval-end` đọc giá trị từ Git thay vì viết tay (D56).
- **Results:**
  - Pha 1: áp root thử lúc 11:25:35 UTC. Sau ≤ 7 s, cả 3 app `Synced`/`Healthy`; ScaledObject đổi từ max 3, threshold 10 (sim) sang max 2, fallback 2, threshold 23.
  - Tắt auto-sync lúc 11:26:17: suốt 2 phút sau, root vẫn không bật lại.
  - Root tự auto-sync commit mới `424a0b2` lúc 11:31:34, sau khi tắt lúc 11:31:32 (history id 2, `initiatedBy.automated`): auto-sync vẫn tắt. Sync tay có `syncOptions` cũng không bật lại.
  - Runner áp A2 với threshold 10 và pause: giữ nguyên suốt 85 s; app hiện `OutOfSync`/`Suspended`. Bật lại auto-sync thì sau ≤ 5 s A2 về đúng Git (threshold 23, hết pause).
  - Đối chứng âm, bỏ `ignoreDifferences`: root bật lại auto-sync sau ≤ 5 s (lần đọc đầu tiên).
  - Make target: `home-eval-begin` chạy 2 lần đều rc 0; `home-eval-end` xoá `vllm-a1` (trỏ Deployment khác), giữ `vllm-a2`, khôi phục `{"prune":true,"selfHeal":true}`.
  - Render `helm template` kps 92.1.1 với 4 lớp values của nhà: `externalLabels.env = home`, volume Secret `optional: true`, Alertmanager giữ RAM và nodeSelector của nhà, KSM có `--custom-resource-state-config-file` và quyền `keda.sh/scaledobjects`; KEDA có PodMonitor `keda-operator`.
  - Kiểm cục bộ: kubeconform 11 thư mục kustomize và 9 Application đạt; `yamllint -s .`, `make alerts-test`, shellcheck, lychee (0 lỗi), ruff đạt; pytest `experiments` 147 đạt, 4 lỗi ở `test_backup_notify` (gọi script bash, lỗi y hệt trên bản chưa sửa, chỉ trên Windows).
- **Incidents:** Lần đầu ép root sync bằng cách patch `operation` không có `syncOptions` thì auto-sync bị bật lại. Nguyên nhân: `RespectIgnoreDifferences` được đọc từ `syncOp.SyncOptions` (`controller/sync.go:239`), không phải từ spec của app. Auto-sync thật chép `spec.syncPolicy.syncOptions` vào operation (`appcontroller.go:2470`); sync tay qua server cũng chép, trừ khi truyền `--sync-option`, vì danh sách đó thay hẳn danh sách của app (`server/application/application.go:2122-2131`). Ghi cạm bẫy này vào comment của root-app và vào README.
- **Deviations:** Kiến trúc §18.2 và Môi trường §14.1 từng ghi "runner tắt auto-sync"; thực tế runner chỉ kiểm, việc tắt và bật làm bằng make target. Root-app có `ignoreDifferences` (thiết kế cũ không có).
- **Links:** nhánh `feat/tr1-argocd-autoscaling-observability`; `envs/home/argocd/root-app.yaml`, `envs/home/argocd/apps/{autoscaling,observability,monitoring,keda}.yaml`, `envs/home/autoscaling/kustomization.yaml`, `experiments/runner/configs.py`, `Makefile`.
- **Thesis:** §4 (GitOps), cạm bẫy "App-of-Apps với selfHeal bật lại auto-sync của app con", kèm dòng thời gian của đối chứng âm và đối chứng dương ở trên; bảng app Argo CD ở nhà.
