# Equine Microbiome Reporter

**Automated PDF report generation for equine gut microbiome analysis from 16S rRNA sequencing data.**

## 🔬 Overview

A Jinja2-based template architecture that transforms raw bacterial abundance CSV data into professional veterinary laboratory reports. The system generates comprehensive 5-page PDF reports featuring species distribution charts, phylum analysis, dysbiosis indices, and clinical interpretations.

**Key Features:** Professional PDF generation • Multi-language support (English, Polish, Japanese) • Automated clinical analysis • FASTQ processing pipeline • LLM-enhanced recommendations

## ✨ Core Capabilities

### Report Generation
- **Professional PDFs**: 5-page laboratory-standard reports with clinical analysis
- **Multi-Language**: English (complete), Polish & Japanese (translation-ready)
- **Jinja2 Templates**: Modular, maintainable template architecture
- **Clinical Intelligence**: Automated dysbiosis index calculation with veterinary reference ranges

### Data Processing
- **FASTQ Pipeline**: Complete workflow from raw sequencing data to PDF reports
- **Quality Control**: Phred scores, GC content, and read length analysis
- **Batch Processing**: Handle multiple samples with progress tracking and validation
- **Data Validation**: Automatic quality checks for species counts and phyla presence

### Advanced Features
- **LLM Integration**: AI-enhanced recommendations using OpenAI, Anthropic, or Google Gemini
- **Clinical Templates**: 8 standardized scenarios for different dysbiosis patterns
- **Translation System**: Automated multi-language translation with scientific glossary
- **Interactive Notebooks**: Jupyter-based workflows for batch processing and analysis

## 🏗️ Architecture

```
src/                          # Core modules
├── data_models.py           # PatientInfo + MicrobiomeData classes
├── csv_processor.py         # CSV → structured data conversion
├── report_generator.py      # Main orchestrator with Jinja2
├── pdf_builder.py          # ReportLab PDF generation
├── batch_processor.py      # Batch processing for multiple files
├── progress_tracker.py     # Progress tracking and QC reports
├── clinical_templates.py   # 8 standardized clinical templates
├── template_selector.py    # Data-driven template selection
├── llm_recommendation_engine.py  # LLM integration (OpenAI, Anthropic, Gemini)
├── fastq_qc.py             # FASTQ quality control analysis
├── fastq_converter.py      # FASTQ to CSV conversion
├── pipeline_integrator.py  # Complete FASTQ → PDF pipeline
├── translation_service.py  # Multi-language translation with glossary
└── template_translator.py  # Batch template translation workflow

templates/                   # Jinja2 templates
├── base/                   # Layout components
├── en/                     # English templates (Week 1)
├── pl/                     # Polish templates (Week 2)
└── jp/                     # Japanese templates (Week 2)

config/                     # YAML configuration
└── report_config.yaml     # Reference ranges, colors, settings
```

## 🚀 Getting Started

### Linux Installation (Recommended)

For Linux systems (Ubuntu/Debian), we recommend using **Poetry** for a clean, platform-independent installation:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Clone repository
git clone https://github.com/trentleslie/equine-microbiome-reporter.git
cd equine-microbiome-reporter

# Install dependencies
poetry install

# Activate environment
poetry shell

