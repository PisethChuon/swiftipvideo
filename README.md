# Swift Tip Video Maker

Makes a short vertical video (1080x1920, 9:16) for TikTok: a "Mistake vs Fix" Swift tip with a typing effect.
You do not need any footage. Everything is drawn with Python, so there is no copyright problem.

## What you get

A video of about 15 seconds with 4 scenes:

1. **Title**: "Swift tip #1, Stop using name!"
2. **Mistake**: the bad code types out, then a red error box appears
3. **Fix**: the safe code types out, then a green result box appears
4. **Outro**: "Follow for more Swift tips"

The video has no sound. You add a sound inside TikTok when you post.

## Requirements

- Python 3 
- Pillow (draws the pictures)
- ffmpeg (makes the video file)

## Setup (Mac, VS Code)

```bash
mkdir tiktok-videos && cd tiktok-videos
python3 -m venv .venv
source .venv/bin/activate
pip install pillow
brew install ffmpeg
```

Put `swift_tip_video.py` in this folder. In VS Code, press `Cmd+Shift+P`, choose
**Python: Select Interpreter**, and pick the one inside `.venv`.

Check that everything works:

```bash
ffmpeg -version
python -c "import PIL; print(PIL.__version__)"
```

## Run

```bash
python swift_tip_video.py --preview     # saves 4 pictures only (a few seconds)
python swift_tip_video.py               # makes swift-tip.mp4
python swift_tip_video.py my-tip.mp4    # choose your own file name
open swift-tip.mp4                      # play it on your Mac
```

Always run `--preview` first. Look at the pictures, then make the video.

## Make your own tip

Open `swift_tip_video.py` and change only the `TIP` section at the top.

| Field | What it is |
| --- | --- |
| `number` | The tip number on the title card |
| `stop_using` | The big red word on the title card |
| `mistake_heading` / `fix_heading` | Short title above each code card |
| `mistake_code` / `fix_code` | The code, one string per line |
| `mistake_error` | Text in the red box |
| `fix_result` | Text in the green box |
| `outro_line1`, `outro_line2`, `outro_small` | Text on the last card |

Rules so the text fits on a phone:

- At most **5 lines** of code
- About **24 characters** per line
- Short headings (about 14 characters)

The script checks this for you and stops with a clear message if a line is too long.

## How it works

Think of a flipbook. Python draws every page (a frame), and ffmpeg stacks the pages into a video.

The script has 7 parts:

1. `TIP`: your content
2. Settings: video size, colors, fonts
3. Helpers: fade colors, color the code words
4. Scenes: each function draws **one frame** for a given time `t`
5. Scene list: how long each scene is, and when the typing starts and ends
6. Render: sends the frames to ffmpeg, one video file per scene
7. Join: the scene files are joined without re-encoding (fast, no quality loss)

## Change the look

| I want to change | Where |
| --- | --- |
| Background, card, red, green | `BG_TOP`, `BG_BOT`, `CARD`, `RED`, `GREEN` |
| Code word colors | `C_TEXT`, `C_KEYWORD`, `C_TYPE`, `C_FUNC`, `C_COMMENT`, `C_STRING` |
| Which words get colored | `KEYWORDS`, `TYPES`, `FUNCS` |
| Code text size | `F_CODE` (54 is good, try 50 if lines look too wide) |
| Typing speed | `TYPING_SPEED` (characters per second) |
| Time to read the result | `duration = box_at + 1.6` in `code_scene_timing` |

## Posting on TikTok

- Upload the video, tap **Add sound**, and pick a sound from TikTok's own library.
- Quiet lo-fi or chill instrumental music fits coding videos. Avoid lyrics.
- Keep the music volume low, around 30 to 50 percent.
- Do not put a song from YouTube or Spotify into the video file. It can get muted or removed.
- Send the video to your phone and watch it there before posting.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ffmpeg: command not found` | Run `brew install ffmpeg`, then close and reopen VS Code |
| `No module named PIL` | Wrong Python. Activate the venv (`source .venv/bin/activate`) or select the interpreter again |
| `Font not found` | Add your font path inside `find_font(...)` in the script |
| `too long` message | Shorten the code line, or lower the size of `F_CODE` |
| Video plays on Mac but not on phone | Keep `-pix_fmt yuv420p` in the ffmpeg command, do not remove it |
| Video is not in the folder you expect | It is saved where you run the command |

## Notes

- Fonts: Menlo and Arial on Mac, Consolas and Arial on Windows, DejaVu on Linux.
  The first font that exists is used.
- I tested the script on Linux. On a Mac the letters look a little different because the fonts are different.
- Add `.venv` to `.gitignore` if you use git.
