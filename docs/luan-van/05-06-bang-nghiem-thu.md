<!-- Mục đích: mục 5.6, bảng nghiệm thu F1–F7, N1–N8 và khuyến nghị cấu hình. Người viết: Trình. Nháp do agent soạn ngày 21/11/2026 từ gói dữ liệu V2 (runs/v2-vm/), nhật ký và docs/chi-tiet/00-thong-so.md; một agent khác đối chiếu từng số; Trình chưa đọc lại. -->
<!-- Số bảng tạm theo mục (Bảng 5.6a, 5.6b) vì các mục 5.1–5.5 chưa có; đánh lại khi ghép chương. -->

## 5.6. Bảng nghiệm thu và khuyến nghị cấu hình

Mục này đối chiếu kết quả của các mục 5.2–5.5 với các yêu cầu và chỉ tiêu đã đặt ra ở chương 3, rồi rút ra khuyến nghị chọn cấu hình autoscaling. Mỗi chỉ tiêu được ghi giá trị đo, ngưỡng và kết luận. Chỉ tiêu nào chưa đạt hoặc chưa đo đều được nêu rõ, kèm lý do.

Trừ khi ghi khác, số đo lấy từ phiên đo V2 (mục 5.1): VM thuê 4 × RTX 4060 Ti 16 GB, model 3B, vLLM v0.31.0, N = 4, năng lực một replica C = 3,5 req/s, threshold của A2 là 37. Mỗi ô ma trận có 1–3 lượt, nên giá trị được ghi cho từng lượt.

Cột "Kết luận" dùng năm mức:
- **Đạt:** số đo thoả ngưỡng.
- **Đạt một phần:** phần chính đã đo và thoả ngưỡng, nhưng một phần của cách kiểm chứng chưa làm; phần còn thiếu ghi ở cột "Ghi chú".
- **Không đạt:** số đo không thoả ngưỡng.
- **Báo cáo:** chỉ tiêu chỉ yêu cầu báo cáo số đo, không có ngưỡng đạt.
- **Chưa đo:** chưa có số đo.

### 5.6.1. Chỉ tiêu nghiệm thu N1–N8

**Bảng 5.6a.** Nghiệm thu các chỉ tiêu N1–N8 (phiên đo V2)

