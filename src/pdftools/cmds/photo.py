"""pdftools photo — deteksi & insert foto ke kotak placeholder di PDF (kasus SKL).

- detect : daftar semua gambar + rect, tandai kandidat placeholder (rasio 3:4 ±tol,
           dominan satu warna = "kotak kosong").
- insert : replace_image di kandidat terbaik, verifikasi keragaman piksel,
           signature digital = tolak + sarankan jalan lain.
Original selalu aman: output file baru (--keep-original default ON).
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

from ..utils import open_pdf_or_die, safe_write

RATIO = 3 / 4          # w/h pas foto
TOLERANCE = 0.15       # ±15%


def _ratio_ok(w: float, h: float) -> bool:
    if h <= 0:
        return False
    r = w / h
    return abs(r - RATIO) / RATIO <= TOLERANCE or abs(r - 1 / RATIO) / RATIO <= TOLERANCE


def _is_monotone(jpeg_bytes: bytes, sample: int = 24) -> bool:
    """True kalau area gambar dominan satu warna (kotak kosong / abu-abu polos)."""
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(jpeg_bytes)).convert("L").resize((sample, sample))
        pixels = set(img.tobytes())
        unique = len(pixels)
        return unique <= max(4, sample * sample // 16)  # ~5% warna unik = polos
    except Exception:
        return False


def _pixel_diversity(page, rect) -> float:
    """Keragaman piksel area (0..1): placeholder polos ~0, foto asli tinggi."""
    pix = page.get_pixmap(clip=rect, dpi=48)
    from PIL import Image

    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    img = img.resize((32, 32))
    raw = img.tobytes()
    colors = len({raw[i:i + 3] for i in range(0, len(raw), 3)})
    return min(1.0, colors / 256)


def _has_signature(doc) -> bool:
    """Deteksi signature digital di beberapa cara (nama field sig / annot / sig_flags)."""
    try:
        if doc.sig_flags:
            return True
    except Exception:
        pass
    try:
        for page in doc:
            for annot in page.annots() or []:
                if annot.type[0] == 3 or "sig" in (annot.type[1] or "").lower():
                    return True
    except Exception:
        pass
    try:
        for page in doc:
            for w in page.widgets() or []:
                if w.field_type_string.lower() in ("signature", "button") and "sig" in w.field_name.lower():
                    return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# photo detect
# ---------------------------------------------------------------------------
def cmd_detect(args: argparse.Namespace) -> None:
    doc = open_pdf_or_die(Path(args.file))
    print(f"File: {args.file} | {doc.page_count} halaman\n")

    if _has_signature(doc):
        print("  [!] PDF ini punya signature digital - jangan dimodif! Suggest: cetak ulang lewat jalur resmi.")
        return

    candidates = 0
    for pno, page in enumerate(doc, start=1):
        for img in page.get_images(full=True):
            xref = img[0]
            rects = page.get_image_rects(xref)
            raw = doc.extract_image(xref)
            mono = _is_monotone(raw["image"])
            for r in rects:
                is_cand = _ratio_ok(r.width, r.height) and mono
                flag = "  <== KANDIDAT placeholder" if is_cand else ""
                if is_cand:
                    candidates += 1
                print(f"p.{pno} xref={xref}: rect=({r.x0:.0f},{r.y0:.0f}) "
                      f"{r.width:.0f}x{r.height:.0f} pt | rasio={'3:4~' if _ratio_ok(r.width, r.height) else 'lain'} "
                      f"| {'polos' if mono else 'berisi'}{flag}")
    if not candidates:
        print("\nGak ada kandidat kotak foto (rasio 3:4 polos). Cek manual: pdftools info")
    doc.close()


# ---------------------------------------------------------------------------
# photo insert
# ---------------------------------------------------------------------------
def cmd_insert(args: argparse.Namespace) -> None:
    import pymupdf

    src = Path(args.file)
    photo = Path(args.photo)
    if not photo.is_file():
        raise SystemExit(f"ERROR: foto gak ada: {photo}")

    doc = open_pdf_or_die(src)

    if _has_signature(doc) and not args.force:
        raise SystemExit(
            "PDF punya signature digital — insert bisa merusak validity.\n"
            "  -> Yakin lanjut? tambah --force"
        )

    images = []
    for pno, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                images.append((pno, xref, r))

    if not images:
        raise SystemExit("Gak ada gambar di PDF ini. Kasus 'kotak foto' yang digambar vektor belum didukung F3.")

    # pilih target
    if args.xref is not None:
        target = next((it for it in images if it[1] == args.xref), None)
        if not target:
            raise SystemExit(f"xref {args.xref} gak ada. Cek: pdftools photo detect")
    elif args.auto:
        scored = [it for it in images if _ratio_ok(it[2].width, it[2].height) and _is_monotone(doc.extract_image(it[1])["image"])]
        if not scored:
            raise SystemExit(
                "Gak ada kandidat placeholder (rasio 3:4 + polos).\n"
                "  -> Lihat daftar gambar: pdftools photo detect, lalu pakai --xref"
            )
        target = scored[0]
    else:
        raise SystemExit("Wajib --auto ATAU --xref <n>. Lihat kandidat: pdftools photo detect")

    pno, xref, rect = target
    print(f"Target: p.{pno + 1} xref={xref} rect={rect.width:.0f}x{rect.height:.0f} pt")

    before = _pixel_diversity(doc[pno], rect)

    # foto -> JPEG pas ukuran target
    from PIL import Image

    img = Image.open(photo).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)

    # replace_image: ganti gambar di xref target (level Page di pymupdf >= 1.24)
    doc[pno].replace_image(xref, stream=buf.getvalue())

    after = _pixel_diversity(doc[pno], rect)
    print(f"  [verifikasi] keragaman piksel: sebelum={before:.2f} sesudah={after:.2f}")
    if before > 0.9:
        print("  [!] Area sebelum insert sudah ramai - mungkin salah target xref!")

    def _write(tmp: Path) -> None:
        doc.save(str(tmp), deflate=True)

    out = Path(args.output)
    final = safe_write(out, _write, replace=False)
    doc.close()

    print(f"  [safe] original '{src.name}' tidak disentuh")
    print(f"Selesai: {final}")
