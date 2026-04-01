import subprocess
import whisper
import json
import os
import re

# ── Config ────────────────────────────────────────────────────────────────────
VIDEO_INPUT      = "temp_synced.mp4"
AUDIO_INPUT      = "output.wav"
TRANSCRIPT_CACHE = "transcript.json"
ASS_OUTPUT       = "subs.ass"
VIDEO_OUTPUT     = "final_with_subs.mp4"

CHUNK_MAX_WORDS    = 4
CHUNK_MAX_DURATION = 1.5   # seconds

# ASS coordinate space is always 1920x1080 regardless of actual video resolution.
# Adjust SUB_Y to move subtitles vertically: 540 = center, 960 = near bottom.
SUB_X = 960
SUB_Y = 600
# ─────────────────────────────────────────────────────────────────────────────

ASS_HEADER = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,90,&H000000FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# PrimaryColour = white, SecondaryColour = red (BGR) — \k highlights in red


def ass_time(sec):
    h, rem = divmod(max(0, sec), 3600)
    m, s   = divmod(rem, 60)
    return f"{int(h)}:{int(m):02}:{int(s):02}.{int((s % 1) * 100):02}"


def clean_word(raw):
    return re.sub(r"(^[^\w]+|[^\w]+$)", "", raw.strip())


def build_chunks(words):
    """Group Whisper word-level entries into short display chunks."""
    chunks, current = [], []

    for w in words:
        word = clean_word(w["word"])
        if not word:
            continue

        too_long = len(current) >= CHUNK_MAX_WORDS
        too_slow = current and (w["start"] - current[0]["start"]) > CHUNK_MAX_DURATION
        new_sent = current and word[0].isupper() and len(current) >= 2

        if current and (too_long or too_slow or new_sent):
            chunks.append(current)
            current = []

        current.append({"word": word, "start": w["start"], "end": w["end"]})

    if current:
        chunks.append(current)

    return chunks


def chunk_to_ass_line(chunk, next_start=None):
    """
    One ASS dialogue line for the full chunk using \\k karaoke tags.
    \\an2\\pos() absolutely pins the bottom-center anchor so the baseline
    never moves regardless of chunk length or line wrapping.
    next_start clamps the end so adjacent chunks never overlap.
    """
    end_s = chunk[-1]["end"] + 0.05
    if next_start is not None:
        end_s = min(end_s, next_start - 0.05)
    parts = [f"{{\\k{int((w['end'] - w['start']) * 100)}}}{w['word']}" for w in chunk]
    text  = "{" + f"\\an2\\pos({SUB_X},{SUB_Y})" + "}" + " ".join(parts)
    return f"Dialogue: 0,{ass_time(chunk[0]['start'] - 0.05)},{ass_time(end_s)},Default,,0,0,0,,{text}\n"


def write_ass(result, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for seg in result["segments"]:
            if not seg.get("words"):
                continue
            chunks = build_chunks(seg["words"])
            for i, chunk in enumerate(chunks):
                next_start = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else None
                f.write(chunk_to_ass_line(chunk, next_start))


# ── Main ──────────────────────────────────────────────────────────────────────
if os.path.exists(TRANSCRIPT_CACHE):
    print(f"Loading transcript from {TRANSCRIPT_CACHE}...")
    with open(TRANSCRIPT_CACHE, "r", encoding="utf-8") as f:
        result = json.load(f)
else:
    print("Transcribing...")
    model  = whisper.load_model("large-v3", device="cpu")
    result = model.transcribe(AUDIO_INPUT, fp16=False, word_timestamps=True)
    with open(TRANSCRIPT_CACHE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Transcript saved to {TRANSCRIPT_CACHE}")

write_ass(result, ASS_OUTPUT)

print("Burning subtitles...")
subprocess.run([
    "ffmpeg", "-y", "-i", VIDEO_INPUT,
    "-vf", f"ass={ASS_OUTPUT},format=yuv420p",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-c:a", "copy", VIDEO_OUTPUT,
], check=True)

print(f"Done → {VIDEO_OUTPUT}")
