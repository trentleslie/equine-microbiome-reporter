"""
TDD Phase 3: Error Handling and Edge Cases Tests

Tests for robust error handling, edge cases, and failure scenarios.
Following RED-GREEN-REFACTOR methodology for production-ready error handling.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import pandas as pd
import os
import tempfile
from pathlib import Path

# Import components for error testing
try:
    from src.kraken2_classifier import Kraken2Classifier, Kraken2FallbackManager, TaxonomyMapper
    from src.pipeline_integrator import MicrobiomePipelineIntegrator
except ImportError:
    # Expected during RED phase - some error handling may not exist yet
    pass


class TestKraken2DatabaseErrors:
    """
    TDD Phase 3 RED: Database-related error handling tests.
    These tests should FAIL until robust error handling is implemented.
    """
    
    def test_kraken2_database_missing_directory(self):
        """RED: Test handling of missing database directory"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Arrange - non-existent database path
        missing_db_path = "/completely/missing/database/path"
        
        # Act - should not crash, should handle gracefully
        classifier = Kraken2Classifier(missing_db_path)
        
        # Assert - should be initialized but marked as invalid
        assert classifier.database_valid is False
    
    def test_kraken2_database_empty_directory(self):
        """RED: Test handling of empty database directory"""
        from src.kraken2_classifier import Kraken2Classifier
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Act - empty directory as database
            classifier = Kraken2Classifier(temp_dir)
            
            # Assert - should recognize invalid database
            assert classifier.validate_database() is False
    
    def test_kraken2_database_corrupted_files(self):
        """RED: Test handling of corrupted database files"""
        from src.kraken2_classifier import Kraken2Classifier
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted database files (empty files)
            for filename in ['hash.k2d', 'opts.k2d', 'taxo.k2d']:
                Path(temp_dir) / filename).touch()  # Empty files
            
            classifier = Kraken2Classifier(temp_dir)
            
            # Should detect corruption and handle gracefully
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, 'kraken2', stderr="Database corrupted")
                
                with pytest.raises(RuntimeError, match="Database corrupted"):
                    classifier.classify_fastq_to_csv(['test.fastq'], 'barcode59')
    
    def test_kraken2_database_permission_denied(self):
        """RED: Test handling of database permission issues"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Mock permission denied error
        with patch('pathlib.Path.exists', side_effect=PermissionError("Permission denied")):
            classifier = Kraken2Classifier("/restricted/database")
            
            # Should handle permission errors gracefully
            assert classifier.validate_database() is False
    
    def test_kraken2_database_network_path_timeout(self):
        """RED: Test handling of network database paths that timeout"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Mock network timeout during database validation
        with patch('pathlib.Path.exists', side_effect=TimeoutError("Network timeout")):
            classifier = Kraken2Classifier("//network/share/database")
            
            # Should handle network timeouts gracefully
            assert classifier.validate_database() is False


