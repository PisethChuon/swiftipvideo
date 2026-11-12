"""
Swift tip video maker
---------------------
Makes a vertical (1080x1920) "Mistake vs Fix" video with a typing effect.

Setup (one time):
    brew install ffmpeg          # Windows: install ffmpeg and add it to PATH
    pip3 install pillow

Run:
    python3 swift_tip_video.py                 # makes swift-tip.mp4
    python3 swift_tip_video.py my-video.mp4    # choose the file name
    python3 swift_tip_video.py --preview       # saves 4 PNG pictures only (fast)

To make a new video, only change the TIP section below.
"""
import os
import re
import subprocess
import sys
import tempfile
from functools import partial

from PIL import Image, ImageDraw, ImageFont

# ======================================================================
# 1. YOUR TIP: change only this part
# ======================================================================
# Rules so the text fits on a phone screen:
#   - code lines: at most 5 lines, about 24 characters per line
#   - headings: short, about 14 characters
TIP = {
    "number": 1,
    "stop_using": "name!",                      # big red word on the title card
    "mistake_heading": "Force unwrap",
    "mistake_code": [
        "// Crashes if nil",
        "let name: String? = nil",
        "print(name!)",
    ],
    "mistake_error": "Fatal error: unexpectedly found nil",
    "fix_heading": "Safe unwrap",
    "fix_code": [
        "// Safe unwrap",
        "let name: String? = nil",
        "if let name {",
        "    print(name)",
        "}",
    ],
    "fix_result": "Prints nothing. No crash.",
    "outro_line1": "Follow for",
    "outro_line2": "more Swift tips",
    "outro_small": "One mistake. One fix.",
}

TYPING_SPEED = 25      # characters per second (higher = faster typing)

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

F_CODE = ImageFont.truetype(MONO, 54)          # code inside the card
F_BIGCODE = ImageFont.truetype(MONO, 150)      # big word on the title card
F_SMALL = ImageFont.truetype(MONO, 38)         # error / result box
F_HEAD = ImageFont.truetype(SANS_BOLD, 84)     # headings
F_BADGE = ImageFont.truetype(SANS_BOLD, 44)    # MISTAKE / FIX pill
F_SUB = ImageFont.truetype(SANS, 46)           # small gray text

CW = F_CODE.getlength("M")   # width of one code character (monospace = all equal)
LH = 86                      # line height of the code

BG_TOP, BG_BOT = (16, 18, 26), (27, 31, 44)    # background gradient
BASE = (22, 25, 35)                            # color we fade from
CARD = (30, 34, 46)
WHITE, GRAY = (255, 255, 255), (140, 150, 170)
RED, GREEN = (255, 95, 86), (60, 200, 120)

# Code colors (like Xcode dark theme)
C_TEXT, C_KEYWORD, C_TYPE, C_FUNC = (230, 232, 240), (252, 95, 163), (93, 216, 255), (103, 183, 164)
C_COMMENT, C_STRING = (108, 121, 134), (252, 106, 93)
KEYWORDS = {"let", "var", "if", "guard", "else", "func", "return", "struct", "class"}
TYPES = {"String", "Int", "Double", "Bool"}
FUNCS = {"print"}

# The code card
CX0, CY0, CX1, CY1 = 60, 620, 1020, 1260

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


def fade_color(color, amount):
    """amount=0 -> color is invisible (same as background), amount=1 -> full color."""
    return tuple(int(b + (c - b) * amount) for c, b in zip(color, BASE))


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


