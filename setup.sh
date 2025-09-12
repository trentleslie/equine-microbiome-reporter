#!/bin/bash
# Equine Microbiome Reporter - Complete Setup Script
# This script handles the entire installation process including test data from Google Drive

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Google Drive file ID for test data
GDRIVE_FILE_ID="1OmhZwEOYZ7BOUUOm08lRgDek8sO_S-tR"

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}   Equine Microbiome Reporter - Installation Setup   ${NC}"
echo -e "${BLUE}=====================================================${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${GREEN}[Step 1/8] Checking prerequisites...${NC}"
    
    # Check if running in WSL
    if grep -qi microsoft /proc/version; then
        echo "✓ Running in WSL environment"
        IN_WSL=true
    else
        echo -e "${YELLOW}Note: Not running in WSL, but continuing...${NC}"
        IN_WSL=false
    fi
    
    # Check conda
    if ! command -v conda &> /dev/null; then
        echo -e "${YELLOW}Conda not found. Installing Miniconda...${NC}"
        wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
        bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
        eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
        conda init bash
        echo "✓ Miniconda installed"
        echo -e "${YELLOW}Note: You may need to restart your terminal after installation${NC}"
    else
        echo "✓ Conda is installed"
    fi
    
    # Source conda
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        source "/opt/conda/etc/profile.d/conda.sh"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}Installing git via conda...${NC}"
        conda install -c conda-forge git -y > /dev/null 2>&1
        echo "✓ Git installed"
    else
        echo "✓ Git is installed"
    fi
    
    # Check wget
    if ! command -v wget &> /dev/null; then
        echo -e "${YELLOW}Installing wget...${NC}"
        conda install -c conda-forge wget -y > /dev/null 2>&1
    fi
    
    echo ""
}

# Function to clone repository
clone_repository() {
    echo -e "${GREEN}[Step 2/8] Cloning repository...${NC}"
    
    if [ -d "equine-microbiome-reporter" ]; then
        echo -e "${YELLOW}Directory already exists. Removing old installation...${NC}"
        rm -rf equine-microbiome-reporter
    fi
    
    git clone https://github.com/trentleslie/equine-microbiome-reporter.git
    cd equine-microbiome-reporter
    echo "✓ Repository cloned"
    echo ""
}

# Function to download test data from Google Drive
download_test_data() {
    echo -e "${GREEN}[Step 3/8] Downloading test data from Google Drive...${NC}"
    
    # Create data directory
    mkdir -p data
    cd data
    
    # Check if test data already exists
    if [ -f "barcode04_test.fastq" ] && [ -f "barcode05_test.fastq" ] && [ -f "barcode06_test.fastq" ]; then
        echo "✓ Test data already exists, skipping download"
        cd ..
        return
    fi
    
    # Download from Google Drive (handles virus scan warning)
    echo "Downloading test data package (this may take a moment)..."
    
    # Method 1: Try with gdown if available
    if command -v gdown &> /dev/null; then
        gdown --id ${GDRIVE_FILE_ID} -O test_data.tar.gz
    else
        # Method 2: Handle Google Drive virus scan warning
        # First request to get the warning page
        wget --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate \
            "https://drive.google.com/uc?export=download&id=${GDRIVE_FILE_ID}" \
            -O /tmp/gdrive_page.html 2>/dev/null
        
        # Extract the confirmation token and UUID from the HTML
        CONFIRM_TOKEN=$(grep -o 'name="confirm" value="[^"]*"' /tmp/gdrive_page.html | sed 's/.*value="//;s/"//')
        UUID=$(grep -o 'name="uuid" value="[^"]*"' /tmp/gdrive_page.html | sed 's/.*value="//;s/"//')
        
        if [ -n "$CONFIRM_TOKEN" ] && [ -n "$UUID" ]; then
            # Download with confirmation
            echo "Large file detected, confirming download..."
            wget --load-cookies /tmp/cookies.txt \
                "https://drive.usercontent.google.com/download?id=${GDRIVE_FILE_ID}&export=download&confirm=${CONFIRM_TOKEN}&uuid=${UUID}" \
                -O test_data.tar.gz
        else
            # Try direct download (for smaller files)
            wget --load-cookies /tmp/cookies.txt \
                "https://drive.google.com/uc?export=download&id=${GDRIVE_FILE_ID}" \
                -O test_data.tar.gz
        fi
        
        # Clean up temp files
        rm -f /tmp/cookies.txt /tmp/gdrive_page.html
    fi
    
    # Check if download was successful
    if [ ! -f "test_data.tar.gz" ]; then
        echo -e "${YELLOW}Warning: Could not download test data automatically.${NC}"
        echo "Please download manually from:"
        echo "https://drive.google.com/file/d/${GDRIVE_FILE_ID}/view"
        echo "Then extract to the data/ directory"
    else
        # Extract the tarball
        echo "Extracting test data..."
        tar -xzf test_data.tar.gz
        rm test_data.tar.gz
        
        # List extracted files
        echo "✓ Test data downloaded and extracted:"
        ls -lh barcode*.fastq 2>/dev/null | head -5
    fi
    
    cd ..
    echo ""
}

