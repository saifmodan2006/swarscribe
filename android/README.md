# SwarScribe for Android

Use a debug APK from the [Android CI workflow](https://github.com/saifmodan2006/swarscribe/actions/workflows/android.yml), or build with JDK 17, Android SDK 34 and Gradle 8.9:

```powershell
gradle -p android testDebugUnitTest lintDebug assembleDebug assembleRelease assembleDebugAndroidTest
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
adb devices -l
gradle -p android connectedDebugAndroidTest
```

The release APK is unsigned. The instrumentation APK exercises a real Android `InputConnection` implementation and sensitive field detection. Run it on a connected emulator or device; it does not require speech recognition. Device verification of microphone permissions, focus changes, and recognition still requires an Android device with a compatible service.

1. Open SwarScribe and grant microphone permission when prompted. Try **Dictate on device**.
2. Tap **Enable the SwarScribe keyboard**. Enable it in Android input settings and select it from the keyboard picker in a text field.
3. Select English or Hindi and tap **Dictate**. Tap again to stop or wait for end of speech. Tap **Switch keyboard** to return to your regular keyboard. SwarScribe skips known password fields and refuses to replace detected selections.
4. On-device speech requires Android 12+ and an on-device recognizer with the selected language installed. Some devices do not ship one. The app does not fall back to the default online recognizer. Android 8–11 can use paired desktop dictation in the companion.
5. The optional floating shortcut opens the companion. It does not type into the underlying app. Long press it to dismiss.

## Pair the companion with a desktop

Start with a trusted TLS certificate and private key for a desktop hostname that resolves to the desktop on your network. The Android device must trust the certificate chain and the URL must match the certificate subject alternative name. For a home network, a domain you control with private DNS and a publicly trusted certificate can work without exposing the service to the internet. The app does not bypass TLS validation or accept HTTP.

On the desktop, first install the API and a speech model. Use the actual LAN address and certificate files in these PowerShell commands:

```powershell
swarscribe model-download --engine whisper --model base
$env:SWARSCRIBE_PAIR_TOKEN = swarscribe pair-token
swarscribe pair-serve --bind 192.168.1.15 --hostname desktop.example.net --port 8443 --cert .\fullchain.pem --key .\privkey.pem
```

Copy the token privately to the companion and enter `https://desktop.example.net:8443`. Tap **Check HTTPS pairing**. Use **Dictate via paired desktop**, then **Stop and send to desktop**. Only this mode sends audio off the phone. The app retains the address locally; the token is entered per activity session. Stop the server and generate a new token to revoke the old one. Allow the port only on a trusted local network. Desktop pairing runs independently of the loopback dashboard.

If diagnostics fail, verify name resolution, same network access, firewall rules, time, certificate trust/name/expiry, and the token. A successful health check verifies pairing; it does not load the model. If inference fails, verify the speech model with the desktop CLI.
