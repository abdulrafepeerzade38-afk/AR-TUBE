#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"

export DISPLAY=:1

pkill -f "python.*main.py" 2>/dev/null || true

termux-x11 :1 >/dev/null 2>&1 &
sleep 3

exec python main.py
