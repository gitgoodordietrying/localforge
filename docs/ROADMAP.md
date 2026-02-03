# LocalForge Roadmap

From game-dev asset pipeline to general-purpose local-first AI orchestration.

---

## Vision

LocalForge follows a **CEO / Manager / Worker** hierarchy:

```
┌────────────────────────────────────────┐
│  PAID AGENT (CEO)                      │  Decides what to do.
│  Claude Code, Codex, Gemini CLI, etc.  │  Pays per token.
└──────────────────┬─────────────────────┘
                   │ invokes
┌──────────────────▼─────────────────────┐
│  LOCALFORGE ENGINE (Manager)           │  Orchestrates recipes.
│  YAML recipes, variable resolution,    │  Free, runs locally.
│  error handling, resource awareness    │
└──────────────────┬─────────────────────┘
                   │ delegates to
┌──────────────────▼─────────────────────┐
│  LOCAL WORKERS                         │  Execute tasks.
│  Ollama · SD · Blender · FFmpeg        │  Free, runs locally.
│  Whisper · ComfyUI · Any CLI tool      │
└────────────────────────────────────────┘
```

**Local-first philosophy:**
- Every tool runs on the user's machine — no cloud APIs required
- Paid agent tokens are spent on reasoning, not grunt work
- The engine is domain-agnostic — recipes define the domain
- New tools integrate via YAML definitions — no Python required (Phase 3+)
- Hardware constraints are first-class: VRAM budgets, model recommendations, graceful degradation

---

## Current State (v0.1.0)

### What exists

| Component | Count | Details |
|-----------|-------|---------|
| Built-in tools | 11 | ollama, sd_client, image_processor, validator, file_ops, batch, blender, ffmpeg, musicgen, acestep, script |
| Recipes | 9 | 3 getting-started, 5 examples, 1 template |
| CLI commands | 5 | run, list, health, init, history |
| Test suite | 79 | tests across config, context, tool discovery, recipe validation |
| CI matrix | 9 jobs | 3 OS × 3 Python versions |
| Agent configs | 4 | Claude Code, Codex, Cursor, generic |

### Architecture

```
localforge/
├── engine/          # runner.py (orchestration), config.py, persistence.py
├── tools/           # 11 auto-discovered tool plugins
├── clients/         # Service API clients (SD, Blender)
└── scripts/         # Setup wizard, health checks
```

**Tool interface:** Every tool exports `TOOL_NAME`, `TOOL_ACTIONS`, and `handle(action, inputs, ctx) -> dict`. The engine auto-discovers tools from `localforge/tools/`. This interface is stable and will not change.

### What works well
- YAML recipe format with variable resolution
- Error handling (abort, skip, retry, refine)
- Refinement loops with validation gates
- Cross-platform support (Windows, macOS, Linux)
- SQLite persistence for run history

### What's missing
- No hardware awareness — recipes fail if resources are insufficient
- No model recommendations — users must know which models fit their GPU
- Tool integration requires Python — barrier for CLI-only tools
- Sequential execution only — no parallel steps
- Game-dev-heavy framing — obscures general-purpose capability
- No self-improvement pathway — can't guide users to enhance their setup

---

## Phase 1: Reframing (S)

**Goal:** Reposition LocalForge as domain-agnostic. Zero code changes to the engine.

### Tasks

| # | Change | Files |
|---|--------|-------|
| 1 | Rewrite README "What Can It Do?" table — lead with domain-diverse examples | `README.md` |
| 2 | Move game-dev recipes to `recipes/domains/game-dev/` | 4 files |
| 3 | Add `recipes/examples/batch-resize.yaml` — zero-service Pillow recipe | New file |
| 4 | Add `recipes/examples/code-review.yaml` — Ollama-only developer recipe | New file |
| 5 | Add `recipes/examples/data-extract.yaml` — Ollama-only data recipe | New file |
| 6 | Update pyproject.toml description and keywords | `pyproject.toml` |
| 7 | Update agent configs — general-purpose framing | 4 files |

### Recipe organization after Phase 1

