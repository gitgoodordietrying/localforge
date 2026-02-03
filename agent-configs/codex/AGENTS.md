# AGENTS.md — LocalForge Integration for Codex

## What This Is
LocalForge is a local-first AI orchestrator. It chains local services (Ollama, Stable Diffusion, Blender, FFmpeg, Pillow) via YAML recipes, saving tokens on the paid agent.

## When to Use It
Use `python -m localforge run` when the task involves:
- Code review or analysis — Ollama recipes
- Data extraction and text processing — Ollama recipes
- Batch image operations (resize, convert) — Pillow recipes
- Image generation (sprites, textures) — SD recipes
- Audio generation (music, sound effects) — audio recipes
- 3D model creation — Blender recipes
- Any multi-step pipeline that can run locally

## Commands
```bash
python -m localforge health                          # Check services
python -m localforge list                            # List recipes
python -m localforge system                          # Hardware profile
python -m localforge run <recipe> --list-inputs      # Show recipe inputs
python -m localforge run <recipe> --input key=value --auto-approve  # Execute
```

## Key Recipes
| Recipe | What It Does | Services Needed |
|--------|-------------|-----------------|
| `recipes/getting-started/hello-localforge.yaml` | Engine test (no services) | None |
| `recipes/getting-started/hello-ollama.yaml` | LLM text generation | Ollama |
| `recipes/examples/code-review.yaml` | Code review pipeline | Ollama |
| `recipes/examples/data-extract.yaml` | Structured data extraction | Ollama |
| `recipes/examples/batch-resize.yaml` | Batch image resize | None (Pillow) |
| `recipes/examples/text-pipeline.yaml` | Multi-step text processing | Ollama |
| `recipes/domains/game-dev/game-sprite.yaml` | Sprite with bg removal | Ollama + SD |
| `recipes/domains/game-dev/tileset.yaml` | Seamless tileable texture | Ollama + SD |
| `recipes/domains/game-dev/music-track.yaml` | Background music | Ollama + MusicGen |
| `recipes/domains/game-dev/3d-model.yaml` | 3D model generation | Blender |

## Token Strategy
Delegate bulk work to Ollama via recipes. Reserve the paid agent for reasoning and orchestration. Copy `recipes/TEMPLATE.yaml` to create new pipelines.
