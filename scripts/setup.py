#!/usr/bin/env python3
"""
LocalForge interactive setup wizard.

Detects available services, creates configuration, and sets up workspace.

Usage:
    python -m localforge init
    python scripts/setup.py
"""

import os
import platform
import shutil
from pathlib import Path


def _check_service(name: str, url: str) -> bool:
    """Check if an HTTP service is running."""
    try:
        import requests
        resp = requests.get(url, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _detect_services() -> dict:
    """Detect which services are available."""
    services = {}

    # Ollama
    if _check_service("Ollama", "http://localhost:11434/api/tags"):
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            models = resp.json().get("models", [])
            services["ollama"] = {
                "available": True,
                "host": "http://localhost:11434",
                "models": [m.get("name", "") for m in models],
            }
        except Exception:
            services["ollama"] = {"available": True, "host": "http://localhost:11434", "models": []}
    else:
        services["ollama"] = {"available": False}

    # SD WebUI
    if _check_service("SD WebUI", "http://localhost:7860/sdapi/v1/sd-models"):
        services["sd"] = {"available": True, "host": "http://localhost:7860"}
    else:
        services["sd"] = {"available": False}

    # Blender
    blender = shutil.which("blender")
    if not blender:
        system = platform.system()
        candidates = []
        if system == "Windows":
            pf = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            bf = pf / "Blender Foundation"
            if bf.exists():
                for d in sorted(bf.iterdir(), reverse=True):
                    exe = d / "blender.exe"
                    if exe.exists():
                        blender = str(exe)
                        break
        elif system == "Darwin":
            mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
            if mac.exists():
                blender = str(mac)
    services["blender"] = {"available": blender is not None, "path": blender}

    # FFmpeg
    ffmpeg = shutil.which("ffmpeg")
    services["ffmpeg"] = {"available": ffmpeg is not None, "path": ffmpeg}

    return services


def _write_config(workspace: Path, services: dict):
    """Write localforge.yaml configuration."""
    lines = [
        "# LocalForge Configuration",
        f"workspace: {workspace}",
        f"output_dir: {workspace / 'output'}",
        f"run_dir: {workspace / 'runs'}",
        "",
        "services:",
    ]

    # Ollama
    if services["ollama"]["available"]:
        host = services["ollama"]["host"]
        models = services["ollama"].get("models", [])
        default_model = models[0] if models else "llama3.2:3b"
        lines.extend([
            "  ollama:",
            f"    host: {host}",
            f"    default_model: {default_model}",
            "    timeout: 60",
        ])
    else:
        lines.extend([
            "  ollama:",
            "    host: http://localhost:11434",
            "    default_model: llama3.2:3b",
        ])

    # SD
    if services["sd"]["available"]:
        lines.extend([
            "  sd:",
            f"    host: {services['sd']['host']}",
            "    timeout: 120",
        ])

    # Blender
    if services["blender"]["available"]:
        lines.extend([
            "  blender:",
            f"    path: {services['blender']['path']}",
        ])

    # FFmpeg
    if services["ffmpeg"]["available"]:
        lines.extend([
            "  ffmpeg:",
            f"    path: {services['ffmpeg']['path']}",
        ])

    lines.extend([
        "",
        "persistence:",
        "  enabled: true",
        f"  db_path: {Path.home() / '.localforge' / 'runs.db'}",
    ])

    config_path = Path.cwd() / "localforge.yaml"
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def run_setup():
    """Run the interactive setup wizard."""
    print("LocalForge Setup\n")

    # Workspace location
    default_workspace = Path.home() / "localforge-workspace"
    workspace_input = input(f"Workspace directory [{default_workspace}]: ").strip()
    workspace = Path(workspace_input) if workspace_input else default_workspace

    # Create workspace
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "output").mkdir(exist_ok=True)
    (workspace / "runs").mkdir(exist_ok=True)
    (workspace / "logs").mkdir(exist_ok=True)

    print(f"\nCreated workspace at {workspace}")

    # Detect services
    print("\nDetecting services...")
    services = _detect_services()

    for name, info in services.items():
        status = "FOUND" if info["available"] else "NOT FOUND"
        extra = ""
        if name == "ollama" and info["available"]:
            models = info.get("models", [])
            extra = f" ({len(models)} models)" if models else ""
        elif name == "blender" and info["available"]:
            extra = f" at {info['path']}"
        elif name == "ffmpeg" and info["available"]:
            extra = f" at {info['path']}"
        print(f"  {name.upper()}: {status}{extra}")

    # Write config
    config_path = _write_config(workspace, services)
    print(f"\nConfiguration written to: {config_path}")

    # Summary
    print("\nReady! Try:")
    available = [n for n, i in services.items() if i["available"]]
    if "ollama" in available:
        print('  python -m localforge run recipes/getting-started/hello-ollama.yaml \\')
        print('    --input prompt="Tell me a joke" --auto-approve')
    elif "sd" in available:
        print('  python -m localforge run recipes/getting-started/hello-sd.yaml \\')
        print('    --input prompt="a sunset" --auto-approve')
    else:
        print("  Install Ollama (https://ollama.ai) to get started.")
    print()


if __name__ == "__main__":
    run_setup()
