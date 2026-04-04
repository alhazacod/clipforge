import subprocess

# -- Config --------------------------------------------------------------------
from config import VIDEO_16X9, VIDEO_9X16

INPUT  = VIDEO_16X9
OUTPUT = VIDEO_9X16
# ------------------------------------------------------------------------------
# Crops to 9:16 by cutting the left and right sides, keeping center.
# crop=w:h:x:y — w/h = output size, x/y = top-left corner of the crop region
# ih*9/16 = the width that produces a 9:16 ratio from the original height
# (iw - ih*9/16)/2 = offset to center the crop horizontally
# ------------------------------------------------------------------------------

subprocess.run([
    "ffmpeg", "-y", "-i", INPUT,
    "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    OUTPUT,
], check=True)

print(f"Video cropped with aspect ratio 6:19 and saved as {OUTPUT}")
