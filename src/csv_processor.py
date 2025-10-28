"""
CSV processing module for microbiome data
Converts CSV files to MicrobiomeData objects
"""

import pandas as pd
import numpy as np
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
try:
    from .data_models import MicrobiomeData
except ImportError:
    from data_models import MicrobiomeData


class CSVProcessor:
    """Process microbiome CSV data into structured format"""

    # Known eukaryotic species to exclude
    EUKARYOTE_SPECIES = {
        'Homo sapiens', 'Papaver somniferum', 'Humulus lupulus',
        'Micromonospora siamensis', 'Phocaeicola vulgatus'
    }

    def __init__(self, csv_path: str, barcode_column: str = None, config_path: str = None):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)

        # Load eukaryote exclusion list from config
        self._load_exclusion_list(config_path)

        # Auto-detect barcode column if not specified
        if barcode_column is None:
            barcode_cols = [col for col in self.df.columns if col.startswith('barcode')]
            if barcode_cols:
                self.barcode_column = barcode_cols[0]
            else:
                # Fall back to any numeric column that isn't a standard column
                standard_cols = ['species', 'phylum', 'genus', 'family', 'order', 'class']
                numeric_cols = [col for col in self.df.columns
                               if col not in standard_cols and pd.api.types.is_numeric_dtype(self.df[col])]
                self.barcode_column = numeric_cols[0] if numeric_cols else "barcode59"
        else:
            self.barcode_column = barcode_column

        # Filter eukaryotes before calculating totals
        self.df = self._filter_eukaryotes(self.df)
        self.total_count = self.df[self.barcode_column].sum()

    def _load_exclusion_list(self, config_path: str = None):
        """Load eukaryote exclusion list from config file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'report_config.yaml'

        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if 'species_filtering' in config:
                        self.EUKARYOTE_SPECIES.update(
                            config['species_filtering'].get('exclude_eukaryotes', [])
                        )
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

    def _filter_eukaryotes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out non-bacterial organisms (eukaryotes, archaea) from the dataframe"""

        # Method 1: Use superkingdom column if available (most reliable)
        superkingdom_col = None
        for col_name in ['superkingdom', 'Superkingdom', 'SUPERKINGDOM', 'domain', 'Domain']:
            if col_name in df.columns:
                superkingdom_col = col_name
                break

        if superkingdom_col:
            # Keep only bacteria
            df = df[df[superkingdom_col] == 'Bacteria'].copy()
            print(f"Filtered by {superkingdom_col}: {len(df)} bacterial entries remaining")
        else:
            # Method 2: Fall back to species name filtering if taxonomy columns not available
            if 'species' in df.columns or 'Species' in df.columns:
                species_col = 'Species' if 'Species' in df.columns else 'species'
                df = df[~df[species_col].isin(self.EUKARYOTE_SPECIES)]
                print(f"Filtered by species names: {len(df)} entries remaining")

        return df

    @staticmethod
    def clean_species_name(name: str) -> str:
        """Clean species name by removing special characters like brackets"""
        # Remove square brackets and their contents
        name = re.sub(r'\[([^\]]+)\]', r'\1', name)
        # Remove any remaining brackets
        name = name.replace('[', '').replace(']', '')
        return name.strip()
    
    def process(self) -> MicrobiomeData:
        """Convert CSV to MicrobiomeData object"""
        species_list = self._get_species_list()

        # Calculate raw phylum distribution (includes all phyla)
        phylum_dist_raw = self._calculate_phylum_distribution(species_list)

        # Calculate dysbiosis index using raw distribution (all bacterial phyla)
        di_score = self._calculate_dysbiosis_index(phylum_dist_raw)

        # Filter phylum distribution for reporting (DI-relevant + Other)
        phylum_dist_filtered = self._filter_phylum_for_reporting(phylum_dist_raw)

        return MicrobiomeData(
            species_list=species_list,
            phylum_distribution=phylum_dist_filtered,  # Use filtered for display in charts
            dysbiosis_index=di_score,
            total_species_count=len(species_list),
            dysbiosis_category=self._get_dysbiosis_category(di_score),
            parasite_results=self._get_default_parasite_results(),
            microscopic_results=self._get_default_microscopic_results(),
            biochemical_results=self._get_default_biochemical_results(),
            clinical_interpretation=self._generate_clinical_interpretation(di_score, phylum_dist_raw),
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
            species_name = row.get('Species', row.get('species', 'Unknown species'))
            genus_name = row.get('Genus', row.get('genus', 'Unknown genus'))

            species_data = {
                'species': self.clean_species_name(species_name),
                'genus': self.clean_species_name(genus_name),
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

    def _filter_phylum_for_reporting(self, phylum_dist: Dict[str, float]) -> Dict[str, float]:
        """Filter phylum distribution to show only DI-relevant phyla + Other bacterial phyla

        This groups minor bacterial phyla into 'Other bacterial phyla' category
        and excludes Unknown/non-bacterial entries from the report.
        """
        # DI-relevant phyla used in dysbiosis index calculation
        DI_PHYLA = {'Actinomycetota', 'Bacillota', 'Bacteroidota', 'Pseudomonadota', 'Fibrobacterota'}

        filtered = {}
        other_total = 0.0

        for phylum, percentage in phylum_dist.items():
            # Skip unknown/empty phyla
            if phylum in ['Unknown phylum', 'Unknown', '', 'unknown', 'UNKNOWN']:
                continue

            if phylum in DI_PHYLA:
                # Include DI-relevant phyla directly
                filtered[phylum] = percentage
            else:
                # Group all other bacterial phyla as "Other"
                other_total += percentage

        # Only add "Other" category if there are minor bacterial phyla
        if other_total > 0:
            filtered['Other bacterial phyla'] = round(other_total, 2)

        return filtered
    
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