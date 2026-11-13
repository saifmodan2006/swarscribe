# SwarScribe for Android

The mobile half of SwarScribe: a companion app plus a system keyboard,
so you can dictate into any app on the phone, the same daily pattern
as Wispr Flow's mobile app, rebuilt on open pieces.

## What is in here

- **SwarScribe keyboard** (`SwarKeyboardService`): an input method
  with one mic button. Tap, speak, and cleaned text lands at the
  cursor in WhatsApp, Gmail, Notes, anywhere.
- **On-device speech** (`SpeechEngine`): Android's built-in
  recognizer with the offline preference set, so devices with an
  on-device model (Pixel, recent Samsung) dictate privately.
- **The cleanup port** (`Cleanup.kt`): the core of the desktop
  cleanup pipeline in Kotlin: fillers, repetitions, self-corrections,
  spoken punctuation, sentence case.
- **Server mode** (`ServerClient` plus the app screen): the phone
  records WAV and sends it to the SwarScribe API running on your own
  desktop (`swarscribe dashboard`), which runs the full Whisper or
  Parakeet models and the complete cleanup pipeline. The request
  never leaves your own Wi-Fi, so the phone gets desktop quality
  with zero cloud.

## Build

Locally, with Android Studio or Gradle 8.9+ and JDK 17:

```bash
cd android
gradle assembleDebug
```

On GitHub, the Android workflow builds the debug APK on every push
that touches `android/` and attaches it as a build artifact, so the
APK is always one click from the Actions tab. That workflow is also
the project's build verification, since the app targets stock
Android APIs only.

## Use

1. Install the APK, open SwarScribe once, allow the microphone.
2. Tap "Enable the SwarScribe keyboard", turn it on, and pick it
   from the keyboard switcher in any app.
3. Optional: run `swarscribe dashboard` on your computer, put its
   address (for example http://192.168.1.10:8000) in the app, and
   server mode gives you full model quality.

## Honest status

This is a complete, buildable project written against standard
Android APIs, and CI compiles it. It has not yet been run on a
physical phone from this repo, and on-device recognition quality
depends on the handset's own speech model. iOS is planned as a
keyboard extension next; Apple requires dictation to round-trip
through the companion app, which is why Wispr's iPhone app works
the way it does too.
