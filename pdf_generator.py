#!/usr/bin/env python3
"""
Automated PDF Report Generator for Equine Microbiome Analysis
Generates comprehensive fecal examination reports from CSV data
"""

import argparse
import textwrap
from datetime import datetime
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


class MicrobiomeReportGenerator:
    """Generates PDF reports for microbiome analysis from CSV data."""

    def __init__(self, csv_file: str, barcode_column: str = 'barcode59'):
        """
        Initialize the report generator.

        Args:
            csv_file: Path to the CSV file containing microbiome data
            barcode_column: Name of the barcode column to analyze
        """
        self.csv_file = csv_file
        self.barcode_column = barcode_column
        self.df = self._load_data()
        if self.df is not None:
            self.total_count = self.df[self.barcode_column].sum()
        else:
            self.total_count = 0

    def _load_data(self) -> Optional[pd.DataFrame]:
        """Load and preprocess the CSV data."""
        try:
            df = pd.read_csv(self.csv_file)
            df.columns = df.columns.str.strip()
            return df
        except FileNotFoundError:
            print(f"Error: CSV file not found at {self.csv_file}")
            return None

    def _calculate_species_percentages(self) -> pd.DataFrame:
        """Calculate species percentages for the specified barcode."""
        species_data = self.df[self.df[self.barcode_column] > 0].copy()
        species_data['percentage'] = (
            species_data[self.barcode_column] / self.total_count * 100
        )
        return species_data.sort_values('percentage', ascending=False)[
            ['species', 'genus', 'phylum', self.barcode_column, 'percentage']
        ]

    def _calculate_phylum_distribution(self) -> Dict[str, float]:
        """Calculate phylum distribution percentages."""
        phylum_counts = self.df[self.df[self.barcode_column] > 0].groupby('phylum')[self.barcode_column].sum()
        return (phylum_counts / self.total_count * 100).to_dict()

    def _create_species_chart(self, ax: plt.Axes, species_data: pd.DataFrame) -> None:
        """Create horizontal bar chart for species distribution."""
        top_species = species_data.head(30)
        y_pos = np.arange(len(top_species))
        ax.barh(y_pos, top_species['percentage'], color='#4CAF50', edgecolor='black', linewidth=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top_species['species'], fontsize=8)
        ax.set_xlabel('Percentage (%)', fontsize=10)
        ax.set_title('Species Distribution', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        for i, (_, row) in enumerate(top_species.iterrows()):
            ax.text(row['percentage'] + 0.1, i, f"{row['percentage']:.2f}%", va='center', fontsize=8)

    def _create_phylum_chart(self, ax: plt.Axes, phylum_dist: Dict[str, float]) -> None:
        """Create pie chart for phylum distribution."""
        sorted_phylums = sorted(phylum_dist.items(), key=lambda x: x[1], reverse=True)
        labels = [f"{phylum}\n{pct:.1f}%" for phylum, pct in sorted_phylums]
        sizes = [pct for _, pct in sorted_phylums]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
        ax.pie(sizes, labels=labels, colors=colors[:len(sizes)], autopct='', startangle=90)
        ax.set_title('Phylum Distribution', fontsize=12, fontweight='bold')

    def _add_patient_info(self, fig: plt.Figure, patient_info: Dict[str, str]) -> None:
        """Add patient information to the report."""
        info_text = ""
        for key, value in patient_info.items():
            wrapped_value = '\n'.join(textwrap.wrap(str(value), width=40))
            info_text += f'{key.replace("_", " ").title()}: {wrapped_value}\n'
        fig.text(0.05, 0.85, info_text, va='top', ha='left', fontsize=10, bbox=dict(boxstyle='round,pad=0.5', fc='aliceblue', alpha=0.5))

    def _add_analysis_summary(self, fig: plt.Figure, species_data: pd.DataFrame, phylum_dist: Dict[str, float]) -> None:
        """Add analysis summary to the report."""
        dominant_phylum = max(phylum_dist, key=phylum_dist.get) if phylum_dist else 'N/A'
        summary_lines = [
            'Analysis Summary:',
            f'- Total Species Detected: {len(species_data)}',
            f'- Dominant Phylum: {dominant_phylum}',
            '- Top 5 Species:'
        ]
        for _, row in species_data.head(5).iterrows():
            summary_lines.append(f"    - {row['species']} ({row['percentage']:.2f}%)")
        summary_text = "\n".join(summary_lines)
        fig.text(0.5, 0.45, summary_text, va='top', ha='left', fontsize=10, bbox=dict(boxstyle='round,pad=0.5', fc='lightyellow', alpha=0.5))

    def _add_species_table(self, pdf: PdfPages, species_data: pd.DataFrame) -> None:
        """Add a detailed species table to the report."""
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis('tight')
        ax.axis('off')
        table_data = [
            [
                row['species'],
                row['genus'],
                row['phylum'],
                f"{row[self.barcode_column]}",
                f"{row['percentage']:.2f}%"
            ]
            for _, row in species_data.iterrows()
        ]
        table = ax.table(cellText=table_data, colLabels=['Species', 'Genus', 'Phylum', 'Count', 'Percentage'], cellLoc='left', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        for i in range(len(table_data) + 1):
            for j in range(5):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        plt.title('Detailed Species Analysis', fontsize=14, fontweight='bold', pad=20)
        pdf.savefig(fig)
        plt.close()

    def generate_report(self, output_file: str, patient_info: Optional[Dict[str, str]] = None) -> None:
        """
        Generate the complete PDF report.

        Args:
            output_file: Path for the output PDF file
            patient_info: Dictionary containing patient information
        """
        if self.df is None:
            return

        patient_info = patient_info or {}
        species_data = self._calculate_species_percentages()
        phylum_dist = self._calculate_phylum_distribution()

        with PdfPages(output_file) as pdf:
            fig = plt.figure(figsize=(11, 8.5))
            fig.suptitle('COMPREHENSIVE FECAL EXAMINATION REPORT', fontsize=16, fontweight='bold', y=0.98)
            self._add_patient_info(fig, patient_info)
            ax1 = plt.subplot2grid((2, 2), (0, 0), colspan=2)
            self._create_species_chart(ax1, species_data)
            ax2 = plt.subplot2grid((2, 2), (1, 0))
            self._create_phylum_chart(ax2, phylum_dist)
            self._add_analysis_summary(fig, species_data, phylum_dist)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            pdf.savefig(fig)
            plt.close()
            self._add_species_table(pdf, species_data)

        print(f"Report generated successfully: {output_file}")


def main():
    """Main function to run the report generator."""
    parser = argparse.ArgumentParser(description='Generate PDF report from microbiome CSV data')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('-o', '--output', default='microbiome_report.pdf', help='Output PDF filename')
    parser.add_argument('-b', '--barcode', default='barcode59', help='Barcode column to analyze')
    parser.add_argument('--name', help='Patient name')
    parser.add_argument('--species', help='Patient species')
    parser.add_argument('--age', help='Patient age')
    parser.add_argument('--sample', help='Sample number')
    args = parser.parse_args()

    patient_info = {
        'Patient Name': args.name,
        'Patient Species': args.species,
        'Patient Age': args.age,
        'Sample Number': args.sample,
        'Date Received': datetime.now().strftime('%d.%m.%Y'),
        'Date Analyzed': datetime.now().strftime('%d.%m.%Y'),
        'Analyzed By': 'Automated System',
        'Requested By': 'N/A'
    }

    generator = MicrobiomeReportGenerator(args.csv_file, args.barcode)
    generator.generate_report(args.output, patient_info)


if __name__ == '__main__':
    main()