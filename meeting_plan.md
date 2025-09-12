# Equine Microbiome Reporter - Meeting Plan

## Meeting Objective
Demonstrate the automated pipeline to reduce manual curation time from 30-40 minutes to 5 minutes per sample (87% reduction).

## Prerequisites
- WSL2 or Linux environment
- 20GB disk space (for Kraken2 database if available)
- 8GB RAM minimum
- Internet connection for installation

## Meeting Flow

### Step 1: Installation (~15-20 minutes)

Run the one-line installer:
```bash
wget https://raw.githubusercontent.com/trentleslie/equine-microbiome-reporter/main/setup.sh && chmod +x setup.sh && ./setup.sh
```

**What happens:**
- Installs conda and git if needed
- Clones the repository
- Downloads test data (20MB) with barcode04, barcode05, barcode06
- Creates conda environment with all dependencies
- **Interactive configuration** - you'll be asked about:
  - Kraken2 database location (can skip if not available)
  - Input/output directories
  - Institution name for reports
- Validates installation
- Generates a demo PDF report

**Expected output:**
```
✅ Installation complete!
✅ Test PDF generated successfully
```

### Step 2: Educational Tutorial (~10 minutes)

Learn how the pipeline works:
```bash
# Activate the conda environment
conda activate equine-microbiome

# Run the interactive tutorial
./tutorial.sh
```

**What it covers:**
- Understanding FASTQ input format
- How Kraken2 classification works
- Clinical filtering process
- Report generation workflow
- Time savings explanation

**Features:**
- Step-by-step explanations
- Color-coded output
- Press Enter to continue through each step
- Works with or without Kraken2 database

### Step 3: Live Demo (~5 minutes)

See the pipeline in action:
```bash
# Run the demo with actual commands
./demo.sh
```

**What happens:**
- Processes `data/barcode04_test.fastq`
- Shows real commands being executed
- Creates timestamped output directory
- Generates Excel review file
- Creates PDF report (if possible)

**Output location:**
- `demo_output_[timestamp]/` directory with all results

### Step 4: Full Pipeline Processing (~5-10 minutes)

Process all three test samples:
```bash
# Process all three barcodes in parallel
python scripts/full_pipeline.py \
  --input-dir data \
  --output-dir results \
  --barcodes barcode04,barcode05,barcode06
```

**Alternative - process all barcodes automatically:**
```bash
python scripts/full_pipeline.py \
  --input-dir data \
  --output-dir results
```

**What happens:**
- Processes 3 samples in parallel
- Runs Kraken2 classification (or uses mock data)
- Applies clinical filtering
- Generates Excel review files
- Creates PDF reports

**Processing time:**
- Manual: 3 samples × 30-40 min = 90-120 minutes
- Automated: 3 samples × 5 min = 15 minutes
- **Time saved: 75-105 minutes (87% reduction)**

### Step 5: Review Generated Outputs (~5 minutes)

#### Excel Review Files
Open the Excel files for manual review:
```bash
# List the Excel files
ls -la results/excel_review/*.xlsx

# On Windows/WSL, you can open directly:
# explorer.exe results/excel_review/
```

**Excel Features:**
- 🔴 **RED** - High clinical relevance (pathogens)
- 🟡 **YELLOW** - Moderate relevance (opportunistic)
- 🟢 **GREEN** - Low relevance (beneficial)
- Summary statistics
- Review instructions

#### PDF Reports
View the generated PDF reports:
```bash
# List the PDF reports
ls -la results/pdf_reports/*.pdf

# On Windows/WSL, you can open directly:
# explorer.exe results/pdf_reports/
```

**PDF Contents:**
- 5-page professional veterinary report
- Patient information
- Microbiome composition charts
- Dysbiosis index
- Clinical recommendations

### Step 6: Discussion Points (~10 minutes)

#### Key Benefits
1. **Time Savings**: 87% reduction in manual curation
2. **Consistency**: Standardized clinical categorization
3. **Quality**: Professional PDF reports
4. **Scalability**: Process 15+ samples in parallel

#### Workflow Integration
1. Receive FASTQ files from sequencing
2. Run pipeline (5 minutes per sample)
3. Review Excel files for accuracy
4. Approve and send PDF reports
5. Archive processed data

#### Customization Options
- Adjust clinical relevance thresholds in `.env`
- Modify report templates for your institution
- Add custom logos and branding
- Configure language (Polish translation available soon)

## Quick Reference Commands

```bash
# Activate environment
conda activate equine-microbiome

# Process single sample
python scripts/full_pipeline.py \
  --input-dir data \
  --output-dir results \
  --barcodes barcode04

# Process all samples
python scripts/full_pipeline.py \
  --input-dir data \
  --output-dir results

# Get help
python scripts/full_pipeline.py --help

# Check configuration
cat .env
```

## Troubleshooting

### If Kraken2 database is not available:
- Pipeline will use mock data for demonstration
- Clinical filtering and report generation still work
- Can add database later

### If PDF generation fails:
- Excel files are still generated for review
- Can use Excel files for manual report creation
- PDF generation can be fixed post-meeting

### Memory issues:
- Reduce parallel processing in `.env`:
  ```
  MAX_PARALLEL_SAMPLES=2
  ```

## Next Steps After Meeting

1. **Configure for production:**
   - Update `.env` with production paths
   - Install full Kraken2 database if needed
   - Set up institution branding

2. **Train staff:**
   - Run tutorial with each operator
   - Practice with test data
   - Document any lab-specific procedures

3. **Establish workflow:**
   - Define sample naming conventions
   - Set up input/output directories
   - Create backup procedures

## Contact for Support

- GitHub Issues: https://github.com/trentleslie/equine-microbiome-reporter/issues
- Documentation: See README.md for detailed instructions

---

**Meeting Duration:** ~45-60 minutes total

**Required from attendees:** 
- Access to WSL2 or Linux system
- Note-taking for lab-specific configuration

**Deliverables:**
- Working pipeline installation
- Processed test samples
- Excel and PDF outputs for review
- Clear understanding of 87% time savings