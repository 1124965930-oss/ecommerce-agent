"""Image generation service — PIL-based mock product images with text overlays."""

import os
import random
import textwrap


class ImageService:
    def __init__(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir

    def generate_product_image(
        self,
        product_title: str,
        features: list[str],
        style: str = "infographic",
        badge: str = None,
    ) -> str:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return self._generate_placeholder(product_title, features)
        return self._generate_pil(product_title, features, style, badge, Image, ImageDraw, ImageFont)

    def _generate_pil(self, title, features, style, badge, Image, ImageDraw, ImageFont):
        w, h = 1000, 1000
        bg_color = (random.randint(240, 255), random.randint(240, 255), random.randint(245, 255))
        img = Image.new("RGB", (w, h), bg_color)
        draw = ImageDraw.Draw(img)

        # Product area (top 55%)
        product_colors = [
            (52, 152, 219), (46, 204, 113), (230, 126, 34),
            (155, 89, 182), (52, 73, 94), (231, 76, 60),
        ]
        base_color = product_colors[hash(title) % len(product_colors)]
        for x in range(120, 880, 20):
            for y in range(60, 500, 20):
                noise = random.randint(-5, 5)
                draw.rectangle(
                    [x, y, x + 18, y + 18],
                    fill=tuple(min(255, max(0, c + noise)) for c in base_color),
                )

        # Product silhouette
        draw.rounded_rectangle([250, 100, 750, 450], radius=40, fill=(255, 255, 255, 220), outline=base_color, width=3)
        draw.ellipse([350, 160, 650, 390], fill=tuple(c // 2 for c in base_color))

        # Try to load a font, fall back to default
        try:
            font_lg = ImageFont.truetype("arial.ttf", 36)
            font_md = ImageFont.truetype("arial.ttf", 24)
            font_sm = ImageFont.truetype("arial.ttf", 18)
        except OSError:
            font_lg = ImageFont.load_default()
            font_md = font_lg
            font_sm = font_lg

        # Product title (wrapped)
        lines = textwrap.wrap(title, width=35)
        y_text = 520
        for line in lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=font_lg)
            dw = bbox[2] - bbox[0]
            draw.text(((w - dw) // 2, y_text), line, fill=(30, 30, 30), font=font_lg)
            y_text += 45

        # Feature bullets
        y_text = 620
        for f in features[:4]:
            draw.rounded_rectangle([120, y_text, 140, y_text + 20], radius=10, fill=base_color)
            draw.text((155, y_text - 2), f"  {f[:55]}", fill=(60, 60, 60), font=font_sm)
            y_text += 40

        # Price / CTA section
        draw.rectangle([0, 860, w, h], fill=(30, 30, 30))
        draw.text((w // 2 - 80, 880), "LIMITED OFFER", fill=(255, 200, 0), font=font_md)
        draw.rounded_rectangle([400, 915, 600, 970], radius=15, fill=(255, 80, 0))
        draw.text((440, 930), "BUY NOW", fill=(255, 255, 255), font=font_lg)

        # Badge
        if badge:
            import math
            badge_x, badge_y, badge_r = 830, 130, 100
            draw.ellipse(
                [badge_x - badge_r, badge_y - badge_r, badge_x + badge_r, badge_y + badge_r],
                fill=(255, 50, 50), outline=(255, 255, 255), width=4,
            )
            # Rotated-ish badge text
            bbox_b = draw.textbbox((0, 0), badge, font=font_md)
            bw = bbox_b[2] - bbox_b[0]
            draw.text((badge_x - bw // 2, badge_y - 15), badge, fill=(255, 255, 255), font=font_md)

        filename = f"product_{abs(hash(title)) % 100000}_{random.randint(100, 999)}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, "PNG")
        return filepath

    def _generate_placeholder(self, title: str, features: list[str]) -> str:
        filename = f"product_{abs(hash(title)) % 100000}_placeholder.png"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"")
        return filepath
