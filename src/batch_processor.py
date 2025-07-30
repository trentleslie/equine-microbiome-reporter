"""
Batch processing module for generating multiple microbiome reports.

This module provides functionality to process multiple CSV files and generate
PDF reports in batch, with support for parallel processing, validation, and
manifest-based processing.
"""

import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import yaml

from .report_generator import ReportGenerator
from .data_models import PatientInfo
from .csv_processor import CSVProcessor


class BatchConfig:
    """Configuration for batch processing."""
    
    def __init__(self, **kwargs):
        """Initialize batch configuration with defaults."""
        # Directories
        self.data_dir = Path(kwargs.get('data_dir', 'data'))
        self.reports_dir = Path(kwargs.get('reports_dir', 'reports/batch_output'))
        
        # Processing settings
        self.language = kwargs.get('language', 'en')
        self.parallel_processing = kwargs.get('parallel_processing', True)
        self.max_workers = kwargs.get('max_workers', min(4, os.cpu_count() or 1))
        
        # Default patient info
        self.default_performed_by = kwargs.get('default_performed_by', 'Laboratory Staff')
        self.default_requested_by = kwargs.get('default_requested_by', 'Veterinarian')
        self.default_species = kwargs.get('default_species', 'Horse')
        
        # Quality control thresholds
        self.min_species_count = kwargs.get('min_species_count', 10)
        self.max_unassigned_percentage = kwargs.get('max_unassigned_percentage', 50.0)
        self.required_phyla = kwargs.get('required_phyla', 
            ["Bacillota", "Bacteroidota", "Pseudomonadota"])
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def to_dict(self):
        """Convert configuration to dictionary."""
        return {
            'data_dir': str(self.data_dir),
            'reports_dir': str(self.reports_dir),
            'language': self.language,
            'parallel_processing': self.parallel_processing,
            'max_workers': self.max_workers,
            'default_performed_by': self.default_performed_by,
            'default_requested_by': self.default_requested_by,
            'default_species': self.default_species,
            'min_species_count': self.min_species_count,
            'max_unassigned_percentage': self.max_unassigned_percentage,
            'required_phyla': self.required_phyla
        }


