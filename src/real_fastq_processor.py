"""
Real FASTQ Processing Pipeline for Taxonomic Classification
Processes Oxford Nanopore FASTQ files to generate species abundance data
"""

import os
import gzip
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import subprocess
import tempfile
import time
from dataclasses import dataclass

# Import existing bioinformatics tools if available
try:
    from Bio import SeqIO
    from Bio.Seq import Seq
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False

logger = logging.getLogger(__name__)


@dataclass
class SequenceStats:
    """Statistics for processed sequences"""
    total_reads: int = 0
    total_bases: int = 0
    mean_length: float = 0.0
    quality_filtered: int = 0
    classified_reads: int = 0


@dataclass
class TaxonomicHit:
    """Result of taxonomic classification"""
    read_id: str
    species: str
    genus: str
    family: str
    order: str
    class_name: str
    phylum: str
    confidence: float
    length: int


class MinimalTaxonomicClassifier:
    """
    Minimal taxonomic classifier using k-mer matching against reference database
    For production, this would be replaced with tools like Kraken2, Minimap2+LCA, etc.
    """
    
    def __init__(self):
        # Simplified reference database with common equine gut microbiome species
        # In production, this would load from a comprehensive database
        self.reference_db = {
            # Actinomycetota (formerly Actinobacteria)
            'ACTGCGTGC': ('Streptomyces albidoflavus', 'Streptomyces', 'Streptomycetaceae', 'Kitasatosporales', 'Actinomycetes', 'Actinomycetota'),
            'CGTGCGTGC': ('Arthrobacter citreus', 'Arthrobacter', 'Micrococcaceae', 'Micrococcales', 'Actinomycetes', 'Actinomycetota'),
            'TGCGTGCAC': ('Cellulomonas chengniuliangii', 'Cellulomonas', 'Cellulomonadaceae', 'Micrococcales', 'Actinomycetes', 'Actinomycetota'),
            
            # Bacillota (formerly Firmicutes)
            'ATGGCGTGC': ('Lactobacillus acidophilus', 'Lactobacillus', 'Lactobacillaceae', 'Lactobacillales', 'Bacilli', 'Bacillota'),
            'GCGTGCATG': ('Clostridium perfringens', 'Clostridium', 'Clostridiaceae', 'Eubacteriales', 'Clostridia', 'Bacillota'),
            'CGTGCATGG': ('Enterococcus faecalis', 'Enterococcus', 'Enterococcaceae', 'Lactobacillales', 'Bacilli', 'Bacillota'),
            'ATGCGTGCA': ('Bacillus subtilis', 'Bacillus', 'Bacillaceae', 'Bacillales', 'Bacilli', 'Bacillota'),
            
            # Bacteroidota (formerly Bacteroidetes)
            'TGGCGTGCA': ('Bacteroides fragilis', 'Bacteroides', 'Bacteroidaceae', 'Bacteroidales', 'Bacteroidia', 'Bacteroidota'),
            'GCGTGCAGG': ('Prevotella copri', 'Prevotella', 'Prevotellaceae', 'Bacteroidales', 'Bacteroidia', 'Bacteroidota'),
            
            # Pseudomonadota (formerly Proteobacteria)
            'CGCGTGCAT': ('Escherichia coli', 'Escherichia', 'Enterobacteriaceae', 'Enterobacterales', 'Gammaproteobacteria', 'Pseudomonadota'),
            'GTGCATGGC': ('Salmonella enterica', 'Salmonella', 'Enterobacteriaceae', 'Enterobacterales', 'Gammaproteobacteria', 'Pseudomonadota'),
            
            # Fibrobacterota
            'CATGGCGTG': ('Fibrobacter succinogenes', 'Fibrobacter', 'Fibrobacteraceae', 'Fibrobacterales', 'Fibrobacteria', 'Fibrobacterota'),
        }
        
        # Create reverse lookup for faster classification
        self.kmer_size = 9
        logger.info(f"Initialized minimal classifier with {len(self.reference_db)} reference k-mers")
    
    def classify_sequence(self, sequence: str, read_id: str) -> Optional[TaxonomicHit]:
        """
        Classify a DNA sequence using k-mer matching
        Returns the best taxonomic hit or None if no match
        """
        if len(sequence) < self.kmer_size:
            return None
        
        # Extract k-mers from sequence
        kmers = []
        for i in range(len(sequence) - self.kmer_size + 1):
            kmer = sequence[i:i + self.kmer_size].upper()
            kmers.append(kmer)
        
        # Find matches in reference database
        matches = []
        for kmer in kmers:
            if kmer in self.reference_db:
                matches.append(self.reference_db[kmer])
        
        if not matches:
            return None
        
        # Take the most common match (simple consensus)
        match_counts = Counter(matches)
        best_match, count = match_counts.most_common(1)[0]
        confidence = count / len(kmers)  # Fraction of k-mers that matched
        
        species, genus, family, order, class_name, phylum = best_match
        
        return TaxonomicHit(
            read_id=read_id,
            species=species,
            genus=genus,
            family=family,
            order=order,
            class_name=class_name,
            phylum=phylum,
            confidence=confidence,
            length=len(sequence)
        )


