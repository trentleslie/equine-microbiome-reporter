"""
FASTQ-to-PDF Pipeline Components
Test-driven development implementation for equine microbiome analysis pipeline.
"""

import os
import zipfile
import logging
import shutil
import time
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import gzip

from data_models import PatientInfo, MicrobiomeData
from csv_processor import CSVProcessor
from report_generator import ReportGenerator
from llm_recommendation_engine import create_recommendation_engine
from real_fastq_processor import process_fastq_directories_to_csv


# Custom exceptions for better error handling
class FASTQProcessingError(Exception):
    """Errors during FASTQ file processing"""
    pass


class CSVValidationError(Exception):
    """Errors during CSV validation"""
    pass


class PerformanceError(Exception):
    """Performance benchmark violations"""
    pass


@dataclass
class ValidationResult:
    """Result of validation operations with detailed feedback"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    outdated_names: List[str] = field(default_factory=list)
    suggested_replacements: Dict[str, str] = field(default_factory=dict)
    column_count_match: bool = False
    required_columns_present: bool = False


@dataclass
class ReportResult:
    """Result of individual report generation"""
    success: bool
    pdf_path: Optional[Path] = None
    patient_name: str = ""
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class ProcessingResult:
    """Result of FASTQ processing stage"""
    success: bool
    csv_path: Optional[str] = None
    processing_time: float = 0.0
    species_count: int = 0
    barcode_count: int = 0
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete pipeline execution result"""
    success: bool
    csv_generated: bool = False
    csv_path: Optional[str] = None
    report_results: List[ReportResult] = field(default_factory=list)
    total_processing_time: float = 0.0
    error: Optional[str] = None


@dataclass 
class PipelineConfig:
    """Configuration for the FASTQ-to-PDF pipeline"""
    data_dir: str  # Directory containing barcode subdirectories
    barcode_dirs: List[str]  # List of barcode directory names (e.g., ['barcode04', 'barcode05'])
    reference_csv: str = "data/25_04_23 bact.csv"
    output_dir: str = "pipeline_output"
    temp_dir: str = "temp_processing"
    parallel_processes: int = 3
    cleanup_temp_files: bool = True
    log_level: str = "INFO"
    performance_benchmarks: bool = False
    csv_filename: str = "processed_abundance.csv"


