#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# infra/provision/install-platform.sh
# Khái niệm: Cài phần nền lên k3s của VM thuê bằng Helm (trình quản lý gói cho Kubernetes): device plugin
#            (báo GPU cho scheduler), kube-prometheus-stack (Prometheus, Grafana), KEDA (autoscaler), GPU
#            exporter, rồi vLLM. Chạy NGAY trên VM: `vast.sh platform` chép các file vào cùng thư mục này.
# Mục đích:  Thay các bước làm tay ngày 08/11 (236 s cho phần nền). Trên cloud chưa dùng Argo CD
#            (group_vars/cloud.yaml), nên đây là cách cài; cùng values với Application ở nhà. Chạy trên VM
#            vì tunnel SSH từng đứt khi phản hồi lớn. Chạy lại an toàn: `helm upgrade --install`, `apply`.
#            In mốc thời gian từng bước làm số đo cho VH5.
# Tham khảo: log phiên 08/11 §7; docs/phien-ban.md (phiên bản chart, phải trùng Application ở nhà)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
t0=$(date +%s)
step() { echo "[$(date -u +%T) +$(( $(date +%s) - t0 ))s] $*"; }
K="k3s kubectl"
# Tạo namespace nếu chưa có: `create --dry-run | apply` không báo lỗi khi đã tồn tại, khác `create` thuần.
ns() { $K create namespace "$1" --dry-run=client -o yaml | $K apply -f - >/dev/null; }

step "helm"
if ! command -v helm >/dev/null; then
  curl -fsSL -o /tmp/helm.tgz https://get.helm.sh/helm-v3.19.0-linux-amd64.tar.gz   # bản đã chạy ở V1
  tar -xzf /tmp/helm.tgz -C /tmp
  install /tmp/linux-amd64/helm /usr/local/bin/helm
fi
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin --force-update >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update >/dev/null
helm repo add kedacore https://kedacore.github.io/charts --force-update >/dev/null

step "device plugin 0.20.1"
# --wait: chỉ sang bước sau khi pod Ready, để lỗi hiện ngay tại bước gây ra nó
helm upgrade --install nvdp nvdp/nvidia-device-plugin --version 0.20.1 -n nvidia-device-plugin \
  --create-namespace -f device-plugin-values.yaml --wait --timeout 5m

step "kube-prometheus-stack 92.1.1"
ns monitoring
# Secret Grafana phải có TRƯỚC chart (values đọc từ Secret). Chỉ tạo một lần để chạy lại không đổi mật khẩu.
$K -n monitoring get secret grafana-admin >/dev/null 2>&1 || \
  $K -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin --from-literal=admin-password="$(openssl rand -hex 12)"
helm upgrade --install kps prometheus-community/kube-prometheus-stack --version 92.1.1 -n monitoring \
  -f kps-values.yaml --wait --timeout 10m
$K apply -f kps-extras.yaml

step "KEDA 2.21.0"
helm upgrade --install keda kedacore/keda --version 2.21.0 -n keda --create-namespace \
  -f keda-values.yaml --wait --timeout 5m

step "GPU exporter"
# Lưu ý: thiếu namespace `gpu` thì apply lỗi; ở nhà Argo CD tự tạo, trên VM thì không (gặp 08/11).
ns gpu
$K apply -f gpu-exporter.yaml

step "vLLM"
ns llm-serving
# Secret chỉ tạo một lần. Không in giá trị khoá ra log; runner tự đọc từ Secret này.
$K -n llm-serving get secret vllm-api-key >/dev/null 2>&1 || \
  $K -n llm-serving create secret generic vllm-api-key --from-literal=key="$(openssl rand -hex 24)"
$K apply -f serving.yaml

step "xong"
$K get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu,CPU:.status.allocatable.cpu,MEM:.status.allocatable.memory
$K get pods -A --no-headers | awk '{print $1,$2,$4}' | column -t
