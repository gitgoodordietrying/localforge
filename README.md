# LocalForge

A local-first workflow orchestrator that uses cheap local LLMs as workers to save tokens on the paid agent you're running.

You have a CLI agent (Claude Code, Codex, Gemini CLI, etc.) that costs real money per token. LocalForge puts local models like Ollama to work as grunt labor — generating prompts, processing text, classifying data — while your paid agent stays in the driver's seat. You define multi-step pipelines as YAML recipes that chain local LLMs, image generators, media tools, and custom scripts. One command runs the whole pipeline.

**Key insight:** Don't burn $5 of Claude tokens on work that a free local Ollama model can do in 2 seconds.

```
┌─────────────────────────────────────┐
│  PAID AGENT (Claude Code, Codex...) │  ← Orchestration + reasoning only
│  Decides WHAT to do, invokes recipes │
└────────────────┬────────────────────┘
                 │ calls
┌────────────────▼────────────────────┐
│  LOCALFORGE ENGINE (runner.py)       │  ← Free, runs locally
│  Executes YAML recipe step-by-step   │
└────────────────┬────────────────────┘
                 │ delegates to
┌────────────────▼────────────────────┐
│  LOCAL WORKERS                       │  ← Free, runs locally
│  Ollama (text) · SD (images)         │
│  Blender (3D) · FFmpeg (media)       │
│  Custom scripts · Any HTTP service   │
└──────────────────────────────────────┘
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-username/localforge.git
cd localforge
pip install -r requirements.txt

# Interactive setup — detects your local services
python -m localforge init

# Run a recipe
python -m localforge run recipes/getting-started/hello-ollama.yaml \
  --input prompt="Tell me a joke" --auto-approve
```

**Prerequisites:** Python 3.9+ and at least one local service (Ollama recommended).

## What Can It Do?

LocalForge is domain-agnostic. The engine runs any multi-step pipeline; the recipes define the domain.

| Use Case | Services Used | Example Recipe |
|----------|---------------|----------------|
| Game sprites with background removal | Ollama + SD | `recipes/examples/game-sprite.yaml` |
| Seamless texture tiles | Ollama + SD | `recipes/examples/tileset.yaml` |
| Background music for games | Ollama + MusicGen + FFmpeg | `recipes/examples/music-track.yaml` |
| 3D model generation | Blender | `recipes/examples/3d-model.yaml` |
| Text processing pipeline | Ollama | `recipes/getting-started/hello-ollama.yaml` |

## Writing Recipes

Recipes are YAML files that define inputs, steps, and outputs. Each step calls a tool with inputs and produces outputs that later steps can reference.

```yaml
name: "hello-world"
version: "1.0"
description: "Generate and save a greeting"

inputs:
  - name: "subject"
    type: "string"
    required: true
    description: "Who to greet"

steps:
  - id: "generate"
    name: "Generate greeting"
    tool: "ollama"
    action: "generate"
    inputs:
      model: "llama3.2:3b"
      prompt: "Write a creative one-line greeting for {{inputs.subject}}"

  - id: "save"
    name: "Save result"
    tool: "file_ops"
    action: "copy"
    inputs:
      source: "{{steps.generate.outputs.response}}"
      destination: "./greeting.txt"
```

### Variable Resolution

```
{{inputs.name}}                  → User-provided input
{{steps.step_id.outputs.key}}    → Output from a previous step
{{config.setting}}               → Recipe config value
{{temp_dir}}                     → Temp directory for this run
{{workflow.run_id}}              → Unique run identifier
{{timestamp}}                    → Current ISO timestamp
```

### Error Handling

Each step supports `on_failure` strategies:

- `abort` — Stop the workflow (default)
- `skip` — Log warning, continue to next step
- `retry` — Retry N times
- `refine` — Enter refinement loop with validation feedback

## Built-in Tools

