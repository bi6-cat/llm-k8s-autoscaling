# llm-k8s-autoscaling

Đồ án tốt nghiệp: *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling* (vLLM + KEDA/HPA + Prometheus trên Kubernetes).

Trọng tâm: khoảng 70% xây dựng và vận hành (IaC, GitOps, autoscaling, SLO, cảnh báo, runbook), 30% đánh giá để nghiệm thu.

- Bản mô tả (tiếng Việt, kèm sơ đồ, gửi GVHD): [docs/mo-ta-chi-tiet-do-an.md](docs/mo-ta-chi-tiet-do-an.md)
- Tài liệu thiết kế và kế hoạch: [docs/chi-tiet/](docs/mo-ta-chi-tiet-do-an.md#bộ-tài-liệu), bắt đầu từ [Thông số và chỉ tiêu](docs/chi-tiet/00-thong-so.md) · Quyết định: [docs/adr/](docs/adr/) · Review: [docs/review/](docs/review/)
- Sơ đồ: [docs/images/](docs/images/) (SVG) · [docs/images/png/](docs/images/png/) (PNG 2× cho Word/slide)
- Tạo lại sơ đồ: `python3 docs/diagrams/build_diagrams.py && bash docs/diagrams/export_png.sh`
