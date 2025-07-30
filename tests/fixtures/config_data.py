"""Configuration data fixtures for testing"""

import yaml
from pathlib import Path

def get_test_report_config():
    """Get test report configuration"""
    return {
        "reference_ranges": {
            "Actinomycetota": [0.1, 8.0],
            "Bacillota": [20.0, 70.0],
            "Bacteroidota": [4.0, 40.0],
            "Pseudomonadota": [2.0, 35.0],
            "Fibrobacterota": [0.1, 5.0],
            "Verrucomicrobiota": [0.1, 3.0]
        },
        "dysbiosis_thresholds": {
            "normal": 20,
            "mild": 50
        },
        "colors": {
            "primary_blue": "#1E3A8A",
            "green": "#10B981",
            "teal": "#14B8A6",
            "red": "#EF4444",
            "yellow": "#F59E0B"
        },
        "laboratory_info": {
            "name": "HippoVet+ Laboratory",
            "address": "Test Address, Test City",
            "phone": "+48 123 456 789",
            "email": "test@hippovet.com"
        }
    }

def get_test_batch_config():
    """Get test batch processing configuration"""
    return {
        "input_dir": "tests/fixtures/csv_files",
        "output_dir": "tests/temp_output",
        "manifest_file": "tests/fixtures/test_manifest.csv",
        "language": "en",
        "parallel_workers": 2,
        "validation_enabled": True,
        "min_species_count": 5,
        "max_dysbiosis_index": 100,
        "timeout_seconds": 300
    }

def create_test_config_file(config_path: Path, config_data: dict = None):
    """Create a test configuration file"""
    if config_data is None:
        config_data = get_test_report_config()
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False)

def get_test_manifest_data():
    """Get test manifest data for batch processing"""
    return [
        {
            "sample_name": "sample_normal",
            "csv_file": "sample_normal.csv",
            "patient_name": "Montana",
            "patient_age": "20 years",
            "sample_number": "506",
            "barcode": "barcode01"
        },
        {
            "sample_name": "sample_dysbiotic", 
            "csv_file": "sample_dysbiotic.csv",
            "patient_name": "Thunder",
            "patient_age": "12 years",
            "sample_number": "507",
            "barcode": "barcode01"
        },
        {
            "sample_name": "sample_minimal",
            "csv_file": "sample_minimal.csv",
            "patient_name": "Lightning",
            "patient_age": "8 years",
            "sample_number": "508",
            "barcode": "barcode01"
        }
    ]

def get_invalid_config_data():
    """Get invalid configuration data for testing error handling"""
    return [
        # Missing required sections
        {
            "colors": {"primary_blue": "#1E3A8A"}
        },
        # Invalid reference ranges
        {
            "reference_ranges": {
                "Bacillota": [70.0, 20.0]  # Min > Max
            },
            "dysbiosis_thresholds": {"normal": 20, "mild": 50}
        },
        # Invalid dysbiosis thresholds
        {
            "reference_ranges": {"Bacillota": [20.0, 70.0]},
            "dysbiosis_thresholds": {"normal": 50, "mild": 20}  # Normal > Mild
        }
    ]