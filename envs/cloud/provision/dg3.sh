#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# envs/cloud/provision/dg3.sh
# Khái niệm: ĐG3 = đo cold start (thời gian từ lúc ra lệnh thêm pod tới lúc pod mới Ready) ở hai mức tối ưu
#            (Kiến trúc §7.1): L0 = node "trắng" (không có image, không có model, không có compile cache, nên
#            phải kéo image ~10 GB và tải model từ Internet); L2 = cấu hình vận hành (image đã có trên node,
#            model trên NVMe, compile cache đã ấm). Cả hai đều xả page cache của RAM trước khi đo, để lần
#            nạp weights không đọc từ RAM (Kiến trúc §7.4 cạm bẫy 1).
# Mục đích:  Đo L0 và L2 đều tay, ghi đủ dữ liệu thô (pod JSON, event, log vLLM có mốc kubelet) để tách 8 pha
#            bằng experiments/runner/vllm_log.py, làm số liệu cho C5 và N5 (Môi trường §12).
#            Chạy TRÊN VM (cần crictl và quyền ghi /proc/sys/vm/drop_caches), với quyền root.
#            Khác Môi trường §12 ở L0: containerd không cho xoá image đang được container dùng, nên L0 scale
#            vLLM về 0, xoá image và cache, rồi đo 0 → 1 (không phải 1 → 2). L2 đo đúng 1 → 2.
# Dùng:      KUBECONFIG=/etc/rancher/k3s/k3s.yaml envs/cloud/provision/dg3.sh L2 1
#            → runs/dg3-v2-4060ti/L2-1/{summary.txt, pod.json, events.json, vllm.log, vllm_log.json, …}
#            Phải không có ScaledObject trong llm-serving (KEDA sẽ tự đổi số replica giữa lúc đo).
# Tham khảo: Môi trường §12; Kiến trúc §7.1, §7.2, §7.4; Thông số §8.3 (L0 × 2, L2 × 3)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../../.."

LEVEL=${1:?L0 hoặc L2}
REP=${2:?số lần lặp, ví dụ 1}
NS=llm-serving
DEPLOY=vllm
CACHE=/mnt/nvme/cache          # hostPath của volume cache (envs/cloud/serving/patch-vllm.yaml)
OUT="runs/dg3-v2-4060ti/$LEVEL-$REP"
TIMEOUT_S=1500                  # L0 gồm kéo image ~10 GB + tải model 6 GB; dư nhiều
[ -e "$OUT" ] && { echo "$OUT đã có; không ghi đè lượt đã đo" >&2; exit 2; }
mkdir -p "$OUT"
exec > >(tee "$OUT/console.log") 2>&1   # mọi output của script vào console.log (bằng chứng phiên đo)

log() { echo "$(date -u +%FT%T.%3NZ) $*"; }
ready_pods() {  # tên các pod vLLM đang Ready, mỗi dòng một tên
  kubectl -n "$NS" get pod -l app=vllm -o json |
    jq -r '.items[] | select(.metadata.deletionTimestamp == null)
           | select(any(.status.conditions[]?; .type == "Ready" and .status == "True")) | .metadata.name'
}
all_pods() { kubectl -n "$NS" get pod -l app=vllm -o name | wc -l; }
wait_count() {  # chờ tới khi số pod (kể cả Terminating) đúng $1
  local want=$1 t=0
  while [ "$(all_pods)" -ne "$want" ]; do
    sleep 5; t=$((t + 5))
    if [ $t -gt 900 ]; then log "quá 900 s chờ $want pod"; exit 1; fi
  done
  # Phải trả 0 tường minh: bản 18/11 kết thúc vòng lặp bằng `[ … ] && { … }`, điều kiện sai trả 1, nên
  # hàm trả 1 và `set -e` dừng script mỗi khi phải chờ ít nhất một vòng (3/5 lượt ĐG3 đầu tiên hỏng).
  return 0
}

if kubectl -n "$NS" get scaledobject -o name 2>/dev/null | grep -q .; then
  log "còn ScaledObject trong $NS: xoá trước (KEDA sẽ đổi số replica giữa lúc đo)"; exit 2
fi
IMAGE=$(kubectl -n "$NS" get deploy "$DEPLOY" -o jsonpath='{.spec.template.spec.containers[0].image}')
log "ĐG3 $LEVEL lần $REP; image $IMAGE"

