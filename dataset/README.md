# Bộ dữ liệu đánh giá autoscaling vLLM trên Kubernetes

Dữ liệu thô mà chương 5 của luận văn dùng: phiên đánh giá chính V2 trên VM thuê (18–19/11/2026) và các lượt trên simulator kind (07–24/11/2026). Trong Git chỉ có file này. Phần dữ liệu (khoảng 38 MB, 853 file) do `analysis/dataset.py` đóng gói từ `runs/` và **chưa được đăng**.

## Nội dung

Bố cục giữ nguyên như `runs/` trên máy đã đo, nên `make analysis DATA=dataset` đọc thẳng được (Makefile, target `analysis`). Giờ ghi theo giờ Việt Nam (UTC+7).

| Thư mục | Là gì | Ngày, máy | Dùng ở |
|---|---|---|---|
| `dg1-v2-4060ti/` | ĐG1: năng lực 1 replica, tải hằng 2; 3; 3,5; 4; 5 req/s (S1-CONST…), `capacity.json` | 18/11, V2 | 5.2, LT5, LT6 |
| `v2-vm/v2-dg2/` | ĐG2: ma trận 17 lượt (S1, S4, A1, A2 × KB1–KB3), `tables/` là 4 bảng do `analysis/build_tables.py` dựng | 18/11, V2 | 5.3, 5.4, VH6 |
| `v2-vm/dg3-v2-4060ti/` | ĐG3: cold start L0, L2 (`summary.txt` 8 pha, log vLLM, event). Ba thư mục `*-failed-wait-count-bug` là lượt hỏng do lỗi hàm `wait_count` của `dg3.sh`, giữ lại làm bằng chứng, không dùng để tính | 18–19/11, V2 | 5.4 |
| `v2-vm/ops-vh*/` | VH2a–c, VH3 (xoá pod, kill tiến trình), VH4 (chặn Prometheus) | 18/11, V2 | 5.5 |
| `v2-vm/*.log`, `*.sh` | Console của runner và script đã chạy trên VM | 18–19/11, V2 | Bằng chứng |
| `v2-evidence/` | Cấu hình đúng bản đã chạy (ma trận, diff, commit), console `make probe` và ĐG1, Node k3s, phần cứng (`vm-identity.txt`), checksum gốc trên VM | 18/11, V2 | Bằng chứng |
| `sim/mp-final-w2/`, `sim/tr7-kb2-sim-2/` | LT5 trên simulator (S1 tải hằng; S1 và A2 với KB2) | 07/11 và 16/11, kind | LT5 |
| `sim/lt7-20261116-165323/` | LT7: tốc độ rescale của HPA, 4 mức đồng thời × 3 lượt | 16/11, kind | LT7 |
| `sim/lt8-20261116-131116/` | LT8: burn rate, tỷ lệ request xấu 10, 30, 60 % × 3 lượt | 16/11, kind | LT8 |
| `ops-vh2-git-20261124-171557/` | VH2 qua Git (Argo CD): lượt chính, 615 request, 0 lỗi | 24/11, kind | 4.5, 5.5 |
| `ops-vh2-git-20261124-164415/` | VH2 qua Git: lượt thử trước lượt chính | 24/11, kind | 4.5 |
| `INDEX.csv` | Mỗi lần thử của runner một dòng (cột ở dưới) | | |
| `SHA256SUMS` | Checksum mọi file, kể cả README này | | |

- **V2:** VM thuê trên Vast.ai, 4 × RTX 4060 Ti 16 GB, k3s v1.36.5, vLLM v0.31.0, model Qwen2.5-3B-Instruct ([Môi trường §3](../docs/chi-tiet/05-moi-truong-danh-gia.md), [ADR-006](../docs/adr/006-chot-may-model-va-kich-ban-truoc-v2.md)).
- **kind:** cluster kind trong WSL2 trên PC, vLLM thay bằng `llm-d-inference-sim` (tên model phục vụ `qwen2.5-1.5b`). Đồng hồ đơn điệu trong WSL2 chạy nhanh hơn giờ thực; `analysis/lt5_little.py` hiệu chỉnh khi tính LT5.

## Định dạng file

