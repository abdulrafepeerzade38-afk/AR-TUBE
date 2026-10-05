#!/usr/bin/env python3
import os, signal, subprocess, shutil, threading, time, ctypes
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests

APP = "AR TUBE"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
DOWNLOADS = Path("/sdcard/Download/ARTube")
CACHE = Path.home() / ".artube_v16_cache"
CACHE.mkdir(parents=True, exist_ok=True)
DOWNLOADS.mkdir(parents=True, exist_ok=True)

BG = "#070910"
PANEL = "#0D1220"
CARD = "#111827"
CARD2 = "#151D2E"
TEXT = "#F7F9FF"
MUTED = "#8F9BB2"
CYAN = "#20D9FF"
PURPLE = "#8B5CF6"
PINK = "#FF4FD8"
BORDER = "#263149"
RED = "#FF4B67"

def pdeathsig():
    try:
        libc = ctypes.CDLL(None)
        libc.prctl(1, signal.SIGTERM)
    except Exception:
        pass

class ARTube(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AR TUBE")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.player = None
        self.player_started = False
        self.results = []
        self.thumb_refs = []
        self.current = None
        self.query = tk.StringVar()
        self.status = tk.StringVar(value="BOOTING…")
        self.fullscreen = False
        self.booting = True
        try:
            self.geometry("1280x720")
            self.resizable(False, False)
            try: self.wm_aspect(16, 9, 16, 9)
            except Exception: pass
        except Exception:
            self.geometry("1280x720")
        try:
            self.configure(cursor="left_ptr")
        except Exception:
            pass
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.stop_only)
        self._show_boot()
        self.after(700, self.watch_x11)
        self.after(250, lambda: self.focus_force())
        # Keep the premium boot screen visible for a full 10 seconds.
        self.after(10000, self._finish_boot)

    def _show_boot(self):
        self.boot_frame = tk.Frame(self, bg="#05060A")
        self.boot_frame.pack(fill="both", expand=True)
        c = tk.Canvas(self.boot_frame, bg="#05060A", highlightthickness=0)
        c.pack(fill="both", expand=True)
        self.boot_canvas = c
        c.create_text(640, 245, text="⚡", fill=CYAN, font=("TkDefaultFont", 54, "bold"), tags="logo")
        c.create_text(640, 315, text="AR TUBE", fill=TEXT, font=("TkDefaultFont", 34, "bold"), tags="title")
        c.create_text(640, 360, text="NEXT-GENERATION VIDEO EXPERIENCE", fill=MUTED, font=("TkDefaultFont", 10, "bold"), tags="sub")
        c.create_rectangle(420, 415, 860, 427, outline=BORDER, fill="#0C1020", width=1, tags="barbg")
        c.create_rectangle(420, 415, 420, 427, outline="", fill=PURPLE, tags="bar")
        c.create_text(640, 458, text="BOOTING", fill=CYAN, font=("TkDefaultFont", 12, "bold"), tags="boottext")
        c.create_text(640, 490, text="Initializing AR TUBE services…", fill=MUTED, font=("TkDefaultFont", 9), tags="detail")
        self._boot_start = time.monotonic()
        self._boot_tick()

    def _boot_tick(self):
        if not getattr(self, "booting", False):
            return
        elapsed = time.monotonic() - self._boot_start
        progress = min(1.0, elapsed / 10.0)
        x2 = 420 + 440 * progress
        try:
            self.boot_canvas.coords("bar", 420, 415, x2, 427)
            dots = "." * (int(elapsed * 2) % 4)
            self.boot_canvas.itemconfigure("boottext", text="BOOTING" + dots)
            stages = [
                "Initializing AR TUBE services…",
                "Loading video engine…",
                "Preparing YouTube search…",
                "Preparing player…",
                "Almost ready…",
            ]
            self.boot_canvas.itemconfigure("detail", text=stages[min(4, int(progress * 5))])
            self.after(100, self._boot_tick)
        except tk.TclError:
            pass

    def _finish_boot(self):
        if not self.booting:
            return
        self.booting = False
        try:
            self.boot_frame.destroy()
        except Exception:
            pass
        self._build()
        self.show_home()
        self.status.set("Ready")
        self.after(250, lambda: self.focus_force())

    def _build(self):
        top = tk.Frame(self, bg=PANEL, height=64)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="AR", bg=PANEL, fg=CYAN, font=("TkDefaultFont", 23, "bold")).pack(side="left", padx=(18,2))
        tk.Label(top, text="TUBE", bg=PANEL, fg=TEXT, font=("TkDefaultFont", 23, "bold")).pack(side="left")
        searchbox = tk.Frame(top, bg=CARD2, highlightthickness=1, highlightbackground=BORDER)
        searchbox.pack(side="left", fill="x", expand=True, padx=22, pady=11)
        self.entry = tk.Entry(searchbox, textvariable=self.query, bg=CARD2, fg=TEXT,
                              insertbackground=CYAN, selectbackground=PURPLE, relief="flat",
                              font=("TkDefaultFont", 13))
        self.entry.pack(side="left", fill="both", expand=True, padx=12)
        self.entry.bind("<Return>", lambda e: self.search())
        tk.Button(searchbox, text="SEARCH", command=self.search, bg=PURPLE, fg="white",
                  activebackground=CYAN, activeforeground=BG, relief="flat", bd=0,
                  font=("TkDefaultFont", 9, "bold"), padx=14).pack(side="right", fill="y")
        tk.Button(top, text="✕", command=self.close, bg=PANEL, fg=RED, relief="flat", bd=0,
                  font=("TkDefaultFont", 18, "bold"), width=3).pack(side="right")
        tk.Button(top, text="⛶", command=self.toggle_fullscreen, bg=PANEL, fg=TEXT,
                  relief="flat", bd=0, font=("TkDefaultFont", 18)).pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        side = tk.Frame(body, bg=PANEL, width=185)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        for label, cmd in [
            ("⌂  HOME", self.show_home),
            ("🔥  TRENDING", lambda: self.do_query("trending 2026")),
            ("♫  MUSIC", lambda: self.do_query("new music 2026")),
            ("🎮  GAMING", lambda: self.do_query("gaming 2026")),
            ("⬇  DOWNLOADS", self.downloads_page),
            ("▶  PLAYER", self.player_page),
        ]:
            b=tk.Button(side,text=label,command=cmd,bg=PANEL,fg=TEXT,activebackground=PURPLE,
                        activeforeground="white",relief="flat",bd=0,anchor="w",
                        padx=18,pady=13,font=("TkDefaultFont",10,"bold"))
            b.pack(fill="x", pady=1)
        tk.Label(side,text="AR TUBE • V17",bg=PANEL,fg=MUTED,font=("TkDefaultFont",8,"bold")).pack(side="bottom",pady=12)

        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        self.scroll = tk.Scrollbar(main, orient="vertical", command=self.canvas.yview)
        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(self.canvas, bg=BG)
        self.window = self.canvas.create_window((0,0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window,width=e.width))
        self.canvas.bind_all("<MouseWheel>", self.wheel)
        self.canvas.bind_all("<Button-4>", lambda e:self.canvas.yview_scroll(-3,"units"))
        self.canvas.bind_all("<Button-5>", lambda e:self.canvas.yview_scroll(3,"units"))

        bottom=tk.Label(self,textvariable=self.status,bg="#090D16",fg=MUTED,anchor="w",padx=12,font=("TkDefaultFont",8))
        bottom.pack(fill="x")

    def wheel(self,e): self.canvas.yview_scroll(int(-e.delta/120),"units")

    def clear(self):
        self.stop_player()
        for w in self.content.winfo_children(): w.destroy()
        self.thumb_refs=[]

    def show_home(self):
        self.clear()
        hero=tk.Frame(self.content,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        hero.pack(fill="x",padx=18,pady=18)
        tk.Label(hero,text="YOUR VIDEO WORLD",bg=PANEL,fg=CYAN,font=("TkDefaultFont",25,"bold")).pack(anchor="w",padx=22,pady=(18,2))
        tk.Label(hero,text="Fast search • clean player • downloads • one active video",bg=PANEL,fg=MUTED,font=("TkDefaultFont",10)).pack(anchor="w",padx=22,pady=(0,18))
        self.do_query("popular music 2026")

    def do_query(self,q):
        self.query.set(q)
        self.search()

    def search(self):
        q=self.query.get().strip()
        if not q: return
        if not API_KEY:
            messagebox.showerror("YouTube API key","Set YOUTUBE_API_KEY in Termux before starting AR TUBE.")
            return
        self.status.set("Searching YouTube…")
        threading.Thread(target=self.search_worker,args=(q,),daemon=True).start()

    def search_worker(self,q):
        try:
            r=requests.get("https://www.googleapis.com/youtube/v3/search",
                params={"part":"snippet","q":q,"type":"video","maxResults":24,"key":API_KEY},timeout=15)
            r.raise_for_status()
            data=r.json()
            arr=[]
            for x in data.get("items",[]):
                vid=x.get("id",{}).get("videoId")
                sn=x.get("snippet",{})
                if vid: arr.append({"id":vid,"title":sn.get("title",""),"channel":sn.get("channelTitle","")})
            self.after(0,lambda:self.render_results(arr,q))
        except Exception as e:
            self.after(0,lambda:messagebox.showerror("Search error",str(e)))
            self.after(0,lambda:self.status.set("Search failed"))

    def render_results(self,arr,q):
        self.clear()
        tk.Label(self.content,text=q,bg=BG,fg=TEXT,font=("TkDefaultFont",21,"bold")).pack(anchor="w",padx=18,pady=(18,4))
        tk.Label(self.content,text=f"{len(arr)} results",bg=BG,fg=MUTED,font=("TkDefaultFont",9)).pack(anchor="w",padx=18,pady=(0,8))
        grid=tk.Frame(self.content,bg=BG); grid.pack(fill="x",padx=18)
        for i,item in enumerate(arr):
            self.card(grid,item,i//3,i%3)
        self.status.set("Ready")

    def card(self,parent,item,row,col):
        f=tk.Frame(parent,bg=CARD,highlightthickness=1,highlightbackground=BORDER)
        f.grid(row=row,column=col,sticky="nsew",padx=5,pady=5)
        parent.grid_columnconfigure(col,weight=1)
        thumb_area=tk.Frame(f,bg="#05070B",height=180)
        thumb_area.pack(fill="x",padx=1,pady=1)
        thumb_area.pack_propagate(False)
        thumb=tk.Label(thumb_area,bg="#05070B",text="LOADING…",fg=MUTED,bd=0)
        thumb.pack(fill="both",expand=True)
        title=tk.Label(f,text=item["title"],bg=CARD,fg=TEXT,justify="left",anchor="w",
                       wraplength=280,font=("TkDefaultFont",9,"bold"))
        title.pack(fill="x",padx=9,pady=(7,2))
        tk.Label(f,text=item["channel"],bg=CARD,fg=MUTED,anchor="w",font=("TkDefaultFont",8)).pack(fill="x",padx=9)
        rowb=tk.Frame(f,bg=CARD); rowb.pack(fill="x",padx=8,pady=8)
        tk.Button(rowb,text="▶ PLAY",command=lambda x=item:self.play(x),bg=PURPLE,fg="white",
                  activebackground=CYAN,relief="flat",bd=0,padx=10,pady=5).pack(side="left")
        tk.Button(rowb,text="↓ DOWNLOAD",command=lambda x=item:self.download(x),bg=CARD2,fg=TEXT,
                  activebackground=CYAN,relief="flat",bd=0,padx=8,pady=5).pack(side="right")
        for w in (f,thumb_area,thumb,title):
            w.bind("<Button-1>",lambda e,x=item:self.play(x))
        threading.Thread(target=self.thumb_worker,args=(item["id"],thumb),daemon=True).start()

    def thumb_worker(self,vid,widget):
        urls=[
            f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
            f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"
        ]
        for u in urls:
            try:
                p=CACHE/f"{vid}.jpg"
                r=requests.get(u,headers={"User-Agent":"Mozilla/5.0"},timeout=8)
                r.raise_for_status()
                p.write_bytes(r.content)
                im=Image.open(p).convert("RGB")
                # YouTube thumbnails are 16:9; render them at a fixed 320x180 card area.
                im=im.resize((320,180),Image.LANCZOS)
                photo=ImageTk.PhotoImage(im)
                self.after(0,lambda w=widget,ph=photo:self.set_thumb(w,ph))
                return
            except Exception: continue
        self.after(0,lambda:self.thumb_failed(widget))

    def set_thumb(self,w,photo):
        try:
            if w.winfo_exists():
                w.configure(image=photo,text="")
                self.thumb_refs.append(photo)
        except Exception: pass

    def thumb_failed(self,w):
        try: w.configure(text="THUMBNAIL UNAVAILABLE",fg=MUTED)
        except: pass

    def player_page(self):
        self.clear()
        box=tk.Frame(self.content,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        box.pack(fill="x",padx=18,pady=18)
        tk.Label(box,text="AR TUBE PLAYER",bg=PANEL,fg=CYAN,font=("TkDefaultFont",11,"bold")).pack(anchor="w",padx=14,pady=(12,4))
        tk.Label(box,text="Video opens in the dedicated X11 MPV surface for reliable rendering.",bg=PANEL,fg=MUTED,font=("TkDefaultFont",9)).pack(anchor="w",padx=14,pady=(0,12))
        area=tk.Frame(box,bg="#000000",height=400); area.pack(fill="x",padx=12,pady=(0,12)); area.pack_propagate(False)
        msg = "Select a video and press PLAY" if not self.current else "Starting video…"
        tk.Label(area,text=msg,bg="#000000",fg=MUTED,font=("TkDefaultFont",14)).place(relx=.5,rely=.5,anchor="center")

    def play(self,item):
        self.stop_player()
        self.current=item
        self.player_page()
        self.status.set("Starting video…")
        threading.Thread(target=self.start_player,args=(item,),daemon=True).start()

    def start_player(self,item):
        mpv=shutil.which("mpv"); ytdlp=shutil.which("yt-dlp")
        if not mpv or not ytdlp:
            msg="Install required packages:\npkg install mpv ffmpeg -y\npip install -U yt-dlp"
            self.after(0,lambda:messagebox.showerror("Player setup",msg))
            self.after(0,lambda:self.status.set("Player dependencies missing"))
            return
        url="https://www.youtube.com/watch?v="+item["id"]
        self.after(0,lambda:self.status.set("Loading video…"))
        # Use one combined stream whenever possible. This avoids the previous
        # audio-only symptom caused by separate video/audio selection.
        fmt="best[height<=720][ext=mp4]/best[height<=720]/best"
        # mpv-x on Termux exposes only the auto GPU context. Do not pass
        # desktop-only x11egl/opengl flags: those made V16 exit immediately.
        cmd=[mpv,
             "--no-terminal","--force-window=yes","--keep-open=no",
             "--no-border","--ontop","--no-osc",
             "--hwdec=no",
             "--vo=gpu","--gpu-context=auto",
             "--autofit=1280x720","--geometry=1280x720+0+0",
             "--title=AR TUBE PLAYER",
             "--ytdl-format="+fmt]
        if shutil.which("deno"):
            cmd.append("--ytdl-raw-options=js-runtimes=deno")
        cmd.append(url)
        try:
            p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                               start_new_session=True,preexec_fn=pdeathsig,text=True)
            self.player=p
            self.after(350,self.check_player)
        except Exception as e:
            self.after(0,lambda:messagebox.showerror("MPV error",str(e)))
            self.after(0,lambda:self.status.set("Player failed to start"))

    def check_player(self):
        p=self.player
        if not p:return
        rc=p.poll()
        if rc is None:
            self.status.set("▶ Playing — one active player")
            self.after(900,self.check_player)
            return
        err=""
        try: err=(p.stderr.read() or "")[-2200:]
        except: pass
        self.player=None
        self.status.set("Player stopped")
        if err:
            self.after(0,lambda e=err:messagebox.showerror("MPV stopped",e))

    def stop_player(self):
        p=self.player; self.player=None
        if not p:return
        try: os.killpg(p.pid,signal.SIGTERM)
        except: pass
        try:p.wait(timeout=.7)
        except:
            try:os.killpg(p.pid,signal.SIGKILL)
            except:pass

    def stop_only(self,e=None):
        self.stop_player()
        self.status.set("Player stopped")
        return "break"

    def downloads_page(self):
        self.clear()
        tk.Label(self.content,text="DOWNLOADS",bg=BG,fg=TEXT,font=("TkDefaultFont",22,"bold")).pack(anchor="w",padx=18,pady=18)
        tk.Label(self.content,text=str(DOWNLOADS),bg=BG,fg=MUTED,font=("TkDefaultFont",10)).pack(anchor="w",padx=18)
        try:
            files=list(DOWNLOADS.glob("*"))
        except: files=[]
        for f in files[:100]:
            tk.Label(self.content,text=f"• {f.name}",bg=BG,fg=TEXT,anchor="w").pack(fill="x",padx=25,pady=3)

    def download(self,item):
        if not shutil.which("yt-dlp"):
            messagebox.showerror("yt-dlp","pip install -U yt-dlp"); return
        self.status.set("Downloading…")
        threading.Thread(target=self.download_worker,args=(item,),daemon=True).start()

    def download_worker(self,item):
        # Always produce a final file named exactly "<YouTube title>.mp4".
        # yt-dlp may use temporary .part/.f* files internally, but they are
        # removed after a successful merge.
        template=str(DOWNLOADS/"%(title)s.%(ext)s")
        url="https://www.youtube.com/watch?v="+item["id"]
        cmd=["yt-dlp",
             "--no-playlist",
             "--restrict-filenames",
             "-f","bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
             "--merge-output-format","mp4",
             "--recode-video","mp4",
             "--remux-video","mp4",
             "-o",template,
             url]
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=1800)
            if p.returncode==0:
                # Remove any accidental sidecar/temp files left in the target folder.
                for f in DOWNLOADS.iterdir():
                    if f.is_file() and f.suffix.lower() in {".part",".ytdl"}:
                        try:f.unlink()
                        except:pass
                self.after(0,lambda:self.status.set("Download complete — MP4"))
            else:
                err=(p.stderr or p.stdout or "Download failed")[-1200:]
                self.after(0,lambda e=err:messagebox.showerror("Download failed",e))
                self.after(0,lambda:self.status.set("Download failed"))
        except Exception as e:
            self.after(0,lambda e=str(e):messagebox.showerror("Download error",e))
            self.after(0,lambda:self.status.set("Download failed"))

    def watch_x11(self):
        try:
            self.winfo_screenwidth()
            self.after(700,self.watch_x11)
        except tk.TclError:
            self.kill_and_exit()

    def kill_and_exit(self):
        self.stop_player()
        os._exit(0)

    def toggle_fullscreen(self,e=None):
        try:
            self.fullscreen=not self.fullscreen
            if self.fullscreen:
                self.attributes("-fullscreen",True)
            else:
                self.attributes("-fullscreen",False)
                self.geometry("1280x720")
                self.resizable(False, False)
                try: self.wm_aspect(16,9,16,9)
                except Exception: pass
        except: pass
        return "break"

    def close(self):
        self.stop_player()
        self.destroy()

if __name__=="__main__":
    ARTube().mainloop()
