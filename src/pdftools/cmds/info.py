"""pdftools info — inspeksi PDF: halaman, ukuran, gambar, signature, metadata."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..utils import fmt_size, open_pdf_or_die, pt2mm


def cmd_info(args: argparse.Namespace) -> None:
    path = Path(args.file)
    doc = open_pdf_or_die(path)

    size = path.stat().st_size
    print(f"File      : {path.name}")
    print(f"Ukuran    : {fmt_size(size)} ({size:,} bytes)")
    print(f"Halaman   : {doc.page_count}")
    print(f"Producer  : {doc.metadata.get('producer') or '-'}")
    print(f"Title     : {doc.metadata.get('title') or '-'}")
    print(f"Author    : {doc.metadata.get('author') or '-'}")

    total_images = 0
    for i, page in enumerate(doc, start=1):
        w_pt, h_pt = page.rect.width, page.rect.height
        print(f"\n-- Halaman {i}: {w_pt:.1f} x {h_pt:.1f} pt "
              f"({pt2mm(w_pt):.1f} x {pt2mm(h_pt):.1f} mm)")

        images = page.get_images(full=True)
        total_images += len(images)
        for img in images:
            xref = img[0]
            rects = page.get_image_rects(xref)
            pos = ", ".join(f"({r.x0:.0f},{r.y0:.0f}) {r.width:.0f}x{r.height:.0f}" for r in rects) or "?"
            print(f"   gambar xref={xref}: di {pos}")

    has_sig = bool(doc.sig_flags) if hasattr(doc, "sig_flags") else False
    if not has_sig:
        try:
            has_sig = any(len(list(page.widgets())) > 0 for page in doc)
        except Exception:
            has_sig = False
    print(f"\nGambar    : {total_images} buah")
    print(f"Signature : {'ADA (digital)' if has_sig else 'tidak ada (digital)'}")

    # pratinjau teks halaman 1
    text = doc[0].get_text().strip()
    preview = text[:200].replace("\n", " | ")
    print(f"Teks p.1  : {preview + '...' if len(text) > 200 else preview or '(kosong / hasil scan)'}")
    doc.close()
