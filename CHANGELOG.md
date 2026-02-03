# Changelog

All notable changes to LocalForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
