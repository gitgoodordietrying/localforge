"""Tests for WorkflowContext variable resolution."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from localforge.engine.runner import WorkflowContext


@pytest.fixture
def ctx():
    """Create a minimal WorkflowContext for testing."""
    import shutil

    recipe = {
        "name": "test-recipe",
        "config": {"max_iterations": 5, "nested": {"key": "value"}},
    }
    inputs = {"name": "world", "count": "3"}
    context = WorkflowContext(recipe, inputs, run_base_dir="./test_runs")
    yield context
    # Clean up test directories
    if context.run_dir.exists():
        shutil.rmtree(context.run_dir.parent, ignore_errors=True)


class TestVariableResolution:
    def test_resolve_input(self, ctx):
        assert ctx.resolve("{{inputs.name}}") == "world"

    def test_resolve_config(self, ctx):
        assert ctx.resolve("{{config.max_iterations}}") == "5"

    def test_resolve_nested_config(self, ctx):
        assert ctx.resolve("{{config.nested.key}}") == "value"

    def test_resolve_temp_dir(self, ctx):
        result = ctx.resolve("{{temp_dir}}")
        assert "temp" in result

    def test_resolve_workflow_name(self, ctx):
        assert ctx.resolve("{{workflow.name}}") == "test-recipe"

    def test_resolve_workflow_run_id(self, ctx):
        result = ctx.resolve("{{workflow.run_id}}")
        assert len(result) == 8  # UUID[:8]

    def test_resolve_timestamp(self, ctx):
        result = ctx.resolve("{{timestamp}}")
        assert "T" in result  # ISO format

    def test_resolve_in_string(self, ctx):
        result = ctx.resolve("Hello {{inputs.name}}!")
        assert result == "Hello world!"

    def test_resolve_multiple(self, ctx):
        result = ctx.resolve("{{inputs.name}} x{{inputs.count}}")
        assert result == "world x3"

    def test_resolve_dict(self, ctx):
        result = ctx.resolve({"key": "{{inputs.name}}", "static": "value"})
        assert result == {"key": "world", "static": "value"}

    def test_resolve_list(self, ctx):
        result = ctx.resolve(["{{inputs.name}}", "static"])
        assert result == ["world", "static"]

    def test_unresolvable_preserved(self, ctx):
        result = ctx.resolve("{{inputs.nonexistent}}")
        # Should preserve the original pattern (warning logged)
        assert "{{" in result or result == "None"

    def test_step_output_resolution(self, ctx):
        ctx.set_step_output("step1", {"result": "hello"})
        assert ctx.resolve("{{steps.step1.outputs.result}}") == "hello"

    def test_non_string_passthrough(self, ctx):
        assert ctx.resolve(42) == 42
        assert ctx.resolve(True) is True
        assert ctx.resolve(None) is None


class TestStepOutputs:
    def test_set_and_get(self, ctx):
        ctx.set_step_output("my_step", {"key": "value"})
        assert ctx.steps_output["my_step"]["outputs"]["key"] == "value"

    def test_multiple_steps(self, ctx):
        ctx.set_step_output("step1", {"a": "1"})
        ctx.set_step_output("step2", {"b": "2"})
        assert ctx.resolve("{{steps.step1.outputs.a}}") == "1"
        assert ctx.resolve("{{steps.step2.outputs.b}}") == "2"


class TestContextInit:
    def test_run_dir_created(self, ctx):
        assert ctx.run_dir.exists()

    def test_temp_dir_created(self, ctx):
        assert ctx.temp_dir.exists()

    def test_run_id_format(self, ctx):
        assert len(ctx.run_id) == 8
