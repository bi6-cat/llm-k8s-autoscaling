<!-- Mục đích: Phụ lục B, quy tắc ghi và quy tắc cảnh báo của đồ án, kèm một unit test mẫu, mà mục 3.5 và 4.6 dẫn tới. Người viết: Trình. -->
<!-- Trích từ main ngày 27/11/2026: common/observability/rules/slo.yaml, common/observability/alerts/llm.yaml, common/observability/alerts/tests/llm-test.yaml (cả ba commit ed381ba). Số test case và kết quả `make alerts-test` chạy lại 27/11/2026 trên máy Trình (promtool 3.15.0). -->

# Phụ lục B. Quy tắc cảnh báo và unit test {.unnumbered}

Quy tắc của Prometheus nằm trong `common/observability/`, khai báo bằng resource `PrometheusRule` để Prometheus Operator tự nạp. Thư mục `rules/` chứa quy tắc ghi (recording rule), tức các biểu thức được tính trước và lưu thành chuỗi mới. Thư mục `alerts/` chứa bảy quy tắc cảnh báo cùng unit test của chúng.
<!-- nguồn: common/observability/ (rules/, alerts/, alerts/tests/) -->

## B.1. Quy tắc ghi tỷ lệ request chậm

Cảnh báo SLO không tính trực tiếp trên histogram của vLLM mà đọc tỷ lệ request có TTFT trên 2,5 s, do quy tắc ghi tính sẵn cho ba cửa sổ 1 phút, 5 phút và 30 phút. Đoạn mã B.1 là bản cửa sổ 5 phút. Hai bản còn lại chỉ khác độ dài cửa sổ.
<!-- nguồn: common/observability/rules/slo.yaml (llm:ttft_bad_ratio:rate1m, rate5m, rate30m), commit ed381ba -->

**Đoạn mã B.1.** Quy tắc ghi tỷ lệ request có TTFT trên 2,5 s trong 5 phút (`rules/slo.yaml`, trích)
<!-- nguồn: common/observability/rules/slo.yaml, commit ed381ba -->

```yaml
- record: llm:ttft_bad_ratio:rate5m
  expr: |
    (
      sum(rate(vllm:time_to_first_token_seconds_count{namespace="llm-serving"}[5m]))
      - sum(rate(vllm:time_to_first_token_seconds_bucket{namespace="llm-serving", le="2.5"}[5m]))
    )
    / sum(rate(vllm:time_to_first_token_seconds_count{namespace="llm-serving"}[5m]))
```

Tử số là số request mỗi giây trừ đi số request có TTFT không quá 2,5 s, tức số request chậm. Khi không có traffic, cả tử và mẫu bằng 0 nên kết quả là NaN, và cảnh báo dùng chuỗi này không kêu.
<!-- nguồn: test case thứ hai trong common/observability/alerts/tests/llm-test.yaml (không có traffic thì NaN, không kêu) -->

## B.2. Bảy quy tắc cảnh báo

Bảng B.1 tóm tắt bảy quy tắc trong `alerts/llm.yaml`. Nhóm đầu báo triệu chứng mà người dùng thấy, nhóm sau báo nguyên nhân ở tầng nền tảng và autoscaling. Mức page cần người trực xử lý ngay, mức ticket xử lý trong giờ làm việc.
<!-- nguồn: comment đầu common/observability/alerts/llm.yaml -->

**Bảng B.1.** Bảy quy tắc cảnh báo, mức và điều kiện kêu

| Cảnh báo | Mức | `for` | Điều kiện |
|---|---|---|---|
| `LLMSLOBurnFast` | page | 1 phút | Tỷ lệ request có TTFT trên 2,5 s vượt 20% ở cả cửa sổ 5 phút và 1 phút |
| `LLMErrorRateHigh` | page | 1 phút | Từ 1% request trả 5xx trong 5 phút, đo ở Traefik |
| `LLMAtMaxReplicas` | ticket | 15 phút | HPA đã bằng số replica tối đa mà vẫn có request chờ |
| `LLMPodPending` | ticket | 10 phút | Có pod vLLM ở trạng thái Pending |
| `LLMPodNotReady` | page | 15 phút | Có pod vLLM đang Running mà chưa Ready |
| `LLMPodCrashLooping` | page | 5 phút | Container vLLM ở CrashLoopBackOff trong 5 phút gần nhất |
| `KedaScalerErrors` | page | 1 phút | ScaledObject đang fallback hoặc không Ready, trừ khi đang tạm dừng |
<!-- nguồn: common/observability/alerts/llm.yaml (expr, for, labels.severity), commit ed381ba -->

