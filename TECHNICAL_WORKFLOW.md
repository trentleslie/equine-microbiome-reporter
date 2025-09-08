# Clinical Filtering System: Current Implementation (Phase 1)

## Overview
This document describes the **actual implemented system** for HippoVet+ that reduces manual sample curation from 30-40 minutes to 5-10 minutes per sample through intelligent filtering and Excel-based review.

---

## 🔄 Current Workflow

### Step 1: Sequencing & Initial Analysis (Unchanged)
Your existing workflow continues as normal:
- Sequence samples on Oxford Nanopore MinION
- Run Epi2Me/Nextflow for taxonomic classification
- Kraken2 generates `.kreport` files

### Step 2: Manual Pipeline Execution
After Epi2Me/Nextflow completes, run one of these commands:

#### Option A: Process from Kraken2 Reports (Recommended)
```bash
python scripts/continue_pipeline.py \
    --kreport-dir /path/to/your/kreports \
    --output-dir results
```

#### Option B: Process from FASTQ Files
```bash
python scripts/full_pipeline.py \
    --input-dir /path/to/fastq \
    --output-dir results
```

#### Option C: Batch Processing (Weekly Workflow)
```bash
python scripts/batch_clinical_processor.py \
    --input /path/to/weekly/samples \
    --output results \
    --parallel
```

### Step 3: Clinical Filtering Applied
The system automatically:
- Removes species below abundance threshold (default: 0.01%)
- Filters out known contaminants
- Applies basic clinical relevance rules
- Reduces species list by ~75-90%

### Step 4: Excel Review Generation
Creates a **color-coded Excel file** with three sheets:

#### Sheet 1: Clinical Review
| Species | Abundance (%) | Clinical Relevance | Include in Report | Notes |
|---------|--------------|-------------------|-------------------|-------|
| 🔴 Streptococcus equi | 15% | HIGH | YES | Known pathogen |
| 🟠 E. coli | 8% | MODERATE | [Review] | Opportunistic |
| ⚪ Phytophthora | 5% | EXCLUDED | NO | Plant parasite |

**Color Coding:**
- 🔴 **RED**: High clinical relevance (known pathogens)
- 🟠 **ORANGE**: Moderate relevance (opportunistic pathogens)
- 🟢 **GREEN**: Beneficial bacteria
- ⚪ **GRAY**: Excluded (plant parasites, contaminants)
- 🟡 **YELLOW**: Requires manual review

#### Sheet 2: Summary Statistics
- Total species before/after filtering
- Reduction percentage
- Count by clinical relevance category

#### Sheet 3: Instructions
- Color code explanations
- Review process guidance
- Threshold definitions

### Step 5: Manual Review (5-10 minutes)
1. Open Excel file from `results/excel_review/`
2. Review species marked as `[Review]` 
3. Change to `YES` or `NO` based on clinical judgment
4. Save the Excel file

### Step 6: PDF Report Generation
The system generates professional PDF reports with:
- Filtered species list
- Abundance charts
- Clinical interpretations
- Located in `results/pdf_reports/`

---

## 💡 Real-World Example

**Before (Manual Process):**
- Open Kraken2 output: 200+ species
- Manually review each species: 30-40 minutes
- Copy relevant ones to report

**After (With Clinical Filtering):**
- Run pipeline: 200 → 25 species (1 minute)
- Open Excel: Review 5-10 uncertain species (5 minutes)
- Total time: 6 minutes

**Time savings: 75-85% reduction**

---

## 🎯 What's Implemented

### ✅ Working Features
- FASTQ to PDF complete pipeline
- Kraken2 report processing
- CSV data transformation
- Clinical filtering with thresholds
- Color-coded Excel review sheets
- Batch processing for multiple samples
- PDF report generation
- Basic pathogen recognition
- Plant parasite exclusion

### ⏳ Phase 2 Enhancements (Future)
- Automatic Epi2Me monitoring
- Background watching service
- Database-specific filtering rules
- Expanded species database
- Desktop shortcuts/installer
- Real-time processing
- Advanced clinical AI recommendations

---

## 🛠️ Installation & Setup

