# Tool Development Guide

## Adding a Custom Tool

1. Create a file in `tools/` named `<name>_tool.py`
2. Export `TOOL_NAME` and `handle()`
3. Use it in recipes with `tool: "<name>"`

## Minimal Example

```python
# tools/weather_tool.py
"""Weather data tool."""

import requests

TOOL_NAME = "weather"
TOOL_ACTIONS = ["current", "forecast"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle weather operations."""
    if action == "current":
        city = inputs.get("city", "London")
        # Your implementation here
        return {"temperature": 20, "condition": "sunny", "city": city}

    elif action == "forecast":
        city = inputs.get("city", "London")
        days = inputs.get("days", 3)
        return {"forecast": [{"day": i, "temp": 20 + i} for i in range(days)]}

    raise ValueError(f"Unknown weather action: {action}")
```

Then use it in a recipe:

```yaml
steps:
  - id: "get_weather"
    tool: "weather"
    action: "current"
    inputs:
      city: "{{inputs.city}}"
```

## Tool Interface

### Required Exports

- `TOOL_NAME` (str): The name used in recipe `tool:` fields
- `handle(action, inputs, ctx)` (function): The entry point

### Parameters

- `action` (str): The action name from the recipe
- `inputs` (dict): Resolved inputs from the recipe step
- `ctx` (WorkflowContext): Provides logging, temp_dir, step outputs, etc.

### Return Value

Return a `dict` of outputs. These become available via `{{steps.step_id.outputs.key}}`.

### Using Context

```python
def handle(action, inputs, ctx):
    ctx.log("Starting work...", "INFO")
    ctx.log("Something went wrong", "WARNING")

    # Use temp directory for intermediate files
    output_path = ctx.temp_dir / "result.txt"

    # Access config
    from engine.config import get_config
    config = get_config()
    host = config.service("my_service").get("host", "localhost")
```

### Optional Exports

- `TOOL_ACTIONS` (list): Document available actions (not enforced)

## Auto-Discovery

The `ToolRegistry` scans `tools/*_tool.py` at startup. If your module fails to import (missing dependency, etc.), it's silently skipped. Run `python -m localforge health` to verify tools loaded correctly.

## Accessing Services

Use `engine.config.get_config()` to read service configuration from `localforge.yaml`. This keeps connection details out of tool code and lets users configure their setup.

```python
from engine.config import get_config

config = get_config()
host = config.service("my_api").get("host", "http://localhost:9000")
```
