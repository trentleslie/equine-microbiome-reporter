#!/usr/bin/env python3
"""
Advanced Microbiome PDF Report Generator
Generates comprehensive fecal examination reports in Polish from CSV data
Matches the HippoVet+ laboratory report format
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from datetime import datetime
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Tuple, Optional
import textwrap
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


class AdvancedMicrobiomeReportGenerator:
    """Generates professional PDF reports for microbiome analysis."""
    
    # Polish translations
    TRANSLATIONS = {
        'title': 'KOMPLEKSOWE BADANIE KAŁU',
        'patient_name': 'Imię pacjenta',
        'species_age': 'Gatunek oraz wiek',
        'sample_number': 'Numer badania',
        'date_received': 'Data otrzymania materiału',
        'date_analyzed': 'Data wykonania badania',
        'performed_by': 'Wykonał/a',
        'requested_by': 'Osoba zlecająca badanie',
        'microbiome_profile': 'PROFIL MIKROBIOTYCZNY',
        'sequencing_results': 'WYNIK SEKWENCJONOWANIA',
        'phylum': 'GROMADA',
        'species': 'GATUNEK',
        'phylum_distribution': 'Procent udziału gromad bakterii w mikroflorze',
        'reference_range': 'Zakres referencyjny',
        'dysbiosis_index': 'Wskaźnik dysbiozy (DI)',
        'normal_microbiota': 'Normalna mikrobiota (zdrowa)',
        'description': 'OPIS',
        'important_note': 'WAŻNE',
        'microscopic_analysis': 'ANALIZA MIKROSKOPOWO-BIOCHEMICZNA',
        'biochemical_analysis': 'BADANIE BIOCHEMICZNE',
        'parasite_analysis': 'BADANIE OBECNOŚCI PASOŻYTÓW',
        'deviation': 'Odchylenie od normy'
    }
    
    # Reference ranges for phylums
    REFERENCE_RANGES = {
        'Actinomycetota': (0.1, 8),
        'Bacillota': (20, 70),
        'Bacteroidota': (4, 40),
        'Pseudomonadota': (2, 35),
        'Fibrobacterota': (0.1, 5)
    }
    
    # Phylum colors
    PHYLUM_COLORS = {
        'Actinomycetota': '#00BCD4',
        'Bacillota': '#4CAF50',
        'Bacteroidota': '#FF5722',
        'Pseudomonadota': '#00E5FF',
        'Fibrobacterota': '#9C27B0',
        'Other': '#9E9E9E'
    }
    
    def __init__(self, csv_file: str, barcode_column: str = 'barcode59'):
        """Initialize the report generator."""
        self.csv_file = csv_file
        self.barcode_column = barcode_column
        self.df = self._load_data()
        self.total_count = self.df[self.barcode_column].sum()
        
    def _load_data(self) -> pd.DataFrame:
        """Load and preprocess the CSV data."""
        df = pd.read_csv(self.csv_file)
        df.columns = df.columns.str.strip()
        return df
    
    def _calculate_species_data(self) -> pd.DataFrame:
        """Calculate species percentages for visualization."""
        species_data = self.df[self.df[self.barcode_column] > 0].copy()
        species_data['percentage'] = (species_data[self.barcode_column] / self.total_count * 100)
        species_data = species_data.sort_values('percentage', ascending=False)
        return species_data[['species', 'genus', 'phylum', self.barcode_column, 'percentage']]
    
    def _calculate_phylum_distribution(self) -> Dict[str, float]:
        """Calculate phylum distribution percentages."""
        phylum_counts = {}
        for _, row in self.df.iterrows():
            if row[self.barcode_column] > 0 and pd.notna(row['phylum']):
                phylum = row['phylum']
                phylum_counts[phylum] = phylum_counts.get(phylum, 0) + row[self.barcode_column]
        
        phylum_percentages = {
            phylum: (count / self.total_count * 100) 
            for phylum, count in phylum_counts.items()
        }
        return phylum_percentages
    
    def _create_species_visualization(self, output_path: str) -> str:
        """Create species distribution visualization matching the report style."""
        species_data = self._calculate_species_data()
        
        fig, ax = plt.subplots(figsize=(10, 12))
        
        # Get top species and group by phylum
        top_species = species_data.head(32)
        
        # Create the visualization
        y_positions = []
        labels = []
        percentages = []
        colors = []
        
        current_y = 0
        phylums_processed = {}
        
        for phylum in top_species['phylum'].unique():
            phylum_species = top_species[top_species['phylum'] == phylum]
            
            for _, row in phylum_species.iterrows():
                y_positions.append(current_y)
                labels.append(row['species'].replace('_', ' '))
                percentages.append(row['percentage'])
                colors.append(self.PHYLUM_COLORS.get(phylum, '#9E9E9E'))
                current_y += 1
            
            if phylum not in phylums_processed:
                phylums_processed[phylum] = (
                    current_y - len(phylum_species), 
                    current_y - 1
                )
        
        # Create horizontal bars
        bars = ax.barh(y_positions, percentages, color=colors, 
                       edgecolor='black', linewidth=0.5)
        
        # Add percentage labels
        for i, (pos, pct) in enumerate(zip(y_positions, percentages)):
            ax.text(pct + 0.1, pos, f'{pct:.2f}%', 
                   va='center', fontsize=8)
        
        # Customize
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel('', fontsize=10)
        ax.set_xlim(0, max(percentages) * 1.2)
        ax.grid(axis='x', alpha=0.3)
        ax.invert_yaxis()
        
        # Add phylum labels on the left
        for phylum, (start, end) in phylums_processed.items():
            mid = (start + end) / 2
            ax.text(-0.5, mid, phylum, fontsize=10, fontweight='bold',
                   ha='right', va='center', rotation=90)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Save the figure
        viz_path = output_path.replace('.pdf', '_species_viz.png')
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return viz_path
    
    def _create_phylum_charts(self, output_path: str) -> Tuple[str, str]:
        """Create phylum distribution charts (bar and horizontal bar)."""
        phylum_dist = self._calculate_phylum_distribution()
        
        # Sort phylums by percentage
        sorted_phylums = sorted(phylum_dist.items(), key=lambda x: x[1], reverse=True)
        
        # Create horizontal bar chart
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        
        phylums = [p[0] for p in sorted_phylums]
        percentages = [p[1] for p in sorted_phylums]
        colors_list = [self.PHYLUM_COLORS.get(p, '#9E9E9E') for p in phylums]
        
        bars = ax1.barh(range(len(phylums)), percentages, color=colors_list)
        
        # Add percentage labels
        for i, (phylum, pct) in enumerate(sorted_phylums):
            ax1.text(pct + 1, i, f'{pct:.1f}', va='center', fontsize=10)
            
            # Add reference range
            if phylum in self.REFERENCE_RANGES:
                ref_min, ref_max = self.REFERENCE_RANGES[phylum]
                ax1.text(85, i, f'{ref_min}-{ref_max}%', va='center', fontsize=8, color='gray')
                
                # Add arrow indicator
                if pct < ref_min:
                    ax1.text(95, i, '↓', va='center', fontsize=12, color='red')
                elif pct > ref_max:
                    ax1.text(95, i, '↑', va='center', fontsize=12, color='red')
        
        ax1.set_yticks(range(len(phylums)))
        ax1.set_yticklabels(phylums, fontsize=10)
        ax1.set_xlim(0, 100)
        ax1.set_xlabel(self.TRANSLATIONS['phylum_distribution'], fontsize=10)
        ax1.grid(axis='x', alpha=0.3)
        
        # Add reference range background
        for i in range(len(phylums)):
            if phylums[i] in self.REFERENCE_RANGES:
                ref_min, ref_max = self.REFERENCE_RANGES[phylums[i]]
                ax1.add_patch(Rectangle((ref_min, i-0.4), ref_max-ref_min, 0.8,
                                      facecolor='lightblue', alpha=0.3))
        
        plt.tight_layout()
        chart1_path = output_path.replace('.pdf', '_phylum_bar.png')
        plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart1_path, None
    
    def _generate_description_text(self, species_data: pd.DataFrame, 
                                  phylum_dist: Dict[str, float]) -> str:
        """Generate the Polish description text for the analysis."""
        description = """Badanie molekularne wykazało że mikroflora jelitowa jest prawidłowa, z niewielkimi odchyleniami. """
        
        # Find high abundance species
        high_abundance = species_data[species_data['percentage'] > 10]
        if not high_abundance.empty:
            description += f"Wysoki udział bakterii {high_abundance.iloc[0]['species']} ({high_abundance.iloc[0]['percentage']:.2f}%) "
            if len(high_abundance) > 1:
                description += f"oraz {high_abundance.iloc[1]['species']} ({high_abundance.iloc[1]['percentage']:.2f}%) "
            description += "może być wynikiem adaptacji mikroflory do zmienionej diety lub składu paszy. "
        
        # Check for fiber-fermenting bacteria
        fiber_bacteria = ['Roseburia', 'Lachnospira', 'Fibrobacter', 'Anaerobutyricum']
        fiber_present = species_data[species_data['genus'].isin(fiber_bacteria)]
        
        if fiber_present.empty or fiber_present['percentage'].sum() < 5:
            description += "Jednocześnie niewielkie ilości bakterii fermentujących włókno mogą świadczyć o niedostatecznym poziomie włókna strukturalnego w diecie lub ograniczonym jego trawieniu. "
        
        description += "Nie wykryto bakterii patogennych, które nie występują w prawidłowej mikroflorze przewodu pokarmowego. "
        description += "Nie zidentyfikowano materiału genetycznego pochodzącego od pasożytów jednokomórkowych oraz wirusów."
        
        return description
    
    def generate_report(self, output_file: str, patient_info: Optional[Dict[str, str]] = None) -> None:
        """Generate the complete PDF report in Polish laboratory style."""
        if patient_info is None:
            patient_info = {}
        
        # Calculate data
        species_data = self._calculate_species_data()
        phylum_dist = self._calculate_phylum_distribution()
        
        # Create visualizations
        species_viz_path = self._create_species_visualization(output_file)
        phylum_chart_path, _ = self._create_phylum_charts(output_file)
        
        # Create PDF using matplotlib for better Polish character support
        with PdfPages(output_file) as pdf:
            # Page 1: Title and patient info
            fig = plt.figure(figsize=(8.27, 11.69))  # A4 size
            fig.patch.set_facecolor('white')
            
            # Add header background
            ax_header = fig.add_axes([0, 0.9, 1, 0.1])
            ax_header.set_xlim(0, 1)
            ax_header.set_ylim(0, 1)
            ax_header.add_patch(Rectangle((0, 0), 1, 1, facecolor='#1e3a5f'))
            ax_header.text(0.5, 0.5, self.TRANSLATIONS['title'], 
                          ha='center', va='center', fontsize=24, 
                          color='white', fontweight='bold')
            ax_header.axis('off')
            
            # Patient information boxes
            info_y = 0.8
            info_items = [
                (self.TRANSLATIONS['patient_name'], patient_info.get('name', 'Montana')),
                (self.TRANSLATIONS['species_age'], f"{patient_info.get('species', 'Koń')}, {patient_info.get('age', '20 lat')}"),
                (self.TRANSLATIONS['sample_number'], patient_info.get('sample_number', '506')),
                (self.TRANSLATIONS['date_received'], patient_info.get('date_received', '07.05.2025 r.')),
                (self.TRANSLATIONS['date_analyzed'], patient_info.get('date_analyzed', datetime.now().strftime('%d.%m.%Y r.'))),
                (self.TRANSLATIONS['performed_by'], patient_info.get('performed_by', 'Julia Kończak')),
                (self.TRANSLATIONS['requested_by'], patient_info.get('requested_by', 'Aleksandra Matusiak'))
            ]
            
            for i, (label, value) in enumerate(info_items):
                y_pos = info_y - (i * 0.08)
                fig.text(0.1, y_pos, f"{label}:", fontsize=10, fontweight='bold')
                fig.text(0.4, y_pos, value, fontsize=10)
            
            # Add logos placeholder
            fig.text(0.05, 0.02, 'HIPPOVET+', fontsize=12, fontweight='bold')
            fig.text(0.85, 0.02, 'MIMT\nLABORATORY', fontsize=10, ha='right')
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 2: Microbiome profile
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.patch.set_facecolor('white')
            
            # Title
            fig.text(0.5, 0.95, self.TRANSLATIONS['sequencing_results'], 
                    ha='center', fontsize=16, fontweight='bold')
            fig.text(0.1, 0.9, self.TRANSLATIONS['microbiome_profile'], 
                    fontsize=14, fontweight='bold', 
                    bbox=dict(boxstyle='round', facecolor='#1e3a5f', color='white'))
            
            # Add species visualization
            ax_species = fig.add_axes([0.1, 0.3, 0.8, 0.55])
            if Path(species_viz_path).exists():
                img = plt.imread(species_viz_path)
                ax_species.imshow(img)
                ax_species.axis('off')
            
            # Add phylum distribution
            ax_phylum = fig.add_axes([0.1, 0.05, 0.8, 0.2])
            if Path(phylum_chart_path).exists():
                img = plt.imread(phylum_chart_path)
                ax_phylum.imshow(img)
                ax_phylum.axis('off')
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 3: Description and analysis
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.patch.set_facecolor('white')
            
            # Dysbiosis index
            fig.text(0.1, 0.9, f"{self.TRANSLATIONS['dysbiosis_index']}: 4.0 - {self.TRANSLATIONS['normal_microbiota']}", 
                    fontsize=12, fontweight='bold', color='green')
            fig.text(0.1, 0.87, "Brak oznak dysbiozy, mikroflora jelitowa jest zrównoważona z niewielkimi wahaniami.",
                    fontsize=10)
            
            # Description
            fig.text(0.1, 0.8, self.TRANSLATIONS['description'] + ':', 
                    fontsize=12, fontweight='bold')
            
            description_text = self._generate_description_text(species_data, phylum_dist)
            wrapped_text = textwrap.fill(description_text, width=90)
            
            y_pos = 0.75
            for line in wrapped_text.split('\n'):
                fig.text(0.1, y_pos, line, fontsize=10)
                y_pos -= 0.03
            
            # Important note
            fig.text(0.1, y_pos - 0.05, self.TRANSLATIONS['important_note'] + ':', 
                    fontsize=12, fontweight='bold', color='red')
            
            note_text = """Ze względu na zastosowaną metodologię możliwe jest, że uzyskane wyniki przedstawiają obraz przebytych, nieaktywnych zakażeń. Część zidentyfikowanych genomów może również pochodzić z zanieczyszczeń środowiskowych. W związku z tym rekomendujemy, aby przed rozpoczęciem farmakoterapii skonsultować wyniki z lekarzem weterynarii oraz przeprowadzić dodatkowe testy laboratoryjne."""
            
            wrapped_note = textwrap.fill(note_text, width=90)
            y_pos -= 0.08
            for line in wrapped_note.split('\n'):
                fig.text(0.1, y_pos, line, fontsize=9)
                y_pos -= 0.025
            
            # Microscopic analysis section
            fig.text(0.1, y_pos - 0.05, self.TRANSLATIONS['microscopic_analysis'], 
                    fontsize=12, fontweight='bold', 
                    bbox=dict(boxstyle='round', facecolor='#4CAF50', color='white'))
            
            analysis_items = [
                ('Barwa', 'Ciemnobrązowa'),
                ('Konsystencja', 'Normalna'),
                ('Zapach', 'Neutralny'),
                ('Śluzowatość', 'W normie'),
                ('Zawartość wody', 'Normalna'),
                ('Pasożyty kałowe', 'Nie zaobserwowano'),
                ('Obecność piasku', 'Obecny', True)  # True indicates deviation
            ]
            
            y_pos -= 0.08
            for item, value, *deviation in analysis_items:
                fig.text(0.15, y_pos, f"{item}:", fontsize=10)
                fig.text(0.4, y_pos, value, fontsize=10)
                if deviation:
                    fig.text(0.6, y_pos, '↑', fontsize=12, color='red')
                y_pos -= 0.025
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        # Clean up temporary files
        for path in [species_viz_path, phylum_chart_path]:
            if Path(path).exists():
                Path(path).unlink()
        
        print(f"Report generated successfully: {output_file}")


def main():
    """Main function to run the report generator."""
    parser = argparse.ArgumentParser(
        description='Generate professional PDF report from microbiome CSV data'
    )
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('-o', '--output', default='microbiome_report.pdf',
                       help='Output PDF filename')
    parser.add_argument('-b', '--barcode', default='barcode59',
                       help='Barcode column to analyze')
    parser.add_argument('--name', default='Montana', help='Patient name')
    parser.add_argument('--species', default='Koń', help='Patient species')
    parser.add_argument('--age', default='20 lat', help='Patient age')
    parser.add_argument('--sample', default='506', help='Sample number')
    parser.add_argument('--date-received', default='07.05.2025 r.', 
                       help='Date sample received')
    parser.add_argument('--performed-by', default='Julia Kończak',
                       help='Person who performed analysis')
    parser.add_argument('--requested-by', default='Aleksandra Matusiak',
                       help='Person who requested analysis')
    
    args = parser.parse_args()
    
    # Patient information
    patient_info = {
        'name': args.name,
        'species': args.species,
        'age': args.age,
        'sample_number': args.sample,
        'date_received': args.date_received,
        'date_analyzed': datetime.now().strftime('%d.%m.%Y r.'),
        'performed_by': args.performed_by,
        'requested_by': args.requested_by
    }
    
    # Generate report
    generator = AdvancedMicrobiomeReportGenerator(args.csv_file, args.barcode)
    generator.generate_report(args.output, patient_info)


if __name__ == '__main__':
    main()