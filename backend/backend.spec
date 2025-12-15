# PyInstaller spec for bundling the Flask backend into a single executable.
# Build command:
#   pyinstaller --clean --noconfirm backend/backend.spec

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.datastruct import Tree

backend_name = "pdfwm_backend"

datas = []
datas += [Tree("templates", prefix="templates")]

hiddenimports = []
hiddenimports += collect_submodules("fitz")
hiddenimports += collect_submodules("PyPDF2")
hiddenimports += collect_submodules("fpdf")
hiddenimports += collect_submodules("reportlab")
hiddenimports += collect_submodules("PIL")
hiddenimports += ["cv2", "numpy"]

fitz_data, fitz_bins, fitz_hidden = collect_all("fitz")
datas += fitz_data
binaries = fitz_bins
hiddenimports += fitz_hidden

try:
    cv2_data, cv2_bins, cv2_hidden = collect_all("cv2")
    datas += cv2_data
    binaries += cv2_bins
    hiddenimports += cv2_hidden
except Exception:
    pass

a = Analysis(
    ["app.py"],
    pathex=["."],
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
    a.binaries,
    a.datas,
    [],
    name=backend_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

