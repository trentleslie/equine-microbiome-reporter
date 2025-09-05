"""
Test-Driven Development for Kraken2 Classification Module

Following TDD Red-Green-Refactor methodology.
Tests written FIRST, then minimal implementation to pass tests.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import pandas as pd
import os
import tempfile
from pathlib import Path

# NOTE: These imports will fail initially - that's the TDD "RED" phase
try:
    from src.kraken2_classifier import Kraken2Classifier, Kraken2FallbackManager
except ImportError:
    # Expected during RED phase - these classes don't exist yet
    pass


class TestKraken2Classifier:
    """
    TDD Phase 1: Core Functionality Tests (RED)
    These tests are written FIRST and should fail initially.
    """
    
    def test_kraken2_classifier_initialization_with_valid_parameters(self):
        """RED: Test initialization with valid database path and threads"""
        # Arrange
        db_path = "/test/kraken2/db"
        threads = 8
        
        # Act & Assert - This WILL FAIL initially (RED phase)
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier(db_path, threads=threads)
        
        assert classifier.db_path == db_path
        assert classifier.threads == threads
        assert classifier.confidence_threshold == 0.1  # default
        
    def test_kraken2_classifier_initialization_with_defaults(self):
        """RED: Test initialization with default parameters"""
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db")
        
        assert classifier.db_path == "/test/db"
        assert classifier.threads == 4  # default
        assert classifier.confidence_threshold == 0.1
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_database_validation_success(self, mock_isdir, mock_exists):
        """RED: Test successful database validation"""
        # Arrange - mock database exists and contains required files
        mock_exists.side_effect = lambda path: True
        mock_isdir.return_value = True
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/valid/db")
        result = classifier.validate_database()
        
        # Assert
        assert result is True
    
    @patch('os.path.exists')
    def test_database_validation_failure_missing_directory(self, mock_exists):
        """RED: Test database validation failure when directory missing"""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/missing/db")
        result = classifier.validate_database()
        
        # Assert
        assert result is False
    
    @patch('subprocess.run')
    def test_kraken2_subprocess_execution_success(self, mock_subprocess):
        """RED: Test successful Kraken2 subprocess execution"""
        # Arrange - mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "C\t1\t9606\t100\tfastq_file.fastq\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db")
        result = classifier._run_kraken2_classification(["test.fastq"], "output_prefix")
        
        # Assert
        assert result is not None
        mock_subprocess.assert_called_once()
        # Check that kraken2 command was called correctly
        args, kwargs = mock_subprocess.call_args
        command = args[0]
        assert "kraken2" in command
        assert "--db" in command
        assert "/test/db" in command
    
    @patch('subprocess.run')
    def test_kraken2_subprocess_execution_failure(self, mock_subprocess):
        """RED: Test Kraken2 subprocess execution failure"""
        # Arrange - mock failed subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Database not found"
        mock_subprocess.return_value = mock_result
        
        # Act & Assert
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db")
        
        with pytest.raises(RuntimeError, match="Kraken2 classification failed"):
            classifier._run_kraken2_classification(["test.fastq"], "output")
    
    def test_csv_format_conversion_single_sample(self):
        """RED: Test conversion of Kraken2 output to project CSV format"""
        # Arrange - mock Kraken2 classification results
        kraken2_results = [
            {
                "species": "Escherichia coli",
                "abundance_reads": 1500,
                "percentage": 15.0,
                "phylum": "Pseudomonadota",
                "genus": "Escherichia"
            },
            {
                "species": "Lactobacillus acidophilus",
                "abundance_reads": 2000,
                "percentage": 20.0,
                "phylum": "Bacillota",
                "genus": "Lactobacillus"
            }
        ]
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db")
        result_df = classifier._convert_to_csv_format(kraken2_results, "barcode59")
        
        # Assert - check CSV format matches project requirements
        expected_columns = ["species", "barcode59", "phylum", "genus"]
        assert list(result_df.columns) == expected_columns
        
        # Check data conversion
        assert len(result_df) == 2
        assert result_df.loc[0, "species"] == "Escherichia coli"
        assert result_df.loc[0, "barcode59"] == 1500  # abundance as reads
        assert result_df.loc[0, "phylum"] == "Pseudomonadota"
        assert result_df.loc[0, "genus"] == "Escherichia"
    
    def test_csv_format_conversion_multiple_samples(self):
        """RED: Test CSV conversion with multiple barcode columns"""
        # Arrange
        results_sample1 = [{"species": "E. coli", "abundance_reads": 100, "phylum": "Pseudomonadota", "genus": "Escherichia"}]
        results_sample2 = [{"species": "E. coli", "abundance_reads": 150, "phylum": "Pseudomonadota", "genus": "Escherichia"}]
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db")
        
        # First sample
        df1 = classifier._convert_to_csv_format(results_sample1, "barcode01")
        # Second sample  
        df2 = classifier._convert_to_csv_format(results_sample2, "barcode02")
        
        # Merge samples (simulating multi-sample CSV)
        merged_df = classifier._merge_sample_results([df1, df2])
        
        # Assert
        expected_cols = ["species", "barcode01", "barcode02", "phylum", "genus"] 
        assert list(merged_df.columns) == expected_cols
        assert merged_df.loc[0, "barcode01"] == 100
        assert merged_df.loc[0, "barcode02"] == 150
    
    @patch('subprocess.run')
    def test_basic_classification_workflow(self, mock_subprocess):
        """RED: Test complete basic workflow from FASTQ to CSV"""
        # Arrange - mock kraken2 output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "C\t1\t9606\t100\tfastq_file.fastq\n"
        mock_subprocess.return_value = mock_result
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isdir', return_value=True):
                    # Act
                    from src.kraken2_classifier import Kraken2Classifier
                    classifier = Kraken2Classifier("/test/db")
                    
                    result_df = classifier.classify_fastq_to_csv(
                        fastq_files=["test.fastq"],
                        barcode_column="barcode59"
                    )
                    
                    # Assert
                    assert isinstance(result_df, pd.DataFrame)
                    assert "barcode59" in result_df.columns
                    assert "species" in result_df.columns
    
    def test_confidence_threshold_filtering(self):
        """RED: Test that low-confidence classifications are filtered"""
        # Arrange - results with varying confidence
        kraken2_results = [
            {"species": "High confidence", "confidence": 0.8, "abundance_reads": 100, "phylum": "TestPhylum", "genus": "TestGenus"},
            {"species": "Low confidence", "confidence": 0.05, "abundance_reads": 50, "phylum": "TestPhylum", "genus": "TestGenus"}
        ]
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db", confidence_threshold=0.1)
        filtered_results = classifier._filter_by_confidence(kraken2_results)
        
        # Assert - only high confidence result should remain
        assert len(filtered_results) == 1
        assert filtered_results[0]["species"] == "High confidence"


class TestKraken2FallbackManager:
    """
    TDD Phase 1: Fallback Management Tests (RED)
    Tests for switching between Kraken2 and existing pipeline.
    """
    
    def test_fallback_manager_initialization(self):
        """RED: Test fallback manager creation"""
        from src.kraken2_classifier import Kraken2FallbackManager
        
        manager = Kraken2FallbackManager(
            kraken2_db_path="/test/db",
            fallback_processor_class="MockProcessor"
        )
        
        assert manager.kraken2_db_path == "/test/db"
        assert manager.fallback_processor_class == "MockProcessor"
        assert manager.use_kraken2 is True  # default should prefer kraken2
    
    @patch('src.kraken2_classifier.Kraken2Classifier')
    def test_fallback_manager_kraken2_success(self, mock_classifier_class):
        """RED: Test successful Kraken2 processing"""
        # Arrange
        mock_classifier = MagicMock()
        mock_classifier.classify_fastq_to_csv.return_value = pd.DataFrame({"test": [1]})
        mock_classifier_class.return_value = mock_classifier
        
        # Act
        from src.kraken2_classifier import Kraken2FallbackManager
        manager = Kraken2FallbackManager("/test/db", "MockProcessor")
        result = manager.process_fastq(["test.fastq"], "barcode59")
        
        # Assert
        assert isinstance(result, pd.DataFrame)
        mock_classifier.classify_fastq_to_csv.assert_called_once_with(["test.fastq"], "barcode59")
    
    @patch('src.kraken2_classifier.Kraken2Classifier')
    def test_fallback_manager_kraken2_failure_triggers_fallback(self, mock_classifier_class):
        """RED: Test fallback when Kraken2 fails"""
        # Arrange - Kraken2 fails
        mock_classifier = MagicMock()
        mock_classifier.classify_fastq_to_csv.side_effect = RuntimeError("Database error")
        mock_classifier_class.return_value = mock_classifier
        
        mock_fallback_processor = MagicMock()
        mock_fallback_result = pd.DataFrame({"fallback": [1]})
        mock_fallback_processor.process_fastq_files.return_value = mock_fallback_result
        
        # Act
        from src.kraken2_classifier import Kraken2FallbackManager
        manager = Kraken2FallbackManager("/test/db", mock_fallback_processor)
        result = manager.process_fastq(["test.fastq"], "barcode59")
        
        # Assert - should use fallback
        assert result.equals(mock_fallback_result)
    
    def test_fallback_manager_disabled_kraken2(self):
        """RED: Test when Kraken2 is explicitly disabled"""
        from src.kraken2_classifier import Kraken2FallbackManager
        
        mock_fallback_processor = MagicMock()
        mock_fallback_result = pd.DataFrame({"fallback_only": [1]})
        mock_fallback_processor.process_fastq_files.return_value = mock_fallback_result
        
        # Act
        manager = Kraken2FallbackManager("/test/db", mock_fallback_processor, use_kraken2=False)
        result = manager.process_fastq(["test.fastq"], "barcode59")
        
        # Assert - should go directly to fallback
        assert result.equals(mock_fallback_result)


class TestKraken2Integration:
    """
    TDD Phase 1: Integration Testing (RED)
    Test integration with existing pipeline components.
    """
    
    @patch('src.kraken2_classifier.Kraken2Classifier')
    @patch.dict('os.environ', {'KRAKEN2_DB_PATH': '/env/test/db'})
    def test_environment_configuration_loading(self, mock_classifier_class):
        """RED: Test loading configuration from environment variables"""
        # Act
        from src.kraken2_classifier import Kraken2FallbackManager
        manager = Kraken2FallbackManager.from_environment()
        
        # Assert
        assert manager.kraken2_db_path == '/env/test/db'
        mock_classifier_class.assert_called_once()
    
    def test_csv_format_compatibility_with_existing_pipeline(self):
        """RED: Test CSV output matches existing pipeline format exactly"""
        # Arrange - mock results in Kraken2 format
        kraken2_results = [
            {"species": "Lactobacillus acidophilus", "abundance_reads": 150, "phylum": "Bacillota", "genus": "Lactobacillus"},
            {"species": "Escherichia coli", "abundance_reads": 80, "phylum": "Pseudomonadota", "genus": "Escherichia"},
        ]
        
        # Act
        from src.kraken2_classifier import Kraken2Classifier
        classifier = Kraken2Classifier("/test/db")
        result_df = classifier._convert_to_csv_format(kraken2_results, "barcode45")
        
        # Assert - exact format match with existing CSV structure
        # Based on conftest.py sample_csv_content fixture format
        expected_columns = ["species", "barcode45", "phylum", "genus"]
        assert list(result_df.columns) == expected_columns
        
        # Check specific data types and values
        assert isinstance(result_df.loc[0, "barcode45"], int)  # abundance as integer
        assert result_df.loc[0, "species"] == "Lactobacillus acidophilus"
        assert result_df.loc[0, "phylum"] == "Bacillota"  # exact phylum name match
        assert result_df.loc[0, "genus"] == "Lactobacillus"


# TDD RED Phase Complete
# These tests should ALL FAIL initially since classes don't exist
# Next step: Implement minimal classes to make tests pass (GREEN phase)