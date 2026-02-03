"""
Script execution tool.

Runs arbitrary user scripts (Python, shell, etc.) as workflow steps.

SECURITY WARNING: This tool executes scripts with the same permissions as the
LocalForge process. Only run recipes from trusted sources. A malicious recipe
could use this tool to execute arbitrary commands on your system.
"""

import subprocess
import sys
from pathlib import Path

TOOL_NAME = "script"
TOOL_ACTIONS = ["run"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle custom script execution."""
    if action == "run":
        script_path = Path(inputs.get("script"))
        args = inputs.get("args", [])
        if isinstance(args, str):
            args = args.split()
        args = [str(a) for a in args]
        timeout = int(inputs.get("timeout", 300))
        working_dir = inputs.get("working_dir", None)

        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Determine interpreter
        ext = script_path.suffix.lower()
        if ext == ".py":
            cmd = [sys.executable, str(script_path)] + args
        elif ext in (".sh", ".bash"):
            cmd = ["bash", str(script_path)] + args
        elif ext in (".ps1",):
            cmd = ["powershell.exe", "-File", str(script_path)] + args
        else:
            cmd = [str(script_path)] + args

        ctx.log(f"Running script: {script_path.name}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
        )

        if result.returncode != 0:
            ctx.log(f"Script stderr: {result.stderr}", "WARNING")

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0,
        }

    raise ValueError(f"Unknown script action: {action}")
