# Kraken2 Setup - Completion Instructions

## Current Status (as of September 7, 2025)

### ✅ Completed Tasks:
1. **Viral Database**: Downloaded and extracted (483MB → 620MB)
2. **Test FASTQ Files**: Created with known bacterial sequences
3. **Kraken2 to CSV Converter**: Script ready at `src/kraken2_to_csv.py`
4. **Test Pipeline Script**: Ready at `scripts/test_kraken2_pipeline.sh`
5. **Initial Testing**: Confirmed Kraken2 works with viral database

### 🔄 In Progress:
- **PlusPFP-16 Database Download**: Currently at ~30% (3.15GB of 10.45GB)
  - Download continuing in background
  - Location: `~/kraken2_db/k2_pluspfp_16gb_20240112.tar.gz`

## Instructions to Complete Setup

### Step 1: Monitor Download Progress
```bash
# Check download progress
bash scripts/monitor_download.sh

# Or manually check file size
ls -lh ~/kraken2_db/k2_pluspfp_16gb_20240112.tar.gz
```

### Step 2: Once Download Completes (10.45GB)
```bash
# Extract the PlusPFP-16 database
cd ~/kraken2_db
tar -xzf k2_pluspfp_16gb_20240112.tar.gz
# This will create a k2_pluspfp_16gb/ directory

# Verify extraction
ls -lh k2_pluspfp_16gb/
```

### Step 3: Run Complete Pipeline Tests
```bash
# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate equine-microbiome

# Run the comprehensive test script
bash scripts/test_kraken2_pipeline.sh
```

### Step 4: Quick Manual Test
```bash
# Test Kraken2 with bacterial database
kraken2 --db ~/kraken2_db/k2_pluspfp_16gb \
        --threads 4 \
        --output test.kraken \
        --report test.kreport \
        --use-names \
        test_fastq/sample1.fastq

# Convert to CSV
python src/kraken2_to_csv.py test.kreport -o test.csv -b 1

# Generate PDF report
python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

patient = PatientInfo(
    name='Test Horse',
    age='5 years',
    sample_number='TEST001'
)
generator = ReportGenerator(language='en')
success = generator.generate_report('test.csv', patient, 'test_report.pdf')
print('✅ Report generated!' if success else '❌ Failed')
"
```

## Expected Results

### With PlusPFP-16 Database:
- Should classify bacterial sequences from test FASTQ files
- Classification rate should be >80% for known bacterial sequences
- Species-level identification for common gut bacteria

### Output Files:
- `kraken2_output/*.kreport` - Kraken2 classification reports
- `kraken2_output/*.csv` - Converted CSV files
- `report_output/*.pdf` - Generated PDF reports

## Troubleshooting

### If Download Fails:
```bash
# Resume download
cd ~/kraken2_db
wget -c https://genome-idx.s3.amazonaws.com/kraken/k2_pluspfp_16gb_20240112.tar.gz
```

### If Extraction Fails (disk space):
```bash
# Check available space
df -h ~/kraken2_db

# Need at least 27GB free (10.5GB compressed + 16GB extracted)
```

### If Kraken2 Fails:
```bash
# Check database integrity
kraken2-inspect --db ~/kraken2_db/k2_pluspfp_16gb

# Verify conda environment
conda list | grep kraken2
```

## Performance Expectations

### With 4 CPU threads:
- Small FASTQ (<1MB): ~1 second
- Medium FASTQ (100MB): ~30 seconds
- Large FASTQ (1GB): ~5 minutes

### Memory Usage:
- PlusPFP-16 database: ~16GB RAM required
- Viral database: <1GB RAM required

## Integration with Main Pipeline

The setup integrates with the existing pipeline:

```python
from src.pipeline_integrator import MicrobiomePipelineIntegrator
from src.data_models import PatientInfo

# Configure pipeline with Kraken2 database
pipeline = MicrobiomePipelineIntegrator(
    kraken2_db="~/kraken2_db/k2_pluspfp_16gb",
    output_dir="pipeline_output"
)

# Process FASTQ directly to PDF
patient = PatientInfo(name="Horse Name", sample_number="001")
results = pipeline.process_sample("sample.fastq", patient, language='en')
```

## Next Steps After Setup

1. **Validate with Real Data**: Test with actual equine microbiome FASTQ files
2. **Optimize Performance**: Adjust thread count based on system resources
3. **Add More Databases**: Consider adding EuPathDB for parasites if needed
4. **Production Deployment**: Set up automated pipeline for batch processing

## Support Files Created

| File | Purpose |
|------|---------|
| `src/kraken2_to_csv.py` | Convert Kraken2 reports to CSV |
| `scripts/test_kraken2_pipeline.sh` | Comprehensive testing script |
| `scripts/monitor_download.sh` | Monitor download progress |
| `test_fastq/*.fastq` | Test FASTQ files with known bacteria |
| `KRAKEN2_SETUP.md` | Complete setup documentation |

## Contact for Issues

If you encounter issues after the download completes, the setup is designed to be self-contained and should work with the test script provided.