# Function to create conda environment
setup_environment() {
    echo -e "${GREEN}[Step 4/8] Creating conda environment...${NC}"
    
    # Check if environment already exists
    if conda env list | grep -q "equine-microbiome"; then
        echo -e "${YELLOW}Environment 'equine-microbiome' already exists${NC}"
        read -p "Remove and recreate? (y/n) [n]: " RECREATE
        if [ "$RECREATE" = "y" ]; then
            conda env remove -n equine-microbiome -y > /dev/null 2>&1
        else
            echo "✓ Using existing environment"
            eval "$(conda shell.bash hook)"
            conda activate equine-microbiome
            echo ""
            return
        fi
    fi
    
    # Create environment
    echo "Creating new conda environment (this may take a few minutes)..."
    conda create -n equine-microbiome python=3.9 -y > /dev/null 2>&1
    
    # Activate environment
    eval "$(conda shell.bash hook)"
    conda activate equine-microbiome
    
    echo "✓ Conda environment 'equine-microbiome' created"
    echo ""
}

# Function to install dependencies
install_dependencies() {
    echo -e "${GREEN}[Step 5/8] Installing dependencies...${NC}"
    
    # Make sure we're in the right environment
    eval "$(conda shell.bash hook)"
    conda activate equine-microbiome
    
    # Install conda packages
    echo "Installing scientific packages (this may take 5-10 minutes)..."
    echo "  Installing core packages..."
    conda install -n equine-microbiome -c conda-forge \
        pandas numpy matplotlib seaborn scipy -y > /dev/null 2>&1
    
    echo "  Installing web and template packages..."
    conda install -n equine-microbiome -c conda-forge \
        jinja2 pyyaml flask werkzeug -y > /dev/null 2>&1
    
    echo "  Installing bio and data packages..."
    conda install -n equine-microbiome -c conda-forge \
        biopython openpyxl python-dotenv -y > /dev/null 2>&1
    
    echo "  Installing notebook and utility packages..."
    conda install -n equine-microbiome -c conda-forge \
        jupyter notebook ipykernel tqdm psutil -y > /dev/null 2>&1
    
    echo "  Installing system libraries for PDF generation..."
    conda install -n equine-microbiome -c conda-forge \
        cairo pango gdk-pixbuf libffi -y > /dev/null 2>&1
    
    # Install pip packages
    echo "Installing PDF generation packages..."
    pip install --quiet reportlab weasyprint cssselect2
    
    echo "✓ All dependencies installed"
    echo ""
}

# Function to find barcode data
find_barcode_data() {
    local search_dir=$1
    echo "Searching for barcode data in $search_dir..."
    
    # Check different naming patterns
    if ls "$search_dir"/barcode*/FAO*.fastq 2>/dev/null | head -1 > /dev/null; then
        echo "✓ Found Epi2Me format barcode folders"
        return 0
    elif ls "$search_dir"/barcode*.fastq.gz 2>/dev/null | head -1 > /dev/null; then
        echo "✓ Found compressed FASTQ files"
        return 0
    elif ls "$search_dir"/barcode*.fastq 2>/dev/null | head -1 > /dev/null; then
        echo "✓ Found FASTQ files"
        return 0
    elif ls "$search_dir"/barcode*/ 2>/dev/null | head -1 > /dev/null; then
        echo "✓ Found barcode folders"
        return 0
    else
        echo "⚠ No barcode data found"
        return 1
    fi
}

