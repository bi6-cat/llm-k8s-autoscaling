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

## 2026-10-25 – Máy tạo tải open-loop v1 (TR5)

- **Mã việc:** TR5 · **Môi trường:** không (máy cá nhân Windows; chưa chạy với vLLM hay simulator)
- **Đã làm:**
  1. Tạo nhánh `feat/tr5-loadgen` từ `origin/main` (thư mục mới, không phụ thuộc scaffold).
  2. Viết gói `loadgen/`: `scenarios.py` (λ(t) và pha của KB1, KB2, KB3 theo Thông số §7, cộng chế độ `CONST` cho các mức λ của ĐG1), `schedule.py` (lịch Poisson bằng thinning, seed theo kịch bản và số thứ tự lượt), `prompts.py` (prompt tổng hợp), `sender.py` (gửi theo lịch, đọc SSE, ghi CSV), `checks.py` (tự kiểm tra Môi trường §17), `__main__.py` (dòng lệnh `python -m loadgen`, có `--dry-run`).
  3. `pyproject.toml` + `uv.lock` (httpx 0.28.1; dev: pytest 9.1.1, ruff 0.17.2). 41 test trong `loadgen/tests/`.
- **Quyết định và lý do:**
  - Bố cục: uv project dạng `package = false`, code import thẳng từ `loadgen/` khi chạy ở gốc repo, đúng bố cục `loadgen/<module>.py` của CONTRIBUTING §1, không thêm tầng `src/`. Lệnh: `uv run --project loadgen pytest loadgen`.
  - **Không dùng tokenizer.** Prompt ghép từ 310 từ tiếng Anh, mỗi từ đúng 1 token với tokenizer Qwen2.5. Đã kiểm bằng `tokenizers` 0.22.1 trên `tokenizer.json` ở revision đã ghim; model nhà và cloud dùng chung một file (cùng sha256 `c0382117…`). Đo được: n từ + phần đầu "Request <id>:" = n + 8 token (với n = 256, 640, 1024). Số token thật (cả chat template) lấy từ `usage.prompt_tokens`. Lý do: `transformers` quá nặng cho pod tạo tải.
  - Seed sinh bằng SHA-256 của `(kịch bản, số thứ tự lượt, luồng)`, không dùng `hash()` của Python (đổi giữa các lần chạy). Hai luồng riêng cho thời điểm gửi và độ dài prompt. Có test ghi cứng giá trị seed để phát hiện ai đó vô tình đổi cách sinh.
  - Bẫy của httpx đã xử lý và có test:
    - client mặc định giới hạn 100 kết nối, khiến open-loop lặng lẽ thành closed-loop khi > 100 request đồng thời → đặt `max_connections=None`;
    - `timeout` của httpx tính cho từng thao tác chứ không cho cả request → bọc bằng `asyncio.timeout(120)`.
  - Bộ điều phối ngủ lặp tới đúng `t_sched`, vì `asyncio.sleep` có thể dậy sớm một khoảng bằng độ phân giải đồng hồ → không bao giờ gửi trước lịch.
  - CSV flush sau mỗi dòng (runner phát hiện treo khi 60 s không có dòng mới); mở file bằng mode `x` để không ghi đè lượt cũ. Khoá API đọc từ biến môi trường `LOADGEN_API_KEY`, không qua tham số dòng lệnh.
