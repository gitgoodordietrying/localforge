"""
MusicGen music generation tool.

Generates music using Facebook's MusicGen model via a local venv.
"""

import subprocess
from pathlib import Path

from engine.config import get_config

TOOL_NAME = "musicgen"
TOOL_ACTIONS = ["generate"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle MusicGen music generation."""
    config = get_config()
    musicgen_dir = inputs.get("musicgen_dir", config.service("musicgen").get("venv_dir"))

    if not musicgen_dir:
        raise RuntimeError(
            "MusicGen not configured. Set services.musicgen.venv_dir in localforge.yaml"
        )

    musicgen_dir = Path(musicgen_dir)
    venv_python = musicgen_dir / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = musicgen_dir / "venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = musicgen_dir / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = musicgen_dir / ".venv" / "bin" / "python"

    generate_script = musicgen_dir / "generate_music.py"

    if action == "generate":
        prompt = inputs.get("prompt", "")
        duration = int(inputs.get("duration", 30))
        model_size = inputs.get("model", "small")
        output_path = inputs.get("output")

        if not output_path:
            output_path = ctx.temp_dir / "generated_music.wav"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(venv_python), str(generate_script),
            prompt,
            "--duration", str(duration),
            "--model", model_size,
            "--output", str(output_path.parent),
            "--name", output_path.stem,
        ]
        if duration > 30:
            cmd.append("--extend")

        ctx.log(f"Generating {duration}s of music with MusicGen ({model_size})...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"MusicGen failed: {result.stderr}")

        generated_file = output_path.with_suffix(".wav")
        if not generated_file.exists():
            possible_files = list(output_path.parent.glob(f"{output_path.stem}*.wav"))
            if possible_files:
                generated_file = possible_files[0]

        return {"output": str(generated_file), "duration": duration, "prompt": prompt}

    raise ValueError(f"Unknown musicgen action: {action}")
