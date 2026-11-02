"""Test utils: parse_pages, fmt_size, safe_write + perilaku lock."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdftools.utils import FileLockError, fmt_size, parse_pages, pt2mm, safe_write


def test_parse_pages_basic():
    assert parse_pages("1,3-4", 10) == [1, 3, 4]


def test_parse_pages_sorted_unique():
    assert parse_pages("4-5,1,1", 10) == [1, 4, 5]


def test_parse_pages_out_of_range():
    with pytest.raises(ValueError):
        parse_pages("1,11", 10)


def test_parse_pages_bad_range():
    with pytest.raises(ValueError):
        parse_pages("5-2", 10)


def test_fmt_size():
    assert fmt_size(512) == "512 B"
    assert "MB" in fmt_size(5 * 1024 * 1024)


def test_pt2mm():
    assert abs(pt2mm(72) - 25.4) < 0.01


def test_safe_write_new_file(tmp_path: Path):
    out = tmp_path / "out.txt"

    def w(p: Path):
        p.write_text("data")

    final = safe_write(out, w)
    assert final == out
    assert final.read_text() == "data"


def test_safe_write_never_overwrites(tmp_path: Path):
    out = tmp_path / "out.txt"
    out.write_text("ORIGINAL")

    def w(p: Path):
        p.write_text("BARU")

    final = safe_write(out, w)
    assert out.read_text() == "ORIGINAL"           # original aman
    assert final.name == "out_BARU.txt"            # output ke file _BARU
    assert final.read_text() == "BARU"


def test_safe_write_replace_explicit(tmp_path: Path):
    out = tmp_path / "out.txt"
    out.write_text("LAMA")

    def w(p: Path):
        p.write_text("BARU")

    final = safe_write(out, w, replace=True)
    assert final == out and final.read_text() == "BARU"


def test_safe_write_writer_error_leaves_original(tmp_path: Path):
    out = tmp_path / "out.txt"
    out.write_text("ORIGINAL")

    def w(p: Path):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        safe_write(out, w)
    assert out.read_text() == "ORIGINAL"           # tak tersentuh
    assert not list(tmp_path.glob("*.tmp"))        # gak ada tmp nyasar
