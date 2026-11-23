<!-- Mục đích: mục 3.5 của luận văn (Thiết kế giám sát, cảnh báo và xử lý sự cố), mẫu văn cho các mục khác. Người viết: Trình. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Số tạm: Bảng 3.5a–3.5b, đánh lại thành Bảng 3.x khi ghép chương 3 (README, mục "Quy ước viết"). -->
<!-- Thông điệp: (1) SLI tính ở phía server, cảnh báo và dashboard đọc chung một bộ recording rule; nghiệm thu dùng log của máy tạo tải vì SLI phía server có điểm mù. (2) Page theo burn rate trên hai cửa sổ 5 phút và 1 phút: vi phạm rõ thì có tin sau khoảng 2,5–3,5 phút, một đợt chậm ngắn thì không page. (3) Hệ thống tự xử lý việc lặp lại; người trực chỉ được gọi khi có việc phải làm, có runbook cho từng cảnh báo, và sửa cấu hình qua Git. -->
<!-- Soát số: chưa · Soát văn phong: chưa · Người viết đọc lại: chưa -->
## 3.5. Thiết kế giám sát, cảnh báo và xử lý sự cố

Giám sát phải cho người vận hành biết ba điều: dịch vụ có đạt SLO ở mục 3.1 không, khi nào cần vào cuộc, và vào cuộc thì làm gì. Nhóm dùng chart kube-prometheus-stack [@kube-prometheus-stack], gồm Prometheus thu metric và tính cảnh báo, Alertmanager gửi tin tới Telegram, Grafana vẽ dashboard. Nguyên tắc chung là để hệ thống tự xử lý việc lặp lại và chỉ gọi người khi có việc cần người làm.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §1 (bảng "Vận hành gồm những việc gì": quan sát, cảnh báo, xử lý); common/platform/kube-prometheus-stack-values.yaml (chart 92.1.1); common/platform/alertmanager-values.yaml (receiver Telegram) -->

### 3.5.1. SLI và dashboard

TTFT là SLI chính của dịch vụ. Người dùng cảm nhận TTFT rõ nhất, và vì vLLM tính TTFT gồm cả thời gian chờ trong hàng đợi, TTFT tăng đầu tiên khi hệ thống quá tải. Tỷ lệ lỗi đo ở Traefik, cửa vào của cluster, vì khi không còn pod Ready thì chỉ Traefik thấy request và trả mã 502 hoặc 503. TPOT ít biến động hơn nên chỉ được vẽ trên dashboard và tính vào tiêu chí request đạt SLO khi nghiệm thu (Bảng 3.5a).
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §2.1 (bảng "Chọn SLI": vì sao chọn TTFT, tỷ lệ lỗi đo ở Traefik, TPOT chỉ theo dõi); common/observability/dashboards/README.md (vLLM thật tính TTFT gồm thời gian chờ); common/observability/rules/slo.yaml (comment Traefik thấy 502/503); docs/chi-tiet/00-thong-so.md §6 (request đạt SLO gồm TTFT và TPOT) -->

**Bảng 3.5a.** SLI và nguồn đo

| SLI | Request tốt khi | Nguồn | Dùng cho |
|---|---|---|---|
| TTFT | TTFT ≤ 2,5 s (mục 3.1) | Histogram `vllm:time_to_first_token_seconds`, bucket `le="2.5"` | Cảnh báo `LLMSLOBurnFast`, dashboard |
| Tỷ lệ lỗi | Không trả mã 5xx | `traefik_service_requests_total` | Cảnh báo `LLMErrorRateHigh`, dashboard |
| TPOT | TPOT ≤ 100 ms | Histogram `vllm:request_time_per_output_token_seconds`, bucket `le="0.1"` | Dashboard |
| Request đạt SLO | TTFT và TPOT đều đạt; không lỗi, không timeout, stream không bị cắt | Log của máy tạo tải | Nghiệm thu (chương 5) |
<!-- nguồn: docs/chi-tiet/00-thong-so.md §6 (TTFT ≤ 2,5 s, TPOT ≤ 100 ms, request đạt SLO); docs/chi-tiet/04-van-hanh.md §2.1 (TPOT = request_time_per_output_token_seconds, sửa 21/11); common/observability/rules/slo.yaml (le="2.5"); common/observability/dashboards/slo-cost.json (TPOT le="0.1"); common/observability/alerts/llm.yaml (LLMSLOBurnFast, LLMErrorRateHigh) -->

