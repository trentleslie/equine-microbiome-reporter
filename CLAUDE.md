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

# Process specific barcodes only
poetry run python scripts/full_pipeline.py --input-dir data/ --output-dir results/ --barcodes barcode04,barcode05

# With custom Kraken2 database
poetry run python scripts/full_pipeline.py --input-dir data/ --output-dir results/ --kraken2-db /path/to/db

# Batch processing (interactive)
poetry run jupyter notebook notebooks/batch_processing.ipynb
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
8. **PDF Generation**: WeasyPrint converts HTML to professional 5-page PDF
9. **Output**: Laboratory-ready report with clinical interpretations

### Key Components
- **`src/data_models.py`**: Core data classes - `PatientInfo` and `MicrobiomeData`
- **`src/kraken2_classifier.py`**: Kraken2 integration with taxonomy mapping
- **`src/clinical_filter.py`**: Veterinary-specific filtering rules (removes plants, identifies pathogens)
- **`src/csv_processor.py`**: CSV parsing, phylum aggregation, dysbiosis calculations
- **`src/chart_generator.py`**: Matplotlib/Seaborn visualizations
- **`scripts/generate_clean_report.py`**: Main report orchestrator using WeasyPrint
- **`scripts/full_pipeline.py`**: End-to-end FASTQ-to-PDF pipeline coordinator
- **`config/report_config.yaml`**: Reference ranges, thresholds, clinical rules

### Template System (Current Production)
- **`templates/clean/`**: Production HTML templates (5 pages)
  - `page1_sequencing.html`: Sequencing results and species charts
  - `page2_phylum.html`: Phylum distribution analysis
  - `page3_clinical.html`: Clinical interpretation and recommendations
  - `page4_summary.html`: Summary and dysbiosis assessment
  - `page5_species_list.html`: Complete species list table
  - `styles.css`: Consistent styling and page layout
  - `report_clean.html`: Master template combining all pages

### Clinical Filtering Architecture
The pipeline implements sophisticated filtering to address HippoVet+'s needs:
- **Kingdom-based exclusion**: Removes Plantae, Archaea (non-veterinary relevant)
- **Clinical relevance scoring**: HIGH (pathogens), MODERATE (opportunistic), LOW (commensal)
- **Database-specific rules**: Different filters for PlusPFP-16, EuPathDB, Viral databases
- **Semi-automated curation**: Excel export for manual review, import corrections
- **Equine pathogen database**: Curated list of clinically relevant species

## Data Formats and Configuration

### CSV Input Format
**Required columns**: `species`, `phylum`, `genus`, `barcode[N]` (where N is sample number)

```csv
species,barcode45,barcode46,...,phylum,genus
Streptomyces sp.,27,45,...,Actinomycetota,Streptomyces
Lactobacillus sp.,156,23,...,Bacillota,Lactobacillus
```

**Critical phylum names** (must match exactly):
- `Actinomycetota`, `Bacillota`, `Bacteroidota`, `Pseudomonadota`, `Fibrobacterota`

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

### Core Modules
- **`src/data_models.py`**: `PatientInfo` and `MicrobiomeData` dataclasses
- **`src/kraken2_classifier.py`**: Kraken2 integration and taxonomy mapping
- **`src/clinical_filter.py`**: Veterinary-specific filtering rules and pathogen database
- **`src/csv_processor.py`**: CSV parsing, phylum aggregation, dysbiosis calculations
- **`src/chart_generator.py`**: Matplotlib/Seaborn chart generation
- **`src/kraken2_to_csv.py`**: Convert Kraken2 reports to CSV format

### Templates and Configuration
- **`templates/clean/`**: Production HTML templates (5-page reports)
- **`config/report_config.yaml`**: Reference ranges, thresholds, clinical rules
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