<!-- Mục đích: mục 3.4 của luận văn (Thiết kế giám sát, SLO và cảnh báo). Người viết: Trình. Quy ước: docs/luan-van/README.md -->
<!-- Số tạm: Bảng 3.4a–3.4d, đánh lại thành Bảng 3.x khi ghép chương 3 (README, mục "Quy ước viết"). -->
## 3.4. Thiết kế giám sát, SLO và cảnh báo

Tầng giám sát trả lời ba câu hỏi: người dùng có đang được phục vụ tốt không, khi nào cần con người vào cuộc và gấp tới mức nào, và khi đó phải làm gì. Thiết kế bám vào bốn yêu cầu ở mục 3.1: ba dashboard (F5); sáu cảnh báo gửi tới Telegram, mỗi cảnh báo có một runbook, tức tài liệu hướng dẫn xử lý riêng (F6); với cấu hình autoscaling A2 (mục 3.3), tỷ lệ request đạt mục tiêu mức dịch vụ (*Service Level Objective*, SLO) từ 95% trở lên khi tải ổn định (N1); cảnh báo SLO kêu trong vòng 5 phút sau khi SLO bị vi phạm thật, và không có page giả, tức cảnh báo gọi người trực (*page*) trong khi tỷ lệ request xấu theo log phía client dưới 20% (N7). Các khái niệm SLI, SLO, ngân sách lỗi, burn rate, TTFT và TPOT được trình bày ở chương 2; mục 3.4.2 và 3.4.3 nhắc lại định nghĩa ở chỗ dùng. Hệ thống dùng chart kube-prometheus-stack [@kube-prometheus-stack], gồm Prometheus, Alertmanager, Grafana và kube-state-metrics.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §3 (F5, F6), §4 (N1, N7); docs/chi-tiet/01-bai-toan-yeu-cau.md §8 ("Biết khi nào có vấn đề và phải làm gì" → F5, F6, N7); common/platform/kube-prometheus-stack-values.yaml (chart 92.1.1) -->

### 3.4.1. Thu thập metric

Prometheus định kỳ kéo (*scrape*) metric từ đường dẫn `/metrics` của từng thành phần, theo các khai báo PodMonitor hoặc ServiceMonitor (tài nguyên của Prometheus Operator, tạo từ manifest và values của chart trong Git) (Bảng 3.4a).

**Bảng 3.4a.** Các nguồn metric và chu kỳ thu

| Nguồn | Metric chính | Chu kỳ | Dùng cho |
|---|---|---|---|
| vLLM, mỗi pod | `vllm:num_requests_running`, `vllm:num_requests_waiting`; histogram TTFT và TPOT; `vllm:kv_cache_usage_perc` | 5 s | SLI; tín hiệu autoscaling |
| Traefik (cửa vào) | `traefik_service_requests_total` theo mã HTTP | 5 s | SLI tỷ lệ lỗi |
| `nvidia_gpu_exporter` | `nvidia_smi_utilization_gpu_ratio`, VRAM, công suất, nhiệt độ | 5 s | Tín hiệu A1; dashboard |
| kube-state-metrics | Trạng thái pod, replica của HPA, condition của ScaledObject | 15 s | Cảnh báo nền tảng; GPU-giờ |
| KEDA operator | Giá trị metric KEDA đọc được, truy vấn lỗi | 15 s | Dashboard; chẩn đoán |
<!-- nguồn: common/serving/podmonitor.yaml (5s); common/platform/kube-prometheus-stack-extras/traefik-podmonitor.yaml (5s); common/platform/gpu-exporter/podmonitor.yaml (5s); common/platform/kube-prometheus-stack-values.yaml (scrapeInterval 15s); common/platform/keda-metrics-values.yaml (PodMonitor, chu kỳ để trống = 15 s); common/platform/kube-state-metrics-values.yaml (kube_scaledobject_status_condition); tên metric GPU từ common/observability/dashboards/serving-gpu.json; docs/chi-tiet/00-thong-so.md §9.4 -->

