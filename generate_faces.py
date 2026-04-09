import os
from PIL import Image, ImageDraw, ImageFont

# Figma face style parameters
W, H = 244, 210
BG_COLOR = (184, 228, 201)  # Light teal #b8e4c9
FG_COLOR = (20, 40, 30)     # Dark green/black for features
PINK = (255, 183, 183)      # Blush pink #ffb7b7
RED = (255, 60, 60)         # Hearts
YELLOW = (255, 215, 0)      # Stars

OUTPUT_DIR = "assets/faces"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_base():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)) # transparent background, we don't draw BG here. Wait, actually if I draw BG it overrides Pygame's scanline effect beautifully if we want, or we can just draw transparency and let face.py handle BG.
    # The Figma assets have a light teal BG. Let's make it transparent so we can use Pygame's CRT effect beneath it!
    # BG_COLOR is just for reference, we will draw transparent PNGs.
    return Image.new('RGBA', (W, H), (0, 0, 0, 0)), ImageDraw.Draw(img)

def save(img, name):
    img.save(os.path.join(OUTPUT_DIR, f"{name}.png"))

def draw_eye(draw, cx, cy, radius=6):
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=FG_COLOR)

def d_neutral():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2 - 10)
    draw_eye(draw, W//2 + 40, H//2 - 10)
    draw.arc([W//2 - 12, H//2, W//2 + 12, H//2 + 15], 0, 180, fill=FG_COLOR, width=4)
    save(img, "neutral")

def d_happy():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2 - 15)
    draw_eye(draw, W//2 + 40, H//2 - 15)
    draw.arc([W//2 - 15, H//2 - 5, W//2 + 15, H//2 + 15], 0, 180, fill=FG_COLOR, width=5)
    # blush
    draw.ellipse([W//2 - 60 - 10, H//2, W//2 - 60 + 10, H//2 + 10], fill=PINK)
    draw.ellipse([W//2 + 60 - 10, H//2, W//2 + 60 + 10, H//2 + 10], fill=PINK)
    save(img, "happy")

def d_angry():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    # angled brows
    draw.line([W//2 - 60, H//2 - 40, W//2 - 20, H//2 - 20], fill=FG_COLOR, width=5, joint="curve")
    draw.line([W//2 + 60, H//2 - 40, W//2 + 20, H//2 - 20], fill=FG_COLOR, width=5, joint="curve")
    draw_eye(draw, W//2 - 40, H//2 - 10, radius=5)
    draw_eye(draw, W//2 + 40, H//2 - 10, radius=5)
    # roaring mouth
    draw.arc([W//2 - 15, H//2 + 10, W//2 + 15, H//2 + 30], 180, 360, fill=FG_COLOR, width=4)
    save(img, "angry")

def d_kawaii():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    # large eyes with white sparkles
    def kawaii_eye(cx, cy):
        draw.ellipse([cx-25, cy-25, cx+25, cy+25], fill=FG_COLOR)
        draw.ellipse([cx+5, cy-15, cx+15, cy-5], fill="white")
        draw.ellipse([cx-15, cy+5, cx-5, cy+15], fill="white")
    kawaii_eye(W//2 - 50, H//2 - 10)
    kawaii_eye(W//2 + 50, H//2 - 10)
    # tiny open mouth
    draw.ellipse([W//2 - 8, H//2 + 15, W//2 + 8, H//2 + 25], fill=FG_COLOR)
    draw.ellipse([W//2 - 65, H//2 + 20, W//2 - 35, H//2 + 30], fill=PINK)
    draw.ellipse([W//2 + 35, H//2 + 20, W//2 + 65, H//2 + 30], fill=PINK)
    save(img, "kawaii")

def d_cat():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    # > < eyes
    draw.line([W//2 - 60, H//2 - 30, W//2 - 30, H//2 - 10, W//2 - 60, H//2 + 10], fill=FG_COLOR, width=5, joint="curve")
    draw.line([W//2 + 60, H//2 - 30, W//2 + 30, H//2 - 10, W//2 + 60, H//2 + 10], fill=FG_COLOR, width=5, joint="curve")
    # ω mouth (3)
    draw.arc([W//2 - 15, H//2 + 10, W//2, H//2 + 25], 0, 180, fill=FG_COLOR, width=4)
    draw.arc([W//2, H//2 + 10, W//2 + 15, H//2 + 25], 0, 180, fill=FG_COLOR, width=4)
    save(img, "cat")

def d_ko():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    # X X eyes
    def x_eye(cx, cy):
        draw.line([cx-15, cy-15, cx+15, cy+15], fill=FG_COLOR, width=6)
        draw.line([cx-15, cy+15, cx+15, cy-15], fill=FG_COLOR, width=6)
    x_eye(W//2 - 40, H//2 - 10)
    x_eye(W//2 + 40, H//2 - 10)
    # flat mouth
    draw.line([W//2 - 15, H//2 + 20, W//2 + 15, H//2 + 20], fill=FG_COLOR, width=5)
    save(img, "ko")

def d_laughing():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2 - 15)
    draw_eye(draw, W//2 + 40, H//2 - 15)
    # wide open D mouth
    draw.chord([W//2 - 20, H//2 - 5, W//2 + 20, H//2 + 25], 0, 180, fill=FG_COLOR)
    save(img, "laughing")

def d_sad():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2)
    draw_eye(draw, W//2 + 40, H//2)
    # frown arc
    draw.arc([W//2 - 15, H//2 + 15, W//2 + 15, H//2 + 35], 180, 360, fill=FG_COLOR, width=4)
    save(img, "sad")

def d_sleeping():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    # closed eyes (U shape)
    draw.arc([W//2 - 55, H//2 - 10, W//2 - 25, H//2 + 10], 0, 180, fill=FG_COLOR, width=4)
    draw.arc([W//2 + 25, H//2 - 10, W//2 + 55, H//2 + 10], 0, 180, fill=FG_COLOR, width=4)
    # cute smile
    draw.arc([W//2 - 10, H//2 + 20, W//2 + 10, H//2 + 30], 0, 180, fill=FG_COLOR, width=4)
    save(img, "sleeping")

def d_thinking():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 45, H//2 - 25)
    draw_eye(draw, W//2 + 35, H//2 - 25)
    draw.line([W//2 - 10, H//2 + 15, W//2 + 10, H//2 + 15], fill=FG_COLOR, width=4)
    save(img, "thinking")

def d_surprised():
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2 - 15, radius=8)
    draw_eye(draw, W//2 + 40, H//2 - 15, radius=8)
    draw.ellipse([W//2 - 15, H//2 + 10, W//2 + 15, H//2 + 40], outline=FG_COLOR, width=4)
    save(img, "surprised")

def d_talking(): # Default taking (a slightly open mouth variant of neutral)
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2 - 10)
    draw_eye(draw, W//2 + 40, H//2 - 10)
    draw.ellipse([W//2 - 12, H//2 + 5, W//2 + 12, H//2 + 20], fill=FG_COLOR)
    save(img, "talking")

def d_excited(): # Reusing joyful/star struck idea
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    # Star eyes
    def draw_star(cx, cy, radius):
        draw.polygon([
            (cx, cy-radius), (cx+radius*0.3, cy-radius*0.3),
            (cx+radius, cy), (cx+radius*0.3, cy+radius*0.3),
            (cx, cy+radius), (cx-radius*0.3, cy+radius*0.3),
            (cx-radius, cy), (cx-radius*0.3, cy-radius*0.3)
        ], fill=YELLOW, outline=FG_COLOR)
    draw_star(W//2 - 45, H//2 - 15, 20)
    draw_star(W//2 + 45, H//2 - 15, 20)
    # big smile
    draw.chord([W//2 - 25, H//2 - 5, W//2 + 25, H//2 + 30], 0, 180, fill=FG_COLOR)
    save(img, "excited")

def d_listening(): # Similar to neutral but eyebrows up or just neutral
    img = Image.new('RGBA', (W, H), (0,0,0,0)); draw = ImageDraw.Draw(img)
    draw_eye(draw, W//2 - 40, H//2 - 10)
    draw_eye(draw, W//2 + 40, H//2 - 10)
    draw.line([W//2 - 10, H//2 + 10, W//2 + 10, H//2 + 10], fill=FG_COLOR, width=4)
    save(img, "listening")

# Call all
d_neutral()
d_happy()
d_angry()
d_kawaii()
d_cat()
d_ko()
d_laughing()
d_sad()
d_sleeping()
d_thinking()
d_surprised()
d_talking()
d_excited()
d_listening()
print("Generated face PNGs.")
