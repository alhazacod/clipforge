# -- Shared config - edit here, applies to all scripts ------------------------

# Files
SCRIPT_FILE       = "script.txt"
AUDIO_FILE        = "output.wav"
TRANSCRIPT_FILE   = "transcript.json"
ASS_FILE          = "subs.ass"
VIDEO_16X9        = "video.mp4"
VIDEO_9X16        = "video_916.mp4"
FINAL_16X9        = "final_with_subs.mp4"
FINAL_9X16        = "final_with_subs_916.mp4"

# Source video paths
SOURCE_VIDEO      = "source_video/original_video_formatted.mp4"
FRAGMENT_FILE     = "source_video/splitting_fragment.mp4"

# TTS
KOKORO_IMAGE      = "ghcr.io/remsky/kokoro-fastapi-cpu:latest"
KOKORO_URL        = "http://localhost:8880/v1/audio/speech"
AUDIO_TEMP_DIR    = "temp_segments"

# Audio mastering
# Mastering target — podcast/radio standard
# -16 LUFS = podcast (Spotify, Apple Podcasts)
# -14 LUFS = YouTube / TikTok / social
LOUDNESS_LUFS     = -16
AUDIO_SPEED       = 1.3   # used by audio_velocity.py

# Subtitles
CHUNK_MAX_WORDS   = 4
CHUNK_MAX_DURATION= 1.5   # seconds
SUB_X             = 960 # ASS coordinate space is always 1920x1080 regardless of actual video resolution.
SUB_Y             = 540
HIGHLIGHT_COLOR   = r"\1c&H00FFFF&"   # BGR
WRITING_COLOR     = r"\1c&HFFFFFF&"   # BGR — white

# Subtitles uses BGR hex color codes (Blue, Green, Red).
#         HBBGGRR
# Red     H0000FF
# Blue    HFF0000
# Green   H00FF00
# Yellow  H00FFFF
# Pink    H7700FF
# White   HFFFFFF
