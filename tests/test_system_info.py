"""Tests for system_info module."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


sys.path.insert(0, str(Path(__file__).parent.parent))

from localforge.engine.system_info import SystemInfo, _load_model_profiles


class TestModelProfiles:
    def test_profiles_load(self):
        """Model profiles YAML should load without error."""
        profiles = _load_model_profiles()
        assert isinstance(profiles, dict)

    def test_profiles_have_ollama(self):
        """Profiles should contain ollama models."""
        profiles = _load_model_profiles()
        assert "ollama" in profiles

    def test_profiles_have_sd(self):
        """Profiles should contain SD configurations."""
        profiles = _load_model_profiles()
        assert "sd" in profiles

    def test_ollama_models_have_vram(self):
        """Each ollama model should specify vram_gb."""
        profiles = _load_model_profiles()
        for model, info in profiles.get("ollama", {}).items():
            assert "vram_gb" in info, f"{model} missing vram_gb"
            assert isinstance(info["vram_gb"], (int, float))

    def test_ollama_models_have_tasks(self):
        """Each ollama model should specify tasks."""
        profiles = _load_model_profiles()
        for model, info in profiles.get("ollama", {}).items():
            assert "tasks" in info, f"{model} missing tasks"
            assert isinstance(info["tasks"], list)

    def test_sd_configs_have_vram(self):
        """Each SD config should specify vram_gb."""
        profiles = _load_model_profiles()
        for key, info in profiles.get("sd", {}).items():
            assert "vram_gb" in info, f"{key} missing vram_gb"


class TestSystemInfoHardware:
    def test_cpu_cores_positive(self):
        """CPU core count should be a positive integer."""
        info = SystemInfo()
        hw = info.hardware
        assert isinstance(hw["cpu_cores"], int)
        assert hw["cpu_cores"] > 0

    def test_hardware_has_platform(self):
        """Hardware info should include platform."""
        info = SystemInfo()
        hw = info.hardware
        assert hw["platform"] in ("Windows", "Linux", "Darwin")

    def test_hardware_has_arch(self):
        """Hardware info should include architecture."""
        info = SystemInfo()
        hw = info.hardware
        assert isinstance(hw["arch"], str)
        assert len(hw["arch"]) > 0

    def test_hardware_cached(self):
        """Hardware detection should be cached after first call."""
        info = SystemInfo()
        hw1 = info.hardware
        hw2 = info.hardware
        assert hw1 is hw2


class TestSystemInfoGPU:
    def test_detect_gpu_returns_dict_or_none(self):
        """GPU detection should return dict with name/vram or None."""
        result = SystemInfo._detect_gpu()
        if result is not None:
            assert "name" in result
            assert "vram_gb" in result
            assert isinstance(result["vram_gb"], float)

    @patch("subprocess.run")
    def test_detect_gpu_parses_nvidia_smi(self, mock_run):
        """Should parse nvidia-smi CSV output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA GeForce RTX 3090, 24576\n",
        )
        result = SystemInfo._detect_gpu()
        assert result is not None
        assert result["name"] == "NVIDIA GeForce RTX 3090"
        assert result["vram_gb"] == 24.0

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_detect_gpu_handles_missing_nvidia_smi(self, mock_run):
        """Should return None if nvidia-smi not found."""
        result = SystemInfo._detect_gpu()
        assert result is None


class TestSystemInfoServices:
    @patch("localforge.engine.system_info.requests", None)
    def test_services_without_requests(self):
        """Should handle missing requests library gracefully."""
        info = SystemInfo()
        info._services = None  # Reset cache
        services = info._detect_services()
        for key, svc in services.items():
            assert svc["running"] is False

    def test_services_returns_dict(self):
        """Services check should return a dict of service statuses."""
        info = SystemInfo()
        services = info.services
        assert isinstance(services, dict)
        assert "ollama" in services
        assert "sd_webui" in services
        assert "comfyui" in services

    def test_service_has_label(self):
        """Each service should have a label."""
        info = SystemInfo()
        for key, svc in info.services.items():
            assert "label" in svc
            assert isinstance(svc["label"], str)


class TestSystemInfoTools:
    def test_tools_returns_dict(self):
        """Tools check should return a dict."""
        info = SystemInfo()
        tools = info.tools
        assert isinstance(tools, dict)

    def test_tools_have_found_field(self):
        """Each tool entry should have a 'found' boolean."""
        info = SystemInfo()
        for name, info_dict in info.tools.items():
            assert "found" in info_dict
            assert isinstance(info_dict["found"], bool)

    def test_tools_check_known_binaries(self):
        """Should check for known tool binaries."""
        info = SystemInfo()
        expected = {"blender", "ffmpeg", "whisper", "yt-dlp", "pandoc", "imagemagick"}
        assert expected.issubset(set(info.tools.keys()))


class TestModelRecommendations:
    def test_can_run_model_with_enough_vram(self):
        """Should return True when VRAM is sufficient."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 16.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        assert info.can_run_model("llama3.2:3b", "ollama") is True
        assert info.can_run_model("mistral:7b", "ollama") is True

    def test_can_run_model_insufficient_vram(self):
        """Should return False when VRAM is insufficient."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 2.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        assert info.can_run_model("codellama:13b", "ollama") is False

    def test_can_run_model_no_gpu(self):
        """Should return False when no GPU detected."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 0.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": None}
        assert info.can_run_model("llama3.2:3b", "ollama") is False

    def test_can_run_model_unknown_model(self):
        """Should return False for unknown model names."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 16.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        assert info.can_run_model("nonexistent:model", "ollama") is False

    def test_recommend_models_general(self):
        """Should recommend models for 'general' task."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 16.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        recs = info.recommend_models("general")
        assert len(recs) > 0
        # Best quality should be first
        qualities = [r["quality"] for r in recs]
        quality_order = {"best": 0, "better": 1, "good": 2, "basic": 3}
        indices = [quality_order.get(q, 4) for q in qualities]
        assert indices == sorted(indices)

    def test_recommend_models_with_low_vram(self):
        """With low VRAM, should recommend fewer/smaller models."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 3.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        recs = info.recommend_models("general")
        for rec in recs:
            assert rec["vram_gb"] <= 3.0

    def test_recommend_sd_config(self):
        """Should recommend highest-resolution SD config that fits."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 12.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        sd = info.recommend_sd_config()
        assert sd is not None
        assert sd["vram_gb"] <= 12.0

    def test_recommend_sd_config_low_vram(self):
        """With very low VRAM, might not recommend any SD config."""
        info = SystemInfo()
        info._hardware = {"vram_gb": 1.0, "cpu_cores": 8, "ram_gb": 32.0,
                          "platform": "Linux", "arch": "x86_64", "gpu": "Test GPU"}
        sd = info.recommend_sd_config()
        assert sd is None


class TestSystemInfoSummary:
    def test_summary_has_all_sections(self):
        """Summary should contain hardware, services, and tools."""
        info = SystemInfo()
        summary = info.summary()
        assert "hardware" in summary
        assert "services" in summary
        assert "tools" in summary

    def test_format_report_returns_string(self):
        """format_report should return a non-empty string."""
        info = SystemInfo()
        report = info.format_report()
        assert isinstance(report, str)
        assert "LocalForge System Profile" in report
        assert "Hardware:" in report
        assert "Services:" in report
        assert "Tools:" in report
