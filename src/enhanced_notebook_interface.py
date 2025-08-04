"""
Enhanced Notebook Interface for FASTQ-to-PDF Pipeline
Supports single-patient aggregation with statistical validation
Based on Gemini feedback for improved scientific rigor
"""

import os
import sys
import logging
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# Add current directory to path to handle imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import processing functions
from real_fastq_processor import process_fastq_directories_to_csv
from barcode_aggregator import (
    EnhancedBarcodeAggregator, 
    AggregationConfig, 
    AggregationResult,
    aggregate_barcodes_for_patient
)

logger = logging.getLogger(__name__)


@dataclass
class PatientInfo:
    """Enhanced patient information for report generation"""
    name: str = "Unknown"
    species: str = "Horse"
    age: str = "Unknown"
    sample_number: str = "001"
    date_received: str = "auto-generated"
    date_analyzed: str = "auto-generated"
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"
    # New fields for technical replicates
    barcode_range: str = ""  # e.g., "004-006"
    notes: str = ""


@dataclass
class ProcessingMode:
    """Processing mode configuration"""
    mode: str = "single_horse"  # "single_horse" or "multiple_horses"
    combine_barcodes: bool = True
    normalization_method: str = "relative_abundance"
    correlation_threshold: float = 0.7
    p_value_threshold: float = 0.05


@dataclass
class EnhancedPipelineResult:
    """Enhanced result of pipeline execution with aggregation details"""
    success: bool
    csv_generated: bool = False
    csv_path: str = None
    combined_csv_path: str = None  # Path to aggregated CSV
    total_processing_time: float = 0.0
    species_count: int = 0
    barcode_count: int = 0
    combined_species_count: int = 0
    aggregation_result: Optional[AggregationResult] = None
    quality_report: Optional[Dict[str, Any]] = None
    error: str = None


def run_enhanced_pipeline(
    data_dir: str, 
    barcode_dirs: List[str], 
    patient: PatientInfo,  # Single patient instead of list
    output_dir: str = "results",
    processing_mode: ProcessingMode = None
) -> EnhancedPipelineResult:
    """
    Enhanced FASTQ-to-PDF pipeline with barcode aggregation
    
    Args:
        data_dir: Directory containing barcode subdirectories
        barcode_dirs: List of barcode directory names (e.g., ['barcode04', 'barcode05'])
        patient: Single patient information
        output_dir: Directory for output files
        processing_mode: Processing configuration
        
    Returns:
        EnhancedPipelineResult with execution details and aggregation metrics
    """
    start_time = time.time()
    
    # Default processing mode
    if processing_mode is None:
        processing_mode = ProcessingMode()
    
    try:
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger.info(f"Starting enhanced FASTQ processing for patient: {patient.name}")
        logger.info(f"Processing mode: {processing_mode.mode}")
        logger.info(f"Barcode directories: {barcode_dirs}")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Process FASTQ files to CSV (original pipeline)
        csv_filename = "processed_abundance.csv"
        csv_path = output_path / csv_filename
        
        logger.info("Step 1: Processing FASTQ files with taxonomic classification...")
        success = process_fastq_directories_to_csv(
            data_dir,
            barcode_dirs,
            str(csv_path)
        )
        
        if not success:
            return EnhancedPipelineResult(
                success=False,
                error="FASTQ processing failed",
                total_processing_time=time.time() - start_time
            )
        
        # Get statistics from generated CSV
        if not csv_path.exists():
            return EnhancedPipelineResult(
                success=False,
                error="Output CSV was not generated",
                total_processing_time=time.time() - start_time
            )
        
        df = pd.read_csv(csv_path)
        original_species_count = len(df)
        barcode_count = len([col for col in df.columns if col.startswith('barcode')])
        
        logger.info(f"Original CSV generated: {original_species_count} species, {barcode_count} barcodes")
        
        # Step 2: Barcode aggregation (if enabled)
        combined_csv_path = None
        aggregation_result = None
        combined_species_count = 0
        
        if processing_mode.combine_barcodes and processing_mode.mode == "single_horse":
            logger.info("Step 2: Aggregating barcodes for single patient...")
            
            # Configure aggregation
            agg_config = AggregationConfig(
                normalization_method=processing_mode.normalization_method,
                correlation_threshold=processing_mode.correlation_threshold,
                p_value_threshold=processing_mode.p_value_threshold
            )
            
            # Find barcode columns in CSV
            barcode_columns = [col for col in df.columns if col.startswith('barcode')]
            if not barcode_columns:
                logger.warning("No barcode columns found - skipping aggregation")
            else:
                # Perform aggregation
                aggregation_result = aggregate_barcodes_for_patient(
                    str(csv_path), 
                    barcode_columns, 
                    patient.name, 
                    agg_config
                )
                
                if aggregation_result.success:
                    # Save combined CSV
                    combined_csv_filename = f"combined_abundance_{patient.name.lower().replace(' ', '_')}.csv"
                    combined_csv_path = output_path / combined_csv_filename
                    aggregation_result.combined_data.to_csv(combined_csv_path, index=False)
                    combined_species_count = len(aggregation_result.combined_data)
                    
                    logger.info(f"Barcode aggregation successful!")
                    logger.info(f"   Combined CSV: {combined_csv_path}")
                    logger.info(f"   Species: {combined_species_count}")
                    logger.info(f"   Total reads: {aggregation_result.combined_total_reads}")
                    
                    # Log validation results
                    for pair, corr in aggregation_result.validation_result.correlations.items():
                        p_val = aggregation_result.validation_result.p_values[pair]
                        logger.info(f"   Correlation {pair}: r={corr:.3f}, p={p_val:.3f}")
                        
                else:
                    logger.warning(f"Barcode aggregation failed: {aggregation_result.error_message}")
        
        # Step 3: Generate quality report
        quality_report = _generate_quality_report(df, aggregation_result, barcode_dirs)
        
        # Calculate total processing time
        total_time = time.time() - start_time
        
        logger.info(f"Enhanced pipeline completed in {total_time:.2f} seconds")
        
        return EnhancedPipelineResult(
            success=True,
            csv_generated=True,
            csv_path=str(csv_path),
            combined_csv_path=str(combined_csv_path) if combined_csv_path else None,
            total_processing_time=total_time,
            species_count=original_species_count,
            barcode_count=barcode_count,
            combined_species_count=combined_species_count,
            aggregation_result=aggregation_result,
            quality_report=quality_report
        )
        
    except Exception as e:
        logger.error(f"Enhanced pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        
        return EnhancedPipelineResult(
            success=False,
            error=str(e),
            total_processing_time=time.time() - start_time
        )


def _generate_quality_report(df: pd.DataFrame, 
                           aggregation_result: Optional[AggregationResult],
                           barcode_dirs: List[str]) -> Dict[str, Any]:
    """
    Generate comprehensive quality report
    """
    quality_report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'barcode_dirs': barcode_dirs,
        'original_data': {},
        'aggregation': {},
        'recommendations': []
    }
    
    # Original data quality metrics
    barcode_columns = [col for col in df.columns if col.startswith('barcode')]
    
    for col in barcode_columns:
        reads = df[col].fillna(0)
        quality_report['original_data'][col] = {
            'total_reads': int(reads.sum()),
            'species_count': int((reads > 0).sum()),
            'max_abundance': float(reads.max()),
            'mean_abundance': float(reads.mean()),
            'top_species': df.loc[reads.idxmax(), 'species'] if reads.max() > 0 else 'None'
        }
    
    # Aggregation quality metrics
    if aggregation_result and aggregation_result.success:
        quality_report['aggregation'] = {
            'success': True,
            'normalization_method': aggregation_result.normalization_stats.get('method', 'unknown'),
            'combined_species_count': len(aggregation_result.combined_data),
            'combined_total_reads': aggregation_result.combined_total_reads,
            'correlations': aggregation_result.validation_result.correlations,
            'p_values': aggregation_result.validation_result.p_values,
            'warnings': aggregation_result.validation_result.warnings,
            'species_overlap': aggregation_result.species_overlap
        }
        
        # Generate recommendations based on quality metrics
        if aggregation_result.validation_result.warnings:
            quality_report['recommendations'].append("Review barcode correlation warnings")
        
        if aggregation_result.combined_total_reads < 100:
            quality_report['recommendations'].append("Low total read count - consider increasing sequencing depth")
            
    else:
        quality_report['aggregation'] = {
            'success': False,
            'error': aggregation_result.error_message if aggregation_result else 'No aggregation performed'
        }
    
    return quality_report


