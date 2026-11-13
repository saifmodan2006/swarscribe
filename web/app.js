// SwarScribe web demo: a faithful JS port of the Python cleanup
// pipeline (fillers, self-corrections, spoken punctuation, calendar
// capitalisation, formal/casual styles) so the demo runs anywhere
// with zero backend. The Python package is the full version.

function removeFillers(t) {
  return t.replace(/\b(um+|uh+|er+|hmm+)\b,?/gi, " ")
          .replace(/\byou know\b,?/gi, " ");
}

function selfCorrect(t) {
  // Single-word swap around "no wait": monday no wait tuesday -> Tuesday
  return t.replace(/(\w+),?\s+no wait,?\s+(\w+)/gi,
    (m, a, b) => b.charAt(0).toUpperCase() + b.slice(1));
}

function spokenPunctuation(t) {
  const map = [["question mark", "?"], ["exclamation mark", "!"],
    ["full stop", "."], ["period", "."], ["comma", ","],
    ["colon", ":"], ["semicolon", ";"], ["new paragraph", "\n\n"],
    ["new line", "\n"]];
  for (const [phrase, sym] of map) {
    t = t.replace(new RegExp("\\s*\\b" + phrase + "\\b\\s*", "gi"), sym + " ");
  }
  return t.replace(/\s+([,.!?;:])/g, "$1").replace(/[ ]{2,}/g, " ").trim();
}

function capitalise(t) {
  t = t.replace(/(^\s*\w|[.!?]\s*\w)/g, (c) => c.toUpperCase());
  const days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];
  for (const d of days) t = t.replace(new RegExp("\\b" + d + "\\b", "gi"),
    d.charAt(0).toUpperCase() + d.slice(1));
  return t.replace(/\bi\b/g, "I");
}

const HOUR_WORDS = { one:1, two:2, three:3, four:4, five:5, six:6, seven:7,
  eight:8, nine:9, ten:10, eleven:11, twelve:12 };
const NUM_WORDS = Object.assign({}, HOUR_WORDS, { thirteen:13, fourteen:14,
  fifteen:15, sixteen:16, seventeen:17, eighteen:18, nineteen:19, twenty:20,
  thirty:30, forty:40, fifty:50, sixty:60, seventy:70, eighty:80, ninety:90, zero:0 });
const HOUR = Object.keys(HOUR_WORDS).join("|");
const DIGIT = Object.keys(NUM_WORDS).filter(w => NUM_WORDS[w] < 10).join("|");
const UNIT = Object.keys(NUM_WORDS).filter(w => NUM_WORDS[w] > 0 && NUM_WORDS[w] < 10).join("|");
const TEEN = Object.keys(NUM_WORDS).filter(w => NUM_WORDS[w] < 20).join("|");
const TENS = "twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety";
const MINUTE = "(?:(?:twenty|thirty|forty|fifty)(?:[ -]+(?:" + UNIT + "))?|(?:" + TEEN + "))";
const CARDINAL = "(?:(?:" + TENS + ")(?:[ -]+(?:" + UNIT + "))?|(?:" + TEEN + "))";
const WHOLE = "(?:(?:" + UNIT + ") hundred(?: (?:and )?" + CARDINAL + ")?|" + CARDINAL + ")";

function number(phrase) {
  let value = 0;
  for (const word of phrase.toLowerCase().split(/[ -]+/)) {
    if (word === "hundred") value *= 100;
    else if (word !== "and") value += NUM_WORDS[word];
  }
  return value;
}

