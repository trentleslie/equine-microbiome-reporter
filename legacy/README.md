# Legacy Code Archive

This directory contains the original implementation files that have been superseded by the new Jinja2-based architecture.

## Legacy Components

### PDF Generators (Original Implementation)
- `pdf_generator.py` - Basic PDF generation
- `advanced_pdf_generator.py` - Polish laboratory format
- `enhanced_pdf_generator.py` - Week 1 MVP (Polish)
- `enhanced_pdf_generator_en.py` - Week 1 MVP (English)
- `template_based_generator.py` - Early template experiment
- `report_templates.py` - Template constants

### Web Application (Phase 2)
- `web_app.py` - Flask web interface
- `run_web_app.sh` - Startup script
- `static/` - CSS, JS, and static assets
- HTML templates for web interface

### Configuration
- `config.yaml` - Legacy configuration format

### Generated Outputs
- `generated_reports/` - Test outputs from legacy system

## Why These Were Moved

The new Jinja2-based architecture provides:
- **Better separation of concerns** (templates vs logic)
- **Multi-language support** (template swapping)
- **Easier maintenance** (edit templates, not code)
- **Future flexibility** (same templates → web app)

## Legacy Usage (Reference Only)

```bash
# Legacy enhanced generator (Polish)
poetry run python legacy/enhanced_pdf_generator.py data/sample.csv -o reports/legacy_report.pdf

# Legacy web app
./legacy/run_web_app.sh
```

**Note**: These legacy components are preserved for reference but should not be used for new development. Use the new `src/` modules and `templates/` system instead.