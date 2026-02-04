# LocalForge — Agent Instructions

LocalForge is a local-first AI orchestrator. It runs multi-step YAML pipelines that delegate work to local services (Ollama, Stable Diffusion, Blender, FFmpeg, Pillow), saving tokens by using free local models for grunt work.

## Quick Reference

```bash
# Check what's available
python -m localforge health          # Which services are running
python -m localforge list            # Available recipes
python -m localforge system          # Hardware profile and model recommendations

# Run a recipe
python -m localforge run <recipe.yaml> --input key=value --auto-approve

# Inspect a recipe before running
python -m localforge run <recipe.yaml> --list-inputs

# View run history
python -m localforge history
```

## Available Recipes

| Recipe | What It Does | Requires |
|--------|-------------|----------|
| `recipes/getting-started/hello-localforge.yaml` | Engine test (no services) | None |
| `recipes/getting-started/hello-ollama.yaml` | Generate text | Ollama |
| `recipes/getting-started/hello-sd.yaml` | Generate image | SD WebUI |
| `recipes/examples/code-review.yaml` | Code review pipeline | Ollama |
| `recipes/examples/data-extract.yaml` | Structured data extraction | Ollama |
| `recipes/examples/batch-resize.yaml` | Batch image resize | None (Pillow) |
| `recipes/examples/text-pipeline.yaml` | Multi-step text processing | Ollama |
| `recipes/domains/game-dev/game-sprite.yaml` | Sprite with bg removal | Ollama + SD |
| `recipes/domains/game-dev/tileset.yaml` | Seamless tile texture | Ollama + SD |
| `recipes/domains/game-dev/music-track.yaml` | Background music | Ollama + MusicGen |
| `recipes/domains/game-dev/3d-model.yaml` | 3D primitive export | Blender |

## When to Use LocalForge

Use `python -m localforge run` when:
- Code review or analysis — delegate to local LLM
- Data extraction or text processing — delegate to local LLM
- Batch image operations (resize, convert) — runs locally via Pillow
- Generating images, textures, sprites — requires SD WebUI
- Processing batch media (audio normalization, format conversion)
- Running multi-step pipelines that would waste tokens if done step-by-step
- Any task where a local LLM can do the work instead of the paid agent

## Writing New Recipes

Copy `recipes/TEMPLATE.yaml` and modify. Recipes chain tools via variable references:
```yaml
steps:
  - id: "step1"
    tool: "ollama"
    action: "generate"
    inputs:
      prompt: "{{inputs.user_input}}"

  - id: "step2"
    tool: "sd_client"
    action: "txt2img"
    inputs:
      prompt: "{{steps.step1.outputs.sd_prompt}}"
```

See `docs/RECIPE-AUTHORING.md` for the full recipe format reference.
