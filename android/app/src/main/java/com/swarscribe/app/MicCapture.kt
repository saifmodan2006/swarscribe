package com.swarscribe.app

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.concurrent.atomic.AtomicBoolean

internal class MicCapture {
    private val stopped = AtomicBoolean(false)
    private val cancelled = AtomicBoolean(false)
    val isCancelled: Boolean get() = cancelled.get()

    fun stop() { stopped.set(true) }
    fun cancel() { cancelled.set(true); stop() }

    @SuppressLint("MissingPermission") // Activity requests RECORD_AUDIO before starting capture.
    fun capture(): ByteArray? {
        val channel = AudioFormat.CHANNEL_IN_MONO
        val format = AudioFormat.ENCODING_PCM_16BIT
        val rate = 16000
        val limit = rate * 2 * 120
        val minimum = AudioRecord.getMinBufferSize(rate, channel, format)
        if (minimum <= 0) throw IOException("This microphone does not support 16 kHz mono audio.")
        val record = AudioRecord(MediaRecorder.AudioSource.MIC, rate, channel, format, minimum * 2)
        val pcm = ByteArrayOutputStream()
        try {
            if (record.state != AudioRecord.STATE_INITIALIZED) throw IOException("Microphone unavailable.")
            if (cancelled.get()) return null
            record.startRecording()
            if (record.recordingState != AudioRecord.RECORDSTATE_RECORDING) throw IOException("Microphone is busy.")
            val buffer = ByteArray(minimum.coerceAtMost(rate / 5 * 2))
            while (!stopped.get() && pcm.size() < limit) {
                val read = record.read(buffer, 0, minOf(buffer.size, limit - pcm.size()))
                if (read < 0) throw IOException("Microphone interrupted (code $read).")
                if (read > 0) pcm.write(buffer, 0, read)
            }
        } finally {
            try {
                if (record.recordingState == AudioRecord.RECORDSTATE_RECORDING) record.stop()
            } finally { record.release() }
        }
        if (cancelled.get()) return null
        if (pcm.size() == 0) throw IOException("No audio captured.")
        return ServerClient.wavBytes(pcm.toByteArray())
    }
}
