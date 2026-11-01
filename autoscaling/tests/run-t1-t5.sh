#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# autoscaling/tests/run-t1-t5.sh
# Khái niệm: Chạy tự động 5 bài kiểm thử nhanh của cấu hình A2 trên simulator (cluster kind):
#            T1 không tải, T2 tải 2,5 × threshold, T3 tắt tải, T4 mất Prometheus (fallback), T5 tạm
#            dừng autoscaling. Trong lúc chạy, mỗi giây ghi một dòng trạng thái HPA vào log.
# Mục đích:  Thay ba terminal chạy tay ở w2.md §9.3 bằng một lệnh: đo thời gian chính xác tới giây
#            và chấm đạt/trượt theo đúng tiêu chí của bảng đó. Log thô là tư liệu cho chương "Triển
#            khai và vận hành" (Kiến trúc §15).
# Dùng:      make sim-test (sau make sim-up), hoặc chỉ một bài: make sim-test T=t4
#            Bài: t1 | t2 (gồm T3, vì T3 là pha "tắt tải" ngay sau T2) | t4 | t5 | all (mặc định)
# Cần:       kubectl, jq, hey; context kind-llm-sim; ScaledObject vllm-a2 đã áp (overlay sim).
# Tham khảo: docs/huong-dan/w2.md §9.3, Kiến trúc §12, §15, Thông số §9.3
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../.."             # về gốc repo, để đường dẫn tương đối dưới đây đúng ở mọi nơi gọi

TEST=${1:-all}
K=(kubectl --context kind-llm-sim)    # mảng bash: "${K[@]}" mở ra đúng từng từ, kể cả khi có dấu cách
N=(-n llm-serving)
HPA=keda-hpa-vllm-a2                   # HPA do KEDA tạo cho ScaledObject vllm-a2 (tên = keda-hpa-<tên SO>)
MAX=3                                  # maxReplicaCount của overlay sim (autoscaling/official/overlays/sim)
LOG=runs/sim/$(date +%Y%m%d-%H%M%S)-t1-t5.log    # runs/ nằm trong .gitignore: dữ liệu thô không commit
mkdir -p "$(dirname "$LOG")"
RESULTS=()                             # mỗi phần tử: "T2 ĐẠT: …" để in tổng kết ở cuối

now() { date +%s; }
say() { echo "$(now) $(date +%T) $*" | tee -a "$LOG"; }
result() { RESULTS+=("$1"); say "KẾT QUẢ $1"; }

# ── Đọc trạng thái ──────────────────────────────────────────────────────────────
# desired: số replica HPA muốn; current: số replica HPA đang tính (= replicas của Deployment).
# Cả hai rỗng khi HPA không tồn tại (lúc tạm dừng, KEDA xoá HPA).
desired() { "${K[@]}" "${N[@]}" get hpa "$HPA" -o jsonpath='{.status.desiredReplicas}' 2>/dev/null || true; }
current() { "${K[@]}" "${N[@]}" get hpa "$HPA" -o jsonpath='{.status.currentReplicas}' 2>/dev/null || true; }
# metric: giá trị HPA đang thấy, đã chia cho số replica (AverageValue), dạng số lượng Kubernetes
metric() {
  "${K[@]}" "${N[@]}" get hpa "$HPA" -o jsonpath='{.status.currentMetrics[0].external.current.averageValue}' \
    2>/dev/null || true
}
# replicas: số replica Deployment đang được đặt (do HPA hoặc do KEDA khi tạm dừng)
replicas() { "${K[@]}" "${N[@]}" get deploy vllm -o jsonpath='{.spec.replicas}'; }
# qty: đổi số lượng kiểu Kubernetes sang số thường: "8334m" (m = mili) = 8,334; "25" = 25
qty() { awk -v q="$1" 'BEGIN { if (q ~ /m$/) { sub(/m$/, "", q); q = q / 1000 } printf "%.3f", q }'; }

