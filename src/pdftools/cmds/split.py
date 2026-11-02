"""pdftools split — pisah halaman: --pages 1,3-4."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..utils import fmt_size, open_pdf_or_die, parse_pages, safe_write


def cmd_split(args: argparse.Namespace) -> None:
    src = Path(args.file)
    doc = open_pdf_or_die(src)
    pages = parse_pages(args.pages, doc.page_count)
    expected_first_text = doc[pages[0] - 1].get_text()  # buat verifikasi isi

    out = Path(args.output)

    def _write(tmp: Path) -> None:
        doc.select([p - 1 for p in pages])  # 0-based
        doc.save(str(tmp), deflate=True)

    final = safe_write(out, _write)
    doc.close()

    # verifikasi: jumlah halaman + isi halaman pertama sama persis
    import pymupdf

    new = pymupdf.open(final)
    count_ok = new.page_count == len(pages)
    first_ok = new[0].get_text() == expected_first_text
    new.close()
    print(f"  [verifikasi] halaman hasil: {len(pages)} (target {pages}) -> {'OK' if count_ok and first_ok else 'BEDA!'}")
    print(f"  Ukuran: {fmt_size(final.stat().st_size)}")
    if not (count_ok and first_ok):
        raise SystemExit("Isi hasil split beda dari permintaan — jangan dipakai!")
    print(f"Selesai: {final}")
