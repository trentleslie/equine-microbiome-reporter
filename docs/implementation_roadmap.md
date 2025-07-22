# Implementation Roadmap - Jinja2 Template Architecture

## Gemini's Final Assessment: ✅ APPROVED

**"This architecture is a significant improvement and well-suited for an MVP while also laying a solid foundation for future expansion."**

### Key Strengths Confirmed:
- ✅ Modular design with excellent separation of concerns
- ✅ Configuration-driven approach using YAML
- ✅ Language support designed from the start
- ✅ Template structure is highly efficient and scalable
- ✅ Future-ready for Phase 2 web application

### Areas to Address:
1. **Error Handling** - Add robust error handling throughout
2. **LLM Integration** - Keep minimally invasive, plugin-like approach
3. **Template Parsing** - MVP approach is sound, can optimize later

## Implementation Plan

### Phase 1: Week 1 (MVP Foundation)

#### Day 1-2: Core Infrastructure
```bash
# Add Jinja2 to project
poetry add jinja2 pyyaml

# Create project structure
mkdir -p src templates/{base,en,pl,jp} config assets tests
mkdir -p templates/en/pages templates/pl/pages templates/jp/pages
```

**Files to Create:**
- `src/data_models.py` - PatientInfo + MicrobiomeData dataclasses
- `src/csv_processor.py` - CSV → MicrobiomeData conversion
- `config/report_config.yaml` - Reference ranges, thresholds
- `templates/en/report_full.j2` - Master English template

#### Day 3-4: Template System
**Priority Order:**
1. Page 1: Title page with pill-shaped boxes
2. Page 2: Species distribution charts
3. Page 3: Clinical analysis sections
4. Page 4: Laboratory results tables
5. Page 5: Educational content

**Template Structure:**
```jinja2
{# templates/en/report_full.j2 #}
{% extends "base/layout.j2" %}
{% block content %}
  {% include "en/pages/page1_title.j2" %}
  {% include "en/pages/page2_sequencing.j2" %}
  {% include "en/pages/page3_clinical.j2" %}
  {% include "en/pages/page4_laboratory.j2" %}
  {% include "en/pages/page5_educational.j2" %}
{% endblock %}
```

#### Day 5: PDF Integration & Testing
- `src/pdf_builder.py` - Parse template output → ReportLab
- `src/report_generator.py` - Main orchestrator
- Test with sample data
- Match reference PDF exactly

### Phase 1: Week 2 (Multi-language & LLM)

#### Multi-language Implementation
```python
# Report generation with language selection
generator = ReportGenerator(language="pl", template="report_full.j2")
generator.generate_report(csv_path, patient_info, output_path)
```

#### LLM Integration (Plugin Approach)
```python
# src/llm_integration.py
class LLMPlugin:
    def generate_summary(self, microbiome_data: MicrobiomeData) -> str:
        # Minimal interface for LLM interaction
        pass

# In ReportGenerator
if self.config.get('use_llm_summary'):
    llm = LLMPlugin()
    microbiome_data.llm_summary = llm.generate_summary(microbiome_data)
```

### Phase 1: Week 3 (Batch Processing)
- Enhance `batch_processor.py` to use new architecture
- Template selection per batch
- Progress tracking
- Error handling and logging

### Phase 1: Week 4 (Testing & Polish)
- Comprehensive test suite
- Performance optimization
- Documentation
- Client feedback integration

## File Structure Implementation

```
equine-microbiome-reporter/
├── src/
│   ├── __init__.py
│   ├── data_models.py          # ✅ Gemini approved
│   ├── csv_processor.py        # ✅ Core component
│   ├── report_generator.py     # ✅ Main orchestrator
│   ├── pdf_builder.py          # ✅ ReportLab integration
│   └── llm_integration.py      # Week 2 - Plugin approach
│
├── templates/
│   ├── base/
│   │   ├── layout.j2          # Master layout
│   │   ├── header.j2          # Reusable header
│   │   └── footer.j2          # Reusable footer
│   │
│   ├── en/
│   │   ├── report_full.j2     # Main English template
│   │   ├── clinical_text.j2   # Clinical interpretations
│   │   └── pages/
│   │       ├── page1_title.j2
│   │       ├── page2_sequencing.j2
│   │       ├── page3_clinical.j2
│   │       ├── page4_laboratory.j2
│   │       └── page5_educational.j2
│   │
│   ├── pl/ (Week 2)
│   └── jp/ (Week 2)
│
├── config/
│   ├── report_config.yaml     # ✅ Configuration-driven
│   ├── phylum_colors.yaml     # Color schemes
│   └── lab_profiles/
│       └── hippovet.yaml
│
├── assets/
│   ├── hippovet_logo.png
│   ├── dna_stock_photo.jpg
│   └── microscope_images/
│
├── tests/
│   ├── test_csv_processor.py
│   ├── test_report_generator.py
│   └── fixtures/
│
├── enhanced_pdf_generator_en.py    # Current working version
├── web_app.py                      # Phase 2
└── batch_processor.py              # Week 3 enhancement
```

## Technical Decisions

### Template → PDF Approach (MVP)
**Chosen:** Custom markup parsed by PDFBuilder
- Jinja2 generates custom XML-like markup
- PDFBuilder parses and converts to ReportLab commands
- Full control over exact positioning and styling

### Error Handling Strategy
```python
# src/report_generator.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ReportGenerator:
    def generate_report(self, csv_path: str, patient_info: PatientInfo, output_path: str) -> bool:
        try:
            # Process CSV
            processor = CSVProcessor(csv_path)
            data = processor.process()
            
            # Generate report
            self._render_and_build(data, patient_info, output_path)
            return True
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            return False
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return False
```

### Configuration Management
```yaml
# config/report_config.yaml
version: "1.0"
reference_ranges:
  Actinomycetota: [0.1, 8.0]
  Bacillota: [20.0, 70.0]
  Bacteroidota: [4.0, 40.0]
  Pseudomonadota: [2.0, 35.0]

colors:
  primary_blue: "#1E3A8A"
  green: "#10B981"
  teal: "#14B8A6"

templates:
  default: "report_full.j2"
  summary: "report_summary.j2"  # Future

llm:
  enabled: false  # Week 2
  provider: "openai"
  model: "gpt-3.5-turbo"
```

## Success Metrics

### Week 1 MVP
- [ ] Generate PDF matching reference exactly
- [ ] Process sample CSV data correctly
- [ ] Template system working with Jinja2
- [ ] Basic error handling implemented

### Week 2
- [ ] Polish and Japanese templates working
- [ ] LLM summary integration
- [ ] Language selection functional

### Week 3
- [ ] Batch processing with new architecture
- [ ] Progress tracking and error reporting

### Week 4
- [ ] Complete test coverage
- [ ] Performance benchmarks
- [ ] Client approval for Phase 1

This roadmap incorporates all of Gemini's feedback and provides a clear path from MVP to full Phase 1 completion.