package com.swarscribe.app

import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView

/**
 * Floating mic bubble: one tap from dictation in any app, the Wispr
 * Flow mobile pattern. Tapping opens MainActivity ready to dictate;
 * long-press removes the bubble. Needs the "draw over other apps"
 * permission, requested from MainActivity.
 */
class BubbleService : Service() {

    private var windowManager: WindowManager? = null
    private var bubble: TextView? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (bubble == null && canDraw()) showBubble()
        return START_STICKY
    }

    private fun canDraw(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(this)

    private fun showBubble() {
        val manager = getSystemService(WINDOW_SERVICE) as WindowManager
        windowManager = manager
        val view = TextView(this).apply {
            text = "🎙"
            textSize = 24f
            gravity = Gravity.CENTER
            setPadding(28, 20, 28, 20)
            setBackgroundColor(0xFFFF5A36.toInt())
            setTextColor(0xFFFAF5EC.toInt())
        }
        val type = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.END or Gravity.CENTER_VERTICAL
            x = 16
        }
        var downX = 0f
        var downY = 0f
        var moved = false
        view.setOnTouchListener { v, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX; downY = event.rawY; moved = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - downX).toInt()
                    val dy = (event.rawY - downY).toInt()
                    if (kotlin.math.abs(dx) + kotlin.math.abs(dy) > 12) moved = true
                    params.x -= dx; params.y += dy
                    downX = event.rawX; downY = event.rawY
                    manager.updateViewLayout(v, params)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (!moved) openDictation()
                    true
                }
                else -> false
            }
        }
        view.setOnLongClickListener {
            stopSelf()
            true
        }
        manager.addView(view, params)
        bubble = view
    }

    private fun openDictation() {
        val intent = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            putExtra(MainActivity.EXTRA_FROM_BUBBLE, true)
        }
        startActivity(intent)
    }

    override fun onDestroy() {
        bubble?.let { windowManager?.removeView(it) }
        bubble = null
        super.onDestroy()
    }
}
