# LocalForge — Agent Instructions

LocalForge runs multi-step YAML pipelines using local AI services (Ollama, Stable Diffusion, Blender, FFmpeg, Pillow). It saves tokens by delegating grunt work to free local models.

## Commands
```bash
python -m localforge health                          # Check services
python -m localforge list                            # List recipes
python -m localforge system                          # Hardware profile
python -m localforge run <recipe> --list-inputs      # Show recipe inputs
python -m localforge run <recipe> --input key=value --auto-approve  # Execute
```

## When to Use
- Code review and analysis → Ollama recipes
- Data extraction and text processing → Ollama recipes
- Batch image operations → Pillow recipes
- Image generation (sprites, textures) → SD recipes
- Audio/music generation → audio recipes
- 3D models → Blender recipes

## Key Recipes
| Recipe | Services |
|--------|----------|
| `recipes/getting-started/hello-localforge.yaml` | None (engine test) |
| `recipes/getting-started/hello-ollama.yaml` | Ollama |
| `recipes/examples/code-review.yaml` | Ollama |
| `recipes/examples/data-extract.yaml` | Ollama |
| `recipes/examples/batch-resize.yaml` | None (Pillow) |
| `recipes/examples/text-pipeline.yaml` | Ollama |
| `recipes/domains/game-dev/game-sprite.yaml` | Ollama + SD |
| `recipes/domains/game-dev/tileset.yaml` | Ollama + SD |
| `recipes/domains/game-dev/music-track.yaml` | Ollama + MusicGen |
| `recipes/domains/game-dev/3d-model.yaml` | Blender |

## Creating Recipes
Copy `recipes/TEMPLATE.yaml` and modify. See `docs/RECIPE-AUTHORING.md` for the full format.

## Token Strategy
Use local Ollama models for grunt work. Reserve the paid agent for reasoning and orchestration.