# Ghi mỗi giây một dòng: epoch, giờ, desired, current (HPA), spec/ready (Deployment), metric HPA đang
# thấy (dạng "8333m" = 8,333), số lần lỗi liên tiếp KEDA gọi Prometheus, điều kiện Fallback của SO.
# Một lệnh kubectl lấy cả 3 object; --ignore-not-found: thiếu HPA (lúc tạm dừng) thì in "-" chứ không lỗi.
# jq: first(…) // {} = lấy object đầu tiên đúng kind, không có thì dùng {} để các trường ra "-".
watch_loop() {
  while true; do
    "${K[@]}" "${N[@]}" get hpa/"$HPA" deploy/vllm scaledobject/vllm-a2 -o json --ignore-not-found 2>/dev/null | jq -r '
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

# wait_for <hàm đọc> <giá trị> <tối đa giây>: chờ tới khi hàm trả đúng giá trị; in số giây đã chờ,
# hoặc "quá-hạn" (và trả mã 1) nếu hết giờ.
wait_for() {
  local fn=$1 want=$2 limit=$3 t0
  t0=$(now)
  while (( $(now) - t0 <= limit )); do
    if [ "$($fn)" = "$want" ]; then echo $(( $(now) - t0 )); return 0; fi
    sleep 1
  done
  echo "quá-hạn"; return 1
}

# load <C> <thời lượng>: hey giữ đúng C request đồng thời (mỗi "worker" gửi xong mới gửi tiếp) trong
# thời lượng đó, qua port-forward cổng 8000. Body: request chat ngắn, max_tokens 200 (request-sim.json).
load() {
  hey -z "$2" -c "$1" -m POST -T application/json -D autoscaling/tests/request-sim.json \
    http://localhost:8000/v1/chat/completions >> "$LOG.hey" 2>&1
}

# Mỗi bài bắt đầu từ trạng thái nghỉ: 1 replica. Sau T2/T4, về 1 mất khoảng 6 phút (300 s + 60 s).
ensure_idle() {
  say "chờ về trạng thái nghỉ (1 replica)"
  wait_for replicas 1 900 >/dev/null || { say "không về được 1 replica sau 900 s"; exit 1; }
}

# ── Các bài ─────────────────────────────────────────────────────────────────────
t1() {  # T1: không tải 120 s → giữ 1 replica, metric 0
  ensure_idle
  say "T1 bắt đầu: không tải 120 s"
  local t0 bad=0
  t0=$(now)
  while (( $(now) - t0 < 120 )); do
    [ "$(desired)" = 1 ] || bad=$((bad + 1))
    sleep 2
  done
  if (( bad == 0 )); then result "T1 ĐẠT: desired=1 suốt 120 s"; else result "T1 TRƯỢT: $bad lần desired≠1"; fi
}

t2() {  # T2: C=25 request đồng thời (2,5 × threshold 10) → desired=3 trong ≤ 15 s, và metric HPA ≈ 25 ÷ số
        # replica. T3: tắt tải → giữ 3 trong 300 s (cửa sổ ổn định), rồi bớt 1 pod mỗi 60 s (Thông số §9.3).
  local c=25 t_load
  ensure_idle
  say "T2 bắt đầu: hey C=$c trong 180 s"
  t_load=$(now)
  load $c 180s &
  local pid=$! up m e
  up=$(wait_for desired $MAX 60 || true)
  # Đọc metric khi HPA đã tính với 3 replica: đợi current=3, thêm 2 chu kỳ sync (5 s) cho chắc
  wait_for current $MAX 30 >/dev/null || true
  sleep 10
  m=$(qty "$(metric)")
  # Mong đợi e = 25 ÷ 3 ≈ 8,33. Cho lệch ±15%: mỗi worker của hey có khoảng hở ngắn giữa hai request.
  # awk `exit !(…)`: điều kiện đúng thì thoát mã 0, nên dùng thẳng được trong `if`.
  e=$(awk -v c=$c -v r=$MAX 'BEGIN { printf "%.3f", c / r }')
  if [[ $up =~ ^[0-9]+$ ]] && (( up <= 15 )) \
     && awk -v m="$m" -v e="$e" 'BEGIN { exit !(m >= 0.85 * e && m <= 1.15 * e) }'; then
    result "T2 ĐẠT: desired=$MAX sau $up s (tiêu chí ≤ 15 s); metric HPA = $m ≈ $c ÷ $MAX"
  else
    result "T2 TRƯỢT: desired=$MAX sau $up s (tiêu chí ≤ 15 s); metric HPA = $m (mong đợi ≈ $c ÷ $MAX)"
  fi
  wait "$pid" || true                  # hey báo lỗi (ví dụ port-forward đứt) thì vẫn đi tiếp sang T3
  # Mốc 0 của T3 là hạn dừng của hey (t_load + 180 s), KHÔNG phải lúc tiến trình hey thoát: tới hạn, hey
  # thôi gửi request mới nhưng còn chờ các request dở dang (tới ~10 s với 200 token × 50 ms). Đo từ lúc hey
  # thoát thì T3 ngắn đi đúng khoảng đó (lần chạy 01/11: 291 s thay vì 301 s).
  local t_end=$(( t_load + 180 )) t2at d2 d1
  say "T3 bắt đầu: hết tải (hey thôi gửi request mới lúc $(date -d "@$t_end" +%T))"
  if wait_for desired 2 600 >/dev/null; then t2at=$(now); d2=$(( t2at - t_end )); else d2="quá-hạn"; fi
  if [ -n "${t2at:-}" ] && wait_for desired 1 300 >/dev/null; then d1=$(( $(now) - t2at )); else d1="quá-hạn"; fi
  # Cửa sổ 300 s tính từ lần cuối HPA còn muốn 3: ngay sau hạn dừng, cộng độ trễ scrape 5 s + sync 5 s,
  # nên cho tới 330 s. Bước 2 → 1 không được nhanh hơn 60 s (policy). Cận dưới trừ 2 s vì thời gian chỉ
  # đọc được theo từng giây.
  if [[ $d2 =~ ^[0-9]+$ && $d1 =~ ^[0-9]+$ ]] && (( d2 >= 298 && d2 <= 330 && d1 >= 58 && d1 <= 90 )); then
    result "T3 ĐẠT: giữ $MAX trong $d2 s sau khi hết tải rồi về 2; về 1 sau thêm $d1 s (tiêu chí 300–330 s; 60–90 s)"
  else
    result "T3 TRƯỢT: về 2 sau $d2 s, về 1 sau thêm $d1 s (tiêu chí 300–330 s; 60–90 s)"
  fi
}

t4() {  # T4: NetworkPolicy chặn KEDA → Prometheus → sau 3 lần lỗi, fallback lên max (15–30 s)
  ensure_idle
  say "T4 bắt đầu: áp NetworkPolicy chặn keda → Prometheus"
  "${K[@]}" apply -f autoscaling/tests/t4-block-keda-to-prometheus.yaml >> "$LOG"
  # Lưu ý: NetworkPolicy chỉ chặn kết nối MỚI. KEDA giữ kết nối keep-alive tới Prometheus (hỏi mỗi 5 s nên
  # kết nối không bao giờ rảnh để đóng), và kết nối đã mở vẫn đi qua (conntrack). Lần chạy 01/11: áp policy
  # 120 s mà KEDA không lỗi lần nào, dù pod mới trong ns keda bị chặn thật. Vì vậy xoá pod keda-operator để
  # pod mới phải mở kết nối mới. Dùng `delete pod` chứ không `rollout restart`: restart sửa template của
  # Deployment, Argo CD ở nhà sẽ hoàn tác. Mốc 0 của T4 là lúc operator mới Ready.
  "${K[@]}" -n keda delete pod -l app=keda-operator >> "$LOG"
  sleep 2                              # chờ ReplicaSet tạo pod mới, để `wait` dưới đây có pod mà chờ
  "${K[@]}" -n keda wait --for=condition=Ready pod -l app=keda-operator --timeout=120s >> "$LOG"
  say "T4: keda-operator mới đã Ready"
  local up f
  up=$(wait_for desired $MAX 120 || true)
  f=$("${K[@]}" "${N[@]}" get scaledobject vllm-a2 -o jsonpath='{.status.health.*.numberOfFailures}')
  "${K[@]}" delete -f autoscaling/tests/t4-block-keda-to-prometheus.yaml >> "$LOG"
  say "T4: đã gỡ NetworkPolicy"
  if [[ $up =~ ^[0-9]+$ ]] && (( up <= 30 )) && (( ${f:-0} >= 3 )); then
    result "T4 ĐẠT: fallback lên $MAX sau $up s, numberOfFailures=$f (tiêu chí ≤ 30 s, ≥ 3 lần lỗi)"
  else
    result "T4 TRƯỢT: lên $MAX sau $up s, numberOfFailures=${f:-?} (tiêu chí ≤ 30 s, ≥ 3 lần lỗi)"
  fi
}

t5() {  # T5: annotation paused-replicas=1 → giữ đúng 1 replica dù có tải (KEDA xoá HPA khi tạm dừng)
  ensure_idle
  say "T5 bắt đầu: paused-replicas=1 rồi hey C=25 trong 60 s"
  "${K[@]}" "${N[@]}" annotate scaledobject vllm-a2 autoscaling.keda.sh/paused-replicas="1" --overwrite >> "$LOG"
  sleep 10                             # chờ KEDA xử lý annotation (xoá HPA) trước khi bơm tải
  load 25 60s &
  local pid=$! peak=1 r
  while kill -0 "$pid" 2>/dev/null; do   # kill -0: chỉ hỏi tiến trình còn sống không, không gửi tín hiệu
    r=$(replicas); (( r > peak )) && peak=$r
    sleep 1
  done
  "${K[@]}" "${N[@]}" annotate scaledobject vllm-a2 autoscaling.keda.sh/paused-replicas- >> "$LOG"   # "-" cuối = xoá
  say "T5: đã gỡ annotation"
  if (( peak == 1 )); then result "T5 ĐẠT: giữ 1 replica suốt 60 s có tải"; else result "T5 TRƯỢT: lên $peak replica"; fi
}

# ── Chạy ────────────────────────────────────────────────────────────────────────
for c in kubectl jq hey; do command -v "$c" >/dev/null || { echo "thiếu $c"; exit 1; }; done
"${K[@]}" "${N[@]}" get scaledobject vllm-a2 >/dev/null || { echo "chưa có ScaledObject vllm-a2: chạy make sim-up trước"; exit 1; }

watch_loop &
WATCH=$!
# port-forward chỉ chuyển tới MỘT pod, nên mọi tải dồn vào pod đầu tiên. Tín hiệu A2 vẫn đúng vì là
# tổng của mọi pod (w2.md §9.3, "Giới hạn của cách bơm tải này").
"${K[@]}" "${N[@]}" port-forward svc/vllm 8000:8000 >/dev/null 2>&1 &
PF=$!
# Dọn dẹp cả khi dừng giữa chừng (Ctrl-C, lỗi): tắt vòng ghi và port-forward, gỡ NetworkPolicy, gỡ
# annotation tạm dừng. `|| true`: thứ đã gỡ rồi thì bỏ qua.
trap 'kill $WATCH $PF 2>/dev/null || true
      "${K[@]}" delete -f autoscaling/tests/t4-block-keda-to-prometheus.yaml --ignore-not-found >/dev/null 2>&1 || true
      "${K[@]}" "${N[@]}" annotate scaledobject vllm-a2 autoscaling.keda.sh/paused-replicas- >/dev/null 2>&1 || true' EXIT
sleep 3                                # chờ port-forward mở cổng

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
