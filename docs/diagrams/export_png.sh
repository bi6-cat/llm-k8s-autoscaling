#!/usr/bin/env bash
# Xuất mọi docs/images/*.svg sang PNG độ phân giải 2x (dùng cho Word/slide) bằng Chrome headless.
# Dùng: bash docs/diagrams/export_png.sh   (biến CHROME để chỉ định trình duyệt khác)
set -euo pipefail
cd "$(dirname "$0")/../images"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p png
# Chrome cần đường dẫn tuyệt đối theo kiểu của hệ điều hành nó chạy. Trên Windows (Git Bash) $PWD có dạng
# /d/..., Chrome không mở được file:///d/... và ghi --screenshot tương đối ra chỗ khác, không báo lỗi;
# cygpath -m đổi thành D:/...
dir="$PWD"
url="file://$PWD"
if command -v cygpath >/dev/null 2>&1; then
  dir="$(cygpath -m "$PWD")"
  url="file:///$dir"
fi
for svg in *.svg; do
  w=$(sed -n 's/.*<svg[^>]* width="\([0-9]*\)".*/\1/p' "$svg" | head -1)
  h=$(sed -n 's/.*<svg[^>]* height="\([0-9]*\)".*/\1/p' "$svg" | head -1)
  png="png/${svg%.svg}.png"
  # Xoá PNG cũ trước, để lần xuất hỏng (Chrome không ghi được) không bị che bởi file của lần trước
  rm -f "$png"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size="$w,$h" --screenshot="$dir/$png" "$url/$svg" >/dev/null 2>&1
  [ -s "$png" ] || { echo "lỗi: Chrome không ghi được $png" >&2; exit 1; }
  echo "$png (${w}x${h} @2x)"
done
