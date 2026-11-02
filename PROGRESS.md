# PROGRESS.md — Tracker Project utilstoolsPDF

> Update file ini di AKHIR tiap sesi kerja (format log di bawah).
> AI: jangan mulai kerja sebelum baca AGENTS.md + bagian "Status" di sini.

## Status: F1–F4 SELESAI ✅ (v0.1.0 — semua 8 command jalan, 22/22 test pass)

| Fase | Isi | Status |
|---|---|---|
| F1 — core | `info`, `scan`, `merge`, `img2pdf` | ✅ Selesai (sesi 1) |
| F2 — html2pdf | headless Chrome/Edge + safe-swap + check-pages | ✅ Selesai (sesi 1) |
| F3 — photo | detect + insert + verifikasi piksel | ✅ Selesai (sesi 1) |
| F4 — bonus | `split`, `compress` | ✅ Selesai (sesi 1) |
| F5? | OCR (`pytesseract`), GUI/web | ⬜ Belum dimulai (out of scope dulu) |

## Detail per command

| Command | Fungsi | Catatan implementasi |
|---|---|---|
| `info` | inspeksi PDF | dimensi pt+mm, gambar+posisi, sig digital, metadata, pratinjau teks |
| `scan` | cari keyword di folder PDF | separator `;` (koma = desimal), `-r` recursive |
| `merge` | gabung PDF + metadata | verifikasi page count, warning >5 MB |
| `img2pdf` | gambar → PDF | `--size 3x4cm` presisi (verifikasi ±0.5mm), `--a4`, PNG→JPEG asli |
| `html2pdf` | HTML → PDF headless | render via %TEMP%, `--check-pages` exit 2, Chrome/Edge auto-detect |
| `photo` | insert foto ke placeholder SKL | detect (rasio 3:4 + polos), insert `Page.replace_image`, verifikasi piksel, tolak PDF bersignature |
| `split` | pisah halaman | `--pages 1,3-4`, verifikasi isi teks |
| `compress` | kecilkan PDF | deflate+garbage+objstms, laporan % |

## Known issues / backlog

- [ ] `compress` masih level 1 (garbage collection) — belum downsample gambar; PDF image-heavy belum banyak menyusut
- [ ] `photo insert` belum handle "kotak foto" yang digambar vektor (bukan image xref)
- [ ] `html2pdf` belum support `--margin` selain `none` (arg ada, belum dipakai)
- [ ] Alias `utpdf` (PLAN.md §2) belum dibuat — butuh installer/launcher `.bat`
- [ ] Belum ada git repo / commit pertama

## Log sesi

### Sesi 1 — 2026-09-10: Eksekusi PLAN.md full F1–F4

- Scaffold: `pyproject.toml` (entry point `pdftools`), requirements, .gitignore, package `src/pdftools`
- Implement 8 command + `utils.py` (safe_write tmp+swap, find_browser, parse_pages)
- 22 test end-to-end via CLI (merge, img2pdf, scan, info, split, photo, utils) — **22/22 pass**
- Smoke test semua command dengan file asli (Chrome headless include)
- Bug yang ditemukan & diperbaiki (detail teknis: lihat AGENTS.md "Pitfall"):
  1. Faktor cm salah di `parse_size` (3x4cm kebaca 3mm)
  2. Separator keyword scan `,` ngerusak desimal "3,88" → `;`
  3. `replace_image` = method Page, bukan Document
  4. Verifikasi split pake `page.number` (selalu renumber) → cek isi teks
  5. Path browser `Program Files (x86)` ke-prefix dobel
  6. Chrome keblok nulis ke folder terlindung → render via %TEMP%
  7. Simbol unicode crash di console cp1252 → ASCII-safe
- Konteks buat AI: bikin `AGENTS.md` + `PROGRESS.md` ini

### Format log (copy template ini tiap sesi)

```
### Sesi N — YYYY-MM-DD: <judul singkat>

- <apa yang dikerjakan>
- <bug/d Insight penting>
- <status akhir: test X/X pass, command terdampak>

```
