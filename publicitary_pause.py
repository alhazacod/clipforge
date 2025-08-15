import subprocess
import os

main_video = "final_with_subs.mp4"
pause_video = "publicitary_pause.mp4"
output_video = "final_with_pause.mp4"

# Get duration of main video
duration = float(subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", main_video
]).decode().strip())

half_duration = duration / 2

first_half = "first_half.mp4"
second_half = "second_half.mp4"

# Cut first half (re-encode to reset timestamps)
subprocess.run([
    "ffmpeg", "-y",
    "-i", main_video,
    "-t", str(half_duration),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    first_half
], check=True)

# Cut second half (re-encode)
subprocess.run([
    "ffmpeg", "-y",
    "-i", main_video,
    "-ss", str(half_duration),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    second_half
], check=True)

# Make concat list
concat_list = "videos_to_concat.txt"
with open(concat_list, "w") as f:
    f.write(f"file '{os.path.abspath(first_half)}'\n")
    f.write(f"file '{os.path.abspath(pause_video)}'\n")
    f.write(f"file '{os.path.abspath(second_half)}'\n")

# Concat with re-encode to fix sync
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list,
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    output_video
], check=True)

print(f"✅ Final video saved as {output_video}")
