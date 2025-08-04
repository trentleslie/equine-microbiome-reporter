#!/usr/bin/env python3
"""
Test the real FASTQ processing pipeline with directory-based input
"""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.real_fastq_processor import process_fastq_directories_to_csv
import logging

def test_real_fastq_processing():
    """Test real FASTQ processing with a subset of files"""
    logging.basicConfig(level=logging.INFO)
    
    data_dir = "data"
    barcode_dirs = ["barcode04", "barcode05", "barcode06"]
    output_csv = "test_real_abundance.csv"
    
    print("🧬 Testing Real FASTQ Processing Pipeline")
    print("=" * 50)
    
    # Check if directories exist
    data_path = Path(data_dir)
    for barcode_dir in barcode_dirs:
        barcode_path = data_path / barcode_dir
        if barcode_path.exists():
            fastq_count = len(list(barcode_path.glob('*.fastq.gz')))
            print(f"✅ {barcode_dir}: {fastq_count} FASTQ files")
        else:
            print(f"❌ {barcode_dir}: Directory missing")
            return False
    
    print("\n🔄 Starting FASTQ processing...")
    
    try:
        # Process FASTQ files
        success = process_fastq_directories_to_csv(data_dir, barcode_dirs, output_csv)
        
        if success and Path(output_csv).exists():
            # Examine results
            import pandas as pd
            df = pd.read_csv(output_csv)
            
            print(f"\n✅ SUCCESS!")
            print(f"📋 Generated CSV: {output_csv}")
            print(f"📊 Species found: {len(df)}")
            print(f"🏷️  Barcode columns: {len([col for col in df.columns if col.startswith('barcode')])}")
            print(f"📈 Total classified reads: {df['total'].sum()}")
            
            print(f"\n🔍 Sample data:")
            display_cols = ['species', 'total', 'phylum', 'barcode04', 'barcode05', 'barcode06']
            available_cols = [col for col in display_cols if col in df.columns]
            print(df[available_cols].head(10))
            
            return True
        else:
            print("❌ Processing failed or no output generated")
            return False
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_fastq_processing()
    if success:
        print("\n🎉 Real FASTQ processing test completed successfully!")
    else:
        print("\n💥 Real FASTQ processing test failed!")
        sys.exit(1)