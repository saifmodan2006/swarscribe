// SwarScribe for Obsidian: select raw dictated text in a note, run the
// command, and it is replaced with SwarScribe-cleaned text via the
// local CLI. Nothing leaves the machine.
const { Plugin, Notice } = require("obsidian");
const { execFile } = require("child_process");

module.exports = class SwarScribePlugin extends Plugin {
  async onload() {
    this.addCommand({
      id: "clean-selection",
      name: "Clean selected dictation",
      editorCallback: (editor) => {
        const selected = editor.getSelection();
        if (!selected) {
          new Notice("Select some raw dictation first.");
          return;
        }
        execFile("swarscribe", ["clean", selected], { timeout: 15000 },
          (error, stdout) => {
            if (error) {
              new Notice("SwarScribe CLI not found: pip install swarscribe");
              return;
            }
            editor.replaceSelection(stdout.replace(/\n$/, ""));
            new Notice("Cleaned by SwarScribe.");
          });
      },
    });
  }
};
