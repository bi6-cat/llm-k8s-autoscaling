<!-- Mục đích: mục 5.6, bảng nghiệm thu F1–F7, N1–N8 và khuyến nghị cấu hình. Người viết: Trình. Nháp ngày 21/11/2026 từ gói dữ liệu V2 (runs/v2-vm/), nhật ký và docs/chi-tiet/00-thong-so.md; 24/11 cắt về ngân sách 2 trang (D96): gộp hai bảng F, N thành một bảng 4 cột (F và N chung một bảng như Bảng 3.1 của mục 3.1, D95), bỏ cột Ngưỡng, Ghi chú và danh sách định nghĩa mức kết luận; Trình chưa đọc lại. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Thông điệp: (1) mọi yêu cầu và chỉ tiêu mức Must đạt hoặc đạt một phần trong phiên đo V2, điểm yếu nhất là tải tăng đột ngột; (2) phần còn thiếu nằm ở khâu kiểm chứng (vòng Git trên GPU thật, dashboard trên GPU thật, Telegram thật, chi phí của N8), không nằm ở chức năng; (3) khuyến nghị A2 làm cấu hình mặc định, đánh đổi là SLO attainment khi tải tăng đột ngột. -->
<!-- Soát số: 27/11/2026 (dòng N2b sửa 28/11 theo ADR-003 G5, §5: người viết đối chiếu, chưa soát độc lập) · Soát văn phong: kiem_van 27/11 · Người viết đọc lại: chưa -->
<!-- Số bảng tạm theo mục (Bảng 5.6a) vì các mục 5.1–5.5 chưa có; đánh lại khi ghép chương. Bảng đầy đủ kèm cột Ghi chú và số từng lượt (bản nháp trước khi cắt, commit bb14810) dùng cho Phụ lục E. Ý đã cắt khi rút gọn 24/11: KB2 chỉ báo cáo SLO 79,4–80,7% (3 lượt); N2a gồm phát hiện 14,7–16,4 s và tạo pod tới Ready 65–66 s; N3 ở KB2: 71,8–75,2% GPU-giờ của S4, kém 19,3–20,6 điểm phần trăm, ở KB3: 91,7–92,3%, chênh 0 điểm; N4: 1.147–1.245 request trong pha giảm, rolling update 2.077 và 4.229 request; N6: xoá pod 0 lỗi / 1.351 request, fallback 0 lỗi / 1.263 request; N7: lúc A2 × KB3 page, tỷ lệ request xấu theo log client là 27% và 38%; F5: số panel 20, 9, 16; giá thuê V2 1,5 USD/giờ (ước tính); mọi số đo mới có trên VM thuê, các kịch bản vận hành ở máy nhà chưa chạy (đưa vào 5.7). -->
<!-- Còn thiếu so với Kế hoạch §11.1 và nguon-tu-lieu.md §2 (dòng 5.6): bảng kiểm chứng LT1–LT8 (dự đoán, số đo, độ lệch, giải thích). Mục hiện đo 1,95 trang khuôn B (ngân sách 2), nên khi thêm bảng LT thì hoặc đưa bảng vào Phụ lục E kèm một câu tóm tắt ở đây, hoặc lấy khoảng 0,5 trang từ mục khác của chương 5. -->

## 5.6. Bảng nghiệm thu và khuyến nghị cấu hình

Bảng nghiệm thu (Bảng 5.6a) đối chiếu kết quả của các mục 5.2–5.5 với các yêu cầu và chỉ tiêu đặt ra ở mục 3.1; từ đó rút ra khuyến nghị chọn cấu hình autoscaling. Số đo trên GPU lấy từ phiên đo V2 (mục 5.1), còn vòng cập nhật qua Git và lần dựng lại theo README được đo trên simulator (mục 5.5).

### 5.6.1. Nghiệm thu yêu cầu và chỉ tiêu

**Bảng 5.6a.** Nghiệm thu F1–F7 và N1–N8 (phiên đo V2 và simulator). Trong ngoặc là ngưỡng của Bảng 3.1; số từng lượt ở Phụ lục E. "Đạt một phần": phần chính đạt, một phần cách kiểm chứng chưa làm. "Báo cáo": chỉ yêu cầu báo cáo số đo.

