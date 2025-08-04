"""
Comprehensive test suite for FASTQ-to-PDF pipeline components
Following TDD approach with concrete test assertions
"""

import pytest
import pandas as pd
import zipfile
import gzip
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from src.fastq_to_pdf_pipeline import (
    FASTQExtractionService,
    StructuralValidationService,
    TaxonomicValidationService,
    PerformanceBenchmarkService,
    BatchPipelineOrchestrator,
    PipelineConfig,
    ValidationResult,
    ReportResult,
    ProcessingResult,
    PipelineResult,
    FASTQProcessingError,
    CSVValidationError,
    PerformanceError
)
from src.data_models import PatientInfo


class TestFASTQExtractionService:
    """Test suite for FASTQ file extraction and validation"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_zip_with_barcodes(self, temp_dir):
        """Create sample zip with barcode directories and FASTQ files"""
        zip_path = Path(temp_dir) / "test_barcodes.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Create barcode directories with FASTQ files
            for barcode in ['04', '05', '06']:
                barcode_dir = f"barcode{barcode}"
                
                # Create sample FASTQ content
                fastq_content = "@read1\nACGTACGT\n+\nIIIIIIII\n@read2\nTGCATGCA\n+\nHHHHHHHH\n"
                
                # Add multiple FASTQ files per barcode
                for i in range(3):
                    file_path = f"{barcode_dir}/sample_{i}.fastq"
                    zf.writestr(file_path, fastq_content)
                    
                    # Also add gzipped version
                    gz_content = gzip.compress(fastq_content.encode())
                    gz_path = f"{barcode_dir}/sample_{i}.fastq.gz"
                    zf.writestr(gz_path, gz_content)
        
        return str(zip_path)
    
    @pytest.fixture
    def corrupted_zip(self, temp_dir):
        """Create corrupted zip file for error testing"""
        zip_path = Path(temp_dir) / "corrupted.zip"
        # Write invalid zip content
        with open(zip_path, 'w') as f:
            f.write("This is not a valid zip file")
        return str(zip_path)
    
    def test_extract_zip_with_multiple_barcodes(self, sample_zip_with_barcodes, temp_dir):
        """Test: Extract zip file and verify directory structure"""
        service = FASTQExtractionService()
        extract_dir = Path(temp_dir) / "extracted"
        
        result = service.extract_and_organize(sample_zip_with_barcodes, str(extract_dir))
        
        # Concrete assertions
        assert isinstance(result, dict)
        assert "04" in result
        assert "05" in result  
        assert "06" in result
        
        # Verify each barcode has FASTQ files
        for barcode in ["04", "05", "06"]:
            assert len(result[barcode]) > 0, f"No FASTQ files found for barcode {barcode}"
            
            # Verify files exist and are readable
            for file_path in result[barcode]:
                assert Path(file_path).exists(), f"FASTQ file does not exist: {file_path}"
                assert Path(file_path).suffix in ['.fastq', '.gz'], f"Invalid file extension: {file_path}"
        
        # Verify files are sorted
        for barcode, files in result.items():
            assert files == sorted(files), f"Files not sorted for barcode {barcode}"
    
    def test_handle_corrupted_zip_file(self, corrupted_zip, temp_dir):
        """Test: Proper exception handling for corrupted zip files"""
        service = FASTQExtractionService()
        
        with pytest.raises(zipfile.BadZipFile, match="Invalid or corrupted zip file"):
            service.extract_and_organize(corrupted_zip, temp_dir)
    
    def test_handle_missing_zip_file(self, temp_dir):
        """Test: Handle non-existent zip files"""
        service = FASTQExtractionService()
        
        with pytest.raises(FileNotFoundError):
            service.extract_and_organize("/nonexistent/file.zip", temp_dir)
    
    def test_validate_fastq_structure_valid_files(self, temp_dir):
        """Test: FASTQ format validation with valid files"""
        service = FASTQExtractionService()
        
        # Create valid FASTQ file
        valid_fastq = Path(temp_dir) / "valid.fastq"
        fastq_content = "@read1\nACGTACGTNNN\n+\nIIIIIIIIIII\n@read2\nTGCATGCA\n+\nHHHHHHHH\n"
        
        with open(valid_fastq, 'w') as f:
            f.write(fastq_content)
        
        # Should pass validation
        assert service.validate_fastq_structure([str(valid_fastq)]) == True
    
    def test_validate_fastq_structure_invalid_header(self, temp_dir):
        """Test: FASTQ validation fails with invalid header"""
        service = FASTQExtractionService()
        
        # Create invalid FASTQ file (missing @ in header)
        invalid_fastq = Path(temp_dir) / "invalid.fastq"
        invalid_content = "read1\nACGTACGT\n+\nIIIIIIII\n"
        
        with open(invalid_fastq, 'w') as f:
            f.write(invalid_content)
        
        with pytest.raises(ValueError, match="Invalid FASTQ format: line 1 should start with @"):
            service.validate_fastq_structure([str(invalid_fastq)])
    
    def test_validate_fastq_structure_gzipped_files(self, temp_dir):
        """Test: FASTQ validation works with gzipped files"""
        service = FASTQExtractionService()
        
        # Create valid gzipped FASTQ file
        gz_fastq = Path(temp_dir) / "valid.fastq.gz"
        fastq_content = "@read1\nACGTACGT\n+\nIIIIIIII\n@read2\nTGCATGCA\n+\nHHHHHHHH\n"
        
        with gzip.open(gz_fastq, 'wt') as f:
            f.write(fastq_content)
        
        # Should pass validation
        assert service.validate_fastq_structure([str(gz_fastq)]) == True
    
    def test_handle_empty_zip(self, temp_dir):
        """Test: Handle zip with no barcode directories"""
        service = FASTQExtractionService()
        
        # Create empty zip
        empty_zip = Path(temp_dir) / "empty.zip"
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            zf.writestr("readme.txt", "No barcode directories here")
        
        with pytest.raises(FASTQProcessingError, match="No barcode directories with FASTQ files found"):
            service.extract_and_organize(str(empty_zip), temp_dir)


class TestStructuralValidationService:
    """Test suite for CSV structural validation"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def reference_csv_mock(self, temp_dir):
        """Create mock reference CSV with expected structure"""
        ref_csv = Path(temp_dir) / "reference.csv"
        ref_data = {
            'species': ['Bacteria A', 'Bacteria B'],
            'barcode04': [100, 200],
            'barcode05': [150, 250],
            'barcode06': [75, 125],
            'total': [325, 575],
            'superkingdom': ['Bacteria', 'Bacteria'],
            'kingdom': ['Bacteria_none', 'Bacteria_none'],
            'phylum': ['Actinomycetota', 'Bacillota'],
            'class': ['Actinomycetes', 'Bacilli'],
            'order': ['Kitasatosporales', 'Lactobacillales'],
            'family': ['Streptomycetaceae', 'Lactobacillaceae'],
            'genus': ['Streptomyces', 'Lactobacillus'],
            'tax': ['Bacteria', 'Bacteria']
        }
        
        pd.DataFrame(ref_data).to_csv(ref_csv, index=False)
        return str(ref_csv)
    
    def test_validate_csv_structure_exact_match(self, reference_csv_mock, temp_dir):
        """Test: Generated CSV matches reference structure exactly"""
        service = StructuralValidationService(reference_csv_mock)
        
        # Create test CSV with correct structure
        test_csv = Path(temp_dir) / "test.csv"
        ref_df = pd.read_csv(reference_csv_mock)
        test_df = ref_df.head(1)  # Subset for testing
        test_df.to_csv(test_csv, index=False)
        
        result = service.validate_structure(str(test_csv))
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.column_count_match == True
        assert result.required_columns_present == True
    
    def test_detect_missing_required_columns(self, temp_dir):
        """Test: Identify specific missing columns"""
        service = StructuralValidationService()
        
        # Create CSV missing required columns
        test_csv = Path(temp_dir) / "incomplete.csv"
        incomplete_df = pd.DataFrame({
            'species': ['Bacteria A', 'Bacteria B'],
            'barcode04': [100, 200]
            # Missing: phylum, genus, total
        })
        incomplete_df.to_csv(test_csv, index=False)
        
        result = service.validate_structure(str(test_csv))
        
        assert result.is_valid == False
        assert 'phylum' in result.missing_columns
        assert 'genus' in result.missing_columns
        assert 'total' in result.missing_columns
        assert len(result.errors) > 0
        assert "Missing required columns" in result.errors[0]
    
    def test_detect_missing_barcode_columns(self, temp_dir):
        """Test: Detect when no barcode columns present"""
        service = StructuralValidationService()
        
        # Create CSV with no barcode columns
        test_csv = Path(temp_dir) / "no_barcodes.csv"
        df = pd.DataFrame({
            'species': ['Bacteria A'],
            'total': [100],
            'phylum': ['Actinomycetota'],
            'genus': ['Streptomyces']
        })
        df.to_csv(test_csv, index=False)
        
        result = service.validate_structure(str(test_csv))
        
        assert result.is_valid == False
        assert "No barcode columns found" in result.errors
    
    def test_dynamic_barcode_detection(self, temp_dir):
        """Test: Handle variable number of barcode columns"""
        service = StructuralValidationService()
        
        # CSV with different barcode pattern
        test_csv = Path(temp_dir) / "dynamic_barcodes.csv"
        df = pd.DataFrame({
            'species': ['Bacteria A'],
            'barcode01': [50],
            'barcode02': [75], 
            'barcode03': [100],
            'total': [225],
            'phylum': ['Actinomycetota'],
            'genus': ['Streptomyces']
        })
        df.to_csv(test_csv, index=False)
        
        detected_barcodes = service.detect_barcode_columns(str(test_csv))
        
        assert detected_barcodes == ['barcode01', 'barcode02', 'barcode03']
        assert len(detected_barcodes) == 3
    
    def test_handle_malformed_csv(self, temp_dir):
        """Test: Handle CSV parsing errors"""
        service = StructuralValidationService()
        
        # Create malformed CSV
        bad_csv = Path(temp_dir) / "malformed.csv"
        with open(bad_csv, 'w') as f:
            f.write("incomplete,csv\nrow1,\nrow2,extra,columns\n")
        
        result = service.validate_structure(str(bad_csv))
        
        assert result.is_valid == False
        assert len(result.errors) > 0
        assert "CSV parsing error" in result.errors[0]


