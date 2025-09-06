"""
Clinical Filtering Module for Veterinary Microbiome Analysis

Addresses HippoVet+ specific requirements:
- Kingdom-based filtering (remove plants, keep relevant bacteria/parasites)
- Clinical relevance scoring for equine health
- Database-specific filtering rules
- Semi-automated curation workflow
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaxonomicKingdom(Enum):
    """Taxonomic kingdoms with veterinary relevance flags."""
    BACTERIA = ("Bacteria", True)
    ARCHAEA = ("Archaea", False)  # Generally excluded
    EUKARYOTA = ("Eukaryota", True)  # Needs filtering
    VIRUSES = ("Viruses", True)  # Needs filtering
    FUNGI = ("Fungi", True)
    PLANTAE = ("Plantae", False)  # Excluded
    UNKNOWN = ("Unknown", False)


class ClinicalRelevance(Enum):
    """Clinical relevance categories for veterinary reporting."""
    HIGH = "high"  # Known pathogens
    MODERATE = "moderate"  # Opportunistic/conditional pathogens
    LOW = "low"  # Commensal/environmental
    EXCLUDED = "excluded"  # Non-veterinary relevant


@dataclass
class FilterRule:
    """Individual filtering rule for species/genus."""
    name: str
    level: str  # 'species', 'genus', 'family'
    action: str  # 'include', 'exclude', 'review'
    relevance: ClinicalRelevance
    notes: str = ""
    min_abundance: float = 0.0  # Minimum % to include


@dataclass
class DatabaseConfig:
    """Configuration for each Kraken2 database."""
    name: str
    allowed_kingdoms: List[str]
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    min_abundance_threshold: float = 0.1
    require_manual_review: bool = True


class VeterinarySpeciesDatabase:
    """
    Curated database of veterinary-relevant species.
    Based on client's manual curation experience.
    """
    
    # Known equine pathogens (always include)
    EQUINE_PATHOGENS = {
        # Bacterial pathogens
        'Streptococcus equi': ClinicalRelevance.HIGH,
        'Rhodococcus equi': ClinicalRelevance.HIGH,
        'Clostridium difficile': ClinicalRelevance.HIGH,
        'Salmonella enterica': ClinicalRelevance.HIGH,
        'Escherichia coli': ClinicalRelevance.MODERATE,
        'Klebsiella pneumoniae': ClinicalRelevance.MODERATE,
        
        # Parasitic pathogens
        'Giardia lamblia': ClinicalRelevance.HIGH,
        'Cryptosporidium parvum': ClinicalRelevance.HIGH,
        'Strongyloides westeri': ClinicalRelevance.HIGH,
        'Parascaris equorum': ClinicalRelevance.HIGH,
        
        # Viral pathogens
        'Equine herpesvirus': ClinicalRelevance.HIGH,
        'Equine influenza virus': ClinicalRelevance.HIGH,
        'Equine rotavirus': ClinicalRelevance.HIGH,
    }
    
    # Plant parasites to exclude (common false positives)
    PLANT_PARASITES = {
        'Phytophthora', 'Pythium', 'Fusarium', 'Alternaria',
        'Botrytis', 'Puccinia', 'Ustilago', 'Rhizoctonia'
    }
    
    # Environmental/non-pathogenic to exclude
    ENVIRONMENTAL_EXCLUDE = {
        'Chlorella', 'Chlamydomonas', 'Volvox', 'Euglena',
        'Paramecium', 'Tetrahymena', 'Dictyostelium'
    }


class ClinicalFilter:
    """
    Main filtering class for clinical curation of Kraken2 results.
    Implements HippoVet+ workflow requirements.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize clinical filter with configuration.
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.rules: Dict[str, FilterRule] = {}
        self.database_configs: Dict[str, DatabaseConfig] = self._get_default_configs()
        self.species_db = VeterinarySpeciesDatabase()
        
        if config_path and config_path.exists():
            self.load_configuration(config_path)
    
    def _get_default_configs(self) -> Dict[str, DatabaseConfig]:
        """Get default database configurations based on client requirements."""
        return {
            'PlusPFP-16': DatabaseConfig(
                name='PlusPFP-16',
                allowed_kingdoms=['Bacteria'],
                exclude_patterns=['Archaea', 'Eukaryota'],
                min_abundance_threshold=0.1,
                require_manual_review=False
            ),
            'EuPathDB': DatabaseConfig(
                name='EuPathDB',
                allowed_kingdoms=['Eukaryota'],
                exclude_patterns=['plant', 'algae', 'fungi'],
                include_patterns=['parasite', 'protozoa'],
                min_abundance_threshold=0.5,
                require_manual_review=True
            ),
            'Viral': DatabaseConfig(
                name='Viral',
                allowed_kingdoms=['Viruses'],
                exclude_patterns=['phage', 'plant virus'],
                include_patterns=['equine', 'mammalian'],
                min_abundance_threshold=0.1,
                require_manual_review=True
            )
        }
    
    def filter_by_kingdom(self, df: pd.DataFrame, database: str) -> pd.DataFrame:
        """
        Filter results by kingdom based on database configuration.
        
        Args:
            df: Kraken2 results DataFrame
            database: Database name (PlusPFP-16, EuPathDB, Viral)
            
        Returns:
            Filtered DataFrame
        """
        config = self.database_configs.get(database)
        if not config:
            logger.warning(f"No configuration for database: {database}")
            return df
        
        # Filter by allowed kingdoms
        if 'kingdom' in df.columns:
            mask = df['kingdom'].isin(config.allowed_kingdoms)
            df_filtered = df[mask].copy()
        else:
            df_filtered = df.copy()
        
        # Apply exclude patterns
        for pattern in config.exclude_patterns:
            mask = ~df_filtered['species'].str.contains(pattern, case=False, na=False)
            df_filtered = df_filtered[mask]
        
        # Apply include patterns (if specified, only keep matches)
        if config.include_patterns:
            include_mask = pd.Series([False] * len(df_filtered), index=df_filtered.index)
            for pattern in config.include_patterns:
                include_mask |= df_filtered['species'].str.contains(
                    pattern, case=False, na=False
                )
            df_filtered = df_filtered[include_mask]
        
        # Filter by abundance threshold
        if 'percentage' in df_filtered.columns:
            df_filtered = df_filtered[
                df_filtered['percentage'] >= config.min_abundance_threshold
            ]
        
        logger.info(f"Filtered {database}: {len(df)} -> {len(df_filtered)} species")
        return df_filtered
    
    def assess_clinical_relevance(self, species: str, abundance: float) -> Tuple[ClinicalRelevance, str]:
        """
        Assess clinical relevance of a species for equine health.
        
        Args:
            species: Species name
            abundance: Relative abundance (percentage)
            
        Returns:
            Tuple of (relevance level, explanation)
        """
        # Check known pathogens
        if species in self.species_db.EQUINE_PATHOGENS:
            relevance = self.species_db.EQUINE_PATHOGENS[species]
            return relevance, f"Known equine pathogen"
        
        # Check plant parasites (exclude)
        genus = species.split()[0] if species else ""
        if genus in self.species_db.PLANT_PARASITES:
            return ClinicalRelevance.EXCLUDED, "Plant parasite - not veterinary relevant"
        
        # Check environmental species (exclude)
        if genus in self.species_db.ENVIRONMENTAL_EXCLUDE:
            return ClinicalRelevance.EXCLUDED, "Environmental organism"
        
        # Abundance-based relevance
        if abundance > 10.0:
            return ClinicalRelevance.MODERATE, f"High abundance ({abundance:.1f}%)"
        elif abundance > 1.0:
            return ClinicalRelevance.LOW, f"Moderate abundance ({abundance:.1f}%)"
        else:
            return ClinicalRelevance.LOW, f"Low abundance ({abundance:.1f}%)"
    
    def process_results(self, df: pd.DataFrame, database: str, 
                       auto_exclude: bool = True) -> pd.DataFrame:
        """
        Complete processing pipeline for Kraken2 results.
        
        Args:
            df: Raw Kraken2 results
            database: Database name
            auto_exclude: Automatically exclude non-relevant species
            
        Returns:
            Processed DataFrame with clinical annotations
        """
        # Initial kingdom filtering
        df_filtered = self.filter_by_kingdom(df, database)
        
        # Add clinical relevance assessment
        relevance_list = []
        notes_list = []
        for _, row in df_filtered.iterrows():
            species = row.get('species', '')
            abundance = row.get('percentage', 0)
            relevance, notes = self.assess_clinical_relevance(species, abundance)
            relevance_list.append(relevance.value)
            notes_list.append(notes)
        
        # Create a copy and add new columns
        df_annotated = df_filtered.copy()
        df_annotated['clinical_relevance'] = relevance_list
        df_annotated['curation_notes'] = notes_list
        
        # Auto-exclude if requested
        if auto_exclude:
            mask = df_annotated['clinical_relevance'] != ClinicalRelevance.EXCLUDED.value
            df_annotated = df_annotated[mask]
        
        # Sort by relevance and abundance
        relevance_order = {
            ClinicalRelevance.HIGH.value: 0,
            ClinicalRelevance.MODERATE.value: 1,
            ClinicalRelevance.LOW.value: 2,
            ClinicalRelevance.EXCLUDED.value: 3
        }
        df_annotated['relevance_rank'] = df_annotated['clinical_relevance'].map(relevance_order)
        df_annotated = df_annotated.sort_values(
            by=['relevance_rank', 'percentage'], 
            ascending=[True, False]
        ).drop('relevance_rank', axis=1)
        
        return df_annotated
    
    def generate_curation_report(self, df: pd.DataFrame, database: str) -> Dict:
        """
        Generate a curation report for manual review.
        
        Args:
            df: Processed results DataFrame
            database: Database name
            
        Returns:
            Dictionary with curation statistics and recommendations
        """
        report = {
            'database': database,
            'total_species': len(df),
            'by_relevance': df['clinical_relevance'].value_counts().to_dict() if 'clinical_relevance' in df.columns else {},
            'requires_review': [],
            'auto_excluded': [],
            'included': []
        }
        
        if 'clinical_relevance' in df.columns:
            # Species requiring manual review
            review_mask = df['clinical_relevance'] == ClinicalRelevance.MODERATE.value
            report['requires_review'] = df[review_mask]['species'].tolist()
            
            # Auto-excluded species
            exclude_mask = df['clinical_relevance'] == ClinicalRelevance.EXCLUDED.value
            report['auto_excluded'] = df[exclude_mask]['species'].tolist()
            
            # Included species
            include_mask = df['clinical_relevance'].isin([
                ClinicalRelevance.HIGH.value, 
                ClinicalRelevance.MODERATE.value
            ])
            report['included'] = df[include_mask]['species'].tolist()
        
        return report
    
    def save_configuration(self, path: Path) -> None:
        """Save current filter configuration to JSON."""
        config = {
            'database_configs': {
                name: {
                    'allowed_kingdoms': cfg.allowed_kingdoms,
                    'exclude_patterns': cfg.exclude_patterns,
                    'include_patterns': cfg.include_patterns,
                    'min_abundance_threshold': cfg.min_abundance_threshold,
                    'require_manual_review': cfg.require_manual_review
                }
                for name, cfg in self.database_configs.items()
            },
            'rules': [
                {
                    'name': rule.name,
                    'level': rule.level,
                    'action': rule.action,
                    'relevance': rule.relevance.value,
                    'notes': rule.notes,
                    'min_abundance': rule.min_abundance
                }
                for rule in self.rules.values()
            ]
        }
        
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_configuration(self, path: Path) -> None:
        """Load filter configuration from JSON."""
        with open(path, 'r') as f:
            config = json.load(f)
        
        # Load database configs
        for name, cfg in config.get('database_configs', {}).items():
            self.database_configs[name] = DatabaseConfig(
                name=name,
                allowed_kingdoms=cfg['allowed_kingdoms'],
                exclude_patterns=cfg.get('exclude_patterns', []),
                include_patterns=cfg.get('include_patterns', []),
                min_abundance_threshold=cfg.get('min_abundance_threshold', 0.1),
                require_manual_review=cfg.get('require_manual_review', True)
            )
        
        # Load rules
        for rule_data in config.get('rules', []):
            rule = FilterRule(
                name=rule_data['name'],
                level=rule_data['level'],
                action=rule_data['action'],
                relevance=ClinicalRelevance(rule_data['relevance']),
                notes=rule_data.get('notes', ''),
                min_abundance=rule_data.get('min_abundance', 0.0)
            )
            self.rules[rule.name] = rule