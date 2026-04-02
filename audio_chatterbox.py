import os
import re
import shutil
import subprocess
import torch
import torchaudio as ta
from pathlib import Path
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

torch.set_num_threads(os.cpu_count())
torch.set_num_interop_threads(os.cpu_count())

# ── Config --------------------------------------------------------------------
INPUT_FILE       = "script.txt"
OUTPUT_FILE      = "output.wav"
RAW_OUTPUT       = "output_raw.wav"
VOICES_DIR       = "voices"       # WAV/MP3 files here — filename = voice name
TEMP_DIR         = "temp_segments"
LANGUAGE         = "es"           # language for all blocks: en, es, fr, de, etc.
DEVICE           = "cpu"
MAX_CHARS        = 200   # split chunks above this length
MIN_CHARS        = 40    # merge chunks below this length into the next one
PAD              = " Bien." # fragment to add to short text so it wont generate gibberish
SHORT_THRESHOLD  = 25 # how short is short the gibberish fix

# CFG_WEIGHT: how closely to follow the reference voice (0.0–1.0)
# 0.0 = ignore reference voice style entirely (most stable, fewest loops)
# 0.5 = default. raise if voice sounds too generic
CFG_WEIGHT   = 0.0

# EXAGGERATION: emotional intensity (0.0–2.0)
EXAGGERATION = 0.3

# Silence trimming
SILENCE_DB       = 50
SILENCE_MIN_SECS = 0.08
# ------------------------------------------------------------------------------
# Script format:
#   <voice name="narrator">Text here.</voice>
#   <voice name="host">More text.</voice>
# ------------------------------------------------------------------------------

def load_voices(directory):
    return {
        f.stem: str(f)
        for f in Path(directory).iterdir()
        if f.suffix.lower() in (".wav", ".mp3", ".flac")
    }

def split_sentences(text, max_chars=MAX_CHARS, min_chars=MIN_CHARS):
    """
    Split text at sentence boundaries, then merge any fragment shorter than
    min_chars into its neighbour so single-word generations are avoided.
    """
    raw = re.split(r'(?<=[.!?…])\s+', text.strip())
    # First pass: split any sentence that exceeds max_chars on commas/semicolons
    sentences = []
    for sent in raw:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) <= max_chars:
            sentences.append(sent)
        else:
            parts = re.split(r'(?<=[,;])\s+', sent)
            current = ""
            for part in parts:
                if current and len(current) + len(part) + 1 > max_chars:
                    sentences.append(current.strip())
                    current = part
                else:
                    current = (current + " " + part).strip() if current else part
            if current:
                sentences.append(current.strip())

    # Second pass: merge short fragments forward so nothing tiny generates alone
    merged = []
    for sent in sentences:
        if merged and len(merged[-1]) < min_chars:
            merged[-1] = merged[-1] + " " + sent
        else:
            merged.append(sent)

    return merged

def trim_silence(wav, sr, db=SILENCE_DB, min_secs=SILENCE_MIN_SECS):
    """Trim leading and trailing silence from a waveform tensor."""
    min_samples = int(min_secs * sr)
    threshold   = wav.abs().max() * (10 ** (-db / 20))
    active      = (wav.abs() > threshold).squeeze()
    indices     = active.nonzero(as_tuple=False).squeeze()
    if indices.numel() < 2:
        return wav
    start = max(0, indices[0].item() - min_samples)
    end   = min(wav.shape[-1], indices[-1].item() + min_samples)
    return wav[..., start:end]

def stabilize_text(text):
    if len(text) < SHORT_THRESHOLD:
        return text + PAD
    return text

def remove_tail(wav, sr):
    # remove last ~200ms (cuts padding audio)
    cut = int(0.9 * sr)
    print(f"sr is: {sr}")
    print(f"removing tail of {cut} of duration.")
    return wav[..., :-cut] if wav.shape[-1] > cut else wav
def remove_tail_new(wav, sr):
    energy = wav.abs()
    threshold = energy.max() * 0.1

    idx = (energy > threshold).nonzero(as_tuple=False)
    if idx.numel() < 2:
        return wav

    end = idx[-1].item()
    return wav[..., :end]

def check_voices_availability(blocks, voices_dir = VOICES_DIR):
    # checks if the voices for the different block are in the voices folder.
    if not blocks:
        raise ValueError('No <voice name="..."> tags found in input file.')

    voices = load_voices(voices_dir)
    if not voices:
        raise FileNotFoundError(f"No audio files found in '{voices_dir}/' folder.")

    for voice_name, _ in blocks:
        if voice_name not in voices:
            raise ValueError(f"Voice '{voice_name}' not found in '{voices_dir}/'. Available: {list(voices)}")

with open(INPUT_FILE, encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(r'<voice\s+name="([^"]+)"\s*>\s*(.*?)\s*</voice>', content, re.DOTALL)

voices = load_voices(VOICES_DIR)
check_voices_availability(blocks, VOICES_DIR)

print("Loading Chatterbox Multilingual...")
model = ChatterboxMultilingualTTS.from_pretrained(device=DEVICE)

print("Encoding voices...")
voice_conds = {}
for name in {name for name, _ in blocks}:
    print(f"  {name}")
    model.prepare_conditionals(voices[name])
    voice_conds[name] = model.conds

os.makedirs(TEMP_DIR, exist_ok=True)
wav_files = []
seg = 0

for i, (voice_name, text) in enumerate(blocks, 1):
    model.conds = voice_conds[voice_name]
    for sentence in split_sentences(text):
        seg += 1
        out_path = f"{TEMP_DIR}/segment_{seg:03d}.wav"
        print(f"[{i}/{len(blocks)}] {voice_name}: {sentence[:70]}{'...' if len(sentence) > 70 else ''}")


        text_in = stabilize_text(sentence)

        wav = model.generate(
            text_in,
            language_id=LANGUAGE,
            cfg_weight=CFG_WEIGHT,
            exaggeration=EXAGGERATION,
        )

        wav = trim_silence(wav, model.sr)

        if len(sentence) < SHORT_THRESHOLD:
            wav = remove_tail(wav, model.sr)
        ta.save(out_path, wav, model.sr)
        wav_files.append(out_path)

concat_file = f"{TEMP_DIR}/concat.txt"
with open(concat_file, "w", encoding="utf-8") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in wav_files)

# Save raw first

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", concat_file, "-c", "copy", RAW_OUTPUT,
], check=True)

# Apply simple radio/podcast chain
subprocess.run([
    "ffmpeg", "-y", "-i", RAW_OUTPUT,
    "-af",
    "highpass=f=80, lowpass=f=8000, "
    "afftdn=nf=-25, "          # noise reduction
    "acompressor=threshold=-18dB:ratio=2:attack=5:release=50, "
    "loudnorm",
    OUTPUT_FILE
], check=True)

shutil.rmtree(TEMP_DIR)
print(f"Done → {OUTPUT_FILE}")