# Test installation
python scripts/test_installation.py
```

**See [docs/LINUX_INSTALLATION.md](docs/LINUX_INSTALLATION.md) for:**
- Complete step-by-step instructions
- System dependencies for WeasyPrint
- Alternative Conda installation
- Troubleshooting common issues

### Automated Setup Script (WSL2/Alternative)

Use our automated setup script for a complete installation with interactive configuration:

```bash
# One-line installation
wget https://raw.githubusercontent.com/trentleslie/equine-microbiome-reporter/main/setup.sh && chmod +x setup.sh && ./setup.sh
```

The setup script will:
- Install conda and git if needed
- Clone the repository
- Download test data (20MB) from Google Drive
- Create conda environment with all dependencies
- **Interactively configure your paths** (Kraken2 database, data directories, etc.)
- Generate a customized `.env` file
- Validate the installation
- Generate a demo PDF report

Total installation time: ~15-20 minutes

### Prerequisites

- Linux environment (native or WSL2)
- 20GB disk space (for Kraken2 database, if using)
- 8GB RAM minimum (16GB recommended)
- Python 3.9+ (for Poetry method)

### Key Dependencies

The conda environment includes all necessary packages:
- **Core**: pandas, numpy, matplotlib, jinja2, pyyaml, biopython
- **PDF Generation**: reportlab, weasyprint
- **Data Processing**: openpyxl, python-dotenv
- **Development**: jupyter notebook, tqdm

## 📚 Interactive Tutorials

After installation, use our interactive scripts to learn the pipeline:

### Tutorial Script - Learn the Concepts
```bash
# Activate environment
conda activate equine-microbiome

# Run interactive tutorial
./tutorial.sh
```

This educational walkthrough explains:
- Understanding FASTQ input data format
- How Kraken2 classification works
- Clinical filtering process (removing plant parasites, identifying pathogens)
- Report generation workflow
- Time savings (87% reduction in manual curation)

**Features**: Step-by-step explanations • Color-coded output • Press Enter to continue • Works with or without Kraken2 database

### Demo Script - See It In Action
```bash
# Run live demo with actual commands
./demo.sh
```

This script actually processes test data and shows:
- Real commands being executed
- Actual output files being created
- Processing time for each step
- Generated Excel and PDF reports

**Output**: Creates a timestamped `demo_output_*/` directory with all results

## ⚡ Quick Start

### Generate a Single Report

```python
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

# Create patient information
patient = PatientInfo(
    name="Montana",
    age="20 years", 
    sample_number="506",
    performed_by="Julia Kończak",
    requested_by="Dr. Alexandra Matusiak"
)

# Generate English report
generator = ReportGenerator(language="en")
success = generator.generate_report(
    csv_path="data/sample_1.csv",
    patient_info=patient,
    output_path="reports/montana_report.pdf"
)

print("✅ Success!" if success else "❌ Failed!")
```

### Command Line Usage

```bash
# Process test data with full pipeline
python scripts/full_pipeline.py --input-dir data --output-dir results

# Process specific barcodes
python scripts/full_pipeline.py --input-dir data --output-dir results --barcodes barcode04,barcode05,barcode06

# Process with Kraken2 database (if configured)
python scripts/full_pipeline.py \
  --input-dir /path/to/fastq \
  --output-dir results \
  --kraken2-db /path/to/database

# Get help on all options
python scripts/full_pipeline.py --help
```

## 🧬 FASTQ Processing Pipeline

### Process Raw Sequencing Data

The system now includes a complete pipeline for processing FASTQ files from 16S rRNA sequencing:

```python
from src.pipeline_integrator import MicrobiomePipelineIntegrator

# Initialize pipeline
pipeline = MicrobiomePipelineIntegrator(output_dir="pipeline_output")

# Process single FASTQ file
results = pipeline.process_sample(
    fastq_file="sample.fastq.gz",
    patient_info={
        'name': 'Montana',
        'age': '20 years',
        'sample_number': '506'
    },
    language="en"  # Generate English PDF
)
```

### Quality Control Analysis

```python
from src.fastq_qc import FASTQQualityControl

# Run QC analysis
qc = FASTQQualityControl("sample.fastq.gz")
qc_results = qc.run_qc()
qc.print_summary()
qc.plot_quality_metrics(save_path="qc_report.png")
```

### Batch Processing

#### Interactive Jupyter Notebook

The easiest way to process multiple files is using the batch processing notebook:

```bash
# Launch the batch processing notebook
jupyter notebook notebooks/batch_processing.ipynb
```

The notebook provides:
- 📊 Interactive progress tracking
- ✅ Automatic quality validation
- 📈 Summary statistics and reports
- 🎯 Simple point-and-click interface

#### Programmatic Batch Processing

```python
from src.batch_processor import BatchProcessor, BatchConfig