| Chỉ tiêu | Mức | Ngưỡng | Kết quả đo | Kết luận | Ghi chú |
|---|---|---|---|---|---|
| N1. Chất lượng phục vụ | Must | SLO attainment của A2 ≥ 95% ở KB1 (pha `steady`) và KB3 (pha `sustain`) | KB1: 100%; 100% (2 lượt). KB3: 100%; 100% (2 lượt) | Đạt | KB2 chỉ báo cáo: 79,8%; 79,4%; 80,7% (3 lượt, pha `pre`, `spike` và `drop`) |
| N2a. Tốc độ phản ứng | Must | Ở KB2, từ lúc tải tăng tới khi replica mới đầu tiên Ready ≤ 2 phút | 81,4; 81,5; 79,7 s (3 lượt) | Đạt | Gồm phát hiện 14,7–16,4 s và tạo pod tới Ready 65–66 s (mức L2, image có sẵn trên node) |
| N2b. Hồi phục | Should | Báo cáo thời gian hồi phục SLO ở KB2; mức dự kiến ≤ 5 phút (tạm) | 426; 430; 409 s, tức 6,8–7,2 phút (3 lượt) | Báo cáo | Dài hơn mức dự kiến. Hàng đợi dồn trong pod có sẵn không chuyển sang pod mới (mục 5.3) |
| N3. Hiệu quả GPU | Should | Ở KB1, A2 dùng ≤ 50% GPU-giờ của S4, SLO attainment kém S4 không quá 5 điểm phần trăm | GPU-giờ bằng 25% của S4 (0,20 so với 0,80 GPU-giờ; 2 lượt như nhau); SLO attainment chênh 0 điểm phần trăm | Đạt | KB2: 71,8–75,2% GPU-giờ của S4, SLO attainment kém 19,3–20,6 điểm phần trăm. KB3: 91,7–92,3%, chênh 0 điểm |
| N4. An toàn khi thay đổi | Must | 0 request lỗi do scale-down và do rolling update, gồm ca chỉ có 1 replica | Scale-down: 0 lỗi trong pha `drop` của 3 lượt A2 × KB2 (1.147; 1.166; 1.245 request). Rolling update: 0 lỗi khi đi từ 1 replica (2.077 request) và khi cả 4 GPU đều có pod (4.229 request) | Đạt | Chưa chạy ở máy nhà (VH1, VH2) |
| N5. Cold start | Should | Cold start mức L2 ≤ 50% so với L0 | L2: 77,7 s (3 lượt: 76; 76; 81 s). L0: 305,5 s (2 lượt: 311; 300 s). Tỷ lệ 25,4% | Đạt | L0 đo từ 0 lên 1 pod, L2 đo từ 1 lên 2 pod (mục 5.4) |
| N6. Tự phục hồi và khôi phục | Must | Pod hỏng được thay tự động; mất Prometheus thì KEDA chuyển sang fallback trong ≤ 30 s; dựng lại từ VM trắng ≤ 30 phút | Xoá pod: pod thay thế Ready sau 67,4 s, 0 lỗi / 1.351 request. Kill tiến trình: container khởi động lại, Ready sau 67,4 s. Fallback lên 4 replica sau 16,8 s, 0 lỗi / 1.263 request. Dựng lại: 8 phút 22 giây (1 lần) | Đạt | Ca kill có 129 lỗi / 1.041 request, nhiều khả năng vì lúc đó chỉ có 1 pod (mục 5.5). Thời gian dựng lại bấm bằng tay |
| N7. Quan sát được | Should | Cảnh báo SLO kích hoạt ≤ 5 phút sau khi SLO bị vi phạm thật (S1 × KB3); không có page giả khi A2 chạy KB1, KB3 | S1 × KB3: 104,5 s (1 lượt). Page giả: 0 trong 17 lượt | Đạt | A2 × KB3 có 1 page mỗi lượt, trong pha `ramp`; lúc page, tỷ lệ request xấu theo log client là 27% và 38%, nên không phải page giả |
| N8. Tái lập và chi phí | Should | Mọi phiên bản được ghim; người thứ hai dựng lại cluster theo README trong < 1 giờ; tiền thuê GPU ≤ 150 USD | Phiên bản: đã ghim (vLLM theo digest, k3s, chart Helm, simulator). Dựng lại bởi người thứ hai: chưa đo. Chi phí: chưa có tổng | Chưa đo | Giá thuê máy V2 là 1,5 USD/giờ (ước tính, theo trang Vast.ai) |

