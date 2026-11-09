#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# infra/provision/vast.sh
# Khái niệm: Script bọc CLI `vastai` (công cụ dòng lệnh của Vast.ai) cho cả vòng đời một máy thuê:
#            tìm offer → thuê → chờ → sinh inventory Ansible → SSH/tunnel → huỷ.
# Mục đích:  Cô lập phần phụ thuộc nhà cung cấp vào MỘT file; đổi nhà cung cấp chỉ phải viết lại file này.
#            Ghi trạng thái vào .vast/ để không bao giờ quên một máy đang tính tiền.
# Dùng:      vast.sh find v0|v2 | rent <offer_id> v0|v2 | wait | probe | inventory | platform | ssh | tunnel
#            | runner-start <matrix> | status | release
#            (thường gọi qua Makefile: make find / rent / bootstrap / release)
#            Loại GPU, số GPU, trần giá đổi bằng biến môi trường, ví dụ:
#              GPU=RTX_4090 NGPU=4 MAX_DPH=3 infra/provision/vast.sh find v2
# Cần:       uv (chạy vastai bản ghim, không cần cài), jq, bc, ssh; VAST_VM_TEMPLATE trong .env;
#            API key cho rent/status/release: `uvx --python 3.12 vastai@1.11.0 set api-key <key>`
#            (find không cần key).
# Tham khảo: docs/huong-dan/w2.md §11.2; Thông số §10.2 (tiêu chí lọc máy); nhật ký Quang 06/11
# ──────────────────────────────────────────────────────────────────────────────

# -e: dừng ngay khi một lệnh lỗi. -u: dùng biến chưa gán là lỗi. -o pipefail: lỗi giữa đường ống
# (a | b) cũng tính là lỗi. Ba cờ này tránh việc script chạy tiếp trong trạng thái sai.
set -euo pipefail
# Về gốc repo (script nằm ở infra/provision/), để mọi đường dẫn bên dưới là tương đối với gốc repo
cd "$(dirname "$0")/../.."
# Thư mục trạng thái (gitignore): instance_id, mode, rented_at, cost.log
STATE=.vast
mkdir -p "$STATE"
# Nạp .env nếu có. `set -a` = mọi biến gán sau đó tự export cho lệnh con; `set +a` tắt lại.
# shellcheck source=/dev/null  # .env là file cục bộ (gitignore), shellcheck không cần đọc nó
if [ -f .env ]; then set -a; . ./.env; set +a; fi

# ── Hàm phụ ──────────────────────────────────────────────────────────────────

# Chạy CLI vastai bản ghim qua uvx (uv tải về môi trường riêng, lần sau dùng lại cache), nên không phải
# cài vào máy. Ép Python 3.12: với Python 3.14 mặc định của máy dev, uv phải build pillow từ mã nguồn
# và hỏng (gặp 06/11). Phiên bản ghim ở docs/phien-ban.md.
vastai() { uvx -q --python 3.12 vastai@1.11.0 "$@"; }

