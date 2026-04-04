import subprocess
import os

# -- Config --------------------------------------------------------------------
from config import ASS_FILE, VIDEO_16X9, VIDEO_9X16, FINAL_16X9, FINAL_9X16

ASS_INPUT = ASS_FILE
VIDEOS = [
    (os.path.splitext(VIDEO_16X9)[0] + "_temp_synced.mp4", FINAL_16X9),
    (os.path.splitext(VIDEO_9X16)[0] + "_temp_synced.mp4", FINAL_9X16),
]
# ------------------------------------------------------------------------------

for input_video, output_video in VIDEOS:
    print(f"Burning subtitles into {input_video}...")
    subprocess.run([
        "ffmpeg", "-y", "-i", input_video,
        "-vf", f"ass={ASS_INPUT},format=yuv420p",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy", output_video,
    ], check=True)
    print(f"Subtitles in {ASS_INPUT} burned in the video and saved as {output_video}")
