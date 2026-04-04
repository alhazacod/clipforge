import whisper
import subprocess
import json
import re

# -- Config --------------------------------------------------------------------
from config import (AUDIO_FILE, TRANSCRIPT_FILE, ASS_FILE,
                    CHUNK_MAX_WORDS, CHUNK_MAX_DURATION,
                    SUB_X, SUB_Y, HIGHLIGHT_COLOR, WRITING_COLOR)

AUDIO_INPUT       = AUDIO_FILE
TRANSCRIPT_OUTPUT = TRANSCRIPT_FILE
ASS_OUTPUT        = ASS_FILE

ASS_HEADER = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,90,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# ------------------------------------------------------------------------------


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


def transcribe(audio_input, transcript_path):
    model  = whisper.load_model("large-v3-turbo", device="cpu")
    result = model.transcribe(audio_input, fp16=False, word_timestamps=True)
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Transcript saved to {transcript_path}")


def ass_time(sec):
    h, rem = divmod(max(0, sec), 3600)
    m, s   = divmod(rem, 60)
    return f"{int(h)}:{int(m):02}:{int(s):02}.{int((s % 1) * 100):02}"


def chunk_to_ass_lines(chunk, next_chunk_start=None):
    """
    One dialogue line per word in the chunk, all sharing the same \pos()
    so the block never moves. The active word is red, all others white.
    """
    lines = []
    pos   = f"\\an5\\pos({SUB_X},{SUB_Y})"

    for i, active in enumerate(chunk):
        words_str = " ".join(
            f"{{{HIGHLIGHT_COLOR}}}{w['word']}{{{WRITING_COLOR}}}" if j == i else w["word"]
            for j, w in enumerate(chunk)
        )
        text  = "{" + pos + "}" + words_str
        start = ass_time(active["start"] - 0.05)

        if i + 1 < len(chunk):
            end = ass_time(chunk[i + 1]["start"] - 0.05)
        elif next_chunk_start is not None:
            end = ass_time(next_chunk_start - 0.05)
        else:
            end = ass_time(active["end"] + 0.05)

        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    return lines


def write_ass(result, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for seg in result["segments"]:
            if not seg.get("words"):
                continue
            chunks = build_chunks(seg["words"])
            for i, chunk in enumerate(chunks):
                next_start = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else None
                f.writelines(chunk_to_ass_lines(chunk, next_start))


def add_stylized_subtitles(transcript, ass_output):
    with open(transcript, "r", encoding="utf-8") as f:
        result = json.load(f)
    write_ass(result, ass_output)
    print(f"Transcript saved to {ass_output}")



# -- Main ----------------------------------------------------------------------

print(f"Transcribing from {AUDIO_INPUT}...")
transcribe(AUDIO_INPUT, TRANSCRIPT_OUTPUT)

print(f"Loading transcript from {TRANSCRIPT_OUTPUT}...")
add_stylized_subtitles(TRANSCRIPT_OUTPUT, ASS_OUTPUT)

