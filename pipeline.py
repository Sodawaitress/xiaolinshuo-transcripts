import sys
import subprocess
import json
from faster_whisper import WhisperModel
from pathlib import Path

OUTPUT_DIR = Path.home() / "podcast-transcripts"

def get_title(url, video_id):
    result = subprocess.run(
        ["python3", "-m", "yt_dlp", "--dump-json", "--no-download", url],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        print(f"警告：无法获取标题，使用 video_id 作为文件名")
        return video_id
    info = json.loads(result.stdout)
    title = info["title"]
    for char in '/\\:*?"<>|':
        title = title.replace(char, "_")
    return title

def get_video_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return url.split("v=")[-1].split("&")[0]

def run(url):
    video_id = get_video_id(url)
    title = get_title(url, video_id)
    print(f"标题：{title}")

    mp3_path = OUTPUT_DIR / f"{video_id}.mp3"
    transcript_path = OUTPUT_DIR / f"{title}_transcript.txt"

    print("下载中...")
    subprocess.run(["python3", "-m", "yt_dlp", "-x", "--audio-format", "mp3",
                    "-o", str(mp3_path), url])

    print("转录中...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(mp3_path), language="zh")

    with open(transcript_path, "w") as f:
        for seg in segments:
            f.write(seg.text + "\n")

    mp3_path.unlink()

    subprocess.run(["git", "-C", str(OUTPUT_DIR), "add", str(transcript_path)])
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "commit", "-m", f"transcript: {title}"])
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "push", "origin", "main"])

    print(f"完成！{title}")

for url in sys.argv[1:]:
    run(url)