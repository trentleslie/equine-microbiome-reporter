#!/usr/bin/env python3
"""
NCBI Batch Pipeline - Download and Process FASTQ files from NCBI SRA

Complete workflow:
1. Download FASTQ files from NCBI SRA using accession numbers
2. Process each file through the Kraken2 pipeline
3. Generate individual PDF reports for each sample

Usage:
    # Using config file
    python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml

    # Using command line
    python scripts/ncbi_batch_pipeline.py --accessions SRR12345 SRR67890 SRR11111

    # With custom output directory
    python scripts/ncbi_batch_pipeline.py --config config/ncbi_samples.yaml --output-dir results/
"""

import os
import sys
import argparse
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ncbi_downloader import NCBIDownloader
from src.data_models import PatientInfo
from src.clinical_filter import ClinicalFilter
from src.csv_processor import CSVProcessor
from scripts.generate_clean_report import generate_clean_report

# Try to import full_pipeline if available
try:
    from scripts.full_pipeline import FullPipeline
    FULL_PIPELINE_AVAILABLE = True
except ImportError:
    FULL_PIPELINE_AVAILABLE = False
    logging.warning("FullPipeline not available, will use simplified workflow")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NCBIBatchPipeline:
    """
    Complete pipeline for downloading NCBI FASTQ files and generating reports.

    Workflow:
    1. Download FASTQ files from NCBI using accession numbers
    2. Optional: Run Kraken2 classification (if configured)
    3. Process CSV data
    4. Generate individual PDF reports
    """

    def __init__(
        self,
        output_dir: Path = Path("ncbi_output"),
        kraken2_db: Optional[Path] = None,
        skip_kraken: bool = False
    ):
        """
        Initialize NCBI batch pipeline.

        Args:
            output_dir: Base output directory for all results
            kraken2_db: Path to Kraken2 database (optional)
            skip_kraken: Skip Kraken2 classification (for CSV-only processing)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.download_dir = self.output_dir / "downloads"
        self.pdf_dir = self.output_dir / "pdf_reports"
        self.csv_dir = self.output_dir / "csv_files"
        self.metadata_dir = self.output_dir / "metadata"

        for dir_ in [self.download_dir, self.pdf_dir, self.csv_dir, self.metadata_dir]:
            dir_.mkdir(parents=True, exist_ok=True)

        # Initialize downloader
        self.downloader = NCBIDownloader(output_dir=self.download_dir)

        # Check Kraken2 setup
        self.skip_kraken = skip_kraken
        self.kraken2_db = kraken2_db or Path(os.getenv('KRAKEN2_DB_PATH', ''))

        if not self.skip_kraken and not self.kraken2_db.exists():
            logger.warning(f"Kraken2 database not found: {self.kraken2_db}")
            logger.warning("Will skip Kraken2 classification step")
            self.skip_kraken = True

        # Initialize components
        self.clinical_filter = ClinicalFilter()

        # Track results
        self.results = {
            'start_time': datetime.now().isoformat(),
            'samples': {}
        }

    def process_sample_fastq(
        self,
        fastq_path: Path,
        patient_info: PatientInfo,
        accession: str
    ) -> bool:
        """
        Process a single FASTQ file through Kraken2 -> CSV -> PDF.

        Args:
            fastq_path: Path to FASTQ file
            patient_info: Patient information
            accession: SRA accession number

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing {accession}...")

        try:
            # If Kraken2 is available, use full pipeline
            if not self.skip_kraken and FULL_PIPELINE_AVAILABLE:
                logger.info("Using Kraken2 classification pipeline")
                # This would call the full Kraken2 workflow
                # For now, we'll use the simplified CSV workflow
                logger.warning("Kraken2 integration not yet implemented in this script")
                logger.warning("Please use scripts/full_pipeline.py for Kraken2 processing")
                return False

            # Simplified workflow: assume CSV already exists or generate from metadata
            logger.info("Using simplified CSV-based workflow")
            logger.warning("This script currently requires pre-processed CSV files")
            logger.warning("For FASTQ -> Kraken2 -> PDF, use: scripts/full_pipeline.py")

            return False

        except Exception as e:
            logger.error(f"Failed to process {accession}: {e}")
            return False

    def process_sample_csv(
        self,
        csv_path: Path,
        patient_info: PatientInfo,
        accession: str
    ) -> bool:
        """
        Process a pre-existing CSV file to generate PDF report.

        Args:
            csv_path: Path to CSV file
            patient_info: Patient information
            accession: Sample identifier

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing CSV for {accession}...")

        try:
            # Generate output path
            output_pdf = self.pdf_dir / f"{accession}_report.pdf"

            # Generate report using existing clean report generator
            success = generate_clean_report(
                csv_path=csv_path,
                patient_info=patient_info,
                output_path=output_pdf
            )

            if success:
                logger.info(f"✅ Generated report: {output_pdf}")
                return True
            else:
                logger.error(f"❌ Failed to generate report for {accession}")
                return False

        except Exception as e:
            logger.error(f"Failed to process CSV {accession}: {e}")
            return False

    def run_batch_download(
        self,
        accessions: List[str],
        sample_info: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Path]:
        """
        Download multiple SRA accessions.

        Args:
            accessions: List of SRA accession numbers
            sample_info: Optional dict mapping accession -> sample metadata

        Returns:
            Dictionary mapping accession -> download path
        """
        logger.info("=" * 70)
        logger.info(f"NCBI BATCH DOWNLOAD - {len(accessions)} samples")
        logger.info("=" * 70)

        # Generate barcodes
        barcodes = [f"barcode{i+1:02d}" for i in range(len(accessions))]

        # Download all accessions
        download_results = self.downloader.download_batch(accessions, barcodes)

        logger.info(f"Downloaded {len(download_results)}/{len(accessions)} samples")

        # Save download summary
        summary = {
            'total_requested': len(accessions),
            'successful_downloads': len(download_results),
            'accessions': accessions,
            'download_paths': {acc: str(path) for acc, path in download_results.items()},
            'timestamp': datetime.now().isoformat()
        }

        summary_file = self.metadata_dir / "download_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Download summary saved: {summary_file}")

        return download_results

    def run_batch_processing(
        self,
        sample_configs: List[Dict]
    ) -> Dict[str, bool]:
        """
        Process multiple samples (download + generate reports).

        Args:
            sample_configs: List of dicts with keys: accession, patient_name, age, etc.

        Returns:
            Dictionary mapping accession -> success status
        """
        logger.info("=" * 70)
        logger.info(f"NCBI BATCH PROCESSING - {len(sample_configs)} samples")
        logger.info("=" * 70)

        results = {}

        # Step 1: Download all samples
        accessions = [config['accession'] for config in sample_configs]
        download_results = self.run_batch_download(accessions)

        # Step 2: Process each downloaded sample
        for config in sample_configs:
            accession = config['accession']

            # Create patient info
            patient_info = PatientInfo(
                name=config.get('name', accession),
                age=config.get('age', 'Unknown'),
                sample_number=config.get('sample_number', accession),
                performed_by=config.get('performed_by', 'Laboratory Staff'),
                requested_by=config.get('requested_by', 'Researcher')
            )

            # Check if download succeeded
            if accession not in download_results:
                logger.error(f"❌ {accession}: Download failed, skipping processing")
                results[accession] = False
                continue

            fastq_path = download_results[accession]

            # Check if CSV already exists (for testing)
            csv_path = self.csv_dir / f"{accession}.csv"

            if csv_path.exists():
                # Process existing CSV
                logger.info(f"Found existing CSV for {accession}")
                success = self.process_sample_csv(csv_path, patient_info, accession)
            else:
                # Process FASTQ
                logger.info(f"Processing FASTQ for {accession}")
                logger.warning("FASTQ processing requires Kraken2 - see full_pipeline.py")
                logger.warning(f"Manual step: Run Kraken2 on {fastq_path}")
                success = False

            results[accession] = success

            # Update results tracking
            self.results['samples'][accession] = {
                'success': success,
                'patient_name': patient_info.name,
                'download_path': str(fastq_path),
                'pdf_path': str(self.pdf_dir / f"{accession}_report.pdf") if success else None
            }

        # Save final results
        self.results['end_time'] = datetime.now().isoformat()
        self.results['total_samples'] = len(sample_configs)
        self.results['successful_reports'] = sum(1 for v in results.values() if v)

        results_file = self.output_dir / "batch_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info("=" * 70)
        logger.info(f"BATCH PROCESSING COMPLETE")
        logger.info(f"Success: {self.results['successful_reports']}/{len(sample_configs)}")
        logger.info(f"Results saved: {results_file}")
        logger.info("=" * 70)

        return results


def load_config(config_path: Path) -> List[Dict]:
    """Load sample configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('samples', [])


