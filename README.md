# Image Compression Web Application

A modern, user-friendly web application for compressing images with detailed quality metrics and visual comparison.

## Features

✨ **Upload & Compress**
- Drag-and-drop or click to upload images
- Support for JPG, PNG, BMP, GIF formats
- Adjustable compression quality (10-95%)

📊 **Detailed Metrics**
- **MSE (Mean Squared Error)**: Pixel-level difference measurement
- **PSNR (Peak Signal-to-Noise Ratio)**: Quality measurement in dB
- **SSIM (Structural Similarity Index)**: Perceptual quality assessment
- **Space Savings**: File size reduction percentage

🎨 **Visual Comparison**
- Side-by-side original and compressed images
- Detailed statistics for each image
- Quality assessment indicator

⬇️ **Download**
- Download compressed images directly
- Timestamped filenames for easy organization

## Installation

### Requirements
- Python 3.7+
- pip (Python package installer)

### Setup

1. **Install Flask and dependencies:**
```bash
pip install flask pillow numpy
```

2. **Configuration** (Optional)
   - Max file size: 100MB (configurable in app.py)
   - Upload folder: `uploads/` (auto-created)

## Running the Application

### Start the Flask server:
```bash
python app.py
```

The application will be available at:
- Local: `http://localhost:5000`
- Network: `http://<your-ip>:5000`

### Access the web interface:
1. Open your web browser
2. Navigate to `http://localhost:5000`
3. Upload an image
4. Adjust compression quality
5. Click "Compress Image"
6. View results and download if satisfied

## Quality Guidelines

Choose quality based on your needs:

| Quality | Best For | File Size Reduction |
|---------|----------|-------------------|
| 10-40% | Web/Mobile (Aggressive) | 70-80% |
| 40-70% | Social Media | 60-70% |
| 70-85% | General Web Use (Recommended) | 50-60% |
| 85-95% | High Quality / Archive | 30-40% |

## Understanding the Metrics

### MSE (Mean Squared Error)
- **Lower is better**
- Measures average squared difference between pixels
- Typical range: 0-255²
- Example: MSE = 50 is generally considered good

### PSNR (Peak Signal-to-Noise Ratio)
- **Higher is better**
- Measured in decibels (dB)
- PSNR > 40dB: Excellent quality
- PSNR 30-40dB: Good quality
- PSNR < 30dB: Noticeable quality loss

### SSIM (Structural Similarity Index)
- **Ranges from 0 to 1** (1 = perfect match)
- SSIM > 0.98: Excellent (perceptually identical)
- SSIM 0.95-0.98: Very Good
- SSIM 0.90-0.95: Good
- SSIM 0.85-0.90: Fair
- SSIM < 0.85: Poor

## File Structure

```
lab2/
├── app.py                          # Flask server
├── README.md                       # This file
├── templates/
│   └── index.html                 # HTML template
├── static/
│   ├── style.css                  # Styling
│   └── script.js                  # Client-side logic
├── uploads/                       # Compressed images (auto-created)
└── sample_images/                 # Sample images for testing
```

## API Endpoints

### POST `/api/compress`
Compress an image

**Parameters:**
- `file`: Image file (multipart/form-data)
- `quality`: Compression quality 10-95 (optional, default: 80)

**Response:**
```json
{
    "success": true,
    "original_image": "base64_encoded_original_image",
    "compressed_image": "base64_encoded_compressed_image",
    "original_size_kb": 43.8,
    "compressed_size_kb": 24.4,
    "compression_ratio": 44.29,
    "original_resolution": [512, 512],
    "mse": 25.5,
    "psnr": 39.8,
    "ssim": 0.9845,
    "quality": 80,
    "filename": "image.jpg",
    "download_filename": "image_compressed_20260416_120530.jpg"
}
```

### GET `/api/download/<filename>`
Download a compressed image

**Parameters:**
- `filename`: Name of the compressed image file

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Any modern browser with ES6 support

## Troubleshooting

**Port already in use:**
```bash
# Change port in app.py
app.run(host='localhost', port=5001)
```

**Module not found errors:**
```bash
pip install --upgrade flask pillow numpy
```

**File upload limit:**
Edit in app.py:
```python
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
```

## Performance Notes

- Initial compression may take 1-3 seconds depending on image size
- Large images (>20MB) may take longer to process
- Server-side processing ensures consistent results across browsers

## License

Open source - feel free to modify and distribute

## Support

For issues or improvements, check the code comments or modify parameters as needed.
