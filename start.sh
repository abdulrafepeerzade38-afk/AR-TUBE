#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")"

echo "================================"
echo "          AR TUBE"
echo "       Starting X11..."
echo "================================"

export DISPLAY=:1

# Stop old AR TUBE processes
pkill -f "python.*main.py" 2>/dev/null || true

# Start Termux:X11
termux-x11 :1 >/dev/null 2>&1 &

sleep 3

echo "Starting AR TUBE GUI..."

python main.py