if [ "$LEVEL" = L2 ]; then
  kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=1
  wait_count 1
  kubectl -n "$NS" wait --for=condition=Ready pod -l app=vllm --timeout=900s
  BEFORE=$(ready_pods)
  WANT=2
elif [ "$LEVEL" = L0 ]; then
  kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=0
  log "chờ mọi pod vLLM tắt (grace period 180 s)"
  wait_count 0
  # Xoá image theo đúng tham chiếu digest mà pod dùng; kiểm lại là đã hết
  crictl rmi "$IMAGE" || true
  if crictl images --digests | grep -q "${IMAGE##*@sha256:}"; then log "image vẫn còn trên node"; exit 1; fi
  rm -rf "${CACHE:?}/hf/"* "${CACHE:?}/vllm/"*
  log "đã xoá image, model (hf/) và compile cache (vllm/); còn lại: $(du -sh "$CACHE" | cut -f1)"
  BEFORE=""
  WANT=1
else
  echo "LEVEL phải là L0 hoặc L2" >&2; exit 2
fi

crictl images --digests > "$OUT/images-before.txt"
du -sh "$CACHE"/hf "$CACHE"/vllm > "$OUT/cache-before.txt" 2>&1 || true
sync; echo 3 > /proc/sys/vm/drop_caches
free -m > "$OUT/free-after-drop.txt"

T_TRIGGER=$(date +%s.%N)
log "TRIGGER scale → $WANT"
kubectl -n "$NS" scale deploy "$DEPLOY" --replicas="$WANT"

# Pod mới = pod không có trong danh sách trước khi scale
NEW=""
for _ in $(seq 1 60); do
  NEW=$(kubectl -n "$NS" get pod -l app=vllm -o json |
    jq -r --arg before "$BEFORE" '.items[] | select(.metadata.deletionTimestamp == null)
      | .metadata.name | select(. as $n | ($before | split("\n") | index($n)) | not)' | head -1)
  [ -n "$NEW" ] && break; sleep 1
done
[ -n "$NEW" ] || { log "không thấy pod mới"; exit 1; }
log "pod mới $NEW"
if ! kubectl -n "$NS" wait --for=condition=Ready "pod/$NEW" --timeout="${TIMEOUT_S}s"; then
  log "pod mới không Ready trong $TIMEOUT_S s"
fi
T_READY_SEEN=$(date +%s.%N)

kubectl -n "$NS" get pod "$NEW" -o json > "$OUT/pod.json"
kubectl -n "$NS" get events --field-selector "involvedObject.name=$NEW" -o json > "$OUT/events.json"
kubectl -n "$NS" logs "$NEW" --timestamps > "$OUT/vllm.log"
crictl images --digests > "$OUT/images-after.txt"
uv run --project experiments python -m experiments.runner.vllm_log "$OUT/vllm.log" > "$OUT/vllm_log.json" || true

READY_AT=$(jq -r '.status.conditions[] | select(.type=="Ready") | .lastTransitionTime' "$OUT/pod.json")
STARTED_AT=$(jq -r '.status.containerStatuses[0].state.running.startedAt // empty' "$OUT/pod.json")
{
  echo "level=$LEVEL rep=$REP pod=$NEW image=$IMAGE"
  echo "trigger_unix=$T_TRIGGER"
  echo "ready_seen_unix=$T_READY_SEEN"
  echo "pod_created=$(jq -r .metadata.creationTimestamp "$OUT/pod.json")"
  echo "container_started=$STARTED_AT"
  echo "pod_ready=$READY_AT"
  echo "trigger_to_ready_s=$(echo "$(date -d "$READY_AT" +%s) - ${T_TRIGGER%.*}" | bc)"
  echo "restarts=$(jq -r '.status.containerStatuses[0].restartCount' "$OUT/pod.json")"
  echo "pull_events:"; jq -r '.items[] | select(.reason=="Pulling" or .reason=="Pulled") | "  \(.lastTimestamp) \(.reason): \(.message)"' "$OUT/events.json"
} | tee "$OUT/summary.txt"

# Trả về 1 replica cho lượt sau (L2 bắt đầu từ 1 pod; L0 tự scale về 0)
kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=1
log "xong $OUT"
