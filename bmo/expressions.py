"""
bmo/expressions.py
==================
Expression definitions for BMO's face.

We no longer need numeric parameters since we are using static PNGs.
We simply define the per-expression animation behaviours.
"""

# Available PNG faces in assets/faces/
# neutral, happy, angry, kawaii, cat, ko, laughing, sad, sleeping, 
# thinking, surprised, talking, excited, listening

EXPRESSION_ANIMS: dict[str, dict] = {
    "neutral":   {"bounce": False, "zzz": False},
    "happy":     {"bounce": True,  "zzz": False},
    "angry":     {"bounce": True,  "zzz": False},
    "kawaii":    {"bounce": True,  "zzz": False},
    "cat":       {"bounce": True,  "zzz": False},
    "ko":        {"bounce": False, "zzz": False},
    "laughing":  {"bounce": True,  "zzz": False},
    "sad":       {"bounce": False, "zzz": False},
    "sleeping":  {"bounce": False, "zzz": True},
    "thinking":  {"bounce": False, "zzz": False},
    "surprised": {"bounce": True,  "zzz": False},
    "talking":   {"bounce": False, "zzz": False},
    "excited":   {"bounce": True,  "zzz": False},
    "listening": {"bounce": False, "zzz": False},
}
