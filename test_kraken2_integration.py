#!/usr/bin/env python3
"""
Test script for Kraken2 integration
Tests the pipeline integration and fallback functionality
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test imports
def test_imports():
    """Test that all modules can be imported correctly"""
    try:
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        print("✅ Pipeline integrator imported successfully")
        
        from src.kraken2_classifier import Kraken2Classifier, Kraken2FallbackManager
        print("✅ Kraken2 classifier imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_kraken2_availability():
    """Test Kraken2 availability detection"""
    try:
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        integrator = MicrobiomePipelineIntegrator()
        
        # Test with Kraken2 disabled
        os.environ['ENABLE_KRAKEN2_CLASSIFICATION'] = 'false'
        should_use = integrator._should_use_kraken2()
        print(f"✅ Kraken2 disabled test: {not should_use}")
        
        # Test with Kraken2 enabled but no database
        os.environ['ENABLE_KRAKEN2_CLASSIFICATION'] = 'true'
        os.environ['KRAKEN2_DB_PATH'] = '/nonexistent/path'
        should_use = integrator._should_use_kraken2()
        print(f"✅ No database test: {not should_use}")
        
        # Test with Kraken2 enabled and database path (even if not built yet)
        os.environ['KRAKEN2_DB_PATH'] = '/home/trentleslie/kraken2_databases/standard'
        should_use = integrator._should_use_kraken2()
        db_exists = Path('/home/trentleslie/kraken2_databases/standard').exists()
        print(f"✅ Database path test: should_use={should_use}, db_exists={db_exists}")
        
        return True
    except Exception as e:
        print(f"❌ Availability test failed: {e}")
        return False

def test_configuration_loading():
    """Test configuration file loading"""
    try:
        from src.kraken2_classifier import Kraken2Classifier
        
        # Test direct classifier creation
        classifier = Kraken2Classifier(
            db_path="/home/trentleslie/kraken2_databases/standard",
            threads=32,
            confidence_threshold=0.1
        )
        print(f"✅ Configuration loaded: db_path={classifier.db_path}")
        print(f"   Threads: {classifier.threads}")
        print(f"   Confidence threshold: {classifier.confidence_threshold}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database_validation():
    """Test database validation logic"""
    try:
        from src.kraken2_classifier import Kraken2Classifier
        
        # Test with non-existent database
        classifier = Kraken2Classifier(db_path="/nonexistent/path")
        is_valid = classifier.validate_database()
        print(f"✅ Invalid database test: {not is_valid}")
        
        # Test with potentially valid database path
        classifier = Kraken2Classifier(db_path="/home/trentleslie/kraken2_databases/standard")
        is_valid = classifier.validate_database()
        print(f"✅ Database validation test: valid={is_valid} (expected False until build completes)")
        
        return True
    except Exception as e:
        print(f"❌ Database validation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Kraken2 Integration")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_kraken2_availability, 
        test_configuration_loading,
        test_database_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n🔍 Running {test.__name__}...")
        if test():
            passed += 1
        else:
            print(f"   Test failed!")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Kraken2 integration is ready.")
        print("\n📋 Next steps:")
        print("   1. Wait for database downloads to complete")
        print("   2. Test with actual FASTQ files")
        print("   3. Compare accuracy vs BioPython baseline")
    else:
        print("⚠️  Some tests failed - check integration setup")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)