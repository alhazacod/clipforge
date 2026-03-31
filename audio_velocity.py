import sys, subprocess, os

speed = 1.5
f = "output.wav"
name, ext = os.path.splitext(f)

subprocess.run([
    "ffmpeg","-i",f,
    "-filter:a",f"atempo={speed}",
    "-vn",f"{name}{int(speed*10)}{ext}"
])
