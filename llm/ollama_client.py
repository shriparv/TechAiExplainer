from __future__ import annotations

import json
import logging

import requests

from core.models import GenerationRequest, TutorialPlan
from utils.cache import DiskCache


class OllamaTutorialGenerator:
    def __init__(self, base_url: str, model: str, timeout_seconds: int, cache: DiskCache) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.cache = cache
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(self, request: GenerationRequest, context: str = "") -> TutorialPlan:
        cache_key = request.model_dump_json()
        cached = self.cache.get_json("tutorials", cache_key)
        if cached:
            self.logger.info("Using cached tutorial for topic: %s", request.topic)
            return TutorialPlan.model_validate(cached)

        schema = TutorialPlan.model_json_schema()
        prompt = self._build_prompt(request, schema, context)
        self.logger.info("Generating tutorial using model: %s (prompt size: %d chars)", self.model, len(prompt))
        print(f"\n--- OLLAMA PROMPT SENT ---\n{prompt}\n--------------------------\n")
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "format": schema,
            },
            timeout=self.timeout_seconds,
            stream=True,
        )
        response.raise_for_status()
        
        full_response = ""
        print("\n--- LLM GENERATION START ---", flush=True)
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                text = chunk.get("response", "")
                full_response += text
                print(text, end="", flush=True)
                if chunk.get("done"):
                    break
        print("\n--- LLM GENERATION COMPLETE ---\n", flush=True)

        if not full_response.strip():
            raise RuntimeError("Ollama returned an empty tutorial payload.")
        
        self.logger.info("LLM generation complete. Parsing response...")
        plan = TutorialPlan.model_validate(json.loads(full_response))
        self.cache.set_json("tutorials", cache_key, plan.model_dump())
        return plan

    def _build_prompt(self, request: GenerationRequest, schema: dict, context: str) -> str:
        # Dynamically calculate slide count based on duration string
        # Rule of thumb: ~2.5 scenes per minute for educational content
        minutes = 5.0
        try:
            val_str = "".join(filter(str.isdigit, request.duration))
            if val_str:
                val = float(val_str)
                if "hour" in request.duration or "h" in request.duration:
                    minutes = val * 60
                else:
                    minutes = val
        except Exception:
            pass
        
        slide_count = max(4, int(minutes * 2.5))
        
        return f"""
You are an expert technical educator and broadcast scriptwriter. Your task is to generate a COMPREHENSIVE, professional-grade educational video tutorial plan.

Topic: {request.topic}
Target Duration: {request.duration} (approx {slide_count} scenes)
Language: {request.language}
Audience: {request.audience}
Style: {request.style}

RESEARCH CONTEXT (from internet search):
{context}

Return ONLY valid JSON matching the provided schema.

CORE GOAL:
Provide a deep, clear, and engaging explanation. Avoid surface-level summaries. Explain the "WHY" and "HOW", not just the "WHAT".

DETAILED REQUIREMENTS:
1. **Tutorial Structure**:
   - Comprehensive Intro: Hook the audience, define the tech, and explain its significance.
   - Deep Dive Architecture: Explain components, data flow, and internal mechanics.
   - Real-world Workflow: Step-by-step how it's used in production.
   - Comparison: Pros/Cons and how it differs from competitors/related techs.
   - Future Outlook: Roadmap, trends, and what's next.

2. **Scene Details**:
   - Narration: Must be educational, detailed, and professional. Each scene should have at least 3-4 sentences of deep explanation.
   - Bullet Points: Provide 3-5 points per slide. Use them to reinforce the narration, not just repeat it.
   - Duration: Ensure durations allow for comfortable reading and listening.

3. **Visual Strategy**:
   - Image Prompts: Describe 3D isometric, high-quality, minimalist technical visuals. 
     * Example: "A sleek 3D isometric laboratory with floating data nodes connected by glowing fiber optics, cinematic lighting, 8k."
     * NO TEXT in images.
   - Diagrams: Include Mermaid or Graphviz diagrams for ANY complex architecture, flow, or comparison.
     * Use "graph TD;" for Mermaid flowcharts.
     * Use "digraph G {{ ... }}" for Graphviz.
     * Ensure the diagrams are syntactically correct and logical.
   - Charts: Include data-driven charts (bar, line, or pie) for technical metrics, performance comparisons, or market trends.
     * Ensure labels and values are realistic and based on the research context.

4. **Tone and Style**:
   - Use the "{request.style}" style consistently.
   - If audience is "{request.audience}", adjust technical depth accordingly but always remain comprehensive.

JSON schema:
{json.dumps(schema)}
""".strip()
