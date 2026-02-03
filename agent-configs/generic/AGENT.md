# LocalForge — Agent Instructions

LocalForge runs multi-step YAML pipelines using local AI services (Ollama, Stable Diffusion, Blender, FFmpeg). It saves tokens by delegating grunt work to free local models.

## Commands
```bash
python -m localforge health                          # Check services
python -m localforge list                            # List recipes
python -m localforge run <recipe> --list-inputs      # Show recipe inputs
python -m localforge run <recipe> --input key=value --auto-approve  # Execute
```

## When to Use
- Image generation (sprites, tilesets, textures) → SD recipes
- Audio/music generation → audio recipes
- 3D models → Blender recipes
- Bulk text processing → Ollama recipes

## Key Recipes
| Recipe | Services |
|--------|----------|
| `recipes/getting-started/hello-localforge.yaml` | None (engine test) |
| `recipes/getting-started/hello-ollama.yaml` | Ollama |
| `recipes/examples/game-sprite.yaml` | Ollama + SD |
| `recipes/examples/tileset.yaml` | Ollama + SD |
| `recipes/examples/music-track.yaml` | Ollama + MusicGen |
| `recipes/examples/3d-model.yaml` | Blender |

## Creating Recipes
Copy `recipes/TEMPLATE.yaml` and modify. See `docs/RECIPE-AUTHORING.md` for the full format.

## Token Strategy
Use local Ollama models for grunt work. Reserve the paid agent for reasoning and orchestration.
