package com.swarscribe.app

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * On-device speech using Android's built-in recognizer.
 *
 * EXTRA_PREFER_OFFLINE asks the system for its on-device model where
 * one is installed (Pixel and recent Samsung devices ship one), so
 * dictation can stay private and offline like the desktop engine.
 * For full Whisper and Parakeet quality, ServerClient sends the same
 * recording to the user's own SwarScribe desktop on their network.
 */
class SpeechEngine(
    context: Context,
    private val onResult: (String) -> Unit,
    private val onError: (String) -> Unit
) {
    private val recognizer: SpeechRecognizer? =
        if (SpeechRecognizer.isRecognitionAvailable(context)) {
            SpeechRecognizer.createSpeechRecognizer(context)
        } else null

    private val listener = object : RecognitionListener {
        override fun onResults(results: Bundle?) {
            val matches =
                results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            val heard = matches?.firstOrNull().orEmpty()
            if (heard.isNotBlank()) onResult(Cleanup.clean(heard))
            else onError("Nothing heard")
        }

        override fun onError(error: Int) {
            onError("Speech error $error")
        }

        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onPartialResults(partialResults: Bundle?) {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    }

    fun start(language: String = "en-IN") {
        val rec = recognizer ?: run {
            onError("No speech recognizer on this device; use Server mode")
            return
        }
        rec.setRecognitionListener(listener)
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        }
        rec.startListening(intent)
    }

    fun stop() {
        recognizer?.stopListening()
    }

    fun destroy() {
        recognizer?.destroy()
    }
}
