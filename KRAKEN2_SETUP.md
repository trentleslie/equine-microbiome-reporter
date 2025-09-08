# Kraken2 Database Setup Documentation

## Setup Date: September 7-8, 2025

## Environment
- **System**: WSL2 Ubuntu on Windows 10 VM
- **Location**: `~/equine-microbiome-reporter/`
- **Conda Environment**: `equine-microbiome` (Kraken2 v2.0.8-beta)
- **Available Disk Space**: 947GB initially

## Databases Downloaded

### 1. Kraken2 Viral Database
- **Source**: https://genome-idx.s3.amazonaws.com/kraken/k2_viral_20240112.tar.gz
- **Version**: January 12, 2024
- **Compressed Size**: 483MB
- **Uncompressed Size**: ~620MB
- **Status**: ✅ Downloaded and extracted
- **Location**: `~/kraken2_db/`

### 2. Kraken2 PlusPFP-16 Database
- **Source**: https://genome-idx.s3.amazonaws.com/kraken/k2_pluspfp_16gb_20240112.tar.gz
- **Version**: January 12, 2024
- **Compressed Size**: 10.5GB
- **Estimated Uncompressed Size**: ~16GB
- **Status**: 🔄 Downloading (in progress)
- **Location**: `~/kraken2_db/k2_pluspfp_16gb/` (once extracted)

## Files Created

### Test FASTQ Files
Created synthetic FASTQ files with known bacterial sequences for testing:

1. **test_fastq/sample1.fastq**
   - Contains sequences from:
     - Bacteroides fragilis
     - Lactobacillus acidophilus
     - Escherichia coli
     - Clostridium difficile
     - Prevotella copri

2. **test_fastq/sample2.fastq**
   - Contains sequences from:
     - Streptococcus equi
     - Fibrobacter succinogenes
     - Akkermansia muciniphila
     - Ruminococcus flavefaciens
     - Bifidobacterium longum
     - Faecalibacterium prausnitzii

### Conversion Scripts

1. **src/kraken2_to_csv.py**
   - Converts Kraken2 .kreport files to CSV format
   - Maps taxonomic ranks to the format expected by report generator
   - Handles phylum name mapping (e.g., Firmicutes → Bacillota)
   - Supports single and multiple sample processing

2. **scripts/test_kraken2_pipeline.sh**
   - Comprehensive test script for the entire pipeline
   - Tests Kraken2 classification
   - Converts reports to CSV
   - Generates PDF reports
   - Tests full FASTQ-to-PDF pipeline

## Initial Test Results

### Viral Database Test
```bash
kraken2 --db ~/kraken2_db --threads 4 --output kraken2_output/sample1.kraken \
        --report kraken2_output/sample1.kreport --use-names test_fastq/sample1.fastq
```

**Result**: 
- 5 sequences processed
- 0 sequences classified (0.00%)
- 5 sequences unclassified (100.00%)

This is expected as the viral database doesn't contain bacterial sequences.

## Pipeline Integration

### Components Integrated:
1. **FASTQ Input** → Test files created with known bacterial sequences
2. **Kraken2 Classification** → Using downloaded databases
3. **Report Conversion** → kraken2_to_csv.py script
4. **CSV Processing** → Compatible with existing report generator
5. **PDF Generation** → Using existing ReportGenerator class

### Pipeline Flow:
```
FASTQ → Kraken2 → .kreport → CSV Converter → Report Generator → PDF
```

## Next Steps

1. **Complete PlusPFP-16 Download**: Currently downloading (~10.5GB total)
2. **Extract PlusPFP-16 Database**: Will expand to ~16GB
3. **Run Full Tests**: Execute test_kraken2_pipeline.sh with bacterial database
4. **Validate Results**: Ensure bacterial sequences are properly classified
5. **Performance Testing**: Measure classification speed and accuracy

## Disk Usage Estimates

| Component | Size |
|-----------|------|
| Viral Database (extracted) | ~620MB |
| PlusPFP-16 (compressed) | 10.5GB |
| PlusPFP-16 (extracted) | ~16GB |
| **Total Required** | ~27GB |

## Known Issues and Solutions

### Issue 1: Incomplete Downloads
**Solution**: Use `wget -c` flag for resumable downloads

### Issue 2: Database Path Configuration
**Solution**: Scripts automatically detect database location

### Issue 3: Phylum Name Mapping
**Solution**: kraken2_to_csv.py includes mapping dictionary for common phylum names

## Performance Metrics (To be updated)

- **Classification Speed**: TBD with PlusPFP-16 database
- **Memory Usage**: TBD
- **Accuracy**: TBD with known sequences

## Commands for Manual Testing

```bash
# Activate environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate equine-microbiome

# Run Kraken2 classification
kraken2 --db ~/kraken2_db/k2_pluspfp_16gb \
        --threads 4 \
        --output output.kraken \
        --report output.kreport \
        --use-names \
        input.fastq

# Convert to CSV
python src/kraken2_to_csv.py output.kreport -o output.csv -b 1

# Generate report
python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

patient = PatientInfo(name='Test Horse', sample_number='001')
generator = ReportGenerator(language='en')
generator.generate_report('output.csv', patient, 'report.pdf')
"
```

## Additional Notes

- The PlusPFP-16 database is optimized for 16GB RAM systems
- Viral database is useful for viral metagenomics but not for bacterial analysis
- The client's production setup uses PlusPFP-16 as the primary database
- EuPathDB database can be added later for parasitic organisms if needed