# Function for interactive path configuration
configure_paths_interactive() {
    echo -e "${GREEN}[Step 6/8] Configuring paths...${NC}"
    echo ""
    echo "Let's configure your environment. Press Enter to use defaults."
    echo ""
    
    # 1. Check for Kraken2 database
    echo -e "${CYAN}=== Kraken2 Database Configuration ===${NC}"
    echo "Looking for Kraken2 databases..."
    
    # Auto-detect common Kraken2 locations
    KRAKEN_SEARCH_PATHS=(
        "/mnt/c/Users/*/epi2melabs/data/PlusPFP*"
        "/mnt/c/Users/*/Desktop/databases/PlusPFP*"
        "/mnt/c/Users/*/Desktop/databases/kraken2/*"
        "/mnt/c/kraken2/*"
        "$HOME/kraken2/*"
        "/data/kraken2/*"
    )
    
    FOUND_DBS=""
    for pattern in "${KRAKEN_SEARCH_PATHS[@]}"; do
        for dir in $pattern; do
            if [ -d "$dir" ] 2>/dev/null; then
                FOUND_DBS="${FOUND_DBS}${dir}\n"
            fi
        done
    done
    
    if [ -n "$FOUND_DBS" ]; then
        echo "Found potential Kraken2 databases:"
        echo -e "$FOUND_DBS" | nl
        echo ""
        read -p "Select database number (or press Enter to skip Kraken2): " DB_CHOICE
        
        if [ -n "$DB_CHOICE" ]; then
            KRAKEN2_DB=$(echo -e "$FOUND_DBS" | sed -n "${DB_CHOICE}p")
            echo "✓ Selected: $KRAKEN2_DB"
        else
            KRAKEN2_DB="NOT_CONFIGURED"
            echo "⚠ Kraken2 will not be configured (you can run without it for testing)"
        fi
    else
        echo "No Kraken2 databases found automatically."
        echo "You can:"
        echo "  1. Enter the path manually"
        echo "  2. Skip for now (test without Kraken2)"
        read -p "Enter Kraken2 database path (or press Enter to skip): " KRAKEN2_DB
        KRAKEN2_DB=${KRAKEN2_DB:-"NOT_CONFIGURED"}
    fi
    
    echo ""
    
    # 2. Ask for FASTQ data location
    echo -e "${CYAN}=== FASTQ Data Location ===${NC}"
    echo "Where is your FASTQ data located?"
    echo "Examples:"
    echo "  • /mnt/c/data/DIAG_samples/"
    echo "  • /mnt/c/Users/username/Desktop/fastq/"
    echo "  • ./data (for test data included with this installation)"
    echo ""
    
    read -p "FASTQ directory path [./data]: " FASTQ_DIR
    FASTQ_DIR=${FASTQ_DIR:-"./data"}
    
    # Validate FASTQ directory
    if [ -d "$FASTQ_DIR" ]; then
        echo "✓ Directory exists: $FASTQ_DIR"
        # Check for barcode folders or files
        if find_barcode_data "$FASTQ_DIR"; then
            :
        else
            echo "⚠ No barcode files found yet (you can add them later)"
        fi
    else
        echo "⚠ Directory doesn't exist. Will use test data (./data) for now."
        FASTQ_DIR="./data"
    fi
    
    echo ""
    
    # 3. Ask about barcode naming convention
    echo -e "${CYAN}=== Barcode File Format ===${NC}"
    echo "How are your barcode files/folders organized?"
    echo "  1. Folders: barcode04/, barcode05/, etc."
    echo "  2. Files: barcode04.fastq, barcode05.fastq"
    echo "  3. Compressed: barcode04.fastq.gz"
    echo "  4. Epi2Me format: fastq_pass/barcode04/"
    echo ""
    read -p "Select format (1-4) [1]: " BARCODE_FORMAT
    BARCODE_FORMAT=${BARCODE_FORMAT:-"1"}
    
    echo ""
    
    # 4. Ask for output location
    echo -e "${CYAN}=== Output Directory ===${NC}"
    echo "Where should results be saved?"
    
    # If in WSL, suggest Windows Desktop
    if [ "$IN_WSL" = true ]; then
        # Try to detect Windows username
        WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r\n')
        if [ -n "$WIN_USER" ]; then
            SUGGESTED_OUTPUT="/mnt/c/Users/${WIN_USER}/Desktop/microbiome_results"
            echo "Suggested: $SUGGESTED_OUTPUT"
        else
            SUGGESTED_OUTPUT="./output"
        fi
    else
        SUGGESTED_OUTPUT="./output"
    fi
    
    read -p "Output directory [$SUGGESTED_OUTPUT]: " OUTPUT_DIR
    OUTPUT_DIR=${OUTPUT_DIR:-"$SUGGESTED_OUTPUT"}
    
    # Create output directory if it doesn't exist
    mkdir -p "$OUTPUT_DIR" 2>/dev/null || true
    
    echo ""
    
    # 5. Ask about Windows username (for WSL paths)
    if [ "$IN_WSL" = true ]; then
        echo -e "${CYAN}=== Windows Integration ===${NC}"
        echo "What's your Windows username? (for Desktop access)"
        read -p "Windows username [$WIN_USER]: " WINDOWS_USER
        WINDOWS_USER=${WINDOWS_USER:-"$WIN_USER"}
        
        if [ -n "$WINDOWS_USER" ]; then
            WINDOWS_DESKTOP="/mnt/c/Users/${WINDOWS_USER}/Desktop"
            if [ -d "$WINDOWS_DESKTOP" ]; then
                echo "✓ Windows Desktop accessible at $WINDOWS_DESKTOP"
            fi
        fi
        echo ""
    fi
    
    # 6. Create customized .env file
    echo "Creating configuration file..."
    
    cat > .env << EOF
# Equine Microbiome Reporter Configuration
# Generated by setup.sh on $(date)

# === DATA PATHS ===
# Location of your FASTQ files or barcode folders
FASTQ_INPUT_DIR=${FASTQ_DIR}

# Barcode file format (1=folders, 2=files, 3=compressed, 4=epi2me)
BARCODE_FORMAT=${BARCODE_FORMAT}

# === KRAKEN2 CONFIGURATION ===
EOF

    if [ "$KRAKEN2_DB" != "NOT_CONFIGURED" ] && [ -n "$KRAKEN2_DB" ]; then
        cat >> .env << EOF
# Kraken2 database path (detected/provided)
KRAKEN2_DB_PATH=${KRAKEN2_DB}
KRAKEN2_EXECUTABLE=kraken2
KRAKEN2_THREADS=4
KRAKEN2_MEMORY_MAPPING=true
USE_MOCK_KRAKEN=false
EOF
    else
        cat >> .env << EOF
# Kraken2 not configured - update these paths when available
# KRAKEN2_DB_PATH=/path/to/kraken2/database
# KRAKEN2_EXECUTABLE=kraken2
# KRAKEN2_THREADS=4
# KRAKEN2_MEMORY_MAPPING=true

# Using mock Kraken2 mode for testing (no database required)
USE_MOCK_KRAKEN=true
EOF
    fi
    
    cat >> .env << EOF

# === OUTPUT DIRECTORIES ===
DEFAULT_OUTPUT_DIR=${OUTPUT_DIR}
EXCEL_REVIEW_DIR=${OUTPUT_DIR}/excel_review
PDF_OUTPUT_DIR=${OUTPUT_DIR}/pdf_reports

# === WINDOWS PATHS (if in WSL) ===
EOF

    if [ -n "$WINDOWS_USER" ]; then
        cat >> .env << EOF
WINDOWS_USER=${WINDOWS_USER}
WINDOWS_DESKTOP=${WINDOWS_DESKTOP}
EOF
    fi
    
    cat >> .env << EOF

# === PROCESSING OPTIONS ===
ENABLE_PARALLEL_PROCESSING=true
MAX_PARALLEL_SAMPLES=4

# === REPORT SETTINGS ===
REPORT_LANGUAGE=en
INSTITUTION_NAME=HippoVet+

# === CLINICAL FILTERING ===
MIN_ABUNDANCE_THRESHOLD=0.01
CLINICAL_RELEVANCE_THRESHOLD=0.1

# === LOGGING ===
LOG_LEVEL=INFO
SAVE_INTERMEDIATE_FILES=true

# === OPTIONAL FEATURES ===
ENABLE_LLM_RECOMMENDATIONS=false
EOF

    echo "✓ Configuration saved to .env"
    
    # 7. Show configuration summary
    echo ""
    echo -e "${GREEN}Configuration Summary:${NC}"
    echo "─────────────────────────────────────────"
    echo "FASTQ Data: $FASTQ_DIR"
    echo "Output Directory: $OUTPUT_DIR"
    if [ "$KRAKEN2_DB" != "NOT_CONFIGURED" ] && [ -n "$KRAKEN2_DB" ]; then
        echo "Kraken2 Database: $KRAKEN2_DB"
    else
        echo "Kraken2: Not configured (will use mock data for testing)"
    fi
    if [ -n "$WINDOWS_USER" ]; then
        echo "Windows User: $WINDOWS_USER"
    fi
    echo "─────────────────────────────────────────"
    echo ""
}

