import sys, subprocess, os

SPEED = 1.5
INPUT = "output.wav"
name, ext = os.path.splitext(INPUT)

subprocess.run([
    "ffmpeg","-i",INPUT,
    "-filter:a",f"atempo={SPEED}",
    "-vn",f"{name}{int(SPEED*10)}{ext}"
])

print(f"Video accelerated by x{SPEED:1.1f} and saved as {name}{int(SPEED*10)}{ext}")
