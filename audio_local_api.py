import os
import re
import time
import shutil
import requests
import subprocess

# -- Config --------------------------------------------------------------------
from config import KOKORO_IMAGE, KOKORO_URL, SCRIPT_FILE, AUDIO_FILE, AUDIO_TEMP_DIR, LOUDNESS_LUFS

INPUT_FILE  = SCRIPT_FILE
OUTPUT_FILE = AUDIO_FILE
TEMP_DIR    = AUDIO_TEMP_DIR
# ------------------------------------------------------------------------------
# Script format for IMPUT_FILE:
#   <voice name="em_santa">More text.</voice>   # Spanish Male Old
#   <voice name="em_alex">More text.</voice>    # Spanish Male Young
#   <voice name="ef_dora">More text.</voice>    # Spanish Female Young
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Podcast/radio filter chain (applied in order):
#   highpass      — cuts rumble and low-end noise below 80Hz
#   equalizer     — -3dB notch at 300Hz to reduce muddiness
#   equalizer     — +2dB presence boost at 3kHz for voice clarity
#   acompressor   — gentle 3:1 compression, evens out volume differences
#                   between speakers and sentences
#   loudnorm      — normalizes to target LUFS so it plays at consistent
#                   volume on all platforms (EBU R128 standard)
#   alimiter      — brickwall limiter at -1dBTP, prevents any clipping
# ------------------------------------------------------------------------------
FILTER_CHAIN = ",".join([
    "highpass=f=80",
    "equalizer=f=300:t=q:w=1:g=-3",
    "equalizer=f=3000:t=q:w=1:g=2",
    "acompressor=threshold=-18dB:ratio=3:attack=5:release=50:makeup=2dB",
    f"loudnorm=I={LOUDNESS_LUFS}:TP=-1.5:LRA=7",
    "alimiter=limit=0.891:level=disabled",
])
# ------------------------------------------------------------------------------

def start_kokoro():
    print("Starting Kokoro...")
    result = subprocess.run(
        ["docker", "run", "-d", "--rm", "-p", "8880:8880", KOKORO_IMAGE],
        capture_output=True, text=True, check=True
    )
    container_id = result.stdout.strip()
 
    # Wait until the API is ready
    for _ in range(900):
        try:
            if requests.get("http://localhost:8880/health", timeout=2).ok:
                print("Kokoro ready.")
                return container_id
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
 
    raise RuntimeError("Kokoro did not become ready in time.")

def stop_kokoro(container_id):
    print("Stopping Kokoro...")
    subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)

# -- Main ----------------------------------------------------------------------

container_id = start_kokoro()
 
try:
    with open(INPUT_FILE, encoding="utf-8") as f:
        content = f.read()

    blocks = re.findall(r'<voice\s+name="([^"]+)"\s*>\s*(.*?)\s*</voice>', content, re.DOTALL)
    if not blocks:
        raise ValueError('No <voice name="..."> tags found in input file.')

    os.makedirs(TEMP_DIR, exist_ok=True)
    wav_files = []

    for i, (voice_name, text) in enumerate(blocks, 1):
        path = f"{TEMP_DIR}/segment_{i:03d}.wav"
        print(f"[{i}/{len(blocks)}] {voice_name}")

        r = requests.post(KOKORO_URL, json={
            "input": text.strip(),
            "voice": voice_name,
            "response_format": "wav",
            "speed": 1.0,
        }, stream=True)
        r.raise_for_status()

        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)

        wav_files.append(path)

    concat_file = f"{TEMP_DIR}/concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in wav_files)

    # Merge all segments then apply mastering chain in one pass
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-af", FILTER_CHAIN,
        "-ar", "24000",        # keep original sample rate
        "-ac", "1",            # mono
        "-c:a", "pcm_s16le",   # clean WAV encoding
        OUTPUT_FILE,
    ], check=True)
    shutil.rmtree(TEMP_DIR)
    print(f"Audio succefully generated and saved as {OUTPUT_FILE}")

finally:
    stop_kokoro(container_id)

