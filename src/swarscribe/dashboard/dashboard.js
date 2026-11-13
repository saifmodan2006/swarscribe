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

function handle(callback, control) {
  return async event => {
    event.preventDefault();
    if (control) control.disabled = true;
    try { await callback(); status.textContent = "Local data is up to date."; }
    catch (error) { status.textContent = "Unable to update dashboard: " + error.message; }
    finally { if (control) control.disabled = false; }
  };
}

function editor(name, entries) {
  const root = byId(name);
  const form = element("form");
  const rows = element("div");
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
    remove.type = "button"; remove.onclick = () => row.remove();
    row.append(heard, written, remove);
    rows.append(row);
  }
  Object.entries(entries).forEach(([key, value]) => add(key, value));
  const more = element("button", "Add row"); more.type = "button"; more.onclick = () => add();
  const save = element("button", "Save " + name);
  const controls = element("div"); controls.className = "actions"; controls.append(more, save);
  form.append(rows, controls);
  form.onsubmit = handle(async () => {
    const pairs = Array.from(rows.children, row =>
      [row.children[0].value.trim().toLowerCase(), row.children[1].value]);
    const values = Object.fromEntries(pairs);
    if (Object.keys(values).length !== pairs.length) throw new Error("Spoken phrases must be unique.");
    const result = await request("/" + name, "PUT", {entries: values});
    editor(name, result.entries);
  }, save);
  root.replaceChildren(form);
}

async function loadHistory() {
  const query = new FormData(byId("search")).get("query");
  const {entries} = await request("/history?q=" + encodeURIComponent(query));
  const root = byId("history");
  root.replaceChildren();
  if (!entries.length) root.append(element("p", "No matching saved dictation."));
  entries.forEach(entry => {
    const row = element("article"); row.className = "item";
    const remove = element("button", "Delete");
    remove.type = "button";
    remove.onclick = handle(async () => {
      await request("/history/" + encodeURIComponent(entry.id), "DELETE");
      await loadHistory();
    }, remove);
    row.append(element("small", new Date(entry.timestamp * 1000).toLocaleString()),
      element("p", entry.text), remove);
    root.append(row);
  });
}

async function initialize() {
  const [stats, models, dictionary, snippets, settings] = await Promise.all(
    ["/stats", "/models", "/dictionary", "/snippets", "/settings"].map(path => request(path)));
  const captions = {total_words:"Words dictated", sessions:"Dictation sessions",
    average_wpm:"Average speaking WPM", minutes_saved:"Estimated minutes saved"};
  for (const [key, caption] of Object.entries(captions)) {
    if (typeof stats[key] !== "number") throw new Error("Usage data is incomplete.");
    const card = element("div");
    card.append(element("b", stats[key].toLocaleString()), element("small", caption));
    byId("stats").append(card);
  }
  for (const model of models.models) {
    byId("models").append(element("li", model.name + " · " + model.engine + " · " +
      (model.downloaded ? "cached" : "no verified cache here")));
  }
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
    await request("/settings", "PUT", fields);
    await loadHistory();
  }, byId("settings").querySelector("button"));
  byId("search").onsubmit = handle(loadHistory);
  byId("clear").onclick = handle(async () => {
    if (!window.confirm("Delete all saved SwarScribe transcripts from this computer?")) return;
    await request("/history", "DELETE");
    await loadHistory();
  }, byId("clear"));
  editor("dictionary", dictionary.entries);
  editor("snippets", snippets.entries);
  await loadHistory();
  byId("panels").hidden = false;
}

handle(initialize)({preventDefault() {}});
