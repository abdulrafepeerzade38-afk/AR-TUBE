#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "================================"
echo "        AR TUBE INSTALLER"
echo "================================"

cd "$(dirname "$0")"

echo "[1/7] Updating Termux..."
pkg update -y

echo "[2/7] Installing repositories..."
pkg install x11-repo -y
pkg install tur-repo -y

echo "[3/7] Installing required packages..."
pkg install python python-pip ffmpeg yt-dlp mpv-x termux-x11-nightly -y

echo "[4/7] Installing Python packages..."
python -m pip install --upgrade pip
python -m pip install requests pillow

echo "[5/7] Creating AR TUBE storage..."
mkdir -p ~/storage/downloads/ARTube
mkdir -p ~/storage/downloads/ARTube/cache

echo "[6/7] Creating configuration..."

if [ ! -f .env ]; then
    echo "YOUTUBE_API_KEY=" > .env
    echo "Created .env"
fi

chmod +x install.sh
chmod +x start.sh 2>/dev/null || true
chmod +x desktop.sh 2>/dev/null || true

echo
echo "================================"
echo "       INSTALLATION DONE"
echo "================================"
echo
echo "Starting AR TUBE..."
echo

bash start.sh
