"""
Comprehensive test fixtures for report generator testing
Combines patient and microbiome data for complete test scenarios
"""

import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from src.data_models import PatientInfo, MicrobiomeData
from tests.fixtures.patient_data import get_sample_patient_data, get_batch_patient_data
from tests.fixtures.microbiome_data import (
    MICROBIOME_NORMAL,
    MICROBIOME_MILD_DYSBIOSIS, 
    MICROBIOME_SEVERE_DYSBIOSIS,
    get_microbiome_by_category
)


def create_sample_patient(name: str = "Montana", sample_number: str = "506") -> PatientInfo:
    """Create a sample patient for testing"""
    return PatientInfo(
        name=name,
        species="Horse",
        age="20 years",
        sample_number=sample_number,
        date_received=datetime.now().strftime('%Y-%m-%d'),
        date_analyzed=datetime.now().strftime('%Y-%m-%d'),
        performed_by="Julia Kończak",
        requested_by="Dr. Alexandra Matusiak"
    )


def create_sample_microbiome(data_type: str = "normal") -> MicrobiomeData:
    """Create sample microbiome data for testing"""
    if data_type == "normal":
        return MICROBIOME_NORMAL
    elif data_type == "mild":
        return MICROBIOME_MILD_DYSBIOSIS
    elif data_type == "dysbiotic" or data_type == "severe":
        return MICROBIOME_SEVERE_DYSBIOSIS
    else:
        return get_microbiome_by_category(data_type)


def create_test_scenario(scenario_name: str) -> Tuple[PatientInfo, MicrobiomeData]:
    """Create complete test scenarios with patient and microbiome data"""
    scenarios = {
        "normal_montana": (
            create_sample_patient("Montana", "506"),
            create_sample_microbiome("normal")
        ),
        "dysbiotic_thunder": (
            create_sample_patient("Thunder", "507"), 
            create_sample_microbiome("dysbiotic")
        ),
        "mild_lightning": (
            create_sample_patient("Lightning", "508"),
            create_sample_microbiome("mild")
        ),
        "elderly_horse": (
            PatientInfo(
                name="Silver",
                species="Horse", 
                age="25 years",
                sample_number="509",
                performed_by="Dr. Senior Technician",
                requested_by="Dr. Geriatric Specialist"
            ),
            create_sample_microbiome("mild")
        ),
        "young_foal": (
            PatientInfo(
                name="Sparkle",
                species="Horse",
                age="2 years", 
                sample_number="510",
                performed_by="Dr. Young Technician",
                requested_by="Dr. Pediatric Veterinarian"
            ),
            create_sample_microbiome("normal")
        ),
        "stressed_racehorse": (
            PatientInfo(
                name="Thunderbolt",
                species="Thoroughbred",
                age="8 years",
                sample_number="511", 
                performed_by="Track Veterinarian",
                requested_by="Dr. Racing Specialist"
            ),
            create_sample_microbiome("dysbiotic")
        )
    }
    
    if scenario_name not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(scenarios.keys())}")
    
    return scenarios[scenario_name]


def create_batch_test_scenarios() -> List[Tuple[str, PatientInfo, MicrobiomeData]]:
    """Create multiple test scenarios for batch testing"""
    scenarios = []
    
    for scenario_name in ["normal_montana", "dysbiotic_thunder", "mild_lightning", "elderly_horse"]:
        patient, microbiome = create_test_scenario(scenario_name)
        scenarios.append((scenario_name, patient, microbiome))
    
    return scenarios


def create_csv_test_file(temp_dir: Path, data_type: str = "normal") -> str:
    """Create a temporary CSV file for testing"""
    if data_type == "normal":
        csv_content = """species,barcode01,phylum,genus
Lactobacillus acidophilus,1850,Bacillota,Lactobacillus
Bacteroides fragilis,1480,Bacteroidota,Bacteroides
Faecalibacterium prausnitzii,1970,Bacillota,Faecalibacterium
Escherichia coli,290,Pseudomonadota,Escherichia
Bifidobacterium bifidum,860,Actinomycetota,Bifidobacterium
Akkermansia muciniphila,180,Verrucomicrobiota,Akkermansia
Roseburia intestinalis,420,Bacillota,Roseburia
Prevotella copri,380,Bacteroidota,Prevotella
Streptococcus thermophilus,320,Bacillota,Streptococcus
Enterococcus faecium,150,Bacillota,Enterococcus
"""
    elif data_type == "dysbiotic":
        csv_content = """species,barcode01,phylum,genus
Escherichia coli,3520,Pseudomonadota,Escherichia
Clostridium difficile,1560,Bacillota,Clostridium
Enterococcus faecalis,1410,Bacillota,Enterococcus
Bacteroides fragilis,940,Bacteroidota,Bacteroides
Lactobacillus acidophilus,390,Bacillota,Lactobacillus
Klebsiella pneumoniae,680,Pseudomonadota,Klebsiella
Staphylococcus aureus,420,Bacillota,Staphylococcus
Pseudomonas aeruginosa,180,Pseudomonadota,Pseudomonas
"""
    elif data_type == "mild":
        csv_content = """species,barcode01,phylum,genus
Lactobacillus acidophilus,1250,Bacillota,Lactobacillus
Escherichia coli,1820,Pseudomonadota,Escherichia
Bacteroides fragilis,1680,Bacteroidota,Bacteroides
Faecalibacterium prausnitzii,1570,Bacillota,Faecalibacterium
Bifidobacterium bifidum,660,Actinomycetota,Bifidobacterium
Enterococcus faecalis,480,Bacillota,Enterococcus
Akkermansia muciniphila,200,Verrucomicrobiota,Akkermansia
Roseburia intestinalis,320,Bacillota,Roseburia
Prevotella copri,280,Bacteroidota,Prevotella
Clostridium butyricum,240,Bacillota,Clostridium
"""
    else:
        raise ValueError(f"Unknown CSV data type: {data_type}")
    
    csv_path = temp_dir / f"test_sample_{data_type}.csv"
    csv_path.write_text(csv_content)
    return str(csv_path)


