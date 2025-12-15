from flask import Flask, render_template, request, send_file, jsonify
import os
import sys
import multiprocessing
import cv2
import numpy as np
import fitz
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from fpdf import FPDF
from PIL import Image
import tempfile
import time
import threading
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from werkzeug.utils import secure_filename

CONVERT_DPI = 400

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEIPASS_DIR = getattr(sys, "_MEIPASS", None)
APP_RESOURCES_DIR = MEIPASS_DIR if MEIPASS_DIR else BASE_DIR
TEMPLATES_DIR = os.path.join(APP_RESOURCES_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)

DATA_DIR = os.getenv("DATA_DIR", BASE_DIR)
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
OUTPUT_DIR = os.path.join(DATA_DIR, "output_images")
OUTPUT_PDF_PATH = os.path.join(DATA_DIR, "output_file.pdf")
UPLOADED_PDF_PATH = os.path.join(UPLOAD_DIR, "uploaded_file.pdf")

# 全局进度状态管理
class ProgressManager:
    def __init__(self):
        self.current_task = None
        self.current_progress = 0
        self.current_stage = "idle"
        self.total_pages = 0
        self.current_page = 0
        self.start_time = None
        self.status = "idle"  # idle, processing, completed, error
        self.error_message = None
        self.lock = threading.Lock()
    
    def start_task(self, total_pages):
        with self.lock:
            self.current_task = f"task_{int(time.time())}"
            self.current_progress = 0
            self.current_stage = "starting"
            self.total_pages = total_pages
            self.current_page = 0
            self.start_time = datetime.now()
            self.status = "processing"
            self.error_message = None
            print(f"[进度管理] 开始任务，总页数: {total_pages}")
    
    def update_progress(self, page, stage=None, progress=None):
        with self.lock:
            self.current_page = page
            if stage:
                self.current_stage = stage
            if progress is not None:
                self.current_progress = progress
            else:
                self.current_progress = (page / self.total_pages) * 100 if self.total_pages > 0 else 0
            
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            if self.current_progress > 0:
                eta = (elapsed / self.current_progress) * (100 - self.current_progress)
            else:
                eta = 0
            
            print(f"[进度] {self.current_stage} - 页面 {page}/{self.total_pages} - 进度: {self.current_progress:.1f}% - 耗时: {elapsed:.1f}s - 预计剩余: {eta:.1f}s")
    
    def complete_task(self):
        with self.lock:
            self.status = "completed"
            self.current_progress = 100
            self.current_stage = "completed"
            total_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            print(f"[进度管理] 任务完成，总耗时: {total_time:.1f}s")
    
    def error_task(self, error_msg):
        with self.lock:
            self.status = "error"
            self.error_message = error_msg
            self.current_stage = "error"
            print(f"[进度管理] 任务出错: {error_msg}")
    
    def get_status(self):
        with self.lock:
            return {
                'status': self.status,
                'progress': self.current_progress,
                'stage': self.current_stage,
                'current_page': self.current_page,
                'total_pages': self.total_pages,
                'error_message': self.error_message,
                'start_time': self.start_time.isoformat() if self.start_time else None
            }

# 全局进度管理器实例
progress_manager = ProgressManager()

@app.before_request
def _handle_preflight():
    if request.method == "OPTIONS":
        return app.make_default_options_response()

@app.after_request
def _add_cors_headers(response):
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
    return response

# 图像去除水印函数
def remove_watermark(image_path):
    img = cv2.imread(image_path)
    lower_hsv = np.array([160, 160, 160])
    upper_hsv = np.array([255, 255, 255])
    mask = cv2.inRange(img, lower_hsv, upper_hsv)
    mask = cv2.GaussianBlur(mask, (1, 1), 0)
    img[mask == 255] = [255, 255, 255]
    cv2.imwrite(image_path, img)
    time.sleep(0.1)  # 模拟处理时间，便于观察进度

# 将PDF转换为图片，并保存到指定目录
def pdf_to_images(pdf_path, output_folder):
    images = []
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    
    progress_manager.update_progress(0, "正在打开PDF文件...")
    
    for page_num in range(total_pages):
        progress_manager.update_progress(page_num + 1, f"正在处理第 {page_num + 1} 页...")
        
        page = doc[page_num]
        # 设置分辨率为400 DPI
        pix = page.get_pixmap(matrix=fitz.Matrix(400 / 72, 400 / 72))
        image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(image_path)
        images.append(image_path)
        
        # 去除每张图片的水印
        remove_watermark(image_path)
    
    doc.close()
    progress_manager.update_progress(total_pages, "图片转换完成")
    return images

