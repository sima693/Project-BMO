"""
bmo/face.py
===========
Pygame face renderer for Project BMO.

Uses static PNG face images mimicking Figma assets.
"""

import math
import os
import pygame

# ---------------------------------------------------------------------------
# Window / layout constants
# ---------------------------------------------------------------------------

WIN_W: int = 480
WIN_H: int = 680

# BMO body rect
BODY_X: int = 60
BODY_Y: int = 15
BODY_W: int = 360
BODY_H: int = 490
BODY_R: int = 28   # corner radius

# Screen
SCREEN_X: int = BODY_X + 58
SCREEN_Y: int = BODY_Y + 72
SCREEN_W: int = 244
SCREEN_H: int = 210
SCREEN_R: int = 14

# Controls layout
DPAD_CX: int = BODY_X + 103
DPAD_CY: int = BODY_Y + 386
DPAD_ARM_LONG: int = 58
DPAD_ARM_SHORT: int = 22

BTN_CLUSTER_CX: int = BODY_X + 263
BTN_CLUSTER_CY: int = BODY_Y + 386
BTN_R: int = 14
BTN_GAP: int = 26

# Chat area
CHAT_Y: int = 515
CHAT_H: int = 108
INPUT_Y: int = 630
INPUT_H: int = 42

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
C_BMO_TEAL       = (72,  178, 140)
C_BMO_DARK       = (46,  118,  90)
C_BMO_LIGHT      = (118, 213, 178)
C_BMO_SHOULDER   = (60,  155, 120)

C_SCREEN_BG      = (184, 228, 201)  # Light teal from Figma
C_SCREEN_BORDER  = (130, 190, 150)

C_DPAD           = (255, 210,  45)
C_DPAD_DARK      = (180, 148,  20)
C_BTN_A          = (255,  85,  85)
C_BTN_B          = (85,  215, 130)
C_BTN_X          = (85,  145, 255)
C_BTN_Y          = (255, 210,  45)
C_BTN_BORDER     = (200, 210, 205)
C_START_SEL      = (150, 170, 162)

C_SPEAKER        = (48,  130,  96)
C_LED_ON         = (80,  255, 120)
C_PORT           = (38,   95,  72)

C_BG             = (10,   15,  26)
C_CHAT_BG        = (17,   24,  38)
C_INPUT_BG       = (24,   32,  48)
C_CHAT_BORDER    = (40,   65,  52)
C_TEXT_USER      = (165, 225, 205)
C_TEXT_BMO       = (232, 248, 242)
C_TEXT_DIM       = (90,  130, 112)
C_TEXT_INPUT     = (220, 240, 232)
C_TEXT_PLACEHOLDER = (65,  95,  82)
C_CURSOR         = (80,  200, 160)
C_THINKING_DOT   = (80,  200, 160)
C_ZZZ            = (140, 200, 175)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _draw_rounded_rect(surface, color, rect, radius, width=0):
    if width == 0:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    else:
        pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def _draw_text_wrapped(surface, text, font, color, x, y, max_width, line_spacing=4):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)

    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + line_spacing
    return y

