from pytubefix import YouTube
import os
import subprocess
import csv
from datetime import datetime

def download_and_merge(url, itag, output_path="./video_format/"):
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(itag)
    progressive = stream.is_progressive

    filename = stream.default_filename
    base, ext = os.path.splitext(filename)
    ext = "." + stream.subtype

    output_file = os.path.join(output_path, filename)

    if progressive:
        print(f"Downloading combined stream: {stream.resolution} {stream.mime_type}")
        stream.download(output_path=output_path)
        print(f"Saved: {output_file}")
    else:
        # Adaptive: must download video + audio, then merge
        print(f"Downloading video-only: {stream.resolution} {stream.mime_type}")
        video_path = os.path.join(output_path, f"video_{itag}{ext}")
        stream.download(output_path=output_path, filename=os.path.basename(video_path))

        # Audio
        audio_stream = yt.streams.filter(only_audio=True, file_extension=stream.subtype).order_by("abr").desc().first()
        audio_ext = "." + audio_stream.subtype
        audio_path = os.path.join(output_path, f"audio_{audio_stream.itag}{audio_ext}")
        print(f"Downloading audio: {audio_stream.abr} {audio_stream.mime_type}")
        audio_stream.download(output_path=output_path, filename=os.path.basename(audio_path))

        # Merge via ffmpeg
        print("Merging video and audio with ffmpeg...")
        merged_path = os.path.join(output_path, "original_video.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c", "copy",
            merged_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(video_path)
        os.remove(audio_path)
        print(f"Merged file saved as: {merged_path}")

    # Log to CSV history
    date_str = datetime.now().strftime("%Y-%m-%d")
    history_exists = os.path.isfile("video_history.csv")
    with open("video_history.csv", "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not history_exists:
            writer.writerow(["Date", "Title", "URL"])
        writer.writerow([date_str, yt.title, url])

    print(f"Logged to video_history.csv: {date_str}, {yt.title}")

def main():
    url = input("Enter YouTube URL: ").strip()
    yt = YouTube(url)
    print(f"Title: {yt.title}\n")

    # List available streams
    streams = yt.streams
    print("Available streams:")
    options = []
    for s in streams:
        label = (f"[{'Prog' if s.is_progressive else 'Adapt'}] itag={s.itag} • "
                 f"{s.resolution or s.abr} • {s.mime_type}")
        print(label)
        options.append(s.itag)

    choice = input("\nEnter the itag of the desired stream: ").strip()
    if not choice.isdigit() or int(choice) not in options:
        print("Invalid choice. Aborting.")
        return

    download_and_merge(url, int(choice))

if __name__ == "__main__":
    main()
