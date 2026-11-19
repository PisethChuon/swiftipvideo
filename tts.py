import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "The boy was confused. He didn't understand what his father really meant. Still, he obeyed and went to the market again. He asked the people he met, \"How much is the time inside this watch worth?\" People looked at him strangely. Some laughed at him. Some told him to go away. Some said, \"What a foolish question.\" The boy felt embarrassed and sad.",
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)