class FASTQExtractionService:
    """Service for extracting and organizing FASTQ files from zip archives"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_and_organize(self, zip_path: str, temp_dir: str) -> Dict[str, List[str]]:
        """
        Extract FASTQ files from zip and organize by barcode
        
        Args:
            zip_path: Path to zip file containing barcode directories
            temp_dir: Temporary directory for extraction
            
        Returns:
            Dict mapping barcode numbers to lists of FASTQ file paths
            
        Raises:
            FASTQProcessingError: If extraction fails
            zipfile.BadZipFile: If zip file is corrupted
            PermissionError: If cannot access files
        """
        try:
            # Ensure temp directory exists
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Organize files by barcode
            barcode_files = {}
            temp_path = Path(temp_dir)
            
            # Look for barcode directories
            for item in temp_path.iterdir():
                if item.is_dir() and item.name.startswith('barcode'):
                    # Extract barcode number (e.g., "barcode04" -> "04")
                    barcode_num = item.name.replace('barcode', '')
                    
                    # Find all FASTQ files in this directory
                    fastq_files = []
                    for fastq_file in item.glob('*.fastq*'):
                        if fastq_file.is_file():
                            fastq_files.append(str(fastq_file))
                    
                    if fastq_files:
                        barcode_files[barcode_num] = sorted(fastq_files)
                        self.logger.info(f"Found {len(fastq_files)} FASTQ files for barcode {barcode_num}")
            
            if not barcode_files:
                raise FASTQProcessingError("No barcode directories with FASTQ files found in zip")
            
            return barcode_files
            
        except zipfile.BadZipFile as e:
            raise zipfile.BadZipFile(f"Invalid or corrupted zip file: {zip_path}") from e
        except PermissionError as e:
            raise PermissionError(f"Cannot access zip file: {zip_path}") from e
        except Exception as e:
            raise FASTQProcessingError(f"Failed to extract FASTQ files: {str(e)}") from e
    
    def validate_fastq_structure(self, fastq_files: List[str]) -> bool:
        """
        Validate FASTQ file format and readability
        
        Args:
            fastq_files: List of FASTQ file paths to validate
            
        Returns:
            True if all files are valid FASTQ format
            
        Raises:
            ValueError: If FASTQ format is invalid
            FASTQProcessingError: If files cannot be read
        """
        for fastq_path in fastq_files:
            try:
                # Determine if file is gzipped
                if fastq_path.endswith('.gz'):
                    opener = gzip.open
                    mode = 'rt'
                else:
                    opener = open
                    mode = 'r'
                
                with opener(fastq_path, mode) as f:
                    lines_read = 0
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Check FASTQ format (4 lines per read)
                        line_in_read = (line_num - 1) % 4
                        
                        if line_in_read == 0:  # Header line
                            if not line.startswith('@'):
                                raise ValueError(f"Invalid FASTQ format: line {line_num} should start with @")
                        elif line_in_read == 1:  # Sequence line
                            if not line.replace('N', '').replace('A', '').replace('T', '').replace('G', '').replace('C', '') == '':
                                # Allow standard DNA bases plus N for unknown
                                pass
                        elif line_in_read == 2:  # Plus line
                            if not line.startswith('+'):
                                raise ValueError(f"Invalid FASTQ format: line {line_num} should start with +")
                        elif line_in_read == 3:  # Quality line
                            # Quality scores should be ASCII characters
                            pass
                        
                        lines_read += 1
                        # Only validate first few reads for performance
                        if lines_read >= 100:  # Check first 25 reads (4 lines each)
                            break
                
                self.logger.debug(f"Validated FASTQ file: {fastq_path}")
                
            except Exception as e:
                raise FASTQProcessingError(f"Cannot validate FASTQ file {fastq_path}: {str(e)}") from e
        
        return True


class StructuralValidationService:
    """Service for validating CSV structure against reference format"""
    
    def __init__(self, reference_csv_path: Optional[str] = None):
        self.reference_csv_path = reference_csv_path
        self.logger = logging.getLogger(__name__)
        
        if reference_csv_path and Path(reference_csv_path).exists():
            self.reference_columns = self._load_reference_structure()
        else:
            self.reference_columns = None
    
    def _load_reference_structure(self) -> List[str]:
        """Load column structure from reference CSV"""
        try:
            df = pd.read_csv(self.reference_csv_path, nrows=0)  # Just get headers
            return list(df.columns)
        except Exception as e:
            self.logger.warning(f"Could not load reference CSV structure: {e}")
            return []
    
    def validate_structure(self, csv_path: str) -> ValidationResult:
        """
        Validate CSV structure with concrete checks
        
        Args:
            csv_path: Path to CSV file to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        try:
            df = pd.read_csv(csv_path)
            errors = []
            warnings = []
            
            # Check required columns
            required_cols = ['species', 'total', 'phylum', 'genus']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
            
            # Detect barcode columns
            barcode_cols = self.detect_barcode_columns(csv_path)
            if len(barcode_cols) == 0:
                errors.append("No barcode columns found")
            
            # Check for taxonomic columns
            taxonomic_cols = ['superkingdom', 'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'tax']
            missing_taxonomic = [col for col in taxonomic_cols if col not in df.columns]
            if missing_taxonomic:
                warnings.append(f"Missing taxonomic columns: {missing_taxonomic}")
            
            # Validate against reference if available
            column_count_match = False
            required_columns_present = len(missing_cols) == 0
            
            if self.reference_columns:
                column_count_match = len(df.columns) == len(self.reference_columns)
                if not column_count_match:
                    warnings.append(f"Column count mismatch: got {len(df.columns)}, expected {len(self.reference_columns)}")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                missing_columns=missing_cols,
                column_count_match=column_count_match,
                required_columns_present=required_columns_present
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"CSV parsing error: {str(e)}"],
                warnings=[]
            )
    
    def detect_barcode_columns(self, csv_path: str) -> List[str]:
        """
        Detect barcode columns in CSV file
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of barcode column names
        """
        try:
            df = pd.read_csv(csv_path, nrows=0)  # Just get headers
            barcode_cols = [col for col in df.columns if col.startswith('barcode')]
            return sorted(barcode_cols)
        except Exception as e:
            self.logger.error(f"Error detecting barcode columns: {e}")
            return []


