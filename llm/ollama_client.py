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
Provide a deep, clear, and engaging explanation. You must act as a Subject Matter Expert and autonomously decide the most critical aspects, features, and technical pillars to teach based on the topic.

DETAILED REQUIREMENTS:
1. **Autonomous Planning Strategy**:
   - Analyze the RESEARCH CONTEXT to identify the core technical pillars (e.g., Performance, Security, unique features, architecture).
   - Design the slides to progressively explain these pillars. 
   - **Mandatory Elements**: 
     * An Introduction slide to hook the audience.
     * An Architecture/Workflow slide with a `diagram_prompt`.
     * A Real-World Use Case slide with an `image_prompt`.
     * Deep dive slides focusing on the features YOU identified.
     * A FINAL SLIDE summarizing and asking for a Like/Subscribe/Comment.
2. **Content Quality**:
   - Narration: Must be educational, detailed, and professional. Each scene should have at least 3-4 sentences of deep explanation.
   - Bullet Points: Provide 3-5 points per slide. Use them to reinforce the narration.
   - Duration: Ensure durations allow for comfortable reading and listening.

3. **Visual Strategy (CRITICAL)**:
   - **Image Prompts**: Demand high-impact, professional-grade technical art. 
     * Style: 3D isometric or cinematic conceptual art. 
     * Keywords: "Vibrant neon accents", "Cyber-tech aesthetic", "Glassmorphism", "Soft volumetric lighting", "8k resolution", "Premium UI elements".
     * Example: "A futuristic data center with translucent glass servers glowing with internal cyan energy, floating holographic UI showing metrics, deep navy background, cinematic octane render."
     * NO TEXT in images.
   - **Diagrams & Charts**: You MUST include at least 2-3 Mermaid diagrams and 1-2 Charts for a topic this length.
     * Diagrams: Use for architecture, state flows, or components.
     * Charts: Use for performance metrics, comparisons, or data trends.
     * Ensure all syntax and data are logical and research-backed.

4. **Tone and Style**:
   - Use the "{request.style}" style consistently.
   - If audience is "{request.audience}", adjust technical depth accordingly but always remain comprehensive.

JSON schema:
{json.dumps(schema)}
""".strip()
