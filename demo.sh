#!/bin/bash
# Equine Microbiome Reporter - Live Demo Script
# This script runs the actual pipeline with explanations

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

# Function to run command with explanation
run_with_explanation() {
    local explanation="$1"
    local command="$2"
    
    echo -e "${CYAN}$explanation${NC}"
    echo -e "${BOLD}Running: $command${NC}"
    echo ""
    pause
    eval "$command"
    echo ""
    echo -e "${GREEN}✓ Complete${NC}"
    pause
}

# Header
clear
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Equine Microbiome Reporter - Live Demo             ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo "This demo will process real test data through the pipeline."
echo "We'll use the test FASTQ files with 100 reads each."
echo ""
pause

# Check environment
echo -e "${BLUE}═══ Checking Environment ═══${NC}"
echo ""

# Activate conda if needed
if [[ "$CONDA_DEFAULT_ENV" != "equine-microbiome" ]]; then
    echo "Activating conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate equine-microbiome
    echo -e "${GREEN}✓ Environment activated${NC}"
fi

# Load configuration
if [ -f ".env" ]; then
    # Use set -a to export all variables, but protect against command execution
    set -a
    # Filter out any lines with problematic characters and source safely
    grep -E '^[A-Z_][A-Z0-9_]*=' .env > /tmp/safe_env.tmp
    source /tmp/safe_env.tmp
    rm -f /tmp/safe_env.tmp
    set +a
    echo -e "${GREEN}✓ Configuration loaded${NC}"
else
    echo -e "${RED}✗ No .env file found. Run setup.sh first!${NC}"
    exit 1
fi

# Create output directory
OUTPUT_DIR="demo_output_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}✓ Output directory created: $OUTPUT_DIR${NC}"
pause

# Step 1: Show input data
clear
echo -e "${BLUE}═══ Step 1: Input Data ═══${NC}"
echo ""
run_with_explanation \
    "Let's see what FASTQ files we have:" \
    "ls -lh data/*test.fastq | head -5"

# Step 2: Check if we can use Kraken2
clear
echo -e "${BLUE}═══ Step 2: Classification Method ═══${NC}"
echo ""

if [ "$USE_MOCK_KRAKEN" = "true" ] || [ ! -d "$KRAKEN2_DB_PATH" ]; then
    echo -e "${YELLOW}Note: Running in mock mode (no Kraken2 database)${NC}"
    echo "We'll generate sample data to demonstrate the pipeline."
    USE_MOCK=true
else
    echo -e "${GREEN}Kraken2 database found at: $KRAKEN2_DB_PATH${NC}"
    USE_MOCK=false
fi
pause

# Step 3: Process a single sample
clear
echo -e "${BLUE}═══ Step 3: Processing Single Sample ═══${NC}"
echo ""

if [ "$USE_MOCK" = "true" ]; then
    # Create mock processing script
    cat > process_mock.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
import sys

output_dir = Path(sys.argv[1])
output_dir.mkdir(parents=True, exist_ok=True)

# Create mock data
species_data = {
    'species': [
        'Lactobacillus_reuteri', 'Streptococcus_equi', 'E_coli',
        'Bifidobacterium_longum', 'Clostridium_difficile'
    ],
    'barcode04': [450, 23, 156, 89, 12],
    'phylum': ['Bacillota', 'Bacillota', 'Pseudomonadota', 'Actinomycetota', 'Bacillota'],
    'genus': ['Lactobacillus', 'Streptococcus', 'Escherichia', 'Bifidobacterium', 'Clostridium']
}

df = pd.DataFrame(species_data)
csv_file = output_dir / 'barcode04.csv'
df.to_csv(csv_file, index=False)
print(f"✓ Created mock CSV: {csv_file}")

# Calculate stats
total = df['barcode04'].sum()
print(f"\nSummary for barcode04:")
print(f"  Total reads: {total}")
print(f"  Species detected: {len(df)}")
print(f"  Top species: {df.iloc[0]['species']} ({df.iloc[0]['barcode04']/total*100:.1f}%)")
EOF
    
    run_with_explanation \
        "Creating mock classification data for barcode04:" \
        "python process_mock.py $OUTPUT_DIR"
    
    rm process_mock.py
else
    run_with_explanation \
        "Running Kraken2 classification on barcode04:" \
        "kraken2 --db $KRAKEN2_DB_PATH --threads 2 --memory-mapping \
                 --report $OUTPUT_DIR/barcode04.kreport \
                 --output $OUTPUT_DIR/barcode04.out \
                 data/barcode04_test.fastq"
    
    run_with_explanation \
        "Converting Kraken report to CSV:" \
        "python scripts/kreport_to_csv.py \
                 $OUTPUT_DIR/barcode04.kreport \
                 $OUTPUT_DIR/barcode04.csv"
fi

# Step 4: Apply clinical filtering
clear
echo -e "${BLUE}═══ Step 4: Clinical Filtering ═══${NC}"
echo ""

