#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# infra/provision/probe.sh
# Khái niệm: Kiểm nhanh một VM vừa thuê: phần cứng, driver, vị trí, mạng thật, tốc độ ghi ổ. Chạy NGAY trên
#            VM (`make probe` đẩy script qua SSH), không cài gì, không đổi gì ngoài một file thử tự xoá.
# Mục đích:  Quyết định giữ hay trả máy TRƯỚC khi bootstrap. Ngày 08/11, cột `inet_down` của Vast không
#            phản ánh mạng thật: máy đầu tiên tải chỉ ~8 MB/s và phải bỏ, máy thứ hai 93,9 MB/s.
# Tham khảo: log phiên 08/11 §1 (docs/nhat-ky/lam-viec/quang/phien-2026-11-08-a4000.md)
# ──────────────────────────────────────────────────────────────────────────────
set -uo pipefail   # không dùng -e: một phép đo lỗi (ví dụ chưa có /mnt/nvme) không được làm mất các phép đo sau

echo "== GPU"
# Tốc độ PCIe lệch giữa các GPU sẽ làm các replica không đồng đều, nên in cả link gen và width
nvidia-smi --query-gpu=index,name,memory.total,driver_version,pcie.link.gen.current,pcie.link.width.current,pcie.link.width.max --format=csv,noheader
echo "== CUDA (image vLLM v0.31.0 cần CUDA 13, driver ≥ 580)"
nvidia-smi | grep -o 'CUDA Version: [0-9.]*'
echo "== CPU (cần ≥ 8 + 3 × số GPU vCPU, xem query() trong vast.sh)"
lscpu | grep -E '^(Model name|CPU\(s\)|Thread|Core|Socket)'
echo "== RAM"
free -g | awk '/Mem/{print $2" GB total, "$7" GB avail"}'
echo "== OS"
# shellcheck source=/dev/null
. /etc/os-release; echo "$PRETTY_NAME, kernel $(uname -r)"
echo "== Disk"
df -h / /mnt/nvme 2>/dev/null | tail -n +2
echo "== Vị trí"
# Tránh host ở Trung Quốc: 08/11 máy ở đó mạng 8 MB/s, cold start ~6 phút. grep chỉ giữ thành phố/nước/ISP.
curl -s -m 5 https://ipinfo.io/json | grep -E '"(city|region|country|org)"' | tr -d '\n'; echo
echo "== unattended-upgrades (phải tắt, nếu không có thể nâng driver giữa chừng như 08/11)"
# [u]: mẫu không khớp chính dòng lệnh này, tránh lỗi pgrep -f tự khớp đã gặp 08/11
pgrep -fa '[u]nattended-upgrade' | head -2 || echo none
echo "== Docker Hub"
curl -s -o /dev/null -m 8 -w "registry-1.docker.io HTTP %{http_code} in %{time_total}s\n" https://registry-1.docker.io/v2/ \
  || echo "registry-1.docker.io FAIL (group_vars cloud đã dùng mirror.gcr.io)"
echo "== Mạng: tải tối đa 20 s từ Hugging Face"
# -w in byte/giây; awk đổi sang MB/s. Đích tiêu chí ≥ 30 MB/s: model 5,8 GB khoảng 3 phút.
curl -sL -o /dev/null -m 20 -w '%{speed_download} %{size_download} %{time_total}\n' \
  "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/resolve/main/model-00001-of-00002.safetensors" \
  | awk '{printf "HF: %.1f MB/s (%.0f MB in %s s)\n", $1/1e6, $2/1e6, $3}'
echo "== Ghi ổ tuần tự (oflag=direct = bỏ qua page cache, đo đúng ổ)"
dd if=/dev/zero of=/root/.probe-ddtest bs=1M count=2000 oflag=direct 2>&1 | tail -1
rm -f /root/.probe-ddtest
