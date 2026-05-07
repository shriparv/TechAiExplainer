import logging
from core.models import GenerationRequest, SlideScene, TutorialPlan


class ScenePlanner:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def normalize(self, request: GenerationRequest, plan: TutorialPlan) -> TutorialPlan:
        # Dynamically calculate target seconds
        target_seconds = 300
        try:
            val_str = "".join(filter(str.isdigit, request.duration))
            if val_str:
                val = float(val_str)
                if "hour" in request.duration or "h" in request.duration:
                    target_seconds = int(val * 3600)
                else:
                    target_seconds = int(val * 60)
        except Exception:
            pass
        current = sum(scene.duration_seconds for scene in plan.scenes)
        if not plan.scenes or current <= 0:
            raise ValueError("Tutorial plan must include scenes with positive durations.")
        scale = target_seconds / current
        self.logger.info("Normalizing tutorial duration: current=%.1fs, target=%ds, scale=%.2f", current, target_seconds, scale)
        plan.scenes = [
            SlideScene(
                **{
                    **scene.model_dump(),
                    "duration_seconds": round(scene.duration_seconds * scale, 2),
                }
            )
            for scene in plan.scenes
        ]
        return plan
