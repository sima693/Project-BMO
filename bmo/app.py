"""
bmo/app.py
==========
Project BMO — Phase 1: The Digital Soul

Main application loop. Ties together:
  • Pygame rendering (FaceRenderer)
  • Static Figma face drawing
  • Blink / bounce / ZZZ animations
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

from bmo.expressions import EXPRESSION_ANIMS
from bmo.face import FaceRenderer, WIN_W, WIN_H, ZzzParticle, SCREEN_X, SCREEN_Y, SCREEN_W
from bmo.ai_engine import BMOAIEngine
from bmo.sentiment import SentimentAnalyzer

STATE_IDLE     = "idle"
STATE_THINKING = "thinking"
STATE_TALKING  = "talking"

def _ai_worker(engine, user_message, result_queue):
    full_response = ""
    try:
        for token in engine.generate_streaming(user_message):
            full_response += token
            result_queue.put(("token", token))
        result_queue.put(("done", full_response))
    except Exception as exc:
        result_queue.put(("error", f"Oh no! BMO broke: {exc}"))

def run():
    pygame.init()
    pygame.display.set_caption("Project BMO — Be More")
    try:
        icon = pygame.Surface((32, 32))
        icon.fill((72, 178, 140))
        pygame.display.set_icon(icon)
    except:
        pass

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    renderer  = FaceRenderer(screen)
    ai_engine = BMOAIEngine()
    sentiment = SentimentAnalyzer()

    app_state       = STATE_IDLE
    target_expr     = "neutral"

    chat_log  = []
    input_text  = ""
    stream_text = ""
    result_q = queue.Queue()

    bounce_phase = 0.0
    zzz_particles = []
    next_zzz_time = time.time() + 1.5

    cursor_blink_timer = 0.0
    cursor_visible     = True
    hold_timer = 0.0
    
    # Blinking logic mapping (we don't lerp now, we swap to 'sleeping' temporarily for blink)
    next_blink_time = time.time() + random.uniform(3, 6)
    is_blinking = False
    blink_timer = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        now = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    msg = input_text.strip()
                    if msg and app_state == STATE_IDLE:
                        chat_log.append(("user", msg))
                        input_text = ""
                        stream_text = ""
                        app_state = STATE_THINKING
                        target_expr = "thinking"
                        threading.Thread(target=_ai_worker, args=(ai_engine, msg, result_q), daemon=True).start()
                elif event.key == pygame.K_BACKSPACE:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        input_text = input_text.rstrip()
                        parts = input_text.rsplit(" ", 1)
                        input_text = parts[0] + " " if len(parts) > 1 else ""
                    else:
                        input_text = input_text[:-1]
                elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    ai_engine.clear_history()
                    chat_log.clear()
                    stream_text = ""
                elif event.unicode and len(input_text) < 200:
                    if app_state == STATE_IDLE:
                        input_text += event.unicode
                        target_expr = "listening"

        try:
            while True:
                item = result_q.get_nowait()
                if item[0] == "token":
                    stream_text += item[1]
                    if app_state == STATE_THINKING:
                        app_state = STATE_TALKING
                        target_expr = "talking"
                elif item[0] == "done":
                    full_response = item[1]
                    expr = sentiment.analyze(full_response)
                    chat_log.append(("bmo", full_response))
                    stream_text = ""
                    target_expr = expr
                    app_state = STATE_TALKING
                    hold_timer = max(2.5, 0.065 * len(full_response.split()))
                elif item[0] == "error":
                    chat_log.append(("bmo", item[1]))
                    stream_text = ""
                    target_expr = "sad"
                    app_state = STATE_TALKING
                    hold_timer = 3.0
        except queue.Empty:
            pass

        if app_state == STATE_TALKING and not stream_text:
            hold_timer -= dt
            if hold_timer <= 0:
                app_state = STATE_IDLE
                target_expr = "neutral"
                hold_timer = 0.0

        if app_state == STATE_IDLE and target_expr == "listening" and not input_text:
            target_expr = "neutral"

        anim = EXPRESSION_ANIMS.get(target_expr, {})

        # Handle simplified blink
        if not is_blinking and now >= next_blink_time and target_expr not in ("sleeping", "ko", "cat"):
            is_blinking = True
            blink_timer = 0.15 # seconds to blink
            next_blink_time = now + random.uniform(3, 7)
            
        render_expr = target_expr
        if is_blinking:
            blink_timer -= dt
            render_expr = "sleeping" # Use sleeping face to simulate eyes closed
            if blink_timer <= 0:
                is_blinking = False

        bounce_y = 0.0
        if anim.get("bounce"):
            bounce_phase += dt * 5.5
            bounce_y = math.sin(bounce_phase) * 5.0

        if target_expr == "sleeping":
            if now >= next_zzz_time:
                spawn_x = SCREEN_X + SCREEN_W - 30 + random.randint(-15, 15)
                spawn_y = SCREEN_Y + 30 + random.randint(-10, 10)
                zzz_particles.append(ZzzParticle(spawn_x, spawn_y))
                next_zzz_time = now + random.uniform(0.8, 1.6)
        zzz_particles = [p for p in zzz_particles if p.update(dt)]

        cursor_blink_timer += dt
        if cursor_blink_timer >= 0.5:
            cursor_blink_timer = 0.0
            cursor_visible = not cursor_visible

        # Simple talking animation state oscillation
        if render_expr == "talking" and stream_text:
            # swap between talking and neutral
            if math.sin(now * 15) > 0:
                render_expr = "talking"
            else:
                render_expr = "neutral"

        renderer.draw(
            target_expr    = render_expr,
            bounce_y       = bounce_y,
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

if __name__ == "__main__":
    run()
