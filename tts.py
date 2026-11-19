import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "The boy nodded and went to the market with the watch. He showed the watch to different people. One man said it was worth 500 rupees. Another said 1,000. Someone else said 800. Everyone gave a different price. Some people even gave the same price, but no one agreed completely.",
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)