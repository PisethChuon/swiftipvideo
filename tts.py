import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "The next day, the man called his son again. He asked him to bring the same watch. The boy brought it and gave it to his father. Then the father said, \"Now go to the market again. This time don't ask the price of the watch. Ask people the price of the time inside this watch.\"",
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)