import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "Finally, he stopped at a small shop where an old man was working. The old shopkeeper was busy repairing watches. When the boy asked him the same question, the old man paused his work. He looked at the boy with a kind smile. He understood what the boy was trying to ask.",
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)