#!/usr/bin/env python3
"""
Generate a clean, modern report layout (pages 2-5 only, no title page)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.data_models import PatientInfo, MicrobiomeData
from src.chart_generator import ChartGenerator
from src.csv_processor import CSVProcessor
from jinja2 import Environment, Template
import yaml
import logging
import pandas as pd
from weasyprint import HTML, CSS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_clean_report(csv_path, patient_info, output_path="clean_report.pdf"):
    """Generate a clean, modern report without title page"""

    csv_path = Path(csv_path)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False

    logger.info(f"Processing: {csv_path}")

    # Find the barcode column
    df = pd.read_csv(csv_path, nrows=1)
    barcode_cols = [c for c in df.columns if c.startswith('barcode')]
    barcode_column = barcode_cols[0] if barcode_cols else None

    if not barcode_column:
        logger.error("No barcode column found in CSV")
        return False

    logger.info(f"Using barcode column: {barcode_column}")

    # Process CSV data
    processor = CSVProcessor(csv_path=csv_path, barcode_column=barcode_column)
    microbiome_data = processor.process()

    if not microbiome_data:
        logger.error("Failed to process CSV data")
        return False

    logger.info(f"Processed {len(microbiome_data.species_list)} species")

    # Generate charts
    logger.info("Generating charts...")
    chart_gen = ChartGenerator(output_dir="temp_charts")
    charts = chart_gen.generate_all_charts(microbiome_data)
    logger.info(f"Generated {len(charts)} charts")

    # Load configuration
    config_path = Path("config/report_config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Load CSS
    css_path = Path("templates/clean/styles.css")
    css_content = css_path.read_text()

    # Load page templates
    template_dir = Path("templates/clean")
    page1_content = (template_dir / "page1_sequencing.html").read_text()
    page2_content = (template_dir / "page2_phylum.html").read_text()
    page3_content = (template_dir / "page3_clinical.html").read_text()
    page4_content = (template_dir / "page4_summary.html").read_text()
    page5_content = (template_dir / "page5_species_list.html").read_text()

    # Load master template
    master_template = (template_dir / "report_clean.html").read_text()

    # Prepare context
    context = {
        'patient': patient_info,
        'data': microbiome_data,
        'charts': charts,
        'config': config,
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'recommendations': microbiome_data.recommendations if hasattr(microbiome_data, 'recommendations') else []
    }

    # Render each page
    env = Environment()

    page1_rendered = env.from_string(page1_content).render(**context)
    page2_rendered = env.from_string(page2_content).render(**context)
    page3_rendered = env.from_string(page3_content).render(**context)
    page4_rendered = env.from_string(page4_content).render(**context)
    page5_rendered = env.from_string(page5_content).render(**context)

    # Combine into master template
    final_context = {
        'patient': patient_info,
        'css_content': css_content,
        'page1_content': page1_rendered,
        'page2_content': page2_rendered,
        'page3_content': page3_rendered,
        'page4_content': page4_rendered,
        'page5_content': page5_rendered
    }

    final_html = env.from_string(master_template).render(**final_context)

    # Save HTML for debugging
    html_path = Path(output_path).with_suffix('.html')
    html_path.write_text(final_html)
    logger.info(f"HTML saved: {html_path}")

    # Convert to PDF using WeasyPrint
    try:
        # Get absolute path for base URL
        base_url = Path.cwd().as_uri() + '/'
        HTML(string=final_html, base_url=base_url).write_pdf(output_path)
        logger.info(f"✅ Clean report generated: {output_path}")
        logger.info("This PDF contains 5 pages of clean, modern layout")
        logger.info("Combine with your NG-GP title page for the complete report")
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return False

def main():
    """Generate a test report with clean layout"""

    # Sample patient info
    patient = PatientInfo(
        name="Montana",
        age="8 years",
        species="Equine",
        sample_number="NG-GP-2024-001",
        date_received="2024-03-15",
        date_analyzed="2024-03-16",
        performed_by="MIMT Genetics Lab",
        requested_by="Dr. Alexandra Matusiak"
    )

    # Find sample data
    sample_csv = Path("data/sample_1.csv")
    if not sample_csv.exists():
        sample_csv = Path("data/barcode04.csv")
        if not sample_csv.exists():
            logger.error("No sample data found")
            return 1

    # Generate report
    output_dir = Path("test_report_output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "clean_report.pdf"

    success = generate_clean_report(sample_csv, patient, output_path)

    if success:
        print("\n✅ Clean report generated successfully!")
        print(f"Output: {output_path}")
        print("\nFeatures:")
        print("  - Modern, clean layout")
        print("  - 5 pages (no title page)")
        print("  - Professional medical report styling")
        print("  - Clear data visualization")
        print("\nNext steps:")
        print("1. Save your NG-GP title page as title_page.pdf")
        print("2. Combine PDFs:")
        print("   pdftk title_page.pdf clean_report.pdf cat output final_report.pdf")
        return 0
    else:
        print("\n❌ Failed to generate report")
        return 1

if __name__ == "__main__":
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Prevent Qt issues
    sys.exit(main())