# NCBI Download and Batch Processing

This module enables downloading FASTQ files from NCBI SRA and processing them through the equine microbiome pipeline.

## Overview

The NCBI download feature is designed for **testing and demonstration purposes** - downloading public equine microbiome datasets from NCBI to test the pipeline. The production workflow for HippoVet+ clients uses local FASTQ files, not NCBI downloads.

## Components

### 1. NCBIDownloader Module (`src/ncbi_downloader.py`)

Downloads FASTQ files from NCBI SRA with two methods:
- **SRA Toolkit** (preferred): Uses `prefetch` + `fasterq-dump` for reliable downloads
- **ENA FTP** (fallback): Direct download from European Nucleotide Archive

**Features:**
- Automatic metadata extraction from NCBI
- Dual-mode download with automatic fallback
- Progress tracking and logging
- Organized output into barcode directories
- Batch download support

### 2. Batch Pipeline Script (`scripts/ncbi_batch_pipeline.py`)

Orchestrates the complete workflow:
1. Download FASTQ files from SRA accessions
2. Organize into pipeline-compatible structure
3. Process through Kraken2 (if configured)
4. Generate individual PDF reports

### 3. Configuration File (`config/ncbi_samples.yaml`)

YAML configuration for batch downloads:
```yaml
samples:
  - accession: "SRR12345678"
    name: "Horse_Sample_1"
    age: "5 years"
    sample_number: "001"
```

## Installation

### 1. Install Core Dependencies

```bash
# Using poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

### 2. Install SRA Toolkit (Optional but Recommended)

**Option A: Using conda**
```bash
conda install -c bioconda sra-tools
```

**Option B: Using apt (Ubuntu/Debian)**
```bash
sudo apt-get install sra-toolkit
```

**Option C: Manual installation**
Download from: https://github.com/ncbi/sra-tools/wiki/01.-Downloading-SRA-Toolkit

**Verify installation:**
```bash
prefetch --version
fasterq-dump --version
```

**Configure SRA Toolkit:**
```bash
vdb-config --interactive
```

### 3. Install wget (for ENA fallback)

```bash
sudo apt-get install wget  # Ubuntu/Debian
```

## Usage

### Quick Start

1. **Update configuration file** with your SRA accessions:
   ```bash
   nano config/ncbi_samples.yaml
   ```

2. **Download and process**:
   ```bash
   python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml
   ```

### Command-Line Options

```bash
# Using config file (recommended)
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml

# Using command-line accessions
python scripts/ncbi_batch_pipeline.py --accessions SRR12345 SRR67890 SRR11111

# Download only (no processing)
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --download-only

# Custom output directory
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --output-dir my_results/

# With specific Kraken2 database
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --kraken2-db /path/to/db

# Skip Kraken2 (CSV processing only)
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --skip-kraken
```

### Python API Usage

```python
from pathlib import Path
from src.ncbi_downloader import NCBIDownloader

# Initialize downloader
downloader = NCBIDownloader(output_dir=Path("downloads"))

# Download single accession
success, output_path = downloader.download_accession("SRR12345678")

if success:
    print(f"Downloaded to: {output_path}")

# Batch download
accessions = ["SRR12345", "SRR67890", "SRR11111"]
barcodes = ["barcode01", "barcode02", "barcode03"]
results = downloader.download_batch(accessions, barcodes)

