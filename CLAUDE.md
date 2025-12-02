# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Equine Microbiome Reporter** - An automated PDF report generation system for equine gut microbiome analysis from 16S rRNA sequencing data. The system processes raw FASTQ files through Kraken2 classification, applies clinical filtering, and generates professional 5-page PDF reports using Jinja2 templates and WeasyPrint.

**Current Status:** Production-ready with English reports in clean template format.

**Key Points:**
- Private project for HippoVet+ veterinary laboratory
- Complete FASTQ-to-PDF pipeline with Kraken2 integration
- Clinical filtering for veterinary-relevant species
- Uses `templates/clean/` for current production reports
- Legacy code preserved in `legacy/` directory

## Development Commands

### Dependencies and Setup
```bash
# Install core dependencies
poetry install

# Optional: Add LLM, translation, or dev tools
poetry install --with dev      # Jupyter notebooks and development tools
poetry install --with llm      # LLM support (OpenAI, Anthropic, Gemini)
poetry install --with translation-free  # Free translation services

# Activate environment
poetry shell
```

### Generate Reports
```bash
# Quick report generation from CSV (most common task)
poetry run python -c "
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

patient = PatientInfo(name='Montana', sample_number='506')
success = generate_clean_report('data/sample_1.csv', patient, 'report.pdf')
print('✅ Success!' if success else '❌ Failed!')
"

# Complete FASTQ-to-PDF pipeline (production workflow)
poetry run python scripts/full_pipeline.py --input-dir data/ --output-dir results/

# Process with multiple languages (English, Polish, Japanese)
poetry run python scripts/full_pipeline.py \
  --input-dir data/ \
  --output-dir results/ \
  --languages en,pl,ja

# Process specific barcodes with multi-language output
poetry run python scripts/full_pipeline.py \
  --input-dir data/ \
  --output-dir results/ \
  --barcodes barcode04,barcode05 \
  --languages en,pl,ja

# Batch multi-language processing (convenience script)
poetry run python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --languages en pl ja \
  --output-dir reports/multilingual

# Batch processing (interactive)
poetry run jupyter notebook notebooks/batch_processing.ipynb
```

### Multi-Language Batch Processing
```bash
# Generate reports in English, Polish, and Japanese for all samples
poetry run python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --languages en pl ja

# Process from manifest file
poetry run python scripts/batch_multilanguage.py \
  --manifest manifest.csv \
  --languages en pl ja

# Single language batch processing (backwards compatible)
poetry run python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --languages en

# With custom settings
poetry run python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --output-dir reports/custom/ \
  --languages en pl ja \
  --workers 8 \
  --no-parallel

# Output: Each sample generates multiple PDFs
# Example: sample_001_en.pdf, sample_001_pl.pdf, sample_001_ja.pdf
```

### Download and Process from NCBI
```bash
# Download FASTQ files from NCBI SRA and generate reports
# First, update config/ncbi_samples.yaml with your SRA accession numbers

# Download and process (full workflow)
poetry run python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml

# Download only (no processing)
poetry run python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --download-only

# Using command-line accessions
poetry run python scripts/ncbi_batch_pipeline.py --accessions SRR12345 SRR67890 SRR11111

# With custom output directory
poetry run python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --output-dir results/

# Note: Requires SRA Toolkit installation
# Install via conda: conda install -c bioconda sra-tools
# Or the script will fallback to direct ENA FTP download
```

### Testing and Validation
```bash
# Run formal test suite
poetry run pytest tests/ --cov=src --cov-report=html

# Validate CSV format
poetry run python scripts/validate_csv_format.py data/sample.csv [barcode_column]

# Validate client data integrity
poetry run python scripts/validate_client_data.py data/

# Test installation and pipeline
poetry run python scripts/test_installation.py

# Validate FASTQ pipeline
poetry run python scripts/validate_fastq_pipeline.py
```

## Architecture Overview

### Complete Pipeline Flow (FASTQ → PDF)
1. **FASTQ Input**: Raw sequencing files organized by barcode
2. **Kraken2 Classification**: Taxonomic identification using PlusPFP-16 database
3. **Clinical Filtering**: Remove non-veterinary taxa (plants, archaea), identify pathogens
4. **CSV Conversion**: Kraken2 reports → abundance tables with phylum mapping
5. **Data Processing**: `CSVProcessor` creates `MicrobiomeData` with dysbiosis calculations
6. **Chart Generation**: Matplotlib/Seaborn charts for species/phylum distribution
7. **Template Rendering**: Jinja2 processes HTML templates with data context
8. **Translation** (if language != 'en'): HTML content translated with scientific term protection
9. **PDF Generation**: WeasyPrint converts HTML to professional 5-page PDF
10. **Output**: Laboratory-ready report with clinical interpretations

