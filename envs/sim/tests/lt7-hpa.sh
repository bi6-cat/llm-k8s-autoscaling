#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# envs/sim/tests/lt7-hpa.sh
# Khái niệm: LT7 (Môi trường §19) kiểm chứng thuật toán HPA trên simulator (cluster kind):
#            (1) ở mỗi mức tải C, HPA chọn đúng desired = ⌈C ÷ threshold⌉, kẹp vào [min, max] (Kiến thức
#            nền §3.1); (2) trễ phản ứng tách được thành từng chặng: chờ lần scrape kế tiếp (chu kỳ 5 s),
#            chờ chu kỳ sync kế tiếp của HPA (5 s), tạo pod, pod Ready.
# Mục đích:  Thu dữ liệu thô cho LT7 (TR8). Mỗi lượt: đưa về 1 replica bằng annotation tạm dừng của KEDA
#            (cách runner reset giữa các lượt), bơm C request đồng thời trong DUR giây, rồi lưu event của HPA,
#            danh sách pod và mẫu Prometheus thô (mốc scrape tới ms). Phần tính toán nằm ở
#            analysis/lt7_hpa.py (có unit test), file này chỉ đo.
# Dùng:      make sim-lt7 (sau make sim-up), hoặc chọn mức tải: make sim-lt7 LEVELS="15 25" REPS=5 DUR=60
#            Mặc định 4 mức × 3 lần, mỗi lượt khoảng 2 phút, tổng khoảng 25 phút. Xong thì tính bảng:
#            uv run --project analysis python -m analysis.lt7_hpa runs/sim/lt7-<giờ>
# Cần:       kubectl, jq, curl, hey; ScaledObject vllm-a2 (overlay sim). CTX = context kubectl.
# Tham khảo: Môi trường §19 (LT7), Kiến thức nền §3.1, Thông số §9.3, run-t1-t5.sh (cùng cách đọc cấu hình)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../../.."             # về gốc repo

export CTX=${CTX:-kind-llm-sim}        # export: load-sim.sh (tiến trình con) dùng cùng context
K=(kubectl --context "$CTX")
N=(-n llm-serving)
SO=vllm-a2
HPA=keda-hpa-$SO                       # HPA do KEDA tạo (tên = keda-hpa-<tên SO>)
PAUSE=autoscaling.keda.sh/paused-replicas
# Mức tải mặc định, với threshold 10 và max 3 (overlay sim): mong đợi 1 (dưới ngưỡng), 2, 3, và 3 vì
# ⌈35 ÷ 10⌉ = 4 bị kẹp ở max. Không chọn C sát biên tolerance (9 ≤ C ≤ 11): ở đó kết quả còn tuỳ cách HPA so
# số thực với 1 ± 10%, không còn là phép thử công thức. Không chọn C cao hơn: cả tải đi vào MỘT pod (port-forward
# của load-sim.sh chỉ nối tới một pod), và pod simulator từng bị liveness restart khi quá tải (nhật ký 16/11).
LEVELS=${LEVELS:-5 15 25 35}
REPS=${REPS:-3}
# Giây tải mỗi lượt: đủ cho quyết định (≤ 10 s), pod mới Ready (vài giây) và khoảng 8 chu kỳ sync sau đó để
# thấy HPA đứng yên ở số replica mới (không lên thêm, không dao động).
DUR=${DUR:-60}
DUR=${DUR%s}                           # nhận cả 60 lẫn 60s (make sim-test-load viết DUR=180s)
OUT=runs/sim/lt7-$(date +%Y%m%d-%H%M%S)   # runs/ nằm trong .gitignore: dữ liệu thô không commit

