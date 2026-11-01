"""Render the GitHub social preview card (Settings -> Social preview).

Run: uv run --no-project --with pillow python assets/social_preview.py
Windows-only as written: it uses the Consolas / Segoe UI fonts in C:/Windows/Fonts.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1280, 640
# GitHub crops unevenly on some surfaces; keep content inside this border
MARGIN = 80
FONTS = Path("C:/Windows/Fonts")
OUT = Path(__file__).with_name("social-preview.png")

# Catppuccin Mocha, to match the demo GIF
BG = "#1e1e2e"
PANEL = "#181825"
TEXT = "#cdd6f4"
SUBTLE = "#a6adc8"
DIM = "#6c7086"
ACCENT = "#94e2d5"
YELLOW = "#f9e2af"

# Real entries from manifests/25d726e0-fe39-4610-ad90-460341bff3c2.manifest (26100.1297)
PDBS = [
    ("ntkrnlmp.pdb", "B6CDAA3A3EF13C3B2799115B0470342B1"),
    ("ntdll.pdb", "E3C16524B6DB48109A895BFE84669AC11"),
    ("kernelbase.pdb", "1C7412263B39BD94062C50743E8662C71"),
    ("tcpip.pdb", "256E595DB835F1FABE3DC077E042F3191"),
]
MORE = "+ ~15,000 more"
BUILDS = "1,600+ Windows builds mapped"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS / name
    try:
        return ImageFont.truetype(str(path), size)
    except OSError as err:
        sys.exit(f"social_preview: cannot load font {path}: {err}")


def main() -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    title = font("segoeuib.ttf", 64)
    subtitle = font("segoeui.ttf", 32)
    mono = font("consola.ttf", 26)
    mono_bold = font("consolab.ttf", 26)

    draw.text((MARGIN, MARGIN - 10), "WindowsSymbolsByVersion", font=title, fill=TEXT)
    draw.text(
        (MARGIN, MARGIN + 75),
        "PDB debug symbols for any Windows build, even airgapped",
        font=subtitle,
        fill=SUBTLE,
    )

    panel_top, panel_bottom = MARGIN + 150, HEIGHT - MARGIN - 50
    draw.rounded_rectangle((MARGIN, panel_top, WIDTH - MARGIN, panel_bottom), radius=14, fill=PANEL)

    x, y, line = MARGIN + 30, panel_top + 24, 38
    draw.text((x, y), ">", font=mono_bold, fill=DIM)
    draw.text((x + 28, y), "winsyms get", font=mono_bold, fill=YELLOW)
    draw.text((x + 28 + 165, y), "26100.1297", font=mono, fill=TEXT)
    y += line + 6
    for name, guid in PDBS:
        draw.text((x + 28, y), name, font=mono, fill=ACCENT)
        draw.text((x + 290, y), guid, font=mono, fill=DIM)
        y += line
    draw.text((x + 28, y), MORE, font=mono, fill=SUBTLE)

    footer_y = HEIGHT - MARGIN - 30
    draw.text((MARGIN, footer_y), BUILDS, font=subtitle, fill=ACCENT)
    pip = "pip install winsyms"
    pip_w = draw.textlength(pip, font=mono_bold)
    draw.text((WIDTH - MARGIN - pip_w, footer_y + 12), pip, font=mono_bold, fill=TEXT)

    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
