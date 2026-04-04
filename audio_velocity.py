import subprocess
from config import AUDIO_FILE, AUDIO_SPEED

INPUT = AUDIO_FILE
SPEED = AUDIO_SPEED

subprocess.run([
    "ffmpeg","-i",INPUT,
    "-filter:a",f"atempo={SPEED}",
    "-vn",f"{INPUT}"
])

print(f"Video accelerated by x{SPEED:1.1f} and saved as {INPUT}")
