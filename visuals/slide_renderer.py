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
        
        # --- MODERN DESIGN SYSTEM ---
        # Palette: Deep Navy / Cyber Blue / Vibrant Accents
        bg_top = (10, 15, 25)
        bg_bottom = (20, 30, 45)
        card_fill = (30, 40, 55, 180) # Semi-transparent for glass effect
        card_border = (80, 120, 255, 100)
        
        text_primary = (255, 255, 255)
        text_secondary = (200, 210, 230)
        accent_color = (0, 210, 255) # Electric Cyan
        accent_secondary = (150, 100, 255) # Cyber Purple
        
        margin = 60
        
        # Load fonts (Prefer Segoe UI on Windows for a cleaner look)
        def get_font(size: int, bold: bool = False):
            try:
                # Try Segoe UI (Standard on Windows)
                paths = [
                    "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
                    "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf"
                ]
                for p in paths:
                    if Path(p).exists():
                        return ImageFont.truetype(p, size)
            except Exception:
                pass
            return ImageFont.load_default()

        title_font = get_font(72, bold=True)
        body_font = get_font(42)
        footer_font = get_font(24)
        
        # Create canvas with background gradient
        image = Image.new("RGBA", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        # 1. Background Gradient
        for y in range(self.height):
            r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * y / self.height)
            g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * y / self.height)
            b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * y / self.height)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b, 255))

        # 2. Decorative Background Elements (Subtle Glows)
        self._draw_glow(draw, (self.width * 0.8, self.height * 0.2), 400, accent_secondary + (30,))
        self._draw_glow(draw, (self.width * 0.2, self.height * 0.8), 300, accent_color + (30,))

        # 3. Dynamic Layout Logic
        assets = []
        if scene.image_path and Path(scene.image_path).exists():
            assets.append(("image", scene.image_path))
        if scene.diagram_path and Path(scene.diagram_path).exists():
            assets.append(("diagram", scene.diagram_path))
        if scene.chart_path and Path(scene.chart_path).exists():
            assets.append(("chart", scene.chart_path))

        # Layout splits
        if assets:
            text_area_width = (self.width * 0.55) - (2 * margin)
            asset_area_x = self.width * 0.55
            asset_area_width = self.width * 0.45 - margin
        else:
            text_area_width = self.width - (2 * margin) - 100
            asset_area_x = self.width
            asset_area_width = 0

        # 4. Glass Card
        card_rect = [margin, margin, self.width - margin, self.height - margin]
        # Overlay for glass effect
        glass_overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        glass_draw = ImageDraw.Draw(glass_overlay)
        glass_draw.rounded_rectangle(card_rect, radius=40, fill=card_fill, outline=card_border, width=2)
        image = Image.alpha_composite(image, glass_overlay)
        draw = ImageDraw.Draw(image)

        # 5. Render Title with Underline
        title_y = margin + 60
        draw.text((margin + 60, title_y), scene.title, fill=text_primary, font=title_font)
        # Accent Underline
        draw.rectangle([margin + 60, title_y + 90, margin + 260, title_y + 98], fill=accent_color)

        # 6. Render Bullet Points
        curr_y = title_y + 160
        bullet_margin = 40
        for bullet in scene.bullet_points:
            wrapped = self._wrap_text(bullet, body_font, text_area_width - bullet_margin)
            # Custom Bullet Marker (Glowy Dot)
            draw.ellipse([margin + 60, curr_y + 15, margin + 75, curr_y + 30], fill=accent_color)
            
            for i, line in enumerate(wrapped):
                draw.text((margin + 60 + bullet_margin, curr_y), line, fill=text_secondary, font=body_font)
                curr_y += 55
            curr_y += 25

        # 7. Render Visual Assets
        if assets:
            available_h = self.height - (2 * margin) - 120
            h_per = available_h // len(assets)
            ay = margin + 60
            for type_name, path in assets:
                try:
                    asset_img = Image.open(path).convert("RGBA")
                    # Scale to fit
                    mw, mh = asset_area_width - 60, h_per - 40
                    asset_img.thumbnail((mw, mh), Image.Resampling.LANCZOS)
                    
                    # Center in slot
                    px = asset_area_x + (mw - asset_img.width) // 2
                    py = ay + (mh - asset_img.height) // 2
                    
                    # Draw a subtle container for the image
                    draw.rounded_rectangle([px-5, py-5, px+asset_img.width+5, py+asset_img.height+5], radius=15, outline=(255,255,255,40), width=1)
                    
                    image.paste(asset_img, (int(px), int(py)), asset_img if asset_img.mode == "RGBA" else None)
                    ay += h_per
                except Exception as e:
                    self.logger.error("Failed to render asset %s: %s", path, e)

        # 8. Footer Info
        footer_text = f"CHAPTER: {scene.title.upper()} | STEP {scene.index}"
        draw.text((margin + 60, self.height - margin - 60), footer_text, fill=accent_color, font=footer_font)
        
        # Save as RGB for video compatibility
        image.convert("RGB").save(output_path)
        return str(output_path)

    def _draw_glow(self, draw: ImageDraw.ImageDraw, pos: tuple[float, float], radius: int, color: tuple[int, int, int, int]):
        """Draws a simple radial glow effect."""
        cx, cy = pos
        for r in range(radius, 0, -10):
            alpha = int(color[3] * (1 - r / radius))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color[:3] + (alpha,))

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
