# Việc sắp làm – Quang

> Cập nhật 29/10/2026 (W4), cuối phiên. Danh sách sống: đánh dấu `[x]` khi xong, ghi chi tiết vào nhật ký tuần. Mã việc theo [Kế hoạch §5.1](../../../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công).

## 1. Tình trạng hiện tại

**Cả dự án (so với kế hoạch):** M1 (18/10) chưa đạt. Trên `main` mới có tài liệu, cảnh báo + runbook (TR4) và máy tạo tải v1 (TR5) của Trình, cả hai chưa chạy trên cluster. Chưa có Argo CD, Prometheus, simulator, CI, V0; **chưa chốt cloud** (hạn 18/10). V1 theo lịch là 31/10–01/11 nhưng chưa có runner.

**Phần của Quang:**

| Mã | Đã xong | Còn lại | Ước tính |
|---|---|---|---|
| Q1 Hạ tầng nhà | k3s trên PC bằng Ansible (idempotent), device plugin, GPU exporter (áp tay); PR A sẵn sàng | Laptop agent (kiểm driver ≥ 580), PodMonitor GPU, giao cho Argo CD | ~70 % |
| Q2 Cloud | Khung `vast.sh`, overlay `cloud` (chỉ ở `temp/w2-scaffold`, chưa chạy) | Chốt cloud, `make bootstrap`, V0 | ~10 % |
| Q3 Serving | vLLM v0.31.0 chạy trên k3s nhà, ghim digest, API key, Ingress, streaming; PR B sẵn sàng | PodMonitor, chuyển sang Argo CD | ~75 % |
| Q4 Cold start | Số đo sơ bộ 486 / 167 / 155 s; compile cache trên hostPath | Pre-pull, đo 8 pha, L0/L2 | ~15 % |
| Q5 Vòng đời pod | Drain và đối chứng trong Docker (W1) | Test trong k8s, rolling update, VH1–VH3 | ~10 % |
| Q6 Runner, ĐG1 | – | Toàn bộ | 0 % |
| Q7 VH5, chi phí | – | Toàn bộ (W5) | 0 % |
| Q8 LT1–LT4 | LT2 có kết quả (lệch < 0,01 %); LT1 có dự đoán | LT1 đo batch = 1; LT3, LT4 | ~35 % |

Phần trăm là ước lượng theo đầu việc, không phải giờ đã dùng.

**Nhánh của Quang** (chưa push, xếp chồng):

| Nhánh | PR | Base | Nội dung |
|---|---|---|---|
| `feat/home-k3s` | A (Q1) | `main` | Ansible k3s, `platform/gpu/`, ghim vLLM v0.31.0, sửa `make lint` |
| `feat/serving` | B (Q3) | `feat/home-k3s` | `serving/` |
| `docs/quang-w4` | C (tài liệu) | `feat/serving` | Nhật ký tuần 04, LT1–LT2, danh sách này, ghi chú `w2.md` |
| `feat/argocd-lab` | không mở PR | – | Bài thực hành Argo CD cá nhân (`lab/argocd/`) |

## 2. Làm ngay, không cần GPU

- [x] Tách `feat/serving` thành PR A + B; `make lint` xanh trên cả hai (29/10).
- [x] LT2 có kết quả, LT1 có dự đoán (29/10).
- [x] Dọn nhánh local, gom nhật ký tuần 04 về một nhánh (29/10).
- [ ] **Push và mở PR A, B** (máy dev chưa có đăng nhập GitHub, phải push từ terminal của Quang):
  - `git push -u origin feat/home-k3s` và `git push origin feat/serving`;
  - PR A: `main` ← `feat/home-k3s`; PR B: `feat/home-k3s` ← `feat/serving`; gán Trình review;
  - merge A xong thì đổi base của B sang `main`; merge B xong thì push và mở PR C (`docs/quang-w4`).
