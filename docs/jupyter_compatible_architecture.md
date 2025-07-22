# Jupyter-Compatible Architecture - Revised

## ✅ Full Jupyter Notebook Compatibility Maintained

The Jinja2 template architecture is **100% compatible** with Jupyter notebooks and actually makes them more powerful.

### Why This Architecture is Perfect for Jupyter

1. **Cleaner Notebook Cells**: Templates separate presentation from logic
2. **Interactive Development**: Easy to test templates and data processing
3. **Batch Processing**: Perfect for iterative CSV processing
4. **Progress Visualization**: Can show template rendering in real-time
5. **Debugging**: Step through each component independently

## Revised Project Structure (Jupyter-First)

```
equine-microbiome-reporter/
├── src/                        # Core modules (importable in notebooks)
│   ├── __init__.py
│   ├── data_models.py          # PatientInfo, MicrobiomeData
│   ├── csv_processor.py        # CSV → Data conversion
│   ├── report_generator.py     # Main generator class
│   ├── pdf_builder.py          # ReportLab integration
│   └── llm_integration.py      # Week 2 LLM features
│
├── notebooks/                  # 📓 CORE DELIVERABLES
│   ├── 01_single_report_generator.ipynb     # Week 1 - Single PDF
│   ├── 02_batch_processor.ipynb             # Week 3 - Multi-file processing
│   ├── 03_quality_control.ipynb             # Week 3 - QC validation
│   ├── 04_fastq_processor.ipynb             # Week 3 - FASTQ pipeline
│   └── examples/
│       ├── sample_analysis.ipynb
│       └── template_development.ipynb
│
├── templates/                  # Jinja2 templates (used by notebooks)
│   ├── en/, pl/, jp/
│   └── base/
│
├── config/
├── assets/
├── data/
└── reports/
```

## Jupyter Notebook Integration Examples

### 1. Single Report Generator Notebook
```python
# notebooks/01_single_report_generator.ipynb

# Cell 1: Setup and Imports
import sys
sys.path.append('../src')

from data_models import PatientInfo, MicrobiomeData
from csv_processor import CSVProcessor
from report_generator import ReportGenerator
import pandas as pd
from pathlib import Path

# Cell 2: Configure Patient Information
patient = PatientInfo(
    name="Montana",
    species="Horse", 
    age="20 years",
    sample_number="506",
    performed_by="Julia Kończak",
    requested_by="Dr. Alexandra Matusiak"
)

print(f"Patient: {patient.name}, Sample: {patient.sample_number}")

# Cell 3: Process CSV Data
csv_path = "../data/sample_1.csv"
processor = CSVProcessor(csv_path, barcode_column="barcode59")
microbiome_data = processor.process()

print(f"Total species: {microbiome_data.total_species_count}")
print(f"Dysbiosis Index: {microbiome_data.dysbiosis_index:.1f}")

# Cell 4: Preview Top Species (Interactive)
import matplotlib.pyplot as plt

top_species = microbiome_data.species_list[:10]
species_names = [s['species'] for s in top_species]
percentages = [s['percentage'] for s in top_species]

plt.figure(figsize=(12, 6))
plt.barh(species_names, percentages)
plt.title("Top 10 Species Distribution")
plt.xlabel("Percentage (%)")
plt.show()

# Cell 5: Generate PDF Report
generator = ReportGenerator(language="en")
output_path = f"../reports/{patient.name}_{patient.sample_number}.pdf"

success = generator.generate_report(csv_path, patient, output_path)
if success:
    print(f"✅ Report generated: {output_path}")
else:
    print("❌ Report generation failed")
```

