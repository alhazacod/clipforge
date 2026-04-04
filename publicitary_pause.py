import subprocess
import os

INPUT_VIDEO = "final_with_subs.mp4"
PAUSE_VIDEO = "publicitary_pause.mp4"
OUTPUT_VIDEO = "final_with_pause.mp4"

# Get duration of main video
duration = float(subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", INPUT_VIDEO
]).decode().strip())

half_duration = duration / 2

first_half = "first_half.mp4"
second_half = "second_half.mp4"

# Cut first half (re-encode to reset timestamps)
subprocess.run([
    "ffmpeg", "-y",
    "-i", INPUT_VIDEO,
    "-t", str(half_duration),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    first_half
], check=True)

# Cut second half (re-encode)
subprocess.run([
    "ffmpeg", "-y",
    "-i", INPUT_VIDEO,
    "-ss", str(half_duration),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    second_half
], check=True)

# Make concat list
concat_list = "videos_to_concat.txt"
with open(concat_list, "w") as f:
    f.write(f"file '{os.path.abspath(first_half)}'\n")
    f.write(f"file '{os.path.abspath(PAUSE_VIDEO)}'\n")
    f.write(f"file '{os.path.abspath(second_half)}'\n")

# Concat with re-encode to fix sync
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list,
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    OUTPUT_VIDEO
], check=True)

print(f"Publicitary pause added and saved as {OUTPUT_VIDEO}")