`LLMErrorRateHigh` đọc chuỗi do Traefik sinh ra. Trong các lượt đánh giá, runner gọi thẳng Service của vLLM, không qua Traefik, nên chuỗi này rỗng và quy tắc không kêu được. Đoạn mã B.2 là quy tắc `LLMSLOBurnFast` đầy đủ.
<!-- nguồn: comment của LLMErrorRateHigh trong common/observability/alerts/llm.yaml: chuỗi llm:error_ratio:rate5m chỉ có khi request đi qua Traefik; runner gọi thẳng Service (envs/*/experiments/matrix*.yaml) -->

**Đoạn mã B.2.** Quy tắc `LLMSLOBurnFast` (`alerts/llm.yaml`)
<!-- nguồn: common/observability/alerts/llm.yaml, commit ed381ba -->

```yaml
- alert: LLMSLOBurnFast
  expr: |
    llm:ttft_bad_ratio:rate5m > (4 * 0.05)
    and
    llm:ttft_bad_ratio:rate1m > (4 * 0.05)
  for: 1m
  labels: {severity: page}
  annotations:
    summary: "Hơn 20% request phải chờ token đầu tiên quá 2,5 s (5 phút và 1 phút gần nhất)"
    description: "Burn rate TTFT ≥ 4 so với SLO 95%. Xem dashboard Autoscaling: replica mong muốn so với đang có, pod đang khởi động."
    runbook_url: "https://github.com/bi6-cat/llm-k8s-autoscaling/blob/main/docs/runbooks/LLMSLOBurnFast.md"
```

Ngưỡng `4 * 0.05` là burn rate 4 so với ngân sách lỗi 5% của SLO 95%. Cửa sổ 5 phút xác nhận vi phạm đủ lâu, cửa sổ 1 phút xác nhận vi phạm vẫn đang diễn ra, nên cảnh báo tắt sớm sau khi hệ thống hồi phục. Annotation không chèn giá trị đo (`$value`), vì unit test so annotation theo từng ký tự.
<!-- nguồn: comment của LLMSLOBurnFast và comment đầu file common/observability/alerts/llm.yaml -->

## B.3. Unit test mẫu

Mỗi quy tắc cảnh báo có ít nhất một unit test trong `alerts/tests/llm-test.yaml`, chạy bằng `promtool test rules`. File có 9 test case cho bảy quy tắc. Lệnh `make alerts-test` kiểm ba việc theo thứ tự. Đầu tiên, mỗi cảnh báo phải có nhãn `severity`, có runbook và có test. Sau đó lệnh kiểm cú pháp của mọi quy tắc, rồi chạy toàn bộ unit test. CI chạy lệnh này ở mỗi PR. Lần chạy lại gần nhất đạt với 4 quy tắc trong `rules/vllm.yaml`, 5 quy tắc trong `rules/slo.yaml` và 7 quy tắc trong `alerts/llm.yaml`.
<!-- nguồn: Makefile (alerts-test, alerts-coverage); .github/workflows/ci.yaml (on: pull_request, bước make alerts-test); make alerts-test SHELL=bash, 27/11/2026, máy Trình (promtool 3.15.0): "SUCCESS: 4 rules found" (vllm.yaml), "SUCCESS: 7 rules found" (llm.yaml), kết thúc "SUCCESS"; 9 test case đếm bằng grep "^  - name:" llm-test.yaml; slo.yaml có 5 dòng record -->

Đoạn mã B.3 là test case đầu tiên của `LLMSLOBurnFast`. Test tạo dữ liệu giả cho 30 phút với 40 request mỗi phút. Từ phút 10 tới phút 20, chỉ một nửa số request có TTFT không quá 2,5 s; trước và sau khoảng đó, mọi request đều đạt. Giá trị `0+10x120` nghĩa là 121 mẫu bắt đầu từ 0, mỗi mẫu tăng 10, cách nhau 15 s.
<!-- nguồn: comment đầu common/observability/alerts/tests/llm-test.yaml (cú pháp giá trị) và comment của test case đầu -->

**Đoạn mã B.3.** Unit test kiểm `LLMSLOBurnFast` kêu khi 50% request chậm và tắt khi hồi phục (trích)
<!-- nguồn: common/observability/alerts/tests/llm-test.yaml, commit ed381ba -->

```yaml
- name: LLMSLOBurnFast kêu khi 50% request chậm, tắt ngay khi hồi phục
  interval: 15s
  input_series:
    - series: 'vllm:time_to_first_token_seconds_count{namespace="llm-serving", pod="vllm-a"}'
      values: '0+10x120'
    - series: 'vllm:time_to_first_token_seconds_bucket{namespace="llm-serving", pod="vllm-a", le="2.5"}'
      values: '0+10x40 405+5x39 610+10x40'
  promql_expr_test:
    - expr: llm:ttft_bad_ratio:rate5m
      eval_time: 20m
      exp_samples:
        - labels: 'llm:ttft_bad_ratio:rate5m'
          value: 0.5
  alert_rule_test:
    - eval_time: 9m
      alertname: LLMSLOBurnFast
      exp_alerts: []
    - eval_time: 11m                   # cửa sổ 5 phút mới khoảng 10% xấu: chưa kêu
      alertname: LLMSLOBurnFast
      exp_alerts: []
    - eval_time: 15m
      alertname: LLMSLOBurnFast
      exp_alerts:
        - exp_labels: {severity: page}
          # … ba annotation như Đoạn mã B.2
    - eval_time: 22m                   # cửa sổ 1 phút đã về 0%: phải tắt
      alertname: LLMSLOBurnFast
      exp_alerts: []
```

Bốn thời điểm kiểm cho thấy hành vi của hai cửa sổ. Ở phút 11, cửa sổ 1 phút đã 50% xấu nhưng cửa sổ 5 phút mới khoảng 10%, vì vậy cảnh báo chưa kêu, và một đợt chậm ngắn không gây page. Ở phút 15, cả hai cửa sổ vượt 20% đã quá 1 phút, nên cảnh báo kêu. Ở phút 22, cửa sổ 5 phút vẫn còn khoảng 30% xấu, nhưng cửa sổ 1 phút đã về 0%, và cảnh báo tắt. Test case thứ hai của quy tắc này kiểm trường hợp không có traffic. Khi đó bộ đếm đứng yên, tỷ lệ là NaN và cảnh báo im lặng.
<!-- nguồn: common/observability/alerts/tests/llm-test.yaml, hai test case đầu và comment tính tay của chúng, commit ed381ba -->
