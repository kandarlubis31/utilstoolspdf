# pdftools (`utilstoolsPDF`)

Toolkit PDF offline untuk Windows — murni CLI, tanpa GUI, tanpa internet.

Prinsip:
- **Original selalu aman** — semua operasi nulis ke file baru; `--replace` eksplisit tetap lewat tmp+swap.
- **Verifikasi built-in** — tiap command cetak bukti hasil (page count, dimensi mm, ukuran KB).
- **Windows-first** — file-lock viewer ditangani: kalau PDF kebuka di viewer, hasil diselamatkan ke `*_BARU.pdf`.
- **Pesan error bisa ditindaklanjuti.**

## Install

```bash
python -m venv .venv
.venv/Scripts/pip install -e .
# entry point: .venv/Scripts/pdftools.exe
```

Butuh Python 3.13+, dependensi: `pymupdf`, `pypdf`, `Pillow` (otomatis kepasang).
`html2pdf` butuh Chrome atau Edge (Edge selalu ada di Windows).

## Command

```
pdftools <command> [args] [--help]
```

### info — inspeksi PDF

```bash
pdftools info file.pdf
```

Jumlah halaman, ukuran file, dimensi halaman (pt & mm), daftar gambar + posisi,
signature digital, metadata, pratinjau teks halaman 1.

### scan — cari keyword di banyak PDF

```bash
pdftools scan . --keywords "IPK;3,88" --recursive
```

Separator keyword pakai `;` — **bukan koma**, karena koma dipake angka desimal
Indonesia ("3,88"). Output: file -> halaman -> baris yang match.

### merge — gabung PDF + metadata

```bash
pdftools merge transkrip.pdf SKL.pdf -o Transkrip_dan_SKL.pdf --title "Transkrip + SKL" --author "Nama Gw"
```

Verifikasi otomatis: jumlah halaman output = total input. Warning kalau > 5 MB
(limit upload form online).

### img2pdf — gambar jadi PDF

```bash
# pas foto ukuran fisik persis (full-bleed)
pdftools img2pdf FotoBaru.png -o Pas_Foto_3x4.pdf --size 3x4cm

# scan KK/KTP/surat fit ke A4
pdftools img2pdf kkterbaru.jpeg -o KK.pdf --a4
```

PNG dikonversi JPEG beneran (bukan rename), default quality 92 (`--quality`).
Dimensi halaman hasil (mm) tercetak sebagai verifikasi.

### html2pdf — HTML print-ready jadi PDF

```bash
pdftools html2pdf CV.html -o CV.pdf --check-pages
```

- Chrome/Edge dicari otomatis; path manual: `--browser "C:\...\chrome.exe"`
- `--check-pages`: kalau hasil > 1 halaman -> WARNING + hint bug CSS klasik, exit code 2
- Render lewat %TEMP% dulu (anti blokir folder terlindungi), lalu safe-swap ke target
- Target dilock viewer? Hasil diselamatkan ke `*_BARU.pdf` + pesan jelas

### photo — insert foto ke kotak placeholder PDF

```bash
# lihat kandidat kotak foto (rasio 3:4 + dominan satu warna)
pdftools photo detect SKL.pdf

# insert otomatis ke kandidat terbaik
pdftools photo insert SKL.pdf FotoBerwarna.jpg -o SKL_foto.pdf --auto

# atau pilih manual dari hasil detect
pdftools photo insert SKL.pdf FotoBerwarna.jpg -o SKL_foto.pdf --xref 13
```

- PDF dengan signature digital ditolak (paksa: `--force`)
- Verifikasi keragaman piksel area sebelum/sesudah
- Original tidak pernah disentuh

### split — pisah halaman

```bash
pdftools split file.pdf --pages 1,3-4 -o bagian.pdf
```

### compress — kecilkan ukuran

```bash
pdftools compress file.pdf -o kecil.pdf --max-mb 5
```

Verifikasi ukuran sebelum/sesudah tercetak.

## Tests

```bash
.venv/Scripts/python -m pytest tests -q
```

## Struktur

```
src/pdftools/
  cli.py        # argparse dispatch semua subcommand
  utils.py      # safe_write (tmp+swap), find_browser, parse_pages, verifikasi
  cmds/         # info, scan, merge, img2pdf, html2pdf, photo, split, compress
tests/          # 22 test + fixtures pembuat PDF mini
```
