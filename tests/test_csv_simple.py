"""
Simple CSV processor test to bypass conftest issues
"""

import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Using installed package imports

# Mock the data_models import to avoid circular dependencies
class MockMicrobiomeData:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Patch the import before loading csv_processor
import unittest.mock
with unittest.mock.patch.dict('sys.modules', {'src.data_models': unittest.mock.MagicMock()}):
    sys.modules['src.data_models'].MicrobiomeData = MockMicrobiomeData
    from src.csv_processor import CSVProcessor


def test_csv_processor_initialization():
    """Test basic CSV processor initialization"""
    test_csv_path = Path(__file__).parent / "fixtures" / "csv_files" / "valid_sample.csv"
    
    processor = CSVProcessor(str(test_csv_path), "barcode01")
    
    assert processor.csv_path == str(test_csv_path)
    assert processor.barcode_column == "barcode01"
    assert isinstance(processor.df, pd.DataFrame)
    assert len(processor.df) > 0
    assert processor.total_count > 0


def test_csv_processor_species_list():
    """Test species list generation"""
    test_csv_path = Path(__file__).parent / "fixtures" / "csv_files" / "valid_sample.csv"
    
    processor = CSVProcessor(str(test_csv_path), "barcode01")
    species_list = processor._get_species_list()
    
    assert isinstance(species_list, list)
    assert len(species_list) > 0
    
    # Check first species structure
    first_species = species_list[0]
    required_keys = ["species", "genus", "phylum", "percentage", "count"]
    for key in required_keys:
        assert key in first_species
    
    # Verify percentages are valid
    for species in species_list:
        assert isinstance(species["percentage"], float)
        assert species["percentage"] > 0
        assert species["count"] > 0


def test_csv_processor_phylum_distribution():
    """Test phylum distribution calculation"""
    test_csv_path = Path(__file__).parent / "fixtures" / "csv_files" / "valid_sample.csv"
    
    processor = CSVProcessor(str(test_csv_path), "barcode01")
    species_list = processor._get_species_list()
    phylum_dist = processor._calculate_phylum_distribution(species_list)
    
    assert isinstance(phylum_dist, dict)
    assert len(phylum_dist) > 0
    
    # Check that percentages are positive
    for phylum, percentage in phylum_dist.items():
        assert isinstance(percentage, float)
        assert percentage > 0


def test_csv_processor_dysbiosis_calculation():
    """Test dysbiosis index calculation"""
    test_csv_path = Path(__file__).parent / "fixtures" / "csv_files" / "valid_sample.csv"
    
    processor = CSVProcessor(str(test_csv_path), "barcode01")
    species_list = processor._get_species_list()
    phylum_dist = processor._calculate_phylum_distribution(species_list)
    dysbiosis_index = processor._calculate_dysbiosis_index(phylum_dist)
    
    assert isinstance(dysbiosis_index, float)
    assert dysbiosis_index >= 0


def test_csv_processor_dysbiotic_sample():
    """Test processing of dysbiotic sample"""
    test_csv_path = Path(__file__).parent / "fixtures" / "csv_files" / "dysbiotic_sample.csv"
    
    processor = CSVProcessor(str(test_csv_path), "barcode01")
    species_list = processor._get_species_list()
    phylum_dist = processor._calculate_phylum_distribution(species_list)
    dysbiosis_index = processor._calculate_dysbiosis_index(phylum_dist)
    
    # Dysbiotic sample should have higher dysbiosis index
    assert dysbiosis_index > 20  # Should be at least mild dysbiosis


def test_csv_processor_category_assignment():
    """Test dysbiosis category assignment"""
    # Create mock processor instance
    processor = CSVProcessor.__new__(CSVProcessor)
    
    # Test categories
    assert processor._get_dysbiosis_category(10.0) == "normal"
    assert processor._get_dysbiosis_category(20.0) == "normal"
    assert processor._get_dysbiosis_category(30.0) == "mild"
    assert processor._get_dysbiosis_category(50.0) == "mild"
    assert processor._get_dysbiosis_category(60.0) == "severe"


def test_csv_processor_recommendations():
    """Test recommendations generation"""
    processor = CSVProcessor.__new__(CSVProcessor)
    
    # Test normal recommendations
    normal_recs = processor._get_recommendations(15.0)
    assert isinstance(normal_recs, list)
    assert len(normal_recs) > 0
    
    # Test severe recommendations
    severe_recs = processor._get_recommendations(75.0)
    assert isinstance(severe_recs, list)
    assert len(severe_recs) > 0
    assert len(severe_recs) != len(normal_recs)  # Should be different


if __name__ == "__main__":
    pytest.main([__file__, "-v"])