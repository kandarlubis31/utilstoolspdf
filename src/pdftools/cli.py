"""pdftools CLI — argparse dispatch semua subcommand."""

from __future__ import annotations

import argparse
import sys

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdftools",
        description="Toolkit PDF offline (Windows-first). Original selalu aman, verifikasi built-in.",
    )
    p.add_argument("--version", action="version", version=f"pdftools {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    # info
    sp = sub.add_parser("info", help="inspeksi PDF: halaman, gambar, signature, metadata")
    sp.add_argument("file", help="file PDF")
    sp.set_defaults(func="pdftools.cmds.info:cmd_info")

    # scan
    sp = sub.add_parser("scan", help="cari keyword di banyak PDF (audit dokumen)")
    sp.add_argument("folder", help="folder berisi PDF")
    sp.add_argument("--keywords", required=True, help="keyword dipisah koma, contoh: \"IPK,3,88\"")
    sp.add_argument("--recursive", "-r", action="store_true", help="telusuri subfolder")
    sp.set_defaults(func="pdftools.cmds.scan:cmd_scan")

    # merge
    sp = sub.add_parser("merge", help="gabung PDF + metadata")
    sp.add_argument("inputs", nargs="+", help="PDF input (2+)")
    sp.add_argument("-o", "--output", required=True, help="file output")
    sp.add_argument("--title", help="metadata Title")
    sp.add_argument("--author", help="metadata Author")
    sp.add_argument("--replace", action="store_true",
                    help="timpa file output eksplisit (tetap via tmp+swap)")
    sp.set_defaults(func="pdftools.cmds.merge:cmd_merge")

    # img2pdf
    sp = sub.add_parser("img2pdf", help="gambar -> PDF (pas foto ukuran fisik / fit A4)")
    sp.add_argument("input", help="file gambar (png/jpg/jpeg)")
    sp.add_argument("-o", "--output", required=True, help="file PDF output")
    sp.add_argument("--size", help='ukuran fisik page, contoh: "3x4cm", "300x400mm", "2x2in"')
    sp.add_argument("--a4", action="store_true", help="fit ke halaman A4 (untuk scan KK/KTP)")
    sp.add_argument("--quality", type=int, default=92, help="kualitas JPEG (default 92)")
    sp.set_defaults(func="pdftools.cmds.img2pdf:cmd_img2pdf")

    # html2pdf
    sp = sub.add_parser("html2pdf", help="HTML print-ready -> PDF via headless Chrome/Edge")
    sp.add_argument("input", help="file HTML")
    sp.add_argument("-o", "--output", required=True, help="file PDF output")
    sp.add_argument("--check-pages", action="store_true",
                    help="WARNING + hint CSS kalau hasil > 1 halaman")
    sp.add_argument("--browser", help="path chrome.exe/msedge eksplisit")
    sp.add_argument("--margin", choices=["none"], default=None,
                    help="margin none (browser udah di-set no-header-footer)")
    sp.set_defaults(func="pdftools.cmds.html2pdf:cmd_html2pdf")

    # photo
    sp = sub.add_parser("photo", help="insert foto ke kotak placeholder PDF (kasus SKL)")
    photo_sub = sp.add_subparsers(dest="photo_command", required=True)

    d = photo_sub.add_parser("detect", help="daftar kandidat kotak foto (rasio 3:4 polos)")
    d.add_argument("file", help="file PDF")
    d.set_defaults(func="pdftools.cmds.photo:cmd_detect")

    ins = photo_sub.add_parser("insert", help="insert foto ke placeholder terpilih")
    ins.add_argument("file", help="file PDF")
    ins.add_argument("photo", help="file foto")
    ins.add_argument("-o", "--output", required=True, help="file output (original aman)")
    ins.add_argument("--xref", type=int, help="xref gambar target (dari photo detect)")
    ins.add_argument("--auto", action="store_true", help="pilih kandidat terbaik otomatis")
    ins.add_argument("--force", action="store_true", help="lanjut walau ada signature digital")
    ins.set_defaults(func="pdftools.cmds.photo:cmd_insert")

    # split
    sp = sub.add_parser("split", help="pisah halaman, contoh: --pages 1,3-4")
    sp.add_argument("file", help="file PDF")
    sp.add_argument("--pages", required=True, help='spesifikasi halaman, contoh: "1,3-4"')
    sp.add_argument("-o", "--output", required=True, help="file output")
    sp.set_defaults(func="pdftools.cmds.split:cmd_split")

    # compress
    sp = sub.add_parser("compress", help="kecilkan ukuran PDF (form online limit upload)")
    sp.add_argument("file", help="file PDF")
    sp.add_argument("-o", "--output", required=True, help="file output")
    sp.add_argument("--max-mb", type=float, default=5.0, help="target maksimum MB (default 5)")
    sp.set_defaults(func="pdftools.cmds.compress:cmd_compress")

    return p


def main(argv: list[str] | None = None) -> int:
    # Windows console sering bukan UTF-8 — paksa UTF-8 biar output gak crash
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        func = args.func
    except AttributeError:  # gak mungkin kalau required=True, jaga-jaga
        parser.print_help()
        return 1

    try:
        module_path, func_name = args.func.split(":")
        import importlib

        mod = importlib.import_module(module_path)
        getattr(mod, func_name)(args)
        return 0
    except KeyboardInterrupt:
        print("\nDibatalkan.")
        return 130
    except SystemExit as exc:
        # SystemExit dari dalam command (pesan error yang jelas) / argparse
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        if code:
            print(code, file=sys.stderr)
            return 1
        return 0
    except Exception as exc:  # noqa: BLE001 — CLI: pesan ramah, bukan traceback
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