vLLM và GPU được thu mỗi 5 s vì là tín hiệu autoscaling: scrape 5 s cộng chu kỳ đồng bộ 5 s của HPA giữ độ trễ đọc tín hiệu quanh 10 s. Traefik dùng cùng chu kỳ 5 s. Trạng thái object đổi chậm hơn nên giữ chu kỳ chung 15 s. `nvidia_gpu_exporter` đọc metric GPU qua `nvidia-smi`, thay cho DCGM exporter, vì DCGM có thể không hỗ trợ đầy đủ GPU dòng GeForce như RTX 5060 ở máy nhà, và đồ án dùng chung một exporter ở cả nhà lẫn VM thuê; exporter này không gắn nhãn pod nên chỉ dùng được khi node chỉ chạy vLLM (mục 3.3). Tên và ý nghĩa metric của vLLM lấy theo tài liệu [@vllm-metrics] và mã nguồn của bản đã ghim v0.31.0.
<!-- nguồn: common/serving/podmonitor.yaml (comment "scrape 5 s + HPA 5 s ≈ 10 s"); docs/chi-tiet/00-thong-so.md §9.3 (sync HPA 5 s); docs/chi-tiet/03-kien-truc-autoscaling.md §13.4, §17.1; docs/adr/005-sua-thiet-ke-sau-review.md T9; common/platform/gpu-exporter/daemonset.yaml (header); docs/chi-tiet/03-kien-truc-autoscaling.md §17.1 (GeForce, dùng ở cả nhà lẫn VM thuê); common/observability/dashboards/README.md (vLLM v0.31.0) -->

Recording rule là biểu thức PromQL được tính định kỳ và lưu thành chuỗi có tên riêng. Bốn quy tắc SLI, tính mỗi 15 s, cho tỷ lệ request có TTFT xấu trên cửa sổ 1, 5, 30 phút (`llm:ttft_bad_ratio:rate1m`…) và tỷ lệ lỗi 5xx trên 5 phút (`llm:error_ratio:rate5m`); cảnh báo và dashboard đọc chung nên luôn khớp nhau. Bốn quy tắc khác, tính mỗi 5 s, phục vụ dashboard. ScaledObject của KEDA không dùng recording rule, vì recording rule thêm một chu kỳ trễ vào vòng autoscaling.
<!-- nguồn: common/observability/rules/slo.yaml (4 rule, evaluationInterval 15 s); common/observability/rules/vllm.yaml (4 rule, interval 5s); common/platform/kube-prometheus-stack-values.yaml (evaluationInterval 15s); CONTRIBUTING.md §4 -->

Ba dashboard của F5 chia theo câu hỏi người xem cần trả lời: *Serving và GPU* (20 panel) cho biết vLLM và GPU đang làm gì; *Autoscaling* (9 panel) đặt replica mong muốn cạnh replica đang có và trạng thái từng pod; *SLO và chi phí* (16 panel) vẽ SLI, burn rate, ngân sách lỗi và GPU-giờ trên đúng khoảng thời gian đang chọn, để xem lại từng lượt đánh giá. GPU-giờ đếm pod đã được xếp lên node, vì pod đang tắt vẫn giữ GPU còn pod Pending thì chưa. Thời gian giữ dữ liệu (*retention*) ở máy nhà là 3 ngày vì PC chỉ có 16 GB RAM; số liệu đánh giá không phụ thuộc retention vì runner xuất riêng dữ liệu từng lượt (mục 4.11).
<!-- nguồn: common/observability/dashboards/README.md; số panel đếm từ serving-gpu.json (20), autoscaling.json (9), slo-cost.json (16) ngày 18/11; docs/chi-tiet/03-kien-truc-autoscaling.md §17.3, §17.4; docs/nhat-ky/lam-viec/trinh/tuan-05.md mục 07/11 TR3 (GPU-giờ theo kube_pod_status_scheduled); envs/home/platform/kube-prometheus-stack-values.yaml (retention 3d, retentionSize 4GB). Lệch: Thông số §9.4 ghi cloud 15 ngày, envs/cloud/platform/ không đặt retention -->

