import csv
import json
from pathlib import Path
from typing import Dict, List, Any

def create_test_csv(data: List[Dict], output_path: Path):
    """Create a CSV file with test data"""
    if not data:
        return
        
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_test_data(filename: str) -> Any:
    """Load test data from JSON file"""
    path = Path(__file__).parent.parent / "fixtures" / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def assert_pdf_exists_and_valid(pdf_path: Path):
    """Assert PDF file exists and has reasonable properties"""
    assert pdf_path.exists(), f"PDF file not found: {pdf_path}"
    assert pdf_path.stat().st_size > 1000, f"PDF file too small: {pdf_path}"
    assert pdf_path.suffix == '.pdf', f"Not a PDF file: {pdf_path}"

def compare_csv_data(actual: List[Dict], expected: List[Dict], tolerance: float = 0.01):
    """Compare CSV data with tolerance for floating point values"""
    assert len(actual) == len(expected), "Different number of rows"
    
    for i, (actual_row, expected_row) in enumerate(zip(actual, expected)):
        for key in expected_row:
            assert key in actual_row, f"Missing key '{key}' in row {i}"
            
            if isinstance(expected_row[key], (int, float)):
                assert abs(actual_row[key] - expected_row[key]) <= tolerance, \
                    f"Value mismatch for '{key}' in row {i}"
            else:
                assert actual_row[key] == expected_row[key], \
                    f"Value mismatch for '{key}' in row {i}"

def create_test_manifest(samples: List[Dict], output_path: Path):
    """Create a manifest CSV file for batch testing"""
    fieldnames = ['sample_name', 'csv_file', 'patient_name', 'patient_age', 'sample_number', 'barcode']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)

def assert_microbiome_data_valid(data: Dict):
    """Assert microbiome data structure is valid"""
    required_fields = [
        'species_list', 'phylum_distribution', 'dysbiosis_index',
        'total_species_count', 'dysbiosis_category', 'clinical_interpretation'
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    assert isinstance(data['species_list'], list), "species_list must be a list"
    assert isinstance(data['phylum_distribution'], dict), "phylum_distribution must be a dict"
    assert isinstance(data['dysbiosis_index'], (int, float)), "dysbiosis_index must be numeric"
    assert isinstance(data['total_species_count'], int), "total_species_count must be an integer"
    assert data['dysbiosis_category'] in ['normal', 'mild', 'severe'], "Invalid dysbiosis_category"

def calculate_test_percentages(abundances: List[int]) -> List[float]:
    """Calculate percentages from abundance values for testing"""
    total = sum(abundances)
    if total == 0:
        return [0.0] * len(abundances)
    return [round((abundance / total) * 100, 2) for abundance in abundances]

def validate_test_output_structure(output_dir: Path, expected_files: List[str]):
    """Validate that output directory contains expected files"""
    assert output_dir.exists(), f"Output directory not found: {output_dir}"
    
    for expected_file in expected_files:
        file_path = output_dir / expected_file
        assert file_path.exists(), f"Expected file not found: {file_path}"

def cleanup_test_files(file_paths: List[Path]):
    """Clean up test files after test completion"""
    for file_path in file_paths:
        if file_path.exists():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)

def create_minimal_csv_data() -> List[Dict]:
    """Create minimal CSV data for basic testing"""
    return [
        {"species": "Test Species 1", "barcode01": 100, "phylum": "Bacillota", "genus": "TestGenus1"},
        {"species": "Test Species 2", "barcode01": 80, "phylum": "Bacteroidota", "genus": "TestGenus2"},
        {"species": "Test Species 3", "barcode01": 60, "phylum": "Pseudomonadota", "genus": "TestGenus3"},
        {"species": "Test Species 4", "barcode01": 40, "phylum": "Actinomycetota", "genus": "TestGenus4"},
        {"species": "Test Species 5", "barcode01": 20, "phylum": "Bacillota", "genus": "TestGenus5"}
    ]