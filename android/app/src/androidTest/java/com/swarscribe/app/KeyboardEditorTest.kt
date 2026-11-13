package com.swarscribe.app

import android.text.InputType
import android.view.View
import android.view.inputmethod.BaseInputConnection
import android.view.inputmethod.EditorInfo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class KeyboardEditorTest {
    @Test fun insertsAtCursorAndDoesNotReplaceSelection() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.runOnMainSync {
            val connection = BaseInputConnection(View(instrumentation.targetContext), true)
            connection.commitText("Hello world", 1)
            connection.setSelection(6, 6)
            assertTrue(KeyboardEditor.insert(connection, "new"))
            assertEquals("Hello new world", connection.editable.toString())
            connection.setSelection(0, 5)
            assertFalse(KeyboardEditor.insert(connection, "replace"))
            assertEquals("Hello new world", connection.editable.toString())
        }
    }

    @Test fun detectsSensitiveFields() {
        val editor = EditorInfo()
        editor.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD
        assertFalse(KeyboardEditor.supports(editor))
        editor.inputType = InputType.TYPE_CLASS_TEXT
        assertTrue(KeyboardEditor.supports(editor))
    }
}
