import os

files = ['videos_to_concat.txt', 
         'first_half.mp4',
         'second_half.mp4',
         'temp_synced.mp4']


for file_path in files:
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: {file_path}")
    else:
        print(f"[WARNING] file {file_path} doesn't exist.")
