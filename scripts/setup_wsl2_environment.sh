#!/bin/bash
# WSL2 Environment Setup Script for HippoVet+ Equine Microbiome Reporter
# Tested on WSL2 with Epi2Me/Nextflow integration

set -e  # Exit on error

echo "==============================================="
echo "HippoVet+ Equine Microbiome Reporter Setup"
echo "WSL2 Environment Configuration"
echo "==============================================="

# Check if running in WSL2
if ! grep -q microsoft /proc/version; then
    echo "⚠️  Warning: Not running in WSL environment"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ WSL environment detected"
    # Check WSL version
    if [[ $(uname -r) == *"WSL2"* ]] || [[ $(uname -r) == *"microsoft-standard-WSL2"* ]]; then
        echo "✅ Running on WSL2"
    else
        echo "ℹ️  Running on WSL1 (WSL2 recommended for better performance)"
    fi
fi

# Function to check command availability
check_command() {
    if command -v $1 &> /dev/null; then
        echo "✅ $1 is installed"
        return 0
    else
        echo "❌ $1 is not installed"
        return 1
    fi
}

# Check prerequisites
echo -e "\n📋 Checking prerequisites..."
MISSING_DEPS=0

if ! check_command conda; then
    echo "   Please install Miniconda or Anaconda first"
    echo "   Visit: https://docs.conda.io/en/latest/miniconda.html"
    MISSING_DEPS=1
fi

if ! check_command git; then
    echo "   Please install git: sudo apt-get install git"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "\n❌ Missing dependencies. Please install them and run this script again."
    exit 1
fi

# Clone or update repository
INSTALL_DIR="$HOME/equine-microbiome-reporter"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "\n📂 Repository already exists at $INSTALL_DIR"
    cd "$INSTALL_DIR"
    echo "   Pulling latest changes..."
    git pull origin main 2>/dev/null || echo "   (Using local version)"
else
    echo -e "\n📥 Cloning repository..."
    git clone https://github.com/trentleslie/equine-microbiome-reporter.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Create conda environment
ENV_NAME="equine-microbiome"
echo -e "\n🐍 Setting up conda environment: $ENV_NAME"

if conda env list | grep -q "^$ENV_NAME "; then
    echo "   Environment already exists. Updating..."
    conda env update -n $ENV_NAME -f environment.yml --prune
else
    echo "   Creating new environment..."
    # Try to use environment.yml first, fall back to manual creation
    if [ -f "environment.yml" ]; then
        conda env create -f environment.yml -n $ENV_NAME
    else
        conda create -n $ENV_NAME python=3.9 -y
        conda activate $ENV_NAME
        
        # Install conda packages
        conda install -c conda-forge \
            pandas numpy matplotlib seaborn scipy \
            jinja2 pyyaml flask werkzeug \
            biopython openpyxl python-dotenv \
            jupyter notebook ipykernel tqdm psutil -y
        
        # Install pip packages
        pip install reportlab weasyprint
    fi
fi

# Activate environment
echo -e "\n🔧 Activating environment..."
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

# Verify installation
echo -e "\n✨ Verifying installation..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from report_generator import ReportGenerator
    from data_models import PatientInfo
    from clinical_filter import ClinicalFilter
    print('✅ Core modules loaded successfully')
except ImportError as e:
    print(f'❌ Error loading modules: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Installation verified successfully"
else
    echo "❌ Installation verification failed"
    exit 1
fi

# Create data directories
echo -e "\n📁 Creating data directories..."
mkdir -p data
mkdir -p reports
mkdir -p batch_output
mkdir -p logs
echo "✅ Directories created"

# WSL2-specific optimizations
echo -e "\n⚡ Applying WSL2 optimizations..."

# Check if .wslconfig exists in Windows user home
WIN_HOME="/mnt/c/Users/$USER"
if [ -d "$WIN_HOME" ]; then
    WSL_CONFIG="$WIN_HOME/.wslconfig"
    if [ ! -f "$WSL_CONFIG" ]; then
        echo "   Creating .wslconfig for optimal performance..."
        cat > "$WSL_CONFIG" << EOF
[wsl2]
memory=8GB
processors=4
swap=4GB
localhostForwarding=true
EOF
        echo "   ⚠️  WSL2 configuration created. Restart WSL for changes to take effect:"
        echo "      Run 'wsl --shutdown' in PowerShell, then restart WSL"
    else
        echo "   .wslconfig already exists"
    fi
fi

# Performance test
echo -e "\n🚀 Running performance test..."
python -c "
import time
import numpy as np

# I/O test
start = time.time()
data = np.random.rand(1000000)
np.save('test_performance.npy', data)
loaded = np.load('test_performance.npy')
io_time = time.time() - start

# Computation test
start = time.time()
result = np.dot(data, data)
compute_time = time.time() - start

import os
os.remove('test_performance.npy')

print(f'   I/O Performance: {1/io_time:.1f} MB/s')
print(f'   Compute Performance: {1000000/compute_time/1000:.1f} KFLOPS')
"

# Integration with Epi2Me
echo -e "\n🔗 Epi2Me/Nextflow Integration"
if [ -d "/mnt/c/Users/hippovet/epi2melabs" ]; then
    echo "✅ Epi2Me installation detected"
    echo "   You can process Kraken2 outputs directly from:"
    echo "   /mnt/c/Users/hippovet/epi2melabs/instances/*/output"
else
    echo "ℹ️  Epi2Me not detected at expected location"
    echo "   Update paths in scripts/epi2me_wrapper.py if needed"
fi

# Create launcher script
LAUNCHER="$HOME/run_microbiome_reporter.sh"
cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
# Quick launcher for Equine Microbiome Reporter

REPO_DIR="$HOME/equine-microbiome-reporter"
cd "$REPO_DIR"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate equine-microbiome

# Launch Jupyter notebook for interactive processing
echo "Starting Jupyter notebook..."
jupyter notebook notebooks/batch_processing.ipynb
EOF

chmod +x "$LAUNCHER"
echo -e "\n📝 Created launcher script: $LAUNCHER"

# Final instructions
echo -e "\n==============================================="
echo "✅ Setup Complete!"
echo "==============================================="
echo ""
echo "To use the system:"
echo "1. Activate environment: conda activate $ENV_NAME"
echo "2. Process single sample:"
echo "   python -m src.report_generator --csv data/sample.csv --output report.pdf"
echo "3. Batch processing:"
echo "   python scripts/batch_clinical_processor.py --input /path/to/csvs --output results/"
echo "4. Interactive mode:"
echo "   $LAUNCHER"
echo ""
echo "For Epi2Me integration:"
echo "   python scripts/epi2me_wrapper.py --instance [INSTANCE_ID]"
echo ""
echo "Documentation: https://github.com/trentleslie/equine-microbiome-reporter"
echo "==============================================="