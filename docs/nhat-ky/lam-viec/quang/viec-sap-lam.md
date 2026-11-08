# Việc sắp làm – Quang

> Cập nhật 06/11/2026 tối (W5; 06/11 thêm time-slicing, bỏ laptop; tối 06/11: runner, PR #12–#14 đã merge, `vast.sh`, khảo sát máy thuê), làm **bản bàn giao**: đọc file này cùng [nhật ký tuần 05](tuan-05.md) là đủ để làm tiếp trên máy khác hoặc trong phiên AI mới. Danh sách sống: đánh dấu `[x]` khi xong, ghi chi tiết vào nhật ký tuần. Mã việc theo [Kế hoạch §5.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công).

## 1. Tình trạng hiện tại

Trang tiến độ có giải thích quy trình (môi trường, chặng, runner, Git, từ điển mã): <https://claude.ai/artifact/9hQJicovMS6rjxdLuNJf5a> (chỉ chủ tài khoản xem được, muốn chia sẻ thì bấm Share trên trang). Trang tiến độ chung của Quang và Trình (08/11): <https://claude.ai/code/artifact/84c8ef49-e9d2-4f5e-8ffd-b0598601982d>.

**Cả dự án:** M1 đạt 2/7, M2 đạt 0/8 ([Kế hoạch §3](../../../chi-tiet/06-ke-hoach-quan-ly.md#3-checklist-các-mốc)). Lịch đã dời ([Kế hoạch §1.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#11-điều-chỉnh-ngày-04112026)): V0+V1 khoảng 11–12/11, **V2 14–15/11**, đóng băng dữ liệu 22/11, không còn phiên dự phòng. Điểm dừng: 07/11 vòng autoscaling chạy trên kind (**đã đạt 04/11**, bằng file nháp của scaffold); **10/11 runner chạy 2 lượt liền không cần can thiệp** (chưa có runner).

**Cloud:** GCP bị chặn quota GPU ngày 05/11, nên **Vast là phương án duy nhất** (đã ghi ADR-004 §7, 06/11). Khảo sát 06/11: không có máy 4 × 4090 VM verified nào ≤ 2 USD/giờ (rẻ nhất 2,67); máy verified chủ yếu 2 GPU (2 × 5060 Ti 0,27 USD/giờ). Chưa chốt máy, N và model (3B thử bằng overlay `cloud-3b`): **họp với Trình, ghi ADR-003**. Phương án A–D ở [nhật ký tuần 05](tuan-05.md).

**Phần của Quang:**

| Mã | Đã xong | Còn lại | Ước tính |
|---|---|---|---|
| Q1 Hạ tầng nhà | k3s trên PC bằng Ansible, chạy trên IP Tailscale; device plugin, GPU exporter; k3s tự lên sau mỗi lần PC khởi động lại | Áp time-slicing (3 GPU replica) lên PC, giao cho Argo CD, dọn pod `Unknown` | ~75 % |
| Q2 Cloud | `vast.sh` (find đã chạy với API thật; rent/wait/release chưa chạy), overlay `cloud` và `cloud-3b` (chưa chạy), Ansible qua syntax-check với inventory cloud | Chốt máy, nạp tiền, API key + template VM vào `.env`, thuê VM 1 GPU rẻ gỡ lỗi bootstrap, V0 | ~25 % |
| Q3 Serving | vLLM trên k3s nhà; overlay `sim` ghim digest, chạy trên kind | PodMonitor thật (cần Prometheus nhà), Argo CD | ~80 % |
| Q4 Cold start | Số đo sơ bộ 486 / 167 / 155 s | Pre-pull, đo 8 pha, L0/L2 | ~15 % |
| Q5 Vòng đời pod | Drain trong Docker (W1); test graceful shutdown trong k8s (06/11, 0 lỗi nhờ grace period) | Nguyên nhân vLLM không thoát; rolling update, VH1–VH3 | ~35 % |
| Q6 Runner, ĐG1 | Runner v1 (kind + nhà), `capacity.py`, ĐG1-mini 0,5B: C = 12,5 req/s (PR #12–#14) | Runner v2: R2, systemd, Telegram; file ma trận V2; ĐG1 trên V0/V2 | ~50 % |
| Q7 VH5, chi phí | – | Toàn bộ | 0 % |
| Q8 LT1–LT4 | LT1 (5060), LT2, LT3 có kết quả trong `van-hanh.md` | LT4; điểm LT1 thứ hai: 0,5B trên 5060 và 7B trên 4090 (V2), thay cho 4050 | ~65 % |

Phần trăm là ước lượng theo đầu việc, không phải giờ đã dùng.

**Nhánh và PR** (06/11 tối): PR #6–#14 đã merge vào `main`. Đang làm: `feat/cloud-prep` (tách từ `feat/dg1-home-05b`, chưa commit, sẽ commit sáng 07/11): overlay `cloud-3b`, `vast.sh`, ADR-004 K6, nhật ký 06/11. Merge `main` vào nhánh đang mở ngay sau mỗi lần merge PR, để conflict nhật ký nhỏ (bài học PR #14).

## 2. Làm ngay (trước 10/11)

- [x] Dời V2 sang 14–15/11, ghi Kế hoạch §1.1 (04/11).
- [x] Vòng autoscaling chạy trên kind: A2 scale 1 → 3 → 1 (04/11).
- [x] LT1 batch = 1, LT2 lúc tải cao, LT3 (05/11).
- [x] ĐG1-mini ở nhà, `capacity-home.json` bản tạm (05/11).
- [x] Push 4 nhánh, mở PR #6 (05/11).
- [x] ~~Mở 3 PR còn lại~~ (PR #7–#14 đã merge, 06/11).
- [x] (06/11, PR #12) **Q6 runner v1 trên simulator** (đường găng, hạn 10/11): áp cấu hình A1/A2, reset, chạy `loadgen` trong pod (gọi Service, **không** dùng `port-forward`), thu metric Prometheus, checkpoint, phát hiện pod vLLM đổi tên giữa lượt thì đánh dấu lượt không hợp lệ. Thay script tạm `runs/dg1-mini-home-20261105/dg1_mini.py` (chỉ có trên máy dev, gitignore).
- [x] (06/11) Khảo sát máy Vast và sửa ADR-004 K6: xem mục Cloud ở trên.
- [x] (08/11) Chốt model **3B** cho V2, rút kịch bản còn 12 / 21 / 17 phút, đỉnh KB2 theo N (nhánh `feat/shorter-scenarios`). N nghiêng về 2; 800.000 VND là tiền nạp GCP, bỏ qua.
- [ ] **Q2 chốt loại máy 2 GPU** (3090 / 5060 Ti / A4000): chạy `GPU=… NGPU=2 MAX_DPH=1.5 infra/provision/vast.sh find v2`, cần driver ≥ 580 (CUDA 13), máy verified; ghi ADR-003; nạp tiền Vast trước 13/11.
- [ ] **10/11** Quang thuê VM 1 GPU thử `rent → bootstrap → release`; **11–12/11** V0+V1 (đo cold start 3B: > 2,5 phút thì nới `spike` của KB2 về 10 phút).
- [ ] **Họp ngắn với Trình:** ngưỡng `throttle_ok` (đề xuất theo `throttled_usec`); lọc lỗi theo cột `error` chứ không theo `status` trong `requests.csv`; sửa comment `pollingInterval` của A2; `for: 1m` của `LLMErrorRateHigh`; cột `id`, `n_in_target`. Nhắc Trình push `feat/tr2-sim`.
- [x] (06/11, runner phiên `dg1-home-05b`: C = 12,5 req/s, B\* = 28,4) **Q6 đo lại ĐG1-mini với cấu hình nhà mới** (0,5B, 1 pod, `gpu-memory-utilization` 0,40): `capacity-home.json` hiện là của 1,5B nên ngưỡng A2 ở nhà phải tính lại. Luồng lấy mẫu ra ngoài pod máy tạo tải (hoặc pod 2 lõi) để hết throttle.
- [x] (06/11, `feat/cloud-prep`) **Q2:** `vast.sh` (lọc verified, bỏ `is_vm_deverified`, tham số GPU/NGPU/MAX_DPH), Ansible syntax-check với inventory cloud.
- [ ] **Q2:** điền `VAST_VM_TEMPLATE` và API key; thuê VM 1 GPU rẻ (≤ 0,15 USD/giờ, 2–4 giờ) chạy `make rent` → `bootstrap` → `release` để gỡ lỗi trước V0.
- [ ] **Q6 runner v2:** đẩy R2 sau mỗi lượt, unit systemd, báo Telegram (bot riêng, không đụng Alertmanager của Trình).
- [ ] **Q4 `make prefetch`** (L2) trên PC.

## 3. Cần PC bật

- [x] ~~**Q1/Q3 áp time-slicing lên PC**~~ (06/11): chạy được 1 pod; 2 pod vừa VRAM nhưng hết RAM, xem `van-hanh.md`. Còn: giải quyết RAM (tắt desktop/zram) rồi thử lại 2 pod. Ghi chú cũ: `helm upgrade` device plugin với `-f device-plugin-values.yaml -f device-plugin-values-home.yaml`, kiểm node báo `nvidia.com/gpu: 3`; áp overlay `home` (0,5B), scale lên 2 rồi 3 pod: cả ba Ready? khởi động cùng lúc có lỗi VRAM không? Đo VRAM (`nvidia-smi`) và RAM (`kubectl top pod`) thực rồi chỉnh `gpu-memory-utilization`, `resources`.
- [x] (06/11) **Q5:** test graceful shutdown với vLLM thật: 144/144 stream ok trong 3 lần; đối chứng grace 5 s cắt 48/48. Nhưng request an toàn là nhờ grace 180 s, vLLM không dừng khi nhận SIGTERM (xem `van-hanh.md` 06/11).
- [ ] (08/11: **tạm chấp nhận** grace 180 s, ghi vào Hạn chế; tối ưu sau nếu cần) **Q5 tìm nguyên nhân:** vLLM 0.31.0 không dừng engine và không thoát khi nhận SIGTERM, ở mọi trạng thái (khởi tạo, nhàn rỗi, đang phục vụ; drain lẫn abort). Thử `kill -TERM` tay, xem tiến trình con, thử bản vLLM khác; kiểm lại trên VM ở V0. Hệ quả nếu không sửa: mỗi lần tắt pod giữ GPU 180 s.
- [ ] **Q4:** manifest pre-pull (giới hạn ghi vì ổ SATA); L2 và đo 8 pha (cần `parse_vllm_log` của TR5); LT4.
- [ ] Dọn 5 pod vLLM cũ (`Unknown`/`Completed`) và pod `loadgen` trong `llm-serving`.
- [ ] TTFT trên k3s cao hơn Docker (p50 +18 %): đo lại gọi thẳng Service, bỏ Ingress.

**Lưu ý vận hành PC** (chi tiết ở [`van-hanh.md`](../../van-hanh.md)):
- **Không suspend** PC khi vLLM đang chạy: `nvidia-suspend` treo (05/11). Muốn nghỉ thì `shutdown`, hoặc scale vLLM về 0 trước.
- **Không xoá máy hay revoke key của PC trên Tailscale:** k3s chạy trên IP Tailscale, mất Tailscale là cluster mất mạng. Key hết hạn 21/04/2027; có thể bật "Disable key expiry".
- RTC của PC từng lệch 7 giờ lúc boot (nghi do dual-boot Windows), nên giờ trong log ngay sau khi boot có thể sai.
- kubeconfig nhà ở `~/.kube/llm-home.yaml` trên máy dev (dùng `KUBECONFIG=~/.kube/llm-home.yaml`); context mặc định của máy dev đang là `kind-llm-sim`.

## 4. Cần ngồi cạnh máy

- [x] ~~Laptop 4050 vào cluster~~: không cần nữa, thay bằng time-slicing trên PC (06/11, [ADR-004 §7](../../../adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md#7-cập-nhật-sau-ngày-08102026)). Drain node (VH3) làm trên kind nhiều node.
- [ ] Quyết định ổ SATA của PC: giữ + giới hạn ghi khi kéo image, hay chuyển `/var/lib/rancher` / cache model sang NVMe.
- [ ] SSH vào PC bằng khoá (tuỳ chọn: mật khẩu hiện tại yếu, nhưng SSH chỉ mở qua LAN và Tailscale).

## 5. Sau đó

- [ ] V0+V1 (11–12/11): `make bootstrap` trên VM Vast, vLLM 7B, `fio`, TPOT, runner 2 lượt.
- [ ] Q6: ĐG1 trên V2 → `capacity.json`, ADR-003.
- [ ] Q5: rolling update theo ADR-005 + VH2 (gồm ca 1 replica, ca đối chứng VH2c); VH1, VH3.
- [ ] Q7: script VH5, sổ chi phí.
- [ ] Viết phần của Quang ở chương 2–3 (LT1–LT3 đã có số liệu cho chương 5).

## 6. Phụ thuộc vào Trình

| Việc của Quang | Cần từ Trình |
|---|---|
| Runner (Q6) | ScaledObject A1–A4 và file ma trận (TR2), push `feat/tr2-sim`; review PR #6 và các PR sau |
| PodMonitor vLLM và GPU ở nhà, số đo từ Prometheus | kube-prometheus-stack trên cluster nhà (TR3) |
| Serving qua Argo CD | Argo CD + App-of-Apps (TR1) |
| Đo 8 pha (Q4) | `parse_vllm_log` (TR5) |
| LT5, LT6 | Dữ liệu đã có trong `capacity-home-1.5b.json` (1,5B) và `capacity-home.json` (0,5B, 06/11), Trình phân tích (TR8) |
