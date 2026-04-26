import sys
import subprocess
import json
from faster_whisper import WhisperModel
from pathlib import Path

OUTPUT_DIR = Path.home() / "podcast-transcripts"

def get_title(url):
    result = subprocess.run(
        ["python3", "-m", "yt_dlp", "--dump-json", "--no-download", url],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    # 去掉文件名不能用的特殊字符
    title = info["title"]
    for char in '/\\:*?"<>|':
        title = title.replace(char, "_")
    return title

def run(url):
    video_id = url.split("v=")[-1].split("&")[0]
    title = get_title(url)
    print(f"标题：{title}")

    print("下载中...")
    subprocess.run(["python3", "-m", "yt_dlp", "-x", "--audio-format", "mp3",
                    "-o", str(OUTPUT_DIR / f"{video_id}.mp3"), url])

    print("转录中...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(OUTPUT_DIR / f"{video_id}.mp3"), language="zh")
    lines = list(segments)

    with open(OUTPUT_DIR / f"{title}_subtitles.txt", "w") as f:
        for seg in lines:
            f.write(f"[{seg.start:.1f}s --> {seg.end:.1f}s] {seg.text}\n")

    with open(OUTPUT_DIR / f"{title}_transcript.txt", "w") as f:
        for seg in lines:
            f.write(seg.text + "\n")

    subprocess.run(["git", "-C", str(OUTPUT_DIR), "add", "."])
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "commit", "-m", f"transcript: {title}"])
    subprocess.run(["git", "-C", str(OUTPUT_DIR), "push", "origin", "main"])

    (OUTPUT_DIR / f"{video_id}.mp3").unlink()
    print(f"完成！{title}")

for url in sys.argv[1:]:
    run(url)