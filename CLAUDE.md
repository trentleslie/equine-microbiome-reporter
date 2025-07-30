# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Equine Microbiome Reporter** - An automated PDF report generation system for equine gut microbiome analysis from 16S rRNA sequencing data. The system uses a **Jinja2-based template architecture** to transform raw bacterial abundance CSV data into professional veterinary laboratory reports supporting multiple languages (English, Polish, Japanese).

**Current Status:** Production-ready with English reports. Polish and Japanese translations pending.

**Key Points for Claude:**
- This is a **private project** for HippoVet+ veterinary laboratory - no open source contributions
- Focus on **practical implementation** over documentation unless explicitly requested
- The system has two parallel architectures: new Jinja2 (active) and legacy (archived)
- Always use the new architecture unless specifically working with legacy code

## Development Commands

### Current Architecture (Jinja2-based)

```bash
# Install dependencies (core)
poetry install

# Install with optional dependencies
poetry install --with dev                    # Jupyter notebooks and development tools
poetry install --with llm                   # LLM support (OpenAI, Anthropic, Gemini)
poetry install --with translation           # Google Cloud Translation (API key required)
poetry install --with translation-free      # Free translation services (no API key)

# Activate virtual environment
poetry shell

# Generate report using new Jinja2 architecture
poetry run python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

# Create patient info
patient = PatientInfo(
    name='Montana', 
    age='20 years', 
    sample_number='506',
    performed_by='Julia Kończak',
    requested_by='Dr. Alexandra Matusiak'
)

# Generate English report
generator = ReportGenerator(language='en')
success = generator.generate_report(
    csv_path='data/sample_1.csv',
    patient_info=patient,
    output_path='reports/montana_report_en.pdf'
)
print('✅ Success!' if success else '❌ Failed!')
"

# Process FASTQ files (requires biopython)
poetry run python -c "
from src.pipeline_integrator import MicrobiomePipelineIntegrator
from src.data_models import PatientInfo

pipeline = MicrobiomePipelineIntegrator(output_dir='pipeline_output')
patient = PatientInfo(name='Montana', sample_number='506')
results = pipeline.process_sample('sample.fastq.gz', patient, language='en')
"

# Run interactive batch processing
poetry run jupyter notebook notebooks/batch_processing.ipynb

# Generate Polish report (Week 2)
# generator = ReportGenerator(language='pl')

# Generate Japanese report (Week 2)  
# generator = ReportGenerator(language='jp')
```

### Legacy Commands (Archived)

```bash
# Legacy generators (moved to legacy/ directory)
poetry run python legacy/enhanced_pdf_generator_en.py data/sample.csv -o reports/legacy_report.pdf

# Legacy web app (Phase 2)
./legacy/run_web_app.sh

# Legacy batch processing (to be updated for new architecture)
poetry run python batch_processor.py -m manifest.csv -o reports/
```

### Testing and Quality Checks

```bash
# No formal test suite - validate by running generation commands
# Check if dependencies work correctly
poetry run python -c "import src.report_generator; print('✅ Core imports working')"

# Validate sample data processing
poetry run python -c "
from src.csv_processor import CSVProcessor
processor = CSVProcessor()
try:
    data = processor.load_csv('data/sample_1.csv', 'barcode59')  # Adjust barcode as needed
    print(f'✅ CSV loaded: {len(data)} species')
except Exception as e:
    print(f'❌ CSV validation failed: {e}')
"

# Check template syntax
poetry run python -c "
from jinja2 import Environment, FileSystemLoader
import os
if os.path.exists('templates/en'):
    env = Environment(loader=FileSystemLoader('templates/en'))
    try:
        template = env.get_template('report_full.j2')
        print('✅ Template syntax valid')
    except Exception as e:
        print(f'❌ Template error: {e}')
"
```

## Architecture Overview (v2 - Jinja2 Template System)

**NEW ARCHITECTURE** - The system has been redesigned with a Jinja2-based template system for better maintainability and multi-language support:

