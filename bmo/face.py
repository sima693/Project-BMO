"""
bmo/face.py
===========
Pygame face renderer for Project BMO.

Everything is drawn procedurally (no image files required) so it:
  • Scales perfectly on any screen or Raspberry Pi display
  • Is fully portable
  • Looks great with smooth anti-aliased shapes

Layout (480 × 680 window):
  ┌────────────────────────────┐
  │   BMO Body (360 × 490)     │  y: 15 → 505
  │  ┌──────────────────────┐  │
  │  │  Screen / Face area  │  │  y: 90 → 295
  │  │  Eyes  +  Mouth      │  │
  │  └──────────────────────┘  │
  │  Controls: D-pad / Buttons │
  └────────────────────────────┘
  │  Chat log (scrolling)      │  y: 515 → 620
  │  Input box                 │  y: 628 → 670
  └────────────────────────────┘

Public API:
    renderer = FaceRenderer(surface)
    renderer.draw(render_state, bounce_y=0.0, mouth_anim=0.0, zzz_particles=[])
"""

import math
import pygame

# ---------------------------------------------------------------------------
# Window / layout constants (shared with app.py via import)
# ---------------------------------------------------------------------------

WIN_W: int = 480
WIN_H: int = 680

# BMO body rect
BODY_X: int = 60
BODY_Y: int = 15
BODY_W: int = 360
BODY_H: int = 490
BODY_R: int = 28   # corner radius

# Screen (face display) rect — inside body
SCREEN_X: int = BODY_X + 58
SCREEN_Y: int = BODY_Y + 72
SCREEN_W: int = BODY_W - 116   # 244 px wide
SCREEN_H: int = 210
SCREEN_R: int = 14

# Eye geometry (relative to screen centre)
_SCR_CX: int = SCREEN_X + SCREEN_W // 2   # 240
_SCR_CY: int = SCREEN_Y + SCREEN_H // 2   # 195 (approx)
EYE_BASE_R: int = 28          # base radius before expression scaling
EYE_SEP: int = 60              # horizontal separation from centre to each eye
EYE_BASE_Y_OFFSET: int = -8   # eyes sit slightly above screen centre

# Mouth geometry
MOUTH_CX: int = _SCR_CX
MOUTH_BASE_Y: int = _SCR_CY + 52
MOUTH_BASE_W: int = 72        # base arc width   before expression scaling
MOUTH_BASE_H: int = 34        # base arc height  before expression scaling

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

# Body
C_BMO_TEAL       = (72,  178, 140)
C_BMO_DARK       = (46,  118,  90)
C_BMO_LIGHT      = (118, 213, 178)
C_BMO_SHOULDER   = (60,  155, 120)

# Screen
C_SCREEN_BG      = (10,   15,  28)
C_SCREEN_BORDER  = (35,   85,  62)

# Face features
C_EYE_WHITE      = (232, 248, 242)
C_EYE_PUPIL      = (14,   20,  38)
C_EYE_SHINE      = (255, 255, 255)
C_EYE_IRIS       = (80,  200, 160)    # iris ring tint
C_MOUTH          = (215, 242, 230)
C_CHEEK          = (255, 140, 120)

# Controls
C_DPAD           = (255, 210,  45)
C_DPAD_DARK      = (180, 148,  20)
C_BTN_A          = (255,  85,  85)    # red   (right)
C_BTN_B          = (85,  215, 130)    # green (bottom)
C_BTN_X          = (85,  145, 255)    # blue  (left)
C_BTN_Y          = (255, 210,  45)    # yellow(top)
C_BTN_BORDER     = (200, 210, 205)
C_START_SEL      = (150, 170, 162)

# Speaker / LED / misc
C_SPEAKER        = (48,  130,  96)
C_LED_ON         = (80,  255, 120)
C_PORT           = (38,   95,  72)

# Chat UI
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
# Helper: draw a rounded rect without relying on pygame 2.x only API
# ---------------------------------------------------------------------------

def _draw_rounded_rect(
    surface: pygame.Surface,
    color: tuple,
    rect: pygame.Rect,
    radius: int,
    width: int = 0,
) -> None:
    """Draw a filled or outlined rounded rectangle."""
    if width == 0:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    else:
        pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


def _draw_text_wrapped(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple,
    x: int,
    y: int,
    max_width: int,
    line_spacing: int = 4,
) -> int:
    """
    Draw word-wrapped text. Returns the y coordinate after the last line.
    """
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + line_spacing
    return y


