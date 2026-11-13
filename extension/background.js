// SwarScribe background worker: clicking the toolbar icon focuses the
// page's first text field so the mic button appears right away.
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const field = document.querySelector(
        "textarea, input[type=text], input[type=search], [contenteditable]");
      if (field) field.focus();
    },
  });
});
