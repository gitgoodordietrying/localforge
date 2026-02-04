"""Tests for engine/config.py"""

# Ensure project root is importable
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from localforge.engine.config import Config, _deep_merge, _expand_path, get_config, reset_config


@pytest.fixture(autouse=True)
def clean_config():
    """Reset global config singleton between tests."""
    reset_config()
    yield
    reset_config()


class TestDeepMerge:
    def test_flat_merge(self):
        assert _deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_override(self):
        assert _deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_nested_merge(self):
        base = {"services": {"ollama": {"host": "http://localhost:11434", "timeout": 60}}}
        override = {"services": {"ollama": {"timeout": 120}}}
        result = _deep_merge(base, override)
        assert result["services"]["ollama"]["host"] == "http://localhost:11434"
        assert result["services"]["ollama"]["timeout"] == 120

    def test_empty_override(self):
        base = {"a": 1, "b": 2}
        assert _deep_merge(base, {}) == base


class TestExpandPath:
    def test_none_returns_none(self):
        assert _expand_path(None) is None

    def test_tilde_expansion(self):
        result = _expand_path("~/test")
        assert "~" not in result
        assert "test" in result

    def test_string_passthrough(self):
        result = _expand_path("/absolute/path")
        assert "absolute" in result


class TestConfig:
    def test_defaults_loaded(self):
        config = Config()
        assert config.ollama_host == "http://localhost:11434"
        assert config.ollama_model == "llama3.2:3b"
        assert config.sd_host == "http://localhost:7860"

    def test_config_from_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "services": {
                    "ollama": {"default_model": "mistral:7b"},
                    "sd": {"timeout": 300},
                }
            }, f)
            config_path = Path(f.name)

        try:
            config = Config(config_path)
            assert config.ollama_model == "mistral:7b"
            assert config.sd_timeout == 300
            # Defaults preserved
            assert config.ollama_host == "http://localhost:11434"
        finally:
            config_path.unlink()

    def test_persistence_defaults(self):
        config = Config()
        assert config.persistence_enabled is True

    def test_get_nested(self):
        config = Config()
        assert config.get("services.ollama.host") == "http://localhost:11434"
        assert config.get("nonexistent.key", "fallback") == "fallback"

    def test_service_accessor(self):
        config = Config()
        ollama_conf = config.service("ollama")
        assert "host" in ollama_conf
        assert "timeout" in ollama_conf

    def test_unknown_service(self):
        config = Config()
        assert config.service("nonexistent") == {}


class TestGetConfig:
    def test_singleton(self):
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_reset(self):
        c1 = get_config()
        reset_config()
        c2 = get_config()
        assert c1 is not c2
