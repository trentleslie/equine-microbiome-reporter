"""
Helper utilities for batch processor testing
"""

import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from src.batch_processor import BatchConfig, BatchProcessor
from src.data_models import PatientInfo


def create_temp_batch_config(**overrides) -> BatchConfig:
    """Create a temporary batch configuration for testing"""
    defaults = {
        'data_dir': Path('tests/fixtures/batch_data/valid_batch'),
        'language': 'en',
        'parallel_processing': False,  # Disable for predictable tests
        'max_workers': 2,
        'min_species_count': 5,
        'max_unassigned_percentage': 60.0,
        'required_phyla': ["Bacillota", "Bacteroidota", "Pseudomonadota"]
    }
    defaults.update(overrides)
    
    # Create temporary reports directory
    temp_dir = tempfile.mkdtemp()
    defaults['reports_dir'] = Path(temp_dir) / 'reports'
    
    return BatchConfig(**defaults)


def create_test_csv_files(directory: Path, file_data: List[Dict]) -> List[Path]:
    """Create test CSV files in specified directory"""
    directory.mkdir(parents=True, exist_ok=True)
    created_files = []
    
    for file_info in file_data:
        file_path = directory / file_info['filename']
        with open(file_path, 'w') as f:
            f.write(file_info['content'])
        created_files.append(file_path)
    
    return created_files


def create_large_batch_files(directory: Path, count: int = 10) -> List[Path]:
    """Create multiple CSV files for large batch testing"""
    directory.mkdir(parents=True, exist_ok=True)
    created_files = []
    
    base_content = """species,barcode{},phylum,genus,family,class,order
Streptomyces coelicolor,50,Actinomycetota,Streptomyces,Streptomycetaceae,Actinomycetes,Streptomycetales
Bacillus subtilis,400,Bacillota,Bacillus,Bacillaceae,Bacilli,Bacillales
Lactobacillus plantarum,300,Bacillota,Lactobacillus,Lactobacillaceae,Bacilli,Lactobacillales
Bacteroides fragilis,350,Bacteroidota,Bacteroides,Bacteroidaceae,Bacteroidia,Bacteroidales
Escherichia coli,200,Pseudomonadota,Escherichia,Enterobacteriaceae,Gammaproteobacteria,Enterobacterales
Pseudomonas aeruginosa,150,Pseudomonadota,Pseudomonas,Pseudomonadaceae,Gammaproteobacteria,Pseudomonadales
Fibrobacter succinogenes,100,Fibrobacterota,Fibrobacter,Fibrobacteraceae,Fibrobacteria,Fibrobacterales"""
    
    for i in range(count):
        filename = f"large_batch_sample_{i+1:02d}.csv"
        file_path = directory / filename
        barcode_num = f"{i+1:02d}"
        content = base_content.format(barcode_num)
        
        with open(file_path, 'w') as f:
            f.write(content)
        created_files.append(file_path)
    
    return created_files


def assert_processing_result(result: Dict, expected_success: bool = True, check_file_exists: bool = False):
    """Assert common properties of processing results"""
    assert 'csv_file' in result
    assert 'success' in result
    assert 'processing_time' in result
    assert 'message' in result
    
    if expected_success:
        assert result['success'] is True
        assert 'output_file' in result
        assert result['output_file'] is not None
        if check_file_exists:
            assert Path(result['output_file']).exists()
    else:
        assert result['success'] is False


def assert_batch_results(results: List[Dict], min_successful: int = 0, check_file_exists: bool = False):
    """Assert properties of batch processing results"""
    assert isinstance(results, list)
    assert len(results) > 0
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    assert len(successful) >= min_successful
    
    # Validate structure of each result
    for result in results:
        assert_processing_result(result, expected_success=result.get('success', False), check_file_exists=check_file_exists)
    
    return {
        'successful': successful,
        'failed': failed,
        'success_rate': len(successful) / len(results) if results else 0
    }


def cleanup_temp_directories(*directories):
    """Clean up temporary directories after tests"""
    for directory in directories:
        if directory and Path(directory).exists():
            shutil.rmtree(directory, ignore_errors=True)


def create_test_patient_info(name: str = "TestHorse", **overrides) -> PatientInfo:
    """Create test patient info with sensible defaults"""
    defaults = {
        'name': name,
        'species': 'Horse',
        'age': '10 years',
        'sample_number': 'TEST-001',
        'performed_by': 'Test Lab Staff',
        'requested_by': 'Test Veterinarian'
    }
    defaults.update(overrides)
    return PatientInfo(**defaults)


def validate_csv_file_format(file_path: Path) -> bool:
    """Validate CSV file has expected structure"""
    try:
        with open(file_path, 'r') as f:
            header = f.readline().strip()
            required_columns = ['species', 'phylum', 'genus']
            return all(col in header for col in required_columns)
    except Exception:
        return False


def count_species_in_csv(file_path: Path, barcode_column: str = None) -> int:
    """Count number of species in CSV file"""
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        
        # Auto-detect barcode column if not specified
        if barcode_column is None:
            barcode_columns = [col for col in df.columns if col.startswith('barcode')]
            if barcode_columns:
                barcode_column = barcode_columns[0]
            else:
                return len(df)
        
        # Count non-zero entries
        return len(df[df[barcode_column] > 0]) if barcode_column in df.columns else len(df)
    except Exception:
        return 0


class MockProgressCallback:
    """Mock progress callback for testing"""
    
    def __init__(self):
        self.calls = []
        self.current = 0
        self.total = 0
    
    def __call__(self, current: int, total: int):
        self.calls.append((current, total))
        self.current = current
        self.total = total
    
    def assert_called(self):
        assert len(self.calls) > 0, "Progress callback was never called"
    
    def assert_completed(self):
        assert self.current == self.total, f"Progress not completed: {self.current}/{self.total}"
    
    def assert_call_count(self, expected_count: int):
        assert len(self.calls) == expected_count, f"Expected {expected_count} calls, got {len(self.calls)}"