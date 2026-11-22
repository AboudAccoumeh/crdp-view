#!/usr/bin/env python3
"""Generate the PWA icons used by manifest.webmanifest.

Run with: python make_icons.py
Requires Pillow (python -m pip install pillow).
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "icons"
GREEN = (11, 122, 75, 255)
GREEN_DARK = (7, 92, 56, 255)
WHITE = (255, 255, 255, 255)


def rounded_icon(size, maskable=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Maskable icons keep the artwork inside the central safe circle, so the
    # platform is free to crop the corners without cutting anything off.
    scale = 0.62 if maskable else 1.0
    pad = (size * (1 - scale)) / 2

    def p(x, y):
        return (pad + x * size * scale, pad + y * size * scale)

    # Rounded green tile.
    r = size * 0.22 * scale
    box = [pad, pad, pad + size * scale, pad + size * scale]
    draw.rounded_rectangle(box, radius=r, fill=GREEN)

    # Document with a folded top-right corner.
    doc = [p(0.27, 0.18), p(0.73, 0.82)]
    draw.rounded_rectangle(doc, radius=size * 0.03 * scale, fill=WHITE)
    draw.polygon([p(0.575, 0.18), p(0.73, 0.335), p(0.575, 0.335)], fill=GREEN_DARK)

    # Text lines.
    w = max(2, round(size * 0.028 * scale))
    for y, end in ((0.45, 0.63), (0.56, 0.63), (0.67, 0.52)):
        draw.line([p(0.36, y), p(end, y)], fill=GREEN, width=w)
    return img


def main():
    OUT.mkdir(exist_ok=True)
    root = OUT.parent
    for size in (192, 512):
        rounded_icon(size).save(OUT / f"icon-{size}.png")
        rounded_icon(size, maskable=True).save(OUT / f"icon-maskable-{size}.png")

    # Browser tab icon, in both vector and classic ICO form.
    (root / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="#fff" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round">\n'
        '  <rect width="24" height="24" rx="5" fill="#0b7a4b" stroke="none"/>\n'
        '  <path d="M6.5 4.5h7l3.5 3.5v11a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1v-13a1 1 0 0 1 1-1.5z"/>\n'
        '  <path d="M13.5 4.5V8H17"/>\n'
        '  <path d="M9 12h6M9 15h6M9 18h4"/>\n'
        '</svg>\n', encoding="utf-8")
    rounded_icon(256).save(root / "favicon.ico",
                           sizes=[(16, 16), (32, 32), (48, 48)])

    for path in sorted(root.glob("favicon.*")):
        print(path)
    for path in sorted(OUT.iterdir()):
        print(path)


if __name__ == "__main__":
    main()
