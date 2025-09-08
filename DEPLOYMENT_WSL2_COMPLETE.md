# WSL2 Deployment Guide for HippoVet+
## Complete Setup Instructions for Monday Testing

### Prerequisites Checklist
- [ ] Windows 10/11 with WSL2 enabled  
- [ ] At least 20GB free disk space
- [ ] 8GB RAM minimum (16GB recommended for full Kraken2 databases)
- [ ] Epi2Me/Nextflow with Kraken2 installed (✅ You already have this)
- [ ] Git installed in WSL2
- [ ] Python 3.9+ or Conda/Miniconda

---

## Step 1: Initial Setup (10 minutes)

### 1.1 Open WSL2 Terminal
```bash
# In Windows PowerShell or Terminal:
wsl
```

### 1.2 Clone the Repository
```bash
cd ~
git clone https://github.com/trentleslie/equine-microbiome-reporter.git
cd equine-microbiome-reporter
```

### 1.3 Check Your Current Directory
```bash
pwd
# Should show: /home/[your-username]/equine-microbiome-reporter
```

---

## Step 2: Environment Configuration (5 minutes)

### 2.1 Create Environment Configuration File
```bash
# Copy the pre-configured template (IMPORTANT: You MUST customize the paths!)
cp .env.hippovet .env

# CRITICAL: Edit the .env file to update ALL paths to match YOUR system
nano .env
# Or use any text editor you prefer
```

### 2.2 Configure Kraken2 Paths in .env
**IMPORTANT: These are EXAMPLE paths - you MUST update them to match YOUR actual Epi2Me installation:**

```bash
# Your actual Kraken2 paths (example based on your setup)
KRAKEN2_DB_PATH=/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-16
KRAKEN2_EXECUTABLE=kraken2  # If kraken2 is in your PATH
KRAKEN2_THREADS=4
KRAKEN2_MEMORY_MAPPING=true  # Set to true if you have <16GB RAM

# Disable LLM features for testing (optional features)
ENABLE_LLM_RECOMMENDATIONS=false
```

**CRITICAL: Verify and update YOUR actual paths:**
1. Find your Epi2Me installation: `ls /mnt/c/Users/*/epi2melabs/`
2. Locate PlusPFP-16 database: `find /mnt/c -name "PlusPFP*" 2>/dev/null`
3. Update ALL paths in .env to match YOUR system
4. The example paths `/mnt/c/Users/hippovet/` are just EXAMPLES - use YOUR username and paths!

---

## Step 3: Python Environment Setup (15 minutes)

### Option A: Using Conda (Recommended)
```bash
# Create conda environment
conda create -n equine-microbiome python=3.9 -y
conda activate equine-microbiome

# Install dependencies
conda install -c conda-forge \
    pandas numpy matplotlib seaborn scipy \
    jinja2 pyyaml flask werkzeug \
    biopython openpyxl python-dotenv \
    jupyter notebook ipykernel tqdm psutil -y

# Install remaining packages via pip
pip install reportlab weasyprint
```

### Option B: Using System Python
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 3.1 Verify Installation
```bash
# Test core imports
python -c "
from src.report_generator import ReportGenerator
from src.clinical_filter import ClinicalFilter
print('✅ Core modules loaded successfully')
"
```

---

## Step 4: Test with Sample Data (5 minutes)

### 4.1 Quick Test with Provided CSV
```bash
# Generate a test report
python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

# Create test patient
patient = PatientInfo(
    name='TestHorse',
    sample_number='TEST001',
    age='5 years',
    performed_by='Lab Tech',
    requested_by='Dr. Smith'
)

# Generate report from sample CSV
generator = ReportGenerator(language='en')
success = generator.generate_report(
    'data/sample_1.csv',  # Using provided sample data
    patient,
    'test_report.pdf'
)
print('✅ Test report generated!' if success else '❌ Generation failed')
"

# Check if PDF was created
ls -lh test_report.pdf
```

---

## Step 5: Process Your Real Data

### 5.1 Prepare Your Data
Your typical workflow with Epi2Me produces `.kreport` files. Place them in the appropriate directory:

```bash
# Create directories for your data
mkdir -p input_data/kreports
mkdir -p input_data/fastq
mkdir -p output

# Copy your Kraken2 reports (if you have them)
cp /mnt/c/Users/hippovet/epi2melabs/instances/*/output/*.kreport input_data/kreports/

# Or copy FASTQ files for full processing
cp /mnt/c/data/DIAG_*/*/fastq_pass/barcode*.fastq.gz input_data/fastq/
```

### 5.2 Run the Full Pipeline

#### For FASTQ Files → PDF Reports:
```bash
python scripts/full_pipeline.py \
    --input-dir input_data/fastq \
    --output-dir output \
    --kraken2-db /mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-16
```

#### For Existing Kraken2 Reports → PDF Reports:
```bash
python scripts/continue_pipeline.py \
    --kreport-dir input_data/kreports \
    --output-dir output
```

### 5.3 Batch Processing (Your Typical 15-Sample Weekly Batch)
```bash
# Process multiple samples at once
python scripts/batch_clinical_processor.py \
    --input /mnt/c/data/weekly_samples/ \
    --output /mnt/c/Users/hippovet/Desktop/results/ \
    --parallel  # Enable parallel processing
```