so() { "${K[@]}" "${N[@]}" get scaledobject "$SO" -o jsonpath="$1" 2>/dev/null || true; }
hpa() { "${K[@]}" "${N[@]}" get hpa "$HPA" -o jsonpath="$1" 2>/dev/null || true; }   # rỗng khi chưa có HPA
say() { echo "$(date +%T) $*" | tee -a "$OUT/lt7.log"; }
# wait_until <tối đa giây> <lệnh…>: chạy lệnh mỗi giây tới khi nó thành công; hết giờ thì trả mã 1
wait_until() { local limit=$1 t=$SECONDS; shift; until "$@"; do (( SECONDS - t < limit )) || return 1; sleep 1; done; }
# prom <PromQL>: kết quả JSON của một instant query, qua proxy của API server (không cần port-forward).
# @uri (jq): mã hoá câu PromQL để đặt vào URL.
prom() { "${K[@]}" get --raw "$PROM/api/v1/query?query=$(jq -rn --arg q "$1" '$q | @uri')"; }
a2() { prom "$QUERY" 2>/dev/null | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo 0; }
# npods: số pod vLLM chưa kết thúc. Pod đang Terminating vẫn ở phase Running nên vẫn được đếm (phải chờ nó đi
# hẳn); pod Failed (ví dụ bị evict) thì không bao giờ đi, đếm vào thì reset chờ mãi.
npods() {
  "${K[@]}" "${N[@]}" get pods -l "$SEL" --field-selector=status.phase!=Failed,status.phase!=Succeeded \
    --no-headers 2>/dev/null | wc -l
}
# restarts: tổng số lần restart container của mọi pod vLLM. Tăng trong một lượt = pod bị restart giữa chừng
# (tải rơi xuống 0), analysis đánh dấu lượt đó không hợp lệ.
restarts() { "${K[@]}" "${N[@]}" get pods -l "$SEL" -o json | jq '[.items[].status.containerStatuses[]?.restartCount] | add // 0'; }

# Đã về nghỉ: KEDA tạm dừng xong (Paused=True, HPA đã bị xoá), còn đúng 1 pod (pod thừa đã xoá hẳn, không còn
# Terminating), pod đó Ready, và Prometheus thấy A2 = 0 (không còn request dở của lượt trước).
idle_paused() {
  [ "$(so '{.status.conditions[?(@.type=="Paused")].status}')" = True ] && [ -z "$(hpa '{.metadata.name}')" ] \
    && [ "$(npods)" = 1 ] \
    && [ "$("${K[@]}" "${N[@]}" get deploy vllm -o jsonpath='{.status.readyReplicas}' 2>/dev/null)" = 1 ] \
    && [ "$(a2)" = 0 ]
}
# HPA mới đã chạy ít nhất một chu kỳ sync: desired = 1 và đã đọc được metric = 0
hpa_fresh() {
  [ "$(hpa '{.status.desiredReplicas}')" = 1 ] \
    && [ "$(hpa '{.status.currentMetrics[0].external.current.averageValue}')" = 0 ]
}

# reset: về 1 replica ngay, không chờ scale-down tự nhiên (cửa sổ 300 s + 60 s mỗi pod). Tạm dừng thì KEDA xoá
# HPA và đặt Deployment về 1; gỡ tạm dừng thì KEDA tạo HPA MỚI (UID mới). HPA controller xoá trạng thái của
# HPA cũ (đề xuất trong cửa sổ ổn định, lịch sử scale-up), nên mọi lượt bắt đầu từ cùng một trạng thái.
reset() {
  "${K[@]}" "${N[@]}" annotate scaledobject "$SO" "$PAUSE=1" --overwrite >/dev/null
  wait_until 180 idle_paused || { say "không về được 1 replica sau 180 s"; exit 1; }
  "${K[@]}" "${N[@]}" annotate scaledobject "$SO" "$PAUSE-" >/dev/null
  wait_until 60 hpa_fresh || { say "KEDA chưa tạo lại HPA (desired=1, metric=0) sau 60 s"; exit 1; }
}

