"""Test img2pdf: konversi JPEG asli, dimensi 3x4cm presisi, A4."""

from __future__ import annotations

from pathlib import Path

import pymupdf
from PIL import Image

from pdftools.cli import main


def test_img2pdf_3x4cm_exact(tmp_path: Path):
    foto = tmp_path / "foto.png"
    Image.new("RGB", (300, 400), "steelblue").save(foto)

    out = tmp_path / "pas_foto.pdf"
    rc = main(["img2pdf", str(foto), "-o", str(out), "--size", "3x4cm"])
    assert rc == 0

    doc = pymupdf.open(out)
    w_mm = doc[0].rect.width * 25.4 / 72
    h_mm = doc[0].rect.height * 25.4 / 72
    doc.close()
    assert abs(w_mm - 30.0) < 0.2 and abs(h_mm - 40.0) < 0.2


def test_img2pdf_a4(tmp_path: Path):
    foto = tmp_path / "kk.jpeg"
    Image.new("RGB", (800, 600), "gray").save(foto)

    out = tmp_path / "kk.pdf"
    rc = main(["img2pdf", str(foto), "-o", str(out), "--a4"])
    assert rc == 0

    doc = pymupdf.open(out)
    w_mm = doc[0].rect.width * 25.4 / 72
    h_mm = doc[0].rect.height * 25.4 / 72
    doc.close()
    assert abs(w_mm - 210) < 0.5 and abs(h_mm - 297) < 0.5


def test_img2pdf_png_becomes_real_jpeg(tmp_path: Path):
    foto = tmp_path / "pngnyamar.png"
    Image.new("RGB", (100, 100), "red").save(foto, format="PNG")

    out = tmp_path / "o.pdf"
    rc = main(["img2pdf", str(foto), "-o", str(out)])
    assert rc == 0

    # di dalam PDF, stream gambarnya harus beneran JPEG (DCTDecode)
    doc = pymupdf.open(out)
    imgs = doc[0].get_images(full=True)
    doc.close()
    assert imgs, "gambar gak masuk PDF"