# Configure batch processing
config = BatchConfig(
    data_dir='data',
    reports_dir='reports/batch_output',
    language='en',
    parallel_processing=True
)

# Process all CSV files in directory
processor = BatchProcessor(config)
results = processor.process_directory(validate=True)

# Generate summary report
summary = processor.generate_summary_report()
print(f"Processed {summary['total_files']} files")
print(f"Success rate: {summary['success_rate']:.1f}%")
```

#### Manifest-Based Processing

```python
import pandas as pd

# Create manifest with patient information
manifest = pd.DataFrame({
    'csv_file': ['sample_1.csv', 'sample_2.csv'],
    'patient_name': ['Montana', 'Thunder'],
    'age': ['20 years', '15 years'],
    'sample_number': ['506', '507'],
    'performed_by': ['Julia Kończak', 'Julia Kończak'],
    'requested_by': ['Dr. Smith', 'Dr. Johnson']
})
manifest.to_csv('manifest.csv', index=False)

# Process using manifest
results = processor.process_from_manifest(Path('manifest.csv'))
```

### Pipeline Features

- **Quality Control**: Phred scores, read lengths, GC content analysis
- **Filtering**: Customizable quality thresholds (Q20/Q30)
- **Visualization**: QC plots and statistics
- **Integration**: Seamless connection to PDF generation

## 📊 Input Data Format

### FASTQ Files
- Standard 16S rRNA sequencing format
- Compressed (.gz) or uncompressed
- Automatically converts to abundance tables

### CSV Files
```csv
species,barcode45,barcode46,...,barcode78,phylum,genus
Streptomyces sp.,0,0,...,27,Actinomycetota,Streptomyces
Lactobacillus sp.,45,23,...,156,Bacillota,Lactobacillus
```

**Required**: `species`, `barcode[N]`, `phylum`, `genus` columns

## ⚙️ Configuration

Configuration is managed through `config/report_config.yaml`:

```yaml
# Reference ranges for dysbiosis calculation
reference_ranges:
  Actinomycetota: [0.1, 8.0]
  Bacillota: [20.0, 70.0]
  Bacteroidota: [4.0, 40.0]
  Pseudomonadota: [2.0, 35.0]

# Dysbiosis thresholds
dysbiosis_thresholds:
  normal: 20
  mild: 50

# Color scheme
colors:
  primary_blue: "#1E3A8A"
  green: "#10B981"
  teal: "#14B8A6"
```

## 🤖 LLM-Powered Recommendations

### Overview

The system includes an AI-powered recommendation engine that enhances clinical interpretations using Large Language Models (LLMs). The engine supports OpenAI, Anthropic Claude, and Google Gemini.

### Features

- **8 Clinical Templates**: Standardized scenarios for different dysbiosis patterns
- **Smart Selection**: Data-driven template selection based on microbiome analysis
- **Few-Shot Prompting**: Consistent, high-quality outputs
- **Multi-Provider Support**: Choose between OpenAI, Anthropic, or Google Gemini
- **Caching**: Reduces API costs with intelligent response caching
- **Fallback Support**: Works without LLM using template recommendations

### Setup

1. Copy `.env.example` to `.env`
2. Add your API key(s):
   ```env
   OPENAI_API_KEY=your-key-here
   ANTHROPIC_API_KEY=your-key-here
   GOOGLE_API_KEY=your-key-here
   
   LLM_PROVIDER=openai  # or anthropic, gemini
   ENABLE_LLM_RECOMMENDATIONS=true
   ```
3. LLM packages are included in the conda environment

### Usage

```python
from src.llm_recommendation_engine import create_recommendation_engine
from src.data_models import PatientInfo, MicrobiomeData

