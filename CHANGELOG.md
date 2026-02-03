# Changelog

All notable changes to LocalForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] - 2026-02-03

### Added
- System discovery: `python -m localforge system` shows hardware, services, tools, and model recommendations
- `SystemInfo` class (`localforge/engine/system_info.py`) — detects CPU, RAM, GPU/VRAM, running services, installed CLI tools
- Model VRAM profiles (`localforge/data/model_profiles.yaml`) — Ollama and SD budgets from real-world profiling
- 3 new domain-diverse example recipes: `batch-resize`, `code-review`, `data-extract`
- `ruff` linting job in CI
- Smoke test job in CI (runs hello-localforge.yaml end-to-end)
- `docs/ROADMAP.md` — 6-phase evolution plan for LocalForge

### Changed
- Reorganized game-dev recipes into `recipes/domains/game-dev/`
- README reframed: domain-diverse examples shown first (code review, data extraction, batch resize)
- pyproject.toml description and keywords updated for general-purpose positioning
- Agent configs (Claude, Codex, Cursor, generic) updated with general-purpose framing and new recipe paths
- All existing lint issues fixed (ruff-clean codebase)

## [0.1.0] - 2026-02-03

### Added
- Workflow engine with YAML recipe format
- 11 built-in tools: ollama, sd_client, image_processor, validator, file_ops, batch, blender, ffmpeg, musicgen, acestep, script
- Auto-discovery of tool plugins from `tools/` directory
- Variable resolution system (`{{inputs.*}}`, `{{steps.*}}`, `{{temp_dir}}`, etc.)
- Error handling strategies: abort, skip, retry, refine
- Refinement loops with validation gates
- Human-in-the-loop approval gates with `--auto-approve` bypass
- SQLite persistence for run history and asset tracking
- Cross-platform Blender auto-detection (Windows, macOS, Linux)
- Interactive setup wizard (`python -m localforge init`)
- Service health check (`python -m localforge health`)
- Getting-started recipes for Ollama and Stable Diffusion
- Example recipes: game sprites, tilesets, music tracks, 3D models, text pipelines
- Agent integration configs for Claude Code, Codex, Cursor, and generic agents
- `pyproject.toml` for pip installation
