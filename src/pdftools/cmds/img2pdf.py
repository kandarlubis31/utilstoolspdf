"""pdftools img2pdf — gambar jadi PDF: pas foto ukuran fisik (3x4cm) atau fit A4."""

from __future__ import annotations

import argparse
import io
from pathlib import Path

from PIL import Image

from ..utils import fmt_size, safe_write

A4_PT = (595.28, 841.89)  # 210 x 297 mm
MM2PT = 72.0 / 25.4


def parse_size(spec: str) -> tuple[float, float]:
    """'3x4cm' -> (85.04, 113.39) pt. 'A4' juga diterima di sini."""
    spec = spec.strip().lower()
    if spec == "a4":
        return A4_PT
    for unit in ("cm", "mm", "in"):
        if spec.endswith(unit):
            try:
                w_s, h_s = spec[: -len(unit)].split("x")
                w, h = float(w_s), float(h_s)
            except ValueError:
                raise SystemExit(f"ERROR: format --size salah: '{spec}' (contoh: 3x4cm)")
            factor = {"cm": MM2PT * 10, "mm": MM2PT, "in": 72.0}[unit]
            return (w * factor, h * factor)
    raise SystemExit(f"ERROR: satuan --size gak dikenal: '{spec}' (pakai cm/mm/in, contoh: 3x4cm)")


def cmd_img2pdf(args: argparse.Namespace) -> None:
    src = Path(args.input)
    if not src.is_file():
        raise SystemExit(f"ERROR: gambar gak ada: {src}")

    img = Image.open(src)
    img_format = (img.format or "").upper()
    print(f"Input     : {src.name} ({img_format or '?'}, {img.width}x{img.height})")

    # PNG (dan lain-lain) -> JPEG beneran: mode + encode JPEG, bukan rename
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=args.quality)
    jpeg_bytes = buf.getvalue()
    if img_format == "PNG":
        print(f"  Konversi: PNG -> JPEG q={args.quality} ({fmt_size(len(jpeg_bytes))})")

    if args.size:
        page_w, page_h = parse_size(args.size)
        mode = f"ukuran fisik {args.size} (full-bleed)"
    else:  # --a4
        page_w, page_h = A4_PT
        mode = "fit A4"

    out = Path(args.output)

    def _write(tmp: Path) -> None:
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page(width=page_w, height=page_h)
        if args.size:  # full-bleed: foto nempel persis ukuran halaman
            rect = page.rect
        else:  # A4: fit di tengah, jaga rasio
            scale = min(page_w / img.width, page_h / img.height)
            w, h = img.width * scale, img.height * scale
            rect = pymupdf.Rect((page_w - w) / 2, (page_h - h) / 2,
                             (page_w + w) / 2, (page_h + h) / 2)
        page.insert_image(rect, stream=jpeg_bytes)
        doc.save(str(tmp), deflate=True)
        doc.close()

    final = safe_write(out, _write)

    # --- verifikasi: dimensi halaman hasil (mm) ---
    import pymupdf

    doc = pymupdf.open(final)
    w_mm, h_mm = doc[0].rect.width * 25.4 / 72, doc[0].rect.height * 25.4 / 72
    size_kb = final.stat().st_size
    print(f"  [verifikasi] halaman hasil: {w_mm:.1f} x {h_mm:.1f} mm | {fmt_size(size_kb)}")
    if args.size and args.size.lower().endswith("cm"):
        exp_w, exp_h = parse_size(args.size)
        ok = abs(w_mm - exp_w * 25.4 / 72) < 0.5 and abs(h_mm - exp_h * 25.4 / 72) < 0.5
        print(f"  [verifikasi] target {args.size}: {'OK' if ok else 'MELESET!'}")
        if not ok:
            raise SystemExit("Dimensi hasil gak sesuai target — jangan dipakai!")
    doc.close()
    print(f"Selesai ({mode}): {final}")