### 1. Core Components
- **Data Models** (`src/data_models.py`): Simplified dataclasses - `PatientInfo` and `MicrobiomeData`
- **CSV Processor** (`src/csv_processor.py`): Converts CSV data to structured data models
- **Report Generator** (`src/report_generator.py`): Main orchestrator using Jinja2 templates
- **PDF Builder** (`src/pdf_builder.py`): ReportLab integration for PDF creation

### 2. Template System
- **Base Templates** (`templates/base/`): Layout, header, footer components
- **Language Templates** (`templates/en/`, `templates/pl/`, `templates/jp/`): Language-specific content
- **Page Templates** (`templates/*/pages/`): Individual page templates for 5-page structure

### 3. Configuration System
- **Report Config** (`config/report_config.yaml`): Reference ranges, thresholds, laboratory info
- **Template Selection**: Automatic language detection and template loading

### 4. Additional Components
- **FASTQ Processing** (`src/fastq_qc.py`, `src/fastq_converter.py`): Complete pipeline from raw sequencing data
- **LLM Integration** (`src/llm_recommendation_engine.py`): AI-powered clinical recommendations  
- **Translation System** (`src/translation_service.py`, `src/template_translator.py`): Multi-language support
- **Batch Processing** (`src/batch_processor.py`): Parallel processing with validation and progress tracking

### 5. Legacy Components (being phased out)
- **Enhanced PDF Generators** (`legacy/enhanced_pdf_generator*.py`): Original implementations for reference
- **Legacy Batch Processor** (`batch_processor.py`): Root-level script being updated for new architecture
- **Web Application** (`legacy/web_app.py`): Phase 2 enhancement

## New Processing Pipeline (Jinja2 Architecture)

1. **CSV Processing**: `CSVProcessor` loads and validates CSV data
2. **Data Modeling**: Converts raw data to `PatientInfo` + `MicrobiomeData` objects
3. **Clinical Analysis**: Calculates dysbiosis index, categorizes results, generates interpretations
4. **Template Rendering**: Jinja2 processes templates with data context for selected language
5. **PDF Generation**: `PDFBuilder` converts template output to professional PDF using ReportLab
6. **Output**: Final 5-page report matching reference design exactly

## Legacy Processing Pipeline (Original)

1. **CSV Data Loading**: Expects UTF-8 encoded CSV with columns: species, barcode[N], phylum, genus
2. **Barcode Selection**: Filters data for specific sample column (e.g., barcode59)
3. **Data Transformation**: Converts counts to percentages, aggregates by phylum
4. **Visualization**: Creates matplotlib charts for species distribution and phylum composition
5. **PDF Generation**: Uses reportlab for professional formatting
6. **Reference Analysis**: Compares phylum percentages against veterinary reference ranges

## Important Configuration

### New Configuration System (`config/report_config.yaml`):
```yaml
reference_ranges:
  Actinomycetota: [0.1, 8.0]
  Bacillota: [20.0, 70.0]
  Bacteroidota: [4.0, 40.0]
  Pseudomonadota: [2.0, 35.0]
  Fibrobacterota: [0.1, 5.0]

dysbiosis_thresholds:
  normal: 20
  mild: 50

colors:
  primary_blue: "#1E3A8A"
  green: "#10B981"
  teal: "#14B8A6"
```

### Legacy Phylum Reference Ranges (in `advanced_pdf_generator.py`):
```python
REFERENCE_RANGES = {
    'Actinomycetota': (0.1, 8),
    'Bacillota': (20, 70),
    'Bacteroidota': (4, 40),
    'Pseudomonadota': (2, 35)
}
```

### CSV Input Format Requirements:

**IMPORTANT**: The system supports two CSV formats. See `docs/csv_format_specification.md` for complete details.

