# Use Cases

LocalForge is domain-agnostic. Here are examples of what you can build with it.

## Game Development

- **Sprites:** Generate pixel art characters with background removal
- **Tilesets:** Seamless textures with validation and refinement
- **Sprite sheets:** Idle animations, directional movement sheets
- **Audio:** Background music tracks and sound effects
- **3D models:** Primitives, dice sets, isometric backgrounds
- **Game starter packs:** Combine all of the above into a single recipe

**Example:** Generate a complete set of game assets by chaining recipes.

## Content Creation

- **Blog posts:** Outline → draft → edit → images → publish-ready
- **Social media:** Text + image generation pipeline
- **Documentation:** Auto-generate from code with formatting
- **Newsletters:** Multi-section content with generated imagery

## Data Processing

- **Text classification:** Use local LLMs to categorize documents
- **Summarization:** Batch process documents through Ollama
- **Data extraction:** Parse and transform structured data
- **Report generation:** Aggregate data → analysis → formatted output

## Publishing

- **Manuscript processing:** Multiple editing passes via LLM
- **Cover design:** Text prompt → SD generation → post-processing
- **Format conversion:** Audio/video transcoding pipelines

## Automation

- **Media processing:** Batch image resize, format conversion, optimization
- **Audio normalization:** Consistent volume levels across files
- **File organization:** Sort, rename, and process file batches
- **Custom pipelines:** Any multi-step process you can define in YAML

## Building Your Own

1. Start with `recipes/TEMPLATE.yaml`
2. Define your inputs and desired outputs
3. Chain tools: Ollama for text → SD for images → FFmpeg for audio
4. Add validation gates for quality control
5. Use refinement loops for iterative improvement