### Key Components
- **`src/data_models.py`**: Core data classes - `PatientInfo` and `MicrobiomeData`
- **`src/kraken2_classifier.py`**: Kraken2 integration with taxonomy mapping
- **`src/clinical_filter.py`**: Veterinary-specific filtering rules (removes plants, identifies pathogens)
- **`src/csv_processor.py`**: CSV parsing, phylum aggregation, dysbiosis calculations
- **`src/chart_generator.py`**: Matplotlib/Seaborn visualizations
- **`src/batch_processor.py`**: Batch orchestration with multi-language and parallel processing
- **`scripts/generate_clean_report.py`**: Single report orchestrator (CSV → PDF with optional translation)
- **`scripts/batch_multilanguage.py`**: Batch wrapper around `BatchProcessor` for CLI usage
- **`scripts/full_pipeline.py`**: End-to-end FASTQ-to-PDF pipeline coordinator
- **`config/report_config.yaml`**: Reference ranges, thresholds, clinical rules

### Batch Processing Architecture

**BatchProcessor** (`src/batch_processor.py`) orchestrates multi-sample, multi-language report generation:

**Key Features:**
- Directory scanning or manifest-based processing
- Parallel sample processing (default: 4 workers)
- Sequential language processing per sample
- Built-in validation (species count, required phyla, unassigned percentage)
- Progress tracking and summary reporting

**Processing Flow:**
```
For each CSV file:
  1. Validate CSV format and quality thresholds
  2. Extract patient info (from manifest or filename)
  3. For each language:
     a. Call generate_clean_report(csv, patient, output_path, language)
     b. Track success/failure per language
  4. Continue to next sample (errors don't block batch)

Output: {sample_stem}_report_{lang}.pdf (e.g., sample_001_report_en.pdf)
```

**Configuration:**
```python
from src.batch_processor import BatchProcessor, BatchConfig

config = BatchConfig(
    data_dir='data/',               # CSV input directory
    reports_dir='reports/',         # PDF output directory
    languages=['en', 'pl', 'ja'],   # Target languages
    parallel_processing=True,       # Process samples in parallel
    workers=4,                      # Number of parallel workers
    min_species_count=10,           # Validation threshold
    max_unassigned_percentage=50.0, # Validation threshold
    required_phyla=['Bacillota', 'Bacteroidota', 'Pseudomonadota']
)

processor = BatchProcessor(config)
results = processor.process_directory()  # or process_from_manifest('manifest.csv')
```

### Template System (Current Production)
- **`templates/clean/`**: Production HTML templates (5 pages)
  - `page1_sequencing.html`: Sequencing results and species charts
  - `page2_phylum.html`: Phylum distribution analysis
  - `page3_clinical.html`: Clinical interpretation and recommendations
  - `page4_summary.html`: Summary and dysbiosis assessment
  - `page5_species_list.html`: Complete species list table
  - `styles.css`: Consistent styling and page layout
  - `report_clean.html`: Master template combining all pages

**Template Rendering Process:**
1. Load 5 page templates individually
2. Render each page with Jinja2 (patient data, charts, microbiome data)
3. Combine rendered pages into master template (`report_clean.html`)
4. Embed CSS via `{{ css_content }}` variable
5. If language != 'en': translate final HTML (not individual templates)
6. Pass complete HTML to WeasyPrint for PDF generation

**Key Variables Available in Templates:**
- `{{ patient.name }}`, `{{ patient.age }}`, `{{ patient.sample_number }}`
- `{{ data.species_list }}`, `{{ data.phylum_distribution }}`
- `{{ data.dysbiosis_index }}`, `{{ data.dysbiosis_category }}`
- `{{ data.clinical_interpretation }}`, `{{ data.recommendations }}`
- `{{ chart_paths.species }}`, `{{ chart_paths.phylum }}`, `{{ chart_paths.comparison }}`

### Clinical Filtering Architecture
The pipeline implements sophisticated filtering to address HippoVet+'s needs:
- **Kingdom-based exclusion**: Removes Plantae, Archaea (non-veterinary relevant)
- **Clinical relevance scoring**: HIGH (pathogens), MODERATE (opportunistic), LOW (commensal)
- **Database-specific rules**: Different filters for PlusPFP-16, EuPathDB, Viral databases
- **Semi-automated curation**: Excel export for manual review, import corrections
- **Equine pathogen database**: Curated list of clinically relevant species

