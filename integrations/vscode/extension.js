// SwarScribe for VS Code: pipes selected (raw dictated) text through
// the local `swarscribe clean` CLI and replaces it with clean text.
// Requires SwarScribe installed on PATH (pip install swarscribe, or the
// one-click binary). Everything runs locally.
const vscode = require("vscode");
const { execFile } = require("child_process");

function runClean(text, extraArgs, done) {
  execFile("swarscribe", ["clean", ...extraArgs, text],
    { timeout: 15000 }, (error, stdout) => {
      if (error) {
        vscode.window.showErrorMessage(
          "SwarScribe CLI not found. Install: pip install swarscribe");
        return;
      }
      done(stdout.replace(/\n$/, ""));
    });
}

function activate(context) {
  const cleanSelection = vscode.commands.registerCommand(
    "swarscribe.cleanSelection", () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.selection.isEmpty) {
        vscode.window.showInformationMessage(
          "Select some raw dictation first.");
        return;
      }
      const selected = editor.document.getText(editor.selection);
      const codeMode = ["python", "javascript", "typescript"]
        .includes(editor.document.languageId);
      runClean(selected, codeMode ? ["--code"] : [], (cleaned) => {
        editor.edit((edit) => edit.replace(editor.selection, cleaned));
      });
    });

  const cleanClipboard = vscode.commands.registerCommand(
    "swarscribe.cleanClipboard", async () => {
      const raw = await vscode.env.clipboard.readText();
      if (!raw) return;
      runClean(raw, [], async (cleaned) => {
        await vscode.env.clipboard.writeText(cleaned);
        vscode.window.showInformationMessage("Clipboard cleaned by SwarScribe.");
      });
    });

  context.subscriptions.push(cleanSelection, cleanClipboard);
}

function deactivate() {}
module.exports = { activate, deactivate };
