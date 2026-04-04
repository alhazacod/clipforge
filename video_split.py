import subprocess
import wave
import os

# -- Config --------------------------------------------------------------------
AUDIO_FILE     = "output.wav"
FRAGMENT_FILE  = "source_video/splitting_fragment.mp4"
SOURCE_VIDEO   = "source_video/original_video_formatted.mp4"
OUTPUT_VIDEO   = "video.mp4"
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
    "-c", "copy", OUTPUT_VIDEO,
], check=True)

# Second part: the rest of the video
temp_fragment = FRAGMENT_FILE + ".tmp.mp4"
subprocess.run([
    "ffmpeg", "-y", "-i", input_video,
    "-ss", str(audio_duration),
    "-c", "copy", temp_fragment,
], check=True)
os.replace(temp_fragment, FRAGMENT_FILE)

print(f"Video clip  -> {OUTPUT_VIDEO} ({audio_duration:.2f}s)")
print(f"Next fragment -> {FRAGMENT_FILE}")
