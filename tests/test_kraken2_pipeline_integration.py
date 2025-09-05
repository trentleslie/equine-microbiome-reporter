"""
TDD Phase 2: Pipeline Integration Tests

Tests for integrating Kraken2 classifier with existing MicrobiomePipelineIntegrator.
These tests follow RED-GREEN-REFACTOR methodology for pipeline modifications.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import pandas as pd
import os
from pathlib import Path
import tempfile

# Import existing pipeline components for integration
try:
    from src.pipeline_integrator import MicrobiomePipelineIntegrator
    from src.data_models import PatientInfo
    from src.kraken2_classifier import Kraken2FallbackManager, Kraken2Classifier
except ImportError:
    # Expected during RED phase - some integration points may not exist yet
    pass


class TestPipelineIntegratorKraken2Selection:
    """
    TDD Phase 2 RED: Test pipeline integrator Kraken2 selection logic.
    These tests should FAIL initially until integration is implemented.
    """
    
    @patch.dict('os.environ', {'USE_KRAKEN2': 'true', 'KRAKEN2_DB_PATH': '/test/kraken2/db'})
    def test_pipeline_integrator_kraken2_enabled_via_environment(self):
        """RED: Test pipeline uses Kraken2 when enabled via environment"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Act - create integrator with environment configuration
        integrator = MicrobiomePipelineIntegrator()
        
        # Assert - should detect Kraken2 configuration
        assert hasattr(integrator, 'use_kraken2')
        assert integrator.use_kraken2 is True
        assert hasattr(integrator, 'kraken2_db_path')
        assert integrator.kraken2_db_path == '/test/kraken2/db'
    
    @patch.dict('os.environ', {'USE_KRAKEN2': 'false'})
    def test_pipeline_integrator_kraken2_disabled_via_environment(self):
        """RED: Test pipeline uses existing converter when Kraken2 disabled"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Act
        integrator = MicrobiomePipelineIntegrator()
        
        # Assert
        assert integrator.use_kraken2 is False
    
    def test_pipeline_integrator_kraken2_auto_detection(self):
        """RED: Test automatic detection of Kraken2 availability"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Mock Kraken2 database detection
        with patch('src.kraken2_classifier.Kraken2Classifier') as mock_classifier:
            mock_instance = Mock()
            mock_instance.validate_database.return_value = True
            mock_classifier.return_value = mock_instance
            
            # Act
            integrator = MicrobiomePipelineIntegrator(auto_detect_kraken2=True)
            
            # Assert
            assert integrator.kraken2_available is True
    
    def test_pipeline_integrator_explicit_kraken2_configuration(self):
        """RED: Test explicit Kraken2 configuration override"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Act
        integrator = MicrobiomePipelineIntegrator(
            kraken2_db_path="/custom/db/path",
            use_kraken2=True
        )
        
        # Assert
        assert integrator.use_kraken2 is True  
        assert integrator.kraken2_db_path == "/custom/db/path"


class TestPipelineIntegratorFallbackLogic:
    """
    TDD Phase 2 RED: Test fallback logic between Kraken2 and existing pipeline.
    """
    
    @patch('src.kraken2_classifier.Kraken2FallbackManager')
    def test_fallback_logic_kraken2_success(self, mock_fallback_manager_class):
        """RED: Test successful Kraken2 processing in pipeline"""
        # Arrange - mock successful Kraken2 processing
        mock_manager = Mock()
        mock_df = pd.DataFrame({
            'species': ['E. coli', 'L. acidophilus'],
            'barcode59': [1500, 2000],
            'phylum': ['Pseudomonadota', 'Bacillota'],
            'genus': ['Escherichia', 'Lactobacillus']
        })
        mock_manager.process_fastq.return_value = mock_df
        mock_fallback_manager_class.return_value = mock_manager
        
        # Act
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        integrator = MicrobiomePipelineIntegrator(use_kraken2=True)
        
        result = integrator.process_sample(
            fastq_file="test.fastq",
            patient_info={'name': 'Test Horse'},
            run_qc=False,
            generate_pdf=False
        )
        
        # Assert
        assert 'kraken2_used' in result
        assert result['kraken2_used'] is True
        assert 'csv_path' in result
    
    @patch('src.kraken2_classifier.Kraken2FallbackManager')
    @patch('src.fastq_converter.FASTQtoCSVConverter')
    def test_fallback_logic_kraken2_failure_triggers_existing_pipeline(self, 
                                                                      mock_converter_class,
                                                                      mock_fallback_manager_class):
        """RED: Test fallback to existing pipeline when Kraken2 fails"""
        # Arrange - Kraken2 fails, existing pipeline succeeds
        mock_manager = Mock()
        mock_manager.process_fastq.side_effect = RuntimeError("Kraken2 database error")
        mock_fallback_manager_class.return_value = mock_manager
        
        mock_converter = Mock()
        mock_fallback_df = pd.DataFrame({'species': ['Fallback result'], 'barcode59': [100]})
        mock_converter.process_fastq_files.return_value = mock_fallback_df
        mock_converter_class.return_value = mock_converter
        
        # Act
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        integrator = MicrobiomePipelineIntegrator(use_kraken2=True)
        
        result = integrator.process_sample(
            fastq_file="test.fastq",
            patient_info={'name': 'Test Horse'},
            run_qc=False,
            generate_pdf=False
        )
        
        # Assert - should use fallback
        assert 'kraken2_used' in result
        assert result['kraken2_used'] is False
        assert 'fallback_reason' in result
    
    def test_fallback_logic_performance_monitoring(self):
        """RED: Test performance monitoring during classification selection"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        with patch('time.time', side_effect=[0, 10, 20, 30]):  # Mock timing
            integrator = MicrobiomePipelineIntegrator(use_kraken2=True)
            
            # Mock processing
            with patch.object(integrator, '_process_with_kraken2', return_value={'test': 'result'}):
                result = integrator.process_sample(
                    fastq_file="test.fastq",
                    patient_info={'name': 'Test'},
                    run_qc=False,
                    generate_pdf=False
                )
            
            # Assert timing information is captured
            assert 'processing_time_seconds' in result
            assert 'classification_method' in result


