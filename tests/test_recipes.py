"""Tests for recipe loading and validation."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

RECIPES_DIR = Path(__file__).parent.parent / "recipes"


def get_all_recipes():
    """Collect all YAML recipe files."""
    recipes = []
    for recipe_path in RECIPES_DIR.rglob("*.yaml"):
        if recipe_path.name.startswith("."):
            continue
        recipes.append(recipe_path)
    return recipes


class TestRecipeParsing:
    @pytest.mark.parametrize("recipe_path", get_all_recipes(),
                             ids=lambda p: str(p.relative_to(RECIPES_DIR)))
    def test_recipe_is_valid_yaml(self, recipe_path):
        """Every recipe file should be valid YAML."""
        with open(recipe_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), f"{recipe_path.name} did not parse as a dict"

    @pytest.mark.parametrize("recipe_path", get_all_recipes(),
                             ids=lambda p: str(p.relative_to(RECIPES_DIR)))
    def test_recipe_has_required_fields(self, recipe_path):
        """Every recipe should have name, version, and steps."""
        with open(recipe_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "name" in data, f"{recipe_path.name} missing 'name'"
        assert "steps" in data, f"{recipe_path.name} missing 'steps'"

    @pytest.mark.parametrize("recipe_path", get_all_recipes(),
                             ids=lambda p: str(p.relative_to(RECIPES_DIR)))
    def test_steps_have_ids(self, recipe_path):
        """Every step should have an id."""
        with open(recipe_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for i, step in enumerate(data.get("steps", [])):
            assert "id" in step, f"{recipe_path.name} step {i} missing 'id'"

    @pytest.mark.parametrize("recipe_path", get_all_recipes(),
                             ids=lambda p: str(p.relative_to(RECIPES_DIR)))
    def test_steps_have_tool_and_action(self, recipe_path):
        """Every tool step should have tool and action fields."""
        with open(recipe_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for step in data.get("steps", []):
            step_type = step.get("type", "tool")
            if step_type in ("approval_gate", "refinement"):
                continue
            assert "tool" in step, f"{recipe_path.name} step '{step.get('id')}' missing 'tool'"
            assert "action" in step, f"{recipe_path.name} step '{step.get('id')}' missing 'action'"
