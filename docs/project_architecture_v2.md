# Equine Microbiome Reporter - Project Architecture v2
## Jinja2-Based Template System

### Project Overview

A scalable, maintainable system for generating professional veterinary microbiome analysis reports from CSV data, supporting multiple languages and customizable templates.

### Core Architecture Principles

1. **Separation of Concerns**: Data processing, template logic, and PDF rendering are independent
2. **Template-Driven**: All content and layout defined in Jinja2 templates
3. **Language Agnostic**: Easy translation through template swapping
4. **MVP-First**: Start simple, build towards complexity
5. **Future-Ready**: Architecture supports Phase 2 web application

### Project Structure

```
equine-microbiome-reporter/
├── src/
│   ├── __init__.py
│   ├── data_models.py          # Simplified dataclasses
│   ├── csv_processor.py        # CSV → Data models
│   ├── report_generator.py     # Main orchestrator
│   ├── pdf_builder.py          # ReportLab PDF creation
│   └── llm_integration.py      # LLM summary generation (Week 2)
│
├── templates/
│   ├── base/
│   │   ├── report_layout.j2    # Master layout template
│   │   ├── page_header.j2      # Reusable header
│   │   └── page_footer.j2      # Reusable footer
│   │
│   ├── en/
│   │   ├── report_full.j2      # Complete English report
│   │   ├── clinical_text.j2    # Clinical interpretations
│   │   ├── recommendations.j2   # Recommendations by DI level
│   │   └── educational.j2       # Page 5 educational content
│   │
│   ├── pl/
│   │   └── ... (Polish versions)
│   │
│   └── jp/
│       └── ... (Japanese versions)
│
├── assets/
│   ├── hippovet_logo.png
│   ├── dna_stock_photo.jpg
│   └── microscope_images/
│       ├── positive_microbiome.jpg
│       └── pathogenic_microbiome.jpg
│
├── config/
│   ├── report_config.yaml      # Report settings, reference ranges
│   ├── phylum_colors.yaml      # Color schemes
│   └── lab_profiles/           # Per-lab customizations
│       └── hippovet.yaml
│
├── data/
│   ├── sample_1.csv
│   └── ...
│
├── reports/
│   └── ... (Generated PDFs)
│
├── tests/
│   ├── test_csv_processor.py
│   ├── test_report_generator.py
│   └── fixtures/
│       └── test_data.csv
│
├── web_app.py                  # Phase 2 Flask application
├── batch_processor.py          # Week 3 batch processing
├── pyproject.toml             # Poetry dependencies
└── README.md
```

### Data Models (Simplified per Gemini)

```python
# src/data_models.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class PatientInfo:
    """Patient and test information"""
    name: str
    species: str = "Horse"
    age: str = "Unknown"
    sample_number: str = "001"
    date_received: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    date_analyzed: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"

@dataclass 
class MicrobiomeData:
    """All microbiome analysis results in one place"""
    # Core microbiome data
    species_list: List[Dict[str, any]]  # [{name, percentage, phylum, genus}, ...]
    phylum_distribution: Dict[str, float]  # {phylum_name: percentage}
    dysbiosis_index: float
    total_species_count: int
    
    # Lab results (simplified for MVP)
    parasite_results: List[Dict[str, any]] = field(default_factory=list)
    microscopic_results: List[Dict[str, any]] = field(default_factory=list)
    biochemical_results: List[Dict[str, any]] = field(default_factory=list)
    
    # Interpretations
    dysbiosis_category: str = "normal"  # normal, mild, severe
    clinical_interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    # Optional LLM content (Week 2)
    llm_summary: Optional[str] = None
    llm_recommendations: Optional[List[str]] = None
```

### Core Components

#### 1. CSV Processor
```python
# src/csv_processor.py
import pandas as pd
from typing import Tuple
from .data_models import MicrobiomeData

class CSVProcessor:
    """Process microbiome CSV data into structured format"""
    
    def __init__(self, csv_path: str, barcode_column: str = "barcode59"):
        self.df = pd.read_csv(csv_path)
        self.barcode_column = barcode_column
        self.total_count = self.df[barcode_column].sum()
    
    def process(self) -> MicrobiomeData:
        """Convert CSV to MicrobiomeData object"""
        species_list = self._get_species_list()
        phylum_dist = self._calculate_phylum_distribution(species_list)
        di_score = self._calculate_dysbiosis_index(phylum_dist)
        
        return MicrobiomeData(
            species_list=species_list,
            phylum_distribution=phylum_dist,
            dysbiosis_index=di_score,
            total_species_count=len(species_list),
            dysbiosis_category=self._get_dysbiosis_category(di_score),
            parasite_results=self._get_default_parasite_results(),
            microscopic_results=self._get_default_microscopic_results(),
            biochemical_results=self._get_default_biochemical_results()
        )
```

