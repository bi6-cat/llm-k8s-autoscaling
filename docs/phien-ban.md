<!-- Mục đích: bảng duy nhất ghim phiên bản mọi thành phần (yêu cầu N8). Tham khảo: docs/huong-dan/w2.md §2.3 -->
# Phiên bản đã ghim

Tra ngày 09/10/2026. Đổi phiên bản: sửa ở đây và ở file dùng nó trong cùng một PR.

| Thành phần | Phiên bản | Dùng ở |
|---|---|---|
| Ubuntu (PC, laptop) | PC: 26.04.1 LTS (bản desktop, ghi ngày 23/10); laptop: 24.04 LTS | – |
| NVIDIA driver PC / laptop | PC: `595.99.02` (open) / laptop: (điền từ `nvidia-smi`). **Cần ≥ 580** cho image vLLM CUDA 13 | – |
| NVIDIA Container Toolkit | PC: `1.20.1` / laptop: (điền từ `nvidia-ctk --version`) | role `nvidia` |
| k3s | `v1.36.5+k3s1` (kênh stable) | `infra/ansible/inventory/group_vars/all.yaml` |
| Argo CD | `v3.5.4` (`core-install.yaml`) | `group_vars/all.yaml` |
| kube-prometheus-stack (chart) | `92.1.1` | `platform/argocd/apps/home/monitoring.yaml`, `Makefile` |
| KEDA (chart) | `2.21.0` | `platform/argocd/apps/home/keda.yaml`, `Makefile` |
| NVIDIA device plugin (chart) | `0.20.1` | `platform/argocd/apps/home/gpu-device-plugin.yaml` |
| nvidia_gpu_exporter | `1.15.1` | `platform/gpu/exporter/daemonset.yaml` |
| vLLM | `vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd…c3` (CUDA 13.0, cần driver ≥ 580). Không dùng `-cu129`: hỏng lúc khởi động, xem [ADR-004 §7](adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md#7-cập-nhật-sau-ngày-08102026) | `serving/base/kustomization.yaml` |
| Model nhà | `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | `serving/overlays/home` |
| Model cloud | `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28` | `serving/overlays/cloud` |
| llm-d-inference-sim | `v0.12.0` | `serving/overlays/sim` |
| kind / node image | `v0.33.0` / `kindest/node:v1.37.0` | laptop; image ở `infra/kind/kind-config.yaml` |
| kubeconform (CI) | `v0.8.0` | `.github/workflows/ci.yaml` |
| GitHub Actions | `actions/checkout@v7`, `lycheeverse/lychee-action@v2` | `.github/workflows/ci.yaml` |
