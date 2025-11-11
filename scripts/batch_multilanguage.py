#!/usr/bin/env python3
"""
Multi-Language Batch Report Generation

Generate microbiome reports in multiple languages for batch processing.
Convenience wrapper around BatchProcessor with multi-language support.

Usage:
    # Generate English, Polish, and Japanese for all CSVs
    python scripts/batch_multilanguage.py --data-dir data/ --languages en pl ja

    # Process from manifest
    python scripts/batch_multilanguage.py --manifest manifest.csv --languages en pl ja

    # With custom output directory
    python scripts/batch_multilanguage.py --data-dir data/ --output-dir reports/multi/ --languages en pl

    # Single language (backwards compatible)
    python scripts/batch_multilanguage.py --data-dir data/ --languages en
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.batch_processor import BatchProcessor, BatchConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for multi-language batch processing."""
    parser = argparse.ArgumentParser(
        description="Generate microbiome reports in multiple languages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate English, Polish, and Japanese reports
  python scripts/batch_multilanguage.py --data-dir data/ --languages en pl ja

  # Process specific CSV files
  python scripts/batch_multilanguage.py --data-dir data/ --languages en pl

  # Use manifest file
  python scripts/batch_multilanguage.py --manifest manifest.csv --languages en pl ja
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--data-dir",
        type=str,
        help="Directory containing CSV files to process"
    )
    input_group.add_argument(
        "--manifest",
        type=str,
        help="Manifest CSV file with patient information and file list"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/multilingual",
        help="Output directory for generated reports (default: reports/multilingual)"
    )

    # Language options
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en"],
        choices=["en", "pl", "ja", "de", "es", "fr", "it", "pt", "ru", "zh", "ko"],
        help="Language codes for report generation (default: en)"
    )

    # Processing options
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel processing (default: True)"
    )
    parser.add_argument(
        "--no-parallel",
        action="store_false",
        dest="parallel",
        help="Disable parallel processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )

    # Validation options
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip CSV validation before processing"
    )
    parser.add_argument(
        "--min-species",
        type=int,
        default=10,
        help="Minimum species count for validation (default: 10)"
    )

    args = parser.parse_args()

    # Print configuration
    logger.info("="*70)
    logger.info("Multi-Language Batch Report Generation")
    logger.info("="*70)
    logger.info(f"Languages: {', '.join(args.languages)}")
    logger.info(f"Reports per sample: {len(args.languages)}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Parallel processing: {args.parallel}")
    if args.parallel:
        logger.info(f"Workers: {args.workers}")
    logger.info("="*70)

    # Configure batch processor
    config = BatchConfig(
        data_dir=args.data_dir if args.data_dir else Path(args.manifest).parent,
        reports_dir=args.output_dir,
        languages=args.languages,  # Multi-language support
        parallel_processing=args.parallel,
        max_workers=args.workers,
        min_species_count=args.min_species
    )

    # Ensure output directory exists
    config.ensure_directories()

    # Create processor
    processor = BatchProcessor(config)

    # Process files
    start_time = datetime.now()

    try:
        if args.manifest:
            logger.info(f"Processing from manifest: {args.manifest}")
            results = processor.process_from_manifest(
                Path(args.manifest),
                progress_callback=progress_callback
            )
        else:
            logger.info(f"Processing directory: {args.data_dir}")
            results = processor.process_directory(
                progress_callback=progress_callback,
                validate=not args.no_validate
            )

        # Generate summary
        summary = processor.generate_summary_report()

        # Print results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total samples processed: {summary['total_files']}")
        logger.info(f"Successful samples: {summary['successful_samples']}")
        logger.info(f"Failed samples: {summary['failed_samples']}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        logger.info(f"\nTotal PDFs generated: {summary['total_pdfs_generated']}")

        # Show per-language breakdown
        logger.info("\nPDFs per language:")
        for lang, count in summary['pdfs_per_language'].items():
            logger.info(f"  {lang.upper()}: {count} PDFs")

        logger.info(f"\nTotal processing time: {duration:.1f} seconds")
        logger.info(f"Average per sample: {summary['average_processing_time_per_sample']:.1f} seconds")
        logger.info(f"\nReports saved to: {args.output_dir}")

        # Save summary to file
        summary_file = Path(args.output_dir) / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"Summary saved to: {summary_file}")

        # Check for failures
        if summary['failed_samples'] > 0:
            logger.warning(f"\n⚠️ {summary['failed_samples']} samples failed")
            if 'failure_reasons' in summary:
                logger.warning("Failure reasons:")
                for reason, count in summary['failure_reasons'].items():
                    logger.warning(f"  {reason}: {count}")
            sys.exit(1)

        logger.info("\n✅ All samples processed successfully!")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def progress_callback(current: int, total: int):
    """Progress callback for displaying processing status."""
    percent = (current / total) * 100
    logger.info(f"Progress: {current}/{total} ({percent:.1f}%)")


if __name__ == "__main__":
    main()
