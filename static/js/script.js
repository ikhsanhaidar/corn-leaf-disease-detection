// ============================================
// DOM Elements
// ============================================
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const previewContainer = document.getElementById('previewContainer');
const uploadForm = document.getElementById('uploadForm');
const loadingOverlay = document.getElementById('loadingOverlay');
const navbar = document.querySelector('.navbar');

// ============================================
// Image Preview Function
// ============================================
function previewImage(event) {
    const file = event.target.files[0];
    
    if (file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            alert('Format file tidak didukung. Harap unggah file JPG, PNG, atau JPEG.');
            return;
        }
        
        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            alert('Ukuran file terlalu besar. Maksimal 5MB.');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            previewContainer.style.display = 'block';
            
            // Add fade-in animation
            preview.style.opacity = '0';
            preview.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                preview.style.opacity = '1';
            }, 10);
        };
        reader.readAsDataURL(file);
    }
}

// ============================================
// Loading Overlay Functions
// ============================================
function showLoading() {
    if (uploadForm.checkValidity()) {
        loadingOverlay.classList.add('active');
        
        // Simulate progress animation
        const progressBar = loadingOverlay.querySelector('.progress-bar');
        let width = 0;
        const interval = setInterval(() => {
            if (width >= 90) {
                clearInterval(interval);
            } else {
                width += 10;
                progressBar.style.width = width + '%';
            }
        }, 300);
    } else {
        // Highlight invalid fields
        const invalidFields = uploadForm.querySelectorAll(':invalid');
        invalidFields.forEach(field => {
            field.style.borderColor = 'var(--danger)';
            field.style.boxShadow = '0 0 0 0.2rem rgba(211, 47, 47, 0.25)';
            
            // Remove highlight after 2 seconds
            setTimeout(() => {
                field.style.borderColor = '';
                field.style.boxShadow = '';
            }, 2000);
        });
    }
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

// ============================================
// Results Download
// ============================================
function downloadResults() {
    // Create a printable version of results
    const printContent = document.querySelector('.results-card').cloneNode(true);
    const printWindow = window.open('', '_blank');
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Laporan Analisis - AgriScan AI</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1, h2, h3 { color: #2E7D32; }
                .print-header { text-align: center; margin-bottom: 30px; }
                .print-header h1 { margin-bottom: 5px; }
                .print-date { color: #666; font-size: 14px; }
                .section { margin-bottom: 20px; }
                .disease-badge { 
                    background: #D32F2F; 
                    color: white; 
                    padding: 10px 20px; 
                    border-radius: 20px; 
                    display: inline-block; 
                    margin: 10px 0; 
                }
                .progress-bar { 
                    height: 10px; 
                    background: #4CAF50; 
                    border-radius: 5px; 
                    margin: 5px 0; 
                }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th { background: #f5f5f5; padding: 10px; text-align: left; }
                td { padding: 8px 10px; border-bottom: 1px solid #eee; }
                .footer { margin-top: 50px; text-align: center; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="print-header">
                <h1>Laporan Analisis Penyakit Daun Jagung</h1>
                <div class="print-date">${new Date().toLocaleDateString('id-ID', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                })}</div>
            </div>
            ${printContent.innerHTML}
            <div class="footer">
                <p>Dibuat dengan AgriScan AI - Sistem Hybrid Deteksi Penyakit Daun Jagung</p>
                <p>© ${new Date().getFullYear()} AgriScan AI. Hak Cipta Dilindungi.</p>
            </div>
        </body>
        </html>
    `);
    
    printWindow.document.close();
    
    // Auto-print after a short delay
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

// Toggle charts visibility
function toggleCharts() {
    const chartsSection = document.getElementById('chartsSection');
    const toggle = document.getElementById('chartToggle');
    
    if (toggle.checked) {
        chartsSection.style.display = 'block';
        chartsSection.style.animation = 'fadeIn 0.5s ease';
    } else {
        chartsSection.style.display = 'none';
    }
}

// Toggle image info
function toggleImageInfo() {
    alert('Informasi Gambar:\n\n- Format: ' + imagePath.split('.').pop().toUpperCase() + 
          '\n- Tanggal Analisis: ' + new Date().toLocaleDateString('id-ID') +
          '\n- Ukuran: Asli dari upload user' +
          '\n- Resolusi: 256x256 pixels (resized untuk analisis)');
}

// Download results
function downloadResults() {
    alert('Fitur ekspor laporan akan segera tersedia!\n\nFitur ini akan meng-generate PDF laporan lengkap hasil analisis.');
}

// Animation for elements
document.addEventListener('DOMContentLoaded', function() {
    // Animate confidence bars
    const confidenceBars = document.querySelectorAll('.confidence-fill');
    confidenceBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 300);
    });
});

// ============================================
// Smooth Scrolling
// ============================================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });
}

// ============================================
// Navbar Scroll Effect
// ============================================
function initNavbarScroll() {
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove shadow based on scroll position
        if (scrollTop > 100) {
            navbar.style.boxShadow = 'var(--shadow-md)';
            navbar.style.padding = '0.8rem 0';
        } else {
            navbar.style.boxShadow = 'var(--shadow-sm)';
            navbar.style.padding = '1.2rem 0';
        }
        
        // Hide/show navbar on scroll (optional)
        if (scrollTop > lastScrollTop && scrollTop > 200) {
            // Scrolling down
            navbar.style.transform = 'translateY(-100%)';
        } else {
            // Scrolling up
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });
}

// ============================================
// Form Validation Enhancement
// ============================================
function initFormValidation() {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Harap pilih gambar terlebih dahulu.');
                fileInput.closest('.upload-area').style.borderColor = 'var(--danger)';
                return false;
            }
            
            // Validate all select inputs
            const selects = form.querySelectorAll('select');
            let isValid = true;
            
            selects.forEach(select => {
                if (!select.value) {
                    isValid = false;
                    select.style.borderColor = 'var(--danger)';
                } else {
                    select.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Harap lengkapi semua data lingkungan.');
                return false;
            }
            
            return true;
        });
    }
}

// ============================================
// Drag and Drop Functionality
// ============================================
function initDragAndDrop() {
    const uploadArea = document.querySelector('.upload-area');
    
    if (uploadArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            uploadArea.style.borderColor = 'var(--accent)';
            uploadArea.style.background = 'rgba(139, 195, 74, 0.15)';
        }
        
        function unhighlight(e) {
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';
        }
        
        // Handle dropped files
        uploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                fileInput.files = files;
                
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }
    }
}

// ============================================
// Initialize Charts (for dynamic data)
// ============================================
function initCharts(probabilitiesDict, cnnConfidence, expertConfidence, hybridConfidence) {
    // This function would be called from the template with actual data
    console.log('Charts initialized with:', {
        probabilitiesDict,
        cnnConfidence,
        expertConfidence,
        hybridConfidence
    });
    
    // Chart initialization code moved to template for Flask variable access
}

// ============================================
// Initialize All Functions
// ============================================
function initApp() {
    // Initialize smooth scrolling
    initSmoothScroll();
    
    // Initialize navbar scroll effects
    initNavbarScroll();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize drag and drop
    initDragAndDrop();
    
    // Auto-hide loading overlay after 5 seconds (fallback)
    setTimeout(() => {
        if (loadingOverlay.classList.contains('active')) {
            hideLoading();
        }
    }, 5000);
    
    console.log('AgriScan AI initialized successfully');
}

// ============================================
// Event Listeners
// ============================================
document.addEventListener('DOMContentLoaded', initApp);

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden
        if (loadingOverlay.classList.contains('active')) {
            loadingOverlay.style.opacity = '0.8';
        }
    } else {
        // Page is visible again
        if (loadingOverlay.classList.contains('active')) {
            loadingOverlay.style.opacity = '1';
        }
    }
});

// Handle form reset
window.addEventListener('pageshow', function(event) {
    // If the page was loaded from cache, reset the form
    if (event.persisted) {
        uploadForm.reset();
        previewContainer.style.display = 'none';
        hideLoading();
    }
});

// ============================================
// Global Functions (accessible from template)
// ============================================
window.previewImage = previewImage;
window.showLoading = showLoading;
window.downloadResults = downloadResults;