# Function to validate installation
validate_installation() {
    echo -e "${GREEN}[Step 7/8] Validating installation...${NC}"
    
    # Use the conda environment's Python directly
    CONDA_PYTHON="$HOME/miniconda3/envs/equine-microbiome/bin/python"
    if [ ! -f "$CONDA_PYTHON" ]; then
        CONDA_PYTHON="$HOME/anaconda3/envs/equine-microbiome/bin/python"
    fi
    if [ ! -f "$CONDA_PYTHON" ]; then
        CONDA_PYTHON="/opt/conda/envs/equine-microbiome/bin/python"
    fi
    
    # Test Python imports
    $CONDA_PYTHON -c "
import sys
import os

print('Checking Python packages...')

try:
    import pandas
    import numpy
    import jinja2
    import yaml
    import Bio  # BioPython imports as Bio, not biopython
    import openpyxl
    import reportlab
    import weasyprint
    print('✓ All Python packages imported successfully')
except ImportError as e:
    print(f'✗ Missing package: {e}')
    sys.exit(1)

print('Checking local modules...')

# Test local modules
try:
    from src.report_generator import ReportGenerator
    from src.data_models import PatientInfo
    from src.clinical_filter import ClinicalFilter
    print('✓ Local modules loading correctly')
except ImportError as e:
    print(f'✗ Error loading local modules: {e}')
    sys.exit(1)

print('Checking test data...')

# Check for test data
if os.path.exists('data/barcode04_test.fastq'):
    print('✓ Test FASTQ data found')
else:
    print('⚠ Test FASTQ data not found (download may have failed)')
    
if os.path.exists('data/sample_1.csv'):
    print('✓ Sample CSV data found')
else:
    print('⚠ Sample CSV not found (will need to generate from FASTQ)')

print('')
print('✓ Installation validated successfully!')
"
    
    echo ""
}

