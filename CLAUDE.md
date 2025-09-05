# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Equine Microbiome Reporter** - An automated PDF report generation system for equine gut microbiome analysis from 16S rRNA sequencing data. Uses a Jinja2-based template architecture to transform CSV data into professional veterinary laboratory reports.

**Current Status:** Production-ready with English reports. Polish and Japanese translations pending.

**Key Points:**
- Private project for HippoVet+ veterinary laboratory
- Focus on practical implementation over documentation
- Uses new Jinja2 architecture (legacy code in `legacy/` directory)

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
# Quick report generation (most common task)
poetry run python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

patient = PatientInfo(name='Montana', sample_number='506')
generator = ReportGenerator(language='en')
success = generator.generate_report('data/sample_1.csv', patient, 'report.pdf')
print('✅ Success!' if success else '❌ Failed!')
"

# Batch processing (interactive)
poetry run jupyter notebook notebooks/batch_processing.ipynb

# FASTQ processing pipeline
poetry run python -c "
from src.pipeline_integrator import MicrobiomePipelineIntegrator
from src.data_models import PatientInfo

pipeline = MicrobiomePipelineIntegrator(output_dir='pipeline_output')
results = pipeline.process_sample('sample.fastq.gz', PatientInfo(name='Test'), 'en')
"
```

### Testing and Validation
```bash
# Run formal test suite
poetry run pytest tests/ --cov=src --cov-report=html

# Quick validation checks
poetry run python -c "import src.report_generator; print('✅ Core imports working')"

# Validate CSV format
poetry run python scripts/validate_csv_format.py data/sample.csv [barcode_column]

# Check template syntax
poetry run python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates/en'))
template = env.get_template('report_full.j2')
print('✅ Template syntax valid')
"
```

## Architecture Overview

### Core Processing Pipeline
1. **CSV → Data Models**: `CSVProcessor` loads CSV and creates `PatientInfo` + `MicrobiomeData` objects
2. **Clinical Analysis**: Calculates dysbiosis index and categorizes results (normal/mild/severe)
3. **Template Rendering**: Jinja2 processes language-specific templates with data context
4. **PDF Generation**: `PDFBuilder` converts HTML to professional PDF using ReportLab
5. **Output**: 5-page veterinary laboratory report

### Key Components
- **`src/data_models.py`**: Two main classes - `PatientInfo` and `MicrobiomeData`
- **`src/report_generator.py`**: Main orchestrator coordinating all steps
- **`src/csv_processor.py`**: CSV parsing and dysbiosis calculations
- **`src/pdf_builder.py`**: HTML-to-PDF conversion with ReportLab
- **`config/report_config.yaml`**: Reference ranges, thresholds, colors

### Template System
- **`templates/base/`**: Shared layout components (header, footer, styles)
- **`templates/en/`**: English templates (complete)
- **`templates/pl/`, `templates/jp/`**: Polish and Japanese (ready for translation)
- **Template structure**: 5-page reports using Jinja2 with modular components

### Additional Features
- **FASTQ Pipeline**: `src/pipeline_integrator.py` - raw sequencing data to PDF
- **Batch Processing**: `src/batch_processor.py` - multiple samples with validation
- **LLM Integration**: `src/llm_recommendation_engine.py` - AI-enhanced recommendations
- **Translation System**: `src/translation_service.py` - multi-language support

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

## Multi-Language Support

### Available Languages
- **✅ English** (`templates/en/`): Complete implementation
- **🚧 Polish** (`templates/pl/`): Ready for translation
- **🚧 Japanese** (`templates/jp/`): Ready for translation

### Language Selection
```python
# English (available)
generator = ReportGenerator(language="en")

# Other languages after translation
generator = ReportGenerator(language="pl")  # Polish
generator = ReportGenerator(language="jp")  # Japanese
```

### Translation Workflow
Use `notebooks/template_translation.ipynb` for automated translation with scientific glossary preservation.

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

### Core Components
- **`src/report_generator.py`**: Main entry point and orchestrator
- **`src/data_models.py`**: PatientInfo and MicrobiomeData classes
- **`src/csv_processor.py`**: CSV parsing and dysbiosis calculations  
- **`src/pdf_builder.py`**: HTML-to-PDF conversion
- **`config/report_config.yaml`**: Reference ranges and thresholds

### Templates and Configuration
- **`templates/en/`**: English templates (complete)
- **`templates/pl/`, `templates/jp/`**: Other languages (ready for translation)
- **`.env.example`**: LLM API configuration template

### Processing Pipelines
- **`src/pipeline_integrator.py`**: FASTQ-to-PDF pipeline
- **`src/batch_processor.py`**: Multi-file processing
- **`notebooks/batch_processing.ipynb`**: Interactive batch processing

### Utilities and Examples
- **`scripts/validate_csv_format.py`**: CSV format validation
- **`notebooks/`**: Interactive examples and workflows
- **`legacy/`**: Original implementation (for reference only)

## Common Issues and Solutions

### Report Generation Failures
1. **CSV format**: Check for required columns (`species`, `barcode[N]`, `phylum`, `genus`)
2. **Phylum names**: Must match reference ranges exactly (e.g., "Bacillota" not "Firmicutes")
3. **Patient info**: Ensure all required PatientInfo fields are provided
4. **Template errors**: Check Jinja2 syntax in `templates/en/`

### Development Workflow
1. Use `poetry shell` to activate environment
2. Test with single report generation first
3. Validate CSV format using `scripts/validate_csv_format.py`
4. Use interactive notebooks for batch processing
5. Run `pytest tests/` for comprehensive testing