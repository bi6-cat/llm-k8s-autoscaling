# llm-k8s-autoscaling

Đồ án tốt nghiệp: *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling*. Phục vụ mô hình ngôn ngữ lớn (vLLM) trên Kubernetes, tự tăng giảm số GPU theo tải (KEDA/HPA), giám sát bằng Prometheus, triển khai bằng GitOps (Argo CD).

Trọng tâm: khoảng 70 % xây dựng và vận hành (IaC, GitOps, autoscaling, SLO, cảnh báo, runbook), 30 % đánh giá để nghiệm thu, kèm kiểm chứng lý thuyết LT1–LT8.

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

## Kiểm tra trước khi mở PR

```bash
make lint alerts-test dashboards-check          # YAML, kustomize, Ansible, rule Prometheus, dashboard
uv run --project experiments pytest experiments # và tương tự cho loadgen
```

CI (`.github/workflows/ci.yaml`) chạy cùng các lệnh này trên mọi PR.

## Sơ đồ

[docs/images/](docs/images/) (SVG) · [docs/images/png/](docs/images/png/) (PNG 2× cho Word/slide). Tạo lại: `python3 docs/diagrams/build_diagrams.py && bash docs/diagrams/export_png.sh`.
