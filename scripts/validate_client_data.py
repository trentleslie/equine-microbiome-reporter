#!/usr/bin/env python3
"""
Client Data Validation Script for HippoVet+

Validates historical client data against the new clinical filtering system
to ensure accuracy and measure improvement metrics.

Usage:
    python validate_client_data.py --historical [CSV] --filtered [CSV] --output [REPORT]
"""

import pandas as pd
import numpy as np
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from clinical_filter import ClinicalFilter
from curation_interface import CurationInterface


class ClientDataValidator:
    """Validate clinical filtering against historical client decisions."""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize validator with output directory.
        
        Args:
            output_dir: Directory for validation reports
        """
        self.output_dir = output_dir or Path("validation_reports")
        self.output_dir.mkdir(exist_ok=True)
        self.filter = ClinicalFilter()
        self.metrics = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1_score': [],
            'time_saved': [],
            'consistency': []
        }
    
    def load_historical_data(self, file_path: Path) -> pd.DataFrame:
        """
        Load historical manually-curated data.
        
        Args:
            file_path: Path to historical CSV file
            
        Returns:
            DataFrame with historical decisions
        """
        df = pd.read_csv(file_path)
        
        # Standardize column names
        column_mapping = {
            'Species': 'species',
            'Abundance': 'percentage',
            'Reads': 'abundance_reads',
            'Include': 'included_manual',
            'Kingdom': 'kingdom'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Convert inclusion column to boolean
        if 'included_manual' in df.columns:
            df['included_manual'] = df['included_manual'].astype(str).str.upper() == 'YES'
        
        print(f"Loaded {len(df)} historical records from {file_path.name}")
        return df
    
    def apply_automated_filtering(self, df: pd.DataFrame, database: str) -> pd.DataFrame:
        """
        Apply automated clinical filtering to data.
        
        Args:
            df: Input DataFrame
            database: Database name for filtering rules
            
        Returns:
            DataFrame with automated filtering decisions
        """
        # Apply clinical filter
        df_filtered = self.filter.process_results(df.copy(), database, auto_exclude=False)
        
        # Mark automated decisions
        df_filtered['included_auto'] = df_filtered['clinical_relevance'].isin(['high', 'moderate'])
        
        return df_filtered
    
    def calculate_agreement_metrics(self, df_comparison: pd.DataFrame) -> Dict:
        """
        Calculate agreement between manual and automated decisions.
        
        Args:
            df_comparison: DataFrame with both manual and auto decisions
            
        Returns:
            Dictionary of agreement metrics
        """
        if 'included_manual' not in df_comparison.columns or 'included_auto' not in df_comparison.columns:
            return {'error': 'Missing required columns for comparison'}
        
        # True/False Positives/Negatives
        tp = ((df_comparison['included_manual'] == True) & 
              (df_comparison['included_auto'] == True)).sum()
        fp = ((df_comparison['included_manual'] == False) & 
              (df_comparison['included_auto'] == True)).sum()
        tn = ((df_comparison['included_manual'] == False) & 
              (df_comparison['included_auto'] == False)).sum()
        fn = ((df_comparison['included_manual'] == True) & 
              (df_comparison['included_auto'] == False)).sum()
        
        # Calculate metrics
        total = len(df_comparison)
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Agreement rate
        agreement = ((df_comparison['included_manual'] == df_comparison['included_auto']).sum() / total) if total > 0 else 0
        
        return {
            'total_species': total,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'agreement_rate': agreement,
            'manual_included': df_comparison['included_manual'].sum(),
            'auto_included': df_comparison['included_auto'].sum()
        }
    
    def identify_disagreements(self, df_comparison: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Identify species where manual and automated decisions disagree.
        
        Args:
            df_comparison: DataFrame with comparison data
            
        Returns:
            Tuple of (false_positives, false_negatives) DataFrames
        """
        # False positives: Auto included but manual excluded
        false_positives = df_comparison[
            (df_comparison['included_auto'] == True) & 
            (df_comparison['included_manual'] == False)
        ].copy()
        
        # False negatives: Manual included but auto excluded
        false_negatives = df_comparison[
            (df_comparison['included_auto'] == False) & 
            (df_comparison['included_manual'] == True)
        ].copy()
        
        return false_positives, false_negatives
    
    def analyze_time_savings(self, df_comparison: pd.DataFrame, 
                           minutes_per_species: float = 0.5) -> Dict:
        """
        Calculate time savings from automation.
        
        Args:
            df_comparison: DataFrame with comparison data
            minutes_per_species: Average manual review time per species
            
        Returns:
            Dictionary with time analysis
        """
        total_species = len(df_comparison)
        
        # Species that don't need review (high confidence auto decisions)
        high_confidence = df_comparison[
            df_comparison['clinical_relevance'].isin(['high', 'excluded'])
        ]
        auto_decided = len(high_confidence)
        
        # Species requiring review (moderate relevance)
        need_review = total_species - auto_decided
        
        # Time calculations
        manual_time = total_species * minutes_per_species
        auto_time = need_review * minutes_per_species  # Only review moderate
        time_saved = manual_time - auto_time
        percent_saved = (time_saved / manual_time * 100) if manual_time > 0 else 0
        
        return {
            'total_species': total_species,
            'auto_decided': auto_decided,
            'need_review': need_review,
            'manual_time_minutes': manual_time,
            'auto_time_minutes': auto_time,
            'time_saved_minutes': time_saved,
            'percent_time_saved': percent_saved
        }
    
    def generate_validation_report(self, metrics: Dict, disagreements: Tuple,
                                  time_analysis: Dict, database: str) -> Path:
        """
        Generate comprehensive validation report.
        
        Args:
            metrics: Agreement metrics
            disagreements: Tuple of disagreement DataFrames
            time_analysis: Time savings analysis
            database: Database name
            
        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"validation_report_{database}_{timestamp}.md"
        
        false_positives, false_negatives = disagreements
        
        with open(report_path, 'w') as f:
            f.write(f"# Clinical Filtering Validation Report\n")
            f.write(f"**Database**: {database}\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary Metrics\n\n")
            f.write(f"- **Total Species**: {metrics['total_species']}\n")
            f.write(f"- **Agreement Rate**: {metrics['agreement_rate']:.1%}\n")
            f.write(f"- **Accuracy**: {metrics['accuracy']:.1%}\n")
            f.write(f"- **Precision**: {metrics['precision']:.1%}\n")
            f.write(f"- **Recall**: {metrics['recall']:.1%}\n")
            f.write(f"- **F1 Score**: {metrics['f1_score']:.3f}\n\n")
            
            f.write("## Confusion Matrix\n\n")
            f.write("| | Manual Include | Manual Exclude |\n")
            f.write("|---|---|---|\n")
            f.write(f"| **Auto Include** | {metrics['true_positives']} | {metrics['false_positives']} |\n")
            f.write(f"| **Auto Exclude** | {metrics['false_negatives']} | {metrics['true_negatives']} |\n\n")
            
            f.write("## Time Savings Analysis\n\n")
            f.write(f"- **Manual Review Time**: {time_analysis['manual_time_minutes']:.1f} minutes\n")
            f.write(f"- **Automated Review Time**: {time_analysis['auto_time_minutes']:.1f} minutes\n")
            f.write(f"- **Time Saved**: {time_analysis['time_saved_minutes']:.1f} minutes ({time_analysis['percent_time_saved']:.1f}%)\n")
            f.write(f"- **Auto-decided Species**: {time_analysis['auto_decided']}/{time_analysis['total_species']}\n\n")
            
            if len(false_positives) > 0:
                f.write("## False Positives (Auto included, Manual excluded)\n\n")
                f.write("| Species | Abundance | Relevance | Notes |\n")
                f.write("|---------|-----------|-----------|-------|\n")
                for _, row in false_positives.head(10).iterrows():
                    f.write(f"| {row['species']} | {row.get('percentage', 0):.2f}% | "
                           f"{row.get('clinical_relevance', 'unknown')} | "
                           f"{row.get('curation_notes', '')} |\n")
                if len(false_positives) > 10:
                    f.write(f"\n*... and {len(false_positives) - 10} more*\n")
            
            if len(false_negatives) > 0:
                f.write("\n## False Negatives (Manual included, Auto excluded)\n\n")
                f.write("| Species | Abundance | Relevance | Notes |\n")
                f.write("|---------|-----------|-----------|-------|\n")
                for _, row in false_negatives.head(10).iterrows():
                    f.write(f"| {row['species']} | {row.get('percentage', 0):.2f}% | "
                           f"{row.get('clinical_relevance', 'unknown')} | "
                           f"{row.get('curation_notes', '')} |\n")
                if len(false_negatives) > 10:
                    f.write(f"\n*... and {len(false_negatives) - 10} more*\n")
            
            f.write("\n## Recommendations\n\n")
            
            # Generate recommendations based on metrics
            if metrics['agreement_rate'] > 0.9:
                f.write("✅ **Excellent agreement** - System ready for production use\n")
            elif metrics['agreement_rate'] > 0.8:
                f.write("⚠️ **Good agreement** - Minor adjustments recommended\n")
            else:
                f.write("❌ **Low agreement** - Significant tuning required\n")
            
            if metrics['precision'] < 0.9:
                f.write("- Consider tightening inclusion criteria to reduce false positives\n")
            if metrics['recall'] < 0.9:
                f.write("- Consider relaxing exclusion criteria to reduce false negatives\n")
            
            if len(false_positives) > len(false_negatives):
                f.write("- System tends to over-include species - adjust thresholds upward\n")
            elif len(false_negatives) > len(false_positives):
                f.write("- System tends to over-exclude species - adjust thresholds downward\n")
        
        print(f"Validation report saved to: {report_path}")
        return report_path
    
    def create_visualization(self, metrics: Dict, database: str) -> Path:
        """
        Create visualization of validation metrics.
        
        Args:
            metrics: Validation metrics
            database: Database name
            
        Returns:
            Path to saved visualization
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'Clinical Filtering Validation - {database}', fontsize=16)
        
        # Confusion Matrix
        ax = axes[0, 0]
        conf_matrix = np.array([
            [metrics['true_positives'], metrics['false_positives']],
            [metrics['false_negatives'], metrics['true_negatives']]
        ])
        sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=['Manual Include', 'Manual Exclude'],
                   yticklabels=['Auto Include', 'Auto Exclude'])
        ax.set_title('Confusion Matrix')
        
        # Metrics Bar Chart
        ax = axes[0, 1]
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
        metric_values = [metrics['accuracy'], metrics['precision'], 
                        metrics['recall'], metrics['f1_score']]
        bars = ax.bar(metric_names, metric_values, color=['green', 'blue', 'orange', 'red'])
        ax.set_ylim(0, 1)
        ax.set_ylabel('Score')
        ax.set_title('Performance Metrics')
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{value:.2f}', ha='center', va='bottom')
        
        # Inclusion Comparison
        ax = axes[1, 0]
        categories = ['Manual', 'Automated']
        included_counts = [metrics['manual_included'], metrics['auto_included']]
        ax.bar(categories, included_counts, color=['lightblue', 'lightgreen'])
        ax.set_ylabel('Species Count')
        ax.set_title('Inclusion Comparison')
        
        # Agreement Pie Chart
        ax = axes[1, 1]
        agreement_data = [
            metrics['true_positives'] + metrics['true_negatives'],
            metrics['false_positives'] + metrics['false_negatives']
        ]
        ax.pie(agreement_data, labels=['Agreement', 'Disagreement'],
              autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
        ax.set_title('Decision Agreement')
        
        plt.tight_layout()
        
        # Save figure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fig_path = self.output_dir / f"validation_plot_{database}_{timestamp}.png"
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Visualization saved to: {fig_path}")
        return fig_path
    
    def validate_batch(self, historical_files: List[Path], database: str) -> Dict:
        """
        Validate multiple historical files.
        
        Args:
            historical_files: List of historical data files
            database: Database name
            
        Returns:
            Aggregated validation metrics
        """
        all_metrics = []
        all_time_savings = []
        
        for file_path in historical_files:
            print(f"\nValidating {file_path.name}...")
            
            # Load historical data
            df_historical = self.load_historical_data(file_path)
            
            # Apply automated filtering
            df_filtered = self.apply_automated_filtering(df_historical, database)
            
            # Calculate metrics
            metrics = self.calculate_agreement_metrics(df_filtered)
            all_metrics.append(metrics)
            
            # Calculate time savings
            time_analysis = self.analyze_time_savings(df_filtered)
            all_time_savings.append(time_analysis)
        
        # Aggregate results
        aggregated = {
            'files_processed': len(historical_files),
            'avg_accuracy': np.mean([m['accuracy'] for m in all_metrics]),
            'avg_precision': np.mean([m['precision'] for m in all_metrics]),
            'avg_recall': np.mean([m['recall'] for m in all_metrics]),
            'avg_f1_score': np.mean([m['f1_score'] for m in all_metrics]),
            'avg_agreement': np.mean([m['agreement_rate'] for m in all_metrics]),
            'total_time_saved': sum(t['time_saved_minutes'] for t in all_time_savings),
            'avg_percent_saved': np.mean([t['percent_time_saved'] for t in all_time_savings])
        }
        
        print(f"\nBatch Validation Complete:")
        print(f"  Average Agreement: {aggregated['avg_agreement']:.1%}")
        print(f"  Average F1 Score: {aggregated['avg_f1_score']:.3f}")
        print(f"  Total Time Saved: {aggregated['total_time_saved']:.1f} minutes")
        
        return aggregated


def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Validate clinical filtering against historical data"
    )
    parser.add_argument(
        "--historical",
        type=Path,
        required=True,
        help="Path to historical manually-curated CSV file(s)"
    )
    parser.add_argument(
        "--database",
        choices=["PlusPFP-16", "EuPathDB", "Viral"],
        required=True,
        help="Database type for filtering rules"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for validation reports"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Create visualization plots"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ClientDataValidator(output_dir=args.output)
    
    # Load historical data
    df_historical = validator.load_historical_data(args.historical)
    
    # Apply automated filtering
    print(f"\nApplying {args.database} filtering rules...")
    df_filtered = validator.apply_automated_filtering(df_historical, args.database)
    
    # Calculate metrics
    print("\nCalculating agreement metrics...")
    metrics = validator.calculate_agreement_metrics(df_filtered)
    
    # Identify disagreements
    false_positives, false_negatives = validator.identify_disagreements(df_filtered)
    
    # Analyze time savings
    time_analysis = validator.analyze_time_savings(df_filtered)
    
    # Generate report
    report_path = validator.generate_validation_report(
        metrics, (false_positives, false_negatives), 
        time_analysis, args.database
    )
    
    # Create visualization if requested
    if args.visualize:
        viz_path = validator.create_visualization(metrics, args.database)
        print(f"Visualization saved to: {viz_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Database: {args.database}")
    print(f"Total Species: {metrics['total_species']}")
    print(f"Agreement Rate: {metrics['agreement_rate']:.1%}")
    print(f"F1 Score: {metrics['f1_score']:.3f}")
    print(f"Time Saved: {time_analysis['time_saved_minutes']:.1f} minutes ({time_analysis['percent_time_saved']:.1f}%)")
    print(f"\nFull report: {report_path}")
    
    # Return success if agreement > 80%
    sys.exit(0 if metrics['agreement_rate'] > 0.8 else 1)


if __name__ == "__main__":
    main()