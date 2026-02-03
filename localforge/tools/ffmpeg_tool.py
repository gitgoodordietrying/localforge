"""
FFmpeg audio/video processing tool.

Provides convert, normalize, loop, trim, and duration operations.
"""

import subprocess
from pathlib import Path

from ..engine.config import get_config

TOOL_NAME = "ffmpeg"
TOOL_ACTIONS = ["convert", "normalize", "loop", "trim", "get_duration"]


def _ffmpeg_path() -> str:
    return get_config().ffmpeg_path


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle FFmpeg audio/video processing."""
    ffmpeg = _ffmpeg_path()

    if action == "convert":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [ffmpeg, "-y", "-i", str(input_path), str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg convert failed: {result.stderr}")
        return {"output": str(output_path)}

    elif action == "normalize":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output",
                                       input_path.with_stem(input_path.stem + "_normalized")))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            ffmpeg, "-y", "-i", str(input_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg normalize failed: {result.stderr}")
        return {"output": str(output_path)}

    elif action == "loop":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output"))
        loop_count = int(inputs.get("count", 2))
        crossfade = float(inputs.get("crossfade", 0.5))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filter_complex = f"acrossfade=d={crossfade}:c1=tri:c2=tri"
        cmd = [
            ffmpeg, "-y",
            "-stream_loop", str(loop_count - 1),
            "-i", str(input_path),
            "-af", filter_complex,
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg loop failed: {result.stderr}")
        return {"output": str(output_path)}

    elif action == "trim":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output"))
        start = inputs.get("start", 0)
        duration = inputs.get("duration")
        end = inputs.get("end")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [ffmpeg, "-y", "-i", str(input_path), "-ss", str(start)]
        if duration:
            cmd.extend(["-t", str(duration)])
        elif end:
            cmd.extend(["-to", str(end)])
        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg trim failed: {result.stderr}")
        return {"output": str(output_path)}

    elif action == "get_duration":
        input_path = Path(inputs.get("input"))
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"FFprobe failed: {result.stderr}")
        duration = float(result.stdout.strip())
        return {"duration": duration}

    raise ValueError(f"Unknown ffmpeg action: {action}")
