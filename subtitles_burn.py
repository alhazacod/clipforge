import subprocess
import argparse

# -- Config --------------------------------------------------------------------
from config import ASS_FILE

parser = argparse.ArgumentParser()
parser.add_argument("--video_path", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

VIDEO_INPUT = args.video_path
VIDEO_OUTPUT = args.output
ASS_INPUT = ASS_FILE
# ------------------------------------------------------------------------------

print(f"Burning subtitles into {VIDEO_INPUT}...")
subprocess.run([
    "ffmpeg", "-y", "-i", VIDEO_INPUT,
    "-vf", f"ass={ASS_INPUT},format=yuv420p",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-c:a", "copy", VIDEO_OUTPUT,
], check=True)
print(f"Subtitles in {ASS_INPUT} burned in the video and saved as {VIDEO_OUTPUT}")
