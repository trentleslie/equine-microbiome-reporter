"""
Comprehensive tests for batch processor module

Tests cover batch processing workflows, validation, parallel processing,
manifest processing, and performance scenarios.
"""

import pytest
import tempfile
import time
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from src.batch_processor import BatchProcessor, BatchConfig
from src.data_models import PatientInfo
from tests.utils.batch_test_helpers import (
    create_temp_batch_config,
    create_test_csv_files,
    create_large_batch_files,
    assert_processing_result,
    assert_batch_results,
    cleanup_temp_directories,
    create_test_patient_info,
    MockProgressCallback,
    count_species_in_csv
)


class TestBatchConfig:
    """Test BatchConfig class functionality"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = BatchConfig()
        
        assert config.data_dir == Path('data')
        assert config.reports_dir == Path('reports/batch_output')
        assert config.language == 'en'
        assert config.parallel_processing is True
        assert config.max_workers <= 4
        assert config.min_species_count == 10
        assert config.max_unassigned_percentage == 50.0
        assert "Bacillota" in config.required_phyla
        assert "Bacteroidota" in config.required_phyla
        assert "Pseudomonadota" in config.required_phyla
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        custom_config = {
            'data_dir': 'custom/data',
            'reports_dir': 'custom/reports',
            'language': 'pl',
            'parallel_processing': False,
            'max_workers': 8,
            'min_species_count': 20,
            'max_unassigned_percentage': 30.0,
            'required_phyla': ["Bacillota", "Bacteroidota"]
        }
        
        config = BatchConfig(**custom_config)
        
        assert config.data_dir == Path('custom/data')
        assert config.reports_dir == Path('custom/reports')
        assert config.language == 'pl'
        assert config.parallel_processing is False
        assert config.max_workers == 8
        assert config.min_species_count == 20
        assert config.max_unassigned_percentage == 30.0
        assert len(config.required_phyla) == 2
    
    def test_ensure_directories(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = BatchConfig(reports_dir=Path(temp_dir) / 'test_reports')
            assert not config.reports_dir.exists()
            
            config.ensure_directories()
            assert config.reports_dir.exists()
            assert config.reports_dir.is_dir()
    
    def test_to_dict(self):
        """Test configuration serialization"""
        config = BatchConfig(language='en', max_workers=4)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['language'] == 'en'
        assert config_dict['max_workers'] == 4
        assert 'data_dir' in config_dict
        assert 'reports_dir' in config_dict


class TestBatchProcessor:
    """Test BatchProcessor class functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration"""
        config = create_temp_batch_config()
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    def test_initialization(self, batch_config):
        """Test processor initialization"""
        processor = BatchProcessor(batch_config)
        
        assert processor.config == batch_config
        assert processor.results == []
        assert processor.errors == []
    
    def test_initialization_with_defaults(self):
        """Test processor initialization with default config"""
        processor = BatchProcessor()
        
        assert isinstance(processor.config, BatchConfig)
        assert processor.results == []
        assert processor.errors == []
    
    def test_extract_patient_info_from_filename(self, processor):
        """Test patient info extraction from various filename formats"""
        # Test date format: DD_MM_YY_name.csv
        patient1 = processor.extract_patient_info_from_filename("25_04_23_montana_bact.csv")
        assert patient1.name == "Montana"
        assert "25.04.2023" in patient1.date_received
        
        # Test sample format: sample_N.csv
        patient2 = processor.extract_patient_info_from_filename("sample_506.csv")
        assert patient2.name == "Sample 506"
        assert patient2.sample_number == "506"
        
        # Test generic name format
        patient3 = processor.extract_patient_info_from_filename("thunder_test.csv")
        assert patient3.name == "Thunder Test"
        
        # Test auto-generated sample number
        patient4 = processor.extract_patient_info_from_filename("test.csv")
        assert patient4.sample_number.startswith("AUTO-")
    
    def test_validate_csv_file_valid(self, processor):
        """Test CSV validation with valid file"""
        csv_path = Path('tests/fixtures/batch_data/valid_batch/sample_batch_1.csv')
        is_valid, message = processor.validate_csv_file(csv_path)
        
        assert is_valid is True
        assert "Validation passed" in message
    
    def test_validate_csv_file_insufficient_species(self, processor):
        """Test CSV validation with insufficient species count"""
        # Create temporary file with too few species
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("species,barcode01,phylum,genus\n")
            f.write("Species1,100,Bacillota,Genus1\n")
            f.write("Species2,50,Bacteroidota,Genus2\n")
            temp_path = Path(f.name)
        
        try:
            is_valid, message = processor.validate_csv_file(temp_path)
            assert is_valid is False
            assert "Too few species" in message
        finally:
            temp_path.unlink()
    
    def test_validate_csv_file_missing_phyla(self, processor):
        """Test CSV validation with missing required phyla"""
        # Create file missing required phyla
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("species,barcode01,phylum,genus\n")
            for i in range(15):
                f.write(f"Species{i},100,Actinomycetota,Genus{i}\n")
            temp_path = Path(f.name)
        
        try:
            is_valid, message = processor.validate_csv_file(temp_path)
            assert is_valid is False
            assert "Missing required phyla" in message
        finally:
            temp_path.unlink()
    
    def test_validate_csv_file_high_unassigned(self, processor):
        """Test CSV validation with high unassigned percentage"""
        csv_path = Path('tests/fixtures/batch_data/mixed_quality/poor_sample.csv')
        is_valid, message = processor.validate_csv_file(csv_path)
        
        assert is_valid is False
        assert "Too many unassigned" in message
    
    def test_validate_csv_file_nonexistent(self, processor):
        """Test CSV validation with non-existent file"""
        csv_path = Path('nonexistent_file.csv')
        is_valid, message = processor.validate_csv_file(csv_path)
        
        assert is_valid is False
        assert "File not found" in message


class TestCoreBatchProcessing:
    """Test core batch processing functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration"""
        config = create_temp_batch_config()
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_single_file_success(self, mock_generator, processor):
        """Test successful single file processing"""
        # Mock successful report generation
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        csv_path = Path('tests/fixtures/batch_data/valid_batch/sample_batch_1.csv')
        result = processor.process_single_file(csv_path, validate=False)
        
        assert_processing_result(result, expected_success=True)
        assert result['patient_name'] == 'Sample 1'  # Based on filename extraction logic
        assert result['processing_time'] > 0
        assert 'Report generated successfully' in result['message']
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_single_file_generation_failure(self, mock_generator, processor):
        """Test single file processing with report generation failure"""
        # Mock failed report generation
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = False
        mock_generator.return_value = mock_instance
        
        csv_path = Path('tests/fixtures/batch_data/valid_batch/sample_batch_1.csv')
        result = processor.process_single_file(csv_path, validate=False)
        
        assert_processing_result(result, expected_success=False)
        assert 'Report generation failed' in result['message']
    
    def test_process_single_file_validation_failure(self, processor):
        """Test single file processing with validation failure"""
        csv_path = Path('tests/fixtures/batch_data/mixed_quality/poor_sample.csv')
        result = processor.process_single_file(csv_path, validate=True)
        
        assert_processing_result(result, expected_success=False)
        assert result['validation_passed'] is False
        assert 'Validation failed' in result['message']
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_single_file_exception_handling(self, mock_generator, processor):
        """Test single file processing exception handling"""
        # Mock exception during report generation
        mock_instance = MagicMock()
        mock_instance.generate_report.side_effect = Exception("Test error")
        mock_generator.return_value = mock_instance
        
        csv_path = Path('tests/fixtures/batch_data/valid_batch/sample_batch_1.csv')
        result = processor.process_single_file(csv_path, validate=False)
        
        assert_processing_result(result, expected_success=False)
        assert 'Error: Test error' in result['message']
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_directory_sequential(self, mock_generator, processor):
        """Test directory processing in sequential mode"""
        # Mock successful report generation
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        processor.config.parallel_processing = False
        results = processor.process_directory(validate=False)
        
        analysis = assert_batch_results(results, min_successful=1)
        assert analysis['success_rate'] > 0.8  # Most should succeed
        assert len(results) == 3  # Three files in valid_batch directory
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_directory_with_progress_callback(self, mock_generator, processor):
        """Test directory processing with progress callback"""
        # Mock successful report generation
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        progress_callback = MockProgressCallback()
        processor.config.parallel_processing = False
        
        results = processor.process_directory(
            progress_callback=progress_callback,
            validate=False
        )
        
        progress_callback.assert_called()
        progress_callback.assert_completed()
        assert len(results) > 0
    
    def test_process_directory_empty_directory(self, processor):
        """Test processing empty directory"""
        # Create empty temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            processor.config.data_dir = Path(temp_dir)
            results = processor.process_directory()
            
            assert results == []
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_directory_mixed_results(self, mock_generator, processor):
        """Test directory processing with mixed success/failure"""
        # Mock alternating success/failure
        mock_instance = MagicMock()
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            return call_count[0] % 2 == 1  # Alternate True/False
        mock_instance.generate_report.side_effect = side_effect
        mock_generator.return_value = mock_instance
        
        processor.config.data_dir = Path('tests/fixtures/batch_data/mixed_quality')
        results = processor.process_directory(validate=False)
        
        analysis = assert_batch_results(results, min_successful=0)
        assert analysis['success_rate'] < 1.0  # Some should fail
        assert len(analysis['failed']) > 0


class TestValidationAndQualityControl:
    """Test validation and quality control functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration with custom validation"""
        config = create_temp_batch_config(
            min_species_count=8,
            max_unassigned_percentage=40.0,
            required_phyla=["Bacillota", "Bacteroidota"]
        )
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    def test_validation_threshold_enforcement(self, processor):
        """Test validation threshold enforcement"""
        # Test file that should pass with lowered thresholds
        csv_path = Path('tests/fixtures/batch_data/mixed_quality/good_sample.csv')
        is_valid, message = processor.validate_csv_file(csv_path)
        assert is_valid is True
        
        # Test file that should fail
        csv_path = Path('tests/fixtures/batch_data/mixed_quality/poor_sample.csv')
        is_valid, message = processor.validate_csv_file(csv_path)
        assert is_valid is False
    
    def test_custom_validation_rules(self, processor):
        """Test custom validation rule configuration"""
        # Verify custom thresholds are applied
        assert processor.config.min_species_count == 8
        assert processor.config.max_unassigned_percentage == 40.0
        assert len(processor.config.required_phyla) == 2
    
    @patch('src.batch_processor.ReportGenerator')
    def test_validation_during_batch_processing(self, mock_generator, processor):
        """Test validation integration during batch processing"""
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        processor.config.data_dir = Path('tests/fixtures/batch_data/mixed_quality')
        results = processor.process_directory(validate=True)
        
        # Should have both successful and failed results due to validation
        analysis = assert_batch_results(results, min_successful=0)
        validation_failures = [r for r in analysis['failed'] 
                             if 'Validation failed' in r.get('message', '')]
        assert len(validation_failures) > 0
    
    def test_quality_control_edge_cases(self, processor):
        """Test quality control with edge cases"""
        # Test with file having exactly threshold values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("species,barcode01,phylum,genus\n")
            # Exactly 8 species (minimum threshold)
            for i in range(4):
                f.write(f"SpeciesB{i},100,Bacillota,GenusB{i}\n")
            for i in range(4):
                f.write(f"SpeciesBact{i},100,Bacteroidota,GenusBact{i}\n")
            temp_path = Path(f.name)
        
        try:
            is_valid, message = processor.validate_csv_file(temp_path)
            assert is_valid is True  # Should pass exactly at threshold
        finally:
            temp_path.unlink()


class TestParallelProcessing:
    """Test parallel processing functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration for parallel processing"""
        config = create_temp_batch_config(
            parallel_processing=True,
            max_workers=2
        )
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture  
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    @patch('src.batch_processor.ReportGenerator')
    def test_parallel_vs_sequential_performance(self, mock_generator, processor):
        """Test parallel processing performance vs sequential"""
        # Create larger batch for meaningful performance comparison
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            create_large_batch_files(temp_path, count=6)
            processor.config.data_dir = temp_path
            
            # Mock report generation with small delay
            mock_instance = MagicMock()
            def slow_generation(*args, **kwargs):
                time.sleep(0.1)  # Small delay to simulate work
                return True
            mock_instance.generate_report.side_effect = slow_generation
            mock_generator.return_value = mock_instance
            
            # Test parallel processing
            processor.config.parallel_processing = True
            start_time = time.time()
            results_parallel = processor.process_directory(validate=False)
            parallel_time = time.time() - start_time
            
            # Test sequential processing
            processor.config.parallel_processing = False
            start_time = time.time()
            results_sequential = processor.process_directory(validate=False)
            sequential_time = time.time() - start_time
            
            # Verify results are equivalent
            assert len(results_parallel) == len(results_sequential)
            
            # Parallel should be faster (allowing some variance for test stability)
            # Only assert if we have enough files to make parallelism worthwhile
            if len(results_parallel) >= 4:
                assert parallel_time < sequential_time * 0.9
    
    @patch('src.batch_processor.ReportGenerator')
    def test_parallel_processing_error_isolation(self, mock_generator, processor):
        """Test error isolation in parallel processing"""
        # Mock mixed success/failure scenarios
        mock_instance = MagicMock()
        call_count = [0]
        def mixed_results(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:  # Every second call fails
                raise Exception(f"Simulated error {call_count[0]}")
            return True
        mock_instance.generate_report.side_effect = mixed_results
        mock_generator.return_value = mock_instance
        
        processor.config.parallel_processing = True
        results = processor.process_directory(validate=False)
        
        # Should have both successful and failed results
        analysis = assert_batch_results(results, min_successful=0)
        # With 3 files and every second call failing, we should have at least 1 failure
        assert len(analysis['failed']) >= 1
        assert len(analysis['successful']) >= 1
    
    @patch('src.batch_processor.ReportGenerator')
    def test_parallel_processing_thread_safety(self, mock_generator, processor):
        """Test thread safety of parallel processing"""
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        # Run parallel processing multiple times to test thread safety
        for _ in range(3):
            results = processor.process_directory(validate=False)
            analysis = assert_batch_results(results, min_successful=1)
            assert analysis['success_rate'] > 0.9
    
    def test_single_file_uses_sequential(self, processor):
        """Test that single file processing doesn't use parallel mode"""
        processor.config.parallel_processing = True
        
        # With only one file, should use sequential processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            create_large_batch_files(temp_path, count=1)
            processor.config.data_dir = temp_path
            
            with patch('src.batch_processor.ProcessPoolExecutor') as mock_executor:
                results = processor.process_directory(validate=False)
                # ProcessPoolExecutor should not be used for single file
                mock_executor.assert_not_called()


