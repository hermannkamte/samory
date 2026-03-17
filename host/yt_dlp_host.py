import sys, json, struct, subprocess, os, time, threading
import psutil

CONFIG_FILE  = os.path.expanduser("~/yt-dlp-config.json")
HISTORY_FILE = os.path.expanduser("~/yt-dlp-history.json")
QUEUE_FILE   = os.path.expanduser("~/yt-dlp-queue.json")

lock = threading.Lock()
current_process = None
current_paused  = False
current_stopped = False

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            try: return json.load(f)
            except: pass
    return {"output_dir": os.path.expanduser("~/Downloads/YT-DLP")}

def save_config(c):
    with open(CONFIG_FILE,"w") as f: json.dump(c,f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            try: return json.load(f)
            except: return []
    return []

def save_history(e):
    h = load_history(); h.insert(0,e); h = h[:100]
    with open(HISTORY_FILE,"w") as f: json.dump(h,f)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            try: return json.load(f)
            except: return []
    return []

def save_queue(items):
    with open(QUEUE_FILE,"w") as f: json.dump(items,f)

def read_msg():
    raw = sys.stdin.buffer.read(4)
    if not raw or len(raw) < 4: return None
    length = struct.unpack("=I", raw)[0]
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))

def send_raw(msg):
    with lock:
        enc = json.dumps(msg).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("=I", len(enc)))
        sys.stdout.buffer.write(enc)
        sys.stdout.buffer.flush()

def build_cmd(mode, url, out):
    pl = ["--yes-playlist"]
    np = ["--no-playlist"]   # pour titre seul
    ba = ["yt-dlp","--newline","--continue","-x","--audio-format","mp3","--audio-quality","0"]
    bv = ["yt-dlp","--newline","--continue","-f","bestvideo+bestaudio/best","--merge-output-format","mp4"]
    return {
        "audio":          ba + np + ["-o", out+"/%(title)s.%(ext)s", url],
        "video":          bv + np + ["-o", out+"/%(title)s.%(ext)s", url],
        "playlist_audio": ba + pl + ["-o", out+"/%(playlist_index)s - %(title)s.%(ext)s", url],
        "playlist_video": bv + pl + ["-o", out+"/%(playlist_index)s - %(title)s.%(ext)s", url],
    }.get(mode)

def run_download(msg_id, url, mode):
    global current_process, current_paused, current_stopped
    cfg     = load_config()
    out     = cfg.get("output_dir", os.path.expanduser("~/Downloads/YT-DLP"))
    os.makedirs(out, exist_ok=True)
    cmd     = build_cmd(mode, url, out)
    if not cmd:
        send_raw({"type":"response","_id":msg_id,"status":"error","message":"mode inconnu"}); return

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    current_stopped = False
    current_paused  = False

    try:
        current_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)

        title = ""
        for line in iter(current_process.stdout.readline, ""):
            if current_stopped: break
            line = line.strip()
            if not line: continue
            if "[download]" in line and "%" in line:
                parts = line.split()
                pct = speed = eta = dl_size = tot_size = ""
                for i, p in enumerate(parts):
                    if p.endswith("%"):
                        try: pct = float(p.replace("%",""))
                        except: pass
                    if p == "of" and i+1 < len(parts): tot_size = parts[i+1]
                    if p == "at" and i+1 < len(parts): speed    = parts[i+1]
                    if p == "ETA" and i+1 < len(parts): eta      = parts[i+1]
                if pct != "" and tot_size:
                    try:
                        unit = ""
                        for u in ("GiB","MiB","KiB","MB","KB"):
                            if tot_size.endswith(u): unit=u; break
                        val = float(tot_size.replace(unit,""))
                        dl_size = f"{val*pct/100:.2f}{unit}"
                    except: pass
                send_raw({"type":"progress","percent":pct,"speed":speed,
                          "eta":eta,"dl_size":dl_size,"tot_size":tot_size})
            if "Destination:" in line:
                raw = line.split("Destination:")[-1].strip()
                title = raw.replace("\\","/").split("/")[-1]

        current_process.wait()
        rc = current_process.returncode

        if current_stopped:
            send_raw({"type":"response","_id":msg_id,"status":"stopped"})
        elif rc in (0, 1):
            save_history({"url":url,"mode":mode,"title":title or url,
                          "time":time.strftime("%Y-%m-%d %H:%M")})
            send_raw({"type":"response","_id":msg_id,"status":"success"})
        else:
            send_raw({"type":"response","_id":msg_id,"status":"error",
                      "message":f"code {rc}"})
    except Exception as e:
        send_raw({"type":"response","_id":msg_id,"status":"error","message":str(e)})
    finally:
        current_process = None

def handle(msg):
    global current_process, current_paused, current_stopped
    action = msg.get("action","")
    mid    = msg.get("_id","")

    if action == "start":
        t = threading.Thread(
            target=run_download,
            args=(mid, msg.get("url",""), msg.get("mode","audio")),
            daemon=True)
        t.start()
        # réponse envoyée par run_download quand terminé

    elif action == "pause":
        if current_process and not current_paused:
            try:
                p = psutil.Process(current_process.pid)
                for c in p.children(recursive=True): c.suspend()
                p.suspend()
                current_paused = True
                send_raw({"type":"response","_id":mid,"status":"ok"})
            except Exception as e:
                send_raw({"type":"response","_id":mid,"status":"error","message":str(e)})
        else:
            send_raw({"type":"response","_id":mid,"status":"error","message":"rien à mettre en pause"})

    elif action == "resume":
        if current_process and current_paused:
            try:
                p = psutil.Process(current_process.pid)
                for c in p.children(recursive=True): c.resume()
                p.resume()
                current_paused = False
                send_raw({"type":"response","_id":mid,"status":"ok"})
            except Exception as e:
                send_raw({"type":"response","_id":mid,"status":"error","message":str(e)})
        else:
            send_raw({"type":"response","_id":mid,"status":"error","message":"rien à reprendre"})

    elif action == "stop":
        current_stopped = True
        if current_process:
            try:
                p = psutil.Process(current_process.pid)
                for c in p.children(recursive=True): c.kill()
                p.kill()
            except: pass
        send_raw({"type":"response","_id":mid,"status":"ok"})

    elif action == "history":
        send_raw({"type":"response","_id":mid,"status":"ok","history":load_history()})

    elif action == "clear_history":
        with open(HISTORY_FILE,"w") as f: json.dump([],f)
        send_raw({"type":"response","_id":mid,"status":"ok"})

    elif action == "get_config":
        send_raw({"type":"response","_id":mid,"status":"ok","config":load_config()})

    elif action == "set_output_dir":
        cfg = load_config(); cfg["output_dir"] = msg.get("path", cfg.get("output_dir",""))
        save_config(cfg)
        send_raw({"type":"response","_id":mid,"status":"ok"})

    elif action == "get_queue":
        send_raw({"type":"response","_id":mid,"status":"ok","queue":load_queue()})

    elif action == "dismiss_queue_item":
        job_id = msg.get("job_id")
        items  = [i for i in load_queue() if i.get("job_id") != job_id]
        save_queue(items)
        send_raw({"type":"response","_id":mid,"status":"ok"})

def main():
    while True:
        msg = read_msg()
        if msg is None: break
        threading.Thread(target=handle, args=(msg,), daemon=True).start()

if __name__ == "__main__":
    main()
