
# video_duration_sum.py
from pathlib import Path
import subprocess
import shlex
import shutil
from typing import Iterable, Optional

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}

def iter_video_files(root: Path, recursive: bool = True) -> Iterable[Path]:
    files = (root.rglob("*") if recursive else root.glob("*"))
    for f in files:
        if f.is_file() and f.suffix.lower() in VIDEO_EXTS:
            yield f

def ffprobe_duration_seconds(path: Path, use_stream_duration: bool = False) -> Optional[float]:
    """
    Returns duration in seconds for a single file using ffprobe, or None on failure.
    - Container (format) duration: format=duration
    - Per-stream duration (first video stream): stream=duration with -select_streams v:0

    See FFmpeg docs and examples:
      ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 file
      ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 file
    """
    if not shutil.which("ffprobe"):
        # ffprobe not installed / not on PATH
        return None

    if use_stream_duration:
        cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=duration ' \
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"'
    else:
        cmd = f'ffprobe -v error -show_entries format=duration ' \
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"'

    try:
        out = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        text = out.decode().strip()
        return float(text) if text else None
    except Exception:
        return None

def sum_folder_durations_seconds(folder: str | Path,
                                 recursive: bool = True,
                                 use_stream_duration: bool = False) -> float:
    """
    Scans the folder for video files and returns the total duration in seconds.
    Set use_stream_duration=True to use per-stream duration instead of container duration.
    """
    root = Path(folder)
    total = 0.0
    for vf in iter_video_files(root, recursive=recursive):
        dur = ffprobe_duration_seconds(vf, use_stream_duration=use_stream_duration)
        if dur is not None:
            total += dur
        else:
            # Could log a warning here; skip files that fail probing
            pass
    return total

def report_folder_durations(folder: str | Path,
                            recursive: bool = True,
                            use_stream_duration: bool = False) -> None:
    """
    Prints a table and totals.
    """
    root = Path(folder)
    print("File\tDuration(s)")
    total = 0.0
    for vf in iter_video_files(root, recursive=recursive):
        dur = ffprobe_duration_seconds(vf, use_stream_duration=use_stream_duration)
        if dur is None:
            print(f"{vf}\tUNKNOWN")
        else:
            total += dur
            print(f"{vf}\t{dur:.3f}")
    print(f"\nTotal duration: {total:.3f} s ({total/60:.2f} min, {total/3600:.2f} h)")
