import subprocess
import os

# ==== CONFIG ====
video_path = "video.mp4"
audio_path = "audio.wav"
temp_video = "temp_synced.mp4"
output_path = "final_with_subs.mp4"
# =================

# 1️⃣ Get audio duration
print("📏 Getting audio duration...")
duration = subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", audio_path
]).decode().strip()

duration = str(float(duration) + 2)

# 2️⃣ Mix original audio (half volume) with new audio (+25% volume)
print("🎬 Mixing original and new audio...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", video_path,       # input 0 (video + original audio)
    "-i", audio_path,       # input 1 (new audio)
    "-t", duration,
    "-filter_complex",
    "[0:a]volume=0.3[a0];[1:a]volume=1.5[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[mix]",
    "-map", "0:v",          # keep original video
    "-map", "[mix]",        # mixed audio
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    temp_video
], check=True)

print(f"✅ Mixed video saved as {temp_video}")
