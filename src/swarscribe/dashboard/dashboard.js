"use strict";
const byId = id => document.getElementById(id);
const status = byId("status");

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

async function request(path, method = "GET", body) {
  const headers = {"X-SwarScribe-Local": "1"};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {method, headers,
    body: body === undefined ? undefined : JSON.stringify(body), cache:"no-store"});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed (" + response.status + ").");
  return data;
}

function showStatus(message, failed = false) {
  status.textContent = message;
  status.dataset.error = failed;
}

function handle(callback, control) {
  return async event => {
    event.preventDefault();
    if (control) control.disabled = true;
    try { showStatus(await callback() || "Local data is up to date."); }
    catch (error) { showStatus("Unable to update dashboard: " + error.message, true); }
    finally { if (control) control.disabled = false; }
  };
}

function editor(name, entries) {
  const root = byId(name);
  const form = element("form");
  const rows = element("div");
  const empty = element("p", "No entries yet. Add a spoken phrase and its replacement.");
  empty.className = "empty";
  function updateEmpty() { empty.hidden = rows.children.length > 0; }
  function add(key = "", value = "") {
    const row = element("div");
    row.className = "entry";
    const heard = element("input");
    heard.value = key; heard.required = true; heard.maxLength = 120;
    heard.placeholder = "Spoken phrase"; heard.setAttribute("aria-label", "Spoken phrase");
    const written = element("textarea");
    written.rows = 1; written.value = value; written.required = true; written.maxLength = 2000;
    written.placeholder = "Replacement"; written.setAttribute("aria-label", "Replacement");
    const remove = element("button", "Remove");
    remove.type = "button";
    remove.onclick = () => { row.remove(); updateEmpty(); more.focus(); };
    row.append(heard, written, remove);
    rows.append(row);
    updateEmpty();
    return heard;
  }
  Object.entries(entries).forEach(([key, value]) => add(key, value));
  const more = element("button", "Add row"); more.type = "button"; more.onclick = () => add().focus();
  const save = element("button", "Save " + name);
  save.className = "primary";
  const controls = element("div"); controls.className = "actions"; controls.append(more, save);
  form.append(empty, rows, controls);
  updateEmpty();
  form.onsubmit = handle(async () => {
    const pairs = Array.from(rows.children, row =>
      [row.children[0].value.trim().toLowerCase(), row.children[1].value]);
    const values = Object.fromEntries(pairs);
    if (Object.keys(values).length !== pairs.length) throw new Error("Spoken phrases must be unique.");
    const result = await request("/" + name, "PUT", {entries: values});
    editor(name, result.entries);
    root.querySelector("button[type=button], button").focus();
  }, save);
  root.replaceChildren(form);
}

function renderHistory(root, entries, removable) {
  root.replaceChildren();
  if (!entries.length) {
    const message = element("p", removable ? "No matching saved dictation." : "New dictation appears here when transcript history is enabled.");
    message.className = "empty";
    root.append(message);
  }
  entries.forEach(entry => {
    const row = element("article"); row.className = "item";
    const actions = element("div");
    actions.className = "actions";
    const copy = element("button", "Copy");
    copy.type = "button";
    copy.onclick = handle(async () => { await navigator.clipboard.writeText(entry.text); return "Transcript copied."; }, copy);
    actions.append(copy);
    if (removable) {
      const remove = element("button", "Delete");
      remove.type = "button";
      remove.className = "danger";
      remove.onclick = handle(async () => {
        await request("/history/" + encodeURIComponent(entry.id), "DELETE");
        await loadHistory();
        byId("search").querySelector("input").focus();
        return "Transcript deleted.";
      }, remove);
      actions.append(remove);
    }
    row.append(element("small", new Date(entry.timestamp * 1000).toLocaleString()),
      element("p", entry.text), actions);
    root.append(row);
  });
}

async function loadHistory() {
  const query = new FormData(byId("search")).get("query").trim();
  const all = await request("/history");
  const filtered = query ? await request("/history?q=" + encodeURIComponent(query)) : all;
  renderHistory(byId("history"), filtered.entries, true);
  renderHistory(byId("recent"), all.entries.slice(0, 3), false);
}