**Lượt của runner** (`<phiên>/<run-id>/attempt-N/`): `metadata.json`, `requests.csv`, `loadgen.json`, `metrics.csv.gz`, `events.jsonl`, `alerts.jsonl`, `pods_*.json`, `logs/<pod>.log`, `checks.json`. Ý nghĩa từng file và từng cột của `requests.csv` ở [Môi trường §14.2](../docs/chi-tiet/05-moi-truong-danh-gia.md#142-dữ-liệu-của-một-lượt). Tóm tắt cột `requests.csv`: `id`, `t_sched`, `t_send`, `t_first`, `t_last` (giây kể từ `t0_unix` trong `loadgen.json`), `n_in_target`, `n_in`, `n_out`, `status`, `error` (rỗng = thành công). `metrics.csv.gz` dạng dài: `ts`, `name`, `labels` (JSON), `value`.

**Kịch bản vận hành** (`ops-vh*/`, do `experiments/ops/vh.py` ghi): `timeline.json` (các mốc `t`, `event`, theo giây UNIX), `summary.json` (đạt hay không, lý do, số request và lỗi, các số đo của kịch bản), `load/` (`requests.csv`, `loadgen.json` cùng định dạng trên; `ops.log` là log của máy tạo tải).

**ĐG3** (`dg3-v2-4060ti/<mức>-<lần>/`, do `envs/cloud/provision/dg3.sh` ghi): `summary.txt` (mốc tạo pod, kéo image, container chạy, Ready, `trigger_to_ready_s`), `vllm.log` và `vllm_log.json` (mốc từng pha trong log vLLM), `events.json`, `pod.json`, ảnh chụp cache và image trước, sau lượt.

**LT7** (`c<đồng thời>-r<lần>/`): `meta.json` (tham số), `hpa.json`, `hpa-rescale.log` (dòng "Successfully rescaled" của controller-manager), `prom-running.json`, `prom-waiting.json` (kết quả range query của Prometheus), `events.json`, `pods.json`, `hey.txt`, `clock-changes.jsonl`. Tính bảng bằng `analysis/lt7_hpa.py`.

**LT8** (`rep<lần>/`): `meta.json` (lịch các mức request xấu), `timeline.json`, `prom.json`, `load/`. Tính bảng bằng `analysis/lt8_burn.py`.

**`INDEX.csv`:** `path` (thư mục lần thử), `session`, `env` (`cloud`, `sim`), `run_id`, `attempt`, `config` (S1, S4, A1, A2), `scenario` (CONST, KB1–KB3), `rate_rps` (tải hằng của CONST), `capacity_rps` (năng lực tham chiếu C mà KB1–KB3 nhân hệ số), `t_begin_local`, `model`, `valid` (theo `checks.json`, [Môi trường §17](../docs/chi-tiet/05-moi-truong-danh-gia.md)).

## Cách dùng

```bash
# Kiểm checksum (hoặc: uv run --project analysis python -m analysis.dataset --check dataset)
cd dataset && sha256sum -c SHA256SUMS
# Dựng lại mọi bảng, hình và số của chương 5 vào một thư mục tạm, rồi so với bản trong Git
make analysis DATA=dataset OUT=/tmp/figures && diff -r /tmp/figures analysis/figures
```

`make analysis` ghi lại `dataset/v2-vm/v2-dg2/tables/` đúng từng byte, nên checksum vẫn khớp sau khi chạy.

## Cách đóng gói

```bash
uv run --project analysis python -m analysis.dataset runs --out dataset --env-file .env
```

Script chép các phiên trong `SESSIONS` (bỏ `figures/` vì dựng lại được, file khoá `.lock` của runner, và log Ansible của `make bootstrap` vì ghi kèm địa chỉ máy thuê). Trước khi chép, script quét mọi file, kể cả `.gz`, tìm token Telegram, token Hugging Face, khoá riêng, chứng chỉ kubeconfig, khoá truy cập, IP công khai, email, và đúng các giá trị trong `.env`; thấy chỗ nào thì dừng, không chép gì, chỉ in tên file và số dòng. Sau đó ghi `INDEX.csv` và `SHA256SUMS`.

## Giấy phép và quyền riêng tư

- Dữ liệu phát hành theo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): được dùng, sửa, phân phối lại, kể cả cho mục đích thương mại, với điều kiện ghi nguồn (nhóm đồ án autoscaling LLM trên Kubernetes, 2026).
- Không có dữ liệu cá nhân: prompt là văn bản tổng hợp do máy tạo tải sinh ([Kế hoạch §10.6](../docs/chi-tiet/06-ke-hoach-quan-ly.md#106-dữ-liệu-đánh-giá-và-nhật-ký-vận-hành)). Tên pod, IP nội bộ của cluster (10.x) và UUID GPU còn trong dữ liệu; chúng không dùng được để truy cập hệ thống nào.
