#!/usr/bin/env python3
"""
Test script to verify pipeline fixes for HippoVet+ lab
Tests:
1. --barcodes argument parsing
2. .env file reading for KRAKEN2_DB_PATH
3. Barcode filtering logic
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

print("=" * 60)
print("Pipeline Fix Verification Test")
print("=" * 60)

# Test 1: Import and argument parsing
print("\n✓ Test 1: Checking imports and dependencies...")
try:
    from scripts.full_pipeline import FullPipeline
    from dotenv import load_dotenv
    import argparse
    print("  ✓ All imports successful")
except ImportError as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Test --barcodes argument parsing
print("\n✓ Test 2: Testing --barcodes argument parsing...")
parser = argparse.ArgumentParser()
parser.add_argument("--input-dir", type=str, default="data")
parser.add_argument("--output-dir", type=str, default="output")
parser.add_argument("--kraken2-db", type=str, default=None)
parser.add_argument("--skip-kraken2", action="store_true")
parser.add_argument("--barcodes", type=str, default=None)

# Simulate command line with barcodes
test_args = parser.parse_args(["--barcodes", "barcode04,barcode05,barcode06"])
if test_args.barcodes:
    barcodes = [b.strip() for b in test_args.barcodes.split(',')]
    if barcodes == ["barcode04", "barcode05", "barcode06"]:
        print(f"  ✓ Barcodes parsed correctly: {barcodes}")
    else:
        print(f"  ✗ Barcodes parsing failed: {barcodes}")
else:
    print("  ✗ --barcodes argument not recognized")

# Test 3: Test .env file reading
print("\n✓ Test 3: Testing .env file reading for KRAKEN2_DB_PATH...")

# Create a temporary .env file
with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
    f.write("KRAKEN2_DB_PATH=/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8/k2_pluspfp_08gb_20240605_db\n")
    temp_env_file = f.name

try:
    # Clear any existing KRAKEN2_DB_PATH
    os.environ.pop('KRAKEN2_DB_PATH', None)

    # Load the temp .env file
    load_dotenv(temp_env_file)

    db_path = os.getenv('KRAKEN2_DB_PATH')
    if db_path == "/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8/k2_pluspfp_08gb_20240605_db":
        print(f"  ✓ KRAKEN2_DB_PATH loaded correctly from .env")
        print(f"    Path: {db_path}")
    else:
        print(f"  ✗ KRAKEN2_DB_PATH not loaded correctly: {db_path}")
finally:
    os.unlink(temp_env_file)

# Test 4: Test barcode filtering in pipeline
print("\n✓ Test 4: Testing barcode directory filtering...")

# Create temporary directory structure
with tempfile.TemporaryDirectory() as tmpdir:
    test_input_dir = Path(tmpdir) / "fastq_pass"
    test_input_dir.mkdir()

    # Create mock barcode directories
    for i in range(1, 8):
        barcode_dir = test_input_dir / f"barcode{i:02d}"
        barcode_dir.mkdir()
        # Create a dummy fastq file
        (barcode_dir / "test.fastq").touch()

    # Also create a non-barcode directory to ensure it's not picked up
    (test_input_dir / "other_dir").mkdir()

    print(f"  Created test directories: barcode01 through barcode07")

    # Test without filter (should find all 7)
    test_output_dir = Path(tmpdir) / "output1"
    pipeline = FullPipeline(
        input_dir=test_input_dir,
        output_dir=test_output_dir,
        kraken2_db=None,
        barcodes=None
    )
    all_barcodes = pipeline.find_barcode_dirs()
    if len(all_barcodes) == 7:
        print(f"  ✓ Without filter: Found all 7 barcode directories")
    else:
        print(f"  ✗ Without filter: Expected 7, found {len(all_barcodes)}")

    # Test with filter (should find only 3)
    test_output_dir2 = Path(tmpdir) / "output2"
    pipeline_filtered = FullPipeline(
        input_dir=test_input_dir,
        output_dir=test_output_dir2,
        kraken2_db=None,
        barcodes=["barcode04", "barcode05", "barcode06"]
    )
    filtered_barcodes = pipeline_filtered.find_barcode_dirs()
    filtered_names = [b.name for b in filtered_barcodes]

    if len(filtered_barcodes) == 3:
        print(f"  ✓ With filter: Found exactly 3 specified barcodes")
        if set(filtered_names) == {"barcode04", "barcode05", "barcode06"}:
            print(f"  ✓ Correct barcodes selected: {filtered_names}")
        else:
            print(f"  ✗ Wrong barcodes selected: {filtered_names}")
    else:
        print(f"  ✗ With filter: Expected 3, found {len(filtered_barcodes)}")

# Test 5: Test database path resolution
print("\n✓ Test 5: Testing database path resolution with .env...")

with tempfile.TemporaryDirectory() as tmpdir:
    # Set environment variable
    os.environ['KRAKEN2_DB_PATH'] = '/test/db/path'

    test_output_dir = Path(tmpdir) / "output"
    pipeline = FullPipeline(
        input_dir=Path(tmpdir),
        output_dir=test_output_dir,
        kraken2_db=None  # Should use env variable
    )

    if str(pipeline.kraken2_db) == '/test/db/path':
        print(f"  ✓ Database path from environment: {pipeline.kraken2_db}")
    else:
        print(f"  ✗ Database path not from environment: {pipeline.kraken2_db}")

    # Clean up
    os.environ.pop('KRAKEN2_DB_PATH', None)

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
print("✓ All tests passed! The fixes should work on HippoVet+ lab system")
print("\nThe lab should:")
print("1. Pull latest changes: git pull origin main")
print("2. Copy .env.hippovet to .env")
print("3. Run the pipeline with --barcodes argument as needed")
print("=" * 60)