### Multi-Language Report Generation

**Translation Architecture:**

The system uses a sophisticated translation pipeline that preserves scientific terminology:

**Core Components:**
- **`src/translation_service.py`**: Base translation service with caching
- **`src/translation/free_translation_service.py`**: Free translation using deep-translator (default) or googletrans (fallback)
- **`src/translation/scientific_glossary.py`**: 40+ curated terms (phyla, species, medical terms)
- **`src/translation/html_content_translator.py`**: HTML translation with term protection

**Translation Process:**
1. Parse final HTML and identify translatable text nodes
2. Protect scientific terms using glossary (replace with placeholders)
3. Translate text using deep-translator API (free, no API key)
4. Restore protected terms in target language
5. Rebuild HTML with translated content
6. Cache translation by MD5 hash in `translation_cache/translation_cache.json`

**Supported Languages:**
- English (en) - baseline, no translation
- Polish (pl) - fully tested
- Japanese (ja) - fully tested
- Others: de, es, fr, it, pt, ru, zh, ko (configurable, untested)

**Scientific Term Protection:**
Protected terms are NOT translated (preserved in Latin/English):
- Bacterial phyla: Actinomycetota, Bacillota, Bacteroidota, Pseudomonadota, Fibrobacterota
- Genus/species names: Lactobacillus, Streptococcus, Escherichia coli, etc.
- Medical terms: dysbiosis, microbiome, microbiota, 16S rRNA
- Veterinary terms: equine, fecal, gastrointestinal

**File Naming Convention:**
`{sample_stem}_report_{lang}.pdf` (e.g., `Montana_report_en.pdf`, `Montana_report_pl.pdf`)

### NCBI Download Integration
For testing and demonstration purposes:
- **`src/ncbi_downloader.py`**: Downloads FASTQ files from NCBI SRA
- **`scripts/ncbi_batch_pipeline.py`**: Orchestrates download → processing → PDF
- **`config/ncbi_samples.yaml`**: Configuration for SRA accessions
- **Dual-mode download**: SRA Toolkit (preferred) or direct ENA FTP (fallback)
- **Metadata extraction**: Automatic fetching of organism, platform, library info from NCBI
- **Batch organization**: Downloads organized into barcode directories for pipeline compatibility

## Data Processing Pipeline

### CSV Processing Flow (`src/csv_processor.py`)

The CSVProcessor is the core data transformation engine:

**Input:** CSV with species, read counts, taxonomy
**Output:** MicrobiomeData object with calculated metrics

**Processing Steps:**
1. **Load CSV** with pandas
2. **Auto-detect barcode column** (first column starting with 'barcode')
3. **Filter eukaryotes:**
   - Method 1: Use `superkingdom=='Bacteria'` if column exists (preferred)
   - Method 2: Exclude known eukaryote species from hardcoded list (fallback)
4. **Calculate percentages** from read counts (after eukaryote filtering)
5. **Build species list** with genus/phylum from taxonomy columns
6. **Calculate phylum distribution** (all bacterial phyla with percentages)
7. **Calculate dysbiosis index** (DI-relevant phyla only: Actinomycetota, Bacillota, Bacteroidota, Pseudomonadota)
8. **Filter phylum display** (DI phyla + "Other bacterial phyla" for charts/tables)
9. **Return MicrobiomeData** with species, phyla, DI, interpretation

**Critical Design Decisions:**
- **Barcode auto-detection**: No need to specify column name manually
- **Eukaryote filtering first**: Ensures bacterial percentages sum to 100%
- **Dual phylum distributions**: Raw (for DI calculation) vs. Display (for charts)
- **"Other bacterial phyla"**: Non-DI phyla grouped to reduce chart clutter

## Data Formats and Configuration

### CSV Input Format
**Required columns**: `species`, `phylum`, `genus`, `barcode[N]` (where N is sample number)

**Optional but recommended**: `superkingdom` (for accurate bacteria-only filtering)

```csv
species,barcode45,barcode46,...,phylum,genus,superkingdom
Streptomyces sp.,27,45,...,Actinomycetota,Streptomyces,Bacteria
Lactobacillus sp.,156,23,...,Bacillota,Lactobacillus,Bacteria
Saccharomyces cerevisiae,10,5,...,Ascomycota,Saccharomyces,Eukaryota
```

