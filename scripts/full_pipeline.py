#!/usr/bin/env python3
"""
Complete FASTQ-to-PDF Pipeline for Equine Microbiome Reporter
Handles the entire workflow from raw FASTQ files to final PDF reports

Workflow:
1. Combine multiple FASTQ files per barcode
2. Run Kraken2 classification
3. Convert Kraken2 reports to CSV
4. Apply clinical filtering
5. Generate PDF reports

Usage:
    python scripts/full_pipeline.py --input-dir data/ --output-dir pipeline_output/
"""

import os
import sys
import subprocess
import pandas as pd
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src and scripts to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))
sys.path.append(str(Path(__file__).parent.parent))

from src.data_models import PatientInfo
from src.clinical_filter import ClinicalFilter
from src.csv_processor import CSVProcessor
from scripts.generate_clean_report import generate_clean_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullPipeline:
    """Complete pipeline from FASTQ to PDF reports."""
    
    def __init__(self, input_dir: Path, output_dir: Path, kraken2_db: Path = None, barcodes: List[str] = None):
        """
        Initialize the pipeline.

        Args:
            input_dir: Directory containing barcode folders with FASTQ files
            output_dir: Output directory for all results
            kraken2_db: Path to Kraken2 database (default: ~/kraken2_db/k2_pluspfp_16gb)
            barcodes: Optional list of specific barcodes to process
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.barcodes = barcodes  # Store the optional barcode filter

        # Set Kraken2 database - check env variable first
        if kraken2_db is None:
            # Try to get from environment variable
            env_db_path = os.getenv('KRAKEN2_DB_PATH')
            if env_db_path:
                self.kraken2_db = Path(env_db_path)
                logger.info(f"Using Kraken2 database from environment: {self.kraken2_db}")
            else:
                # Fall back to default
                self.kraken2_db = Path.home() / "kraken2_db" / "k2_pluspfp_16gb"
                logger.info(f"Using default Kraken2 database: {self.kraken2_db}")
        else:
            self.kraken2_db = Path(kraken2_db)
            
        # Create subdirectories
        self.combined_dir = self.output_dir / "combined_fastq"
        self.kraken_dir = self.output_dir / "kraken_output"
        self.csv_dir = self.output_dir / "csv_files"
        self.excel_dir = self.output_dir / "excel_review"
        self.pdf_dir = self.output_dir / "pdf_reports"
        
        for dir_ in [self.combined_dir, self.kraken_dir, self.csv_dir, 
                     self.excel_dir, self.pdf_dir]:
            dir_.mkdir(parents=True, exist_ok=True)
            
        # Initialize components
        self.clinical_filter = ClinicalFilter()
        
        # Track metrics
        self.metrics = {
            'start_time': datetime.now(),
            'samples_processed': 0,
            'times': {}
        }
        
    def find_barcode_dirs(self) -> List[Path]:
        """Find all barcode directories in input directory."""
        barcode_dirs = []
        for item in self.input_dir.iterdir():
            if item.is_dir() and item.name.startswith('barcode'):
                # If specific barcodes are requested, filter by them
                if self.barcodes:
                    if item.name in self.barcodes:
                        barcode_dirs.append(item)
                else:
                    barcode_dirs.append(item)
        return sorted(barcode_dirs)
    
    def combine_fastq_files(self, barcode_dir: Path) -> Path:
        """
        Combine multiple FASTQ files from a barcode directory.
        
        Args:
            barcode_dir: Directory containing FASTQ.gz files
            
        Returns:
            Path to combined FASTQ file
        """
        barcode_name = barcode_dir.name
        logger.info(f"Combining FASTQ files for {barcode_name}")
        
        # Find all FASTQ files
        fastq_files = list(barcode_dir.glob("*.fastq.gz"))
        if not fastq_files:
            raise FileNotFoundError(f"No FASTQ files found in {barcode_dir}")
            
        # Output file
        combined_file = self.combined_dir / f"{barcode_name}_combined.fastq"
        
        # Combine using zcat
        cmd = f"zcat {barcode_dir}/*.fastq.gz > {combined_file}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to combine FASTQ files: {result.stderr}")
            
        # Count reads
        with open(combined_file, 'r') as f:
            lines = sum(1 for _ in f)
            reads = lines // 4
            
        logger.info(f"  Combined {len(fastq_files)} files → {reads:,} reads")
        return combined_file
    
    def run_kraken2(self, fastq_file: Path, sample_name: str) -> Tuple[Path, Path]:
        """
        Run Kraken2 classification on FASTQ file.
        
        Args:
            fastq_file: Combined FASTQ file
            sample_name: Sample identifier
            
        Returns:
            Tuple of (kraken_output, kraken_report) paths
        """
        logger.info(f"Running Kraken2 on {sample_name}")
        
        # Check if database exists
        if not self.kraken2_db.exists():
            raise FileNotFoundError(f"Kraken2 database not found at {self.kraken2_db}")
            
        # Output files
        kraken_output = self.kraken_dir / f"{sample_name}.kraken"
        kraken_report = self.kraken_dir / f"{sample_name}.kreport"
        
        # Build Kraken2 command
        # Use memory-mapping for large databases when RAM is limited
        cmd = [
            "kraken2",
            "--db", str(self.kraken2_db),
            "--threads", "4",
            "--memory-mapping",  # Use disk instead of loading entire DB to RAM
            "--output", str(kraken_output),
            "--report", str(kraken_report),
            "--use-names",
            "--report-zero-counts",
            str(fastq_file)
        ]
        
        # Run Kraken2
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"Kraken2 error: {result.stderr}")
            raise RuntimeError(f"Kraken2 failed: {result.stderr}")
            
        logger.info(f"  Classification complete in {elapsed:.1f} seconds")
        return kraken_output, kraken_report
    
    def kreport_to_csv(self, kreport_file: Path, sample_name: str) -> Path:
        """
        Convert Kraken2 report to CSV format for report generator.
        
        Args:
            kreport_file: Kraken2 report file
            sample_name: Sample identifier
            
        Returns:
            Path to CSV file
        """
        logger.info(f"Converting Kraken2 report to CSV for {sample_name}")
        
        # Read Kraken2 report
        kreport_df = pd.read_csv(
            kreport_file,
            sep='\t',
            header=None,
            names=['percentage', 'reads_clade', 'reads_taxon', 'rank', 'taxid', 'name']
        )
        
        # Filter for species level (S) and significant abundance
        species_df = kreport_df[
            (kreport_df['rank'] == 'S') & 
            (kreport_df['percentage'] > 0.01)
        ].copy()
        
        # Clean species names
        species_df['name'] = species_df['name'].str.strip()
        
        # Get phylum information by parsing the taxonomy tree
        # For now, use a simplified approach - would need full taxonomy lookup
        phylum_map = {
            'Escherichia': 'Pseudomonadota',
            'Salmonella': 'Pseudomonadota',
            'Lactobacillus': 'Bacillota',
            'Bacillus': 'Bacillota',
            'Clostridium': 'Bacillota',
            'Bacteroides': 'Bacteroidota',
            'Prevotella': 'Bacteroidota',
            'Streptomyces': 'Actinomycetota',
            'Bifidobacterium': 'Actinomycetota',
            'Fibrobacter': 'Fibrobacterota'
        }
        
        # Extract genus from species name
        species_df['genus'] = species_df['name'].str.split().str[0]
        
        # Map to phylum
        species_df['phylum'] = species_df['genus'].map(phylum_map).fillna('Unknown')
        
        # Create output format matching expected CSV structure
        output_df = pd.DataFrame({
            'species': species_df['name'],
            f'barcode_{sample_name}': species_df['reads_taxon'],  # Use read counts
            'phylum': species_df['phylum'],
            'genus': species_df['genus']
        })
        
        # Save CSV
        csv_file = self.csv_dir / f"{sample_name}.csv"
        output_df.to_csv(csv_file, index=False)
        
        logger.info(f"  Converted {len(output_df)} species to CSV")
        return csv_file
    
    def apply_clinical_filter(self, csv_file: Path, sample_name: str) -> Tuple[Path, Path]:
        """
        Apply clinical filtering to CSV data.
        
        Args:
            csv_file: CSV file with species data
            sample_name: Sample identifier
            
        Returns:
            Tuple of (filtered_csv, excel_review) paths
        """
        logger.info(f"Applying clinical filtering for {sample_name}")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Apply filtering for PlusPFP-16 database
        filtered_df = self.clinical_filter.filter_by_kingdom(df, "PlusPFP-16")
        
        # Save filtered CSV
        filtered_csv = self.csv_dir / f"{sample_name}_filtered.csv"
        filtered_df.to_csv(filtered_csv, index=False)
        
        # Generate enhanced Excel review file with clinical assessment
        excel_file = self.excel_dir / f"{sample_name}_review.xlsx"
        
        # Import and use the enhanced generator
        from generate_clinical_excel import ClinicalExcelGenerator
        excel_generator = ClinicalExcelGenerator()
        excel_generator.generate_review_excel(
            filtered_csv, 
            excel_file,
            sample_name=sample_name
        )
        
        logger.info(f"  Filtered {len(df)} → {len(filtered_df)} species")
        logger.info(f"  Excel review file created: {excel_file.name}")
        return filtered_csv, excel_file
    
    def generate_pdf_report(self, csv_file: Path, sample_name: str) -> Path:
        """
        Generate PDF report from CSV data.
        
        Args:
            csv_file: Filtered CSV file
            sample_name: Sample identifier
            
        Returns:
            Path to PDF report
        """
        logger.info(f"Generating PDF report for {sample_name}")
        
        # Create patient info
        patient = PatientInfo(
            name=f"Sample_{sample_name}",
            sample_number=sample_name,
            age="Unknown",
            performed_by="Automated Pipeline",
            requested_by="Testing"
        )
        
        # Generate report using clean template
        pdf_file = self.pdf_dir / f"{sample_name}_report.pdf"

        try:
            generate_clean_report(
                str(csv_file),
                patient,
                str(pdf_file)
            )
            success = True
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            success = False

        if not success:
            raise RuntimeError(f"Failed to generate PDF for {sample_name}")
            
        logger.info(f"  PDF report generated: {pdf_file.name}")
        return pdf_file
    
    def process_sample(self, barcode_dir: Path) -> Dict:
        """
        Process a single sample through the entire pipeline.
        
        Args:
            barcode_dir: Directory containing FASTQ files
            
        Returns:
            Dictionary with processing results and metrics
        """
        sample_name = barcode_dir.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {sample_name}")
        logger.info(f"{'='*60}")
        
        sample_start = time.time()
        results = {'sample': sample_name}
        
        try:
            # Step 1: Combine FASTQ files
            combined_fastq = self.combine_fastq_files(barcode_dir)
            results['combined_fastq'] = str(combined_fastq)
            
            # Step 2: Run Kraken2
            kraken_output, kraken_report = self.run_kraken2(combined_fastq, sample_name)
            results['kraken_report'] = str(kraken_report)
            
            # Step 3: Convert to CSV
            csv_file = self.kreport_to_csv(kraken_report, sample_name)
            results['csv_file'] = str(csv_file)
            
            # Step 4: Apply clinical filtering
            filtered_csv, excel_review = self.apply_clinical_filter(csv_file, sample_name)
            results['filtered_csv'] = str(filtered_csv)
            results['excel_review'] = str(excel_review)
            
            # Step 5: Generate PDF report
            pdf_report = self.generate_pdf_report(filtered_csv, sample_name)
            results['pdf_report'] = str(pdf_report)
            
            # Calculate metrics
            elapsed = time.time() - sample_start
            results['processing_time'] = elapsed
            results['status'] = 'success'
            
            logger.info(f"✅ {sample_name} complete in {elapsed:.1f} seconds")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {sample_name}: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            
        return results
    
    def run(self) -> Dict:
        """
        Run the complete pipeline on all samples.
        
        Returns:
            Dictionary with overall metrics and results
        """
        logger.info("Starting Full FASTQ-to-PDF Pipeline")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Kraken2 database: {self.kraken2_db}")
        
        # Find all barcode directories
        barcode_dirs = self.find_barcode_dirs()
        logger.info(f"Found {len(barcode_dirs)} samples to process")
        
        # Process each sample
        results = []
        for barcode_dir in barcode_dirs:
            result = self.process_sample(barcode_dir)
            results.append(result)
            self.metrics['samples_processed'] += 1
        
        # Calculate overall metrics
        self.metrics['end_time'] = datetime.now()
        self.metrics['total_time'] = (
            self.metrics['end_time'] - self.metrics['start_time']
        ).total_seconds()
        
        # Save results summary
        summary_file = self.output_dir / "pipeline_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'metrics': {
                    'start_time': self.metrics['start_time'].isoformat(),
                    'end_time': self.metrics['end_time'].isoformat(),
                    'total_time_seconds': self.metrics['total_time'],
                    'samples_processed': self.metrics['samples_processed']
                },
                'results': results
            }, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("Pipeline Complete!")
        logger.info(f"{'='*60}")
        logger.info(f"Samples processed: {self.metrics['samples_processed']}")
        logger.info(f"Total time: {self.metrics['total_time']:.1f} seconds")
        logger.info(f"Average per sample: {self.metrics['total_time']/len(barcode_dirs):.1f} seconds")
        logger.info(f"Results saved to: {self.output_dir}")
        
        successful = sum(1 for r in results if r.get('status') == 'success')
        if successful < len(results):
            logger.warning(f"⚠️ {len(results) - successful} samples failed")
            
        return {
            'metrics': self.metrics,
            'results': results
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Complete FASTQ-to-PDF pipeline for Equine Microbiome Reporter"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data",
        help="Directory containing barcode folders with FASTQ files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="pipeline_output",
        help="Output directory for all results"
    )
    parser.add_argument(
        "--kraken2-db",
        type=str,
        default=None,
        help="Path to Kraken2 database (default: ~/kraken2_db/k2_pluspfp_16gb)"
    )
    parser.add_argument(
        "--skip-kraken2",
        action="store_true",
        help="Skip Kraken2 if .kreport files already exist"
    )
    parser.add_argument(
        "--barcodes",
        type=str,
        default=None,
        help="Comma-separated list of specific barcodes to process (e.g., barcode04,barcode05,barcode06)"
    )

    args = parser.parse_args()
    
    # Parse barcodes if provided
    barcodes = None
    if args.barcodes:
        barcodes = [b.strip() for b in args.barcodes.split(',')]
        logger.info(f"Processing specific barcodes: {barcodes}")

    # Create pipeline
    pipeline = FullPipeline(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        kraken2_db=Path(args.kraken2_db) if args.kraken2_db else None,
        barcodes=barcodes
    )
    
    # Run pipeline
    try:
        results = pipeline.run()
        sys.exit(0 if results['metrics']['samples_processed'] > 0 else 1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()