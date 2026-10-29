# Việc sắp làm – Quang

> Cập nhật 29/10/2026 (W4). Danh sách sống: đánh dấu `[x]` khi xong, ghi chi tiết vào nhật ký tuần. Mã việc theo [Kế hoạch §5.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công).

## 1. Tình trạng hiện tại

**Cả dự án (so với kế hoạch):** M1 (18/10) chưa đạt. Trên `main` mới có tài liệu, cảnh báo + runbook (TR4) và máy tạo tải v1 (TR5) của Trình, cả hai chưa chạy trên cluster. Chưa có Argo CD, Prometheus, simulator, CI, V0; **chưa chốt cloud** (hạn 18/10). V1 theo lịch là 31/10–01/11 nhưng chưa có runner.

**Phần của Quang:**

| Mã | Đã xong | Còn lại | Ước tính |
|---|---|---|---|
| Q1 Hạ tầng nhà | k3s trên PC bằng Ansible (idempotent), device plugin, GPU exporter (áp tay) | Laptop agent (kiểm driver ≥ 580), PodMonitor GPU, giao cho Argo CD | ~70 % |
| Q2 Cloud | Khung `vast.sh`, overlay `cloud` (chỉ ở `temp/w2-scaffold`, chưa chạy) | Chốt cloud, `make bootstrap`, V0 | ~10 % |
| Q3 Serving | vLLM v0.31.0 chạy trên k3s nhà, ghim digest, API key, Ingress, streaming | Merge `feat/serving`, PodMonitor, chuyển sang Argo CD | ~70 % |
| Q4 Cold start | Số đo sơ bộ 486 / 167 / 155 s; compile cache trên hostPath | Pre-pull, đo 8 pha, L0/L2 | ~15 % |
| Q5 Vòng đời pod | Drain và đối chứng trong Docker (W1) | Test trong k8s, rolling update, VH1–VH3 | ~10 % |
| Q6 Runner, ĐG1 | – | Toàn bộ | 0 % |
| Q7 VH5, chi phí | – | Toàn bộ (W5) | 0 % |
| Q8 LT1–LT4 | Đã có số cho LT1 (TPOT 9,3 ms) và LT2 (≈ 28 KB/token) | Viết vào `van-hanh.md`; đo LT3, LT4 | ~20 % |

Code của Q1, Q3 nằm trên nhánh `origin/feat/serving` (7 commit, **chưa mở PR**, merge thử với `main` không xung đột).

## 2. Ưu tiên P0: tuần này (29/10–01/11)

- [ ] **Mở PR `feat/serving` → `main`** (Q1, Q3). Chạy `make lint` trước; Trình review. Lý do: Argo CD đọc từ `main`, phần GitOps của Trình cần manifest serving trên `main`.
- [ ] **Chốt với Trình** (họp ngắn, ghi vào `docs/nhat-ky/tuan-04.md`):
  - [ ] Cloud: Vast hay GCP (ADR-004 K6, trễ từ 18/10).
  - [ ] V1: dời hay bỏ. Không có runner thì V1 không đạt mục đích "runner chạy 2 lượt"; có thể gộp V0 + V1 thành một phiên ngắn để kiểm VM, driver ≥ 580, `fio`, TPOT.
  - [ ] V2 còn giữ 07–08/11 không, hay dời 14–15/11 theo Kế hoạch §8 (mất phiên dự phòng).
  - [ ] Trình đồng ý hai thay đổi giao diện đang chờ Quang: `for: 1m` của `LLMErrorRateHigh`; cột `id`, `n_in_target` trong `requests.csv`.
- [ ] **Q5: test graceful shutdown trong k8s** (30 stream + xoá pod, kèm ca đối chứng `--shutdown-timeout 0`). Trước đó tìm hiểu vì sao pod đang khởi tạo không thoát khi nhận SIGTERM (phải chờ hết `terminationGracePeriodSeconds: 180`).
- [ ] **Q8: viết LT1, LT2** vào `docs/nhat-ky/van-hanh.md` theo mẫu dự đoán → số đo → giải thích (đã có số từ W1 và k3s).
- [ ] **Quyết định ổ SATA của PC**: giữ nguyên + giới hạn ghi khi kéo image, hay chuyển `/var/lib/rancher` / cache model sang NVMe. Ảnh hưởng VH5 và L0.

## 3. Ưu tiên P1: W5 (02–08/11)

- [ ] **Q6 runner** v1: áp cấu hình, reset, chạy máy tạo tải của Trình, thu thập, checkpoint. Bản đầu chạy với cluster nhà, chưa cần đẩy R2.
- [ ] **Q6 ĐG1-mini** ở nhà → `capacity-home.json` (dùng chế độ `CONST` của `loadgen`).
- [ ] **Q4 L2**: pre-pull image (DaemonSet hoặc `crictl` có giới hạn ghi), mount compile cache; đo 8 pha bằng `parse_vllm_log` (TR5 của Trình).
- [ ] **Q2**: tách `vast.sh`, overlay `cloud`, Ansible cho VM ra nhánh `feat/cloud`; `make bootstrap` < 30 phút; chạy phiên V0 nếu đã chốt Vast.
- [ ] **Q1 laptop agent**: kiểm driver ≥ 580, sửa SSH host key, thêm vào nhóm `k3s_agent`. Cần cho VH2 và KB2-mini.
- [ ] **Q5**: rolling update theo ADR-005 + VH2 (gồm ca 1 replica, ca đối chứng VH2c).
- [ ] **Q8**: LT3 (batching), LT4 (cold start).
- [ ] Nạp tiền Vast trước 06/11 (nếu giữ V2 07–08/11).

## 4. P2: trước đóng băng dữ liệu

- [ ] Q5: VH1, VH3 ở nhà.
- [ ] Q7: script VH5 (dựng VM từ máy trắng), sổ chi phí.
- [ ] Q6: ĐG1 trên V2 → `capacity.json`, ADR-003.
- [ ] Viết phần của Quang ở chương 2–3 (LLM inference, vLLM, GPU trên K8s; kiến trúc, serving, vận hành, môi trường).

## 5. Phụ thuộc vào Trình

| Việc của Quang | Cần từ Trình |
|---|---|
| PodMonitor vLLM và GPU, số đo từ Prometheus | kube-prometheus-stack (TR3) |
| Serving qua Argo CD | Argo CD + App-of-Apps (TR1) |
| Đo 8 pha (Q4) | `parse_vllm_log` (TR5) |
| Runner (Q6) | Máy tạo tải chạy được trong cluster, file ma trận, ScaledObject A1–A4 (TR2) |

## 6. Việc lặt vặt còn treo

- [ ] TTFT trên k3s cao hơn Docker W1 (p50 +18 %, p99 +46–57 %): chưa rõ nguyên nhân (Traefik? CPU?). Đo lại gọi thẳng Service, bỏ Ingress.
- [ ] KV-cache trên k3s 112.160 token so với 101.120 trong Docker: tìm nguyên nhân (có thể desktop chiếm ít VRAM hơn).
- [ ] Sửa mục 28/10 ở nhật ký tuần 04 (nhánh `feat/argocd-lab`): ghi "phần k3s của đồ án chưa chạy thật" là sai, k3s đã chạy trên PC từ 23/10.
- [ ] Sau khi `feat/serving` merge: xoá `feat/ansible-k3s` (đã nằm trong `feat/serving`); giữ `temp/w2-scaffold` tới khi tách xong `vast.sh`, `platform/`, `infra/kind/`.
