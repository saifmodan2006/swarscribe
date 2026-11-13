// SwarScribe cleanup, browser port (mirrors web/cleanup.js rules).
(function () {
  const FILLERS = ["um", "uh", "erm", "hmm", "mm"];
  function cleanText(raw) {
    let t = " " + String(raw).toLowerCase().replace(/\s+/g, " ") + " ";
    t = t.replace(/\b(\w+) \1\b/g, "$1");
    for (const f of FILLERS) t = t.replace(new RegExp(` ${f}[,.]? `, "g"), " ");
    t = t.replace(/\b(\w+) no wait (\w+)\b/g, "$2");
    t = t.replace(/ comma /g, ", ").replace(/ period /g, ". ")
      .replace(/ question mark /g, "? ").replace(/ exclamation mark /g, "! ")
      .replace(/ colon /g, ": ").replace(/ new line /g, "\n")
      .replace(/ open bracket /g, "(").replace(/ close bracket /g, ")");
    t = t.replace(/\s+([,.!?;:])/g, "$1").replace(/\s+/g, " ").trim();
    t = t.replace(/(^\s*[a-z])|([.!?]\s+[a-z])/g, (m) => m.toUpperCase());
    if (t && !/[.!?]$/.test(t)) t += ".";
    return t;
  }
  window.SwarCleanup = { cleanText };
})();
