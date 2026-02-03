# CLAUDE.md — LocalForge Integration

## Workflow Runner
Run `python -m localforge run <recipe> --auto-approve` to execute pipelines.
Use `python -m localforge list` to see available recipes.
Use `python -m localforge health` to check which services are running.

## Token Savings
Use Ollama for bulk text work (prompt engineering, summarization, classification).
Only use Claude for orchestration, reasoning, and complex decisions.

## Commands
```bash
python -m localforge run recipes/examples/game-sprite.yaml \
  --input "description=spaceship" --input "output_path=./ship.png" --auto-approve
python -m localforge run recipes/examples/tileset.yaml \
  --input "theme=grass" --input "output_path=./tile.png" --auto-approve
python -m localforge health
```