```
recipes/
├── getting-started/         # Zero to working (unchanged)
│   ├── hello-localforge.yaml
│   ├── hello-ollama.yaml
│   └── hello-sd.yaml
├── examples/                # Domain-diverse showcase
│   ├── batch-resize.yaml    # NEW — zero-service, Pillow only
│   ├── code-review.yaml     # NEW — Ollama only
│   ├── data-extract.yaml    # NEW — Ollama only
│   └── text-pipeline.yaml   # Existing
├── domains/
│   └── game-dev/            # MOVED from examples/
│       ├── game-sprite.yaml
│       ├── tileset.yaml
│       ├── music-track.yaml
│       └── 3d-model.yaml
└── TEMPLATE.yaml
```

### Success criteria
- `python -m localforge list` shows reorganized recipes
- `test_recipes.py` auto-discovers all YAML files (moved + new) — all pass
- README first table row is NOT game-specific

---

## Phase 2: System Discovery & Resource Awareness (M)

**Goal:** LocalForge knows what hardware and services are available, and can recommend models.

### New files

**`localforge/engine/system_info.py`**

```python
class SystemInfo:
    """Detect hardware, services, and installed tools."""

    def _detect_hardware(self) -> dict:
        """Detect RAM (os), CPU cores (os.cpu_count()), GPU/VRAM (nvidia-smi)."""
        ...

    def _detect_services(self) -> dict:
        """Check Ollama (:11434), SD WebUI (:7860), ComfyUI (:8188)."""
        ...

    def _detect_tools(self) -> dict:
        """Check Blender, FFmpeg, whisper, etc. via shutil.which()."""
        ...

    def can_run_model(self, model: str, vram_budget: dict) -> bool:
        """Check if a model fits within available VRAM."""
        ...

    def recommend_model(self, task: str) -> str:
        """Suggest the best model for a task given hardware constraints."""
        ...

    def summary(self) -> dict:
        """Return complete system profile."""
        ...
```

**`localforge/data/model_profiles.yaml`**

VRAM budgets derived from real-world profiling:

```yaml
ollama:
  mistral:7b:
    vram_gb: 5.0
    tasks: [general, chat, summarization]
    quality: good
  llama3.1:8b:
    vram_gb: 5.5
    tasks: [general, chat, reasoning]
    quality: good
  codellama:13b:
    vram_gb: 9.0
    tasks: [code, review]
    quality: better
  llava:13b:
    vram_gb: 8.0
    tasks: [vision, description]
    quality: good
  llama3.2:3b:
    vram_gb: 2.5
    tasks: [general, chat, classification]
    quality: basic

sd:
  sd15_512:
    label: "SD 1.5 @ 512×512"
    vram_gb: 4.0
  sd15_768:
    label: "SD 1.5 @ 768×768"
    vram_gb: 6.0
  sdxl_1024:
    label: "SDXL @ 1024×1024"
    vram_gb: 11.0
```

### CLI addition

```bash
python -m localforge system
```

Output:
```
LocalForge System Profile

Hardware:
  CPU: 12 cores
  RAM: 32.0 GB
  GPU: NVIDIA RTX 3090 (24.0 GB VRAM)

Services:
  Ollama: RUNNING (localhost:11434) — 5 models loaded
  SD WebUI: RUNNING (localhost:7860)
  ComfyUI: NOT RUNNING

Tools:
  Blender: FOUND (4.0.2)
  FFmpeg: FOUND (6.1)
  Whisper: NOT FOUND

Model Recommendations:
  General text: llama3.1:8b (5.5 GB, fits in VRAM)
  Code review: codellama:13b (9.0 GB, fits in VRAM)
  Image gen: SDXL @ 1024×1024 (11.0 GB, fits in VRAM)
```

### Resource management patterns

These env vars optimize Ollama for multi-model workflows:

```bash
OLLAMA_FLASH_ATTENTION=1       # Faster inference on supported GPUs
OLLAMA_KV_CACHE_TYPE=q8_0      # Reduced VRAM usage for KV cache
OLLAMA_MAX_LOADED_MODELS=3     # Cap concurrent models in VRAM
```

Process hygiene (from production experience):
1. Check if service is running before starting: `curl -s localhost:<port>`
2. Track PIDs when spawning background processes
3. Kill stale processes if they don't respond within timeout
4. Monitor memory thresholds before loading new models
5. Verify cleanup: no zombie processes after workflow completion

### Success criteria
- `python -m localforge system` prints hardware info without error
- `SystemInfo` works on Windows, macOS, Linux (graceful degradation if nvidia-smi missing)
- 10+ unit tests for system_info module
- Model recommendations match available VRAM

---

## Phase 3: Generic Tool Integration (L)

