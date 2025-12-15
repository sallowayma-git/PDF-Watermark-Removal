# PyInstaller spec for bundling the Flask backend into a single executable.
# Build command:
#   pyinstaller --clean --noconfirm backend/backend.spec

from pathlib import Path
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules

backend_name = "pdfwm_backend"

repo_root = Path(SPECPATH).resolve().parent

datas = []
def _toc_to_pairs(toc_items):
    pairs = []
    for item in toc_items:
        if isinstance(item, (list, tuple)) and len(item) == 3:
            dest, src, _typecode = item
            pairs.append((src, dest))
        else:
            pairs.append(item)
    return pairs

templates_dir = repo_root / "templates"
if templates_dir.is_dir():
    for p in templates_dir.rglob("*"):
        if p.is_file():
            rel = p.relative_to(templates_dir)
            dest_dir = str((Path("templates") / rel.parent).as_posix())
            if dest_dir == "templates/.":
                dest_dir = "templates"
            datas.append((str(p), dest_dir))

hiddenimports = []
hiddenimports += collect_submodules("fitz")
hiddenimports += collect_submodules("PyPDF2")
hiddenimports += collect_submodules("fpdf")
hiddenimports += collect_submodules("reportlab")
hiddenimports += collect_submodules("PIL")
hiddenimports += ["cv2", "numpy"]

fitz_data, fitz_bins, fitz_hidden = collect_all("fitz")
datas += _toc_to_pairs(fitz_data)
binaries = _toc_to_pairs(fitz_bins)
hiddenimports += fitz_hidden

try:
    cv2_data, cv2_bins, cv2_hidden = collect_all("cv2")
    datas += _toc_to_pairs(cv2_data)
    binaries += _toc_to_pairs(cv2_bins)
    hiddenimports += cv2_hidden
except Exception:
    pass

a = Analysis(
    [str(repo_root / "app.py")],
    pathex=[str(repo_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    name=backend_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    runtime_tmpdir=None,
    console=True,
    exclude_binaries=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=backend_name,
)
