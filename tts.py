import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "Once upon a time there lived a man in a small village. He was very worried about his son. His son was lazy and careless. He never worked. He just wandered here and there in the village all day long.",
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)