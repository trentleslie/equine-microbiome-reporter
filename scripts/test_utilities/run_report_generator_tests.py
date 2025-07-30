#!/usr/bin/env python3
"""
Simplified test runner for ReportGenerator functionality
Runs key tests without requiring full pytest environment
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def run_test(test_name, test_function):
    """Run a single test and report results"""
    try:
        test_function()
        print(f"✅ {test_name}: PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name}: FAILED - {e}")
        if '--verbose' in sys.argv:
            traceback.print_exc()
        return False

def test_initialization():
    """Test ReportGenerator initialization"""
    from src.report_generator import ReportGenerator
    
    # Test default initialization
    generator = ReportGenerator()
    assert generator.language == "en"
    assert generator.template_name == "report_full.j2"
    assert generator.config is not None
    
    # Test custom language
    generator_pl = ReportGenerator(language="pl")
    assert generator_pl.language == "pl"
    
    # Test config loading
    assert "reference_ranges" in generator.config
    assert "dysbiosis_thresholds" in generator.config

def test_clinical_interpretation():
    """Test clinical interpretation generation"""
    from src.report_generator import ReportGenerator
    from tests.fixtures.report_data import create_sample_microbiome
    
    generator = ReportGenerator()
    
    # Test normal microbiome
    normal_data = create_sample_microbiome("normal")
    interpretation = generator._generate_clinical_text(normal_data)
    assert "normal" in interpretation.lower()
    
    # Test dysbiotic microbiome
    dysbiotic_data = create_sample_microbiome("dysbiotic")
    interpretation = generator._generate_clinical_text(dysbiotic_data)
    assert "severe" in interpretation.lower()
    assert "dysbiosis" in interpretation.lower()

def test_recommendations():
    """Test recommendation generation"""
    from src.report_generator import ReportGenerator
    from src.data_models import MicrobiomeData
    
    generator = ReportGenerator()
    
    # Test normal recommendations
    normal_data = MicrobiomeData(dysbiosis_index=15.0)
    recs = generator._get_recommendations(normal_data)
    assert len(recs) > 0
    assert any("continue" in rec.lower() for rec in recs)
    
    # Test severe recommendations
    severe_data = MicrobiomeData(dysbiosis_index=75.0)
    recs = generator._get_recommendations(severe_data)
    assert len(recs) > 0
    assert any("veterinary" in rec.lower() for rec in recs)

def test_template_context():
    """Test template context preparation"""
    from src.report_generator import ReportGenerator
    from tests.fixtures.report_data import create_sample_patient, create_sample_microbiome
    from unittest.mock import Mock, patch
    
    generator = ReportGenerator()
    patient = create_sample_patient()
    microbiome = create_sample_microbiome()
    chart_paths = {"test": "/tmp/test.png"}
    
    # Mock the template environment to test context preparation
    with patch.object(generator.env, 'get_template') as mock_get_template:
        mock_template = Mock()
        mock_get_template.return_value = mock_template
        mock_template.render.return_value = "test content"
        
        result = generator._render_template(patient, microbiome, chart_paths)
        
        # Verify template was called with correct context
        mock_template.render.assert_called_once()
        call_args = mock_template.render.call_args[1]  # keyword arguments
        
        assert "patient" in call_args
        assert "data" in call_args
        assert "config" in call_args
        assert "lang" in call_args
        assert "charts" in call_args

def test_fixtures():
    """Test that our test fixtures work correctly"""
    from tests.fixtures.report_data import (
        create_sample_patient, 
        create_sample_microbiome,
        create_test_scenario,
        create_batch_test_scenarios
    )
    
    # Test patient creation
    patient = create_sample_patient("TestHorse", "999")
    assert patient.name == "TestHorse"
    assert patient.sample_number == "999"
    
    # Test microbiome creation
    normal_microbiome = create_sample_microbiome("normal")
    assert normal_microbiome.dysbiosis_category == "normal"
    assert normal_microbiome.total_species_count > 0
    
    mild_microbiome = create_sample_microbiome("mild")
    assert mild_microbiome.dysbiosis_category == "mild"
    
    # Test scenarios
    patient, microbiome = create_test_scenario("normal_montana")
    assert patient.name == "Montana"
    assert microbiome.dysbiosis_category == "normal"
    
    # Test batch scenarios
    batch_scenarios = create_batch_test_scenarios()
    assert len(batch_scenarios) >= 3

def test_performance_data():
    """Test performance test data generation"""
    from tests.fixtures.report_data import get_performance_test_data
    
    patient, microbiome = get_performance_test_data()
    assert microbiome.total_species_count == 1000
    assert len(microbiome.species_list) == 1000
    assert patient.name == "Performance Test Horse"

def test_error_scenarios():
    """Test error handling scenarios"""
    from tests.fixtures.report_data import create_error_test_scenarios
    from src.report_generator import ReportGenerator
    
    generator = ReportGenerator()
    error_scenarios = create_error_test_scenarios()
    
    # Test that we can create scenarios without exceptions
    assert "empty_patient_name" in error_scenarios
    assert "invalid_microbiome" in error_scenarios
    
    # Test that generator handles edge cases gracefully
    _, invalid_microbiome = error_scenarios["invalid_microbiome"]
    interpretation = generator._generate_clinical_text(invalid_microbiome)
    assert isinstance(interpretation, str)

def main():
    """Run all tests"""
    print("🧪 Running ReportGenerator Test Suite")
    print("=" * 50)
    
    tests = [
        ("Initialization", test_initialization),
        ("Clinical Interpretation", test_clinical_interpretation),
        ("Recommendations", test_recommendations),
        ("Template Context", test_template_context),
        ("Test Fixtures", test_fixtures),
        ("Performance Data", test_performance_data),
        ("Error Scenarios", test_error_scenarios),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())