# ======================================================================
# 4. SCENES: each function draws ONE frame for time t (in seconds)
# ======================================================================
def scene_title(t):
    img, d = new_frame()
    # Each line fades in a little later than the one before
    a0, a1, a2 = clamp(t / 0.4), clamp((t - 0.5) / 0.4), clamp((t - 1.1) / 0.4)
    d.text((W // 2, 620), f"SWIFT TIP #{TIP['number']}", font=F_BADGE, fill=fade_color(GRAY, a0), anchor="mm")
    d.text((W // 2, 780), "Stop using", font=F_HEAD, fill=fade_color(WHITE, a0), anchor="mm")
    d.text((W // 2, 960), TIP["stop_using"], font=F_BIGCODE, fill=fade_color(RED, a1), anchor="mm")
    d.text((W // 2, 1150), "Here is the safe way", font=F_SUB, fill=fade_color(GRAY, a2), anchor="mm")
    return img


def scene_code(t, label, pill_color, heading, lines, box_text, box_color, type_start, type_end, box_at):
    """The Mistake and Fix scenes. Code is typed between type_start and type_end."""
    img, d = new_frame()

    # Pill (MISTAKE / FIX) and heading
    d.rounded_rectangle([W // 2 - 190, 290, W // 2 + 190, 385], radius=48, fill=pill_color)
    d.text((W // 2, 337), label, font=F_BADGE, fill=WHITE, anchor="mm")
    d.text((W // 2, 495), heading, font=F_HEAD, fill=WHITE, anchor="mm")

    # Code card with the three window dots
    d.rounded_rectangle([CX0, CY0, CX1, CY1], radius=36, fill=CARD)
    for i, dot in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = CX0 + 55 + i * 44
        d.ellipse([cx - 13, CY0 + 32, cx + 13, CY0 + 58], fill=dot)

    # Typing effect: work out how many characters are visible right now
    rows = [tokenize(line) for line in lines]
    total = sum(len(r) for r in rows)
    progress = clamp((t - type_start) / (type_end - type_start))
    visible = int(total * progress + 0.5)

    # Draw the visible characters one by one, remember where the last one ended
    x0, y0 = CX0 + 50, CY0 + 110
    cursor_pos, count = (x0, y0), 0
    for li, row in enumerate(rows):
        y = y0 + li * LH
        for ci, (ch, color) in enumerate(row):
            if count >= visible:
                break
            if ch != " ":
                d.text((x0 + ci * CW, y), ch, font=F_CODE, fill=color)
            cursor_pos = (x0 + (ci + 1) * CW, y)
            count += 1
        if count >= visible:
            break

    # Blinking cursor (always on while typing, blinks after)
    if t >= type_start - 0.3 and (progress < 1 or int(t * 2.5) % 2 == 0):
        cx, cy = cursor_pos
        d.rectangle([cx + 3, cy + 6, cx + 11, cy + 66], fill=(235, 238, 245))

    # Result box under the card (error in red, or success in green)
    if t >= box_at:
        a = clamp((t - box_at) / 0.25)
        d.rounded_rectangle([CX0, 1320, CX1, 1480], radius=30,
                            fill=fade_color(box_color, 0.2 * a), outline=fade_color(box_color, a), width=4)
        d.text((W // 2, 1400), box_text, font=F_SMALL, fill=fade_color(WHITE, a), anchor="mm")
    return img


def scene_outro(t):
    img, d = new_frame()
    a1, a2 = clamp(t / 0.4), clamp((t - 0.4) / 0.4)
    d.text((W // 2, 760), TIP["outro_line1"], font=F_HEAD, fill=fade_color(WHITE, a1), anchor="mm")
    d.text((W // 2, 880), TIP["outro_line2"], font=F_HEAD, fill=fade_color(C_TYPE, a1), anchor="mm")
    d.text((W // 2, 1040), TIP["outro_small"], font=F_SUB, fill=fade_color(GRAY, a2), anchor="mm")
    return img


# ======================================================================
# 5. BUILD THE LIST OF SCENES
# ======================================================================
def check_text_fits():
    """Stop early with a clear message if the text would run off the screen."""
    max_chars = int((CX1 - CX0 - 100) / CW)
    for key in ("mistake_code", "fix_code"):
        if len(TIP[key]) > 5:
            sys.exit(f"{key}: use at most 5 lines.")
        for line in TIP[key]:
            if len(line) > max_chars:
                sys.exit(f"{key}: this line is too long ({len(line)} chars, max {max_chars}):\n  {line}")


def code_scene_timing(lines):
    """Typing time depends on how much code there is."""
    total = sum(len(line) for line in lines)
    type_start = 0.5
    type_end = type_start + total / TYPING_SPEED
    box_at = type_end + 0.5
    duration = box_at + 1.6
    return type_start, type_end, box_at, duration


def build_scenes():
    scenes = [("1_title", 2.6, scene_title, 1.6)]   # (name, seconds, draw function, preview time)

    for name, label, pill, heading, lines, box_text, box_color in [
        ("2_mistake", "MISTAKE", (220, 60, 60), TIP["mistake_heading"], TIP["mistake_code"], TIP["mistake_error"], RED),
        ("3_fix", "FIX", (34, 160, 90), TIP["fix_heading"], TIP["fix_code"], TIP["fix_result"], GREEN),
    ]:
        ts, te, box_at, dur = code_scene_timing(lines)
        fn = partial(scene_code, label=label, pill_color=pill, heading=heading, lines=lines,
                     box_text=box_text, box_color=box_color, type_start=ts, type_end=te, box_at=box_at)
        scenes.append((name, dur, fn, box_at + 0.6))

    scenes.append(("4_outro", 2.2, scene_outro, 1.2))
    return scenes


# ======================================================================
# 6. RENDER: draw frames -> send to ffmpeg -> join the scenes
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
        # Fast check: save one picture per scene, no video
        for name, _, draw_frame, preview_t in scenes:
            draw_frame(preview_t).save(f"preview_{name}.png")
        print("Saved preview_*.png")
        return

    out_file = args[0] if args else "swift-tip.mp4"
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