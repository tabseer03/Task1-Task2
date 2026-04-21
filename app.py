from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
from PIL import Image
import numpy as np
import os
import io
import base64
from datetime import datetime
import json

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create upload folder
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

class ImageCompressionTool:
    """Image compression tool with error metrics calculation"""
    
    @staticmethod
    def calculate_mse(original_img, compressed_img):
        """Calculate Mean Squared Error between two images"""
        # Ensure same size
        if original_img.size != compressed_img.size:
            compressed_img = compressed_img.resize(original_img.size, Image.Resampling.LANCZOS)
        
        # Convert to numpy arrays
        orig_array = np.array(original_img, dtype=np.float32)
        comp_array = np.array(compressed_img, dtype=np.float32)
        
        # Calculate MSE
        mse = np.mean((orig_array - comp_array) ** 2)
        return float(mse)
    
    @staticmethod
    def calculate_psnr(mse):
        """Calculate Peak Signal-to-Noise Ratio"""
        if mse == 0:
            return float('inf')
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        return float(psnr)
    
    @staticmethod
    def calculate_ssim(original_img, compressed_img):
        """Calculate Structural Similarity Index (simplified)"""
        if original_img.size != compressed_img.size:
            compressed_img = compressed_img.resize(original_img.size, Image.Resampling.LANCZOS)
        
        orig_array = np.array(original_img, dtype=np.float32)
        comp_array = np.array(compressed_img, dtype=np.float32)
        
        # Calculate variance
        orig_mean = np.mean(orig_array)
        comp_mean = np.mean(comp_array)
        orig_var = np.var(orig_array)
        comp_var = np.var(comp_array)
        
        # Simplified SSIM calculation
        covariance = np.mean((orig_array - orig_mean) * (comp_array - comp_mean))
        
        c1 = 6.5025
        c2 = 58.5225
        
        numerator = (2 * orig_mean * comp_mean + c1) * (2 * covariance + c2)
        denominator = (orig_mean ** 2 + comp_mean ** 2 + c1) * (orig_var + comp_var + c2)
        
        ssim = numerator / denominator
        return float(np.clip(ssim, 0, 1))
    
    @staticmethod
    def compress_image(input_path, quality=80):
        """Compress image and return stats"""
        try:
            img = Image.open(input_path)
            original_size = os.path.getsize(input_path)
            original_resolution = img.size
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save compressed image to bytes
            compressed_buffer = io.BytesIO()
            img.save(compressed_buffer, format='JPEG', quality=quality, optimize=True)
            compressed_size = compressed_buffer.tell() + len(compressed_buffer.getvalue())
            
            # Load compressed image from bytes
            compressed_img = Image.open(io.BytesIO(compressed_buffer.getvalue()))
            
            # Calculate metrics
            mse = ImageCompressionTool.calculate_mse(img, compressed_img)
            psnr = ImageCompressionTool.calculate_psnr(mse)
            ssim = ImageCompressionTool.calculate_ssim(img, compressed_img)
            
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            return {
                'success': True,
                'original_size_kb': round(original_size / 1024, 2),
                'compressed_size_kb': round(compressed_size / 1024, 2),
                'compression_ratio': round(compression_ratio, 2),
                'original_resolution': original_resolution,
                'mse': round(mse, 2),
                'psnr': round(psnr, 2),
                'ssim': round(ssim, 4),
                'quality': quality,
                'compressed_img': compressed_img,
                'compressed_bytes': compressed_buffer.getvalue()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

def image_to_base64(img):
    """Convert PIL image to base64 string"""
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    quality = int(request.form.get('quality', 80))
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif')):
        return jsonify({'success': False, 'error': 'Invalid file format. Supported: JPG, PNG, BMP, GIF'}), 400
    
    try:
        # Save uploaded file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + file.filename)
        file.save(temp_path)
        
        # Open original image
        original_img = Image.open(temp_path)
        if original_img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', original_img.size, (255, 255, 255))
            rgb_img.paste(original_img, mask=original_img.split()[-1] if original_img.mode == 'RGBA' else None)
            original_img = rgb_img
        elif original_img.mode != 'RGB':
            original_img = original_img.convert('RGB')
        
        # Compress
        result = ImageCompressionTool.compress_image(temp_path, quality)
        
        if not result['success']:
            return jsonify({'success': False, 'error': result['error']}), 400
        
        # Convert images to base64
        original_b64 = image_to_base64(original_img)
        compressed_b64 = image_to_base64(result['compressed_img'])
        
        # Clean up
        os.remove(temp_path)
        
        response = {
            'success': True,
            'original_image': original_b64,
            'compressed_image': compressed_b64,
            'original_size_kb': result['original_size_kb'],
            'compressed_size_kb': result['compressed_size_kb'],
            'compression_ratio': result['compression_ratio'],
            'original_resolution': result['original_resolution'],
            'mse': result['mse'],
            'psnr': result['psnr'],
            'ssim': result['ssim'],
            'quality': result['quality'],
            'filename': file.filename
        }
        
        # Save compressed image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_without_ext = os.path.splitext(file.filename)[0]
        compressed_filename = f"{filename_without_ext}_compressed_{timestamp}.jpg"
        compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
        result['compressed_img'].save(compressed_path)
        response['download_filename'] = compressed_filename
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
