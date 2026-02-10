#!/usr/bin/env python3
"""
Quick report generation CLI for Gosia and lab staff.

Usage:
    python scripts/quick_report.py data/sample_1.csv --name Montana --sample-number 506
    python scripts/quick_report.py data/sample_1.csv --name Montana -l pl
    python scripts/quick_report.py data/sample_1.csv --name Montana --reviewed-by "Dr. Nowicka"
    python scripts/quick_report.py --help
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is importable (same pattern as batch_multilanguage.py)
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Generate an equine microbiome PDF report from a CSV file.",
        epilog="""Examples:
  python scripts/quick_report.py data/sample_1.csv --name Montana --sample-number 506
  python scripts/quick_report.py data/sample_1.csv --name Montana --age "8 years" --breed Arabian -l pl
  python scripts/quick_report.py data/sample_1.csv --name Montana --reviewed-by "Dr. Nowicka"
  python scripts/quick_report.py data/sample_1.csv --name Montana --barcode barcode25 -o my_report.pdf""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("csv_path", help="Path to CSV file with microbiome data")
    parser.add_argument("-o", "--output", help="Output PDF path (default: auto-generated)")
    parser.add_argument("--name", default="Unknown", help="Horse name (default: Unknown)")
    parser.add_argument("--breed", default="", help="Breed (e.g., Arabian, Thoroughbred)")
    parser.add_argument("--sex", default="", help="Sex (Mare, Stallion, Gelding)")
    parser.add_argument("--age", default="Unknown", help="Age (default: Unknown)")
    parser.add_argument("--owner", default="", help="Owner or farm name")
    parser.add_argument("--sample-number", default="001", help="Lab sample number (default: 001)")
    parser.add_argument("--collection-date", default="", help="Sample collection date (e.g., 2026-01-15)")
    parser.add_argument("-l", "--language", default="en", choices=["en", "pl", "de"],
                        help="Report language (default: en)")
    parser.add_argument("--barcode", default=None, help="Specific barcode column (default: auto-detect)")
    parser.add_argument("--clinical-assessment", default="", help="Manual clinical interpretation text")
    parser.add_argument("--clinical-recommendations", default="", help="Manual clinical recommendations text")
    parser.add_argument("--reviewed-by", default="", help="Clinician name (auto-sets review date to today)")

    args = parser.parse_args()

    # Validate CSV exists
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    # WSL2 compatibility
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Import after env setup to avoid early Qt init
    from scripts.generate_clean_report import generate_clean_report
    from src.data_models import PatientInfo

    # Suppress all library logging so output stays clean for Gosia
    # (must be after imports since generate_clean_report calls basicConfig at load time)
    logging.disable(logging.INFO)

    # Build PatientInfo
    patient = PatientInfo(
        name=args.name,
        breed=args.breed,
        sex=args.sex,
        age=args.age,
        owner_name=args.owner,
        sample_number=args.sample_number,
        collection_date=args.collection_date,
        clinical_assessment=args.clinical_assessment,
        clinical_recommendations=args.clinical_recommendations,
        reviewed_by=args.reviewed_by,
        review_date=datetime.now().strftime("%Y-%m-%d") if args.reviewed_by else "",
    )

    # Auto-generate output filename if not specified
    if args.output:
        output_path = args.output
    else:
        stem = args.name if args.name != "Unknown" else csv_path.stem
        # Sanitize filename
        stem = stem.replace(" ", "_")
        barcode_suffix = f"_{args.barcode}" if args.barcode else ""
        output_path = f"{stem}{barcode_suffix}_report_{args.language}.pdf"

    print(f"Generating report for {args.name}...")
    print(f"  CSV:      {csv_path}")
    print(f"  Language: {args.language}")
    if args.collection_date:
        print(f"  Collected: {args.collection_date}")
    if args.barcode:
        print(f"  Barcode:  {args.barcode}")
    if args.reviewed_by:
        print(f"  Reviewed: {args.reviewed_by} ({patient.review_date})")
    print(f"  Output:   {output_path}")
    print()

    success = generate_clean_report(
        csv_path=str(csv_path),
        patient_info=patient,
        output_path=output_path,
        language=args.language,
        barcode_column=args.barcode,
    )

    if success:
        print(f"Done! Report saved to: {output_path}")
    else:
        print("Error: Report generation failed. Check the CSV file and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
