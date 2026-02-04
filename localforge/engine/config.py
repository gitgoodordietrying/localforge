"""
LocalForge configuration loader.

Reads configuration from localforge.yaml (project-local or global).

Search order:
  1. ./localforge.yaml (current directory)
  2. ~/.localforge/config.yaml (global)
  3. Built-in defaults
"""

import os
import platform
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# Built-in defaults
DEFAULTS = {
    "workspace": "~/localforge-workspace",
    "output_dir": "~/localforge-workspace/output",
    "run_dir": "~/localforge-workspace/runs",
    "services": {
        "ollama": {
            "host": "http://localhost:11434",
            "default_model": "llama3.2:3b",
            "timeout": 60,
        },
        "sd": {
            "host": "http://localhost:7860",
            "timeout": 120,
        },
        "blender": {
            "path": None,  # Auto-detect
        },
        "ffmpeg": {
            "path": "ffmpeg",
        },
        "musicgen": {
            "venv_dir": None,
        },
        "acestep": {
            "venv_dir": None,
        },
    },
    "persistence": {
        "enabled": True,
        "db_path": "~/.localforge/runs.db",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base, returning new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _expand_path(p: Any) -> Optional[str]:
    """Expand ~ and environment variables in a path string."""
    if p is None:
        return None
    return str(Path(os.path.expanduser(os.path.expandvars(str(p)))).resolve())


def _detect_blender() -> Optional[str]:
    """Try to find Blender executable on the system."""
    import shutil

    # Check PATH first
    blender = shutil.which("blender")
    if blender:
        return blender

    # Platform-specific common locations
    system = platform.system()
    candidates = []

    if system == "Windows":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        for version in ["4.2", "4.1", "4.0", "3.6"]:
            candidates.append(
                Path(program_files) / "Blender Foundation" / f"Blender {version}" / "blender.exe"
            )
    elif system == "Darwin":
        candidates.append(Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    else:
        candidates.extend([
            Path("/usr/bin/blender"),
            Path("/usr/local/bin/blender"),
            Path("/snap/bin/blender"),
        ])

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


class Config:
    """LocalForge configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self._raw = dict(DEFAULTS)

        # Load from file if available
        loaded = self._load_config_file(config_path)
        if loaded:
            self._raw = _deep_merge(self._raw, loaded)

        # Auto-detect blender if not set
        if not self._raw["services"]["blender"]["path"]:
            detected = _detect_blender()
            if detected:
                self._raw["services"]["blender"]["path"] = detected

    def _load_config_file(self, explicit_path: Optional[Path] = None) -> Optional[dict]:
        """Load config from YAML file."""
        if yaml is None:
            return None

        paths_to_try = []
        if explicit_path:
            paths_to_try.append(Path(explicit_path))
        paths_to_try.extend([
            Path.cwd() / "localforge.yaml",
            Path.home() / ".localforge" / "config.yaml",
        ])

        for path in paths_to_try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        return data
        return None

    @property
    def workspace(self) -> str:
        return _expand_path(self._raw["workspace"])

    @property
    def output_dir(self) -> str:
        return _expand_path(self._raw["output_dir"])

    @property
    def run_dir(self) -> str:
        return _expand_path(self._raw["run_dir"])

    def service(self, name: str) -> dict:
        """Get service configuration."""
        return self._raw.get("services", {}).get(name, {})

    @property
    def ollama_host(self) -> str:
        return self.service("ollama").get("host", "http://localhost:11434")

    @property
    def ollama_model(self) -> str:
        return self.service("ollama").get("default_model", "llama3.2:3b")

    @property
    def sd_host(self) -> str:
        return self.service("sd").get("host", "http://localhost:7860")

    @property
    def sd_timeout(self) -> int:
        return self.service("sd").get("timeout", 120)

    @property
    def blender_path(self) -> Optional[str]:
        return self.service("blender").get("path")

    @property
    def ffmpeg_path(self) -> str:
        return self.service("ffmpeg").get("path", "ffmpeg")

    @property
    def persistence_enabled(self) -> bool:
        return self._raw.get("persistence", {}).get("enabled", True)

    @property
    def persistence_db_path(self) -> str:
        db = self._raw.get("persistence", {}).get("db_path", "~/.localforge/runs.db")
        return _expand_path(db)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a raw config value by dot-separated key."""
        parts = key.split(".")
        obj = self._raw
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                return default
            if obj is None:
                return default
        return obj


# Module-level singleton
_config: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reset_config():
    """Reset the global config (for testing)."""
    global _config
    _config = None
