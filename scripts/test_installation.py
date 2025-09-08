#!/usr/bin/env python3
"""
Installation Test Script for HippoVet+
Run this to verify your setup is complete and working.
"""

import os
import sys
from pathlib import Path
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing Python imports...")
    try:
        from report_generator import ReportGenerator
        print("  ✅ report_generator")
    except ImportError as e:
        print(f"  ❌ report_generator: {e}")
        return False
    
    try:
        from clinical_filter import ClinicalFilter
        print("  ✅ clinical_filter")
    except ImportError as e:
        print(f"  ❌ clinical_filter: {e}")
        return False
    
    try:
        from data_models import PatientInfo, MicrobiomeData
        print("  ✅ data_models")
    except ImportError as e:
        print(f"  ❌ data_models: {e}")
        return False
    
    try:
        import pandas
        print("  ✅ pandas")
    except ImportError:
        print("  ❌ pandas - Run: pip install pandas")
        return False
    
    try:
        import reportlab
        print("  ✅ reportlab")
    except ImportError:
        print("  ❌ reportlab - Run: pip install reportlab")
        return False
    
    try:
        import weasyprint
        print("  ✅ weasyprint")
    except ImportError:
        print("  ❌ weasyprint - Run: pip install weasyprint")
        return False
    
    return True

def test_environment():
    """Test environment configuration."""
    print("\nTesting environment configuration...")
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("  ✅ .env file exists")
        
        # Check key configurations
        with open(env_file) as f:
            content = f.read()
            if "KRAKEN2_DB_PATH" in content:
                print("  ✅ Kraken2 database path configured")
            else:
                print("  ⚠️  Kraken2 database path not configured")
    else:
        print("  ❌ .env file not found - Copy .env.example to .env")
        print("     Run: cp .env.example .env")
        return False
    
    return True

def test_kraken2():
    """Test Kraken2 installation."""
    print("\nTesting Kraken2...")
    
    try:
        result = subprocess.run(["kraken2", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"  ✅ Kraken2 installed: {version}")
            return True
        else:
            print("  ❌ Kraken2 not working properly")
            return False
    except FileNotFoundError:
        print("  ⚠️  Kraken2 not found in PATH")
        print("     This is OK if you're using Epi2Me's Kraken2")
        return True  # Not critical for basic functionality

def test_sample_data():
    """Test that sample data exists."""
    print("\nTesting sample data...")
    
    sample_files = [
        "data/sample_1.csv",
        "data/sample_2.csv",
        "data/sample_3.csv"
    ]
    
    all_exist = True
    for file in sample_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} not found")
            all_exist = False
    
    return all_exist

def test_report_generation():
    """Test actual report generation."""
    print("\nTesting report generation...")
    
    try:
        from report_generator import ReportGenerator
        from data_models import PatientInfo
        
        # Create test patient
        patient = PatientInfo(
            name="TestHorse",
            sample_number="TEST001",
            age="5 years"
        )
        
        # Try to generate report
        generator = ReportGenerator(language="en")
        
        # Use sample data if it exists
        sample_csv = "data/sample_1.csv"
        if not Path(sample_csv).exists():
            print("  ⚠️  Sample data not found, skipping report test")
            return True
        
        output_pdf = "test_installation_report.pdf"
        success = generator.generate_report(sample_csv, patient, output_pdf)
        
        if success and Path(output_pdf).exists():
            size_kb = Path(output_pdf).stat().st_size / 1024
            print(f"  ✅ Test report generated: {output_pdf} ({size_kb:.1f} KB)")
            return True
        else:
            print("  ❌ Report generation failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error during report generation: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("HippoVet+ Equine Microbiome Reporter - Installation Test")
    print("="*60)
    
    tests_passed = 0
    tests_total = 5
    
    # Run tests
    if test_imports():
        tests_passed += 1
    
    if test_environment():
        tests_passed += 1
    
    if test_kraken2():
        tests_passed += 1
    
    if test_sample_data():
        tests_passed += 1
    
    if test_report_generation():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! System is ready for use.")
        print("\nNext steps:")
        print("1. Process a real sample with your data")
        print("2. Review the Excel output for clinical filtering")
        print("3. Check the PDF report quality")
        return 0
    elif tests_passed >= 3:
        print("⚠️  Most tests passed. Basic functionality should work.")
        print("\nRecommended actions:")
        print("- Review any failed tests above")
        print("- Ensure .env file is properly configured")
        return 0
    else:
        print("❌ Multiple tests failed. Please review the setup.")
        print("\nTroubleshooting:")
        print("1. Ensure you're in the conda environment:")
        print("   conda activate equine-microbiome")
        print("2. Install missing dependencies:")
        print("   pip install -r requirements.txt")
        print("3. Configure .env file:")
        print("   cp .env.example .env")
        return 1

if __name__ == "__main__":
    sys.exit(main())