def create_expected_template_context(patient: PatientInfo, microbiome: MicrobiomeData, 
                                   language: str = "en") -> Dict:
    """Create expected template context for validation"""
    return {
        "patient": patient,
        "data": microbiome,
        "lang": language,
        "config": {
            "reference_ranges": {
                "Actinomycetota": [0.1, 8.0],
                "Bacillota": [20.0, 70.0],
                "Bacteroidota": [4.0, 40.0],
                "Pseudomonadota": [2.0, 35.0],
                "Fibrobacterota": [0.1, 5.0]
            },
            "dysbiosis_thresholds": {
                "normal": 20,
                "mild": 50
            },
            "colors": {
                "primary_blue": "#1E3A8A",
                "green": "#10B981",
                "teal": "#14B8A6"
            }
        },
        "charts": {
            "species_pie": "/tmp/species_pie.png",
            "phylum_bar": "/tmp/phylum_bar.png",
            "dysbiosis_gauge": "/tmp/dysbiosis_gauge.png"
        }
    }


def create_mock_chart_paths(temp_dir: Path = None) -> Dict[str, str]:
    """Create mock chart file paths for testing"""
    if temp_dir:
        return {
            "species_pie": str(temp_dir / "species_pie.png"),
            "phylum_bar": str(temp_dir / "phylum_bar.png"), 
            "dysbiosis_gauge": str(temp_dir / "dysbiosis_gauge.png"),
            "diversity_trend": str(temp_dir / "diversity_trend.png")
        }
    else:
        return {
            "species_pie": "/tmp/species_pie.png",
            "phylum_bar": "/tmp/phylum_bar.png",
            "dysbiosis_gauge": "/tmp/dysbiosis_gauge.png",
            "diversity_trend": "/tmp/diversity_trend.png"
        }


def save_test_context_json(context: Dict, output_path: Path):
    """Save test context as JSON for comparison"""
    # Convert dataclasses to dicts for JSON serialization
    json_context = {}
    
    for key, value in context.items():
        if hasattr(value, '__dict__'):
            json_context[key] = value.__dict__
        else:
            json_context[key] = value
    
    with open(output_path, 'w') as f:
        json.dump(json_context, f, indent=2, default=str)


def create_edge_case_scenarios() -> List[Tuple[str, PatientInfo, MicrobiomeData]]:
    """Create edge case scenarios for testing"""
    scenarios = []
    
    # Minimal data scenario
    minimal_patient = PatientInfo(
        name="Minimal",
        sample_number="001"
    )
    minimal_microbiome = MicrobiomeData(
        species_list=[
            {"name": "Single species", "percentage": 100.0, "phylum": "Bacillota"}
        ],
        phylum_distribution={"Bacillota": 100.0},
        dysbiosis_index=0.0,
        total_species_count=1,
        dysbiosis_category="normal"
    )
    scenarios.append(("minimal_data", minimal_patient, minimal_microbiome))
    
    # Maximum dysbiosis scenario
    severe_microbiome = MicrobiomeData(
        species_list=[
            {"name": "Pathogenic species", "percentage": 90.0, "phylum": "Pseudomonadota"},
            {"name": "Minor species", "percentage": 10.0, "phylum": "Bacillota"}
        ],
        phylum_distribution={"Pseudomonadota": 90.0, "Bacillota": 10.0},
        dysbiosis_index=95.0,
        total_species_count=2,
        dysbiosis_category="severe"
    )
    scenarios.append(("maximum_dysbiosis", minimal_patient, severe_microbiome))
    
    # High diversity scenario
    high_diversity_species = []
    phylum_dist = {}
    for i in range(50):
        phylum = ["Bacillota", "Bacteroidota", "Pseudomonadota", "Actinomycetota"][i % 4]
        high_diversity_species.append({
            "name": f"Species {i}",
            "percentage": 2.0,
            "phylum": phylum
        })
        phylum_dist[phylum] = phylum_dist.get(phylum, 0) + 2.0
    
    high_diversity_microbiome = MicrobiomeData(
        species_list=high_diversity_species,
        phylum_distribution=phylum_dist,
        dysbiosis_index=15.0,
        total_species_count=50,
        dysbiosis_category="normal"
    )
    scenarios.append(("high_diversity", minimal_patient, high_diversity_microbiome))
    
    return scenarios