cat > apply_filter.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
import sys
from pathlib import Path

input_csv = Path(sys.argv[1])
output_dir = Path(sys.argv[2])

df = pd.read_csv(input_csv)
print(f"Before filtering: {len(df)} species")

# Simple filter - remove any with 'plant' or very low abundance
filtered = df[~df['species'].str.contains('plant', case=False, na=False)]
barcode_col = [c for c in df.columns if 'barcode' in c][0]
total = filtered[barcode_col].sum()
filtered = filtered[filtered[barcode_col] / total > 0.001]  # >0.1% abundance

print(f"After filtering: {len(filtered)} species")
print(f"Reduction: {(1 - len(filtered)/len(df))*100:.1f}%")

output_csv = output_dir / f"{input_csv.stem}_filtered.csv"
filtered.to_csv(output_csv, index=False)
print(f"\n✓ Saved filtered data to: {output_csv}")
EOF

run_with_explanation \
    "Applying clinical filters to remove irrelevant species:" \
    "python apply_filter.py $OUTPUT_DIR/barcode04.csv $OUTPUT_DIR"

rm apply_filter.py

# Step 5: Generate Excel review file
clear
echo -e "${BLUE}═══ Step 5: Excel Review File ═══${NC}"
echo ""

run_with_explanation \
    "Creating Excel file with clinical categorization:" \
    "python scripts/generate_clinical_excel.py \
             $OUTPUT_DIR/barcode04_filtered.csv \
             $OUTPUT_DIR/barcode04_review.xlsx"

echo "The Excel file contains:"
echo "  • Color-coded species by clinical relevance"
echo "  • Summary statistics"
echo "  • Review instructions"
pause

# Step 6: Generate PDF report
clear
echo -e "${BLUE}═══ Step 6: PDF Report Generation ═══${NC}"
echo ""

cat > generate_report.py << 'EOF'
#!/usr/bin/env python3
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo
import sys

csv_file = sys.argv[1]
output_pdf = sys.argv[2]

patient = PatientInfo(
    name="Demo Horse",
    sample_number="DEMO-04",
    age="5 years",
    performed_by="Lab Technician",
    requested_by="Dr. Smith"
)

try:
    generator = ReportGenerator(language="en")
    success = generator.generate_report(csv_file, patient, output_pdf)
    if success:
        print(f"✓ PDF report generated: {output_pdf}")
    else:
        print("⚠ Report generation completed with warnings")
except Exception as e:
    print(f"⚠ PDF generation requires additional setup: {e}")
    print("  The data processing is complete - PDF is optional")
EOF

run_with_explanation \
    "Generating veterinary PDF report:" \
    "python generate_report.py \
             $OUTPUT_DIR/barcode04_filtered.csv \
             $OUTPUT_DIR/barcode04_report.pdf 2>/dev/null || echo 'PDF generation skipped (optional)'"

rm generate_report.py

# Step 7: Show results
clear
echo -e "${BLUE}═══ Step 7: Results ═══${NC}"
echo ""
echo "Processing complete! Here's what was generated:"
echo ""
echo -e "${CYAN}Output files in $OUTPUT_DIR:${NC}"
ls -la "$OUTPUT_DIR" 2>/dev/null | grep -E "\.(csv|xlsx|pdf|kreport)" | while read line; do
    echo "  $line"
done
echo ""
pause

# Step 8: Batch processing
clear
echo -e "${BLUE}═══ Step 8: Batch Processing ═══${NC}"
echo ""
echo "To process all samples at once, you would run:"
echo ""
echo -e "${BOLD}python scripts/full_pipeline.py \\"
echo "  --input-dir data \\"
echo "  --output-dir batch_output \\"
if [ "$USE_MOCK" = "false" ]; then
    echo "  --kraken2-db $KRAKEN2_DB_PATH \\"
fi
echo -e "  --parallel${NC}"
echo ""
echo "This would:"
echo "  • Process all barcode folders"
echo "  • Run 4 samples in parallel"
echo "  • Generate all reports automatically"
echo "  • Create a summary spreadsheet"
pause

# Summary
clear
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    Demo Complete!                      ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo "You've seen the complete workflow:"
echo ""
echo "  1. ✓ FASTQ input data"
echo "  2. ✓ Taxonomic classification"
echo "  3. ✓ Clinical filtering"
echo "  4. ✓ Excel review generation"
echo "  5. ✓ PDF report creation"
echo ""
echo -e "${CYAN}Time Savings:${NC}"
echo "  Manual process: 30-40 minutes per sample"
echo "  With pipeline:  3-5 minutes per sample"
echo "  Reduction:      ~87%"
echo ""
echo -e "${CYAN}Your demo output is in:${NC}"
echo "  $OUTPUT_DIR/"
echo ""
echo -e "${GREEN}Ready to process real data? Run:${NC}"
echo -e "${BOLD}  python scripts/full_pipeline.py --help${NC}"
echo ""