class ZzzParticle:
    def __init__(self, x: int, y: int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.age = 0.0
        self.lifetime = 2.0

    def update(self, dt: float) -> bool:
        self.age += dt
        self.y -= 20 * dt
        self.x += 8 * dt * math.sin(self.age * 2)
        return self.age < self.lifetime

    def draw(self, surface, font):
        alpha = max(0, int(255 * (1 - self.age / self.lifetime)))
        if alpha <= 0: return
        glyph = font.render("z", True, C_ZZZ)
        glyph.set_alpha(alpha)
        surface.blit(glyph, (int(self.x), int(self.y)))

# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------
class FaceRenderer:
    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        pygame.font.init()
        self._font_chat  = pygame.font.SysFont("Consolas, Courier New, monospace", 14)
        self._font_input = pygame.font.SysFont("Consolas, Courier New, monospace", 15)
        self._font_label = pygame.font.SysFont("Arial, Helvetica, sans-serif",     11)
        self._font_zzz   = pygame.font.SysFont("Arial", 18, bold=True)
        
        self.faces = {}
        self._load_faces()
        self._scanlines = self._build_scanlines()

    def _load_faces(self):
        faces_dir = os.path.join("assets", "faces")
        if os.path.exists(faces_dir):
            for file in os.listdir(faces_dir):
                if file.endswith(".png"):
                    name = file[:-4]
                    try:
                        self.faces[name] = pygame.image.load(os.path.join(faces_dir, file)).convert_alpha()
                    except:
                        pass
        if "neutral" not in self.faces:
            # Fallback blank surface
            surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            self.faces["neutral"] = surf

    def draw(self, target_expr="neutral", bounce_y=0.0, zzz_particles=None, 
             cursor_visible=True, input_text="", chat_log=None, 
             streaming_text="", app_state="idle"):
        
        self.surface.fill(C_BG)
        by = int(bounce_y)

        self._draw_body(by)
        self._draw_screen(by, target_expr)
        
        if zzz_particles:
            for p in zzz_particles:
                p.draw(self.surface, self._font_zzz)
                
        self._draw_controls(by)
        self._draw_body_details(by)
        self._draw_chat_area(chat_log or [], streaming_text, app_state)
        self._draw_input_box(input_text, cursor_visible, app_state)

    def _draw_body(self, by: int) -> None:
        body_rect = pygame.Rect(BODY_X, BODY_Y + by, BODY_W, BODY_H)
        pygame.draw.rect(self.surface, (5, 10, 20), body_rect.move(4, 6), border_radius=BODY_R)
        pygame.draw.rect(self.surface, C_BMO_DARK, body_rect, border_radius=BODY_R)
        pygame.draw.rect(self.surface, C_BMO_TEAL, body_rect.inflate(-4, -4), border_radius=BODY_R - 2)
        
        hl_surf = pygame.Surface((12, BODY_H - 20), pygame.SRCALPHA)
        for i in range(BODY_H - 20):
            alpha = max(0, 60 - int(60 * i / (BODY_H - 20)))
            pygame.draw.line(hl_surf, (*C_BMO_LIGHT, alpha), (0, i), (11, i))
        self.surface.blit(hl_surf, (BODY_X + 8, BODY_Y + by + 8))

    def _draw_screen(self, by: int, expr: str) -> None:
        bezel_rect = pygame.Rect(SCREEN_X - 6, SCREEN_Y + by - 5, SCREEN_W + 12, SCREEN_H + 10)
        pygame.draw.rect(self.surface, C_BMO_DARK, bezel_rect, border_radius=SCREEN_R + 4)
        
        screen_rect = pygame.Rect(SCREEN_X, SCREEN_Y + by, SCREEN_W, SCREEN_H)
        pygame.draw.rect(self.surface, C_SCREEN_BG, screen_rect, border_radius=SCREEN_R)

        face_img = self.faces.get(expr, self.faces.get("neutral"))
        if face_img:
            self.surface.blit(face_img, (SCREEN_X, SCREEN_Y + by))

        self.surface.blit(self._scanlines, (SCREEN_X, SCREEN_Y + by))
        pygame.draw.rect(self.surface, C_SCREEN_BORDER, screen_rect, width=2, border_radius=SCREEN_R)

    def _draw_controls(self, by: int) -> None:
        cy = by
        dpad_cx, dpad_cy = DPAD_CX, DPAD_CY + cy
        arm_l, arm_s = DPAD_ARM_LONG, DPAD_ARM_SHORT

        for dx, dy in ((2, 2),):
            pygame.draw.rect(self.surface, C_DPAD_DARK, pygame.Rect(dpad_cx - arm_l//2 + dx, dpad_cy - arm_s//2 + dy, arm_l, arm_s), border_radius=4)
            pygame.draw.rect(self.surface, C_DPAD_DARK, pygame.Rect(dpad_cx - arm_s//2 + dx, dpad_cy - arm_l//2 + dy, arm_s, arm_l), border_radius=4)

        pygame.draw.rect(self.surface, C_DPAD, pygame.Rect(dpad_cx - arm_l//2, dpad_cy - arm_s//2, arm_l, arm_s), border_radius=4)
        pygame.draw.rect(self.surface, C_DPAD, pygame.Rect(dpad_cx - arm_s//2, dpad_cy - arm_l//2, arm_s, arm_l), border_radius=4)
        pygame.draw.circle(self.surface, C_DPAD, (dpad_cx, dpad_cy), arm_s // 2 - 1)

        bcx, bcy, g, r = BTN_CLUSTER_CX, BTN_CLUSTER_CY + cy, BTN_GAP, BTN_R
        for bx, by_, color, label in [(bcx, bcy-g, C_BTN_Y, "Y"), (bcx+g, bcy, C_BTN_A, "A"), (bcx, bcy+g, C_BTN_B, "B"), (bcx-g, bcy, C_BTN_X, "X")]:
            pygame.draw.circle(self.surface, tuple(max(0, c-60) for c in color), (bx+2, by_+2), r)
            pygame.draw.circle(self.surface, color, (bx, by_), r)
            pygame.draw.circle(self.surface, C_BTN_BORDER, (bx, by_), r, 1)

        for i, label in enumerate(("SELECT", "START")):
            bx, by_ = BODY_X + 138 + i * 72, BODY_Y + 326 + cy
            btn_rect = pygame.Rect(bx, by_, 52, 14)
            pygame.draw.rect(self.surface, C_BMO_DARK, btn_rect.move(1, 1), border_radius=7)
            pygame.draw.rect(self.surface, C_START_SEL, btn_rect, border_radius=7)
            lbl = self._font_label.render(label, True, (40, 60, 52))
            self.surface.blit(lbl, (bx + btn_rect.w // 2 - lbl.get_width() // 2, by_ + 1))

    def _draw_body_details(self, by: int) -> None:
        for side_x in (BODY_X - 14, BODY_X + BODY_W - 4):
            pygame.draw.rect(self.surface, C_BMO_SHOULDER, pygame.Rect(side_x, BODY_Y + by + 60, 18, 28), border_radius=6)
            pygame.draw.rect(self.surface, C_BMO_DARK, pygame.Rect(side_x, BODY_Y + by + 60, 18, 28), width=1, border_radius=6)

        grill_x, grill_y = (SCREEN_X + SCREEN_W//2) - (7 * 9) // 2, BODY_Y + by + 305
        for row in range(3):
            for col in range(8):
                pygame.draw.circle(self.surface, C_SPEAKER, (grill_x + col * 9, grill_y + row * 9), 2)

        led_x, led_y = BODY_X + BODY_W - 30, BODY_Y + by + 28
        glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C_LED_ON, 60), (10, 10), 10)
        self.surface.blit(glow, (led_x - 10, led_y - 10))
        pygame.draw.circle(self.surface, C_LED_ON, (led_x, led_y), 5)

        pygame.draw.rect(self.surface, C_PORT, pygame.Rect((SCREEN_X+SCREEN_W//2) - 55, BODY_Y + by + BODY_H - 18, 110, 12), border_radius=4)
        
        for sx, sy in [(BODY_X + 18, BODY_Y + by + 20), (BODY_X + BODY_W - 18, BODY_Y + by + 20),
                       (BODY_X + 18, BODY_Y + by + BODY_H - 20), (BODY_X + BODY_W - 18, BODY_Y + by + BODY_H - 20)]:
            pygame.draw.circle(self.surface, C_BMO_DARK, (sx, sy), 5)
            pygame.draw.circle(self.surface, C_BMO_SHOULDER, (sx, sy), 3)

    def _draw_chat_area(self, chat_log, streaming_text, app_state):
        area_rect = pygame.Rect(10, CHAT_Y, WIN_W - 20, CHAT_H)
        _draw_rounded_rect(self.surface, C_CHAT_BG, area_rect, 10)
        _draw_rounded_rect(self.surface, C_CHAT_BORDER, area_rect, 10, width=1)

        entries = list(chat_log[-4:])
        if streaming_text: entries.append(("bmo", streaming_text + "▌"))

        y = CHAT_Y + 10
        available_w = WIN_W - 56

        for role, text in entries:
            lbl_txt, log_col = ("YOU", C_TEXT_USER) if role == "user" else ("BMO", C_TEXT_BMO)
            label = self._font_label.render(lbl_txt, True, C_TEXT_DIM)
            lx = WIN_W - 28 - label.get_width() if role == "user" else 28
            self.surface.blit(label, (lx, y))
            y += label.get_height() + 1
            y = _draw_text_wrapped(self.surface, text, self._font_chat, log_col, 28, y, available_w)
            y += 4

        if app_state == "thinking" and not streaming_text:
            import time
            dots = "•" * (int(time.time() * 2) % 4) or " "
            thinking_surf = self._font_chat.render(f"BMO is thinking {dots}", True, C_THINKING_DOT)
            self.surface.blit(thinking_surf, (28, min(y, CHAT_Y + CHAT_H - thinking_surf.get_height() - 8)))

    def _draw_input_box(self, input_text, cursor_visible, app_state):
        box_rect = pygame.Rect(10, INPUT_Y, WIN_W - 20, INPUT_H)
        _draw_rounded_rect(self.surface, C_INPUT_BG, box_rect, 8)
        
        display, color = (input_text, C_TEXT_INPUT) if input_text else ("Talk to BMO…  (Enter to send)", C_TEXT_PLACEHOLDER)
        txt_surf = self._font_input.render(display, True, color)
        inner_w = WIN_W - 44
        if txt_surf.get_width() > inner_w:
            txt_surf = txt_surf.subsurface(pygame.Rect(txt_surf.get_width() - inner_w, 0, inner_w, txt_surf.get_height()))
            
        ty = INPUT_Y + (INPUT_H - txt_surf.get_height()) // 2
        self.surface.blit(txt_surf, (22, ty))

        if cursor_visible and input_text:
            cx = min(22 + self._font_input.size(input_text)[0], 22 + inner_w)
            pygame.draw.line(self.surface, C_CURSOR, (cx, ty + 2), (cx, ty + txt_surf.get_height() - 2), 2)
            
        if app_state != "idle":
            text = {"thinking": "⟳ thinking", "talking": "⟳ responding"}.get(app_state, "")
            if text:
                mode_surf = self._font_label.render(text, True, C_THINKING_DOT)
                self.surface.blit(mode_surf, (WIN_W - 10 - mode_surf.get_width(), INPUT_Y - 16))

    def _build_scanlines(self):
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(surf, (0, 0, 0, 18), (0, y), (SCREEN_W, y), 1)
        return surf