### 2. Batch Processing Notebook (Week 3 Core Deliverable)
```python
# notebooks/02_batch_processor.ipynb

# Cell 1: Batch Processing Setup
import os
import pandas as pd
from glob import glob
from tqdm.notebook import tqdm
import concurrent.futures
from datetime import datetime

# Import our modules
from report_generator import ReportGenerator
from data_models import PatientInfo

# Cell 2: Load Manifest File
manifest_df = pd.read_csv("../manifest.csv")
print(f"Found {len(manifest_df)} samples to process")
manifest_df.head()

# Cell 3: Define Batch Processing Function
def process_single_sample(row):
    """Process a single sample from manifest"""
    try:
        # Create patient info from manifest row
        patient = PatientInfo(
            name=row['patient_name'],
            species=row['species'],
            age=row['age'],
            sample_number=row['sample_number'],
            date_received=row['date_received'],
            performed_by=row['performed_by'],
            requested_by=row['requested_by']
        )
        
        # Generate report
        generator = ReportGenerator(language="en")  # Could be row['language']
        output_path = f"../reports/{patient.name}_{patient.sample_number}.pdf"
        
        success = generator.generate_report(row['csv_file'], patient, output_path)
        
        return {
            'sample': row['sample_number'],
            'success': success,
            'output_path': output_path if success else None,
            'error': None
        }
        
    except Exception as e:
        return {
            'sample': row['sample_number'],
            'success': False,
            'output_path': None,
            'error': str(e)
        }

# Cell 4: Execute Batch Processing with Progress Bar
results = []

# Sequential processing with progress bar
for idx, row in tqdm(manifest_df.iterrows(), total=len(manifest_df), desc="Processing samples"):
    result = process_single_sample(row)
    results.append(result)
    
    # Real-time status update
    if result['success']:
        print(f"✅ {result['sample']}: {result['output_path']}")
    else:
        print(f"❌ {result['sample']}: {result['error']}")

# Cell 5: Parallel Processing (Advanced)
# Uncomment for faster processing
# with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#     futures = [executor.submit(process_single_sample, row) 
#                for idx, row in manifest_df.iterrows()]
#     
#     results = []
#     for future in tqdm(concurrent.futures.as_completed(futures), 
#                        total=len(futures), desc="Processing"):
#         results.append(future.result())

# Cell 6: Results Summary and Quality Control
results_df = pd.DataFrame(results)
success_rate = (results_df['success'].sum() / len(results_df)) * 100

print(f"\n📊 BATCH PROCESSING SUMMARY")
print(f"Total samples: {len(results_df)}")
print(f"Successful: {results_df['success'].sum()}")
print(f"Failed: {(~results_df['success']).sum()}")
print(f"Success rate: {success_rate:.1f}%")

# Show failed samples
if (~results_df['success']).any():
    print("\n❌ FAILED SAMPLES:")
    failed_df = results_df[~results_df['success']]
    for _, row in failed_df.iterrows():
        print(f"  {row['sample']}: {row['error']}")

# Cell 7: Export Results Log
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_path = f"../reports/batch_log_{timestamp}.csv"
results_df.to_csv(log_path, index=False)
print(f"\n📄 Results log saved: {log_path}")
```

### 3. Quality Control Notebook
```python
# notebooks/03_quality_control.ipynb

# Cell 1: QC Analysis
def validate_pdf_quality(pdf_path):
    """Validate generated PDF meets quality standards"""
    checks = {
        'file_exists': Path(pdf_path).exists(),
        'file_size_ok': Path(pdf_path).stat().st_size > 100000,  # >100KB
        'is_pdf': pdf_path.endswith('.pdf')
    }
    return checks

# Cell 2: Batch QC Validation
qc_results = []
for result in results:
    if result['success']:
        qc = validate_pdf_quality(result['output_path'])
        qc['sample'] = result['sample']
        qc_results.append(qc)

qc_df = pd.DataFrame(qc_results)
print("Quality Control Results:")
print(qc_df.describe())
```

## Key Benefits for Jupyter Workflows

### 1. **Interactive Development**
- Test templates live in notebook cells
- Visualize data processing steps
- Debug each component independently

### 2. **Progress Tracking**
```python
# Real-time progress with tqdm
for sample in tqdm(samples):
    generate_report(sample)
```

### 3. **Data Visualization** 
```python
# Preview charts before PDF generation
plt.figure(figsize=(10, 6))
plot_species_distribution(microbiome_data)
plt.show()
```

### 4. **Error Handling & QC**
```python
# Catch and analyze errors interactively
try:
    result = process_sample(csv_file)
except Exception as e:
    print(f"Error: {e}")
    # Debug interactively
```

### 5. **Template Development**
```python
# Test template rendering
from jinja2 import Template
template = Template("Dysbiosis Index: {{ di_score }}")
print(template.render(di_score=15.3))
```

## Integration with Existing Architecture

The Jinja2 template system **enhances** Jupyter notebooks by:

1. **Cleaner Code**: Templates keep notebook cells focused on logic
2. **Reusability**: Same templates work across all notebooks  
3. **Language Support**: Easy to switch languages in notebooks
4. **Maintenance**: Update templates without touching notebook code

## Week 3 Deliverable: Batch Processing Notebook

The architecture fully supports the required **Batch Processing Jupyter Notebook**:

✅ Multi-file CSV processing  
✅ Progress tracking and error reporting  
✅ Automated PDF generation  
✅ Quality control validation  

**Plus additional benefits:**
- Interactive development
- Real-time visualization
- Error debugging
- Parallel processing options
- Results logging and analysis

The template architecture makes Jupyter notebooks **more powerful**, not less compatible.