class TestManifestProcessing:
    """Test manifest-based processing functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration"""
        config = create_temp_batch_config()
        # Point to the batch data directory for manifest files
        config.data_dir = Path('tests/fixtures/batch_data/valid_batch')
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_from_valid_manifest(self, mock_generator, processor):
        """Test processing from valid manifest file"""
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        manifest_path = Path('tests/fixtures/manifests/valid_manifest.csv')
        results = processor.process_from_manifest(manifest_path)
        
        analysis = assert_batch_results(results, min_successful=3)
        assert len(results) == 3
        
        # Verify patient information was used from manifest
        for result in analysis['successful']:
            assert result['patient_name'] in ['Thunder', 'Montana', 'Lightning']
    
    @patch('src.batch_processor.ReportGenerator')
    def test_process_from_manifest_with_progress(self, mock_generator, processor):
        """Test manifest processing with progress callback"""
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        progress_callback = MockProgressCallback()
        manifest_path = Path('tests/fixtures/manifests/valid_manifest.csv')
        
        results = processor.process_from_manifest(
            manifest_path,
            progress_callback=progress_callback
        )
        
        progress_callback.assert_called()
        progress_callback.assert_completed()
        assert len(results) > 0
    
    @patch('src.batch_processor.ReportGenerator')  
    def test_process_from_manifest_error_handling(self, mock_generator, processor):
        """Test manifest processing error handling"""
        # Mock exception during report generation
        mock_instance = MagicMock()
        mock_instance.generate_report.side_effect = Exception("Test error")
        mock_generator.return_value = mock_instance
        
        manifest_path = Path('tests/fixtures/manifests/valid_manifest.csv')
        results = processor.process_from_manifest(manifest_path)
        
        # All should fail but not crash the processor
        assert len(results) == 3
        for result in results:
            assert result['success'] is False
            assert 'error' in result
    
    def test_manifest_patient_info_extraction(self, processor):
        """Test patient information extraction from manifest"""
        manifest_path = Path('tests/fixtures/manifests/valid_manifest.csv')
        manifest_df = pd.read_csv(manifest_path)
        
        # Verify manifest structure
        assert 'csv_file' in manifest_df.columns
        assert 'patient_name' in manifest_df.columns
        assert 'species' in manifest_df.columns
        
        # Verify data content
        first_row = manifest_df.iloc[0]
        assert first_row['patient_name'] == 'Thunder'
        assert first_row['species'] == 'Horse'
        assert first_row['sample_number'] == '506-A'


