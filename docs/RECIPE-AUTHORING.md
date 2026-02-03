# Recipe Authoring Guide

## Structure

Every recipe is a YAML file with these sections:

```yaml
name: "my-recipe"
version: "1.0"
description: "What this recipe produces"

inputs:       # What the user provides
outputs:      # What the recipe produces (documentation)
config:       # Workflow settings
steps:        # The actual work
cleanup:      # Post-workflow actions
```

## Inputs

Define what the user must provide:

```yaml
inputs:
  - name: "description"
    type: "string"
    required: true
    description: "What to generate"

  - name: "width"
    type: "number"
    default: 512
    description: "Image width"
```

Types: `string`, `number`, `path`. Use `required: true` for mandatory inputs. Provide `default` for optional ones.

## Steps

Each step calls a tool with an action:

```yaml
steps:
  - id: "unique_id"           # Referenced by later steps
    name: "Human description"  # Shown in logs
    tool: "ollama"             # Which tool to use
    action: "generate"         # Which action on that tool
    inputs:                    # Passed to the tool handler
      prompt: "{{inputs.description}}"
```

### Variable References

Use `{{...}}` to reference values:
- `{{inputs.name}}` — User input
- `{{steps.step_id.outputs.key}}` — Previous step output
- `{{temp_dir}}` — Temp directory
- `{{workflow.run_id}}` — Run ID
- `{{timestamp}}` — Current time

### Error Handling

```yaml
  - id: "risky_step"
    tool: "sd_client"
    action: "txt2img"
    inputs: ...
    on_failure: "skip"     # abort | skip | retry | refine
    retry_count: 3         # For retry mode
```

### Validation Gates

```yaml
  - id: "validate"
    tool: "validator"
    action: "check_image"
    inputs:
      image: "{{steps.generate.outputs.primary}}"
      checks:
        has_transparency: true
    gate: true              # Fail workflow if validation fails
    on_failure: "refine"    # Or enter refinement loop
    refinement:
      steps:
        - id: "fix"
          tool: "image_processor"
          action: "make_seamless"
          inputs:
            input: "{{steps.resize.outputs.output}}"
            output: "{{steps.resize.outputs.output}}"
```

### Approval Gates

```yaml
  - id: "review"
    type: "approval_gate"
    name: "Review generated image"
    message: "Check the image at {{steps.generate.outputs.primary}}"
    options: ["approve", "reject", "regenerate"]
    default_action: "approve"
```

Use `--auto-approve` to skip all gates.

## Cleanup

```yaml
cleanup:
  on_success:
    - action: "delete"
      path: "{{temp_dir}}"
  on_failure:
    - action: "preserve"
      path: "{{temp_dir}}"
      reason: "debug"
```

Actions: `delete`, `preserve`, `move` (with `source` and `destination`).

## Available Tools

See `recipes/TEMPLATE.yaml` for the complete tool reference, or run `python -m localforge list` to see all recipes with their descriptions.

## Tips

- Start with `recipes/TEMPLATE.yaml` as a base
- Use Ollama to generate optimized prompts for SD (saves iterations)
- Set `config.max_iterations` for refinement loops
- Use `on_failure: "skip"` for non-critical steps
- Test with `--list-inputs` before running
