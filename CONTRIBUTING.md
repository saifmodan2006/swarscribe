# Contributing to SwarScribe

You can help by sharing a reproducible formatting example, checking a device workflow, fixing a guide, or opening a pull request. Start in the [browser studio](https://saifmodan2006.github.io/swarscribe/web/#try) to try the text pipeline without installing a model.

## Report what you found

1. Search [open issues](https://github.com/saifmodan2006/swarscribe/issues) for similar reports.
2. Choose a [bug, accessibility, or idea form](https://github.com/saifmodan2006/swarscribe/issues/new/choose).
3. Include the platform, version or commit, steps, and what you expected to happen. For studio cleanup, expand **Report a formatting problem** and select **Copy test case**. Review the text before pasting it into the issue.

Use invented names and replace personal text, audio, tokens, and private paths before posting. Report security problems privately using the [security policy](SECURITY.md).

## Build your first change

Fork [SwarScribe](https://github.com/saifmodan2006/swarscribe/fork), clone your fork, and make a branch. Replace `YOUR-USERNAME` with your GitHub username.

```powershell
git clone https://github.com/YOUR-USERNAME/swarscribe.git
cd swarscribe
git switch -c my-first-change
py -3.12 -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -e ".[api,dev]"
& $py -m pytest -q
& $py examples/demo.py
```

On macOS or Linux, use `python3 -m venv .venv` and `.venv/bin/python` for the Python commands. The suite includes API tests. The `api,dev` extras install their dependencies without pulling speech models or desktop audio libraries.

### Pick a small task

- **Formatting:** Reproduce a case with `swarscribe clean` or in the browser studio. Add the case to the corresponding test suite and compare results if the change should apply on both surfaces.
- **Accessibility:** Try the studio and workspace with keyboard only, browser zoom at 200%, or a screen reader. Report the control, the action, and the actual result.
- **Device testing:** Try the current Windows setup or Android debug build and share the exact editor or device version. Check the [roadmap](docs/ROADMAP.md) for workflows that need verification.
- **Documentation:** Follow a setup guide in a fresh environment and update a missing step or confusing error message.

### Find the code and run the relevant checks

| Area | Start here | Check your change |
| --- | --- | --- |
| Cleanup, formats, commands, code mode | `src/swarscribe/` and `tests/` | `python -m pytest -q` |
| Public studio | `web/` | `node --test web/format.test.cjs` and open `/web/` after starting `python -m http.server 8080` at the repo root |
| Windows tray and local workspace | `src/swarscribe/desktop.py`, `tray.py`, `api.py`, and `dashboard/` | See the [Windows guide](docs/WINDOWS.md). Run `swarscribe dashboard` to check the workspace without a speech model. |
| Android companion and keyboard | `android/app/` | `gradle -p android testDebugUnitTest lintDebug assembleDebug` with JDK 17, Gradle 8.9, and Android SDK 34 |
| Speech engines | `src/swarscribe/transcribe.py` and `benchmarks/verify_speech.py` | See the [speech CI job](.github/workflows/ci.yml) for the model, fixture, and offline verification command. |

Use the virtual environment’s Python for the commands in the table. See the [Android guide](android/README.md) for installation and instrumentation tests and [Architecture](docs/ARCHITECTURE.md) for an overview of the data paths.

## Open a pull request

Keep the change focused. Describe the user-visible behavior, link any issue, and list the checks you ran. Screenshots are helpful for visual changes when they contain only sample data. Add a focused regression test for behavior that existing tests miss.

Keep optional runtimes in dependency extras. Audio and transcripts should stay local by default. Use the [roadmap](docs/ROADMAP.md) to discuss larger ideas before investing in an implementation.
