# SwarScribe Chrome extension

Dictate into any text field on the web: Gmail, LinkedIn, ChatGPT,
docs, forms. A small coral mic button appears next to the field you
focus; speak, and cleaned text lands at your cursor.

## Install (developer mode, 1 minute)

1. Open `chrome://extensions`, turn on **Developer mode**.
2. Click **Load unpacked**, choose this `extension/` folder.
3. Focus any text field and tap the **🎙 Swar** button.

## Honest notes

- Speech recognition uses the browser's built-in recognizer, the same
  one the web demo uses. In Chrome that recognition is a Google service;
  the cleanup itself runs locally in the page and this extension sends
  nothing anywhere.
- For fully offline recognition, use the desktop app, which runs
  Whisper and Parakeet on your machine.
- Store submission (icons, listing copy, privacy form) is prepared in
  this folder; publishing needs the developer account holder to submit,
  which is a one-time manual step.