### 3.4.2. SLI và SLO

Chỉ số mức dịch vụ (*Service Level Indicator*, SLI) là tỷ lệ sự kiện tốt trên tổng sự kiện; mục tiêu mức dịch vụ (*Service Level Objective*, SLO) là mục tiêu cho SLI đó; 1 − SLO là ngân sách lỗi (*error budget*). Các SLI của đồ án nằm ở Bảng 3.4b.

**Bảng 3.4b.** SLI, nguồn đo và SLO

| SLI | Request tốt khi | Nguồn | SLO | Dùng cho |
|---|---|---|---|---|
| TTFT | TTFT ≤ 2,5 s | `vllm:time_to_first_token_seconds`, bucket `le="2.5"` | 95% (ngân sách 5%) | Cảnh báo `LLMSLOBurnFast` |
| TPOT | TPOT ≤ 100 ms | `vllm:request_time_per_output_token_seconds` (trung bình mỗi request), bucket `le="0.1"`; `vllm:inter_token_latency_seconds` (từng khoảng giữa hai token) | Gộp vào "request đạt SLO" | Dashboard |
| Tỷ lệ lỗi | Không trả 5xx | `traefik_service_requests_total` | 99% (ngân sách 1%) | Cảnh báo `LLMErrorRateHigh` |
| Request đạt SLO | TTFT, TPOT đều đạt; không lỗi, không timeout, stream không bị cắt | Log của máy tạo tải | 95% (N1) | Nghiệm thu (chương 5) |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §4 (N1), §6; docs/chi-tiet/04-van-hanh.md §2.1, §2.2; common/observability/rules/slo.yaml; common/observability/dashboards/slo-cost.json (TPOT dùng vllm:request_time_per_output_token_seconds le="0.1"); common/observability/dashboards/serving-gpu.json (vẽ vllm:inter_token_latency_seconds cạnh vạch 100 ms). Vận hành §2.1 chỉ ghi inter_token_latency. TTFT 2,5 s còn đánh dấu "tạm" ở Thông số §6; ADR-003 chưa có (18/11) -->

Thời gian tới token đầu (*time to first token*, TTFT) là SLI chính, vì người dùng cảm nhận nó rõ nhất; trên vLLM, TTFT gồm cả thời gian chờ trong hàng đợi nên tăng đầu tiên khi quá tải. Thời gian sinh mỗi token tiếp theo (*time per output token*, TPOT) có ngưỡng 100 ms, tức ít nhất 10 token/s, nhanh hơn tốc độ đọc; TPOT ít biến động hơn nên không dùng để cảnh báo; nó được vẽ trên dashboard và gộp vào tiêu chí request đạt SLO khi nghiệm thu. Tỷ lệ lỗi đo ở Traefik, vì khi không còn pod Ready thì chỉ Traefik thấy request và trả 502 hoặc 503. SLI cộng gộp mọi pod, vì SLO đặt cho cả dịch vụ. Mức 95% áp cho tải ổn định, tức pha `steady` của KB1 và riêng pha `sustain` của KB3, không áp cho kịch bản tăng đột ngột KB2: khi tải tăng gấp 6 lần trong 30 giây thì hệ thống nào có cold start cũng vi phạm SLO vài phút.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §2.1; docs/chi-tiet/00-thong-so.md §4 ("Vì sao chọn các ngưỡng này": 95%), §6 (TPOT 100 ms ≈ ≥ 10 token/s); common/observability/rules/slo.yaml (comment Traefik; sum gộp mọi pod); common/observability/dashboards/README.md (vLLM thật tính TTFT gồm thời gian chờ) -->

