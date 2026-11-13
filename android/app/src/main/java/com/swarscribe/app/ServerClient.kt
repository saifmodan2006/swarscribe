package com.swarscribe.app

import android.util.Base64
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.URI
import java.net.URL
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLException

object ServerClient {
    fun address(serverUrl: String): URL {
        val uri = try { URI(serverUrl.trim()) } catch (e: Exception) {
            throw IllegalArgumentException("Enter a valid HTTPS desktop URL.")
        }
        require(uri.scheme == "https" && uri.host != null && uri.userInfo == null &&
            uri.rawQuery == null && uri.rawFragment == null &&
            (uri.rawPath.isNullOrEmpty() || uri.rawPath == "/") &&
            (uri.port == -1 || uri.port in 1..65535)) {
            "Use an HTTPS desktop address with no path or credentials."
        }
        return uri.toURL()
    }

    fun check(serverUrl: String, token: String) {
        val result = request(serverUrl, token, "/health")
        check(result.optBoolean("paired")) { "This is not a SwarScribe pairing endpoint." }
    }

    fun transcribe(serverUrl: String, token: String, wav: ByteArray, language: String): String {
        val body = JSONObject().apply {
            put("wav_base64", Base64.encodeToString(wav, Base64.NO_WRAP))
            put("language", language)
        }
        val text = request(serverUrl, token, "/transcribe", body).optString("text")
        if (text.isBlank()) throw IOException("Desktop returned no dictation.")
        return text
    }

    private fun request(serverUrl: String, token: String, path: String, body: JSONObject? = null): JSONObject {
        require(Regex("[A-Za-z0-9_-]{32,128}").matches(token)) { "Paste a valid desktop pairing token." }
        val endpoint = address(serverUrl)
        val connection = URL(endpoint, path).openConnection() as HttpsURLConnection
        try {
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 5_000
            connection.readTimeout = 120_000
            connection.setRequestProperty("Authorization", "Bearer $token")
            if (body != null) {
                val bytes = body.toString().toByteArray(Charsets.UTF_8)
                connection.requestMethod = "POST"
                connection.setRequestProperty("Content-Type", "application/json")
                connection.doOutput = true
                connection.setFixedLengthStreamingMode(bytes.size)
                connection.outputStream.use { it.write(bytes) }
            }
            val code = connection.responseCode
            if (code !in 200..299) throw IOException(when (code) {
                401 -> "Pairing token rejected. Check the token on the desktop."
                403, 404 -> "Desktop address is not the configured HTTPS pairing endpoint."
                413 -> "Recording exceeds the desktop upload limit."
                422 -> "Desktop could not recognize this recording."
                429 -> "Desktop is busy. Try again."
                503 -> "Desktop speech model is unavailable. Check desktop setup."
                else -> "Desktop returned HTTP $code."
            })
            val bytes = ByteArrayOutputStream()
            connection.inputStream.use { stream ->
                val buffer = ByteArray(8192)
                while (true) {
                    val length = stream.read(buffer)
                    if (length < 0) break
                    if (bytes.size() + length > 1024 * 1024) throw IOException("Desktop reply is too large.")
                    bytes.write(buffer, 0, length)
                }
            }
            return JSONObject(bytes.toString(Charsets.UTF_8.name()))
        } catch (e: SSLException) {
            throw IOException("TLS verification failed. Check the certificate name, trust and expiry.", e)
        } catch (e: java.net.SocketTimeoutException) {
            throw IOException("Desktop timed out. Check connectivity and model readiness.", e)
        } catch (e: java.net.ConnectException) {
            throw IOException("Could not connect. Check the address, Wi-Fi, firewall and pairing service.", e)
        } finally {
            connection.disconnect()
        }
    }

    fun wavBytes(data: ByteArray, sampleRate: Int = 16000): ByteArray {
        val out = ByteArrayOutputStream()
        fun le(v: Int, n: Int) { for (i in 0 until n) out.write((v shr (i * 8)) and 0xFF) }
        out.write("RIFF".toByteArray()); le(36 + data.size, 4)
        out.write("WAVEfmt ".toByteArray()); le(16, 4)
        le(1, 2); le(1, 2); le(sampleRate, 4); le(sampleRate * 2, 4)
        le(2, 2); le(16, 2)
        out.write("data".toByteArray()); le(data.size, 4); out.write(data)
        return out.toByteArray()
    }
}