**Goal:** Define new tools in YAML — no Python code required. Unlocks CLI tools like Whisper, yt-dlp, ImageMagick, pandoc, etc.

### YAML tool definition format

```yaml
# localforge/data/tools/whisper.yaml
name: whisper
version: "1.0"
type: cli
description: "Speech-to-text transcription"

actions:
  transcribe:
    command: "whisper {{inputs.audio_file}} --model {{inputs.model}} --output_dir {{inputs.output_dir}}"
    inputs:
      audio_file:
        type: path
        required: true
        description: "Audio file to transcribe"
      model:
        type: string
        default: "base"
        choices: [tiny, base, small, medium, large]
      output_dir:
        type: path
        default: "{{temp_dir}}"
    outputs:
      transcript: "{{inputs.output_dir}}/{{inputs.audio_file|stem}}.txt"

requirements:
  binary: whisper
  install_hint: "pip install openai-whisper"
  min_vram_gb: 2.0  # for 'base' model

# More examples: yt-dlp, pandoc, ImageMagick, tesseract
```

### Engine changes

```python
class YamlToolLoader:
    """Load tool definitions from YAML files in localforge/data/tools/."""

    def discover(self) -> list[dict]:
        """Find all *.yaml files in the tools directory."""
        ...

    def load(self, path: Path) -> YamlTool:
        """Parse YAML tool definition into a callable tool."""
        ...

class YamlTool:
    """A tool defined entirely in YAML — wraps CLI commands."""

    TOOL_NAME: str
    TOOL_ACTIONS: list[str]

    def handle(self, action: str, inputs: dict, ctx) -> dict:
        """Build command string, execute subprocess, capture outputs."""
        ...
```

### Integration with auto-discovery

The existing `ToolRegistry` in `runner.py` discovers Python tools from `localforge/tools/`. Phase 3 extends this to also discover YAML tools from `localforge/data/tools/`. Both types implement the same `handle(action, inputs, ctx) -> dict` interface.

### Success criteria
- `python -m localforge list-tools` shows both Python and YAML tools
- A Whisper YAML tool can transcribe audio via recipe
- Existing Python tools unaffected
- 15+ tests for YAML tool loader

---

## Phase 4: Smart Orchestration (XL)

**Goal:** Parallel step execution with resource-aware scheduling. Independent steps run concurrently; resource conflicts are serialized.

### Recipe format extension

```yaml
steps:
  - id: "generate_prompt"
    tool: "ollama"
    action: "generate"
    inputs: { ... }

  # These two steps are independent — can run in parallel
  - id: "generate_image"
    tool: "sd_client"
    action: "txt2img"
    depends_on: ["generate_prompt"]
    inputs:
      prompt: "{{steps.generate_prompt.outputs.response}}"

  - id: "generate_music"
    tool: "musicgen"
    action: "generate"
    depends_on: ["generate_prompt"]
    inputs:
      description: "{{steps.generate_prompt.outputs.response}}"

  # This step waits for both
  - id: "package"
    tool: "file_ops"
    action: "copy_multiple"
    depends_on: ["generate_image", "generate_music"]
```

**Backward compatibility:** `depends_on` is optional. Omitting it = sequential execution (current behavior). Existing recipes work unchanged.

### Engine changes

```python
class StepScheduler:
    """Build DAG from depends_on, dispatch ready steps concurrently."""

    def __init__(self, steps: list[dict], system_info: SystemInfo):
        self.dag = self._build_dag(steps)
        self.system_info = system_info

    def _build_dag(self, steps) -> dict:
        """Parse depends_on into a directed acyclic graph."""
        ...

    def _check_resources(self, step: dict) -> bool:
        """Verify VRAM/RAM available for this step's tool."""
        ...

    def next_batch(self, completed: set[str]) -> list[dict]:
        """Return steps whose dependencies are met and resources available."""
        ...
```

**Execution:** `ThreadPoolExecutor` runs independent steps concurrently. The scheduler checks resource availability before dispatching — if two steps both need the GPU, they're serialized.

### Success criteria
- Recipes with `depends_on` execute steps in parallel
- Recipes without `depends_on` execute sequentially (unchanged)
- Resource conflicts are detected and serialized
- 20+ tests covering DAG construction, scheduling, resource checks
- No existing tests break

---

## Phase 5: Knowledge Seeds & Self-Evolution (M)

