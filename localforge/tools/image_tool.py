"""
Image processing tool.

Provides background removal, resizing, seamless tiling, sprite sheets,
and animation generation using Pillow and numpy.
"""

import math
from pathlib import Path

TOOL_NAME = "image_processor"
TOOL_ACTIONS = [
    "remove_bg", "resize", "batch_remove_bg", "make_seamless",
    "tile_preview", "create_idle_animation", "create_directional_sheet",
    "assemble_sheet",
]


def _remove_bg_color(image, color, tolerance):
    """Remove a specific background color."""
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if (abs(r - color[0]) <= tolerance and
                    abs(g - color[1]) <= tolerance and
                    abs(b - color[2]) <= tolerance):
                pixels[x, y] = (r, g, b, 0)
    return image


def _check_seamless(image, max_diff: int = 20) -> float:
    """Check if a tile is seamless. Returns score 0.0-1.0."""
    import numpy as np

    arr = np.array(image)
    left_edge = arr[:, 0, :]
    right_edge = arr[:, -1, :]
    lr_diff = np.abs(left_edge.astype(int) - right_edge.astype(int))
    lr_match = np.mean(lr_diff < max_diff)

    top_edge = arr[0, :, :]
    bottom_edge = arr[-1, :, :]
    tb_diff = np.abs(top_edge.astype(int) - bottom_edge.astype(int))
    tb_match = np.mean(tb_diff < max_diff)

    return (lr_match + tb_match) / 2


def _make_seamless(image, blend_width: int = 8):
    """Make a tile seamless by blending opposite edges."""
    import numpy as np
    from PIL import Image as PILImage

    arr = np.array(image).astype(float)
    blend = np.linspace(0, 1, blend_width)

    for i, factor in enumerate(blend):
        arr[:, -(blend_width - i), :] = (
            arr[:, -(blend_width - i), :] * (1 - factor) +
            arr[:, i, :] * factor
        )

    for i, factor in enumerate(blend):
        arr[-(blend_width - i), :, :] = (
            arr[-(blend_width - i), :, :] * (1 - factor) +
            arr[i, :, :] * factor
        )

    return PILImage.fromarray(arr.astype(np.uint8))


def _create_idle_animation(image, frames: int = 4, bob_pixels: int = 2):
    """Create idle animation frames by vertical bobbing."""
    from PIL import Image as PILImage

    width, height = image.size
    animation_frames = []
    for i in range(frames):
        phase = (i / frames) * 2 * math.pi
        offset_y = int(math.sin(phase) * bob_pixels)
        frame = PILImage.new("RGBA", (width, height), (0, 0, 0, 0))
        frame.paste(image, (0, offset_y), image if image.mode == "RGBA" else None)
        animation_frames.append(frame)
    return animation_frames


