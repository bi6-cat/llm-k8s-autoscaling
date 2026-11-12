# Việc sắp làm – Quang

> Cập nhật **09/11/2026** (W6, sau V0+V1), làm **bản bàn giao**: đọc file này cùng [nhật ký tuần 05](tuan-05.md) và [log phiên 08/11](phien-2026-11-08-a4000.md) là đủ để làm tiếp trên máy khác hoặc trong phiên AI mới. Danh sách sống: đánh dấu `[x]` khi xong, ghi chi tiết vào nhật ký tuần. Mã việc theo [Kế hoạch §5.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công).

## 1. Tình trạng hiện tại

Trang tiến độ tổng quát (quy trình, chặng, từ điển mã): <https://claude.ai/artifact/9hQJicovMS6rjxdLuNJf5a>. Trang ngắn "Đường tới V2": <https://claude.ai/code/artifact/84c8ef49-e9d2-4f5e-8ffd-b0598601982d>. Báo cáo phiên A4000: <https://claude.ai/code/artifact/4c4ab8e2-6e1d-47a7-9d4b-8470c78c74be>. Cả ba chỉ chủ tài khoản xem được; muốn chia sẻ thì bấm Share trên trang.

**Cả dự án:** M1 đạt 7/7, M2 đạt 2/8 ([Kế hoạch §3](../../../chi-tiet/06-ke-hoach-quan-ly.md#3-checklist-các-mốc)). **V0+V1 đã xong 08/11** (sớm 3 ngày). Còn: **V2 14–15/11**, đóng băng dữ liệu 22/11, không còn phiên dự phòng.

**Cloud:** Vast VM. Đã thử 2 máy 08/11: 2 × 5060 Ti (Trung Quốc, unverified: mạng 8 MB/s, cold start 6 phút, loại) và **4 × RTX A4000** (Séc, $0,611/giờ: dựng 12,5 phút, cold start ~2 phút, ĐG1 thử C = 4,5 req/s, V1 2 lượt). Model **3B**, N = 4, kịch bản 12 / 24 / 17 phút. Máy V2: loại 4 × A4000 nhưng **≥ 20 vCPU** (máy V1 có 15 vCPU, thiếu CPU cho máy tạo tải). Tiêu chí: verified, ngoài Trung Quốc, đo mạng thật ngay khi thuê. 800.000 VND đã nạp là tiền GCP; tiền Vast nạp riêng.

**Phần của Quang:**

| Mã | Đã xong | Còn lại | Ước tính |
|---|---|---|---|
| Q1 Hạ tầng nhà | k3s bằng Ansible trên IP Tailscale, device plugin, GPU exporter, time-slicing 2 GPU replica, Argo CD quản lý | Dọn pod `Unknown`, quyết định ổ SATA | ~90 % |
| Q2 Cloud | 2 VM thật; Ansible cho VM (mirror Docker Hub, tắt tự nâng cấp, giữ driver); cài nền bằng helm (script tay 236 s) | Chốt máy V2, nạp tiền; đưa tải sẵn model/image và cài nền vào Ansible/Makefile; script kiểm máy | ~75 % |
| Q3 Serving | vLLM qua Argo CD ở nhà; overlay `cloud-3b` chạy trên VM | TTFT k3s cao hơn Docker 18 % (p50), đo lại bỏ Ingress | ~90 % |
| Q4 Cold start | L2 trên A4000: 152 s / 108 s (có cache) / 3 pod đồng thời 117–122 s | L0; đo 8 pha bằng `parse_vllm_log` (PR #24); ĐG3 trên V2 | ~45 % |
| Q5 Vòng đời pod | Test graceful shutdown 144/144 (nhờ grace 180 s) | Nguyên nhân vLLM bỏ qua SIGTERM (tạm chấp nhận); rolling update, VH1–VH3 | ~35 % |
| Q6 Runner, ĐG1 | Runner trên kind, nhà, VM; ĐG1-mini 0,5B (C = 12,5); ĐG1 thử 3B (C = 4,5); V1 2 lượt; sửa UTIL trong `capacity.py` | Runner v2: R2, systemd, Telegram; ĐG1 chính thức trên V2 → ADR-003 | ~70 % |
| Q7 VH5, chi phí | Dựng từ VM trắng 12,5 phút; chi phí phiên A4000 ≈ $1,5 | VH5 bấm giờ chính thức trên V2; sổ chi phí | ~30 % |
| Q8 LT1–LT4 | LT1 (5060), LT2, LT3 | LT4; điểm LT1 thứ hai từ benchmark A4000 | ~65 % |

Phần trăm là ước lượng theo đầu việc, không phải giờ đã dùng.

**Nhánh và PR** (09/11): PR #24, #25, #26 đã merge vào `main`. PR #27 merge nhầm vào `feat/v2-prep` (base không phải `main`), nên 7 commit dọn dẹp được đưa vào `main` bằng nhánh `chore/v2-prep-to-main`. Từ nay tách nhánh mới từ `main`; trước khi merge PR dưới của một chồng PR, đổi base PR trên về `main`.

## 2. Làm ngay (trước V2, hạn 13/11)

- [x] (08/11) Chốt model **3B**, rút kịch bản 12 / 24 / 17 phút, đỉnh KB2 theo N, N = 4.
- [x] (08/11) **V0+V1** trên VM Vast: bootstrap, cold start, benchmark, ĐG1 thử, runner 2 lượt có KEDA.
- [x] (08/11) Sửa UTIL trong `capacity.py` (lấy GPU bận nhất mỗi lần scrape).
- [ ] **Họp với Trình:** chốt máy V2 (4 × A4000, ≥ 20 vCPU), nạp tiền Vast; đọc kết quả V1 (hàng đợi ghim vào pod cũ, A1 kẹt ở 2 replica); các điểm cũ: lọc lỗi theo cột `error`, comment `pollingInterval` của A2, `for: 1m` của `LLMErrorRateHigh`.
- [x] ~~Review PR #24, #25 của Trình~~: Trình đã tự merge (08–09/11), Quang chưa review. Hai phần này chưa chạy với log vLLM thật: kiểm bằng một lượt ngắn đầu V2.
- [x] (09/11, code xong, **chưa chạy trên VM**) **Q2:** `cloud-prefetch`, `make cloud-platform`, `make probe`, bộ lọc v2 mới.
- [x] (09/11, code xong, **chưa thử R2 và Telegram thật**) **Q6 runner v2:** R2, systemd, Telegram.
- [x] (09/11, chạy trên kind, **chưa chạy trên GPU**) **Q5, Q7:** `make ops-tests` (VH2–VH4), `make vh5`.
- [x] (09/11) **Merge theo thứ tự:** PR #28 `chore/v2-prep-to-main` → #29 A1 → #30 cloud → #31 runner → #32 VH, đều vào `main`. Không PR nào có review trên GitHub; Trình đồng ý truy vấn A1 (ADR-006 C7) qua tin nhắn ngày 12/11.
- [x] (10/11, 12/11) **Đồng bộ tài liệu với ADR-006:** ADR-006 + chỉ mục ADR; Thông số, Bài toán, Kiến trúc, Vận hành, Môi trường, Kế hoạch, Kiến thức nền, mô tả tổng; trạng thái ADR-004/005; Hình 6, 9; ghi chú lỗi thời ở W1, W2. PR #33 (nhánh `docs/sync-after-v1`), chưa merge.
- [x] (12/11) **Chốt ADR-006 §3:** Quang đề xuất, Trình đồng ý qua tin nhắn; ghi ở ADR-006 §3.1. Làm trước V2: Argo CD app `autoscaling`/`observability` (TR1), Alertmanager → Telegram (TR4). Lược: Sealed Secrets, NetworkPolicy/rate limit, Argo CD trên VM, các lệnh `make burnin`/`capacity`/`analysis` (vẫn phải đo ĐG1 → ADR-003 và làm biểu đồ chương 5).
- [ ] **Tạo `.env`:** `VAST_VM_TEMPLATE`, API key Vast, khoá R2, bot Telegram; thử `make backup` và một tin Telegram trước V2.
- [ ] **Chốt máy V2:** 09/11 Vast không có offer VM 4 × A4000; chỉ có 4 × 5090 / 4 × 4090 từ $2,4/giờ và thay đổi trong vài phút. Theo dõi `make find`.
- [ ] Sao lưu `runs/` bằng `make backup` (V0+V1 chỉ có trên laptop; cần `.env`).
- [ ] Thử toàn bộ đường VM (`make probe vh5 run`) bằng một VM rẻ trước V2 nếu kịp: các script này chưa từng chạy trên VM.

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

- [ ] V2 (14–15/11): VH5 từ VM trắng, ĐG1 → `capacity.json` → ADR-003, ma trận 17 lượt, ĐG3 cold start L0/L2.
- [ ] Q5: chạy VH1–VH4 trên GPU thật (`make ops-tests`); VH2 qua Git + Argo CD ở nhà.
- [ ] Q7: chạy `make vh5` trên V2, sổ chi phí.
- [ ] Viết phần của Quang ở chương 2–3; chương 5 dùng thêm quan sát V1 (hàng đợi ghim vào pod cũ).

## 6. Phụ thuộc vào Trình

| Việc của Quang | Cần từ Trình |
|---|---|
| Runner, V2 (Q6) | ~~Review truy vấn A1~~: Trình đồng ý 12/11 (qua tin nhắn). Truy vấn chưa chạy trên cluster, lần đầu là V2 |
| Demo (F3, F6) | Argo CD app `autoscaling`/`observability` (TR1) và Alertmanager → Telegram (TR4) trước V2 (ADR-006 §3.1) |
| PodMonitor vLLM và GPU ở nhà, số đo từ Prometheus | kube-prometheus-stack trên cluster nhà (TR3) |
| Serving qua Argo CD | Argo CD + App-of-Apps (TR1) |
| Đo 8 pha (Q4) | `parse_vllm_log` (TR5, đã merge; chưa chạy với log vLLM thật) |
| LT5, LT6 | Dữ liệu đã có trong `capacity-home*.json` và `runs/v1-a4000/` (V1 minh hoạ LT6), Trình phân tích (TR8) |
