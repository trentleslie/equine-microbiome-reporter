#!/usr/bin/env python3
"""
CSV Format Validator for Microbiome Data
Validates CSV files against the Equine Microbiome Reporter format specification
"""

import pandas as pd
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CSVFormatValidator:
    """Validates microbiome CSV files against format specification"""
    
    # Required columns for different formats
    REQUIRED_COLUMNS_FULL = {'species', 'phylum', 'genus', 'family', 'class', 'order'}
    REQUIRED_COLUMNS_SIMPLE = {'species', 'phylum', 'genus'}
    
    # Reference phyla that must match exactly
    REFERENCE_PHYLA = {
        'Actinomycetota', 'Bacillota', 'Bacteroidota', 
        'Pseudomonadota', 'Fibrobacterota'
    }
    
    # Barcode column pattern
    BARCODE_PATTERN = re.compile(r'^barcode\d+$')
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.errors = []
        self.warnings = []
        self.info = []
        self.df = None
        
    def validate(self) -> bool:
        """Run all validation checks"""
        print(f"\n{'='*60}")
        print(f"Validating CSV: {self.csv_path}")
        print(f"{'='*60}\n")
        
        # Check file exists
        if not self._check_file_exists():
            return False
            
        # Load CSV
        if not self._load_csv():
            return False
            
        # Run validation checks
        self._check_required_columns()
        self._check_barcode_columns()
        self._check_data_types()
        self._check_phylum_names()
        self._check_species_format()
        self._check_data_integrity()
        self._check_minimum_requirements()
        
        # Report results
        self._report_results()
        
        return len(self.errors) == 0
    
    def _check_file_exists(self) -> bool:
        """Check if file exists"""
        if not self.csv_path.exists():
            self.errors.append(f"File not found: {self.csv_path}")
            return False
        return True
    
    def _load_csv(self) -> bool:
        """Load CSV file"""
        try:
            self.df = pd.read_csv(self.csv_path)
            self.info.append(f"Successfully loaded CSV with {len(self.df)} rows and {len(self.df.columns)} columns")
            return True
        except Exception as e:
            self.errors.append(f"Failed to load CSV: {str(e)}")
            return False
    
    def _check_required_columns(self):
        """Check for required columns"""
        columns_lower = {col.lower() for col in self.df.columns}
        
        # Check which format we have
        if all(col in columns_lower for col in self.REQUIRED_COLUMNS_FULL):
            self.info.append("Detected FULL format with all taxonomic columns")
            format_type = "FULL"
        elif all(col in columns_lower for col in self.REQUIRED_COLUMNS_SIMPLE):
            self.info.append("Detected SIMPLE format with essential columns")
            format_type = "SIMPLE"
        else:
            missing = self.REQUIRED_COLUMNS_SIMPLE - columns_lower
            self.errors.append(f"Missing required columns: {missing}")
            return
            
        # Check for case sensitivity issues
        for col in self.df.columns:
            if col.lower() in ['species', 'phylum', 'genus', 'family', 'class', 'order']:
                if col != col.lower():
                    self.warnings.append(f"Column '{col}' uses mixed case - lowercase recommended")
    
    def _check_barcode_columns(self):
        """Check for barcode columns"""
        barcode_cols = [col for col in self.df.columns if self.BARCODE_PATTERN.match(col)]
        
        if not barcode_cols:
            self.errors.append("No barcode columns found (expected format: barcode[N])")
        else:
            self.info.append(f"Found {len(barcode_cols)} barcode columns: {', '.join(sorted(barcode_cols)[:5])}{'...' if len(barcode_cols) > 5 else ''}")
            
            # Check if barcode columns have valid data
            for col in barcode_cols:
                if self.df[col].dtype not in ['int64', 'float64']:
                    self.errors.append(f"Barcode column '{col}' contains non-numeric data")
                elif (self.df[col] < 0).any():
                    self.errors.append(f"Barcode column '{col}' contains negative values")
    
    def _check_data_types(self):
        """Check data types of columns"""
        # Get column names in lowercase for checking
        col_map = {col.lower(): col for col in self.df.columns}
        
        # Check string columns
        string_cols = ['species', 'phylum', 'genus', 'family', 'class', 'order']
        for col in string_cols:
            if col in col_map:
                actual_col = col_map[col]
                if self.df[actual_col].dtype != 'object':
                    self.warnings.append(f"Column '{actual_col}' should contain text data")
    
    def _check_phylum_names(self):
        """Check phylum names against reference"""
        col_map = {col.lower(): col for col in self.df.columns}
        
        if 'phylum' in col_map:
            phylum_col = col_map['phylum']
            unique_phyla = set(self.df[phylum_col].dropna().unique())
            
            # Check reference phyla
            ref_phyla_in_data = unique_phyla & self.REFERENCE_PHYLA
            self.info.append(f"Reference phyla found: {', '.join(sorted(ref_phyla_in_data))}")
            
            # Check for non-reference phyla
            non_ref_phyla = unique_phyla - self.REFERENCE_PHYLA
            if non_ref_phyla:
                self.info.append(f"Additional phyla found: {', '.join(sorted(non_ref_phyla))}")
            
            # Warn if missing important reference phyla
            missing_ref = self.REFERENCE_PHYLA - unique_phyla
            if missing_ref:
                self.warnings.append(f"Missing reference phyla: {', '.join(sorted(missing_ref))}")
    
    def _check_species_format(self):
        """Check species name format"""
        col_map = {col.lower(): col for col in self.df.columns}
        
        if 'species' in col_map:
            species_col = col_map['species']
            species_sample = self.df[species_col].dropna().head(10)
            
            # Check for scientific nomenclature
            invalid_species = []
            for species in species_sample:
                if not isinstance(species, str) or len(species.split()) < 2:
                    invalid_species.append(str(species))
            
            if invalid_species:
                self.warnings.append(f"Some species names may not follow scientific nomenclature: {', '.join(invalid_species[:3])}")
    
    def _check_data_integrity(self):
        """Check data integrity"""
        # Check for empty rows
        empty_rows = self.df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            self.errors.append(f"Found {empty_rows} completely empty rows")
        
        # Check barcode data
        barcode_cols = [col for col in self.df.columns if self.BARCODE_PATTERN.match(col)]
        if barcode_cols:
            # Check if all barcodes are zero
            for col in barcode_cols:
                if (self.df[col] == 0).all():
                    self.warnings.append(f"Barcode column '{col}' contains only zeros")
                else:
                    non_zero_count = (self.df[col] > 0).sum()
                    total_count = self.df[col].sum()
                    self.info.append(f"Barcode '{col}': {non_zero_count} species, {int(total_count)} total reads")
    
    def _check_minimum_requirements(self):
        """Check minimum data requirements"""
        # Check minimum species count
        col_map = {col.lower(): col for col in self.df.columns}
        if 'species' in col_map:
            species_count = self.df[col_map['species']].nunique()
            if species_count < 10:
                self.warnings.append(f"Only {species_count} unique species found (recommend >= 10)")
            else:
                self.info.append(f"Found {species_count} unique species")
        
        # Check if any barcode has sufficient data
        barcode_cols = [col for col in self.df.columns if self.BARCODE_PATTERN.match(col)]
        has_sufficient_data = False
        for col in barcode_cols:
            if (self.df[col] > 0).sum() >= 10:
                has_sufficient_data = True
                break
        
        if not has_sufficient_data:
            self.warnings.append("No barcode column has >= 10 species with non-zero counts")
    
    def _report_results(self):
        """Report validation results"""
        print("VALIDATION RESULTS")
        print("-" * 60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if self.info:
            print(f"\nℹ️  INFO ({len(self.info)}):")
            for info in self.info:
                print(f"   - {info}")
        
        print("\n" + "-" * 60)
        if self.errors:
            print("❌ VALIDATION FAILED")
        else:
            print("✅ VALIDATION PASSED")
        print("=" * 60 + "\n")
    
    def test_with_csv_processor(self, barcode_column: str = None) -> bool:
        """Test if CSV works with CSVProcessor"""
        print(f"\nTesting compatibility with CSVProcessor...")
        
        try:
            # Try to import CSVProcessor
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.csv_processor import CSVProcessor
            from src.data_models import MicrobiomeData
            
            # Find a barcode column if not specified
            if not barcode_column:
                barcode_cols = [col for col in self.df.columns if self.BARCODE_PATTERN.match(col)]
                if barcode_cols:
                    # Pick the one with most non-zero values
                    barcode_column = max(barcode_cols, key=lambda col: (self.df[col] > 0).sum())
                else:
                    print("   ❌ No barcode columns found for testing")
                    return False
            
            print(f"   Testing with barcode column: {barcode_column}")
            
            # Initialize processor
            processor = CSVProcessor(str(self.csv_path), barcode_column)
            
            # Process data
            microbiome_data = processor.process()
            
            # Report results
            print(f"   ✅ Successfully processed!")
            print(f"   - Species count: {microbiome_data.total_species_count}")
            print(f"   - Dysbiosis index: {microbiome_data.dysbiosis_index}")
            print(f"   - Dysbiosis category: {microbiome_data.dysbiosis_category}")
            print(f"   - Phyla found: {', '.join(microbiome_data.phylum_distribution.keys())}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to process: {str(e)}")
            return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python validate_csv_format.py <csv_file> [barcode_column]")
        print("\nExample:")
        print("  python validate_csv_format.py data/sample_1.csv")
        print("  python validate_csv_format.py data/25_04_23\\ bact.csv barcode59")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    barcode_column = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Run validation
    validator = CSVFormatValidator(csv_file)
    is_valid = validator.validate()
    
    # Test with CSVProcessor if valid
    if is_valid:
        validator.test_with_csv_processor(barcode_column)
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()