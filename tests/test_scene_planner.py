from core.models import DiagramSpec, GenerationRequest, SlideScene, TutorialPlan
from slides.scene_builder import ScenePlanner


def test_scene_planner_scales_to_duration() -> None:
    plan = TutorialPlan(
        topic="Kubernetes",
        language="en",
        audience="beginner",
        style="educational",
        duration="3min",
        introduction_hook="hook",
        architecture_explanation="architecture",
        workflow_explanation="workflow",
        real_life_use_cases=["one"],
        pros_and_cons={"pros": ["p"], "cons": ["c"]},
        related_technologies=["Docker"],
        learning_roadmap=["Learn containers"],
        scenes=[
            SlideScene(index=1, title="a", bullet_points=["x"], narration="n", image_prompt="p", duration_seconds=10),
            SlideScene(index=2, title="b", bullet_points=["y"], narration="n", image_prompt="p", duration_seconds=10),
        ],
        diagrams=[DiagramSpec(title="arch", diagram_type="mermaid", source="graph TD\nA-->B")],
        intro_cta="Like and subscribe",
        outro_cta="Next topic",
    )
    result = ScenePlanner().normalize(
        GenerationRequest(topic="Kubernetes", duration="3min"),
        plan,
    )
    assert round(sum(scene.duration_seconds for scene in result.scenes)) == 180