Histogram chỉ lưu bộ đếm tích luỹ theo các biên bucket cố định, nên ngưỡng SLO phải trùng một biên có thật của phiên bản vLLM đã ghim. Nếu ghi `le="2"` mà không có bucket đó, truy vấn trả về rỗng và cảnh báo không bao giờ kêu, mà không có lỗi nào được báo. Bản thiết kế đầu ghi hai ngưỡng lệch nhau: SLO 2 s cho nghiệm thu, nhưng recording rule dùng bucket 2,5 s, nên cảnh báo và nghiệm thu đo hai thứ khác nhau. Sau review, nhóm dùng một ngưỡng chung cho cảnh báo (N7) và nghiệm thu (N1), giá trị hiện tại là 2,5 s, và đã kiểm biên này có trên `/metrics` của vLLM v0.31.0. Ngưỡng TPOT 100 ms cũng trùng bucket `le="0.1"`.
<!-- nguồn: docs/adr/005-sua-thiet-ke-sau-review.md T3; docs/chi-tiet/04-van-hanh.md §2.1; common/observability/rules/slo.yaml (comment le="2.5", vllm/v1/metrics/buckets.py); docs/nhat-ky/lam-viec/quang/tuan-03.md mục 23/10 và docs/nhat-ky/tuan-01.md (le="2.5" có trên /metrics); docs/nhat-ky/lam-viec/trinh/tuan-05.md mục 07/11 TR3 (TPOT có bucket 0,1) -->

