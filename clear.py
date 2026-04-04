import os

files = [
         'output.wav',
         'video.mp4',
         'video_temp_synced.mp4',
         'video_916.mp4',
         'video_916_temp_synced.mp4',
         'final_with_subs.mp4',
         'final_with_subs_with_pause.mp4',
         'final_with_subs_916.mp4',
         'final_with_subs_916_with_pause.mp4',
         'transcript.json',
         'subs.ass',
         #'script.txt',
         ]


for file_path in files:
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: {file_path}")
    else:
        print(f"[WARNING] file {file_path} doesn't exist.")