### Prerequisites
- WSL2 with Ubuntu
- Conda/Miniconda installed
- Kraken2 databases (via Epi2Me)
- 8GB RAM minimum

### Quick Setup
```bash
# Clone repository
git clone https://github.com/trentleslie/equine-microbiome-reporter.git
cd equine-microbiome-reporter

# Create environment
conda create -n equine-microbiome python=3.9 -y
conda activate equine-microbiome

# Install dependencies
conda install -c conda-forge pandas numpy matplotlib seaborn scipy \
    jinja2 pyyaml biopython openpyxl python-dotenv tqdm psutil -y
pip install reportlab weasyprint

# Configure paths (IMPORTANT: Update to match your system!)
cp .env.hippovet .env
nano .env  # Edit paths to match your Epi2Me installation

# Test installation
python scripts/test_installation.py
```

---

## 📁 File Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| Input (Kraken2) | `/path/to/kreports/` | Kraken2 report files |
| Input (FASTQ) | `/path/to/fastq/` | Raw sequencing files |
| Processing | `~/equine-microbiome-reporter/` | Pipeline scripts |
| Output Excel | `results/excel_review/` | Review spreadsheets |
| Output PDF | `results/pdf_reports/` | Final reports |
| Output CSV | `results/csv_files/` | Processed data |

---

## ⚡ Daily Usage

### Single Sample Processing
```bash
# Activate environment
conda activate equine-microbiome

# Process sample
python scripts/continue_pipeline.py \
    --kreport-dir /mnt/c/data/todays_sample \
    --output-dir /mnt/c/Users/hippovet/Desktop/results

# Review Excel file and generate final report
```

### Weekly Batch Processing
```bash
# Process entire week's samples at once
python scripts/batch_clinical_processor.py \
    --input /mnt/c/data/DIAG_08_09_2025 \
    --output /mnt/c/Users/hippovet/Desktop/weekly_results \
    --parallel
```

---

## 📊 Performance Metrics

### Time Savings
- **Current manual process**: 30-40 minutes per sample
- **With clinical filtering**: 5-10 minutes per sample
- **Reduction**: 75-85% time savings
- **Weekly impact** (15 samples): 6-8 hours saved

### Quality Improvements
- **Consistency**: Standardized filtering across all samples
- **Accuracy**: Reduced human error in species identification
- **Traceability**: Excel files document all filtering decisions

---

## 🔧 Configuration & Customization

### Key Settings in `.env` file:
```bash
# Abundance thresholds
MIN_ABUNDANCE_THRESHOLD=0.01  # Minimum 0.01% to include
CLINICAL_RELEVANCE_THRESHOLD=0.1  # 0.1% for clinical relevance

# Database paths (UPDATE THESE!)
KRAKEN2_DB_PATH=/your/actual/path/to/PlusPFP-16
OUTPUT_BASE_PATH=/your/preferred/output/location
```

### Clinical Relevance Rules
Edit `scripts/generate_clinical_excel.py` to customize:
- High relevance pathogen list
- Moderate relevance species
- Excluded organisms
- Abundance thresholds

---

## 📈 Results & Validation

The system has been tested with:
- Real FASTQ data (barcode04, barcode05, barcode06)
- Mock Kraken2 reports
- Various abundance distributions

Typical results:
- 75-90% reduction in species count
- 5-10 species requiring manual review
- Consistent pathogen detection
- Reliable plant parasite exclusion

---

## 🚀 Next Steps for Monday Testing

1. **Clone repository and set up environment** (20 minutes)
2. **Update `.env` file with your paths** (5 minutes)
3. **Run test with sample data** (5 minutes)
4. **Process 3-5 real samples** (30 minutes)
5. **Evaluate time savings** 
6. **Provide feedback for Phase 2 enhancements**

---

## 💬 Support

For issues or questions:
- GitHub: https://github.com/trentleslie/equine-microbiome-reporter
- Email: trentleslie@gmail.com
- Documentation: See DEPLOYMENT_WSL2_COMPLETE.md for detailed setup

---

*Version 1.0 - Phase 1 Implementation*  
*Ready for Monday testing at HippoVet+*