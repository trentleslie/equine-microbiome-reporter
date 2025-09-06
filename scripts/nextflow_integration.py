#!/usr/bin/env python3
"""
Nextflow/Epi2Me Integration Script for HippoVet+

Processes Kraken2 output from Epi2Me workflow and applies clinical filtering.
Compatible with wf-metagenomics pipeline output structure.

Usage:
    python nextflow_integration.py --input /path/to/epi2me/output --database PlusPFP-16
"""

import argparse
import pandas as pd
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from clinical_filter import ClinicalFilter
from curation_interface import CurationInterface
from kraken2_classifier import TaxonomyMapper


class NextflowProcessor:
    """Process Epi2Me/Nextflow output with clinical filtering."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize processor for Nextflow output.
        
        Args:
            output_dir: Epi2Me instance output directory
        """
        self.output_dir = Path(output_dir)
        self.filter = ClinicalFilter()
        self.curator = CurationInterface()
        self.taxonomy_mapper = TaxonomyMapper()
        
        # Validate output directory structure
        self._validate_directory()
    
    def _validate_directory(self) -> None:
        """Validate Epi2Me output directory structure."""
        expected_paths = [
            self.output_dir / "wf-metagenomics-report.html",
            self.output_dir / "kraken2-classified"
        ]
        
        missing = [p for p in expected_paths if not p.exists()]
        if missing:
            print(f"Warning: Missing expected paths: {missing}")
    
    def find_kraken_reports(self) -> Dict[str, Path]:
        """
        Find all Kraken2 report files in Epi2Me output.
        
        Returns:
            Dictionary mapping barcode to report path
        """
        reports = {}
        
        # Check kraken2-classified directory
        kraken_dir = self.output_dir / "kraken2-classified"
        if kraken_dir.exists():
            for report_file in kraken_dir.glob("*.kreport2"):
                barcode = report_file.stem.replace(".kreport2", "")
                reports[barcode] = report_file
        
        # Also check for kreport files
        for report_file in self.output_dir.glob("**/*.kreport"):
            barcode = report_file.stem
            if barcode not in reports:
                reports[barcode] = report_file
        
        print(f"Found {len(reports)} Kraken2 reports")
        return reports
    
    def parse_kreport(self, report_path: Path) -> pd.DataFrame:
        """
        Parse Kraken2 report file from Epi2Me.
        
        Args:
            report_path: Path to .kreport or .kreport2 file
            
        Returns:
            DataFrame with parsed results
        """
        results = []
        
        with open(report_path, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 6:
                        percentage = float(parts[0])
                        num_reads_covered = int(parts[1])
                        num_reads_assigned = int(parts[2])
                        rank_code = parts[3]
                        ncbi_taxid = int(parts[4])
                        name = parts[5].strip()
                        
                        # Extract kingdom from hierarchy
                        kingdom = self._extract_kingdom(name, rank_code)
                        
                        results.append({
                            'percentage': percentage,
                            'abundance_reads': num_reads_assigned,
                            'reads_covered': num_reads_covered,
                            'rank': rank_code,
                            'taxid': ncbi_taxid,
                            'species': name,
                            'kingdom': kingdom,
                            'genus': self.taxonomy_mapper.extract_genus(name),
                            'phylum': self.taxonomy_mapper.map_to_phylum(name)
                        })
        
        return pd.DataFrame(results)
    
    def _extract_kingdom(self, name: str, rank_code: str) -> str:
        """
        Extract kingdom from species name and rank.
        
        Args:
            name: Species/taxon name
            rank_code: Kraken2 rank code
            
        Returns:
            Kingdom name
        """
        # Simple heuristic based on common patterns
        name_lower = name.lower()
        
        if 'virus' in name_lower or 'phage' in name_lower:
            return 'Viruses'
        elif 'bacteria' in name_lower or rank_code in ['D', 'P', 'C', 'O', 'F', 'G', 'S']:
            # Check for bacterial ranks
            if any(term in name_lower for term in ['plant', 'fungi', 'metazoa', 'eukaryota']):
                return 'Eukaryota'
            return 'Bacteria'
        elif 'archaea' in name_lower:
            return 'Archaea'
        elif any(term in name_lower for term in ['fungi', 'fungus']):
            return 'Fungi'
        elif any(term in name_lower for term in ['plant', 'viridiplantae']):
            return 'Plantae'
        else:
            return 'Unknown'
    
    def process_database(self, database_name: str, report_paths: Dict[str, Path]) -> Dict:
        """
        Process all samples for a specific database with clinical filtering.
        
        Args:
            database_name: Name of the database (PlusPFP-16, EuPathDB, Viral)
            report_paths: Dictionary of barcode to report paths
            
        Returns:
            Processing results dictionary
        """
        results = {
            'database': database_name,
            'samples_processed': [],
            'filtered_results': {},
            'curation_files': []
        }
        
        for barcode, report_path in report_paths.items():
            print(f"\nProcessing {barcode}...")
            
            # Parse Kraken2 report
            df_raw = self.parse_kreport(report_path)
            print(f"  Raw species count: {len(df_raw)}")
            
            # Filter to species level only
            df_species = df_raw[df_raw['rank'] == 'S'].copy()
            print(f"  Species-level entries: {len(df_species)}")
            
            # Apply clinical filtering
            df_filtered = self.filter.process_results(
                df_species, 
                database_name,
                auto_exclude=True
            )
            print(f"  After clinical filtering: {len(df_filtered)}")
            
            # Store results
            results['samples_processed'].append(barcode)
            results['filtered_results'][barcode] = df_filtered
            
            # Export for manual review if needed
            if self.filter.database_configs[database_name].require_manual_review:
                excel_path = self.curator.export_for_excel_review(
                    df_filtered, 
                    f"{database_name}_{barcode}"
                )
                results['curation_files'].append(excel_path)
                print(f"  Exported for review: {excel_path}")
        
        return results
    
    def generate_integration_report(self, results: Dict) -> Path:
        """
        Generate summary report of processing.
        
        Args:
            results: Processing results dictionary
            
        Returns:
            Path to report file
        """
        report_path = self.curator.output_dir / "nextflow_integration_report.json"
        
        # Add statistics
        results['statistics'] = {
            'total_samples': len(results['samples_processed']),
            'total_species_before': sum(
                len(df) for df in results['filtered_results'].values()
            ),
            'review_files_created': len(results['curation_files'])
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nIntegration report saved: {report_path}")
        return report_path


def main():
    """Main entry point for Nextflow integration."""
    parser = argparse.ArgumentParser(
        description="Process Epi2Me/Nextflow output with clinical filtering"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to Epi2Me instance output directory"
    )
    parser.add_argument(
        "--database",
        choices=["PlusPFP-16", "EuPathDB", "Viral"],
        default="PlusPFP-16",
        help="Database type for filtering rules"
    )
    parser.add_argument(
        "--output",
        help="Output directory for results (default: curation_results)"
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = NextflowProcessor(Path(args.input))
    
    if args.output:
        processor.curator.output_dir = Path(args.output)
        processor.curator.output_dir.mkdir(exist_ok=True)
    
    # Find Kraken2 reports
    report_paths = processor.find_kraken_reports()
    
    if not report_paths:
        print("Error: No Kraken2 reports found in the specified directory")
        sys.exit(1)
    
    # Process with clinical filtering
    results = processor.process_database(args.database, report_paths)
    
    # Generate report
    report_path = processor.generate_integration_report(results)
    
    print("\n" + "="*50)
    print("Processing Complete!")
    print(f"Database: {args.database}")
    print(f"Samples processed: {len(results['samples_processed'])}")
    print(f"Review files created: {len(results['curation_files'])}")
    print("\nNext steps:")
    print("1. Review Excel files in curation_results/")
    print("2. Mark species to include/exclude")
    print("3. Run final report generation with reviewed data")


if __name__ == "__main__":
    main()