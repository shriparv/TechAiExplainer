# TechExplainerAI

`TechExplainerAI` is a complete local-first Python project that turns a technology topic into a polished educational explainer video using Ollama, ComfyUI, Mermaid CLI, Graphviz, Piper TTS, MoviePy, and FFmpeg with NVIDIA NVENC.

The pipeline is:

1. Generate structured tutorial content with Ollama (`llama3`)
2. Break content into scenes and slides
3. Generate images with ComfyUI / SDXL
4. Generate Mermaid and Graphviz diagrams
5. Synthesize narration and subtitles with Piper
6. Compose slides, transitions, and timing with MoviePy
7. Export the final MP4 with FFmpeg `h264_nvenc`
8. Optionally upload the final video to YouTube

## Repository Layout

```text
TechExplainerAI/
├── main.py
├── requirements.txt
├── README.md
├── pyproject.toml
├── config/
├── core/
├── llm/
├── visuals/
├── tts/
├── diagrams/
├── render/
├── slides/
├── uploads/
├── api/
├── frontend/
├── output/
└── utils/
```

## Local Tooling Prerequisites

- `ollama` with model `llama3`
- `ComfyUI` running locally with API access
- `mmdc` from Mermaid CLI
- `dot` from Graphviz
- `piper`
- `ffmpeg` compiled with `h264_nvenc`
- Python 3.10+

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Default Configuration

Copy the defaults in [config/default.yaml](/C:/Users/dwive/OneDrive/Documents/New%20project/config/default.yaml) or override with environment variables:

- `TECHEXPLAINER_OLLAMA_BASE_URL`
- `TECHEXPLAINER_OLLAMA_MODEL`
- `TECHEXPLAINER_COMFYUI_BASE_URL`
- `TECHEXPLAINER_PIPER_MODEL_PATH`
- `TECHEXPLAINER_OUTPUT_DIR`
- `TECHEXPLAINER_FFMPEG_PATH`
- `TECHEXPLAINER_FFPROBE_PATH`
- `TECHEXPLAINER_MERMAID_CLI`
- `TECHEXPLAINER_GRAPHVIZ_DOT`

## CLI

```bash
python main.py --topic "Kubernetes" --duration 5min --language en --audience beginner --style educational
```

Useful flags:

- `--skip-images`
- `--skip-diagrams`
- `--skip-tts`
- `--skip-video`
- `--config config/default.yaml`
- `--youtube`

## API

```bash
uvicorn api.app:app --reload
```

POST `/generate` with:

```json
{
  "topic": "Vector Databases",
  "duration": "5min",
  "language": "en",
  "audience": "beginner",
  "style": "educational"
}
```

## Gradio Frontend

```bash
python -m frontend.app
```

## Example Output

Generated runs create a timestamped directory under [output](/C:/Users/dwive/OneDrive/Documents/New%20project/output) containing:

```text
output/<slug>/
├── plan.json
├── tutorial.json
├── slides/
├── images/
├── diagrams/
├── audio/
├── subtitles/
├── video/
└── final/
```

Key artifacts:

- `tutorial.json`: full structured tutorial payload
- `slides/*.png`: rendered slide images
- `images/*.png`: ComfyUI generated scene images
- `diagrams/*.png`: Mermaid and Graphviz diagrams
- `audio/narration_*.wav`: Piper generated narration
- `subtitles/tutorial.srt`: synced subtitles
- `final/<slug>.mp4`: final rendered explainer video

## Example Topics

- `Kubernetes`
- `RAG Architecture`
- `Microservices`
- `Kafka Streams`
- `Zero Trust Security`
- `MLOps Pipeline`

## Notes

- The project is designed to run fully locally.
- When a local dependency is unavailable, the pipeline raises explicit runtime errors with the exact missing command or endpoint.
- YouTube upload is stubbed behind a pluggable uploader contract so credentials can be added without touching the main pipeline.