**Goal:** LocalForge can guide users (and AI agents) to improve their setup — install better models, optimize services, add new tools.

### Concept

A "seed" is an executable playbook that describes how to enhance a local AI capability. Seeds live in `docs/seeds/` and are written to be actionable by both humans and AI agents.

```
docs/seeds/
├── install-ollama-models.md      # Which models to install for which tasks
├── optimize-sd-webui.md          # VRAM optimization, model selection
├── add-whisper.md                # Install and integrate speech-to-text
├── add-comfyui.md                # Install and integrate ComfyUI
├── optimize-ollama-performance.md # Env vars, quantization, batch settings
└── TEMPLATE.md                   # Template for writing new seeds
```

### Seed format

Each seed contains:
1. **What it does** — one sentence
2. **Prerequisites** — hardware requirements, dependencies
3. **Exact commands** — copy-paste-ready, with expected output
4. **Verification** — how to confirm it worked
5. **Integration** — how to use it in LocalForge recipes
6. **VRAM/resource impact** — what this costs in GPU/RAM

### CLI command

```bash
python -m localforge seed list                 # List available seeds
python -m localforge seed show <topic>         # Display a seed
python -m localforge seed check <topic>        # Check prerequisites
```

### Enhancement pattern

Proven workflow from production use:

1. **Identify** a stock tool (e.g., SD WebUI with default model)
2. **Profile** hardware (available VRAM, CPU, RAM)
3. **Optimize** configuration (resolution, batch size, sampler)
4. **Install** better models (CivitAI checkpoints, LoRAs)
5. **Build** middleware bridge (Python client, YAML tool def)
6. **Integrate** into workflows (recipe that uses the tool)
7. **Document** gains (before/after metrics, VRAM usage)

This pattern applies to every local AI tool and is the basis for seed creation.

### Success criteria
- 5+ seeds covering major tools
- `python -m localforge seed list` shows available seeds
- Seeds are actionable by AI agents (exact commands, file paths, expected outputs)
- TEMPLATE.md makes it easy to write new seeds

---

## Phase 6: Ecosystem (XL)

**Goal:** LocalForge becomes a platform — MCP server for remote agents, community tool registry, agent-config generation.

### MCP Server

Expose LocalForge capabilities as an MCP (Model Context Protocol) server:

```python
# localforge/mcp/server.py
class LocalForgeMCPServer:
    """Expose recipes and tools via MCP for remote agent access."""

    def list_tools(self) -> list[dict]:
        """Return available tools and their actions."""
        ...

    def list_recipes(self) -> list[dict]:
        """Return available recipes with input schemas."""
        ...

    def run_recipe(self, recipe: str, inputs: dict) -> dict:
        """Execute a recipe and return results."""
        ...

    def system_info(self) -> dict:
        """Return hardware/service profile."""
        ...
```

This lets remote agents (Claude Desktop, other MCP clients) invoke LocalForge without SSH or CLI access.

### Community tool registry

```bash
python -m localforge tools install whisper     # Install from registry
python -m localforge tools search "audio"      # Search available tools
python -m localforge tools publish my-tool     # Share a YAML tool
```

Registry is a simple GitHub repo with YAML tool definitions — no binary distribution, just definitions.

### Agent-config generation

```bash
python -m localforge agent-config generate     # Auto-generate from installed tools
```

Scans installed tools, available recipes, and hardware to produce a tailored agent config (CLAUDE.md, AGENTS.md, etc.) that tells the agent exactly what this machine can do.

### Success criteria
- MCP server passes protocol compliance tests
- At least 10 community tool definitions
- Agent-config generator produces accurate configs
- All existing functionality unaffected

---

## Stability Guarantees

### Test layers

| Layer | What it catches | When it runs |
|-------|----------------|--------------|
| Unit tests | Logic bugs in individual modules | Every commit |
| Recipe validation | Broken/invalid YAML recipes | Every commit (auto-discovered) |
| Smoke test | Engine regression (end-to-end) | Every CI run |
| Lint | Style issues, unused imports | Every CI run |

### CI configuration

```yaml
# .github/workflows/tests.yml
jobs:
  test:                    # 3 OS × 3 Python = 9 jobs
  lint:                    # ruff check
  smoke:                   # Run hello-localforge.yaml end-to-end
```

### Progressive disclosure

New capabilities are introduced without breaking existing behavior:

