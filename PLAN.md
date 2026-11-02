# PLAN / SPEC — utilstoolsPDF (`pdftools`)

> Toolkit PDF offline untuk Windows — dikompilasi dari workflow nyata sesi lamaran Freeport Sep 2026.
> Semua fitur di bawah = operasi yang sebelumnya dilakukan manual via script ad-hoc, sekarang jadi CLI reusable.
> Prinsip: **original selalu aman** (tidak pernah menimpa tanpa salinan), **verifikasi built-in** setelah tiap operasi, **zero GUI dependency** (jalan di terminal), **offline total**.

---

## 1. Kenapa tools ini ada

| Masalah nyata | Solusi di toolkit |
|---|---|
| Export CV HTML → PDF harus buka Chrome manual, kadang hasil 2 halaman karena bug CSS | `html2pdf` — headless Chrome/Edge + cek jumlah halaman otomatis |
| PDF lama ke-lock saat mau ditimpa (viewer kebuka) | `--safe` default: tulis ke tmp → atomic swap → pesan jelas kalau dilock |
| Convert foto → PDF pas foto ukuran fisik (3x4 cm) | `img2pdf` — opsi `--size 3x4cm` |
| Merge transkrip + SKL jadi satu file | `merge` — urutan file + metadata (Title/Author) |
| Insert foto ke kotak "Foto" kosong di SKL | `photo insert` — auto-detect placeholder rasio 3:4 |
| Cek isi PDF (jumlah halaman, IPK, tanggal, tanda tangan) | `info` + `scan` — cari keyword di banyak PDF sekaligus |

---

## 2. Nama & Lokasi

- **Folder project**: `C:\Users\KandarLubis\Desktop\Project\python\utilstoolsPDF`
- **Nama CLI**: `pdftools` (alias `utpdf`)
- **Python**: 3.13+ (sudah terpasang di mesin ini)
- **Dependensi** (semua sudah terbukti terpasang/terpakai di sesi nyata):
  - `pymupdf` — render, replace image, extract text, signature check
  - `pypdf` — merge, split, metadata, page count
  - `Pillow` — image → PDF, resize/crop
  - stdlib: `argparse`, `shutil`, `subprocess`, `pathlib` — tanpa framework CLI berat

---

## 3. Perintah (CLI spec)

```
pdftools <command> [args]
```

### 3.1 `info` — inspeksi PDF
```
pdftools info file.pdf
```
Output: jumlah halaman, ukuran file, ukuran halaman (pt & mm), daftar gambar + posisi, ada/tidak signature, metadata (Title/Author/Producer), pratinjau teks halaman 1 (200 char pertama).

### 3.2 `scan` — cari keyword di banyak PDF (audit dokumen)
```
pdftools scan <folder> --keywords "IPK,3.88,Tanggal" [--recursive]
```
Output tabel: file → halaman → baris yang match. Use case nyata: cari di PDF mana angka IPK 3,88 vs 3,86 muncul (persis kasus KHS D3 vs KHS sem 6).

### 3.3 `merge` — gabung PDF + metadata
```
pdftools merge a.pdf b.pdf [c.pdf ...] -o hasil.pdf [--title "..." --author "..."]
```
Aturan: original TIDAK pernah ditimpa (output baru atau `--replace` eksplisit). Verifikasi: jumlah halaman output = total input, ukuran < 5 MB warning untuk form online.

### 3.4 `img2pdf` — gambar jadi PDF
```
pdftools img2pdf foto.png -o out.pdf [--size 3x4cm | --a4] [--quality 92]
```
- `--size 3x4cm`: page = ukuran fisik persis (full-bleed) → pas foto untuk form
- `--a4`: fit ke halaman A4 (untuk scan KK/KTP/surat)
- Auto-convert PNG→JPEG beneran (bukan PNG nyamar .jpg), kualitas default 92
- Verifikasi: cek dimensi halaman hasil (mm) tercetak ke terminal

### 3.5 `html2pdf` — HTML print-ready → PDF
```
pdftools html2pdf input.html -o out.pdf [--check-pages] [--margin none]
```
- Cari Chrome/Edge otomatis (`Program Files` x2 path), fallback `--browser` path manual
- `--user-data-dir` profil sementara (hindari konflik Chrome yang sedang jalan)
- Render → cek `/Count` di PDF hasil → kalau > 1 halaman padahal `--check-pages`, cetak WARNING + hint bug CSS klasik (`min-height` + padding > A4)
- `--safe`: tulis ke `*.tmp.pdf` → coba atomic swap → kalau target dilock viewer: simpan sebagai `_BARU.pdf` + pesan "tutup viewer dulu" (persis kasus SKL kemarin)

