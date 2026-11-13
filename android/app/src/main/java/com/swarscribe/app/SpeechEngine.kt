package com.swarscribe.app

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/** Uses Android's on-device service exclusively. All calls run on the main thread. */
class SpeechEngine(
    private val context: Context,
    private val onResult: (String) -> Unit,
    private val onError: (String) -> Unit,
    private val onProcessing: () -> Unit
) {
    enum class State { IDLE, LISTENING, PROCESSING }
    var state = State.IDLE
        private set
    private var recognizer: SpeechRecognizer? = null

    fun start(language: String) {
        if (state != State.IDLE) return
        if (Build.VERSION.SDK_INT < 31 || !SpeechRecognizer.isOnDeviceRecognitionAvailable(context)) {
            onError("On-device speech is unavailable. Use Android 12+ with an offline speech service, or use desktop pairing in SwarScribe.")
            return
        }
        try {
            val session = SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
            recognizer = session
            session.setRecognitionListener(object : RecognitionListener {
                override fun onResults(results: Bundle?) {
                    if (recognizer !== session) return
                    val heard = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        ?.firstOrNull().orEmpty()
                    cancel()
                    if (heard.isBlank()) onError("No speech recognized.")
                    else onResult(Cleanup.clean(heard))
                }
                override fun onError(error: Int) {
                    if (recognizer !== session) return
                    cancel()
                    onError(when (error) {
                        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Allow microphone access in SwarScribe settings."
                        SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED,
                        SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE ->
                            "Install this offline language in your Android speech settings, or choose another language."
                        SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech recognized."
                        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Microphone is busy. Try again."
                        else -> "On-device recognition failed (code $error). Check the installed offline speech service."
                    })
                }
                override fun onEndOfSpeech() {
                    if (recognizer === session) {
                        state = State.PROCESSING
                        onProcessing()
                    }
                }
                override fun onReadyForSpeech(params: Bundle?) {}
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
            state = State.LISTENING
            session.startListening(Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
                putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            })
        } catch (e: RuntimeException) {
            cancel()
            onError("Could not start the on-device recognizer. Check microphone permission and offline language setup.")
        }
    }

    fun stop() {
        if (state != State.LISTENING) return
        state = State.PROCESSING
        onProcessing()
        try {
            recognizer?.stopListening()
        } catch (e: RuntimeException) {
            cancel()
            onError("Could not stop the recognizer. Try again.")
        }
    }

    fun cancel() {
        val session = recognizer
        recognizer = null
        state = State.IDLE
        session?.destroy()
    }
}
