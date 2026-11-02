"""Test merge: page count, metadata, original aman."""

from __future__ import annotations

from pathlib import Path

import pymupdf
from pypdf import PdfReader

from pdftools.cli import main


def test_merge_two_pdfs(tmp_path: Path):
    a = pymupdf.open()
    a.new_page()
    a.save(tmp_path / "a.pdf")
    a.close()
    b = pymupdf.open()
    b.new_page()
    b.new_page()
    b.save(tmp_path / "b.pdf")
    b.close()

    out = tmp_path / "gabungan.pdf"
    rc = main(["merge", str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf"),
               "-o", str(out), "--title", "Tes", "--author", "Gw"])
    assert rc == 0

    reader = PdfReader(out)
    assert len(reader.pages) == 3
    assert reader.metadata.title == "Tes"


def test_merge_never_touches_original(tmp_path: Path):
    a = tmp_path / "a.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(a)
    doc.close()
    before = a.read_bytes()

    out = tmp_path / "a.pdf"  # output "nimpa" — harus di-rename jadi _BARU
    rc = main(["merge", str(a), str(a), "-o", str(out)])
    assert rc == 0
    assert a.read_bytes() == before              # original byte-per-byte sama
    assert (tmp_path / "a_BARU.pdf").exists()


def test_merge_missing_input_fails(tmp_path: Path):
    rc = main(["merge", str(tmp_path / "gakada.pdf"), "-o", str(tmp_path / "o.pdf")])
    assert rc == 1
