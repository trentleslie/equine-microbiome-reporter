#!/usr/bin/env python3
"""
Batch PDF Report Processor for Microbiome Analysis
Automates the generation of multiple PDF reports from CSV files
"""

import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import yaml
import json
from typing import Dict, List, Optional
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback

# Import the report generator (assuming it's in the same directory or in Python path)
try:
    from advanced_pdf_generator import AdvancedMicrobiomeReportGenerator
except ImportError:
    print("Error: advanced_pdf_generator.py not found. Please ensure it's in the same directory.")
    sys.exit(1)


class BatchReportProcessor:
    """Batch processes multiple CSV files to generate PDF reports."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the batch processor.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
        """
        self.config = self._load_config(config_file) if config_file else {}
        self.setup_logging()
        
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif config_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError("Configuration file must be YAML or JSON")
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'batch_report_processing.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_single_file(self, csv_file: str, output_dir: str, 
                          patient_data: Optional[Dict] = None) -> bool:
        """
        Process a single CSV file to generate a PDF report.
        
        Args:
            csv_file: Path to the CSV file
            output_dir: Directory to save the PDF report
            patient_data: Optional patient information
            
        Returns:
            Success status
        """
        try:
            csv_path = Path(csv_file)
            
            if not csv_path.exists():
                self.logger.error(f"CSV file not found: {csv_file}")
                return False
            
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            output_file = output_path / f"{csv_path.stem}_report.pdf"
            
            # Get patient info from config or use defaults
            if patient_data is None:
                patient_data = self._get_patient_data_from_filename(csv_path.stem)
            
            # Get barcode column
            barcode_column = self.config.get('barcode_column', 'barcode59')
            
            self.logger.info(f"Processing {csv_file} -> {output_file}")
            
            # Generate the report
            generator = AdvancedMicrobiomeReportGenerator(str(csv_path), barcode_column)
            generator.generate_report(str(output_file), patient_data)
            
            self.logger.info(f"Successfully generated report: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {csv_file}: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False
    
    def _get_patient_data_from_filename(self, filename: str) -> Dict[str, str]:
        """
        Extract patient data from filename or use defaults.
        Expected format: DD_MM_YY_name.csv or similar
        """
        parts = filename.split('_')
        
        patient_data = {
            'name': 'Unknown',
            'species': self.config.get('default_species', 'Koń'),
            'age': self.config.get('default_age', 'Unknown'),
            'sample_number': 'Auto-' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'date_received': datetime.now().strftime('%d.%m.%Y r.'),
            'performed_by': self.config.get('performed_by', 'Laboratory Staff'),
            'requested_by': self.config.get('requested_by', 'Veterinarian')
        }
        
        # Try to extract name from filename
        if len(parts) >= 4:
            # Assume format: DD_MM_YY_name
            patient_data['name'] = parts[3].replace('.csv', '').capitalize()
            try:
                date_str = f"{parts[0]}.{parts[1]}.20{parts[2]} r."
                patient_data['date_received'] = date_str
            except:
                pass
        
        return patient_data
    
    def process_directory(self, input_dir: str, output_dir: str, 
                         pattern: str = "*.csv", parallel: bool = True) -> Dict[str, bool]:
        """
        Process all CSV files in a directory.
        
        Args:
            input_dir: Directory containing CSV files
            output_dir: Directory to save PDF reports
            pattern: File pattern to match (default: *.csv)
            parallel: Whether to process files in parallel
            
        Returns:
            Dictionary mapping filenames to success status
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise ValueError(f"Input directory not found: {input_dir}")
        
        # Find all CSV files
        csv_files = list(input_path.glob(pattern))
        
        if not csv_files:
            self.logger.warning(f"No CSV files found in {input_dir} matching pattern {pattern}")
            return {}
        
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        
        results = {}
        
        if parallel:
            # Process files in parallel
            max_workers = self.config.get('max_workers', os.cpu_count())
            
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.process_single_file, str(csv_file), output_dir): csv_file
                    for csv_file in csv_files
                }
                
                for future in as_completed(future_to_file):
                    csv_file = future_to_file[future]
                    try:
                        success = future.result()
                        results[str(csv_file)] = success
                    except Exception as e:
                        self.logger.error(f"Error processing {csv_file}: {str(e)}")
                        results[str(csv_file)] = False
        else:
            # Process files sequentially
            for csv_file in csv_files:
                success = self.process_single_file(str(csv_file), output_dir)
                results[str(csv_file)] = success
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        self.logger.info(f"Processing complete: {successful} successful, {failed} failed")
        
        return results
    
    def process_from_manifest(self, manifest_file: str, output_dir: str) -> Dict[str, bool]:
        """
        Process files based on a manifest file containing patient information.
        
        Manifest format (CSV):
        csv_file,patient_name,species,age,sample_number,date_received,performed_by,requested_by
        
        Args:
            manifest_file: Path to manifest CSV file
            output_dir: Directory to save PDF reports
            
        Returns:
            Dictionary mapping filenames to success status
        """
        manifest_df = pd.read_csv(manifest_file)
        results = {}
        
        for _, row in manifest_df.iterrows():
            csv_file = row['csv_file']
            
            # Extract patient data from manifest
            patient_data = {
                'name': row.get('patient_name', 'Unknown'),
                'species': row.get('species', 'Koń'),
                'age': row.get('age', 'Unknown'),
                'sample_number': row.get('sample_number', 'Auto'),
                'date_received': row.get('date_received', datetime.now().strftime('%d.%m.%Y r.')),
                'performed_by': row.get('performed_by', 'Laboratory Staff'),
                'requested_by': row.get('requested_by', 'Veterinarian')
            }
            
            success = self.process_single_file(csv_file, output_dir, patient_data)
            results[csv_file] = success
        
        return results


# Example configuration file (config.yaml):
EXAMPLE_CONFIG = """
# Batch Report Processing Configuration

# Default barcode column to analyze
barcode_column: barcode59

# Default patient information
default_species: Koń
default_age: Unknown
performed_by: Julia Kończak
requested_by: Aleksandra Matusiak

# Processing settings
max_workers: 4  # Number of parallel processes
log_level: INFO
log_file: batch_processing.log

# Output settings
output_format: pdf
create_summary: true
"""

# Example manifest file (manifest.csv):
EXAMPLE_MANIFEST = """csv_file,patient_name,species,age,sample_number,date_received,performed_by,requested_by
data/25_04_23_bact.csv,Montana,Koń,20 lat,506,07.05.2025 r.,Julia Kończak,Aleksandra Matusiak
data/26_04_23_bact.csv,Thunder,Koń,15 lat,507,08.05.2025 r.,Julia Kończak,Dr. Smith
data/27_04_23_bact.csv,Lightning,Koń,8 lat,508,09.05.2025 r.,Julia Kończak,Dr. Johnson
"""


def main():
    """Main function for batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch process microbiome CSV files to generate PDF reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all CSV files in a directory
  python batch_processor.py -i data/ -o reports/
  
  # Process with configuration file
  python batch_processor.py -i data/ -o reports/ -c config.yaml
  
  # Process from manifest file
  python batch_processor.py -m manifest.csv -o reports/
  
  # Process single file
  python batch_processor.py -f data/sample.csv -o reports/
        """
    )
    
    parser.add_argument('-i', '--input-dir', help='Input directory containing CSV files')
    parser.add_argument('-o', '--output-dir', required=True, help='Output directory for PDF reports')
    parser.add_argument('-c', '--config', help='Configuration file (YAML or JSON)')
    parser.add_argument('-m', '--manifest', help='Manifest file with patient information')
    parser.add_argument('-f', '--file', help='Process single CSV file')
    parser.add_argument('-p', '--pattern', default='*.csv', help='File pattern to match (default: *.csv)')
    parser.add_argument('--no-parallel', action='store_true', help='Disable parallel processing')
    parser.add_argument('--create-example-config', action='store_true', 
                       help='Create example configuration file')
    parser.add_argument('--create-example-manifest', action='store_true',
                       help='Create example manifest file')
    
    args = parser.parse_args()
    
    # Create example files if requested
    if args.create_example_config:
        with open('config_example.yaml', 'w') as f:
            f.write(EXAMPLE_CONFIG)
        print("Created example configuration file: config_example.yaml")
        return
    
    if args.create_example_manifest:
        with open('manifest_example.csv', 'w') as f:
            f.write(EXAMPLE_MANIFEST.strip())
        print("Created example manifest file: manifest_example.csv")
        return
    
    # Initialize processor
    processor = BatchReportProcessor(args.config)
    
    # Process based on input type
    if args.file:
        # Process single file
        success = processor.process_single_file(args.file, args.output_dir)
        sys.exit(0 if success else 1)
    
    elif args.manifest:
        # Process from manifest
        results = processor.process_from_manifest(args.manifest, args.output_dir)
        
    elif args.input_dir:
        # Process directory
        results = processor.process_directory(
            args.input_dir, 
            args.output_dir, 
            args.pattern,
            parallel=not args.no_parallel
        )
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # Print summary
    if results:
        successful = sum(1 for success in results.values() if success)
        print(f"\nProcessing complete: {successful}/{len(results)} files processed successfully")
        
        # Print failed files
        failed_files = [f for f, success in results.items() if not success]
        if failed_files:
            print("\nFailed files:")
            for f in failed_files:
                print(f"  - {f}")


if __name__ == '__main__':
    main()