class TestKraken2ExecutionErrors:
    """
    TDD Phase 3 RED: Kraken2 execution error handling tests.
    """
    
    @patch('subprocess.run')
    def test_kraken2_executable_not_found(self, mock_subprocess):
        """RED: Test handling when kraken2 executable is not in PATH"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Arrange - kraken2 not found
        mock_subprocess.side_effect = FileNotFoundError("kraken2: command not found")
        
        classifier = Kraken2Classifier("/test/db")
        
        # Act & Assert - should raise informative error
        with pytest.raises(RuntimeError, match="Kraken2 not found in PATH"):
            classifier.classify_fastq_to_csv(['test.fastq'], 'barcode59')
    
    @patch('subprocess.run')
    def test_kraken2_out_of_memory_error(self, mock_subprocess):
        """RED: Test handling of out-of-memory errors during classification"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Arrange - out of memory error
        mock_result = Mock()
        mock_result.returncode = 137  # SIGKILL (often OOM)
        mock_result.stderr = "kraken2: std::bad_alloc"
        mock_subprocess.return_value = mock_result
        
        classifier = Kraken2Classifier("/test/db")
        
        # Act & Assert - should provide helpful error message
        with pytest.raises(RuntimeError, match="out of memory|memory allocation"):
            classifier.classify_fastq_to_csv(['test.fastq'], 'barcode59')
    
    @patch('subprocess.run')
    def test_kraken2_disk_space_error(self, mock_subprocess):
        """RED: Test handling of insufficient disk space"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Arrange - disk space error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "No space left on device"
        mock_subprocess.return_value = mock_result
        
        classifier = Kraken2Classifier("/test/db")
        
        # Act & Assert - should detect disk space issues
        with pytest.raises(RuntimeError, match="disk space|No space left"):
            classifier.classify_fastq_to_csv(['test.fastq'], 'barcode59')
    
    @patch('subprocess.run')
    def test_kraken2_interrupted_execution(self, mock_subprocess):
        """RED: Test handling of interrupted Kraken2 execution"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Arrange - interrupted execution
        mock_subprocess.side_effect = KeyboardInterrupt("Process interrupted")
        
        classifier = Kraken2Classifier("/test/db")
        
        # Act & Assert - should handle interruption gracefully
        with pytest.raises(KeyboardInterrupt):
            classifier.classify_fastq_to_csv(['test.fastq'], 'barcode59')