class TestPerformanceAndScaling:
    """Test performance and scaling functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration for performance testing"""
        config = create_temp_batch_config(
            parallel_processing=True,
            max_workers=2
        )
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    @patch('src.batch_processor.ReportGenerator')
    def test_large_batch_performance(self, mock_generator, processor):
        """Test performance with large number of files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_count = 12
            create_large_batch_files(temp_path, count=file_count)
            processor.config.data_dir = temp_path
            
            # Mock fast report generation
            mock_instance = MagicMock()
            mock_instance.generate_report.return_value = True
            mock_generator.return_value = mock_instance
            
            start_time = time.time()
            results = processor.process_directory(validate=False)
            processing_time = time.time() - start_time
            
            assert len(results) == file_count
            # Should complete reasonably quickly (adjust threshold as needed)
            assert processing_time < 10.0  # 10 seconds max for 12 files
            
            analysis = assert_batch_results(results, min_successful=file_count)
            assert analysis['success_rate'] == 1.0
    
    @patch('src.batch_processor.ReportGenerator')
    def test_resource_usage_monitoring(self, mock_generator, processor):
        """Test system resource usage during batch processing"""
        import psutil
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            create_large_batch_files(temp_path, count=8)
            processor.config.data_dir = temp_path
            
            mock_instance = MagicMock()
            mock_instance.generate_report.return_value = True
            mock_generator.return_value = mock_instance
            
            # Monitor memory before processing
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            results = processor.process_directory(validate=False)
            
            # Monitor memory after processing
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 100MB for test data)
            assert memory_increase < 100 * 1024 * 1024  # 100MB threshold
            assert len(results) == 8
    
    def test_concurrent_batch_safety(self, processor):
        """Test multiple batch processors can run safely"""
        def run_batch_process(proc, directory):
            """Helper function to run batch processing"""
            proc.config.data_dir = directory
            return proc.process_directory(validate=False)
        
        # Create multiple temp directories with data
        temp_dirs = []
        try:
            for i in range(3):
                temp_dir = tempfile.mkdtemp()
                temp_path = Path(temp_dir)
                create_large_batch_files(temp_path, count=3)
                temp_dirs.append(temp_path)
            
            # Create multiple processors
            processors = [
                BatchProcessor(create_temp_batch_config()) 
                for _ in range(3)
            ]
            
            # Run concurrent processing
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(run_batch_process, proc, directory)
                    for proc, directory in zip(processors, temp_dirs)
                ]
                
                results_list = [future.result() for future in futures]
            
            # Verify all processes completed successfully
            for results in results_list:
                assert len(results) == 3
                
        finally:
            # Cleanup temp directories
            cleanup_temp_directories(*temp_dirs)


class TestSummaryAndReporting:
    """Test summary generation and reporting functionality"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration"""
        config = create_temp_batch_config()
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    def test_generate_summary_report_empty(self, processor):
        """Test summary generation with no results"""
        summary = processor.generate_summary_report()
        assert summary == {}
    
    @patch('src.batch_processor.ReportGenerator')
    def test_generate_summary_report_with_results(self, mock_generator, processor):
        """Test summary generation with processing results"""
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        # Process some files to generate results
        results = processor.process_directory(validate=False)
        summary = processor.generate_summary_report()
        
        assert 'timestamp' in summary
        assert 'total_files' in summary
        assert 'successful' in summary
        assert 'failed' in summary
        assert 'success_rate' in summary
        assert 'total_processing_time' in summary
        assert 'average_processing_time' in summary
        assert 'configuration' in summary
        
        assert summary['total_files'] == len(results)
        assert summary['success_rate'] >= 0
        assert summary['success_rate'] <= 100
    
    @patch('src.batch_processor.ReportGenerator')
    def test_generate_summary_with_failures(self, mock_generator, processor):
        """Test summary generation with some failures"""
        # Mock mixed success/failure
        mock_instance = MagicMock()
        call_count = [0]
        def mixed_results(*args, **kwargs):
            call_count[0] += 1
            return call_count[0] % 2 == 1  # Alternate success/failure
        mock_instance.generate_report.side_effect = mixed_results
        mock_generator.return_value = mock_instance
        
        results = processor.process_directory(validate=False)
        summary = processor.generate_summary_report()
        
        assert summary['failed'] > 0
        assert 'failure_reasons' in summary
        assert isinstance(summary['failure_reasons'], dict)
    
    def test_save_results_to_csv(self, processor):
        """Test saving results to CSV file"""
        # Add some mock results
        processor.results = [
            {
                'csv_file': 'test1.csv',
                'success': True,
                'processing_time': 1.5,
                'message': 'Success'
            },
            {
                'csv_file': 'test2.csv', 
                'success': False,
                'processing_time': 0.8,
                'message': 'Failed'
            }
        ]
        
        output_path = processor.save_results_to_csv()
        
        assert output_path.exists()
        assert output_path.suffix == '.csv'
        assert 'batch_report_' in output_path.name
        
        # Verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert 'csv_file' in df.columns
        assert 'success' in df.columns
        assert 'processing_time' in df.columns
    
    def test_save_results_to_custom_path(self, processor):
        """Test saving results to custom path"""
        processor.results = [{'csv_file': 'test.csv', 'success': True}]
        
        custom_path = processor.config.reports_dir / 'custom_report.csv'
        output_path = processor.save_results_to_csv(custom_path)
        
        assert output_path == custom_path
        assert output_path.exists()


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration"""
        config = create_temp_batch_config()
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    def test_individual_file_failure_isolation(self, processor):
        """Test that individual file failures don't break batch processing"""
        processor.config.data_dir = Path('tests/fixtures/batch_data/mixed_quality')
        
        # Process with validation to ensure some failures
        results = processor.process_directory(validate=True)
        
        # Should have both successful and failed results
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        assert len(successful) > 0  # Some should succeed
        assert len(failed) > 0      # Some should fail
        assert len(results) == len(successful) + len(failed)
    
    def test_error_message_clarity(self, processor):
        """Test that error messages are clear and helpful"""
        # Test with invalid file
        csv_path = Path('tests/fixtures/batch_data/mixed_quality/invalid_sample.csv')
        result = processor.process_single_file(csv_path, validate=True)
        
        assert result['success'] is False
        assert len(result['message']) > 10  # Should have meaningful message
        assert 'Validation failed' in result['message']
    
    @patch('src.batch_processor.ReportGenerator')
    def test_batch_continuation_after_errors(self, mock_generator, processor):
        """Test batch continuation after individual errors"""
        # Mock alternating success/exception
        mock_instance = MagicMock()
        call_count = [0]
        def alternating_error(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise Exception("Simulated error")
            return True
        mock_instance.generate_report.side_effect = alternating_error
        mock_generator.return_value = mock_instance
        
        results = processor.process_directory(validate=False)
        
        # Should have processed all files despite errors
        assert len(results) == 3  # Number of files in valid_batch
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        assert len(successful) > 0
        assert len(failed) > 0
        assert len(successful) + len(failed) == len(results)


# Integration test to verify overall functionality
class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""
    
    @pytest.fixture
    def batch_config(self):
        """Create test batch configuration"""
        config = create_temp_batch_config()
        yield config
        cleanup_temp_directories(config.reports_dir.parent)
    
    @pytest.fixture
    def processor(self, batch_config):
        """Create test batch processor"""
        batch_config.ensure_directories()
        return BatchProcessor(batch_config)
    
    @patch('src.batch_processor.ReportGenerator')
    def test_end_to_end_batch_workflow(self, mock_generator, processor):
        """Test complete end-to-end batch processing workflow"""
        mock_instance = MagicMock()
        mock_instance.generate_report.return_value = True
        mock_generator.return_value = mock_instance
        
        progress_callback = MockProgressCallback()
        
        # Process directory with progress tracking
        results = processor.process_directory(
            progress_callback=progress_callback,
            validate=True
        )
        
        # Verify processing completed
        assert len(results) > 0
        progress_callback.assert_called()
        progress_callback.assert_completed()
        
        # Generate summary
        summary = processor.generate_summary_report()
        assert summary['total_files'] == len(results)
        
        # Save results
        csv_path = processor.save_results_to_csv()
        assert csv_path.exists()
        
        # Verify report directory was created
        assert processor.config.reports_dir.exists()
    
    @patch('src.batch_processor.ReportGenerator')
    def test_production_simulation(self, mock_generator, processor):
        """Test simulation of production batch processing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create realistic batch size
            create_large_batch_files(temp_path, count=20)
            processor.config.data_dir = temp_path
            processor.config.parallel_processing = True
            processor.config.max_workers = 4
            
            mock_instance = MagicMock()
            mock_instance.generate_report.return_value = True
            mock_generator.return_value = mock_instance
            
            start_time = time.time()
            results = processor.process_directory(validate=True)
            total_time = time.time() - start_time
            
            # Verify performance metrics
            assert len(results) == 20
            assert total_time < 30  # Should complete within 30 seconds
            
            summary = processor.generate_summary_report()
            assert summary['success_rate'] > 90  # High success rate expected