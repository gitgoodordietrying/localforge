"""
ACE-Step music generation tool.

Generates music with lyrics using the ACE-Step model via a local venv.
"""

import subprocess
from pathlib import Path

from ..engine.config import get_config

TOOL_NAME = "acestep"
TOOL_ACTIONS = ["generate"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle ACE-Step music generation."""
    config = get_config()
    acestep_dir = inputs.get("acestep_dir", config.service("acestep").get("venv_dir"))

    if not acestep_dir:
        raise RuntimeError(
            "ACE-Step not configured. Set services.acestep.venv_dir in localforge.yaml"
        )

    acestep_dir = Path(acestep_dir)
    venv_python = acestep_dir / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = acestep_dir / "venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = acestep_dir / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = acestep_dir / ".venv" / "bin" / "python"

    generate_script = acestep_dir / "generate.py"

    if action == "generate":
        prompt = inputs.get("prompt", "")
        lyrics = inputs.get("lyrics", "")
        duration = int(inputs.get("duration", 60))
        output_path = inputs.get("output")
        steps = int(inputs.get("steps", 27))

        if not output_path:
            output_path = ctx.temp_dir / "acestep_music.wav"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(venv_python), str(generate_script),
            prompt,
            "--duration", str(duration),
            "--output", str(output_path),
            "--steps", str(steps),
        ]
        if lyrics:
            cmd.extend(["--lyrics", lyrics])

        ctx.log(f"Generating {duration}s of music with ACE-Step...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)

        if result.returncode != 0:
            raise RuntimeError(f"ACE-Step failed: {result.stderr}")

        return {"output": str(output_path), "duration": duration, "prompt": prompt}

    raise ValueError(f"Unknown acestep action: {action}")
