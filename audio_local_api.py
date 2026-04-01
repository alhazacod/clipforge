import os
import re
import requests
import subprocess

# --- CONFIG ---
KOKORO_URL = "http://localhost:8880/v1/audio/speech"
INPUT_FILE = "script.txt"
OUTPUT_FILE = "output.wav"
TEMP_DIR = "temp_segments"
# ---------------

# Create temp dir if not exists
os.makedirs(TEMP_DIR, exist_ok=True)

# 1. Read the input text
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# 2. Extract <voice name="..."> blocks
voice_blocks = re.findall(r'<voice\s+name="([^"]+)">\s*(.*?)\s*</voice>', content, re.DOTALL)

if not voice_blocks:
    raise ValueError('No <voice name="..."> tags found in the input text.')

wav_files = []

# 3. Generate audio for each block
for i, (voice_name, text) in enumerate(voice_blocks, start=1):
    text = text.strip()
    output_path = f"{TEMP_DIR}/segment_{i:03d}.wav"
    wav_files.append(output_path)

    print(f"[{i}/{len(voice_blocks)}] Generating voice '{voice_name}'...")

    payload = {
        "input": text,
        "voice": voice_name,
        "response_format": "wav",
        "velocity": 1.0
    }

    response = requests.post(KOKORO_URL, json=payload, stream=True)
    if response.status_code != 200:
        print(f" Error {response.status_code}: {response.text}")
        continue

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                f.write(chunk)

# 4. Create concat list for ffmpeg
concat_file = f"{TEMP_DIR}/concat.txt"
with open(concat_file, "w", encoding="utf-8") as f:
    for wav in wav_files:
        # ffmpeg requires absolute paths or relative paths with safe=0
        f.write(f"file '{os.path.abspath(wav)}'\n")

# 5. Merge with ffmpeg
print(f"\n Combining {len(wav_files)} segments into {OUTPUT_FILE}...")
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_file,
    "-c", "copy",
    OUTPUT_FILE
], check=True)

print(f" Done! Saved combined audio as '{OUTPUT_FILE}'")
