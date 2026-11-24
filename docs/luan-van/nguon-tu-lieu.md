<!-- Mục đích: chỉ chỗ tìm tư liệu cho từng mục luận văn (thiết kế, nhật ký, dữ liệu, hình, trang báo cáo), trạng thái số liệu ngày 20/11/2026 và những gì chưa được viết số. Người viết: Quang. File không ghép vào .docx (tên không bắt đầu bằng số). -->
# Nguồn tư liệu để viết luận văn

Cập nhật **20/11/2026**, sau phiên V2 (18–19/11); số mục ở §1, §2 đánh lại theo dàn ý ngày 23/11. Đọc cùng [README.md](README.md) (quy ước viết) và [Kế hoạch §11.1](../chi-tiet/06-ke-hoach-quan-ly.md#111-dàn-ý-luận-văn-5565-trang) (dàn ý, số trang, người viết).

Cách dùng: tìm mục mình viết ở [§2](#2-từng-mục-nguồn-nào), mở các nguồn trong cột "Nguồn", lấy số từ [§3](#3-số-liệu-đã-chốt) (mỗi số có nơi gốc để đặt vào comment `<!-- nguồn: … -->`), và kiểm [§4](#4-chưa-có-không-được-viết-số) trước khi viết bất kỳ con số nào.

## 1. Bản đồ các loại nguồn

| Loại | Ở đâu | Dùng để |
|---|---|---|
| Thiết kế | [`docs/chi-tiet/00`–`06`](../chi-tiet/) và [mô tả tổng](../mo-ta-chi-tiet-do-an.md) | Chương 1–3: lý do, kiến trúc, cách tính. Là **ý định**; chỗ nào lệch với cái đã làm thì viết theo nhật ký và mã nguồn |
| Quyết định | [`docs/adr/`](../adr/): 001 lựa chọn ban đầu, 002 trọng tâm vận hành, 004 phạm vi rút gọn và cloud, 005 sửa thiết kế sau review, 006 chốt máy, model, kịch bản trước V2 | Đoạn "vì sao chọn X, bỏ Y" ở chương 3–4. ADR-003 (chốt năng lực) **chưa viết** |
| Nhật ký cá nhân | [`lam-viec/quang/`](../nhat-ky/lam-viec/quang/), [`lam-viec/trinh/`](../nhat-ky/lam-viec/trinh/), mỗi tuần một file; mục nào cũng có dòng **Thesis** ghi mục luận văn nó phục vụ | Chương 4 (đã làm gì, gặp sự cố gì), chương 5 (số đo). Tìm nhanh: `grep -n "Thesis:.*§5" docs/nhat-ky/lam-viec/*/tuan-*.md` |
| Nhật ký vận hành | [`docs/nhat-ky/van-hanh.md`](../nhat-ky/van-hanh.md) | Sự cố (4.6), các phiên thuê GPU, **LT1–LT8** (lý thuyết → dự đoán → đo → lệch) |
| Nhật ký họp | [`docs/nhat-ky/tuan-01.md`](../nhat-ky/tuan-01.md), [`tuan-05.md`](../nhat-ky/tuan-05.md) | Mốc, quyết định của nhóm |
| Bàn giao của Quang | [`viec-sap-lam.md`](../nhat-ky/lam-viec/quang/viec-sap-lam.md) (tình trạng Q1–Q8 tới 16/11), [`phien-2026-11-08-a4000.md`](../nhat-ky/lam-viec/quang/phien-2026-11-08-a4000.md) (phiên V0+V1 từng bước) | 4.1, 4.4, 5.1, 5.2 |
| Runbook | [`docs/runbooks/`](../runbooks/), 7 file | 4.6, Phụ lục C |
| Phiên bản | [`docs/phien-ban.md`](../phien-ban.md) | Bảng phiên bản (phụ lục), tên phiên bản trong bài |
| Sơ đồ | `docs/images/*.svg` (bản PNG ở `docs/images/png/`, sinh từ `docs/diagrams/`) | Hình chương 1–4. Hình 7 lệch cái đã làm ở 6 chỗ (nhật ký Trình 18/11), chưa sửa |
| Biểu đồ kết quả | [`analysis/figures/`](../../analysis/figures/): LT5, LT6, LT7, LT8 (SVG + CSV); bảng và hình C1–C4 của V2 ở [`analysis/figures/v2-dg2/`](../../analysis/figures/v2-dg2/) | Chương 5. Hình C1–C4 chưa được xem lại bố cục (§5) |
| Báo cáo HTML trong repo | [`docs/bao-cao/bao-cao-ky-thuat.html`](../bao-cao/bao-cao-ky-thuat.html) (số đo 08/11, mô phỏng ma trận); [`docs/bao-cao/de-xuat-v3/`](../bao-cao/de-xuat-v3/) (tờ trình V3, bốn hướng nâng cấp, mô phỏng Holt-Winters, ski-rental) | Số đo 08/11 là **sơ bộ**. Phần V3 là **đề xuất, không chạy**: chỉ dùng cho chương 6 (hướng phát triển), không dùng như kết quả |
| Dữ liệu thô | `runs/` (không nằm trong Git) | Xem §5 |

### 1.1. Trang báo cáo trên claude.ai (artifact)

Các trang này do Quang tạo trong phiên Claude, **mặc định chỉ Quang xem được**; Quang phải bấm Share trên từng trang thì Trình mới mở được. Repo đang công khai, nên nếu chia sẻ kiểu "ai có link cũng xem" thì người ngoài cũng mở được. Số trong các trang đều chép từ nhật ký; khi viết, **trích từ nhật ký hoặc `runs/`, không trích từ trang**.

Cột "Nội dung" lấy theo tiêu đề trang và mục nhật ký nhắc tới trang đó; ngày là lần cập nhật cuối.

| Trang | Ngày | Nội dung | Dùng cho |
|---|---|---|---|
| [Phiên đo V2 · 4 × RTX 4060 Ti](https://claude.ai/code/artifact/d3325c38-ac4e-4056-a9b3-8d8afb7ec8c1) | 20/11 | Báo cáo tổng hợp phiên V2 (`Q-07` 19/11) | §5.2–5.5, Hạn chế |
| [Tiến độ đồ án vLLM Autoscaling](https://claude.ai/code/artifact/ece6b3ec-1aff-401c-a18e-e4c38a554053) | 18/11 | Tiến độ trước V2 | Bối cảnh |
| [LLM serving co giãn trên Kubernetes](https://claude.ai/code/artifact/2a62182e-a1f1-4c64-b5a4-5b25427e9f07) | 12/11 | Trang tổng quan dự án | Chương 1–3, slide |
| [Tờ trình nâng cấp V3](https://claude.ai/code/artifact/4b436b76-148e-4c07-9532-53cb1dfd6e84) | 13/11 | Đề xuất V3 (`Q-06` 13/11; nguồn ở `de-xuat-v3/to-trinh.html`) | Chương 6 |
| [Bốn hướng nâng cấp bài toán](https://claude.ai/code/artifact/9bc6694c-e114-493e-af23-ab28568fcf01) | 13/11 | Các hướng nâng cấp (`Q-06` 13–14/11; nguồn ở `de-xuat-v3/cac-huong-nang-cap.html`) | Chương 6 |
| [Phiên 4 × A4000](https://claude.ai/code/artifact/4c4ab8e2-6e1d-47a7-9d4b-8470c78c74be) | 08/11 | Báo cáo phiên V0+V1 (`viec-sap-lam.md` §1) | 4.1, 4.4, 3.2 |
| [Phiên thử VM Vast 08/11](https://claude.ai/code/artifact/79913d78-663a-4805-b9e3-2e6610b41d5a) | 08/11 | Phiên thử VM ngày 08/11 | 3.2, 4.1 |
| [Đường tới V2](https://claude.ai/code/artifact/84c8ef49-e9d2-4f5e-8ffd-b0598601982d) | 08/11 | Các việc trước V2 (`viec-sap-lam.md` §1) | Bối cảnh |
| [Tiến độ đồ án autoscaling vLLM](https://claude.ai/code/artifact/466d38fb-9947-4a91-98ad-61e8b4f98f99) | 08/11 | Trang tiến độ trước V0+V1 (`Q-05` 05/11) | Bối cảnh |
| [Trang tiến độ tổng quát](https://claude.ai/artifact/9hQJicovMS6rjxdLuNJf5a) | – | Quy trình, chặng, từ điển mã (`viec-sap-lam.md` §1) | Bối cảnh |
| [Báo cáo ngày 06/11](https://claude.ai/code/artifact/c8d8eb10-5b38-443f-984c-ad4ffb346e92) | 06/11 | Báo cáo ngày 06/11 | 4.2, 4.5, 4.6 |
| [Báo cáo phiên 04/11 – chạy local](https://claude.ai/code/artifact/4ed81c5c-a016-4292-ae90-71c103d3ba53) | 03/11 | Phiên chạy local (kind) | 4.3 |

## 2. Từng mục: nguồn nào

Số mục theo dàn ý ở Kế hoạch §11.1. Bản base do Trình viết; người sở hữu tính năng theo Kế hoạch §5.1 soát kỹ mục tương ứng. Tên nhật ký viết tắt: `Q-07` = `lam-viec/quang/tuan-07.md`, `T-05` = `lam-viec/trinh/tuan-05.md`, `VH` = `van-hanh.md`. Ngày trong ngoặc là tiêu đề mục nhật ký.

### Chương 1–2

| Mục | Nguồn |
|---|---|
| 1.1 Bối cảnh, 1.2 Phát biểu bài toán | Bài toán §1–§7 (§4: Hình 1; §5: vì sao vận hành LLM trên GPU khó; §6: ba yêu cầu kéo nhau); mô tả tổng |
| 1.3 Mục tiêu, phạm vi và giả định | Bài toán §9 (bảy mục tiêu của đề cương), §11, §12 (phạm vi, giả định G1–G7); mô tả tổng; ADR-002, ADR-004 |
| 1.4 Phương pháp và tổ chức thực hiện | Kế hoạch §1, §2 (lịch, mốc, kế hoạch tuần), §5.1 (phân công), §7 (quy trình làm việc); CONTRIBUTING §7 (PR, CI); `docs/adr/`; nhật ký họp; cách trình bày: `quy-tac-viet.md` §2.2 |
| 1.5 Đóng góp, 1.6 Cấu trúc luận văn | Ba thông điệp TĐ1–TĐ3 (Kế hoạch §11.1); số ở §3 dưới đây |
| 2.1 Phục vụ LLM và vLLM | Kiến thức nền §1, §2; LT1–LT3 trong `VH` (phần lý thuyết) |
| 2.2 Hàng đợi và năng lực phục vụ | Bài toán §3; LT5 trong `VH` (phần lý thuyết) |
| 2.3 GPU trên Kubernetes | Kiến thức nền §4; LT6 trong `VH` (phần lý thuyết) |
| 2.4 Autoscaling trên Kubernetes | Kiến thức nền §3; LT7 trong `VH` (phần lý thuyết) |
| 2.5 Vận hành theo SLO và GitOps | Kiến thức nền §5; LT8 trong `VH` (phần lý thuyết) |
| 2.6 Giải pháp liên quan | Kiến thức nền §6; `tai-lieu.bib` |

### Chương 3

| Mục | Nguồn |
|---|---|
| 3.1 Yêu cầu và chỉ tiêu nghiệm thu | Thông số §3–§6 (§6: giá trị SLO); Bài toán §8–§10 (ma trận truy vết); bảng mã định danh: `quy-tac-viet.md` §4 |
| 3.2 Kiến trúc tổng thể | Kiến trúc §1–§5, §18; Vận hành §7–§9 (dựng lại, bảo mật, chi phí); Môi trường §1–§3 (hai tầng dùng chung manifest); Thông số §10; ADR-004 §7; ADR-006 C2, §3.1; Hình 2, 3, 6 |
| 3.3 Thiết kế autoscaling | Kiến trúc §6, §9–§16; Thông số §8, §9; ADR-006 C7 (truy vấn A1); Hình 4, 14, 15 |
| 3.4 Cold start và thay đổi an toàn | Kiến trúc §3, §7, §8; Vận hành §5; ADR-005; Hình 5, 12, 13, 16 |
| 3.5 Giám sát, cảnh báo, xử lý sự cố | **Đã có bản nháp**: [`03-05-giam-sat-slo-canh-bao.md`](03-05-giam-sat-slo-canh-bao.md) (viết theo dàn ý cũ; khi viết lại thì thêm phần xử lý sự cố và chuyển giá trị SLO sang 3.1); Kiến trúc §17; Vận hành §1–§4, §6; Hình 7 |
| 3.6 Thiết kế đánh giá | Môi trường §7–§17, §19; Thông số §7, §8; Bài toán §9 (chỉ số của đề cương); cách chấm cảnh báo và page giả: `analysis/vh6_window.py`, LT8 |

### Chương 4

| Mục | Nguồn |
|---|---|
| 4.1 Hạ tầng và cluster | `Q-03` (23/10: k3s bằng Ansible); `Q-05` (02/11: IP Tailscale; 06/11: dựng lại sau cài lại OS); `phien-2026-11-08-a4000.md` §2–§7; `Q-06` (09/11: tự động hoá VM); `Q-07` (16/11: `vast.sh attach`); sự cố 23/10, 02/11, 05/11 trong `VH`; mã: `ansible/`, `envs/cloud/provision/` |
| 4.1 GitOps, CI, bí mật | `T-04` (TR1 CI); `T-06` (15/11: app `autoscaling`, `observability`); `Q-05` (06/11: Argo CD tiếp quản nhà); `Q-07` (16/11: Argo CD mất đồng bộ sau refactor); ADR-006 §3.1 (lược Sealed Secrets) |
| 4.1 Bảo mật tối thiểu | Vận hành §8; ADR-006 §3.1 (lược NetworkPolicy, rate limit); API key không có → 401 (Kế hoạch §3, M1) |
| 4.1 Dựng lại từ máy trắng | Vận hành §7; VH5 (`Q-07` 18/11) |
| 4.2 Phục vụ vLLM trên GPU | `Q-03` (vLLM trên 5060, chốt image `v0.31.0`); `Q-05` (06/11: time-slicing, 2 pod chung GPU, overlay `cloud-3b`); sự cố hết RAM 06/11 trong `VH`; mã: `common/serving/`, `envs/*/serving/` |
| 4.3 Autoscaling | `T-04`, `T-05` (TR2: T1–T5, A1/A3/A4, ma trận); `Q-05` (04/11: vòng autoscaling trên kind); `Q-06` (09/11: sửa truy vấn A1); mã: `common/autoscaling/` |
| 4.4 Rút ngắn cold start | `phien-2026-11-08-a4000.md` §6, §9; `VH` 08/11 và LT4 (16/11); `Q-07` (16/11: LT4 page cache nguội/ấm; 18–19/11: `dg3.sh`, L0/L2); mã: `envs/cloud/provision/dg3.sh`, `parse_vllm_log` (`T-05` 08/11) |
| 4.5 Scale-down và cập nhật không rớt request | Graceful shutdown (`Q-05` 06/11, `VH` 06/11); ADR-005; Vận hành §5; `VH` 09/11 (VH2 trên kind), 16/11 (VH2a N = 2); `Q-07` (19/11: vh2a/b/c trên N = 4) |
| 4.6 Giám sát và SLO | `T-05` (TR3: 3 dashboard); `common/observability/` |
| 4.6 Cảnh báo và runbook | `T-03` (TR4: 7 quy tắc, promtool, runbook); `T-06` (Telegram, `KedaScalerErrors`); `docs/runbooks/` |
| 4.6 Sự cố và tự phục hồi | Các mục sự cố trong `VH`; VH3 (`Q-07` 19/11); image vLLM bị GC (`Q-07` 16/11) |
| 4.7 Công cụ đánh giá | `T-03`, `T-05` (TR5: loadgen, tiêu chí hợp lệ, `PodWatcher`); runner (`Q-05` 06/11, `Q-06` 09/11); `build_tables` (`T-06`, `T-07`) |
| Kết chương 4 | Kế hoạch §9.3 (R21: cặp vấn đề → cách xử lý → số đo); Bài toán §5, §13 |

### Chương 5–6

| Mục | Nguồn |
|---|---|
| 5.1 Môi trường và điều kiện đo | `Q-07` (18/11: probe, máy 4060 Ti thay A4000, 17/17 lượt hợp lệ); `runs/v2-evidence/` (UUID GPU, `systemd-detect-virt`); Môi trường §4–§6 |
| 5.1 Chi phí | `Q-05` (06/11: khảo sát giá); `phien-2026-11-08-a4000.md` §15; `Q-07` (18/11: giá 1,5 USD/giờ); chi phí thực tế của V2 chưa có (§4) |
| 5.2 Năng lực một replica (ĐG1) | `Q-07` (18/11: bảng ĐG1); [`envs/cloud/experiments/capacity.json`](../../envs/cloud/experiments/capacity.json); `phien-2026-11-08-a4000.md` §12 (ĐG1 thử); LT1–LT3 trong `VH` |
| 5.3 Autoscaling so với tĩnh (C1–C4) | `Q-07` (18/11: bảng 11 ô; 19/11: nguyên nhân lỗi A2 × KB2, pha giảm tải); [`analysis/figures/v2-dg2/`](../../analysis/figures/v2-dg2/) (`runs.csv`, `cells.csv`, `phases.csv`, hình C1–C4); `analysis/dg2_a2.py`; LT5 (phần V2 lấy số ĐG1, `Q-07` 18/11), LT6, LT7 |
| 5.4 Cold start (C5) | `Q-07` (19/11: ĐG3); `runs/v2-vm/dg3-v2-4060ti/*/summary.txt`, `vllm_log.json` (đủ 8 mốc pha) |
| 5.5 VH1–VH3, VH5 | `Q-07` (19/11); `runs/v2-vm/ops-vh*/summary.json`; VH1 trên máy thuê là pha giảm tải của KB2 (dẫn chéo 5.3); VH3 drain chỉ có trên kind (`VH` 09/11) |
| 5.5 VH4, VH6 | VH4: `Q-07` (19/11: fallback 16,8 s), `analysis/vh4_windows.py`; VH6: `analysis/figures/v2-dg2/alerts.csv`, `analysis/vh6_window.py`, LT8; bảng từng lượt và ý đã cắt ngày 24/11: comment đầu file `05-05-kich-ban-van-hanh.md` (trước 24/11 là `05-05b-vh4-vh6.md`), bản đầy đủ ở commit `bc49ff6` |
| 5.5 Graceful shutdown | `VH` 06/11 (144/144 stream; ca đối chứng grace 5 s) |
| 5.6 Tổng hợp | Bảng nghiệm thu: Bài toán (bảng yêu cầu → đánh giá → chỉ số), Thông số §4, số ở §3 dưới đây; bảng LT1–LT8: `VH`, Môi trường §19; khuyến nghị cấu hình: Kiến trúc §16 |
| 5.7 Hạn chế của phép đo | §6 dưới đây |
| 6.1 Kết luận | Ba thông điệp TĐ1–TĐ3 (Kế hoạch §11.1) |
| 6.2 Hạn chế của hệ thống và phạm vi | §6 dưới đây; Bài toán §11, §12; ADR-006 §3.1 |
| 6.3 Hướng phát triển | Kế hoạch §12 (E1–E13); `docs/bao-cao/de-xuat-v3/`; `Q-06` (13–15/11: các hướng nâng cấp) |
| Phụ lục A–F | A: `common/serving/`, `common/autoscaling/`; B: `common/observability/alerts/` (kèm `tests/`); C: `docs/runbooks/`; D: `docs/phien-ban.md`; E: `analysis/figures/v2-dg2/`; F: Kế hoạch §1, §5.1 |
| Slide, video | Kế hoạch §11.2, §11.3 |

## 3. Số liệu đã chốt

Mọi số dưới đây đã có trong nhật ký; cột "Gốc" là nơi đặt vào comment nguồn. Số đo V2: VM 4 × RTX 4060 Ti 16 GB, Qwen2.5-3B, vLLM `v0.31.0`, N = 4.

| Nội dung | Giá trị | Gốc |
|---|---|---|
| ĐG1: năng lực một replica | C = 3,5 req/s; B\* = 46,3; threshold A2 = 37; λ = 4 chỉ đạt SLO 28,5 % | `Q-07` 18/11; `envs/cloud/experiments/capacity.json` |
| ĐG2: số lượt | 17/17 hợp lệ, 11 ô, khoảng 24 phút/lượt | `Q-07` 18/11 |
| A2 × KB1 | SLO 100 %, GPU-giờ −75 % so với S4 | `Q-07` 18/11 |
| A2 × KB2 | SLO 79,4–80,7 %; 37 / 82 / 93 lỗi (đều `Timeout`, pha spike); phản ứng 79,7–81,5 s; hồi phục 409–430 s | `Q-07` 18/11, 19/11; phản ứng: `analysis/figures/v2-dg2/runs.csv` (`react_s`) |
| A2 × KB2, nguyên nhân | Pod có sẵn giữ hàng đợi tối đa 416–428 request khoảng 385–390 s; pod mới 0–9; Service chia đều | `Q-07` 19/11 |
| A1 | Lên 4 replica cả ở KB1; GPU-giờ chỉ −5 đến −10 % | `Q-07` 18/11 |
| S1 (tĩnh 1 replica) | KB2 SLO 12,5 %, KB3 0 % | `Q-07` 18/11 |
| Scale-down (N4, VH1) | Pha `drop` của 5 lượt KB2: 0 lỗi, SLO 100 % | `Q-07` 19/11 |
| ĐG3 cold start | L2 = 76 / 76 / 81 s (TB 77,7 s); L0 = 311 / 300 s, kéo image 9,04 GB khoảng 2 phút 35 giây | `Q-07` 19/11 |
| VH2 | vh2a 141,4 s (từ 1 replica), vh2b 371,6 s (4 pod, `maxSurge: 0`), vh2c kẹt Pending đúng dự đoán; 0 lỗi | `Q-07` 19/11 |
| VH3 | vh3-delete thay pod 67,4 s, 0 lỗi; vh3-kill 129 lỗi / 1.041 request (xem Hạn chế) | `Q-07` 19/11 |
| VH4 | Fallback lên max replica sau 16,8 s (N6 ≤ 30 s) | `Q-07` 19/11 |
| VH5 | Từ máy trắng tới vLLM Ready 8 phút 22 giây (bootstrap 5 phút 8 giây), **bấm tay**, chưa phải `make vh5` | `Q-07` 18/11 |
| Graceful shutdown ở nhà | 144/144 stream trong 3 lần; đối chứng grace 5 s cắt 48/48; an toàn nhờ grace 180 s, không phải nhờ drain | `VH` 06/11 |
| Phiên V0+V1 (A4000) | ĐG1 thử C = 4,5 req/s; dựng VM 12,5 phút; chi phí khoảng 1,5 USD | `phien-2026-11-08-a4000.md` |
| LT5–LT8 | Kết quả và hình | `VH` phần LT5–LT8; `analysis/figures/` |

## 4. Chưa có: không được viết số

- **Chi phí thực tế V2:** chờ Quang đọc trang Billing của Vast. Hiện chỉ có giá 1,5 USD/giờ.
- **ADR-003** (chốt C, B\*, SLO, threshold): chưa viết; số đã có ở `capacity.json`.
- **Hình C1–C4 trên V2:** đã có ở `analysis/figures/v2-dg2/`, chưa xem lại bố cục. **C5** (cold start 8 pha) và **C6** (VH2): chưa có script.
- **Bảng nghiệm thu F1–F7, N1–N8:** chưa điền. Nhật ký 19/11 đã đánh giá N1, N2a, N3 (KB1), N4, N6; N2b chỉ báo cáo.
- **VH5 ở nhà do Trình dựng lại** (N8), **VH6 tổng hợp**, **T6, T7**, **checklist bảo mật**: chưa làm.
- **Phần V2 của LT1, LT5, LT6:** mới có số trong nhật ký, chưa đưa vào `van-hanh.md`.
- **Tin cảnh báo tới Telegram trong V2:** suốt các lượt có `AlertmanagerFailedToSendAlerts`, chưa rõ nguyên nhân; không khẳng định cảnh báo đã tới Telegram trong V2.
- **Nguyên nhân vLLM 0.31.0 không dừng khi nhận SIGTERM:** chưa tìm.

## 5. Lấy dữ liệu V2

`runs/` không nằm trong Git. Quang gửi riêng file `v2-data-20261119.tar.gz` (khoảng 9,5 MB; gồm `dg1-v2-4060ti/`, `v2-vm/`, `v2-evidence/`) kèm file `.sha256`. Trong `v2-evidence/` có log Ansible chứa IP máy thuê (máy đã xoá): không đăng file này công khai.

```bash
# Từ gốc repo. Kiểm file nén, giải nén vào runs/, rồi kiểm từng file.
sha256sum -c v2-data-20261119.tar.gz.sha256
tar -xzf v2-data-20261119.tar.gz -C runs/
(cd runs && sha256sum -c --quiet v2-evidence/SHA256SUMS)
# Kỳ vọng đúng 1 dòng FAILED: v2-evidence/vm-final-state.txt được ghi 3 s sau khi lập danh sách checksum (02:05:02 so với 02:04:59 ngày 19/11).

# Bảng (đã có sẵn trong runs/v2-vm/v2-dg2/tables/) và hình C1–C4:
uv run --project analysis python -m analysis.build_tables runs/v2-vm/v2-dg2 --baseline S4
uv run --project analysis python -m analysis.charts runs/v2-vm/v2-dg2 --baseline S4
```

Ngày 20/11, lệnh `analysis.charts` trên đã chạy được, ra 6 hình: `c1-kb2-cloud-r1..r3`, `c2-slo-cloud`, `c3-gpu-cloud`, `c4-tradeoff-cloud`. Các hình chưa được xem lại bố cục.

## 6. Hạn chế đã biết (để viết mục 5.7 và 6.2)

| Hạn chế | Gốc |
|---|---|
| Máy đánh giá là 4 × RTX 4060 Ti, không phải 4 × A4000 như ADR-006 C2; C = 3,5 chỉ đúng với máy này | `Q-07` 18/11 |
| A2 không đạt SLO dưới spike KB2: load balancing của Service không biết hàng đợi của từng pod | `Q-07` 19/11 |
| Mỗi ô ma trận chỉ 1–3 lượt | `Q-07` 18/11 |
| vh3-kill có lẽ chạy khi chỉ có 1 pod, nên lỗi cả cluster trong 67 s; chưa kiểm số pod lúc kill | `Q-07` 19/11 |
| L0 đo 0 → 1 pod thay vì 1 → 2 (containerd không xoá được image đang dùng); theo `trigger_unix`, 2 trong 3 lượt L2 chạy sau L0-2 (L2-2 chạy trước), không phải cả 3 như nhật ký ghi | `Q-07` 18/11, 19/11; `summary.txt` |
| ĐG3 xoá page cache trước mọi lượt, nên L2 (75,7–80,8 s) chậm hơn pod mới của A2 × KB2 (65–66 s); chỉ khoảng 6,7 s của khoảng chênh được giải thích (nạp weights); chưa tách phần import trong pha khởi động tiến trình (52,7–56,8% cold start L2); không đo tốc độ đĩa của VM nên LT4 chưa kiểm được phần định lượng; L0 chỉ 2 lượt | `05-04-cold-start.md` (nguồn trong comment) |
| Không sao lưu R2 trong phiên; runner chạy trong tmux với `--no-backup` | `Q-07` 18/11 |
| `metadata.json` của ĐG2 ghi commit `10c0527` dù tree có hai file ma trận chưa commit; `vh.py` dùng bản PR #46 chưa merge | `Q-07` 18/11 |
| vLLM không dừng khi nhận SIGTERM, pod giữ GPU đủ grace 180 s | `VH` 06/11 |
| Cluster nhà một node; drain node (VH3) chỉ thử trên kind | Kế hoạch §5.1, `VH` 09/11 |
| `LLMErrorRateHigh` nhạy với đợt lỗi ngắn ở tải thấp; chưa có dead man's switch | `T-07` 18/11 |
| VH4 chính thức chỉ một lượt, ở 0,5 C: chưa thử mất tín hiệu lúc tải cao; NetworkPolicy chỉ mô phỏng gói tin bị bỏ; Prometheus vẫn trả lời mà mất metric vLLM thì không có fallback, không có cảnh báo từ KEDA; fallback giữ đủ 4 GPU suốt lúc mất tín hiệu, và theo cấu hình thêm ít nhất 300 s chờ scale-down (tính từ `stabilizationWindowSeconds`, chưa đo vì tải dừng 305 s sau gỡ chặn); chưa chạy ở nhà | `runs/v2-vm/ops-vh4-*/summary.json`; Kiến trúc §13.4; `scaledobject-a2.yaml` |
| VH6 chỉ chấm được `LLMSLOBurnFast`: cảnh báo về pod chỉ có unit test (`KedaScalerErrors` thêm một lần chặn trên simulator 15/11); `LLMErrorRateHigh` không kiểm được vì máy tạo tải không qua Traefik; thời gian tới page dựa trên một lượt S1 × KB3, cả 7 page đều ở tỷ lệ xấu cao, vùng 20–23% chưa đo (LT8: x ≳ 0,23 mới chắc dưới 5 phút); chưa chạy ở nhà | `runs.csv`, `alerts.csv`; `VH` mục LT8 |
| Cảnh báo lỗi gửi tin đi qua chính đường đang hỏng: `AlertmanagerFailedToSendAlerts` ở mức warning nên không gửi, bản critical gửi tới Telegram; chưa có bước gửi tin thử hay dừng bước dựng khi thiếu Secret (cho 6.2) | `alerts.csv`; `alertmanager-secret.sh`; nhật ký Quang tuần 07 mục 18/11 |
| Lược Sealed Secrets, NetworkPolicy, rate limit, Argo CD trên VM | ADR-006 §3.1 |