def get_performance_test_data() -> Tuple[PatientInfo, MicrobiomeData]:
    """Get large dataset for performance testing"""
    # Create large species list
    large_species_list = []
    phylum_counts = {"Bacillota": 0, "Bacteroidota": 0, "Pseudomonadota": 0, "Actinomycetota": 0}
    
    for i in range(1000):
        phylum = list(phylum_counts.keys())[i % 4]
        percentage = max(0.01, 100.0 / 1000 + (i % 10) * 0.001)  # Vary percentages slightly
        
        large_species_list.append({
            "name": f"Performance test species {i:04d}",
            "percentage": percentage,
            "phylum": phylum,
            "genus": f"Genus_{i // 10}"
        })
        phylum_counts[phylum] += percentage
    
    # Normalize percentages
    total_percentage = sum(phylum_counts.values())
    for phylum in phylum_counts:
        phylum_counts[phylum] = (phylum_counts[phylum] / total_percentage) * 100
    
    patient = PatientInfo(
        name="Performance Test Horse",
        age="Performance years",
        sample_number="PERF001",
        performed_by="Performance Technician",
        requested_by="Performance Veterinarian"
    )
    
    microbiome = MicrobiomeData(
        species_list=large_species_list,
        phylum_distribution=phylum_counts,
        dysbiosis_index=25.5,
        total_species_count=1000,
        dysbiosis_category="mild",
        clinical_interpretation="Performance test with large dataset",
        recommendations=["Monitor performance", "Optimize for large datasets"]
    )
    
    return patient, microbiome


def create_language_test_scenarios() -> Dict[str, Tuple[PatientInfo, MicrobiomeData]]:
    """Create test scenarios for different language support"""
    base_patient, base_microbiome = create_test_scenario("normal_montana")
    
    return {
        "english": (base_patient, base_microbiome),
        "polish": (
            PatientInfo(
                name="Koń Polski",
                age="5 lat",
                sample_number="PL001",
                performed_by="Dr. Jan Kowalski", 
                requested_by="Dr. Anna Nowak"
            ),
            base_microbiome
        ),
        "japanese": (
            PatientInfo(
                name="日本の馬",
                age="3歳",
                sample_number="JP001",
                performed_by="田中博士",
                requested_by="佐藤博士"
            ),
            base_microbiome
        )
    }


def create_error_test_scenarios() -> Dict[str, Tuple[PatientInfo, MicrobiomeData]]:
    """Create scenarios for testing error handling"""
    scenarios = {}
    
    # Empty patient name
    empty_name_patient = PatientInfo(
        name="",
        sample_number="ERR001"
    )
    scenarios["empty_patient_name"] = (empty_name_patient, create_sample_microbiome("normal"))
    
    # Invalid dysbiosis index
    invalid_microbiome = MicrobiomeData(
        species_list=[],
        phylum_distribution={},
        dysbiosis_index=-1.0,  # Invalid
        total_species_count=0,
        dysbiosis_category="unknown"
    )
    scenarios["invalid_microbiome"] = (create_sample_patient(), invalid_microbiome)
    
    # Missing required data
    incomplete_microbiome = MicrobiomeData()  # All defaults
    scenarios["incomplete_microbiome"] = (create_sample_patient(), incomplete_microbiome)
    
    return scenarios


# Convenience functions for common test patterns

def get_quick_test_data() -> Tuple[PatientInfo, MicrobiomeData]:
    """Get quick test data for simple tests"""
    return create_test_scenario("normal_montana")


def get_error_test_data() -> Tuple[PatientInfo, MicrobiomeData]:
    """Get test data that should trigger error handling"""
    scenarios = create_error_test_scenarios()
    return scenarios["invalid_microbiome"]


def get_batch_test_data() -> List[Tuple[str, PatientInfo, MicrobiomeData]]:
    """Get multiple test scenarios for batch processing tests"""
    return create_batch_test_scenarios()


if __name__ == "__main__":
    # Demo usage of test fixtures
    print("Creating test scenarios...")
    
    # Create normal scenario
    patient, microbiome = create_test_scenario("normal_montana")
    print(f"Normal scenario: {patient.name}, dysbiosis: {microbiome.dysbiosis_index}")
    
    # Create batch scenarios
    batch_scenarios = create_batch_test_scenarios()
    print(f"Created {len(batch_scenarios)} batch scenarios")
    
    # Create edge cases
    edge_cases = create_edge_case_scenarios()
    print(f"Created {len(edge_cases)} edge case scenarios")
    
    # Performance test
    perf_patient, perf_microbiome = get_performance_test_data()
    print(f"Performance test: {perf_microbiome.total_species_count} species")
    
    print("All test fixtures created successfully!")