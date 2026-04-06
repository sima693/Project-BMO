"""
bmo/app.py
==========
Project BMO — Phase 1: The Digital Soul

Main application loop. Ties together:
  • Pygame rendering (FaceRenderer)
  • Expression state machine + smooth interpolation
  • Blink / bounce / eye-dart / ZZZ animations
  • AI streaming (Ollama) in a background thread
  • VADER sentiment → expression mapping
  • Chat UI (input box + scrolling log)

Run with:
    python -m bmo.app
"""

import math
import queue
import random
import sys
import threading
import time

import pygame

from bmo.expressions import (
    EXPRESSION_ANIMS,
    EXPRESSIONS,
    lerp_state,
    make_initial_state,
)
from bmo.face import (
    WIN_W,
    WIN_H,
    FaceRenderer,
    ZzzParticle,
    SCREEN_X, SCREEN_Y, SCREEN_W,
)
from bmo.ai_engine import BMOAIEngine
from bmo.sentiment import SentimentAnalyzer

# ---------------------------------------------------------------------------
# Application states
# ---------------------------------------------------------------------------

STATE_IDLE     = "idle"
STATE_THINKING = "thinking"
STATE_TALKING  = "talking"

# ---------------------------------------------------------------------------
# Background AI worker
# ---------------------------------------------------------------------------