# run <C> <lần>: một lượt, dữ liệu vào $OUT/c<C>-r<lần>/
run() {
  local c=$1 rep=$2 d uid r0 pid t0 span jitter
  d="$OUT/c$c-r$rep"
  mkdir -p "$d"
  reset
  # Lệch pha ngẫu nhiên trong [0; chu kỳ sync): reset tạo HPA mới, HPA sync lần đầu ngay khi được tạo rồi cứ
  # 5 s một lần. Bơm tải ngay sau reset thì mốc 0 luôn rơi vào cùng một pha của chu kỳ sync, và d_decide
  # không còn đại diện cho tải tới vào lúc bất kỳ (phiên đầu 16/11: d_decide chỉ quanh 3–4 s hoặc 8–9 s).
  jitter=$(awk -v r="$RANDOM" -v p="$SYNC_S" 'BEGIN { printf "%.3f", r / 32768 * p }')
  sleep "$jitter"
  uid=$(hpa '{.metadata.uid}')
  r0=$(restarts)
  say "C=$c lần $rep: tải $DUR s (HPA $uid)"
  envs/sim/tests/load-sim.sh "$c" "${DUR}s" > "$d/hey.txt" 2>&1 &
  pid=$!
  # Mốc 0 = giờ thực lúc hey bắt đầu, tới ms (load-sim.sh in). Event, pod và mẫu Prometheus đều ghi theo giờ
  # thực của cùng một kernel (WSL2, các node kind là container), nên so trực tiếp được với nhau.
  # grep -s: không báo lỗi khi file chưa kịp được tạo (tiến trình nền chưa mở xong file)
  if ! wait_until 20 grep -qs '^load-sim: giờ thực ' "$d/hey.txt"; then
    say "load-sim.sh không bắt đầu tải sau 20 s (xem $d/hey.txt)"; kill "$pid" 2>/dev/null || true; exit 1
  fi
  t0=$(sed -nE 's/^load-sim: giờ thực ([0-9.]+)$/\1/p' "$d/hey.txt")
  # Chụp HPA 5 s trước hạn dừng, khi tải còn đủ: desired và metric lúc này là trạng thái ổn định của mức tải.
  # Chụp sau khi hey thoát thì muộn: hey còn chờ request dở dang tới ~10 s, tải đã giảm dần.
  sleep "$(awk -v t0="$t0" -v d="$DUR" -v now="$(date +%s.%N)" 'BEGIN { s = t0 + d - 5 - now; print (s > 0 ? s : 0) }')"
  "${K[@]}" "${N[@]}" get hpa "$HPA" -o json > "$d/hpa.json"
  wait "$pid" || say "load-sim.sh thoát với lỗi (xem $d/hey.txt)"
  # Event của đúng HPA lượt này (lọc theo UID; HPA của lượt trước cùng tên nhưng khác UID). Event cũ hơn 1 giờ
  # bị xoá (TTL mặc định), nên phải lấy ngay sau mỗi lượt.
  "${K[@]}" "${N[@]}" get events --field-selector "involvedObject.uid=$uid" -o json > "$d/events.json"
  "${K[@]}" "${N[@]}" get pods -l "$SEL" -o json > "$d/pods.json"
  # Mốc quyết định của HPA tới µs: dòng "Successfully rescaled" của kube-controller-manager (event chỉ tới
  # giây). Lấy từ 5 s trước mốc 0; analysis/lt7_hpa.py chỉ giữ dòng nằm trong cửa sổ của lượt này.
  # Đọc log lỗi thì báo, analysis tự quay về event. `|| true` ở grep: lượt không scale (C dưới ngưỡng) thì
  # không có dòng nào và grep trả mã 1.
  if ! "${K[@]}" -n kube-system logs "$KCM" \
       --since-time="$(date -u -d "@$(( ${t0%.*} - 5 ))" +%Y-%m-%dT%H:%M:%SZ)" > "$d/kcm.log"; then
    say "C=$c lần $rep: không đọc được log $KCM, analysis sẽ dùng event (mốc tới giây)"
  fi
  grep '"Successfully rescaled"' "$d/kcm.log" | grep -F "HPA=\"llm-serving/$HPA\"" > "$d/hpa-rescale.log" || true
  rm -f "$d/kcm.log"
  # Các lần chỉnh giờ của máy: trên WSL2, giờ thực bị kéo lùi theo Windows khoảng mỗi 32 s, và systemd-resolved
  # ghi "Clock change detected" ngay sau mỗi lần. journald đóng dấu mỗi dòng bằng cả giờ thực lẫn giờ đơn điệu,
  # nên analysis đổi được mọi mốc giờ thực của lượt sang đồng hồ đơn điệu (MonoClock). Lấy từ 120 s trước mốc
  # 0, để có lần chỉnh trước mốc 0. Máy không có journal hoặc không bị chỉnh giờ: file rỗng, dùng giờ thực.
  journalctl --since="@$(( ${t0%.*} - 120 ))" -o json --no-pager 2>/dev/null \
    | jq -c 'select(.MESSAGE == "Clock change detected. Flushing caches.")
             | {wall_us: .__REALTIME_TIMESTAMP, mono_us: .__MONOTONIC_TIMESTAMP}' > "$d/clock-changes.jsonl" || true
  # Mẫu thô (range vector, không gộp): mỗi lần scrape của mỗi pod một mẫu, mốc = lúc scrape. Lấy từ 15 s
  # trước mốc 0 tới bây giờ.
  span=$(awk -v t0="$t0" -v now="$(date +%s)" 'BEGIN { printf "%d", now - t0 + 15 }')
  for m in running waiting; do
    prom "vllm:num_requests_${m}{namespace=\"llm-serving\"}[${span}s]" > "$d/prom-$m.json"
  done
  jq -n --argjson c "$c" --argjson rep "$rep" --argjson t0 "$t0" --argjson dur "$DUR" \
    --argjson thr "$THRESHOLD" --argjson lo "$MIN" --argjson hi "$MAX" --arg uid "$uid" \
    --arg scrape "$SCRAPE" --arg sync "$SYNC" --argjson r0 "$r0" --argjson r1 "$(restarts)" \
    --argjson jitter "$jitter" \
    '{c: $c, rep: $rep, t0: $t0, dur_s: $dur, threshold: $thr, min_replicas: $lo, max_replicas: $hi,
      hpa_uid: $uid, scrape_interval: $scrape, hpa_sync_period: $sync, jitter_s: $jitter,
      restarts_before: $r0, restarts_after: $r1}' > "$d/meta.json"
  say "C=$c lần $rep: xong, HPA desired=$(jq -r '.status.desiredReplicas' "$d/hpa.json"), restart $r0 → $(jq .restarts_after "$d/meta.json")"
}

