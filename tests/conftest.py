"""Fixtures pembuat file test: PDF mini, gambar, placeholder 3:4 polos."""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image


def make_pdf(path: Path, n_pages: int = 2, text: str = "Halo PDF") -> Path:
    doc = pymupdf.open()
    for i in range(n_pages):
        page = doc.new_page()
        page.insert_text((72, 100), f"{text} hal {i + 1}", fontsize=14)
    doc.save(path)
    doc.close()
    return path


def make_pdf_with_placeholder(path: Path) -> Path:
    """PDF berisi 1 kotak placeholder 3:4 polos (abu) + 1 gambar berisi."""
    doc = pymupdf.open()
    page = doc.new_page()

    # placeholder: abu polos, rasio 3:4 (60x80 pt)
    mono = Image.new("L", (60, 80), 200)
    buf_mono = io.BytesIO()
    mono.save(buf_mono, format="JPEG", quality=92)
    page.insert_image(pymupdf.Rect(100, 100, 160, 180), stream=buf_mono.getvalue())

    # gambar "berisi": gradient
    gradient = Image.new("L", (80, 60))
    gradient.putdata([int((x + y) * 255 / 140) for y in range(60) for x in range(80)])
    buf_g = io.BytesIO()
    gradient.save(buf_g, format="JPEG", quality=92)
    page.insert_image(pymupdf.Rect(200, 100, 280, 160), stream=buf_g.getvalue())

    doc.save(path)
    doc.close()
    return path


def make_image(path: Path, size: tuple[int, int] = (300, 400), color: str = "tomato") -> Path:
    img = Image.new("RGB", size, color)
    img.save(path)
    return path