#### Quick Reference:
- **Required columns**: `species`, `phylum`, `genus`, and at least one `barcode[N]` column
- **Column names**: Case-sensitive in CSVProcessor (expects capitalized: 'Species', 'Phylum', 'Genus')
  - Note: Current CSV files use lowercase, CSVProcessor handles with `.get()` fallback
- **Barcode format**: `barcode` followed by number (e.g., barcode59, barcode45)
- **Species names**: Scientific nomenclature (e.g., "Streptomyces albidoflavus")
- **Phylum names**: Must match reference ranges exactly:
  - `Actinomycetota` (0.1-8.0%)
  - `Bacillota` (20.0-70.0%)
  - `Bacteroidota` (4.0-40.0%)
  - `Pseudomonadota` (2.0-35.0%)
  - `Fibrobacterota` (0.1-5.0%)

#### Validation Tool:
```bash
# Validate CSV format
poetry run python scripts/validate_csv_format.py data/sample.csv [barcode_column]
```

### New Data Models (Jinja2 Architecture):
```python
# src/data_models.py
@dataclass
class PatientInfo:
    name: str = "Unknown"
    species: str = "Horse"
    age: str = "Unknown"
    sample_number: str = "001"
    date_received: str = "auto-generated"
    date_analyzed: str = "auto-generated"
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"

@dataclass
class MicrobiomeData:
    species_list: List[Dict[str, any]]  # [{name, percentage, phylum}, ...]
    phylum_distribution: Dict[str, float]  # {phylum: percentage}
    dysbiosis_index: float
    total_species_count: int
    dysbiosis_category: str  # normal, mild, severe
    clinical_interpretation: str
    recommendations: List[str]
    # Lab results for tables
    parasite_results: List[Dict]
    microscopic_results: List[Dict]
    biochemical_results: List[Dict]
    # Optional LLM content (Week 2)
    llm_summary: Optional[str] = None
```

### Legacy Patient Information Structure:
```python
patient_info = {
    'name': str,
    'species': str,
    'age': str,
    'sample_number': str,
    'date_received': str,
    'performed_by': str,
    'requested_by': str
}
```

## Multi-Language Support (New Architecture)

The Jinja2 template system supports multiple languages through separate template directories:

### Current Implementation:
- **✅ English** (`templates/en/`): Complete implementation for Week 1 MVP
  - `report_full.j2` - Master 5-page template
  - `clinical_text.j2` - Clinical interpretation templates
  - `recommendations.j2` - Dysbiosis-based recommendations
  - `educational.j2` - Educational content macros
  - `pages/` - Individual page templates (page1-page5)

### Week 2 Implementation:
- **🚧 Polish** (`templates/pl/`): Directory created, templates pending
- **🚧 Japanese** (`templates/jp/`): Directory created, templates pending

### Usage:
```python
# Generate English report (Week 1 - Available Now)
generator = ReportGenerator(language="en")
success = generator.generate_report(csv_path, patient_info, output_path)

# Generate Polish report (Week 2 - Template translation needed)
# generator = ReportGenerator(language="pl")

# Generate Japanese report (Week 2 - Template translation needed)
# generator = ReportGenerator(language="jp")
```

## Legacy Polish Language Support

The original system generates reports entirely in Polish, including:
- Clinical interpretations based on dysbiosis index
- Phylum distribution descriptions
- Analysis sections and recommendations
- All UI elements in the web application

When modifying legacy report text, ensure Polish language formatting and veterinary terminology are maintained.

## Common Tasks & Solutions

### Generate a Report Quickly
```bash
# Most common task - generate English report with minimal setup
poetry run python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

generator = ReportGenerator(language='en')
patient = PatientInfo(name='TestHorse', sample_number='001')
generator.generate_report('data/sample_1.csv', patient, 'test_report.pdf')
"
```

### Debug Report Generation Issues
1. **Check CSV format**: Ensure columns match: `species`, `barcode[N]`, `phylum`, `genus`
2. **Verify phylum names**: Must match reference ranges exactly (e.g., "Bacillota" not "Firmicutes")
3. **Template errors**: Check `templates/en/` for Jinja2 syntax issues
4. **PDF generation**: Look for ReportLab errors in stack trace

