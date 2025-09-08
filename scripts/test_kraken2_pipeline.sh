#!/bin/bash
# Test script for Kraken2 pipeline integration with Equine Microbiome Reporter

set -e  # Exit on error

echo "==========================================="
echo "Kraken2 Pipeline Test Script"
echo "==========================================="
echo ""

# Configuration
KRAKEN2_DB_DIR="$HOME/kraken2_db"
TEST_FASTQ_DIR="test_fastq"
OUTPUT_DIR="kraken2_output"
REPORT_OUTPUT_DIR="report_output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "equine-microbiome" ]]; then
    print_warning "Activating equine-microbiome conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate equine-microbiome
fi

# Check if Kraken2 is installed
if ! command -v kraken2 &> /dev/null; then
    print_error "Kraken2 is not installed or not in PATH"
    exit 1
fi
print_status "Kraken2 version: $(kraken2 --version | head -n1)"

# Check if databases exist
print_status "Checking Kraken2 databases..."
if [ -d "$KRAKEN2_DB_DIR/k2_pluspfp_16gb" ]; then
    DB_PATH="$KRAKEN2_DB_DIR/k2_pluspfp_16gb"
    print_status "Using PlusPFP-16 database at: $DB_PATH"
elif [ -f "$KRAKEN2_DB_DIR/hash.k2d" ]; then
    DB_PATH="$KRAKEN2_DB_DIR"
    print_status "Using database at: $DB_PATH"
else
    print_error "No Kraken2 database found in $KRAKEN2_DB_DIR"
    print_error "Please ensure the database is downloaded and extracted"
    exit 1
fi

# Create output directories
print_status "Creating output directories..."
mkdir -p "$OUTPUT_DIR"
mkdir -p "$REPORT_OUTPUT_DIR"

# Test 1: Run Kraken2 on test FASTQ files
print_status "Running Kraken2 classification on test samples..."
echo ""