Ngưỡng của mỗi SLI phải trùng một biên bucket có thật của histogram trong bản vLLM đã ghim [@vllm-metrics]. Nếu ghi `le="2"` mà bản đó không có biên này, truy vấn trả về rỗng và cảnh báo im lặng mà không báo lỗi. Nhóm đã kiểm hai biên 2,5 s và 0,1 s trên `/metrics` của vLLM v0.31.0. SLI được tính sẵn bằng recording rule trên cửa sổ 1, 5 và 30 phút. Cảnh báo và dashboard đọc chung các chuỗi này nên hai nơi cho cùng một số.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §2.1 (điểm lưu ý thứ nhất: ngưỡng trùng biên bucket); docs/adr/005-sua-thiet-ke-sau-review.md T3; docs/chi-tiet/00-thong-so.md §6 (đã kiểm 23/10: v0.31.0 có le="2.5"); docs/nhat-ky/lam-viec/trinh/tuan-05.md mục 07/11 TR3 (TPOT có bucket 0,1); common/observability/rules/slo.yaml (rate1m, rate5m, rate30m và error_ratio:rate5m) -->

Nghiệm thu dùng log của máy tạo tải, vì SLI phía server có ba điểm mù. Histogram TTFT chỉ ghi request đã có token đầu, nên bỏ sót request hết thời gian chờ khi còn trong hàng đợi. Request bị cắt giữa stream vẫn mang mã 200, vì header đã gửi đi. Trong các lượt đánh giá, máy tạo tải gọi thẳng Service của vLLM nên Traefik không thấy lỗi của các lượt này. Cách đối chiếu mỗi page với log của máy tạo tải nằm ở mục 3.6.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §2.1 (điểm lưu ý thứ hai, thứ ba); envs/cloud/experiments/matrix-v2.yaml (target.service_url http://vllm.llm-serving.svc:8000); docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 16/11 TR7 (llm:error_ratio:rate5m rỗng khi gọi thẳng Service); docs/chi-tiet/00-thong-so.md §4 (N7 đối chiếu với log client) -->

Ba dashboard chia theo câu hỏi mà người xem cần trả lời. Dashboard *Serving và GPU* cho biết hàng đợi và KV cache của từng pod cùng trạng thái từng GPU. Dashboard *Autoscaling* đặt số replica mà HPA muốn cạnh số replica đang có. Dashboard *SLO và chi phí* vẽ SLI, burn rate, ngân sách lỗi còn lại và GPU-giờ trên khoảng thời gian đang chọn, để xem lại được từng lượt đánh giá.
<!-- nguồn: docs/chi-tiet/00-thong-so.md §3 (F5: 3 dashboard); common/observability/dashboards/README.md; tiêu đề panel trong common/observability/dashboards/serving-gpu.json ("Request đang chờ", "KV-cache đang dùng", "GPU (nvidia_gpu_exporter, mỗi đường một GPU)"), autoscaling.json ("Số replica: HPA muốn và thực tế"), slo-cost.json ("Burn rate TTFT", "Ngân sách lỗi TTFT còn lại", "GPU-giờ") -->

### 3.5.2. Cảnh báo theo burn rate

Page về chất lượng phục vụ dựa trên burn rate trên hai cửa sổ (mục 2.5), không dựa trên ngưỡng p95 của TTFT. Với SLO 99,9%, SRE Workbook [@sre-workbook] đề xuất page ở burn rate 14,4 trên cả cửa sổ 1 giờ và 5 phút. Nhóm rút hai cửa sổ còn 5 phút và 1 phút, vì mỗi lượt đánh giá chỉ dài 12–24 phút. Với cửa sổ 1 giờ, cảnh báo cần ít nhất 12 phút mới kêu (ước tính), quá giới hạn phát hiện 5 phút ở mục 3.1.
<!-- nguồn: docs/chi-tiet/02-kien-thuc-nen.md §5.2; docs/chi-tiet/04-van-hanh.md §2.2 (lượt dài 12–24 phút, cửa sổ rút ngắn), §3.3 (14,4; 1 giờ và 5 phút); common/observability/alerts/llm.yaml (comment vai trò hai cửa sổ); docs/chi-tiet/00-thong-so.md §4 (N7: ≤ 5 phút); 12 phút = 3600 · 0,2 / 1, cùng cách tính ở đoạn sau -->

`LLMSLOBurnFast` kêu khi burn rate vượt 4 trên cả hai cửa sổ trong 1 phút liên tục (`for: 1m`). Với SLO 95%, mức này ứng với 20% request có TTFT vượt 2,5 s. Mốc 20% trùng mốc định nghĩa page giả ở mục 3.6, nên cảnh báo và cách chấm cảnh báo dùng cùng một ngưỡng. Thời gian từ lúc vi phạm tới lúc có tin nhắn ước lượng được nếu giả sử tốc độ request không đổi và trước đó đã có 5 phút traffic tốt. Khi tỷ lệ request xấu nhảy từ 0 lên $x$, tỷ lệ trên cửa sổ 5 phút vượt ngưỡng $\theta = 0{,}2$ sau $300\theta / x$ giây. Cộng 60 s của `for` và 30 s Alertmanager chờ gom nhóm (mục 3.5.3), tin nhắn tới sau khoảng
<!-- nguồn: common/observability/alerts/llm.yaml (LLMSLOBurnFast: rate5m > 4 * 0.05 and rate1m > 4 * 0.05, for 1m, severity page); docs/chi-tiet/00-thong-so.md §4 (N7: page giả < 20%), §6 (SLO 95%); docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 16/11 "công cụ đo LT8" (dự đoán θ·300/x + 60 s); common/platform/alertmanager-values.yaml (group_wait 30s) -->

$$t_{\text{báo}} \approx \frac{300\,\theta}{x} + 60 + 30 \quad \text{(giây)}.$$

Với $x$ từ 50% tới 100%, $t_{\text{báo}}$ khoảng 2,5–3,5 phút (ước tính), chưa tính trễ scrape 5 s và chu kỳ tính rule 15 s. Vi phạm càng nhẹ thì ngân sách bị tiêu càng chậm, nên khi $x$ chỉ nhỉnh hơn 20% thì $t_{\text{báo}}$ có thể vượt 5 phút. Sau khi hồi phục, cửa sổ 1 phút xuống dưới ngưỡng sau $60(1 - \theta / x)$ giây, nên cảnh báo tắt trong vòng một phút. Chương 5 so dự đoán này (LT8) với số đo.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.3 (ước tính 3–4 phút); docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 16/11 "công cụ đo LT8" (hết cảnh báo 60·(1 − θ/x)); common/serving/podmonitor.yaml (scrape 5s); common/platform/kube-prometheus-stack-values.yaml (evaluationInterval 15s); docs/nhat-ky/van-hanh.md mục LT8 "Hệ quả cho V2 (VH6)" (x gần 0,2 thì có thể vượt 5 phút). 2,5–3,5 phút tính từ công thức (x = 1: 150 s; x = 0,5: 210 s), không phải số đo -->

### 3.5.3. Danh sách cảnh báo và định tuyến

Mỗi cảnh báo phải dẫn tới một việc người trực cần làm, nếu không thì sửa hoặc bỏ. Page dành cho lúc người dùng đang bị ảnh hưởng và cần người trực ngay. Ticket dành cho sự cố chờ được tới giờ làm việc. Mỗi quy tắc có một runbook và một unit test chạy trong CI (Bảng 3.5b).
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.1 (nguyên tắc 1, 2, 4, 5); CONTRIBUTING.md §4 (promtool test rules trong CI); common/observability/alerts/tests/llm-test.yaml; docs/runbooks/ (7 file) -->

**Bảng 3.5b.** Bảy quy tắc cảnh báo

| Cảnh báo | Điều kiện (rút gọn) | `for` | Mức | Lý do của điều kiện |
|---|---|---|---|---|
| `LLMSLOBurnFast` | Hơn 20% request có TTFT > 2,5 s, trên cả cửa sổ 5 phút và 1 phút | 1 phút | page | Người dùng phải chờ lâu (mục 3.5.2) |
| `LLMErrorRateHigh` | Tỷ lệ 5xx ≥ 1% trong 5 phút | 1 phút | page | Request bị từ chối; ngưỡng bằng ngân sách lỗi của SLO tỷ lệ lỗi |
| `LLMAtMaxReplicas` | Số replica bằng mức tối đa **và** hàng đợi > 0 | 15 phút | ticket | Autoscaling hết dư địa; chạy tối đa mà vẫn kịp thì chưa phải vấn đề |
| `LLMPodPending` | Pod vLLM ở trạng thái Pending | 10 phút | ticket | Thường do hết GPU |
| `LLMPodNotReady` | Pod vLLM đang Running nhưng chưa Ready | 15 phút | page | Lâu hơn cold start tối đa |
| `LLMPodCrashLooping` | Có `CrashLoopBackOff` trong 5 phút gần nhất | 5 phút | page | OOM, sai tham số, lỗi CUDA |
| `KedaScalerErrors` | ScaledObject có `Fallback=True` hoặc `Ready` khác True, trừ khi `Paused` | 1 phút | page | Autoscaling mất tín hiệu, giữ số replica cố định |
<!-- nguồn: common/observability/alerts/llm.yaml (7 rule: expr, for, severity, comment lý do từng rule); docs/chi-tiet/04-van-hanh.md §3.2; docs/chi-tiet/00-thong-so.md §6 (SLO tỷ lệ lỗi 99%, ngân sách 1%) -->

Bảy quy tắc ứng với sáu cảnh báo bắt buộc ở mục 3.1, vì trường hợp pod không khởi động được tách thành hai quy tắc. Hai cảnh báo đầu là triệu chứng người dùng thấy, năm cảnh báo sau chỉ ra nguyên nhân nằm ở pod hay ở autoscaling. Quy tắc lỗi 5xx có một điểm yếu đã biết. Một đợt vài lỗi 503 ngắn vẫn làm nó page, vì đợt lỗi nằm trong cửa sổ 5 phút lâu hơn 1 phút của `for` (mục 6.2).
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.1 (nguyên tắc 3: triệu chứng trước, nguyên nhân sau), §3.2 (6 cảnh báo = 7 quy tắc, 7 runbook); common/observability/alerts/llm.yaml (LLMErrorRateHigh: comment "for: 1m KHÔNG lọc được một đợt lỗi ngắn"); docs/nhat-ky/lam-viec/trinh/tuan-07.md mục 18/11 (thử bằng promtool: 1 req/s, đợt 5 lỗi 503 vẫn page) -->

Alertmanager định tuyến cảnh báo theo nhãn mức độ [@alertmanager-config]. Page tới Telegram, nhắc lại mỗi giờ nếu chưa hết và báo cả lúc đã hết. Ticket và cảnh báo critical có sẵn của chart chỉ báo một lần trong một phiên đo. Các mức warning và info của chart không được gửi đi. Chart có sẵn 134 cảnh báo, 100 ở hai mức này, và nhiều cái trùng ý với cảnh báo của nhóm, như `KubeHpaMaxedOut` với `LLMAtMaxReplicas`. Cảnh báo cùng tên gom thành một tin, có nhãn môi trường và link runbook.
<!-- nguồn: common/platform/alertmanager-values.yaml (route: Watchdog và gốc "null"; page repeat_interval 1h, send_resolved true; ticket|critical repeat_interval 24h, send_resolved false, comment "24 h dài hơn cả một phiên V2"; comment 134 cảnh báo, 100 warning/info, helm template chart 92.1.1 ngày 15/11; group_by [alertname]; template có link Runbook); envs/{home,cloud,sim}/platform/kube-prometheus-stack-values.yaml (externalLabels env); docs/chi-tiet/04-van-hanh.md §3.4 -->

### 3.5.4. Xử lý sự cố và vai trò người trực

Hệ thống tự xử lý các sự cố lặp lại, còn người trực quyết định những việc cần phán đoán. Khi tiến trình vLLM chết, kubelet khởi động lại container. Khi một pod bị xoá, ReplicaSet tạo pod mới. Khi KEDA không truy vấn được Prometheus quá 3 lần liên tiếp, KEDA chuyển sang chế độ fallback và giữ số replica ở mức tối đa [@keda-scaledobject-spec] (mục 3.3). Người trực vào cuộc khi có page, làm theo runbook, và quyết định các việc như rollback một bản cập nhật, chuyển pod khỏi một GPU lỗi hay đề xuất thêm GPU.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §6 (bảng "Sự cố và tự phục hồi": nền tảng tự xử lý và người trực làm gì); common/autoscaling/a2/scaledobject-a2.yaml (fallback failureThreshold 3, replicas 4 = max); docs/runbooks/LLMSLOBurnFast.md, LLMAtMaxReplicas.md (đề xuất thêm GPU) -->

Mỗi runbook dài khoảng nửa trang và theo một khung chung. Runbook nói cảnh báo nghĩa là gì, người dùng đang thấy gì, cần xem gì trong 5 phút đầu, và xử lý từng nguyên nhân ra sao. Phần cuối nói khi nào gọi thêm người và ghi lại gì sau sự cố. Ví dụ, runbook của `LLMSLOBurnFast` (Phụ lục C) bảo người trực xem trước số replica HPA muốn so với số đang có, rồi xem hàng đợi ở từng pod. Nếu pod mới đang cold start thì chỉ theo dõi, còn nếu cảnh báo kêu ngay sau một bản cập nhật thì rollback. Sau 15 phút chưa rõ nguyên nhân thì gọi người thứ hai.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §4.1 (mẫu: Ý nghĩa, Ảnh hưởng, Chẩn đoán nhanh ≤ 5 phút, Xử lý, Leo thang, Sau sự cố), §4.2; docs/runbooks/ (7 file, 29–53 dòng); docs/runbooks/LLMSLOBurnFast.md (chẩn đoán nhanh, bảng xử lý, leo thang sau 15 phút) -->

Mọi thay đổi cấu hình để xử lý sự cố đều đi qua Git, kể cả rollback bằng `git revert`, nên lần sửa nào cũng có lịch sử và đảo ngược được. Thao tác trực tiếp trên cluster chỉ dùng để chẩn đoán, hoặc cho việc không đổi cấu hình như xoá một pod chậm bất thường. Sau sự cố, người trực ghi vào nhật ký vận hành và bổ sung runbook nếu thiếu bước.
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §1 (chú thích Hình 7: mọi thay đổi để xử lý đều đi qua Git), §5.4 (rollback bằng git revert); docs/chi-tiet/00-thong-so.md §3 (F3: không thao tác tay trên cluster); docs/runbooks/LLMSLOBurnFast.md (xoá pod chậm; mục "Sau sự cố") -->

Prometheus vừa thu metric vừa tính cảnh báo, nên khi Prometheus sập thì mọi cảnh báo cùng im lặng. Nhóm chưa nối cảnh báo `Watchdog` của chart, vốn kêu liên tục, tới một dịch vụ bên ngoài báo động khi mất tín hiệu, nên mất Prometheus chưa được báo tự động (mục 6.2). Phía người dùng vẫn có fallback của KEDA giữ số replica ở mức tối đa. Nếu Prometheus còn chạy mà KEDA không tới được, `KedaScalerErrors` page sau 1 phút. Khi mất metric nguồn, KEDA coi kết quả rỗng là 0 và không bật fallback, nên mỗi lượt đánh giá kiểm riêng tín hiệu có liên tục không (mục 3.6).
<!-- nguồn: docs/chi-tiet/04-van-hanh.md §3.5; common/platform/alertmanager-values.yaml (Watchdog → "null"); common/observability/alerts/llm.yaml (KedaScalerErrors for 1m; comment "Prometheus sập thì rule không chạy"); docs/chi-tiet/03-kien-truc-autoscaling.md §13.4 (ignoreNullValues; lượt invalid khi tín hiệu mất mẫu > 15 s); docs/adr/005-sua-thiet-ke-sau-review.md T6 -->
