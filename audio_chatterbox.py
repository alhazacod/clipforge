import os
import re
import shutil
import subprocess
import torch
import torchaudio as ta
from pathlib import Path
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# Optional imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: 'whisper' not installed. Fallback for short phrases disabled.")
try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    print("Warning: 'noisereduce' not installed. Final noise reduction skipped.")

torch.set_num_threads(os.cpu_count())
torch.set_num_interop_threads(os.cpu_count())

# -- Config --------------------------------------------------------------------
INPUT_FILE   = "script.txt"
OUTPUT_FILE  = "output.wav"
RAW_OUTPUT   = "output_raw.wav"
VOICES_DIR   = "voices"
TEMP_DIR     = "temp_segments"
LANGUAGE     = "es"               # language for all blocks
DEVICE       = "cpu"
MAX_CHARS    = 400
MIN_CHARS    = 40

CFG_WEIGHT   = 0.0                # 0.0 = most stable
EXAGGERATION = 0.3

# Short‑segment fallback
SHORT_TEXT_LEN = MIN_CHARS               # segments shorter than this are candidates
PADDING_PREFIX = "Mi amigo me dijo: "         # phrase in target language
PADDING_SUFFIX = " ¿entiendes lo que quizo decir?"   # optional suffix

# Silence trimming (unchanged)
SILENCE_DB       = 70
SILENCE_MIN_SECS = 0.08

# Final audio processing (ffmpeg filters)
# We'll apply: high‑pass filter, compressor, noise gate, and a subtle echo
AUDIO_FILTERS = (
    "loudnorm=I=-16:LRA=7:tp=-2,"
    "highpass=f=90,"
    "acompressor=threshold=-21dB:ratio=2:attack=50:release=80,"
    "loudnorm=I=-16:LRA=7:tp=-2"
)
# ------------------------------------------------------------------------------

# (load_voices, split_sentences, trim_silence functions unchanged)
def load_voices(directory):
    return {f.stem: str(f) for f in Path(directory).iterdir()
            if f.suffix.lower() in (".wav", ".mp3", ".flac")}

def split_sentences(text, max_chars=MAX_CHARS, min_chars=MIN_CHARS):
    raw = re.split(r'(?<=[.!?…])\s+', text.strip())
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
    merged = []
    for sent in sentences:
        if merged and len(merged[-1]) < min_chars:
            merged[-1] = merged[-1] + " " + sent
        else:
            merged.append(sent)
    return merged

def trim_silence(wav, sr, db=SILENCE_DB, min_secs=SILENCE_MIN_SECS):
    min_samples = int(min_secs * sr)
    threshold   = wav.abs().max() * (10 ** (-db / 20))
    active      = (wav.abs() > threshold).squeeze()
    indices     = active.nonzero(as_tuple=False).squeeze()
    if indices.numel() < 2:
        return wav
    start = max(0, indices[0].item() - min_samples)
    end   = min(wav.shape[-1], indices[-1].item() + min_samples)
    return wav[..., start:end]

def get_audio_duration(wav, sr):
    return wav.shape[-1] / sr

def extract_target_audio(padded_wav, padded_text, target_text, sr, model_whisper):
    """Use Whisper to find timestamps of target_text in padded audio, then extract."""
    # Save padded audio temporarily
    temp_padded = Path(TEMP_DIR) / "padded_temp.wav"
    ta.save(temp_padded, padded_wav, sr)
    # Transcribe with word timestamps
    result = model_whisper.transcribe(str(temp_padded), word_timestamps=True, language=LANGUAGE)
    # Find segments that contain target_text (ignore case)
    target_lower = target_text.lower()
    start_time = None
    end_time = None
    for seg in result["segments"]:
        seg_text = seg["text"].lower()
        if target_lower in seg_text:
            start_time = seg["start"]
            end_time = seg["end"]
            break
    if start_time is not None:
        # Extract portion
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        extracted = padded_wav[..., start_sample:end_sample]
        # Trim silence again
        extracted = trim_silence(extracted, sr)
        return extracted
    else:
        # Fallback: return original padded audio (should not happen)
        return padded_wav

