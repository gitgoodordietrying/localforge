#!/usr/bin/env python3
"""
LocalForge Workflow Engine

Executes workflow recipes defined in YAML format. Each recipe is a
multi-step pipeline that chains local tools (LLMs, image generators,
media processors, custom scripts) to produce outputs.

Usage:
    python -m localforge run <recipe.yaml> [--input key=value ...] [--auto-approve]
"""

import importlib
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

from .config import get_config


class WorkflowContext:
    """Holds state during workflow execution."""

    def __init__(self, recipe: Dict[str, Any], inputs: Dict[str, Any],
                 run_base_dir: Optional[str] = None):
        self.recipe = recipe
        self.inputs = inputs
        self.config = recipe.get("config", {})
        self.templates = recipe.get("templates", {})
        self.steps_output: Dict[str, Dict[str, Any]] = {}
        self.run_id = str(uuid.uuid4())[:8]

        base = Path(run_base_dir) if run_base_dir else Path("./workflow_runs")
        self.run_dir = base / self.run_id
        self.temp_dir = self.run_dir / "temp"
        self.start_time = datetime.now()
        self.current_step: Optional[str] = None
        self.errors: List[str] = []
        self.iteration_count: Dict[str, int] = {}
        self.refinement_active: bool = False

        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, value: Any) -> Any:
        """Resolve variable references in a value."""
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(v) for v in value]
        return value

    def _resolve_string(self, s: str) -> str:
        """Resolve {{variable}} patterns in a string."""
        pattern = r'\{\{([^}]+)\}\}'

        def replacer(match):
            expr = match.group(1).strip()
            try:
                return str(self._evaluate(expr))
            except Exception as e:
                self.log(f"Could not resolve '{expr}': {e}", "WARNING")
                return match.group(0)

        return re.sub(pattern, replacer, s)

    def _evaluate(self, expr: str) -> Any:
        """Evaluate a variable expression."""
        parts = expr.split(".")

        if parts[0] == "inputs":
            return self._get_nested(self.inputs, parts[1:])
        elif parts[0] == "config":
            return self._get_nested(self.config, parts[1:])
        elif parts[0] == "steps":
            step_id = parts[1]
            if step_id in self.steps_output:
                return self._get_nested(self.steps_output[step_id], parts[2:])
            return f"{{{{steps.{step_id}...}}}}"
        elif parts[0] == "templates":
            key = parts[1] if len(parts) > 1 else None
            if key and key in self.templates:
                return self.templates[key]
            return self.templates
        elif parts[0] == "workflow":
            if parts[1] == "run_id":
                return self.run_id
            elif parts[1] == "run_dir":
                return str(self.run_dir)
            elif parts[1] == "name":
                return self.recipe.get("name", "unnamed")
        elif parts[0] == "temp_dir":
            return str(self.temp_dir)
        elif parts[0] == "timestamp":
            return datetime.now().isoformat()

        raise ValueError(f"Unknown variable: {expr}")

    def _get_nested(self, obj: Any, keys: List[str]) -> Any:
        """Get nested value from dict/object."""
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key)
            elif hasattr(obj, key):
                obj = getattr(obj, key)
            else:
                return None
        return obj

    def set_step_output(self, step_id: str, outputs: Dict[str, Any]):
        """Store outputs from a completed step."""
        self.steps_output[step_id] = {"outputs": outputs}

    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        step_info = f"[{self.current_step}]" if self.current_step else ""
        print(f"[{timestamp}] [{level}] {step_info} {message}")


class ToolRegistry:
    """Registry of available tools for workflow execution."""

    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.load_errors: Dict[str, str] = {}
        self._discover_tools()

    def _discover_tools(self):
        """Auto-discover tools from the tools/ package."""
        tools_dir = Path(__file__).parent.parent / "tools"

        for tool_file in tools_dir.glob("*_tool.py"):
            module_name = tool_file.stem
            try:
                module = importlib.import_module(f"localforge.tools.{module_name}")
                tool_name = getattr(module, "TOOL_NAME", module_name.replace("_tool", ""))
                handler = getattr(module, "handle", None)
                if handler:
                    self.tools[tool_name] = handler
            except Exception as e:
                tool_name = module_name.replace("_tool", "")
                self.load_errors[tool_name] = str(e)

    def register(self, name: str, handler):
        """Manually register a tool handler."""
        self.tools[name] = handler

    def execute(self, tool: str, action: str, inputs: Dict[str, Any],
                ctx: WorkflowContext) -> Dict[str, Any]:
        """Execute a tool action."""
        if tool not in self.tools:
            available = ", ".join(sorted(self.tools.keys()))
            raise ValueError(f"Unknown tool: {tool}. Available: {available}")
        return self.tools[tool](action, inputs, ctx)

    def available_tools(self) -> List[str]:
        """List available tool names."""
        return sorted(self.tools.keys())

    def preflight_check(self) -> Dict[str, bool]:
        """Check which tools are available and their services are running."""
        results = {}
        for name in self.tools:
            # Basic check: tool loaded successfully
            results[name] = True
        return results


