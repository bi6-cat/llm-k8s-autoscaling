# Việc sắp làm – Quang

> Cập nhật 05/11/2026 (W5), làm **bản bàn giao**: đọc file này cùng [nhật ký tuần 05](tuan-05.md) là đủ để làm tiếp trên máy khác hoặc trong phiên AI mới. Danh sách sống: đánh dấu `[x]` khi xong, ghi chi tiết vào nhật ký tuần. Mã việc theo [Kế hoạch §5.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công).

## 1. Tình trạng hiện tại

**Cả dự án:** M1 đạt 2/7, M2 đạt 0/8 ([Kế hoạch §3](../../../chi-tiet/06-ke-hoach-quan-ly.md#3-checklist-các-mốc)). Lịch đã dời ([Kế hoạch §1.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#11-điều-chỉnh-ngày-04112026)): V0+V1 khoảng 11–12/11, **V2 14–15/11**, đóng băng dữ liệu 22/11, không còn phiên dự phòng. Điểm dừng: 07/11 vòng autoscaling chạy trên kind (**đã đạt 04/11**, bằng file nháp của scaffold); **10/11 runner chạy 2 lượt liền không cần can thiệp** (chưa có runner).

**Cloud:** GCP bị chặn quota GPU ngày 05/11 ("not eligible … between 0 and 0"), nên coi **Vast là phương án duy nhất**. Chưa sửa ADR-004 K6.

**Phần của Quang:**

| Mã | Đã xong | Còn lại | Ước tính |
|---|---|---|---|
| Q1 Hạ tầng nhà | k3s trên PC bằng Ansible, chạy trên IP Tailscale; device plugin, GPU exporter; k3s tự lên sau mỗi lần PC khởi động lại | Laptop agent, giao cho Argo CD, dọn pod `Unknown` | ~75 % |
| Q2 Cloud | Khung `vast.sh`, overlay `cloud` (chưa chạy) | Tìm máy Vast, nạp tiền, `make bootstrap`, V0 | ~10 % |
| Q3 Serving | vLLM trên k3s nhà; overlay `sim` ghim digest, chạy trên kind | PodMonitor thật (cần Prometheus nhà), Argo CD | ~80 % |
| Q4 Cold start | Số đo sơ bộ 486 / 167 / 155 s | Pre-pull, đo 8 pha, L0/L2 | ~15 % |
| Q5 Vòng đời pod | Drain trong Docker (W1) | Graceful shutdown trong k8s, rolling update, VH1–VH3 | ~10 % |
| Q6 Runner, ĐG1 | ĐG1-mini bản tạm: `experiments/capacity-home.json` (C = 6 req/s) | **Runner v1**, đo lại ĐG1 quanh λ = 6 | ~15 % |
| Q7 VH5, chi phí | – | Toàn bộ | 0 % |
| Q8 LT1–LT4 | LT1 (5060), LT2, LT3 có kết quả trong `van-hanh.md` | LT4, LT1 trên 4050 | ~65 % |

Phần trăm là ước lượng theo đầu việc, không phải giờ đã dùng.

**Nhánh và PR** (đã push ngày 05/11, xếp chồng; merge theo thứ tự, chọn "Create a merge commit", **không squash**, xoá nhánh sau khi merge để GitHub tự đổi base của PR sau):

| Nhánh | PR | Base | Nội dung |
|---|---|---|---|
| `feat/home-k3s` | #6 (Q1), CI xanh | `main` | Ansible k3s, IP Tailscale, `platform/gpu/`, đã gộp `main` (CI) |
| `feat/serving` | chưa mở | `feat/home-k3s` | `serving/` |
| `docs/quang-w4` | chưa mở | `feat/serving` | Checklist mốc, dời V2, nhật ký tuần 04–05 |
| `feat/serving-sim` | chưa mở | `docs/quang-w4` | Overlay `sim` ghim digest, `capacity-home.json`, LT1–LT3, file này |

Lệnh mở 3 PR còn lại (mô tả PR viết theo nhật ký tuần 05):
`gh pr create --base feat/home-k3s --head feat/serving …`, `--base feat/serving --head docs/quang-w4 …`, `--base docs/quang-w4 --head feat/serving-sim …`.

## 2. Làm ngay (trước 10/11)

- [x] Dời V2 sang 14–15/11, ghi Kế hoạch §1.1 (04/11).
- [x] Vòng autoscaling chạy trên kind: A2 scale 1 → 3 → 1 (04/11).
- [x] LT1 batch = 1, LT2 lúc tải cao, LT3 (05/11).
- [x] ĐG1-mini ở nhà, `capacity-home.json` bản tạm (05/11).
- [x] Push 4 nhánh, mở PR #6 (05/11).
- [ ] **Mở 3 PR còn lại**, gán Trình review.
- [ ] **Q6 runner v1 trên simulator** (đường găng, hạn 10/11): áp cấu hình A1/A2, reset, chạy `loadgen` trong pod (gọi Service, **không** dùng `port-forward`), thu metric Prometheus, checkpoint, phát hiện pod vLLM đổi tên giữa lượt thì đánh dấu lượt không hợp lệ. Thay script tạm `runs/dg1-mini-home-20261105/dg1_mini.py` (chỉ có trên máy dev, gitignore).
- [ ] **Q2 tìm máy Vast** 4 × 4090 chế độ VM cho 11–12/11 và 14–15/11 (dự phòng 3090/A5000); làm rõ 800.000 VND đã nạp vào đâu, nạp thêm nếu cần; sửa ADR-004 K6 (chọn Vast, GCP bị chặn quota).
- [ ] **Họp ngắn với Trình:** ngưỡng `throttle_ok` (đề xuất theo `throttled_usec`); lọc lỗi theo cột `error` chứ không theo `status` trong `requests.csv`; sửa comment `pollingInterval` của A2; `for: 1m` của `LLMErrorRateHigh`; cột `id`, `n_in_target`. Nhắc Trình push `feat/tr2-sim`.
- [ ] **Q6 đo lại ĐG1 quanh λ = 6:** λ = 5,75–7 bước 0,25, luồng lấy mẫu ra ngoài pod máy tạo tải (hoặc pod 2 lõi) để hết throttle.
- [ ] **Q2:** tách `vast.sh`, overlay `cloud`, Ansible cho VM sang `feat/cloud`; kiểm cú pháp.

## 3. Cần PC bật

- [ ] **Q5:** test graceful shutdown với vLLM thật (3 lần + ca đối chứng).
- [ ] **Q5 tìm nguyên nhân:** pod vLLM đang khởi tạo không thoát khi nhận SIGTERM.
- [ ] **Q4:** manifest pre-pull (giới hạn ghi vì ổ SATA); L2 và đo 8 pha (cần `parse_vllm_log` của TR5); LT4.
- [ ] Dọn 5 pod vLLM cũ (`Unknown`/`Completed`) và pod `loadgen` trong `llm-serving`.
- [ ] TTFT trên k3s cao hơn Docker (p50 +18 %): đo lại gọi thẳng Service, bỏ Ingress.

**Lưu ý vận hành PC** (chi tiết ở [`van-hanh.md`](../../van-hanh.md)):
- **Không suspend** PC khi vLLM đang chạy: `nvidia-suspend` treo (05/11). Muốn nghỉ thì `shutdown`, hoặc scale vLLM về 0 trước.
- **Không xoá máy hay revoke key của PC trên Tailscale:** k3s chạy trên IP Tailscale, mất Tailscale là cluster mất mạng. Key hết hạn 21/04/2027; có thể bật "Disable key expiry".
- RTC của PC từng lệch 7 giờ lúc boot (nghi do dual-boot Windows), nên giờ trong log ngay sau khi boot có thể sai.
- kubeconfig nhà ở `~/.kube/llm-home.yaml` trên máy dev (dùng `KUBECONFIG=~/.kube/llm-home.yaml`); context mặc định của máy dev đang là `kind-llm-sim`.

## 4. Cần ngồi cạnh máy

- [ ] Laptop 4050 vào cluster: kiểm driver ≥ 580, sửa SSH host key, thêm vào `k3s_agent`. Cần cho VH2, KB2-mini, LT1 phần 4050.
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
| LT5, LT6 | Dữ liệu đã có trong `capacity-home.json`, Trình phân tích (TR8) |