print(f"Successfully downloaded {len(results)} samples")
```

## Finding Equine Microbiome Datasets

### Search NCBI SRA

1. Go to: https://www.ncbi.nlm.nih.gov/sra
2. Search terms:
   - "equine microbiome"
   - "horse gut microbiome"
   - "equine fecal 16S"
   - "horse hindgut amplicon"

3. Filters:
   - **Library Strategy:** AMPLICON
   - **Platform:** ILLUMINA
   - **Source:** METAGENOMIC

### Example BioProjects

Real equine microbiome studies on NCBI:

- **PRJNA516732**: Equine Gut Microbiome Study
- **PRJNA685642**: Horse Fecal Microbiome Analysis
- **PRJNA397906**: Equine Hindgut Microbial Community
- **PRJNA293441**: Equine Colonic Microbiome
- **PRJNA352475**: Horse Microbiota Diversity

### Getting Accession Numbers

From a BioProject page:
1. Click "SRA Experiments"
2. Select samples of interest
3. Copy SRA Run accessions (SRRxxxxxxx)
4. Add to `config/ncbi_samples.yaml`

## Output Structure

```
ncbi_output/
├── downloads/              # Downloaded FASTQ files
│   ├── barcode01/
│   │   ├── SRR12345678/
│   │   │   ├── SRR12345678_1.fastq.gz
│   │   │   ├── SRR12345678_2.fastq.gz
│   │   │   └── SRR12345678_metadata.json
│   ├── barcode02/
│   └── barcode03/
├── csv_files/              # Processed CSV data
│   ├── SRR12345678.csv
│   ├── SRR67890.csv
│   └── SRR11111.csv
├── pdf_reports/            # Generated reports
│   ├── SRR12345678_report.pdf
│   ├── SRR67890_report.pdf
│   └── SRR11111_report.pdf
├── metadata/               # Download metadata
│   └── download_summary.json
└── batch_results.json      # Processing results
```

## Troubleshooting

### SRA Toolkit Issues

**Problem:** `prefetch: command not found`
- **Solution:** Install SRA Toolkit (see Installation section) or script will fallback to ENA FTP

**Problem:** `prefetch` fails with "cart file not found"
- **Solution:** Run `vdb-config --interactive` to configure SRA Toolkit

**Problem:** Download is very slow
- **Solution:** Configure prefetch cache location with more space

### Download Failures

**Problem:** ENA FTP URLs return 404
- **Solution:** Some accessions have non-standard naming. Install SRA Toolkit for better reliability

**Problem:** Timeout errors
- **Solution:** Increase timeout in `ncbi_downloader.py` (default 1 hour)

**Problem:** Metadata fetch fails
- **Solution:** Check internet connection and firewall settings for NCBI E-utilities

### Processing Failures

**Problem:** "No barcode column found in CSV"
- **Solution:** Downloaded data needs Kraken2 processing first. Use `scripts/full_pipeline.py`

**Problem:** Kraken2 database not found
- **Solution:** Set `KRAKEN2_DB_PATH` in `.env` or use `--kraken2-db` flag

**Problem:** "FASTQ processing requires Kraken2"
- **Solution:** Current implementation requires pre-processed CSV. For FASTQ→PDF, manually run:
  ```bash
  python scripts/full_pipeline.py --input-dir downloads/barcode01/ --output-dir results/
  ```

## Workflow Integration

### For Testing Pipeline

```bash
# 1. Download test datasets from NCBI
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --download-only

# 2. Process with full Kraken2 pipeline
python scripts/full_pipeline.py --input-dir ncbi_output/downloads/barcode01/ --output-dir results/

# 3. Generate final reports
python scripts/generate_clean_report.py results/csv_files/sample.csv patient.json output.pdf
```

### For Production (HippoVet+ Workflow)

**Note:** Production workflow does **not** use NCBI downloads. Client samples come from local FASTQ files:

```bash
# Production: Process local client FASTQ files
python scripts/full_pipeline.py --input-dir /path/to/client/data/ --output-dir /path/to/results/
```

## Performance Notes

### Download Times

Typical download times for 16S amplicon data:
- Small datasets (<100MB): 2-5 minutes
- Medium datasets (100MB-1GB): 10-30 minutes
- Large datasets (>1GB): 30+ minutes

### Batch Processing

For multiple samples:
- Sequential download (default): Stable, reliable
- SRA Toolkit: Faster, more reliable than FTP
- ENA FTP: Good fallback, works without sra-tools

## Development Notes

### Why Download-Only Mode?

The current implementation focuses on downloading FASTQ files. The actual Kraken2→PDF processing is handled by the existing `full_pipeline.py` script. This separation was chosen because:

1. **Modularity**: Download and processing can be run independently
2. **Flexibility**: Users can inspect downloads before processing
3. **Reuse**: Leverages existing well-tested pipeline code
4. **Testing**: Allows testing download functionality without Kraken2 database

### Future Enhancements

Possible improvements:
- Direct Kraken2 integration in batch pipeline
- Parallel downloads with asyncio
- Resume failed downloads
- Full NCBI taxonomy integration
- Automatic BioProject download (all samples)
- SRA metadata-to-patient-info mapping

## Examples

### Example 1: Download Three Equine Samples

```yaml
# config/ncbi_samples.yaml
samples:
  - accession: "SRR8439523"
    name: "Horse_Foal_Control"
    age: "3 months"
    sample_number: "001"

  - accession: "SRR8439524"
    name: "Horse_Foal_Treated"
    age: "3 months"
    sample_number: "002"

  - accession: "SRR8439525"
    name: "Horse_Adult_Control"
    age: "5 years"
    sample_number: "003"
```

```bash
python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml
```

### Example 2: Quick Test with Single Accession

```bash
python scripts/ncbi_batch_pipeline.py --accessions SRR8439523 --download-only
```

### Example 3: Python Script Integration

```python
from pathlib import Path
from src.ncbi_downloader import NCBIDownloader
from src.data_models import PatientInfo

# Download
downloader = NCBIDownloader(output_dir=Path("test_downloads"))
success, fastq_path = downloader.download_accession("SRR8439523", barcode="barcode01")

if success:
    print(f"Downloaded to: {fastq_path}")

    # Process with your pipeline
    # ... (integrate with existing pipeline code)
```

## Support

For issues or questions:
1. Check this README's Troubleshooting section
2. Review logs in console output
3. Check NCBI SRA website for accession validity
4. Verify SRA Toolkit installation with `prefetch --version`

## Credits

- SRA Toolkit: NCBI
- ENA FTP: European Bioinformatics Institute
- FASTQ processing: Existing equine-microbiome-reporter pipeline
