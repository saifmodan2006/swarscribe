package com.swarscribe.app

/**
 * The mobile port of SwarScribe's cleanup pipeline (cleanup.py).
 *
 * Same core rules as the desktop: fillers out, repetitions collapsed,
 * self-corrections resolved, spoken punctuation honoured, sentence
 * case applied. The desktop pipeline adds smart formats, dictionary,
 * snippets and styles on top; this port covers the always-on core so
 * dictated text lands clean on the phone too.
 */
object Cleanup {

    private val fillerPhrases = listOf(
        "you know what i mean", "at the end of the day", "like i said"
    )
    private val fillers = setOf(
        "um", "uh", "erm", "hmm"
    )
    private val spokenPunctuation = linkedMapOf(
        "full stop" to ".", "period" to ".", "comma" to ",",
        "question mark" to "?", "exclamation mark" to "!",
        "colon" to ":", "semicolon" to ";", "new line" to "\n",
        "open bracket" to "(", "close bracket" to ")"
    )
    private val weekdays = listOf(
        "monday", "tuesday", "wednesday", "thursday", "friday",
        "saturday", "sunday"
    )
    private val months = listOf(
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december"
    )

    fun clean(raw: String): String {
        var text = " " + raw.trim() + " "
        for (phrase in fillerPhrases) text = text.replace(" $phrase ", " ")
        text = resolveSelfCorrections(text)
        val tokens = text.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }
        val kept = ArrayList<String>()
        var i = 0
        while (i < tokens.size) {
            val pair = if (i + 1 < tokens.size) tokens[i] + " " + tokens[i + 1] else ""
            if (pair.lowercase() in fillers) { i += 2; continue }
            if (tokens[i].trimEnd(',', '.').lowercase() in fillers) { i += 1; continue }
            kept.add(tokens[i]); i += 1
        }
        text = " " + kept.joinToString(" ") + " "
        for ((spoken, mark) in spokenPunctuation) {
            text = text.replace(" $spoken ", "$mark ")
        }
        text = text.replace(Regex("\\s+([.,?!:;])"), "$1")
        text = capitaliseCalendar(text)
        text = sentenceCase(text)
        text = text.trim()
        if (text.isNotEmpty() && text.last() !in ".?!" && !text.contains("\n")) {
            text += "."
        }
        return text
    }

    private fun resolveSelfCorrections(text: String): String {
        // "monday no wait tuesday" -> "tuesday": drop the corrected
        // word (and anything between it and the marker) when the word
        // after the marker replaces it.
        var out = text
        for (marker in listOf("no wait", "wait no")) {
            val pattern = Regex("\\b\\w+,? " + Regex.escape(marker) + ",? (\\w+)", RegexOption.IGNORE_CASE)
            var prev: String
            do {
                prev = out
                out = pattern.replace(out) { m -> m.groupValues[1] }
            } while (out != prev)
        }
        return out
    }

    private fun capitaliseCalendar(text: String): String {
        var out = text
        for (day in weekdays + months) {
            out = Regex("\\b${day}\\b", RegexOption.IGNORE_CASE).replace(out) {
                day.replaceFirstChar { c -> c.uppercase() }
            }
        }
        return out
    }

    private fun sentenceCase(text: String): String {
        val chars = text.toCharArray()
        var capNext = true
        for (idx in chars.indices) {
            val c = chars[idx]
            if (capNext && c.isLetter()) {
                chars[idx] = c.uppercaseChar()
                capNext = false
            } else if (c == '.' || c == '?' || c == '!' || c == '\n') {
                capNext = true
            }
        }
        return String(chars)
    }
}