---

## Step 6: Review Clinical Filtering Results

### 6.1 Check Generated Files
```bash
# List all outputs
ls -la output/

# You should see:
# - combined_fastq/     # Combined FASTQ files
# - kraken_output/      # Kraken2 classification results
# - csv_files/          # Processed CSV data
# - excel_review/       # ⭐ Excel files for manual review
# - pdf_reports/        # Final PDF reports
```

### 6.2 Review Excel Files
The Excel files in `excel_review/` contain three sheets:
1. **Filtered_Species** - Clinically relevant species
2. **Summary** - Filtering statistics
3. **Original_Data** - Complete unfiltered results

Open these in Excel to:
- Review filtered species
- Add/remove species based on clinical judgment
- Check filtering effectiveness (should show ~75% reduction)

### 6.3 Customizing Clinical Filters
Edit `config/clinical_relevance.json` to add your own rules:
```json
{
  "always_include": [
    "Salmonella enterica",
    "Clostridium difficile"
  ],
  "always_exclude": [
    "Plant parasites",
    "Environmental bacteria"
  ],
  "abundance_threshold": 0.1
}
```

---

## Step 7: Performance Optimization

### 7.1 For Systems with Limited RAM (<16GB)
```bash
# Edit .env file
KRAKEN2_MEMORY_MAPPING=true  # Use disk instead of RAM
KRAKEN2_THREADS=2  # Reduce thread count
```

### 7.2 WSL2 Memory Configuration
Create or edit `C:\Users\[username]\.wslconfig`:
```ini
[wsl2]
memory=8GB  # Allocate specific amount to WSL2
processors=4
swap=4GB
localhostForwarding=true
```

Then restart WSL2:
```powershell
wsl --shutdown
wsl
```

---

## Step 8: Troubleshooting

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| "Database not found" | Check KRAKEN2_DB_PATH in .env file |
| "Out of memory" | Enable memory mapping: KRAKEN2_MEMORY_MAPPING=true |
| "Permission denied" | Run: `chmod +x scripts/*.py` |
| "Module not found" | Activate conda environment: `conda activate equine-microbiome` |
| "Kraken2 fails" | Verify database path and check available disk space |

### 8.1 Test Kraken2 Separately
```bash
# Test if Kraken2 works with your database
kraken2 --db /path/to/your/database \
        --threads 2 \
        --memory-mapping \
        --report test.kreport \
        test_sample.fastq
```

### 8.2 Check Logs
```bash
# View processing logs
tail -f output/pipeline.log

# Check for errors
grep ERROR output/pipeline.log
```

---

## Step 9: Quick Start Commands (Copy & Paste)

### Complete Setup in One Go:
```bash
# 1. Clone and enter directory
cd ~ && git clone https://github.com/trentleslie/equine-microbiome-reporter.git && cd equine-microbiome-reporter

# 2. Setup environment
conda create -n equine-microbiome python=3.9 -y && conda activate equine-microbiome

# 3. Install dependencies
conda install -c conda-forge pandas numpy matplotlib seaborn scipy jinja2 pyyaml flask werkzeug biopython openpyxl python-dotenv jupyter notebook ipykernel tqdm psutil -y && pip install reportlab weasyprint

# 4. Configure
cp .env.example .env && echo "Edit .env file with your paths"

# 5. Test
python -c "from src.report_generator import ReportGenerator; print('✅ Ready!')"
```

---

## Step 10: Monday Testing Checklist

### Before Testing:
- [ ] WSL2 is running
- [ ] Repository cloned
- [ ] Environment configured (.env file edited)
- [ ] Dependencies installed
- [ ] Test report generated successfully

### During Testing:
- [ ] Process one sample first
- [ ] Check Excel review file
- [ ] Verify PDF report quality
- [ ] Test batch processing with 3+ samples
- [ ] Measure time savings

### Success Metrics:
- [ ] Manual curation time reduced from 30-40 min to 5-10 min ✅
- [ ] Excel files generated for review ✅
- [ ] PDF reports match quality standards ✅
- [ ] Batch processing handles 15 samples ✅

---

## Support & Contact

**During Testing:**
- GitHub Issues: https://github.com/trentleslie/equine-microbiome-reporter/issues
- Email: trentleslie@gmail.com

**Key Files to Review:**
- `scripts/full_pipeline.py` - Main pipeline script
- `src/clinical_filter.py` - Clinical filtering logic
- `config/report_config.yaml` - Thresholds and settings

**Performance Expectations:**
- Single sample: 30-60 seconds
- 15-sample batch: 10-15 minutes
- Memory usage: 2-4GB (without Kraken2), 8-16GB (with Kraken2)

---

## Appendix: Your Specific Setup Details

Based on our discussion, your environment has:
- **Epi2Me location**: `/mnt/c/Users/hippovet/epi2melabs/`
- **Databases**: PlusPFP-16, EuPathDB, Viral
- **Typical batch**: 15 samples weekly
- **Current bottleneck**: Manual curation (30-40 min/sample)
- **Expected improvement**: 5-10 min/sample (75% reduction)

The system is designed to integrate seamlessly with your existing Epi2Me/Nextflow workflow while dramatically reducing manual curation time.

**Ready for Monday testing! 🚀**