import pytest
import tempfile
from pathlib import Path
from src.data_models import PatientInfo, MicrobiomeData
from src.batch_processor import BatchConfig

@pytest.fixture
def temp_dir():
    """Provide temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_patient():
    """Provide sample patient information"""
    return PatientInfo(
        name="Test Patient",
        age="15 years",
        species="Horse", 
        sample_number="TEST001",
        performed_by="Test Lab Tech",
        requested_by="Dr. Test Vet"
    )

@pytest.fixture
def sample_csv_data():
    """Provide sample CSV data structure"""
    return [
        {"species": "Lactobacillus acidophilus", "phylum": "Bacillota", "genus": "Lactobacillus", "abundance": 150},
        {"species": "Bacteroides fragilis", "phylum": "Bacteroidota", "genus": "Bacteroides", "abundance": 120},
        {"species": "Escherichia coli", "phylum": "Pseudomonadota", "genus": "Escherichia", "abundance": 80},
        {"species": "Bifidobacterium bifidum", "phylum": "Actinomycetota", "genus": "Bifidobacterium", "abundance": 70},
        {"species": "Faecalibacterium prausnitzii", "phylum": "Bacillota", "genus": "Faecalibacterium", "abundance": 160},
        {"species": "Prevotella melaninogenica", "phylum": "Bacteroidota", "genus": "Prevotella", "abundance": 90},
        {"species": "Clostridium butyricum", "phylum": "Bacillota", "genus": "Clostridium", "abundance": 75},
        {"species": "Akkermansia muciniphila", "phylum": "Verrucomicrobiota", "genus": "Akkermansia", "abundance": 45}
    ]

@pytest.fixture
def sample_microbiome_data():
    """Provide sample microbiome data structure"""
    return MicrobiomeData(
        species_list=[
            {"name": "Lactobacillus acidophilus", "percentage": 18.5, "phylum": "Bacillota"},
            {"name": "Bacteroides fragilis", "percentage": 14.8, "phylum": "Bacteroidota"},
            {"name": "Faecalibacterium prausnitzii", "percentage": 19.7, "phylum": "Bacillota"},
            {"name": "Escherichia coli", "percentage": 9.9, "phylum": "Pseudomonadota"},
            {"name": "Bifidobacterium bifidum", "percentage": 8.6, "phylum": "Actinomycetota"}
        ],
        phylum_distribution={
            "Bacillota": 55.2,
            "Bacteroidota": 25.8,
            "Pseudomonadota": 12.4,
            "Actinomycetota": 4.8,
            "Verrucomicrobiota": 1.8
        },
        dysbiosis_index=15.5,
        total_species_count=25,
        dysbiosis_category="normal",
        clinical_interpretation="The microbiome composition appears normal with healthy diversity.",
        recommendations=[
            "Continue current diet",
            "Monitor for changes in behavior or appetite",
            "Consider prebiotic supplements if digestive issues arise"
        ],
        parasite_results=[
            {"parameter": "Cryptosporidium", "result": "Negative", "reference": "Negative"},
            {"parameter": "Giardia", "result": "Negative", "reference": "Negative"}
        ],
        microscopic_results=[
            {"parameter": "RBC", "result": "0-2/hpf", "reference": "0-2/hpf"},
            {"parameter": "WBC", "result": "2-5/hpf", "reference": "0-5/hpf"}
        ],
        biochemical_results=[
            {"parameter": "pH", "result": "6.8", "reference": "6.0-7.5"},
            {"parameter": "Protein", "result": "Negative", "reference": "Negative"}
        ]
    )

@pytest.fixture
def test_config():
    """Provide test configuration"""
    return {
        "data_dir": "tests/fixtures/csv_files",
        "output_dir": "tests/temp_output",
        "language": "en"
    }

@pytest.fixture
def batch_config():
    """Provide batch processing configuration"""
    return BatchConfig(
        input_dir="tests/fixtures/csv_files",
        output_dir="tests/temp_output",
        manifest_file="tests/fixtures/test_manifest.csv",
        language="en",
        parallel_workers=2,
        validation_enabled=True,
        min_species_count=5,
        max_dysbiosis_index=100
    )

@pytest.fixture
def sample_csv_content():
    """Provide sample CSV file content as string"""
    return """species,barcode01,barcode02,phylum,genus
Lactobacillus acidophilus,145,132,Bacillota,Lactobacillus
Bacteroides fragilis,89,94,Bacteroidota,Bacteroides
Bifidobacterium bifidum,67,71,Actinomycetota,Bifidobacterium
Escherichia coli,23,18,Pseudomonadota,Escherichia
Faecalibacterium prausnitzii,156,148,Bacillota,Faecalibacterium
Prevotella melaninogenica,78,82,Bacteroidota,Prevotella
Clostridium butyricum,45,52,Bacillota,Clostridium
Akkermansia muciniphila,34,28,Verrucomicrobiota,Akkermansia
Streptococcus thermophilus,19,22,Bacillota,Streptococcus
Enterococcus faecalis,12,15,Bacillota,Enterococcus"""

@pytest.fixture
def dysbiotic_csv_data():
    """Provide CSV data representing dysbiotic microbiome"""
    return [
        {"species": "Escherichia coli", "phylum": "Pseudomonadota", "genus": "Escherichia", "abundance": 450},
        {"species": "Clostridium difficile", "phylum": "Bacillota", "genus": "Clostridium", "abundance": 200},
        {"species": "Enterococcus faecalis", "phylum": "Bacillota", "genus": "Enterococcus", "abundance": 180},
        {"species": "Bacteroides fragilis", "phylum": "Bacteroidota", "genus": "Bacteroides", "abundance": 120},
        {"species": "Lactobacillus acidophilus", "phylum": "Bacillota", "genus": "Lactobacillus", "abundance": 50}
    ]