**Critical phylum names** (must match exactly for dysbiosis index):
- `Actinomycetota`, `Bacillota`, `Bacteroidota`, `Pseudomonadota`, `Fibrobacterota`

**Barcode Column Detection:**
- System automatically finds first column starting with 'barcode'
- Multiple barcode columns supported (e.g., barcode45, barcode46, barcode47)
- Manual specification via `barcode_column` parameter if needed

### Data Models (`src/data_models.py`)
```python
@dataclass
class PatientInfo:
    name: str = "Unknown"
    age: str = "Unknown"
    sample_number: str = "001"
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"

@dataclass
class MicrobiomeData:
    species_list: List[Dict]           # [{name, percentage, phylum}, ...]
    phylum_distribution: Dict[str, float]  # {phylum: percentage}
    dysbiosis_index: float
    dysbiosis_category: str           # normal, mild, severe
    clinical_interpretation: str
    recommendations: List[str]
```

### Configuration (`config/report_config.yaml`)
```yaml
reference_ranges:
  Actinomycetota: [0.1, 8.0]
  Bacillota: [20.0, 70.0]
  Bacteroidota: [4.0, 40.0]
  Pseudomonadota: [2.0, 35.0]

dysbiosis_thresholds:
  normal: 20    # Index < 20 = normal
  mild: 50      # Index 20-50 = mild, >50 = severe
```

## Environment Configuration

### Required Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
# Kraken2 Database Paths
KRAKEN2_DB_PATH=/path/to/k2_pluspfp_16gb
KRAKEN2_SILVA_DB=/path/to/EuPathDB  # Optional: parasites
KRAKEN2_VIRAL_DB=/path/to/Viral     # Optional: viruses

# Clinical Filtering
MIN_ABUNDANCE_THRESHOLD=0.01
PLUSPFP16_EXCLUDE_KINGDOMS=Plantae,Archaea
CLINICAL_RELEVANCE_THRESHOLD=0.1

# Output Directories
DEFAULT_OUTPUT_DIR=/path/to/results
EXCEL_REVIEW_DIR=/path/to/excel_review
PDF_OUTPUT_DIR=/path/to/pdf_reports

# Optional: LLM Integration
ENABLE_LLM_RECOMMENDATIONS=false
LLM_PROVIDER=none
```

### Path Conventions
The system uses WSL2 path format: `/mnt/c/Users/${USER}/hippovet/...`
Adjust for your environment or use relative paths.

## LLM-Powered Recommendations

### Setup (Optional)
1. Copy `.env.example` to `.env` and add API keys
2. Install: `poetry install --with llm`
3. Enable: Set `ENABLE_LLM_RECOMMENDATIONS=true` in `.env`

### Usage
```python
from src.llm_recommendation_engine import create_recommendation_engine

