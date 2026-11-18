import numpy as np
import soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")  # "a" = American English

scenes = [
    "A boy always put off his tasks until tomorrow.",
    "One day, an old gardener handed him a handful of seeds and said",
    "Plant them before sundown, and they will grow into shade trees.",
    "Wait until morning, and the birds will take them. The boy stopped to play first",
    "Thinking he still had plenty of daylight.",
    "When he finally reached the garden",
    "The sun had set and the seeds were gone.",
    "The secret isn't having more hours—it's acting while the light is still up."
]

for n, text in enumerate(scenes, 1):
    chunks = [audio.numpy() for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    sf.write(f"scene_{n:02d}.wav", np.concatenate(chunks), 24000)
    print("saved", n)