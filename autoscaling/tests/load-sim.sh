#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# autoscaling/tests/load-sim.sh
# Khái niệm: Bơm tải đồng thời vào simulator bằng `hey`: giữ đúng C request đang chờ trả lời (mỗi
#            "worker" gửi xong mới gửi tiếp) trong một khoảng thời gian, qua một port-forward tới svc/vllm.
# Mục đích:  Một chỗ duy nhất định nghĩa tải cho T2, T5: `make sim-test-load` (chạy tay) và
#            run-t1-t5.sh (chạy tự động) cùng gọi file này, nên hai cách chạy gửi đúng một kiểu tải.
# Dùng:      autoscaling/tests/load-sim.sh <C> <thời lượng>, ví dụ 25 180s (make sim-test-load C=25 DUR=180s).
#            Luôn tự mở port-forward riêng ở một cổng local ngẫu nhiên và tự tắt khi xong, nên không cần
#            port-forward ở terminal khác và không đụng cổng 8000 của cách chạy tay (w2.md §9.3).
# Tham khảo: docs/huong-dan/w2.md §9.3
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../.."             # về gốc repo, để đường dẫn tới request-sim.json đúng ở mọi nơi gọi

C=${1:-25}
DUR=${2:-120s}
K=(kubectl --context "${CTX:-kind-llm-sim}" -n llm-serving)   # CTX: Makefile truyền kind-$(KIND_CLUSTER)

# ready <cổng>: simulator có trả lời qua cổng đó không. /health/ready là readiness của simulator (w1.md §5.2).
ready() { curl -fsS -o /dev/null --max-time 2 "http://127.0.0.1:$1/health/ready" 2>/dev/null; }

pf=""
hp=""
pfout=$(mktemp)                        # nơi port-forward in cổng nó đã chọn
# Dọn dẹp khi thoát vì bất kỳ lý do gì: tắt hey và port-forward do file này mở. TERM/INT (bị dừng giữa
# chừng) đổi thành `exit` để trap EXIT chạy. hey chạy nền rồi `wait`, vì bash chỉ xử lý tín hiệu khi
# lệnh đang chạy ở tiền cảnh kết thúc, còn `wait` thì bị ngắt ngay.
trap 'kill $hp $pf 2>/dev/null || true; rm -f "$pfout"' EXIT
trap 'exit 143' TERM INT

# `:8000` = cổng local để trống, kubectl tự chọn một cổng rảnh. Không dùng lại port-forward sẵn có ở cổng
# 8000: nó có thể trỏ tới cluster khác (tải đi nhầm chỗ trong khi run-t1-t5.sh theo dõi CTX), hoặc cổng
# đang bị chiếm bởi thứ khác và kubectl báo "address already in use".
"${K[@]}" port-forward svc/vllm :8000 >"$pfout" 2>&1 &
pf=$!
port=""
for _ in $(seq 1 20); do
  # Khi đã nghe, kubectl in "Forwarding from 127.0.0.1:<cổng> -> 8000"
  port=$(sed -nE 's/^Forwarding from 127\.0\.0\.1:([0-9]+) .*/\1/p' "$pfout" | head -1)
  [ -n "$port" ] && ready "$port" && break
  sleep 0.5
done
if [ -z "$port" ] || ! ready "$port"; then
  { echo "load-sim: không mở được port-forward tới svc/vllm. Output của kubectl:"; cat "$pfout"; } >&2
  exit 1
fi

# Mốc bắt đầu tải, theo cùng đồng hồ đơn điệu với now() của run-t1-t5.sh (giây trong /proc/uptime; xem lý
# do ở đó). run-t1-t5.sh đọc dòng này để đo T2/T3 từ lúc hey thật sự chạy, không tính thời gian mở
# port-forward ở trên (thường 1–2 s, tối đa 10 s).
if read -r up _ 2>/dev/null < /proc/uptime; then t0=${up%.*}; else t0=$(date +%s); fi
echo "load-sim: hey bắt đầu $t0"
# -z: thời lượng; -c: số worker đồng thời; -D: body lấy từ file; -T: Content-Type
hey -z "$DUR" -c "$C" -m POST -T application/json -D autoscaling/tests/request-sim.json \
  "http://127.0.0.1:$port/v1/chat/completions" &
hp=$!
wait "$hp"