def main():
    parser = argparse.ArgumentParser(
        description="Download FASTQ files from NCBI and generate microbiome reports"
    )

    parser.add_argument(
        '--config',
        type=Path,
        help='YAML configuration file with sample information'
    )

    parser.add_argument(
        '--accessions',
        nargs='+',
        help='SRA accession numbers (space-separated)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('ncbi_output'),
        help='Output directory for all results'
    )

    parser.add_argument(
        '--kraken2-db',
        type=Path,
        help='Path to Kraken2 database'
    )

    parser.add_argument(
        '--skip-kraken',
        action='store_true',
        help='Skip Kraken2 classification (for CSV-only processing)'
    )

    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only download files, skip processing'
    )

    args = parser.parse_args()

    # Load sample configurations
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        sample_configs = load_config(args.config)
    elif args.accessions:
        logger.info(f"Using {len(args.accessions)} accessions from command line")
        sample_configs = [
            {
                'accession': acc,
                'name': f"Sample_{acc}",
                'sample_number': acc
            }
            for acc in args.accessions
        ]
    else:
        logger.error("Must provide either --config or --accessions")
        sys.exit(1)

    # Initialize pipeline
    pipeline = NCBIBatchPipeline(
        output_dir=args.output_dir,
        kraken2_db=args.kraken2_db,
        skip_kraken=args.skip_kraken
    )

    # Run pipeline
    if args.download_only:
        # Download only
        accessions = [config['accession'] for config in sample_configs]
        results = pipeline.run_batch_download(accessions)
        logger.info(f"Downloaded {len(results)} samples")
    else:
        # Full processing
        results = pipeline.run_batch_processing(sample_configs)

        # Print summary
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"\n{'='*70}")
        logger.info(f"FINAL SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total samples: {len(results)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {len(results) - success_count}")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    main()
