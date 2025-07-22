# Equine Microbiome Reporter

**Professional PDF report generation for equine gut microbiome analysis using Jinja2 templates and ReportLab.**

## 🔬 Overview

This repository provides a modern, template-based system for automatically generating professional veterinary laboratory reports from microbiome sequencing CSV data. The system transforms raw bacterial abundance data into comprehensive 5-page PDF reports featuring species distribution charts, phylum analysis, dysbiosis indices, and clinical interpretations.

**New Architecture:** The system uses a **Jinja2-based template architecture** supporting multiple languages and professional PDF generation with ReportLab.

## ✨ Features

- 🎨 **Template-Based Design**: Jinja2 templates for easy customization and maintenance
- 🌍 **Multi-Language Support**: English (Week 1), Polish & Japanese (Week 2)
- 📊 **Professional PDF Generation**: 5-page reports matching reference laboratory standards
- 🔬 **Clinical Analysis**: Automated dysbiosis index calculation and clinical interpretations
- 📈 **Data Visualization**: Species distribution charts and phylum composition analysis
- ⚖️ **Veterinary Standards**: Specialized for equine gut microbiome with clinical reference ranges
- 🚀 **Scalable Architecture**: Modular design supporting batch processing and web applications

## 🏗️ Architecture

```
src/                          # Core modules
├── data_models.py           # PatientInfo + MicrobiomeData classes
├── csv_processor.py         # CSV → structured data conversion
├── report_generator.py      # Main orchestrator with Jinja2
├── pdf_builder.py          # ReportLab PDF generation
└── llm_integration.py      # Week 2 LLM features

templates/                   # Jinja2 templates
├── base/                   # Layout components
├── en/                     # English templates (Week 1)
├── pl/                     # Polish templates (Week 2)
└── jp/                     # Japanese templates (Week 2)

config/                     # YAML configuration
└── report_config.yaml     # Reference ranges, colors, settings
```

## 🚀 Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Prerequisites

- Python 3.8+
- Poetry (install from https://python-poetry.org/docs/#installation)

### Setup

```bash
# Clone the repository
git clone [repository-url]
cd equine-microbiome-reporter

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Dependencies

- **jinja2** - Template engine
- **pyyaml** - Configuration management
- **pandas** - Data processing
- **matplotlib** - Visualization
- **reportlab** - PDF generation
- **numpy** - Numerical operations

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
# Ensure you're in the Poetry environment
poetry shell

# Generate report using Python script
poetry run python -c "
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo

patient = PatientInfo(name='Montana', age='20 years', sample_number='506')
generator = ReportGenerator(language='en')
success = generator.generate_report('data/sample_1.csv', patient, 'reports/report.pdf')
print('✅ Success!' if success else '❌ Failed!')
"
```

## 📊 Input Data Format

The system expects CSV files with bacterial abundance data:

```csv
species,barcode45,barcode46,...,barcode78,phylum,genus
Streptomyces sp.,0,0,...,27,Actinomycetota,Streptomyces
Lactobacillus sp.,45,23,...,156,Bacillota,Lactobacillus
```

### Required Columns
- `species`: Bacterial species name
- `barcode[N]`: Abundance counts for each sample
- `phylum`: Bacterial phylum classification
- `genus`: Bacterial genus classification

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

## 🌍 Multi-Language Support

### Current Implementation (Week 1)
- **✅ English**: Complete template set with clinical interpretations
- **🚧 Polish**: Directory structure ready for Week 2
- **🚧 Japanese**: Directory structure ready for Week 2

### Language Selection

```python
# English (available now)
generator = ReportGenerator(language="en")

# Polish (Week 2)
generator = ReportGenerator(language="pl")

# Japanese (Week 2)
generator = ReportGenerator(language="jp")
```

## 📄 Report Structure

The generated 5-page PDF reports include:

1. **Title Page**: Patient information, laboratory branding
2. **Sequencing Results**: Species distribution charts, dysbiosis index
3. **Clinical Analysis**: Interpretation, recommendations
4. **Laboratory Results**: Parasitological, microscopic, biochemical data
5. **Educational Content**: Microbiome health information

## 🔬 Clinical Features

- **Dysbiosis Index**: Automated calculation based on phylum deviations
- **Clinical Interpretations**: Evidence-based recommendations
- **Reference Ranges**: Veterinary-specific normal values
- **Risk Stratification**: Normal, mild, severe dysbiosis categories

## 📁 Project Organization

```
equine-microbiome-reporter/
├── src/                    # ✅ Core architecture
├── templates/              # ✅ Jinja2 templates  
├── config/                 # ✅ YAML configuration
├── data/                   # Sample CSV files
├── reports/                # Generated PDF outputs
├── assets/                 # Images and logos
├── docs/                   # Documentation and planning
├── legacy/                 # Archived original code
├── examples/               # Tutorial notebooks
└── tests/                  # Test files
```

## 🚀 Development Roadmap

### ✅ Week 1 (MVP Complete)
- Jinja2 template architecture
- English report generation
- Professional 5-page PDF layout
- Clinical analysis and recommendations

### 🚧 Week 2 (In Progress)
- Polish and Japanese template translations
- LLM-powered clinical summaries
- Enhanced recommendation engine

### 📋 Week 3 (Planned)
- Jupyter notebook batch processing
- FASTQ file processing pipeline
- Quality control validation

### 🌐 Phase 2 (Future)
- Web application interface
- Real-time processing dashboard
- User management system

## 🧪 Legacy Components

Original implementations are preserved in the `legacy/` directory:

```bash
# Run legacy generators (for reference)
poetry run python legacy/enhanced_pdf_generator_en.py data/sample.csv -o reports/legacy.pdf

# Legacy web application
./legacy/run_web_app.sh
```

## 🤝 For Developers

### Key Classes

- **`PatientInfo`**: Patient and test metadata
- **`MicrobiomeData`**: Complete microbiome analysis results
- **`CSVProcessor`**: Data processing and clinical calculations
- **`ReportGenerator`**: Template orchestration
- **`PDFBuilder`**: Professional PDF generation

### Adding New Languages

1. Create template directory: `templates/[language_code]/`
2. Translate templates from `templates/en/`
3. Update clinical interpretations for local terminology
4. Test with `ReportGenerator(language="[language_code]")`

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

## 📝 Contributing

Contributions are welcome! Please see the `docs/` directory for architecture documentation and development guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏥 Acknowledgments

- Developed for HippoVet+ veterinary laboratory
- Based on 16S rRNA sequencing analysis workflows  
- Designed for equine gut microbiome research
- Reference PDF design provided by veterinary professionals

---

## 🔗 Links

- **Documentation**: See `docs/` directory for detailed architecture and implementation plans
- **Legacy Code**: Original implementations preserved in `legacy/` directory
- **Examples**: Tutorial notebooks in `examples/` directory