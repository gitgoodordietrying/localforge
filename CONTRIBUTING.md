# Contributing to LocalForge

Contributions are welcome. Here's how to get involved.

## Reporting Issues

- Search [existing issues](https://github.com/gitgoodordietrying/localforge/issues) first
- Include: Python version, OS, error message, recipe (if applicable)
- For service-related issues, include `python -m localforge health` output

## Development Setup

```bash
git clone https://github.com/gitgoodordietrying/localforge.git
cd localforge
pip install -e ".[full]"
python -m pytest tests/
```

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Run `python -m pytest tests/` and ensure all tests pass
5. Update documentation if you changed behavior
6. Submit a PR with a clear description of what changed and why

## Adding a New Tool

1. Create `tools/my_tool.py` implementing the tool interface:
   ```python
   TOOL_NAME = "my_tool"
   TOOL_ACTIONS = ["action_name"]

   def handle(action: str, inputs: dict, ctx) -> dict:
       if action == "action_name":
           # Do work...
           return {"result": "value"}
       raise ValueError(f"Unknown action: {action}")
   ```
2. The engine auto-discovers files matching `tools/*_tool.py`
3. Add a test in `tests/`
4. Update `recipes/TEMPLATE.yaml` with the new tool's actions
5. Document the tool in README.md's Built-in Tools table

## Code Style

- Python 3.9+ compatible
- Type hints on public function signatures
- Docstrings on classes and public functions
- Handle errors with clear messages that help users fix the problem
- No hardcoded paths — use `engine/config.py` for service locations

## What We're Looking For

- New tool integrations (Whisper, ComfyUI, etc.)
- Recipe contributions for new domains
- Cross-platform fixes
- Documentation improvements
- Test coverage improvements
