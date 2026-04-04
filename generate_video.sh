#!/bin/bash
set -e  # stop on any error

PYTHON="python"  # change to "python3" or a venv path if needed

echo "[1/6] Generating audio..."
$PYTHON audio_local_api.py

echo "[2/6] Adjusting audio speed..."
$PYTHON audio_velocity.py

echo "[3/6] Splitting video..."
$PYTHON video_split.py

echo "[4/6] Cropping to 9:16..."
$PYTHON video_crop.py

echo "[5/6] Transcribing and generating subtitles..."
$PYTHON subtitles_transcription.py

echo "[6/6] Burning subtitles..."
$PYTHON subtitles_burn.py

echo ""
echo "Pipeline complete."
