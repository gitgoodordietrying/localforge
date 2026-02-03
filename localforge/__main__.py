#!/usr/bin/env python3
"""
LocalForge CLI entry point.

Usage:
    python -m localforge run <recipe> [--input key=value] [--auto-approve]
    python -m localforge list [<directory>]
    python -m localforge health
    python -m localforge init
    python -m localforge history [--limit N]
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def cmd_run(args):
    """Run a workflow recipe."""
    # Add project root to path so imports work
    sys.path.insert(0, str(Path(__file__).parent))

    from engine.runner import WorkflowRunner

    recipe_path = Path(args.recipe)
    if not recipe_path.exists():
        print(f"Recipe not found: {recipe_path}")
        sys.exit(1)

    with open(recipe_path, "r", encoding="utf-8") as f:
        recipe = yaml.safe_load(f)

    if args.list_inputs:
        print(f"Workflow: {recipe.get('name', 'unnamed')}")
        print(f"Description: {recipe.get('description', 'No description')}")
        print("\nInputs:")
        for inp in recipe.get("inputs", []):
            req = "*" if inp.get("required", False) else " "
            default = f" (default: {inp.get('default')})" if "default" in inp else ""
            choices = f" [{', '.join(str(c) for c in inp.get('choices', []))}]" if "choices" in inp else ""
            print(f"  {req} {inp['name']}: {inp.get('description', '')}{choices}{default}")
        return

    # Parse inputs
    inputs = {}
    for item in args.input or []:
        if "=" in item:
            key, value = item.split("=", 1)
            inputs[key] = value

    # Apply defaults
    for inp in recipe.get("inputs", []):
        if inp["name"] not in inputs and "default" in inp:
            inputs[inp["name"]] = inp["default"]

    # Check required
    missing = [
        inp["name"]
        for inp in recipe.get("inputs", [])
        if inp.get("required", False) and inp["name"] not in inputs
    ]
    if missing:
        print(f"Missing required inputs: {', '.join(missing)}")
        print("Use --list-inputs to see all inputs")
        sys.exit(1)

    runner = WorkflowRunner(auto_approve=args.auto_approve)
    result = runner.run(recipe_path, inputs)

    if result["success"]:
        print(f"\nWorkflow completed successfully!")
        print(f"Run directory: {result['run_dir']}")
    else:
        print(f"\nWorkflow failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


def cmd_list(args):
    """List available recipes."""
    recipes_dir = Path(args.directory) if args.directory else Path(__file__).parent.parent / "recipes"

    if not recipes_dir.exists():
        print(f"Directory not found: {recipes_dir}")
        sys.exit(1)

    recipes = sorted(recipes_dir.rglob("*.yaml"))
    if not recipes:
        print("No recipes found.")
        return

    print(f"Available recipes in {recipes_dir}:\n")
    for recipe_path in recipes:
        if recipe_path.name.startswith("."):
            continue
        try:
            with open(recipe_path, "r", encoding="utf-8") as f:
                recipe = yaml.safe_load(f)
            name = recipe.get("name", recipe_path.stem)
            desc = recipe.get("description", "")
            rel = recipe_path.relative_to(recipes_dir)
            print(f"  {rel}")
            print(f"    {name}: {desc}")
        except Exception:
            print(f"  {recipe_path.relative_to(recipes_dir)} (parse error)")
    print()


def cmd_health(args):
    """Check service health."""
    sys.path.insert(0, str(Path(__file__).parent))

    import requests

    checks = {
        "Ollama": ("http://localhost:11434/api/tags", "GET"),
        "SD WebUI": ("http://localhost:7860/sdapi/v1/sd-models", "GET"),
    }

    print("LocalForge Service Health\n")

    for name, (url, method) in checks.items():
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                print(f"  {name}: RUNNING ({url})")
            else:
                print(f"  {name}: ERROR (status {resp.status_code})")
        except requests.exceptions.RequestException:
            print(f"  {name}: NOT RUNNING")

    # Check Blender
    import shutil
    blender = shutil.which("blender")
    if blender:
        print(f"  Blender: FOUND ({blender})")
    else:
        print(f"  Blender: NOT FOUND")

    # Check FFmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        print(f"  FFmpeg: FOUND ({ffmpeg})")
    else:
        print(f"  FFmpeg: NOT FOUND")

    print()


def cmd_init(args):
    """Interactive setup wizard."""
    sys.path.insert(0, str(Path(__file__).parent))
    from scripts.setup import run_setup
    run_setup()


def cmd_history(args):
    """Show workflow run history."""
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from engine.persistence import get_persistence
        db = get_persistence()
        runs = db.list_runs(limit=args.limit)

        if not runs:
            print("No workflow runs recorded.")
            return

        print(f"Recent workflow runs (last {args.limit}):\n")
        for run in runs:
            status_icon = {"completed": "+", "failed": "!", "running": "~"}.get(
                run["status"], "?"
            )
            print(f"  [{status_icon}] {run['id']} - {run['recipe_name']} ({run['status']})")
            print(f"      {run['created_at']}")
        print()
    except Exception as e:
        print(f"Could not load history: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog="localforge",
        description="LocalForge - Local-first workflow orchestrator",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run
    run_parser = subparsers.add_parser("run", help="Run a workflow recipe")
    run_parser.add_argument("recipe", type=str, help="Path to recipe YAML")
    run_parser.add_argument("--input", "-i", action="append", default=[],
                            help="Input as key=value")
    run_parser.add_argument("--auto-approve", "-y", action="store_true",
                            help="Auto-approve all gates")
    run_parser.add_argument("--list-inputs", action="store_true",
                            help="List recipe inputs and exit")

    # list
    list_parser = subparsers.add_parser("list", help="List available recipes")
    list_parser.add_argument("directory", nargs="?", help="Recipes directory")

    # health
    subparsers.add_parser("health", help="Check service health")

    # init
    subparsers.add_parser("init", help="Interactive setup")

    # history
    hist_parser = subparsers.add_parser("history", help="Show run history")
    hist_parser.add_argument("--limit", "-n", type=int, default=20)

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "health":
        cmd_health(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "history":
        cmd_history(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
