"""pdftools html2pdf — HTML print-ready -> PDF via headless Chrome/Edge.

Fitur sesuai PLAN.md §3.5:
- auto-detect Chrome/Edge, fallback --browser path manual
- --user-data-dir sementara (hindari konflik Chrome yang lagi jalan)
- --check-pages: WARNING + hint bug CSS klasik kalau hasil > 1 halaman
- safe-swap: target dilock viewer -> simpan _BARU.pdf + pesan jelas

Catatan: render DILAKUKAN ke file di %TEMP% dulu — Chrome kadang keblok
(Controlled Folder Access / permission) nulis langsung ke folder target
mis. Desktop, sedangkan move dari temp selalu bisa.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from ..utils import find_browser, fmt_size, headless_print, make_profile_dir, safe_write


def cmd_html2pdf(args: argparse.Namespace) -> None:
    src = Path(args.input).resolve()
    if not src.is_file():
        raise SystemExit(f"ERROR: HTML gak ada: {src}")

    out = Path(args.output).resolve()
    browser = find_browser(args.browser)
    print(f"Browser   : {browser}")

    profile = make_profile_dir()
    # hasil mentahan browser di %TEMP% (anti blokir folder terlindungi)
    render_tmp = Path(tempfile.gettempdir()) / f"pdftools_render_{os.getpid()}_{out.stem}.pdf"
    try:
        headless_print(browser, src.as_uri(), str(render_tmp), profile)
    finally:
        import shutil

        shutil.rmtree(profile, ignore_errors=True)

    if not render_tmp.is_file():
        raise SystemExit("ERROR: browser gak ngasilin file PDF. Cek HTML-nya valid.")

    # --- verifikasi page count sebelum dianggap sukses ---
    import pymupdf

    probe = pymupdf.open(render_tmp)
    n_pages = probe.page_count
    probe.close()
    print(f"Render OK : {n_pages} halaman, {fmt_size(render_tmp.stat().st_size)}")

    try:
        if args.check_pages and n_pages > 1:
            print(
                f"\n  [!] WARNING: hasil {n_pages} halaman, bukan 1!\n"
                "  Hint bug CSS klasik:\n"
                "    - 'min-height: 100vh' + padding bikin overflow > A4 (297mm)\n"
                "    - margin @page / body gak 0\n"
                "    - elemen terakhir nyambah halaman baru karena tinggal 1-2px\n"
                "  Cek: @page { size: A4; margin: 0 } dan matikan min-height."
            )
            raise SystemExit(2)  # exit code khusus: render sukses tapi jumlah halaman salah

        def _write(tmp: Path) -> None:
            os.replace(render_tmp, tmp)

        final = safe_write(out, _write)
    finally:
        render_tmp.unlink(missing_ok=True)

    print(f"Selesai: {final}")
