from __future__ import annotations

import copy
import json
import logging
import time
from pathlib import Path

import requests

from utils.cache import DiskCache


class ComfyUIClient:
    def __init__(self, base_url: str, workflow_path: str, poll_interval_seconds: int, cache: DiskCache) -> None:
        self.base_url = base_url.rstrip("/")
        self.workflow_template = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
        self.poll_interval_seconds = poll_interval_seconds
        self.cache = cache
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_image(self, prompt: str, output_dir: Path, name: str) -> str | None:
        cached = self.cache.get_json("images", prompt)
        if cached and Path(cached["path"]).exists():
            self.logger.info("Using cached image for: %s", prompt[:50])
            return cached["path"]

        try:
            self.logger.info("Submitting prompt to ComfyUI: %s...", prompt[:50])
            print(f"\n--- COMFYUI IMAGE PROMPT ---\n{prompt}\n----------------------------")
            workflow = copy.deepcopy(self.workflow_template)
            
            # Dynamic node targeting for different workflows
            if "91" in workflow: # Qwen-Image-2512 Workflow
                workflow["91"]["inputs"]["w_0"] = prompt
            elif "6" in workflow: # Standard SDXL/Flux Workflow
                workflow["6"]["inputs"]["text"] = prompt
            else:
                self.logger.warning("Could not find a recognized prompt node in workflow. Attempting default node 6.")
                workflow["6"]["inputs"]["text"] = prompt
                
            response = requests.post(f"{self.base_url}/prompt", json={"prompt": workflow}, timeout=10)
            response.raise_for_status()
            prompt_id = response.json()["prompt_id"]
            self.logger.info("Prompt submitted (ID: %s). Waiting for image generation...", prompt_id)
            image_path = self._wait_for_image(prompt_id, output_dir, name)
            self.cache.set_json("images", prompt, {"path": image_path})
            print(f"--- COMFYUI IMAGE SAVED: {image_path} ---\n")
            return image_path
        except Exception as e:
            self.logger.warning("ComfyUI generation failed (server may be offline or model missing): %s", e)
            return None

    def _wait_for_image(self, prompt_id: str, output_dir: Path, name: str) -> str:
        output_dir.mkdir(parents=True, exist_ok=True)
        start_time = time.time()
        while True:
            self.logger.debug("Polling ComfyUI for prompt %s (elapsed: %.1fs)", prompt_id, time.time() - start_time)
            history = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=30)
            history.raise_for_status()
            payload = history.json()
            if prompt_id in payload:
                outputs = payload[prompt_id].get("outputs", {})
                for node_output in outputs.values():
                    for image in node_output.get("images", []):
                        filename = image["filename"]
                        subfolder = image.get("subfolder", "")
                        image_response = requests.get(
                            f"{self.base_url}/view",
                            params={"filename": filename, "subfolder": subfolder, "type": image.get("type", "output")},
                            timeout=60,
                        )
                        image_response.raise_for_status()
                        target = output_dir / f"{name}.png"
                        target.write_bytes(image_response.content)
                        return str(target)
            time.sleep(self.poll_interval_seconds)
