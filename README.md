# llm-k8s-autoscaling

Đồ án tốt nghiệp: *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling* (vLLM + KEDA/HPA + Prometheus trên Kubernetes).

Trọng tâm: khoảng 70% xây dựng và vận hành (IaC, GitOps, autoscaling, SLO, cảnh báo, runbook), 30% đánh giá để nghiệm thu, kèm kiểm chứng lý thuyết LT1–LT8.

## Đọc gì trước

| Muốn | Đọc |
|---|---|
| Hiểu đồ án trong 10 phút | [Bản mô tả](docs/mo-ta-chi-tiet-do-an.md) |
| Bắt tay làm tuần này | Hướng dẫn tuần: [W1](docs/huong-dan/w1.md), [W2](docs/huong-dan/w2.md) |
| Biết ai làm gì, khi nào | [Kế hoạch §5.1 (phân công)](docs/chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công), [§2 (lịch tuần)](docs/chi-tiet/06-ke-hoach-quan-ly.md#2-kế-hoạch-từng-tuần) |
| Thông số, ngưỡng, phiên bản | [Thông số và chỉ tiêu](docs/chi-tiet/00-thong-so.md), [Phiên bản đã ghim](docs/phien-ban.md) |
| Vì sao chọn như vậy | [Quyết định (ADR)](docs/adr/) và [bộ tài liệu thiết kế](docs/mo-ta-chi-tiet-do-an.md#bộ-tài-liệu) |
| Viết code, đặt file, mở PR | [CONTRIBUTING.md](CONTRIBUTING.md) · Quy tắc cho AI agent (gồm ghi nhật ký): [AGENTS.md](AGENTS.md) |

## Lệnh thường dùng

```bash
make help        # danh sách lệnh
make home-up     # dựng k3s + Argo CD ở nhà (Ansible)
make sim-up      # dựng simulator trên laptop (kind, không cần GPU)
make lint        # kiểm tra trước khi mở PR
```

## Sơ đồ

[docs/images/](docs/images/) (SVG) · [docs/images/png/](docs/images/png/) (PNG 2× cho Word/slide). Tạo lại: `python3 docs/diagrams/build_diagrams.py && bash docs/diagrams/export_png.sh`.
