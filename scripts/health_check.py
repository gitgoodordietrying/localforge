#!/usr/bin/env python3
"""
Cross-platform service health check.

Detects and reports the status of all LocalForge-compatible services.

Usage:
    python scripts/health_check.py
    python -m localforge health
"""

import shutil
import subprocess
import sys


def check_http(name: str, url: str) -> dict:
    """Check an HTTP service."""
    try:
        import requests
        resp = requests.get(url, timeout=3)
        return {"name": name, "status": "running", "url": url, "code": resp.status_code}
    except Exception:
        return {"name": name, "status": "not running", "url": url}


def check_binary(name: str, binary: str = None) -> dict:
    """Check if a binary is available."""
    path = shutil.which(binary or name.lower())
    if path:
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=10
            )
            version = result.stdout.strip().split("\n")[0] if result.stdout else "unknown"
            return {"name": name, "status": "found", "path": path, "version": version}
        except Exception:
            return {"name": name, "status": "found", "path": path}
    return {"name": name, "status": "not found"}


def run_health_check():
    """Run all health checks and print results."""
    print("LocalForge Service Health Check\n")

    http_services = [
        ("Ollama", "http://localhost:11434/api/tags"),
        ("SD WebUI", "http://localhost:7860/sdapi/v1/sd-models"),
        ("ComfyUI", "http://localhost:8188/system_stats"),
    ]

    binaries = [
        ("Blender", "blender"),
        ("FFmpeg", "ffmpeg"),
        ("Python", sys.executable),
    ]

    print("HTTP Services:")
    for name, url in http_services:
        result = check_http(name, url)
        status = result["status"].upper()
        print(f"  {name}: {status} ({url})")

    print("\nBinaries:")
    for name, binary in binaries:
        result = check_binary(name, binary)
        status = result["status"].upper()
        extra = f" ({result.get('path', '')})" if result["status"] == "found" else ""
        print(f"  {name}: {status}{extra}")

    # Check Python packages
    print("\nPython Packages:")
    packages = ["yaml", "requests", "PIL", "numpy", "rembg"]
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  {pkg}: INSTALLED")
        except ImportError:
            req = "OPTIONAL" if pkg in ("numpy", "rembg") else "REQUIRED"
            print(f"  {pkg}: NOT INSTALLED ({req})")

    print()


if __name__ == "__main__":
    run_health_check()
