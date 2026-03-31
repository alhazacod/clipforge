import os
import subprocess
from datetime import timedelta

def run_ffmpeg(cmd):
    """Run ffmpeg command and raise error if fails."""
    result = subprocess.run(cmd, check=True)
    if result.returncode != 0:
        print(result.stderr.decode())
        raise RuntimeError("ffmpeg command failed.")

def split_video(file_path, split_time):
    """Split a video into two parts at split_time."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    base_name, ext = os.path.splitext(file_path)
    first_part = f"{base_name}_part1{ext}"
    second_part = f"{base_name}_part2{ext}"
    name_first_split = first_part

    # 1️⃣ Save the first segment
    cmd1 = [
        "ffmpeg", "-y",
        "-i", file_path,
        "-t", split_time,
        "-c", "copy",
        first_part
    ]
    run_ffmpeg(cmd1)

    # 2️⃣ Save the rest of the video
    cmd2 = [
        "ffmpeg", "-y",
        "-i", file_path,
        "-ss", split_time,
        "-c", "copy",
        second_part
    ]
    run_ffmpeg(cmd2)

    # 3️⃣ Delete original file
    #os.remove(file_path)
    #print(f"Original file deleted: {file_path}")
    print(f"Saved:\n  {first_part}\n  {second_part}")


def crop_to_9_16(input_file):
    """Crop the video to 9:16 ratio, centered horizontally."""
    base_name, ext = os.path.splitext(input_file)
    cropped_file = f"{base_name}_9x16{ext}"

    # Crop height stays full, width is adjusted to match 9:16 ratio
    # crop=w:h:x:y where x = center offset
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0",
        "-c:a", "copy",
        cropped_file
    ]
    run_ffmpeg(cmd)
    print(f"Cropped 9:16 video saved as {cropped_file}")


def crop_and_scale_to_9_16(input_file):
    """Crop to 9:16 ratio and scale to 1080x1920."""
    base_name, ext = os.path.splitext(input_file)
    output_file = f"{base_name}_1080x1920{ext}"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920",
        "-c:a", "copy",
        output_file
    ]
    run_ffmpeg(cmd)
    print(f"Rescaled video saved as {output_file}")

def main():
    file_path = input("Enter video file path: ").strip()
    split_time = input("Enter split time (seconds or HH:MM:SS): ").strip()

    # Convert seconds to HH:MM:SS if user gave only seconds
    if split_time.isdigit():
        split_time = str(timedelta(seconds=int(split_time)))

    split_video(file_path, split_time)
    base_name, ext = os.path.splitext(file_path)
    first_part = f"{base_name}_part1{ext}"
    #crop_and_scale_to_9_16(first_part)
    crop_to_9_16(first_part)

if __name__ == "__main__":
    main()
