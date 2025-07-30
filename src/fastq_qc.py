"""
FASTQ Quality Control Module

Analyzes FASTQ files for quality metrics including Phred scores,
read length distribution, GC content, and base composition.
"""

import gzip
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
from collections import defaultdict
from typing import Dict, Optional
from pathlib import Path


class FASTQQualityControl:
    """Class for performing quality control on FASTQ files"""
    
    def __init__(self, fastq_path: str, sample_size: int = 10000):
        """
        Initialize QC analyzer
        
        Args:
            fastq_path: Path to FASTQ file (can be gzipped)
            sample_size: Number of reads to sample for QC (default 10000)
        """
        self.fastq_path = fastq_path
        self.sample_size = sample_size
        self.is_gzipped = fastq_path.endswith('.gz')
        self.qc_results = {}
        
    def run_qc(self) -> Dict:
        """Run complete quality control analysis"""
        print(f"Running QC on {self.fastq_path}...")
        
        # Open file appropriately
        if self.is_gzipped:
            handle = gzip.open(self.fastq_path, "rt")
        else:
            handle = open(self.fastq_path, "r")
        
        # Initialize metrics
        quality_scores = []
        read_lengths = []
        gc_contents = []
        base_composition = defaultdict(int)
        total_bases = 0
        
        # Process reads
        for i, record in enumerate(SeqIO.parse(handle, "fastq")):
            if i >= self.sample_size:
                break
                
            # Quality scores
            quality_scores.extend(record.letter_annotations["phred_quality"])
            
            # Read length
            read_lengths.append(len(record.seq))
            
            # GC content
            gc_contents.append(gc_fraction(record.seq) * 100)
            
            # Base composition
            for base in str(record.seq):
                base_composition[base] += 1
                total_bases += 1
        
        handle.close()
        
        # Calculate statistics
        self.qc_results = {
            'mean_quality': np.mean(quality_scores),
            'median_quality': np.median(quality_scores),
            'min_quality': np.min(quality_scores),
            'max_quality': np.max(quality_scores),
            'quality_scores': quality_scores,
            'mean_read_length': np.mean(read_lengths),
            'median_read_length': np.median(read_lengths),
            'read_lengths': read_lengths,
            'mean_gc_content': np.mean(gc_contents),
            'gc_contents': gc_contents,
            'base_composition': {base: count/total_bases*100 
                               for base, count in base_composition.items()},
            'total_reads_analyzed': i + 1
        }
        
        return self.qc_results
    
    def plot_quality_metrics(self, save_path: Optional[str] = None):
        """Generate QC plots"""
        if not self.qc_results:
            raise ValueError("Run QC analysis first using run_qc()")
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('FASTQ Quality Control Report', fontsize=16)
        
        # Plot 1: Quality score distribution
        axes[0, 0].hist(self.qc_results['quality_scores'], bins=40, alpha=0.7, color='blue')
        axes[0, 0].axvline(x=20, color='red', linestyle='--', label='Q20 threshold')
        axes[0, 0].axvline(x=30, color='green', linestyle='--', label='Q30 threshold')
        axes[0, 0].set_xlabel('Phred Quality Score')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Quality Score Distribution')
        axes[0, 0].legend()
        
        # Plot 2: Read length distribution
        axes[0, 1].hist(self.qc_results['read_lengths'], bins=30, alpha=0.7, color='green')
        axes[0, 1].set_xlabel('Read Length (bp)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Read Length Distribution')
        
        # Plot 3: GC content distribution
        axes[1, 0].hist(self.qc_results['gc_contents'], bins=30, alpha=0.7, color='orange')
        axes[1, 0].set_xlabel('GC Content (%)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('GC Content Distribution')
        
        # Plot 4: Base composition
        bases = list(self.qc_results['base_composition'].keys())
        percentages = list(self.qc_results['base_composition'].values())
        axes[1, 1].bar(bases, percentages, alpha=0.7)
        axes[1, 1].set_xlabel('Base')
        axes[1, 1].set_ylabel('Percentage (%)')
        axes[1, 1].set_title('Base Composition')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
        
    def print_summary(self):
        """Print QC summary statistics"""
        if not self.qc_results:
            raise ValueError("Run QC analysis first using run_qc()")
            
        print("\n=== FASTQ Quality Control Summary ===")
        print(f"Total reads analyzed: {self.qc_results['total_reads_analyzed']:,}")
        print(f"\nQuality Scores:")
        print(f"  Mean: {self.qc_results['mean_quality']:.1f}")
        print(f"  Median: {self.qc_results['median_quality']:.1f}")
        print(f"  Range: {self.qc_results['min_quality']}-{self.qc_results['max_quality']}")
        print(f"\nRead Lengths:")
        print(f"  Mean: {self.qc_results['mean_read_length']:.1f} bp")
        print(f"  Median: {self.qc_results['median_read_length']:.1f} bp")
        print(f"\nGC Content:")
        print(f"  Mean: {self.qc_results['mean_gc_content']:.1f}%")
        print(f"\nBase Composition:")
        for base, pct in sorted(self.qc_results['base_composition'].items()):
            print(f"  {base}: {pct:.1f}%")
    
    def get_qc_summary(self) -> Dict:
        """Get a concise summary of QC results"""
        if not self.qc_results:
            raise ValueError("Run QC analysis first using run_qc()")
            
        return {
            'total_reads': self.qc_results['total_reads_analyzed'],
            'mean_quality': round(self.qc_results['mean_quality'], 1),
            'mean_read_length': round(self.qc_results['mean_read_length'], 1),
            'mean_gc_content': round(self.qc_results['mean_gc_content'], 1),
            'q20_percentage': sum(1 for q in self.qc_results['quality_scores'] if q >= 20) / len(self.qc_results['quality_scores']) * 100,
            'q30_percentage': sum(1 for q in self.qc_results['quality_scores'] if q >= 30) / len(self.qc_results['quality_scores']) * 100
        }