### 3.6 `photo` — insert foto ke kotak placeholder PDF
```
pdftools photo insert skl.pdf foto.jpg -o out.pdf [--xref 13] [--auto]
pdftools photo detect skl.pdf          # daftar kandidat kotak foto
```
- `detect`: daftar semua gambar + rect; tandai kandidat placeholder (rasio 3:4 ± toleransi, dominan satu warna)
- `insert --auto`: pilih kandidat terbaik → `page.replace_image()` → `saveIncr()`
- Verifikasi otomatis: keragaman piksel di area foto (placeholder = monoton; foto = tinggi), signature check before/after (kalau PDF punya signature digital → tolak + sarankan jalan lain)
- `--keep-original` default ON: output file baru, asli tidak disentuh

### 3.7 `split` — pisah halaman (bonus, fase 4)
```
pdftools split file.pdf --pages 1,3-4 -o bagian.pdf
```

### 3.8 `compress` — kecilkan ukuran (bonus, fase 4)
```
pdftools compress file.pdf -o kecil.pdf [--max-mb 5]
```
Target: dokumen form online yang mentok limit upload. Garansi: verifikasi ukuran akhir + kualitas minimal.

---

## 4. Aturan desain (hard rules)

1. **Jangan pernah merusak original** — semua operasi menulis ke file baru; `--replace` harus eksplisit dan tetap via tmp+swap.
2. **Verifikasi setelah aksi** — tiap command cetak bukti hasil (page count, dimensi, keragaman piksel, ukuran KB). Bukan cuma "sukses" kosong.
3. **Pesan error yang bisa ditindaklanjuti** — "file dilock: tutup viewer PDF lalu ulangi", "rasio bukan 3:4: yakin lanjut? (--force)".
4. **Windows-first** — path & file-lock Windows ditangani bener; jalan juga di POSIX karena stdlib.
5. **Tanpa GUI, tanpa server** — murni CLI, cepat, bisa masuk script batch/otomasi lain.
6. **Bahasa output**: Indonesia santai (konsisten gaya user).

---

## 5. Struktur repo

```
utilstoolsPDF/
├── PLAN.md                # dokumen ini
├── README.md              # cara pakai + contoh nyata
├── pyproject.toml         # metadata + entry point pdftools=src.pdftools.cli:main
├── requirements.txt       # pymupdf, pypdf, Pillow
├── src/pdftools/
│   ├── __init__.py        # versi
│   ├── cli.py             # argparse dispatch semua subcommand
│   ├── utils.py           # safe_write(tmp+swap), find_browser(), page_count(), fmt_size()
│   └── cmds/
│       ├── info.py
│       ├── scan.py
│       ├── merge.py
│       ├── img2pdf.py
│       ├── html2pdf.py
│       ├── photo.py
│       ├── split.py
│       └── compress.py
└── tests/
    ├── test_merge.py
    ├── test_img2pdf.py
    └── fixtures/          # PDF & gambar kecil untuk test
```

---

## 6. Roadmap implementasi

| Fase | Isi | Estimasi | Kriteria selesai |
|---|---|---|---|
| **F1 — core** | `info`, `scan`, `merge`, `img2pdf` | 1 sesi | 4 command jalan + verifikasi output + test merge & img2pdf |
| **F2 — html2pdf** | wrapper headless + safe-swap + check-pages | 1 sesi | export CV real → 1 halaman terverifikasi; test kasus lock |
| **F3 — photo** | detect + insert + verifikasi pixel | 1 sesi | insert foto ke SKL asli → hasil identik kasus nyata |
| **F4 — bonus** | `split`, `compress` | sisa waktu | — |

Catatan F2: kebutuhan Chrome terpasang (sudah ada di mesin); kalau tidak ketemu → fallback Edge (Windows selalu punya).

---

## 7. Contoh pemakaian nyata (dari kasus sesi ini)

```bash
# 1. Export CV print-ready + pastiin 1 halaman
pdftools html2pdf CV_Aulia_FGP.html -o CV_Aulia_FGP.pdf --check-pages

# 2. Pas foto 3x4 cm untuk form
pdftools img2pdf FotoBaru.png -o Pas_Foto_3x4.pdf --size 3x4cm

# 3. Scan KK & KTP foto jadi PDF A4
pdftools img2pdf kkterbaru.jpeg -o KK.pdf --a4

# 4. Gabung transkrip + SKL
pdftools merge transkrip.pdf SKL.pdf -o Transkrip_dan_SKL.pdf --title "Transkrip + SKL" --author "Aulia Iskandar Lubis"

# 5. Insert foto ke kotak kosong SKL
pdftools photo detect SKL.pdf
pdftools photo insert SKL.pdf FotoBerwarna.jpg -o SKL_foto.pdf

# 6. Audit: di PDF mana IPK 3,88 muncul?
pdftools scan . --keywords "IPK,3,88" --recursive
```

---

## 8. Out of scope (saat ini)

- GUI/web interface (mungkin F5 kalau terasa perlu)
- OCR (baca PDF hasil scan tanpa text layer) — nanti bisa tambah via `pytesseract` di fase terpisah
- Konversi PDF → Word/Excel
