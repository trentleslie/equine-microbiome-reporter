# Project Structure - Organized

This document describes the clean, organized project structure after reorganization.

## Current Active Architecture (Jinja2-based)

```
equine-microbiome-reporter/
├── 📁 src/                         # Core source code (NEW)
│   ├── __init__.py
│   ├── data_models.py              # PatientInfo + MicrobiomeData
│   └── csv_processor.py            # CSV → Data models conversion
│
├── 📁 templates/                   # Jinja2 templates (NEW)
│   ├── base/                       # Base layout components
│   │   ├── layout.j2
│   │   ├── header.j2
│   │   └── footer.j2
│   ├── en/                         # English templates
│   │   ├── report_full.j2
│   │   └── pages/                  # Individual page templates
│   │       ├── page1_title.j2
│   │       ├── page2_sequencing.j2
│   │       ├── page3_clinical.j2
│   │       ├── page4_laboratory.j2
│   │       └── page5_educational.j2
│   ├── pl/                         # Polish templates (Week 2)
│   └── jp/                         # Japanese templates (Week 2)
│
├── 📁 config/                      # Configuration files (NEW)
│   └── report_config.yaml         # Reference ranges, colors, settings
│
├── 📁 data/                        # Sample CSV data
│   ├── sample_1.csv
│   ├── sample_2.csv
│   ├── sample_3.csv
│   └── 25_04_23 bact.csv
│
├── 📁 assets/                      # Images and logos
│   ├── hippovet_logo.png
│   └── dna_stock_photo.jpg
│
├── 📁 reports/                     # Generated PDF outputs
│   ├── basic_report.pdf
│   ├── montana_advanced_report.pdf
│   └── batch/
│
├── 📁 notebooks/                   # Jupyter notebooks (Week 3)
├── 📁 tests/                       # Test files
├── 📁 examples/                    # Example notebooks and tutorials
│   └── tutorial.ipynb
│
├── 📁 docs/                        # Documentation and planning
│   ├── implementation_roadmap.md
│   ├── project_architecture_v2.md
│   ├── jupyter_compatible_architecture.md
│   ├── reference_pdf_specification.md
│   └── reference_report/           # Reference PDF images
│
├── 📁 legacy/                      # Legacy code (archived)
│   ├── advanced_pdf_generator.py
│   ├── enhanced_pdf_generator*.py
│   ├── web_app.py
│   ├── static/
│   └── generated_reports/
│
├── 📄 CLAUDE.md                    # Instructions for Claude
├── 📄 README.md                    # Project overview
├── 📄 pyproject.toml              # Poetry dependencies
├── 📄 manifest.csv                # Sample manifest file
├── 📄 batch_processor.py          # To be updated for new architecture
└── 📄 PROJECT_STRUCTURE.md        # This file
```

## ✅ Complete MVP Implementation

All core modules have been implemented:

```
src/
├── __init__.py                    # ✅ Package init
├── data_models.py                 # ✅ PatientInfo + MicrobiomeData
├── csv_processor.py               # ✅ CSV → Data models conversion
├── report_generator.py            # ✅ Main orchestrator
├── pdf_builder.py                 # ✅ ReportLab integration
└── llm_integration.py             # ✅ Week 2 LLM features (placeholder)
```

## What Was Moved and Why

### ✅ Moved to `legacy/`
- **Old PDF generators**: `advanced_pdf_generator.py`, `enhanced_pdf_generator*.py`, etc.
- **Legacy web app**: `web_app.py`, `static/`, HTML templates
- **Old configuration**: `config.yaml`
- **Generated test files**: Previous PDF outputs

### ✅ Moved to `docs/`
- **Planning documents**: Architecture plans, implementation roadmaps
- **Reference materials**: PDF specifications, reference images
- **Research notes**: Implementation gaps, MVP plans

### ✅ Moved to `examples/`
- **Tutorial notebook**: Educational materials

### ✅ Deleted
- **Temporary files**: Log files, test PDFs
- **Temporary directories**: `temp/`, `uploads/`

## Current vs Legacy

| Aspect | NEW (Jinja2) | LEGACY |
|--------|-------------|---------|
| **Templates** | `templates/` with Jinja2 | Hardcoded in Python |
| **Data Models** | `src/data_models.py` dataclasses | Dictionaries |
| **Languages** | Template swapping | Hardcoded Polish |
| **Configuration** | `config/report_config.yaml` | Constants in code |
| **Structure** | Modular `src/` directory | Single files |
| **Maintenance** | Template editing | Code changes |

## Next Steps

1. **Complete Week 1 MVP**: Implement `report_generator.py` and `pdf_builder.py`
2. **Test new architecture**: Generate sample PDFs
3. **Week 2**: Add Polish/Japanese templates
4. **Week 3**: Update `batch_processor.py` for new architecture
5. **Week 4**: Enhanced web app using new system

This clean structure separates active development from legacy code while preserving all historical work for reference.