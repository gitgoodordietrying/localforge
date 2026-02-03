"""
Batch operations tool.

Iterates over items and executes workflow steps for each,
enabling foreach-style loops in recipes.
"""

TOOL_NAME = "batch"
TOOL_ACTIONS = ["foreach"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle batch operations."""
    if action != "foreach":
        raise ValueError(f"Unknown batch action: {action}")

    # Parse items list
    items_input = inputs.get("items", "")
    if isinstance(items_input, str):
        items = [item.strip() for item in items_input.split(",") if item.strip()]
    else:
        items = list(items_input)

    workflow_steps = inputs.get("workflow_steps", [])
    if not workflow_steps:
        raise ValueError("batch.foreach requires workflow_steps")

    # Import here to avoid circular dependency
    from ..engine.runner import ToolRegistry

    tool_registry = ToolRegistry()
    results = []
    ctx.log(f"Processing {len(items)} items in batch")

    for item_index, item in enumerate(items):
        ctx.log(f"Batch item {item_index + 1}/{len(items)}: {item}")

        item_outputs = {}

        for step in workflow_steps:
            step_id = step.get("id", f"batch_step_{item_index}")
            tool = step.get("tool")
            step_action = step.get("action")
            step_inputs = step.get("inputs", {})

            resolved_inputs = {}
            for key, value in step_inputs.items():
                if isinstance(value, str):
                    value = value.replace("{{item}}", str(item))
                    value = value.replace("{{item_index}}", str(item_index))

                    for prev_step_id, prev_outputs in item_outputs.items():
                        for out_key, out_val in prev_outputs.items():
                            placeholder = f"{{{{{prev_step_id}.outputs.{out_key}}}}}"
                            if placeholder in value:
                                value = value.replace(placeholder, str(out_val))

                    value = ctx.resolve(value)
                resolved_inputs[key] = value

            step_result = tool_registry.execute(tool, step_action, resolved_inputs, ctx)
            item_outputs[step_id] = step_result

        results.append({
            "item": item,
            "index": item_index,
            "outputs": item_outputs,
        })

    return {
        "results": results,
        "count": len(results),
        "items_processed": items,
    }
