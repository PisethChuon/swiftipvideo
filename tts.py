import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "The old watch ticked softly on the table.",
    "Every tick was a moment that would never come back.",
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)