class TaxonomicValidationService:
    """Service for validating taxonomic data and nomenclature"""
    
    # Modern GTDB nomenclature mappings
    GTDB_MAPPINGS = {
        'Actinobacteria': 'Actinomycetota',
        'Firmicutes': 'Bacillota',
        'Bacteroidetes': 'Bacteroidota',
        'Proteobacteria': 'Pseudomonadota'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_taxonomic_data(self, csv_path: str) -> ValidationResult:
        """
        Validate taxonomic nomenclature with specific checks
        
        Args:
            csv_path: Path to CSV file to validate
            
        Returns:
            ValidationResult with taxonomic validation details
        """
        try:
            df = pd.read_csv(csv_path)
            errors = []
            warnings = []
            outdated_names = []
            
            if 'phylum' in df.columns:
                unique_phyla = df['phylum'].dropna().unique()
                for phylum in unique_phyla:
                    if phylum in self.GTDB_MAPPINGS:
                        outdated_names.append(phylum)
                        warnings.append(f"Outdated phylum name '{phylum}', should be '{self.GTDB_MAPPINGS[phylum]}'")
            
            # Check species name format
            if 'species' in df.columns:
                species_names = df['species'].dropna()
                invalid_species = []
                for species in species_names:
                    # Basic check for scientific name format (Genus species)
                    if not isinstance(species, str) or len(species.split()) < 2:
                        invalid_species.append(species)
                
                if invalid_species and len(invalid_species) > len(species_names) * 0.1:  # More than 10% invalid
                    warnings.append(f"Many species names may not be in proper scientific format")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                outdated_names=outdated_names,
                suggested_replacements=self.GTDB_MAPPINGS
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Taxonomic validation error: {str(e)}"],
                warnings=[]
            )


class PerformanceBenchmarkService:
    """Service for monitoring performance and enforcing benchmarks"""
    
    def __init__(self, enable_benchmarks: bool = False):
        self.enable_benchmarks = enable_benchmarks
        self.logger = logging.getLogger(__name__)
        
        # Performance limits (in seconds and MB)
        self.benchmarks = {
            'fastq_extraction': {'max_time': 300, 'max_memory': 2048},  # 5 min, 2GB
            'csv_generation': {'max_time': 600, 'max_memory': 4096},    # 10 min, 4GB
            'pdf_generation': {'max_time': 120, 'max_memory': 1024}     # 2 min, 1GB
        }
    
    def benchmark_pipeline_stage(self, stage_name: str, execution_time: float, memory_usage: float = None):
        """
        Record and validate performance metrics
        
        Args:
            stage_name: Name of the pipeline stage
            execution_time: Time taken in seconds
            memory_usage: Peak memory usage in MB (optional)
            
        Raises:
            PerformanceError: If benchmarks are exceeded
        """
        if not self.enable_benchmarks:
            return
        
        if stage_name in self.benchmarks:
            limits = self.benchmarks[stage_name]
            
            if execution_time > limits['max_time']:
                raise PerformanceError(
                    f"{stage_name} exceeded time limit: {execution_time:.2f}s > {limits['max_time']}s"
                )
            
            if memory_usage and memory_usage > limits['max_memory']:
                raise PerformanceError(
                    f"{stage_name} exceeded memory limit: {memory_usage:.2f}MB > {limits['max_memory']}MB"
                )
            
            self.logger.info(f"Performance benchmark passed for {stage_name}: {execution_time:.2f}s")


