"""
Ollama LLM tool — the key "worker" integration.

Delegates text generation to local Ollama models, saving tokens
on the paid agent running the workflow.
"""

import requests

from ..engine.config import get_config

TOOL_NAME = "ollama"
TOOL_ACTIONS = ["generate"]


def handle(action: str, inputs: dict, ctx) -> dict:
    """Handle Ollama LLM operations."""
    config = get_config()

    model = inputs.get("model", config.ollama_model)
    prompt = inputs.get("prompt", "")
    system = inputs.get("system", "")
    host = inputs.get("host", config.ollama_host)

    if action == "generate":
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            response = requests.post(
                f"{host}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                },
                timeout=config.service("ollama").get("timeout", 60),
            )
            result = response.json()
            text = result.get("response", "")
            return {"response": text, "sd_prompt": text}
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {host}. "
                f"Is it running? Start it with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Ollama request timed out (model: {model}). "
                f"The model may be loading — try again, or increase timeout in localforge.yaml"
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    raise ValueError(f"Unknown ollama action: {action}")
