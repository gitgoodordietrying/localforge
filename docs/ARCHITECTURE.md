# Architecture

## Overview

LocalForge is a workflow engine that executes YAML-defined pipelines by dispatching steps to local tools and services.

```
User/Agent → CLI (__main__.py)
                → WorkflowRunner (engine/runner.py)
                    → ToolRegistry (auto-discovers tools/*.py)
                        → Tool handlers (ollama, sd, image, etc.)
                            → Service clients (clients/*.py)
                                → External services (Ollama, SD, Blender, etc.)
```

## Core Components

### WorkflowContext (`engine/runner.py`)
Holds all state during a workflow run:
- Input values from the user
- Step outputs (accumulated as steps complete)
- Variable resolution (`{{inputs.x}}`, `{{steps.y.outputs.z}}`)
- Temp directory management
- Logging

### ToolRegistry (`engine/runner.py`)
Auto-discovers tool modules from the `tools/` directory. Each tool module exports:
- `TOOL_NAME`: String identifier used in recipes
- `handle(action, inputs, ctx)`: Entry point that dispatches to the correct action

### WorkflowRunner (`engine/runner.py`)
Orchestrates recipe execution:
1. Load YAML recipe
2. Create WorkflowContext
3. Execute steps sequentially
4. Handle error strategies (abort, skip, retry, refine)
5. Execute cleanup actions
6. Return results

### Config (`engine/config.py`)
Reads from `localforge.yaml` with fallback to `~/.localforge/config.yaml` and built-in defaults. Provides typed access to service configuration.

### Persistence (`engine/persistence.py`)
SQLite-based tracking of workflow runs, step executions, and assets. Enables history viewing and future resume capability.

## Variable Resolution

The `{{variable}}` syntax is resolved recursively through all string values in step inputs before execution:

| Pattern | Resolves To |
|---------|------------|
| `{{inputs.name}}` | User-provided input value |
| `{{steps.id.outputs.key}}` | Output from a completed step |
| `{{config.key}}` | Recipe config value |
| `{{temp_dir}}` | Run-specific temp directory |
| `{{workflow.run_id}}` | Unique 8-char run ID |
| `{{timestamp}}` | ISO timestamp |

## Error Handling

Each step can specify `on_failure`:
- **abort** (default): Stop the workflow, trigger failure cleanup
- **skip**: Log warning, continue to next step
- **retry**: Retry the step N times (`retry_count`)
- **refine**: Enter a refinement loop using `refinement.steps`, re-validate after each iteration up to `config.max_iterations`

## Tool Plugin System

Tools are Python modules in `localforge/tools/` matching `*_tool.py`. The registry imports them at startup. To add a custom tool:

1. Create `localforge/tools/my_tool.py`
2. Export `TOOL_NAME = "my_tool"`
3. Export `def handle(action, inputs, ctx) -> dict`
4. Use `tool: "my_tool"` in recipes

## Data Flow

```
Recipe YAML → parse → WorkflowContext
    → Step 1: resolve inputs → execute tool → store outputs
    → Step 2: resolve inputs (can reference Step 1 outputs) → execute → store
    → ...
    → Cleanup actions
    → Return result dict
```
