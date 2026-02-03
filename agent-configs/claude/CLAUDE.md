# CLAUDE.md — LocalForge Integration

## What This Is
LocalForge is a local workflow orchestrator. It runs multi-step YAML pipelines using local AI services (Ollama, Stable Diffusion, Blender, FFmpeg) so you don't spend tokens on grunt work.

## When to Use It
- Generating images (sprites, tilesets, textures) — use SD recipes
- Generating music or sound effects — use audio recipes
- Bulk text processing (summarization, classification) — use Ollama recipes
- 3D model creation — use Blender recipes
- Any multi-step pipeline that chains local tools

## Commands
```bash
# Check what's available
python -m localforge health          # Which services are running
python -m localforge list            # Available recipes

# Run a recipe
python -m localforge run <recipe.yaml> \
  --input "key=value" --auto-approve

# See what a recipe needs before running
python -m localforge run <recipe.yaml> --list-inputs
```

## Example Workflows
```bash
# Generate a game sprite
python -m localforge run recipes/examples/game-sprite.yaml \
  --input "description=spaceship" --input "output_path=./ship.png" --auto-approve

# Generate a tileable texture
python -m localforge run recipes/examples/tileset.yaml \
  --input "theme=grass" --input "output_path=./grass.png" --auto-approve

# Generate background music
python -m localforge run recipes/examples/music-track.yaml \
  --input "genre=orchestral" --input "mood=epic" \
  --input "output_path=./theme.wav" --auto-approve

# Generate a 3D model
python -m localforge run recipes/examples/3d-model.yaml \
  --input "description=treasure chest" --input "output_path=./chest.glb" --auto-approve
```

## Token Savings Strategy
Use Ollama for bulk text work (prompt engineering, summarization, classification, data extraction). Only use Claude for orchestration, reasoning, and complex decisions. A recipe that calls Ollama 10 times costs $0 in tokens vs $0.50+ if Claude did the same work.

## Creating New Recipes
Copy `recipes/TEMPLATE.yaml` and modify it. The engine auto-discovers tools from `tools/`. See `docs/RECIPE-AUTHORING.md` for the full recipe format reference.
