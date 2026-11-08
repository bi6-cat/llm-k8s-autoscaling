<!-- Mục đích: bảng duy nhất ghim phiên bản mọi thành phần (yêu cầu N8). Tham khảo: docs/huong-dan/w2.md §2.3 -->
# Phiên bản đã ghim

Tra ngày 09/10/2026; các dòng của CI tra ngày 01/11/2026. Đổi phiên bản: sửa ở đây và ở file dùng nó trong cùng một PR.

| Thành phần | Phiên bản | Dùng ở |
|---|---|---|
| Ubuntu (PC, laptop) | PC: 26.04.1 LTS (bản desktop, ghi ngày 23/10); laptop: 24.04 LTS | – |
| NVIDIA driver PC / laptop | PC: `595.99.02` (open) / laptop: (điền từ `nvidia-smi`). **Cần ≥ 580** cho image vLLM CUDA 13 | – |
| NVIDIA Container Toolkit | PC: `1.20.1` / laptop: (điền từ `nvidia-ctk --version`) | role `nvidia` |
| k3s | `v1.36.5+k3s1` (kênh stable) | `infra/ansible/inventory/group_vars/all.yaml` |
| Argo CD | `v3.5.4` (`core-install.yaml`) | `group_vars/all.yaml` |
| kube-prometheus-stack (chart) | `92.1.1` | `platform/argocd/apps/home/monitoring.yaml`, `Makefile` |
| KEDA (chart) | `2.21.0` | `platform/argocd/apps/home/keda.yaml`, `Makefile` |
| NVIDIA device plugin (chart) | `0.20.1`; ở nhà thêm time-slicing 2 GPU replica (`device-plugin-values-home.yaml`, từ 06/11) | `platform/argocd/apps/home/gpu-device-plugin.yaml`, `platform/gpu/` |
| nvidia_gpu_exporter | `1.15.1` | `platform/gpu/exporter/daemonset.yaml` |
| vLLM | `vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd…c3` (CUDA 13.0, cần driver ≥ 580). Không dùng `-cu129`: hỏng lúc khởi động, xem [ADR-004 §7](adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md#7-cập-nhật-sau-ngày-08102026) | `serving/base/kustomization.yaml` |
| Model nhà | `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775` (tra 06/11). Trước 06/11: `Qwen2.5-1.5B-Instruct@989aa798…06`, dùng cho LT1–LT3 và `capacity-home.json` | `serving/overlays/home` |
| Model cloud (V2) | `Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1` (tra 06/11; chốt cho V2 ngày 08/11) | `serving/overlays/cloud-3b` |
| Model cloud (7B, không dùng cho V2) | `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28` | `serving/overlays/cloud` |
| vastai (CLI) | `vastai@1.11.0`, chạy qua `uvx --python 3.12` (Python 3.14 không build được pillow, 06/11) | `infra/provision/vast.sh` |
| llm-d-inference-sim | `ghcr.io/llm-d/llm-d-inference-sim:v0.12.0@sha256:c6838d86…60` (linux/amd64, tra 04/11) | `serving/overlays/sim/kustomization.yaml` |
| kind / node image | `v0.33.0` / `kindest/node:v1.37.0@sha256:a1ed56cf…0ae5` | máy simulator; image ở `infra/kind/kind-config.yaml` |
| Helm, kubectl (máy simulator) | `v4.3.1`, `v1.36.5` (= kubectl của CI) | `make sim-up` |
| kubeconform (CI) | `v0.8.0` | `.github/workflows/ci.yaml` |
| kubectl (CI) | `v1.36.5`, trùng k3s | `.github/workflows/ci.yaml` |
| Schema CRD cho kubeconform | `datreeio/CRDs-catalog` commit `5a706a68…` (01/11/2026) | `.github/workflows/ci.yaml` |
| promtool (CI) | `3.15.0`, trùng Prometheus của chart kube-prometheus-stack 92.1.1 | `.github/workflows/ci.yaml` |
| yq, bản của mikefarah (CI và `make alerts-coverage`) | `v4.54.1` | `.github/workflows/ci.yaml`; máy cá nhân cài cùng bản |
| yamllint (CI) | `1.38.0`; phụ thuộc giải theo mốc 01/11/2026 (PyYAML 6.0.3, pathspec 1.1.1) | `.github/workflows/ci.yaml` |
| actionlint, shellcheck, lychee (CI) | `1.7.12`, `0.11.0`, `0.24.2` | `.github/workflows/ci.yaml` |
| uv, Python (CI cho `loadgen/`) | `0.13.1`; Python `3.11` và `3.15` | `.github/workflows/ci.yaml` |
| GitHub Actions | `actions/checkout@v7.0.1`, `astral-sh/setup-uv@v10.3.2`, ghim theo commit SHA | `.github/workflows/ci.yaml` |
