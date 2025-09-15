# Testing the Updated Pipeline Configuration

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

# 5. Run the demo
./demo.sh
```

## What the Demo Does

The demo will process one test sample (barcode04) through the complete pipeline:
- Run Kraken2 classification using your PlusPFP-8 database
- Filter for clinically relevant bacteria
- Generate an Excel file for review (with color coding)
- Create a PDF report

**Processing time:** About 2-3 minutes

## Where to Find the Output

After the demo completes, you'll see a new folder:
```
demo_output_YYYYMMDD_HHMMSS/
├── barcode04.kreport        # Kraken2 classification results
├── barcode04.csv            # Processed bacterial abundance
├── barcode04_filtered.csv   # Clinically filtered data
├── barcode04_review.xlsx    # Excel file with color coding (RED/YELLOW/GREEN)
└── barcode04_report.pdf     # Final PDF report (if PDF generation works)
```

For example: `demo_output_20250915_143022/`

## Opening the Results

From WSL2, you can open the results directly in Windows:
```bash
# Open the folder in Windows Explorer
explorer.exe demo_output_*/

# Or specifically open the Excel file
explorer.exe demo_output_*/*.xlsx
```

## If Everything Works

Once the demo succeeds, you can process all three test samples:
```bash
python scripts/full_pipeline.py \
  --input-dir data \
  --output-dir results \
  --barcodes barcode04,barcode05,barcode06
```

This will create:
```
results/
├── kreports/           # Kraken2 reports for all samples
├── csv_files/          # Processed data
├── filtered_csv/       # Filtered data
├── excel_review/       # Excel files for manual review
└── pdf_reports/        # Final PDF reports
```

## Troubleshooting

If you get any errors, please send me:
1. The error message
2. Output of: `ls -la /mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8/*.k2d`
3. Output of: `which kraken2`

The pipeline should now work seamlessly with your existing Kraken2 database. Let me know how the test goes!

Best regards,
[Your name]

---

**Quick Reference:**
- Database location: `/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8`
- Test data: `data/barcode04_test.fastq`
- Demo output: `demo_output_[timestamp]/`
- Full processing output: `results/`