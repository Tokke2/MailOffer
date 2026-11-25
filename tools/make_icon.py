"""Render committed vector artwork. Build-only dependencies: Pillow, resvg-py.

No generated imagery or fonts are needed at runtime. Print masters stay SVG.
"""
from __future__ import annotations

from tools.generate_branding import generate_all, render_rasters


def build() -> None:
    generate_all()
    render_rasters()


if __name__ == "__main__":
    build()
