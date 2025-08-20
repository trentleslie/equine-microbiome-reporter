"""
Notebook Interface for FASTQ-to-PDF Pipeline
Simple interface that avoids relative import issues when using from Jupyter notebooks
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add current directory to path to handle imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the real processing function directly
from real_fastq_processor import process_fastq_directories_to_csv

@dataclass
class PatientInfo:
    """Patient information for report generation"""
    name: str = "Unknown"
    species: str = "Horse"
    age: str = "Unknown"
    sample_number: str = "001"
    date_received: str = "auto-generated"
    date_analyzed: str = "auto-generated"
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"

@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    success: bool
    csv_generated: bool = False
    csv_path: str = None
    total_processing_time: float = 0.0
    species_count: int = 0
    barcode_count: int = 0
    error: str = None

def run_simple_pipeline(data_dir: str, barcode_dirs: List[str], patients: List[PatientInfo], output_dir: str = "results") -> PipelineResult:
    """
    Simple FASTQ-to-CSV pipeline execution for notebook users
    
    Args:
        data_dir: Directory containing barcode subdirectories
        barcode_dirs: List of barcode directory names (e.g., ['barcode04', 'barcode05'])
        patients: List of patient information
        output_dir: Directory for output files
        
    Returns:
        PipelineResult with execution details
    """
    import time
    import pandas as pd
    
    start_time = time.time()
    
    try:
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting FASTQ processing from directories: {barcode_dirs}")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process FASTQ files to CSV
        csv_filename = "processed_abundance.csv"
        csv_path = output_path / csv_filename
        
        logger.info("Processing FASTQ files with taxonomic classification...")
        success = process_fastq_directories_to_csv(
            data_dir,
            barcode_dirs,
            str(csv_path)
        )
        
        if not success:
            return PipelineResult(
                success=False,
                error="FASTQ processing failed",
                total_processing_time=time.time() - start_time
            )
        
        # Get statistics from generated CSV
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            species_count = len(df)
            barcode_count = len([col for col in df.columns if col.startswith('barcode')])
        else:
            return PipelineResult(
                success=False,
                error="Output CSV was not generated",
                total_processing_time=time.time() - start_time
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"FASTQ processing completed in {processing_time:.2f}s")
        logger.info(f"Generated {species_count} species from {df['total'].sum()} classified reads")
        
        return PipelineResult(
            success=True,
            csv_generated=True,
            csv_path=str(csv_path),
            total_processing_time=processing_time,
            species_count=species_count,
            barcode_count=barcode_count
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger = logging.getLogger(__name__)
        logger.error(f"Pipeline failed: {str(e)}")
        
        return PipelineResult(
            success=False,
            error=str(e),
            total_processing_time=processing_time
        )

# Compatibility functions for existing notebook
def create_pipeline_config(data_dir: str, barcode_dirs: List[str], output_dir: str) -> Dict[str, Any]:
    """Create a simple configuration dictionary"""
    return {
        'data_dir': data_dir,
        'barcode_dirs': barcode_dirs,
        'output_dir': output_dir
    }

def generate_simple_pdf_report(csv_path: str, patient_info: PatientInfo, output_path: str, barcode_column: str = None) -> bool:
    """
    Generate professional PDF report from CSV data using Jinja2 templates
    
    Args:
        csv_path: Path to processed CSV file
        patient_info: Patient information
        output_path: Where to save the PDF
        barcode_column: Specific barcode column to process (optional)
        
    Returns:
        bool: True if successful
    """
    try:
        # Use the new ReportGenerator with working visualizations
        from report_generator import ReportGenerator
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Generating professional PDF report with charts for {patient_info.name}")
        
        generator = ReportGenerator(language="en", template_name="simple_report.j2")
        success = generator.generate_report(csv_path, patient_info, output_path, barcode_column)
        
        if success:
            logger.info(f"Professional PDF report generated: {output_path}")
        else:
            logger.error("Failed to generate professional PDF report")
            
        return success
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"PDF generation failed: {e}")
        traceback.print_exc()
        return False