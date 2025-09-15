#!/bin/bash
# Equine Microbiome Reporter - Clean Demo Script
# Uses the new clean template system

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Function to pause
pause() {
    echo ""
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read -r
}

# Header
clear
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Equine Microbiome Reporter - Clean Demo            ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo "This demo generates a clean, modern 4-page report"
echo "using the simplified template system."
echo ""
pause

# Check environment
echo -e "${BLUE}═══ Step 1: Checking Environment ═══${NC}"
echo ""

# Load environment if exists
if [ -f .env ]; then
    echo -e "${GREEN}✓ Loading configuration from .env${NC}"
    # Parse .env file safely
    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^#.*$ ]] && [[ -n "$key" ]]; then
            # Remove inline comments and trim whitespace
            value="${value%%#*}"
            value="${value%"${value##*[![:space:]]}"}"
            export "$key=$value" 2>/dev/null
        fi
    done < .env
else
    echo -e "${YELLOW}⚠ No .env file found, using defaults${NC}"
fi

# Check conda environment
if conda info --envs | grep -q equine-microbiome; then
    echo -e "${GREEN}✓ Conda environment 'equine-microbiome' found${NC}"
    PYTHON_CMD="/home/trent/miniconda3/envs/equine-microbiome/bin/python"
else
    echo -e "${YELLOW}⚠ Using system Python${NC}"
    PYTHON_CMD="python3"
fi

# Check for sample data
if [ -f "data/sample_1.csv" ]; then
    echo -e "${GREEN}✓ Sample data found${NC}"
    SAMPLE_CSV="data/sample_1.csv"
elif [ -f "data/barcode04.csv" ]; then
    echo -e "${GREEN}✓ Barcode data found${NC}"
    SAMPLE_CSV="data/barcode04.csv"
else
    echo -e "${RED}✗ No sample data found${NC}"
    echo "Please run the pipeline first to generate sample data."
    exit 1
fi

pause

# Create output directory
OUTPUT_DIR="demo_output_$(date +%Y%m%d_%H%M%S)"
echo -e "${BLUE}═══ Step 2: Creating Output Directory ═══${NC}"
echo ""
echo -e "${CYAN}Creating: $OUTPUT_DIR/${NC}"
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}✓ Directory created${NC}"
pause

# Process the data
echo -e "${BLUE}═══ Step 3: Processing Sample Data ═══${NC}"
echo ""
echo -e "${CYAN}Input: $SAMPLE_CSV${NC}"
echo -e "${CYAN}This will:${NC}"
echo "  1. Load and process CSV data"
echo "  2. Calculate dysbiosis index"
echo "  3. Generate professional charts"
echo "  4. Create clean 4-page PDF report"
echo ""
pause

# Run the clean report generator
echo -e "${BOLD}Running clean report generator...${NC}"
echo ""

QT_QPA_PLATFORM=offscreen $PYTHON_CMD << EOF
import sys
from pathlib import Path
sys.path.append('.')

from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

# Sample patient info
patient = PatientInfo(
    name="Demo Horse",
    age="10 years",
    species="Equine",
    sample_number="DEMO-001",
    date_received="$(date +%Y-%m-%d)",
    date_analyzed="$(date +%Y-%m-%d)",
    performed_by="Demo Lab",
    requested_by="Demo Veterinarian"
)

# Generate report
output_path = Path("$OUTPUT_DIR/clean_report.pdf")
success = generate_clean_report("$SAMPLE_CSV", patient, output_path)

if success:
    print("✅ Report generated successfully!")
else:
    print("❌ Report generation failed")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Report generation complete!${NC}"
else
    echo ""
    echo -e "${RED}✗ Report generation failed${NC}"
    exit 1
fi

pause

# Display results
echo -e "${BLUE}═══ Step 4: Results ═══${NC}"
echo ""
echo -e "${GREEN}Success! Your report has been generated.${NC}"
echo ""
echo "Output files:"
echo -e "  ${CYAN}$OUTPUT_DIR/clean_report.pdf${NC} - 4-page report (no title)"
echo -e "  ${CYAN}$OUTPUT_DIR/clean_report.html${NC} - HTML version"
echo ""
echo "The PDF contains:"
echo "  • Page 1: Sequencing Results & Dysbiosis Index"
echo "  • Page 2: Phylum Distribution Analysis"
echo "  • Page 3: Clinical Interpretation"
echo "  • Page 4: Summary & Management Guidelines"
echo ""
echo "To combine with your title page:"
echo -e "  ${BOLD}pdftk title_page.pdf $OUTPUT_DIR/clean_report.pdf cat output final_report.pdf${NC}"
echo ""

# Open results if on WSL
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "${YELLOW}Would you like to open the PDF? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        explorer.exe "$OUTPUT_DIR/clean_report.pdf" 2>/dev/null || echo "Please open manually: $OUTPUT_DIR/clean_report.pdf"
    fi
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Demo complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"