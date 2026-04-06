#!/bin/bash
set -e  # stop on any error

PYTHON="python"  

# echo "Formating the background video..."
# $PYTHON video_format.py --input "source_video/original_video.mp4" --output "source_video/original_video_formated.mp4"
#
# echo "[1/8] Generating audio..."
# $PYTHON audio_local_api.py
#
# echo "[2/8] Adjusting audio speed..."
# $PYTHON audio_velocity.py
#
# echo "[3/8] Transcribing and generating subtitles..."
# $PYTHON subtitles_transcription.py
#
# echo "[4/8] Splitting video..."
# $PYTHON video_split.py
#
# echo "[5/8] Cropping to 9:16..."
# $PYTHON video_crop.py
#
# echo "[6/8] merging video and audio..."
# $PYTHON video_audio_track.py --video_path video.mp4
# $PYTHON video_audio_track.py --video_path video_916.mp4
#
# echo "[7/8] Burning subtitles..."
# $PYTHON subtitles_burn.py --video_path video_temp_synced.mp4 --output final_with_subs.mp4
# $PYTHON subtitles_burn.py --video_path video_916_temp_synced.mp4 --output final_with_subs_916.mp4

echo "[8/8] Adding publicity pause..."
$PYTHON publicity_pause.py --video_path final_with_subs.mp4 --pause_path publicity_pause.mp4
$PYTHON publicity_pause.py --video_path final_with_subs_916.mp4 --pause_path publicity_pause_916.mp4

echo ""
echo "Pipeline complete."