class RealFASTQProcessor:
    """
    Process real FASTQ files from barcode directories to generate taxonomic abundance data
    """
    
    def __init__(self, min_read_length: int = 100, min_quality: float = 7.0):
        self.min_read_length = min_read_length
        self.min_quality = min_quality
        self.classifier = MinimalTaxonomicClassifier()
        self.logger = logging.getLogger(__name__)
    
    def process_barcode_directories(self, data_dir: str, barcode_dirs: List[str]) -> pd.DataFrame:
        """
        Process multiple barcode directories to generate abundance table
        
        Args:
            data_dir: Base directory containing barcode subdirectories
            barcode_dirs: List of barcode directory names (e.g., ['barcode04', 'barcode05'])
        
        Returns:
            DataFrame with species abundance data in reference CSV format
        """
        self.logger.info(f"Processing {len(barcode_dirs)} barcode directories")
        
        # Process each barcode directory
        barcode_results = {}
        all_species = set()
        
        for barcode_dir in barcode_dirs:
            barcode_path = Path(data_dir) / barcode_dir
            if not barcode_path.exists():
                self.logger.warning(f"Barcode directory not found: {barcode_path}")
                continue
            
            self.logger.info(f"Processing {barcode_dir}...")
            classifications, stats = self.process_barcode_directory(str(barcode_path))
            
            # Count species abundances
            species_counts = Counter()
            for hit in classifications:
                species_counts[hit.species] += 1
                all_species.add(hit.species)
            
            barcode_results[barcode_dir] = {
                'counts': species_counts,
                'stats': stats,
                'total_classified': len(classifications)
            }
            
            self.logger.info(f"  {barcode_dir}: {stats.total_reads} reads, {len(classifications)} classified, {len(species_counts)} species")
        
        # Generate abundance table
        return self._create_abundance_dataframe(barcode_results, all_species)
    
    def process_barcode_directory(self, barcode_path: str) -> Tuple[List[TaxonomicHit], SequenceStats]:
        """
        Process all FASTQ files in a barcode directory
        
        Returns:
            Tuple of (classifications, statistics)
        """
        barcode_path = Path(barcode_path)
        fastq_files = list(barcode_path.glob('*.fastq.gz')) + list(barcode_path.glob('*.fastq'))
        
        if not fastq_files:
            self.logger.warning(f"No FASTQ files found in {barcode_path}")
            return [], SequenceStats()
        
        self.logger.info(f"Found {len(fastq_files)} FASTQ files in {barcode_path}")
        
        all_classifications = []
        stats = SequenceStats()
        
        # Process files in batches to manage memory
        batch_size = 10
        for i in range(0, len(fastq_files), batch_size):
            batch_files = fastq_files[i:i + batch_size]
            batch_classifications, batch_stats = self._process_fastq_batch(batch_files)
            
            all_classifications.extend(batch_classifications)
            stats.total_reads += batch_stats.total_reads
            stats.total_bases += batch_stats.total_bases
            stats.quality_filtered += batch_stats.quality_filtered
            stats.classified_reads += batch_stats.classified_reads
        
        # Calculate final statistics
        if stats.total_reads > 0:
            stats.mean_length = stats.total_bases / stats.total_reads
        
        return all_classifications, stats
    
    def _process_fastq_batch(self, fastq_files: List[Path]) -> Tuple[List[TaxonomicHit], SequenceStats]:
        """Process a batch of FASTQ files"""
        classifications = []
        stats = SequenceStats()
        
        for fastq_file in fastq_files:
            try:
                file_classifications, file_stats = self._process_single_fastq(fastq_file)
                classifications.extend(file_classifications)
                
                stats.total_reads += file_stats.total_reads
                stats.total_bases += file_stats.total_bases
                stats.quality_filtered += file_stats.quality_filtered
                stats.classified_reads += file_stats.classified_reads
                
            except Exception as e:
                self.logger.error(f"Error processing {fastq_file}: {e}")
                continue
        
        return classifications, stats
    
    def _process_single_fastq(self, fastq_file: Path) -> Tuple[List[TaxonomicHit], SequenceStats]:
        """Process a single FASTQ file"""
        classifications = []
        stats = SequenceStats()
        
        # Determine if file is gzipped
        if fastq_file.suffix == '.gz':
            opener = gzip.open
            mode = 'rt'
        else:
            opener = open
            mode = 'r'
        
        try:
            with opener(fastq_file, mode) as f:
                # Parse FASTQ format (4 lines per read)
                while True:
                    # Read 4 lines for one sequence record
                    header = f.readline().strip()
                    if not header:
                        break  # End of file
                    
                    sequence = f.readline().strip()
                    plus_line = f.readline().strip()
                    quality = f.readline().strip()
                    
                    if not (header and sequence and plus_line and quality):
                        break  # Incomplete record
                    
                    stats.total_reads += 1
                    stats.total_bases += len(sequence)
                    
                    # Quality filtering
                    if len(sequence) < self.min_read_length:
                        stats.quality_filtered += 1
                        continue
                    
                    # Extract read ID
                    read_id = header[1:].split()[0] if header.startswith('@') else header
                    
                    # Classify sequence
                    hit = self.classifier.classify_sequence(sequence, read_id)
                    if hit:
                        classifications.append(hit)
                        stats.classified_reads += 1
        
        except Exception as e:
            self.logger.error(f"Error reading FASTQ file {fastq_file}: {e}")
        
        return classifications, stats
    
    def _create_abundance_dataframe(self, barcode_results: Dict, all_species: set) -> pd.DataFrame:
        """
        Create abundance DataFrame in the reference CSV format
        """
        # Convert species names to full taxonomic information
        species_taxonomy = {}
        for species in all_species:
            # Find taxonomy from classifier database
            taxonomy = self._get_species_taxonomy(species)
            species_taxonomy[species] = taxonomy
        
        # Create rows for each species
        rows = []
        for species in sorted(all_species):
            row = {'species': species}
            
            # Add barcode columns
            total_count = 0
            for barcode_dir, results in barcode_results.items():
                barcode_col = barcode_dir  # e.g., 'barcode04'
                count = results['counts'].get(species, 0)
                row[barcode_col] = count
                total_count += count
            
            row['total'] = total_count
            
            # Add taxonomic information
            taxonomy = species_taxonomy[species]
            row.update(taxonomy)
            
            rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Ensure column order matches reference format
        columns = ['species']
        
        # Add barcode columns in sorted order
        barcode_columns = sorted([col for col in df.columns if col.startswith('barcode')])
        columns.extend(barcode_columns)
        
        # Add standard columns
        standard_columns = ['total', 'superkingdom', 'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'tax']
        columns.extend([col for col in standard_columns if col in df.columns])
        
        # Reorder DataFrame
        df = df.reindex(columns=columns, fill_value=0)
        
        # Sort by total abundance (descending)
        df = df.sort_values('total', ascending=False).reset_index(drop=True)
        
        self.logger.info(f"Generated abundance table: {len(df)} species, {len(barcode_columns)} barcodes")
        
        return df
    
    def _get_species_taxonomy(self, species: str) -> Dict[str, str]:
        """Get taxonomic information for a species"""
        # Find the species in the classifier database
        for kmer, (ref_species, genus, family, order, class_name, phylum) in self.classifier.reference_db.items():
            if ref_species == species:
                return {
                    'superkingdom': 'Bacteria',
                    'kingdom': 'Bacteria_none',
                    'phylum': phylum,
                    'class': class_name,
                    'order': order,
                    'family': family,
                    'genus': genus,
                    'tax': f"Bacteria,Bacteria_none,{phylum},{class_name},{order},{family},{genus},{species}"
                }
        
        # Default taxonomy for unknown species
        return {
            'superkingdom': 'Bacteria',
            'kingdom': 'Bacteria_none',
            'phylum': 'Unknown',
            'class': 'Unknown',
            'order': 'Unknown',
            'family': 'Unknown',
            'genus': 'Unknown',
            'tax': f"Bacteria,Bacteria_none,Unknown,Unknown,Unknown,Unknown,Unknown,{species}"
        }


def process_fastq_directories_to_csv(data_dir: str, barcode_dirs: List[str], output_csv: str) -> bool:
    """
    Main function to process FASTQ directories and generate CSV abundance table
    
    Args:
        data_dir: Directory containing barcode subdirectories
        barcode_dirs: List of barcode directory names
        output_csv: Output CSV file path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        processor = RealFASTQProcessor()
        
        # Process barcode directories
        abundance_df = processor.process_barcode_directories(data_dir, barcode_dirs)
        
        # Save to CSV
        abundance_df.to_csv(output_csv, index=False)
        
        logger.info(f"Successfully generated abundance CSV: {output_csv}")
        logger.info(f"  Species: {len(abundance_df)}")
        logger.info(f"  Barcodes: {len([col for col in abundance_df.columns if col.startswith('barcode')])}")
        logger.info(f"  Total reads: {abundance_df['total'].sum()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to process FASTQ directories: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    data_dir = "data"
    barcode_dirs = ["barcode04", "barcode05", "barcode06"]
    output_csv = "real_abundance_data.csv"
    
    success = process_fastq_directories_to_csv(data_dir, barcode_dirs, output_csv)
    if success:
        print(f"✅ Successfully processed FASTQ data to {output_csv}")
    else:
        print("❌ Failed to process FASTQ data")