class TestFASTQInputErrors:
    """
    TDD Phase 3 RED: FASTQ file input error handling tests.
    """
    
    def test_fastq_file_not_found(self):
        """RED: Test handling of missing FASTQ files"""
        from src.kraken2_classifier import Kraken2Classifier
        
        classifier = Kraken2Classifier("/test/db")
        
        # Act & Assert - should validate input files
        with pytest.raises(FileNotFoundError, match="FASTQ file not found"):
            classifier.classify_fastq_to_csv(['nonexistent.fastq'], 'barcode59')
    
    def test_fastq_file_empty(self):
        """RED: Test handling of empty FASTQ files"""
        from src.kraken2_classifier import Kraken2Classifier
        
        with tempfile.NamedTemporaryFile(suffix='.fastq', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            classifier = Kraken2Classifier("/test/db")
            
            # Should detect empty files and handle appropriately
            result = classifier.classify_fastq_to_csv([tmp_path], 'barcode59')
            
            # Should return empty DataFrame with correct structure
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            assert 'species' in result.columns
            assert 'barcode59' in result.columns
            
        finally:
            os.unlink(tmp_path)
    
    def test_fastq_file_malformed(self):
        """RED: Test handling of malformed FASTQ files"""
        from src.kraken2_classifier import Kraken2Classifier
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fastq', delete=False) as tmp:
            # Write malformed FASTQ content
            tmp.write("This is not a valid FASTQ file\n")
            tmp.write("Missing proper headers\n")
            tmp_path = tmp.name
        
        try:
            classifier = Kraken2Classifier("/test/db")
            
            # Should handle malformed FASTQ files gracefully
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 1
                mock_result.stderr = "Invalid FASTQ format"
                mock_run.return_value = mock_result
                
                with pytest.raises(RuntimeError, match="Invalid FASTQ format"):
                    classifier.classify_fastq_to_csv([tmp_path], 'barcode59')
                    
        finally:
            os.unlink(tmp_path)
    
    def test_fastq_multiple_files_mixed_validity(self):
        """RED: Test handling when some FASTQ files are valid, others invalid"""
        from src.kraken2_classifier import Kraken2Classifier
        
        # Create valid and invalid files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fastq', delete=False) as valid_file:
            valid_file.write("@seq1\nATCG\n+\nIIII\n")
            valid_path = valid_file.name
        
        invalid_path = "/nonexistent/file.fastq"
        
        try:
            classifier = Kraken2Classifier("/test/db")
            
            # Should validate all files before processing
            with pytest.raises(FileNotFoundError):
                classifier.classify_fastq_to_csv([valid_path, invalid_path], 'barcode59')
                
        finally:
            os.unlink(valid_path)


class TestFallbackManagerErrorHandling:
    """
    TDD Phase 3 RED: Fallback manager error handling tests.
    """
    
    def test_fallback_manager_both_methods_fail(self):
        """RED: Test when both Kraken2 and fallback processor fail"""
        from src.kraken2_classifier import Kraken2FallbackManager
        
        # Mock both Kraken2 and fallback failing
        mock_fallback_processor = Mock()
        mock_fallback_processor.process_fastq_files.side_effect = RuntimeError("Fallback also failed")
        
        manager = Kraken2FallbackManager(
            kraken2_db_path="/test/db",
            fallback_processor_class=mock_fallback_processor,
            use_kraken2=True
        )
        
        with patch.object(manager, 'kraken2_classifier') as mock_classifier:
            mock_classifier.classify_fastq_to_csv.side_effect = RuntimeError("Kraken2 failed")
            
            # Should raise informative error when both methods fail
            with pytest.raises(RuntimeError, match="All classification methods failed"):
                manager.process_fastq(['test.fastq'], 'barcode59')
    
    def test_fallback_manager_invalid_fallback_processor(self):
        """RED: Test handling of invalid fallback processor"""
        from src.kraken2_classifier import Kraken2FallbackManager
        
        # Create manager with invalid fallback processor
        invalid_processor = "not_a_valid_processor"
        
        with pytest.raises(TypeError, match="Invalid fallback processor"):
            manager = Kraken2FallbackManager(
                kraken2_db_path="/test/db",
                fallback_processor_class=invalid_processor
            )
    
    def test_fallback_manager_low_classification_rate_detection(self):
        """RED: Test detection of low classification rates requiring fallback"""
        from src.kraken2_classifier import Kraken2FallbackManager
        
        # Mock Kraken2 returning very low classification rate
        mock_classifier = Mock()
        low_quality_result = pd.DataFrame({
            'species': ['Unclassified', 'Unclassified'],
            'barcode59': [1000, 2000],  # High read counts but unclassified
            'phylum': ['Unclassified', 'Unclassified'],
            'genus': ['Unclassified', 'Unclassified']
        })
        mock_classifier.classify_fastq_to_csv.return_value = low_quality_result
        
        # Mock fallback processor with better results
        mock_fallback_processor = Mock()
        better_result = pd.DataFrame({
            'species': ['Lactobacillus acidophilus'],
            'barcode59': [1500],
            'phylum': ['Bacillota'],
            'genus': ['Lactobacillus']
        })
        mock_fallback_processor.process_fastq_files.return_value = better_result
        
        manager = Kraken2FallbackManager(
            kraken2_db_path="/test/db",
            fallback_processor_class=mock_fallback_processor
        )
        manager.kraken2_classifier = mock_classifier
        
        # Should detect low quality and use fallback
        result = manager.process_fastq(['test.fastq'], 'barcode59')
        
        # Should use better fallback result
        assert 'Lactobacillus acidophilus' in result['species'].values


class TestPipelineIntegrationErrorHandling:
    """
    TDD Phase 3 RED: Pipeline integration error handling tests.
    """
    
    def test_pipeline_integrator_invalid_configuration_combinations(self):
        """RED: Test handling of invalid configuration combinations"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Test invalid thread count
        with pytest.raises(ValueError, match="Threads must be positive"):
            MicrobiomePipelineIntegrator(
                use_kraken2=True,
                kraken2_threads=-1
            )
        
        # Test invalid confidence threshold
        with pytest.raises(ValueError, match="Confidence threshold must be between"):
            MicrobiomePipelineIntegrator(
                use_kraken2=True,
                kraken2_confidence=2.0  # > 1.0
            )
    
    def test_pipeline_integrator_recovery_from_partial_failures(self):
        """RED: Test recovery when some pipeline steps fail"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        integrator = MicrobiomePipelineIntegrator(use_kraken2=True)
        
        # Mock QC failure but classification success
        with patch('src.fastq_qc.FASTQQualityControl') as mock_qc_class:
            mock_qc = Mock()
            mock_qc.run_qc.side_effect = RuntimeError("QC failed")
            mock_qc_class.return_value = mock_qc
            
            # Should continue pipeline despite QC failure
            result = integrator.process_sample(
                fastq_file="test.fastq",
                patient_info={'name': 'Test'},
                run_qc=True,
                generate_pdf=False
            )
            
            # Should have error info but still process
            assert 'qc_error' in result
            assert result['classification_method'] is not None


class TestEdgeCaseDataHandling:
    """
    TDD Phase 3 RED: Edge case data handling tests.
    """
    
    def test_taxonomy_mapper_edge_cases(self):
        """RED: Test taxonomy mapping with unusual species names"""
        from src.kraken2_classifier import TaxonomyMapper
        
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "Single",  # Single word
            "Multiple word species name with extras",  # Very long name
            "Genus sp.",  # Common sp. notation
            "Genus spp.",  # Multiple species notation
            "Genus cf. species",  # Compare notation
            "Genus_species_with_underscores",  # Underscore format
            "123 Numeric genus",  # Numeric prefix
            "Genus-with-hyphens species",  # Hyphenated genus
        ]
        
        for edge_case in edge_cases:
            # Should not crash on any input
            genus = TaxonomyMapper.extract_genus(edge_case)
            phylum = TaxonomyMapper.map_to_phylum(edge_case)
            
            assert isinstance(genus, str)
            assert isinstance(phylum, str)
            assert genus != ""  # Should always return something
            assert phylum != ""  # Should always return something
    
    def test_csv_format_conversion_with_extreme_values(self):
        """RED: Test CSV conversion with extreme abundance values"""
        from src.kraken2_classifier import Kraken2Classifier
        
        classifier = Kraken2Classifier("/test/db")
        
        extreme_results = [
            {
                'species': 'Extreme high',
                'abundance_reads': 999999999,  # Very high
                'phylum': 'TestPhylum',
                'genus': 'TestGenus'
            },
            {
                'species': 'Zero abundance',
                'abundance_reads': 0,  # Zero
                'phylum': 'TestPhylum',
                'genus': 'TestGenus'
            },
            {
                'species': 'Fractional',
                'abundance_reads': 0.1,  # Fractional (should be converted to int)
                'phylum': 'TestPhylum',
                'genus': 'TestGenus'
            }
        ]
        
        # Should handle all extreme values gracefully
        result_df = classifier._convert_to_csv_format(extreme_results, 'barcode01')
        
        assert len(result_df) == 3
        assert all(isinstance(val, (int, float)) for val in result_df['barcode01'])
    
    def test_concurrent_processing_race_conditions(self):
        """RED: Test handling of concurrent access to shared resources"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        import threading
        import time
        
        integrator = MicrobiomePipelineIntegrator()
        
        # Simulate concurrent access to temporary files
        def concurrent_process():
            try:
                result = integrator.process_sample(
                    fastq_file="test.fastq",
                    patient_info={'name': f'Thread-{threading.current_thread().ident}'},
                    run_qc=False,
                    generate_pdf=False
                )
                return result
            except Exception as e:
                return {'error': str(e)}
        
        # Run multiple threads concurrently
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda: results.append(concurrent_process()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access gracefully (no deadlocks/corruption)
        assert len(results) == 3
        # At least one should succeed or provide meaningful error
        assert any('error' not in result or 'classification_method' in result for result in results)


# TDD Phase 3 RED Complete
# These error handling tests should FAIL until robust error handling is implemented
# Next: Implement comprehensive error handling (GREEN phase)