# Legacy compatibility function
def run_simple_pipeline(data_dir: str, barcode_dirs: List[str], 
                       patients: List[PatientInfo], output_dir: str = "results") -> EnhancedPipelineResult:
    """
    Legacy compatibility function - converts multiple patients to single patient mode
    """
    if len(patients) > 1:
        logger.warning(f"Multiple patients provided ({len(patients)}) - using first patient for single-horse mode")
    
    patient = patients[0] if patients else PatientInfo()
    
    # Set barcode range for documentation
    if len(barcode_dirs) > 1:
        patient.barcode_range = f"{barcode_dirs[0]}-{barcode_dirs[-1]}"
        patient.notes = f"Combined analysis from {len(barcode_dirs)} technical replicates"
    
    return run_enhanced_pipeline(data_dir, barcode_dirs, patient, output_dir)


def generate_simple_pdf_report(csv_path: str, patient_info: PatientInfo, 
                             output_path: str, barcode_column: str = None) -> bool:
    """
    Generate PDF report - enhanced to work with combined CSV data
    """
    try:
        from notebook_pdf_generator import NotebookPDFGenerator
        
        # Determine which CSV to use
        csv_file = Path(csv_path)
        
        # If this is a combined CSV, use it directly
        if 'combined_abundance' in csv_file.name:
            barcode_column = 'total_combined'  # Use combined column
            logger.info(f"Generating report from combined CSV: {csv_file.name}")
        else:
            logger.info(f"Generating report from original CSV with barcode: {barcode_column}")
        
        generator = NotebookPDFGenerator(language="en")
        success = generator.generate_report(csv_path, patient_info, output_path, barcode_column)
        
        if success:
            logger.info(f"PDF report generated successfully: {output_path}")
        else:
            logger.error(f"PDF report generation failed")
            
        return success
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    patient = PatientInfo(
        name="Montana",
        age="20 years",
        sample_number="004-006_combined",
        performed_by="Dr. Smith",
        requested_by="Owner Johnson"
    )
    
    processing_mode = ProcessingMode(
        mode="single_horse",
        combine_barcodes=True,
        normalization_method="relative_abundance",
        correlation_threshold=0.7
    )
    
    # Test with sample data
    result = run_enhanced_pipeline(
        data_dir="../data",
        barcode_dirs=["barcode04", "barcode05", "barcode06"],
        patient=patient,
        output_dir="enhanced_results",
        processing_mode=processing_mode
    )
    
    if result.success:
        print(f"✅ Enhanced pipeline successful!")
        print(f"   Original species: {result.species_count}")
        print(f"   Combined species: {result.combined_species_count}")
        print(f"   Processing time: {result.total_processing_time:.2f}s")
    else:
        print(f"❌ Pipeline failed: {result.error}")