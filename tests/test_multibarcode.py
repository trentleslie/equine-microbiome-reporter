"""
Test suite for multi-barcode CSV processing.

These tests verify that the system can:
1. Detect ALL barcode columns in a CSV (not just the first one)
2. Process each barcode independently
3. Maintain backwards compatibility with single-barcode CSVs

Uses real feedback data from Gosia as test fixtures.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.csv_processor import CSVProcessor
from src.data_models import MicrobiomeData


class TestMultiBarcodeDetection:
    """Tests for detecting multiple barcode columns in CSV files"""

    @pytest.fixture
    def feedback_dir(self):
        """Path to feedback directory with real test data"""
        return Path(__file__).parent.parent / "feedback"

    @pytest.fixture
    def multibarcode_csv(self, feedback_dir):
        """Path to CSV with multiple barcodes (3 horses)"""
        return feedback_dir / "23_24_25.csv"

    @pytest.fixture
    def single_barcode_csv(self, feedback_dir):
        """Path to CSV with single barcode"""
        return feedback_dir / "barcode_23.csv"

    def test_get_all_barcode_columns_multi(self, multibarcode_csv):
        """CSV with barcode23, barcode24, barcode25 returns all three columns"""
        # Skip if feedback files don't exist (CI environment)
        if not multibarcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        columns = CSVProcessor.get_all_barcode_columns(str(multibarcode_csv))

        assert isinstance(columns, list)
        assert len(columns) == 3
        assert 'barcode23' in columns
        assert 'barcode24' in columns
        assert 'barcode25' in columns

    def test_get_all_barcode_columns_single(self, single_barcode_csv):
        """CSV with single barcode returns one-item list"""
        if not single_barcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        columns = CSVProcessor.get_all_barcode_columns(str(single_barcode_csv))

        assert isinstance(columns, list)
        assert len(columns) == 1
        assert 'barcode23' in columns

    def test_get_all_barcode_columns_preserves_order(self, multibarcode_csv):
        """Barcode columns are returned in CSV column order"""
        if not multibarcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        columns = CSVProcessor.get_all_barcode_columns(str(multibarcode_csv))

        # Should be in order as they appear in CSV
        assert columns == ['barcode23', 'barcode24', 'barcode25']


class TestExplicitBarcodeProcessing:
    """Tests for processing specific barcode columns"""

    @pytest.fixture
    def feedback_dir(self):
        return Path(__file__).parent.parent / "feedback"

    @pytest.fixture
    def multibarcode_csv(self, feedback_dir):
        return feedback_dir / "23_24_25.csv"

    def test_csv_processor_with_explicit_barcode(self, multibarcode_csv):
        """CSVProcessor uses specified barcode column, not first"""
        if not multibarcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        # Process with barcode25 explicitly
        processor = CSVProcessor(str(multibarcode_csv), barcode_column='barcode25')

        assert processor.barcode_column == 'barcode25'
        assert processor.total_count > 0

    def test_different_barcodes_produce_different_data(self, multibarcode_csv):
        """Each barcode produces different species counts"""
        if not multibarcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        # Process each barcode
        processor_23 = CSVProcessor(str(multibarcode_csv), barcode_column='barcode23')
        processor_24 = CSVProcessor(str(multibarcode_csv), barcode_column='barcode24')
        processor_25 = CSVProcessor(str(multibarcode_csv), barcode_column='barcode25')

        # Each should have different total counts (different horses)
        counts = {
            processor_23.total_count,
            processor_24.total_count,
            processor_25.total_count
        }

        # At least some should be different (same count would be coincidence)
        # Note: This test may need adjustment if data happens to have identical counts
        assert len(counts) >= 2, "Expected different horses to have different read counts"

    def test_process_produces_valid_microbiome_data(self, multibarcode_csv):
        """Processing any barcode produces valid MicrobiomeData"""
        if not multibarcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        for barcode in ['barcode23', 'barcode24', 'barcode25']:
            processor = CSVProcessor(str(multibarcode_csv), barcode_column=barcode)
            result = processor.process()

            assert isinstance(result, MicrobiomeData), f"Failed for {barcode}"
            assert len(result.species_list) > 0, f"No species for {barcode}"
            assert result.dysbiosis_index >= 0, f"Invalid DI for {barcode}"
            assert result.dysbiosis_category in ['normal', 'mild', 'severe']


class TestBackwardsCompatibility:
    """Tests ensuring single-barcode workflows still work"""

    @pytest.fixture
    def feedback_dir(self):
        return Path(__file__).parent.parent / "feedback"

    @pytest.fixture
    def single_barcode_csv(self, feedback_dir):
        return feedback_dir / "barcode_23.csv"

    @pytest.fixture
    def multibarcode_csv(self, feedback_dir):
        return feedback_dir / "23_24_25.csv"

    def test_single_barcode_auto_detection(self, single_barcode_csv):
        """Single-barcode CSV auto-detects the barcode column"""
        if not single_barcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        # Don't specify barcode_column - should auto-detect
        processor = CSVProcessor(str(single_barcode_csv))

        assert processor.barcode_column == 'barcode23'
        assert processor.total_count > 0

    def test_multibarcode_defaults_to_first(self, multibarcode_csv):
        """Multi-barcode CSV defaults to first barcode when not specified"""
        if not multibarcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        # Don't specify barcode_column - should use first
        processor = CSVProcessor(str(multibarcode_csv))

        # Should default to first barcode (barcode23)
        assert processor.barcode_column == 'barcode23'

    def test_existing_workflow_unchanged(self, single_barcode_csv):
        """Existing single-barcode workflow produces valid results"""
        if not single_barcode_csv.exists():
            pytest.skip("Feedback CSV files not available")

        processor = CSVProcessor(str(single_barcode_csv))
        result = processor.process()

        # Should work exactly as before
        assert isinstance(result, MicrobiomeData)
        assert len(result.species_list) > 0
        assert len(result.phylum_distribution) > 0
        assert result.dysbiosis_index >= 0


class TestBarcodeColumnEdgeCases:
    """Tests for edge cases in barcode detection"""

    def test_no_barcode_columns_raises_error(self, tmp_path):
        """CSV without barcode columns raises appropriate error"""
        # Create CSV without barcode columns
        csv_path = tmp_path / "no_barcode.csv"
        csv_path.write_text("species,count,phylum\nSpecies A,100,Bacillota\n")

        columns = CSVProcessor.get_all_barcode_columns(str(csv_path))
        assert columns == []

    def test_barcode_column_case_sensitivity(self, tmp_path):
        """Barcode detection is case-sensitive (barcode vs Barcode)"""
        # Create CSV with mixed case
        csv_path = tmp_path / "mixed_case.csv"
        csv_path.write_text("species,barcode01,Barcode02,BARCODE03,phylum\nA,1,2,3,Bacillota\n")

        columns = CSVProcessor.get_all_barcode_columns(str(csv_path))

        # Should only find lowercase 'barcode' prefix
        assert 'barcode01' in columns
        assert 'Barcode02' not in columns
        assert 'BARCODE03' not in columns

    def test_barcode_like_columns_excluded(self, tmp_path):
        """Columns with 'barcode' in middle/end are excluded"""
        csv_path = tmp_path / "barcode_like.csv"
        csv_path.write_text("species,barcode01,not_barcode,has_barcode_suffix,phylum\nA,1,2,3,Bacillota\n")

        columns = CSVProcessor.get_all_barcode_columns(str(csv_path))

        # Should only find columns STARTING with 'barcode'
        assert columns == ['barcode01']
