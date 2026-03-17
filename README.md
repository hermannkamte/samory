# Samory

<div align="center">

**Open Source Audio & Video Downloader**

*Named after Samory Touré — West African sovereign and resistance leader*

[![License](https://img.shields.io/badge/License-Apache_2.0-BDA18A.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-9C7F67.svg)]()
[![yt-dlp](https://img.shields.io/badge/Powered_by-yt--dlp-BDA18A.svg)](https://github.com/yt-dlp/yt-dlp)

</div>

---

## What is Samory?

Samory is a free, open source downloader for audio and video from YouTube and 1000+ other sites.

- **Desktop app** — Windows .exe, multi-download queue, real-time progress, pause/resume/stop, 6 UN languages
- **Chrome extension** — download directly from the browser, synchronized with the app

---

## Features

- MP3 audio / MP4 video download
- Full playlist support
- Single track from playlist URL (`--no-playlist`)
- Real-time progress bar: %, speed, ETA, file size
- Pause / Resume / Stop per download
- Persistent queue — interrupted downloads restored on restart
- Shared history between app and extension
- 6 UN languages: French, English, Spanish, Arabic, Chinese, Russian
- Light / Dark / Auto theme
- Configurable output folder

---

## Prerequisites

```bash
winget install yt-dlp
winget install ffmpeg
pip install psutil
```

---

## Installation

### Desktop App

Download `SAMORY.exe` from [Releases](https://github.com/hermannkamte/samory/releases) and run it.

### Chrome Extension

1. Open `chrome://extensions` → enable Developer mode
2. Click **Load unpacked** → select the `extension/` folder
3. Copy the extension ID
4. Run in PowerShell:

```powershell
$id = "YOUR_EXTENSION_ID"
$json = Get-Content "host\com.hka.ytdlp.json" | ConvertFrom-Json
$json.allowed_origins = @("chrome-extension://$id/")
$json | ConvertTo-Json | Out-File "host\com.hka.ytdlp.json" -Encoding UTF8

$regPath = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.hka.ytdlp"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "(Default)" -Value "$PWD\host\com.hka.ytdlp.json"
```

---

## Project Structure

```
samory/
├── app/
│   └── samory.py           # Desktop app (Python + Tkinter)
├── extension/
│   ├── manifest.json       # Chrome MV3 manifest
│   ├── background.js       # Native messaging bridge
│   ├── popup.html          # Extension UI
│   └── popup.js            # Extension logic
├── host/
│   ├── yt_dlp_host.py      # Native messaging host
│   ├── yt_dlp_host.bat     # Host launcher
│   └── com.hka.ytdlp.json  # Host manifest
├── assets/
│   ├── logo.svg
│   └── samory.ico
├── LICENSE
└── README.md
```

---

## Build .exe

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --icon="assets\samory.ico" --add-data "assets\samory.ico;." --name "SAMORY" "app\samory.py"
```

---

## License

Copyright 2026 Hermann Kamté — Yaoundé, Cameroon  
Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE).

---

## Author

**Hermann Kamté** — Architect & Developer, Yaoundé, Cameroon  
[github.com/hermannkamte](https://github.com/hermannkamte)