# ── Chạy ────────────────────────────────────────────────────────────────────────
for c in kubectl jq curl hey; do command -v "$c" >/dev/null || { echo "thiếu $c"; exit 1; }; done
"${K[@]}" "${N[@]}" get scaledobject "$SO" >/dev/null || { echo "chưa có ScaledObject $SO: chạy make sim-up trước"; exit 1; }

# Thông số lấy từ chính cluster, không viết cứng (như run-t1-t5.sh)
MIN=$(so '{.spec.minReplicaCount}')
MAX=$(so '{.spec.maxReplicaCount}')
THRESHOLD=$(so '{.spec.triggers[0].metadata.threshold}')
[[ $MIN =~ ^[0-9]+$ && $MAX =~ ^[0-9]+$ && $THRESHOLD =~ ^[0-9]+$ ]] \
  || { echo "ScaledObject $SO thiếu minReplicaCount, maxReplicaCount hoặc threshold nguyên"; exit 1; }
(( MIN == 1 )) || { echo "LT7 bắt đầu mỗi lượt từ 1 replica, cần minReplicaCount = 1 (đang là $MIN)"; exit 1; }
# Kiểm tham số trước khi chạy: giá trị sai (DUR=1m, LEVELS="15,25") làm hey thoát ngay hoặc jq lỗi giữa phiên
[[ $DUR =~ ^[0-9]+$ && $REPS =~ ^[0-9]+$ ]] || { echo "DUR (giây) và REPS phải là số nguyên: DUR=$DUR REPS=$REPS"; exit 1; }
(( DUR >= 20 )) || { echo "DUR ≥ 20 s: cần chỗ cho quyết định (≤ 11 s) và ảnh chụp HPA 5 s trước hạn dừng"; exit 1; }
for c in $LEVELS; do [[ $c =~ ^[0-9]+$ ]] || { echo "LEVELS là các số nguyên cách nhau bởi dấu cách: '$LEVELS'"; exit 1; }; done
QUERY=$(so '{.spec.triggers[0].metadata.query}')
# serverAddress dạng http://<service>.<namespace>.svc:<cổng> → đường proxy của API server tới Service đó
PROM=$(so '{.spec.triggers[0].metadata.serverAddress}' \
  | sed -E 's#^http://([^.]+)\.([^.]+)\.svc(\.cluster\.local)?:([0-9]+).*#/api/v1/namespaces/\2/services/http:\1:\4/proxy#')
