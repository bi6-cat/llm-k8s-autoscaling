# llm-k8s-autoscaling

Đồ án tốt nghiệp: *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling*. Phục vụ mô hình ngôn ngữ lớn (vLLM) trên Kubernetes, tự tăng giảm số GPU theo tải (KEDA/HPA), giám sát bằng Prometheus, triển khai bằng GitOps (Argo CD).

Trọng tâm: khoảng 70 % xây dựng và vận hành (IaC, GitOps, autoscaling, SLO, cảnh báo, runbook), 30 % đánh giá để nghiệm thu, kèm kiểm chứng lý thuyết LT1–LT8.

**Đọc nhanh cho người không trực tiếp làm:** báo cáo kỹ thuật có hình và biểu đồ ở [docs/bao-cao/](docs/bao-cao/).

## Repo chia theo hai câu hỏi

```text
envs/            CHẠY Ở ĐÂU: mỗi môi trường một thư mục, có README hướng dẫn chạy từ đầu đến cuối
├── home/        PC ở nhà (RTX 5060 8 GB), k3s + Argo CD          → demo, vận hành thử
├── cloud/       VM thuê trên Vast.ai (4 × RTX A4000 16 GB)        → phiên đánh giá V2
└── sim/         kind + simulator trên laptop, không cần GPU       → kiểm thử autoscaling nhanh
common/          CHẠY CÁI GÌ: manifest giống nhau ở mọi môi trường (vLLM, A2, cảnh báo, dashboard)
ansible/         dựng k3s từ máy trắng (dùng cho home và cloud)
loadgen/         máy tạo tải (Python)
experiments/     runner chạy ma trận đánh giá, kịch bản vận hành VH2–VH4 (Python)
docs/            thiết kế, quyết định (ADR), runbook, nhật ký, báo cáo
```

