"""Test photo detect + insert: kandidat 3:4 polos ketemu, foto masuk, original aman."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from pdftools.cli import main
from tests.conftest import make_pdf_with_placeholder


def test_detect_finds_placeholder(tmp_path: Path, capsys):
    pdf = make_pdf_with_placeholder(tmp_path / "skl.pdf")

    rc = main(["photo", "detect", str(pdf)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "KANDIDAT placeholder" in out


def test_insert_photo(tmp_path: Path):
    pdf = make_pdf_with_placeholder(tmp_path / "skl.pdf")
    original_bytes = pdf.read_bytes()
    foto = tmp_path / "pas_foto.jpg"

    # foto beneran ramai (gradient) biar verifikasi keragaman naik
    from PIL import Image

    img = Image.new("RGB", (300, 400))
    img.putdata([(r % 256, g % 256, b % 256)
                 for g in range(400) for r, b in [(g * 2, 255 - g)]])
    img.save(foto, format="JPEG", quality=92)

    out = tmp_path / "skl_foto.pdf"
    rc = main(["photo", "insert", str(pdf), str(foto), "-o", str(out), "--auto"])
    assert rc == 0

    assert pdf.read_bytes() == original_bytes  # original aman
    assert out.exists()

    # placeholder terganti: foto 300x400 masuk ke daftar gambar PDF hasil
    doc = pymupdf.open(out)
    assert doc.page_count == 1
    imgs = doc[0].get_images(full=True)
    doc.close()
    assert any(im[2] == 300 and im[3] == 400 for im in imgs), "foto gak masuk"
