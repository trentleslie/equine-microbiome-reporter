"""
Template selection logic for clinical recommendations.

This module provides data-driven selection of the most appropriate
clinical template based on microbiome analysis results.
"""

import yaml
from typing import Dict, Optional
from pathlib import Path

from .clinical_templates import ClinicalScenario, DysbiosisLevel
from .data_models import MicrobiomeData, PatientInfo


class TemplateSelector:
    """Selects appropriate clinical templates based on microbiome data"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "report_config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.reference_ranges = self.config['reference_ranges']
        self.dysbiosis_thresholds = self.config['dysbiosis_thresholds']
    
    def analyze_phylum_deviations(self, phylum_distribution: Dict[str, float]) -> Dict[str, float]:
        """Calculate deviation from reference ranges for each phylum"""
        deviations = {}
        
        for phylum, percentage in phylum_distribution.items():
            if phylum in self.reference_ranges:
                min_val, max_val = self.reference_ranges[phylum]
                
                if percentage < min_val:
                    # Negative value indicates deficiency
                    deviations[phylum] = (percentage - min_val) / min_val
                elif percentage > max_val:
                    # Positive value indicates excess
                    deviations[phylum] = (percentage - max_val) / max_val
                else:
                    deviations[phylum] = 0.0
        
        return deviations
    
    def get_dysbiosis_level(self, dysbiosis_index: float) -> DysbiosisLevel:
        """Categorize dysbiosis severity"""
        if dysbiosis_index <= self.dysbiosis_thresholds['normal']:
            return DysbiosisLevel.NORMAL
        elif dysbiosis_index <= self.dysbiosis_thresholds['mild']:
            return DysbiosisLevel.MILD
        elif dysbiosis_index <= 75:  # Moderate threshold
            return DysbiosisLevel.MODERATE
        else:
            return DysbiosisLevel.SEVERE
    
    def select_template(
        self,
        microbiome_data: MicrobiomeData,
        patient_info: Optional[PatientInfo] = None,
        clinical_history: Optional[Dict] = None
    ) -> ClinicalScenario:
        """
        Select the most appropriate clinical template based on microbiome data.
        
        Args:
            microbiome_data: Analyzed microbiome data
            patient_info: Patient information (optional)
            clinical_history: Clinical history including recent treatments
            
        Returns:
            Selected clinical scenario
        """
        
        dysbiosis_level = self.get_dysbiosis_level(microbiome_data.dysbiosis_index)
        deviations = self.analyze_phylum_deviations(microbiome_data.phylum_distribution)
        
        # Check for post-antibiotic scenario
        if clinical_history and clinical_history.get('recent_antibiotics', False):
            return ClinicalScenario.POST_ANTIBIOTIC
        
        # Normal microbiome
        if dysbiosis_level == DysbiosisLevel.NORMAL:
            return ClinicalScenario.HEALTHY_MAINTENANCE
        
        # Severe dysbiosis
        if dysbiosis_level == DysbiosisLevel.SEVERE:
            # Check if chronic based on history
            if clinical_history and clinical_history.get('chronic_issues', False):
                return ClinicalScenario.CHRONIC_DYSBIOSIS
            return ClinicalScenario.ACUTE_DYSBIOSIS
        
        # Find the most significant deviation
        if deviations:
            max_deviation_phylum = max(deviations.items(), key=lambda x: abs(x[1]))
            phylum_name, deviation_value = max_deviation_phylum
            
            # Specific phylum imbalances
            if phylum_name == 'Bacteroidota' and deviation_value < -0.5:  # >50% below minimum
                return ClinicalScenario.BACTEROIDOTA_DEFICIENCY
            elif phylum_name == 'Bacillota' and deviation_value > 0.3:  # >30% above maximum
                return ClinicalScenario.BACILLOTA_EXCESS
            elif phylum_name == 'Pseudomonadota' and deviation_value > 0.3:
                return ClinicalScenario.PSEUDOMONADOTA_EXCESS
        
        # Default to mild imbalance
        return ClinicalScenario.MILD_IMBALANCE
    
    def calculate_confidence(
        self,
        microbiome_data: MicrobiomeData,
        selected_scenario: ClinicalScenario
    ) -> float:
        """
        Calculate confidence score for the recommendation.
        
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0
        
        # Factor 1: Species diversity (more species = more reliable)
        if microbiome_data.total_species_count < 50:
            confidence *= 0.7
        elif microbiome_data.total_species_count < 100:
            confidence *= 0.85
        
        # Factor 2: Dysbiosis severity match
        if microbiome_data.dysbiosis_category == "severe" and \
           selected_scenario not in [ClinicalScenario.ACUTE_DYSBIOSIS, 
                                    ClinicalScenario.CHRONIC_DYSBIOSIS]:
            confidence *= 0.8
        
        # Factor 3: Data completeness
        known_phyla = ["Bacillota", "Bacteroidota", "Pseudomonadota", "Actinomycetota"]
        present_phyla = sum(1 for p in known_phyla if p in microbiome_data.phylum_distribution)
        confidence *= (present_phyla / len(known_phyla))
        
        return round(confidence, 2)