"""
bmo/expressions.py
==================
Expression parameter dictionary for BMO's face.

Each expression defines target values for the face renderer.
All numeric values are lerped smoothly when transitioning between expressions.

Parameter reference:
  eye_scale     : float  0.3-1.5   — overall eye size multiplier
  eye_squeeze_y : float  0.0-1.0   — vertical squish (0=open, 1=fully closed)
  pupil_scale   : float  0.3-0.7   — pupil radius as fraction of eye radius
  pupil_x       : float -1.0-1.0   — pupil horizontal offset (fraction of eye radius)
  pupil_y       : float -1.0-1.0   — pupil vertical offset
  mouth_curve   : float -1.0-1.0   — mouth curve (-1=max frown, 0=line, 1=max smile)
  mouth_width   : float  0.5-1.5   — mouth width multiplier
  mouth_open    : float  0.0-1.0   — jaw openness (0=closed, 1=open) — talking anim
  brow_raise    : float -1.0-1.0   — brow position (-1=angry, 0=neutral, 1=surprised)
  cheek_blush   : float  0.0-1.0   — blush intensity
  eye_y_offset  : float -0.3-0.3   — shift eyes up/down on screen
  mouth_type    : str               — drawing mode for mouth shape
"""

# ---------------------------------------------------------------------------
# Core expression targets
# ---------------------------------------------------------------------------

EXPRESSIONS: dict[str, dict] = {

    "neutral": {
        "eye_scale":     1.00,
        "eye_squeeze_y": 0.00,
        "pupil_scale":   0.50,
        "pupil_x":       0.00,
        "pupil_y":       0.00,
        "mouth_curve":   0.00,
        "mouth_width":   1.00,
        "mouth_open":    0.00,
        "brow_raise":    0.00,
        "cheek_blush":   0.00,
        "eye_y_offset":  0.00,
        "mouth_type":    "line",
    },

    "happy": {
        "eye_scale":     1.10,
        "eye_squeeze_y": 0.00,
        "pupil_scale":   0.45,
        "pupil_x":       0.00,
        "pupil_y":      -0.10,
        "mouth_curve":   0.70,
        "mouth_width":   1.20,
        "mouth_open":    0.00,
        "brow_raise":    0.30,
        "cheek_blush":   0.60,
        "eye_y_offset": -0.10,
        "mouth_type":    "arc",
    },

    "excited": {
        "eye_scale":     1.30,
        "eye_squeeze_y": 0.00,
        "pupil_scale":   0.55,
        "pupil_x":       0.00,
        "pupil_y":      -0.15,
        "mouth_curve":   1.00,
        "mouth_width":   1.40,
        "mouth_open":    0.20,
        "brow_raise":    0.60,
        "cheek_blush":   1.00,
        "eye_y_offset": -0.15,
        "mouth_type":    "arc",
    },

    "thinking": {
        "eye_scale":     0.85,
        "eye_squeeze_y": 0.15,
        "pupil_scale":   0.60,
        "pupil_x":       0.40,   # looking to the upper-right
        "pupil_y":      -0.25,
        "mouth_curve":   0.00,
        "mouth_width":   0.55,
        "mouth_open":    0.30,
        "brow_raise":    0.45,
        "cheek_blush":   0.00,
        "eye_y_offset":  0.00,
        "mouth_type":    "o",
    },

    "sad": {
        "eye_scale":     0.90,
        "eye_squeeze_y": 0.12,
        "pupil_scale":   0.50,
        "pupil_x":       0.00,
        "pupil_y":       0.25,   # downcast eyes
        "mouth_curve":  -0.65,
        "mouth_width":   0.90,
        "mouth_open":    0.00,
        "brow_raise":   -0.35,
        "cheek_blush":   0.00,
        "eye_y_offset":  0.10,
        "mouth_type":    "arc",
    },

    "surprised": {
        "eye_scale":     1.45,
        "eye_squeeze_y": 0.00,
        "pupil_scale":   0.38,
        "pupil_x":       0.00,
        "pupil_y":       0.00,
        "mouth_curve":   0.00,
        "mouth_width":   0.90,
        "mouth_open":    0.80,
        "brow_raise":    1.00,
        "cheek_blush":   0.00,
        "eye_y_offset": -0.20,
        "mouth_type":    "o",
    },

    "talking": {
        "eye_scale":     1.00,
        "eye_squeeze_y": 0.00,
        "pupil_scale":   0.50,
        "pupil_x":       0.00,
        "pupil_y":       0.00,
        "mouth_curve":   0.25,
        "mouth_width":   1.10,
        "mouth_open":    0.50,   # base openness; animated in app.py
        "brow_raise":    0.10,
        "cheek_blush":   0.20,
        "eye_y_offset":  0.00,
        "mouth_type":    "talking",
    },

    "sleeping": {
        "eye_scale":     0.30,
        "eye_squeeze_y": 1.00,   # fully closed
        "pupil_scale":   0.50,
        "pupil_x":       0.00,
        "pupil_y":       0.00,
        "mouth_curve":   0.10,
        "mouth_width":   0.65,
        "mouth_open":    0.00,
        "brow_raise":   -0.10,
        "cheek_blush":   0.00,
        "eye_y_offset":  0.05,
        "mouth_type":    "line",
    },

    "listening": {
        "eye_scale":     1.05,
        "eye_squeeze_y": 0.05,
        "pupil_scale":   0.55,
        "pupil_x":       0.00,
        "pupil_y":       0.00,
        "mouth_curve":   0.10,
        "mouth_width":   0.80,
        "mouth_open":    0.00,
        "brow_raise":    0.20,
        "cheek_blush":   0.10,
        "eye_y_offset":  0.00,
        "mouth_type":    "line",
    },
}