1. **Optional imports** — Pattern already established (rembg, psutil). New features behind try/except with helpful install messages.
2. **Graceful CLI** — New commands fail with "install X to enable" rather than tracebacks.
3. **Optional recipe fields** — `depends_on` is optional; omitting = sequential. `resources` is optional; omitting = no resource checks.
4. **Stable tool interface** — `handle(action, inputs, ctx) -> dict` never changes. YAML tools implement the same interface.

### Backward compatibility rules

- Moving recipes preserves discoverability (test_recipes.py uses `rglob`)
- No changes to `handle(action, inputs, ctx) -> dict` tool interface
- No changes to recipe YAML format (only additions)
- No changes to variable resolution syntax
- New CLI commands are additive (existing commands unchanged)
- Config file format only gains new optional fields

---

## Phase Dependency Diagram

```
Phase 1: Reframing ─────────────┐
  (content only, no code)        │
                                 ▼
Phase 2: System Discovery ──────┤
  (system_info, model profiles)  │
                                 ▼
Phase 3: Generic Tools ─────────┤
  (YAML tool loader)            │
                                 ▼
Phase 4: Smart Orchestration ───┤
  (parallel execution, DAG)     │
                                 ▼
Phase 5: Knowledge Seeds ───────┤
  (docs/seeds/, CLI commands)   │
                                 ▼
Phase 6: Ecosystem
  (MCP server, registry)
```

Phases 1-2 are independent of each other and can be done in parallel.
Phase 3 benefits from Phase 2 (resource checks for YAML tools).
Phase 4 requires Phase 2 (resource-aware scheduling needs SystemInfo).
Phase 5 can start after Phase 2 (seeds reference model profiles).
Phase 6 requires Phases 3-4 (MCP exposes the full tool/scheduling system).

---

## Sprint Planning Guide

### Sprint 1 (current) — Phases 1 + 2 foundation

**Batch 1: Reframing**
- Rewrite README examples
- Reorganize recipes into domains/
- Create 3 new domain-diverse example recipes
- Update pyproject.toml and agent configs

**Batch 2: System discovery foundation**
- Create `localforge/engine/system_info.py`
- Create `localforge/data/model_profiles.yaml`
- Add `python -m localforge system` CLI command
- Write 10+ tests for SystemInfo

**Batch 3: Stability**
- Add ruff linting to CI
- Add smoke test to CI
- Bump version to 0.2.0
- Verify all tests pass (79 existing + ~15 new)

### Sprint 2 — Phase 2 completion + Phase 3 start

- Wire SystemInfo into recipe pre-flight checks
- `python -m localforge system --json` for programmatic access
- Start YAML tool loader prototype
- First 3 YAML tool definitions (whisper, yt-dlp, pandoc)

### Sprint 3 — Phase 3 completion + Phase 4 start

- YAML tool loader production-ready
- 10+ YAML tool definitions
- `depends_on` field parsing in runner
- StepScheduler prototype

### Sprint 4 — Phase 4 completion + Phase 5

- Parallel execution with ThreadPoolExecutor
- Resource-aware scheduling
- First 5 knowledge seeds
- `python -m localforge seed` CLI

### Sprint 5 — Phase 6

- MCP server prototype
- Agent-config generation
- Community tool registry design

---

## File Reference

### Existing files (stable, not modified by roadmap)

| File | Purpose |
|------|---------|
| `localforge/engine/runner.py` | Workflow execution engine |
| `localforge/engine/config.py` | Configuration management |
| `localforge/engine/persistence.py` | SQLite persistence |
| `localforge/tools/*.py` | 11 built-in tool plugins |
| `localforge/clients/*.py` | Service API clients |

### New files (by phase)

| Phase | File | Purpose |
|-------|------|---------|
| 2 | `localforge/engine/system_info.py` | Hardware/service detection |
| 2 | `localforge/data/model_profiles.yaml` | VRAM budgets and model data |
| 3 | `localforge/data/tools/*.yaml` | YAML tool definitions |
| 3 | `localforge/engine/yaml_tool_loader.py` | Load YAML tools |
| 4 | `localforge/engine/scheduler.py` | DAG-based step scheduler |
| 5 | `docs/seeds/*.md` | Knowledge seed playbooks |
| 6 | `localforge/mcp/server.py` | MCP server |
| 6 | `localforge/mcp/registry.py` | Tool registry client |