function smartFormatsJS(t) {
  // Email: "saif modan at gmail dot com" -> saifmodan@gmail.com
  t = t.replace(/\b((?:(?!(?:is|the|my|email|address|send|please|and|to)\s)\w+\s+){0,3}(?!(?:is|the|my|email|address|send|please|and|to)\b)\w+)\s+at\s+((?:\w+\s+){0,2}\w+)\s+dot\s+(com|in|io|org|net|dev|ai)\b/gi,
    (m, a, b, tld) => a.replace(/\s+/g, "").toLowerCase() + "@" +
      b.replace(/\s+/g, "").toLowerCase() + "." + tld.toLowerCase());
  // Website: "devbysaif dot in" -> devbysaif.in
  t = t.replace(/\b(\w+)\s+dot\s+(com|in|io|org|net|dev|ai)\b/gi,
    (m, a, tld) => a.toLowerCase() + "." + tld.toLowerCase());
  // Time: "five thirty pm" -> 5:30 PM ; "five pm" -> 5 PM
  const time = new RegExp("\\b(" + HOUR + ") +(" + MINUTE + ") +(am|pm)\\b", "gi");
  const renderTime = (h, minute) => HOUR_WORDS[h.toLowerCase()] + ":" + String(number(minute)).padStart(2, "0");
  t = t.replace(time, (m, h, minute, ap) => renderTime(h, minute) + " " + ap.toUpperCase());
  // Without AM/PM, convert only a whole phrase or after a time cue.
  const bareTime = new RegExp("(^|\\b(?:at|around|by) +)(" + HOUR + ") +(" + MINUTE +
    ")(?=\\s*(?:[,.!?;]|$))", "gi");
  t = t.replace(bareTime, (m, cue, h, minute) => cue + renderTime(h, minute));
  t = t.replace(new RegExp("\\b(" + HOUR + ") +(am|pm)\\b", "gi"),
    (m, h, ap) => HOUR_WORDS[h.toLowerCase()] + " " + ap.toUpperCase());
  // Date: "fifteen november 2026" -> 15 November 2026
  const months = "january february march april may june july august september october november december".split(" ");
  t = t.replace(new RegExp("\\b(" + CARDINAL + ") +(" + months.join("|") + ")\\b(?: +(\\d{4}))?", "gi"),
    (m, a, mon, yr) => {
      const v = number(a);
      const max = new Date(Date.UTC(Number(yr || 2000), months.indexOf(mon.toLowerCase()) + 1, 0)).getUTCDate();
      if (v < 1 || v > max) return m;
      return v + " " + mon.charAt(0).toUpperCase() + mon.slice(1).toLowerCase() + (yr ? " " + yr : "");
    });
  const decimal = new RegExp("\\b(" + WHOLE + ") point ((?:" + DIGIT + ")(?: +(?:" + DIGIT + "))*)\\b", "gi");
  t = t.replace(decimal, (m, whole, digits) => number(whole) + "." +
    digits.toLowerCase().split(/ +/).map(w => NUM_WORDS[w]).join(""));
  t = t.replace(new RegExp("\\b(" + WHOLE + ") +(rupees|dollars|euros|pounds)\\b", "gi"),
    (m, whole, currency) => number(whole) + " " + currency);
  // Built-in snippet from the Python defaults.
  t = t.replace(/\bmy portfolio\b/gi, "https://www.devbysaif.in/");
  return t;
}

function countEdits(before, after) {
  const a = before.toLowerCase().split(/\s+/), b = after.toLowerCase().split(/\s+/);
  let diff = Math.abs(a.length - b.length);
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) diff++;
  return diff;
}

function applyStyleJS(t, style) {
  const exp = { "can't": "cannot", "won't": "will not", "don't": "do not",
    "i'm": "I am", "it's": "it is", "that's": "that is", "let's": "let us" };
  const con = Object.fromEntries(Object.entries(exp).map(([k, v]) => [v, k]));
  const swap = (map) => { for (const [a, b] of Object.entries(map))
    t = t.replace(new RegExp("\\b" + a + "\\b", "gi"), b); };
  if (style === "formal" || style === "email") swap(exp);
  if (style === "casual") swap(con);
  if (style === "email") t = t.replace(/^(hi|hey)\b/i, "Hello");
  return t;
}

function toCodeJS(t) {
  t = t.replace(/snake case ((?:\w+\s+){0,4}?\w+?)(?=\s+equals\b|$)/gi,
    (m, g) => g.trim().toLowerCase().split(/\s+/).join("_"));
  t = t.replace(/camel case ((?:\w+\s+){0,4}\w+)$/gi,
    (m, g) => { const w = g.trim().toLowerCase().split(/\s+/);
      return w[0] + w.slice(1).map(x => x.charAt(0).toUpperCase() + x.slice(1)).join(""); });
  const nums = { five: "5", four: "4", three: "3", two: "2", one: "1", zero: "0", ten: "10" };
  for (const [w, d] of Object.entries(nums))
    t = t.replace(new RegExp("\\b" + w + "\\b", "gi"), d);
  return t.replace(/\s*\bdouble equals\b\s*/gi, " == ")
    .replace(/\s*\bequals\b\s*/gi, " = ");
}

function formatTranscript(raw, {code = false, style = ""} = {}) {
  if (code) return toCodeJS(raw.trim());
  const text = applyStyleJS(capitalise(smartFormatsJS(spokenPunctuation(removeFillers(selfCorrect(raw))))), style);
  const list = text.match(/^first\s+(.+?)\s+second\s+(.+?)\s+third\s+(.+)$/i);
  if (list) return list.slice(1).map(item => "- " + item.trim().replace(/[,.]$/, "")).join("\n");
  return text && /[a-z0-9]$/i.test(text) ? text + "." : text;
}

function exampleReport(input, output, options) {
  return JSON.stringify({input, output, mode: options.code ? "code" : "dictation",
    style: options.style || "default"}, null, 2);
}

if (typeof module !== "undefined") module.exports = {formatTranscript, smartFormatsJS, exampleReport};

