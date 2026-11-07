#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# autoscaling/tests/run-t1-t5.sh
# Khái niệm: Chạy tự động 5 bài kiểm thử nhanh của cấu hình A2 trên simulator (cluster kind):
#            T1 không tải, T2 tải 2,5 × threshold, T3 tắt tải, T4 mất Prometheus (fallback), T5 tạm
#            dừng autoscaling. Trong lúc chạy, mỗi giây ghi một dòng trạng thái HPA vào log.
# Mục đích:  Thay ba terminal chạy tay ở w2.md §9.3 bằng một lệnh: đo thời gian chính xác tới giây
#            và chấm đạt/trượt theo đúng tiêu chí của bảng đó. Log thô là tư liệu cho chương "Triển
#            khai và vận hành" (Kiến trúc §15) và cho LT7 (Môi trường §19).
# Dùng:      make sim-test (sau make sim-up), hoặc chỉ một bài: make sim-test T=t4
#            Bài: t1 | t2 (gồm T3, vì T3 là pha "tắt tải" ngay sau T2) | t4 | t5 | all (mặc định)
# Cần:       kubectl, jq, curl, hey; ScaledObject vllm-a2 đã áp (overlay sim). CTX = context kubectl
#            (mặc định kind-llm-sim; Makefile truyền kind-$(KIND_CLUSTER)).
# Tham khảo: docs/huong-dan/w2.md §9.3, Kiến trúc §12, §15, Thông số §9.3
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../.."             # về gốc repo, để đường dẫn tương đối dưới đây đúng ở mọi nơi gọi

TEST=${1:-all}
export CTX=${CTX:-kind-llm-sim}        # export: load-sim.sh (tiến trình con) dùng cùng context
K=(kubectl --context "$CTX")           # mảng bash: "${K[@]}" mở ra đúng từng từ, kể cả khi có dấu cách
N=(-n llm-serving)
SO=vllm-a2
HPA=keda-hpa-$SO                       # HPA do KEDA tạo cho ScaledObject (tên = keda-hpa-<tên SO>)
LOG=runs/sim/$(date +%Y%m%d-%H%M%S)-t1-t5.log    # runs/ nằm trong .gitignore: dữ liệu thô không commit
RESULTS=()                             # mỗi phần tử: "T2 ĐẠT: …" để in tổng kết ở cuối

now() { date +%s; }
say() { echo "$(now) $(date +%T) $*" | tee -a "$LOG"; }
result() { RESULTS+=("$1"); say "KẾT QUẢ $1"; }

# ── Đọc trạng thái ──────────────────────────────────────────────────────────────
# Hàm đọc trả chuỗi rỗng khi lỗi (`|| true`): dưới `set -e`, một lần API server chập chờn trong phép gán
# `x=$(…)` sẽ làm dừng cả script giữa chừng.
# hpa <trường>: một trường trong status của HPA; rỗng khi HPA không tồn tại (lúc tạm dừng, KEDA xoá HPA)
hpa() { "${K[@]}" "${N[@]}" get hpa "$HPA" -o jsonpath="{.status.$1}" 2>/dev/null || true; }
desired() { hpa desiredReplicas; }     # số replica HPA muốn
current() { hpa currentReplicas; }     # số replica HPA đang tính (= replicas của Deployment)
metric() { hpa 'currentMetrics[0].external.current.averageValue'; }   # đã chia cho số replica (AverageValue)
# so <jsonpath>: một trường của ScaledObject
so() { "${K[@]}" "${N[@]}" get scaledobject "$SO" -o jsonpath="$1" 2>/dev/null || true; }
# failures: số lần lỗi liên tiếp khi KEDA gọi Prometheus. status.health có một mục cho mỗi metric; lấy max
# như watch_loop, để luôn ra MỘT số kể cả khi có nhiều mục (thêm trigger, hoặc mục cũ sau khi đổi tên).
failures() {
  "${K[@]}" "${N[@]}" get scaledobject "$SO" -o json 2>/dev/null \
    | jq -r '[.status.health[]?.numberOfFailures] | max // 0' 2>/dev/null || true
}
paused() { so '{.status.conditions[?(@.type=="Paused")].status}'; }   # "True" khi KEDA đã tạm dừng SO
# replicas: số replica Deployment đang được đặt (do HPA, hoặc do KEDA khi tạm dừng)
replicas() { "${K[@]}" "${N[@]}" get deploy vllm -o jsonpath='{.spec.replicas}' 2>/dev/null || true; }
# qty: đổi số lượng kiểu Kubernetes sang số thường: "8334m" (m = mili) = 8,334; "25" = 25
qty() { awk -v q="$1" 'BEGIN { if (q ~ /m$/) { sub(/m$/, "", q); q = q / 1000 } printf "%.3f", q }'; }
# a2: giá trị câu PromQL của trigger lúc này, hỏi thẳng Prometheus qua API server (không qua KEDA, không cần
# port-forward). T5 dùng nó để biết tải có thật sự tới simulator không, vì lúc tạm dừng không có HPA.
a2() {
  "${K[@]}" get --raw "$PROM/api/v1/query?query=$QUERY" 2>/dev/null \
    | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo 0
}