def _ai_worker(
    engine: BMOAIEngine,
    user_message: str,
    result_queue: "queue.Queue[tuple]",
) -> None:
    """
    Runs in a daemon thread. Streams tokens from the AI engine and
    puts them into result_queue as ("token", str) tuples.
    Signals completion with ("done", full_response) or ("error", msg).
    """
    full_response = ""
    try:
        for token in engine.generate_streaming(user_message):
            full_response += token
            result_queue.put(("token", token))
        result_queue.put(("done", full_response))
    except Exception as exc:
        result_queue.put(("error", f"Oh no! BMO broke: {exc}"))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run() -> None:
    pygame.init()
    pygame.display.set_caption("Project BMO — Be More")

    # Try to set a custom window icon (teal square with B)
    try:
        icon = pygame.Surface((32, 32))
        icon.fill((72, 178, 140))
        pygame.display.set_icon(icon)
    except Exception:
        pass

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    # Core components
    renderer  = FaceRenderer(screen)
    ai_engine = BMOAIEngine()
    sentiment = SentimentAnalyzer()

    # ---------------------
    # App state
    # ---------------------
    app_state       = STATE_IDLE
    target_expr     = "neutral"
    render_state    = make_initial_state("neutral")

    chat_log: list[tuple[str, str]] = []   # [(role, text), ...]
    input_text  = ""
    stream_text = ""          # partial response being streamed
    result_q: queue.Queue = queue.Queue()

    # ---------------------
    # Animation state
    # ---------------------

    # Blink
    next_blink_time = time.time() + random.uniform(2.5, 5.0)
    blink_phase     = 0.0      # 0 = open, cycles 0→1→0 per blink
    is_blinking     = False

    # Bounce (happy / excited expressions)
    bounce_phase = 0.0

    # Eye dart (thinking expression)
    eye_dart_x = 0.0

    # Pupil wander (idle / neutral)
    wander_phase = 0.0

    # Talking mouth animation
    mouth_anim_phase = 0.0

    # ZZZ particles (sleeping expression)
    zzz_particles: list[ZzzParticle] = []
    next_zzz_time = time.time() + 1.5

    # Cursor blink
    cursor_blink_timer = 0.0
    cursor_visible     = True

    # Post-talking hold timer
    hold_timer = 0.0   # seconds to show response expression before returning to idle

    # ---------------------
    # Main loop
    # ---------------------
    running = True
    while running:
        dt = clock.tick(60) / 1000.0    # delta-time in seconds (capped at 60 FPS)
        now = time.time()

        # ------------------------------------------------------------------
        # Event handling
        # ------------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_RETURN:
                    msg = input_text.strip()
                    if msg and app_state == STATE_IDLE:
                        # Send message
                        chat_log.append(("user", msg))
                        input_text  = ""
                        stream_text = ""
                        app_state   = STATE_THINKING
                        target_expr = "thinking"
                        threading.Thread(
                            target=_ai_worker,
                            args=(ai_engine, msg, result_q),
                            daemon=True,
                        ).start()

                elif event.key == pygame.K_BACKSPACE:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # Ctrl+Backspace: delete last word
                        input_text = input_text.rstrip()
                        parts = input_text.rsplit(" ", 1)
                        input_text = parts[0] + " " if len(parts) > 1 else ""
                    else:
                        input_text = input_text[:-1]

                elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+C: clear conversation history
                    ai_engine.clear_history()
                    chat_log.clear()
                    stream_text = ""

                elif event.unicode and len(input_text) < 200:
                    if app_state == STATE_IDLE:
                        input_text += event.unicode
                        # Switch to listening expression when user types
                        target_expr = "listening"

        # ------------------------------------------------------------------
        # Consume AI result queue
        # ------------------------------------------------------------------
        try:
            while True:
                item = result_q.get_nowait()
                kind = item[0]

                if kind == "token":
                    token = item[1]
                    stream_text += token
                    if app_state == STATE_THINKING:
                        app_state   = STATE_TALKING
                        target_expr = "talking"

                elif kind == "done":
                    full_response = item[1]
                    # Sentiment analysis → expression
                    expr = sentiment.analyze(full_response)
                    chat_log.append(("bmo", full_response))
                    stream_text = ""
                    target_expr = expr
                    app_state   = STATE_TALKING   # hold expression briefly
                    hold_timer  = max(2.5, 0.065 * len(full_response.split()))

                elif kind == "error":
                    err_msg = item[1]
                    chat_log.append(("bmo", err_msg))
                    stream_text = ""
                    target_expr = "sad"
                    app_state   = STATE_TALKING
                    hold_timer  = 3.0

        except queue.Empty:
            pass

        # ------------------------------------------------------------------
        # State transitions
        # ------------------------------------------------------------------
        if app_state == STATE_TALKING and stream_text == "":
            # Counting down hold timer before going idle
            hold_timer -= dt
            if hold_timer <= 0:
                app_state   = STATE_IDLE
                target_expr = "neutral"
                hold_timer  = 0.0

        # Return listening→neutral if user stops typing for a bit
        if app_state == STATE_IDLE and target_expr == "listening" and not input_text:
            target_expr = "neutral"

        # ------------------------------------------------------------------
        # Animation updates
        # ------------------------------------------------------------------

        anim = EXPRESSION_ANIMS.get(target_expr, {})

        # --- Blink ---
        if not is_blinking and now >= next_blink_time:
            is_blinking     = True
            blink_phase     = 0.0
            blink_interval  = anim.get("blink_interval", 4.0)
            next_blink_time = now + random.uniform(blink_interval * 0.7, blink_interval * 1.3)

        if is_blinking:
            blink_phase += dt * 9.0   # speed through blink
            if blink_phase >= 2.0:
                is_blinking = False
                blink_phase = 0.0

        # Triangle wave: 0→1 closing, 1→2 opening
        blink_squeeze = max(0.0, 1.0 - abs(blink_phase - 1.0)) if is_blinking else 0.0

        # --- Bounce (happy / excited) ---
        bounce_y = 0.0
        if anim.get("bounce"):
            bounce_phase += dt * 5.5
            bounce_y = math.sin(bounce_phase) * 5.0

        # --- Eye dart (thinking) ---
        if anim.get("eye_dart"):
            eye_dart_x = math.sin(now * 1.4) * 0.45
        else:
            eye_dart_x = 0.0

        # --- Pupil wander (neutral / listening) ---
        wander_x = 0.0
        wander_y = 0.0
        if anim.get("pupil_wander"):
            wander_phase += dt
            wander_x = math.sin(wander_phase * 0.5) * 0.18
            wander_y = math.cos(wander_phase * 0.37) * 0.12

        # --- Talking mouth oscillation ---
        mouth_anim = 0.0
        if app_state in (STATE_THINKING, STATE_TALKING) and stream_text:
            mouth_anim_phase += dt * 9.0
            mouth_anim = abs(math.sin(mouth_anim_phase)) * 0.9

        # --- ZZZ particles (sleeping) ---
        if target_expr == "sleeping":
            if now >= next_zzz_time:
                spawn_x = SCREEN_X + SCREEN_W - 30 + random.randint(-15, 15)
                spawn_y = SCREEN_Y + 30 + random.randint(-10, 10)
                zzz_particles.append(ZzzParticle(spawn_x, spawn_y))
                next_zzz_time = now + random.uniform(0.8, 1.6)
        zzz_particles = [p for p in zzz_particles if p.update(dt)]

        # --- Cursor blink ---
        cursor_blink_timer += dt
        if cursor_blink_timer >= 0.5:
            cursor_blink_timer = 0.0
            cursor_visible     = not cursor_visible

        # ------------------------------------------------------------------
        # Lerp render state toward target expression
        # ------------------------------------------------------------------
        lerp_state(render_state, target_expr, dt, speed=5.5)

        # Build final render state (apply animation overrides)
        draw_state = dict(render_state)

        # Apply blink (override eye_squeeze_y upward only)
        draw_state["eye_squeeze_y"] = max(
            render_state["eye_squeeze_y"], blink_squeeze
        )

        # Apply eye dart / pupil wander on top of expression's pupil_x
        draw_state["pupil_x"] = render_state["pupil_x"] + eye_dart_x + wander_x
        draw_state["pupil_y"] = render_state["pupil_y"] + wander_y

        # ------------------------------------------------------------------
        # Render
        # ------------------------------------------------------------------
        renderer.draw(
            state          = draw_state,
            bounce_y       = bounce_y,
            mouth_anim     = mouth_anim,
            zzz_particles  = zzz_particles,
            cursor_visible = cursor_visible,
            input_text     = input_text,
            chat_log       = chat_log,
            streaming_text = stream_text,
            app_state      = app_state,
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run()