class BatchProcessor:
    """Batch processor for microbiome reports."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize batch processor with configuration."""
        self.config = config or BatchConfig()
        self.results = []
        self.errors = []
        
    def extract_patient_info_from_filename(self, filename: str) -> PatientInfo:
        """Extract patient information from filename.
        
        Expected formats:
        - DD_MM_YY_name.csv
        - sample_N.csv
        - name.csv
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            PatientInfo object with extracted information
        """
        base_name = Path(filename).stem
        parts = base_name.split('_')
        
        patient_info = PatientInfo(
            species=self.config.default_species,
            performed_by=self.config.default_performed_by,
            requested_by=self.config.default_requested_by
        )
        
        # Try to extract date and name from filename
        if len(parts) >= 4 and parts[0].isdigit() and parts[1].isdigit():
            # Format: DD_MM_YY_name
            patient_info.name = ' '.join(parts[3:]).replace('bact', '').strip().title()
            try:
                date_str = f"{parts[0]}.{parts[1]}.20{parts[2]}"
                patient_info.date_received = date_str
            except:
                pass
        elif base_name.startswith('sample_'):
            # Format: sample_N
            patient_info.name = f"Sample {parts[-1]}"
            patient_info.sample_number = parts[-1]
        else:
            # Use filename as name
            patient_info.name = base_name.replace('_', ' ').title()
            
        # Generate sample number if not set
        if patient_info.sample_number == "001":
            patient_info.sample_number = f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')[-6:]}"
            
        return patient_info
    
    def validate_csv_file(self, csv_path: Path) -> Tuple[bool, str]:
        """Validate CSV file for quality control.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check file exists
            if not csv_path.exists():
                return False, f"File not found: {csv_path}"
                
            # Try to load with CSVProcessor
            # First, auto-detect barcode column
            import pandas as pd
            df = pd.read_csv(csv_path)
            barcode_columns = [col for col in df.columns if col.startswith('barcode')]
            if not barcode_columns:
                return False, "No barcode columns found in CSV"
            
            barcode_column = barcode_columns[0]  # Use first barcode column found
            processor = CSVProcessor(str(csv_path), barcode_column)
            data = processor.process()
            
            # Quality checks
            if data.total_species_count < self.config.min_species_count:
                return False, f"Too few species detected: {data.total_species_count} < {self.config.min_species_count}"
                
            # Check for required phyla
            missing_phyla = []
            for phylum in self.config.required_phyla:
                if phylum not in data.phylum_distribution or data.phylum_distribution[phylum] == 0:
                    missing_phyla.append(phylum)
                    
            if missing_phyla:
                return False, f"Missing required phyla: {', '.join(missing_phyla)}"
                
            # Check unassigned percentage
            unassigned = data.phylum_distribution.get('Unassigned', 0)
            if unassigned > self.config.max_unassigned_percentage:
                return False, f"Too many unassigned species: {unassigned:.1f}% > {self.config.max_unassigned_percentage}%"
                
            return True, "Validation passed"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def process_single_file(self, csv_path: Path, validate: bool = True) -> Dict:
        """Process a single CSV file to generate PDF report.
        
        Args:
            csv_path: Path to CSV file
            validate: Whether to validate file before processing
            
        Returns:
            Dictionary with processing results
        """
        result = {
            'csv_file': str(csv_path),
            'output_file': None,
            'success': False,
            'message': '',
            'processing_time': 0,
            'patient_name': '',
            'validation_passed': True
        }
        
        start_time = time.time()
        
        try:
            # Validate file if requested
            if validate:
                is_valid, validation_msg = self.validate_csv_file(csv_path)
                result['validation_passed'] = is_valid
                if not is_valid:
                    result['message'] = f"Validation failed: {validation_msg}"
                    return result
            
            # Extract patient info
            patient_info = self.extract_patient_info_from_filename(csv_path.name)
            result['patient_name'] = patient_info.name
            
            # Generate output filename
            output_filename = f"{csv_path.stem}_report_{self.config.language}.pdf"
            output_path = self.config.reports_dir / output_filename
            
            # Generate report
            generator = ReportGenerator(language=self.config.language)
            success = generator.generate_report(
                csv_path=str(csv_path),
                patient_info=patient_info,
                output_path=str(output_path)
            )
            
            if success:
                result['success'] = True
                result['output_file'] = str(output_path)
                result['message'] = 'Report generated successfully'
            else:
                result['message'] = 'Report generation failed'
                
        except Exception as e:
            result['message'] = f"Error: {str(e)}"
            
        finally:
            result['processing_time'] = time.time() - start_time
            
        return result
    
    def process_directory(self, progress_callback: Optional[Callable] = None, 
                         validate: bool = True) -> List[Dict]:
        """Process all CSV files in the data directory.
        
        Args:
            progress_callback: Optional callback function for progress updates
            validate: Whether to validate files before processing
            
        Returns:
            List of processing results
        """
        # Find all CSV files
        csv_files = list(self.config.data_dir.glob("*.csv"))
        
        if not csv_files:
            return []
        
        results = []
        
        if self.config.parallel_processing and len(csv_files) > 1:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_file = {
                    executor.submit(self.process_single_file, csv_file, validate): csv_file
                    for csv_file in csv_files
                }
                
                for i, future in enumerate(as_completed(future_to_file)):
                    csv_file = future_to_file[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'csv_file': str(csv_file),
                            'success': False,
                            'message': f"Processing error: {str(e)}"
                        })
                    
                    if progress_callback:
                        progress_callback(i + 1, len(csv_files))
        else:
            # Sequential processing
            for i, csv_file in enumerate(csv_files):
                result = self.process_single_file(csv_file, validate)
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, len(csv_files))
        
        self.results = results
        return results
    
    def process_from_manifest(self, manifest_path: Path, 
                            progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Process files using a manifest with patient information.
        
        Args:
            manifest_path: Path to manifest CSV file
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processing results
        """
        manifest_df = pd.read_csv(manifest_path)
        results = []
        
        for idx, row in manifest_df.iterrows():
            # Create patient info from manifest
            patient_info = PatientInfo(
                name=row.get('patient_name', 'Unknown'),
                species=row.get('species', self.config.default_species),
                age=row.get('age', 'Unknown'),
                sample_number=row.get('sample_number', 'AUTO'),
                performed_by=row.get('performed_by', self.config.default_performed_by),
                requested_by=row.get('requested_by', self.config.default_requested_by)
            )
            
            # Process file
            csv_path = self.config.data_dir / row['csv_file']
            output_path = self.config.reports_dir / f"{patient_info.name.replace(' ', '_')}_report_{self.config.language}.pdf"
            
            start_time = time.time()
            
            try:
                generator = ReportGenerator(language=self.config.language)
                success = generator.generate_report(
                    csv_path=str(csv_path),
                    patient_info=patient_info,
                    output_path=str(output_path)
                )
                
                results.append({
                    'csv_file': row['csv_file'],
                    'patient_name': patient_info.name,
                    'success': success,
                    'output_file': str(output_path) if success else None,
                    'processing_time': time.time() - start_time,
                    'message': 'Report generated successfully' if success else 'Report generation failed'
                })
                
            except Exception as e:
                results.append({
                    'csv_file': row['csv_file'],
                    'patient_name': patient_info.name,
                    'success': False,
                    'error': str(e),
                    'message': f'Error: {str(e)}',
                    'processing_time': time.time() - start_time
                })
            
            if progress_callback:
                progress_callback(idx + 1, len(manifest_df))
        
        self.results = results
        return results
    
    def generate_summary_report(self) -> Dict:
        """Generate summary statistics from processing results.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.results:
            return {}
            
        successful = sum(1 for r in self.results if r.get('success', False))
        failed = len(self.results) - successful
        
        total_time = sum(r.get('processing_time', 0) for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': len(self.results),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(self.results) * 100) if self.results else 0,
            'total_processing_time': total_time,
            'average_processing_time': avg_time,
            'configuration': self.config.to_dict()
        }
        
        # Add failure reasons if any
        if failed > 0:
            failures = [r for r in self.results if not r.get('success', False)]
            failure_reasons = {}
            for f in failures:
                reason = f.get('message', 'Unknown error')
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            summary['failure_reasons'] = failure_reasons
        
        return summary
    
    def save_results_to_csv(self, output_path: Optional[Path] = None) -> Path:
        """Save processing results to CSV file.
        
        Args:
            output_path: Optional path for output file
            
        Returns:
            Path to saved CSV file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.config.reports_dir / f"batch_report_{timestamp}.csv"
            
        df = pd.DataFrame(self.results)
        df.to_csv(output_path, index=False)
        
        return output_path