@echo off
chcp 65001 >nul
title PDF水印去除工具 - 服务器
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║          PDF 水印去除工具 - 服务器启动器                     ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo       √ Python 已安装
echo.

echo [2/4] 检查依赖包...
echo       正在检查 Flask...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo       × Flask 未安装，正在安装...
    pip install flask
)
echo       √ Flask 已就绪

echo       正在检查 PyMuPDF...
python -c "import fitz" >nul 2>&1
if errorlevel 1 (
    echo       × PyMuPDF 未安装，正在安装...
    pip install pymupdf
)
echo       √ PyMuPDF 已就绪

echo       正在检查 Pillow...
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo       × Pillow 未安装，正在安装...
    pip install pillow
)
echo       √ Pillow 已就绪
echo.

echo [3/4] 启动服务器...
echo.
echo  ┌────────────────────────────────────────────────────────────┐
echo  │  服务器地址: http://localhost:5000                         │
echo  │  按 Ctrl+C 停止服务器                                      │
echo  └────────────────────────────────────────────────────────────┘
echo.

echo [4/4] 正在打开浏览器...
timeout /t 2 >nul
start http://localhost:5000

echo.
echo ═══════════════════════ 服务器日志 ═══════════════════════════
echo.

python app.py

echo.
color 0C
echo [!] 服务器已停止
pause