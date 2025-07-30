"""
Comprehensive test suite for CSV processor module
Tests CSV loading, data processing, and clinical calculations
"""

import pytest
import pandas as pd
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.csv_processor import CSVProcessor
from src.data_models import MicrobiomeData


class TestCSVProcessor:
    """Test suite for CSVProcessor class"""
    
    @pytest.fixture
    def test_data_dir(self):
        """Path to test fixture CSV files"""
        return Path(__file__).parent / "fixtures" / "csv_files"
    
    @pytest.fixture
    def valid_csv_path(self, test_data_dir):
        """Path to valid test CSV file"""
        return str(test_data_dir / "valid_sample.csv")
    
    @pytest.fixture
    def dysbiotic_csv_path(self, test_data_dir):
        """Path to dysbiotic test CSV file"""
        return str(test_data_dir / "dysbiotic_sample.csv")
    
    @pytest.fixture
    def minimal_csv_path(self, test_data_dir):
        """Path to minimal test CSV file"""
        return str(test_data_dir / "minimal_sample.csv")
    
    @pytest.fixture
    def edge_cases_csv_path(self, test_data_dir):
        """Path to edge cases test CSV file"""
        return str(test_data_dir / "edge_cases.csv")
    
    @pytest.fixture
    def invalid_csv_path(self, test_data_dir):
        """Path to invalid format test CSV file"""
        return str(test_data_dir / "invalid_format.csv")
    
    @pytest.fixture
    def large_csv_path(self, test_data_dir):
        """Path to large test CSV file"""
        return str(test_data_dir / "large_sample.csv")

    # CSV Loading Tests
    
    def test_load_valid_csv(self, valid_csv_path):
        """Test loading a valid CSV file"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        
        assert processor.csv_path == valid_csv_path
        assert processor.barcode_column == "barcode01"
        assert isinstance(processor.df, pd.DataFrame)
        assert len(processor.df) > 0
        assert "species" in processor.df.columns
        assert "phylum" in processor.df.columns
        assert "barcode01" in processor.df.columns
        assert processor.total_count > 0
    
    def test_invalid_file_path(self):
        """Test handling non-existent CSV file"""
        with pytest.raises(FileNotFoundError):
            CSVProcessor("nonexistent.csv", "barcode01")
    
    def test_invalid_barcode_column(self, valid_csv_path):
        """Test handling invalid barcode column"""
        with pytest.raises(KeyError):
            CSVProcessor(valid_csv_path, "nonexistent_barcode")
    
    def test_empty_barcode_column(self, edge_cases_csv_path):
        """Test handling barcode column with all zeros"""
        processor = CSVProcessor(edge_cases_csv_path, "barcode01")
        # Should still initialize but total_count may be low
        assert processor.total_count >= 0
    
    def test_missing_required_columns(self, invalid_csv_path):
        """Test handling CSV with missing required columns"""
        with pytest.raises(KeyError):
            CSVProcessor(invalid_csv_path, "barcode01")

    # Data Processing Tests
    
    def test_species_list_generation(self, valid_csv_path):
        """Test species list generation with percentages"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        assert isinstance(species_list, list)
        assert len(species_list) > 0
        
        # Check structure of species data
        for species in species_list:
            assert "species" in species
            assert "genus" in species
            assert "phylum" in species
            assert "percentage" in species
            assert "count" in species
            assert isinstance(species["percentage"], float)
            assert isinstance(species["count"], int)
            assert species["count"] > 0  # Should filter out zero counts
        
        # Check that percentages sum to approximately 100%
        total_percentage = sum(s["percentage"] for s in species_list)
        assert 99.0 <= total_percentage <= 101.0  # Allow for rounding
    
    def test_species_list_sorting(self, valid_csv_path):
        """Test that species are sorted by percentage descending"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        percentages = [s["percentage"] for s in species_list]
        assert percentages == sorted(percentages, reverse=True)
    
    def test_zero_count_filtering(self, edge_cases_csv_path):
        """Test that zero count species are filtered out"""
        processor = CSVProcessor(edge_cases_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        # Should not include the zero count species
        zero_count_species = [s for s in species_list if s["count"] == 0]
        assert len(zero_count_species) == 0
    
    def test_phylum_distribution_calculation(self, valid_csv_path):
        """Test phylum distribution aggregation"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        species_list = processor._get_species_list()
        phylum_dist = processor._calculate_phylum_distribution(species_list)
        
        assert isinstance(phylum_dist, dict)
        assert len(phylum_dist) > 0
        
        # Check that all percentages are positive
        for phylum, percentage in phylum_dist.items():
            assert isinstance(percentage, float)
            assert percentage > 0
        
        # Verify phylum totals match species sums
        manual_phylum_calc = {}
        for species in species_list:
            phylum = species["phylum"]
            if phylum not in manual_phylum_calc:
                manual_phylum_calc[phylum] = 0
            manual_phylum_calc[phylum] += species["percentage"]
        
        for phylum in phylum_dist:
            expected = round(manual_phylum_calc[phylum], 2)
            actual = phylum_dist[phylum]
            assert abs(expected - actual) < 0.01  # Allow for rounding

    # Clinical Calculation Tests
    
    def test_dysbiosis_index_calculation_normal(self, valid_csv_path):
        """Test dysbiosis index calculation for normal microbiome"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        species_list = processor._get_species_list()
        phylum_dist = processor._calculate_phylum_distribution(species_list)
        dysbiosis_index = processor._calculate_dysbiosis_index(phylum_dist)
        
        assert isinstance(dysbiosis_index, float)
        assert dysbiosis_index >= 0
        # Valid sample should have relatively low dysbiosis
        assert dysbiosis_index < 100
    
    def test_dysbiosis_index_calculation_dysbiotic(self, dysbiotic_csv_path):
        """Test dysbiosis index calculation for dysbiotic microbiome"""
        processor = CSVProcessor(dysbiotic_csv_path, "barcode01")
        species_list = processor._get_species_list()
        phylum_dist = processor._calculate_phylum_distribution(species_list)
        dysbiosis_index = processor._calculate_dysbiosis_index(phylum_dist)
        
        assert isinstance(dysbiosis_index, float)
        assert dysbiosis_index >= 0
        # Dysbiotic sample should have higher dysbiosis index
        assert dysbiosis_index > 20  # Should be at least mild dysbiosis
    
    def test_dysbiosis_index_boundary_conditions(self):
        """Test dysbiosis calculation at reference range boundaries"""
        processor = CSVProcessor.__new__(CSVProcessor)  # Create without __init__
        
        # Test perfect normal ranges (should give 0 dysbiosis)
        perfect_phylum_dist = {
            'Actinomycetota': 4.0,  # Mid-range
            'Bacillota': 45.0,      # Mid-range
            'Bacteroidota': 22.0,   # Mid-range
            'Pseudomonadota': 18.0, # Mid-range
            'Fibrobacterota': 2.5   # Mid-range
        }
        dysbiosis_index = processor._calculate_dysbiosis_index(perfect_phylum_dist)
        assert dysbiosis_index == 0.0
        
        # Test extreme values (should give high dysbiosis)
        extreme_phylum_dist = {
            'Actinomycetota': 0.0,    # Below minimum
            'Bacillota': 10.0,        # Below minimum
            'Bacteroidota': 1.0,      # Below minimum
            'Pseudomonadota': 80.0,   # Above maximum
            'Fibrobacterota': 0.0     # Below minimum
        }
        dysbiosis_index = processor._calculate_dysbiosis_index(extreme_phylum_dist)
        assert dysbiosis_index > 100
    
    def test_dysbiosis_category_assignment(self):
        """Test dysbiosis category assignment"""
        processor = CSVProcessor.__new__(CSVProcessor)  # Create without __init__
        
        # Test normal category
        assert processor._get_dysbiosis_category(10.0) == "normal"
        assert processor._get_dysbiosis_category(20.0) == "normal"
        
        # Test mild category  
        assert processor._get_dysbiosis_category(25.0) == "mild"
        assert processor._get_dysbiosis_category(50.0) == "mild"
        
        # Test severe category
        assert processor._get_dysbiosis_category(60.0) == "severe"
        assert processor._get_dysbiosis_category(100.0) == "severe"
    
    def test_clinical_interpretation_generation(self):
        """Test clinical interpretation text generation"""
        processor = CSVProcessor.__new__(CSVProcessor)  # Create without __init__
        
        # Test normal interpretation
        normal_interp = processor._generate_clinical_interpretation(15.0, {})
        assert "normal" in normal_interp.lower()
        assert "healthy" in normal_interp.lower()
        
        # Test mild dysbiosis interpretation
        mild_interp = processor._generate_clinical_interpretation(35.0, {})
        assert "mild" in mild_interp.lower()
        assert "dysbiosis" in mild_interp.lower()
        
        # Test severe dysbiosis interpretation
        severe_interp = processor._generate_clinical_interpretation(75.0, {})
        assert "severe" in severe_interp.lower()
        assert "dysbiosis" in severe_interp.lower()
    
    def test_recommendations_generation(self):
        """Test recommendations based on dysbiosis level"""
        processor = CSVProcessor.__new__(CSVProcessor)  # Create without __init__
        
        # Test normal recommendations
        normal_recs = processor._get_recommendations(15.0)
        assert isinstance(normal_recs, list)
        assert len(normal_recs) > 0
        assert any("continue" in rec.lower() for rec in normal_recs)
        
        # Test mild dysbiosis recommendations
        mild_recs = processor._get_recommendations(35.0)
        assert isinstance(mild_recs, list)
        assert len(mild_recs) > 0
        assert any("probiotic" in rec.lower() for rec in mild_recs)
        
        # Test severe dysbiosis recommendations
        severe_recs = processor._get_recommendations(75.0)
        assert isinstance(severe_recs, list)
        assert len(severe_recs) > 0
        assert any("intervention" in rec.lower() or "veterinary" in rec.lower() for rec in severe_recs)

    # Integration Tests
    
    def test_full_processing_pipeline(self, valid_csv_path):
        """Test complete processing pipeline"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        microbiome_data = processor.process()
        
        # Verify MicrobiomeData structure
        assert isinstance(microbiome_data, MicrobiomeData)
        assert isinstance(microbiome_data.species_list, list)
        assert isinstance(microbiome_data.phylum_distribution, dict)
        assert isinstance(microbiome_data.dysbiosis_index, float)
        assert isinstance(microbiome_data.total_species_count, int)
        assert isinstance(microbiome_data.dysbiosis_category, str)
        assert isinstance(microbiome_data.clinical_interpretation, str)
        assert isinstance(microbiome_data.recommendations, list)
        assert isinstance(microbiome_data.parasite_results, list)
        assert isinstance(microbiome_data.microscopic_results, list)
        assert isinstance(microbiome_data.biochemical_results, list)
        
        # Verify data consistency
        assert microbiome_data.total_species_count == len(microbiome_data.species_list)
        assert microbiome_data.dysbiosis_category in ["normal", "mild", "severe"]
        assert len(microbiome_data.clinical_interpretation) > 0
        assert len(microbiome_data.recommendations) > 0
    
    def test_default_results_generation(self, valid_csv_path):
        """Test generation of default laboratory results"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        
        # Test parasite results
        parasite_results = processor._get_default_parasite_results()
        assert isinstance(parasite_results, list)
        assert len(parasite_results) > 0
        for result in parasite_results:
            assert "name" in result
            assert "result" in result
        
        # Test microscopic results
        microscopic_results = processor._get_default_microscopic_results()
        assert isinstance(microscopic_results, list)
        assert len(microscopic_results) > 0
        for result in microscopic_results:
            assert "parameter" in result
            assert "result" in result
            assert "reference" in result
        
        # Test biochemical results
        biochemical_results = processor._get_default_biochemical_results()
        assert isinstance(biochemical_results, list)
        assert len(biochemical_results) > 0
        for result in biochemical_results:
            assert "parameter" in result
            assert "result" in result
            assert "reference" in result

    # Performance Tests
    
    def test_large_file_processing(self, large_csv_path):
        """Test processing of large CSV files"""
        processor = CSVProcessor(large_csv_path, "barcode01")
        
        # Should handle large files without issues
        species_list = processor._get_species_list()
        assert len(species_list) > 20  # Large file should have many species
        
        # Processing should complete in reasonable time
        import time
        start_time = time.time()
        microbiome_data = processor.process()
        processing_time = time.time() - start_time
        
        assert processing_time < 5.0  # Should process in under 5 seconds
        assert isinstance(microbiome_data, MicrobiomeData)
    
    def test_percentage_calculation_accuracy(self, valid_csv_path):
        """Test accuracy of percentage calculations"""
        processor = CSVProcessor(valid_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        # Manually calculate percentages and compare
        total_count = processor.total_count
        for species in species_list:
            expected_percentage = (species["count"] / total_count) * 100
            actual_percentage = species["percentage"]
            assert abs(expected_percentage - actual_percentage) < 0.01
    
    def test_reference_range_validation(self):
        """Test reference ranges match configuration"""
        processor = CSVProcessor.__new__(CSVProcessor)  # Create without __init__
        
        # The reference ranges in the method should match config
        # This is a smoke test to ensure ranges are reasonable
        test_phylum_dist = {
            'Actinomycetota': 4.0,
            'Bacillota': 45.0,
            'Bacteroidota': 22.0,
            'Pseudomonadota': 18.0,
            'Fibrobacterota': 2.5
        }
        
        # Should not raise any exceptions
        dysbiosis_index = processor._calculate_dysbiosis_index(test_phylum_dist)
        assert isinstance(dysbiosis_index, (int, float))
        assert dysbiosis_index >= 0

    # Edge Cases and Error Handling
    
    def test_unknown_phylum_handling(self, edge_cases_csv_path):
        """Test handling of unknown phylum names"""
        processor = CSVProcessor(edge_cases_csv_path, "barcode01")
        species_list = processor._get_species_list()
        phylum_dist = processor._calculate_phylum_distribution(species_list)
        
        # Should handle unknown phyla gracefully
        assert "UnknownPhylum" in phylum_dist
        
        # Dysbiosis calculation should still work
        dysbiosis_index = processor._calculate_dysbiosis_index(phylum_dist)
        assert isinstance(dysbiosis_index, float)
        assert dysbiosis_index >= 0
    
    def test_empty_species_name_handling(self, edge_cases_csv_path):
        """Test handling of empty species names"""
        processor = CSVProcessor(edge_cases_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        # Should have fallback for empty names
        empty_species = [s for s in species_list if not s["species"]]
        if empty_species:
            # Should have fallback value
            assert all(s["species"] == "Unknown species" for s in empty_species)
    
    def test_special_characters_handling(self, edge_cases_csv_path):
        """Test handling of special characters in species names"""
        processor = CSVProcessor(edge_cases_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        # Should handle special characters without errors
        special_species = [s for s in species_list if '"' in s["species"]]
        assert len(special_species) > 0  # Should find the special character species
    
    def test_high_count_values(self, edge_cases_csv_path):
        """Test handling of very high count values"""
        processor = CSVProcessor(edge_cases_csv_path, "barcode01")
        species_list = processor._get_species_list()
        
        # Should handle high counts without overflow
        high_count_species = [s for s in species_list if s["count"] > 100000]
        if high_count_species:
            for species in high_count_species:
                assert isinstance(species["percentage"], float)
                assert species["percentage"] > 0
                assert species["percentage"] <= 100
# - Test data validation and error handling
# - Test barcode column selection
# - Test species data processing
# - Test phylum distribution calculations
# - Test dysbiosis index calculations
# - Test clinical interpretation generation
# - Test edge cases (empty files, malformed data, etc.)

def test_placeholder():
    """Placeholder test to ensure pytest discovers this module"""
    assert True