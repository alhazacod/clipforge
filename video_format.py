import subprocess
import argparse
 
# -- Config --------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

INPUT = args.input
OUTPUT = args.output
 
# H.264 + AAC — universally supported, TikTok/YouTube/Reels standard
# yuv420p   — maximum compatibility (required by most platforms)
# crf 18    — high quality (lower = better, 18-23 is the sweet spot)
# preset slow — better compression at same quality, worth it for a one-time format step
# 1080x1920 — vertical 9:16 format for short-form (change to 1920x1080 for landscape)
VIDEO_CODEC   = "h264_nvenc"
AUDIO_CODEC   = "aac"
RESOLUTION    = "1920:1080"   # width:height
CRF           = "18"
PRESET        = "p5"
AUDIO_BITRATE = "192k"
# ------------------------------------------------------------------------------
 
subprocess.run([
    "ffmpeg", "-y", "-i", INPUT,
    "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=decrease,"
           f"pad={RESOLUTION}:(ow-iw)/2:(oh-ih)/2,setsar=1",
    "-c:v", "h264_nvenc",
    "-preset", "p5",
    "-cq", "18",
    "-pix_fmt", "yuv420p",
    "-g", "30", 
    "-keyint_min", "30",
    "-c:a", "aac", "-b:a", AUDIO_BITRATE,
    OUTPUT,
], check=True)
 
print(f"Video formated with resolution {RESOLUTION} and saved as {OUTPUT}")