# Create recommendation engine
engine = create_recommendation_engine()

# Process sample with AI recommendations
results = engine.process_sample(
    microbiome_data=microbiome_data,
    patient_info=patient_info,
    clinical_history={"symptoms": "loose stools"}
)

# Results include template selection and personalized recommendations
print(f"Selected Template: {results['template_info']['title']}")
print(f"AI Recommendations: {results['recommendations']}")
```

### Clinical Templates

1. **Healthy Maintenance**: Normal microbiome
2. **Mild Imbalance**: Early intervention needed
3. **Bacteroidota Deficiency**: Fiber processing support
4. **Bacillota Excess**: Starch reduction protocol
5. **Pseudomonadota Excess**: Inflammatory response
6. **Acute Dysbiosis**: Intensive intervention
7. **Chronic Dysbiosis**: Long-term management
8. **Post-Antibiotic**: Microbiome restoration

For interactive examples, see the [LLM Recommendation Notebook](notebooks/llm_recommendation_engine.ipynb).

## 🌍 Multi-Language Support

### Current Implementation
- **✅ English**: Complete template set with clinical interpretations
- **🚧 Polish**: Translation system ready, templates pending translation
- **🚧 Japanese**: Translation system ready, templates pending translation

### Language Selection

```python
# English (available now)
generator = ReportGenerator(language="en")

# Polish (after translation)
generator = ReportGenerator(language="pl")

# Japanese (after translation)  
generator = ReportGenerator(language="ja")
```

### Template Translation System

The project includes an automated translation system that preserves scientific terminology:

```python
from src.translation_service import get_translation_service
from src.template_translator import TemplateTranslationWorkflow

# Use free translation service (no API key needed)
translation_service = get_translation_service("free")

# Translate all templates to Polish and Japanese
workflow = TemplateTranslationWorkflow(
    project_root=Path("."),
    translation_service=translation_service,
    target_languages=["pl", "ja"]
)
results = workflow.translate_all_templates()

# Create Excel files for expert review
workflow.create_review_spreadsheet("pl")
workflow.create_review_spreadsheet("ja")
```

Features:
- **Scientific Glossary**: Preserves bacterial names and medical terminology
- **Jinja2 Protection**: Maintains template syntax during translation
- **Excel Export**: Creates spreadsheets for veterinary expert review
- **Caching**: Reduces API costs by storing translations
- **Free Option**: Works without API keys using googletrans

For detailed usage, see the [Translation Notebook](notebooks/template_translation.ipynb).

## 📄 Generated Report Structure

Each 5-page PDF includes:

1. **Title Page**: Patient information, laboratory branding
2. **Sequencing Results**: Species distribution charts, dysbiosis index
3. **Clinical Analysis**: Interpretation and recommendations
4. **Laboratory Results**: Parasitological, microscopic, biochemical data
5. **Educational Content**: Microbiome health information

**Clinical Intelligence**: Automated dysbiosis calculation • Evidence-based recommendations • Veterinary reference ranges • Risk stratification (normal/mild/severe)

## 📁 Project Structure

```
equine-microbiome-reporter/
├── src/                    # Core modules and pipeline components
├── templates/              # Jinja2 templates (en/pl/jp)
├── config/                 # YAML configuration files
├── notebooks/              # Interactive Jupyter notebooks
├── data/                   # Sample CSV files
├── reports/                # Generated PDF outputs
├── pipeline_output/        # FASTQ processing results
├── assets/                 # Images and logos
├── docs/                   # Documentation
└── legacy/                 # Original implementation
```

## 📈 Development Status

### ✅ Complete
- **Core Architecture**: Jinja2 template system with multi-language support
- **English Reports**: Full 5-page PDF generation with clinical analysis
- **FASTQ Processing**: Complete pipeline from sequencing data to reports
- **Batch Processing**: Interactive notebooks with progress tracking
- **LLM Integration**: AI-powered recommendations with multiple providers
- **Translation System**: Automated translation with scientific glossary

### 🚧 In Progress
- **Polish Translation**: Template structure ready, translation pending
- **Japanese Translation**: Template structure ready, translation pending

### 🔮 Future Enhancements
- **Web Interface**: Browser-based report generation
- **Real-time Dashboard**: Processing status and analytics
- **API Integration**: RESTful endpoints for external systems

## 🧪 Legacy Components

Original implementations are preserved in the `legacy/` directory:

```bash
# Run legacy generators (for reference)
python legacy/enhanced_pdf_generator_en.py data/sample.csv -o reports/legacy.pdf

