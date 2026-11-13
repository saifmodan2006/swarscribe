package com.swarscribe.app

import android.Manifest
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import java.io.ByteArrayOutputStream
import kotlin.concurrent.thread

/**
 * The companion app: dictate here to try it, set your desktop's
 * server address for full-quality mode, and jump to the settings
 * screen that enables the SwarScribe keyboard.
 */
class MainActivity : AppCompatActivity() {

    private var engine: SpeechEngine? = null
    private var recording = false
    private var audioThread: Thread? = null
    private val pcm = ByteArrayOutputStream()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val output = findViewById<TextView>(R.id.outputText)
        val status = findViewById<TextView>(R.id.statusText)
        val serverUrl = findViewById<EditText>(R.id.serverUrl)

        ActivityCompat.requestPermissions(
            this, arrayOf(Manifest.permission.RECORD_AUDIO), 1
        )

        engine = SpeechEngine(
            this,
            onResult = { cleaned ->
                runOnUiThread {
                    output.text = cleaned
                    status.setText(R.string.kb_ready)
                }
            },
            onError = { message ->
                runOnUiThread { status.text = message }
            }
        )

        findViewById<Button>(R.id.dictateButton).setOnClickListener {
            status.setText(R.string.kb_listening)
            engine?.start()
        }

        findViewById<Button>(R.id.serverButton).setOnClickListener {
            if (!recording) startServerRecording(status)
            else stopServerRecording(serverUrl.text.toString(), output, status)
        }

        findViewById<Button>(R.id.keyboardSettingsButton).setOnClickListener {
            startActivity(
                android.content.Intent(
                    android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS
                )
            )
        }

        findViewById<Button>(R.id.bubbleButton).setOnClickListener {
            toggleBubble()
        }

        if (intent.getBooleanExtra(EXTRA_FROM_BUBBLE, false)) {
            status.setText(R.string.kb_listening)
            engine?.start()
        }
    }

    private fun toggleBubble() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M
            && !android.provider.Settings.canDrawOverlays(this)
        ) {
            startActivity(
                android.content.Intent(
                    android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    android.net.Uri.parse("package:$packageName")
                )
            )
            return
        }
        startService(android.content.Intent(this, BubbleService::class.java))
    }

    companion object {
        const val EXTRA_FROM_BUBBLE = "from_bubble"
    }

    private fun startServerRecording(status: TextView) {
        recording = true
        pcm.reset()
        status.setText(R.string.server_recording)
        audioThread = thread {
            val bufferSize = AudioRecord.getMinBufferSize(
                16000, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )
            val record = AudioRecord(
                MediaRecorder.AudioSource.MIC, 16000,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT, bufferSize
            )
            val buffer = ByteArray(bufferSize)
            record.startRecording()
            while (recording) {
                val read = record.read(buffer, 0, buffer.size)
                if (read > 0) pcm.write(buffer, 0, read)
            }
            record.stop()
            record.release()
        }
    }

    private fun stopServerRecording(
        url: String, output: TextView, status: TextView
    ) {
        recording = false
        audioThread?.join(500)
        status.setText(R.string.server_sending)
        ServerClient.transcribe(
            url, ServerClient.wavBytes(pcm),
            onDone = { clean ->
                runOnUiThread {
                    output.text = clean
                    status.setText(R.string.kb_ready)
                }
            },
            onError = { message ->
                runOnUiThread { status.text = message }
            }
        )
    }

    override fun onDestroy() {
        engine?.destroy()
        super.onDestroy()
    }
}