| Yêu cầu, chỉ tiêu | Mức | Kết quả, phần còn thiếu | Kết luận |
|---|---|---|---|
| F1. API có streaming | Must | ĐG1–ĐG3 chạy qua API có streaming | Đạt |
| F2. Tự điều chỉnh replica | Must | A2 trong [1, 4]; T7 chưa chạy | Đạt một phần |
| F3. Triển khai qua Git | Must | Cập nhật, rollback qua Git trên simulator, 0 lỗi; trên GPU chỉ qua annotation | Đạt |
| F4. Dựng từ máy trắng | Must | 8 phút 22 giây (1 lần) | Đạt |
| F5. Ba dashboard | Must | Đủ 3 dashboard; chưa chụp trên GPU thật | Đạt một phần |
| F6. Cảnh báo tới Telegram | Must | Chưa gửi Telegram thật | Đạt một phần |
| F7. Bảo vệ tối thiểu | Should | API key, SSH tunnel; checklist chưa chạy | Chưa đo |
| N1. SLO attainment | Must | 100% ở KB1, KB3 (≥ 95%) | Đạt |
| N2a. Tốc độ phản ứng | Must | 79,7–81,5 s (≤ 2 phút) | Đạt |
| N2b. Hồi phục | Should | 409–430 s, vượt mức tham chiếu 5 phút | Báo cáo |
| N3. Hiệu quả GPU | Should | 25% GPU-giờ của S4; SLO chênh 0 điểm phần trăm | Đạt |
| N4. An toàn khi thay đổi | Must | 0 lỗi, kể cả lúc 1 replica | Đạt |
| N5. Cold start | Should | L2 bằng 25,3% L0 (≤ 50%) | Đạt |
| N6. Tự phục hồi | Must | Thay pod 67,4 s; fallback 16,8 s; dựng lại như F4 | Đạt |
| N7. Quan sát được | Should | 104 s (≤ 5 phút); 0 page giả | Đạt |
| N8. Tái lập, chi phí | Should | Dựng lại theo README 25 phút trên simulator; thiếu chi phí | Đạt một phần |