class TestEnvironmentConfigurationLoading:
    """
    TDD Phase 2 RED: Test loading configuration from environment variables.
    """
    
    @patch.dict('os.environ', {
        'KRAKEN2_DB_PATH': '/env/kraken2/db',
        'KRAKEN2_THREADS': '8', 
        'KRAKEN2_CONFIDENCE': '0.2',
        'USE_KRAKEN2': 'true'
    })
    def test_comprehensive_environment_configuration_loading(self):
        """RED: Test loading all Kraken2 config from environment"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Act
        integrator = MicrobiomePipelineIntegrator.from_environment()
        
        # Assert
        assert integrator.kraken2_db_path == '/env/kraken2/db'
        assert integrator.kraken2_threads == 8
        assert integrator.kraken2_confidence == 0.2
        assert integrator.use_kraken2 is True
    
    @patch.dict('os.environ', {}, clear=True)
    def test_environment_configuration_with_defaults(self):
        """RED: Test fallback to defaults when environment not set"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Act
        integrator = MicrobiomePipelineIntegrator.from_environment()
        
        # Assert defaults are used
        assert integrator.use_kraken2 is False  # Default to existing pipeline
        assert hasattr(integrator, 'kraken2_threads')
        assert integrator.kraken2_threads == 4  # Default threads
    
    def test_environment_configuration_validation(self):
        """RED: Test validation of environment configuration"""
        with patch.dict('os.environ', {'KRAKEN2_THREADS': 'invalid_number'}):
            from src.pipeline_integrator import MicrobiomePipelineIntegrator
            
            # Should handle invalid environment values gracefully
            integrator = MicrobiomePipelineIntegrator.from_environment()
            assert isinstance(integrator.kraken2_threads, int)


