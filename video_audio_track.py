import subprocess
import os

# -- Config --------------------------------------------------------------------
VIDEO_PATH = "video.mp4"
AUDIO_PATH = "output.wav"
TEMP_VIDEO = "temp_synced.mp4"
# ------------------------------------------------------------------------------

# 1️⃣ Get audio duration
duration = subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", AUDIO_PATH
]).decode().strip()

duration = str(float(duration) + 2)

# 2️⃣ Mix original audio (half volume) with new audio (+25% volume)
print("Merging speech and video.")
subprocess.run([
    "ffmpeg", "-y",
    "-i", VIDEO_PATH,       # input 0 (video + original audio)
    "-i", AUDIO_PATH,       # input 1 (new audio)
    "-t", duration,
    "-filter_complex",
    "[0:a]volume=0.3[a0];[1:a]volume=1.7[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[mix]",
    "-map", "0:v",          # keep original video
    "-map", "[mix]",        # mixed audio
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    TEMP_VIDEO
], check=True)

print(f"Video and speech merged in a single video and saved as {TEMP_VIDEO}")
