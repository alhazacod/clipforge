import subprocess
import wave
import os

# -- Config --------------------------------------------------------------------
from config import AUDIO_FILE, FRAGMENT_FILE, SOURCE_VIDEO, VIDEO_16X9

AUDIO_FILE    = AUDIO_FILE
FRAGMENT_FILE = FRAGMENT_FILE
SOURCE_VIDEO  = SOURCE_VIDEO
OUTPUT_VIDEO  = VIDEO_16X9
# ------------------------------------------------------------------------------

# Get audio duration in seconds
with wave.open(AUDIO_FILE) as wav:
    audio_duration = wav.getnframes() / wav.getframerate()

# On first run use the formatted source; afterwards use the rolling fragment
input_video = FRAGMENT_FILE if os.path.exists(FRAGMENT_FILE) else SOURCE_VIDEO

# First part: same length as the audio
subprocess.run([
    "ffmpeg", "-y", "-i", input_video,
    "-t", str(audio_duration),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    OUTPUT_VIDEO,
], check=True)

# Second part: the rest of the video
temp_fragment = FRAGMENT_FILE + ".tmp.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-ss", str(audio_duration),
    "-i", input_video,
    "-c", "copy",
    "-avoid_negative_ts", "1",
    temp_fragment,
], check=True)
os.replace(temp_fragment, FRAGMENT_FILE)

print(f"Video clip  -> {OUTPUT_VIDEO} ({audio_duration:.2f}s)")
print(f"Next fragment -> {FRAGMENT_FILE}")