- [ ] **Chốt với Trình** (họp ngắn, ghi vào `docs/nhat-ky/tuan-04.md`):
  - [ ] Cloud: Vast hay GCP (ADR-004 K6, trễ từ 18/10).
  - [ ] V1: dời hay bỏ. Không có runner thì V1 không đạt mục đích; có thể gộp V0 + V1 thành một phiên ngắn để kiểm VM, driver ≥ 580, `fio`, TPOT.
  - [ ] V2 giữ 07–08/11 hay dời 14–15/11 theo Kế hoạch §8 (mất phiên dự phòng).
  - [ ] Hai thay đổi giao diện Trình chờ Quang đồng ý: `for: 1m` của `LLMErrorRateHigh`; cột `id`, `n_in_target` trong `requests.csv`.
  - [ ] Ai tách `platform/argocd/`, `platform/kube-prometheus-stack/`, `infra/kind/` từ `temp/w2-scaffold` (TR1, TR2, TR3). Docker trên máy Trình đang hỏng, nên Quang có thể dựng simulator trên máy dev.
- [ ] **Q6 runner v1 trên simulator** (việc lớn nhất, đường găng của V2): kind + `llm-d-inference-sim` trên máy dev; runner áp cấu hình, reset, chạy `loadgen`, thu thập, checkpoint. Chưa cần đẩy R2.
- [ ] **Q5 chuẩn bị:** script "30 stream + xoá pod" có ca đối chứng; chạy thử với simulator.
- [ ] **Q5 tìm nguyên nhân:** pod vLLM đang khởi tạo không thoát khi nhận SIGTERM (đọc mã nguồn vLLM v0.31.0 phần shutdown).
- [ ] **Q2:** tách `vast.sh`, overlay `cloud`, Ansible cho VM sang nhánh `feat/cloud`; kiểm cú pháp.
- [ ] **Q4:** manifest pre-pull (giới hạn ghi vì ổ SATA của PC).
- [ ] Dọn nhánh trên GitHub (đã merge hoặc bỏ): `dev`, `plan`, `feat/project-structure`, `feat/tr4-alerts`, `feat/tr5-loadgen`. Hỏi Trình trước với hai nhánh của Trình.

## 3. Cần PC bật (làm qua Tailscale, chép `~/.kube/llm-home.yaml` sang máy dev trước)

- [ ] **LT1:** `kubectl exec` vào pod vLLM, `vllm bench serve --max-concurrency 1 --num-prompts 20` (random 512/256, `--ignore-eos`); kiểm băng thông bằng `nvidia-smi -q`.
- [ ] **LT2 phần còn lại:** dòng memory profiling trong `kubectl logs`; `nvidia-smi` để kiểm giả thuyết +11.040 token KV; `vllm:kv_cache_usage_perc` lúc tải cao.
- [ ] **Q5:** test graceful shutdown với vLLM thật (3 lần + ca đối chứng).
- [ ] **Q6:** ĐG1-mini → `capacity-home.json` (chế độ `CONST` của `loadgen`); dữ liệu này cũng dùng cho LT3.
- [ ] **Q4:** L2 và đo 8 pha (cần `parse_vllm_log` của TR5); LT4.
- [ ] TTFT trên k3s cao hơn Docker (p50 +18 %): đo lại gọi thẳng Service, bỏ Ingress.

## 4. Cần ngồi cạnh máy

- [ ] Laptop 4050 vào cluster: kiểm driver ≥ 580, sửa SSH host key, thêm vào `k3s_agent`. Cần cho VH2, KB2-mini, LT1 phần 4050.
- [ ] Quyết định ổ SATA của PC: giữ + giới hạn ghi khi kéo image, hay chuyển `/var/lib/rancher` / cache model sang NVMe. Ảnh hưởng VH5 và L0.

## 5. Sau đó (W5 trở đi)

- [ ] Q5: rolling update theo ADR-005 + VH2 (gồm ca 1 replica, ca đối chứng VH2c); VH1, VH3.
- [ ] Q8: LT3 (batching, từ ĐG1-mini).
- [ ] Q7: script VH5, sổ chi phí. Nạp tiền Vast trước 06/11 nếu giữ V2 07–08/11.
- [ ] Q6: ĐG1 trên V2 → `capacity.json`, ADR-003.
- [ ] Viết phần của Quang ở chương 2–3.

## 6. Phụ thuộc vào Trình

| Việc của Quang | Cần từ Trình |
|---|---|
| PodMonitor vLLM và GPU, số đo từ Prometheus | kube-prometheus-stack (TR3) |
| Serving qua Argo CD | Argo CD + App-of-Apps (TR1) |
| Đo 8 pha (Q4) | `parse_vllm_log` (TR5) |
| Runner (Q6) | File ma trận, ScaledObject A1–A4 (TR2); review PR A, B |
