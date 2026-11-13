// FlowScribe web demo: a faithful JS port of the Python cleanup
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
  let t = $("input").value.trim();
  if (!t) return;
  const started = performance.now();
  t = capitalise(spokenPunctuation(removeFillers(selfCorrect(t))));
  if ($("code").checked) t = toCodeJS(t);
  t = applyStyleJS(t, $("style").value);
  if (t && /[a-z0-9]$/i.test(t)) t += ".";
  $("output").value = t;
  const words = t.split(/\s+/).filter(Boolean).length;
  wordCount += words;
  const secs = ((performance.now() - started) / 1000).toFixed(2);
  $("stats").textContent = words + " words cleaned in " + secs +
    "s on this device. Session total: " + wordCount + " words.";
}

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
