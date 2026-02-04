"""
Validation tool — quality gates for workflow outputs.

Checks images for transparency, dimensions, file size, and seamlessness.
"""

from pathlib import Path

TOOL_NAME = "validator"
TOOL_ACTIONS = ["check_image", "check_tileset", "check_sprites"]


def _check_seamless(image, max_diff: int = 20) -> float:
    """Check if a tile is seamless. Returns score 0.0-1.0."""
    from ._image_utils import check_seamless
    return check_seamless(image, max_diff)


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle validation operations."""
    from PIL import Image

    if action == "check_tileset":
        image_path = Path(inputs.get("image"))
        checks = inputs.get("checks", {})

        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        results = {"passed": True, "failures": [], "scores": {}}

        if checks.get("seamless"):
            threshold = checks.get("seamless_threshold", "medium")
            threshold_config = {
                "low": {"max_diff": 40, "min_score": 0.5},
                "medium": {"max_diff": 30, "min_score": 0.65},
                "high": {"max_diff": 20, "min_score": 0.8},
            }
            cfg = threshold_config.get(threshold, threshold_config["medium"])
            seamless_score = _check_seamless(image, cfg["max_diff"])
            results["scores"]["seamless"] = seamless_score

            if seamless_score < cfg["min_score"]:
                results["passed"] = False
                results["failures"].append(
                    f"Seamless score {seamless_score:.2f} < {cfg['min_score']} "
                    f"(threshold: {threshold})"
                )

        if "min_size" in checks:
            min_size = checks["min_size"]
            if image.width < min_size or image.height < min_size:
                results["passed"] = False
                results["failures"].append(
                    f"Size {image.width}x{image.height} < {min_size}"
                )

        if checks.get("square") and image.width != image.height:
            results["passed"] = False
            results["failures"].append(f"Not square: {image.width}x{image.height}")

        return results

    elif action == "check_image":
        image_path = Path(inputs.get("image"))
        checks = inputs.get("checks", {})

        image = Image.open(image_path)
        results = {"passed": True, "failures": []}

        if checks.get("has_transparency"):
            if image.mode != "RGBA":
                results["passed"] = False
                results["failures"].append("No alpha channel")
            else:
                has_transparent = any(p[3] < 255 for p in image.getdata())
                if not has_transparent:
                    results["passed"] = False
                    results["failures"].append("No transparent pixels")

        if "min_width" in checks and image.width < checks["min_width"]:
            results["passed"] = False
            results["failures"].append(f"Width {image.width} < {checks['min_width']}")

        if "min_height" in checks and image.height < checks["min_height"]:
            results["passed"] = False
            results["failures"].append(f"Height {image.height} < {checks['min_height']}")

        if "max_file_size_kb" in checks:
            size_kb = image_path.stat().st_size / 1024
            if size_kb > checks["max_file_size_kb"]:
                results["passed"] = False
                results["failures"].append(
                    f"Size {size_kb:.1f}KB > {checks['max_file_size_kb']}KB"
                )

        return results

    elif action == "check_sprites":
        images_dir = Path(inputs.get("images_dir"))
        checks = inputs.get("checks", [])

        valid_images = []
        quality_scores = {}

        for img_path in images_dir.glob("*.png"):
            result = handle("check_image", {
                "image": str(img_path),
                "checks": {c: True for c in checks} if isinstance(checks, list) else checks,
            }, ctx)
            if result["passed"]:
                valid_images.append(str(img_path))
                quality_scores[str(img_path)] = 1.0
            else:
                quality_scores[str(img_path)] = 0.0

        return {"valid_images": valid_images, "quality_scores": quality_scores}

    raise ValueError(f"Unknown validator action: {action}")