Mỗi thư mục trong `envs/<env>/` chỉ chứa **phần khác biệt** của môi trường đó (model nào, bao nhiêu GPU, cách cài) và chồng lên `common/`. Vì vậy cùng một Deployment vLLM, cùng một cấu hình autoscaling A2 và cùng bộ cảnh báo chạy ở cả ba nơi; kết quả đo ở nơi này có ý nghĩa cho nơi kia. Chi tiết từng thư mục: [CONTRIBUTING §1](CONTRIBUTING.md#1-thư-mục).

| Muốn chạy | Đọc | Lệnh đầu tiên |
|---|---|---|
| Demo ở nhà trên GPU thật | [envs/home/README.md](envs/home/README.md) | `make home-up` |
| Phiên đánh giá trên máy thuê | [envs/cloud/README.md](envs/cloud/README.md) | `make find MODE=v2` |
| Thử autoscaling không cần GPU | [envs/sim/README.md](envs/sim/README.md) | `make sim-up` |

`make help` in mọi lệnh, chia nhóm theo đúng ba môi trường trên.

## Đọc gì tiếp

| Muốn | Đọc |
|---|---|
| Hiểu đồ án trong 10 phút | [Bản mô tả](docs/mo-ta-chi-tiet-do-an.md) |
| Thông số, ngưỡng, phiên bản | [Thông số và chỉ tiêu](docs/chi-tiet/00-thong-so.md), [Phiên bản đã ghim](docs/phien-ban.md) |
| Vì sao chọn như vậy | [Quyết định (ADR)](docs/adr/), mới nhất là [ADR-006](docs/adr/006-chot-may-model-va-kich-ban-truoc-v2.md) |
| Ai làm gì, khi nào | [Kế hoạch §5.1 (phân công)](docs/chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công), [§2 (lịch tuần)](docs/chi-tiet/06-ke-hoach-quan-ly.md#2-kế-hoạch-từng-tuần) |
| Viết code, đặt file, mở PR | [CONTRIBUTING.md](CONTRIBUTING.md) · Quy tắc cho AI agent (gồm ghi nhật ký): [AGENTS.md](AGENTS.md) |

## Tái lập

Dàn ý theo [Kế hoạch §10.7](docs/chi-tiet/06-ke-hoach-quan-ly.md#107-hướng-dẫn-tái-lập-và-vận-hành-dàn-ý-readme). Lệnh chi tiết của từng môi trường nằm trong README của môi trường đó.

1. **Yêu cầu.** Máy có GPU NVIDIA (ở nhà) hoặc tài khoản Vast.ai (máy thuê); không có GPU thì dùng simulator. Công cụ: `kubectl`, `helm`, `ansible`, `uv` (Python), `make`, `vastai` CLI cho máy thuê, Tailscale để nối cluster nhà; simulator cần thêm Docker, `kind`, `hey`. Phiên bản: [docs/phien-ban.md](docs/phien-ban.md).
2. **Chạy nhanh.** Ở nhà: `make home-up`, rồi chạy runner theo [envs/home/README.md](envs/home/README.md) (`--matrix envs/home/experiments/matrix.yaml`). Không có GPU: `make sim-up`, rồi runner theo [envs/sim/README.md](envs/sim/README.md) (`--matrix envs/sim/experiments/matrix.yaml`).
3. **Phiên đánh giá trên máy thuê.** Mười bước từ `make find MODE=v2` tới `make backup-check && make release`, gồm ĐG1, ma trận ĐG2 và kịch bản vận hành: [envs/cloud/README.md](envs/cloud/README.md#một-phiên-đầy-đủ). File `.env` cần template Vast, khoá R2 và bot Telegram.
4. **Vận hành.** Cập nhật phiên bản và rollback: [Vận hành §5.3](docs/chi-tiet/04-van-hanh.md#53-quy-trình-cập-nhật-qua-gitops). Xử lý cảnh báo: [docs/runbooks/](docs/runbooks/). Dựng lại từ đầu: [Vận hành §7](docs/chi-tiet/04-van-hanh.md#7-dựng-lại-từ-đầu-khôi-phục-sau-thảm-hoạ).
5. **Tái tạo bảng và hình từ dữ liệu.** `make analysis` đọc dữ liệu từ `runs/` (bảng ĐG2 ghi trước vào `runs/v2-vm/v2-dg2/tables/`, rồi chép sang), ghi đè `analysis/figures/`: 4 bảng và biểu đồ C1–C4 của ĐG2, số phụ của mục 5.3 và VH4, VH6, bảng và hình LT5–LT8. Sau đó `git status --short analysis/figures` sạch nghĩa là mọi file tái lập đúng từng byte. Ghi ra chỗ khác: `make analysis OUT=<thư mục>`. Bộ dữ liệu công bố (`dataset/`, dùng bằng `make analysis DATA=dataset`) đóng gói bằng `analysis/dataset.py`, chưa đăng ([dataset/README.md](dataset/README.md)). Chưa nằm trong lệnh này: bảng cold start 8 pha của ĐG3 (runner ghi `summary.txt` trong từng lượt) và hình trong `docs/images/` (mục [Sơ đồ](#sơ-đồ)).
6. **Phiên bản đã dùng.** Bảng phiên bản đã ghim của image, chart và công cụ (image chính kèm digest): [docs/phien-ban.md](docs/phien-ban.md).
7. **Lỗi thường gặp.**

   | Lỗi | Xem |
   |---|---|
   | Argo CD đặt lại `replicas` mà HPA vừa đổi | [Kiến trúc §18.3](docs/chi-tiet/03-kien-truc-autoscaling.md#183-cạm-bẫy-argo-cd-và-hpa-tranh-nhau-replicas) |
   | Prometheus không nhận PodMonitor thiếu label `release` | [Kiến trúc §17.1](docs/chi-tiet/03-kien-truc-autoscaling.md#171-thu-thập) |
   | vLLM lỗi khi thiếu `/dev/shm` | [Thông số §9.2](docs/chi-tiet/00-thong-so.md#92-deployment-vllm) |
   | Metric GPU khác tên và label giữa DCGM và `nvidia_gpu_exporter` | [Kiến trúc §17.1](docs/chi-tiet/03-kien-truc-autoscaling.md#171-thu-thập), [§13.3](docs/chi-tiet/03-kien-truc-autoscaling.md#133-a1-a3-a4-chỉ-khác-phần-triggers) |
   | Ngưỡng TTFT không trùng biên bucket của histogram | [Thông số §6](docs/chi-tiet/00-thong-so.md#6-slo) |
   | `--shutdown-timeout` không giữ được request khi scale-down | [Thông số §9.1](docs/chi-tiet/00-thong-so.md#91-vllm) |

## Kiểm tra trước khi mở PR

```bash
make lint alerts-test dashboards-check          # YAML, kustomize, Ansible, rule Prometheus, dashboard
uv run --project experiments pytest experiments # và tương tự cho loadgen, analysis
```

CI (`.github/workflows/ci.yaml`) chạy cùng các lệnh này trên mọi PR.

## Sơ đồ

[docs/images/](docs/images/) (SVG) · [docs/images/png/](docs/images/png/) (PNG 2× cho Word/slide). Tạo lại: `python3 docs/diagrams/build_diagrams.py && bash docs/diagrams/export_png.sh`.
