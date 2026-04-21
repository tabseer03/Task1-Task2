// File input and upload area
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const compressBtn = document.getElementById('compressBtn');
const qualitySlider = document.getElementById('qualitySlider');
const qualityValue = document.getElementById('qualityValue');
const errorMessage = document.getElementById('errorMessage');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');

let selectedFile = null;
let compressionResult = null;

// Quality slider update
qualitySlider.addEventListener('input', (e) => {
    qualityValue.textContent = e.target.value;
});

// File input click
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// File selection
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

function handleFileSelect(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file');
        return;
    }

    // Validate file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
        showError('File size must be less than 100MB');
        return;
    }

    selectedFile = file;
    const fileName = file.name;
    const fileSize = (file.size / 1024).toFixed(2);
    
    document.getElementById('uploadText').textContent = 
        `✓ ${fileName} selected (${fileSize} KB)`;
    
    compressBtn.disabled = false;
    hideError();
}

// Compress button
compressBtn.addEventListener('click', compressImage);

async function compressImage() {
    if (!selectedFile) {
        showError('Please select an image first');
        return;
    }

    const quality = qualitySlider.value;
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('quality', quality);

    try {
        showLoading(true);
        compressBtn.disabled = true;
        hideError();

        const response = await fetch('/api/compress', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            showError(data.error || 'Compression failed');
            return;
        }

        compressionResult = data;
        displayResults(data);
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        showError('Error during compression: ' + error.message);
    } finally {
        showLoading(false);
        compressBtn.disabled = false;
    }
}

function displayResults(data) {
    // Display images
    document.getElementById('originalImage').src = data.original_image;
    document.getElementById('compressedImage').src = data.compressed_image;

    // File info
    document.getElementById('origFilename').textContent = data.filename;
    document.getElementById('origSize').textContent = data.original_size_kb;
    document.getElementById('origResolution').textContent = 
        `${data.original_resolution[0]} × ${data.original_resolution[1]}`;

    document.getElementById('compQuality').textContent = data.quality;
    document.getElementById('compSize').textContent = data.compressed_size_kb;
    
    const spaceSaved = (data.original_size_kb - data.compressed_size_kb).toFixed(2);
    document.getElementById('spaceSaved').textContent = spaceSaved + ' KB';

    // Statistics
    document.getElementById('statRatio').textContent = data.compression_ratio;
    document.getElementById('statSaved').textContent = spaceSaved;
    document.getElementById('statMSE').textContent = data.mse;
    document.getElementById('statPSNR').textContent = data.psnr;
    document.getElementById('statSSIM').textContent = data.ssim;

    // Quality assessment
    const assessment = getQualityAssessment(data);
    const qualityCard = document.querySelector('.quality-indicator');
    document.getElementById('qualityAssessment').textContent = assessment.text;
    qualityCard.style.background = `linear-gradient(135deg, ${assessment.color1} 0%, ${assessment.color2} 100%)`;
}

function getQualityAssessment(data) {
    const ssim = data.ssim;
    
    if (ssim >= 0.98) {
        return { text: 'Excellent', color1: '#6bcf7f', color2: '#4fa35f' };
    } else if (ssim >= 0.95) {
        return { text: 'Very Good', color1: '#4fa35f', color2: '#3d8b4f' };
    } else if (ssim >= 0.90) {
        return { text: 'Good', color1: '#667eea', color2: '#764ba2' };
    } else if (ssim >= 0.85) {
        return { text: 'Fair', color1: '#ffd93d', color2: '#ffb700' };
    } else {
        return { text: 'Poor', color1: '#ff6b6b', color2: '#ff5252' };
    }
}

// Download button
downloadBtn.addEventListener('click', () => {
    if (compressionResult) {
        const filename = compressionResult.download_filename;
        window.location.href = `/api/download/${filename}`;
    }
});

// Reset button
resetBtn.addEventListener('click', () => {
    selectedFile = null;
    compressionResult = null;
    fileInput.value = '';
    document.getElementById('uploadText').textContent = 
        'Drag and drop your image here or click to select';
    compressBtn.disabled = true;
    resultsSection.style.display = 'none';
    qualitySlider.value = 80;
    qualityValue.textContent = '80';
    hideError();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Utility functions
function showLoading(show) {
    loadingSpinner.style.display = show ? 'block' : 'none';
}

function showError(message) {
    errorMessage.textContent = '⚠️ ' + message;
    errorMessage.style.display = 'block';
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
    errorMessage.style.display = 'none';
}

// Initialize
console.log('Image Compression Tool loaded successfully');
