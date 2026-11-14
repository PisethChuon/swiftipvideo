"""
Swift lesson video maker
------------------------
Makes a vertical (1080x1920) explainer video:
  1. title question
  2. analogy (blueprint -> house)
  3. one-sentence definition
  4. code that types out, then highlights parts of it
  5. summary cards
  6. outro

Setup (one time):
    brew install ffmpeg          # Windows: install ffmpeg and add it to PATH
    pip3 install pillow

Run:
    python3 swift_lesson_video.py                 # makes swift-lesson.mp4
    python3 swift_lesson_video.py my-lesson.mp4   # choose the file name
    python3 swift_lesson_video.py --preview       # saves PNG pictures only (fast)

To make a new lesson, only change the LESSON section below.
"""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

# ======================================================================
# 1. YOUR LESSON: change only this part
# ======================================================================
# Rules so the text fits on a phone screen:
#   - code: at most 8 lines, at most 34 characters per line
#   - every other text: keep it short (one idea per line)
LESSON = {
    "part": "SWIFT BASICS  ·  PART 1",
    "title_a": "What is a",
    "title_b": "class?",

    # Scene 2: the analogy
    "analogy_head_a": "Think of a class",
    "analogy_head_b": "as a blueprint",
    "left_label": "BLUEPRINT",
    "left_note": "describes a house",
    "right_label": "HOUSE",
    "right_note": "a real house",
    "analogy_foot": "A blueprint is not a house.",

    # Scene 3: the definition
    "describe_a": "A Swift class describes",
    "describe_b": "what an object has",       # amber = properties
    "describe_c": "and what it can do",       # cyan  = methods

    # Scene 4: the code
    "code_heading": "Our first class",
    "code": [
        "class Song {",
        '    var title = "Unknown"',
        '    var artist = "Unknown"',
        "",
        "    func play() {",
        r'        print("Playing \(title)")',
        "    }",
        "}",
    ],
    "prop_lines": (1, 2),         # which code lines to highlight (first line = 0)
    "prop_label": "PROPERTIES",
    "prop_text": "store information",
    "method_lines": (4, 6),
    "method_label": "METHODS",
    "method_text": "functions that belong to a type",

    # Scene 5: summary
    "notice": "Notice something?",
    "notice_sub": "A class can contain both",

    # Scene 6: outro
    "outro_a": "Follow for",
    "outro_b": "Part 2",
    "outro_small": "One idea. One video.",
}

TYPING_SPEED = 32      # characters per second (higher = faster typing)

# ======================================================================
# 2. SETTINGS: video size, colors, fonts
# ======================================================================
W, H, FPS = 1080, 1920, 30          # 9:16 vertical video for TikTok


def find_font(*paths):
    """Return the first font file that exists on this computer."""
    for p in paths:
        if os.path.exists(p):
            return p
    sys.exit("Font not found. Add a font path to find_font() in this script. Tried:\n  " + "\n  ".join(paths))