- **Kết quả và số đo:**
  - `pytest`: 41 passed trên Python 3.11, 3.12 và 3.15 (Windows). `ruff format --check`, `ruff check`: đạt.
  - Mutation test (13 cách làm hỏng code: pool 100, bỏ timeout, closed-loop, tính chunk `role` là token đầu, bỏ `include_usage`, ngủ một lần, sai hệ số KB2/KB3, seed bằng `hash()`, bỏ thinning…): 12/13 bị bắt. Cái còn lại ("dùng chung một luồng ngẫu nhiên") là mutation tương đương: `poisson_times` sinh xong mọi thời điểm trước khi rút độ dài prompt, nên hành vi không đổi.
  - `--dry-run` KB2, C = 1,2 req/s: 2644 request; pha pre khoảng 0,4–0,7 req/s, spike 3,0–3,8 req/s (kỳ vọng 3,6), drop 0,45–0,72 req/s (kỳ vọng 0,6). Số đếm theo từng phút nên dao động kiểu Poisson.
  - Smoke test dòng lệnh với server SSE giả trên 127.0.0.1, CONST 5 req/s × 10 s: 57/57 request, 0 lỗi; lệch lịch p50 9 ms, p99 18–19 ms; độ trễ event loop p99 7 ms, max 34 ms; CPU tối đa 6,6–15,3% một lõi. Số đo trên Windows (đồng hồ hẹn giờ thô hơn Linux), không phải trong pod.
  - **Chưa chạy với vLLM thật hay llm-d-inference-sim**, nên chưa kiểm được `ignore_eos` và định dạng chunk `usage` của server thật.
- **Sự cố:**
  - Test "không giới hạn kết nối" (socket thật, 150 request) đỏ 5/15 lần trên Python 3.11 Windows. Thăm dò cho thấy kết nối loopback đầu tiên mất ~0,35 s, làm mọi TTFT cùng tăng (0,65–0,88 s), không phải do pool. Đổi tiêu chí sang độ chênh TTFT (max − min < 0,5 s, server giữ 1 s): 0/12 lần đỏ trên 3.11, 0/6 trên 3.15, mutation "pool 100" vẫn bị bắt.
  - Mutation "pool 100" lúc đầu viết sai: `httpx.Limits()` không tham số là không giới hạn; giới hạn 100 chỉ là `DEFAULT_LIMITS` của client.
  - Docker Desktop tự tắt khi khởi động: log ghi `POST /license/reject` (điều khoản bản quyền bị từ chối). Không tự chấp nhận thay Trình. Vì vậy chưa chạy được simulator.
  - Công cụ Bash của agent lỗi tạm thời ở khâu kiểm tra quyền nhiều lần; chuyển sang PowerShell.
- **Khác thiết kế:**
  - `requests.csv` thêm cột `id` và `n_in_target` (số từ đã lên lịch); `n_in` là `usage.prompt_tokens` của server, gồm cả chat template (Môi trường §14.2 ghi `n_in` là số token của prompt). Cần Quang đồng ý vì runner và `build_tables.py` đọc file này (Kế hoạch §6, giao diện "Dữ liệu").
  - Thêm file `loadgen.json` (tham số, seed, `t0_unix`, pha, kết quả tự kiểm tra) để runner gộp vào `metadata.json` và `checks.json`.
  - CPU đo theo tỷ lệ **một lõi** (event loop chỉ chạy trên một luồng); thiết kế ghi "CPU < 70%" mà không nói tính trên gì.
  - Độ trễ event loop: thiết kế chỉ ghi "không có khoảng nghẽn bất thường", không có ngưỡng số, nên v1 chỉ báo cáo p99 và max, chưa chấm đạt/trượt. Cần chốt ngưỡng ở `00-thong-so.md`.
- **Còn phải làm:** chạy với simulator (cần Docker hoặc kind) và với vLLM ở nhà; image + Pod Guaranteed cho máy tạo tải trong cluster (Môi trường §3.6); route Traefik riêng cho máy tạo tải (Thông số §7); job `python` trong CI.
- **Liên kết:** nhánh `feat/tr5-loadgen`; `loadgen/`.
- **Dùng cho luận văn:** chương môi trường đánh giá (Môi trường §9): open-loop và lý do; phép thinning; cách sinh prompt không cần tokenizer; các bẫy của client HTTP (pool, timeout, đồng hồ) và cách test bắt chúng (mutation test). Có thể vẽ hình: λ(t) của KB2 và số request mỗi phút từ `--dry-run`.
