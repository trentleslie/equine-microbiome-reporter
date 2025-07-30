"""
Test fixtures for MicrobiomeData

Provides realistic sample microbiome data for testing data models
and report generation functionality with various dysbiosis scenarios.
"""

from src.data_models import MicrobiomeData
from typing import List, Dict, Any

# Normal microbiome composition
MICROBIOME_NORMAL = MicrobiomeData(
    species_list=[
        {"name": "Faecalibacterium prausnitzii", "percentage": 19.7, "phylum": "Bacillota", "genus": "Faecalibacterium"},
        {"name": "Lactobacillus acidophilus", "percentage": 18.5, "phylum": "Bacillota", "genus": "Lactobacillus"},
        {"name": "Bacteroides fragilis", "percentage": 14.8, "phylum": "Bacteroidota", "genus": "Bacteroides"},
        {"name": "Bifidobacterium longum", "percentage": 8.6, "phylum": "Actinomycetota", "genus": "Bifidobacterium"},
        {"name": "Escherichia coli", "percentage": 2.9, "phylum": "Pseudomonadota", "genus": "Escherichia"}
    ],
    phylum_distribution={
        "Bacillota": 55.2,
        "Bacteroidota": 25.8,
        "Pseudomonadota": 12.4,
        "Actinomycetota": 4.8,
        "Fibrobacterota": 1.8
    },
    dysbiosis_index=15.5,
    total_species_count=147,
    dysbiosis_category="normal",
    clinical_interpretation="The microbiome composition appears normal with healthy diversity and balanced phylum representation.",
    recommendations=[
        "Continue current diet and management practices",
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

# Mild dysbiosis
MICROBIOME_MILD_DYSBIOSIS = MicrobiomeData(
    species_list=[
        {"name": "Escherichia coli", "percentage": 18.2, "phylum": "Pseudomonadota", "genus": "Escherichia"},
        {"name": "Bacteroides fragilis", "percentage": 16.8, "phylum": "Bacteroidota", "genus": "Bacteroides"},
        {"name": "Faecalibacterium prausnitzii", "percentage": 15.7, "phylum": "Bacillota", "genus": "Faecalibacterium"},
        {"name": "Lactobacillus acidophilus", "percentage": 12.5, "phylum": "Bacillota", "genus": "Lactobacillus"},
        {"name": "Bifidobacterium longum", "percentage": 6.6, "phylum": "Actinomycetota", "genus": "Bifidobacterium"}
    ],
    phylum_distribution={
        "Bacillota": 42.2,
        "Pseudomonadota": 28.4,
        "Bacteroidota": 18.8,
        "Actinomycetota": 8.6,
        "Fibrobacterota": 2.0
    },
    dysbiosis_index=35.8,
    total_species_count=89,
    dysbiosis_category="mild",
    clinical_interpretation="The microbiome shows mild dysbiosis with some imbalance in bacterial populations.",
    recommendations=[
        "Monitor diet and feeding patterns closely",
        "Consider prebiotic supplementation",
        "Retest in 4-6 weeks to monitor progress"
    ],
    parasite_results=[
        {"parameter": "Cryptosporidium", "result": "Negative", "reference": "Negative"},
        {"parameter": "Giardia", "result": "Negative", "reference": "Negative"}
    ],
    microscopic_results=[
        {"parameter": "RBC", "result": "2-3/hpf", "reference": "0-2/hpf"},
        {"parameter": "WBC", "result": "6-8/hpf", "reference": "0-5/hpf"}
    ],
    biochemical_results=[
        {"parameter": "pH", "result": "6.2", "reference": "6.0-7.5"},
        {"parameter": "Protein", "result": "Trace", "reference": "Negative"}
    ]
)

# Severe dysbiosis
MICROBIOME_SEVERE_DYSBIOSIS = MicrobiomeData(
    species_list=[
        {"name": "Escherichia coli", "percentage": 35.2, "phylum": "Pseudomonadota", "genus": "Escherichia"},
        {"name": "Clostridium difficile", "percentage": 15.6, "phylum": "Bacillota", "genus": "Clostridium"},
        {"name": "Enterococcus faecalis", "percentage": 14.1, "phylum": "Bacillota", "genus": "Enterococcus"},
        {"name": "Bacteroides fragilis", "percentage": 9.4, "phylum": "Bacteroidota", "genus": "Bacteroides"},
        {"name": "Lactobacillus acidophilus", "percentage": 3.9, "phylum": "Bacillota", "genus": "Lactobacillus"}
    ],
    phylum_distribution={
        "Pseudomonadota": 48.7,
        "Bacillota": 35.6,
        "Bacteroidota": 12.4,
        "Actinomycetota": 2.3,
        "Fibrobacterota": 1.0
    },
    dysbiosis_index=75.3,
    total_species_count=42,
    dysbiosis_category="severe",
    clinical_interpretation="The microbiome shows severe dysbiosis with significant pathogen overgrowth and reduced beneficial bacteria.",
    recommendations=[
        "Immediate veterinary consultation recommended",
        "Consider targeted probiotic therapy",
        "Dietary modification may be necessary",
        "Monitor closely for clinical symptoms"
    ],
    parasite_results=[
        {"parameter": "Cryptosporidium", "result": "Negative", "reference": "Negative"},
        {"parameter": "Giardia", "result": "Positive", "reference": "Negative"}
    ],
    microscopic_results=[
        {"parameter": "RBC", "result": "5-8/hpf", "reference": "0-2/hpf"},
        {"parameter": "WBC", "result": "15-20/hpf", "reference": "0-5/hpf"}
    ],
    biochemical_results=[
        {"parameter": "pH", "result": "5.2", "reference": "6.0-7.5"},
        {"parameter": "Protein", "result": "Positive", "reference": "Negative"}
    ]
)

# Minimal microbiome data for testing edge cases
MICROBIOME_MINIMAL = MicrobiomeData(
    dysbiosis_index=0.0,
    total_species_count=0,
    dysbiosis_category="normal"
)

# Large species list for performance testing
def get_large_species_list(count: int = 300) -> List[Dict[str, Any]]:
    """Generate large species list for performance testing"""
    species_list = []
    phyla = ["Bacillota", "Bacteroidota", "Pseudomonadota", "Actinomycetota", "Fibrobacterota"]
    
    for i in range(count):
        species = {
            "name": f"Test_species_{i}",
            "percentage": round(100.0 / count, 3),
            "phylum": phyla[i % len(phyla)],
            "genus": f"Test_genus_{i}"
        }
        species_list.append(species)
    
    return species_list

MICROBIOME_LARGE = MicrobiomeData(
    species_list=get_large_species_list(300),
    phylum_distribution={
        "Bacillota": 35.0,
        "Bacteroidota": 25.0,
        "Pseudomonadota": 20.0,
        "Actinomycetota": 15.0,
        "Fibrobacterota": 5.0
    },
    dysbiosis_index=25.0,
    total_species_count=300,
    dysbiosis_category="normal"
)

# Collection of all test microbiome data
ALL_TEST_MICROBIOMES = [
    MICROBIOME_NORMAL,
    MICROBIOME_MILD_DYSBIOSIS,
    MICROBIOME_SEVERE_DYSBIOSIS,
    MICROBIOME_MINIMAL,
    MICROBIOME_LARGE
]

def get_microbiome_by_category(category: str) -> MicrobiomeData:
    """Get microbiome data by dysbiosis category"""
    category_map = {
        "normal": MICROBIOME_NORMAL,
        "mild": MICROBIOME_MILD_DYSBIOSIS,
        "severe": MICROBIOME_SEVERE_DYSBIOSIS,
        "minimal": MICROBIOME_MINIMAL,
        "large": MICROBIOME_LARGE
    }
    
    if category not in category_map:
        raise ValueError(f"Unknown category: {category}. Available: {list(category_map.keys())}")
    
    return category_map[category]

def get_default_microbiome() -> MicrobiomeData:
    """Get default microbiome for simple tests"""
    return MICROBIOME_NORMAL