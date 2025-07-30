"""Custom assertions for microbiome testing"""

import pytest
from pathlib import Path
from typing import Dict, List, Any, Union
import re

def assert_valid_species_name(species_name: str):
    """Assert species name follows scientific naming convention"""
    assert isinstance(species_name, str), "Species name must be a string"
    assert len(species_name.strip()) > 0, "Species name cannot be empty"
    
    # Basic scientific name pattern (Genus species)
    pattern = r'^[A-Z][a-z]+ [a-z]+.*$'
    assert re.match(pattern, species_name.strip()), f"Invalid species name format: {species_name}"

def assert_valid_phylum_name(phylum_name: str):
    """Assert phylum name is valid"""
    valid_phyla = {
        'Actinomycetota', 'Bacillota', 'Bacteroidota', 'Pseudomonadota',
        'Fibrobacterota', 'Verrucomicrobiota', 'Spirochaetota',
        'Planctomycetota', 'Fusobacteriota'
    }
    
    assert phylum_name in valid_phyla, f"Invalid phylum name: {phylum_name}"

def assert_percentage_sum_valid(percentages: List[float], tolerance: float = 1.0):
    """Assert percentages sum to approximately 100%"""
    total = sum(percentages)
    assert abs(total - 100.0) <= tolerance, f"Percentages sum to {total}, expected ~100%"

def assert_dysbiosis_index_valid(index: Union[int, float]):
    """Assert dysbiosis index is within valid range"""
    assert isinstance(index, (int, float)), "Dysbiosis index must be numeric"
    assert 0 <= index <= 100, f"Dysbiosis index {index} out of range [0-100]"

def assert_dysbiosis_category_valid(category: str, dysbiosis_index: Union[int, float]):
    """Assert dysbiosis category matches the index value"""
    valid_categories = {'normal', 'mild', 'severe'}
    assert category in valid_categories, f"Invalid dysbiosis category: {category}"
    
    # Check category matches index
    if dysbiosis_index <= 20:
        assert category == 'normal', f"Index {dysbiosis_index} should be 'normal', got '{category}'"
    elif dysbiosis_index <= 50:
        assert category == 'mild', f"Index {dysbiosis_index} should be 'mild', got '{category}'"
    else:
        assert category == 'severe', f"Index {dysbiosis_index} should be 'severe', got '{category}'"

def assert_valid_csv_structure(csv_data: List[Dict], required_columns: List[str]):
    """Assert CSV data has required structure"""
    assert isinstance(csv_data, list), "CSV data must be a list"
    assert len(csv_data) > 0, "CSV data cannot be empty"
    
    for required_col in required_columns:
        for row in csv_data:
            assert required_col in row, f"Missing required column: {required_col}"

def assert_template_rendered_properly(rendered_content: str, expected_patterns: List[str]):
    """Assert template was rendered with expected content"""
    assert isinstance(rendered_content, str), "Rendered content must be a string"
    assert len(rendered_content.strip()) > 0, "Rendered content cannot be empty"
    
    for pattern in expected_patterns:
        assert pattern in rendered_content, f"Expected pattern not found: {pattern}"

def assert_patient_info_complete(patient_info: Dict):
    """Assert patient information is complete"""
    required_fields = ['name', 'age', 'species', 'sample_number']
    
    for field in required_fields:
        assert field in patient_info, f"Missing required patient field: {field}"
        assert patient_info[field] is not None, f"Patient field '{field}' cannot be None"
        assert str(patient_info[field]).strip() != "", f"Patient field '{field}' cannot be empty"

def assert_batch_results_valid(results: Dict):
    """Assert batch processing results are valid"""
    required_fields = ['total_processed', 'successful', 'failed', 'results']
    
    for field in required_fields:
        assert field in results, f"Missing batch result field: {field}"
    
    assert results['total_processed'] == results['successful'] + results['failed'], \
        "Total processed doesn't match successful + failed"
    
    assert isinstance(results['results'], list), "Results must be a list"

def assert_report_content_valid(content: str, language: str = 'en'):
    """Assert report content contains expected elements"""
    assert isinstance(content, str), "Report content must be a string"
    assert len(content.strip()) > 0, "Report content cannot be empty"
    
    # Common patterns that should appear in any language
    common_patterns = ['%', 'DNA', 'RNA']  # Scientific notation should be consistent
    
    for pattern in common_patterns:
        assert pattern in content, f"Missing expected scientific notation: {pattern}"
    
    # Language-specific patterns
    if language == 'en':
        english_patterns = ['Microbiome', 'Analysis', 'Results']
        for pattern in english_patterns:
            assert pattern in content, f"Missing English pattern: {pattern}"

def assert_file_permissions_valid(file_path: Path):
    """Assert file has appropriate permissions"""
    assert file_path.exists(), f"File does not exist: {file_path}"
    
    # Check file is readable
    assert file_path.is_file(), f"Path is not a file: {file_path}"
    
    # Check file size is reasonable
    file_size = file_path.stat().st_size
    assert file_size > 0, f"File is empty: {file_path}"