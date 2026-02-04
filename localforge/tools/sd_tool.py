"""
Stable Diffusion WebUI tool.

Generates images via the AUTOMATIC1111 SD WebUI API.
"""

import base64

from ..engine.config import get_config

TOOL_NAME = "sd_client"
TOOL_ACTIONS = ["txt2img", "img2img", "get_models"]


def _get_client(ctx):
    """Get SD client, falling back to direct API if client not importable."""
    try:
        from ..clients.sd_client import SDClient

        config = get_config()
        return SDClient(host=config.sd_host, timeout=config.sd_timeout)
    except ImportError:
        return None


def _sd_direct_api(action: str, inputs: dict, ctx) -> dict:
    """Fallback direct API call if sd_client import fails."""
    import requests

    config = get_config()
    host = config.sd_host

    if action == "txt2img":
        payload = {
            "prompt": inputs.get("prompt", ""),
            "negative_prompt": inputs.get("negative_prompt", ""),
            "width": int(inputs.get("width", 512)),
            "height": int(inputs.get("height", 512)),
            "steps": inputs.get("steps", 20),
            "cfg_scale": inputs.get("cfg_scale", 7.0),
            "batch_size": inputs.get("batch_size", 1),
            "sampler_name": inputs.get("sampler_name", "Euler a"),
        }
        if inputs.get("tiling"):
            payload["tiling"] = True

        response = requests.post(
            f"{host}/sdapi/v1/txt2img", json=payload, timeout=config.sd_timeout
        )
        result = response.json()
        outputs = {}
        for i, img_b64 in enumerate(result.get("images", [])):
            output_path = ctx.temp_dir / f"generated_{i}.png"
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            outputs[f"image_{i}"] = str(output_path)
        if result.get("images"):
            outputs["primary"] = outputs["image_0"]
        return outputs

    raise ValueError(
        f"SD direct API fallback only supports txt2img, not '{action}'. "
        "Install the full package to enable all actions: pip install -e \".[full]\""
    )


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle Stable Diffusion operations."""
    client = _get_client(ctx)

    if client is None:
        ctx.log("SD client not available, using direct API call", "WARNING")
        return _sd_direct_api(action, inputs, ctx)

    if not client.check_status():
        raise RuntimeError("SD WebUI is not running. Start it first.")

    if action == "txt2img":
        width = int(inputs.get("width", 512))
        height = int(inputs.get("height", 512))

        kwargs = {
            "prompt": inputs.get("prompt", ""),
            "negative_prompt": inputs.get("negative_prompt", ""),
            "width": width,
            "height": height,
            "steps": inputs.get("steps", 20),
            "cfg_scale": inputs.get("cfg_scale", 7.0),
            "sampler_name": inputs.get("sampler_name", "Euler a"),
            "batch_size": inputs.get("batch_size", 1),
        }
        if inputs.get("tiling"):
            kwargs["tiling"] = True

        result = client.txt2img(**kwargs)

        outputs = {}
        images = result.get("images", [])
        for i, img_b64 in enumerate(images):
            output_path = ctx.temp_dir / f"generated_{i}.png"
            client.save_image(result, output_path, index=i)
            outputs[f"image_{i}"] = str(output_path)

        if images:
            outputs["raw_images"] = [
                str(ctx.temp_dir / f"generated_{i}.png") for i in range(len(images))
            ]
            outputs["primary"] = outputs["image_0"]

        return outputs

    elif action == "img2img":
        result = client.img2img(
            prompt=inputs.get("prompt", ""),
            init_image=inputs.get("init_image"),
            denoising_strength=inputs.get("denoising_strength", 0.7),
            **{
                k: v
                for k, v in inputs.items()
                if k not in ["prompt", "init_image", "denoising_strength"]
            },
        )
        output_path = ctx.temp_dir / "img2img_result.png"
        client.save_image(result, output_path)
        return {"image": str(output_path)}

    elif action == "get_models":
        return {"models": client.get_models()}

    raise ValueError(f"Unknown sd_client action: {action}")
