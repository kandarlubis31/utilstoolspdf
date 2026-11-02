# AGENTS.md — Konteks Project utilstoolsPDF (`pdftools`)

> File ini buat AI agent (Codebuff/Freebuff & lainnya): **baca ini dulu sebelum apa-apa**
> biar gak perlu scan ulang project. Kalau lo ngubah struktur/perilaku project,
> **UPDATE file ini + PROGRESS.md di sesi yang sama.**

## Snapshot

- **Apa**: Toolkit PDF offline Windows-first, murni CLI (tanpa GUI/server/internet)
- **Stack**: Python 3.13+ | deps: `pymupdf` 1.28+, `pypdf`, `Pillow` | stdlib argparse
- **Spec lengkap**: `PLAN.md` (baca kalau butuh detail use case)
- **Status tracker**: `PROGRESS.md` (selalu update setelah kerja)

## Struktur

```
src/pdftools/
  cli.py          # argparse dispatcher, lazy import per subcommand, force UTF-8 stdout
  utils.py        # safe_write(tmp+swap), find_browser, parse_pages, fmt_size, check_open_pdf
  cmds/           # info, scan, merge, img2pdf, html2pdf, photo, split, compress
tests/
  conftest.py     # fixtures: make_pdf, make_pdf_with_placeholder, make_image
  test_*.py       # 22 test, semua via CLI main() end-to-end
pyproject.toml    # entry point: pdftools = pdftools.cli:main
```

## Cara jalanin (environment ini)

```bash
.venv/Scripts/python -m pytest tests -q          # test
.venv/Scripts/pdftools.exe <command>             # CLI (venv, install editable)
```

## Hard rules (JANGAN dilanggar)

1. **Original selalu aman** — semua output lewat `safe_write()` di utils.py
   (tulis ke `*.tmp` → `os.replace`). Default TIDAK nimpa: file ada → `<stem>_BARU.pdf`.
   `--replace` eksplisit tapi tetap lewat tmp+swap. JANGAN pernah tulis langsung ke file input.
2. **Verifikasi built-in** — tiap command WAJIB cetak bukti hasil (page count,
   dimensi mm, ukuran KB, keragaman piksel). Bukan cuma "selesai".
3. **Pesan error actionable** — contoh: file dilock → "tutup viewer dulu";
   keyword kosong → kasih contoh pemakaian.
4. **Output CLI ASCII-safe** — JANGAN pakai simbol unicode (⚠ … → ±) di print:
   Windows console sering cp1252 → UnicodeEncodeError. Pakai `[!]` dan `...`.
   (cli.py sudah force UTF-8 reconfigure, tapi tetap jaga-jaga.)
5. **Bahasa output Indonesia santai.**

## Pitfall yang sudah kebukti (JANGAN diulang)

- `pymupdf` 1.28: `replace_image` itu method **Page** (`doc[pno].replace_image(xref, ...)`),
  bukan Document. `import fitz` deprecated → selalu `import pymupdf`.
- `page.number` setelah `doc.select()` selalu renumber 0..n → verifikasi split
  jangan bandingkan nomor halaman, bandingkan **isi teks**.
- Koma = separator desimal Indonesia ("3,88") → separator keyword scan = `;`.
- Chrome sering keblok nulis langsung ke folder terlindung (Controlled Folder
  Access di Desktop) → html2pdf render ke `%TEMP%` dulu, lalu move.
- Path browser: gabung `ProgramFiles(x86)` env var dengan path relatif, jangan
  prefix dobel "Program Files\Program Files (x86)".
- Konversi ukuran: 1 cm = 28.3465 pt (`MM2PT * 10`), bukan 2.83465.
- `SystemExit` dari command harus ditangkap di `cli.main()` (jangan biarkan
  traceback mentah / exit code asing bocor).

## Konvensi kode

- Type hints di signature publik; docstring singkat per module.
- Import pymupdf di dalam fungsi (lazy) kecuali perlu di top-level.
- Test end-to-end lewat `pdftools.cli.main([...])` — cek `rc == 0` + efek file.
- Nama variabel/pesan boleh campur Indonesia (konsisten gaya existing).
