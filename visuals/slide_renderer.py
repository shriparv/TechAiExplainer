import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.models import SlideScene


class SlideComposer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.logger = logging.getLogger(self.__class__.__name__)

    def render(self, scene: SlideScene, output_path: Path) -> str:
        self.logger.info("Rendering slide %d: %s", scene.index, scene.title)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Base colors and layout constants
        bg_color = (14, 18, 24)
        card_color = (24, 30, 38)
        text_primary = (240, 240, 240)
        text_secondary = (220, 224, 230)
        accent_color = (130, 180, 255)
        
        margin = 80
        content_x = margin + 50
        max_text_width = (self.width // 2) - margin
        
        # Load fonts
        try:
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            title_font = ImageFont.truetype(font_path, 64)
            body_font = ImageFont.truetype(font_path, 38)
            footer_font = ImageFont.truetype(font_path, 24)
        except Exception:
            self.logger.warning("Arial font not found, falling back to default")
            title_font = body_font = footer_font = ImageFont.load_default()

        # Create canvas
        image = Image.new("RGB", (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        # Background card
        draw.rounded_rectangle((margin, margin, self.width - margin, self.height - margin), radius=32, fill=card_color)
        
        # Title
        draw.text((content_x, margin + 40), scene.title, fill=text_primary, font=title_font)
        
        # Bullet points with wrapping
        y = margin + 160
        for bullet in scene.bullet_points:
            wrapped_lines = self._wrap_text(bullet, body_font, max_text_width)
            for line in wrapped_lines:
                draw.text((content_x + 20, y), f"- {line}" if line == wrapped_lines[0] else f"  {line}", fill=text_secondary, font=body_font)
                y += 55
            y += 20

        # Footer
        footer = f"Scene {scene.index} | Duration: {scene.duration_seconds:.1f}s"
        draw.text((content_x, self.height - margin - 50), footer, fill=accent_color, font=footer_font)

        # Visual Assets (Right Side)
        right_content_x = (self.width // 2) + 40
        available_height = self.height - (2 * margin) - 100
        
        assets = []
        if scene.image_path and Path(scene.image_path).exists():
            assets.append(("image", scene.image_path))
        if scene.diagram_path and Path(scene.diagram_path).exists():
            assets.append(("diagram", scene.diagram_path))
        if scene.chart_path and Path(scene.chart_path).exists():
            assets.append(("chart", scene.chart_path))

        if assets:
            # Distribute height between assets
            h_per_asset = available_height // len(assets)
            curr_y = margin + 50
            for type_name, path in assets:
                asset_img = Image.open(path).convert("RGBA" if type_name == "diagram" else "RGB")
                
                # Resize keeping aspect ratio
                max_w = self.width - right_content_x - margin - 40
                max_h = h_per_asset - 40
                
                asset_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                
                # Center asset in its assigned slot
                paste_x = right_content_x + (max_w - asset_img.width) // 2
                paste_y = curr_y + (max_h - asset_img.height) // 2
                
                if asset_img.mode == "RGBA":
                    # Use alpha for diagram transparency if supported
                    temp = Image.new("RGB", asset_img.size, card_color)
                    temp.paste(asset_img, mask=asset_img.split()[3])
                    image.paste(temp, (paste_x, paste_y))
                else:
                    image.paste(asset_img, (paste_x, paste_y))
                
                curr_y += h_per_asset

        image.save(output_path)
        return str(output_path)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            w = font.getlength(test_line)
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        return lines
