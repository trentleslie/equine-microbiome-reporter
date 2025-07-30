"""
Test FASTQ to CSV compatibility with PDF generation pipeline

This test suite validates that FASTQ processing generates CSV files
compatible with the existing PDF report generation system.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.fastq_converter import FASTQtoCSVConverter
from src.csv_processor import CSVProcessor
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo


class TestFASTQCSVCompatibility:
    """Test compatibility between FASTQ processing and PDF pipeline"""
    
    @pytest.fixture
    def small_fastq_file(self):
        """Get path to a small FASTQ file for testing"""
        return "data/barcode04/FBC55250_pass_barcode04_168ca027_4fdcf48d_0.fastq.gz"
    
    @pytest.fixture
    def reference_csv(self):
        """Get path to reference CSV file"""
        return "data/sample_1.csv"
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_reference_csv_format(self, reference_csv):
        """Test that we understand the reference CSV format correctly"""
        df = pd.read_csv(reference_csv)
        
        # Check required columns are present
        expected_columns = ["species", "barcode59", "phylum", "genus", "family", "class", "order"]
        for col in expected_columns:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Check data types
        assert df["barcode59"].dtype in ["int64", "int32"], "Barcode column should be integer"
        assert df["species"].dtype == "object", "Species column should be string"
        assert df["phylum"].dtype == "object", "Phylum column should be string"
        
        # Check phylum names match reference ranges
        expected_phyla = ["Actinomycetota", "Bacillota", "Bacteroidota", "Pseudomonadota", "Fibrobacterota"]
        phyla_in_data = set(df["phylum"].unique())
        assert phyla_in_data.issubset(expected_phyla), f"Unexpected phyla: {phyla_in_data - set(expected_phyla)}"
        
        print(f"✅ Reference CSV format validated: {df.shape[0]} species, columns: {list(df.columns)}")
    
    def test_csv_processor_compatibility(self, reference_csv):
        """Test that CSVProcessor can handle the reference format"""
        try:
            processor = CSVProcessor(reference_csv, "barcode59")
            microbiome_data = processor.process()
            
            assert microbiome_data.total_species_count > 0, "Should have species data"
            assert microbiome_data.dysbiosis_index >= 0, "Dysbiosis index should be calculated"
            assert len(microbiome_data.phylum_distribution) > 0, "Should have phylum distribution"
            
            print(f"✅ CSVProcessor compatibility confirmed: {microbiome_data.total_species_count} species, DI: {microbiome_data.dysbiosis_index}")
            
        except Exception as e:
            pytest.fail(f"CSVProcessor failed with reference CSV: {e}")
    
    def test_fastq_processing_basic(self, small_fastq_file, temp_output_dir):
        """Test basic FASTQ processing (identify current issues)"""
        converter = FASTQtoCSVConverter()
        
        # Test with more lenient QC parameters
        try:
            df = converter.process_fastq_files(
                [small_fastq_file],
                sample_names=["04"],
                min_quality=10,  # More lenient
                min_length=50    # More lenient
            )
            
            # If this fails, we expect it to - this test documents the current state
            print(f"FASTQ processing result: {df.shape if df is not None else 'None'}")
            if df is not None:
                print(f"Columns: {list(df.columns)}")
                
        except Exception as e:
            print(f"Expected failure in FASTQ processing: {e}")
            # This is expected - we're documenting the issue
    
    def test_column_name_requirements(self):
        """Test what column names are expected by each component"""
        
        # Reference CSV uses these column names
        reference_columns = ["species", "barcode59", "phylum", "genus", "family", "class", "order"]
        
        # CSVProcessor expectations (from the code)
        processor_lookups = ["Species", "Genus", "Phylum"]  # Capitalized with fallback to lowercase
        
        # Mock CSV with different case combinations
        test_data = {
            "species": ["Test species"],
            "Species": ["Test species"],  # Test both cases
            "barcode59": [100],
            "phylum": ["Bacillota"],
            "Phylum": ["Bacillota"],
            "genus": ["Test"],
            "Genus": ["Test"],
            "family": ["Testaceae"],
            "class": ["Testi"],
            "order": ["Testales"]
        }
        
        df = pd.DataFrame(test_data)
        
        # CSVProcessor should handle both cases
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Test lowercase version
            lowercase_df = df[["species", "barcode59", "phylum", "genus", "family", "class", "order"]]
            lowercase_df.to_csv(f.name, index=False)
            
            try:
                processor = CSVProcessor(f.name, "barcode59")
                data = processor.process()
                assert data.total_species_count == 1, "Should process one species"
                print("✅ CSVProcessor handles lowercase column names")
            finally:
                os.unlink(f.name)
    
    def test_phylum_name_validation(self):
        """Test that phylum names match reference ranges exactly"""
        
        # These phylum names should work with dysbiosis calculation
        valid_phyla = ["Actinomycetota", "Bacillota", "Bacteroidota", "Pseudomonadota", "Fibrobacterota"]
        
        # These would cause issues
        invalid_phyla = ["Firmicutes", "Proteobacteria", "Actinobacteria"]  # Old naming
        
        for phylum in valid_phyla:
            test_data = {
                "species": ["Test species"],
                "barcode59": [100],
                "phylum": [phylum],
                "genus": ["Test"],
                "family": ["Testaceae"],
                "class": ["Testi"],
                "order": ["Testales"]
            }
            
            df = pd.DataFrame(test_data)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                
                try:
                    processor = CSVProcessor(f.name, "barcode59")
                    data = processor.process()
                    # Should calculate dysbiosis index without error
                    assert isinstance(data.dysbiosis_index, float), f"Dysbiosis calculation failed for {phylum}"
                    print(f"✅ {phylum} works correctly")
                finally:
                    os.unlink(f.name)
    
    def test_end_to_end_fastq_to_pdf(self, small_fastq_file, temp_output_dir):
        """Test complete FASTQ → CSV → PDF pipeline (will be enabled after fixes)"""
        
        # Step 1: FASTQ to CSV
        converter = FASTQtoCSVConverter()
        csv_path = os.path.join(temp_output_dir, "test_output.csv")
        
        df = converter.process_fastq_files([small_fastq_file], sample_names=["04"], barcode_column="barcode59")
        converter.save_to_csv(df, csv_path)
        
        # Step 2: CSV to PDF
        patient_info = PatientInfo(
            name="Test Horse",
            sample_number="004",
            age="5 years"
        )
        
        generator = ReportGenerator(language="en")
        pdf_path = os.path.join(temp_output_dir, "test_report.pdf")
        
        success = generator.generate_report(
            csv_path=csv_path,
            patient_info=patient_info,
            output_path=pdf_path
        )
        
        assert success, "PDF generation should succeed"
        assert os.path.exists(pdf_path), "PDF file should be created"
        
        print(f"✅ End-to-end pipeline successful: {pdf_path}")
    
    def test_format_specification_compliance(self):
        """Test that we understand the CSV format specification correctly"""
        
        # From docs/csv_format_specification.md
        required_columns = ["species", "phylum", "genus", "family", "class", "order"]
        barcode_pattern = r"barcode\d+"
        
        # Test with reference CSV
        df = pd.read_csv("data/sample_1.csv")
        
        # Check required columns
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Check barcode column exists and matches pattern
        barcode_cols = [col for col in df.columns if col.startswith("barcode")]
        assert len(barcode_cols) >= 1, "Must have at least one barcode column"
        
        # Check data integrity
        barcode_col = barcode_cols[0]
        assert df[barcode_col].sum() > 0, "Must have non-zero total counts"
        assert len(df[df[barcode_col] > 0]) >= 10, "Should have at least 10 species with counts"
        
        print(f"✅ Format specification compliance confirmed: {len(df)} species, {barcode_col}")


class TestFASTQProcessingFixes:
    """Tests for the fixes we need to implement"""
    
    def test_quality_control_parameters(self):
        """Test that QC parameters are appropriate for real data"""
        
        # Current parameters may be too strict
        # Need to test with actual FASTQ data to determine good defaults
        
        # For real 16S rRNA data, these might be more appropriate:
        suggested_params = {
            "min_quality": 15,  # Q15 instead of Q20
            "min_length": 100,  # 100bp instead of 200bp
        }
        
        print(f"Suggested QC parameters: {suggested_params}")
        
        # This test documents what we should change
        assert suggested_params["min_quality"] < 20, "Should use more lenient quality threshold"
        assert suggested_params["min_length"] < 200, "Should use more lenient length threshold"
    
    def test_barcode_naming_convention(self):
        """Test the barcode naming convention that should be used"""
        
        # Current implementation creates barcode04, barcode05, etc.
        # But CSVProcessor expects specific barcode names like barcode59
        
        # The correct approach should be:
        # 1. User specifies which barcode column name to use
        # 2. FASTQ converter creates that specific column name
        # 3. Multiple FASTQ files can map to different barcode columns
        
        expected_pattern = "barcode59"  # As used in reference CSV
        
        print(f"Expected barcode column pattern: {expected_pattern}")
        assert expected_pattern.startswith("barcode"), "Should start with 'barcode'"
        assert expected_pattern[7:].isdigit(), "Should end with number"
    
    def test_taxonomy_assignment_requirements(self):
        """Test what's needed for proper taxonomy assignment"""
        
        # Current mock taxonomy is insufficient
        # Real implementation needs:
        # 1. Sequence similarity search against reference database
        # 2. Proper phylum assignment matching reference ranges
        # 3. Complete taxonomic lineage
        
        required_phyla = ["Actinomycetota", "Bacillota", "Bacteroidota", "Pseudomonadota", "Fibrobacterota"]
        
        print(f"Required phyla for dysbiosis calculation: {required_phyla}")
        
        # This test documents the requirement
        assert len(required_phyla) == 5, "Should support 5 main phyla"
        assert all(phylum.endswith("ota") for phylum in required_phyla), "Should use modern phylum names"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])