#!/bin/bash
# Simple wrapper script to run the pipeline with conda environment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  HippoVet+ Equine Microbiome Pipeline Runner${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${YELLOW}⚠️  Conda not found. Please install Miniconda first.${NC}"
    exit 1
fi

# Activate conda environment
echo "Activating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh || source /opt/conda/etc/profile.d/conda.sh || source /usr/local/conda/etc/profile.d/conda.sh
conda activate equine-microbiome

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Failed to activate environment. Creating it now...${NC}"
    conda create -n equine-microbiome python=3.9 -y
    conda activate equine-microbiome
    echo "Installing dependencies..."
    conda install -c conda-forge pandas numpy matplotlib seaborn scipy jinja2 pyyaml flask werkzeug biopython openpyxl python-dotenv jupyter notebook ipykernel tqdm psutil -y
    pip install reportlab weasyprint
fi

# Check what the user wants to do
if [ "$1" == "test" ]; then
    echo -e "${GREEN}Running installation test...${NC}"
    python scripts/test_installation.py
    
elif [ "$1" == "sample" ]; then
    echo -e "${GREEN}Processing sample data...${NC}"
    python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

patient = PatientInfo(name='SampleHorse', sample_number='001')
generator = ReportGenerator(language='en')
if generator.generate_report('data/sample_1.csv', patient, 'sample_report.pdf'):
    print('✅ Sample report generated: sample_report.pdf')
else:
    print('❌ Failed to generate report')
"

elif [ "$1" == "batch" ]; then
    if [ -z "$2" ]; then
        echo -e "${YELLOW}Usage: ./run_pipeline.sh batch /path/to/input /path/to/output${NC}"
        exit 1
    fi
    echo -e "${GREEN}Running batch processing...${NC}"
    python scripts/batch_clinical_processor.py --input "$2" --output "${3:-output}" --parallel
    
elif [ "$1" == "full" ]; then
    if [ -z "$2" ]; then
        echo -e "${YELLOW}Usage: ./run_pipeline.sh full /path/to/fastq/dir /path/to/output${NC}"
        exit 1
    fi
    echo -e "${GREEN}Running full pipeline on FASTQ files...${NC}"
    python scripts/full_pipeline.py --input-dir "$2" --output-dir "${3:-output}"
    
elif [ "$1" == "kreport" ]; then
    if [ -z "$2" ]; then
        echo -e "${YELLOW}Usage: ./run_pipeline.sh kreport /path/to/kreports /path/to/output${NC}"
        exit 1
    fi
    echo -e "${GREEN}Processing Kraken2 reports...${NC}"
    python scripts/continue_pipeline.py --kreport-dir "$2" --output-dir "${3:-output}"
    
else
    echo "Usage: ./run_pipeline.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  test                    - Run installation test"
    echo "  sample                  - Process sample data"
    echo "  batch <input> <output>  - Batch process multiple samples"
    echo "  full <input> <output>   - Run full pipeline on FASTQ files"
    echo "  kreport <input> <output>- Process existing Kraken2 reports"
    echo ""
    echo "Examples:"
    echo "  ./run_pipeline.sh test"
    echo "  ./run_pipeline.sh sample"
    echo "  ./run_pipeline.sh batch /mnt/c/data/weekly_samples output/"
    echo "  ./run_pipeline.sh full /mnt/c/data/fastq_files output/"
    echo "  ./run_pipeline.sh kreport /mnt/c/data/kreports output/"
fi

echo ""
echo -e "${GREEN}Done!${NC}"