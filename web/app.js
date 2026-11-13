// SwarScribe web demo: a faithful JS port of the Python cleanup
// pipeline (fillers, self-corrections, spoken punctuation, calendar
// capitalisation, formal/casual styles) so the demo runs anywhere
// with zero backend. The Python package is the full version.

const $ = (id) => document.getElementById(id);
let wordCount = 0;

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
  thirty:30 });

function smartFormatsJS(t) {
  // Email: "saif modan at gmail dot com" -> saifmodan@gmail.com
  t = t.replace(/\b((?:(?!(?:is|the|my|email|address|send|please|and|to)\s)\w+\s+){0,3}(?!(?:is|the|my|email|address|send|please|and|to)\b)\w+)\s+at\s+((?:\w+\s+){0,2}\w+)\s+dot\s+(com|in|io|org|net|dev|ai)\b/gi,
    (m, a, b, tld) => a.replace(/\s+/g, "").toLowerCase() + "@" +
      b.replace(/\s+/g, "").toLowerCase() + "." + tld.toLowerCase());
  // Website: "devbysaif dot in" -> devbysaif.in
  t = t.replace(/\b(\w+)\s+dot\s+(com|in|io|org|net|dev|ai)\b/gi,
    (m, a, tld) => a.toLowerCase() + "." + tld.toLowerCase());
  // Time: "five thirty pm" -> 5:30 PM ; "five pm" -> 5 PM
  t = t.replace(/\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(twenty|thirty|forty|fifty)(?:\s+(one|two|three|four|five|six|seven|eight|nine))?\s+(am|pm)\b/gi,
    (m, h, tens, ones, ap) => HOUR_WORDS[h.toLowerCase()] + ":" +
      String(NUM_WORDS[tens.toLowerCase()] + (ones ? HOUR_WORDS[ones.toLowerCase()] : 0)).padStart(2, "0") +
      " " + ap.toUpperCase());
  t = t.replace(/\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(am|pm)\b/gi,
    (m, h, ap) => HOUR_WORDS[h.toLowerCase()] + " " + ap.toUpperCase());
  // Date: "fifteen november 2026" -> 15 November 2026
  t = t.replace(/\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty)(?:\s+(one|two|three|four|five|six|seven|eight|nine))?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b(?:\s+(\d{4}))?/gi,
    (m, a, b, mon, yr) => {
      let v = NUM_WORDS[a.toLowerCase()] + (b ? HOUR_WORDS[b.toLowerCase()] : 0);
      if (v > 31) return m;
      return v + " " + mon.charAt(0).toUpperCase() + mon.slice(1).toLowerCase() + (yr ? " " + yr : "");
    });
  // Built-in snippet from the Python defaults.
  t = t.replace(/\bmy portfolio\b/gi, "https://www.devbysaif.in/");
  return t;
}

let sessionWords = 0, sessionEdits = 0;
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
  t = t.replace(/snake case ((?:\w+\s+){0,4}\w+?)(?=\s+equals\b|$)/gi,
    (m, g) => g.trim().toLowerCase().split(/\s+/).join("_"));
  t = t.replace(/camel case ((?:\w+\s+){0,4}\w+)$/gi,
    (m, g) => { const w = g.trim().toLowerCase().split(/\s+/);
      return w[0] + w.slice(1).map(x => x.charAt(0).toUpperCase() + x.slice(1)).join(""); });
  const nums = { five: "5", four: "4", three: "3", two: "2", one: "1", zero: "0", ten: "10" };
  for (const [w, d] of Object.entries(nums))
    t = t.replace(new RegExp("\\b" + w + "\\b", "gi"), d);
  return t.replace(/\s*equals\s*/gi, " = ");
}

function clean() {
  let raw = $("input").value.trim();
  if (!raw) return;
  const started = performance.now();
  let t = capitalise(smartFormatsJS(spokenPunctuation(removeFillers(selfCorrect(raw)))));
  if ($("code").checked) t = toCodeJS(t);
  t = applyStyleJS(t, $("style").value);
  if (t && /[a-z0-9]$/i.test(t) && !$("code").checked) t += ".";
  $("output").value = t;
  const words = t.split(/\s+/).filter(Boolean).length;
  wordCount += words;
  sessionWords += words;
  sessionEdits += countEdits(raw, t);
  $("stat-words").textContent = sessionWords;
  $("stat-edits").textContent = sessionEdits;
  const secs = ((performance.now() - started) / 1000).toFixed(2);
  $("stats").textContent = words + " words cleaned in " + secs +
    "s on this device. Session total: " + wordCount + " words.";
}

document.querySelectorAll("[data-example]").forEach((chip) =>
  chip.addEventListener("click", () => {
    $("input").value = chip.dataset.example;
    clean();
  }));

$("clean").addEventListener("click", clean);
$("copy").addEventListener("click", () =>
  navigator.clipboard.writeText($("output").value));

document.querySelectorAll("[data-cmd]").forEach((btn) =>
  btn.addEventListener("click", () => {
    let t = $("output").value;
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
if (SR) {
  const rec = new SR();
  rec.lang = "en-IN"; rec.interimResults = false;
  rec.onresult = (e) => { $("input").value =
    Array.from(e.results).map((r) => r[0].transcript).join(" "); clean(); };
  $("mic").addEventListener("click", () => rec.start());
} else {
  $("mic").disabled = true;
  $("mic").textContent = "Mic not supported in this browser";
}