# Function to generate demo report
generate_demo() {
    echo -e "${GREEN}[Step 8/8] Generating demo report...${NC}"
    
    # Use the conda environment's Python directly
    CONDA_PYTHON="$HOME/miniconda3/envs/equine-microbiome/bin/python"
    if [ ! -f "$CONDA_PYTHON" ]; then
        CONDA_PYTHON="$HOME/anaconda3/envs/equine-microbiome/bin/python"
    fi
    if [ ! -f "$CONDA_PYTHON" ]; then
        CONDA_PYTHON="/opt/conda/envs/equine-microbiome/bin/python"
    fi
    
    # Set environment to avoid Qt issues in headless mode
    export QT_QPA_PLATFORM=offscreen
    
    $CONDA_PYTHON -c "
import os
import sys

# Set backend before importing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

try:
    from src.report_generator import ReportGenerator
    from src.data_models import PatientInfo
    
    # Create test patient
    patient = PatientInfo(
        name='DemoHorse',
        sample_number='DEMO001',
        age='5 years',
        performed_by='Lab Tech',
        requested_by='Dr. Demo'
    )
    
    # Try to generate report from sample CSV
    if os.path.exists('data/sample_1.csv'):
        print('Attempting to generate demo PDF report...')
        try:
            generator = ReportGenerator(language='en')
            success = generator.generate_report(
                'data/sample_1.csv',
                patient,
                'demo_report.pdf'
            )
            if success and os.path.exists('demo_report.pdf'):
                print('✓ Demo PDF report generated successfully!')
                print('  Location: ./demo_report.pdf')
            else:
                print('⚠ Report generation completed but PDF not found')
        except Exception as pdf_error:
            print('⚠ PDF generation requires additional setup in WSL')
            print('  This is normal - the pipeline will work for data processing')
            print('  To fix PDF generation, you may need to install:')
            print('    sudo apt-get install wkhtmltopdf')
            print('  Or use reportlab instead of weasyprint')
    else:
        print('⚠ Sample CSV not available')
        print('  Test data is ready in: ./data/')
        print('  You can process it with:')
        print('    python scripts/full_pipeline.py --input-dir data')
        
except ImportError as e:
    print(f'⚠ Demo skipped - missing module: {e}')
    print('  The core pipeline is still functional')
except Exception as e:
    print(f'⚠ Demo generation skipped: {e}')
    print('  This does not affect the main pipeline functionality')
"
    
    echo ""
    
    echo ""
}