class TestTaxonomicValidationService:
    """Test suite for taxonomic data validation"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_validate_gtdb_nomenclature_modern_names(self, temp_dir):
        """Test: Accept modern GTDB phylum names"""
        service = TaxonomicValidationService()
        
        # CSV with modern GTDB names
        valid_csv = Path(temp_dir) / "gtdb_valid.csv"
        valid_df = pd.DataFrame({
            'species': ['Streptomyces albidoflavus', 'Lactobacillus acidophilus'],
            'phylum': ['Actinomycetota', 'Bacillota'],  # Modern GTDB names
            'genus': ['Streptomyces', 'Lactobacillus']
        })
        valid_df.to_csv(valid_csv, index=False)
        
        result = service.validate_taxonomic_data(str(valid_csv))
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert len(result.outdated_names) == 0
    
    def test_detect_outdated_phylum_names(self, temp_dir):
        """Test: Detect and suggest replacements for outdated names"""
        service = TaxonomicValidationService()
        
        # CSV with outdated names
        invalid_csv = Path(temp_dir) / "gtdb_invalid.csv"
        invalid_df = pd.DataFrame({
            'species': ['Streptomyces albidoflavus', 'Lactobacillus acidophilus'],
            'phylum': ['Actinobacteria', 'Firmicutes'],  # Outdated names
            'genus': ['Streptomyces', 'Lactobacillus']
        })
        invalid_df.to_csv(invalid_csv, index=False)
        
        result = service.validate_taxonomic_data(str(invalid_csv))
        
        assert result.is_valid == True  # Warnings, not errors
        assert len(result.warnings) == 2
        assert 'Actinobacteria' in result.outdated_names
        assert 'Firmicutes' in result.outdated_names
        assert result.suggested_replacements['Actinobacteria'] == 'Actinomycetota'
        assert result.suggested_replacements['Firmicutes'] == 'Bacillota'
    
    def test_validate_species_name_format(self, temp_dir):
        """Test: Check scientific name format for species"""
        service = TaxonomicValidationService()
        
        # CSV with poorly formatted species names
        test_csv = Path(temp_dir) / "bad_species.csv"
        test_df = pd.DataFrame({
            'species': ['bacteria', 'E.coli', 'Streptomyces albidoflavus', ''],  # Mix of good and bad
            'phylum': ['Actinomycetota', 'Pseudomonadota', 'Actinomycetota', 'Bacillota']
        })
        test_df.to_csv(test_csv, index=False)
        
        result = service.validate_taxonomic_data(str(test_csv))
        
        # Should generate warnings for high percentage of invalid names
        # (We have 3 out of 4 invalid names, which is > 10% threshold)
        assert len(result.warnings) > 0
        warning_text = ' '.join(result.warnings)
        assert 'scientific format' in warning_text.lower()
    
    def test_handle_missing_taxonomic_columns(self, temp_dir):
        """Test: Handle CSV without taxonomic columns"""
        service = TaxonomicValidationService()
        
        # CSV without phylum column
        test_csv = Path(temp_dir) / "no_taxonomy.csv"
        test_df = pd.DataFrame({
            'species': ['Bacteria A'],
            'barcode04': [100]
        })
        test_df.to_csv(test_csv, index=False)
        
        result = service.validate_taxonomic_data(str(test_csv))
        
        # Should still be valid, just no taxonomic checks performed
        assert result.is_valid == True
        assert len(result.warnings) == 0


class TestPerformanceBenchmarkService:
    """Test suite for performance monitoring and benchmarks"""
    
    def test_benchmark_within_limits(self):
        """Test: Accept performance within benchmark limits"""
        service = PerformanceBenchmarkService(enable_benchmarks=True)
        
        # Should not raise exception for acceptable performance
        service.benchmark_pipeline_stage('fastq_extraction', 120.0, 1000.0)  # 2 min, 1GB
    
    def test_benchmark_time_limit_exceeded(self):
        """Test: Raise exception when time limit exceeded"""
        service = PerformanceBenchmarkService(enable_benchmarks=True)
        
        with pytest.raises(PerformanceError, match="exceeded time limit"):
            service.benchmark_pipeline_stage('fastq_extraction', 400.0)  # 6.7 min > 5 min limit
    
    def test_benchmark_memory_limit_exceeded(self):
        """Test: Raise exception when memory limit exceeded"""
        service = PerformanceBenchmarkService(enable_benchmarks=True)
        
        with pytest.raises(PerformanceError, match="exceeded memory limit"):
            service.benchmark_pipeline_stage('csv_generation', 300.0, 5000.0)  # 5GB > 4GB limit
    
    def test_benchmarks_disabled(self):
        """Test: No exceptions when benchmarks disabled"""
        service = PerformanceBenchmarkService(enable_benchmarks=False)
        
        # Should not raise exception even with poor performance
        service.benchmark_pipeline_stage('fastq_extraction', 1000.0, 10000.0)
    
    def test_unknown_stage_ignored(self):
        """Test: Unknown benchmark stages are ignored"""
        service = PerformanceBenchmarkService(enable_benchmarks=True)
        
        # Should not raise exception for unknown stage
        service.benchmark_pipeline_stage('unknown_stage', 1000.0, 10000.0)


class TestBatchPipelineOrchestrator:
    """Test suite for complete pipeline orchestration"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def pipeline_config(self, temp_dir):
        """Create test pipeline configuration"""
        # Create mock reference CSV
        ref_csv = Path(temp_dir) / "reference.csv"
        ref_data = {
            'species': ['Test Species'],
            'barcode04': [100],
            'total': [100],
            'phylum': ['Actinomycetota'],
            'genus': ['TestGenus']
        }
        pd.DataFrame(ref_data).to_csv(ref_csv, index=False)
        
        return PipelineConfig(
            fastq_zip_path="test.zip",  # Will be mocked
            reference_csv=str(ref_csv),
            output_dir=str(Path(temp_dir) / "output"),
            temp_dir=str(Path(temp_dir) / "temp")
        )
    
    def test_pipeline_initialization(self, pipeline_config):
        """Test: Pipeline initializes with correct configuration"""
        orchestrator = BatchPipelineOrchestrator(pipeline_config)
        
        assert orchestrator.config == pipeline_config
        assert orchestrator.extraction_service is not None
        assert orchestrator.structural_validator is not None
        assert orchestrator.taxonomic_validator is not None
        assert orchestrator.report_generator is not None
        
        # Output directory should be created
        assert Path(pipeline_config.output_dir).exists()
    
    @patch('src.fastq_to_pdf_pipeline.FASTQExtractionService')
    def test_process_fastq_to_csv_success(self, mock_extraction_service, pipeline_config, temp_dir):
        """Test: Successful FASTQ to CSV processing"""
        # Mock the extraction service
        mock_service_instance = MagicMock()
        mock_extraction_service.return_value = mock_service_instance
        
        mock_service_instance.extract_and_organize.return_value = {
            '04': ['file1.fastq', 'file2.fastq'],
            '05': ['file3.fastq'],
            '06': ['file4.fastq', 'file5.fastq']
        }
        mock_service_instance.validate_fastq_structure.return_value = True
        
        orchestrator = BatchPipelineOrchestrator(pipeline_config)
        output_csv = str(Path(temp_dir) / "output.csv")
        
        result = orchestrator.process_fastq_to_csv("test.zip", output_csv)
        
        assert result.success == True
        assert result.csv_path == output_csv
        assert result.barcode_count == 3
        assert result.processing_time > 0
        assert Path(output_csv).exists()
    
    def test_generate_batch_reports_success(self, pipeline_config, temp_dir):
        """Test: Successful batch report generation"""
        # Create mock CSV file
        csv_path = Path(temp_dir) / "test.csv"
        csv_data = {
            'species': ['Test Species A', 'Test Species B'],
            'barcode04': [100, 200],
            'barcode05': [150, 250],
            'total': [250, 450],
            'phylum': ['Actinomycetota', 'Bacillota'],
            'genus': ['TestGenusA', 'TestGenusB']
        }
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)
        
        patients = [
            PatientInfo(name="TestHorse1", sample_number="004"),
            PatientInfo(name="TestHorse2", sample_number="005")
        ]
        
        # Mock the report generator to avoid actual PDF generation
        with patch.object(BatchPipelineOrchestrator, 'report_generator') as mock_generator:
            mock_generator.generate_report.return_value = True
            
            orchestrator = BatchPipelineOrchestrator(pipeline_config)
            results = orchestrator.generate_batch_reports(str(csv_path), patients, temp_dir)
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].patient_name == "TestHorse1"
        assert results[1].patient_name == "TestHorse2"
    
    def test_generate_batch_reports_partial_failure(self, pipeline_config, temp_dir):
        """Test: Continue processing when one report fails"""
        # Create mock CSV
        csv_path = Path(temp_dir) / "test.csv"
        csv_data = {
            'species': ['Test Species'],
            'barcode04': [100],
            'barcode05': [150],
            'total': [250],
            'phylum': ['Actinomycetota'],
            'genus': ['TestGenus']
        }
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)
        
        patients = [
            PatientInfo(name="ValidHorse", sample_number="004"),
            PatientInfo(name="", sample_number="005"),  # Invalid - empty name
        ]
        
        # Mock report generator with selective failure
        with patch.object(BatchPipelineOrchestrator, 'report_generator') as mock_generator:
            def side_effect(*args, **kwargs):
                patient_info = args[1] if len(args) > 1 else kwargs.get('patient_info')
                return bool(patient_info.name)  # Fail if name is empty
            
            mock_generator.generate_report.side_effect = side_effect
            
            orchestrator = BatchPipelineOrchestrator(pipeline_config)
            results = orchestrator.generate_batch_reports(str(csv_path), patients, temp_dir)
        
        assert len(results) == 2
        assert results[0].success == True
        assert results[1].success == False
        assert results[0].patient_name == "ValidHorse"
        assert results[1].patient_name == ""
    
    @patch('src.fastq_to_pdf_pipeline.BatchPipelineOrchestrator.process_fastq_to_csv')
    @patch('src.fastq_to_pdf_pipeline.BatchPipelineOrchestrator.generate_batch_reports')
    def test_run_complete_pipeline_success(self, mock_generate_reports, mock_process_fastq, pipeline_config):
        """Test: Complete pipeline execution success"""
        # Mock successful FASTQ processing
        mock_process_fastq.return_value = ProcessingResult(
            success=True,
            csv_path="test.csv",
            processing_time=120.0,
            species_count=100,
            barcode_count=3
        )
        
        # Mock successful report generation
        mock_generate_reports.return_value = [
            ReportResult(success=True, pdf_path=Path("report1.pdf"), patient_name="Horse1"),
            ReportResult(success=True, pdf_path=Path("report2.pdf"), patient_name="Horse2"),
            ReportResult(success=True, pdf_path=Path("report3.pdf"), patient_name="Horse3")
        ]
        
        patients = [
            PatientInfo(name="Horse1", sample_number="004"),
            PatientInfo(name="Horse2", sample_number="005"),
            PatientInfo(name="Horse3", sample_number="006")
        ]
        
        orchestrator = BatchPipelineOrchestrator(pipeline_config)
        result = orchestrator.run_complete_pipeline(patients)
        
        assert result.success == True
        assert result.csv_generated == True
        assert len(result.report_results) == 3
        assert all(r.success for r in result.report_results)
        assert result.total_processing_time > 0
    
    @patch('src.fastq_to_pdf_pipeline.BatchPipelineOrchestrator.process_fastq_to_csv')
    def test_run_complete_pipeline_fastq_failure(self, mock_process_fastq, pipeline_config):
        """Test: Pipeline fails gracefully when FASTQ processing fails"""
        # Mock FASTQ processing failure
        mock_process_fastq.return_value = ProcessingResult(
            success=False,
            error="FASTQ extraction failed"
        )
        
        patients = [PatientInfo(name="Horse1", sample_number="004")]
        
        orchestrator = BatchPipelineOrchestrator(pipeline_config)
        result = orchestrator.run_complete_pipeline(patients)
        
        assert result.success == False
        assert result.csv_generated == False
        assert "FASTQ processing failed" in result.error
        assert result.total_processing_time > 0


