# ADR-006: Chốt cloud, model, kịch bản tải và các điểm kỹ thuật trước phiên V2

- **Trạng thái:** Đã chấp nhận ngày 10/11/2026. Gom lại các quyết định đã đưa ra trong khoảng 04–09/11/2026 (họp nhóm 04/11, rà tiến độ 08/11, phiên V0+V1 08/11, sửa A1 09/11) mà trước đó chỉ nằm rải rác trong [Thông số](../chi-tiet/00-thong-so.md) ("Sửa ngày 08/11"), [ADR-004 §7](004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md#7-cập-nhật-sau-ngày-08102026) và nhật ký.
- **Người quyết định:** Nhóm (Quang và Trình). Việc nào Trình chưa review thì ghi rõ.
- **Thay thế một phần:** [ADR-004](004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md) K4, K5, K6, K9 và [ADR-005](005-sua-thiet-ke-sau-review.md) T1 (phần "cần kiểm chứng"); chi tiết ở §4.
- **Liên quan:** [Thông số §2, §7, §8, §9, §10, §11](../chi-tiet/00-thong-so.md), [Môi trường §3, §6](../chi-tiet/05-moi-truong-danh-gia.md), [Kế hoạch §1.1](../chi-tiet/06-ke-hoach-quan-ly.md#11-điều-chỉnh-ngày-04112026), [nhật ký vận hành](../nhat-ky/van-hanh.md) các mục 06/11 và 08/11, [nhật ký Quang tuần 05](../nhat-ky/lam-viec/quang/tuan-05.md) (08/11) và [tuần 06](../nhat-ky/lam-viec/quang/tuan-06.md) (09/11).

ADR-003 vẫn được dành cho **kết quả đo năng lực và các giá trị chốt** (C, B\*, threshold, ngưỡng N2b, N3 theo N) trong phiên V2. ADR này chỉ chốt những gì phải chốt **trước** V2.

## 1. Bối cảnh

ADR-004 (08/10) giả định thuê 4 × RTX 4090 chế độ VM trên Vast.ai, dự phòng GCP, model 7B. Từ 05/11 tới 09/11 nhóm biết thêm:

| Ngày | Sự kiện |
|---|---|
| 04/11 | M1 đạt 2/7, M2 đạt 0/8: V2 dời sang 14–15/11, mất phiên dự phòng V3, đóng băng dữ liệu 22/11 ([nhật ký họp tuần 05](../nhat-ky/tuan-05.md)) |
| 05/11 | GCP từ chối tăng quota GPU ("not eligible for a quota increase"): phương án dự phòng K5(2) không dùng được |
| 06/11 | Khảo sát API Vast: không có máy 4 × 4090 VM verified nào ≤ 2 USD/giờ cả máy; máy 4 GPU giá rẻ đều unverified. Tiêu chí K6 **không đạt** |
| 06/11 | Test graceful shutdown ở nhà: vLLM 0.31.0 **không dừng khi nhận SIGTERM** ở mọi chế độ; 144/144 stream an toàn là nhờ grace period 180 s, không phải nhờ `--shutdown-timeout` |
| 08/11 | Phiên V0+V1: VM 4 × RTX A4000 16 GB (Séc, 0,611 USD/giờ cả máy) dựng từ máy trắng tới vLLM phục vụ trong 12,5 phút; cold start 3B 108–152 s; ĐG1 thử C = 4,5 req/s; runner chạy 2 lượt liền. Máy chỉ có 15 vCPU nên máy tạo tải vượt ngưỡng CPU |
| 09/11 | Lượt V1 A1 × KB3 kẹt ở 2 replica sau tải vì một mẫu GPU util 100 % của pod đang tắt |

## 2. Quyết định

| # | Nội dung | Quyết định | Lý do |
|---|---|---|---|
| C1 | Cloud | **Chỉ còn Vast.ai chế độ VM.** GCP bị loại hẳn (quota bị từ chối). Không còn phương án dự phòng bằng nhà cung cấp khác; dự phòng là **máy Vast khác** | Không còn thời gian xây lịch sử tài khoản GCP trước 14/11 |
| C2 | Loại máy V2 | **4 × RTX A4000 16 GB, chế độ VM, verified, ngoài Trung Quốc, ≥ 20 vCPU**, đo mạng thật bằng `make probe` ngay khi thuê. Nếu ngày 14/11 không có offer: (a) 4 × RTX 4090 VM (khoảng 2,4–2,7 USD/giờ cả máy, ≈ 55–60 USD cho 22 giờ, vẫn dưới trần 150 USD); (b) máy 2 GPU (2 × A4000 hoặc 2 × 5060 Ti) với **N = 2** và viết lại N3 theo N ở ADR-003 (ADR-005 T12) | A4000 đã chạy trọn V0+V1; giá bằng 1/4 máy 4090; 16 GB đủ cho 3B. 15 vCPU của máy V1 không đủ cho 4 pod vLLM × 3 lõi + máy tạo tải 3 lõi |
| C3 | Model cloud | **Qwen2.5-3B-Instruct** (overlay `serving/overlays/cloud-3b`), thay 7B. Overlay `cloud` (7B) giữ lại để tham khảo, không dùng cho V2 | Mọi chỉ tiêu tính theo C nên kết luận về autoscaling không phụ thuộc cỡ model; vừa GPU 16 GB; cold start ngắn hơn. Cái giá: số cold start đẹp hơn 7B, ghi vào Hạn chế. Giấy phép Qwen Research License (không phải Apache-2.0), dùng cho học thuật được, ghi trong luận văn |
| C4 | N | **N = 4** làm mặc định; code và ma trận tham số hoá theo N để chạy được N = 2 nếu rơi vào C2(b) | Giữ đúng S4 và N3 như thiết kế |
| C5 | Kịch bản tải | KB1 / KB2 / KB3 = **12 / 24 / 17 phút** (trước: 20 / 25 / 25); **đỉnh KB2 = 0,75 × N × C** (trước: cố định 3,0 C). Chi tiết và giới hạn khi rút ở [Thông số §7](../chi-tiet/00-thong-so.md#7-kịch-bản-tải) | Để V2 còn giờ cho lần lặp; đỉnh theo N để chạy được máy 2 GPU |
| C6 | KEDA `timeout` | `timeout: "1000"` ms cho mọi trigger Prometheus (mặc định 3000) | Với 3000 ms, T4 trên kind 3/7 lần vượt N6 (30 s); với 1000 ms 8/8 lần đạt (07/11) |
| C7 | Truy vấn A1 | `sum(avg_over_time(nvidia_smi_utilization_gpu_ratio[15s])) * 100` thay cho `sum(nvidia_smi_utilization_gpu_ratio) * 100` | Hạ một mẫu nhiễu 100 % của GPU vừa tắt xuống 33 %, khỏi kẹt replica; scale-up trễ thêm 5–20 s trên dữ liệu V1. **Quang làm thay phần TR2, Trình cần review**; chưa chạy với KEDA trên cluster, lần đầu là V2 |
| C8 | Graceful shutdown | **Tạm chấp nhận** cấu hình hiện tại (preStop 20 s + `--shutdown-timeout 150` + grace 180 s): request an toàn nhờ grace period giữ pod sống tới 180 s. Không gỡ lỗi vLLM trước V2. Ghi vào Hạn chế: (1) request kéo dài quá ~160 s sau SIGTERM vẫn bị SIGKILL cắt; (2) mỗi lần tắt, pod giữ GPU đủ 180 s, nên scale-down và rolling update tốn thêm 3 phút mỗi pod | Thời gian tới V2 không đủ để tìm nguyên nhân trong vLLM; N4 vẫn đo được |
| C9 | Lịch | V0+V1 gộp, **đã xong 08/11**; **V2 14–15/11**; không còn V3; đóng băng dữ liệu **22/11**, không lùi | Theo họp 04/11 |
| C10 | Tiền | 800.000 VND đã nạp là tiền GCP, không dùng được cho Vast. Tiền Vast nạp riêng trước 13/11, đủ ≥ 1,3 × chi phí dự kiến V2 | – |

## 3. Tình trạng phạm vi tới 10/11 (không đổi mức Must/Should, chỉ ghi nhận)

Các mục dưới đây có trong thiết kế nhưng **chưa có trong repo**. Nhóm chưa quyết định làm hay hạ mức; cần chốt ở buổi họp trước V2.

| Hạng mục | Thiết kế | Thực tế 10/11 |
|---|---|---|
| Sealed Secrets (F7, [Vận hành §7–§8](../chi-tiet/04-van-hanh.md#8-bảo-mật-tối-thiểu)) | Bí mật mã hoá trong Git | Chưa có; Secret `vllm-api-key`, `grafana-admin` tạo tay bằng `kubectl` |
| NetworkPolicy, rate limit Traefik, route riêng cho máy tạo tải (F7, ADR-005 T5) | Trong `serving/base/` | Chưa có; máy tạo tải gọi thẳng Service trong cluster |
| Argo CD app `autoscaling` (ADR-005 T7) và app cho `observability/` | Trong `platform/argocd/apps/home/` | Chưa có; A2, rule, cảnh báo, dashboard áp bằng `kubectl apply -k` |
| Argo CD trên VM thuê (F3, [Vận hành §7](../chi-tiet/04-van-hanh.md#7-dựng-lại-từ-đầu-khôi-phục-sau-thảm-hoạ)) | `make bootstrap` cài Argo CD + root-app | Cloud cài nền bằng helm qua `make cloud-platform` (`argocd_enabled: false`); VH2 trên VM kích hoạt rollout bằng annotation, không qua Git |
| Alertmanager → Telegram (F6) | 6 cảnh báo tới Telegram | Rule và runbook có, unit test đạt; chưa áp lên cluster, chưa có Telegram cho Alertmanager (Telegram của runner thì có) |
| `make burnin`, `make capacity`, `make analysis`, gói `analysis/` (TR7) | [Môi trường §3.7](../chi-tiet/05-moi-truong-danh-gia.md#37-tự-động-hoá-bằng-makefile) | Chưa có; burn-in rút gọn làm bằng `make probe` + `vllm bench serve` tay; ĐG1 chạy bằng `make run MATRIX=experiments/matrix-dg1-*.yaml` |

## 4. Các mục bị thay thế

| Mục | Nội dung cũ | Nội dung mới |
|---|---|---|
| ADR-004 K4 | 4 × RTX 4090, một lần thuê 07–08/11 | C2, C9 |
| ADR-004 K5 | Dự phòng (1) máy Vast khác 14–15/11, (2) GCP g2/L4 | C1, C2: chỉ còn máy Vast khác; không còn cuối tuần dự phòng |
| ADR-004 K6 | Tiêu chí ≥ 3 offer 4 × 4090 ≤ 0,50 USD/GPU-giờ; hạn 18/10 | Không đạt; C2 |
| ADR-004 K9 | Qwen2.5-7B trên GPU 24 GB | C3: Qwen2.5-3B trên GPU 16 GB |
| ADR-005 T1 | `--shutdown-timeout=150`, cần kiểm chứng | C8: cờ có, nhưng không có tác dụng trên vLLM 0.31.0; an toàn nhờ grace period |
| Thông số §7 (bản trước 08/11) | 20 / 25 / 25 phút, đỉnh KB2 3,0 C | C5 |
| Thông số §8.1 (A1) | `sum(nvidia_smi_utilization_gpu_ratio) * 100` | C7 |

Các mục còn lại của ADR-004 và ADR-005 giữ nguyên.

## 5. Hệ quả

- Mọi số đo của chương 5 sẽ gắn với **RTX A4000 (card workstation Ampere, 16 GB) và model 3B**, không phải 4090 và 7B như bản mô tả 3.0. Phần Hạn chế của luận văn ghi rõ, kèm ước lượng ngoại suy theo kích thước weights cho cold start.
- GPU-giờ của A2 ở KB2 cộng thêm 180 s mỗi pod bị tắt (C8); khi so với S4 ở N3 phải nói rõ phần này.
- Không còn phiên dự phòng: V2 hỏng thì áp dụng các dòng còn lại của [Kế hoạch §8](../chi-tiet/06-ke-hoach-quan-ly.md#8-dự-phòng-và-cắt-giảm-phạm-vi), chấp nhận ô chỉ có 1 lượt.
- C7 đổi tín hiệu A1 so với thiết kế gốc; nếu Trình không đồng ý thì đổi lại trước V2 và ghi vào ADR này.

## 6. Việc còn mở

| Việc | Hạn |
|---|---|
| Trình review C7 (truy vấn A1) | Trước V2 |
| Họp chốt §3: làm hay hạ mức Sealed Secrets, NetworkPolicy/rate limit, Argo CD app `autoscaling`/`observability`, Telegram cho Alertmanager | Trước V2 (13/11) |
| Chốt offer máy V2 bằng `make find MODE=v2` sáng 14/11; nạp tiền Vast | 13–14/11 |
| ADR-003: C, B\*, threshold, ngưỡng N2b, N3 theo N | Trong V2 |
