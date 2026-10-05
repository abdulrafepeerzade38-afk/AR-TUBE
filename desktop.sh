#!/data/data/com.termux/files/usr/bin/bash
set -u
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
export DISPLAY="${DISPLAY:-:1}"

cleanup() {
  pkill -TERM -P $$ 2>/dev/null || true
  pkill -TERM -x mpv 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP

if ! command -v termux-x11 >/dev/null 2>&1; then
  echo "termux-x11 is not installed."
  echo "Install: pkg install x11-repo termux-x11-nightly -y"
  exit 1
fi

if ! pgrep -f "termux-x11 :1" >/dev/null 2>&1; then
  termux-x11 :1 -legacy-drawing >/dev/null 2>&1 &
  sleep 2
fi

python "$APP_DIR/main.py"
