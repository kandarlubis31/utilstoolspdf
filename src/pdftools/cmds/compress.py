"""pdftools compress — kecilkan PDF untuk form online yang mentok limit upload."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..utils import fmt_size, open_pdf_or_die, safe_write


def cmd_compress(args: argparse.Namespace) -> None:
    src = Path(args.file)
    doc = open_pdf_or_die(src)
    before = src.stat().st_size

    out = Path(args.output)

    def _write(tmp: Path) -> None:
        doc.save(str(tmp), deflate=True, garbage=4, use_objstms=1)
        if before > 1.5 * 1024 * 1024:  # coba turunkan resolusi gambar kalau file gede
            import pymupdf

            for page in doc:
                # clean contents buang resource tak terpakai; shrink image via pixmap re-insert diabaikan (F4 sederhana)
                page.clean_contents()

    final = safe_write(out, _write)
    doc.close()

    after = final.stat().st_size
    pct = (1 - after / before) * 100 if before else 0
    print(f"  [verifikasi] {fmt_size(before)} -> {fmt_size(after)} (-{pct:.0f}%)")

    max_bytes = args.max_mb * 1024 * 1024
    if after > max_bytes:
        print(f"  [!] Masih > {args.max_mb} MB. Saran: compress lebih agresif belum didukung F4; "
              "coba scan ulang dokumen dengan DPI lebih rendah.")
    print(f"Selesai: {final}")
