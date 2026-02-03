"""
Blender 3D tool.

Delegates to the Blender client for rendering, model creation,
texture generation, and dice creation.
"""

from pathlib import Path

from engine.config import get_config

TOOL_NAME = "blender"
TOOL_ACTIONS = [
    "render", "render_animation", "create_primitive", "create_text_3d",
    "generate_texture", "render_isometric", "create_dice", "create_dice_set",
]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle Blender 3D operations."""
    from clients.blender_client import BlenderClient

    config = get_config()
    blender_path = inputs.get("blender_path", config.blender_path)
    client = BlenderClient(blender_path=Path(blender_path) if blender_path else None)

    if action == "render":
        result = client.render_scene(
            blend_file=Path(inputs.get("blend_file")),
            output_path=Path(inputs.get("output_path")),
            resolution=tuple(inputs.get("resolution", [1920, 1080])),
            samples=int(inputs.get("samples", 128)),
        )
        return {"output": str(result)}

    elif action == "render_animation":
        result = client.render_animation(
            blend_file=Path(inputs.get("blend_file")),
            output_dir=Path(inputs.get("output_dir")),
            frame_start=int(inputs.get("frame_start", 1)),
            frame_end=int(inputs.get("frame_end", 24)),
            resolution=tuple(inputs.get("resolution", [1920, 1080])),
        )
        return {"output_dir": str(result)}

    elif action == "create_primitive":
        result = client.create_primitive(
            shape=inputs.get("shape"),
            output_path=Path(inputs.get("output_path")),
            size=float(inputs.get("size", 1.0)),
            subdivisions=int(inputs.get("subdivisions", 2)),
        )
        return {"output": str(result)}

    elif action == "create_text_3d":
        result = client.create_text_3d(
            text=inputs.get("text"),
            output_path=Path(inputs.get("output_path")),
            font_size=float(inputs.get("font_size", 1.0)),
            extrude=float(inputs.get("extrude", 0.1)),
        )
        return {"output": str(result)}

    elif action == "generate_texture":
        result = client.generate_procedural_texture(
            texture_type=inputs.get("texture_type"),
            output_path=Path(inputs.get("output_path")),
            resolution=int(inputs.get("resolution", 1024)),
        )
        return {"output": str(result)}

    elif action == "render_isometric":
        result = client.render_isometric_background(
            output_path=Path(inputs.get("output_path")),
            scene_type=inputs.get("scene_type", "landscape"),
            resolution=tuple(inputs.get("resolution", [1920, 1080])),
        )
        return {"output": str(result)}

    elif action == "create_dice":
        result = client.create_dice(
            dice_type=inputs.get("dice_type"),
            output_path=Path(inputs.get("output_path")),
            size=float(inputs.get("size", 1.0)),
            texture_resolution=int(inputs.get("texture_resolution", 1024)),
            export_uv_layout=bool(inputs.get("export_uv_layout", True)),
            export_svg=bool(inputs.get("export_svg", True)),
        )
        return {k: str(v) for k, v in result.items()}

    elif action == "create_dice_set":
        result = client.create_dice_set(
            output_dir=Path(inputs.get("output_dir")),
            size=float(inputs.get("size", 1.0)),
            texture_resolution=int(inputs.get("texture_resolution", 1024)),
        )
        return {
            dice_type: {k: str(v) for k, v in paths.items()}
            for dice_type, paths in result.items()
        }

    raise ValueError(f"Unknown blender action: {action}")
