package com.swarscribe.app

import android.inputmethodservice.InputMethodService
import android.view.LayoutInflater
import android.view.View
import android.widget.TextView

/**
 * The SwarScribe keyboard: one big mic button, nothing else to learn.
 *
 * Enable it under Settings > System > Languages and input, switch to
 * it from any app's keyboard picker, tap the mic, speak, and cleaned
 * text is committed at the cursor, the Wispr Flow mobile pattern,
 * rebuilt on open pieces.
 */
class SwarKeyboardService : InputMethodService() {

    private var engine: SpeechEngine? = null
    private var statusView: TextView? = null

    override fun onCreateInputView(): View {
        val view = LayoutInflater.from(this)
            .inflate(R.layout.keyboard_view, null)
        statusView = view.findViewById(R.id.kbStatus)
        engine = SpeechEngine(
            this,
            onResult = { cleaned ->
                currentInputConnection?.commitText(cleaned + " ", 1)
                statusView?.text = getString(R.string.kb_ready)
            },
            onError = { message ->
                statusView?.text = message
            }
        )
        view.findViewById<View>(R.id.kbMic).setOnClickListener {
            statusView?.text = getString(R.string.kb_listening)
            engine?.start()
        }
        return view
    }

    override fun onDestroy() {
        engine?.destroy()
        engine = null
        super.onDestroy()
    }
}