<!-- nguồn: N1–N3: analysis/figures/v2-dg2/runs.csv (slo_attainment, scored_phases, detect_s, create_to_ready_s, react_s, recovery_s, gpu_h, gpu_vs_baseline, slo_delta_vs_baseline_pp); nhật ký Quang tuần 07 mục 18/11 (bảng 11 ô), 19/11 (nguyên nhân A2 × KB2: hàng đợi 416–428 request ở pod có sẵn) -->
<!-- nguồn: N4: analysis/figures/v2-dg2/phases.csv (pha drop của A2-KB2-1/2/3: n_error = 0, replicas_ready_mean 2,8; 2,5; 2,6), runs.csv (scale_downs = 3 mỗi lượt; n_error toàn lượt = số lỗi của pha spike); runs/v2-vm/ops-vh2a-*/summary.json (replicas_before 1, rollout_s 141,4), ops-vh2b-*/summary.json (rollout_s 371,6); VH 16/11 ("Chưa làm: VH1–VH4 trên GPU nhà") -->
<!-- nguồn: N5: runs/v2-vm/dg3-v2-4060ti/{L2-1,L2-2,L2-3,L0-1,L0-2}/summary.txt (trigger_to_ready_s); nhật ký Quang tuần 07 mục 18/11 (lý do L0 đo 0 → 1) -->
<!-- nguồn: N6: runs/v2-vm/ops-vh3-delete-*/summary.json (replace_s 67,38, ready_before 2), ops-vh3-kill-*/summary.json (recover_s 67,45, 129 lỗi), ops-vh4-*/summary.json (fallback_s 16,80, replicas_before 1, max_replicas 4); nhật ký Quang tuần 07 mục 18/11 (8 phút 22 giây từ đầu bootstrap tới vLLM Ready, bấm tay) -->
<!-- nguồn: N7: analysis/figures/v2-dg2/runs.csv (time_to_alert_s, false_pages), alerts.csv (client_bad_ratio 0,272 và 0,378 ở A2-KB3; đợt kêu ở −176 s của A2-KB3-2 có firing_at_start = True, còn từ lượt trước, không tính) -->
<!-- nguồn: N8: runs/v2-vm/dg3-v2-4060ti/*/summary.txt (vllm/vllm-openai:v0.31.0@sha256:c1c9…); ansible/inventory/group_vars/all.yaml (k3s v1.36.5+k3s1); envs/cloud/provision/install-platform.sh (nvidia-device-plugin 0.20.1, kube-prometheus-stack 92.1.1, KEDA 2.21.0); nhật ký Quang tuần 07 mục 18/11 (1,5 USD/giờ); nguon-tu-lieu.md §4 (chi phí thực tế chưa có) -->

Cả bốn chỉ tiêu mức Must về số đo (N1, N2a, N4, N6) đều đạt trong phiên đo V2. Kết quả yếu nhất nằm ở kịch bản tải tăng đột ngột KB2. Ở đó A2 có replica mới Ready sau 79,7–81,5 s, tức đạt N2a, với khoảng dư nhỏ nhất là 38,5 s. Tuy vậy, SLO attainment chỉ còn khoảng 80%, và phải mất 409–430 s SLO mới hồi phục. Nguyên nhân là hàng đợi dồn vào pod có sẵn trong lúc chờ cold start, và sau khi các pod mới đã Ready, request mới vẫn được chia đều cho cả pod đó (mục 5.3). Chỉ tiêu N8 chưa kết luận được, vì thiếu hai phần: chưa có người thứ hai dựng lại cluster theo README, và chưa có tổng chi phí thuê thực tế.

### 5.6.2. Yêu cầu chức năng F1–F7

**Bảng 5.6b.** Nghiệm thu các yêu cầu chức năng F1–F7

| Yêu cầu | Mức | Cách kiểm chứng | Kết quả | Kết luận | Ghi chú |
|---|---|---|---|---|---|
| F1. Phục vụ model mở 3–8B qua API tương thích OpenAI, có streaming | Must | Gọi API có streaming; chạy được ĐG1–ĐG3 | Qwen2.5-3B-Instruct trên vLLM v0.31.0, gọi `/v1/chat/completions` có streaming. ĐG1 đủ 5 mức tải, ĐG2 17/17 lượt hợp lệ, ĐG3 5 lượt | Đạt | Máy tạo tải đo TTFT và TPOT từ chính luồng streaming |
| F2. Tự điều chỉnh số replica trong [1, N] theo tải | Must | Bài kiểm thử T1–T7; ĐG2 | A2 giữ 1 replica ở KB1, lên 4 replica ở KB2 và KB3, và giảm lại trong pha `drop` của KB2. T1–T5 chạy tự động trên simulator | Đạt | T6 (đổi cấu hình, chỉ còn một HPA) mới kiểm trên simulator, chưa chạy ở máy nhà; T7 (A4, mức Could) chưa chạy |
| F3. Triển khai, cập nhật và rollback qua Git | Must | VH2: cập nhật và rollback bằng `git revert` | Argo CD quản lý cluster ở máy nhà theo mô hình App-of-Apps (7 Application ở trạng thái Synced và Healthy). Cập nhật qua Git rồi rollback bằng `git revert`: chưa chạy | Đạt một phần | VM thuê không dùng Argo CD; rolling update trên VM thuê được kích hoạt trực tiếp, không qua Git |
| F4. Dựng toàn bộ từ máy trắng bằng vài lệnh `make` | Must | VH5 | VM thuê: `make attach`, `make probe`, `make bootstrap`, `make cloud-platform`, mất 8 phút 22 giây từ đầu bootstrap tới vLLM Ready | Đạt | Bấm giờ bằng tay, 1 lần. Máy nhà dựng lại được bằng Ansible, nhưng phần sau k3s còn bước tay |
| F5. Ba dashboard | Must | Kiểm tra trong mọi lượt; ảnh chụp đưa vào luận văn | 3 dashboard (Serving và GPU 20 panel; Autoscaling 9 panel; SLO và chi phí 16 panel), được cài cùng nền tảng trên VM thuê. Mọi truy vấn chạy được trên simulator; CI kiểm cú pháp và PromQL của dashboard | Đạt một phần | Chưa có ảnh chụp dashboard trên GPU thật |
| F6. Sáu cảnh báo gửi tới Telegram, mỗi cảnh báo có runbook | Must | VH6 | 7 quy tắc (6 cảnh báo), mỗi quy tắc có runbook và unit test, CI kiểm cả hai. Trong V2, `LLMSLOBurnFast` kêu đúng ở 7 đợt tính được, 0 page giả. Đường Alertmanager → Telegram đã kiểm với API Telegram giả trên simulator | Đạt một phần | Chưa gửi tới Telegram thật. Trong V2, Alertmanager báo lỗi gửi tới Telegram suốt 17 lượt, và không có bằng chứng tin nào tới nơi; nhiều khả năng do thiếu Secret Telegram, chưa kiểm trực tiếp được (mục 5.5.6) |
| F7. Bảo vệ tối thiểu | Should | Checklist bảo mật | API key: khoá ngẫu nhiên 24 byte, lưu trong Secret và đưa vào vLLM bằng biến môi trường. VM thuê chỉ truy cập qua SSH tunnel | Chưa đo | Checklist chưa chạy. Phạm vi đã thu hẹp còn API key và mạng riêng (mục 3.x) |

<!-- nguồn: F1: envs/cloud/serving/patch-vllm.yaml (--model=Qwen/Qwen2.5-3B-Instruct); loadgen/sender.py (CHAT_PATH); nhật ký Quang tuần 07 mục 18/11 (ĐG1 5 lượt hợp lệ; ĐG2 17/17), 19/11 (ĐG3) -->
<!-- nguồn: F2: analysis/figures/v2-dg2/runs.csv (replicas_max, scale_ups, scale_downs); nhật ký Trình tuần 04 mục 01/11 (T1–T5 trên kind); nhật ký Trình tuần 05 mục 07/11 (cơ chế T6 trên kind); Kế hoạch mốc M2 (ghi chú 08/11: chưa có T6, T7) -->
<!-- nguồn: F3: VH 16/11 (7 app Synced/Healthy sau khi áp lại root-app); ADR-006 §3.1 (VM thuê dùng helm, không Argo CD); runs/v2-evidence/config/vh.py-pr46 (trigger_rollout: patch annotation) -->
<!-- nguồn: F4: nhật ký Quang tuần 07 mục 18/11 (bootstrap 5 phút 8 giây, cloud-platform 82 s, vLLM Ready 90 s; tổng 8 phút 22 giây); VH 06/11 (dựng lại máy nhà, còn bước tay) -->
<!-- nguồn: F5: nhật ký Trình tuần 05 mục 07/11 (TR3: 3 dashboard, số panel, kiểm truy vấn qua /api/ds/query trên kind, make dashboards-check); envs/cloud/provision/install-platform.sh (nạp 3 dashboard) -->
<!-- nguồn: F6: docs/chi-tiet/04-van-hanh.md §3.2; docs/runbooks/ (7 file); Makefile alerts-coverage; nhật ký Trình tuần 06 mục 15/11 (tg-mock; chưa thử Telegram thật); analysis/figures/v2-dg2/alerts.csv; GHI-CHU-CHO-TRINH §3 điểm 1 -->
<!-- nguồn: F7: envs/cloud/provision/install-platform.sh (openssl rand -hex 24); common/serving/deployment.yaml (VLLM_API_KEY); 00-thong-so.md §3 F7 (sửa 12/11); nguon-tu-lieu.md §4 (checklist bảo mật chưa làm) -->

F1, F2 và F4 đạt. Bốn yêu cầu còn lại mới đạt một phần hoặc chưa đo, và phần còn thiếu đều nằm ở khâu kiểm chứng chứ không nằm ở chức năng. F3 thiếu lần cập nhật rồi rollback qua Git. F5 thiếu ảnh chụp dashboard trên GPU thật. F6 thiếu bằng chứng tin cảnh báo tới được Telegram thật. Riêng F6, phần quyết định cảnh báo có kêu hay không đã được kiểm trong V2, dựa trên trạng thái cảnh báo của Prometheus. Phần chưa kiểm là khâu gửi tin đi.

### 5.6.3. Khuyến nghị cấu hình

Kết quả ĐG2 cho thấy nên chọn A2 thay cho A1 làm cấu hình autoscaling mặc định. A1 scale theo GPU utilization và lên 4 replica ngay ở KB1, khi tải chỉ bằng 0,5C, nên chỉ tiết kiệm 9,4–10,3% GPU-giờ so với S4. A2 giữ 1 replica ở cùng tải, dùng 25% GPU-giờ của S4 mà SLO attainment vẫn đạt 100%. Ở KB3, tải tăng dần, nên cả hai cấu hình đều kịp scale lên trước pha `sustain` và đạt 100% SLO attainment. Mức GPU-giờ của hai cấu hình ở KB3 gần nhau: A1 92,7%, A2 91,7–92,3% so với S4.

A2 có giới hạn ở tải tăng đột ngột (KB2). Ở kịch bản này, A1 đạt 100% SLO attainment, nhưng chỉ vì A1 đã ở 4 replica ngay lúc tải bắt đầu tăng. Vì vậy A1 dùng tới 95,1–95,4% GPU-giờ của S4, gần như cấu hình tĩnh. A2 tiết kiệm 24,8–28,2% GPU-giờ, đổi lại SLO attainment kém khoảng 20 điểm phần trăm. Với dịch vụ có tải tăng đột ngột, hai hướng dưới đây có thể giảm cái giá đó mà vẫn giữ được phần lớn mức tiết kiệm của A2 (đề xuất, chưa thực hiện; chương 6):
- Định tuyến request theo độ dài hàng đợi của từng pod, thay cho cách chia đều của Service.
- Giữ số replica tối thiểu cao hơn trong những khung giờ biết trước là có tải tăng đột ngột.

<!-- nguồn: analysis/figures/v2-dg2/runs.csv (replicas_at_rise = 4 ở A1-KB2-1/2; gpu_vs_baseline: A1-KB1 0,897 và 0,906; A1-KB2 0,954 và 0,951; A1-KB3 0,927; A2-KB3 0,917 và 0,923; A2-KB2 0,752, 0,718 và 0,722); LT6 (GPU utilization bão hoà ở tải thấp); nhật ký Quang tuần 05 (hướng phát triển: load shedding, router theo tải); nhật ký Quang tuần 07 mục 19/11 (Service chia đều) -->
