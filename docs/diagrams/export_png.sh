#!/usr/bin/env bash
# Xuất mọi docs/images/*.svg sang PNG độ phân giải 2x (dùng cho Word/slide) bằng Chrome headless.
# Dùng: bash docs/diagrams/export_png.sh   (biến CHROME để chỉ định trình duyệt khác; mặc định là chỗ cài
#       Chrome thường gặp trên macOS, hoặc trên Windows khi chạy bằng Git Bash)
set -euo pipefail
cd "$(dirname "$0")/../images"
mkdir -p png
# Chrome cần đường dẫn tuyệt đối theo kiểu của hệ điều hành nó chạy. Trên Windows (Git Bash) $PWD có dạng
# /d/..., Chrome không mở được file:///d/... và ghi --screenshot tương đối ra chỗ khác, không báo lỗi;
# cygpath -m đổi thành D:/...
dir="$PWD"
url="file://$PWD"
default_chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if command -v cygpath >/dev/null 2>&1; then
  dir="$(cygpath -m "$PWD")"
  url="file:///$dir"
  default_chrome="/c/Program Files/Google/Chrome/Application/chrome.exe"
fi
CHROME="${CHROME:-$default_chrome}"
[ -x "$CHROME" ] || { echo "lỗi: không chạy được Chrome ở '$CHROME'; đặt biến CHROME" >&2; exit 1; }
for svg in *.svg; do
  w=$(sed -n 's/.*<svg[^>]* width="\([0-9]*\)".*/\1/p' "$svg" | head -1)
  h=$(sed -n 's/.*<svg[^>]* height="\([0-9]*\)".*/\1/p' "$svg" | head -1)
  png="png/${svg%.svg}.png"
  # Ghi ra file tạm rồi mới thay PNG cũ: lần xuất hỏng giữ nguyên PNG đã commit và báo lỗi, thay vì để lại
  # file cũ như thể đã xuất xong (Chrome lỗi vẫn có thể thoát 0, nên kiểm file chứ không kiểm mã thoát).
  tmp="png/.${svg%.svg}.tmp.png"
  rm -f "$tmp"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size="$w,$h" --screenshot="$dir/$tmp" "$url/$svg" >/dev/null 2>&1 || true
  [ -s "$tmp" ] || { rm -f "$tmp"; echo "lỗi: Chrome không ghi được $png" >&2; exit 1; }
  mv -f "$tmp" "$png"
  echo "$png (${w}x${h} @2x)"
done
