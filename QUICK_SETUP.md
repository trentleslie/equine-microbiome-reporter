# Quick Setup Guide - Equine Microbiome Reporter

## One-Line Installation

```bash
wget https://raw.githubusercontent.com/ai-asa/equine-microbiome-reporter/main/setup.sh && chmod +x setup.sh && ./setup.sh
```

That's it! The script will handle everything.

## What the Setup Script Does

1. **Installs Prerequisites**
   - Conda (if not present)
   - Git (if not present)
   
2. **Downloads Everything**
   - Clones the repository
   - Downloads test data from Google Drive
   - Extracts test FASTQ files

3. **Creates Environment**
   - Sets up conda environment `equine-microbiome`
   - Installs all Python dependencies
   - Configures PDF generation tools

4. **Interactive Configuration**
   - Searches for Kraken2 databases
   - Asks for your data location
   - Configures output directories
   - Detects WSL and sets Windows paths

5. **Validates Installation**
   - Tests all imports
   - Generates demo report
   - Provides test commands

## Interactive Configuration Example

The script will ask you a few questions:

```
=== Kraken2 Database Configuration ===
Found potential Kraken2 databases:
  1. /mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-16
Select database number (or press Enter to skip): 1

=== FASTQ Data Location ===
FASTQ directory path [./data]: /mnt/c/data/samples

=== Barcode File Format ===
How are your barcode files organized?
  1. Folders: barcode04/, barcode05/
  2. Files: barcode04.fastq
  3. Compressed: barcode04.fastq.gz
  4. Epi2Me format: fastq_pass/barcode04/
Select format (1-4) [1]: 1

=== Output Directory ===
Output directory [/mnt/c/Users/yourname/Desktop/microbiome_results]: [Enter]
```

## After Installation

1. **Activate the environment:**
   ```bash
   conda activate equine-microbiome
   ```

2. **Test with included data:**
   ```bash
   python scripts/full_pipeline.py --input-dir data --output-dir test_output
   ```

3. **Use your own data:**
   ```bash
   python scripts/full_pipeline.py \
     --input-dir /path/to/your/fastq \
     --output-dir /path/to/results \
     --kraken2-db /path/to/database
   ```

## If Kraken2 is Not Available

The script will configure "mock mode" which allows testing without Kraken2:

```bash
# Generate test reports without Kraken2
python scripts/generate_mock_reports.py --input-dir data

# Or use sample CSV data
python -c "from src.report_generator import ReportGenerator; \
           from src.data_models import PatientInfo; \
           generator = ReportGenerator(); \
           generator.generate_report('data/sample_1.csv', \
                                   PatientInfo(name='Test'), \
                                   'test.pdf')"
```

## Troubleshooting

### Download Issues
If the Google Drive download fails:
1. Download manually: https://drive.google.com/file/d/1OmhZwEOYZ7BOUUOm08lRgDek8sO_S-tR/view
2. Extract to `data/` directory:
   ```bash
   tar -xzf test_data.tar.gz -C equine-microbiome-reporter/data/
   ```

### Conda Issues
If conda commands don't work after installation:
```bash
# Restart your terminal, or:
source ~/.bashrc
```

### WSL Path Issues
Use `/mnt/c/` format for Windows drives:
- ✅ `/mnt/c/Users/username/Desktop`
- ❌ `C:\Users\username\Desktop`

### Memory Issues
If you get out-of-memory errors:
1. Edit `.env` file
2. Set `KRAKEN2_MEMORY_MAPPING=true`
3. Reduce `KRAKEN2_THREADS=2`

## File Locations After Setup

```
equine-microbiome-reporter/
├── setup.sh                 # The setup script
├── .env                     # Your configuration (created by setup)
├── data/
│   ├── barcode04_test.fastq  # Test data (100 reads)
│   ├── barcode05_test.fastq  # Test data (100 reads)
│   ├── barcode06_test.fastq  # Test data (100 reads)
│   └── sample_1.csv          # Sample CSV for testing
├── scripts/
│   ├── full_pipeline.py      # Main pipeline script
│   └── continue_pipeline.py  # For existing Kraken2 reports
└── src/
    └── [pipeline modules]
```

## Configuration File (.env)

The setup creates a `.env` file with your settings:

```bash
# Your data location
FASTQ_INPUT_DIR=/mnt/c/data/samples

# Kraken2 settings (if available)
KRAKEN2_DB_PATH=/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-16

# Output locations
DEFAULT_OUTPUT_DIR=/mnt/c/Users/username/Desktop/microbiome_results

# Processing options
ENABLE_PARALLEL_PROCESSING=true
MAX_PARALLEL_SAMPLES=4
```

You can edit this file anytime to change settings.

## Support

- **Documentation**: Check `DEPLOYMENT_WSL2_COMPLETE.md` for detailed info
- **Clinical Filtering**: See `CLINICAL_FILTERING_IMPLEMENTATION.md`
- **Issues**: https://github.com/ai-asa/equine-microbiome-reporter/issues

## Quick Test After Setup

```bash
# Activate environment
conda activate equine-microbiome

# Generate a test report
python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

patient = PatientInfo(name='QuickTest', sample_number='001')
generator = ReportGenerator()
generator.generate_report('data/sample_1.csv', patient, 'quick_test.pdf')
print('✓ Test successful! Check quick_test.pdf')
"
```

The whole process should take about 15-20 minutes on first run (mostly downloading dependencies).