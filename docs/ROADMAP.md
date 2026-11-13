# SwarScribe roadmap

SwarScribe is in alpha. The current focus is verifying how dictation behaves on real devices and making it easier to reproduce problems. See the [changelog](../CHANGELOG.md) for shipped work.

| Area | What needs help | What a useful result looks like |
| --- | --- | --- |
| Windows insertion | Test Notepad, browser text fields, VS Code, and Word | Report the app version, focus and selection behavior, and whether Unicode text arrived at the cursor |
| Android keyboard | Test on-device recognition, language changes, and insertion on Android 12+ | Include the phone and OS version, language, recognizer availability, and the result in an editable field |
| Android pairing | Try the companion with a desktop certificate trusted by the phone | Report the result of Check connection and an end-to-end dictation, with the token removed |
| Multilingual speech | Try English, Hindi, and mixed speech with a licensed or self-recorded fixture | Record the model and device, reference text, and actual output. Note recognition or script errors. |
| Accessibility | Use the studio and workspace with keyboard only, zoom, or a screen reader | Give a short reproduction that identifies the control, expected behavior, and observed barrier |

For a first contribution, choose one workflow, try it, and share the result through the [feedback forms](https://github.com/saifmodan2006/swarscribe/issues/new/choose). The [contributor guide](../CONTRIBUTING.md) includes local setup and test commands.

Later ideas include signed installers, broader benchmark coverage, and better model setup. These depend on platform verification and maintainer capacity. For a larger proposal, [open an idea](https://github.com/saifmodan2006/swarscribe/issues/new?template=idea.yml) with the workflow it would improve.
