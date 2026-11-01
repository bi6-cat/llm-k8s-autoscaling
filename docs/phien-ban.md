<!-- Mục đích: bảng duy nhất ghim phiên bản mọi thành phần (yêu cầu N8). Tham khảo: docs/huong-dan/w2.md §2.3 -->
# Phiên bản đã ghim

Tra ngày 09/10/2026; các dòng của CI tra ngày 01/11/2026. Đổi phiên bản: sửa ở đây và ở file dùng nó trong cùng một PR.

| Thành phần | Phiên bản | Dùng ở |
|---|---|---|
| Ubuntu (PC, laptop) | 24.04 LTS server | – |
| NVIDIA driver PC / laptop | (điền từ `nvidia-smi`) | – |
| NVIDIA Container Toolkit | (điền từ `nvidia-ctk --version`) | role `nvidia` |
| k3s | `v1.36.5+k3s1` (kênh stable) | `infra/ansible/inventory/group_vars/all.yaml` |
| Argo CD | `v3.5.4` (`core-install.yaml`) | `group_vars/all.yaml` |
| kube-prometheus-stack (chart) | `92.1.1` | `platform/argocd/apps/home/monitoring.yaml`, `Makefile` |
| KEDA (chart) | `2.21.0` | `platform/argocd/apps/home/keda.yaml`, `Makefile` |
| NVIDIA device plugin (chart) | `0.20.1` | `platform/argocd/apps/home/gpu-device-plugin.yaml` |
| nvidia_gpu_exporter | `1.15.1` | `platform/gpu/exporter/daemonset.yaml` |
| vLLM | `vllm/vllm-openai:v0.31.0-cu129@sha256:ff29e51a…eeb` | `serving/base/kustomization.yaml` |
| Model nhà | `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | `serving/overlays/home` |
| Model cloud | `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28` | `serving/overlays/cloud` |
| llm-d-inference-sim | `v0.12.0` | `serving/overlays/sim` |
| kind / node image | `v0.33.0` / `kindest/node:v1.37.0` | laptop; image ở `infra/kind/kind-config.yaml` |
| kubeconform (CI) | `v0.8.0` | `.github/workflows/ci.yaml` |
| kubectl (CI) | `v1.36.5`, trùng k3s | `.github/workflows/ci.yaml` |
| Schema CRD cho kubeconform | `datreeio/CRDs-catalog` commit `5a706a68…` (01/11/2026) | `.github/workflows/ci.yaml` |
| promtool (CI) | `3.15.0`, trùng Prometheus của chart kube-prometheus-stack 92.1.1 | `.github/workflows/ci.yaml` |
| yq, bản của mikefarah (CI và `make alerts-coverage`) | `v4.54.1` | `.github/workflows/ci.yaml`; máy cá nhân cài cùng bản |
| yamllint (CI) | `1.38.0`; phụ thuộc giải theo mốc 01/11/2026 (PyYAML 6.0.3, pathspec 1.1.1) | `.github/workflows/ci.yaml` |
| actionlint, shellcheck, lychee (CI) | `1.7.12`, `0.11.0`, `0.24.2` | `.github/workflows/ci.yaml` |
| uv, Python (CI cho `loadgen/`) | `0.13.1`; Python `3.11` và `3.15` | `.github/workflows/ci.yaml` |
| GitHub Actions | `actions/checkout@v7.0.1`, `astral-sh/setup-uv@v10.3.2`, ghim theo commit SHA | `.github/workflows/ci.yaml` |