### Working with FASTQ Files
```python
# Convert FASTQ to CSV first
from src.fastq_converter import FASTQtoCSVConverter
converter = FASTQtoCSVConverter()
converter.convert_fastq_to_csv("sample.fastq.gz", "output.csv")

# Then generate report from CSV
```

### Batch Processing Best Practices
- Use the **interactive notebook** at `notebooks/batch_processing.ipynb` for visual progress
- Set validation thresholds in `BatchConfig` to catch data quality issues early
- Check `reports/batch_output/summary_report.json` for processing statistics

## Important File Locations

### When User Asks About...
- **"How do I generate a report?"** → Show code from this file's Quick Start section
- **"Where are the templates?"** → `templates/en/` (active), `templates/pl/` and `templates/jp/` (pending)
- **"How do I configure settings?"** → `config/report_config.yaml`
- **"Where are examples?"** → `notebooks/` directory has interactive examples
- **"What about the old system?"** → `legacy/` directory (archived, not for new development)
- **"How do I process FASTQ files?"** → Use `src/pipeline_integrator.py` or `notebooks/fastq_processing_pipeline.ipynb`
- **"How do I use LLM recommendations?"** → Set up API keys, use `src/llm_recommendation_engine.py` or `notebooks/llm_recommendation_engine.ipynb`
- **"How do I translate templates?"** → Use `notebooks/template_translation.ipynb`
- **"Where are test reports?"** → `docs/test_reports/` for documentation, `temp/test_output/` for generated artifacts
- **"Where are utility scripts?"** → `scripts/` for validation tools, `scripts/test_utilities/` for test runners

### Key Files to Know
- **Main entry point**: `src/report_generator.py`
- **Data processing**: `src/csv_processor.py` 
- **Clinical logic**: `src/csv_processor.py` (dysbiosis calculation)
- **PDF generation**: `src/pdf_builder.py`
- **Configuration**: `config/report_config.yaml`
- **FASTQ pipeline**: `src/pipeline_integrator.py`
- **Batch processing**: `src/batch_processor.py`
- **LLM recommendations**: `src/llm_recommendation_engine.py`

## Testing & Validation

### Quick Validation Checks
```python
# Validate CSV data before processing
from src.csv_processor import CSVProcessor
processor = CSVProcessor()
data = processor.load_csv("data/sample.csv", "barcode59")
print(f"Species count: {len(data)}")  # Should be > 10
print(f"Phyla: {set(row['phylum'] for row in data)}")  # Should include main phyla
```

### Common Validation Errors
- **"No data for barcode"**: Wrong barcode column name
- **"Invalid phylum"**: Phylum name doesn't match reference ranges
- **"PDF generation failed"**: Usually missing patient info or template error

## Performance Considerations

- **Large CSV files**: The system handles up to 1000 species efficiently
- **Batch processing**: Use parallel processing for > 10 files
- **LLM recommendations**: Cache responses to reduce API costs
- **Translation**: Use batch translation for multiple templates

## Troubleshooting Checklist

When something isn't working:
1. ✓ Correct Python environment? (`poetry shell`)
2. ✓ All dependencies installed? (`poetry install`)
3. ✓ CSV format correct? (check required columns)
4. ✓ Using correct architecture? (new Jinja2, not legacy)
5. ✓ Patient info complete? (all required fields)
6. ✓ Output directory exists? (create if needed)

## DO NOT's for Claude

1. **DON'T** create new documentation files unless explicitly requested
2. **DON'T** suggest open-source contribution workflows
3. **DON'T** mix legacy and new architecture code
4. **DON'T** modify `config/report_config.yaml` without careful consideration
5. **DON'T** assume FASTQ processing is always needed - most users work with CSV
6. **DON'T** create example or test files in the main directories