#### 2. Report Generator (Main Orchestrator)
```python
# src/report_generator.py
from jinja2 import Environment, FileSystemLoader
from .data_models import PatientInfo, MicrobiomeData
from .csv_processor import CSVProcessor
from .pdf_builder import PDFBuilder
import yaml

class ReportGenerator:
    """Main report generation orchestrator"""
    
    def __init__(self, language: str = "en", template_name: str = "report_full.j2"):
        self.language = language
        self.template_name = template_name
        
        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load configuration
        with open('config/report_config.yaml') as f:
            self.config = yaml.safe_load(f)
    
    def generate_report(self, csv_path: str, patient_info: PatientInfo, output_path: str):
        """Generate complete PDF report"""
        # Process CSV data
        processor = CSVProcessor(csv_path)
        microbiome_data = processor.process()
        
        # Add clinical interpretations
        microbiome_data.clinical_interpretation = self._generate_clinical_text(microbiome_data)
        microbiome_data.recommendations = self._get_recommendations(microbiome_data)
        
        # Render template
        template = self.env.get_template(f"{self.language}/{self.template_name}")
        content = template.render(
            patient=patient_info,
            data=microbiome_data,
            config=self.config,
            lang=self.language
        )
        
        # Build PDF
        builder = PDFBuilder()
        builder.build_from_content(content, output_path, patient_info, microbiome_data)
```

#### 3. Template Structure
```jinja2
{# templates/en/report_full.j2 #}
{# Master template that includes all pages #}

{% set title = "COMPREHENSIVE FECAL EXAMINATION" %}

{# Page 1: Title Page #}
{% include 'en/pages/page1_title.j2' %}

{# Page 2: Sequencing Results #}
{% include 'en/pages/page2_sequencing.j2' %}

{# Page 3: Clinical Analysis #}
{% include 'en/pages/page3_clinical.j2' %}

{# Page 4: Laboratory Results #}
{% include 'en/pages/page4_laboratory.j2' %}

{# Page 5: Educational Content #}
{% include 'en/pages/page5_educational.j2' %}
```

```jinja2
{# templates/en/pages/page3_clinical.j2 #}
<page>
  <section type="dysbiosis">
    <title>Dysbiosis Index (DI): {{ "%.1f"|format(data.dysbiosis_index) }}</title>
    <content>
      {% if data.dysbiosis_category == "normal" %}
        Normal microbiota (healthy). Lack of dysbiosis signs; gut microflora is balanced with minor deviations.
      {% elif data.dysbiosis_category == "mild" %}
        Mild dysbiosis detected. Moderate imbalance in gut microflora composition requiring monitoring.
      {% else %}
        Severe dysbiosis detected. Significant imbalance in gut microflora requiring intervention.
      {% endif %}
    </content>
  </section>
  
  <section type="green-header">
    <title>UNICELLULAR PARASITE PROFILE</title>
    <content>{{ data.parasite_profile | default("No unicellular parasite genome identified in the sample") }}</content>
  </section>
  
  <section type="clinical-description">
    <title>DESCRIPTION</title>
    <content>{{ data.clinical_interpretation }}</content>
  </section>
</page>
```

#### 4. PDF Builder (ReportLab Integration)
```python
# src/pdf_builder.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import xml.etree.ElementTree as ET

class PDFBuilder:
    """Build PDF from template-generated content"""
    
    def __init__(self):
        self.width, self.height = A4
        self.colors = {
            'green': colors.HexColor('#10B981'),
            'primary_blue': colors.HexColor('#1E3A8A'),
            'teal': colors.HexColor('#14B8A6')
        }
    
    def build_from_content(self, content: str, output_path: str, 
                          patient_info: PatientInfo, data: MicrobiomeData):
        """Parse template output and create PDF"""
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Parse the template output (pseudo-XML/HTML)
        pages = self._parse_content(content)
        
        for page_num, page in enumerate(pages, 1):
            if page_num > 1:
                c.showPage()
            
            # Draw page elements
            self._draw_page(c, page, page_num, patient_info, data)
        
        c.save()
    
    def _draw_pill_box(self, c, x, y, width, height, text):
        """Draw rounded rectangle with text"""
        radius = height / 2
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor('#E5E7EB'))
        c.roundRect(x, y, width, height, radius, stroke=1, fill=1)
        c.setFillColor(colors.HexColor('#1F2937'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(x + width/2, y + height/3, text)
        c.restoreState()
```

### Configuration Files

```yaml
# config/report_config.yaml
reference_ranges:
  Actinomycetota: [0.1, 8.0]
  Bacillota: [20.0, 70.0]
  Bacteroidota: [4.0, 40.0]
  Pseudomonadota: [2.0, 35.0]
  Fibrobacterota: [0.1, 5.0]

dysbiosis_thresholds:
  normal: 20
  mild: 50

default_lab_results:
  parasites:
    - name: "Anoplocephala perfoliata"
      result: "Not observed"
    - name: "Oxyuris equi"
      result: "Not observed"
    - name: "Parascaris equorum"
      result: "Not observed"
    - name: "Strongylidae"
      result: "Not observed"
```

### Development Workflow

1. **Week 1 - MVP**
   - Implement basic data models
   - Create English templates matching reference PDF
   - Build PDF generation with exact styling
   - Test with sample data

2. **Week 2 - Multi-language & LLM**
   - Add Polish templates
   - Add Japanese templates
   - Integrate LLM for summaries (llm_integration.py)
   - Template selection logic

3. **Week 3 - Batch Processing**
   - Enhance batch_processor.py
   - Add progress tracking
   - Parallel processing
   - Error handling

4. **Week 4 - Testing & Polish**
   - Comprehensive testing
   - Documentation
   - Performance optimization
   - Client feedback integration

### Key Benefits of This Architecture

1. **Maintainability**: Templates are separate from logic
2. **Scalability**: Easy to add new languages or report types
3. **Testability**: Each component can be tested independently
4. **Flexibility**: Configuration-driven behavior
5. **Future-Ready**: Same templates can generate HTML for web app