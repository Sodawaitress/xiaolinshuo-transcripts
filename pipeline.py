import sys
import subprocess
from faster_whisper import WhisperModel
from pathlib import Path

OUTPUT_DIR = Path.home() / "podcast-transcripts"

def run(url):
    video_id = url.split("v=")[-1].split("&")[0]

    print("下载中...")
    subprocess.run(["python3", "-m", "yt_dlp", "-x", "--audio-format", "mp3",
                    "-o", str(OUTPUT_DIR / f"{video_id}.mp3"), url])

    print("转录中...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(OUTPUT_DIR / f"{video_id}.mp3"), language="zh")
    lines = list(segments)

    sub_file = OUTPUT_DIR / f"{video_id}_subtitles.txt"
    txt_file = OUTPUT_DIR / f"{video_id}_transcript.txt"

    with open(sub_file, "w") as f:
        for seg in lines:
            f.write(f"[{seg.start:.1f}s --> {seg.end:.1f}s] {seg.text}\n")

    with open(txt_file, "w") as f:
        for seg in lines:
            f.write(seg.text + "\n")

    # 自动提交到 git
    print("提交到 git...")
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "add", "."])
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "commit", "-m", f"transcript: {video_id}"])
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "push", "origin", "main"])

    # 删除 mp3
    mp3_file = OUTPUT_DIR / f"{video_id}.mp3"
    mp3_file.unlink()
    print(f"mp3 已删除，完成！{video_id}")

run(sys.argv[1])