[[ $PROM == /api/v1/namespaces/* ]] || { echo "serverAddress '$PROM' không có dạng http://<service>.<namespace>.svc:<cổng>"; exit 1; }
prom "$QUERY" 2>/dev/null | jq -e '.status == "success"' >/dev/null \
  || { echo "Không chạy được câu PromQL của $SO qua $PROM (Prometheus chưa sẵn sàng?)"; exit 1; }
# Nhãn chọn pod của Deployment (app=vllm), để đếm và liệt kê đúng pod vLLM
SEL=$("${K[@]}" "${N[@]}" get deploy vllm -o json \
  | jq -r '.spec.selector.matchLabels | to_entries | map("\(.key)=\(.value)") | join(",")')
# Hai chu kỳ quyết định chặn trên của trễ: scrape (PodMonitor) và sync HPA (cờ kube-controller-manager)
SCRAPE=$("${K[@]}" "${N[@]}" get podmonitor vllm -o jsonpath='{.spec.podMetricsEndpoints[0].interval}' 2>/dev/null || true)
SYNC=$("${K[@]}" -n kube-system get pod -l component=kube-controller-manager -o json 2>/dev/null \
  | jq -r '[.items[0].spec.containers[0].command[] | select(startswith("--horizontal-pod-autoscaler-sync-period="))
           | sub(".*="; "")][0] // "15s (mặc định)"' || true)
# Chu kỳ sync ra giây, từ dạng duration của Go (5s, 1m0s, 1m30s); đọc không được thì lấy mặc định 15 s
SYNC_S=$(awk -v d="${SYNC%% *}" 'BEGIN {
  while (match(d, /^[0-9.]+[hms]/)) {
    u = substr(d, RLENGTH, 1); s += substr(d, 1, RLENGTH - 1) * (u == "h" ? 3600 : (u == "m" ? 60 : 1))
    d = substr(d, RLENGTH + 1)
  }
  print (s > 0 ? s : 15) }')
KCM=$("${K[@]}" -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')

mkdir -p "$OUT"
say "cấu hình: min=$MIN max=$MAX threshold=$THRESHOLD scrape=$SCRAPE sync HPA=$SYNC; mức tải C=$LEVELS × $REPS lần, $DUR s mỗi lượt"
# Dừng giữa chừng (Ctrl-C, lỗi): tắt load-sim.sh (nó tự tắt hey và port-forward) và gỡ annotation tạm dừng,
# để cluster không bị kẹt ở trạng thái tạm dừng. `|| true`: thứ đã gỡ rồi thì bỏ qua.
trap 'jobs -p | xargs -r kill 2>/dev/null || true
      "${K[@]}" "${N[@]}" annotate scaledobject "$SO" "$PAUSE-" >/dev/null 2>&1 || true' EXIT

# Lặp theo vòng (mọi mức tải, rồi lặp lại), không lặp liền một mức: nếu cluster trôi dần (pod chậm lên hơn,
# Prometheus chậm hơn) thì ảnh hưởng chia đều cho các mức, không dồn vào mức chạy sau cùng.
for rep in $(seq 1 "$REPS"); do
  for c in $LEVELS; do run "$c" "$rep"; done
done

# Thời gian KEDA xử lý một lần HPA hỏi metric (gRPC GetMetrics trong keda-operator, gồm cả câu PromQL) và độ
# trễ Prometheus trả lời KEDA, trong suốt phiên: cho biết phần d_sync vượt chu kỳ 5 s có nằm ở KEDA không.
# Cần PodMonitor của keda-operator (common/platform/keda-metrics-values.yaml); không có thì bỏ qua.
span=$(( SECONDS + 60 ))
# num <PromQL>: giá trị của kết quả đầu tiên nếu là số JSON hợp lệ, ngược lại `null` (không có chuỗi nào,
# hoặc Prometheus trả "NaN"). Metric nào thiếu thì chỉ ô đó null, các ô khác vẫn ghi.
num() {
  local v
  v=$(prom "$1" 2>/dev/null | jq -r '.data.result[0].value[1] // empty' 2>/dev/null || true)
  if [[ $v =~ ^[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?$ ]]; then echo "$v"; else echo null; fi
}
s=$(num "sum(increase(keda_internal_metricsservice_grpc_server_handling_seconds_sum{grpc_method=\"GetMetrics\"}[${span}s]))")
n=$(num "sum(increase(keda_internal_metricsservice_grpc_server_handling_seconds_count{grpc_method=\"GetMetrics\"}[${span}s]))")
l=$(num "max_over_time(keda_scaler_metrics_latency_seconds{scaledObject=\"$SO\"}[${span}s])")
jq -n --argjson s "$s" --argjson n "$n" --argjson l "$l" --argjson span "$span" \
  '{grpc_mean_s: (if $s != null and $n != null and $n > 0 then $s / $n else null end),
    grpc_count: $n, scaler_latency_max_s: $l, window_s: $span}' > "$OUT/keda.json"
[ "$s$n$l" != nullnullnull ] || say "không đọc được metric nào của keda-operator (PodMonitor chưa bật?)"
say "xong; tính bảng: uv run --project analysis python -m analysis.lt7_hpa $OUT"
