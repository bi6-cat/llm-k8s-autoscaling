#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# common/platform/alertmanager-secret.sh
# Khái niệm: Secret = object Kubernetes giữ dữ liệu nhạy cảm (ở đây: token bot Telegram và chat id).
#            Alertmanager đọc hai key của Secret alertmanager-telegram qua file (alertmanager-values.yaml).
# Mục đích:  Tạo hoặc cập nhật Secret đó từ .env, cho mọi môi trường, bằng một lệnh kubectl do người gọi
#            truyền vào (context kind, k3s qua ssh…). Token không lọt vào dòng lệnh của tiến trình nào (không
#            dùng --from-literal) và không ghi ra đĩa: YAML đi thẳng vào stdin của `kubectl apply -f -`.
#            .env chưa có hai biến thì in cảnh báo rồi thoát 0: Alertmanager vẫn chạy, chỉ không gửi được tin.
# Dùng:      common/platform/alertmanager-secret.sh <lệnh kubectl…>
#              sim:   … kubectl --context kind-llm-sim          (make sim-up tự gọi)
#              cloud: … ssh -p <port> root@<host> k3s kubectl   (vast.sh platform tự gọi)
#              nhà:   make alertmanager-secret CTX=<context>   (chỉ có tác dụng khi Application monitoring
#                     đã nạp alertmanager-values.yaml, việc 6b; trước đó Alertmanager ở nhà không đọc Secret)
# Tham khảo: Vận hành §3.4, §8; .env.example; CONTRIBUTING §2 (bí mật)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/../.."
[ $# -gt 0 ] || { echo "Dùng: $0 <lệnh kubectl…>, ví dụ: $0 kubectl --context kind-llm-sim" >&2; exit 2; }

# Giá trị đã có trong môi trường (vast.sh đã nạp .env, hoặc người gọi tự đặt) được ưu tiên. Chỉ khi còn thiếu
# mới đọc .env, và .env chỉ lấp chỗ trống: một .env chép từ .env.example (hai biến để trống) không xoá được
# giá trị truyền qua môi trường. `set -a` = mọi biến gán sau đó tự export; `set +a` tắt lại.
token=${ALERTMANAGER_TELEGRAM_BOT_TOKEN:-}
chat=${ALERTMANAGER_TELEGRAM_CHAT_ID:-}
if { [ -z "$token" ] || [ -z "$chat" ]; } && [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null  # .env là file cục bộ (gitignore), shellcheck không cần đọc nó
  . ./.env
  set +a
  token=${token:-${ALERTMANAGER_TELEGRAM_BOT_TOKEN:-}}
  chat=${chat:-${ALERTMANAGER_TELEGRAM_CHAT_ID:-}}
fi
if [ -z "$token" ] || [ -z "$chat" ]; then
  echo "alertmanager-secret: .env chưa có ALERTMANAGER_TELEGRAM_BOT_TOKEN và ALERTMANAGER_TELEGRAM_CHAT_ID;" \
       "bỏ qua (Alertmanager vẫn chạy nhưng không gửi được Telegram)" >&2
  exit 0
fi
# Kiểm dạng ngay tại đây: Alertmanager chỉ đọc file lúc gửi tin, nên giá trị sai chỉ lộ ra khi đã có sự cố.
# Token của Bot API có dạng <id bot>:<35 ký tự chữ, số, _ hoặc ->. Chat id là số nguyên; nhóm thì âm
# (-100… với supergroup).
[[ $token =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]] || { echo "alertmanager-secret: token sai dạng <số>:<chuỗi>" >&2; exit 1; }
[[ $chat =~ ^-?[0-9]+$ ]] || { echo "alertmanager-secret: chat id phải là số nguyên (nhóm: số âm)" >&2; exit 1; }

# Secret lưu giá trị ở dạng base64 trong `data:`. printf là lệnh có sẵn của bash (không tạo tiến trình
# mới), nên token chỉ đi qua pipe vào stdin của base64. `tr -d '\n'`: base64 GNU tự xuống dòng sau 76 ký tự.
b64() { printf %s "$1" | base64 | tr -d '\n'; }

# Gửi kèm Namespace: ở cloud, script chạy trước khi chart tạo namespace monitoring. apply với object đã có
# thì không đổi gì. Gọi "$@" apply -f -: với ssh, phần sau host thành lệnh chạy trên VM và stdin đi theo.
"$@" apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata: {name: monitoring}
---
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-telegram
  namespace: monitoring
type: Opaque
data:
  bot-token: $(b64 "$token")
  chat-id: $(b64 "$chat")
EOF
