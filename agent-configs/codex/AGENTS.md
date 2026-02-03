# AGENTS.md — LocalForge Integration for Codex

## LocalForge Workflow Runner
Multi-step YAML pipelines for local AI services.

### Running Recipes
```bash
python -m localforge run <recipe.yaml> --input key=value --auto-approve
```

### Listing Recipes
```bash
python -m localforge list
```

### Health Check
```bash
python -m localforge health
```

### Token Optimization
Delegate bulk text work to local Ollama models via recipes.
Reserve the paid agent for orchestration and reasoning.
