import subprocess
import whisper
import os
import torch
import re

# ==== CONFIG ====
video_path = "video.mp4"
audio_path = "output.wav"
temp_video = "temp_synced.mp4"
subs_path = "subs.srt"
ass_path = "subs.ass"
output_path = "final_with_subs.mp4"
# =================

device = "cpu"
print(f"📝 Transcribing on {device.upper()}...")

# Load Whisper model
model = whisper.load_model("large-v3", device=device)

# Transcribe with word-level timestamps
result = model.transcribe(audio_path, fp16=(device != "cpu"), word_timestamps=True)

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def create_tiktok_chunks(words, max_words=4, max_duration=1.5):
    """Create TikTok-style chunks with 3-5 words and natural phrasing"""
    chunks = []
    current_chunk = []
    current_start = None
    current_end = None
    
    for word_info in words:
        word = word_info['word'].strip()
        start = word_info['start']
        end = word_info['end']
        
        # Skip empty words
        if not word:
            continue
            
        # Clean the word (remove punctuation issues)
        word = re.sub(r'^[^\w]+', '', word)
        word = re.sub(r'[^\w]+$', '', word)
        
        if not word:
            continue
            
        if current_start is None:
            current_start = start
            
        # Check if we should break the chunk
        should_break = (
            len(current_chunk) >= max_words or
            (current_chunk and (end - current_start) > max_duration) or
            word in ['.', '!', '?', ',', ';', ':'] or
            (current_chunk and word[0].isupper() and len(current_chunk) >= 2)
        )
        
        if should_break and current_chunk:
            # Finalize current chunk
            chunks.append({
                'text': ' '.join(current_chunk),
                'start': current_start,
                'end': current_end
            })
            # Start new chunk
            current_chunk = [word]
            current_start = start
            current_end = end
        else:
            current_chunk.append(word)
            current_end = end
    
    # Add the last chunk if exists
    if current_chunk:
        chunks.append({
            'text': ' '.join(current_chunk),
            'start': current_start,
            'end': current_end
        })
    
    return chunks

print("✍️ Generating TikTok-style ASS subtitles...")

with open(ass_path, "w", encoding="utf-8") as f:
    # ASS header with TikTok-style formatting
    f.write("""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,100,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,5,0,0,60,1
Style: Outline,Arial Black,100,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,5,0,0,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")

    for seg in result["segments"]:
        if not seg.get('words'):
            continue
            
        words = seg['words']
        chunks = create_tiktok_chunks(words)
        
        for chunk in chunks:
            chunk_start = chunk['start']
            chunk_end = chunk['end']
            chunk_text = chunk['text'].strip()
            
            # Skip empty chunks
            if not chunk_text:
                continue
                
            # Add slight padding for better readability
            duration = chunk_end - chunk_start
            chunk_start = max(0, chunk_start - 0.05)  # Reduced from 0.1 to 0.05
            chunk_end = chunk_end + 0.05  # Reduced from 0.1 to 0.05
            
            def ass_time(sec):
                h = int(sec // 3600)
                m = int((sec % 3600) // 60)
                s = int(sec % 60)
                cs = int((sec % 1) * 100)
                return f"{h}:{m:02}:{s:02}.{cs:02}"
            
            # TikTok-style text formatting - break into 2 lines max
            words_in_chunk = chunk_text.split()
            if len(words_in_chunk) <= 2:
                # Single line for short chunks
                display_text = chunk_text
            else:
                # Split into 2 lines for longer chunks
                split_point = len(words_in_chunk) // 2
                line1 = ' '.join(words_in_chunk[:split_point])
                line2 = ' '.join(words_in_chunk[split_point:])
                display_text = f"{line1}\\N{line2}"
            
            # Faster TikTok-style animation
            total_duration = chunk_end - chunk_start
            fade_in = 20  # Reduced from 100 to 20
            fade_out = 20  # Reduced from 100 to 20
            
            # Much faster animation timing
            grow_ms = 20  # Reduced from 30 to 20
            shrink_duration = 20  # Reduced from 30 to 20
            shrink_start_ms = int((chunk_end - chunk_start) * 1000) - shrink_duration
            end_ms = int((chunk_end - chunk_start) * 1000)
            
            # Main subtitle with faster pop effect
            anim_text = (
                "{\\fs20\\t(0," + str(grow_ms) + ",\\fs48)"
                "\\t(" + str(shrink_start_ms) + "," + str(end_ms) + ",\\fs20)"
                "\\fad(" + str(fade_in) + "," + str(fade_out) + ")}" + display_text
            )
            
            # Write main subtitle
            f.write(
                f"Dialogue: 0,{ass_time(chunk_start)},{ass_time(chunk_end)},Default,,0,0,40,,{anim_text}\n"
            )
            
            # Optional: Add outline version for better readability
            outline_anim = (
                "{\\fs20\\t(0," + str(grow_ms) + ",\\fs48)"
                "\\t(" + str(shrink_start_ms) + "," + str(end_ms) + ",\\fs20)"
                "\\fad(" + str(fade_in) + "," + str(fade_out) + ")}" + display_text
            )
            f.write(
                f"Dialogue: 0,{ass_time(chunk_start)},{ass_time(chunk_end)},Outline,,0,0,40,,{outline_anim}\n"
            )

print("🔥 Burning TikTok-style subtitles into video...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", temp_video,
    "-vf", f"ass={ass_path},format=yuv420p",
    "-c:v", "libx264",
    "-crf", "18",
    "-preset", "fast",
    "-c:a", "copy",
    output_path
], check=True)

print(f"✅ Done! TikTok-style video saved to {output_path}")