# Legacy web application
./legacy/run_web_app.sh
```

## 🛠️ Technical Details

### Key Components

**Core Processing**
- `PatientInfo` & `MicrobiomeData`: Data models for patient and analysis results
- `CSVProcessor`: CSV parsing and clinical calculations
- `ReportGenerator`: Main orchestrator using Jinja2 templates
- `PDFBuilder`: ReportLab integration for PDF creation

**FASTQ Pipeline**
- `FASTQQualityControl`: Quality metrics and visualization
- `FASTQtoCSVConverter`: Sequence data to abundance tables
- `MicrobiomePipelineIntegrator`: End-to-end pipeline coordinator

**Advanced Features**
- `BatchProcessor`: Multi-file processing with validation
- `LLMRecommendationEngine`: AI-powered clinical insights
- `TranslationService`: Multi-language support with glossary
- `ClinicalTemplate` & `TemplateSelector`: Standardized recommendations

### Adding New Languages

#### Automated Translation Workflow:
1. Run the translation notebook: `jupyter notebook notebooks/template_translation.ipynb`
2. Templates are automatically translated with scientific glossary
3. Review Excel files with veterinary language experts
4. Apply corrections back to templates
5. Test with `ReportGenerator(language="[language_code]")`

#### Manual Translation:
1. Create template directory: `templates/[language_code]/`
2. Copy and translate templates from `templates/en/`
3. Update clinical interpretations for local terminology
4. Ensure scientific terms follow the glossary

### Template Customization

Templates use Jinja2 syntax with data objects:

```jinja2
{# Clinical interpretation #}
{% if data.dysbiosis_category == "normal" %}
  Normal microbiota detected...
{% elif data.dysbiosis_category == "mild" %}
  Mild dysbiosis requires monitoring...
{% endif %}

{# Patient information #}
Patient: {{ patient.name }} ({{ patient.age }})
Sample: {{ patient.sample_number }}
```

## 📊 Example Usage

### Single Report Generation

```python
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

# Process multiple samples
patients = [
    PatientInfo(name="Montana", sample_number="506"),
    PatientInfo(name="Thunder", sample_number="507"),
]

generator = ReportGenerator(language="en")

for patient in patients:
    csv_path = f"data/sample_{patient.sample_number}.csv"
    output_path = f"reports/{patient.name}_report.pdf"
    
    success = generator.generate_report(csv_path, patient, output_path)
    print(f"{patient.name}: {'✅' if success else '❌'}")
```

### Batch Processing with Quality Control

```python
from src.batch_processor import BatchProcessor, BatchConfig

# Configure with quality thresholds
config = BatchConfig(
    min_species_count=10,
    max_unassigned_percentage=50.0,
    required_phyla=["Bacillota", "Bacteroidota", "Pseudomonadota"]
)

# Process and validate
processor = BatchProcessor(config)
results = processor.process_directory(validate=True)

# Check validation failures
for result in results:
    if not result['validation_passed']:
        print(f"⚠️ {result['csv_file']}: {result['message']}")
```

## 🏥 About

Developed for HippoVet+ veterinary laboratory, designed specifically for equine gut microbiome research using 16S rRNA sequencing analysis workflows.

---

**Documentation**: `docs/` • **Legacy Code**: `legacy/` • **Examples**: `notebooks/`