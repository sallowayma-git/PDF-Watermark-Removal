# PDF-Watermark-Removal
由于有时在抄别人的实验报告会带上水印，所以做了个pdf水印去除的工具，所有类型pdf都可用。

## **需要的库：**

pip install opencv-python

pip install fitz

pip install fpdf

pip install flask

还有一些常见的PIL、numpy等等，具体见app.py

## **如何运行：**

安装所需的库之后，运行app.py，会给出网址（运行在本地），点击进入即可。

在网站中上传pdf文件，点击去除水印，下载去除后的pdf文件

## Electron 桌面版（可选）

此模式会用 Electron 启动本项目的 Flask 后端，并在桌面窗口中打开页面。

前置条件：
- Node.js（建议 18+）
- Python3（仅用于“构建后端可执行文件”），以及本项目 Python 依赖（opencv-python、PyMuPDF/fitz、fpdf、flask 等）

开发运行：
- `npm install`
- `npm run dev`

打包（electron-builder）：
- `npm run dist`

说明：
- 默认会尝试启动内置后端可执行文件目录 `backend/pdfwm_backend`（运行时不依赖用户机器 Python）。
- 构建该可执行文件：`npm run backend:build`（需要先 `pip install -r requirements-backend.txt`），产物会生成在 `backend/pdfwm_backend/`。
- 如果未构建可执行文件，开发模式会回退到用系统 Python 启动 `app.py`（可用环境变量 `PYTHON_BIN` 指定 Python 可执行文件路径）。
- 打包后上传/输出文件会写到系统用户目录下的 Electron `userData/backend-data`（不会写进应用安装目录）。

### Windows 打包

由于 PyInstaller/Electron 需要目标系统环境，Windows 版本建议用以下两种方式之一：

- 在 Windows 机器上本地构建：
  - `pip install -r requirements-backend.txt`
  - `npm install`
  - `npm run backend:build`
  - `npm run dist`（生成 `dist/*.exe` 安装包）

- 用 GitHub Actions 自动构建：
  - 推送新 tag（例如 `v0.1.1`）后，会触发 `.github/workflows/build-windows.yml`，产物在 Actions Artifacts 与 Release 附件里。

### macOS 自动构建

- 推送新 tag（例如 `v0.1.1`）后，会触发 `.github/workflows/build-macos.yml`，产物在 Actions Artifacts 与 Release 附件里。

## **原理：**

将pdf转为多张图片，用cv方法去除每张图片水印，再转回pdf

可以自行设置转换图片的分辨率，默认为300DPI，分辨率越高，去除水印后下载的pdf文件和上传的源文件之间的清晰度差距越小（失真越小）。

如果不是一页密密麻麻很多小字的pdf，不需要很高DPI即可保证处理后的pdf文件与原文件清晰度一致，300DPI完全够用。

## **注意：**

处理pdf文件时间=0.8s * 文件页数（有时间加个进度条）

基本只针对灰色（暗色）水印

pdf转换的图片默认设置300DPI，基本满足需求，可能有部分pdf去除水印后会清晰度损失。计划之后再提供自行设置分辨率功能。

## 另：单图像去除水印
运行UI1.html(如Open In Browser)，即可在网站中去除图片水印、对比处理前后图像、下载处理后图像

### 图像去除水印网页↓↓↓

![PS_%ROHKWH$CSV4X1_Z6QRY](https://github.com/StuHude/PDF-Watermark-Removal/assets/89311278/3db93765-0b97-4cfc-a9d4-3fceb2ba68e7)
