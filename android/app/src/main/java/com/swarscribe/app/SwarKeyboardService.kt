package com.swarscribe.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.inputmethodservice.InputMethodService
import android.text.InputType
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.widget.Button
import android.widget.TextView
import androidx.core.content.ContextCompat

internal object KeyboardEditor {
    fun supports(info: EditorInfo?): Boolean {
        val type = info?.inputType ?: return false
        val kind = type and InputType.TYPE_MASK_CLASS
        val variation = type and InputType.TYPE_MASK_VARIATION
        return when (kind) {
            InputType.TYPE_CLASS_TEXT -> variation !in setOf(InputType.TYPE_TEXT_VARIATION_PASSWORD,
                InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD, InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD)
            InputType.TYPE_CLASS_NUMBER -> variation != InputType.TYPE_NUMBER_VARIATION_PASSWORD
            else -> false
        }
    }

    fun insert(connection: InputConnection, text: String): Boolean {
        if (text.isBlank() || connection.getSelectedText(0)?.isNotEmpty() == true) return false
        return connection.commitText("$text ", 1)
    }
}

class SwarKeyboardService : InputMethodService() {
    private var engine: SpeechEngine? = null
    private var target: InputConnection? = null
    private var status: TextView? = null
    private var mic: Button? = null

    private fun ready(message: String) {
        target = null
        status?.text = message
        mic?.text = "Dictate"
        mic?.isEnabled = true
    }

    override fun onCreateInputView(): View {
        engine?.cancel()
        val view = layoutInflater.inflate(R.layout.keyboard_view, null)
        status = view.findViewById(R.id.kbStatus)
        mic = view.findViewById(R.id.kbMic)
        val lang = view.findViewById<Button>(R.id.kbLanguage)
        val prefs = getSharedPreferences("dictation", MODE_PRIVATE)
        var hindi = prefs.getBoolean("keyboard_hindi", false)
        lang.text = if (hindi) "Hindi" else "English"
        lang.setOnClickListener {
            if (engine?.state == SpeechEngine.State.IDLE) {
                hindi = !hindi
                prefs.edit().putBoolean("keyboard_hindi", hindi).apply()
                lang.text = if (hindi) "Hindi" else "English"
            }
        }
        view.findViewById<Button>(R.id.kbSettings).setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }
        view.findViewById<Button>(R.id.kbSwitch).setOnClickListener {
            getSystemService(android.view.inputmethod.InputMethodManager::class.java).showInputMethodPicker()
        }
        engine = SpeechEngine(this, { text ->
            val connection = target
            val inserted = connection != null && connection === currentInputConnection &&
                KeyboardEditor.supports(currentInputEditorInfo) && KeyboardEditor.insert(connection, text)
            ready(if (inserted) "Text inserted." else "Editor changed, refused insertion, or has a selection.")
        }, { ready(it) }, {
            status?.text = "Recognizing on this device…"
            mic?.isEnabled = false
        })
        mic?.setOnClickListener {
            if (engine?.state == SpeechEngine.State.LISTENING) {
                engine?.stop()
            } else if (!KeyboardEditor.supports(currentInputEditorInfo)) {
                ready("Dictation is unavailable in this field.")
            } else if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                ready("Open Settings and allow the microphone in SwarScribe.")
            } else {
                target = currentInputConnection
                engine?.start(if (hindi) "hi-IN" else "en-IN")
                if (engine?.state == SpeechEngine.State.LISTENING) {
                    status?.text = "Listening on this device…"
                    mic?.text = "Stop recording"
                }
            }
        }
        return view
    }

    override fun onFinishInputView(finishingInput: Boolean) {
        engine?.cancel()
        ready("Ready for on-device dictation.")
        super.onFinishInputView(finishingInput)
    }

    override fun onFinishInput() {
        engine?.cancel()
        target = null
        super.onFinishInput()
    }

    override fun onDestroy() {
        engine?.cancel()
        engine = null
        super.onDestroy()
    }
}
