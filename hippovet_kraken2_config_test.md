# Testing the Updated Pipeline Configuration

## Important Updates
- **New clean report design**: Modern 4-page layout (no title page)
- **Simplified system**: All old templates removed, only clean templates remain
- **Kraken2 required**: Install with `conda install -c bioconda kraken2 -y` if not present

## Quick Test Instructions

Please open WSL2 Ubuntu and run these commands:

```bash
# 1. Navigate to the project folder
cd ~/equine-microbiome-reporter

# 2. Get the latest updates
git pull

# 3. Copy the HippoVet configuration
cp .env.hippovet .env

# 4. Activate the conda environment
conda activate equine-microbiome

# 5. Install Kraken2 if needed
conda install -c bioconda kraken2 -y

# 6. Run the demo
./demo.sh
```

## What the Demo Does

The demo generates a **clean, modern 4-page PDF report** using the simplified template system:
- Load and process CSV data
- Calculate dysbiosis index
- Generate professional charts
- Create clean PDF report (pages 2-5 only, no title page)

**Processing time:** About 10-15 seconds

## Where to Find the Output

After the demo completes, you'll see a new folder:
```
demo_output_YYYYMMDD_HHMMSS/
├── clean_report.pdf     # 4-page PDF report (no title page)
└── clean_report.html    # HTML version for review
```

For example: `demo_output_20250915_143022/`

**Note**: The system now generates ONLY the clean report format. The Excel files are generated separately by the full pipeline script.

## Opening the Results

From WSL2, you can open the results directly in Windows:
```bash
# Open the PDF in Windows
explorer.exe demo_output_*/clean_report.pdf
```

## The New Report Structure

The PDF contains 4 professional pages:
1. **Sequencing Results** - Species distribution & dysbiosis index
2. **Phylum Analysis** - Distribution charts and comparisons
3. **Clinical Interpretation** - Assessment and recommendations
4. **Summary & Guidelines** - Management recommendations

To add your NG-GP title page:
1. Save your title page as `title_page.pdf`
2. Combine: `pdftk title_page.pdf demo_output_*/clean_report.pdf cat output final_report.pdf`

## Processing Real FASTQ Data

For actual FASTQ processing with Kraken2:
```bash
python scripts/full_pipeline.py \
  --input-dir data \
  --output-dir results \
  --barcodes barcode04,barcode05,barcode06
```

This will create:
```
results/
├── kreports/           # Kraken2 reports
├── csv_files/          # Processed data
├── filtered_csv/       # Filtered data
├── excel_review/       # Excel files for manual review
└── pdf_reports/        # Final PDF reports
```

## Troubleshooting

### If Kraken2 is not found:
```bash
conda install -c bioconda kraken2 -y
```

### If the database path is wrong:
Edit `.env` and set:
```
KRAKEN2_DB_PATH=/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8
```

### To verify Kraken2 works:
```bash
kraken2 --db /mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8 --version
```

If you get any errors, please send:
1. The error message
2. Output of: `ls -la /mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8/*.k2d`
3. Output of: `which kraken2`

## What's New in This Version

✅ **Completely redesigned report system**
- Clean, modern 4-page layout
- No title page (add your own)
- Professional medical report styling

✅ **Simplified codebase**
- Removed all old templates
- Single report generation path
- Faster processing

✅ **Better integration**
- Works with your existing Kraken2 database
- Automatic environment detection
- Improved error handling

---

**Quick Reference:**
- Database location: `/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8`
- Test command: `./demo.sh`
- Demo output: `demo_output_[timestamp]/clean_report.pdf`
- Full pipeline: `scripts/full_pipeline.py`