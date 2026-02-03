# LocalForge — Agent Instructions

LocalForge runs multi-step YAML pipelines using local AI services.

## Commands
- `python -m localforge run <recipe> --auto-approve` — Execute a pipeline
- `python -m localforge list` — List available recipes
- `python -m localforge health` — Check service status
- `python -m localforge run <recipe> --list-inputs` — Show recipe inputs

## Key Recipes
See `recipes/` directory. Copy `recipes/TEMPLATE.yaml` to create new ones.

## Token Savings
Use local Ollama models for grunt work. Reserve the paid agent for reasoning.