function bindDemo() {
const $ = id => document.getElementById(id);
const status = $("status");
let sessionWords = 0, sessionEdits = 0;

function clean(count = true) {
  clearReport();
  const raw = $("input").value.trim();
  const t = formatTranscript(raw, {code:$("code").checked, style:$("style").value});
  $("output").value = t;
  const words = t.split(/\s+/).filter(Boolean).length;
  if (count && raw && t) {
    sessionWords += words;
    sessionEdits += countEdits(raw, t);
  }
  $("stat-words").textContent = sessionWords;
  $("stat-edits").textContent = sessionEdits;
  status.textContent = raw ? words + " words in the output." : "Enter text or try the browser mic.";
}

document.querySelectorAll("[data-example]").forEach((chip) =>
  chip.addEventListener("click", () => {
    $("input").value = chip.dataset.example;
    $("code").checked = chip.dataset.code === "true";
    clean();
  }));

$("clean").addEventListener("click", () => clean());
for (const id of ["code", "style"]) $(id).addEventListener("change", () => clean(false));
$("clear").addEventListener("click", () => {
  if (recognition) {
    const old = recognition;
    recognition = null;
    try { old.abort(); } catch { /* already ended */ }
    $("mic").disabled = false;
    $("mic").textContent = "Start browser mic";
  }
  $("input").value = "";
  clean(false);
  $("input").focus();
});
$("copy").addEventListener("click", async () => {
  if (!$("output").value) { status.textContent = "There is no output to copy yet."; return; }
  try { await navigator.clipboard.writeText($("output").value); status.textContent = "Copied."; }
  catch { status.textContent = "Copy failed. Select and copy the output manually."; $("output").select(); }
});

const report = $("example-report");
const reportStatus = $("example-status");
$("copy-example").addEventListener("click", async () => {
  const input = $("input").value.trim();
  if (!input) {
    report.hidden = true;
    report.value = "";
    reportStatus.textContent = "Enter a test phrase or choose an example first.";
    return;
  }
  const options = {code: $("code").checked, style: $("style").value};
  const reproduction = exampleReport(input, formatTranscript(input, options), options);
  report.hidden = true;
  report.value = "";
  try {
    await navigator.clipboard.writeText(reproduction);
    reportStatus.textContent = "Test case copied. Add your expected output in the bug form.";
  } catch {
    report.value = reproduction;
    report.hidden = false;
    report.focus();
    report.select();
    reportStatus.textContent = "Copy this test case manually.";
  }
});
function clearReport() {
  report.hidden = true;
  report.value = "";
  reportStatus.textContent = "";
}
$("input").addEventListener("input", clearReport);

document.querySelectorAll("[data-cmd]").forEach((btn) =>
  btn.addEventListener("click", () => {
    let t = $("output").value;
    if (!t) { status.textContent = "Clean some text before applying a command."; return; }
    const cmd = btn.dataset.cmd;
    if (cmd === "make it formal") t = applyStyleJS(t, "formal");
    if (cmd === "make it shorter")
      t = t.replace(/\b(very|really|just|actually|basically)\b\s*/gi, "");
    if (cmd === "make it a list")
      t = t.replace(/\.$/, "").split(/,\s*|\s+and\s+/)
           .map((x) => "- " + x.trim()).join("\n");
    if (cmd === "uppercase") t = t.toUpperCase();
    $("output").value = t;
  }));

// Mic input via the browser SpeechRecognition API when available.
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
if (SR) {
  const mic = $("mic");
  mic.addEventListener("click", () => {
    if (recognition) {
      mic.disabled = true;
      status.textContent = "Recognizing…";
      try { recognition.stop(); }
      catch { mic.disabled = false; status.textContent = "The browser mic could not stop."; }
      return;
    }
    const rec = new SR();
    recognition = rec;
    rec.lang = $("language").value;
    rec.onresult = e => {
      if (recognition !== rec) return;
      const text = Array.from(e.results).map(r => r[0].transcript).join(" ");
      $("input").value = [$("input").value.trim(), text].filter(Boolean).join(" ");
      clean();
    };
    rec.onerror = e => { if (recognition === rec) status.textContent = "Browser speech error: " + e.error + ". You can still type or paste text."; };
    rec.onend = () => { if (recognition !== rec) return;
      recognition = null; mic.disabled = false; mic.textContent = "Start browser mic";
      if (status.textContent === "Listening via your browser…" || status.textContent === "Recognizing…")
        status.textContent = "No browser transcript received.";
    };
    try { rec.start(); mic.textContent = "Stop mic"; status.textContent = "Listening via your browser…"; }
    catch { recognition = null; status.textContent = "The browser microphone could not start."; }
  });
} else {
  $("mic").disabled = true;
  $("mic").textContent = "Mic not supported in this browser";
}
}

if (typeof document !== "undefined") bindDemo();
