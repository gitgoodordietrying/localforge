"""System discovery and hardware profiling for LocalForge."""

import os
import platform
import shutil
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None


def _load_model_profiles() -> dict:
    """Load model VRAM profiles from data/model_profiles.yaml."""
    if yaml is None:
        return {}
    profiles_path = Path(__file__).parent.parent / "data" / "model_profiles.yaml"
    if not profiles_path.exists():
        return {}
    with open(profiles_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class SystemInfo:
    """Detect hardware, services, and installed tools."""

    def __init__(self):
        self._hardware = None
        self._services = None
        self._tools = None
        self._profiles = None

    @property
    def hardware(self) -> dict:
        if self._hardware is None:
            self._hardware = self._detect_hardware()
        return self._hardware

    @property
    def services(self) -> dict:
        if self._services is None:
            self._services = self._detect_services()
        return self._services

    @property
    def tools(self) -> dict:
        if self._tools is None:
            self._tools = self._detect_tools()
        return self._tools

    @property
    def profiles(self) -> dict:
        if self._profiles is None:
            self._profiles = _load_model_profiles()
        return self._profiles

    def _detect_hardware(self) -> dict:
        """Detect RAM, CPU cores, and GPU/VRAM."""
        hw = {
            "cpu_cores": os.cpu_count() or 0,
            "ram_gb": self._get_ram_gb(),
            "platform": platform.system(),
            "arch": platform.machine(),
            "gpu": None,
            "vram_gb": 0.0,
        }
        gpu_info = self._detect_gpu()
        if gpu_info:
            hw["gpu"] = gpu_info.get("name")
            hw["vram_gb"] = gpu_info.get("vram_gb", 0.0)
        return hw

    @staticmethod
    def _get_ram_gb() -> float:
        """Get total RAM in GB. Uses /proc/meminfo on Linux, os-level on others."""
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024 ** 3), 1)
        except ImportError:
            pass
        # Fallback: try /proc/meminfo on Linux
        if platform.system() == "Linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            return round(kb / (1024 ** 2), 1)
            except (OSError, ValueError):
                pass
        # Fallback: try wmic on Windows
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if line.isdigit():
                        return round(int(line) / (1024 ** 3), 1)
            except (subprocess.SubprocessError, OSError, ValueError):
                pass
        return 0.0

    @staticmethod
    def _detect_gpu() -> dict | None:
        """Detect NVIDIA GPU and VRAM via nvidia-smi."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split("\n")[0]
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    name = parts[0]
                    vram_mb = float(parts[1])
                    return {"name": name, "vram_gb": round(vram_mb / 1024, 1)}
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
        return None

    def _detect_services(self) -> dict:
        """Check which services are running."""
        service_checks = {
            "ollama": ("http://localhost:11434/api/tags", "Ollama"),
            "sd_webui": ("http://localhost:7860/sdapi/v1/sd-models", "SD WebUI"),
            "comfyui": ("http://localhost:8188/system_stats", "ComfyUI"),
        }
        result = {}
        for key, (url, label) in service_checks.items():
            result[key] = self._check_service(url, label)
        return result

    @staticmethod
    def _check_service(url: str, label: str) -> dict:
        """Check if an HTTP service is running."""
        if requests is None:
            return {"label": label, "running": False, "error": "requests not installed"}
        try:
            resp = requests.get(url, timeout=3)
            return {
                "label": label,
                "running": resp.status_code == 200,
                "status_code": resp.status_code,
            }
        except Exception:
            return {"label": label, "running": False}

    def _detect_tools(self) -> dict:
        """Check which CLI tools are available."""
        tool_checks = {
            "blender": "blender",
            "ffmpeg": "ffmpeg",
            "whisper": "whisper",
            "yt-dlp": "yt-dlp",
            "pandoc": "pandoc",
            "imagemagick": "magick",
        }
        result = {}
        for name, binary in tool_checks.items():
            path = shutil.which(binary)
            result[name] = {
                "found": path is not None,
                "path": path,
            }
        return result

    def can_run_model(self, model: str, category: str = "ollama") -> bool:
        """Check if a model fits within available VRAM."""
        vram = self.hardware.get("vram_gb", 0.0)
        if vram <= 0:
            return False
        cat_profiles = self.profiles.get(category, {})
        profile = cat_profiles.get(model)
        if profile is None:
            return False
        required = profile.get("vram_gb", 0.0)
        return vram >= required

    def recommend_models(self, task: str = "general") -> list[dict]:
        """Recommend models that fit in available VRAM for a given task."""
        vram = self.hardware.get("vram_gb", 0.0)
        ollama_profiles = self.profiles.get("ollama", {})
        recommendations = []
        for model_name, profile in ollama_profiles.items():
            required = profile.get("vram_gb", 0.0)
            tasks = profile.get("tasks", [])
            if required <= vram and task in tasks:
                recommendations.append({
                    "model": model_name,
                    "vram_gb": required,
                    "quality": profile.get("quality", "unknown"),
                    "description": profile.get("description", ""),
                })
        # Sort by quality tier: best > better > good > basic
        quality_order = {"best": 0, "better": 1, "good": 2, "basic": 3, "unknown": 4}
        recommendations.sort(key=lambda r: quality_order.get(r["quality"], 4))
        return recommendations

    def recommend_sd_config(self) -> dict | None:
        """Recommend SD configuration based on available VRAM."""
        vram = self.hardware.get("vram_gb", 0.0)
        sd_profiles = self.profiles.get("sd", {})
        best = None
        for key, profile in sd_profiles.items():
            required = profile.get("vram_gb", 0.0)
            if required <= vram:
                if best is None or required > best.get("vram_gb", 0.0):
                    best = {
                        "key": key,
                        "label": profile.get("label", key),
                        "vram_gb": required,
                        "resolution": profile.get("resolution", []),
                    }
        return best

    def summary(self) -> dict:
        """Return complete system profile."""
        return {
            "hardware": self.hardware,
            "services": self.services,
            "tools": self.tools,
        }

    def format_report(self) -> str:
        """Format a human-readable system report."""
        lines = ["LocalForge System Profile", ""]

        # Hardware
        hw = self.hardware
        lines.append("Hardware:")
        lines.append(f"  CPU: {hw['cpu_cores']} cores")
        if hw["ram_gb"] > 0:
            lines.append(f"  RAM: {hw['ram_gb']} GB")
        else:
            lines.append("  RAM: unknown")
        if hw["gpu"]:
            lines.append(f"  GPU: {hw['gpu']} ({hw['vram_gb']} GB VRAM)")
        else:
            lines.append("  GPU: not detected (no NVIDIA GPU or nvidia-smi not found)")
        lines.append("")

        # Services
        lines.append("Services:")
        for key, svc in self.services.items():
            status = "RUNNING" if svc.get("running") else "NOT RUNNING"
            lines.append(f"  {svc['label']}: {status}")
        lines.append("")

        # Tools
        lines.append("Tools:")
        for name, info in self.tools.items():
            if info["found"]:
                lines.append(f"  {name}: FOUND ({info['path']})")
            else:
                lines.append(f"  {name}: NOT FOUND")
        lines.append("")

        # Model recommendations
        vram = hw.get("vram_gb", 0.0)
        if vram > 0:
            lines.append("Model Recommendations:")
            for task in ["general", "code"]:
                recs = self.recommend_models(task)
                if recs:
                    best = recs[0]
                    lines.append(
                        f"  {task.title()}: {best['model']} "
                        f"({best['vram_gb']} GB VRAM, {best['quality']} quality)"
                    )
            sd = self.recommend_sd_config()
            if sd:
                lines.append(
                    f"  Image gen: {sd['label']} ({sd['vram_gb']} GB VRAM)"
                )
            lines.append("")
        else:
            lines.append("Model Recommendations:")
            lines.append("  Cannot recommend models — GPU VRAM not detected")
            lines.append("")

        return "\n".join(lines)