for fastq_file in $TEST_FASTQ_DIR/*.fastq; do
    if [ -f "$fastq_file" ]; then
        basename=$(basename "$fastq_file" .fastq)
        print_status "Processing $basename..."
        
        # Run Kraken2
        kraken2 --db "$DB_PATH" \
                --threads 4 \
                --output "$OUTPUT_DIR/${basename}.kraken" \
                --report "$OUTPUT_DIR/${basename}.kreport" \
                --use-names \
                "$fastq_file" 2>&1 | tee "$OUTPUT_DIR/${basename}.log"
        
        # Check if successful
        if [ -f "$OUTPUT_DIR/${basename}.kreport" ]; then
            print_status "✅ Successfully generated report: ${basename}.kreport"
            
            # Show summary statistics
            echo "  Summary statistics:"
            echo -n "    Total classified reads: "
            grep -c "^C" "$OUTPUT_DIR/${basename}.kraken" 2>/dev/null || echo "0"
            echo -n "    Total unclassified reads: "
            grep -c "^U" "$OUTPUT_DIR/${basename}.kraken" 2>/dev/null || echo "0"
            
            # Show top 5 species
            echo "  Top 5 species detected:"
            awk '$4=="S" {printf "    - %s: %.2f%%\n", $6, $1}' "$OUTPUT_DIR/${basename}.kreport" | head -5
        else
            print_error "Failed to generate report for $basename"
        fi
        echo ""
    fi
done

# Test 2: Convert Kraken2 reports to CSV
print_status "Converting Kraken2 reports to CSV format..."
echo ""

for kreport_file in $OUTPUT_DIR/*.kreport; do
    if [ -f "$kreport_file" ]; then
        basename=$(basename "$kreport_file" .kreport)
        csv_file="$OUTPUT_DIR/${basename}.csv"
        
        print_status "Converting $basename.kreport to CSV..."
        python src/kraken2_to_csv.py "$kreport_file" -o "$csv_file" -b 1
        
        if [ -f "$csv_file" ]; then
            print_status "✅ Successfully created: ${basename}.csv"
            echo "  First 5 lines of CSV:"
            head -5 "$csv_file" | sed 's/^/    /'
        else
            print_error "Failed to convert $basename.kreport"
        fi
        echo ""
    fi
done

# Test 3: Merge multiple samples (if more than one)
kreport_count=$(ls -1 $OUTPUT_DIR/*.kreport 2>/dev/null | wc -l)
if [ "$kreport_count" -gt 1 ]; then
    print_status "Merging multiple Kraken2 reports..."
    python src/kraken2_to_csv.py $OUTPUT_DIR/*.kreport -o "$OUTPUT_DIR/merged_samples.csv"
    
    if [ -f "$OUTPUT_DIR/merged_samples.csv" ]; then
        print_status "✅ Successfully created merged CSV"
        echo "  Merged CSV structure:"
        head -1 "$OUTPUT_DIR/merged_samples.csv" | sed 's/^/    /'
    fi
    echo ""
fi

# Test 4: Generate PDF reports from CSV files
print_status "Generating PDF reports from CSV files..."
echo ""

# Create a Python script to test report generation
cat > "$OUTPUT_DIR/test_report_generation.py" << 'EOF'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.report_generator import ReportGenerator
from src.data_models import PatientInfo
import glob

# Find all CSV files
csv_files = glob.glob("kraken2_output/*.csv")

for csv_file in csv_files:
    basename = os.path.basename(csv_file).replace('.csv', '')
    
    # Skip merged file for individual reports
    if basename == 'merged_samples':
        continue
    
    print(f"Generating report for {basename}...")
    
    # Create patient info
    patient = PatientInfo(
        name=f"Test Horse {basename}",
        age="5 years",
        sample_number=basename,
        performed_by="Laboratory Staff",
        requested_by="Test Veterinarian"
    )
    
    # Generate report
    generator = ReportGenerator(language='en')
    output_pdf = f"report_output/{basename}_report.pdf"
    
    try:
        success = generator.generate_report(csv_file, patient, output_pdf)
        if success:
            print(f"✅ Successfully generated: {output_pdf}")
        else:
            print(f"❌ Failed to generate report for {basename}")
    except Exception as e:
        print(f"❌ Error generating report: {e}")
    
    print()
EOF

python "$OUTPUT_DIR/test_report_generation.py"

# Test 5: Test the complete pipeline integration
print_status "Testing complete FASTQ-to-PDF pipeline..."
echo ""

cat > "$OUTPUT_DIR/test_full_pipeline.py" << 'EOF'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline_integrator import MicrobiomePipelineIntegrator
from src.data_models import PatientInfo
import glob

# Test with first FASTQ file
fastq_files = glob.glob("test_fastq/*.fastq")
if fastq_files:
    fastq_file = fastq_files[0]
    print(f"Testing full pipeline with: {fastq_file}")
    
    patient = PatientInfo(
        name="Pipeline Test Horse",
        age="6 years",
        sample_number="PIPE001",
        performed_by="Pipeline Tester",
        requested_by="Dr. Test"
    )
    
    # Initialize pipeline
    pipeline = MicrobiomePipelineIntegrator(
        kraken2_db=os.path.expanduser("~/kraken2_db/k2_pluspfp_16gb"),
        output_dir="pipeline_output"
    )
    
    # Process sample
    try:
        results = pipeline.process_sample(fastq_file, patient, language='en')
        
        if results['success']:
            print("✅ Pipeline completed successfully!")
            print(f"   Report: {results['report_path']}")
            print(f"   CSV: {results['csv_path']}")
            print(f"   Kraken2 report: {results['kraken2_report']}")
        else:
            print(f"❌ Pipeline failed: {results.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
else:
    print("No FASTQ files found for testing")
EOF

python "$OUTPUT_DIR/test_full_pipeline.py"

# Summary
echo ""
echo "==========================================="
echo "Test Summary"
echo "==========================================="

# Count results
kreport_count=$(ls -1 $OUTPUT_DIR/*.kreport 2>/dev/null | wc -l)
csv_count=$(ls -1 $OUTPUT_DIR/*.csv 2>/dev/null | wc -l)
pdf_count=$(ls -1 $REPORT_OUTPUT_DIR/*.pdf 2>/dev/null | wc -l)

print_status "Results:"
echo "  - Kraken2 reports generated: $kreport_count"
echo "  - CSV files created: $csv_count"
echo "  - PDF reports generated: $pdf_count"
echo ""

# Check disk usage
print_status "Disk usage:"
if [ -d "$KRAKEN2_DB_DIR" ]; then
    echo -n "  - Database size: "
    du -sh "$KRAKEN2_DB_DIR" 2>/dev/null | cut -f1
fi
echo -n "  - Output size: "
du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1
echo ""

print_status "Test complete! Check the output directories for results:"
echo "  - Kraken2 outputs: $OUTPUT_DIR/"
echo "  - PDF reports: $REPORT_OUTPUT_DIR/"
echo "  - Pipeline outputs: pipeline_output/"