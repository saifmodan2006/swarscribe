package com.swarscribe.app

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.Spinner
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {
    private lateinit var engine: SpeechEngine
    private lateinit var status: TextView
    private lateinit var output: TextView
    private lateinit var local: Button
    private lateinit var desktop: Button
    private lateinit var diagnostics: Button
    private lateinit var copy: Button
    private lateinit var language: Spinner
    private var capture: MicCapture? = null
    private var activeCapture: MicCapture? = null
    private var operation = 0
    private var busy = false
    private var pendingPermission: (() -> Unit)? = null

    private val permission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val next = pendingPermission
        pendingPermission = null
        if (granted) next?.invoke() else status.text = "Microphone denied. Allow access in Android app settings."
    }

    private fun withMic(block: () -> Unit) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED)
            block()
        else {
            pendingPermission = block
            permission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun update(message: String) {
        status.text = message
        local.setText(if (engine.state == SpeechEngine.State.LISTENING) R.string.stop_local_recording else R.string.dictate_on_device)
        desktop.setText(if (capture != null) R.string.stop_and_send else R.string.dictate_via_desktop)
        local.isEnabled = !busy && engine.state != SpeechEngine.State.PROCESSING
        desktop.isEnabled = capture != null || (!busy && engine.state == SpeechEngine.State.IDLE)
        diagnostics.isEnabled = !busy && engine.state == SpeechEngine.State.IDLE
        language.isEnabled = !busy && engine.state == SpeechEngine.State.IDLE
        copy.isEnabled = output.text.isNotBlank()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        output = findViewById(R.id.outputText)
        status = findViewById(R.id.statusText)
        local = findViewById(R.id.dictateButton)
        desktop = findViewById(R.id.serverButton)
        diagnostics = findViewById(R.id.checkConnection)
        copy = findViewById(R.id.copyTranscript)
        language = findViewById(R.id.language)
        val url = findViewById<EditText>(R.id.serverUrl)
        val token = findViewById<EditText>(R.id.pairToken)
        val preferences = getSharedPreferences("dictation", MODE_PRIVATE)
        url.setText(preferences.getString("desktop", ""))
        language.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item,
            listOf(R.string.language_english, R.string.language_hindi, R.string.language_mixed).map(::getString))
            .apply { setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item) }
        language.setSelection(preferences.getInt("language", 0).coerceIn(0, 2))
        engine = SpeechEngine(this, { output.text = it; update("On-device transcript ready.") },
            { update(it) }, { update("Recognizing on this device…") })
        copy.setOnClickListener {
            val text = output.text
            if (text.isNotBlank()) {
                getSystemService(ClipboardManager::class.java).setPrimaryClip(
                    ClipData.newPlainText(getString(R.string.transcript_title), text))
                update(getString(R.string.transcript_copied))
            }
        }
        local.setOnClickListener {
            if (engine.state == SpeechEngine.State.LISTENING) engine.stop()
            else withMic {
                if (language.selectedItemPosition == 2) {
                    update("Choose English or Hindi for Android on-device speech, or use desktop auto detection.")
                } else {
                    preferences.edit().putInt("language", language.selectedItemPosition).apply()
                    engine.start(if (language.selectedItemPosition == 1) "hi-IN" else "en-IN")
                    if (engine.state == SpeechEngine.State.LISTENING) update("Listening on this device…")
                }
            }
        }

        fun paired(recordAudio: Boolean) {
            val host = url.text.toString().trim()
            val key = token.text.toString().trim()
            try {
                ServerClient.address(host)
                require(Regex("[A-Za-z0-9_-]{32,128}").matches(key)) { "Paste the desktop pairing token." }
            } catch (e: IllegalArgumentException) {
                update(e.message ?: "Invalid desktop pairing settings.")
                return
            }
            val languageIndex = language.selectedItemPosition
            val selected = listOf("en", "hi", "hinglish")[languageIndex]
            preferences.edit().putString("desktop", host).putInt("language", languageIndex).apply()
            val session = if (recordAudio) MicCapture() else null
            capture = session
            activeCapture = session
            busy = true
            val id = ++operation
            update(if (recordAudio) "Recording locally. Stop to send to the paired desktop." else "Checking HTTPS pairing…")
            thread(name = "SwarScribe desktop connection") {
                val result = runCatching {
                    if (session == null) {
                        ServerClient.check(host, key)
                        null
                    } else {
                        val wav = session.capture() ?: return@thread
                        if (session.isCancelled) return@thread
                        runOnUiThread {
                            if (id == operation) { capture = null; update("Sending audio to the paired desktop…") }
                        }
                        ServerClient.transcribe(host, key, wav, selected)
                    }
                }
                runOnUiThread {
                    if (id != operation) return@runOnUiThread
                    capture = null
                    activeCapture = null
                    busy = false
                    result.fold(onSuccess = {
                        if (it != null) output.text = it
                        update(if (it != null) "Desktop transcript ready." else "HTTPS and pairing token verified.")
                    }, onFailure = { update(it.message ?: "Desktop operation failed.") })
                }
            }
        }

        diagnostics.setOnClickListener { paired(false) }
        desktop.setOnClickListener {
            val session = capture
            if (session != null) {
                capture = null
                session.stop()
                update("Stopping microphone…")
            } else if (!busy) withMic { paired(true) }
        }
        findViewById<Button>(R.id.keyboardSettingsButton).setOnClickListener {
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        }
        findViewById<Button>(R.id.bubbleButton).setOnClickListener {
            if (!Settings.canDrawOverlays(this)) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            } else {
                startService(Intent(this, BubbleService::class.java))
                update("Floating shortcut enabled. Tap it to open SwarScribe; hold it to dismiss.")
            }
        }
        update(if (intent.getBooleanExtra(EXTRA_FROM_BUBBLE, false)) "Choose a dictation mode to begin."
               else getString(R.string.mobile_ready))
    }

    override fun onStop() {
        super.onStop()
        ++operation
        activeCapture?.cancel()
        capture = null
        activeCapture = null
        busy = false
        engine.cancel()
        update("Ready. Any active recording was cancelled.")
    }

    companion object { const val EXTRA_FROM_BUBBLE = "from_bubble" }
}
