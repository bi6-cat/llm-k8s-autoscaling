#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# autoscaling/tests/load-sim.sh
# Khái niệm: Bơm tải đồng thời vào simulator bằng `hey`: giữ đúng C request đang chờ trả lời (mỗi
#            "worker" gửi xong mới gửi tiếp) trong một khoảng thời gian, qua port-forward cổng 8000.
# Mục đích:  Một chỗ duy nhất định nghĩa tải cho T2, T5: `make sim-test-load` (chạy tay) và
#            run-t1-t5.sh (chạy tự động) cùng gọi file này, nên hai cách chạy gửi đúng một kiểu tải.
# Dùng:      autoscaling/tests/load-sim.sh <C> <thời lượng>, ví dụ 25 180s (make sim-test-load C=25 DUR=180s).
#            Đã có port-forward ở terminal khác (cách chạy tay, w2.md §9.3) thì dùng luôn; chưa có thì tự
#            mở, và tự tắt khi xong.
# Tham khảo: docs/huong-dan/w2.md §9.3
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../.."             # về gốc repo, để đường dẫn tới request-sim.json đúng ở mọi nơi gọi

C=${1:-25}
DUR=${2:-120s}
K=(kubectl --context "${CTX:-kind-llm-sim}" -n llm-serving)   # CTX: Makefile truyền kind-$(KIND_CLUSTER)

# ready: cổng 8000 có trả lời không. /health/ready là readiness của simulator (w1.md §5.2).
ready() { curl -fsS -o /dev/null --max-time 2 http://localhost:8000/health/ready 2>/dev/null; }

pf=""
hp=""
# Dọn dẹp khi thoát vì bất kỳ lý do gì: tắt hey và port-forward do file này mở. TERM/INT (bị dừng giữa
# chừng) đổi thành `exit` để trap EXIT chạy. hey chạy nền rồi `wait`, vì bash chỉ xử lý tín hiệu khi
# lệnh đang chạy ở tiền cảnh kết thúc, còn `wait` thì bị ngắt ngay.
trap 'kill $hp $pf 2>/dev/null || true' EXIT
trap 'exit 143' TERM INT

if ! ready; then
  "${K[@]}" port-forward svc/vllm 8000:8000 >/dev/null 2>&1 &
  pf=$!
  for _ in $(seq 1 20); do ready && break; sleep 0.5; done
  ready || { echo "load-sim: không mở được port-forward tới svc/vllm (cổng 8000)" >&2; exit 1; }
fi

# -z: thời lượng; -c: số worker đồng thời; -D: body lấy từ file; -T: Content-Type
hey -z "$DUR" -c "$C" -m POST -T application/json -D autoscaling/tests/request-sim.json \
  http://localhost:8000/v1/chat/completions &
hp=$!
wait "$hp"
