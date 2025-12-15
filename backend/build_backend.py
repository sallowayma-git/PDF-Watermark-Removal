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

    built_dir = dist_dir / "pdfwm_backend"
    if not built_dir.exists():
        print(f"未找到构建产物目录：{built_dir}")
        return 3

    out_dir = repo_root / "backend" / "pdfwm_backend"
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    shutil.move(str(built_dir), str(out_dir))
    print("Built backend:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