<!-- nguồn: F1: envs/cloud/serving/patch-vllm.yaml (--model=Qwen/Qwen2.5-3B-Instruct); loadgen/sender.py (CHAT_PATH); nhật ký Quang tuần 07 mục 18/11 (ĐG1 5 lượt hợp lệ; ĐG2 17/17), 19/11 (ĐG3) -->
<!-- nguồn: F2: analysis/figures/v2-dg2/runs.csv (replicas_max, scale_ups, scale_downs); nhật ký Trình tuần 04 mục 01/11 (T1–T5 trên kind); nhật ký Trình tuần 05 mục 07/11 (cơ chế T6 trên kind); Kế hoạch mốc M2 (ghi chú 08/11: chưa có T6, T7) -->
<!-- nguồn: F3: VH 16/11 (7 app Synced/Healthy sau khi áp lại root-app); ADR-006 §3.1 (VM thuê dùng helm, không Argo CD); runs/v2-evidence/config/vh.py-pr46 (trigger_rollout: patch annotation); ADR-007 D2 (PR #75: phần Git của VH2 kiểm trên kind); nhật ký Trình tuần 08 mục 25/11 trên nhánh feat/tr8-vh2-git-run (PR #78: 4 commit qua Argo CD, 615 request, 0 lỗi, TTFT 206 → 306 → 206 ms) -->
<!-- nguồn: F4: nhật ký Quang tuần 07 mục 18/11 (bootstrap 5 phút 8 giây, cloud-platform 82 s, vLLM Ready 90 s; tổng 8 phút 22 giây); VH 06/11 (dựng lại máy nhà, còn bước tay) -->
<!-- nguồn: F5: nhật ký Trình tuần 05 mục 07/11 (TR3: 3 dashboard, số panel, kiểm truy vấn qua /api/ds/query trên kind, make dashboards-check); envs/cloud/provision/install-platform.sh (nạp 3 dashboard) -->
<!-- nguồn: F6: docs/chi-tiet/04-van-hanh.md §3.2; docs/runbooks/ (7 file); Makefile alerts-coverage; nhật ký Trình tuần 06 mục 15/11 (tg-mock; chưa thử Telegram thật); analysis/figures/v2-dg2/alerts.csv (7 đợt LLMSLOBurnFast tính được); GHI-CHU-CHO-TRINH §3 điểm 1 -->
<!-- nguồn: F7: envs/cloud/provision/install-platform.sh (openssl rand -hex 24); common/serving/deployment.yaml (VLLM_API_KEY); 00-thong-so.md §3 F7 (sửa 12/11); nguon-tu-lieu.md §4 (checklist bảo mật chưa làm) -->
<!-- nguồn: N1–N3: analysis/figures/v2-dg2/runs.csv (slo_attainment, scored_phases, detect_s, create_to_ready_s, react_s, recovery_s, gpu_h, gpu_vs_baseline, slo_delta_vs_baseline_pp); nhật ký Quang tuần 07 mục 18/11 (bảng 11 ô), 19/11 (nguyên nhân A2 × KB2: hàng đợi 416–428 request ở pod có sẵn); docs/adr/003-ket-qua-dg1-va-gia-tri-chot.md G5 (N2b: mức tham chiếu 5 phút, chỉ báo cáo, không tính đạt hay trượt) và §5 (409–430 s vượt mức tham chiếu) -->
<!-- nguồn: N4: analysis/figures/v2-dg2/phases.csv (pha drop của A2-KB2-1/2/3: n_error = 0, replicas_ready_mean 2,8; 2,5; 2,6), runs.csv (scale_downs = 3 mỗi lượt; n_error toàn lượt = số lỗi của pha spike); runs/v2-vm/ops-vh2a-*/summary.json (replicas_before 1, rollout_s 141,4), ops-vh2b-*/summary.json (rollout_s 371,6); VH 16/11 ("Chưa làm: VH1–VH4 trên GPU nhà") -->
<!-- nguồn: N5: runs/v2-vm/dg3-v2-4060ti/{L2-1,L2-2,L2-3,L0-1,L0-2}/summary.txt (ready_seen_unix − trigger_unix, trung bình 77,4 / 305,7 s; theo trigger_to_ready_s nguyên giây là 25,4%; 05-04-cold-start.md); nhật ký Quang tuần 07 mục 18/11 (lý do L0 đo 0 → 1) -->
<!-- nguồn: N6: runs/v2-vm/ops-vh3-delete-*/summary.json (replace_s 67,38, ready_before 2), ops-vh3-kill-*/summary.json (recover_s 67,45, 129 lỗi / 1.041 request), ops-vh4-*/summary.json (fallback_s 16,80, replicas_before 1, max_replicas 4); nhật ký Quang tuần 07 mục 18/11 (8 phút 22 giây từ đầu bootstrap tới vLLM Ready, bấm tay) -->
<!-- nguồn: N7: analysis/figures/v2-dg2/runs.csv (time_to_alert_s, false_pages), alerts.csv (client_bad_ratio 0,272 và 0,378 ở A2-KB3; đợt kêu ở −176 s của A2-KB3-2 có firing_at_start = True, còn từ lượt trước, không tính) -->
<!-- nguồn: N8: runs/v2-vm/dg3-v2-4060ti/*/summary.txt (vllm/vllm-openai:v0.31.0@sha256:c1c9…); ansible/inventory/group_vars/all.yaml (k3s v1.36.5+k3s1); envs/cloud/provision/install-platform.sh (nvidia-device-plugin 0.20.1, kube-prometheus-stack 92.1.1, KEDA 2.21.0); nguon-tu-lieu.md §4 (chi phí thực tế chưa có); van-hanh.md mục 24/11 "N8" trên nhánh docs/tr8-n8-sim-rebuild (PR #76: 1.481 s từ sim-down tới hết sim-test, T1–T5 đạt); ADR-007 D4 -->

Theo Bảng 5.6a, mọi yêu cầu và chỉ tiêu mức Must đều đạt hoặc đạt một phần. Điểm yếu nhất là tải tăng đột ngột, kịch bản mà N1 chỉ yêu cầu báo cáo. Replica mới Ready sớm hơn ngưỡng 2 phút ít nhất 38,5 s, nhưng SLO attainment chỉ còn khoảng 80% và cần 409–430 s (3 lượt) mới hồi phục. Nguyên nhân là hàng đợi dồn vào pod có sẵn trong lúc chờ cold start (mục 5.3). Page trong pha tăng dần của A2 × KB3 không bị tính là page giả, vì lúc đó 27% và 38% request xấu theo log của máy tạo tải (2 lượt). Chỉ tiêu tự phục hồi đạt, nhưng ca dừng tiến trình vLLM có 129 lỗi trên 1.041 request, nhiều khả năng vì lúc đó chỉ có một pod (mục 5.5).

<!-- nguồn: analysis/figures/v2-dg2/runs.csv (react_s 79,7–81,5; slo_attainment A2-KB2 0,794–0,807; recovery_s 409–430); nhật ký Quang tuần 07 mục 19/11 (hàng đợi ở pod có sẵn, Service chia đều); runs/v2-vm/ops-vh3-kill-*/summary.json (129 lỗi / 1.041 request); alerts.csv (client_bad_ratio 0,272 và 0,378 ở A2-KB3) -->

Các phần còn thiếu đều nằm ở khâu kiểm chứng, không nằm ở chức năng. Bài kiểm thử T7 của F2 chưa chạy. Vòng cập nhật và rollback qua Git mới chạy trên simulator, chưa trọn vòng trên GPU thật. Nhóm cũng chưa chụp dashboard trên GPU thật và chưa gửi cảnh báo tới Telegram thật. Với F6, cảnh báo kêu đúng lúc đã được kiểm trong V2, còn khâu gửi tin thì Alertmanager báo lỗi suốt 17 lượt, nhiều khả năng do thiếu Secret Telegram (mục 5.5). Chỉ tiêu N8 mới đạt phần tái lập, với lần dựng lại theo README mất khoảng 25 phút trên simulator, còn tổng chi phí thuê chưa có.

<!-- nguồn: analysis/figures/v2-dg2/alerts.csv; GHI-CHU-CHO-TRINH §3 điểm 1 (Alertmanager báo lỗi gửi Telegram suốt 17 lượt); nguon-tu-lieu.md §4 (chi phí thực tế chưa có) -->

### 5.6.2. Khuyến nghị cấu hình

Nhóm khuyến nghị A2 làm cấu hình autoscaling mặc định, thay cho A1 (mục 5.3). Scale theo GPU utilization, A1 lên 4 replica ngay khi tải chỉ bằng 0,5 C, nên chỉ tiết kiệm 9,4–10,3% GPU-giờ so với cấu hình tĩnh 4 replica (2 lượt). Ở cùng tải, A2 giữ 1 replica và dùng 25% GPU-giờ của cấu hình tĩnh, SLO attainment vẫn đạt 100%. Ở kịch bản tải cao kéo dài, trong pha duy trì được chấm, hai cấu hình cùng đạt 100% và dùng 91,7–92,7% GPU-giờ của cấu hình tĩnh (3 lượt).

<!-- nguồn: analysis/figures/v2-dg2/runs.csv (gpu_vs_baseline: A1-KB1 0,897 và 0,906; A2-KB1 0,25; A1-KB3 0,927; A2-KB3 0,917 và 0,923; slo_attainment = 1 ở KB1, KB3); LT6 (GPU utilization bão hoà ở tải thấp) -->

Đổi lại, A2 kém hơn khi tải tăng đột ngột. A1 giữ được 100% SLO attainment chỉ vì đã ở 4 replica từ trước, nên dùng tới 95,1–95,4% GPU-giờ của cấu hình tĩnh (2 lượt). A2 tiết kiệm 24,8–28,2% GPU-giờ (3 lượt) nhưng SLO attainment kém khoảng 20 điểm phần trăm. Hai hướng có thể giảm cái giá này (đề xuất, chưa thực hiện; chương 6). Một là định tuyến request theo độ dài hàng đợi của từng pod, thay cho cách chia đều của Service. Hai là nâng số replica tối thiểu trong những khung giờ biết trước có tải tăng đột ngột.

<!-- nguồn: analysis/figures/v2-dg2/runs.csv (replicas_at_rise = 4 ở A1-KB2-1/2; gpu_vs_baseline: A1-KB2 0,954 và 0,951; A2-KB2 0,752, 0,718 và 0,722); nhật ký Quang tuần 05 (hướng phát triển: load shedding, router theo tải); nhật ký Quang tuần 07 mục 19/11 (Service chia đều) -->
