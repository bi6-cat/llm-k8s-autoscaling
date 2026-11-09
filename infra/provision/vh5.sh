#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# infra/provision/vh5.sh
# Khái niệm: VH5 = kịch bản "dựng lại từ máy trắng": từ VM Ubuntu vừa thuê tới khi API vLLM trả lời được.
# Mục đích:  Bấm giờ từng bước làm số đo cho N6 (≤ 30 phút; Thông số §4) thay vì ghi tay như 08/11. Dừng ngay
#            nếu một bước lỗi, nhưng vẫn giữ file thời gian. Gọi sau `make rent`, thời gian thuê không tính.
# Dùng:      make vh5   → runs/vh5-<thời điểm>/timeline.txt và log từng bước
# Tham khảo: Vận hành §7; Môi trường §13
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT="runs/vh5-$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
T0=$(date +%s)
LIMIT_S=1800   # N6: 30 phút

# Chạy một bước, ghi giây bắt đầu và thời lượng. pipefail nên lỗi của lệnh không bị `tee` che mất.
step() {
  local name=$1 s; shift; s=$(date +%s)
  echo "== $name (+$((s - T0)) s)"
  "$@" 2>&1 | tee "$OUT/$name.log"
  echo "$name start=+$((s - T0))s took=$(( $(date +%s) - s ))s" | tee -a "$OUT/timeline.txt"
}

# Chờ pod vLLM Ready rồi gọi API có streaming từ chính VM. ClusterIP gọi được từ node nên không cần tunnel.
# `stream: true` + đọc dòng `data:` đầu tiên: xác nhận API thật sự sinh token, không chỉ mở cổng.
check_api() {
  local host port
  read -r host port < <(infra/provision/vast.sh target)
  ssh -p "$port" "root@$host" bash -s <<'REMOTE'
set -euo pipefail
K="k3s kubectl -n llm-serving"
$K rollout status deploy/vllm --timeout=900s
ip=$($K get svc vllm -o jsonpath='{.spec.clusterIP}')
key=$($K get secret vllm-api-key -o jsonpath='{.data.key}' | base64 -d)
model=$($K get deploy vllm -o yaml | grep -oP -- '--served-model-name=\K\S+')
curl -sN -m 120 "http://$ip:8000/v1/chat/completions" -H "Authorization: Bearer $key" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"$model\",\"stream\":true,\"max_tokens\":8,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}" \
  | grep -m1 '^data:' | cut -c1-120
REMOTE
}

step bootstrap make bootstrap
step platform make cloud-platform
step api check_api

TOTAL=$(( $(date +%s) - T0 ))
echo "total=${TOTAL}s limit=${LIMIT_S}s" | tee -a "$OUT/timeline.txt"
if [ "$TOTAL" -le "$LIMIT_S" ]; then echo "VH5 ĐẠT (N6)"; else echo "VH5 KHÔNG đạt: quá ${LIMIT_S} s"; exit 1; fi