# Ghi mỗi giây một dòng: epoch, giờ, desired, current (HPA), spec/ready (Deployment), metric HPA đang
# thấy, số lần lỗi liên tiếp KEDA gọi Prometheus, điều kiện Fallback của SO. Một lệnh kubectl lấy cả 3
# object; --ignore-not-found: thiếu HPA (lúc tạm dừng) thì in "-" chứ không lỗi.
# jq: first(…) // {} = lấy object đầu tiên đúng kind, không có thì dùng {} để các trường ra "-".
watch_loop() {
  while true; do
    "${K[@]}" "${N[@]}" get hpa/"$HPA" deploy/vllm scaledobject/"$SO" -o json --ignore-not-found 2>/dev/null | jq -r '
      (.items // []) as $it
      | (first($it[] | select(.kind == "HorizontalPodAutoscaler")) // {}) as $h
      | (first($it[] | select(.kind == "Deployment")) // {}) as $d
      | (first($it[] | select(.kind == "ScaledObject")) // {}) as $s
      | "desired=\($h.status.desiredReplicas // "-") current=\($h.status.currentReplicas // "-")"
        + " spec=\($d.spec.replicas // "-") ready=\($d.status.readyReplicas // 0)"
        + " metric=\($h.status.currentMetrics[0].external.current.averageValue // "-")"
        + " failures=\([$s.status.health[]?.numberOfFailures] | max // 0)"
        + " fallback=\([$s.status.conditions[]? | select(.type == "Fallback") | .status][0] // "-")"' \
      | sed "s/^/$(now) $(date +%T) /" >> "$LOG" || true
    sleep 1
  done
}

# wait_for <hàm đọc> <giá trị> <tối đa giây> [mốc 0]: chờ tới khi hàm trả đúng giá trị; in số giây tính
# từ mốc 0 (epoch; mặc định là lúc gọi), hoặc "quá-hạn" (và trả mã 1) nếu hết giờ.
wait_for() {
  local fn=$1 want=$2 limit=$3 t0=${4:-}
  [ -n "$t0" ] || t0=$(now)
  while (( $(now) - t0 <= limit )); do
    if [ "$($fn)" = "$want" ]; then echo $(( $(now) - t0 )); return 0; fi
    sleep 1
  done
  echo "quá-hạn"; return 1
}

# Mỗi bài bắt đầu từ trạng thái nghỉ: 1 replica. Sau T2/T4, về 1 mất khoảng 6 phút (300 s + 60 s).
ensure_idle() {
  say "chờ về trạng thái nghỉ (1 replica)"
  wait_for replicas 1 900 >/dev/null || { say "không về được 1 replica sau 900 s"; exit 1; }
}

# load_start <epoch lúc gọi load-sim.sh>: chờ load-sim.sh in mốc "hey bắt đầu <epoch>" vào $LOG.hey (tối đa
# 20 s, gồm thời gian mở port-forward), in epoch đó. Chỉ nhận mốc ≥ lúc gọi, để T5 không đọc nhầm mốc
# của T2 trong cùng file log.
load_start() {
  local t
  for _ in $(seq 1 40); do
    t=$(sed -nE 's/^load-sim: hey bắt đầu ([0-9]+)$/\1/p' "$LOG.hey" 2>/dev/null | tail -1)
    if [ -n "$t" ] && (( t >= $1 )); then echo "$t"; return 0; fi
    sleep 0.5
  done
  return 1
}

# ── Các bài ─────────────────────────────────────────────────────────────────────
t1() {  # T1: không tải 120 s → giữ 1 replica, metric 0
  ensure_idle
  say "T1 bắt đầu: không tải 120 s"
  local t0 m bad=0
  t0=$(now)
  while (( $(now) - t0 < 120 )); do
    # metric rỗng = HPA chưa thấy giá trị nào (`<unknown>`): không tính là 0, vì qty "" cũng ra 0.000
    m=$(metric)
    { [ "$(desired)" = 1 ] && [ -n "$m" ] && [ "$(qty "$m")" = 0.000 ]; } || bad=$((bad + 1))
    sleep 2
  done
  if (( bad == 0 )); then result "T1 ĐẠT: desired=1, metric=0 suốt 120 s"
  else result "T1 TRƯỢT: $bad lần đọc có desired≠1, hoặc metric≠0 hay chưa có metric"; fi
}

t2() {  # T2: C request đồng thời (2,5 × threshold) → desired=UP trong ≤ 15 s, metric HPA ≈ C ÷ số replica.
        # T3: tắt tải → giữ UP trong 300 s (cửa sổ ổn định), rồi bớt 1 pod mỗi 60 s (Thông số §9.3).
  local t_call t_load pid up m e
  ensure_idle
  say "T2 bắt đầu: hey C=$C trong 180 s"
  t_call=$(now)
  autoscaling/tests/load-sim.sh "$C" 180s >> "$LOG.hey" 2>&1 &
  pid=$!
  # Mốc 0 của T2 là lúc hey thật sự chạy, không phải lúc gọi load-sim.sh (trước đó còn mở port-forward)
  if ! t_load=$(load_start "$t_call"); then
    result "T2 TRƯỢT: load-sim.sh không bắt đầu tải sau 20 s (xem $LOG.hey); bỏ qua T3"
    kill "$pid" 2>/dev/null || true; wait "$pid" || true
    return
  fi
  say "T2: hey bắt đầu sau $(( t_load - t_call )) s mở port-forward"
  up=$(wait_for desired "$UP" 60 "$t_load" || true)
  # Đọc metric khi HPA đã tính với UP replica: đợi current=UP, thêm 2 chu kỳ sync (5 s) cho chắc
  wait_for current "$UP" 30 >/dev/null || true
  sleep 10
  m=$(qty "$(metric)")
  # Mong đợi e = C ÷ UP (25 ÷ 3 ≈ 8,33). Cho lệch ±15%: mỗi worker của hey có khoảng hở ngắn giữa hai
  # request. awk `exit !(…)`: điều kiện đúng thì thoát mã 0, nên dùng thẳng được trong `if`.
  e=$(awk -v c="$C" -v r="$UP" 'BEGIN { printf "%.3f", c / r }')
  if [[ $up =~ ^[0-9]+$ ]] && (( up <= 15 )) \
     && awk -v m="$m" -v e="$e" 'BEGIN { exit !(m >= 0.85 * e && m <= 1.15 * e) }'; then
    result "T2 ĐẠT: desired=$UP sau $up s (tiêu chí ≤ 15 s); metric HPA = $m ≈ $C ÷ $UP"
  else
    result "T2 TRƯỢT: desired=$UP sau $up s (tiêu chí ≤ 15 s); metric HPA = $m (mong đợi ≈ $e)"
  fi
  wait "$pid" || true                  # hey hoặc port-forward lỗi thì vẫn đi tiếp sang T3 (log ở $LOG.hey)

  # Mốc 0 của T3 là hạn dừng của hey (t_load + 180 s, t_load = lúc hey bắt đầu), KHÔNG phải lúc tiến trình
  # hey thoát: tới hạn, hey thôi gửi request mới nhưng còn chờ các request dở dang (tới ~10 s với 200 token
  # × 50 ms). Đo từ lúc hey thoát thì T3 ngắn đi đúng khoảng đó (lần chạy 01/11: 291 s thay vì 301 s).
  local t_end=$(( t_load + 180 )) t_mid="" d_mid d_one
  say "T3 bắt đầu: hết tải (hey thôi gửi request mới lúc $(date -d "@$t_end" +%T))"
  if wait_for desired $(( UP - 1 )) 600 >/dev/null; then t_mid=$(now); d_mid=$(( t_mid - t_end )); else d_mid="quá-hạn"; fi
  if [ -n "$t_mid" ] && wait_for desired 1 300 >/dev/null; then d_one=$(( $(now) - t_mid )); else d_one="quá-hạn"; fi
  # Cửa sổ 300 s tính từ lần cuối HPA còn muốn UP: ngay sau hạn dừng, cộng độ trễ scrape 5 s + sync 5 s,
  # nên cho tới 330 s. Bước sau không được nhanh hơn 60 s (policy). Cận dưới trừ 2 s vì thời gian chỉ đọc
  # được theo từng giây.
  if [[ $d_mid =~ ^[0-9]+$ && $d_one =~ ^[0-9]+$ ]] \
     && (( d_mid >= 298 && d_mid <= 330 && d_one >= 58 && d_one <= 90 )); then
    result "T3 ĐẠT: giữ $UP trong $d_mid s sau khi hết tải rồi về $(( UP - 1 )); về 1 sau thêm $d_one s (tiêu chí 300–330 s; 60–90 s)"
  else
    result "T3 TRƯỢT: về $(( UP - 1 )) sau $d_mid s, về 1 sau thêm $d_one s (tiêu chí 300–330 s; 60–90 s)"
  fi
}

t4() {  # T4: NetworkPolicy chặn KEDA → Prometheus → sau 3 lần lỗi, fallback lên FALLBACK replica (≤ 30 s)
  local ka f0 up f rec
  ensure_idle
  # NetworkPolicy chỉ chặn kết nối MỚI. KEDA phải mở kết nối mới cho mỗi lần hỏi (KEDA_HTTP_DISABLE_KEEP_ALIVE
  # trong platform/keda/values.yaml); thiếu biến này thì kết nối keep-alive cũ vẫn đi qua và T4 trượt oan.
  ka=$("${K[@]}" -n keda get deploy keda-operator \
         -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="KEDA_HTTP_DISABLE_KEEP_ALIVE")].value}' \
         2>/dev/null || true)
  if [ "$ka" != true ]; then
    result "T4 TRƯỢT: keda-operator chưa có KEDA_HTTP_DISABLE_KEEP_ALIVE=true (platform/keda/values.yaml); chạy lại make sim-up"
    return
  fi
  # Trước khi chặn, KEDA phải khoẻ (0 lỗi); sau khi gỡ, lỗi phải hết. Hai điều này nối lỗi với đúng policy.
  f0=$(failures)
  if [ "${f0:-0}" != 0 ]; then result "T4 TRƯỢT: trước khi áp policy, KEDA đã lỗi $f0 lần"; return; fi
  say "T4 bắt đầu: áp NetworkPolicy chặn keda → Prometheus"
  "${K[@]}" apply -f autoscaling/tests/t4-block-keda-to-prometheus.yaml >> "$LOG"
  up=$(wait_for desired "$FALLBACK" 120 || true)
  f=$(failures)
  "${K[@]}" delete -f autoscaling/tests/t4-block-keda-to-prometheus.yaml >> "$LOG"
  say "T4: đã gỡ NetworkPolicy"
  rec=$(wait_for failures 0 30 || true)
  # Không đặt cận dưới: lần chạy 01/11 thấy lỗi thứ 2 và thứ 3 chỉ cách nhau 2 s (KEDA hỏi cả theo HPA lẫn
  # theo vòng polling của nó), nên 3 lần lỗi có thể đến sớm hơn 3 chu kỳ sync HPA.
  if [[ $up =~ ^[0-9]+$ && $rec =~ ^[0-9]+$ ]] && (( up <= 30 && ${f:-0} >= 3 )); then
    result "T4 ĐẠT: fallback lên $FALLBACK sau $up s, numberOfFailures=$f; gỡ policy thì hết lỗi sau $rec s (tiêu chí ≤ 30 s, ≥ 3 lỗi)"
  else
    result "T4 TRƯỢT: lên $FALLBACK sau $up s, numberOfFailures=${f:-?}, hết lỗi sau $rec s (tiêu chí ≤ 30 s, ≥ 3 lỗi)"
  fi
}

t5() {  # T5: annotation paused-replicas=1 → giữ đúng 1 replica dù có tải (KEDA xoá HPA khi tạm dừng)
  local pid peak=1 peak_a2=0 r a need
  ensure_idle
  say "T5 bắt đầu: paused-replicas=1 rồi hey C=$C trong 60 s"
  "${K[@]}" "${N[@]}" annotate scaledobject "$SO" autoscaling.keda.sh/paused-replicas="1" --overwrite >> "$LOG"
  # Chờ KEDA xử lý xong annotation rồi mới bơm tải: điều kiện Paused=True VÀ HPA đã bị xoá (desired rỗng).
  # Bơm tải khi HPA cũ còn thì HPA scale lên và T5 trượt oan.
  if ! wait_for paused True 30 >/dev/null || ! wait_for desired "" 30 >/dev/null; then
    result "T5 TRƯỢT: sau 30 s KEDA chưa tạm dừng (Paused=$(paused), HPA desired=$(desired)); xem log keda-operator"
    "${K[@]}" "${N[@]}" annotate scaledobject "$SO" autoscaling.keda.sh/paused-replicas- >> "$LOG"
    return
  fi
  say "T5: KEDA đã tạm dừng (Paused=True, HPA đã xoá)"
  autoscaling/tests/load-sim.sh "$C" 60s >> "$LOG.hey" 2>&1 &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do   # kill -0: chỉ hỏi tiến trình còn sống không, không gửi tín hiệu
    r=$(replicas)
    [[ $r =~ ^[0-9]+$ ]] && (( r > peak )) && peak=$r
    a=$(a2)
    peak_a2=$(awk -v a="$a" -v p="$peak_a2" 'BEGIN { m = (a + 0 > p + 0) ? a : p; print m }')
    sleep 1
  done
  wait "$pid" || true
  "${K[@]}" "${N[@]}" annotate scaledobject "$SO" autoscaling.keda.sh/paused-replicas- >> "$LOG"   # "-" cuối = xoá
  say "T5: đã gỡ annotation"
  # Giữ 1 replica chỉ có nghĩa khi tải thật sự tới simulator: A2 phải đủ để lên UP nếu không tạm dừng,
  # tức ⌈A2 ÷ threshold⌉ ≥ UP, tức A2 ≥ (UP − 1) × threshold + 1.
  need=$(( (UP - 1) * THRESHOLD + 1 ))
  if (( peak == 1 )) && awk -v a="$peak_a2" -v n="$need" 'BEGIN { exit !(a + 0 >= n) }'; then
    result "T5 ĐẠT: giữ 1 replica suốt 60 s có tải; A2 cao nhất $peak_a2 (≥ $need: không tạm dừng thì đã lên $UP)"
  else
    result "T5 TRƯỢT: replica cao nhất $peak, A2 cao nhất $peak_a2 (cần đúng 1 replica và A2 ≥ $need)"
  fi
}

# ── Chạy ────────────────────────────────────────────────────────────────────────
for c in kubectl jq curl hey; do command -v "$c" >/dev/null || { echo "thiếu $c"; exit 1; }; done
"${K[@]}" "${N[@]}" get scaledobject "$SO" >/dev/null || { echo "chưa có ScaledObject $SO: chạy make sim-up trước"; exit 1; }

# Thông số lấy từ chính ScaledObject (overlay sim), không viết cứng, để sửa overlay thì bài thử đổi theo.
MAX=$(so '{.spec.maxReplicaCount}')
FALLBACK=$(so '{.spec.fallback.replicas}')
THRESHOLD=$(so '{.spec.triggers[0].metadata.threshold}')
[[ $MAX =~ ^[0-9]+$ && $FALLBACK =~ ^[0-9]+$ && $THRESHOLD =~ ^[0-9]+$ ]] \
  || { echo "ScaledObject $SO thiếu maxReplicaCount, fallback.replicas hoặc threshold nguyên"; exit 1; }
(( MAX >= 3 )) || { echo "T1–T5 cần maxReplicaCount ≥ 3 (đang là $MAX)"; exit 1; }
# Thông số §9.3: fallback.replicas = maxReplicaCount. Overlay đổi max mà quên đổi fallback thì HPA kẹp
# desired ở max, T4 chờ FALLBACK mãi không tới và trượt oan; dừng ngay để báo đúng chỗ sai.
(( FALLBACK == MAX )) || { echo "fallback.replicas ($FALLBACK) ≠ maxReplicaCount ($MAX): sửa overlay (Thông số §9.3)"; exit 1; }
C=$(( THRESHOLD * 5 / 2 ))             # 2,5 × threshold (w2.md §9.3): threshold 10 → 25 request đồng thời
UP=$(( (C + THRESHOLD - 1) / THRESHOLD ))   # desired mong đợi ở T2 = ⌈C ÷ threshold⌉ = 3
# Câu PromQL và địa chỉ Prometheus lấy đúng từ trigger, để T5 kiểm cùng tín hiệu KEDA dùng. serverAddress
# dạng http://<service>.<namespace>.svc:<cổng> → đường proxy của API server tới Service đó.
# @uri (jq): mã hoá câu PromQL để đặt được vào URL.
QUERY=$(jq -rn --arg q "$(so '{.spec.triggers[0].metadata.query}')" '$q | @uri')
PROM=$(so '{.spec.triggers[0].metadata.serverAddress}' \
  | sed -E 's#^http://([^.]+)\.([^.]+)\.svc(\.cluster\.local)?:([0-9]+).*#/api/v1/namespaces/\2/services/http:\1:\4/proxy#')
# a2() đổi mọi lỗi thành 0, nên kiểm một lần ở đây: serverAddress không đúng dạng trên (sed không đổi được)
# hoặc câu PromQL lỗi thì dừng ngay, thay vì để T5 báo "A2 cao nhất 0" như thể tải không tới simulator.
[[ $PROM == /api/v1/namespaces/* ]] \
  || { echo "serverAddress '$PROM' không có dạng http://<service>.<namespace>.svc:<cổng>"; exit 1; }
"${K[@]}" get --raw "$PROM/api/v1/query?query=$QUERY" 2>/dev/null | jq -e '.status == "success"' >/dev/null \
  || { echo "Không chạy được câu PromQL của $SO qua $PROM (Prometheus chưa sẵn sàng?)"; exit 1; }

mkdir -p "$(dirname "$LOG")"
say "cấu hình: max=$MAX fallback=$FALLBACK threshold=$THRESHOLD → C=$C, T2 mong đợi desired=$UP"
watch_loop &
# Dọn dẹp cả khi dừng giữa chừng (Ctrl-C, lỗi): dừng các tiến trình nền (vòng ghi, load-sim.sh tự tắt hey và
# port-forward của nó), gỡ NetworkPolicy, gỡ annotation tạm dừng. `|| true`: thứ đã gỡ rồi thì bỏ qua.
trap 'jobs -p | xargs -r kill 2>/dev/null || true
      "${K[@]}" delete -f autoscaling/tests/t4-block-keda-to-prometheus.yaml --ignore-not-found >/dev/null 2>&1 || true
      "${K[@]}" "${N[@]}" annotate scaledobject "$SO" autoscaling.keda.sh/paused-replicas- >/dev/null 2>&1 || true' EXIT

case $TEST in
  t1) t1 ;;
  t2) t2 ;;
  t4) t4 ;;
  t5) t5 ;;
  all) t1; t2; t4; t5 ;;
  *) echo "bài không hợp lệ: $TEST (t1 | t2 | t4 | t5 | all)"; exit 1 ;;
esac

echo; echo "Tổng kết (log: $LOG):"
printf '  %s\n' "${RESULTS[@]}"
[[ ! " ${RESULTS[*]} " =~ TRƯỢT ]]     # mã thoát 1 nếu có bài trượt, để make báo lỗi