engine = create_recommendation_engine()
results = engine.process_sample(microbiome_data, patient_info)
```

Supports OpenAI, Anthropic Claude, and Google Gemini with 8 clinical templates for different dysbiosis patterns.

## Key File Locations

### Core Pipeline Scripts
- **`scripts/full_pipeline.py`**: Complete FASTQ-to-PDF orchestrator (main production script)
- **`scripts/generate_clean_report.py`**: CSV-to-PDF report generation with WeasyPrint
- **`scripts/batch_clinical_processor.py`**: Batch processing with clinical filtering
- **`scripts/generate_clinical_excel.py`**: Create Excel files for manual curation
- **`scripts/ncbi_batch_pipeline.py`**: Download from NCBI SRA and batch process (for testing)

### Core Modules
- **`src/data_models.py`**: `PatientInfo` and `MicrobiomeData` dataclasses
- **`src/kraken2_classifier.py`**: Kraken2 integration and taxonomy mapping
- **`src/clinical_filter.py`**: Veterinary-specific filtering rules and pathogen database
- **`src/csv_processor.py`**: CSV parsing, phylum aggregation, dysbiosis calculations
- **`src/chart_generator.py`**: Matplotlib/Seaborn chart generation
- **`src/kraken2_to_csv.py`**: Convert Kraken2 reports to CSV format
- **`src/ncbi_downloader.py`**: Download FASTQ files from NCBI SRA (for testing)

### Templates and Configuration
- **`templates/clean/`**: Production HTML templates (5-page reports)
- **`config/report_config.yaml`**: Reference ranges, thresholds, clinical rules
- **`config/ncbi_samples.yaml`**: SRA accession configuration for NCBI downloads
- **`.env.example`**: Environment configuration template

### Validation and Testing
- **`scripts/validate_csv_format.py`**: CSV format validation
- **`scripts/validate_client_data.py`**: Data integrity checks
- **`scripts/validate_fastq_pipeline.py`**: FASTQ pipeline validation
- **`scripts/test_installation.py`**: Installation verification

### Interactive Notebooks
- **`notebooks/batch_processing.ipynb`**: Interactive batch processing
- **`notebooks/fastq_processing_pipeline.ipynb`**: FASTQ workflow examples
- **`notebooks/llm_recommendation_engine.ipynb`**: LLM integration examples
- **`notebooks/template_translation.ipynb`**: Translation workflows

### Legacy Code
- **`legacy/`**: Original implementation (for reference only, not production)

## Important Architectural Patterns

### Module Dependencies and Import Structure

**Scripts Package:**
The `scripts/` directory is a Python package (has `__init__.py`) that can be imported:
```python
from scripts.generate_clean_report import generate_clean_report
```

**Src Package:**
Core modules in `src/` follow standard imports:
```python
from src.data_models import PatientInfo, MicrobiomeData
from src.batch_processor import BatchProcessor, BatchConfig
from src.csv_processor import CSVProcessor
```

**DO NOT** use `sys.path.append()` for imports - all directories are proper packages.

### Chart Generation and Cleanup

**Chart Lifecycle:**
1. `ChartGenerator` creates PNG files in `temp_charts/` directory
2. Charts embedded in HTML via file paths
3. WeasyPrint reads PNG files during PDF generation
4. **Charts are NOT auto-deleted** - manual cleanup or reuse on next run

**Chart Types:**
- `species_distribution.png` - Top 10 species bar chart
- `phylum_distribution.png` - Phylum composition pie chart
- `phylum_comparison.png` - DI phyla vs reference ranges

### Configuration Hierarchy

**Precedence (highest to lowest):**
1. **Command-line arguments** - Override everything
2. **BatchConfig object** - Programmatic configuration
3. **Environment variables** (.env file) - Database paths, thresholds
4. **report_config.yaml** - Reference ranges, clinical rules
5. **Code defaults** - Fallback values

**Example:**
```python
# .env has KRAKEN2_DB_PATH=/path/to/db
# report_config.yaml has dysbiosis_threshold: 20

# Command-line overrides both:
python scripts/full_pipeline.py --kraken2-db /other/db  # Uses /other/db, not .env
```

### Parallel vs Sequential Processing

**Batch Processing:**
- **Samples**: Processed in parallel (ProcessPoolExecutor, default 4 workers)
- **Languages**: Processed sequentially per sample (avoids translation API rate limits)

**Example with 4 samples, 3 languages:**
```
Time with parallelization: ~55 seconds
  - 4 samples processed simultaneously
  - Each sample: 3 languages × ~5 seconds = ~15 seconds

Time without parallelization: ~180 seconds
  - 12 total reports × ~15 seconds each