Nghiệm thu dùng log của máy tạo tải, vì SLI phía server có ba điểm mù. Histogram TTFT chỉ ghi request đã có token đầu, nên bỏ qua request bị timeout khi còn trong hàng đợi. Request bị cắt giữa stream vẫn mang mã 200, vì header đã gửi đi. Trong các lượt đánh giá, máy tạo tải gọi thẳng Service của vLLM, không đi qua Traefik, nên SLI lỗi không thấy lỗi của các lượt này. SLI phía server vẫn cần cho cảnh báo trong lúc vận hành, còn N7 đối chiếu mỗi page với tỷ lệ request xấu theo log client.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §2.1 (ba điểm lưu ý); docs/chi-tiet/00-thong-so.md §4 (N7), §6; envs/cloud/experiments/matrix-v2.yaml (target.service_url http://vllm.llm-serving.svc:8000); docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 16/11 TR7 (llm:error_ratio:rate5m rỗng khi gọi thẳng Service). Lệch: Thông số §7 vẫn ghi máy tạo tải đi qua route riêng của Traefik (đã lược, ADR-006 §3.1) -->

### 3.4.3. Cảnh báo theo burn rate

Cảnh báo kiểu "TTFT phân vị 95 vượt ngưỡng" dễ kêu vì nhiễu ngắn và không cho biết mức nghiêm trọng. Đồ án cảnh báo theo tốc độ tiêu hao ngân sách lỗi (*burn rate*):

$$\text{burn rate} = \frac{\text{tỷ lệ request xấu trong cửa sổ}}{1 - \text{SLO}}$$

Với SLO 95%, burn rate lớn nhất là 20, khi mọi request đều xấu. Chương "Alerting on SLOs" của SRE Workbook [@sre-workbook] xét hai cửa sổ cùng lúc: cửa sổ dài xác nhận vấn đề có thật, cửa sổ ngắn xác nhận vấn đề còn tiếp diễn để cảnh báo tắt nhanh khi đã hồi phục; với SLO 99,9%, sách gợi ý page ở burn rate 14,4 trên cửa sổ 1 giờ và 5 phút. Đồ án dùng cửa sổ 5 phút và 1 phút:

```promql
llm:ttft_bad_ratio:rate5m > (4 * 0.05)
and
llm:ttft_bad_ratio:rate1m > (4 * 0.05)
```

kèm `for: 1m`: điều kiện phải đúng liên tục 1 phút thì cảnh báo mới chuyển từ *pending* sang *firing*. Burn rate 4 ứng với 20% request có TTFT vượt 2,5 s, cũng là ngưỡng định nghĩa page giả của N7, nên cảnh báo và nghiệm thu dùng chung ngưỡng 20% (N7 tính request xấu theo log client, gồm cả TPOT và lỗi). Cặp cửa sổ rút ngắn (5 phút thay cho 1 giờ) nhạy hơn với đợt xấu ngắn; điều kiện hai cửa sổ cộng `for` giảm rủi ro này, và số page giả được đo trong VH6 (chương 5). Mức ticket `LLMSLOBurnSlow` (10% trên 30 phút và 5 phút) thuộc nhóm Could, chưa làm.
<!-- nguồn: docs/chi-tiet/02-kien-thuc-nen.md §5.2; docs/chi-tiet/04-van-hanh.md §3.2 (cảnh báo phụ), §3.3 (14,4; 1 giờ và 5 phút; burn rate tối đa 20); common/observability/alerts/llm.yaml (LLMSLOBurnFast: expr, for 1m, page; comment vai trò hai cửa sổ); docs/chi-tiet/00-thong-so.md §4 (N7: page giả < 20%), §5 (LLMSLOBurnSlow: Could) -->

Thời gian phát hiện ước lượng được từ thiết kế, với hai giả định: tốc độ request không đổi, và trước đó đã có ít nhất 5 phút traffic tốt. Nếu tỷ lệ request xấu nhảy từ 0 lên $x$, sau $t$ giây tỷ lệ trên cửa sổ 5 phút xấp xỉ $x t / 300$, nên vượt ngưỡng $\theta = 0{,}2$ sau $300\theta / x$ giây; cửa sổ 1 phút vượt sớm hơn. Cộng `for` 60 s và 30 s gom nhóm của Alertmanager (mục 3.4.5), tin nhắn tới sau khoảng

$$t_{\text{báo}} \approx \frac{300\,\theta}{x} + 60 + 30 \quad \text{(giây)}.$$

Công thức bỏ qua trễ scrape (5 s) và chu kỳ tính rule (15 s). Với $x$ từ 50% đến 100%, $t_{\text{báo}}$ khoảng 2,5–3,5 phút, trong giới hạn 5 phút của N7. Vi phạm càng nhẹ thì cảnh báo càng chậm, vì ngân sách bị tiêu chậm: khi $x$ chỉ nhỉnh hơn 20%, $t_{\text{báo}}$ có thể vượt 5 phút (cách N7 đặt mốc vi phạm và số đo ở chương 5); không vượt 20% thì không kêu. Cửa sổ 1 giờ cho $3600\theta / x \ge 720$ giây, tức ít nhất 12 phút, vượt xa giới hạn 5 phút của N7. Sau khi hồi phục, cửa sổ 1 phút xuống dưới ngưỡng sau $60(1 - \theta / x)$ giây, nên quy tắc hết firing trong vòng một phút; tin "đã hết" tới muộn hơn, vì Alertmanager chờ `group_interval` 5 phút mới báo thay đổi của nhóm. Khi vận hành thật chỉ cần đổi độ dài cửa sổ; số đo thực tế ở chương 5.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.3 (ước tính 3–4 phút); docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 16/11 "công cụ đo LT8" (dự đoán θ·300/x + 60 s; hết cảnh báo 60·(1 − θ/x)); common/platform/alertmanager-values.yaml (group_wait 30s, group_interval 5m); common/serving/podmonitor.yaml (scrape 5s); common/platform/kube-prometheus-stack-values.yaml (evaluationInterval 15s); docs/nhat-ky/van-hanh.md mục LT8 "Hệ quả cho V2 (VH6)" (x gần 0,2 thì có thể vượt 5 phút). 2,5–3,5 phút và 12 phút tính từ công thức, không phải số đo -->

Tỷ lệ xấu tính theo dạng (tổng − tốt) / tổng. Khi không có traffic, phép chia 0/0 cho kết quả NaN, mà mọi phép so sánh với NaN đều sai, nên cảnh báo im lặng; đó là điều mong muốn, vì không có request thì không ai bị ảnh hưởng. Một unit test giữ hành vi này (mục 4.7).
<!-- nguồn: common/observability/rules/slo.yaml (comment (0 − 0)/0 = NaN); docs/chi-tiet/04-van-hanh.md §2.3; common/observability/alerts/tests/llm-test.yaml (test "LLMSLOBurnFast im lặng khi không có traffic") -->

### 3.4.4. Danh sách cảnh báo

Bộ cảnh báo theo năm nguyên tắc: mỗi cảnh báo dẫn tới một hành động; có hai mức, *page* khi người dùng đang bị ảnh hưởng và cần người trực ngay, *ticket* khi xử lý trong giờ làm việc là đủ; triệu chứng (SLO) trước, nguyên nhân (pod, HPA, KEDA) sau; mỗi cảnh báo có `runbook_url` trỏ tới một runbook khoảng nửa trang; mỗi quy tắc có unit test `promtool test rules` chạy trong CI để bắt biểu thức rỗng (mục 4.7). F6 đếm sáu cảnh báo nhưng có bảy quy tắc và bảy runbook, vì "pod vLLM không khởi động được" tách thành `LLMPodNotReady` và `LLMPodCrashLooping` (Bảng 3.4c).
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.1, §3.2 (6 cảnh báo = 7 quy tắc, 7 runbook), §4.1; CONTRIBUTING.md §4; common/observability/alerts/tests/llm-test.yaml (8 test); docs/runbooks/ (7 file) -->

**Bảng 3.4c.** Bảy quy tắc của sáu cảnh báo bắt buộc

| Cảnh báo | Điều kiện (rút gọn) | `for` | Mức | Ý nghĩa; lý do của điều kiện |
|---|---|---|---|---|
| `LLMSLOBurnFast` | Hơn 20% request có TTFT > 2,5 s, trên cả cửa sổ 5 phút và 1 phút | 1 phút | page | Người dùng phải chờ lâu (mục 3.4.3) |
| `LLMErrorRateHigh` | Tỷ lệ 5xx ≥ 1% trong 5 phút | 1 phút | page | Request bị từ chối; ngưỡng đúng bằng ngân sách lỗi (xem dưới bảng) |
| `LLMAtMaxReplicas` | Replica bằng mức tối đa **và** hàng đợi > 0 | 15 phút | ticket | Autoscaling hết dư địa; chạy tối đa mà vẫn kịp thì chưa phải vấn đề |
| `LLMPodPending` | Pod vLLM ở trạng thái Pending | 10 phút | ticket | Thường do hết GPU |
| `LLMPodNotReady` | Pod vLLM đang Running nhưng chưa Ready | 15 phút | page | Lâu hơn cold start tối đa; chỉ xét Running để không trùng `LLMPodPending` |
| `LLMPodCrashLooping` | Có `CrashLoopBackOff` trong 5 phút gần nhất | 5 phút | page | OOM, sai tham số, lỗi CUDA; xét cả cửa sổ vì trạng thái chờ biến mất mỗi lần container chạy lại, làm `for` đặt lại |
| `KedaScalerErrors` | ScaledObject có `Fallback=True` hoặc `Ready` khác True, trừ khi `Paused` | 1 phút | page | Autoscaling bị "mù", giữ số replica cố định |
<!-- nguồn: common/observability/alerts/llm.yaml (7 rule: expr, for, severity, comment lý do từng rule); docs/chi-tiet/04-van-hanh.md §3.2; docs/nhat-ky/lam-viec/trinh/tuan-03.md mục 25/10 (Quyết định và lý do) -->

`LLMErrorRateHigh` nhạy hơn nhiều so với `LLMSLOBurnFast`: ngưỡng 1% trên cửa sổ 5 phút ứng với burn rate 1. Thiết kế dự định dùng `for: 1m` để không page vì vài lỗi 503 lẻ khi chuyển pod, nhưng `for` không lọc được trường hợp này. Ví dụ ở tải thấp 1 request/s, năm lỗi liền nhau đã chiếm khoảng 1,7% cửa sổ 5 phút và nằm trong cửa sổ suốt 5 phút, lâu hơn 1 phút của `for`, nên cảnh báo vẫn kêu. Nhóm giữ nguyên quy tắc trong đợt đánh giá để không đổi cấu hình đã kiểm thử sát ngày đóng băng dữ liệu; chuyển sang dạng burn rate hai cửa sổ như `LLMSLOBurnFast` là một hướng cải tiến (chương 6).
<!-- nguồn: common/observability/alerts/llm.yaml (LLMErrorRateHigh: expr >= 0.01, for 1m, comment "một lần chuyển pod có thể sinh vài 503 lẻ"); docs/chi-tiet/04-van-hanh.md §3.2; phép tính 5 / 300 ≈ 1,7%; thử bằng promtool và quyết định giữ nguyên: docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 18/11 "Luận văn: khung docs/luan-van/ và mục 3.4" -->

Tín hiệu của `KedaScalerErrors` được chọn lại sau khi thử. Bản đầu đếm lỗi truy vấn của KEDA; trên cluster kind, quy tắc đó không bao giờ kêu dù đã đạt unit test, vì khi đã vào fallback, KEDA v2.21.0 ngừng tăng bộ đếm lỗi. Quy tắc hiện tại đọc condition của ScaledObject qua kube-state-metrics, là triệu chứng giữ nguyên suốt sự cố. Bài học: unit test chỉ kiểm biểu thức trên dữ liệu tự tạo, nên cảnh báo còn phải được thử bằng sự cố thật (VH4, VH6, chương 5).
<!-- nguồn: common/observability/alerts/llm.yaml (KedaScalerErrors, comment); docs/nhat-ky/lam-viec/trinh/tuan-06.md hai mục 15/11 về KedaScalerErrors (rule cũ increase(keda_scaler_detail_errors_total[2m]) >= 3; bộ đếm = 1 khi numberOfFailures = 67; pkg/fallback/fallback.go trả err = nil); common/platform/kube-state-metrics-values.yaml -->

### 3.4.5. Định tuyến và thông báo

Alertmanager nhận cảnh báo từ Prometheus, định tuyến từng cảnh báo theo một cây rồi gom nhóm trong từng nhánh [@alertmanager-config]: mỗi cảnh báo dừng ở nhánh đầu tiên khớp nhãn, không khớp nhánh nào thì về gốc (Bảng 3.4d).

**Bảng 3.4d.** Định tuyến cảnh báo trong Alertmanager

| Nhánh (theo thứ tự) | Cảnh báo | Nơi nhận | Nhắc lại | Báo lúc hết |
|---|---|---|---|---|
| `alertname = Watchdog` | `Watchdog` của chart | Không gửi | – | – |
| `severity = page` | 5 quy tắc page | Telegram | Mỗi 1 giờ | Có |
| `severity = ticket` hoặc `critical` | 2 quy tắc ticket; critical của chart | Telegram | Sau 24 giờ | Không |
| Gốc | Warning, info của chart | Không gửi | – | – |
<!-- nguồn: common/platform/alertmanager-values.yaml (route, receivers, repeat_interval 1h/24h, send_resolved); docs/chi-tiet/00-thong-so.md §9.4 -->

Gốc không gửi đi đâu, vì chart có sẵn 134 cảnh báo, 100 ở mức warning hoặc info; nhiều cái trùng ý với cảnh báo của nhóm (như `KubeHpaMaxedOut` với `LLMAtMaxReplicas`) và sẽ kêu liên tục khi đánh giá, trái nguyên tắc mỗi tin phải dẫn tới hành động. Chúng vẫn hiện trên giao diện; chỉ cảnh báo critical của chart, hiếm và đáng biết ngay như đĩa sắp đầy, mới tới Telegram. Bản thiết kế đầu đặt gốc là ticket và bị bỏ vì lý do này. Ticket chỉ báo một lần, vì 24 giờ dài hơn một phiên đánh giá. Cảnh báo gom theo tên (ba pod cùng crash là một tin): nhóm mới chờ 30 s để gom rồi mới báo, nhóm đã báo thì chờ 5 phút mới báo thay đổi (cảnh báo mới vào nhóm hoặc đã hết). Tin có nhãn môi trường (`[home]`, `[sim]`, `[cloud]`) vì ba nơi dùng chung một bot, có link runbook, và mỗi danh sách (đang kêu, đã hết) tối đa 8 dòng tóm tắt để không vượt 4.096 ký tự của Telegram. Token bot và mã nhóm chat nằm trong Secret, không nằm trong Git (mục 4.2).
<!-- nguồn: common/platform/alertmanager-values.yaml (gốc "null": 134 cảnh báo, 100 warning/info, helm template chart 92.1.1 ngày 15/11; critical; group_by [alertname], group_wait 30s, group_interval 5m; template 8 dòng, 4096 ký tự; bot_token_file, chat_id_file); envs/{home,cloud,sim}/platform/kube-prometheus-stack-values.yaml (externalLabels env); docs/nhat-ky/lam-viec/trinh/tuan-06.md mục 15/11 "Alertmanager → Telegram" (Deviations: gốc route cũ là ticket) -->

### 3.4.6. Giám sát chính hệ thống giám sát

Quy tắc cảnh báo chạy trên chính Prometheus, nên Prometheus sập thì mọi cảnh báo cùng im lặng. `Watchdog` của chart luôn kêu để chứng minh đường Prometheus → Alertmanager còn sống; gửi nó tới một dịch vụ heartbeat bên ngoài, báo động khi mất tín hiệu (*dead man's switch*), là phần tuỳ chọn chưa làm, nên mất Prometheus chưa được báo tự động; đây là một hạn chế của đồ án. Ở phía autoscaling, ScaledObject A2 có chế độ dự phòng (*fallback*) [@keda-scaledobject-spec]: truy vấn tới Prometheus lỗi quá 3 lần liên tiếp thì KEDA giữ số replica ở mức tối đa, vì thừa GPU chỉ tốn tiền còn thiếu GPU thì người dùng chịu trễ. Mỗi chu kỳ đồng bộ 5 s, HPA hỏi metric server của KEDA và KEDA truy vấn Prometheus ngay lúc đó, mỗi truy vấn chờ tối đa 1 s; vì vậy lần lỗi thứ tư, cũng là lúc vào fallback, tới sau khoảng 20 s, trong giới hạn 30 s của N6 (số đo ở chương 5). Nếu Prometheus vẫn chạy nhưng KEDA không tới được nó (ví dụ mạng bị chặn, như kịch bản VH4), condition `Fallback=True` kích hoạt thêm `KedaScalerErrors` sau `for: 1m`; nếu chính Prometheus sập thì quy tắc này cũng im lặng, chỉ còn fallback bảo vệ người dùng. Mất một exporter thì khác: KEDA coi kết quả rỗng là 0 và không bật fallback, nên mỗi lượt đánh giá kiểm riêng tín hiệu có liên tục không (mục 3.3). VH4 kiểm đường fallback (chương 5).
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.5; common/platform/alertmanager-values.yaml (Watchdog → "null"); common/autoscaling/a2/scaledobject-a2.yaml (fallback failureThreshold 3, replicas = max; comment pollingInterval: với minReplicaCount ≥ 1, HPA hỏi mỗi chu kỳ sync 5 s; timeout "1000"; comment "thà thừa GPU còn hơn thiếu", "fallback sau khoảng 20 s"); docs/chi-tiet/00-thong-so.md §4 (N6 ≤ 30 s), §9.3; docs/chi-tiet/03-kien-truc-autoscaling.md §13.4 (ignoreNullValues; lượt invalid khi tín hiệu mất mẫu > 15 s); docs/adr/005-sua-thiet-ke-sau-review.md T6; docs/adr/006-chot-may-model-va-kich-ban-truoc-v2.md §3.1 (VH4 dùng NetworkPolicy tạm); common/observability/alerts/llm.yaml (KedaScalerErrors: for 1m; comment "Prometheus sập thì rule không chạy") -->

Hiện thực của các thiết kế trên được trình bày ở mục 4.6 và 4.7.
