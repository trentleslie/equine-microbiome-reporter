#!/usr/bin/env python3
"""
Manifest Template Generator for Equine Microbiome Reporter

Auto-detects barcodes from EPI2ME CSV files and generates a pre-populated
manifest template for lab staff to fill in patient info and clinical notes.

Usage:
    python scripts/generate_manifest_template.py --csv data/23_24_25.csv --output manifest.csv
    python scripts/generate_manifest_template.py --csv data/23_24_25.csv  # outputs to {csv_stem}_manifest.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from datetime import datetime


# Manifest columns with default values
MANIFEST_COLUMNS = [
    'barcode',              # Auto-populated from CSV
    'horse_name',           # Patient name
    'owner_name',           # Owner/farm name
    'collection_date',      # Sample collection date
    'breed',                # Horse breed
    'sex',                  # Mare/Stallion/Gelding
    'age',                  # Horse age
    'clinical_assessment',   # Manual clinical interpretation
    'clinical_recommendations',  # Manual recommendations
    'reviewed_by',          # Clinician name
    'review_date',          # Date of clinical review
]

# Barcode column pattern
BARCODE_PATTERN = re.compile(r'^barcode\d+$')


def detect_barcodes(csv_path: Path) -> list:
    """Detect all barcode columns in the CSV file."""
    barcodes = []

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader, [])

        for header in headers:
            if BARCODE_PATTERN.match(header):
                barcodes.append(header)

    return sorted(barcodes, key=lambda x: int(re.search(r'\d+', x).group()))


def generate_manifest_template(csv_path: Path, output_path: Path) -> bool:
    """Generate a manifest template from the input CSV."""

    # Detect barcodes
    barcodes = detect_barcodes(csv_path)

    if not barcodes:
        print(f"Error: No barcode columns found in {csv_path}")
        print("Expected columns matching pattern 'barcode[N]' (e.g., barcode23, barcode24)")
        return False

    print(f"Detected {len(barcodes)} barcodes: {', '.join(barcodes)}")

    # Generate manifest rows
    today = datetime.now().strftime('%Y-%m-%d')
    rows = []

    for barcode in barcodes:
        row = {
            'barcode': barcode,
            'horse_name': '',
            'owner_name': '',
            'collection_date': '',
            'breed': '',
            'sex': '',
            'age': '',
            'clinical_assessment': '',
            'clinical_recommendations': '',
            'reviewed_by': '',
            'review_date': '',
        }
        rows.append(row)

    # Write manifest
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

        # Add instructions as comments (CSV doesn't support comments, but we can add an instruction row)

    print(f"\nManifest template generated: {output_path}")
    print(f"\nInstructions:")
    print(f"  1. Open {output_path} in Excel or a spreadsheet editor")
    print(f"  2. Fill in patient info for each barcode")
    print(f"  3. Add clinical_assessment and clinical_recommendations if available")
    print(f"  4. Add reviewed_by and review_date after clinical review")
    print(f"  5. Leave fields empty for placeholder text in reports")
    print(f"\nField descriptions:")
    print(f"  - barcode: Auto-populated, do not modify")
    print(f"  - horse_name: Patient/horse name")
    print(f"  - owner_name: Owner or farm name")
    print(f"  - collection_date: Sample collection date (YYYY-MM-DD)")
    print(f"  - breed: Horse breed (e.g., Arabian, Thoroughbred)")
    print(f"  - sex: Mare, Stallion, or Gelding")
    print(f"  - age: Horse age (e.g., '8 years')")
    print(f"  - clinical_assessment: Manual clinical interpretation (or leave empty)")
    print(f"  - clinical_recommendations: Manual recommendations (or leave empty)")
    print(f"  - reviewed_by: Clinician name who reviewed the report")
    print(f"  - review_date: Date of clinical review (YYYY-MM-DD)")

    return True


def load_manifest(manifest_path: Path) -> dict:
    """
    Load a manifest CSV and return a dictionary mapping barcode -> PatientInfo fields.

    Returns:
        dict: {barcode: {horse_name, owner_name, collection_date, ...}, ...}
    """
    manifest = {}

    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            barcode = row.get('barcode', '').strip()
            if barcode:
                manifest[barcode] = {
                    'horse_name': row.get('horse_name', '').strip(),
                    'owner_name': row.get('owner_name', '').strip(),
                    'collection_date': row.get('collection_date', '').strip(),
                    'breed': row.get('breed', '').strip(),
                    'sex': row.get('sex', '').strip(),
                    'age': row.get('age', '').strip(),
                    'clinical_assessment': row.get('clinical_assessment', '').strip(),
                    'clinical_recommendations': row.get('clinical_recommendations', '').strip(),
                    'reviewed_by': row.get('reviewed_by', '').strip(),
                    'review_date': row.get('review_date', '').strip(),
                }

    return manifest


def validate_manifest_against_csv(manifest_path: Path, csv_path: Path) -> tuple:
    """
    Validate manifest barcodes against CSV barcodes.

    Returns:
        tuple: (valid_barcodes, skipped_barcodes, error_barcodes)
            - valid_barcodes: In both manifest and CSV
            - skipped_barcodes: In CSV but not in manifest (will be skipped)
            - error_barcodes: In manifest but not in CSV (error condition)
    """
    csv_barcodes = set(detect_barcodes(csv_path))
    manifest_data = load_manifest(manifest_path)
    manifest_barcodes = set(manifest_data.keys())

    valid_barcodes = csv_barcodes & manifest_barcodes
    skipped_barcodes = csv_barcodes - manifest_barcodes
    error_barcodes = manifest_barcodes - csv_barcodes

    return list(valid_barcodes), list(skipped_barcodes), list(error_barcodes)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Generate manifest template from EPI2ME CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate manifest from CSV (output to same directory)
    python scripts/generate_manifest_template.py --csv data/23_24_25.csv

    # Specify output path
    python scripts/generate_manifest_template.py --csv data/23_24_25.csv --output manifest.csv

    # Validate manifest against CSV
    python scripts/generate_manifest_template.py --csv data/23_24_25.csv --manifest manifest.csv --validate
        """
    )

    parser.add_argument('--csv', required=True, help='Input EPI2ME CSV file with barcode columns')
    parser.add_argument('--output', '-o', help='Output manifest CSV path (default: {csv_stem}_manifest.csv)')
    parser.add_argument('--manifest', '-m', help='Existing manifest to validate')
    parser.add_argument('--validate', action='store_true', help='Validate manifest against CSV')

    args = parser.parse_args()

    csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    # Validation mode
    if args.validate and args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"Error: Manifest file not found: {manifest_path}")
            sys.exit(1)

        valid, skipped, errors = validate_manifest_against_csv(manifest_path, csv_path)

        print(f"\nValidation Results:")
        print(f"{'='*50}")

        if valid:
            print(f"\n  Valid barcodes ({len(valid)}):")
            for b in sorted(valid):
                print(f"    {b}: Found in CSV, will process")

        if skipped:
            print(f"\n  Skipped barcodes ({len(skipped)}):")
            for b in sorted(skipped):
                print(f"    {b}: In CSV but not in manifest, skipping")

        if errors:
            print(f"\n  ERRORS ({len(errors)}):")
            for b in sorted(errors):
                print(f"    {b}: In manifest but NOT in CSV")

        print(f"\n{'='*50}")
        print(f"Summary: {len(valid)} valid, {len(skipped)} skipped, {len(errors)} errors")

        if errors:
            print("\nERROR: Some manifest barcodes not found in CSV. Please fix manifest.")
            sys.exit(1)
        else:
            print("\nValidation passed.")
            sys.exit(0)

    # Generation mode
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = csv_path.parent / f"{csv_path.stem}_manifest.csv"

    success = generate_manifest_template(csv_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
