"""pdftools merge — gabung PDF + metadata. Original TIDAK pernah ditimpa."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfWriter

from ..utils import fmt_size, safe_write


def cmd_merge(args: argparse.Namespace) -> None:
    inputs = [Path(p) for p in args.inputs]
    for p in inputs:
        if not p.is_file():
            raise SystemExit(f"ERROR: input gak ada: {p}")

    writer = PdfWriter()
    for p in inputs:
        writer.append(str(p))
        print(f"  + {p.name}")

    if args.title:
        writer.add_metadata({"/Title": args.title})
    if args.author:
        writer.add_metadata({"/Author": args.author})

    out = Path(args.output)

    def _write(tmp: Path) -> None:
        with open(tmp, "wb") as fh:
            writer.write(fh)

    final = safe_write(out, _write)

    # --- verifikasi (hard rule #2) ---
    from pypdf import PdfReader

    expected = sum(len(PdfReader(str(p)).pages) for p in inputs)
    got = len(PdfReader(str(final)).pages)
    mark = "OK" if got == expected else "BEDA!"
    print(f"  [verifikasi] halaman output = {got} (target {expected}) -> {mark}")
    if got != expected:
        raise SystemExit("Jumlah halaman hasil merge beda dari total input — jangan dipakai!")

    size = final.stat().st_size
    print(f"  Ukuran hasil: {fmt_size(size)}")
    if size > 5 * 1024 * 1024:
        print("  [!] > 5 MB - banyak form online mentok di limit ini. Coba: pdftools compress")
    print(f"Selesai: {final}")
