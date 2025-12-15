import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    try:
        import PyInstaller  # noqa: F401
    except Exception:
        print("PyInstaller 未安装。请先执行：pip install pyinstaller")
        return 2

    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    for d in (dist_dir, build_dir):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    spec_path = repo_root / "backend" / "backend.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(spec_path)]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

    exe_name = "pdfwm_backend.exe" if sys.platform.startswith("win") else "pdfwm_backend"
    built_path = dist_dir / exe_name
    if not built_path.exists():
        print(f"未找到构建产物：{built_path}")
        return 3

    out_path = repo_root / "backend" / exe_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    shutil.move(str(built_path), str(out_path))
    print("Built backend:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

