#!/usr/bin/env python3
"""
Continue the pipeline from existing Kraken2 reports.
Processes: kreport → CSV → Clinical filtering → PDF reports
"""

import sys
import argparse
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from full_pipeline import FullPipeline
from data_models import PatientInfo
from report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Process existing Kraken2 reports through the rest of the pipeline."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process existing Kraken2 reports')
    parser.add_argument('--kreport-dir', type=Path, required=True,
                        help='Directory containing Kraken2 .kreport files')
    parser.add_argument('--output-dir', type=Path, default=Path('pipeline_output'),
                        help='Output directory for results (default: pipeline_output)')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize pipeline with proper directories
    pipeline = FullPipeline(
        input_dir=args.kreport_dir,  # Use kreport_dir as input
        output_dir=args.output_dir,
        kraken2_db=Path.home() / "kraken2_db"
    )
    
    # Find existing kreport files in the specified directory
    kreport_files = list(args.kreport_dir.glob("*.kreport"))
    logger.info(f"Found {len(kreport_files)} Kraken2 reports to process")
    
    for kreport_file in kreport_files:
        sample_name = kreport_file.stem
        logger.info(f"\nProcessing {sample_name}")
        
        try:
            # Step 1: Convert to CSV
            logger.info("  Converting to CSV...")
            csv_file = pipeline.kreport_to_csv(kreport_file, sample_name)
            
            # Step 2: Apply clinical filtering
            logger.info("  Applying clinical filtering...")
            filtered_csv, excel_review = pipeline.apply_clinical_filter(csv_file, sample_name)
            
            # Step 3: Generate PDF report
            logger.info("  Generating PDF report...")
            pdf_report = pipeline.generate_pdf_report(filtered_csv, sample_name)
            
            logger.info(f"✅ {sample_name} complete!")
            logger.info(f"   CSV: {csv_file}")
            logger.info(f"   Excel: {excel_review}")
            logger.info(f"   PDF: {pdf_report}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {sample_name}: {e}")
    
    logger.info("\n" + "="*60)
    logger.info("Pipeline continuation complete!")
    logger.info(f"Results in: {args.output_dir}/")
    
    # List all outputs
    pdf_files = list((args.output_dir / "pdf_reports").glob("*.pdf"))
    if pdf_files:
        logger.info(f"\n📄 Generated PDF reports:")
        for pdf in pdf_files:
            logger.info(f"   • {pdf.name}")


if __name__ == "__main__":
    main()