# 将图片合并为PDF
def images_to_pdf(image_paths, output_path):
    progress_manager.update_progress(0, "正在生成PDF文件...")
    
    pdf_writer = FPDF(unit='pt', format='A4')
    total_images = len(image_paths)
    
    for i, image_path in enumerate(image_paths):
        progress_manager.update_progress(i + 1, f"正在添加图片 {i + 1}/{total_images}...")
        
        with Image.open(image_path) as img:
            width, height = img.size

            # 计算实际DPI（假设从pdf转图片时已设置为400 DPI）
            dpi = 400
            ratio = min(A4_SIZE_PX_72DPI[0] / width, A4_SIZE_PX_72DPI[1] / height)

            # 缩放图像以适应A4纸张，并保持长宽比
            img_resized = img.resize((int(width * ratio), int(height * ratio)))

            # 创建临时文件并写入图片数据
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                img_resized.save(temp_file.name, format='PNG')

            # 添加一页
            pdf_writer.add_page()

            # 使用临时文件路径添加图像到PDF
            pdf_writer.image(temp_file.name, x=0, y=0, w=A4_SIZE_PX_72DPI[0], h=A4_SIZE_PX_72DPI[1])

    # 清理临时文件
    for image_path in image_paths:
        _, temp_filename = os.path.split(image_path)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    pdf_writer.output(output_path)
    progress_manager.update_progress(len(image_paths), "PDF生成完成")

# 后台处理函数
def process_watermark_removal():
    try:
        pdf_path = UPLOADED_PDF_PATH
        output_folder = OUTPUT_DIR
        
        if not os.path.exists(pdf_path):
            progress_manager.error_task("未找到上传的PDF文件")
            return
            
        os.makedirs(output_folder, exist_ok=True)
        
        # 获取PDF页数
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
        
        progress_manager.start_task(total_pages)
        
        # 转换PDF为图片
        image_paths = pdf_to_images(pdf_path, output_folder)
        
        # 生成新的PDF
        images_to_pdf(image_paths, OUTPUT_PDF_PATH)
        
        progress_manager.complete_task()
        
    except Exception as e:
        error_msg = f"处理过程中发生错误: {str(e)}"
        progress_manager.error_task(error_msg)
        print(f"[错误] {error_msg}")

# 定义A4纸张在72dpi下的像素尺寸（宽度和高度）
A4_SIZE_PX_72DPI = (595, 842)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'missing form field: file'}), 400

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename or "")
    if not filename:
        return jsonify({'error': 'empty filename'}), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    uploaded_file.save(UPLOADED_PDF_PATH)
    return jsonify({'status': 'ok', 'filename': filename}), 200

@app.route('/remove_watermark', methods=['GET'])
def remove_watermark_route():
    """启动异步水印去除任务"""
    try:
        if not os.path.exists(UPLOADED_PDF_PATH):
            return jsonify({
                'status': 'error',
                'message': '未找到已上传的PDF文件，请先上传'
            }), 400

        # 启动后台任务
        thread = threading.Thread(target=process_watermark_removal)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': '水印去除任务已启动'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'启动任务失败: {str(e)}'
        }), 500

@app.route('/progress', methods=['GET'])
def get_progress():
    """获取处理进度"""
    status = progress_manager.get_status()
    return jsonify(status)

@app.route('/download')
def download():
    if os.path.exists(OUTPUT_PDF_PATH):
        return send_file(OUTPUT_PDF_PATH, as_attachment=True)
    else:
        return jsonify({'error': '文件不存在'}), 404

if __name__ == '__main__':
    multiprocessing.freeze_support()
    host = os.getenv('HOST', '0.0.0.0')
    try:
        port = int(os.getenv('PORT', '5001'))
    except ValueError:
        port = 5001
    debug = os.getenv('FLASK_DEBUG', '1') not in ('0', 'false', 'False', 'no', 'NO')
    app.run(debug=debug, host=host, port=port)