class TestPublicAPI:
    """Test suite for public API functions"""
    
    def test_create_pipeline(self):
        """Test: Pipeline factory function"""
        config = PipelineConfig(fastq_zip_path="test.zip")
        pipeline = pytest.importorskip('src.fastq_to_pdf_pipeline').create_pipeline(config)
        
        assert isinstance(pipeline, BatchPipelineOrchestrator)
        assert pipeline.config == config
    
    @patch('src.fastq_to_pdf_pipeline.BatchPipelineOrchestrator.run_complete_pipeline')
    def test_run_simple_pipeline(self, mock_run_pipeline):
        """Test: Simple pipeline execution function"""
        mock_run_pipeline.return_value = PipelineResult(success=True)
        
        patients = [PatientInfo(name="TestHorse", sample_number="001")]
        
        result = pytest.importorskip('src.fastq_to_pdf_pipeline').run_simple_pipeline(
            "test.zip", patients, "output_dir"
        )
        
        assert result.success == True
        mock_run_pipeline.assert_called_once()


# Integration tests using real data
class TestIntegrationWithRealData:
    """Integration tests using actual project data"""
    
    @pytest.mark.integration
    def test_structural_validation_with_real_reference(self):
        """Test: Validate against actual reference CSV"""
        reference_csv = "data/25_04_23 bact.csv"
        
        # Skip if reference file doesn't exist
        if not Path(reference_csv).exists():
            pytest.skip("Reference CSV not found")
        
        service = StructuralValidationService(reference_csv)
        
        # Test with the reference file itself
        result = service.validate_structure(reference_csv)
        
        assert result.is_valid == True
        assert result.column_count_match == True
        assert result.required_columns_present == True
    
    @pytest.mark.integration
    def test_taxonomic_validation_with_real_data(self):
        """Test: Taxonomic validation with real reference data"""
        reference_csv = "data/25_04_23 bact.csv"
        
        if not Path(reference_csv).exists():
            pytest.skip("Reference CSV not found")
        
        service = TaxonomicValidationService()
        result = service.validate_taxonomic_data(reference_csv)
        
        # Real data should be valid (or have known warnings)
        assert result.is_valid == True
        
        # Log any warnings for review
        if result.warnings:
            print(f"Taxonomic warnings in reference data: {result.warnings}")
    
    @pytest.mark.integration
    def test_barcode_detection_with_real_data(self):
        """Test: Barcode detection with actual reference CSV"""
        reference_csv = "data/25_04_23 bact.csv"
        
        if not Path(reference_csv).exists():
            pytest.skip("Reference CSV not found")
        
        service = StructuralValidationService()
        barcode_columns = service.detect_barcode_columns(reference_csv)
        
        # Should detect multiple barcode columns
        assert len(barcode_columns) > 0
        assert all(col.startswith('barcode') for col in barcode_columns)
        
        # Log detected barcodes for verification
        print(f"Detected barcode columns: {barcode_columns}")


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance and benchmark tests"""
    
    @pytest.mark.performance
    def test_csv_validation_performance(self, tmp_path):
        """Test: CSV validation completes within acceptable time"""
        # Create large CSV for performance testing
        large_data = {
            'species': [f'Species_{i}' for i in range(1000)],
            'barcode04': list(range(1000)),
            'barcode05': list(range(1000, 2000)),
            'total': list(range(2000, 3000)),
            'phylum': ['Actinomycetota'] * 1000,
            'genus': [f'Genus_{i}' for i in range(1000)]
        }
        
        large_csv = tmp_path / "large.csv"
        pd.DataFrame(large_data).to_csv(large_csv, index=False)
        
        service = StructuralValidationService()
        
        start_time = time.time()
        result = service.validate_structure(str(large_csv))
        processing_time = time.time() - start_time
        
        # Should complete within 5 seconds for 1000 rows
        assert processing_time < 5.0
        assert result.is_valid == True
        
        print(f"CSV validation took {processing_time:.2f}s for 1000 species")