# Tool Setup Guide

How to install and configure the services that LocalForge can use.

## Ollama (Recommended)

Local LLM runner. Used for prompt engineering, text processing, and classification.

**Install:**
- https://ollama.ai — Download for your platform

**Pull a model:**
```bash
ollama pull llama3.2:3b      # Small, fast
ollama pull mistral:7b        # Medium, good quality
```

**Verify:**
```bash
curl http://localhost:11434/api/tags
```

**Config:**
```yaml
services:
  ollama:
    host: http://localhost:11434
    default_model: llama3.2:3b
```

## Stable Diffusion WebUI

Image generation via AUTOMATIC1111's web UI.

**Install:**
- https://github.com/AUTOMATIC1111/stable-diffusion-webui

**Start with API enabled:**
```bash
./webui.sh --api
# or on Windows:
webui-user.bat  # (edit to add --api flag)
```

**Verify:**
```bash
curl http://localhost:7860/sdapi/v1/sd-models
```

**Config:**
```yaml
services:
  sd:
    host: http://localhost:7860
    timeout: 120
```

## Blender

3D modeling and rendering.

**Install:**
- https://www.blender.org/download/

**Verify:**
```bash
blender --version
```

**Config:**
```yaml
services:
  blender:
    path: /usr/bin/blender
    # or: C:\Program Files\Blender Foundation\Blender 4.2\blender.exe
    # or: /Applications/Blender.app/Contents/MacOS/Blender
```

If Blender is in your PATH, LocalForge auto-detects it.

## FFmpeg

Audio and video processing.

**Install:**
- **Windows:** https://ffmpeg.org/download.html (add to PATH)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` or `sudo dnf install ffmpeg`

**Verify:**
```bash
ffmpeg -version
```

## MusicGen (Optional)

Music generation using Facebook's AudioCraft.

**Install:**
```bash
git clone https://github.com/facebookresearch/audiocraft.git
cd audiocraft
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
```

**Config:**
```yaml
services:
  musicgen:
    venv_dir: /path/to/audiocraft
```

## Checking Everything

Run the health check to verify your setup:

```bash
python -m localforge health
```

This reports which services are running and which tools are available.