# Paths are listed for Mac, Windows, Linux. The first one that exists is used.
MONO = find_font("/System/Library/Fonts/Menlo.ttc",
                 "C:/Windows/Fonts/consola.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
SANS = find_font("/System/Library/Fonts/Supplemental/Arial.ttf",
                 "C:/Windows/Fonts/arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
SANS_BOLD = find_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                      "C:/Windows/Fonts/arialbd.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

F_CODE = ImageFont.truetype(MONO, 42)          # code inside the card
F_BIGCODE = ImageFont.truetype(MONO, 150)      # big word on the title card
F_HEAD = ImageFont.truetype(SANS_BOLD, 84)     # big headings
F_LINE = ImageFont.truetype(SANS_BOLD, 72)     # colored lines
F_MED = ImageFont.truetype(SANS_BOLD, 52)      # medium text
F_LABEL = ImageFont.truetype(SANS_BOLD, 54)    # PROPERTIES / METHODS
F_BADGE = ImageFont.truetype(SANS_BOLD, 44)    # small labels
F_SUB = ImageFont.truetype(SANS, 46)           # small gray text
F_NOTE = ImageFont.truetype(SANS, 40)          # notes under the cards

CW = F_CODE.getlength("M")   # width of one code character (monospace = all equal)
LH = 68                      # line height of the code

BG_TOP, BG_BOT = (16, 18, 26), (27, 31, 44)    # background gradient
BASE = (22, 25, 35)                            # color we fade from
CARD = (30, 34, 46)
HILITE = (46, 54, 74)                          # highlighted code rows
WHITE, GRAY = (255, 255, 255), (140, 150, 170)

# Code colors (like Xcode dark theme)
C_TEXT, C_KEYWORD, C_TYPE, C_FUNC = (230, 232, 240), (252, 95, 163), (93, 216, 255), (103, 183, 164)
C_COMMENT, C_STRING = (108, 121, 134), (252, 106, 93)
KEYWORDS = {"let", "var", "if", "guard", "else", "func", "return", "struct", "class"}
TYPES = {"String", "Int", "Double", "Bool", "Song"}
FUNCS = {"print"}

PROP_COLOR = (255, 189, 46)    # amber: properties ("what it has")
METH_COLOR = C_TYPE            # cyan: methods ("what it can do")

# The code card
CX0, CY0, CX1, CY1 = 60, 380, 1020, 1150

# Background picture is made once and copied for every frame (faster)
_mask = Image.linear_gradient("L").resize((W, H))
BG = Image.composite(Image.new("RGB", (W, H), BG_BOT), Image.new("RGB", (W, H), BG_TOP), _mask)
FLAT = Image.new("RGB", (W, H), BG_TOP)


# ======================================================================
# 3. SMALL HELPERS
# ======================================================================
def clamp(x):
    """Keep a number between 0 and 1."""
    return max(0.0, min(1.0, x))


def mix(c1, c2, amount):
    """Blend two colors. amount=0 -> c1, amount=1 -> c2."""
    return tuple(int(a + (b - a) * amount) for a, b in zip(c1, c2))


def fade(color, amount):
    """amount=0 -> invisible (same as background), amount=1 -> full color."""
    return mix(BASE, color, amount)


def tokenize(line):
    """Split one line of code into (character, color) pairs for syntax colors."""
    out = []
    for m in re.finditer(r'//.*|"[^"]*"|\w+|\s|.', line):
        s = m.group(0)
        if s.startswith("//"):
            color = C_COMMENT
        elif s.startswith('"'):
            color = C_STRING
        elif s in KEYWORDS:
            color = C_KEYWORD
        elif s in TYPES:
            color = C_TYPE
        elif s in FUNCS:
            color = C_FUNC
        else:
            color = C_TEXT
        out += [(ch, color) for ch in s]
    return out


def new_frame():
    img = BG.copy()
    return img, ImageDraw.Draw(img)


def code_timing():
    """Typing time depends on how much code there is. Returns the key moments (seconds)."""
    total = sum(len(line) for line in LESSON["code"])
    type_start = 0.5
    type_end = type_start + total / TYPING_SPEED
    prop_at = type_end + 0.6            # properties get highlighted
    meth_at = prop_at + 2.4             # then methods
    duration = meth_at + 2.6
    return type_start, type_end, prop_at, meth_at, duration


TYPE_START, TYPE_END, PROP_AT, METH_AT, CODE_DUR = code_timing()


# ======================================================================
# 4. DRAWING THE HOUSE (blueprint = lines only, house = filled colors)
# ======================================================================
def draw_house(d, cx, cy, a, filled):
    body = [cx - 110, cy - 5, cx + 110, cy + 105]
    roof = [(cx - 140, cy - 5), (cx, cy - 110), (cx + 140, cy - 5)]
    door = [cx - 26, cy + 45, cx + 26, cy + 105]
    windows = [[cx - 92, cy + 20, cx - 48, cy + 62], [cx + 48, cy + 20, cx + 92, cy + 62]]
    if filled:
        d.rectangle(body, fill=fade((240, 205, 150), a))
        d.polygon(roof, fill=fade((200, 72, 62), a))
        d.rectangle(door, fill=fade((120, 80, 52), a))
        for w in windows:
            d.rectangle(w, fill=fade((150, 210, 255), a))
    else:
        line = fade((225, 238, 255), a)
        d.rectangle(body, outline=line, width=5)
        d.line(roof + [roof[0]], fill=line, width=5, joint="curve")
        d.rectangle(door, outline=line, width=5)
        for w in windows:
            d.rectangle(w, outline=line, width=5)


# ======================================================================
# 5. SCENES: each function draws ONE frame for time t (in seconds)
# ======================================================================
def scene_title(t):
    L = LESSON
    img, d = new_frame()
    a0, a1, a2 = clamp(t / 0.4), clamp((t - 0.5) / 0.4), clamp((t - 1.1) / 0.4)
    d.text((W // 2, 640), L["part"], font=F_BADGE, fill=fade(GRAY, a0), anchor="mm")
    d.text((W // 2, 800), L["title_a"], font=F_HEAD, fill=fade(WHITE, a1), anchor="mm")
    d.text((W // 2, 980), L["title_b"], font=F_BIGCODE, fill=fade(C_KEYWORD, a2), anchor="mm")
    return img


CARD_L, CARD_R = (80, 640, 480, 1040), (600, 640, 1000, 1040)


def scene_analogy(t):
    L = LESSON
    img, d = new_frame()
    a0 = clamp(t / 0.4)
    d.text((W // 2, 330), L["analogy_head_a"], font=F_HEAD, fill=fade(WHITE, a0), anchor="mm")
    d.text((W // 2, 440), L["analogy_head_b"], font=F_HEAD, fill=fade(C_TYPE, a0), anchor="mm")

    # Left card: the blueprint (blue paper with a grid and white lines)
    aL = clamp((t - 0.5) / 0.4)
    x0, y0, x1, y1 = CARD_L
    d.rounded_rectangle(CARD_L, radius=30, fill=fade((30, 70, 130), aL))
    for gx in range(x0 + 20, x1 - 10, 40):
        d.line([(gx, y0 + 20), (gx, y1 - 20)], fill=fade((52, 100, 170), aL), width=1)
    for gy in range(y0 + 20, y1 - 10, 40):
        d.line([(x0 + 20, gy), (x1 - 20, gy)], fill=fade((52, 100, 170), aL), width=1)
    draw_house(d, (x0 + x1) // 2, 850, aL, filled=False)
    d.text(((x0 + x1) // 2, 1100), L["left_label"], font=F_BADGE, fill=fade(WHITE, aL), anchor="mm")
    aLn = clamp((t - 0.9) / 0.4)
    d.text(((x0 + x1) // 2, 1160), L["left_note"], font=F_NOTE, fill=fade(GRAY, aLn), anchor="mm")

    # Arrow between the cards
    aA = clamp((t - 1.3) / 0.3)
    d.line([(505, 840), (555, 840)], fill=fade(GRAY, aA), width=10)
    d.polygon([(555, 812), (588, 840), (555, 868)], fill=fade(GRAY, aA))

    # Right card: the real house
    aR = clamp((t - 1.6) / 0.4)
    x0, y0, x1, y1 = CARD_R
    d.rounded_rectangle(CARD_R, radius=30, fill=fade((52, 62, 84), aR))
    draw_house(d, (x0 + x1) // 2, 850, aR, filled=True)
    d.text(((x0 + x1) // 2, 1100), L["right_label"], font=F_BADGE, fill=fade(WHITE, aR), anchor="mm")
    aRn = clamp((t - 2.0) / 0.4)
    d.text(((x0 + x1) // 2, 1160), L["right_note"], font=F_NOTE, fill=fade(GRAY, aRn), anchor="mm")

    # The key sentence
    aF = clamp((t - 3.0) / 0.4)
    d.text((W // 2, 1340), L["analogy_foot"], font=F_MED, fill=fade(WHITE, aF), anchor="mm")
    return img


def scene_describe(t):
    L = LESSON
    img, d = new_frame()
    a0, a1, a2 = clamp(t / 0.4), clamp((t - 0.6) / 0.4), clamp((t - 1.4) / 0.4)
    d.text((W // 2, 640), L["describe_a"], font=F_MED, fill=fade(WHITE, a0), anchor="mm")
    d.text((W // 2, 800), L["describe_b"], font=F_LINE, fill=fade(PROP_COLOR, a1), anchor="mm")
    d.text((W // 2, 940), L["describe_c"], font=F_LINE, fill=fade(METH_COLOR, a2), anchor="mm")
    return img


def scene_code(t):
    L = LESSON
    img, d = new_frame()
    d.text((W // 2, 270), L["code_heading"], font=F_HEAD, fill=WHITE, anchor="mm")

    # Code card with the three window dots
    d.rounded_rectangle([CX0, CY0, CX1, CY1], radius=36, fill=CARD)
    for i, dot in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = CX0 + 55 + i * 44
        d.ellipse([cx - 13, CY0 + 32, cx + 13, CY0 + 58], fill=dot)

    # Which part is highlighted right now?
    if t >= METH_AT:
        active, hl_start, color = L["method_lines"], METH_AT, METH_COLOR
        label, text = L["method_label"], L["method_text"]
    elif t >= PROP_AT:
        active, hl_start, color = L["prop_lines"], PROP_AT, PROP_COLOR
        label, text = L["prop_label"], L["prop_text"]
    else:
        active = None

    rows = [tokenize(line) for line in L["code"]]
    x0, y0 = CX0 + 50, CY0 + 110

    # Highlight bar behind the active rows
    dim = 1.0
    if active:
        a = clamp((t - hl_start) / 0.25)
        dim = 1.0 - 0.65 * a                   # other rows become dim
        top = y0 + active[0] * LH - 10
        bottom = y0 + (active[1] + 1) * LH - 10
        d.rounded_rectangle([CX0 + 20, top, CX1 - 20, bottom], radius=14, fill=mix(CARD, HILITE, a))
        d.rectangle([CX0 + 20, top + 6, CX0 + 28, bottom - 6], fill=mix(CARD, color, a))

    # Typing effect: how many characters are visible right now?
    total = sum(len(r) for r in rows)
    progress = clamp((t - TYPE_START) / (TYPE_END - TYPE_START))
    visible = int(total * progress + 0.5)

    cursor_pos, count = (x0, y0), 0
    for li, row in enumerate(rows):
        y = y0 + li * LH
        in_active = active is not None and active[0] <= li <= active[1]
        for ci, (ch, col) in enumerate(row):
            if count >= visible:
                break
            if ch != " ":
                c = col if (active is None or in_active) else mix(HILITE, col, 1.0 - 0.65 * clamp((t - hl_start) / 0.25))
                d.text((x0 + ci * CW, y), ch, font=F_CODE, fill=c)
            cursor_pos = (x0 + (ci + 1) * CW, y)
            count += 1
        if count >= visible:
            break

    # Blinking cursor (only until the highlights start)
    if active is None and t >= TYPE_START - 0.3 and (progress < 1 or int(t * 2.5) % 2 == 0):
        cx, cy = cursor_pos
        d.rectangle([cx + 3, cy + 2, cx + 10, cy + 50], fill=(235, 238, 245))

    # Label box under the card
    if active:
        a = clamp((t - hl_start) / 0.25)
        d.rounded_rectangle([CX0, 1220, CX1, 1420], radius=30,
                            fill=fade(color, 0.18 * a), outline=fade(color, a), width=4)
        d.text((W // 2, 1285), label, font=F_LABEL, fill=fade(color, a), anchor="mm")
        d.text((W // 2, 1360), text, font=F_SUB, fill=fade(WHITE, a), anchor="mm")
    return img


def scene_notice(t):
    L = LESSON
    img, d = new_frame()
    a0, a1 = clamp(t / 0.4), clamp((t - 0.5) / 0.4)
    d.text((W // 2, 470), L["notice"], font=F_HEAD, fill=fade(WHITE, a0), anchor="mm")
    d.text((W // 2, 590), L["notice_sub"], font=F_SUB, fill=fade(GRAY, a1), anchor="mm")
    cards = [(L["prop_label"], L["prop_text"], PROP_COLOR), (L["method_label"], L["method_text"], METH_COLOR)]
    for k, (label, text, color) in enumerate(cards):
        a = clamp((t - (1.2 + k * 1.0)) / 0.4)
        top = 720 + k * 270
        d.rounded_rectangle([CX0, top, CX1, top + 230], radius=30,
                            fill=fade(color, 0.18 * a), outline=fade(color, a), width=4)
        d.text((W // 2, top + 80), label, font=F_LABEL, fill=fade(color, a), anchor="mm")
        d.text((W // 2, top + 158), text, font=F_SUB, fill=fade(WHITE, a), anchor="mm")
    return img


def scene_outro(t):
    L = LESSON
    img, d = new_frame()
    a1, a2 = clamp(t / 0.4), clamp((t - 0.4) / 0.4)
    d.text((W // 2, 760), L["outro_a"], font=F_HEAD, fill=fade(WHITE, a1), anchor="mm")
    d.text((W // 2, 880), L["outro_b"], font=F_HEAD, fill=fade(C_TYPE, a1), anchor="mm")
    d.text((W // 2, 1040), L["outro_small"], font=F_SUB, fill=fade(GRAY, a2), anchor="mm")
    return img


# ======================================================================
# 6. THE SCENE LIST: (name, seconds, draw function, preview times)
# ======================================================================
def build_scenes():
    return [
        ("1_title", 2.6, scene_title, [1.8]),
        ("2_analogy", 5.2, scene_analogy, [1.2, 3.6]),
        ("3_describe", 3.2, scene_describe, [2.2]),
        ("4_code", CODE_DUR, scene_code, [TYPE_END - 1.0, PROP_AT + 1.0, METH_AT + 1.0]),
        ("5_notice", 5.0, scene_notice, [4.0]),
        ("6_outro", 2.4, scene_outro, [1.4]),
    ]


def check_text_fits():
    """Stop early with a clear message if the code would run off the card."""
    max_chars = int((CX1 - CX0 - 100) / CW)
    code = LESSON["code"]
    if len(code) > 8:
        sys.exit("code: use at most 8 lines.")
    for line in code:
        if len(line) > max_chars:
            sys.exit(f"code: this line is too long ({len(line)} characters, max {max_chars}):\n  {line}\n"
                     "Shorten it, because long lines are too small to read on a phone.")


# ======================================================================
# 7. RENDER: draw frames -> send to ffmpeg -> join the scenes
# ======================================================================
def render_scene(folder, name, duration, draw_frame):
    """Draw every frame of one scene and pipe it into ffmpeg (no PNG files needed)."""
    tmp_file = os.path.join(folder, name + ".tmp.mp4")
    final_file = os.path.join(folder, name + ".mp4")
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
         "-pix_fmt", "yuv420p",              # needed, or phones can not play the video
         tmp_file],
        stdin=subprocess.PIPE)

    for i in range(int(duration * FPS)):
        t = i / FPS
        img = draw_frame(t)
        # Fade in at the start and fade out at the end of every scene (0.2 seconds)
        a = clamp(min(t / 0.2, (duration - t) / 0.2))
        if a < 1:
            img = Image.blend(FLAT, img, a)
        ff.stdin.write(img.tobytes())

    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg failed. Is ffmpeg installed? Try: ffmpeg -version")
    os.rename(tmp_file, final_file)          # only a finished file gets the real name
    return final_file


def main():
    check_text_fits()
    scenes = build_scenes()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--preview" in sys.argv:
        # Fast check: save pictures at key moments, no video
        for name, _, draw_frame, times in scenes:
            for k, t in enumerate(times):
                draw_frame(t).save(f"preview_{name}_{k + 1}.png")
        print("Saved preview_*.png")
        return

    out_file = args[0] if args else "swift-lesson.mp4"
    with tempfile.TemporaryDirectory() as folder:
        parts = [render_scene(folder, name, dur, fn) for name, dur, fn, _ in scenes]

        # Join the scene files without re-encoding (fast, no quality loss)
        list_file = os.path.join(folder, "list.txt")
        with open(list_file, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        tmp_out = out_file + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", list_file, "-c", "copy", tmp_out], check=True)
        os.replace(tmp_out, out_file)
    print("Done:", out_file)


if __name__ == "__main__":
    main()