```

### Translation Caching Strategy

**Cache Key:** MD5 hash of source text
**Cache Storage:** `translation_cache/translation_cache.json`
**Cache Behavior:**
- Persistent across runs
- Shared across all samples and languages
- Reduces API calls by ~90% on repeated text
- Safe to delete (will regenerate on next run)

**When to Clear Cache:**
- Translation quality issues
- Glossary terms updated
- Switching translation providers

## Common Issues and Solutions

### Kraken2 Database Issues
1. **Database not found**: Set `KRAKEN2_DB_PATH` in `.env` to correct location
2. **Memory errors**: Use `KRAKEN2_MEMORY_MAPPING=false` or increase available RAM
3. **Database permissions**: Ensure read access to database directory
4. **Missing hash.k2d files**: Rebuild database with `kraken2-build`

### Clinical Filtering Issues
1. **Too many plants**: Check `PLUSPFP16_EXCLUDE_KINGDOMS` includes "Plantae"
2. **Missing pathogens**: Review `src/clinical_filter.py` pathogen database
3. **Excel export fails**: Ensure `EXCEL_REVIEW_DIR` is writable
4. **Incorrect relevance scores**: Adjust `CLINICAL_RELEVANCE_THRESHOLD` in `.env`

### Report Generation Failures
1. **CSV format errors**: Validate with `scripts/validate_csv_format.py`
2. **Phylum names**: Must use modern taxonomy (e.g., "Bacillota" not "Firmicutes")
3. **Missing charts**: Check `temp_charts/` directory exists and is writable
4. **PDF generation fails**: Verify WeasyPrint installation (requires system libraries)
5. **Template errors**: Check Jinja2 syntax in `templates/clean/`

### Development Workflow Best Practices
1. **Environment setup**: Copy `.env.example` to `.env` before first run
2. **Test incrementally**: Start with CSV → PDF, then add Kraken2, then full pipeline
3. **Use validation scripts**: Run `scripts/test_installation.py` after setup
4. **Check logs**: Review console output for detailed error messages
5. **Interactive debugging**: Use Jupyter notebooks in `notebooks/` for step-by-step testing
6. **Mock mode**: Set `USE_MOCK_KRAKEN=true` to test without Kraken2 database

### WSL2-Specific Notes
- Use `/mnt/c/` prefix for Windows paths
- Kraken2 database typically at `/mnt/c/Users/${USER}/hippovet/epi2melabs/data/`
- Ensure Windows filesystem paths are accessible from WSL2
- Use `wslpath` command to convert between Windows and WSL2 paths

### NCBI Download Issues
1. **SRA Toolkit not found**: Install with `conda install -c bioconda sra-tools` or script will fallback to ENA FTP
2. **Download timeout**: Large FASTQ files may take time; increase timeout in `ncbi_downloader.py`
3. **ENA FTP URLs fail**: Some accessions have non-standard naming; SRA Toolkit is more reliable
4. **Metadata fetch fails**: Check internet connectivity to NCBI E-utilities
5. **No FASTQ files found**: Verify the accession is for Amplicon/16S data, not WGS or other types

### Multi-Language Processing Issues
1. **Translation fails**: Check internet connection - uses online translation service
2. **Polish/Japanese characters broken**: Ensure UTF-8 encoding in PDF generation
3. **Scientific terms translated**: Add terms to glossary in `src/translation_service.py`
4. **One language fails but others succeed**: Pipeline continues; check logs for specific error
5. **Slow batch processing**: Translation adds 5-10 seconds per language per report
6. **Missing translations**: Free service has rate limits; add delays or use paid API

### Multi-Language Workflow Tips
1. **Test with English first**: Ensure report generation works before adding translations
2. **Start with two languages**: Test en + pl or en + ja before full batch
3. **Check sample output**: Verify translations are correct with veterinary expert
4. **Parallel processing**: Samples processed in parallel, languages sequential per sample
5. **Client workflow**: EPI2ME FASTQ → full_pipeline.py → Multi-language PDFs
6. **File organization**: All languages for one sample grouped together in output directory

### NCBI Workflow Tips
1. **Finding equine datasets**: Search NCBI SRA for "equine microbiome 16S" or "horse gut amplicon"
2. **Verify before download**: Check accession metadata on NCBI website first
3. **Test with one sample**: Download single accession before batch processing
4. **Use config file**: Easier to manage multiple samples with `config/ncbi_samples.yaml`
5. **Download-only mode**: Test downloads first with `--download-only` flag
6. **SRA Toolkit setup**: Configure with `vdb-config --interactive` for optimal performance

### Conda Environment Issues (Linux)

**Problem**: Environment creation fails with errors like "excluded by strict repo priority", "nothing provides __win", or "package conflicts"

**Root Cause**: The `environment.yml` file contains platform-specific packages and exact version pins that may not work on all Linux systems.

**Solutions**:

1. **Use `environment_linux.yml` instead** (Recommended for Linux):
   ```bash
   conda env create -f environment_linux.yml
   conda activate equine-microbiome
   ```
   This file uses version ranges and no platform-specific dependencies.

2. **Switch to Poetry** (Best option for cross-platform compatibility):
   ```bash
   # Remove any existing conda environment
   conda env remove -n equine-microbiome

   # Install with Poetry instead
   poetry install
   poetry shell
   ```
   Poetry is platform-independent and handles dependencies more reliably.

3. **Relax conda channel priority** (If you must use original environment.yml):
   ```bash
   conda config --set channel_priority flexible
   conda env create -f environment.yml --force
   ```

**Git Merge Conflict with `translation_cache/`**:

If you see:
```
error: The following untracked working tree files would be overwritten by merge:
translation_cache/translation_cache.json
```

**Solution**:
```bash
# Option 1: Remove the cache (safe - will regenerate)
rm -rf translation_cache/

# Option 2: Stash temporarily
git stash --include-untracked
git pull
git stash pop
```

The `.gitignore` has been updated to prevent this issue in future pulls.

**For complete Linux installation instructions**, see [docs/LINUX_INSTALLATION.md](docs/LINUX_INSTALLATION.md).