| Tool | Actions | Service Required |
|------|---------|-----------------|
| `ollama` | generate | Ollama |
| `sd_client` | txt2img, img2img, get_models | Stable Diffusion WebUI |
| `image_processor` | remove_bg, resize, make_seamless, tile_preview, create_idle_animation, create_directional_sheet, assemble_sheet | None (Pillow) |
| `validator` | check_image, check_tileset, check_sprites | None (Pillow + numpy) |
| `file_ops` | copy, move, delete, mkdir, list | None |
| `batch` | foreach | None |
| `blender` | render, create_primitive, create_text_3d, generate_texture, create_dice | Blender |
| `ffmpeg` | convert, normalize, loop, trim, get_duration | FFmpeg |
| `musicgen` | generate | MusicGen |
| `acestep` | generate | ACE-Step |
| `script` | run | None |

## Project Structure

```
localforge/
├── engine/
│   ├── runner.py          # Workflow engine
│   ├── config.py          # Configuration loader
│   └── persistence.py     # SQLite job tracking
├── tools/
│   ├── ollama_tool.py     # Local LLM integration
│   ├── sd_tool.py         # Stable Diffusion
│   ├── image_tool.py      # Image processing
│   ├── validator_tool.py  # Quality gates
│   ├── file_tool.py       # File operations
│   ├── batch_tool.py      # Iteration
│   ├── blender_tool.py    # 3D rendering
│   ├── ffmpeg_tool.py     # Media processing
│   ├── musicgen_tool.py   # Music generation
│   ├── acestep_tool.py    # ACE-Step music
│   └── script_tool.py     # Custom scripts
├── clients/
│   ├── sd_client.py       # SD WebUI API client
│   └── blender_client.py  # Blender subprocess client
├── recipes/
│   ├── getting-started/   # Minimal examples
│   ├── examples/          # Domain-diverse examples
│   └── TEMPLATE.yaml      # Recipe authoring reference
├── scripts/
│   ├── setup.py           # localforge init
│   └── health_check.py    # Service detection
├── docs/                  # Documentation
├── localforge.yaml.example
├── requirements.txt
└── README.md
```

## Configuration

LocalForge reads from `localforge.yaml` in your project root (or `~/.localforge/config.yaml` globally):

```yaml
# localforge.yaml
workspace: ~/localforge-workspace
output_dir: ~/localforge-workspace/output

services:
  ollama:
    host: http://localhost:11434
    default_model: llama3.2:3b
  sd:
    host: http://localhost:7860
    timeout: 120
  blender:
    path: /usr/bin/blender  # or C:\Program Files\Blender Foundation\Blender 4.x\blender.exe
  ffmpeg:
    path: ffmpeg  # uses PATH by default

persistence:
  enabled: true
  db_path: ~/.localforge/runs.db
```

## Agent Integration

LocalForge works with any CLI agent. Example AGENT.md for your project:

```markdown
## LocalForge Workflows
Run `python -m localforge run <recipe> --auto-approve` to execute pipelines.
Use `python -m localforge list` to see available recipes.
Use `python -m localforge health` to check which services are running.
```

See `agent-configs/` for ready-made config examples for Claude Code, Cursor, Codex, and others.

## Adding Custom Tools

Drop a Python file in `tools/` that implements the tool interface:

```python
# tools/my_tool.py
def handle(action: str, inputs: dict, ctx) -> dict:
    if action == "my_action":
        # Do work...
        return {"result": "done"}
    raise ValueError(f"Unknown action: {action}")

TOOL_NAME = "my_tool"
TOOL_ACTIONS = ["my_action"]
```

The engine auto-discovers tools in the `tools/` directory.

## Requirements

**Minimum:** Python 3.9+, PyYAML, requests

**Full:** Pillow, numpy, rembg (for AI background removal)

**Services (install what you need):**
- [Ollama](https://ollama.ai) — Local LLMs (recommended)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) — Image generation
- [Blender](https://www.blender.org) — 3D modeling and rendering
- [FFmpeg](https://ffmpeg.org) — Audio/video processing
- [MusicGen](https://github.com/facebookresearch/audiocraft) — Music generation

## License

MIT
