import subprocess
 
# -- Config --------------------------------------------------------------------
INPUT  = "source_video/original_video.mp4"
OUTPUT = "source_video/original_video_formatted.mp4"
 
# H.264 + AAC — universally supported, TikTok/YouTube/Reels standard
# yuv420p   — maximum compatibility (required by most platforms)
# crf 18    — high quality (lower = better, 18-23 is the sweet spot)
# preset slow — better compression at same quality, worth it for a one-time format step
# 1080x1920 — vertical 9:16 format for short-form (change to 1920x1080 for landscape)
VIDEO_CODEC   = "libx264"
AUDIO_CODEC   = "aac"
RESOLUTION    = "1920:1080"   # width:height
CRF           = "18"
PRESET        = "fast"
AUDIO_BITRATE = "192k"
# ------------------------------------------------------------------------------
 
subprocess.run([
    "ffmpeg", "-y", "-i", INPUT,
    "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=decrease,"
           f"pad={RESOLUTION}:(ow-iw)/2:(oh-ih)/2,setsar=1",
    "-c:v", VIDEO_CODEC, "-crf", CRF, "-preset", PRESET, "-pix_fmt", "yuv420p",
    "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
    OUTPUT,
], check=True)
 
print(f"Video formated with resolution {RESOLUTION} and saved as {OUTPUT}")
