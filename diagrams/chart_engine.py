from __future__ import annotations

import logging
from pathlib import Path
import matplotlib.pyplot as plt
from core.models import ChartSpec

class ChartEngine:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        # Use a dark theme for the charts to match the UI
        plt.style.use('dark_background')

    def render_all(self, charts: list[ChartSpec], output_dir: Path) -> list[ChartSpec]:
        if not charts:
            return []
        
        output_dir.mkdir(parents=True, exist_ok=True)
        for i, chart in enumerate(charts):
            filename = f"chart_{i:02d}.png"
            path = output_dir / filename
            try:
                self.render_chart(chart, path)
                chart.output_path = str(path)
            except Exception as e:
                self.logger.error("Failed to render chart '%s': %s", chart.title, e)
        return charts

    def render_chart(self, chart: ChartSpec, output_path: Path) -> str:
        plt.figure(figsize=(8, 6), dpi=100)
        
        # Consistent color palette
        colors = ['#82B4FF', '#A082FF', '#82FFB4', '#FF82B4', '#FFB482']
        
        if chart.chart_type == "bar":
            plt.bar(chart.labels, chart.values, color=colors[:len(chart.labels)])
            if chart.x_label: plt.xlabel(chart.x_label)
            if chart.y_label: plt.ylabel(chart.y_label)
        
        elif chart.chart_type == "line":
            plt.plot(chart.labels, chart.values, marker='o', color='#82B4FF', linewidth=3)
            if chart.x_label: plt.xlabel(chart.x_label)
            if chart.y_label: plt.ylabel(chart.y_label)
            
        elif chart.chart_type == "pie":
            plt.pie(chart.values, labels=chart.labels, autopct='%1.1f%%', colors=colors[:len(chart.labels)])
            
        plt.title(chart.title, pad=20, fontsize=14)
        plt.tight_layout()
        
        # Save with transparent background or matching card color
        plt.savefig(output_path, transparent=True)
        plt.close()
        return str(output_path)
