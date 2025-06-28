# Equine Microbiome Reporter

Automated PDF report generation for equine gut microbiome analysis from 16S rRNA sequencing data.

## Overview

This repository provides tools to automatically generate professional veterinary laboratory reports from microbiome sequencing CSV data. It transforms raw bacterial abundance data into comprehensive PDF reports featuring species distribution charts, phylum analysis, dysbiosis indices, and clinical interpretations in Polish language format matching HippoVet+ laboratory standards.

## Features

- 📊 **Automated Visualization**: Generate species distribution charts and phylum composition graphs
- 🔬 **Clinical Analysis**: Calculate dysbiosis indices and identify potential health indicators
- 🌍 **Polish Language Support**: Full support for Polish veterinary terminology and report formatting
- ⚡ **Batch Processing**: Process multiple samples in parallel with configurable workflows
- 📄 **Professional Reports**: Generate publication-ready PDF reports matching laboratory standards
- 🏥 **Veterinary Focus**: Specialized for equine gut microbiome analysis with relevant reference ranges

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Prerequisites

- Python 3.8+
- Poetry (install from https://python-poetry.org/docs/#installation)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/equine-microbiome-reporter.git
cd equine-microbiome-reporter

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Dependencies

The project dependencies are managed through `pyproject.toml`:

- pandas (>=1.3.0)
- matplotlib (>=3.4.0)
- numpy (>=1.21.0)
- reportlab (>=3.6.0)
- PyYAML (>=6.0)
- Flask (>=2.3.0) - for web application
- Werkzeug (>=2.3.0) - Flask dependency

## Quick Start

### Process a Single Sample

```bash
# Ensure you're in the Poetry environment
poetry shell

# Basic report generation
python pdf_generator.py data/sample.csv -o reports/sample_report.pdf

# Advanced Polish laboratory format
python advanced_pdf_generator.py data/sample.csv -o reports/sample_report.pdf \
    --name "Montana" \
    --age "20 lat" \
    --sample "506"
```

### Batch Process Multiple Samples

```bash
# Process all CSV files in a directory
python batch_processor.py -i data/ -o reports/

# Process with configuration file
python batch_processor.py -i data/ -o reports/ -c config.yaml

# Process from manifest with patient details
python batch_processor.py -m manifest.csv -o reports/
```

### Running Without Activating Poetry Shell

You can also run scripts directly with Poetry:

```bash
poetry run python pdf_generator.py data/sample.csv -o reports/sample_report.pdf
```

## Input Data Format

The tool expects CSV files with the following structure:

```csv
species,barcode45,barcode46,...,barcode78,total,phylum,genus,family,...
Streptomyces sp.,0,0,...,27,46,Actinomycetota,Streptomyces,Streptomycetaceae,...
```

### Required Columns
- `species`: Bacterial species name
- `barcode[N]`: Abundance counts for each barcode/sample
- `phylum`: Bacterial phylum classification
- `genus`: Bacterial genus classification

## Configuration

Create a configuration file (`config.yaml`) for batch processing:

```yaml
# Default barcode column to analyze
barcode_column: barcode59

# Default patient information
default_species: Koń
default_age: Unknown
performed_by: Julia Kończak
requested_by: Aleksandra Matusiak

# Processing settings
max_workers: 4
log_level: INFO
```

Save this as `config.yaml` in your project directory.

## Manifest File Format

For batch processing with specific patient data, create a manifest CSV:

```csv
csv_file,patient_name,species,age,sample_number,date_received,performed_by,requested_by
data/sample1.csv,Montana,Koń,20 lat,506,07.05.2025 r.,Julia Kończak,Aleksandra Matusiak
data/sample2.csv,Thunder,Koń,15 lat,507,08.05.2025 r.,Julia Kończak,Dr. Smith
```

Save this as `manifest.csv` in your project directory.

## Output

The tool generates comprehensive PDF reports including:

- Patient information header
- Species distribution visualization
- Phylum composition analysis with reference ranges
- Dysbiosis index calculation
- Clinical interpretation in Polish
- Microscopic and biochemical analysis sections
- Parasite screening results

## Web Application

### Running the Web Interface

For a user-friendly web interface, run the Flask application:

```bash
# Using the startup script
./run_web_app.sh

# Or directly with Poetry
poetry run python web_app.py
```

The web application will be available at `http://localhost:5001`

### Web Application Features

- **Easy Upload**: Drag-and-drop CSV file upload
- **Interactive Configuration**: Configure patient information through web forms
- **Barcode Selection**: Choose which sample (barcode) to analyze
- **Instant Download**: Generate and download PDF reports immediately
- **Example Data**: Download example CSV file to understand the format

### Using the Web Interface

1. Navigate to `http://localhost:5001`
2. Upload your microbiome CSV file
3. Select the barcode column to analyze
4. Fill in patient information
5. Click "Generate Report"
6. Download your PDF report

## Advanced Usage

### Custom Phylum Reference Ranges

Modify reference ranges in `advanced_pdf_generator.py`:

```python
REFERENCE_RANGES = {
    'Actinomycetota': (0.1, 8),
    'Bacillota': (20, 70),
    'Bacteroidota': (4, 40),
    'Pseudomonadota': (2, 35)
}
```

### Custom Color Schemes

Adjust visualization colors:

```python
PHYLUM_COLORS = {
    'Actinomycetota': '#00BCD4',
    'Bacillota': '#4CAF50',
    'Bacteroidota': '#FF5722',
    'Pseudomonadota': '#00E5FF'
}
```

## For LLM Agents

### Repository Structure
```
equine-microbiome-reporter/
├── pdf_generator.py              # Basic PDF generation script
├── advanced_pdf_generator.py     # Advanced Polish laboratory format generator
├── batch_processor.py            # Batch processing automation
├── pyproject.toml                # Poetry configuration and dependencies
├── LICENSE                       # MIT License
└── README.md                     # This file
```

### Key Functions and Classes

#### `AdvancedMicrobiomeReportGenerator` (advanced_pdf_generator.py)
- `__init__(csv_file, barcode_column)`: Initialize with CSV data
- `generate_report(output_file, patient_info)`: Generate complete PDF report
- `_calculate_species_data()`: Process species abundance data
- `_calculate_phylum_distribution()`: Calculate phylum percentages
- `_create_species_visualization()`: Generate species bar charts
- `_generate_description_text()`: Create Polish clinical interpretation

#### `BatchReportProcessor` (batch_processor.py)
- `process_single_file(csv_file, output_dir, patient_data)`: Process one CSV file
- `process_directory(input_dir, output_dir, pattern, parallel)`: Process multiple files
- `process_from_manifest(manifest_file, output_dir)`: Process using manifest data

### API Usage Example

```python
from advanced_pdf_generator import AdvancedMicrobiomeReportGenerator

# Initialize generator
generator = AdvancedMicrobiomeReportGenerator('data/sample.csv', 'barcode59')

# Set patient information
patient_info = {
    'name': 'Montana',
    'species': 'Koń',
    'age': '20 lat',
    'sample_number': '506',
    'date_received': '07.05.2025 r.',
    'performed_by': 'Julia Kończak',
    'requested_by': 'Aleksandra Matusiak'
}

# Generate report
generator.generate_report('output/report.pdf', patient_info)
```

### Data Processing Pipeline

1. **CSV Loading**: Read bacterial abundance data with pandas
2. **Data Filtering**: Select samples with non-zero counts for specified barcode
3. **Percentage Calculation**: Convert counts to percentages of total abundance
4. **Phylum Aggregation**: Sum species counts by phylum classification
5. **Visualization**: Create horizontal bar charts for species and phylum data
6. **PDF Generation**: Compile visualizations and text into formatted PDF
7. **Batch Processing**: Optionally process multiple files in parallel

### Integration Notes

- The tool expects UTF-8 encoded CSV files
- Polish language characters are fully supported
- PDF generation uses matplotlib for charts and reportlab for advanced formatting
- Parallel processing uses Python's ProcessPoolExecutor
- Logging follows Python standard logging format
- All file paths support both Windows and Unix systems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Developed for HippoVet+ veterinary laboratory
- Based on 16S rRNA sequencing analysis workflows
- Designed for equine gut microbiome research

## Contact

For questions or support, please open an issue on GitHub or contact the repository maintainers.

---

## Example Output

The generated PDF reports include:
- Professional laboratory header with patient information
- Species distribution visualization showing top bacterial species
- Phylum composition analysis with reference ranges
- Clinical interpretation in Polish language
- Microscopic and biochemical analysis sections