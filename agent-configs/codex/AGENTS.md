# AGENTS.md — LocalForge Integration for Codex

## What This Is
LocalForge is a local workflow orchestrator. It chains local AI services (Ollama, Stable Diffusion, Blender, FFmpeg) via YAML recipes, saving tokens on the paid agent.

## When to Use It
Use `python -m localforge run` when the task involves:
- Image generation (sprites, tilesets, textures, icons)
- Audio generation (music tracks, sound effects)
- 3D model creation (primitives, dice, renders)
- Bulk text processing (prompt engineering, classification, summarization)
- Any multi-step pipeline that can run locally

## Commands
```bash
python -m localforge health                          # Check services
python -m localforge list                            # List recipes
python -m localforge run <recipe> --list-inputs      # Show recipe inputs
python -m localforge run <recipe> --input key=value --auto-approve  # Execute
```

## Key Recipes
| Recipe | What It Does | Services Needed |
|--------|-------------|-----------------|
| `recipes/getting-started/hello-localforge.yaml` | Engine test (no services) | None |
| `recipes/getting-started/hello-ollama.yaml` | LLM text generation | Ollama |
| `recipes/getting-started/hello-sd.yaml` | Image generation | SD WebUI |
| `recipes/examples/game-sprite.yaml` | Sprite with bg removal | Ollama + SD |
| `recipes/examples/tileset.yaml` | Seamless tileable texture | Ollama + SD |
| `recipes/examples/music-track.yaml` | Background music | Ollama + MusicGen |
| `recipes/examples/3d-model.yaml` | 3D model generation | Blender |

## Token Strategy
Delegate bulk work to Ollama via recipes. Reserve the paid agent for reasoning and orchestration. Copy `recipes/TEMPLATE.yaml` to create new pipelines.