class BatchPipelineOrchestrator:
    """Main pipeline coordinator with comprehensive error handling"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize services
        self.extraction_service = FASTQExtractionService()
        self.structural_validator = StructuralValidationService(config.reference_csv)
        self.taxonomic_validator = TaxonomicValidationService()
        self.performance_service = PerformanceBenchmarkService(config.performance_benchmarks)
        
        # Initialize existing components
        self.report_generator = ReportGenerator(language='en')
        
        # Initialize LLM engine (optional, gracefully handle failures)
        try:
            self.llm_engine = create_recommendation_engine()
        except Exception as e:
            self.logger.warning(f"LLM engine initialization failed: {e}")
            self.llm_engine = None
        
        # Ensure output directory exists
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the pipeline"""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def process_fastq_to_csv(self, output_csv: str) -> ProcessingResult:
        """
        Process FASTQ files from barcode directories to generate species abundance CSV
        
        Args:
            output_csv: Path for output CSV file
            
        Returns:
            ProcessingResult with processing details
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting real FASTQ processing from directories: {self.config.barcode_dirs}")
            
            # Validate barcode directories exist
            missing_dirs = []
            for barcode_dir in self.config.barcode_dirs:
                barcode_path = Path(self.config.data_dir) / barcode_dir
                if not barcode_path.exists():
                    missing_dirs.append(barcode_dir)
            
            if missing_dirs:
                raise FASTQProcessingError(f"Missing barcode directories: {missing_dirs}")
            
            # Process FASTQ files using real taxonomic classification
            self.logger.info("Processing FASTQ files with taxonomic classification...")
            success = process_fastq_directories_to_csv(
                self.config.data_dir,
                self.config.barcode_dirs,
                output_csv
            )
            
            if not success:
                raise FASTQProcessingError("FASTQ processing failed")
            
            # Get statistics from generated CSV
            if Path(output_csv).exists():
                df = pd.read_csv(output_csv)
                species_count = len(df)
                barcode_count = len([col for col in df.columns if col.startswith('barcode')])
                total_reads = df['total'].sum()
            else:
                raise FASTQProcessingError("Output CSV was not generated")
            
            processing_time = time.time() - start_time
            
            # Performance benchmark
            self.performance_service.benchmark_pipeline_stage(
                'fastq_extraction', processing_time, self._get_memory_usage()
            )
            
            self.logger.info(f"Real FASTQ processing completed in {processing_time:.2f}s")
            self.logger.info(f"  Generated {species_count} species from {total_reads} classified reads")
            
            return ProcessingResult(
                success=True,
                csv_path=output_csv,
                processing_time=processing_time,
                species_count=species_count,
                barcode_count=barcode_count
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"FASTQ processing failed: {str(e)}")
            
            return ProcessingResult(
                success=False,
                processing_time=processing_time,
                error=str(e)
            )
        finally:
            # Cleanup temporary files if requested
            if self.config.cleanup_temp_files:
                self._cleanup_temp_files()
    
    def _create_placeholder_csv(self, fastq_files: Dict[str, List[str]], output_path: str) -> Dict[str, Any]:
        """
        Create placeholder CSV with correct structure for testing
        In production, this would be replaced with actual FASTQ processing
        """
        # Load reference CSV to get structure
        if Path(self.config.reference_csv).exists():
            ref_df = pd.read_csv(self.config.reference_csv)
            
            # Create subset with correct barcode columns
            barcode_columns = [f"barcode{bc.zfill(2)}" for bc in sorted(fastq_files.keys())]
            
            # Select subset of species from reference
            sample_df = ref_df.head(50).copy()  # Use first 50 species
            
            # Zero out all existing barcode columns first
            for col in sample_df.columns:
                if col.startswith('barcode'):
                    sample_df[col] = 0
            
            # Add data for our specific barcodes (replace existing or add new)
            for barcode in barcode_columns:
                # Add some realistic random counts
                import numpy as np
                np.random.seed(42)  # Reproducible
                sample_df[barcode] = np.random.randint(10, 1000, len(sample_df))
            
            # Recalculate total using only our barcode columns
            sample_df['total'] = sample_df[barcode_columns].sum(axis=1)
            
            # Save to output path
            sample_df.to_csv(output_path, index=False)
            
            return {
                'species_count': len(sample_df),
                'barcode_count': len(barcode_columns)
            }
        else:
            # Create minimal CSV structure
            data = {
                'species': ['Streptomyces albidoflavus', 'Arthrobacter citreus'],
                'phylum': ['Actinomycetota', 'Actinomycetota'],
                'genus': ['Streptomyces', 'Arthrobacter'],
                'total': [100, 200]
            }
            
            # Add barcode columns
            for barcode in fastq_files.keys():
                col_name = f"barcode{barcode.zfill(2)}"
                data[col_name] = [50, 100] if barcode == list(fastq_files.keys())[0] else [25, 50]
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            return {
                'species_count': len(df),
                'barcode_count': len(fastq_files)
            }
    
    def generate_batch_reports(self, csv_path: str, patients: List[PatientInfo], output_dir: str) -> List[ReportResult]:
        """
        Generate PDF reports for each patient/barcode
        
        Args:
            csv_path: Path to processed CSV file
            patients: List of patient information
            output_dir: Directory for output PDF files
            
        Returns:
            List of ReportResult objects
        """
        results = []
        
        # Load CSV data
        try:
            # Detect available barcodes
            barcode_columns = self.structural_validator.detect_barcode_columns(csv_path)
            self.logger.info(f"Found barcode columns: {barcode_columns}")
            
        except Exception as e:
            self.logger.error(f"Failed to analyze CSV structure: {e}")
            return [ReportResult(success=False, error=f"CSV analysis failed: {e}") for _ in patients]
        
        for i, patient in enumerate(patients):
            start_time = time.time()
            
            try:
                # Map patient to barcode (assuming order matches)
                if i < len(barcode_columns):
                    barcode_col = barcode_columns[i]
                    self.logger.info(f"Processing {patient.name} with {barcode_col}")
                    
                    # The CSV path and barcode column will be passed to report generator directly
                    
                    # Generate PDF report
                    pdf_filename = f"report_{patient.name}_{patient.sample_number}.pdf"
                    pdf_path = Path(output_dir) / pdf_filename
                    
                    # For now, use a wrapper to handle barcode column
                    # Create a modified CSV processor that works with the specific barcode
                    success = self._generate_report_with_barcode(
                        csv_path=csv_path,
                        patient_info=patient,
                        output_path=str(pdf_path),
                        barcode_column=barcode_col
                    )
                    
                    processing_time = time.time() - start_time
                    
                    if success:
                        results.append(ReportResult(
                            success=True,
                            pdf_path=pdf_path,
                            patient_name=patient.name,
                            processing_time=processing_time
                        ))
                        self.logger.info(f"Successfully generated report for {patient.name}")
                    else:
                        results.append(ReportResult(
                            success=False,
                            patient_name=patient.name,
                            error="PDF generation failed",
                            processing_time=processing_time
                        ))
                else:
                    results.append(ReportResult(
                        success=False,
                        patient_name=patient.name,
                        error=f"No barcode column available for patient {i+1}"
                    ))
                    
            except Exception as e:
                processing_time = time.time() - start_time
                self.logger.error(f"Report generation failed for {patient.name}: {e}")
                results.append(ReportResult(
                    success=False,
                    patient_name=patient.name,
                    error=str(e),
                    processing_time=processing_time
                ))
        
        return results
    
    def _generate_report_with_barcode(self, csv_path: str, patient_info: PatientInfo, output_path: str, barcode_column: str) -> bool:
        """
        Generate report with specific barcode column
        Wrapper to handle barcode-specific CSV processing
        """
        try:
            # Create a temporary CSV processor to get the microbiome data
            processor = CSVProcessor(csv_path, barcode_column)
            microbiome_data = processor.process()
            
            # Use the report generator's template system
            template_context = {
                'patient': patient_info,
                'microbiome_data': microbiome_data,
                'config': self.report_generator.config
            }
            
            # Generate using the PDF builder directly
            pdf_builder = self.report_generator.pdf_builder
            return pdf_builder.generate_pdf(template_context, output_path)
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return False
    
    def run_complete_pipeline(self, patients: List[PatientInfo], output_dir: Optional[str] = None) -> PipelineResult:
        """
        Execute complete FASTQ-to-PDF pipeline
        
        Args:
            patients: List of patient information
            output_dir: Output directory (uses config default if None)
            
        Returns:
            PipelineResult with complete execution details
        """
        start_time = time.time()
        output_dir = output_dir or self.config.output_dir
        
        try:
            self.logger.info("Starting complete FASTQ-to-PDF pipeline")
            
            # Step 1: Process FASTQ to CSV
            csv_path = Path(output_dir) / self.config.csv_filename
            processing_result = self.process_fastq_to_csv(str(csv_path))
            
            if not processing_result.success:
                return PipelineResult(
                    success=False,
                    error=f"FASTQ processing failed: {processing_result.error}",
                    total_processing_time=time.time() - start_time
                )
            
            # Step 2: Validate CSV format
            self.logger.info("Validating CSV format...")
            structural_result = self.structural_validator.validate_structure(str(csv_path))
            taxonomic_result = self.taxonomic_validator.validate_taxonomic_data(str(csv_path))
            
            if not structural_result.is_valid:
                self.logger.warning(f"CSV validation issues: {structural_result.errors}")
            
            if taxonomic_result.warnings:
                self.logger.warning(f"Taxonomic warnings: {taxonomic_result.warnings}")
            
            # Step 3: Generate PDF reports
            self.logger.info("Generating PDF reports...")
            report_results = self.generate_batch_reports(str(csv_path), patients, output_dir)
            
            total_time = time.time() - start_time
            successful_reports = sum(1 for r in report_results if r.success)
            
            self.logger.info(f"Pipeline completed in {total_time:.2f}s")
            self.logger.info(f"Generated {successful_reports}/{len(patients)} reports successfully")
            
            return PipelineResult(
                success=True,
                csv_generated=True,
                csv_path=str(csv_path),
                report_results=report_results,
                total_processing_time=total_time
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Pipeline failed: {str(e)}")
            
            return PipelineResult(
                success=False,
                error=str(e),
                total_processing_time=total_time
            )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0
    
    def _cleanup_temp_files(self):
        """Clean up temporary files and directories"""
        try:
            if Path(self.config.temp_dir).exists():
                shutil.rmtree(self.config.temp_dir)
                self.logger.info(f"Cleaned up temporary directory: {self.config.temp_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")


# Public API functions for simple notebook interface

def create_pipeline(config: PipelineConfig) -> BatchPipelineOrchestrator:
    """Factory method for creating configured pipeline"""
    return BatchPipelineOrchestrator(config)


def run_simple_pipeline(data_dir: str, barcode_dirs: List[str], patients: List[PatientInfo], output_dir: str = "results") -> PipelineResult:
    """
    Simple one-function pipeline execution for notebook users
    
    Args:
        data_dir: Directory containing barcode subdirectories
        barcode_dirs: List of barcode directory names (e.g., ['barcode04', 'barcode05'])
        patients: List of patient information
        output_dir: Directory for output files
        
    Returns:
        PipelineResult with execution details
    """
    config = PipelineConfig(data_dir=data_dir, barcode_dirs=barcode_dirs, output_dir=output_dir)
    pipeline = create_pipeline(config)
    return pipeline.run_complete_pipeline(patients, output_dir)