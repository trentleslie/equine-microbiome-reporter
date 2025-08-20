"""
CSV processing module for microbiome data
Converts CSV files to MicrobiomeData objects
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
try:
    from .data_models import MicrobiomeData
except ImportError:
    from data_models import MicrobiomeData


class CSVProcessor:
    """Process microbiome CSV data into structured format"""
    
    def __init__(self, csv_path: str, barcode_column: str = "barcode59"):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.barcode_column = barcode_column
        self.total_count = self.df[barcode_column].sum()
    
    def process(self) -> MicrobiomeData:
        """Convert CSV to MicrobiomeData object"""
        species_list = self._get_species_list()
        phylum_dist = self._calculate_phylum_distribution(species_list)
        di_score = self._calculate_dysbiosis_index(phylum_dist)
        
        return MicrobiomeData(
            species_list=species_list,
            phylum_distribution=phylum_dist,
            dysbiosis_index=di_score,
            total_species_count=len(species_list),
            dysbiosis_category=self._get_dysbiosis_category(di_score),
            parasite_results=self._get_default_parasite_results(),
            microscopic_results=self._get_default_microscopic_results(),
            biochemical_results=self._get_default_biochemical_results(),
            clinical_interpretation=self._generate_clinical_interpretation(di_score, phylum_dist),
            recommendations=self._get_recommendations(di_score)
        )
    
    def _get_species_list(self) -> List[Dict[str, any]]:
        """Extract species list with percentages from CSV"""
        # Filter out zero counts and calculate percentages
        filtered_df = self.df[self.df[self.barcode_column] > 0].copy()
        filtered_df['percentage'] = (filtered_df[self.barcode_column] / self.total_count) * 100
        
        # Sort by percentage descending
        filtered_df = filtered_df.sort_values('percentage', ascending=False)
        
        species_list = []
        for _, row in filtered_df.iterrows():
            species_data = {
                'species': row.get('Species', row.get('species', 'Unknown species')),
                'genus': row.get('Genus', row.get('genus', 'Unknown genus')),
                'phylum': row.get('Phylum', row.get('phylum', 'Unknown phylum')),
                'percentage': round(row['percentage'], 2),
                'count': int(row[self.barcode_column])
            }
            species_list.append(species_data)
        
        return species_list
    
    def _calculate_phylum_distribution(self, species_list: List[Dict]) -> Dict[str, float]:
        """Calculate phylum-level distribution"""
        phylum_counts = {}
        
        for species in species_list:
            phylum = species['phylum']
            if phylum not in phylum_counts:
                phylum_counts[phylum] = 0
            phylum_counts[phylum] += species['percentage']
        
        return {k: round(v, 2) for k, v in phylum_counts.items()}
    
    def _calculate_dysbiosis_index(self, phylum_dist: Dict[str, float]) -> float:
        """Calculate dysbiosis index based on phylum distribution"""
        # Reference ranges for major phyla
        reference_ranges = {
            'Actinomycetota': (0.1, 8.0),
            'Bacillota': (20.0, 70.0),
            'Bacteroidota': (4.0, 40.0),
            'Pseudomonadota': (2.0, 35.0),
            'Fibrobacterota': (0.1, 5.0)
        }
        
        dysbiosis_score = 0.0
        
        for phylum, (min_ref, max_ref) in reference_ranges.items():
            actual = phylum_dist.get(phylum, 0)
            
            if actual < min_ref:
                dysbiosis_score += (min_ref - actual) / min_ref * 18
            elif actual > max_ref:
                dysbiosis_score += (actual - max_ref) / max_ref * 18
        
        return round(dysbiosis_score, 1)
    
    def _get_dysbiosis_category(self, dysbiosis_index: float) -> str:
        """Categorize dysbiosis severity"""
        if dysbiosis_index <= 20:
            return "normal"
        elif dysbiosis_index <= 50:
            return "mild"
        else:
            return "severe"
    
    def _generate_clinical_interpretation(self, dysbiosis_index: float, phylum_dist: Dict[str, float]) -> str:
        """Generate clinical interpretation based on results"""
        if dysbiosis_index <= 20:
            return "Normal microbiota (healthy). Lack of dysbiosis signs; gut microflora is balanced with minor deviations."
        elif dysbiosis_index <= 50:
            return "Mild dysbiosis detected. Moderate imbalance in gut microflora composition requiring monitoring."
        else:
            return "Severe dysbiosis detected. Significant imbalance in gut microflora requiring intervention."
    
    def _get_recommendations(self, dysbiosis_index: float) -> List[str]:
        """Get recommendations based on dysbiosis level"""
        if dysbiosis_index <= 20:
            return [
                "Continue current feeding regimen",
                "Regular monitoring recommended",
                "Consider prebiotics if stress occurs"
            ]
        elif dysbiosis_index <= 50:
            return [
                "Review current diet composition",
                "Consider probiotic supplementation",
                "Monitor for clinical symptoms",
                "Retest in 4-6 weeks"
            ]
        else:
            return [
                "Immediate dietary intervention required",
                "Veterinary consultation recommended",
                "Probiotic therapy indicated",
                "Follow-up testing in 2-3 weeks"
            ]
    
    def _get_default_parasite_results(self) -> List[Dict[str, any]]:
        """Default parasite examination results"""
        return [
            {"name": "Anoplocephala perfoliata", "result": "Not observed"},
            {"name": "Oxyuris equi", "result": "Not observed"},
            {"name": "Parascaris equorum", "result": "Not observed"},
            {"name": "Strongylidae", "result": "Not observed"}
        ]
    
    def _get_default_microscopic_results(self) -> List[Dict[str, any]]:
        """Default microscopic examination results"""
        return [
            {"parameter": "Starch grains", "result": "Few", "reference": "Few to moderate"},
            {"parameter": "Plant fibers", "result": "Moderate", "reference": "Moderate to many"},
            {"parameter": "Fat droplets", "result": "Few", "reference": "Few"},
            {"parameter": "Leukocytes", "result": "Few", "reference": "Few"}
        ]
    
    def _get_default_biochemical_results(self) -> List[Dict[str, any]]:
        """Default biochemical examination results"""
        return [
            {"parameter": "pH", "result": "7.2", "reference": "6.5-7.5"},
            {"parameter": "Ammonia", "result": "Low", "reference": "Low to moderate"},
            {"parameter": "Short-chain fatty acids", "result": "Normal", "reference": "Normal range"}
        ]