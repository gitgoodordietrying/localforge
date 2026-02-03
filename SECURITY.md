# Security Policy

## Important

LocalForge executes workflow recipes that can run arbitrary code on your system via the `script` tool, shell commands via `ffmpeg`, and subprocess calls via `blender`. **Only run recipes from sources you trust.**

There is no sandboxing. Recipes execute with the same permissions as the Python process.

## Reporting Vulnerabilities

If you discover a security issue, please report it privately:

1. **Do not** open a public GitHub issue
2. Email the maintainers or use [GitHub Security Advisories](https://github.com/gitgoodordietrying/localforge/security/advisories/new)
3. Include steps to reproduce and potential impact

We will acknowledge receipt within 72 hours and provide a fix timeline.

## Scope

Security concerns we care about:
- Path traversal that escapes the workspace
- Unintended code execution outside of the `script` tool
- Credential leaks in logs or persistence layer
- Dependency vulnerabilities

Out of scope (by design):
- The `script` tool executing arbitrary code — this is intentional
- Blender/FFmpeg subprocess execution — this is intentional
- Local network requests to Ollama/SD — this is intentional
