#!/usr/bin/env python3
"""
Convert Kraken2 report files to CSV format for Equine Microbiome Reporter.

This script converts .kreport files from Kraken2 into the CSV format
expected by the report generator, with columns: species, barcode[N], phylum, genus.
"""

import pandas as pd
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional


def parse_kreport(kreport_file: str) -> pd.DataFrame:
    """
    Parse a Kraken2 report file into a DataFrame.
    
    Args:
        kreport_file: Path to the .kreport file
        
    Returns:
        DataFrame with parsed Kraken2 report data
    """
    columns = ['percentage', 'reads_clade', 'reads_taxon', 'rank', 'taxid', 'name']
    
    data = []
    with open(kreport_file, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 6:
                # Extract data from each line
                percentage = float(parts[0])
                reads_clade = int(parts[1])
                reads_taxon = int(parts[2])
                rank = parts[3]
                taxid = parts[4]
                name = parts[5].strip()
                
                data.append({
                    'percentage': percentage,
                    'reads_clade': reads_clade,
                    'reads_taxon': reads_taxon,
                    'rank': rank,
                    'taxid': taxid,
                    'name': name
                })
    
    return pd.DataFrame(data)


def extract_taxonomy_mapping(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Extract taxonomy mapping from Kraken2 report.
    
    Creates a mapping of species to their phylum and genus.
    
    Args:
        df: DataFrame with parsed Kraken2 report
        
    Returns:
        Dictionary mapping species names to their taxonomy
    """
    taxonomy = {}
    current_phylum = None
    current_genus = None
    
    for _, row in df.iterrows():
        rank = row['rank']
        name = row['name']
        
        if rank == 'P':  # Phylum
            current_phylum = name
        elif rank == 'G':  # Genus
            current_genus = name
        elif rank == 'S':  # Species
            if current_phylum and current_genus:
                taxonomy[name] = {
                    'phylum': current_phylum,
                    'genus': current_genus
                }
    
    return taxonomy


def kreport_to_csv(kreport_file: str, output_csv: str, barcode_num: int = 1) -> None:
    """
    Convert Kraken2 report to CSV format expected by report generator.
    
    Args:
        kreport_file: Path to input .kreport file
        output_csv: Path to output CSV file
        barcode_num: Barcode number for the sample
    """
    # Parse the kreport file
    df = parse_kreport(kreport_file)
    
    # Filter for species-level data
    species_df = df[df['rank'] == 'S'].copy()
    
    # Get taxonomy mapping
    taxonomy = extract_taxonomy_mapping(df)
    
    # Build output dataframe
    output_data = []
    for _, row in species_df.iterrows():
        species_name = row['name']
        percentage = row['percentage']
        
        # Map common phylum names to expected format
        phylum_mapping = {
            'Firmicutes': 'Bacillota',
            'Bacteroidetes': 'Bacteroidota',
            'Proteobacteria': 'Pseudomonadota',
            'Actinobacteria': 'Actinomycetota',
            'Fibrobacteres': 'Fibrobacterota'
        }
        
        if species_name in taxonomy:
            phylum = taxonomy[species_name]['phylum']
            genus = taxonomy[species_name]['genus']
            
            # Apply phylum name mapping
            phylum = phylum_mapping.get(phylum, phylum)
            
            output_data.append({
                'species': species_name,
                f'barcode{barcode_num}': percentage,
                'phylum': phylum,
                'genus': genus
            })
    
    # Create output DataFrame
    output_df = pd.DataFrame(output_data)
    
    # Sort by abundance (descending)
    output_df = output_df.sort_values(f'barcode{barcode_num}', ascending=False)
    
    # Save to CSV
    output_df.to_csv(output_csv, index=False)
    print(f"✅ Converted {kreport_file} to {output_csv}")
    print(f"   Found {len(output_df)} species")
    print(f"   Top 5 species:")
    for i, row in output_df.head().iterrows():
        print(f"   - {row['species']}: {row[f'barcode{barcode_num}']:.2f}%")


def merge_multiple_samples(kreport_files: List[str], output_csv: str) -> None:
    """
    Merge multiple Kraken2 reports into a single CSV.
    
    Args:
        kreport_files: List of paths to .kreport files
        output_csv: Path to output CSV file
    """
    all_data = {}
    all_taxonomy = {}
    
    # Process each kreport file
    for i, kreport_file in enumerate(kreport_files, 1):
        df = parse_kreport(kreport_file)
        species_df = df[df['rank'] == 'S']
        taxonomy = extract_taxonomy_mapping(df)
        
        # Store data for each species
        for _, row in species_df.iterrows():
            species_name = row['name']
            percentage = row['percentage']
            
            if species_name not in all_data:
                all_data[species_name] = {}
            all_data[species_name][f'barcode{i}'] = percentage
            
            if species_name not in all_taxonomy and species_name in taxonomy:
                all_taxonomy[species_name] = taxonomy[species_name]
    
    # Build output dataframe
    output_data = []
    phylum_mapping = {
        'Firmicutes': 'Bacillota',
        'Bacteroidetes': 'Bacteroidota',
        'Proteobacteria': 'Pseudomonadota',
        'Actinobacteria': 'Actinomycetota',
        'Fibrobacteres': 'Fibrobacterota'
    }
    
    for species_name, abundances in all_data.items():
        row = {'species': species_name}
        
        # Add barcode columns
        for i in range(1, len(kreport_files) + 1):
            barcode_col = f'barcode{i}'
            row[barcode_col] = abundances.get(barcode_col, 0.0)
        
        # Add taxonomy
        if species_name in all_taxonomy:
            phylum = all_taxonomy[species_name]['phylum']
            genus = all_taxonomy[species_name]['genus']
            row['phylum'] = phylum_mapping.get(phylum, phylum)
            row['genus'] = genus
        else:
            row['phylum'] = 'Unknown'
            row['genus'] = 'Unknown'
        
        output_data.append(row)
    
    # Create output DataFrame
    output_df = pd.DataFrame(output_data)
    
    # Sort by total abundance
    barcode_cols = [f'barcode{i}' for i in range(1, len(kreport_files) + 1)]
    output_df['total'] = output_df[barcode_cols].sum(axis=1)
    output_df = output_df.sort_values('total', ascending=False)
    output_df = output_df.drop('total', axis=1)
    
    # Save to CSV
    output_df.to_csv(output_csv, index=False)
    print(f"✅ Merged {len(kreport_files)} samples into {output_csv}")
    print(f"   Total species found: {len(output_df)}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert Kraken2 report files to CSV format for Equine Microbiome Reporter'
    )
    parser.add_argument(
        'input',
        nargs='+',
        help='Input .kreport file(s)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output CSV file'
    )
    parser.add_argument(
        '-b', '--barcode',
        type=int,
        default=1,
        help='Barcode number for single sample (default: 1)'
    )
    
    args = parser.parse_args()
    
    if len(args.input) == 1:
        # Single sample
        kreport_to_csv(args.input[0], args.output, args.barcode)
    else:
        # Multiple samples
        merge_multiple_samples(args.input, args.output)


if __name__ == '__main__':
    main()