class TestEndToEndFastqToCsv:
    """
    TDD Phase 2 RED: Test complete FASTQ to CSV workflow with Kraken2 integration.
    """
    
    @patch('src.kraken2_classifier.Kraken2FallbackManager')
    def test_end_to_end_fastq_to_csv_kraken2_workflow(self, mock_fallback_manager_class):
        """RED: Test complete workflow from FASTQ input to CSV output via Kraken2"""
        # Arrange - mock Kraken2 processing
        mock_manager = Mock()
        expected_csv_data = pd.DataFrame({
            'species': ['Lactobacillus acidophilus', 'Bacteroides fragilis'],
            'barcode59': [2000, 1500],
            'phylum': ['Bacillota', 'Bacteroidota'], 
            'genus': ['Lactobacillus', 'Bacteroides']
        })
        mock_manager.process_fastq.return_value = expected_csv_data
        mock_fallback_manager_class.return_value = mock_manager
        
        # Act
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        integrator = MicrobiomePipelineIntegrator(use_kraken2=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock FASTQ file
            fastq_path = Path(temp_dir) / "test.fastq"
            fastq_path.write_text("@seq1\nATCG\n+\nIIII\n")
            
            result = integrator.process_sample(
                fastq_file=str(fastq_path),
                patient_info={'name': 'Test Patient', 'sample_number': '59'},
                run_qc=False,
                generate_pdf=False
            )
        
        # Assert
        assert 'csv_path' in result
        assert result['kraken2_used'] is True
        
        # Verify CSV content matches expected format
        if 'csv_path' in result:
            saved_df = pd.read_csv(result['csv_path'])
            assert 'species' in saved_df.columns
            assert 'barcode59' in saved_df.columns
            assert 'phylum' in saved_df.columns
            assert 'genus' in saved_df.columns
    
    @patch('src.fastq_qc.FASTQQualityControl')
    @patch('src.kraken2_classifier.Kraken2FallbackManager')
    def test_end_to_end_with_quality_control_integration(self, 
                                                        mock_fallback_manager_class,
                                                        mock_qc_class):
        """RED: Test workflow includes QC when requested with Kraken2"""
        # Arrange
        mock_qc = Mock()
        mock_qc.run_qc.return_value = {'mean_quality': 30}
        mock_qc.get_qc_summary.return_value = {'mean_quality': 30, 'total_reads': 1000}
        mock_qc_class.return_value = mock_qc
        
        mock_manager = Mock()
        mock_manager.process_fastq.return_value = pd.DataFrame({'species': ['Test'], 'barcode59': [100]})
        mock_fallback_manager_class.return_value = mock_manager
        
        # Act
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        integrator = MicrobiomePipelineIntegrator(use_kraken2=True)
        
        result = integrator.process_sample(
            fastq_file="test.fastq",
            patient_info={'name': 'Test'},
            run_qc=True,  # Enable QC
            generate_pdf=False
        )
        
        # Assert QC integration
        assert 'qc_summary' in result
        assert result['qc_summary']['mean_quality'] == 30
    
    def test_csv_format_compatibility_validation(self):
        """RED: Test that Kraken2 output exactly matches existing CSV format"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Create test data in both formats
        kraken2_format = pd.DataFrame({
            'species': ['Lactobacillus acidophilus'],
            'barcode45': [150],
            'phylum': ['Bacillota'],
            'genus': ['Lactobacillus']
        })
        
        # Validate format compatibility
        integrator = MicrobiomePipelineIntegrator()
        is_compatible = integrator._validate_csv_format_compatibility(kraken2_format)
        
        assert is_compatible is True
        assert list(kraken2_format.columns) == ['species', 'barcode45', 'phylum', 'genus']


class TestKraken2IntegrationConfiguration:
    """
    TDD Phase 2 RED: Test configuration and setup of Kraken2 integration.
    """
    
    def test_kraken2_integration_disabled_by_default(self):
        """RED: Test Kraken2 is disabled by default (safe fallback)"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        integrator = MicrobiomePipelineIntegrator()
        
        # By default, should use existing pipeline for safety
        assert integrator.use_kraken2 is False
    
    def test_kraken2_integration_database_path_validation(self):
        """RED: Test database path validation during setup"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        # Test with valid path
        with patch('pathlib.Path.exists', return_value=True):
            integrator = MicrobiomePipelineIntegrator(
                kraken2_db_path="/valid/db/path",
                use_kraken2=True
            )
            assert integrator.kraken2_db_path == "/valid/db/path"
        
        # Test with invalid path - should disable Kraken2
        with patch('pathlib.Path.exists', return_value=False):
            integrator = MicrobiomePipelineIntegrator(
                kraken2_db_path="/invalid/db/path", 
                use_kraken2=True
            )
            # Should fall back to existing pipeline
            assert integrator.use_kraken2 is False
    
    def test_kraken2_integration_thread_configuration(self):
        """RED: Test thread configuration for Kraken2"""
        from src.pipeline_integrator import MicrobiomePipelineIntegrator
        
        integrator = MicrobiomePipelineIntegrator(
            use_kraken2=True,
            kraken2_threads=16
        )
        
        assert integrator.kraken2_threads == 16


# TDD Phase 2 RED Complete
# These integration tests should FAIL until pipeline_integrator.py is modified
# Next: Implement the integration functionality (GREEN phase)