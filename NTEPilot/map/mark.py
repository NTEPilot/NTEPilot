import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .map_data import map_data

DEBUG_DIR = Path("./debug")

def mark_teleports(output=None):
    if output is None:
        output = DEBUG_DIR / "map_marked.png"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.open(map_data.BIG_MAP_FILE).convert("RGBA")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except IOError:
        font = ImageFont.load_default()

    for teleport in map_data.iter_visible_teleports():
        x = round(teleport.map_x)
        y = round(teleport.map_y)
        label = str(teleport.number)
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        radius = max(48, int(max(text_w, text_h) * 0.85))
        fill = (18, 18, 18, 220)
        outline = (255, 218, 66, 255)

        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=8)
        draw.text((x - text_w / 2, y - text_h / 2 - 5), label, fill=(255, 255, 255, 255), font=font)

    image.save(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mark teleport numbers on the big map.")
    parser.add_argument("--output", default=None, help="Output image path. Defaults to debug/map_marked.png.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mark_teleports(args.output)


if __name__ == "__main__":
    main()
