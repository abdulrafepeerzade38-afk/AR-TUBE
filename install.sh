#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"

pkg update -y
pkg install x11-repo tur-repo -y
pkg install python python-pip ffmpeg yt-dlp mpv-x termux-x11-nightly -y

python -m pip install requests pillow

termux-setup-storage

mkdir -p ~/storage/downloads/ARTube

[ -f .env ] || printf 'YOUTUBE_API_KEY=\n' > .env

chmod +x install.sh start.sh desktop.sh

echo "AR TUBE installation complete."
bash start.sh
