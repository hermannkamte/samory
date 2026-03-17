let port = null;
const pending = {};

function getPort() {
  if (port) return port;
  port = chrome.runtime.connectNative("com.hka.ytdlp");
  port.onMessage.addListener(function(msg) {
    if (msg.type === "progress") {
      chrome.runtime.sendMessage(msg).catch(function(){});
    } else if (msg.type === "response" && msg._id && pending[msg._id]) {
      pending[msg._id](msg);
      delete pending[msg._id];
    }
  });
  port.onDisconnect.addListener(function() { port = null; });
  return port;
}

chrome.runtime.onMessage.addListener(function(msg, sender, sendResponse) {
  var id = Math.random().toString(36).slice(2);
  msg._id = id;
  pending[id] = sendResponse;
  try {
    getPort().postMessage(msg);
  } catch(e) {
    port = null;
    try { getPort().postMessage(msg); }
    catch(e2) { sendResponse({type:"response", status:"error", message:String(e2)}); }
  }
  return true;
});
