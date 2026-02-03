"""
File operations tool.

Provides copy, move, delete, mkdir, list operations for workflow steps.
"""

import shutil
from pathlib import Path

TOOL_NAME = "file_ops"
TOOL_ACTIONS = ["copy", "move", "delete", "mkdir", "copy_multiple", "list"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle file operations."""
    if action == "copy":
        src = Path(inputs.get("source"))
        dst = Path(inputs.get("destination"))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return {"destination": str(dst)}

    elif action == "move":
        src = Path(inputs.get("source"))
        dst = Path(inputs.get("destination"))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"destination": str(dst)}

    elif action == "delete":
        path = Path(inputs.get("path"))
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
        return {"deleted": str(path)}

    elif action == "mkdir":
        path = Path(inputs.get("path"))
        path.mkdir(parents=True, exist_ok=True)
        return {"created": str(path)}

    elif action == "copy_multiple":
        copies = inputs.get("copies", [])
        results = []
        for copy_spec in copies:
            src = Path(copy_spec.get("source"))
            dst = Path(copy_spec.get("destination"))
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            results.append({"source": str(src), "destination": str(dst)})
        return {"copies": results}

    elif action == "list":
        path = Path(inputs.get("path", "."))
        pattern = inputs.get("pattern", "*")
        files = list(path.glob(pattern))
        return {"files": [str(f) for f in files], "count": len(files)}

    raise ValueError(f"Unknown file_ops action: {action}")
