"""
Test fixtures for FASTQ-to-PDF pipeline testing
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
import tempfile
import zipfile
import gzip

from src.data_models import PatientInfo


def create_sample_fastq_content() -> str:
    """Create valid FASTQ content for testing"""
    return """@read1
ACGTACGTACGTACGTACGTACGTACGTACGT
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@read2  
TGCATGCATGCATGCATGCATGCATGCATGCA
+
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
@read3
ATCGATCGATCGATCGATCGATCGATCGATCG
+
JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
"""


def create_reference_csv_data() -> Dict[str, List]:
    """Create reference CSV data matching 25_04_23 bact.csv structure"""
    return {
        'species': [
            'Streptomyces albidoflavus',
            'Arthrobacter citreus', 
            'Lactobacillus acidophilus',
            'Bifidobacterium longum',
            'Clostridium perfringens'
        ],
        'barcode04': [150, 200, 300, 100, 50],
        'barcode05': [120, 180, 250, 80, 70],
        'barcode06': [100, 220, 280, 90, 60],
        'total': [370, 600, 830, 270, 180],
        'superkingdom': ['Bacteria'] * 5,
        'kingdom': ['Bacteria_none'] * 5,
        'phylum': [
            'Actinomycetota',
            'Actinomycetota', 
            'Bacillota',
            'Actinomycetota',
            'Bacillota'
        ],
        'class': [
            'Actinomycetes',
            'Actinomycetes',
            'Bacilli',
            'Actinomycetes', 
            'Clostridia'
        ],
        'order': [
            'Kitasatosporales',
            'Micrococcales',
            'Lactobacillales',
            'Bifidobacteriales',
            'Eubacteriales'
        ],
        'family': [
            'Streptomycetaceae',
            'Micrococcaceae', 
            'Lactobacillaceae',
            'Bifidobacteriaceae',
            'Clostridiaceae'
        ],
        'genus': [
            'Streptomyces',
            'Arthrobacter',
            'Lactobacillus', 
            'Bifidobacterium',
            'Clostridium'
        ],
        'tax': [
            'Bacteria,Bacteria_none,Actinomycetota,Actinomycetes,Kitasatosporales,Streptomycetaceae,Streptomyces,Streptomyces albidoflavus',
            'Bacteria,Bacteria_none,Actinomycetota,Actinomycetes,Micrococcales,Micrococcaceae,Arthrobacter,Arthrobacter citreus',
            'Bacteria,Bacteria_none,Bacillota,Bacilli,Lactobacillales,Lactobacillaceae,Lactobacillus,Lactobacillus acidophilus',
            'Bacteria,Bacteria_none,Actinomycetota,Actinomycetes,Bifidobacteriales,Bifidobacteriaceae,Bifidobacterium,Bifidobacterium longum',
            'Bacteria,Bacteria_none,Bacillota,Clostridia,Eubacteriales,Clostridiaceae,Clostridium,Clostridium perfringens'
        ]
    }


def create_test_patients() -> List[PatientInfo]:
    """Create test patient information"""
    return [
        PatientInfo(
            name="Thunder",
            age="12 years",
            sample_number="004",
            performed_by="Dr. Test",
            requested_by="Owner Test"
        ),
        PatientInfo(
            name="Lightning", 
            age="8 years",
            sample_number="005",
            performed_by="Dr. Test",
            requested_by="Owner Test"
        ),
        PatientInfo(
            name="Storm",
            age="15 years", 
            sample_number="006",
            performed_by="Dr. Test",
            requested_by="Owner Test"
        )
    ]


def create_invalid_csv_data() -> Dict[str, List]:
    """Create CSV data with various validation issues"""
    return {
        'species': ['bacteria', 'E.coli', ''],  # Invalid scientific names
        'barcode04': [100, 200, 300],
        'phylum': ['Actinobacteria', 'Proteobacteria', 'Firmicutes'],  # Outdated names
        'genus': ['Unknown', 'Escherichia', ''],
        # Missing 'total' column
    }


def create_fastq_zip_fixture(temp_dir: str) -> str:
    """
    Create a complete FASTQ zip file fixture for testing
    
    Args:
        temp_dir: Temporary directory path
        
    Returns:
        Path to created zip file
    """
    zip_path = Path(temp_dir) / "test_barcodes.zip"
    fastq_content = create_sample_fastq_content()
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Create barcode directories with FASTQ files
        for barcode in ['04', '05', '06']:
            barcode_dir = f"barcode{barcode}"
            
            # Add multiple FASTQ files per barcode
            for i in range(2):
                # Regular FASTQ file
                file_path = f"{barcode_dir}/FBC55250_pass_barcode{barcode}_sample_{i}.fastq"
                zf.writestr(file_path, fastq_content)
                
                # Gzipped FASTQ file
                gz_content = gzip.compress(fastq_content.encode())
                gz_path = f"{barcode_dir}/FBC55250_pass_barcode{barcode}_sample_{i}.fastq.gz"
                zf.writestr(gz_path, gz_content)
    
    return str(zip_path)


def create_reference_csv_fixture(temp_dir: str) -> str:
    """
    Create reference CSV file fixture matching project structure
    
    Args:
        temp_dir: Temporary directory path
        
    Returns:
        Path to created reference CSV
    """
    csv_path = Path(temp_dir) / "reference.csv"
    ref_data = create_reference_csv_data()
    
    df = pd.DataFrame(ref_data)
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)


def create_corrupted_zip_fixture(temp_dir: str) -> str:
    """Create corrupted zip file for error testing"""
    zip_path = Path(temp_dir) / "corrupted.zip"
    
    # Write invalid zip content
    with open(zip_path, 'w') as f:
        f.write("This is not a valid zip file content")
    
    return str(zip_path)


def create_empty_zip_fixture(temp_dir: str) -> str:
    """Create empty zip file (no barcode directories)"""
    zip_path = Path(temp_dir) / "empty.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("readme.txt", "This zip contains no barcode directories")
        zf.writestr("other_file.txt", "Just some random content")
    
    return str(zip_path)


def create_minimal_csv_data() -> Dict[str, List]:
    """Create minimal valid CSV data for testing"""
    return {
        'species': ['Test Species A', 'Test Species B'],
        'barcode04': [100, 200],
        'barcode05': [150, 250],
        'total': [250, 450],
        'phylum': ['Actinomycetota', 'Bacillota'],
        'genus': ['TestGenusA', 'TestGenusB']
    }


class TestDataFactory:
    """Factory class for creating various test data configurations"""
    
    @staticmethod
    def create_csv_with_barcodes(barcodes: List[str], species_count: int = 10) -> pd.DataFrame:
        """Create CSV with specific barcode columns"""
        data = {
            'species': [f'Species_{i}' for i in range(species_count)],
            'phylum': ['Actinomycetota'] * species_count,
            'genus': [f'Genus_{i}' for i in range(species_count)]
        }
        
        # Add barcode columns
        for barcode in barcodes:
            col_name = f"barcode{barcode.zfill(2)}"
            data[col_name] = [i * 10 for i in range(species_count)]
        
        # Calculate total
        barcode_cols = [f"barcode{bc.zfill(2)}" for bc in barcodes]
        df = pd.DataFrame(data)
        df['total'] = df[barcode_cols].sum(axis=1)
        
        return df
    
    @staticmethod
    def create_csv_with_taxonomic_issues(issue_type: str) -> pd.DataFrame:
        """Create CSV with specific taxonomic validation issues"""
        base_data = {
            'species': ['Streptomyces albidoflavus', 'Lactobacillus acidophilus'],
            'barcode04': [100, 200],
            'total': [100, 200],
            'genus': ['Streptomyces', 'Lactobacillus']
        }
        
        if issue_type == 'outdated_phylum':
            base_data['phylum'] = ['Actinobacteria', 'Firmicutes']  # Outdated names
        elif issue_type == 'missing_phylum':
            # Don't add phylum column
            pass
        elif issue_type == 'invalid_species':
            base_data['species'] = ['bacteria', 'E.coli']  # Invalid format
        else:
            base_data['phylum'] = ['Actinomycetota', 'Bacillota']  # Valid
        
        return pd.DataFrame(base_data)
    
    @staticmethod
    def create_large_dataset(species_count: int, barcode_count: int) -> pd.DataFrame:
        """Create large dataset for performance testing"""
        import random
        
        phyla = ['Actinomycetota', 'Bacillota', 'Bacteroidota', 'Pseudomonadota']
        
        data = {
            'species': [f'Species_{i}' for i in range(species_count)],
            'phylum': [random.choice(phyla) for _ in range(species_count)],
            'genus': [f'Genus_{i}' for i in range(species_count)]
        }
        
        # Add barcode columns
        barcode_cols = []
        for i in range(barcode_count):
            col_name = f"barcode{str(i+1).zfill(2)}"
            barcode_cols.append(col_name)
            data[col_name] = [random.randint(0, 1000) for _ in range(species_count)]
        
        df = pd.DataFrame(data)
        df['total'] = df[barcode_cols].sum(axis=1)
        
        return df