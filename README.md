# llm-k8s-autoscaling

Đồ án tốt nghiệp: *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling* (vLLM + KEDA/HPA + Prometheus/DCGM trên Kubernetes).

Trọng tâm: khoảng 70% xây dựng và vận hành (IaC, GitOps, autoscaling, SLO, cảnh báo, runbook), 30% đánh giá để nghiệm thu.

- Bản mô tả chi tiết (tiếng Việt, kèm sơ đồ): [docs/mo-ta-chi-tiet-do-an.md](docs/mo-ta-chi-tiet-do-an.md)
- Tài liệu chuyên sâu: [docs/chi-tiet/](docs/chi-tiet/README.md) · Quyết định: [docs/adr/](docs/adr/)
- Sơ đồ: [docs/images/](docs/images/) (SVG) · [docs/images/png/](docs/images/png/) (PNG 2× cho Word/slide)
- Tạo lại sơ đồ: `python3 docs/diagrams/build_diagrams.py && bash docs/diagrams/export_png.sh`