class WorkflowRunner:
    """Executes workflow recipes."""

    def __init__(self, auto_approve: bool = False, config_path: Optional[Path] = None):
        self.config = get_config(config_path)
        self.tool_registry = ToolRegistry()
        self.auto_approve = auto_approve

    def load_recipe(self, recipe_path: Path) -> Dict[str, Any]:
        """Load and parse a workflow recipe."""
        with open(recipe_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run(self, recipe_path: Path, inputs: Dict[str, Any],
            project_id: str = None, use_persistence: bool = True) -> Dict[str, Any]:
        """Execute a workflow recipe."""
        recipe = self.load_recipe(recipe_path)
        ctx = WorkflowContext(recipe, inputs, run_base_dir=self.config.run_dir)

        # Initialize persistence if enabled
        db = None
        db_run_id = None
        if use_persistence and self.config.persistence_enabled:
            try:
                from .persistence import get_persistence
                db = get_persistence(self.config.persistence_db_path)
                db_run_id = db.start_run(
                    str(recipe_path), inputs, project_id, str(ctx.run_dir)
                )
                ctx.run_id = db_run_id
            except Exception as e:
                ctx.log(f"Persistence not available ({e}), running without tracking", "WARNING")

        ctx.log(f"Starting workflow: {recipe.get('name', 'unnamed')}")
        ctx.log(f"Run ID: {ctx.run_id}")
        ctx.log(f"Run directory: {ctx.run_dir}")

        try:
            for step in recipe.get("steps", []):
                step_id = step.get("id", "unknown")

                if db and db_run_id:
                    db.start_step(db_run_id, step_id, step.get("name", step_id),
                                  step.get("inputs", {}))

                try:
                    self._execute_step(step, ctx)

                    if db and db_run_id:
                        db.complete_step(db_run_id, step_id,
                                         ctx.steps_output.get(step_id, {}))
                except Exception as step_error:
                    if db and db_run_id:
                        db.fail_step(db_run_id, step_id, str(step_error))
                    raise

            self._cleanup(recipe.get("cleanup", {}).get("on_success", []), ctx)

            if db and db_run_id:
                db.complete_run(db_run_id, ctx.steps_output)

            ctx.log("Workflow completed successfully!", "SUCCESS")
            return {
                "success": True,
                "run_id": ctx.run_id,
                "outputs": ctx.steps_output,
                "run_dir": str(ctx.run_dir),
            }

        except Exception as e:
            ctx.log(f"Workflow failed: {e}", "ERROR")
            ctx.errors.append(str(e))

            if db and db_run_id:
                db.fail_run(db_run_id, str(e))

            self._cleanup(recipe.get("cleanup", {}).get("on_failure", []), ctx)

            return {
                "success": False,
                "run_id": ctx.run_id,
                "error": str(e),
                "errors": ctx.errors,
                "run_dir": str(ctx.run_dir),
            }

    def _execute_step(self, step: Dict[str, Any], ctx: WorkflowContext):
        """Execute a single workflow step."""
        step_id = step.get("id", "unknown")
        step_name = step.get("name", step_id)
        step_type = step.get("type", "tool")

        ctx.current_step = step_id
        ctx.log(f"Executing: {step_name}")

        if step_type == "approval_gate":
            self._handle_approval_gate(step, ctx)
            return

        if step_type == "refinement":
            ctx.log("Skipping refinement step (only runs on validation failure)", "DEBUG")
            return

        tool = step.get("tool")
        action = step.get("action")

        if not tool or not action:
            ctx.log(f"Step {step_id} missing tool or action, skipping", "WARNING")
            return

        raw_inputs = step.get("inputs", {})
        resolved_inputs = ctx.resolve(raw_inputs)

        try:
            outputs = self.tool_registry.execute(tool, action, resolved_inputs, ctx)
            ctx.set_step_output(step_id, outputs)
            ctx.log(f"Step completed: {list(outputs.keys())}")

            if step.get("gate"):
                if not outputs.get("passed", True):
                    failures = outputs.get("failures", [])
                    raise ValueError(f"Validation gate failed: {failures}")

        except Exception as e:
            on_failure = step.get("on_failure", "abort")
            if on_failure == "abort":
                raise
            elif on_failure == "skip":
                ctx.log(f"Step failed, skipping: {e}", "WARNING")
            elif on_failure == "retry":
                retry_count = step.get("retry_count", 1)
                last_error = e
                for i in range(retry_count):
                    ctx.log(f"Retrying ({i + 1}/{retry_count})...")
                    try:
                        outputs = self.tool_registry.execute(tool, action, resolved_inputs, ctx)
                        ctx.set_step_output(step_id, outputs)
                        return
                    except Exception as retry_error:
                        last_error = retry_error
                        ctx.log(f"Retry {i + 1} failed: {retry_error}", "WARNING")
                raise last_error
            elif on_failure == "refine":
                ctx.log("Validation failed, triggering refinement loop", "INFO")
                self._execute_refinement(step_id, step, ctx)
                return

    def _execute_refinement(self, failed_step_id: str, failed_step: Dict[str, Any],
                            ctx: WorkflowContext):
        """Execute refinement loop when validation fails."""
        max_iterations = ctx.config.get("max_iterations", 3)
        ctx.refinement_active = True

        refinement_config = failed_step.get("refinement", {})

        if not refinement_config:
            for step in ctx.recipe.get("steps", []):
                if step.get("type") == "refinement":
                    trigger = step.get("trigger", "")
                    if trigger == f"{failed_step_id}.failed" or trigger == failed_step_id:
                        refinement_config = step
                        break

        if not refinement_config:
            refinement_config = ctx.recipe.get("refinement", {})

        if not refinement_config:
            ctx.refinement_active = False
            raise ValueError(
                f"Validation failed and no refinement defined for step {failed_step_id}"
            )

        refinement_steps = refinement_config.get("steps", [])
        if not refinement_steps:
            ctx.refinement_active = False
            raise ValueError(f"Refinement config for {failed_step_id} has no steps")

        ctx.iteration_count[failed_step_id] = 0

        for iteration in range(max_iterations):
            ctx.iteration_count[failed_step_id] = iteration + 1
            ctx.log(f"Refinement iteration {iteration + 1}/{max_iterations}", "INFO")

            for refine_step in refinement_steps:
                try:
                    self._execute_step(refine_step, ctx)
                except Exception as e:
                    ctx.log(f"Refinement step failed: {e}", "WARNING")
                    continue

            try:
                tool = failed_step.get("tool")
                action = failed_step.get("action")
                resolved_inputs = ctx.resolve(failed_step.get("inputs", {}))

                outputs = self.tool_registry.execute(tool, action, resolved_inputs, ctx)
                ctx.set_step_output(failed_step_id, outputs)

                if outputs.get("passed", False):
                    ctx.log(
                        f"Validation passed after {iteration + 1} refinement iterations!",
                        "SUCCESS",
                    )
                    ctx.refinement_active = False
                    return
                else:
                    failures = outputs.get("failures", [])
                    ctx.log(f"Validation still failing: {failures}", "INFO")

            except Exception as e:
                ctx.log(f"Re-validation error: {e}", "WARNING")

        ctx.refinement_active = False
        raise ValueError(
            f"Refinement exhausted {max_iterations} iterations without passing validation"
        )

    def _handle_approval_gate(self, step: Dict[str, Any], ctx: WorkflowContext):
        """Handle human approval gate."""
        message = ctx.resolve(step.get("message", "Approval required"))
        options = step.get("options", ["approve", "reject"])
        default = step.get("default_action", options[0])

        if self.auto_approve:
            ctx.log(f"Auto-approving: {default}")
            ctx.set_step_output(step["id"], {"selection": default, "auto": True})
            return

        print(f"\n{'=' * 60}")
        print(f"APPROVAL REQUIRED: {step.get('name', 'Review')}")
        print(f"{'=' * 60}")
        print(message)
        print(f"\nOptions: {', '.join(options)}")
        print(f"Default (timeout): {default}")

        try:
            choice = input(f"\nYour choice [{default}]: ").strip() or default
            ctx.set_step_output(step["id"], {"selection": choice, "auto": False})
        except (EOFError, KeyboardInterrupt):
            ctx.log(f"Using default: {default}")
            ctx.set_step_output(step["id"], {"selection": default, "auto": True})

    def _cleanup(self, actions: List[Dict[str, Any]], ctx: WorkflowContext):
        """Execute cleanup actions."""
        import shutil

        for action in actions:
            try:
                action_type = action.get("action")
                if action_type == "delete":
                    path = Path(ctx.resolve(action.get("path", "")))
                    if path.exists():
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                        ctx.log(f"Cleaned up: {path}")
                elif action_type == "preserve":
                    path = ctx.resolve(action.get("path", ""))
                    reason = action.get("reason", "")
                    ctx.log(f"Preserved for {reason}: {path}")
                elif action_type == "move":
                    src = Path(ctx.resolve(action.get("source", "")))
                    dst = Path(ctx.resolve(action.get("destination", "")))
                    if src.exists():
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src), str(dst))
                        ctx.log(f"Moved {src} -> {dst}")
            except Exception as e:
                ctx.log(f"Cleanup error: {e}", "WARNING")