def _create_sprite_sheet(frames: list, columns: int = None):
    """Assemble frames into a sprite sheet."""
    from PIL import Image as PILImage

    if not frames:
        raise ValueError("No frames provided")
    frame_width, frame_height = frames[0].size
    num_frames = len(frames)
    columns = columns or num_frames
    rows = (num_frames + columns - 1) // columns

    sheet = PILImage.new("RGBA", (frame_width * columns, frame_height * rows), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        col = i % columns
        row = i // columns
        sheet.paste(frame, (col * frame_width, row * frame_height))
    return sheet


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle image processing operations."""
    from PIL import Image

    if action == "remove_bg":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output", ctx.temp_dir / "processed.png"))
        method = inputs.get("method", "auto")
        tolerance = inputs.get("tolerance", 30)

        image = Image.open(input_path)
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        if method == "auto":
            pixels = image.load()
            bg_color = pixels[0, 0][:3]
            image = _remove_bg_color(image, bg_color, tolerance)
        elif method == "color":
            bg_color = inputs.get("bg_color", (0, 0, 0))
            image = _remove_bg_color(image, bg_color, tolerance)
        elif method == "ai":
            try:
                from rembg import remove
                image = remove(image)
            except ImportError:
                ctx.log("rembg not available, falling back to auto", "WARNING")
                pixels = image.load()
                bg_color = pixels[0, 0][:3]
                image = _remove_bg_color(image, bg_color, tolerance)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG")
        return {"output": str(output_path)}

    elif action == "batch_remove_bg":
        input_dir = Path(inputs.get("input_dir"))
        output_dir = Path(inputs.get("output_dir", ctx.temp_dir / "processed"))
        output_dir.mkdir(parents=True, exist_ok=True)

        processed = []
        for img_path in input_dir.glob("*.png"):
            result = handle("remove_bg", {
                "input": str(img_path),
                "output": str(output_dir / img_path.name),
                "method": inputs.get("method", "auto"),
                "tolerance": inputs.get("tolerance", 30),
            }, ctx)
            processed.append(result["output"])
        return {"processed_images": processed, "output_dir": str(output_dir)}

    elif action == "resize":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output", ctx.temp_dir / "resized.png"))

        if "size" in inputs:
            size = inputs.get("size")
            if isinstance(size, str):
                w, h = map(int, size.lower().split("x"))
            else:
                w, h = size
        else:
            w = int(inputs.get("width", 64))
            h = int(inputs.get("height", w))

        image = Image.open(input_path)
        method = inputs.get("method", "lanczos")
        resampling = {
            "lanczos": Image.Resampling.LANCZOS,
            "bilinear": Image.Resampling.BILINEAR,
            "nearest": Image.Resampling.NEAREST,
        }.get(method, Image.Resampling.LANCZOS)

        image = image.resize((w, h), resampling)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG")
        return {"output": str(output_path)}

    elif action == "make_seamless":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output", ctx.temp_dir / "seamless.png"))
        blend_width = inputs.get("blend_width", 8)

        image = Image.open(input_path)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        result = _make_seamless(image, blend_width)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path, "PNG")
        return {"output": str(output_path)}

    elif action == "tile_preview":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output", ctx.temp_dir / "preview.png"))
        grid_size = inputs.get("grid_size", 3)

        image = Image.open(input_path)
        tile_w, tile_h = image.size
        preview = Image.new(image.mode, (tile_w * grid_size, tile_h * grid_size))
        for row in range(grid_size):
            for col in range(grid_size):
                preview.paste(image, (col * tile_w, row * tile_h))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        preview.save(output_path, "PNG")
        return {"output": str(output_path)}

    elif action == "create_idle_animation":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output", ctx.temp_dir / "idle_sheet.png"))
        frames = int(inputs.get("frames", 4))
        bob_pixels = int(inputs.get("bob_pixels", 2))

        image = Image.open(input_path)
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        animation_frames = _create_idle_animation(image, frames, bob_pixels)
        sheet = _create_sprite_sheet(animation_frames)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, "PNG")
        return {
            "output": str(output_path),
            "frame_count": frames,
            "frame_width": image.width,
            "frame_height": image.height,
        }

    elif action == "create_directional_sheet":
        input_path = Path(inputs.get("input"))
        output_path = Path(inputs.get("output", ctx.temp_dir / "directional_sheet.png"))
        directions = int(inputs.get("directions", 4))

        image = Image.open(input_path)
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        frames_per_direction = 4
        bob_pixels = 2
        front_frames = _create_idle_animation(image, frames_per_direction, bob_pixels)

        all_rows = []
        if directions >= 4:
            all_rows.append(front_frames)  # Down
            all_rows.append([f.transpose(Image.FLIP_LEFT_RIGHT) for f in front_frames])  # Left
            all_rows.append(list(front_frames))  # Right
            all_rows.append(list(front_frames))  # Up (placeholder)

        frame_w, frame_h = image.size
        sheet = Image.new("RGBA",
                          (frame_w * frames_per_direction, frame_h * len(all_rows)),
                          (0, 0, 0, 0))
        for row_idx, row_frames in enumerate(all_rows):
            for col_idx, frame in enumerate(row_frames):
                sheet.paste(frame, (col_idx * frame_w, row_idx * frame_h))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, "PNG")
        return {"output": str(output_path), "directions": directions, "frames_per_direction": 4}

    elif action == "assemble_sheet":
        input_paths = inputs.get("inputs", [])
        output_path = Path(inputs.get("output", ctx.temp_dir / "sheet.png"))
        columns = inputs.get("columns", len(input_paths))

        frames = [Image.open(p).convert("RGBA") for p in input_paths]
        sheet = _create_sprite_sheet(frames, columns)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, "PNG")
        return {"output": str(output_path), "frame_count": len(frames)}

    raise ValueError(f"Unknown image_processor action: {action}")
