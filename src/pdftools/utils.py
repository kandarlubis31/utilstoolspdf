"""Helper bersama: safe_write (tmp+swap), find_browser, parse_pages, fmt_size.

Hard rules (PLAN.md §4):
- Original TIDAK pernah ditimpa tanpa jalur tmp+swap yang aman.
- Pesan error harus bisa ditindaklanjuti.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
MM_PER_PT = 25.4 / 72.0  # 1 pt = 0.3528 mm


class FileLockError(RuntimeError):
    """Dilempar saat target file dilock proses lain (mis. viewer PDF kebuka)."""


def fmt_size(num_bytes: int | float) -> str:
    """Ukuran file enak dibaca: 512 B, 1.2 MB, dst."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def pt2mm(pt: float) -> float:
    return pt * MM_PER_PT


def check_open_pdf(path: Path) -> None:
    """Windows: cek dulu file bisa dibuka mode append — kalau dilock viewer,
    gagal SEKARANG dengan pesan jelas, bukan setelah file rusak."""
    if not path.exists():
        return
    if os.name != "nt":  # POSIX: gak ada file-lock mengunci write eksklusif
        return
    try:
        with open(path, "ab"):
            pass
    except PermissionError as exc:
        raise FileLockError(
            f"'{path.name}' lagi dibuka di viewer PDF.\n"
            f"  -> Tutup viewer-nya dulu, lalu ulangi perintah."
        ) from exc


def safe_write(target: Path, writer, *, replace: bool = False) -> Path:
    """Tulis hasil operasi tanpa pernah ngerusak original.

    - `writer(tmp_path)` dipanggil dengan Path tujuan sementara (*.tmp.pdf).
    - Default: kalau `target` sudah ada, output pindah ke `<stem>_BARU.pdf`.
    - `replace=True`: atomic os.replace dari tmp ke target (butuh `--replace`).
    - File dilock viewer? Data aman di tmp, diangkat FileLockError dengan pesan.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    final = target
    if not replace and target.exists():
        final = target.with_name(f"{target.stem}_BARU{target.suffix}")

    tmp = target.with_name(f"{target.stem}.tmp{target.suffix}")
    writer(tmp)  # kalau gagal di sini, original tidak tersentuh sama sekali

    try:
        os.replace(tmp, final)
    except PermissionError as exc:
        keep = target.with_name(f"{target.stem}_BARU{target.suffix}")
        shutil.move(str(tmp), str(keep))
        raise FileLockError(
            f"Target '{final.name}' dilock (viewer kebuka?).\n"
            f"  -> Hasil aman disimpan sebagai '{keep.name}'.\n"
            f"  -> Tutup viewer dulu kalau mau timpa '{final.name}'."
        ) from exc

    if not replace and final != target and target.exists():
        print(f"  [safe] original tidak disentuh; hasil = '{final.name}'")
    return final


# ---------------------------------------------------------------------------
# Browser discovery (html2pdf)
# ---------------------------------------------------------------------------
_BROWSER_RELATIVE = [
    r"Google\Chrome\Application\chrome.exe",
    r"Microsoft\Edge\Application\msedge.exe",
]


def _browser_candidates() -> list[str]:
    """Full path kandidat: PF & PF(x86) x Chrome & Edge + fallback POSIX."""
    pf1 = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf2 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    win = [str(Path(pf) / rel) for pf in (pf1, pf2) for rel in _BROWSER_RELATIVE]
    posix = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/microsoft-edge",
    ]
    return win + posix


def find_browser(explicit: str | None = None) -> str:
    """Cari Chrome/Edge: path eksplisit -> PATH -> lokasi standar Windows."""
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return str(p)
        raise FileNotFoundError(f"Browser tidak ketemu di: {explicit}")

    exe = "chrome.exe" if os.name == "nt" else "google-chrome"
    found = shutil.which(exe) or shutil.which("chromium") or shutil.which("msedge")
    if found:
        return found

    for cand in _browser_candidates():
        p = Path(cand)
        if p.is_file():
            return str(p)

    raise FileNotFoundError(
        "Chrome/Edge gak ketemu.\n"
        "  -> Pasang Chrome, atau kasih path manual: --browser \"C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe\""
    )


# ---------------------------------------------------------------------------
# Page-range parser: "1,3-4" -> [1, 3, 4] (1-based, diurutkan unik)
# ---------------------------------------------------------------------------
def parse_pages(spec: str, max_page: int) -> list[int]:
    """Parse spesifikasi halaman `1,3-4` jadi list int 1-based."""
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo_s, hi_s = part.split("-", 1)
            try:
                lo, hi = int(lo_s), int(hi_s)
            except ValueError:
                raise ValueError(f"Rentang halaman salah: '{part}'")
            if lo < 1 or hi < lo or hi > max_page:
                raise ValueError(f"Rentang '{part}' di luar 1..{max_page}")
            pages.update(range(lo, hi + 1))
        else:
            try:
                n = int(part)
            except ValueError:
                raise ValueError(f"Nomor halaman salah: '{part}'")
            if n < 1 or n > max_page:
                raise ValueError(f"Halaman {n} di luar 1..{max_page}")
            pages.add(n)
    if not pages:
        raise ValueError("Spesifikasi halaman kosong")
    return sorted(pages)


def open_pdf_or_die(path: Path):
    """Buka PDF dengan pymupdf; error-nya bikin paham, bukan bingung."""
    import pymupdf

    path = Path(path)
    if not path.is_file():
        sys.exit(f"ERROR: file gak ada: {path}")
    try:
        return pymupdf.open(path)
    except Exception as exc:  # noqa: BLE001 — tampilkan apa adanya, pesan ramah
        sys.exit(f"ERROR: gak bisa buka '{path.name}' — bukan PDF valid? ({exc})")


def verify_pages(doc, expected: int, label: str) -> None:
    """Bukti verifikasi (hard rule #2): jumlah halaman harus pas."""
    actual = doc.page_count
    mark = "OK" if actual == expected else "BEDA"
    print(f"  [verifikasi] {label}: {actual} halaman (target {expected}) -> {mark}")
    if actual != expected:
        raise RuntimeError(f"Jumlah halaman {label} = {actual}, harusnya {expected}")


def make_profile_dir(prefix: str = "pdftools_") -> str:
    """User-data-dir sementara biar gak konflik sama Chrome yang lagi jalan."""
    return tempfile.mkdtemp(prefix=prefix)


def headless_print(browser: str, html_url: str, out_pdf: str, profile_dir: str) -> None:
    """Panggil browser headless mode print-to-PDF (devtools protocol lama yang stabil)."""
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        f"--user-data-dir={profile_dir}",
        "--no-pdf-header-footer",
        "--print-to-pdf=" + out_pdf,
        html_url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not Path(out_pdf).is_file():
        raise RuntimeError(
            f"Browser gagal render (exit {proc.returncode}).\n"
            f"  stderr: {proc.stderr.strip()[:500]}"
        )
