import subprocess
import os
import argparse

# -- Config --------------------------------------------------------------------
PAUSE_VIDEO = "publicitary_pause.mp4"
TEMP_DIR    = "temp_segments"
# ------------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--video_path", required=True)
args = parser.parse_args()

INPUT_VIDEO  = args.video_path
OUTPUT_VIDEO = os.path.splitext(INPUT_VIDEO)[0] + "_with_pause.mp4"

os.makedirs(TEMP_DIR, exist_ok=True)
first_half  = f"{TEMP_DIR}/first_half.mp4"
second_half = f"{TEMP_DIR}/second_half.mp4"
concat_list = f"{TEMP_DIR}/concat.txt"

duration = float(subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", INPUT_VIDEO
]).decode().strip())

half = duration / 2

subprocess.run([
    "ffmpeg", "-y", "-i", INPUT_VIDEO,
    "-t", str(half),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k", first_half,
], check=True)

subprocess.run([
    "ffmpeg", "-y", "-i", INPUT_VIDEO,
    "-ss", str(half),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k", second_half,
], check=True)

with open(concat_list, "w") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in [first_half, PAUSE_VIDEO, second_half])

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k", OUTPUT_VIDEO,
], check=True)

import shutil
shutil.rmtree(TEMP_DIR)

print(f"Publicity pause added for {INPUT_VIDEO} and saved as {OUTPUT_VIDEO}")