# ---------------------------------------------------------------------------
# Per-expression animation behaviours (read by app.py)
# ---------------------------------------------------------------------------

EXPRESSION_ANIMS: dict[str, dict] = {
    "neutral":   {"blink_interval": 4.0, "bounce": False, "pupil_wander": True,  "eye_dart": False, "zzz": False},
    "happy":     {"blink_interval": 5.5, "bounce": True,  "pupil_wander": False, "eye_dart": False, "zzz": False},
    "excited":   {"blink_interval": 7.0, "bounce": True,  "pupil_wander": False, "eye_dart": False, "zzz": False},
    "thinking":  {"blink_interval": 8.0, "bounce": False, "pupil_wander": False, "eye_dart": True,  "zzz": False},
    "sad":       {"blink_interval": 3.0, "bounce": False, "pupil_wander": False, "eye_dart": False, "zzz": False},
    "surprised": {"blink_interval": 99., "bounce": False, "pupil_wander": False, "eye_dart": False, "zzz": False},
    "talking":   {"blink_interval": 5.0, "bounce": False, "pupil_wander": False, "eye_dart": False, "zzz": False},
    "sleeping":  {"blink_interval": 99., "bounce": False, "pupil_wander": False, "eye_dart": False, "zzz": True},
    "listening": {"blink_interval": 4.5, "bounce": False, "pupil_wander": True,  "eye_dart": False, "zzz": False},
}


def lerp_state(current: dict, target_name: str, dt: float, speed: float = 6.0) -> dict:
    """
    Lerp all numeric values in current render state toward the target expression.
    Non-numeric keys (mouth_type) are snapped immediately when the target changes.
    Returns the updated current state (mutates in place and returns it).
    """
    target = EXPRESSIONS[target_name]
    for key, target_val in target.items():
        if isinstance(target_val, (int, float)):
            curr_val = current.get(key, target_val)
            current[key] = curr_val + (target_val - curr_val) * min(1.0, speed * dt)
        else:
            current[key] = target_val   # snap strings immediately
    return current


def make_initial_state(expression: str = "neutral") -> dict:
    """Return a fresh copy of an expression's parameters as the starting render state."""
    return dict(EXPRESSIONS[expression])