# Main script
with open(INPUT_FILE, encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(r'<voice\s+name="([^"]+)"\s*>\s*(.*?)\s*</voice>', content, re.DOTALL)
if not blocks:
    raise ValueError('No <voice name="..."> tags found.')

voices = load_voices(VOICES_DIR)
if not voices:
    raise FileNotFoundError(f"No audio files found in '{VOICES_DIR}/'.")

for voice_name, _ in blocks:
    if voice_name not in voices:
        raise ValueError(f"Voice '{voice_name}' not found. Available: {list(voices)}")

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

# Initialize Whisper if needed
whisper_model = None
if WHISPER_AVAILABLE:
    whisper_model = whisper.load_model("tiny", device=DEVICE)

for i, (voice_name, text) in enumerate(blocks, 1):
    model.conds = voice_conds[voice_name]
    for sentence in split_sentences(text):
        seg += 1
        out_path = f"{TEMP_DIR}/segment_{seg:03d}.wav"
        print(f"[{i}/{len(blocks)}] {voice_name}: {sentence[:70]}{'...' if len(sentence) > 70 else ''}")

        # Generate audio normally
        wav = model.generate(
            sentence,
            language_id=LANGUAGE,
            cfg_weight=CFG_WEIGHT,
            exaggeration=EXAGGERATION,
        )
        wav = trim_silence(wav, model.sr)

        # Check if segment is short and potentially problematic
        if len(sentence) < SHORT_TEXT_LEN and WHISPER_AVAILABLE:
            duration = get_audio_duration(wav, model.sr)
            expected_duration = len(sentence) / 5.0  # rough chars per second
            if duration > 2.0 * expected_duration:   # too long => gibberish
                print(f"  Detected possible gibberish (duration {duration:.2f}s). Regenerating with padding...")
                # Build padded text
                padded_text = PADDING_PREFIX + sentence + PADDING_SUFFIX
                # Generate padded audio
                padded_wav = model.generate(
                    padded_text,
                    language_id=LANGUAGE,
                    cfg_weight=CFG_WEIGHT,
                    exaggeration=EXAGGERATION,
                )
                # Extract target part
                wav = extract_target_audio(padded_wav, padded_text, sentence, model.sr, whisper_model)

        ta.save(out_path, wav, model.sr)
        wav_files.append(out_path)

# Concatenate all segments
concat_file = f"{TEMP_DIR}/concat.txt"
with open(concat_file, "w", encoding="utf-8") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in wav_files)

# Save unfiltered concatenated audio
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", concat_file, "-c", "copy", RAW_OUTPUT,
], check=True)

# Apply filters to create final output
if NOISEREDUCE_AVAILABLE:
    # Optional: use noisereduce to remove background noise before ffmpeg filters
    # This adds a bit of time but improves quality
    print("Applying noise reduction...")
    import numpy as np
    import scipy.io.wavfile as wavfile
    # Load the unfiltered audio
    sr, data = wavfile.read(RAW_OUTPUT)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / 32768.0
    # Reduce noise (assuming first 0.5s is noise)
    data = nr.reduce_noise(y=data, sr=sr, prop_decrease=0.8)
    # Convert back to int16 and save temporary file
    data = (data * 32767).astype(np.int16)
    temp_denoised = f"{TEMP_DIR}/denoised.wav"
    wavfile.write(temp_denoised, sr, data)
    # Now apply ffmpeg filters
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_denoised,
        "-af", AUDIO_FILTERS, OUTPUT_FILE
    ], check=True)
else:
    # No noisereduce, just ffmpeg filters
    subprocess.run([
        "ffmpeg", "-y", "-i", RAW_OUTPUT,
        "-af", AUDIO_FILTERS, OUTPUT_FILE
    ], check=True)

# Clean up
shutil.rmtree(TEMP_DIR)
print(f"Done → {OUTPUT_FILE} (unfiltered saved as {RAW_OUTPUT})")
