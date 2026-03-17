var paused = false;

// ── Helpers ───────────────────────────────────────────────
function send(msg, cb) {
  chrome.runtime.sendMessage(msg, function(res) {
    cb(chrome.runtime.lastError ? null : res);
  });
}

function setStatus(txt, cls) {
  var el = document.getElementById("status");
  el.textContent = txt; el.className = cls || "";
}

function setRunning(on) {
  ["mp3","mp4","pl_audio","pl_video"].forEach(function(id) {
    document.getElementById(id).disabled = on;
  });
  document.getElementById("ctrl").classList.toggle("show", on);
  document.getElementById("prog-wrap").style.display = on ? "block" : "none";
  if (!on) {
    document.getElementById("prog-bar").style.width = "0%";
    paused = false;
    document.getElementById("btn-pause").disabled  = false;
    document.getElementById("btn-resume").disabled = true;
  }
}

// ── Tabs ──────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach(function(tab) {
  tab.addEventListener("click", function() {
    document.querySelectorAll(".tab").forEach(function(t)  { t.classList.remove("active"); });
    document.querySelectorAll(".panel").forEach(function(p) { p.classList.remove("active"); });
    tab.classList.add("active");
    document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
    if (tab.dataset.tab === "hist")  loadHist();
    if (tab.dataset.tab === "queue") loadQueue();
    if (tab.dataset.tab === "set")   loadCfg();
  });
});

// ── URL auto-fill ─────────────────────────────────────────
chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
  if (tabs[0]) document.getElementById("url").value = tabs[0].url;
});

// ── Écoute progression depuis background ─────────────────
chrome.runtime.onMessage.addListener(function(msg) {
  if (msg.type !== "progress") return;
  var pct   = msg.percent || 0;
  var speed = msg.speed   || "";
  var eta   = msg.eta     || "";
  var dlsz  = msg.dl_size || "";
  var totsz = msg.tot_size|| "";
  document.getElementById("prog-bar").style.width = pct + "%";
  var info = pct.toFixed(1) + "%";
  if (dlsz && totsz) info += "  " + dlsz + " / " + totsz;
  if (speed) info += "  ↓" + speed;
  if (eta)   info += "  ETA " + eta;
  setStatus(info);
});

// ── Download ──────────────────────────────────────────────
function download(mode) {
  var url = document.getElementById("url").value.trim();
  if (!url) { setStatus("⚠ URL vide", "err"); return; }
  setStatus("⏳ Démarrage...");
  setRunning(true);
  send({ action: "start", url: url, mode: mode }, function(res) {
    setRunning(false);
    if (!res)                      { setStatus("✗ Host inaccessible", "err"); return; }
    if (res.status === "success")  { setStatus("✓ Terminé !", "ok"); }
    else if (res.status === "stopped") { setStatus("⏹ Arrêté", ""); }
    else                           { setStatus("✗ " + (res.message || "Erreur"), "err"); }
  });
}

document.getElementById("mp3").addEventListener("click",      function() { download("audio"); });
document.getElementById("mp4").addEventListener("click",      function() { download("video"); });
document.getElementById("pl_audio").addEventListener("click", function() { download("playlist_audio"); });
document.getElementById("pl_video").addEventListener("click", function() { download("playlist_video"); });

// ── Pause / Reprendre / Stop ──────────────────────────────
document.getElementById("btn-pause").addEventListener("click", function() {
  send({ action: "pause" }, function(res) {
    if (res && res.status === "ok") {
      paused = true;
      document.getElementById("btn-pause").disabled  = true;
      document.getElementById("btn-resume").disabled = false;
      setStatus("⏸ En pause");
    }
  });
});

document.getElementById("btn-resume").addEventListener("click", function() {
  send({ action: "resume" }, function(res) {
    if (res && res.status === "ok") {
      paused = false;
      document.getElementById("btn-pause").disabled  = false;
      document.getElementById("btn-resume").disabled = true;
      setStatus("⏳ Reprise...");
    }
  });
});

