"""Tests for tool auto-discovery and registry."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from localforge.engine.runner import ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


class TestToolDiscovery:
    def test_tools_discovered(self, registry):
        """At least the core tools should load (they have no heavy deps)."""
        tools = registry.available_tools()
        assert len(tools) > 0

    def test_file_ops_loaded(self, registry):
        """file_ops has no external deps, should always load."""
        assert "file_ops" in registry.available_tools()

    def test_batch_loaded(self, registry):
        """batch has no external deps, should always load."""
        assert "batch" in registry.available_tools()

    def test_ollama_loaded(self, registry):
        """ollama only needs requests, should load."""
        assert "ollama" in registry.available_tools()

    def test_script_loaded(self, registry):
        """script has no external deps, should always load."""
        assert "script" in registry.available_tools()


class TestToolExecution:
    def test_unknown_tool_error(self, registry):
        """Unknown tool should raise with available tools listed."""
        with pytest.raises(ValueError, match="Unknown tool"):
            from localforge.engine.runner import WorkflowContext
            ctx = WorkflowContext({"name": "test"}, {}, run_base_dir="./test_runs")
            registry.execute("nonexistent_tool", "action", {}, ctx)

    def test_file_ops_mkdir(self, registry):
        """file_ops.mkdir should work without any services."""
        import shutil

        from localforge.engine.runner import WorkflowContext

        ctx = WorkflowContext({"name": "test"}, {}, run_base_dir="./test_runs")
        test_dir = str(ctx.temp_dir / "test_mkdir")

        try:
            registry.execute("file_ops", "mkdir", {"path": test_dir}, ctx)
            assert Path(test_dir).exists()
        finally:
            shutil.rmtree(ctx.run_dir.parent, ignore_errors=True)


class TestPreflight:
    def test_preflight_returns_loaded_tools(self, registry):
        results = registry.preflight_check()
        assert isinstance(results, dict)
        for tool_name, status in results.items():
            assert status is True  # Loaded tools are marked True
