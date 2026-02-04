# LocalForge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/gitgoodordietrying/localforge/actions/workflows/tests.yml/badge.svg)](https://github.com/gitgoodordietrying/localforge/actions/workflows/tests.yml)

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
git clone https://github.com/gitgoodordietrying/localforge.git
cd localforge
pip install -e .

# Interactive setup — detects your local services
python -m localforge init

# Verify the engine works (no services needed)
python -m localforge run recipes/getting-started/hello-localforge.yaml --auto-approve

# Run a recipe with Ollama
python -m localforge run recipes/getting-started/hello-ollama.yaml \
  --input prompt="Tell me a joke" --auto-approve
```

**Prerequisites:** Python 3.9+ and at least one local service ([Ollama](https://ollama.com) recommended).

## What Can It Do?

LocalForge is domain-agnostic. The engine runs any multi-step pipeline; the recipes define the domain.

| Use Case | Services Used | Example Recipe |
|----------|---------------|----------------|
| Batch image resize | None (Pillow) | `recipes/examples/batch-resize.yaml` |
| Code review | Ollama | `recipes/examples/code-review.yaml` |
| Data extraction from text | Ollama | `recipes/examples/data-extract.yaml` |
| Text processing pipeline | Ollama | `recipes/examples/text-pipeline.yaml` |
| Game sprites with background removal | Ollama + SD | `recipes/domains/game-dev/game-sprite.yaml` |
| Seamless texture tiles | Ollama + SD | `recipes/domains/game-dev/tileset.yaml` |
| Background music | Ollama + MusicGen + FFmpeg | `recipes/domains/game-dev/music-track.yaml` |
| 3D model generation | Blender | `recipes/domains/game-dev/3d-model.yaml` |
| Engine test (zero dependencies) | None | `recipes/getting-started/hello-localforge.yaml` |

## Writing Recipes

Recipes are YAML files that define inputs, steps, and outputs. Each step calls a tool with inputs and produces outputs that later steps can reference. See [docs/RECIPE-AUTHORING.md](docs/RECIPE-AUTHORING.md) for the full format reference.

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
- `retry` — Retry N times (set `retry_count`)
- `refine` — Enter refinement loop with validation feedback

## Built-in Tools

| Tool | Actions | Requires |
|------|---------|----------|
| `ollama` | generate | Ollama |
| `sd_client` | txt2img, img2img, get_models | SD WebUI |
| `image_processor` | remove_bg, resize, batch_remove_bg, make_seamless, tile_preview, create_idle_animation, create_directional_sheet, assemble_sheet | Pillow |
| `validator` | check_image, check_tileset, check_sprites | Pillow + numpy |
| `file_ops` | copy, move, delete, mkdir, copy_multiple, list, read | None |
| `batch` | foreach | None |
| `blender` | render, render_animation, create_primitive, create_text_3d, generate_texture, render_isometric, create_dice, create_dice_set | Blender |
| `ffmpeg` | convert, normalize, loop, trim, get_duration | FFmpeg |
| `musicgen` | generate | MusicGen |
| `acestep` | generate | ACE-Step |
| `script` | run | None |

## Project Structure

```
localforge/                        # Repo root
├── localforge/                    # Python package
│   ├── engine/                    # Workflow engine, config, persistence
│   ├── tools/                     # Auto-discovered tool plugins (11 built-in)
│   ├── clients/                   # Service API clients (SD, Blender)
│   └── scripts/                   # Setup wizard, health checks
├── recipes/
│   ├── getting-started/           # Minimal examples (start here)
│   ├── examples/                  # Domain-diverse examples
│   ├── domains/                   # Domain-specific recipes
│   │   └── game-dev/             # Game development recipes
│   └── TEMPLATE.yaml              # Recipe authoring reference
├── agent-configs/                 # Ready-made agent integration configs
├── tests/                         # Test suite
├── docs/                          # Documentation
├── pyproject.toml                 # Package config (pip install -e .)
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
    path: null  # auto-detected on all platforms
  ffmpeg:
    path: ffmpeg  # uses PATH by default

persistence:
  enabled: true
  db_path: ~/.localforge/runs.db
```

## Agent Integration

LocalForge works with any CLI agent. Copy the appropriate config into your project:

| Agent | Config File | Copy To |
|-------|-------------|---------|
| Claude Code | `agent-configs/claude/CLAUDE.md` | Project root |
| Codex | `agent-configs/codex/AGENTS.md` | Project root |
| Cursor | `agent-configs/cursor/.cursorrules` | Project root |
| Other | `agent-configs/generic/AGENT.md` | Project root |

Each config tells the agent what LocalForge can do, when to use it, and includes ready-to-run commands.

## Adding Custom Tools

Drop a Python file in `localforge/tools/` that implements the tool interface:

```python
# localforge/tools/my_tool.py
TOOL_NAME = "my_tool"
TOOL_ACTIONS = ["my_action"]

def handle(action: str, inputs: dict, ctx) -> dict:
    if action == "my_action":
        # Do work...
        return {"result": "done"}
    raise ValueError(f"Unknown action: {action}")
```

The engine auto-discovers tools in the `localforge/tools/` directory.

## Troubleshooting

**"Cannot connect to Ollama"** — Start Ollama with `ollama serve`, then verify with `python -m localforge health`.

**"SD WebUI is not running"** — Start Stable Diffusion WebUI with `--api` flag. Default port is 7860.

**"Blender not found"** — Set the path in `localforge.yaml` under `services.blender.path`, or add Blender to your system PATH.

**"Recipe not found"** — Use the full relative path: `python -m localforge run recipes/getting-started/hello-localforge.yaml`. Run `python -m localforge list` to see all available recipes.

**"Missing required inputs"** — Check what the recipe needs: `python -m localforge run <recipe> --list-inputs`.

**Tests failing?** — Run `pip install -e ".[full]"` to install all optional dependencies, then `python -m pytest tests/ -v`.

## Security

LocalForge executes user-provided recipes that can run arbitrary code via the `script` tool and subprocess calls via `blender` and `ffmpeg`. **Only run recipes from sources you trust.** There is no sandboxing — recipes execute with the same permissions as the Python process. See [SECURITY.md](SECURITY.md) for details.

## Requirements

**Minimum:** Python 3.9+, PyYAML, requests

**Full:** `pip install -e ".[full]"` (adds Pillow, numpy, rembg for image processing)

**Services (install what you need):**
- [Ollama](https://ollama.com) — Local LLMs (recommended starting point)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) — Image generation
- [Blender](https://www.blender.org) — 3D modeling and rendering
- [FFmpeg](https://ffmpeg.org) — Audio/video processing
- [MusicGen](https://github.com/facebookresearch/audiocraft) — Music generation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, PR process, and how to add new tools.

## License

MIT — see [LICENSE](LICENSE).
