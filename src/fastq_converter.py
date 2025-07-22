"""
FASTQ to CSV Converter Module

Processes FASTQ files containing 16S rRNA sequences and converts them
to the CSV format required by the Equine Microbiome Reporter.
"""

import gzip
import pandas as pd
import numpy as np
from Bio import SeqIO
from collections import defaultdict
from typing import Dict, List, Optional
from pathlib import Path


class FASTQtoCSVConverter:
    """Convert FASTQ files to CSV format for microbiome analysis"""
    
    def __init__(self, taxonomy_db_path: Optional[str] = None):
        """
        Initialize converter
        
        Args:
            taxonomy_db_path: Path to taxonomy database (e.g., SILVA, Greengenes)
        """
        self.taxonomy_db_path = taxonomy_db_path
        self.sequences = {}
        self.abundances = defaultdict(lambda: defaultdict(int))
        
    def process_fastq_files(self, 
                          fastq_files: List[str], 
                          sample_names: Optional[List[str]] = None,
                          min_quality: int = 20,
                          min_length: int = 200) -> pd.DataFrame:
        """
        Process multiple FASTQ files and create abundance table
        
        Args:
            fastq_files: List of FASTQ file paths
            sample_names: List of sample names (default: use file names)
            min_quality: Minimum average quality score
            min_length: Minimum sequence length
            
        Returns:
            DataFrame in the format expected by the reporter
        """
        if sample_names is None:
            sample_names = [Path(f).stem for f in fastq_files]
            
        # Process each FASTQ file
        for i, (fastq_file, sample_name) in enumerate(zip(fastq_files, sample_names)):
            print(f"Processing {sample_name} ({i+1}/{len(fastq_files)})...")
            self._process_single_fastq(fastq_file, sample_name, min_quality, min_length)
        
        # Convert to DataFrame
        df = self._create_abundance_dataframe(sample_names)
        
        return df
    
    def _process_single_fastq(self, fastq_file: str, sample_name: str,
                            min_quality: int, min_length: int):
        """Process a single FASTQ file"""
        # Open file appropriately
        if fastq_file.endswith('.gz'):
            handle = gzip.open(fastq_file, "rt")
        else:
            handle = open(fastq_file, "r")
        
        sequences_processed = 0
        sequences_passed = 0
        
        for record in SeqIO.parse(handle, "fastq"):
            sequences_processed += 1
            
            # Quality filtering
            avg_quality = np.mean(record.letter_annotations["phred_quality"])
            if avg_quality < min_quality or len(record.seq) < min_length:
                continue
                
            sequences_passed += 1
            
            # Simple sequence clustering (in practice, use DADA2, VSEARCH, or similar)
            # For this example, we'll use exact sequence matching
            seq_str = str(record.seq)
            self.sequences[seq_str] = self.sequences.get(seq_str, 0) + 1
            self.abundances[sample_name][seq_str] += 1
        
        handle.close()
        print(f"  - Processed {sequences_processed} sequences, {sequences_passed} passed QC")
    
    def _create_abundance_dataframe(self, sample_names: List[str]) -> pd.DataFrame:
        """Create abundance DataFrame in the expected format"""
        # For this example, we'll create mock taxonomy assignments
        # In practice, you would use a real taxonomy classifier
        
        rows = []
        
        # Mock taxonomy data (replace with real taxonomy assignment)
        mock_taxonomy = self._get_mock_taxonomy()
        
        # Create rows for each taxonomy assignment
        for i, (seq, total_count) in enumerate(sorted(self.sequences.items(), 
                                                     key=lambda x: x[1], 
                                                     reverse=True)[:100]):
            # Use mock taxonomy (cycling through available entries)
            tax = mock_taxonomy[i % len(mock_taxonomy)]
            
            row = {
                "species": tax["species"],
                "phylum": tax["phylum"],
                "genus": tax["genus"],
                "family": tax["family"],
                "class": tax["class"],
                "order": tax["order"]
            }
            
            # Add abundance data for each sample
            for sample_name in sample_names:
                # Use barcode naming convention
                barcode_col = f"barcode{sample_name.split('_')[-1]}" \
                             if '_' in sample_name else f"barcode{i+50}"
                row[barcode_col] = self.abundances[sample_name].get(seq, 0)
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Ensure all required columns are present
        required_cols = ["species", "phylum", "genus", "family", "class", "order"]
        barcode_cols = [col for col in df.columns if col.startswith("barcode")]
        
        # Reorder columns
        df = df[required_cols + barcode_cols]
        
        return df
    
    def _get_mock_taxonomy(self) -> List[Dict]:
        """Get mock taxonomy data for demonstration purposes"""
        return [
            {"species": "Brachybacterium sp. Z12", "phylum": "Actinomycetota", 
             "genus": "Brachybacterium", "family": "Dermabacteraceae",
             "class": "Actinomycetes", "order": "Micrococcales"},
            {"species": "Brachybacterium vulturis", "phylum": "Actinomycetota",
             "genus": "Brachybacterium", "family": "Dermabacteraceae",
             "class": "Actinomycetes", "order": "Micrococcales"},
            {"species": "Glutamicibacter arilaitensis", "phylum": "Actinomycetota",
             "genus": "Glutamicibacter", "family": "Micrococcaceae",
             "class": "Actinomycetes", "order": "Micrococcales"},
            {"species": "Lysinibacillus sp. 2017", "phylum": "Bacillota",
             "genus": "Lysinibacillus", "family": "Bacillaceae",
             "class": "Bacilli", "order": "Bacillales"},
            {"species": "Kurthia zopfii", "phylum": "Bacillota",
             "genus": "Kurthia", "family": "Planococcaceae",
             "class": "Bacilli", "order": "Bacillales"},
            {"species": "Solibacillus sp. FSL H8-0523", "phylum": "Bacillota",
             "genus": "Solibacillus", "family": "Planococcaceae",
             "class": "Bacilli", "order": "Bacillales"},
            {"species": "Weissella confusa", "phylum": "Bacillota",
             "genus": "Weissella", "family": "Lactobacillaceae",
             "class": "Bacilli", "order": "Lactobacillales"},
            {"species": "Streptococcus equinus", "phylum": "Bacillota",
             "genus": "Streptococcus", "family": "Streptococcaceae",
             "class": "Bacilli", "order": "Lactobacillales"},
            {"species": "Sphingobacterium sp. ML3W", "phylum": "Bacteroidota",
             "genus": "Sphingobacterium", "family": "Sphingobacteriaceae",
             "class": "Sphingobacteriia", "order": "Sphingobacteriales"},
            {"species": "Acinetobacter baumannii", "phylum": "Pseudomonadota",
             "genus": "Acinetobacter", "family": "Moraxellaceae",
             "class": "Gammaproteobacteria", "order": "Moraxellales"},
            {"species": "Comamonas aquatica", "phylum": "Pseudomonadota",
             "genus": "Comamonas", "family": "Comamonadaceae",
             "class": "Betaproteobacteria", "order": "Burkholderiales"},
        ]
    
    def save_to_csv(self, df: pd.DataFrame, output_path: str):
        """Save DataFrame to CSV file"""
        df.to_csv(output_path, index=False)
        print(f"\nSaved abundance table to {output_path}")
        print(f"Shape: {df.shape}")
        print(f"Samples: {[col for col in df.columns if col.startswith('barcode')]}")
    
    def get_processing_stats(self) -> Dict:
        """Get statistics about the processing"""
        total_sequences = sum(self.sequences.values())
        unique_sequences = len(self.sequences)
        
        sample_stats = {}
        for sample, seqs in self.abundances.items():
            sample_stats[sample] = {
                'total_reads': sum(seqs.values()),
                'unique_sequences': len(seqs)
            }
        
        return {
            'total_sequences': total_sequences,
            'unique_sequences': unique_sequences,
            'samples_processed': len(self.abundances),
            'sample_statistics': sample_stats
        }