function updateShortcut(settings) {
  const shortcuts = settings.hotkey.split("+").map(key => element("kbd", key.trim().toUpperCase()));
  byId("shortcut").replaceChildren(...shortcuts);
  byId("shortcut-help").textContent = settings.toggle
    ? "With the tray running, tap the shortcut to start or stop. Press Esc to cancel."
    : "With the tray running, hold the shortcut to record. Release it to transcribe.";
}

async function refreshUsage() {
  const [stats, modelData] = await Promise.all([request("/stats"), request("/models"), loadHistory()]);
  const captions = {total_words:"Words dictated", sessions:"Dictation sessions",
    average_wpm:"Average speaking WPM", minutes_saved:"Estimated minutes saved"};
  const metrics = [];
  for (const [key, caption] of Object.entries(captions)) {
    if (typeof stats[key] !== "number") throw new Error("Usage data is incomplete.");
    const card = element("div");
    card.className = "metric";
    card.append(element("b", stats[key].toLocaleString()), element("small", caption));
    metrics.push(card);
  }
  byId("stats").replaceChildren(...metrics);
  byId("models").replaceChildren(...modelData.models.map(model => {
    const card = element("li");
    card.className = "model";
    card.append(element("h3", model.name),
      element("small", model.engine + " · ~" + model.size_mb.toLocaleString() + " MB"),
      element("p", model.note),
      element("small", model.downloaded ? "Cached on this computer" : "No verified local cache"));
    return card;
  }));
}

function navigate(hash = location.hash) {
  const links = Array.from(document.querySelectorAll("[data-page]"));
  const current = links.find(link => link.hash === hash) || links[0];
  for (const link of links) {
    if (link === current) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
    byId(link.dataset.page).hidden = link !== current;
  }
  byId("breadcrumb").textContent = "Workspace / " + current.lastChild.textContent.trim();
}

async function initialize() {
  const [dictionary, snippets, settings] = await Promise.all(
    ["/dictionary", "/snippets", "/settings"].map(path => request(path)));
  for (const [name, value] of Object.entries(settings)) {
    const control = byId("settings").elements.namedItem(name);
    if (control.type === "checkbox") control.checked = value;
    else {
      if (control.tagName === "SELECT" && value && !Array.from(control.options).some(o => o.value === value))
        control.add(new Option(value, value));
      control.value = value ?? "";
    }
  }
  byId("settings").onsubmit = handle(async () => {
    const fields = Object.fromEntries(new FormData(byId("settings")));
    for (const field of ["toggle", "local_only", "keep_history"])
      fields[field] = byId("settings").elements.namedItem(field).checked;
    for (const field of ["style", "language", "model", "ollama_model"]) fields[field] ||= null;
    fields.history_days = Number(fields.history_days);
    const saved = await request("/settings", "PUT", fields);
    updateShortcut(saved);
    await loadHistory();
    return "Settings saved.";
  }, byId("settings").querySelector("button"));
  byId("search").onsubmit = handle(loadHistory);
  byId("clear").onclick = handle(async () => {
    if (!window.confirm("Delete all saved SwarScribe transcripts from this computer?")) return "History kept.";
    await request("/history", "DELETE");
    await loadHistory();
    return "Saved transcripts cleared.";
  }, byId("clear"));
  editor("dictionary", dictionary.entries);
  editor("snippets", snippets.entries);
  updateShortcut(settings);
  await refreshUsage();
  byId("panels").hidden = false;
  byId("refresh").hidden = false;
  byId("refresh").onclick = handle(refreshUsage, byId("refresh"));
  byId("copy-command").onclick = handle(async () => {
    await navigator.clipboard.writeText(byId("model-command").textContent);
    return "Model download command copied.";
  }, byId("copy-command"));
}

navigate();
window.addEventListener("hashchange", () => navigate());
for (const link of document.querySelectorAll("[data-page]")) {
  link.addEventListener("click", event => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (location.hash !== link.hash) window.history.pushState(null, "", link.hash);
    navigate(link.hash);
  });
}
window.addEventListener("popstate", () => navigate());
handle(initialize)({preventDefault() {}});
