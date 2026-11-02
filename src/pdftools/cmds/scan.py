"""pdftools scan — cari keyword di banyak PDF sekaligus (audit dokumen).

Use case nyata: cari di PDF mana "3,88" vs "3,86" muncul.

Separator keyword pakai ';' — koma tetep buat angka desimal Indonesia ("3,88").
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..utils import open_pdf_or_die


def iter_pdfs(folder: Path, recursive: bool):
    pattern = "**/*.pdf" if recursive else "*.pdf"
    yield from sorted(folder.glob(pattern))


def cmd_scan(args: argparse.Namespace) -> None:
    folder = Path(args.folder)
    if not folder.is_dir():
        raise SystemExit(f"ERROR: folder gak ada: {folder}")

    keywords = [k.strip() for k in args.keywords.split(";") if k.strip()]
    if not keywords:
        raise SystemExit('ERROR: --keywords kosong. Contoh: --keywords "IPK;3,88"')

    pdfs = list(iter_pdfs(folder, args.recursive))
    if not pdfs:
        print("Gak ada PDF di folder itu.")
        return

    print(f"Scan {len(pdfs)} PDF | keywords: {', '.join(keywords)}\n")

    total_hits = 0
    for pdf in pdfs:
        doc = open_pdf_or_die(pdf)
        hits: list[tuple[int, str]] = []
        for pno, page in enumerate(doc, start=1):
            for line in page.get_text().splitlines():
                for kw in keywords:
                    if kw.lower() in line.lower():
                        snippet = line.strip()[:80]
                        hits.append((pno, snippet))
                        break  # 1 baris cukup 1x per halaman
        doc.close()

        if hits:
            print(f"{pdf.name}  ({len(hits)} match)")
            for pno, snippet in hits[:20]:
                print(f"   p.{pno}: {snippet}")
            if len(hits) > 20:
                print(f"   ... dan {len(hits) - 20} lagi")
            print()
            total_hits += len(hits)
        else:
            print(f"{pdf.name}  (gak ada match)\n")

    print(f"Selesai. Total {total_hits} baris match di {len(pdfs)} PDF.")
