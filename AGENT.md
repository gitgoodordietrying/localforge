# LocalForge — Agent Instructions

LocalForge is a local-first workflow orchestrator. It runs multi-step YAML pipelines that delegate work to local services (Ollama, Stable Diffusion, Blender, FFmpeg, etc.), saving tokens by using free local LLMs for grunt work.

## Quick Reference

```bash
# Run a recipe
python -m localforge run <recipe.yaml> --input key=value --auto-approve

# List available recipes
python -m localforge list

# Check service health
python -m localforge health

# List recipe inputs
python -m localforge run <recipe.yaml> --list-inputs

# View run history
python -m localforge history
```

## Available Recipes

| Recipe | What It Does | Requires |
|--------|-------------|----------|
| `recipes/getting-started/hello-ollama.yaml` | Generate text | Ollama |
| `recipes/getting-started/hello-sd.yaml` | Generate image | SD WebUI |
| `recipes/examples/game-sprite.yaml` | Sprite with bg removal | Ollama + SD |
| `recipes/examples/tileset.yaml` | Seamless tile texture | Ollama + SD |
| `recipes/examples/music-track.yaml` | Background music | Ollama + MusicGen |
| `recipes/examples/3d-model.yaml` | 3D primitive export | Blender |
| `recipes/examples/text-pipeline.yaml` | Multi-step text processing | Ollama |

## When to Use LocalForge

Use `python -m localforge run` when:
- Generating images, textures, sprites, or 3D models
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