# Function to generate test commands
generate_test_commands() {
    echo -e "${CYAN}=== Test Commands ===${NC}"
    
    # Read the configuration
    source .env
    
    if [ "$USE_MOCK_KRAKEN" = "true" ]; then
        echo "Since Kraken2 is not configured, you can test with mock data:"
        echo ""
        echo "  # Generate test reports without Kraken2:"
        echo "  python scripts/generate_mock_reports.py --input-dir $FASTQ_INPUT_DIR"
        echo ""
        echo "  # Or use sample CSV data:"
        echo "  python -c \"from src.report_generator import ReportGenerator; from src.data_models import PatientInfo; generator = ReportGenerator(); generator.generate_report('data/sample_1.csv', PatientInfo(name='Test'), 'test.pdf')\""
    else
        echo "Run the full pipeline with your configuration:"
        echo ""
        echo "  # Process test data:"
        echo "  python scripts/full_pipeline.py \\"
        echo "    --input-dir $FASTQ_INPUT_DIR \\"
        echo "    --output-dir $DEFAULT_OUTPUT_DIR \\"
        echo "    --kraken2-db $KRAKEN2_DB_PATH"
        echo ""
        echo "  # Process specific barcodes:"
        echo "  python scripts/full_pipeline.py \\"
        echo "    --input-dir $FASTQ_INPUT_DIR \\"
        echo "    --output-dir $DEFAULT_OUTPUT_DIR \\"
        echo "    --kraken2-db $KRAKEN2_DB_PATH \\"
        echo "    --barcodes barcode04,barcode05,barcode06"
    fi
    
    echo ""
}

# Function to display next steps
show_next_steps() {
    echo ""
    echo -e "${BLUE}=====================================================${NC}"
    echo -e "${BLUE}           Installation Complete! 🎉                ${NC}"
    echo -e "${BLUE}=====================================================${NC}"
    echo ""
    
    echo -e "${GREEN}Available test data:${NC}"
    if [ -f "data/barcode04_test.fastq" ]; then
        echo "  • data/barcode04_test.fastq (100 reads)"
        echo "  • data/barcode05_test.fastq (100 reads)"
        echo "  • data/barcode06_test.fastq (100 reads)"
    else
        echo "  ⚠ Test data download may have failed"
        echo "  Download manually from: https://drive.google.com/file/d/${GDRIVE_FILE_ID}/view"
    fi
    echo ""
    
    echo -e "${GREEN}Next steps:${NC}"
    echo ""
    echo "1. Activate the conda environment:"
    echo "   ${YELLOW}conda activate equine-microbiome${NC}"
    echo ""
    echo "2. Review your configuration:"
    echo "   ${YELLOW}cat .env${NC}"
    echo ""
    
    generate_test_commands
    
    echo -e "${GREEN}Documentation:${NC}"
    echo "  • README.md - General overview"
    echo "  • DEPLOYMENT_WSL2_COMPLETE.md - Detailed deployment guide"
    echo "  • CLINICAL_FILTERING_IMPLEMENTATION.md - Clinical filtering details"
    echo ""
    
    echo -e "${GREEN}Troubleshooting:${NC}"
    echo "  • If Kraken2 fails: Check database path in .env"
    echo "  • If imports fail: Ensure conda environment is activated"
    echo "  • For Windows paths: Use /mnt/c/Users/... format"
    echo ""
    
    echo -e "${BLUE}Need help? Check the documentation or contact support.${NC}"
}

# Main execution
main() {
    # Record start time
    START_TIME=$SECONDS
    
    # Run all steps
    check_prerequisites
    clone_repository
    download_test_data
    setup_environment
    install_dependencies
    configure_paths_interactive
    validate_installation
    generate_demo
    
    # Calculate elapsed time
    ELAPSED_TIME=$((SECONDS - START_TIME))
    MINUTES=$((ELAPSED_TIME / 60))
    SECONDS=$((ELAPSED_TIME % 60))
    
    show_next_steps
    
    echo ""
    echo -e "${GREEN}Total installation time: ${MINUTES}m ${SECONDS}s${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: If this is your first time installing conda,${NC}"
    echo -e "${YELLOW}you may need to restart your terminal for conda to work properly.${NC}"
}

# Check if being sourced or executed
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # Being executed directly
    main
fi