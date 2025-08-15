import subprocess
import whisper
import os
import torch

# ==== CONFIG ====
video_path = "video.mp4"
audio_path = "audio.wav"
temp_video = "temp_synced.mp4"
subs_path = "subs.srt"
ass_path = "subs.ass"
output_path = "final_with_subs.mp4"
# =================

device = "cpu"
print(f"📝 Transcribing on {device.upper()}...")
model = whisper.load_model("small", device=device)

result = model.transcribe(audio_path, fp16=False if device == "cpu" else True)

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


# 4️⃣ Create SRT with small chunks
print("✍️ Generating animated ASS subtitles...")

with open(ass_path, "w", encoding="utf-8") as f:
    # ASS header (defines styles)
    f.write("""[Script Info]
                ScriptType: v4.00+
                PlayResX: 1920
                PlayResY: 1080
                Timer: 100.0000

                [V4+ Styles]
                Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
                Style: Default,Roboto,68,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,200,200,0,0,1,4,0,5,0,0,40,0

                [Events]
                Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
                """)

# Config for fixed time chunks
    chunk_duration = 1.0  # seconds each subtitle stays on screen

    for seg in result["segments"]:
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_duration = seg_end - seg_start

        # Break segment into fixed time intervals
        current_time = seg_start
        words = seg["text"].strip().split()
        word_index = 0

        while current_time < seg_end and word_index < len(words):
            # Collect words that fit in the current chunk
            chunk_words = []
            chunk_start = current_time
            chunk_end = min(seg_end, chunk_start + chunk_duration)

            # Estimate how many words fit in this chunk based on average duration per word
            avg_word_time = seg_duration / len(words)
            words_in_chunk = max(1, round(chunk_duration / avg_word_time))

            chunk_words = words[word_index:word_index + words_in_chunk]
            word_index += words_in_chunk
            current_time = chunk_end

            # Offset so it appears slightly early
            offset = -0.03
            chunk_start = max(0, chunk_start + offset)
            chunk_end = max(0, chunk_end + offset)

            # ASS time formatter
            def ass_time(sec):
                h = int(sec // 3600)
                m = int((sec % 3600) // 60)
                s = int(sec % 60)
                cs = int((sec % 1) * 100)
                return f"{h}:{m:02}:{s:02}.{cs:02}"

            # Wrap text before animating
            chunk_text = " ".join(chunk_words)
            max_chars_per_line = 15
            words_in_line = chunk_text.split()
            lines = []
            line = []
            for w in words_in_line:
                if sum(len(x) for x in line) + len(w) + len(line) > max_chars_per_line:
                    lines.append(" ".join(line))
                    line = []
                line.append(w)
            if line:
                lines.append(" ".join(line))
            chunk_text = "\\N".join(lines)  # ASS line break

            # Animation timing
            grow_ms = 30  
            shrink_duration = 30
            shrink_start_ms = int((chunk_end - chunk_start) * 1000) - shrink_duration
            end_ms = int((chunk_end - chunk_start) * 1000)

            anim_text = (
                "{\\fs20\\t(0," + str(grow_ms) + ",\\fs48)"
                "\\t(" + str(shrink_start_ms) + "," + str(end_ms) + ",\\fs20)"
                "\\fad(0," + str(shrink_duration) + ")}" + chunk_text
            )

            f.write(
                f"Dialogue: 0,{ass_time(chunk_start)},{ass_time(chunk_end)},Default,,0,0,40,,{anim_text}\n"
            )


# 5️⃣ Burn subtitles in TikTok style, centered vertically
print("🔥 Burning subtitles into video...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", temp_video,
    "-vf", f"ass={ass_path}",
    "-c:v", "libx264",   # re-encode video so subs are burned in
    "-crf", "18",        # high quality
    "-preset", "fast",   # reasonable speed
    "-c:a", "copy",      # keep audio untouched
    output_path
], check=True)

# 6️⃣ Cleanup
#os.remove(temp_video)
print(f"✅ Done! Output saved to {output_path}")
