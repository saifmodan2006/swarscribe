// Adds a small SwarScribe mic button next to focused text fields.
// Uses the browser's own speech recognition where available; the
// cleanup always runs locally in this page. Nothing is uploaded by
// this extension: recognition, if used, is the browser's own service,
// exactly as with the GitHub Pages demo.
(function () {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let button = null;
  let activeField = null;
  let recognizer = null;

  function makeButton() {
    const b = document.createElement("button");
    b.textContent = "🎙 Swar";
    b.title = "Dictate with SwarScribe";
    b.style.cssText = "position:absolute;z-index:2147483647;background:#FF5A36;" +
      "color:#FAF5EC;border:none;border-radius:999px;padding:4px 10px;" +
      "font:600 12px system-ui;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.3)";
    b.addEventListener("mousedown", (e) => { e.preventDefault(); toggle(); });
    document.body.appendChild(b);
    return b;
  }

  function place(field) {
    const r = field.getBoundingClientRect();
    button.style.left = (window.scrollX + r.right - 74) + "px";
    button.style.top = (window.scrollY + r.top - 30) + "px";
  }

  function toggle() {
    if (!Recognition) {
      alert("This browser has no speech recognition. Type or paste raw " +
            "dictation, select it, and press the button is not needed: " +
            "SwarScribe cleanup runs in the full web demo.");
      return;
    }
    if (recognizer) { recognizer.stop(); recognizer = null; button.textContent = "🎙 Swar"; return; }
    recognizer = new Recognition();
    recognizer.lang = "en-IN";
    recognizer.interimResults = false;
    recognizer.onresult = (event) => {
      const raw = event.results[0][0].transcript;
      const cleaned = window.SwarCleanup.cleanText(raw);
      insertAtCursor(activeField, cleaned);
    };
    recognizer.onend = () => { recognizer = null; if (button) button.textContent = "🎙 Swar"; };
    button.textContent = "● Listening";
    recognizer.start();
  }

  function insertAtCursor(field, text) {
    if (!field) return;
    if (field.isContentEditable) {
      document.execCommand("insertText", false, text);
      return;
    }
    const start = field.selectionStart || field.value.length;
    const end = field.selectionEnd || field.value.length;
    field.value = field.value.slice(0, start) + text + field.value.slice(end);
    field.dispatchEvent(new Event("input", { bubbles: true }));
  }

  document.addEventListener("focusin", (e) => {
    const f = e.target;
    const ok = f && (f.tagName === "TEXTAREA" || f.isContentEditable ||
      (f.tagName === "INPUT" && ["text", "search", ""].includes(f.type)));
    if (!ok) return;
    activeField = f;
    if (!button) button = makeButton();
    button.style.display = "block";
    place(f);
  });
  document.addEventListener("focusout", () => {
    setTimeout(() => { if (button && !recognizer) button.style.display = "none"; }, 200);
  });
})();
