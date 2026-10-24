# Nhật ký làm việc – Trình – Tuần 03 (19–25/10/2026)

## 2026-10-25 – Recording rule, 7 quy tắc cảnh báo, unit test promtool, 7 runbook (TR4)

- **Mã việc:** TR4 · **Môi trường:** không (chỉ trên máy cá nhân, chưa áp lên cluster)
- **Đã làm:**
  1. Tạo nhánh `feat/tr4-alerts` từ `origin/main`. Việc này độc lập với `temp/w2-scaffold`: `observability/` và `docs/runbooks/` là thư mục mới, và values của kube-prometheus-stack trong scaffold đặt `ruleSelectorNilUsesHelmValues: false` nên PrometheusRule ở đâu cũng được nạp.
  2. Viết recording rule: `observability/rules/slo.yaml` (`llm:ttft_bad_ratio:rate1m|5m|30m`, `llm:error_ratio:rate5m`) và `observability/rules/vllm.yaml` (4 rule cho dashboard, interval 5 s, theo Kiến trúc §17.2).
  3. Viết `observability/alerts/llm.yaml` gồm 7 quy tắc cho 6 cảnh báo của F6: `LLMSLOBurnFast`, `LLMErrorRateHigh` (page); `LLMAtMaxReplicas`, `LLMPodPending` (ticket); `LLMPodNotReady`, `LLMPodCrashLooping`, `KedaScalerErrors` (page).
  4. Viết unit test `observability/alerts/tests/llm-test.yaml`: 8 test, mỗi cảnh báo có ca phải kêu và ca không được kêu.
  5. Thêm `make alerts-test`: tách `spec:` của PrometheusRule thành file rule thuần cho promtool, để repo chỉ giữ một bản rule. Thêm `observability` vào vòng `kubectl kustomize` của `make lint`.
  6. Viết 7 runbook trong `docs/runbooks/` theo mẫu Vận hành §4.1.
- **Quyết định và lý do:**
  - Rule viết dạng CRD `PrometheusRule` (cluster dùng trực tiếp), còn promtool đọc bản tách bằng `sed`, thay vì giữ hai bản song song dễ lệch nhau. Không dùng `yq` để không thêm công cụ phải cài. Đổi lại, `spec:` phải là key cuối file (đã ghi trong header).
  - Đối chiếu tên metric với mã nguồn phiên bản đã ghim, không dựa vào trí nhớ:
    - vLLM v0.31.0 (`vllm/v1/metrics/buckets.py`): TTFT có bucket `2.5`, nên ngưỡng SLO 2,5 s dùng được.
    - KEDA v2.21.0 (`pkg/metricscollector/prommetrics.go`): bộ đếm lỗi là `keda_scaler_detail_errors_total`, nhãn `namespace, metric, scaledObject, scaler, triggerIndex, type`.
  - `LLMPodNotReady` chỉ xét pod phase Running, để pod Pending (cũng là không Ready) không page trùng với `LLMPodPending`.
  - `LLMPodCrashLooping` dùng `max_over_time(...[5m])`, vì trong CrashLoopBackOff chuỗi `waiting_reason` mất đi mỗi lần container chạy lại, làm `for:` đặt lại và cảnh báo không bao giờ kêu.
  - `KedaScalerErrors`: `increase(...[2m]) >= 3` + `for: 1m` (≈ số lỗi để KEDA vào fallback), để lỗi mạng lẻ không page. Chỉ lọc theo `scaledObject`, không lọc theo `namespace`: nhãn `namespace` của KEDA trùng nhãn target nên bị đổi thành `exported_namespace` khi scrape.
  - Test dùng mutation để kiểm chính test: cố ý làm hỏng rule 11 cách (bucket sai, bỏ cửa sổ 1m, bỏ lọc service/namespace/phase, bỏ `max_over_time`, đổi ngưỡng, tên metric cũ của KEDA). Lần đầu có 4 mutation lọt; sửa test (thêm ca hồi phục cho BurnFast, dùng `stale` thay `_` cho CrashLooping, dời điểm kiểm KEDA về 6m45s) thì cả 11 đều bị bắt.
- **Kết quả và số đo:**
  - `promtool check rules` (promtool 3.13.4, bản Windows tải từ GitHub, đã kiểm sha256): `slo.yaml` 4 rule, `vllm.yaml` 4 rule, `llm.yaml` 7 rule, đều SUCCESS.
  - `promtool test rules observability/alerts/tests/llm-test.yaml`: SUCCESS (8 test). Mutation: 11/11 bị bắt.
  - `yamllint -s observability` đạt; `kubectl kustomize observability` ra 3 PrometheusRule.
  - **Chưa chạy `make alerts-test` bằng make thật** (Windows không có make, không có WSL). Đã chạy tay các lệnh tương đương của recipe.
  - **Chưa áp lên cluster**, chưa thấy cảnh báo kêu thật. Máy của Trình chưa có kubeconfig vào cluster nhà.
- **Sự cố:**
  - Docker Desktop tắt nên không chạy promtool bằng image `prom/prometheus`: tải bản zip Windows vào thư mục tạm.
  - `yamllint -s .` toàn repo báo `.yamllint.yaml` sai ký tự xuống dòng: do `core.autocrlf=true` trên Windows đổi LF → CRLF ở working copy; trong Git vẫn là LF. Không liên quan thay đổi này.
- **Khác thiết kế:**
  - Vận hành §3.2 ghi `keda_scaler_errors_total` (tên cũ). Dùng `keda_scaler_detail_errors_total` theo KEDA 2.21. Cần sửa thiết kế.
  - `LLMErrorRateHigh` thêm `for: 1m` (thiết kế không ghi `for`). Lý do: vài 503 lẻ khi chuyển pod không nên page. Cần Quang đồng ý.
  - Ví dụ tên service Traefik đổi từ dạng `...-8000` sang `llm-serving-vllm-http@kubernetes`, vì Ingress trên `feat/serving` trỏ cổng theo tên `http`. Regex `llm-serving-.*` không đổi.
- **Còn phải làm để cảnh báo chạy thật:**
  - Bật metric của KEDA operator (`prometheus.operator.enabled`, `podMonitor.enabled` trong `platform/keda/values.yaml`; chart mặc định tắt). Thuộc `feat/keda`.
  - Thêm Application Argo CD trỏ `observability/` (Kiến trúc §18.1); thêm job `alerts` vào CI (Kế hoạch, bảng CI).
  - Kiểm chứng trên cluster nhà: bucket `le="2.5"` trên `/metrics`, tên service Traefik, nhãn của kube-state-metrics.
  - Alertmanager → Telegram (TR4 phần sau), có tính tới việc kube-prometheus-stack đã có sẵn các cảnh báo mặc định (`KubePodCrashLooping`, `KubeHpaMaxedOut`…) trùng ý với một số cảnh báo ở đây.
- **Liên kết:** nhánh `feat/tr4-alerts`; `observability/`, `docs/runbooks/`, `Makefile`.
- **Dùng cho luận văn:** §4.6–4.8 (SLI/SLO, cảnh báo burn rate, runbook); phần kiểm thử cảnh báo bằng `promtool test rules` + mutation test (bảng 11 mutation). Hình 7 (SLO → cảnh báo → runbook) đã có.
