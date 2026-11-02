"""Test scan + info + split: keyword match, inspeksi, pisah halaman."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from pdftools.cli import main


def _mk(path: Path, text: str, pages: int = 1) -> Path:
    doc = pymupdf.open()
    for i in range(pages):
        p = doc.new_page()
        p.insert_text((72, 100), text if i == 0 else f"hal {i + 1}", fontsize=12)
    doc.save(path)
    doc.close()
    return path


def test_scan_finds_keyword(tmp_path: Path, capsys):
    _mk(tmp_path / "khs1.pdf", "IPK 3,88 Semester 6")
    _mk(tmp_path / "khs2.pdf", "IPK 3,86 D3")

    rc = main(["scan", str(tmp_path), "--keywords", "3,88"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "khs1.pdf" in out and "3,88" in out
    assert "khs2.pdf" in out and "gak ada match" in out


def test_scan_recursive(tmp_path: Path):
    sub = tmp_path / "sub"
    sub.mkdir()
    _mk(sub / "dalam.pdf", "Tanggal 2026-09-10")

    rc = main(["scan", str(tmp_path), "--keywords", "Tanggal", "--recursive"])
    assert rc == 0


def test_info_shows_pages(tmp_path: Path, capsys):
    f = _mk(tmp_path / "doc.pdf", "Isi dokumen", pages=3)
    rc = main(["info", str(f)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Halaman   : 3" in out
    assert "Isi dokumen" in out


def test_split_pages_range(tmp_path: Path):
    f = _mk(tmp_path / "full.pdf", "awal", pages=4)
    out = tmp_path / "bagian.pdf"

    rc = main(["split", str(f), "--pages", "1,3-4", "-o", str(out)])
    assert rc == 0

    doc = pymupdf.open(out)
    texts = [p.get_text() for p in doc]
    doc.close()
    assert len(texts) == 3
    assert "awal" in texts[0]
