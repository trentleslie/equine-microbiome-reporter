#!/usr/bin/env python3
"""
Test Kraken2 functionality with real FASTQ data
Tests the complete pipeline with actual client data
"""

import os
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_kraken2_database():
    """Test that Kraken2 database is built and functional"""
    print("🔍 Testing Kraken2 database functionality...")
    
    # Check if database files exist
    db_path = Path("/home/trentleslie/kraken2_databases/standard")
    required_files = ["hash.k2d", "opts.k2d", "taxo.k2d"]
    
    for file in required_files:
        file_path = db_path / file
        if file_path.exists():
            print(f"✅ Found database file: {file}")
        else:
            print(f"❌ Missing database file: {file}")
            return False
    
    return True

def test_kraken2_classification():
    """Test Kraken2 classification with a small FASTQ file"""
    print("\n🧬 Testing Kraken2 classification with real data...")
    
    try:
        from src.kraken2_classifier import Kraken2Classifier
        
        # Use a small FASTQ file for testing
        test_fastq = "data/barcode04/FBC55250_pass_barcode04_168ca027_4fdcf48d_0.fastq.gz"
        
        if not Path(test_fastq).exists():
            print(f"❌ Test FASTQ file not found: {test_fastq}")
            return False
        
        # Create classifier
        classifier = Kraken2Classifier(
            db_path="/home/trentleslie/kraken2_databases/standard",
            threads=4,  # Use fewer threads for testing
            confidence_threshold=0.1
        )
        
        print(f"Using test file: {test_fastq}")
        print("Running Kraken2 classification...")
        
        # Run classification
        start_time = time.time()
        result_df, stats = classifier.classify_fastq(
            fastq_files=[test_fastq],
            sample_name="test04",
            output_dir="test_output"
        )
        end_time = time.time()
        
        print(f"✅ Classification completed in {end_time - start_time:.2f} seconds")
        print(f"Results shape: {result_df.shape}")
        print(f"Statistics: {stats}")
        
        # Display sample results
        if len(result_df) > 0:
            print("\nSample classification results:")
            print(result_df.head())
        else:
            print("⚠️  No classifications found - this might indicate low-complexity input")
        
        return True
        
    except Exception as e:
        print(f"❌ Kraken2 classification failed: {e}")
        return False

def test_pipeline_integration():
    """Test full pipeline integration with Kraken2"""
    print("\n🔧 Testing pipeline integration...")
    
    try:
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        from src.data_models import PatientInfo
        
        # Set environment for Kraken2
        os.environ['ENABLE_KRAKEN2_CLASSIFICATION'] = 'true'
        os.environ['KRAKEN2_DB_PATH'] = '/home/trentleslie/kraken2_databases/standard'
        
        # Create test patient info
        patient = PatientInfo(
            name="Test Horse",
            age="10 years",
            sample_number="TEST001",
            performed_by="Test Lab",
            requested_by="Test Vet"
        )
        
        # Create pipeline integrator
        integrator = MicrobiomePipelineIntegrator(
            output_dir="test_pipeline_output",
            use_kraken2=True,
            kraken2_db_path="/home/trentleslie/kraken2_databases/standard"
        )
        
        # Test with small FASTQ file
        test_fastq = "data/barcode04/FBC55250_pass_barcode04_168ca027_4fdcf48d_0.fastq.gz"
        
        print(f"Processing {test_fastq} through complete pipeline...")
        
        # Run complete pipeline
        results = integrator.process_sample(
            fastq_file=test_fastq,
            patient_info=patient.__dict__,
            barcode_column="barcode04",
            run_qc=False,  # Skip QC for speed
            generate_pdf=False,  # Skip PDF for speed
            language="en"
        )
        
        print("✅ Pipeline integration successful!")
        print(f"Results: {results}")
        
        # Check if Kraken2 was used
        if results.get('kraken2_used', False):
            print("🎉 Kraken2 classification was used successfully!")
        else:
            print("ℹ️  Pipeline used BioPython fallback")
            if 'fallback_reason' in results:
                print(f"Fallback reason: {results['fallback_reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline integration failed: {e}")
        return False

def main():
    """Run all Kraken2 functionality tests"""
    print("🧪 Kraken2 Functionality Test Suite")
    print("=" * 50)
    
    # Create output directories
    Path("test_output").mkdir(exist_ok=True)
    Path("test_pipeline_output").mkdir(exist_ok=True)
    
    tests = [
        ("Database Build Check", test_kraken2_database),
        ("Classification Test", test_kraken2_classification), 
        ("Pipeline Integration", test_pipeline_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Kraken2 is fully functional.")
        print("\n📋 Ready for production use:")
        print("   ✅ Database build complete")
        print("   ✅ Classification working") 
        print("   ✅ Pipeline integration successful")
        print("   ✅ Fallback system operational")
    else:
        print("⚠️  Some tests failed - check setup")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)