# Tiêu chí lọc offer theo cú pháp của `vastai search offers` (Thông số §10.2).
#   v0: 1 GPU để thử và gỡ lỗi bootstrap.
#   v2: NGPU GPU (mặc định 4) cho đợt đánh giá; thêm disk_bw ≥ 1000 MB/s vì cold start L2 đọc model từ ổ.
#       CPU ≥ 8 + 3N: 4 lõi dự trữ (reserved-cpus) + 3 lõi/pod vLLM + 3 lõi máy tạo tải + ~1 lõi pod khác;
#       N = 4 → 20. Máy V1 có 15 vCPU nên máy tạo tải vượt ngưỡng (log phiên 08/11 §14). RAM ≥ 24 GB/GPU:
#       pod 3B 16 GiB + phần nền. Mặc định A4000 16 GB theo V1. Lưu ý (09/11): hôm đó Vast không có offer VM
#       4 × A4000 nào; chỉ có 4 × 4090 và 4 × 5090 từ 2,4 USD/giờ, phải nâng MAX_DPH và đổi GPU.
# GPU: tên GPU theo cú pháp vastai, dấu cách thay bằng `_` (RTX_4090, RTX_3090, RTX_5060_Ti…).
# vms_enabled=true: máy cho thuê chế độ VM (có systemd, chạy được k3s), không phải container.
# verified=true: chỉ máy Vast đã xác minh, khớp với giao diện web. Lưu ý (06/11): thiếu điều kiện này
#   thì kết quả có cả máy unverified/deverified, nhìn rẻ nhưng giao diện không hiện.
# reliability>0.98: tỷ lệ máy chạy ổn định theo thống kê của Vast.
# Bỏ inet_down: cột này không phản ánh mạng thật (08/11); đo thật bằng `vast.sh probe` ngay sau khi thuê.
query() {
  local gpu=${GPU:-RTX_A4000} n=${NGPU:-4} max=${MAX_DPH:-2.0}
  local common="gpu_name=$gpu vms_enabled=true verified=true rentable=true reliability>0.98"
  case "$1" in
    v0) echo "num_gpus=1 $common cpu_cores_effective>=8 cpu_ram>=32 disk_space>=150" ;;
    v2) echo "num_gpus=$n $common cpu_cores_effective>=$((8 + 3 * n)) cpu_ram>=$((24 * n)) disk_space>=300" \
             "disk_bw>=1000 dph_total<=$max" ;;
    *) echo "MODE phải là v0 hoặc v2" >&2; exit 2 ;;
  esac
}
# Dung lượng ổ (GB) xin khi thuê: model (7B ~15 GB, 3B ~6 GB) + image vLLM (~10 GB) + dữ liệu đánh giá
disk_gb() { if [ "$1" = v2 ]; then echo 300; else echo 150; fi; }
# ID instance đang thuê; dừng script nếu chưa thuê
instance_id() { cat "$STATE/instance_id" 2>/dev/null || { echo "Chưa có instance (.vast/instance_id)" >&2; exit 1; }; }
# Đổi "ssh://root@host:port" (vastai ssh-url in ra) thành "host port" để đọc bằng `read -r host port`
ssh_target() {
  vastai ssh-url "$(instance_id)" | sed -E 's#ssh://[^@]+@([^:]+):([0-9]+).*#\1 \2#'
}

# ── Các lệnh ─────────────────────────────────────────────────────────────────
# Mỗi lệnh là một hàm cmd_<tên>; dòng cuối file gọi hàm theo tham số đầu tiên.

