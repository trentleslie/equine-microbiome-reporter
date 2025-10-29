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
echo -e "${BLUE}   Equine Microbiome Reporter - Multilingual Demo       ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo "This demo generates clean, modern 5-page reports"
echo "in multiple languages using Google Translate API."
echo ""
echo "Features:"
echo "  • Professional PDF reports with charts"
echo "  • Multi-language support (English, Polish, Japanese)"
echo "  • Preserves scientific terminology accuracy"
echo "  • Free translation service (no API key required)"
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

# Check conda environment and find Python path dynamically
if conda info --envs | grep -q equine-microbiome; then
    echo -e "${GREEN}✓ Conda environment 'equine-microbiome' found${NC}"
    # Get the conda base path dynamically
    CONDA_BASE=$(conda info --base)
    PYTHON_CMD="${CONDA_BASE}/envs/equine-microbiome/bin/python"

    # If the Python binary doesn't exist at that path, try to find it
    if [ ! -f "$PYTHON_CMD" ]; then
        # Try to activate and find python
        PYTHON_CMD=$(conda run -n equine-microbiome which python 2>/dev/null || echo "python")
    fi
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

# Check WeasyPrint/cffi dependencies
echo "Checking PDF generation libraries..."
$PYTHON_CMD -c "from weasyprint import HTML" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ WeasyPrint import failed (cffi/libffi issue)${NC}"
    echo ""
    echo "This is usually caused by a cffi version mismatch."
    echo "To fix, run:"
    echo -e "  ${CYAN}conda activate equine-microbiome${NC}"
    echo -e "  ${CYAN}pip install --force-reinstall cffi${NC}"
    echo ""
    echo "Or update your environment:"
    echo -e "  ${CYAN}conda env update -f environment.yml --prune${NC}"
    echo ""
    echo "See docs/ENVIRONMENT_TROUBLESHOOTING.md for more help"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ PDF generation libraries available${NC}"

pause

# Ask about translation
echo -e "${BLUE}═══ Step 2: Translation Options ═══${NC}"
echo ""
echo "Would you like to generate translated reports?"
echo "Available languages:"
echo "  en - English (default)"
echo "  pl - Polish"
echo "  ja - Japanese"
echo ""
echo -e "${CYAN}Enter language codes (comma-separated, or press Enter for English only):${NC}"
read -r LANGUAGES

# Process language input
if [ -z "$LANGUAGES" ]; then
    LANGUAGES="en"
    echo -e "${GREEN}✓ Using English only${NC}"
else
    echo -e "${GREEN}✓ Selected languages: $LANGUAGES${NC}"

    # Check for translation dependencies if non-English language requested
    if [[ "$LANGUAGES" != "en" ]]; then
        echo ""
        echo "Checking translation dependencies..."
        $PYTHON_CMD -c "import deep_translator, googletrans, translatepy" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Translation dependencies not found${NC}"
            echo ""
            echo "Translation requires these packages:"
            echo "  - deep-translator"
            echo "  - googletrans"
            echo "  - translatepy"
            echo ""
            echo "To install them, run:"
            echo -e "  ${CYAN}conda activate equine-microbiome${NC}"
            echo -e "  ${CYAN}pip install deep-translator googletrans translatepy${NC}"
            echo ""
            echo "Or update your environment:"
            echo -e "  ${CYAN}conda env update -f environment.yml --prune${NC}"
            echo ""
            echo "See docs/TRANSLATION_INSTALL.md for more help"
            echo ""
            exit 1
        fi
        echo -e "${GREEN}✓ Translation dependencies available${NC}"
    fi
fi
pause

# Create output directory
OUTPUT_DIR="demo_output_$(date +%Y%m%d_%H%M%S)"
echo -e "${BLUE}═══ Step 3: Creating Output Directory ═══${NC}"
echo ""
echo -e "${CYAN}Creating: $OUTPUT_DIR/${NC}"
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}✓ Directory created${NC}"
pause

# Process the data
echo -e "${BLUE}═══ Step 4: Processing Sample Data ═══${NC}"
echo ""
echo -e "${CYAN}Input: $SAMPLE_CSV${NC}"
echo -e "${CYAN}This will:${NC}"
echo "  1. Load and process CSV data"
echo "  2. Calculate dysbiosis index"
echo "  3. Generate professional charts"
echo "  4. Create clean 4-page PDF report"
echo ""
pause

# Run the clean report generator for each language
echo -e "${BOLD}Running clean report generator...${NC}"
echo ""

# Convert comma-separated languages to array
IFS=',' read -ra LANG_ARRAY <<< "$LANGUAGES"

# Process each language
for LANG in "${LANG_ARRAY[@]}"; do
    # Trim whitespace
    LANG=$(echo "$LANG" | xargs)

    # Get language name for display
    case $LANG in
        en) LANG_NAME="English" ;;
        pl) LANG_NAME="Polish" ;;
        ja) LANG_NAME="Japanese" ;;
        *) LANG_NAME="$LANG" ;;
    esac

    echo -e "${CYAN}Generating $LANG_NAME report...${NC}"

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
output_path = Path("$OUTPUT_DIR/clean_report_$LANG.pdf")
success = generate_clean_report("$SAMPLE_CSV", patient, output_path, language="$LANG")

if success:
    print("✅ $LANG_NAME report generated successfully!")
else:
    print("❌ $LANG_NAME report generation failed")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $LANG_NAME report complete${NC}"
    else
        echo -e "${RED}✗ $LANG_NAME report failed${NC}"
    fi
    echo ""
done

echo ""
echo -e "${GREEN}✓ All reports generated successfully!${NC}"

pause

# Display results
echo -e "${BLUE}═══ Step 5: Results ═══${NC}"
echo ""
echo -e "${GREEN}Success! Your reports have been generated.${NC}"
echo ""
echo "Output files:"

# List all generated reports
for LANG in "${LANG_ARRAY[@]}"; do
    LANG=$(echo "$LANG" | xargs)
    case $LANG in
        en) LANG_NAME="English" ;;
        pl) LANG_NAME="Polish" ;;
        ja) LANG_NAME="Japanese" ;;
        *) LANG_NAME="$LANG" ;;
    esac

    if [ -f "$OUTPUT_DIR/clean_report_$LANG.pdf" ]; then
        echo -e "  ${CYAN}$OUTPUT_DIR/clean_report_$LANG.pdf${NC} - $LANG_NAME (4-page report)"
        echo -e "  ${CYAN}$OUTPUT_DIR/clean_report_$LANG.html${NC} - $LANG_NAME (HTML version)"
    fi
done

echo ""
echo "Each PDF contains:"
echo "  • Page 1: Sequencing Results & Dysbiosis Index"
echo "  • Page 2: Phylum Distribution Analysis"
echo "  • Page 3: Clinical Interpretation"
echo "  • Page 4: Summary & Management Guidelines"
echo "  • Page 5: Complete Species List"
echo ""
echo "To combine with your title page:"
echo -e "  ${BOLD}pdftk title_page.pdf $OUTPUT_DIR/clean_report_[LANG].pdf cat output final_report.pdf${NC}"
echo ""

# Open results if on WSL
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "${YELLOW}Would you like to open the PDFs? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        for LANG in "${LANG_ARRAY[@]}"; do
            LANG=$(echo "$LANG" | xargs)
            PDF_PATH="$OUTPUT_DIR/clean_report_$LANG.pdf"
            if [ -f "$PDF_PATH" ]; then
                explorer.exe "$PDF_PATH" 2>/dev/null &
            fi
        done
        echo "Opening PDFs in default viewer..."
    fi
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Demo complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"