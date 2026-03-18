import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, os, json, time, uuid, datetime
import psutil

VERSION      = "3.0.0"
FONT         = "Bahnschrift"  # DIN-style, libre, Windows 10/11
CONFIG_FILE  = os.path.expanduser("~/yt-dlp-config.json")
HISTORY_FILE = os.path.expanduser("~/yt-dlp-history.json")
QUEUE_FILE   = os.path.expanduser("~/yt-dlp-queue.json")

def load_config():
    d = {"output_dir": os.path.expanduser("~/Downloads/YT-DLP"),
         "language": "fr", "theme": "auto", "max_concurrent": 3}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            try: d.update(json.load(f))
            except: pass
    return d

def save_config(c):
    with open(CONFIG_FILE, "w") as f: json.dump(c, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            try: return json.load(f)
            except: return []
    return []

def save_history(e):
    h = load_history(); h.insert(0, e); h = h[:100]
    with open(HISTORY_FILE, "w") as f: json.dump(h, f)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            try: return json.load(f)
            except: return []
    return []

def save_queue(jobs_dict):
    items = []
    for job_id, row in jobs_dict.items():
        items.append({
            "job_id": job_id, "url": row.url, "mode": row.mode,
            "title": getattr(row, "last_title", ""),
            "status": "done"        if getattr(row, "success", False)
                      else "stopped" if row.finished
                      else "interrupted"
        })
    with open(QUEUE_FILE, "w") as f: json.dump(items, f, indent=2)

PALETTES = {
    "dark": dict(
        bg="#2a2420",bg2="#332e28",bg3="#3d3630",bg4="#4a4238",
        fg="#F5EFE6",fg2="#a09080",
        accent="#9C7F67",green="#7a6a58",amber="#BDA18A",
        dark_btn="#4a4238",
        entry_bg="#3d3630",entry_fg="#F5EFE6",
        list_bg="#3d3630",sel_bg="#9C7F67",warn="#BDA18A"
    ),
    "light": dict(
        bg="#F5EFE6",bg2="#ede5da",bg3="#e0d5c8",bg4="#cfc3b4",
        fg="#2a2420",fg2="#7a6e64",
        accent="#9C7F67",green="#6a5a4a",amber="#BDA18A",
        dark_btn="#9a8a7a",
        entry_bg="#F5EFE6",entry_fg="#2a2420",
        list_bg="#ede5da",sel_bg="#9C7F67",warn="#BDA18A"
    )
}
C = dict(PALETTES["dark"])

def resolve_theme(setting):
    if setting == "auto":
        return "light" if 6 <= datetime.datetime.now().hour < 18 else "dark"
    return setting

def apply_palette(setting):
    global C
    C.update(PALETTES[resolve_theme(setting)])

LANG = "fr"
STRINGS = {
    "fr": dict(
        tab_dl="Telecharger",tab_hist="Historique",tab_set="Parametres",about_btn="i",
        url_lbl="URL",mp3="Audio MP3",mp4="Video MP4",pl_mp3="Playlist MP3",pl_mp4="Playlist MP4",
        queue_lbl="File de telechargements",clear_done="Effacer termines",no_dl="Aucun telechargement",
        s_dl="En cours...",s_done="Termine",s_pause="En pause",s_stop="Arrete",s_err="Erreur",
        s_interrupted="Interrompu",restart="Relancer",dismiss="X",url_empty="URL vide",
        hist_lbl="Telechargements recents",hist_clr="Effacer",hist_empty="  Aucun telechargement",
        confirm="Confirmer",confirm_clr="Effacer tout l'historique ?",
        set_lang="Langue",set_theme="Theme",theme_dark="Sombre",theme_light="Clair",theme_auto="Auto (heure)",
        set_max="Telechargements simultanes max",set_dir="Dossier de sortie",
        save="Enregistrer",saved="Enregistre",browse="...",about_title="A propos",about_ver="Version",
        about_desc="Telechargeur audio/video\nbased sur yt-dlp + ffmpeg",
        about_deps="Dependances : yt-dlp, ffmpeg, Python, psutil",
        active="actif(s)",restart_note="Redemarrez l'app pour appliquer les changements.",
        max_warning="Maximum de telechargements simultanes atteint.",
        restored_banner="Telechargements interrompus restaures - cliquez Relancer pour continuer."
    ),
    "en": dict(
        tab_dl="Download",tab_hist="History",tab_set="Settings",about_btn="i",
        url_lbl="URL",mp3="Audio MP3",mp4="Video MP4",pl_mp3="Playlist MP3",pl_mp4="Playlist MP4",
        queue_lbl="Download queue",clear_done="Clear finished",no_dl="No active downloads",
        s_dl="Downloading...",s_done="Done",s_pause="Paused",s_stop="Stopped",s_err="Error",
        s_interrupted="Interrupted",restart="Restart",dismiss="X",url_empty="Empty URL",
        hist_lbl="Recent downloads",hist_clr="Clear",hist_empty="  No downloads yet",
        confirm="Confirm",confirm_clr="Clear all history?",
        set_lang="Language",set_theme="Theme",theme_dark="Dark",theme_light="Light",theme_auto="Auto (time)",
        set_max="Max concurrent downloads",set_dir="Output folder",
        save="Save",saved="Saved",browse="...",about_title="About",about_ver="Version",
        about_desc="Audio/video downloader\nbased on yt-dlp + ffmpeg",
        about_deps="Dependencies: yt-dlp, ffmpeg, Python, psutil",
        active="active",restart_note="Restart the app to apply changes.",
        max_warning="Maximum concurrent downloads reached.",
        restored_banner="Interrupted downloads restored - click Restart to continue."
    ),
    "es": dict(
        tab_dl="Descargar",tab_hist="Historial",tab_set="Ajustes",about_btn="i",
        url_lbl="URL",mp3="Audio MP3",mp4="Video MP4",pl_mp3="Lista MP3",pl_mp4="Lista MP4",
        queue_lbl="Cola de descargas",clear_done="Borrar terminados",no_dl="Sin descargas activas",
        s_dl="Descargando...",s_done="Completado",s_pause="En pausa",s_stop="Detenido",s_err="Error",
        s_interrupted="Interrumpido",restart="Reanudar",dismiss="X",url_empty="URL vacia",
        hist_lbl="Descargas recientes",hist_clr="Borrar",hist_empty="  Sin descargas",
        confirm="Confirmar",confirm_clr="Borrar todo el historial?",
        set_lang="Idioma",set_theme="Tema",theme_dark="Oscuro",theme_light="Claro",theme_auto="Auto (hora)",
        set_max="Descargas simultaneas max.",set_dir="Carpeta de salida",
        save="Guardar",saved="Guardado",browse="...",about_title="Acerca de",about_ver="Version",
        about_desc="Descargador de audio/video\nbased en yt-dlp + ffmpeg",
        about_deps="Dependencias: yt-dlp, ffmpeg, Python, psutil",
        active="activo(s)",restart_note="Reinicia la app para aplicar los cambios.",
        max_warning="Limite de descargas simultaneas alcanzado.",
        restored_banner="Descargas interrumpidas restauradas - clic Reanudar para continuar."
    ),
    "ar": dict(
        tab_dl="تحميل",tab_hist="السجل",tab_set="الإعدادات",about_btn="i",
        url_lbl="الرابط",mp3="صوت MP3",mp4="فيديو MP4",pl_mp3="قائمة MP3",pl_mp4="قائمة MP4",
        queue_lbl="قائمة التحميل",clear_done="حذف المكتمل",no_dl="لا توجد تحميلات",
        s_dl="جارٍ التحميل...",s_done="اكتمل",s_pause="متوقف",s_stop="موقوف",s_err="خطأ",
        s_interrupted="مقاطع",restart="إعادة",dismiss="X",url_empty="الرابط فارغ",
        hist_lbl="التحميلات الأخيرة",hist_clr="حذف",hist_empty="  لا توجد تحميلات",
        confirm="تأكيد",confirm_clr="حذف كل السجل؟",
        set_lang="اللغة",set_theme="المظهر",theme_dark="داكن",theme_light="فاتح",theme_auto="تلقائي",
        set_max="الحد الأقصى للتحميلات",set_dir="مجلد الحفظ",
        save="حفظ",saved="تم الحفظ",browse="...",about_title="حول",about_ver="الإصدار",
        about_desc="محمّل صوت وفيديو\nيعتمد على yt-dlp + ffmpeg",
        about_deps="التبعيات: yt-dlp, ffmpeg, Python, psutil",
        active="نشط",restart_note="أعد تشغيل التطبيق لتطبيق التغييرات.",
        max_warning="تم الوصول للحد الأقصى من التحميلات.",
        restored_banner="تم استعادة التحميلات المقاطعة - اضغط إعادة للمتابعة."
    ),
    "zh": dict(
        tab_dl="下载",tab_hist="历史",tab_set="设置",about_btn="i",
        url_lbl="网址",mp3="音频 MP3",mp4="视频 MP4",pl_mp3="播放列表 MP3",pl_mp4="播放列表 MP4",
        queue_lbl="下载队列",clear_done="清除已完成",no_dl="暂无下载",
        s_dl="下载中...",s_done="完成",s_pause="已暂停",s_stop="已停止",s_err="错误",
        s_interrupted="已中断",restart="重新开始",dismiss="X",url_empty="网址为空",
        hist_lbl="最近下载",hist_clr="清除",hist_empty="  暂无记录",
        confirm="确认",confirm_clr="清除所有历史记录？",
        set_lang="语言",set_theme="主题",theme_dark="深色",theme_light="浅色",theme_auto="自动",
        set_max="最大同时下载数",set_dir="输出文件夹",
        save="保存",saved="已保存",browse="...",about_title="关于",about_ver="版本",
        about_desc="音视频下载器\n基于 yt-dlp + ffmpeg",
        about_deps="依赖: yt-dlp, ffmpeg, Python, psutil",
        active="活跃",restart_note="重启应用以应用更改。",
        max_warning="已达到最大同时下载数。",
        restored_banner="已恢复中断的下载 - 点击重新开始继续。"
    ),
    "ru": dict(
        tab_dl="Загрузить",tab_hist="История",tab_set="Настройки",about_btn="i",
        url_lbl="URL",mp3="Аудио MP3",mp4="Видео MP4",pl_mp3="Плейлист MP3",pl_mp4="Плейлист MP4",
        queue_lbl="Очередь загрузок",clear_done="Очистить завершённые",no_dl="Нет активных загрузок",
        s_dl="Загрузка...",s_done="Завершено",s_pause="На паузе",s_stop="Остановлено",s_err="Ошибка",
        s_interrupted="Прервано",restart="Перезапустить",dismiss="X",url_empty="Пустой URL",
        hist_lbl="Недавние загрузки",hist_clr="Очистить",hist_empty="  Нет загрузок",
        confirm="Подтвердить",confirm_clr="Очистить всю историю?",
        set_lang="Язык",set_theme="Тема",theme_dark="Тёмная",theme_light="Светлая",theme_auto="Авто",
        set_max="Макс. одновременных загрузок",set_dir="Папка назначения",
        save="Сохранить",saved="Сохранено",browse="...",about_title="О программе",about_ver="Версия",
        about_desc="Загрузчик аудио/видео\nна основе yt-dlp + ffmpeg",
        about_deps="Зависимости: yt-dlp, ffmpeg, Python, psutil",
        active="активных",restart_note="Перезапустите приложение для применения изменений.",
        max_warning="Достигнут максимум одновременных загрузок.",
        restored_banner="Прерванные загрузки восстановлены - нажмите Перезапустить для продолжения."
    )
}
LANG_NAMES = {"fr":"Français","en":"English","es":"Español","ar":"العربية","zh":"中文","ru":"Русский"}

def s(key):
    return STRINGS.get(LANG, STRINGS["fr"]).get(key, key)


class DownloadRow(tk.Frame):
    def __init__(self, parent, job_id, url, mode, out_dir, on_done, on_queue_change):
        super().__init__(parent, bg=C["bg3"], pady=6, padx=8)
        self.job_id=job_id; self.url=url; self.mode=mode; self.out_dir=out_dir
        self.on_done=on_done; self.on_queue_change=on_queue_change
        self.process=None; self.paused=False; self.finished=False
        self.success=False; self.last_title=""
        self._build()
        threading.Thread(target=self._run, daemon=True).start()

    def _build(self):
        MC={"audio":C["accent"],"video":"#555","playlist_audio":C["dark_btn"],"playlist_video":C["dark_btn"]}
        ML={"audio":"MP3","video":"MP4","playlist_audio":"PL MP3","playlist_video":"PL MP4"}
        top=tk.Frame(self,bg=C["bg3"]); top.pack(fill="x")
        tk.Label(top,text=ML.get(self.mode,"?"),bg=MC.get(self.mode,C["bg3"]),
                 fg="#fff",font=(FONT,8,"bold"),padx=6,pady=2).pack(side="left")
        url_s=self.url[:52]+"..." if len(self.url)>52 else self.url
        self.title_lbl=tk.Label(top,text=url_s,bg=C["bg3"],fg=C["fg2"],font=(FONT,8),anchor="w")
        self.title_lbl.pack(side="left",padx=(6,0),fill="x",expand=True)
        sid=f"row{self.job_id}.Horizontal.TProgressbar"
        ttk.Style().configure(sid,troughcolor=C["bg2"],background=C["accent"],thickness=7)
        self.prog=ttk.Progressbar(self,style=sid,orient="horizontal",
                                  mode="determinate",maximum=100,value=0)
        self.prog.pack(fill="x",pady=(5,4))
        bot=tk.Frame(self,bg=C["bg3"]); bot.pack(fill="x")
        self.status_lbl=tk.Label(bot,text=s("s_dl"),bg=C["bg3"],fg=C["fg2"],font=(FONT,8))
        self.status_lbl.pack(side="left")
        ctrl=tk.Frame(bot,bg=C["bg3"]); ctrl.pack(side="right")
        self.pause_btn=tk.Button(ctrl,text="||",bg=C["amber"],fg="#fff",relief="flat",
                                 font=(FONT,9),cursor="hand2",padx=6,pady=2,command=self._pause)
        self.pause_btn.pack(side="left",padx=2)
        self.resume_btn=tk.Button(ctrl,text=">",bg=C["green"],fg="#fff",relief="flat",
                                  font=(FONT,9),cursor="hand2",padx=6,pady=2,
                                  command=self._resume,state="disabled")
        self.resume_btn.pack(side="left",padx=2)
        self.stop_btn=tk.Button(ctrl,text="[]",bg="#7b241c",fg="#fff",relief="flat",
                                font=(FONT,9),cursor="hand2",padx=6,pady=2,command=self._stop)
        self.stop_btn.pack(side="left",padx=2)
        tk.Frame(self,bg=C["bg4"],height=1).pack(fill="x",pady=(4,0))

    def _cmd(self):
        out=self.out_dir; pl=["--yes-playlist"]
        ba=["yt-dlp","--newline","-x","--audio-format","mp3","--audio-quality","0"]
        bv=["yt-dlp","--newline","-f","bestvideo+bestaudio/best","--merge-output-format","mp4"]
        return {
            "audio":          ba+["-o",out+"/%(title)s.%(ext)s",self.url],
            "video":          bv+["-o",out+"/%(title)s.%(ext)s",self.url],
            "playlist_audio": ba+pl+["-o",out+"/%(playlist_index)s - %(title)s.%(ext)s",self.url],
            "playlist_video": bv+pl+["-o",out+"/%(playlist_index)s - %(title)s.%(ext)s",self.url],
        }.get(self.mode, ba+["-o",out+"/%(title)s.%(ext)s",self.url])

    def _run(self):
        try:
            si=subprocess.STARTUPINFO()
            si.dwFlags|=subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow=0
            self.process=subprocess.Popen(self._cmd(),stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",bufsize=1,
                startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
            for line in iter(self.process.stdout.readline,""):
                line=line.strip()
                if not line: continue
                if "[download]" in line and "%" in line:
                    parts=line.split()
                    for i,p in enumerate(parts):
                        if p.endswith("%"):
                            try:
                                pct=float(p.replace("%",""))
                                total_size=""
                                for j,x in enumerate(parts):
                                    if x=="of" and j+1<len(parts):
                                        total_size=parts[j+1]; break
                                dl_size=""
                                if total_size:
                                    try:
                                        unit=""
                                        for u in ("GiB","MiB","KiB","KB","MB","GB"):
                                            if total_size.endswith(u):
                                                unit=u; break
                                        val=float(total_size.replace(unit,""))
                                        dl_val=val*pct/100
                                        dl_size=f"{dl_val:.2f}{unit}"
                                    except: pass
                                speed=next((parts[k+1] for k,x in enumerate(parts)
                                            if x=="at" and k+1<len(parts)),"")
                                eta=next((parts[k+1] for k,x in enumerate(parts)
                                          if x=="ETA" and k+1<len(parts)),"")
                                size_info=f"  {dl_size} / {total_size}" if dl_size and total_size else ""
                                info=f"{pct:.1f}%{size_info}"
                                if speed: info+=f"  ↓{speed}"
                                if eta:   info+=f"  ETA {eta}"
                                self.after(0,lambda v=pct,t=info:(
                                    self.prog.config(value=v),
                                    self.status_lbl.config(text=t)))
                            except: pass
                if "Destination:" in line:
                    raw=line.split("Destination:")[-1].strip()
                    self.last_title=raw.replace("\\","/").split("/")[-1]
                    short=self.last_title[:48]+"..." if len(self.last_title)>48 else self.last_title
                    self.after(0,lambda t=short:self.title_lbl.config(text=t,fg=C["fg"]))
            self.process.wait()
            if self.process.returncode in (0, 1) and not self.finished:
                save_history({"url":self.url,"mode":self.mode,
                              "title":self.last_title or self.url,
                              "time":time.strftime("%Y-%m-%d %H:%M")})
                self.success=True; self.after(0,self._mark_done)
            elif not self.finished:
                self.after(0,lambda:self._mark_error(f"code {self.process.returncode}"))
        except Exception as e:
            if not self.finished: self.after(0,lambda:self._mark_error(str(e)[:60]))

    def _mark_done(self):
        self.finished=True
        sid=f"done{self.job_id}.Horizontal.TProgressbar"
        ttk.Style().configure(sid,troughcolor=C["bg2"],background=C["green"],thickness=7)
        self.prog.config(style=sid,value=100)
        self.status_lbl.config(text=s("s_done"),fg=C["green"])
        for b in (self.pause_btn,self.resume_btn,self.stop_btn): b.config(state="disabled")
        self.on_done(self.job_id); self.on_queue_change()

    def _mark_error(self,msg):
        self.finished=True; self.prog.config(value=0)
        self.status_lbl.config(text=f'{s("s_err")}: {msg}',fg=C["accent"])
        for b in (self.pause_btn,self.resume_btn,self.stop_btn): b.config(state="disabled")
        self.on_done(self.job_id); self.on_queue_change()

    def _pause(self):
        if not self.process or self.paused: return
        try:
            p=psutil.Process(self.process.pid)
            for c in p.children(recursive=True): c.suspend()
            p.suspend(); self.paused=True
            self.pause_btn.config(state="disabled"); self.resume_btn.config(state="normal")
            self.status_lbl.config(text=s("s_pause"),fg=C["amber"]); self.on_queue_change()
        except: pass

    def _resume(self):
        if not self.process or not self.paused: return
        try:
            p=psutil.Process(self.process.pid)
            for c in p.children(recursive=True): c.resume()
            p.resume(); self.paused=False
            self.pause_btn.config(state="normal"); self.resume_btn.config(state="disabled")
            self.status_lbl.config(text=s("s_dl"),fg=C["fg2"]); self.on_queue_change()
        except: pass

    def _stop(self):
        self.finished=True
        if self.paused: self._resume()
        if self.process:
            try:
                p=psutil.Process(self.process.pid)
                for c in p.children(recursive=True): c.kill()
                p.kill()
            except: pass
        self.status_lbl.config(text=s("s_stop"),fg=C["fg2"])
        for b in (self.pause_btn,self.resume_btn,self.stop_btn): b.config(state="disabled")
        self.on_done(self.job_id); self.on_queue_change()


class RestoredRow(tk.Frame):
    def __init__(self,parent,job_id,url,mode,title,on_restart,on_dismiss):
        super().__init__(parent,bg=C["bg3"],pady=6,padx=8)
        self.job_id=job_id; self.url=url; self.mode=mode
        self.last_title=title; self.finished=True; self.success=False
        self._build(on_restart,on_dismiss)

    def _build(self,on_restart,on_dismiss):
        ML={"audio":"MP3","video":"MP4","playlist_audio":"PL MP3","playlist_video":"PL MP4"}
        top=tk.Frame(self,bg=C["bg3"]); top.pack(fill="x")
        tk.Label(top,text=ML.get(self.mode,"?"),bg=C["warn"],fg="#fff",
                 font=(FONT,8,"bold"),padx=6,pady=2).pack(side="left")
        display=self.last_title or self.url
        short=display[:52]+"..." if len(display)>52 else display
        tk.Label(top,text=short,bg=C["bg3"],fg=C["fg2"],
                 font=(FONT,8),anchor="w").pack(side="left",padx=(6,0),fill="x",expand=True)
        bot=tk.Frame(self,bg=C["bg3"]); bot.pack(fill="x",pady=(6,0))
        tk.Label(bot,text=s("s_interrupted"),bg=C["bg3"],
                 fg=C["warn"],font=(FONT,8,"bold")).pack(side="left")
        ctrl=tk.Frame(bot,bg=C["bg3"]); ctrl.pack(side="right")
        tk.Button(ctrl,text=s("restart"),bg=C["green"],fg="#fff",relief="flat",
                  font=(FONT,9,"bold"),cursor="hand2",padx=8,pady=2,
                  command=lambda:on_restart(self.job_id,self.url,self.mode)
                  ).pack(side="left",padx=2)
        tk.Button(ctrl,text=s("dismiss"),bg=C["bg4"],fg=C["fg2"],relief="flat",
                  font=(FONT,9),cursor="hand2",padx=6,pady=2,
                  command=lambda:on_dismiss(self.job_id)
                  ).pack(side="left",padx=2)
        tk.Frame(self,bg=C["bg4"],height=1).pack(fill="x",pady=(4,0))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg=load_config()
        global LANG,C
        LANG=self.cfg.get("language","fr"); apply_palette(self.cfg.get("theme","auto"))
        self.title("Samory")
        # Icône fenêtre + barre des tâches
        try:
            import sys
            from PIL import Image as PILImage, ImageTk
            base = sys._MEIPASS if hasattr(sys,"_MEIPASS") else os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base,"samory_logo.png")
            ico_path  = os.path.join(base,"samory.ico")
            if os.path.exists(logo_path):
                pil = PILImage.open(logo_path).resize((256,256), PILImage.LANCZOS)
                self._app_icon = ImageTk.PhotoImage(pil)
                self.iconphoto(True, self._app_icon)
            elif os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except: pass
        self.geometry("530x660")
        self.resizable(False,True); self.configure(bg=C["bg"])
        self.jobs={}
        self.protocol("WM_DELETE_WINDOW",self._on_close)
        self._build(); self._restore_queue(); self._auto_theme_check()

    def _on_close(self):
        save_queue(self.jobs); self.destroy()

    def _auto_theme_check(self):
        if self.cfg.get("theme")=="auto":
            new=PALETTES[resolve_theme("auto")]
            if any(C.get(k)!=v for k,v in new.items()):
                apply_palette("auto"); self._rebuild()
        self.after(60000,self._auto_theme_check)

    def _restore_queue(self):
        items=[i for i in load_queue() if i.get("status")=="interrupted"]
        if not items: return
        banner=tk.Frame(self.queue_frame,bg=C["warn"],pady=6)
        banner.pack(fill="x",pady=(0,6))
        tk.Label(banner,text=s("restored_banner"),bg=C["warn"],fg="#fff",
                 font=(FONT,9,"bold"),wraplength=460,justify="left").pack(padx=10)
        self.empty_lbl.pack_forget()
        for item in items:
            job_id=item.get("job_id",str(uuid.uuid4())[:8])
            row=RestoredRow(self.queue_frame,job_id,item["url"],item["mode"],
                            item.get("title",""),
                            self._on_restored_restart,self._on_restored_dismiss)
            row.pack(fill="x",pady=(0,4))
            self.jobs[job_id]=row
        self._update_count()

    def _on_restored_restart(self,job_id,url,mode):
        old=self.jobs.get(job_id)
        if old: old.destroy()
        active=sum(1 for jid,r in self.jobs.items() if not r.finished and jid!=job_id)
        if active>=self.cfg.get("max_concurrent",3):
            messagebox.showwarning(s("confirm"),s("max_warning")); return
        out=self.cfg.get("output_dir",os.path.expanduser("~/Downloads/YT-DLP"))
        os.makedirs(out,exist_ok=True)
        row=DownloadRow(self.queue_frame,job_id,url,mode,out,
                        self._on_done,lambda:save_queue(self.jobs))
        row.pack(fill="x",pady=(0,4))
        self.jobs[job_id]=row
        self._update_count(); save_queue(self.jobs)

    def _on_restored_dismiss(self,job_id):
        row=self.jobs.pop(job_id,None)
        if row: row.destroy()
        if not self.jobs: self.empty_lbl.pack(pady=20)
        self._update_count(); save_queue(self.jobs)

    def _build(self):
        self.hdr=tk.Frame(self,bg=C["accent"],height=50)
        self.hdr.pack(fill="x"); self.hdr.pack_propagate(False)
        tk.Label(self.hdr,text="Samory",bg=C["accent"],fg=C["bg"],
                 font=(FONT,13,"bold")).pack(side="left",padx=16,pady=12)
        self.count_lbl=tk.Label(self.hdr,text="",bg=C["accent"],fg="#fff",font=(FONT,9))
        self.count_lbl.pack(side="right",padx=(0,4))
        tk.Button(self.hdr,text=s("about_btn"),bg=C["accent"],fg="#fff",relief="flat",
                  font=(FONT,12,"bold"),cursor="hand2",padx=10,
                  command=self._show_about).pack(side="right")
        style=ttk.Style(); style.theme_use("default")
        style.configure("TNotebook",background=C["bg"],borderwidth=0)
        style.configure("TNotebook.Tab",background=C["bg3"],foreground=C["fg2"],
                        padding=[14,6],font=(FONT,10))
        style.map("TNotebook.Tab",background=[("selected","#BDA18A")],
                  foreground=[("selected","#2a2420")])
        style.configure("TFrame",background=C["bg2"])
        self.nb=ttk.Notebook(self); self.nb.pack(fill="both",expand=True,padx=12,pady=10)
        self.tab_dl=ttk.Frame(self.nb); self.tab_hist=ttk.Frame(self.nb)
        self.tab_set=ttk.Frame(self.nb); self.tab_ext=ttk.Frame(self.nb)
        self.nb.add(self.tab_dl,text=s("tab_dl"))
        self.nb.add(self.tab_hist,text=s("tab_hist"))
        self.nb.add(self.tab_set,text=s("tab_set"))
        self.nb.add(self.tab_ext,text="Extension")
        self.nb.bind("<<NotebookTabChanged>>",self._on_tab)
        self._build_dl(); self._build_hist(); self._build_set(); self._build_ext()

    def _rebuild(self):
        for w in self.winfo_children(): w.destroy()
        self.jobs={}; self._build(); self._restore_queue()

    def _build_dl(self):
        f=self.tab_dl
        tk.Label(f,text=s("url_lbl"),bg=C["bg2"],fg=C["fg2"],
                 font=(FONT,9)).pack(anchor="w",padx=14,pady=(14,2))
        self.url_var=tk.StringVar()
        tk.Entry(f,textvariable=self.url_var,bg=C["entry_bg"],fg=C["entry_fg"],
                 insertbackground=C["entry_fg"],relief="flat",
                 font=(FONT,10)).pack(fill="x",padx=14)
        bf=tk.Frame(f,bg=C["bg2"]); bf.pack(fill="x",padx=14,pady=(10,0))
        for key,color,mode in [("mp3",C["accent"],"audio"),("mp4",C["bg3"],"video"),
                                ("pl_mp3",C["dark_btn"],"playlist_audio"),
                                ("pl_mp4",C["dark_btn"],"playlist_video")]:
            tk.Button(bf,text=s(key),bg=color,fg="#fff",activebackground=color,
                      relief="flat",font=(FONT,10,"bold"),cursor="hand2",bd=0,pady=7,
                      command=lambda m=mode:self._add_dl(m)).pack(fill="x",pady=2)
        tk.Frame(f,bg=C["bg4"],height=1).pack(fill="x",padx=14,pady=(12,0))
        hdr=tk.Frame(f,bg=C["bg2"]); hdr.pack(fill="x",padx=14,pady=(6,4))
        tk.Label(hdr,text=s("queue_lbl"),bg=C["bg2"],fg=C["fg2"],
                 font=(FONT,9,"bold")).pack(side="left")
        tk.Button(hdr,text=s("clear_done"),bg=C["bg3"],fg=C["fg2"],relief="flat",
                  font=(FONT,8),cursor="hand2",command=self._clear_done).pack(side="right")
        container=tk.Frame(f,bg=C["bg2"])
        container.pack(fill="both",expand=True,padx=14,pady=(0,10))
        self.canvas=tk.Canvas(container,bg=C["bg2"],highlightthickness=0)
        sb=tk.Scrollbar(container,orient="vertical",command=self.canvas.yview,
                        bg=C["bg3"],troughcolor=C["bg2"])
        self.queue_frame=tk.Frame(self.canvas,bg=C["bg2"])
        self.queue_frame.bind("<Configure>",
            lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0),window=self.queue_frame,anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")
        self.empty_lbl=tk.Label(self.queue_frame,text=s("no_dl"),
                                bg=C["bg2"],fg=C["bg4"],font=(FONT,9))
        self.empty_lbl.pack(pady=20)

    def _add_dl(self,mode):
        url=self.url_var.get().strip()
        if not url: messagebox.showwarning(s("confirm"),s("url_empty")); return
        active=sum(1 for r in self.jobs.values() if not r.finished)
        if active>=self.cfg.get("max_concurrent",3):
            messagebox.showwarning(s("confirm"),s("max_warning")); return
        out=self.cfg.get("output_dir",os.path.expanduser("~/Downloads/YT-DLP"))
        os.makedirs(out,exist_ok=True)
        job_id=str(uuid.uuid4())[:8]
        self.empty_lbl.pack_forget()
        row=DownloadRow(self.queue_frame,job_id,url,mode,out,
                        self._on_done,lambda:save_queue(self.jobs))
        row.pack(fill="x",pady=(0,4))
        self.jobs[job_id]=row; self.url_var.set("")
        self._update_count(); save_queue(self.jobs)

    def _on_done(self,job_id): self._update_count()

    def _clear_done(self):
        to_rm=[jid for jid,r in self.jobs.items() if r.finished]
        for jid in to_rm: self.jobs[jid].destroy(); del self.jobs[jid]
        if not self.jobs: self.empty_lbl.pack(pady=20)
        self._update_count(); save_queue(self.jobs)

    def _update_count(self):
        active=sum(1 for r in self.jobs.values() if not r.finished)
        self.count_lbl.config(text=f"{active} {s('active')}" if active else "")

    def _build_hist(self):
        f=self.tab_hist
        top=tk.Frame(f,bg=C["bg2"]); top.pack(fill="x",padx=14,pady=(12,6))
        tk.Label(top,text=s("hist_lbl"),bg=C["bg2"],fg=C["fg"],
                 font=(FONT,10,"bold")).pack(side="left")
        tk.Button(top,text=s("hist_clr"),bg=C["bg3"],fg=C["fg2"],relief="flat",
                  font=(FONT,9),cursor="hand2",command=self._clear_hist).pack(side="right")
        frame=tk.Frame(f,bg=C["bg2"])
        frame.pack(fill="both",expand=True,padx=14,pady=(0,12))
        sb=tk.Scrollbar(frame,bg=C["bg3"],troughcolor=C["bg2"]); sb.pack(side="right",fill="y")
        self.hist_list=tk.Listbox(frame,bg=C["list_bg"],fg=C["fg"],relief="flat",
                                  font=(FONT,9),selectbackground=C["sel_bg"],
                                  activestyle="none",bd=0,yscrollcommand=sb.set)
        self.hist_list.pack(fill="both",expand=True)
        sb.config(command=self.hist_list.yview)

    def _load_hist(self):
        self.hist_list.delete(0,tk.END)
        h=load_history()
        if not h: self.hist_list.insert(tk.END,s("hist_empty")); return
        for item in h:
            self.hist_list.insert(tk.END,
                f"  {item.get('time','')}  [{item.get('mode','')}]  "
                f"{item.get('title',item.get('url',''))}")

    def _clear_hist(self):
        if messagebox.askyesno(s("confirm"),s("confirm_clr")):
            with open(HISTORY_FILE,"w") as f: json.dump([],f)
            self._load_hist()

    def _build_set(self):
        f=self.tab_set
        def section(key):
            tk.Label(f,text=s(key),bg=C["bg2"],fg=C["fg2"],
                     font=(FONT,9,"bold")).pack(anchor="w",padx=14,pady=(16,4))
        section("set_lang")
        self.lang_var=tk.StringVar(value=self.cfg.get("language","fr"))
        lf=tk.Frame(f,bg=C["bg2"]); lf.pack(fill="x",padx=14)
        for code,name in LANG_NAMES.items():
            tk.Radiobutton(lf,text=name,variable=self.lang_var,value=code,
                           bg=C["bg2"],fg=C["fg"],selectcolor=C["bg3"],
                           activebackground=C["bg2"],font=(FONT,9)
                           ).pack(side="left",padx=(0,8))
        section("set_theme")
        self.theme_var=tk.StringVar(value=self.cfg.get("theme","auto"))
        tf=tk.Frame(f,bg=C["bg2"]); tf.pack(fill="x",padx=14)
        for val,key in [("dark","theme_dark"),("light","theme_light"),("auto","theme_auto")]:
            tk.Radiobutton(tf,text=s(key),variable=self.theme_var,value=val,
                           bg=C["bg2"],fg=C["fg"],selectcolor=C["bg3"],
                           activebackground=C["bg2"],font=(FONT,9)
                           ).pack(side="left",padx=(0,12))
        section("set_max")
        self.max_var=tk.IntVar(value=self.cfg.get("max_concurrent",3))
        mf=tk.Frame(f,bg=C["bg2"]); mf.pack(fill="x",padx=14)
        for v in [1,2,3,4,5]:
            tk.Radiobutton(mf,text=str(v),variable=self.max_var,value=v,
                           bg=C["bg2"],fg=C["fg"],selectcolor=C["bg3"],
                           activebackground=C["bg2"],font=(FONT,9)
                           ).pack(side="left",padx=(0,10))
        section("set_dir")
        row=tk.Frame(f,bg=C["bg2"]); row.pack(fill="x",padx=14)
        self.dir_var=tk.StringVar(value=self.cfg.get("output_dir",""))
        tk.Entry(row,textvariable=self.dir_var,bg=C["entry_bg"],fg=C["entry_fg"],
                 insertbackground=C["entry_fg"],relief="flat",
                 font=(FONT,9)).pack(side="left",fill="x",expand=True)
        tk.Button(row,text=s("browse"),bg=C["bg3"],fg=C["fg"],relief="flat",
                  font=(FONT,11),cursor="hand2",
                  command=self._browse).pack(side="left",padx=(6,0))
        tk.Button(f,text=s("save"),bg=C["dark_btn"],fg="#fff",activebackground=C["dark_btn"],
                  relief="flat",font=(FONT,10,"bold"),cursor="hand2",pady=8,
                  command=self._save_settings).pack(fill="x",padx=14,pady=(16,0))
        self.set_status=tk.Label(f,text="",bg=C["bg2"],fg=C["green"],font=(FONT,9))
        self.set_status.pack(pady=(6,0))
        self.restart_lbl=tk.Label(f,text="",bg=C["bg2"],fg=C["amber"],font=(FONT,8))
        self.restart_lbl.pack()

    def _browse(self):
        d=filedialog.askdirectory(initialdir=self.dir_var.get())
        if d: self.dir_var.set(d)

    def _save_settings(self):
        global LANG
        old_lang=self.cfg.get("language"); old_theme=self.cfg.get("theme")
        self.cfg["language"]=self.lang_var.get(); self.cfg["theme"]=self.theme_var.get()
        self.cfg["max_concurrent"]=self.max_var.get(); self.cfg["output_dir"]=self.dir_var.get()
        save_config(self.cfg); LANG=self.cfg["language"]; apply_palette(self.cfg["theme"])
        if self.cfg["language"]!=old_lang or self.cfg["theme"]!=old_theme:
            self.restart_lbl.config(text=s("restart_note")); self.after(400,self._rebuild)
        else:
            self.set_status.config(text=s("saved"))
            self.after(2000,lambda:self.set_status.config(text=""))

    def _show_about(self):
        win=tk.Toplevel(self)
        win.title(s("about_title"))
        win.geometry("420x620")
        win.resizable(False,False)
        win.configure(bg=C["bg2"])
        win.grab_set()
        try:
            import sys
            base=sys._MEIPASS if hasattr(sys,"_MEIPASS") else os.path.dirname(os.path.abspath(__file__))
            ico=os.path.join(base,"samory.ico")
            if os.path.exists(ico): win.iconbitmap(ico)
        except: pass

        # Bande accent en haut
        tk.Frame(win,bg=C["accent"],height=4).pack(fill="x")

        # Zone titre — logo exact SVG : fond #F5EFE6, S #9C7F67 Georgia
        hdr=tk.Frame(win,bg=C["bg"])
        hdr.pack(fill="x")
        try:
            import sys
            base=sys._MEIPASS if hasattr(sys,"_MEIPASS") else os.path.dirname(os.path.abspath(__file__))
            logo_path=os.path.join(base,"samory_logo.png")
            if os.path.exists(logo_path):
                from PIL import Image as PILImage, ImageTk
                pil=PILImage.open(logo_path).resize((96,96),PILImage.LANCZOS)
                _img=ImageTk.PhotoImage(pil)
                lbl=tk.Label(hdr,image=_img,bg=C["bg"]); lbl.image=_img
                lbl.pack(pady=(24,0))
            else: raise FileNotFoundError
        except:
            logo=tk.Canvas(hdr,width=96,height=96,bg=C["bg"],highlightthickness=0)
            logo.pack(pady=(24,0))
            logo.create_polygon(12,0,84,0,96,12,96,84,84,96,12,96,0,84,0,12,
                                smooth=True,fill="#F5EFE6",outline="")
            logo.create_text(48,54,text="S",fill="#9C7F67",
                             font=("Georgia",58,"bold"),anchor="center")
        tk.Label(hdr,text="S  A  M  O  R  Y",bg=C["bg"],fg="#9C7F67",
                 font=("Georgia",12)).pack(pady=(8,0))
        tk.Label(hdr,text="Open Source Audio & Video Downloader",
                 bg=C["bg"],fg=C["fg2"],font=(FONT,9)).pack(pady=(4,14))

        # Corps
        body=tk.Frame(win,bg=C["bg2"])
        body.pack(fill="both",expand=False)

        def sep():
            tk.Frame(body,bg=C["bg4"],height=1).pack(fill="x",padx=24,pady=8)

        def row(label,value,value_color=None):
            f=tk.Frame(body,bg=C["bg2"])
            f.pack(fill="x",padx=24,pady=2)
            tk.Label(f,text=label,bg=C["bg2"],fg=C["fg2"],
                     font=(FONT,9),width=14,anchor="w").pack(side="left")
            tk.Label(f,text=value,bg=C["bg2"],
                     fg=value_color or C["fg"],
                     font=(FONT,9,"bold"),anchor="w").pack(side="left")

        sep()
        row("Version",    VERSION)
        row("Licence",    "Apache 2.0 — Open Source", C["accent"])
        row("Plateforme", "Windows 10 / 11")
        sep()
        row("Créé par",   "Hermann Kamté", C["amber"])
        row("Origine",    "Yaoundé, Cameroun")
        sep()
        row("Moteur DL",  "yt-dlp  (1000+ sites)")
        row("Audio",      "ffmpeg")
        row("Interface",  "Python / Tkinter")
        row("Processus",  "psutil")
        sep()

        # Résumé Apache 2.0
        tk.Label(body,
            text=(
                "Licence Apache 2.0 — libre d'utilisation, modification\n"
                "et distribution. Les brevets des contributeurs sont\n"
                "protégés. Toute redistribution doit mentionner\n"
                "l'auteur original : Hermann Kamté."
            ),
            bg=C["bg2"],fg=C["fg2"],font=(FONT,8),justify="center"
        ).pack(padx=24,pady=(0,6))

        # Lien GitHub
        gh=tk.Label(body,text="github.com/hermannkamte",
                    bg=C["bg2"],fg=C["accent"],font=(FONT,9,"underline"),
                    cursor="hand2",command=lambda:__import__("webbrowser").open("https://github.com/hermannkamte"))
        gh.pack(pady=(0,4))

        sep()

        # Bouton installer l'extension Chrome
        tk.Button(body,
            text="Installer l'extension Chrome",
            bg=C["bg3"],fg=C["accent"],relief="flat",
            font=(FONT,10,"bold"),cursor="hand2",pady=8,
            command=lambda:__import__("webbrowser").open(
                "https://chrome.google.com/webstore/detail/samory/bjkcfmjlecjpihnopchgbdphjgfmheek")
        ).pack(fill="x",padx=24,pady=(0,6))

        tk.Button(body,text="OK",bg=C["accent"],fg=C["bg"],relief="flat",
                  font=(FONT,10,"bold"),cursor="hand2",pady=8,
                  command=win.destroy).pack(fill="x",padx=24,pady=(0,16))


    def _build_ext(self):
        f=self.tab_ext
        # Logo centré
        try:
            import sys
            base=sys._MEIPASS if hasattr(sys,"_MEIPASS") else os.path.dirname(os.path.abspath(__file__))
            logo_path=os.path.join(base,"samory_logo.png")
            if os.path.exists(logo_path):
                from PIL import Image as PILImage, ImageTk
                pil=PILImage.open(logo_path).resize((80,80),PILImage.LANCZOS)
                _img2=ImageTk.PhotoImage(pil)
                lbl2=tk.Label(f,image=_img2,bg=C["bg2"]); lbl2.image=_img2
                lbl2.pack(pady=(24,0))
            else: raise FileNotFoundError
        except:
            logo=tk.Canvas(f,width=80,height=80,bg=C["bg2"],highlightthickness=0)
            logo.pack(pady=(24,0))
            logo.create_polygon(10,0,70,0,80,10,80,70,70,80,10,80,0,70,0,10,
                                smooth=True,fill="#F5EFE6",outline="")
            logo.create_text(40,44,text="S",fill="#9C7F67",
                             font=("Georgia",46,"bold"),anchor="center")
        tk.Label(f,text="Extension Chrome",bg=C["bg2"],fg=C["fg"],
                 font=(FONT,11,"bold")).pack(pady=(10,2))
        tk.Label(f,text="Téléchargez directement depuis votre navigateur",
                 bg=C["bg2"],fg=C["fg2"],font=(FONT,9)).pack()
        tk.Frame(f,bg=C["bg4"],height=1).pack(fill="x",padx=24,pady=14)
        # Statut
        tk.Label(f,text="Fonctionnalités de l'extension :",
                 bg=C["bg2"],fg=C["fg2"],font=(FONT,9,"bold")).pack(anchor="w",padx=24)
        features=[
            "⬇  Audio MP3 / Vidéo MP4",
            "⬇  Playlists complètes",
            "📋  File synchronisée avec l'app",
            "🕘  Historique partagé",
            "⏸  Pause / Reprendre / Arrêter",
            "🌍  1000+ sites supportés",
        ]
        for feat in features:
            tk.Label(f,text=feat,bg=C["bg2"],fg=C["fg"],
                     font=(FONT,9),anchor="w").pack(anchor="w",padx=32,pady=1)
        tk.Frame(f,bg=C["bg4"],height=1).pack(fill="x",padx=24,pady=14)
        # Bouton installer
        tk.Button(f,text="⬇  Installer l'extension Chrome",
                  bg=C["accent"],fg="#F5EFE6",relief="flat",
                  font=(FONT,10,"bold"),cursor="hand2",pady=10,
                  command=lambda:__import__("webbrowser").open(
                      "https://chrome.google.com/webstore/detail/samory/bjkcfmjlecjpihnopchgbdphjgfmheek"
                  )).pack(fill="x",padx=24,pady=(0,8))
        # Lien GitHub
        gh=tk.Label(f,text="Code source : github.com/hermannkamte/samory",
                    bg=C["bg2"],fg=C["accent"],font=(FONT,8,"underline"),cursor="hand2")
        gh.pack(pady=(0,8))
        gh.bind("<Button-1>",lambda e:__import__("webbrowser").open(
            "https://github.com/hermannkamte/samory"))

    def _on_tab(self,event):
        tab=self.nb.tab(self.nb.select(),"text")
        if s("tab_hist").strip() in tab: self._load_hist()
        if s("tab_set").strip()  in tab:
            self.cfg=load_config(); self.dir_var.set(self.cfg.get("output_dir",""))


if __name__=="__main__":
    app=App(); app.mainloop()