# In 8 offer rẻ nhất (-o dph_total = sắp theo giá/giờ). jq:
#   select(.is_vm_deverified | not): bỏ máy đã trượt bài kiểm tra VM của Vast. Trường này không lọc được
#     trong cú pháp search, nên lọc sau (06/11: 15/45 offer VM có cờ này).
#   Mỗi offer một dòng: id, số GPU × tên, giá cả máy và giá/GPU, độ tin cậy %, CPU, RAM, tốc độ đọc ổ,
#   driver của host, vị trí. Driver cần ≥ 580 cho image vLLM v0.31.0 (CUDA 13); chưa rõ VM dùng driver
#   của host hay của template, nên in ra để kiểm ở V0.
cmd_find() {
  local q out; q=$(query "${1:?v0|v2}")
  echo "Lọc: $q" >&2
  out=$(vastai search offers "$q" -o 'dph_total' --raw | jq -r '[.[] | select(.is_vm_deverified | not)] | .[:8][] |
    "\(.id)\t\(.num_gpus)x\(.gpu_name)\t$\(.dph_total*1000|round/1000)/h ($\(.dph_total/.num_gpus*1000|round/1000)/GPU)\trel=\((.reliability2 // .reliability)*1000|round/10)%\tcpu=\(.cpu_cores_effective|round)\tram=\(.cpu_ram/1024|round)GB\tdisk_bw=\(.disk_bw|round)MB/s\tdrv=\(.driver_version)\t\(.geolocation)"')
  # Không có offer thì nói rõ và gợi ý nới tiêu chí, thay vì in ra rỗng
  if [ -z "$out" ]; then
    echo "Không có offer khớp. Thử đổi GPU=…, NGPU=… hoặc nâng MAX_DPH=… (mặc định 2.0)." >&2; return 1
  fi
  echo "$out"
}

# Thuê một offer. Từ chối nếu đang có máy chưa huỷ (tránh quên một máy đang tính tiền).
# --ssh --direct: vào máy bằng SSH trực tiếp tới IP của máy (không qua proxy của Vast).
cmd_rent() {
  local offer=${1:?offer id} mode=${2:?v0|v2}
  : "${VAST_VM_TEMPLATE:?Đặt VAST_VM_TEMPLATE trong .env}"     # `:` = lệnh rỗng; chỉ để kiểm biến đã đặt
  if [ -f "$STATE/instance_id" ]; then echo "Đang có instance $(cat "$STATE/instance_id"); chạy release trước." >&2; exit 1; fi
  vastai create instance "$offer" --template_hash "$VAST_VM_TEMPLATE" --disk "$(disk_gb "$mode")" \
    --ssh --direct --label "llm-thesis-$mode" --raw | jq -r '.new_contract' > "$STATE/instance_id"
  echo "$mode" > "$STATE/mode"
  date -u +%s > "$STATE/rented_at"                             # giờ bắt đầu (epoch giây) để tính tiền khi release
  echo "Đã tạo instance $(cat "$STATE/instance_id")"
}

# Chờ máy chạy (tối đa 90 × 20 s = 30 phút), rồi chờ tới khi SSH vào được.
# accept-new: tự tin khoá SSH của máy MỚI lần đầu, nhưng vẫn báo lỗi nếu khoá của một máy đã biết bị đổi.
cmd_wait() {
  local id st host port; id=$(instance_id)
  for _ in $(seq 1 90); do
    st=$(vastai show instance "$id" --raw | jq -r '.actual_status')
    echo "$(date +%T) $st"
    [ "$st" = running ] && break
    sleep 20
  done
  if [ "$st" != running ]; then echo "Máy chưa chạy sau 30 phút; xem console Vast, cân nhắc release." >&2; exit 1; fi
  read -r host port < <(ssh_target)
  until ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -p "$port" "root@$host" true 2>/dev/null; do
    echo "$(date +%T) chờ SSH…"; sleep 10
  done
  echo "SSH sẵn sàng: ssh -p $port root@$host"
}

# Sinh inventory Ansible cho máy đang thuê. VM duy nhất vừa là k3s_server vừa chạy GPU.
# Nhóm `cloud` → Ansible tự nạp inventory/group_vars/cloud.yaml. File chứa IP công khai nên đã gitignore.
cmd_inventory() {
  local host port; read -r host port < <(ssh_target)
  cat > infra/ansible/inventory/cloud.yaml <<EOF
# Sinh bởi infra/provision/vast.sh — không commit (đã gitignore)
all:
  children:
    cloud:
      children:
        k3s_server:
          hosts:
            vast-$(instance_id):
              ansible_host: $host
              ansible_port: $port
              ansible_user: root
      vars:
        ansible_ssh_common_args: "-o StrictHostKeyChecking=accept-new"
EOF
  echo "Đã ghi infra/ansible/inventory/cloud.yaml"
}

# Kiểm máy vừa thuê trước khi bootstrap: đẩy probe.sh qua SSH và chạy trên VM (bash -s = đọc script từ stdin).
cmd_probe() {
  local host port; read -r host port < <(ssh_target)
  ssh -p "$port" "root@$host" bash -s < infra/provision/probe.sh
}

# Cài phần nền và vLLM. Render manifest trên máy dev (có repo), chép sang VM, chạy install-platform.sh tại đó.
# OVERLAY: overlay serving, mặc định cloud-3b (model V2).
cmd_platform() {
  local host port dir overlay=${OVERLAY:-cloud-3b}; read -r host port < <(ssh_target)
  dir=$(mktemp -d); trap 'rm -rf "$dir"' RETURN      # thư mục tạm tự xoá khi hàm kết thúc
  cp infra/provision/install-platform.sh "$dir/"
  cp platform/gpu/device-plugin-values.yaml "$dir/"
  cp platform/kube-prometheus-stack/values.yaml "$dir/kps-values.yaml"
  cp platform/keda/values.yaml "$dir/keda-values.yaml"
  kubectl kustomize platform/kube-prometheus-stack/extras > "$dir/kps-extras.yaml"
  kubectl kustomize platform/gpu/exporter > "$dir/gpu-exporter.yaml"
  kubectl kustomize "serving/overlays/$overlay" > "$dir/serving.yaml"
  # tar qua ssh: chép cả thư mục bằng một kết nối, không cần rsync trên VM
  tar -C "$dir" -cf - . | ssh -p "$port" "root@$host" 'mkdir -p /root/platform && tar -C /root/platform -xf -'
  ssh -p "$port" "root@$host" bash /root/platform/install-platform.sh
}

# Chạy ma trận bằng systemd trên VM. Lấy đúng commit đang đứng (phải đã push): metadata.json của mỗi lượt ghi
# commit này (N8), nên từ chối nếu cây làm việc có thay đổi chưa commit.
cmd_runner-start() {
  local matrix=${1:?file ma trận, ví dụ experiments/matrix-v2.yaml} host port sha url
  read -r host port < <(ssh_target)
  if [ -n "$(git status --porcelain)" ]; then echo "Có thay đổi chưa commit; commit và push trước." >&2; exit 1; fi
  sha=$(git rev-parse HEAD); url=$(git remote get-url origin)
  git branch -r --contains "$sha" | grep -q . || { echo "Commit $sha chưa push." >&2; exit 1; }
  # .env chứa khoá: chép qua stdin của ssh (không nằm trên dòng lệnh), quyền 600 trên VM
  ssh -p "$port" "root@$host" bash -s -- "$url" "$sha" "$matrix" <<'REMOTE'
set -euo pipefail
url=$1 sha=$2 matrix=$3
command -v git >/dev/null || apt-get install -y git
command -v rclone >/dev/null || {
  # Bản ghim (docs/phien-ban.md); unzip bằng Python vì image Ubuntu tối giản có thể không có unzip
  curl -fsSL -o /tmp/rclone.zip https://downloads.rclone.org/v1.71.2/rclone-v1.71.2-linux-amd64.zip
  python3 -m zipfile -e /tmp/rclone.zip /tmp/rclone-x
  install /tmp/rclone-x/rclone-v1.71.2-linux-amd64/rclone /usr/local/bin/rclone
}
[ -d /opt/llm-runner/.git ] || git clone "$url" /opt/llm-runner
git -C /opt/llm-runner fetch -q origin
git -C /opt/llm-runner checkout -q "$sha"
printf 'MATRIX=%s
KUBECONFIG=/etc/rancher/k3s/k3s.yaml
' "$matrix" > /opt/llm-runner/runner.env
cp /opt/llm-runner/infra/provision/llm-runner.service /etc/systemd/system/llm-runner.service
systemctl daemon-reload
REMOTE
  ssh -p "$port" "root@$host" 'umask 077; cat > /opt/llm-runner/.env' < .env
  ssh -p "$port" "root@$host" 'systemctl enable --now llm-runner && systemctl --no-pager status llm-runner | head -5'
  echo "Xem log: make ssh rồi journalctl -u llm-runner -f"
}

# Mở shell trên VM. `exec` thay tiến trình script bằng ssh (Ctrl-D là thoát luôn).
cmd_ssh() { local host port; read -r host port < <(ssh_target); exec ssh -p "$port" "root@$host"; }

# SSH tunnel: cổng 16443 trên máy dev → cổng 6443 (API server) trên VM. -N = không mở shell, chỉ chuyển
# cổng. Kubeconfig llm-cloud trỏ tới 127.0.0.1:16443 (group_vars/cloud.yaml). Giữ terminal này mở.
cmd_tunnel() {
  local host port; read -r host port < <(ssh_target)
  echo "Tunnel 127.0.0.1:16443 → API server của VM (Ctrl-C để đóng)"
  exec ssh -N -L 16443:127.0.0.1:6443 -p "$port" "root@$host"
}

# Trạng thái máy và số dư tài khoản
cmd_status() {
  vastai show instance "$(instance_id)" --raw | jq '{id, actual_status, gpu_name, num_gpus, dph_total, public_ipaddr}'
  vastai show user --raw | jq '{credit}'
}

# Huỷ máy và ghi chi phí ước tính = số giờ × giá/giờ vào .vast/cost.log (dùng cho sổ chi phí).
# Hỏi xác nhận vì mọi dữ liệu trên VM mất vĩnh viễn. bc = máy tính số thực (bash chỉ tính số nguyên).
cmd_release() {
  local id dph start hours ok host port; id=$(instance_id)
  # Dữ liệu trên VM mất khi huỷ (Môi trường §3.8): đòi R2 có đủ cả dữ liệu trên VM lẫn trên máy dev.
  # FORCE_RELEASE=1 để bỏ qua, ví dụ máy lỗi ngay sau khi thuê nên chưa có dữ liệu.
  if [ "${FORCE_RELEASE:-0}" != 1 ]; then
    read -r host port < <(ssh_target)
    ssh -p "$port" "root@$host" \
      'if [ -d /opt/llm-runner/runs ]; then cd /opt/llm-runner; set -a; . ./.env; set +a; uv run --project experiments python -m experiments.runner.backup check; fi' \
      || { echo "Dữ liệu trên VM chưa sao lưu đủ (hoặc không kiểm được). Dừng; FORCE_RELEASE=1 để bỏ qua." >&2; exit 1; }
    if [ -d runs ] && [ -n "${R2_REMOTE:-}" ]; then
      uv run --project experiments python -m experiments.runner.backup check \
        || { echo "runs/ trên máy này chưa sao lưu đủ. Dừng; FORCE_RELEASE=1 để bỏ qua." >&2; exit 1; }
    fi
  fi
  dph=$(vastai show instance "$id" --raw | jq -r '.dph_total')
  start=$(cat "$STATE/rented_at"); hours=$(echo "scale=2; ($(date -u +%s) - $start) / 3600" | bc)
  read -r -p "Huỷ instance $id? Dữ liệu trên VM sẽ mất. Gõ yes: " ok
  [ "$ok" = yes ] || exit 1
  vastai destroy instance "$id"
  echo "$(date -u +%FT%TZ) instance=$id mode=$(cat "$STATE/mode") hours=$hours dph=$dph cost≈$(echo "$hours * $dph" | bc)" \
    | tee -a "$STATE/cost.log"
  rm -f "$STATE/instance_id" "$STATE/mode" "$STATE/rented_at"
}

# Gọi hàm theo lệnh: `vast.sh rent 123 v0` → cmd_rent 123 v0. "${@:2}" = mọi tham số từ thứ 2 trở đi.
# `${1:?…}` = báo lỗi kèm danh sách lệnh nếu không truyền tham số nào.
"cmd_${1:?lệnh: find|rent|wait|probe|inventory|platform|ssh|tunnel|runner-start|status|release}" "${@:2}"
