import subprocess
import argparse
import os
import shutil

# -- Config --------------------------------------------------------------------
TEMP_DIR = "temp_segments"
# ------------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--video_path", required=True)
parser.add_argument("--pause_path", required=True)
args = parser.parse_args()

INPUT_VIDEO  = args.video_path
PAUSE_VIDEO  = args.pause_path
OUTPUT_VIDEO = os.path.splitext(INPUT_VIDEO)[0] + "_with_pause.mp4"

os.makedirs(TEMP_DIR, exist_ok=True)

first_half   = f"{TEMP_DIR}/first_half.mp4"
second_half  = f"{TEMP_DIR}/second_half.mp4"
pause_normal = f"{TEMP_DIR}/pause_normalised.mp4"
concat_list  = f"{TEMP_DIR}/concat.txt"

# ------------------------------------------------------------------------------
# 1. Get main video properties (to re-encode pause video accordingly)
# ------------------------------------------------------------------------------
def get_stream_info(file_path, stream_type):
    """Return a dict with codec, sample_rate, channels, etc."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", stream_type,
        "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate,width,height,r_frame_rate",
        "-of", "default=noprint_wrappers=1", file_path
    ]
    out = subprocess.check_output(cmd).decode().strip()
    info = {}
    for line in out.split('\n'):
        if '=' in line:
            k, v = line.split('=')
            info[k] = v
    return info

video_info = get_stream_info(INPUT_VIDEO, "v:0")
audio_info = get_stream_info(INPUT_VIDEO, "a:0")

# ------------------------------------------------------------------------------
# 2. Normalise the pause video to match main video's streams
# ------------------------------------------------------------------------------
print("Normalising pause video...")
subprocess.run([
    "ffmpeg", "-y", "-i", PAUSE_VIDEO,
    "-vf", f"fps={video_info.get('r_frame_rate', '30')},scale={video_info.get('width', '1920')}:{video_info.get('height', '1080')},setsar=1",
    "-pix_fmt", "yuv420p",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", audio_info.get('bit_rate', '192k'),
    "-ar", audio_info.get('sample_rate', '44100'),
    "-ac", audio_info.get('channels', '2'),
    "-avoid_negative_ts", "make_zero",
    "-fflags", "+genpts",
    pause_normal
], check=True)

# ------------------------------------------------------------------------------
# 3. Split main video at half duration (timestamps start at 0)
# ------------------------------------------------------------------------------
duration = float(subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "csv=p=0", INPUT_VIDEO
]).decode().strip())

half = duration / 2

print(f"Splitting main video at {half:.2f}s...")
# First half (0 to half)
subprocess.run([
    "ffmpeg", "-y", "-i", INPUT_VIDEO,
    "-t", str(half),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-avoid_negative_ts", "make_zero",
    first_half
], check=True)

# Second half (half to end)
subprocess.run([
    "ffmpeg", "-y", "-ss", str(half), "-i", INPUT_VIDEO,
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-avoid_negative_ts", "make_zero",
    second_half
], check=True)

# ------------------------------------------------------------------------------
# 4. Concatenate with timestamp regeneration
# ------------------------------------------------------------------------------
with open(concat_list, "w") as f:
    for p in [first_half, pause_normal, second_half]:
        f.write(f"file '{os.path.abspath(p)}'\n")

print("Concatenating segments...")
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-fflags", "+genpts",      # regenerate timestamps
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    OUTPUT_VIDEO
], check=True)

# ------------------------------------------------------------------------------
# 5. Cleanup
# ------------------------------------------------------------------------------
shutil.rmtree(TEMP_DIR)
print(f"Publicity pause added -> {OUTPUT_VIDEO}")