document.getElementById("btn-stop").addEventListener("click", function() {
  send({ action: "stop" }, function() {
    setRunning(false);
    setStatus("⏹ Arrêté");
  });
});

// ── File (queue) ──────────────────────────────────────────
var ML = { audio:"MP3", video:"MP4", playlist_audio:"PL MP3", playlist_video:"PL MP4" };

function loadQueue() {
  send({ action: "get_queue" }, function(res) {
    var el = document.getElementById("queue-list");
    if (!res || !res.queue || !res.queue.length) {
      el.innerHTML = '<div class="q-empty">Aucun téléchargement en file</div>'; return;
    }
    el.innerHTML = res.queue.map(function(item) {
      var isInt = item.status === "interrupted";
      var pct   = item.percent || 0;
      var label = ML[item.mode] || item.mode;
      var title = (item.title || item.url || "").substring(0, 44);
      var stTxt = isInt ? "⚠ Interrompu" : (item.status === "done" ? "✓ Terminé" : item.status || "");
      return '<div class="qrow">'
        + '<div class="qrow-top"><span class="qbadge ' + (isInt ? "bm-int" : "bm-" + item.mode) + '">' + label + '</span>'
        + '<span class="qtitle">' + title + '</span></div>'
        + '<div class="qpbg"><div class="qpbar' + (isInt ? " int" : "") + '" style="width:' + pct + '%"></div></div>'
        + '<div class="qbot"><span class="qst' + (isInt ? " int" : "") + '">' + stTxt + (pct > 0 ? " — " + pct.toFixed(0) + "%" : "") + '</span>'
        + '<div class="qacts">'
        + (isInt ? '<button class="qbtn qbtn-r" onclick="resumeItem(\'' + item.job_id + '\',\'' + item.url.replace(/'/g,"\\'") + '\',\'' + item.mode + '\')">▶ Reprendre</button>' : '')
        + '<button class="qbtn qbtn-d" onclick="dismissItem(\'' + item.job_id + '\')">✕</button>'
        + '</div></div></div>';
    }).join("");
  });
}

function resumeItem(jobId, url, mode) {
  send({ action: "start", url: url, mode: mode }, function(res) {
    if (res && res.status === "success") dismissItem(jobId); else loadQueue();
  });
}

function dismissItem(jobId) {
  send({ action: "dismiss_queue_item", job_id: jobId }, function() { loadQueue(); });
}

document.getElementById("refresh-queue").addEventListener("click", loadQueue);

// ── Historique ────────────────────────────────────────────
function loadHist() {
  send({ action: "history" }, function(res) {
    var el = document.getElementById("hist-list");
    if (!res || !res.history || !res.history.length) {
      el.innerHTML = '<div class="empty">Aucun téléchargement</div>'; return;
    }
    el.innerHTML = res.history.map(function(h) {
      return '<div class="hist-item"><div class="ht">' + (h.title || h.url || "") + '</div>'
        + '<div class="hm">' + (h.mode || "") + ' · ' + (h.time || "") + '</div></div>';
    }).join("");
  });
}

document.getElementById("clr-hist").addEventListener("click", function() {
  send({ action: "clear_history" }, function() { loadHist(); });
});

// ── Config ────────────────────────────────────────────────
function loadCfg() {
  send({ action: "get_config" }, function(res) {
    if (res && res.config) document.getElementById("out-dir").value = res.config.output_dir || "";
  });
}

document.getElementById("save-dir").addEventListener("click", function() {
  var path = document.getElementById("out-dir").value.trim();
  if (!path) return;
  send({ action: "set_output_dir", path: path }, function(res) {
    var el = document.getElementById("set-msg");
    el.textContent = res && res.status === "ok" ? "✓ Enregistré" : "✗ Erreur";
    setTimeout(function() { el.textContent = ""; }, 2000);
  });
});

// ── About GitHub ──────────────────────────────────────────
document.getElementById("gh-link").addEventListener("click", function() {
  chrome.tabs.create({ url: "https://github.com/hermannkamte" });
});
