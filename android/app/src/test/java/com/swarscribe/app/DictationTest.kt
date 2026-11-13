package com.swarscribe.app

import org.junit.Assert.*
import org.junit.Test
import java.nio.ByteBuffer
import java.nio.ByteOrder

class DictationTest {
    @Test fun strictPairingAddress() {
        assertEquals("desktop.example.net", ServerClient.address("https://desktop.example.net:8443").host)
        for (url in listOf("http://192.168.1.5", "https://user@desktop.test",
            "https://desktop.test/private", "https://desktop.test#fragment",
            "https://desktop.test?query=1", "https://desktop.test:99999")) {
            assertThrows(url, IllegalArgumentException::class.java) { ServerClient.address(url) }
        }
    }

    @Test fun wavHeaderMatchesPcm() {
        val pcm = byteArrayOf(1, 2, 3, 4)
        val wav = ServerClient.wavBytes(pcm)
        val bytes = ByteBuffer.wrap(wav).order(ByteOrder.LITTLE_ENDIAN)
        assertEquals(40, bytes.getInt(4))
        assertEquals(16000, bytes.getInt(24))
        assertEquals(4, bytes.getInt(40))
        assertArrayEquals(pcm, wav.copyOfRange(44, 48))
    }

    @Test fun cleanupPreservesMeaningAndBrandSpelling() {
        assertEquals("I like Supabase.", Cleanup.clean("um I like Supabase"))
        assertEquals("Meeting on Tuesday.", Cleanup.clean("meeting on monday no wait tuesday"))
    }
}
