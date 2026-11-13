package com.swarscribe.app

import android.util.Base64
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * Server mode: the phone records, the user's own desktop transcribes.
 *
 * Sends WAV audio to POST /transcribe on the SwarScribe API running
 * on the user's computer (same Wi-Fi). That is how the phone gets
 * full Whisper and Parakeet quality with zero cloud: the request
 * never leaves the home network.
 */
object ServerClient {

    fun transcribe(
        serverUrl: String,
        wavBytes: ByteArray,
        language: String? = null,
        onDone: (String) -> Unit,
        onError: (String) -> Unit
    ) {
        thread {
            try {
                val body = JSONObject().apply {
                    put(
                        "wav_base64",
                        Base64.encodeToString(wavBytes, Base64.NO_WRAP)
                    )
                    if (language != null) put("language", language)
                }
                val conn = URL(serverUrl.trimEnd('/') + "/transcribe")
                    .openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                conn.outputStream.use { it.write(body.toString().toByteArray()) }
                val stream =
                    if (conn.responseCode in 200..299) conn.inputStream
                    else conn.errorStream
                val text = stream.bufferedReader().readText()
                val clean = JSONObject(text).optString("text")
                if (clean.isNotBlank()) onDone(clean)
                else onError("Server replied without text")
            } catch (e: Exception) {
                onError("Server unreachable: ${e.message}")
            }
        }
    }

    /** Minimal WAV writer for 16 kHz mono 16-bit PCM from AudioRecord. */
    fun wavBytes(pcm: ByteArrayOutputStream, sampleRate: Int = 16000): ByteArray {
        val data = pcm.toByteArray()
        val out = ByteArrayOutputStream()
        fun writeIntLE(v: Int) {
            out.write(v and 0xFF); out.write(v shr 8 and 0xFF)
            out.write(v shr 16 and 0xFF); out.write(v shr 24 and 0xFF)
        }
        fun writeShortLE(v: Int) {
            out.write(v and 0xFF); out.write(v shr 8 and 0xFF)
        }
        out.write("RIFF".toByteArray()); writeIntLE(36 + data.size)
        out.write("WAVE".toByteArray())
        out.write("fmt ".toByteArray()); writeIntLE(16)
        writeShortLE(1); writeShortLE(1)
        writeIntLE(sampleRate); writeIntLE(sampleRate * 2)
        writeShortLE(2); writeShortLE(16)
        out.write("data".toByteArray()); writeIntLE(data.size)
        out.write(data)
        return out.toByteArray()
    }
}