# ---------------------------------------------------------------------------
# ZZZ particle system for sleeping expression
# ---------------------------------------------------------------------------

class ZzzParticle:
    def __init__(self, x: int, y: int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.size = 10
        self.alpha = 255
        self.age = 0.0
        self.lifetime = 2.0  # seconds

    def update(self, dt: float) -> bool:
        """Returns True while still alive."""
        self.age += dt
        progress = self.age / self.lifetime
        self.y -= 20 * dt          # float upward
        self.x += 8 * dt * math.sin(self.age * 2)  # gentle drift
        self.size = 10 + int(8 * progress)
        self.alpha = max(0, int(255 * (1 - progress)))
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.alpha <= 0:
            return
        glyph = font.render("z", True, C_ZZZ)
        glyph.set_alpha(self.alpha)
        surface.blit(glyph, (int(self.x), int(self.y)))


# ---------------------------------------------------------------------------
# Main renderer class
# ---------------------------------------------------------------------------

class FaceRenderer:
    """
    Renders the complete BMO scene onto the provided pygame Surface.

    Call draw() once per frame from the main application loop.
    """

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface

        # Load / create fonts
        pygame.font.init()
        self._font_chat  = pygame.font.SysFont("Consolas, Courier New, monospace", 14)
        self._font_input = pygame.font.SysFont("Consolas, Courier New, monospace", 15)
        self._font_label = pygame.font.SysFont("Arial, Helvetica, sans-serif",     11)
        self._font_zzz   = pygame.font.SysFont("Arial", 18, bold=True)
        self._font_status = pygame.font.SysFont("Arial", 12)

        # Pre-build scan-line overlay for the screen (static surface, reused every frame)
        self._scanlines = self._build_scanlines()

        # Screen glow surface
        self._screen_glow = self._build_screen_glow()

    # ------------------------------------------------------------------
    # Top-level draw call
    # ------------------------------------------------------------------

    def draw(
        self,
        state: dict,
        bounce_y: float = 0.0,
        mouth_anim: float = 0.0,
        zzz_particles: list | None = None,
        cursor_visible: bool = True,
        input_text: str = "",
        chat_log: list | None = None,
        streaming_text: str = "",
        app_state: str = "idle",
    ) -> None:
        """
        Draw the full BMO scene.

        Args:
            state           : current render state dict (from expressions.py)
            bounce_y        : vertical pixel offset for bounce animation
            mouth_anim      : 0-1 extra mouth openness for talking animation
            zzz_particles   : list of ZzzParticle objects (for sleeping)
            cursor_visible  : whether text cursor blinks on
            input_text      : current text in the input box
            chat_log        : list of (role, text) tuples
            streaming_text  : partial AI response being streamed
            app_state       : "idle" | "thinking" | "talking"
        """
        # Background
        self.surface.fill(C_BG)

        # === BMO Body (with bounce offset) ===
        by = int(bounce_y)
        self._draw_body(by)
        self._draw_screen(by)
        self._draw_eyes(state, by)
        self._draw_mouth(state, by, mouth_anim)
        self._draw_screen_overlays(by)
        if zzz_particles:
            for p in zzz_particles:
                p.draw(self.surface, self._font_zzz)
        self._draw_controls(by)
        self._draw_body_details(by)

        # === Chat UI ===
        self._draw_chat_area(chat_log or [], streaming_text, app_state)
        self._draw_input_box(input_text, cursor_visible, app_state)

    # ------------------------------------------------------------------
    # Body drawing
    # ------------------------------------------------------------------

    def _draw_body(self, by: int) -> None:
        body_rect = pygame.Rect(BODY_X, BODY_Y + by, BODY_W, BODY_H)

        # Drop shadow
        shadow_rect = body_rect.move(4, 6)
        pygame.draw.rect(self.surface, (5, 10, 20), shadow_rect, border_radius=BODY_R)

        # Dark outline
        pygame.draw.rect(self.surface, C_BMO_DARK, body_rect, border_radius=BODY_R)

        # Main body (1px inset)
        inner_rect = body_rect.inflate(-4, -4)
        pygame.draw.rect(self.surface, C_BMO_TEAL, inner_rect, border_radius=BODY_R - 2)

        # Top-left highlight strip — gives the console a 3D feel
        highlight_rect = pygame.Rect(BODY_X + 8, BODY_Y + by + 8, 12, BODY_H - 20)
        hl_surf = pygame.Surface((12, BODY_H - 20), pygame.SRCALPHA)
        for i in range(BODY_H - 20):
            alpha = max(0, 60 - int(60 * i / (BODY_H - 20)))
            pygame.draw.line(hl_surf, (*C_BMO_LIGHT, alpha), (0, i), (11, i))
        self.surface.blit(hl_surf, (BODY_X + 8, BODY_Y + by + 8))

    def _draw_screen(self, by: int) -> None:
        """Draw the screen bezel and dark screen background."""
        # Glow
        self.surface.blit(self._screen_glow, (SCREEN_X - 8, SCREEN_Y + by - 8))

        # Bezel
        bezel_rect = pygame.Rect(SCREEN_X - 6, SCREEN_Y + by - 5, SCREEN_W + 12, SCREEN_H + 10)
        pygame.draw.rect(self.surface, C_BMO_DARK, bezel_rect, border_radius=SCREEN_R + 4)

        # Screen background
        screen_rect = pygame.Rect(SCREEN_X, SCREEN_Y + by, SCREEN_W, SCREEN_H)
        pygame.draw.rect(self.surface, C_SCREEN_BG, screen_rect, border_radius=SCREEN_R)

    def _draw_screen_overlays(self, by: int) -> None:
        """Draw scan lines on top of the face elements."""
        self.surface.blit(self._scanlines, (SCREEN_X, SCREEN_Y + by))

        # Subtle screen border glow
        screen_rect = pygame.Rect(SCREEN_X, SCREEN_Y + by, SCREEN_W, SCREEN_H)
        pygame.draw.rect(self.surface, C_SCREEN_BORDER, screen_rect, width=2, border_radius=SCREEN_R)

    # ------------------------------------------------------------------
    # Eye drawing
    # ------------------------------------------------------------------

    def _draw_eyes(self, state: dict, by: int) -> None:
        eye_scale     = state.get("eye_scale",     1.0)
        eye_squeeze_y = state.get("eye_squeeze_y", 0.0)
        pupil_scale   = state.get("pupil_scale",   0.5)
        pupil_x       = state.get("pupil_x",       0.0)
        pupil_y       = state.get("pupil_y",       0.0)
        eye_y_offset  = state.get("eye_y_offset",  0.0)

        r = max(1, int(EYE_BASE_R * eye_scale))
        ry = max(1, int(r * (1.0 - eye_squeeze_y)))   # vertical radius for squinting

        scr_cy = SCREEN_Y + by + SCREEN_H // 2
        ey = int(scr_cy + EYE_BASE_Y_OFFSET + eye_y_offset * SCREEN_H * 0.4)

        for sign in (-1, 1):   # -1 = left eye, +1 = right eye
            cx = _SCR_CX + sign * EYE_SEP

            # --- White sclera (as an ellipse to allow squinting) ---
            eye_rect = pygame.Rect(cx - r, ey - ry, r * 2, ry * 2)
            if ry < 3:
                # Fully blinked — draw a horizontal line
                pygame.draw.line(self.surface, C_EYE_WHITE, (cx - r, ey), (cx + r, ey), 3)
                continue

            pygame.draw.ellipse(self.surface, C_EYE_WHITE, eye_rect)

            # --- Iris ring ---
            iris_r = max(1, int(r * 0.72))
            iris_ry = max(1, int(ry * 0.72))
            iris_rect = pygame.Rect(cx - iris_r, ey - iris_ry, iris_r * 2, iris_ry * 2)
            pygame.draw.ellipse(self.surface, C_EYE_IRIS, iris_rect)

            # --- Pupil ---
            pr = max(1, int(r * pupil_scale))
            pry = max(1, int(ry * pupil_scale))
            px = int(cx + pupil_x * (r - pr))
            py = int(ey + pupil_y * (ry - pry))
            pr  = min(pr,  iris_r  - 1)
            pry = min(pry, iris_ry - 1)
            if pr > 0 and pry > 0:
                pupil_rect = pygame.Rect(px - pr, py - pry, pr * 2, pry * 2)
                pygame.draw.ellipse(self.surface, C_EYE_PUPIL, pupil_rect)

                # Shine dot
                shine_r = max(1, pr // 3)
                pygame.draw.circle(
                    self.surface, C_EYE_SHINE,
                    (px - pr // 3, py - pry // 3), shine_r
                )

    # ------------------------------------------------------------------
    # Mouth drawing
    # ------------------------------------------------------------------

    def _draw_mouth(self, state: dict, by: int, mouth_anim: float) -> None:
        mouth_type  = state.get("mouth_type",  "line")
        mouth_curve = state.get("mouth_curve",  0.0)
        mouth_width = state.get("mouth_width",  1.0)
        mouth_open  = state.get("mouth_open",   0.0)

        w  = int(MOUTH_BASE_W * mouth_width)
        h  = max(4, int(MOUTH_BASE_H * abs(mouth_curve)))
        my = MOUTH_BASE_Y + by
        mx = MOUTH_CX

        if mouth_type == "line":
            # Simple flat horizontal line
            lw = max(6, w)
            pygame.draw.line(self.surface, C_MOUTH, (mx - lw // 2, my), (mx + lw // 2, my), 4)

        elif mouth_type == "arc":
            h = max(8, h)
            arc_rect = pygame.Rect(mx - w // 2, my - h // 2, w, h)
            if mouth_curve > 0:
                # Smile: bottom half of ellipse
                pygame.draw.arc(self.surface, C_MOUTH, arc_rect, math.pi, 2 * math.pi, 4)
            else:
                # Frown: top half of ellipse
                pygame.draw.arc(self.surface, C_MOUTH, arc_rect, 0, math.pi, 4)

        elif mouth_type == "o":
            # Small "O" circle
            or_ = max(4, int(w * 0.28))
            pygame.draw.circle(self.surface, C_MOUTH, (mx, my), or_, 3)

        elif mouth_type == "talking":
            # Animated open oval — oscillates with mouth_anim
            open_h = max(6, int((mouth_open + mouth_anim) * MOUTH_BASE_H * 1.2))
            open_w = max(12, int(w * 0.80))
            talk_rect = pygame.Rect(mx - open_w // 2, my - open_h // 2, open_w, open_h)
            # Fill with very dark inside
            pygame.draw.ellipse(self.surface, (8, 12, 22), talk_rect)
            # Outline
            pygame.draw.ellipse(self.surface, C_MOUTH, talk_rect, 3)

            # Small teeth line
            if open_h > 12:
                tooth_y = my - open_h // 4
                pygame.draw.line(
                    self.surface, C_MOUTH,
                    (mx - open_w // 2 + 4, tooth_y),
                    (mx + open_w // 2 - 4, tooth_y),
                    2,
                )

    # ------------------------------------------------------------------
    # D-pad + buttons
    # ------------------------------------------------------------------

    def _draw_controls(self, by: int) -> None:
        cy = by  # offset

        # ---- D-pad ----
        dpad_cx = DPAD_CX
        dpad_cy = DPAD_CY + cy
        arm_l   = DPAD_ARM_LONG
        arm_s   = DPAD_ARM_SHORT

        # Shadow
        for dx, dy in ((2, 2),):
            h_rect = pygame.Rect(dpad_cx - arm_l // 2 + dx, dpad_cy - arm_s // 2 + dy, arm_l, arm_s)
            v_rect = pygame.Rect(dpad_cx - arm_s // 2 + dx, dpad_cy - arm_l // 2 + dy, arm_s, arm_l)
            pygame.draw.rect(self.surface, C_DPAD_DARK, h_rect, border_radius=4)
            pygame.draw.rect(self.surface, C_DPAD_DARK, v_rect, border_radius=4)

        # Main arms
        h_rect = pygame.Rect(dpad_cx - arm_l // 2, dpad_cy - arm_s // 2, arm_l, arm_s)
        v_rect = pygame.Rect(dpad_cx - arm_s // 2, dpad_cy - arm_l // 2, arm_s, arm_l)
        pygame.draw.rect(self.surface, C_DPAD, h_rect, border_radius=4)
        pygame.draw.rect(self.surface, C_DPAD, v_rect, border_radius=4)

        # Centre nub
        pygame.draw.circle(self.surface, C_DPAD, (dpad_cx, dpad_cy), arm_s // 2 - 1)

        # ---- Button cluster (A=right red, B=bottom green, X=left blue, Y=top yellow) ----
        bcx = BTN_CLUSTER_CX
        bcy = BTN_CLUSTER_CY + cy
        g   = BTN_GAP
        r   = BTN_R
        buttons = [
            (bcx,     bcy - g, C_BTN_Y, "Y"),   # top
            (bcx + g, bcy,     C_BTN_A, "A"),   # right
            (bcx,     bcy + g, C_BTN_B, "B"),   # bottom
            (bcx - g, bcy,     C_BTN_X, "X"),   # left
        ]
        for bx, by_, color, label in buttons:
            # Shadow
            pygame.draw.circle(self.surface, tuple(max(0, c - 60) for c in color), (bx + 2, by_ + 2), r)
            # Button
            pygame.draw.circle(self.surface, color, (bx, by_), r)
            # Border
            pygame.draw.circle(self.surface, C_BTN_BORDER, (bx, by_), r, 1)

        # ---- Start / Select ----
        for i, label in enumerate(("SELECT", "START")):
            bx = BODY_X + 138 + i * 72
            by_ = BODY_Y + 326 + cy
            btn_rect = pygame.Rect(bx, by_, 52, 14)
            pygame.draw.rect(self.surface, C_BMO_DARK, btn_rect.move(1, 1), border_radius=7)
            pygame.draw.rect(self.surface, C_START_SEL, btn_rect, border_radius=7)
            lbl = self._font_label.render(label, True, (40, 60, 52))
            self.surface.blit(lbl, (bx + btn_rect.w // 2 - lbl.get_width() // 2, by_ + 1))

    # ------------------------------------------------------------------
    # Body detail elements
    # ------------------------------------------------------------------

    def _draw_body_details(self, by: int) -> None:
        """Shoulder bumps, speaker grille, status LED, bottom port."""

        # Shoulder bumps (side of body)
        for side_x in (BODY_X - 14, BODY_X + BODY_W - 4):
            bump_rect = pygame.Rect(side_x, BODY_Y + by + 60, 18, 28)
            pygame.draw.rect(self.surface, C_BMO_SHOULDER, bump_rect, border_radius=6)
            pygame.draw.rect(self.surface, C_BMO_DARK, bump_rect, width=1, border_radius=6)

        # Speaker grill (3 rows × 8 dots centred below screen)
        dot_r   = 2
        dot_gap = 9
        grill_x = _SCR_CX - (7 * dot_gap) // 2
        grill_y = BODY_Y + by + 305
        for row in range(3):
            for col in range(8):
                dx = grill_x + col * dot_gap
                dy = grill_y + row * dot_gap
                pygame.draw.circle(self.surface, C_SPEAKER, (dx, dy), dot_r)

        # Status LED (top right of body)
        led_x = BODY_X + BODY_W - 30
        led_y = BODY_Y + by + 28
        # Glow halo (alpha surface)
        glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C_LED_ON, 60), (10, 10), 10)
        self.surface.blit(glow, (led_x - 10, led_y - 10))
        pygame.draw.circle(self.surface, C_LED_ON, (led_x, led_y), 5)

        # Bottom port / connector
        port_rect = pygame.Rect(_SCR_CX - 55, BODY_Y + by + BODY_H - 18, 110, 12)
        pygame.draw.rect(self.surface, C_PORT, port_rect, border_radius=4)
        pygame.draw.rect(self.surface, C_BMO_DARK, port_rect, width=1, border_radius=4)

        # Screw nubs at body corners
        screw_positions = [
            (BODY_X + 18, BODY_Y + by + 20),
            (BODY_X + BODY_W - 18, BODY_Y + by + 20),
            (BODY_X + 18, BODY_Y + by + BODY_H - 20),
            (BODY_X + BODY_W - 18, BODY_Y + by + BODY_H - 20),
        ]
        for sx, sy in screw_positions:
            pygame.draw.circle(self.surface, C_BMO_DARK, (sx, sy), 5)
            pygame.draw.circle(self.surface, C_BMO_SHOULDER, (sx, sy), 3)

    # ------------------------------------------------------------------
    # Chat UI
    # ------------------------------------------------------------------

    def _draw_chat_area(
        self,
        chat_log: list[tuple[str, str]],
        streaming_text: str,
        app_state: str,
    ) -> None:
        """Render the last few chat messages below BMO's body."""
        area_rect = pygame.Rect(10, CHAT_Y, WIN_W - 20, CHAT_H)
        _draw_rounded_rect(self.surface, C_CHAT_BG, area_rect, 10)
        _draw_rounded_rect(self.surface, C_CHAT_BORDER, area_rect, 10, width=1)

        # Collect lines to display (most recent at bottom)
        all_entries: list[tuple[str, str]] = list(chat_log[-4:])
        if streaming_text:
            all_entries.append(("bmo", streaming_text + "▌"))

        pad_x = 18
        y = CHAT_Y + 10
        available_w = WIN_W - 20 - pad_x * 2

        for role, text in all_entries:
            if role == "user":
                label = self._font_label.render("YOU", True, C_TEXT_DIM)
                self.surface.blit(label, (WIN_W - 10 - pad_x - label.get_width(), y))
                y += label.get_height() + 1
                y = _draw_text_wrapped(
                    self.surface, text, self._font_chat, C_TEXT_USER,
                    pad_x + 10, y, available_w - 10
                )
            else:
                label = self._font_label.render("BMO", True, C_TEXT_DIM)
                self.surface.blit(label, (pad_x + 10, y))
                y += label.get_height() + 1
                y = _draw_text_wrapped(
                    self.surface, text, self._font_chat, C_TEXT_BMO,
                    pad_x + 10, y, available_w
                )
            y += 4   # spacing between entries

        # "Thinking…" animated dots when waiting
        if app_state == "thinking" and not streaming_text:
            import time
            dot_count = int(time.time() * 2) % 4
            dots = "•" * dot_count or " "
            thinking_surf = self._font_chat.render(f"BMO is thinking {dots}", True, C_THINKING_DOT)
            tx = pad_x + 10
            ty = min(y, CHAT_Y + CHAT_H - thinking_surf.get_height() - 8)
            self.surface.blit(thinking_surf, (tx, ty))

    def _draw_input_box(
        self,
        input_text: str,
        cursor_visible: bool,
        app_state: str,
    ) -> None:
        """Render the text input area."""
        box_rect = pygame.Rect(10, INPUT_Y, WIN_W - 20, INPUT_H)
        _draw_rounded_rect(self.surface, C_INPUT_BG, box_rect, 8)
        _draw_rounded_rect(self.surface, C_CHAT_BORDER, box_rect, 8, width=1)

        pad = 12
        inner_w = WIN_W - 20 - pad * 2

        if input_text:
            display = input_text
            color   = C_TEXT_INPUT
        else:
            display = "Talk to BMO…  (Enter to send)"
            color   = C_TEXT_PLACEHOLDER

        # Truncate from left if text overflows
        txt_surf = self._font_input.render(display, True, color)
        if txt_surf.get_width() > inner_w:
            # Clip surface to fit
            clip_rect = pygame.Rect(txt_surf.get_width() - inner_w, 0, inner_w, txt_surf.get_height())
            txt_surf = txt_surf.subsurface(clip_rect)

        ty = INPUT_Y + (INPUT_H - txt_surf.get_height()) // 2
        self.surface.blit(txt_surf, (pad + 10, ty))

        # Blinking cursor
        if cursor_visible and input_text:
            cursor_x = pad + 10 + self._font_input.size(input_text)[0]
            cursor_x = min(cursor_x, pad + 10 + inner_w)
            pygame.draw.line(
                self.surface, C_CURSOR,
                (cursor_x, ty + 2),
                (cursor_x, ty + txt_surf.get_height() - 2),
                2,
            )

        # Mode indicator label
        if app_state != "idle":
            mode_text = {"thinking": "⟳ thinking", "talking": "⟳ responding"}.get(app_state, "")
            if mode_text:
                mode_surf = self._font_label.render(mode_text, True, C_THINKING_DOT)
                self.surface.blit(mode_surf, (WIN_W - 10 - mode_surf.get_width(), INPUT_Y - 16))

    # ------------------------------------------------------------------
    # Static surface builders
    # ------------------------------------------------------------------

    def _build_scanlines(self) -> pygame.Surface:
        """Create a semi-transparent scan-line overlay for the screen area."""
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(surf, (0, 0, 0, 18), (0, y), (SCREEN_W, y), 1)
        return surf

    def _build_screen_glow(self) -> pygame.Surface:
        """Create a soft teal glow halo for around the screen."""
        gw, gh = SCREEN_W + 16, SCREEN_H + 16
        surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        for i in range(8):
            alpha = 12 - i
            pygame.draw.rect(
                surf,
                (60, 180, 120, max(0, alpha)),
                pygame.Rect(i, i, gw - i * 2, gh - i * 2),
                border_radius=SCREEN_R + 6,
            )
        return surf
