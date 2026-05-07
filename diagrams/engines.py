from __future__ import annotations

import logging
from pathlib import Path

from core.models import DiagramSpec
from utils.command import CommandRunner


class DiagramEngine:
    def __init__(self, mermaid_cli: str, graphviz_dot: str, runner: CommandRunner) -> None:
        self.mermaid_cli = mermaid_cli
        self.graphviz_dot = graphviz_dot
        self.runner = runner
        self.logger = logging.getLogger(self.__class__.__name__)

    def render_all(self, diagrams: list[DiagramSpec], output_dir: Path) -> list[DiagramSpec]:
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered: list[DiagramSpec] = []
        for index, diagram in enumerate(diagrams, start=1):
            out_path = output_dir / f"diagram_{index:02d}.png"
            self.logger.info("Rendering diagram %d: %s (%s)", index, diagram.title, diagram.diagram_type)
            try:
                if diagram.diagram_type == "mermaid":
                    self._render_mermaid(diagram.source, out_path)
                else:
                    self._render_graphviz(diagram.source, out_path)
                rendered.append(diagram.model_copy(update={"output_path": str(out_path)}))
                self.logger.info("Successfully rendered diagram %d", index)
            except Exception as e:
                self.logger.error("Failed to render diagram %d (%s): %s", index, diagram.title, e)
                # We still append the spec but with no output_path so the pipeline can continue
                rendered.append(diagram.model_copy(update={"output_path": None}))
        return rendered

    def _render_mermaid(self, source: str, output_path: Path) -> None:
        self.runner.ensure_command(self.mermaid_cli)
        source_path = output_path.with_suffix(".mmd")
        self.runner.write_text_file(source_path, source)
        self.runner.run([self.mermaid_cli, "-i", str(source_path), "-o", str(output_path), "-b", "transparent"])

    def _render_graphviz(self, source: str, output_path: Path) -> None:
        self.runner.ensure_command(self.graphviz_dot)
        source_path = output_path.with_suffix(".dot")
        self.runner.write_text_file(source_path, source)
        self.runner.run([self.graphviz_dot, "-Tpng", str(source_path), "-o", str(output_path)])
