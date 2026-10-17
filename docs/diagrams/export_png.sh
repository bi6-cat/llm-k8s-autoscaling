#!/usr/bin/env bash
# Xuất mọi docs/images/*.svg sang PNG độ phân giải 2x (dùng cho Word/slide) bằng Chrome headless.
# Dùng: bash docs/diagrams/export_png.sh   (biến CHROME để chỉ định trình duyệt khác)
set -euo pipefail
cd "$(dirname "$0")/../images"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p png
for svg in *.svg; do
  w=$(sed -n 's/.*<svg[^>]* width="\([0-9]*\)".*/\1/p' "$svg" | head -1)
  h=$(sed -n 's/.*<svg[^>]* height="\([0-9]*\)".*/\1/p' "$svg" | head -1)
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size="$w,$h" --screenshot="png/${svg%.svg}.png" "file://$PWD/$svg" >/dev/null 2>&1
  echo "png/${svg%.svg}.png (${w}x${h} @2x)"
done
