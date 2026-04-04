import subprocess
import os
from config import AUDIO_FILE, AUDIO_SPEED

INPUT = AUDIO_FILE
SPEED = AUDIO_SPEED

TEMP = "tmp_"+INPUT

subprocess.run([
    "ffmpeg", "-y", "-i", INPUT,
    "-filter:a", f"atempo={SPEED}",
    "-vn", TEMP
], check=True)

os.replace(TEMP, INPUT)  # overwrite original safely

print(f"Audio accelerated by x{SPEED:1.1f} and saved as {INPUT}")
