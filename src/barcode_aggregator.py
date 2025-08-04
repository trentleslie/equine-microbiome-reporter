"""
Enhanced Barcode Aggregation with Statistical Validation
Combines technical replicates with proper normalization and quality control
Based on Gemini feedback for scientific rigor
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from scipy.stats import spearmanr, pearsonr
import logging
import warnings

logger = logging.getLogger(__name__)


@dataclass
class AggregationConfig:
    """Configuration for barcode aggregation"""
    normalization_method: str = "relative_abundance"  # cpm, rarefaction, relative_abundance
    correlation_method: str = "spearman"  # spearman, pearson
    correlation_threshold: float = 0.7
    p_value_threshold: float = 0.05
    quality_threshold: int = 20  # Phred score
    min_read_length: int = 100
    min_reads_per_barcode: int = 10  # Minimum reads for valid barcode


@dataclass
class ValidationResult:
    """Results from barcode validation"""
    correlations: Dict[str, float]
    p_values: Dict[str, float]
    valid_combinations: List[Tuple[str, str]]
    warnings: List[str]
    quality_metrics: Dict[str, Any]


@dataclass
class AggregationResult:
    """Results from barcode aggregation"""
    combined_data: pd.DataFrame
    validation_result: ValidationResult
    normalization_stats: Dict[str, Any]
    total_reads_per_barcode: Dict[str, int]
    combined_total_reads: int
    species_overlap: Dict[str, int]
    success: bool
    error_message: Optional[str] = None


class EnhancedBarcodeAggregator:
    """
    Enhanced barcode aggregator with normalization and statistical validation
    """
    
    def __init__(self, config: AggregationConfig = None):
        self.config = config or AggregationConfig()
        
    def aggregate_barcodes(self, csv_path: str, barcode_columns: List[str], 
                          patient_name: str = "Unknown") -> AggregationResult:
        """
        Aggregate multiple barcode columns into single combined profile
        
        Args:
            csv_path: Path to CSV with barcode columns
            barcode_columns: List of barcode column names to combine
            patient_name: Patient name for logging
            
        Returns:
            AggregationResult with combined data and validation metrics
        """
        try:
            logger.info(f"Starting barcode aggregation for {patient_name}")
            logger.info(f"Combining barcodes: {barcode_columns}")
            
            # Load and validate data
            df = pd.read_csv(csv_path)
            validation_result = self._validate_barcodes(df, barcode_columns)
            
            if not validation_result.valid_combinations:
                return AggregationResult(
                    combined_data=pd.DataFrame(),
                    validation_result=validation_result,
                    normalization_stats={},
                    total_reads_per_barcode={},
                    combined_total_reads=0,
                    species_overlap={},
                    success=False,
                    error_message="No valid barcode combinations found"
                )
            
            # Normalize data before aggregation
            normalized_df = self._normalize_data(df, barcode_columns)
            
            # Aggregate barcodes
            combined_df = self._combine_barcodes(normalized_df, barcode_columns)
            
            # Calculate statistics
            total_reads_per_barcode = {col: int(df[col].sum()) for col in barcode_columns}
            combined_total_reads = int(combined_df['total_combined'].sum())
            species_overlap = self._calculate_species_overlap(df, barcode_columns)
            
            # Normalization statistics
            normalization_stats = self._calculate_normalization_stats(df, normalized_df, barcode_columns)
            
            logger.info(f"Aggregation successful: {len(combined_df)} species, {combined_total_reads} total reads")
            
            return AggregationResult(
                combined_data=combined_df,
                validation_result=validation_result,
                normalization_stats=normalization_stats,
                total_reads_per_barcode=total_reads_per_barcode,
                combined_total_reads=combined_total_reads,
                species_overlap=species_overlap,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Barcode aggregation failed: {e}")
            return AggregationResult(
                combined_data=pd.DataFrame(),
                validation_result=ValidationResult({}, {}, [], [str(e)], {}),
                normalization_stats={},
                total_reads_per_barcode={},
                combined_total_reads=0,
                species_overlap={},
                success=False,
                error_message=str(e)
            )
    
    def _validate_barcodes(self, df: pd.DataFrame, barcode_columns: List[str]) -> ValidationResult:
        """
        Validate barcode data using statistical correlation analysis
        """
        correlations = {}
        p_values = {}
        valid_combinations = []
        warnings_list = []
        quality_metrics = {}
        
        # Check if barcode columns exist
        missing_columns = [col for col in barcode_columns if col not in df.columns]
        if missing_columns:
            warnings_list.append(f"Missing barcode columns: {missing_columns}")
            return ValidationResult(correlations, p_values, valid_combinations, warnings_list, quality_metrics)
        
        # Quality metrics per barcode
        for col in barcode_columns:
            reads = df[col].fillna(0)
            total_reads = reads.sum()
            non_zero_species = (reads > 0).sum()
            
            quality_metrics[col] = {
                'total_reads': int(total_reads),
                'species_count': int(non_zero_species),
                'max_abundance': float(reads.max()),
                'mean_abundance': float(reads.mean()),
                'median_abundance': float(reads.median())
            }
            
            # Check minimum read threshold
            if total_reads < self.config.min_reads_per_barcode:
                warnings_list.append(f"Low read count in {col}: {total_reads} < {self.config.min_reads_per_barcode}")
        
        # Pairwise correlation analysis
        for i, col1 in enumerate(barcode_columns):
            for j, col2 in enumerate(barcode_columns[i+1:], i+1):
                data1 = df[col1].fillna(0)
                data2 = df[col2].fillna(0)
                
                # Calculate correlation
                if self.config.correlation_method == "spearman":
                    corr_coeff, p_value = spearmanr(data1, data2)
                else:  # pearson
                    corr_coeff, p_value = pearsonr(data1, data2)
                
                pair_key = f"{col1}_vs_{col2}"
                correlations[pair_key] = float(corr_coeff) if not np.isnan(corr_coeff) else 0.0
                p_values[pair_key] = float(p_value) if not np.isnan(p_value) else 1.0
                
                # Validate correlation
                if corr_coeff >= self.config.correlation_threshold and p_value <= self.config.p_value_threshold:
                    valid_combinations.append((col1, col2))
                    logger.info(f"Valid correlation {col1}-{col2}: r={corr_coeff:.3f}, p={p_value:.3f}")
                else:
                    warning_msg = f"Low correlation {col1}-{col2}: r={corr_coeff:.3f}, p={p_value:.3f}"
                    warnings_list.append(warning_msg)
                    logger.warning(warning_msg)
        
        # Overall validation assessment
        if len(valid_combinations) < len(barcode_columns) - 1:
            warnings_list.append("Some barcodes show poor correlation - may not represent same sample")
        
        return ValidationResult(correlations, p_values, valid_combinations, warnings_list, quality_metrics)
    
    def _normalize_data(self, df: pd.DataFrame, barcode_columns: List[str]) -> pd.DataFrame:
        """
        Normalize barcode data using specified method
        """
        normalized_df = df.copy()
        
        if self.config.normalization_method == "relative_abundance":
            # Convert to relative abundance (percentages)
            for col in barcode_columns:
                total_reads = df[col].sum()
                if total_reads > 0:
                    normalized_df[col] = (df[col] / total_reads) * 100
                else:
                    normalized_df[col] = 0
                    
        elif self.config.normalization_method == "cpm":
            # Counts per million
            for col in barcode_columns:
                total_reads = df[col].sum()
                if total_reads > 0:
                    normalized_df[col] = (df[col] / total_reads) * 1_000_000
                else:
                    normalized_df[col] = 0
                    
        elif self.config.normalization_method == "rarefaction":
            # Rarefy to minimum depth
            min_depth = min([df[col].sum() for col in barcode_columns if df[col].sum() > 0])
            if min_depth > 0:
                for col in barcode_columns:
                    total_reads = df[col].sum()
                    if total_reads > 0:
                        normalized_df[col] = (df[col] / total_reads) * min_depth
                    else:
                        normalized_df[col] = 0
        
        logger.info(f"Applied {self.config.normalization_method} normalization to {len(barcode_columns)} barcodes")
        return normalized_df
    
    def _combine_barcodes(self, df: pd.DataFrame, barcode_columns: List[str]) -> pd.DataFrame:
        """
        Combine normalized barcode data into single profile
        """
        # Create combined dataframe
        combined_df = df[['species', 'phylum', 'genus']].copy()
        
        # Sum normalized abundances across barcodes
        combined_df['total_combined'] = df[barcode_columns].sum(axis=1)
        
        # Add 'total' column for compatibility with existing PDF generator
        combined_df['total'] = combined_df['total_combined']
        
        # Remove species with zero combined abundance
        combined_df = combined_df[combined_df['total_combined'] > 0].copy()
        
        # Sort by abundance (descending)
        combined_df = combined_df.sort_values('total_combined', ascending=False).reset_index(drop=True)
        
        logger.info(f"Combined {len(barcode_columns)} barcodes into {len(combined_df)} species")
        return combined_df
    
    def _calculate_species_overlap(self, df: pd.DataFrame, barcode_columns: List[str]) -> Dict[str, int]:
        """
        Calculate species overlap between barcodes
        """
        overlap_stats = {}
        
        # Species present in each barcode
        species_per_barcode = {}
        for col in barcode_columns:
            species_per_barcode[col] = set(df[df[col] > 0]['species'].tolist())
        
        # Calculate overlaps
        all_species = set()
        for species_set in species_per_barcode.values():
            all_species.update(species_set)
        
        overlap_stats['total_unique_species'] = len(all_species)
        overlap_stats['species_per_barcode'] = {k: len(v) for k, v in species_per_barcode.items()}
        
        # Common species across all barcodes
        if species_per_barcode:
            common_species = set.intersection(*species_per_barcode.values())
            overlap_stats['common_to_all_barcodes'] = len(common_species)
        else:
            overlap_stats['common_to_all_barcodes'] = 0
        
        return overlap_stats
    
    def _calculate_normalization_stats(self, original_df: pd.DataFrame, 
                                     normalized_df: pd.DataFrame, 
                                     barcode_columns: List[str]) -> Dict[str, Any]:
        """
        Calculate normalization statistics
        """
        stats = {
            'method': self.config.normalization_method,
            'original_totals': {},
            'normalized_totals': {},
            'scaling_factors': {}
        }
        
        for col in barcode_columns:
            original_total = original_df[col].sum()
            normalized_total = normalized_df[col].sum()
            
            stats['original_totals'][col] = float(original_total)
            stats['normalized_totals'][col] = float(normalized_total)
            
            if original_total > 0:
                stats['scaling_factors'][col] = float(normalized_total / original_total)
            else:
                stats['scaling_factors'][col] = 0.0
        
        return stats


def aggregate_barcodes_for_patient(csv_path: str, barcode_columns: List[str], 
                                 patient_name: str = "Unknown",
                                 config: AggregationConfig = None) -> AggregationResult:
    """
    Convenience function to aggregate barcodes for a single patient
    
    Args:
        csv_path: Path to CSV with barcode data
        barcode_columns: List of barcode columns to combine
        patient_name: Patient name for logging
        config: Aggregation configuration
        
    Returns:
        AggregationResult with combined data and validation
    """
    aggregator = EnhancedBarcodeAggregator(config)
    return aggregator.aggregate_barcodes(csv_path, barcode_columns, patient_name)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    config = AggregationConfig(
        normalization_method="relative_abundance",
        correlation_threshold=0.7,
        p_value_threshold=0.05
    )
    
    # Test with sample data
    sample_csv = "../notebooks/pipeline_results/processed_abundance.csv"
    barcodes = ["barcode04", "barcode05", "barcode06"]
    
    if Path(sample_csv).exists():
        result = aggregate_barcodes_for_patient(sample_csv, barcodes, "Montana", config)
        
        if result.success:
            print(f"✅ Aggregation successful!")
            print(f"   Combined species: {len(result.combined_data)}")
            print(f"   Total reads: {result.combined_total_reads}")
            print(f"   Correlations: {result.validation_result.correlations}")
        else:
            print(f"❌ Aggregation failed: {result.error_message}")
    else:
        print(f"Sample CSV not found: {sample_csv}")