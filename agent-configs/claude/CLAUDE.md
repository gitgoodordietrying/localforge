# CLAUDE.md — LocalForge Integration

## What This Is
LocalForge is a local-first AI orchestrator. It runs multi-step YAML pipelines using local services (Ollama, Stable Diffusion, Blender, FFmpeg, Pillow, any CLI tool) so you don't spend tokens on grunt work.

## When to Use It
- Bulk text processing (summarization, classification, extraction) — Ollama recipes
- Code review and analysis — Ollama recipes
- Image processing (resize, convert, batch operations) — Pillow recipes
- Image generation (sprites, textures, art) — SD recipes
- Audio/music generation — audio recipes
- 3D model creation — Blender recipes
- Any multi-step pipeline that chains local tools

## Commands
```bash
# Check what's available
python -m localforge health          # Which services are running
python -m localforge list            # Available recipes
python -m localforge system          # Hardware profile and model recommendations

# Run a recipe
python -m localforge run <recipe.yaml> \
  --input "key=value" --auto-approve

# See what a recipe needs before running
python -m localforge run <recipe.yaml> --list-inputs
```

## Example Workflows
```bash
# Code review (Ollama only)
python -m localforge run recipes/examples/code-review.yaml \
  --input "file_path=./src/main.py" --auto-approve

# Data extraction (Ollama only)
python -m localforge run recipes/examples/data-extract.yaml \
  --input "topic=contact info" --input "text=Call John at 555-0123" --auto-approve

# Batch image resize (no services needed)
python -m localforge run recipes/examples/batch-resize.yaml \
  --input "input_dir=./photos" --input "output_dir=./thumbs" --auto-approve

# Text processing pipeline
python -m localforge run recipes/examples/text-pipeline.yaml \
  --input "topic=artificial intelligence" --auto-approve

# Game sprite generation (Ollama + SD)
python -m localforge run recipes/domains/game-dev/game-sprite.yaml \
  --input "description=spaceship" --input "output_path=./ship.png" --auto-approve
```

## Token Savings Strategy
Use Ollama for bulk text work (prompt engineering, summarization, classification, data extraction). Only use Claude for orchestration, reasoning, and complex decisions. A recipe that calls Ollama 10 times costs $0 in tokens vs $0.50+ if Claude did the same work.

## Creating New Recipes
Copy `recipes/TEMPLATE.yaml` and modify it. The engine auto-discovers tools from `tools/`. See `docs/RECIPE-AUTHORING.md` for the full recipe format reference.
