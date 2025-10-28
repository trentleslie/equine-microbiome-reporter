#!/usr/bin/env python3
"""
Validation script for phylum filtering and non-bacterial organism exclusion
Tests all the changes made based on lab feedback
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.csv_processor import CSVProcessor
from src.data_models import PatientInfo


def validate_filtering(csv_path: str, barcode_column: str):
    """Validate that filtering works correctly"""

    print("=" * 70)
    print("VALIDATION: Phylum Filtering & Non-Bacterial Organism Exclusion")
    print("=" * 70)

    # Process the data
    processor = CSVProcessor(csv_path=csv_path, barcode_column=barcode_column)
    data = processor.process()

    issues = []
    passes = []

    # Test 1: No non-bacterial species
    print("\n[Test 1] Checking for non-bacterial species...")
    non_bacterial = []
    for species in data.species_list:
        phylum = species.get('phylum', '')
        # Check for plant/animal/fungal species (these shouldn't exist if filtering works)
        if phylum in ['Unknown phylum', 'Unknown', '', 'unknown']:
            non_bacterial.append(f"{species['species']} (phylum: '{phylum}')")

    if non_bacterial:
        issues.append(f"Found {len(non_bacterial)} species with unknown/empty phylum:")
        for item in non_bacterial[:5]:  # Show first 5
            issues.append(f"  - {item}")
        if len(non_bacterial) > 5:
            issues.append(f"  ... and {len(non_bacterial) - 5} more")
    else:
        passes.append("✅ All species have valid bacterial phyla")

    # Test 2: Phylum distribution contains only DI-relevant + Other
    print("\n[Test 2] Checking phylum distribution...")
    expected_phyla = {
        'Actinomycetota', 'Bacillota', 'Bacteroidota',
        'Pseudomonadota', 'Fibrobacterota', 'Other bacterial phyla'
    }

    print(f"\nPhylum distribution ({len(data.phylum_distribution)} phyla):")
    for phylum, pct in sorted(data.phylum_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {phylum}: {pct:.2f}%")

    # Check for Unknown in distribution
    has_unknown = any('Unknown' in p or 'unknown' in p for p in data.phylum_distribution.keys())
    if has_unknown:
        issues.append("❌ Found 'Unknown' phylum in distribution")
    else:
        passes.append("✅ No 'Unknown' phylum in distribution")

    # Check that all phyla are either DI-relevant or "Other"
    unexpected_phyla = set(data.phylum_distribution.keys()) - expected_phyla
    if unexpected_phyla:
        issues.append(f"❌ Found unexpected phyla (should be grouped as 'Other'): {unexpected_phyla}")
    else:
        passes.append("✅ All phyla are either DI-relevant or grouped as 'Other'")

    # Test 3: "Other bacterial phyla" category
    print("\n[Test 3] Checking 'Other bacterial phyla' category...")
    has_other = 'Other bacterial phyla' in data.phylum_distribution
    if has_other:
        other_pct = data.phylum_distribution['Other bacterial phyla']
        passes.append(f"✅ 'Other bacterial phyla' category present: {other_pct:.2f}%")
    else:
        print("  ℹ️  No 'Other bacterial phyla' (all species in DI-relevant phyla)")

    # Test 4: Total percentage should be ~100%
    print("\n[Test 4] Checking total percentage...")
    total_pct = sum(data.phylum_distribution.values())
    if 99.0 <= total_pct <= 101.0:
        passes.append(f"✅ Total percentage is {total_pct:.2f}% (expected ~100%)")
    else:
        issues.append(f"⚠️  Total percentage is {total_pct:.2f}% (expected ~100%)")

    # Test 5: Dysbiosis index calculated
    print("\n[Test 5] Checking dysbiosis index calculation...")
    if data.dysbiosis_index >= 0:
        passes.append(f"✅ Dysbiosis index calculated: {data.dysbiosis_index:.1f}")
        passes.append(f"✅ Category: {data.dysbiosis_category}")
    else:
        issues.append("❌ Dysbiosis index not calculated properly")

    # Test 6: Species count
    print("\n[Test 6] Checking species count...")
    species_count = len(data.species_list)
    if species_count > 0:
        passes.append(f"✅ Found {species_count} bacterial species")
    else:
        issues.append("❌ No bacterial species found")

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n✅ Passed tests: {len(passes)}")
    for p in passes:
        print(f"  {p}")

    if issues:
        print(f"\n❌ Failed tests: {len(issues)}")
        for issue in issues:
            print(f"  {issue}")

    print("\n" + "=" * 70)

    return len(issues) == 0


def main():
    """Run validation"""

    print("\n🔬 Phylum Filtering Validation Script\n")

    # Use barcode67 data for validation
    csv_path = "data/25_04_23 bact.csv"
    barcode_column = "barcode67"

    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return 1

    # Run validation
    success = validate_filtering(csv_path, barcode_column)

    if success:
        print("\n✅ All validation tests passed!")
        print("\nNext steps:")
        print("1. Generate a new PDF report with: python scripts/generate_clean_report.py")
        print("2. Verify visually:")
        print("   - No plants/archaea in species table (Page 4)")
        print("   - Phylum charts show only bacterial phyla + 'Other'")
        print("   - No 'Unknown' phylum in charts")
        print("   - Species table is on Page 4, not Page 1")
        return 0
    else:
        print("\n⚠️  Some validation tests failed!")
        print("Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
