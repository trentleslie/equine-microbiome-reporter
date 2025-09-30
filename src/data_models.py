"""
Simplified data models for microbiome report generation
Based on Gemini's recommendation to use just 2 dataclasses
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class PatientInfo:
    """Patient and test information"""
    name: str = "Unknown"
    species: str = "Horse"
    age: str = "Unknown"
    sample_number: str = "001"
    case_number: str = ""  # Laboratory case/reference number
    date_received: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    date_analyzed: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"


@dataclass 
class MicrobiomeData:
    """All microbiome analysis results in one place"""
    # Core microbiome data
    species_list: List[Dict[str, any]] = field(default_factory=list)  # [{name, percentage, phylum, genus}, ...]
    phylum_distribution: Dict[str, float] = field(default_factory=dict)  # {phylum_name: percentage}
    dysbiosis_index: float = 0.0
    total_species_count: int = 0
    
    # Lab results (simplified for MVP)
    parasite_results: List[Dict[str, any]] = field(default_factory=list)
    microscopic_results: List[Dict[str, any]] = field(default_factory=list)
    biochemical_results: List[Dict[str, any]] = field(default_factory=list)
    
    # Interpretations
    dysbiosis_category: str = "normal"  # normal, mild, severe
    clinical_interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    # Optional LLM content (Week 2)
    llm_summary: Optional[str] = None
    llm_recommendations: Optional[List[str]] = None