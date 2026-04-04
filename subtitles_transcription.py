import whisper
import json
import re

# -- Config --------------------------------------------------------------------
AUDIO_INPUT      = "output.wav"
TRANSCRIPT_OUTPUT= "transcript.json"

CHUNK_MAX_WORDS    = 4
CHUNK_MAX_DURATION = 1.5   # seconds
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



print(f"Transcribing from {AUDIO_INPUT}...")
transcribe(AUDIO_INPUT, TRANSCRIPT_OUTPUT)
