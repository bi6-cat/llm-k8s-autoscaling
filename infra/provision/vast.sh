#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# infra/provision/vast.sh
# Khái niệm: Script bọc CLI `vastai` (công cụ dòng lệnh của Vast.ai) cho cả vòng đời một máy thuê:
#            tìm offer → thuê → chờ → sinh inventory Ansible → SSH/tunnel → huỷ.
# Mục đích:  Cô lập phần phụ thuộc nhà cung cấp vào MỘT file; đổi sang GCP chỉ phải viết lại file này.
#            Ghi trạng thái vào .vast/ để không bao giờ quên một máy đang tính tiền.
# Dùng:      vast.sh find v0|v2 | rent <offer_id> v0|v2 | wait | inventory | ssh | tunnel | status | release
#            (thường gọi qua Makefile: make find / rent / bootstrap / release)
# Cần:       vastai (đã `vastai set api-key`), jq, bc, ssh; VAST_VM_TEMPLATE trong .env
# Tham khảo: docs/huong-dan/w2.md §11.2
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
if [ -f .env ]; then set -a; . ./.env; set +a; fi

# ── Hàm phụ ──────────────────────────────────────────────────────────────────

# Tiêu chí lọc offer theo cú pháp của `vastai search offers`.
#   v0: 1 × 4090 để thử (12 lõi, 48 GB RAM, 150 GB ổ).
#   v2: 4 × 4090 cho đợt đánh giá; thêm disk_bw ≥ 1000 MB/s (cold start L2) và giá ≤ 2 USD/giờ.
# vms_enabled=true: chỉ máy cho thuê chế độ VM (có systemd, chạy được k3s), không phải container.
# reliability > 0.98: tỷ lệ máy chạy ổn định theo thống kê của Vast.
query() {
  case "$1" in
    v0) echo 'num_gpus=1 gpu_name=RTX_4090 vms_enabled=true rentable=true reliability>0.98 cpu_cores_effective>=12 cpu_ram>=48 disk_space>=150 inet_down>=500' ;;
    v2) echo 'num_gpus=4 gpu_name=RTX_4090 vms_enabled=true rentable=true reliability>0.98 cpu_cores_effective>=32 cpu_ram>=128 disk_space>=300 disk_bw>=1000 inet_down>=500 dph_total<=2.0' ;;
    *) echo "MODE phải là v0 hoặc v2" >&2; exit 2 ;;
  esac
}
# Dung lượng ổ (GB) xin khi thuê: model 7B + image vLLM + dữ liệu đánh giá
disk_gb() { if [ "$1" = v2 ]; then echo 300; else echo 150; fi; }
# ID instance đang thuê; dừng script nếu chưa thuê
instance_id() { cat "$STATE/instance_id" 2>/dev/null || { echo "Chưa có instance (.vast/instance_id)" >&2; exit 1; }; }
# Đổi "ssh://root@host:port" (vastai ssh-url in ra) thành "host port" để đọc bằng `read -r host port`
ssh_target() {
  vastai ssh-url "$(instance_id)" | sed -E 's#ssh://[^@]+@([^:]+):([0-9]+).*#\1 \2#'
}

# ── Các lệnh ─────────────────────────────────────────────────────────────────
# Mỗi lệnh là một hàm cmd_<tên>; dòng cuối file gọi hàm theo tham số đầu tiên.

# In 5 offer rẻ nhất (-o dph_total = sắp theo giá/giờ). jq định dạng mỗi offer thành một dòng:
# id, số GPU, giá (làm tròn 2 số), độ tin cậy %, CPU, RAM (GB), tốc độ đọc ổ, vị trí.
cmd_find() {
  vastai search offers "$(query "${1:?v0|v2}")" -o 'dph_total' --raw | jq -r '.[:5][] |
    "\(.id)\t\(.num_gpus)x\(.gpu_name)\t$\(.dph_total*100|round/100)/h\trel=\((.reliability2 // .reliability)*100|round)%\tcpu=\(.cpu_cores_effective)\tram=\(.cpu_ram/1024|round)GB\tdisk_bw=\(.disk_bw|round)MB/s\t\(.geolocation)"'
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
  local id st; id=$(instance_id)
  for _ in $(seq 1 90); do
    st=$(vastai show instance "$id" --raw | jq -r '.actual_status')
    echo "$(date +%T) $st"
    [ "$st" = running ] && break
    sleep 20
  done
  read -r host port < <(ssh_target)
  until ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -p "$port" "root@$host" true 2>/dev/null; do
    echo "$(date +%T) chờ SSH…"; sleep 10
  done
  echo "SSH sẵn sàng: ssh -p $port root@$host"
}

# Sinh inventory Ansible cho máy đang thuê. VM duy nhất vừa là k3s_server vừa chạy GPU.
# Nhóm `cloud` → Ansible tự nạp inventory/group_vars/cloud.yaml.
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

# Mở shell trên VM. `exec` thay tiến trình script bằng ssh (Ctrl-D là thoát luôn).
cmd_ssh() { local host port; read -r host port < <(ssh_target); exec ssh -p "$port" "root@$host"; }

# SSH tunnel: cổng 16443 trên laptop → cổng 6443 (API server) trên VM. -N = không mở shell, chỉ chuyển
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
  local id dph start hours; id=$(instance_id)
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
"cmd_${1:?lệnh: find|rent|wait|inventory|ssh|tunnel|status|release}" "${@:2}"
