"""
Stable Diffusion WebUI API client.

Provides image generation capabilities via the AUTOMATIC1111 API.

Usage:
    from clients.sd_client import SDClient

    client = SDClient()
    if client.check_status():
        result = client.txt2img("pixel art spaceship", width=64, height=64)
        client.save_image(result, "spaceship.png")
"""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests


class SDClient:
    """Client for Stable Diffusion WebUI API."""

    def __init__(self, host: str = "http://localhost:7860", timeout: int = 120):
        self.host = host.rstrip("/")
        self.timeout = timeout

    def check_status(self) -> bool:
        """Check if SD WebUI is running."""
        try:
            response = requests.get(f"{self.host}/sdapi/v1/sd-models", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available checkpoint models."""
        try:
            response = requests.get(
                f"{self.host}/sdapi/v1/sd-models", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def get_current_model(self) -> Optional[str]:
        """Get currently loaded model name."""
        try:
            response = requests.get(
                f"{self.host}/sdapi/v1/options", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get("sd_model_checkpoint")
        except requests.exceptions.RequestException:
            return None

    def set_model(self, model_name: str) -> bool:
        """Set the active checkpoint model."""
        try:
            response = requests.post(
                f"{self.host}/sdapi/v1/options",
                json={"sd_model_checkpoint": model_name},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            return False

    def txt2img(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler_name: str = "Euler a",
        seed: int = -1,
        batch_size: int = 1,
        n_iter: int = 1,
        **options,
    ) -> Dict[str, Any]:
        """Generate image from text prompt."""
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler_name,
            "seed": seed,
            "batch_size": batch_size,
            "n_iter": n_iter,
            **options,
        }

        try:
            response = requests.post(
                f"{self.host}/sdapi/v1/txt2img",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"images": [], "parameters": payload, "info": str(e)}

    def img2img(
        self,
        prompt: str,
        init_image: Union[str, Path, bytes],
        negative_prompt: str = "",
        denoising_strength: float = 0.7,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler_name: str = "Euler a",
        seed: int = -1,
        **options,
    ) -> Dict[str, Any]:
        """Generate image from image + prompt."""
        if isinstance(init_image, (str, Path)):
            path = Path(init_image)
            if path.exists():
                with open(path, "rb") as f:
                    init_image_b64 = base64.b64encode(f.read()).decode("utf-8")
            else:
                init_image_b64 = str(init_image)
        elif isinstance(init_image, bytes):
            init_image_b64 = base64.b64encode(init_image).decode("utf-8")
        else:
            init_image_b64 = init_image

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "init_images": [init_image_b64],
            "denoising_strength": denoising_strength,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler_name,
            "seed": seed,
            **options,
        }

        try:
            response = requests.post(
                f"{self.host}/sdapi/v1/img2img",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"images": [], "parameters": payload, "info": str(e)}

    def get_samplers(self) -> List[Dict[str, Any]]:
        """Get available samplers."""
        try:
            response = requests.get(
                f"{self.host}/sdapi/v1/samplers", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def get_progress(self) -> Dict[str, Any]:
        """Get current generation progress."""
        try:
            response = requests.get(
                f"{self.host}/sdapi/v1/progress", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {"progress": 0, "eta_relative": 0}

    def interrupt(self) -> bool:
        """Interrupt current generation."""
        try:
            response = requests.post(
                f"{self.host}/sdapi/v1/interrupt", timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def save_image(
        result: Dict[str, Any], output_path: Union[str, Path], index: int = 0
    ) -> bool:
        """Save generated image to file."""
        try:
            images = result.get("images", [])
            if not images or index >= len(images):
                return False

            image_data = base64.b64decode(images[index])
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(image_data)
            return True
        except Exception:
            return False

    def generate_and_save(
        self, prompt: str, output_path: Union[str, Path], **kwargs
    ) -> bool:
        """Generate image and save directly."""
        result = self.txt2img(prompt, **kwargs)
        return self.save_image(result, output_path)


def is_sd_running(host: str = "http://localhost:7860") -> bool:
    """Check if SD WebUI is running."""
    return SDClient(host).check_status()
