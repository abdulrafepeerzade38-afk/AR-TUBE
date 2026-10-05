# AR TUBE V17

Desktop-style AR TUBE for Termux:X11.

## Highlights
- Premium 10-second animated AR TUBE BOOTING screen.
- Interactive Tk/X11 interface after boot.
- YouTube Data API search using `YOUTUBE_API_KEY`.
- Thumbnail cards and Play/Download buttons.
- One active MPV player; starting another stops the previous one.
- Uses Termux `mpv-x` with the supported `auto` GPU context; removes the unsupported `x11egl`/OpenGL flags from V16.
- Landscape 16:9 layout.
- Downloads to `/sdcard/Download/ARTube` as MP4.

## Run
```bash
pkg update -y && pkg install git -y && git clone https://github.com/abdulrafepeerzade38-afk/AR-TUBE.git ~/AR-TUBE && cd ~/AR-TUBE && bash install.sh
```
