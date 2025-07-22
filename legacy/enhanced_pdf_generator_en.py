#!/usr/bin/env python3
"""
Enhanced Microbiome PDF Report Generator - Week 1 MVP (English Version)
Professional laboratory reports with branding and multi-page structure
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from datetime import datetime
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Tuple, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import os
import tempfile


class EnhancedMicrobiomeReportGenerator:
    """Enhanced PDF report generator with professional formatting."""
    
    # Page dimensions
    PAGE_WIDTH = A4[0]
    PAGE_HEIGHT = A4[1]
    MARGIN = 50
    
    # Asset paths
    LOGO_PATH = 'assets/hippovet_logo.png'
    DNA_HELIX_PATH = 'assets/dna_stock_photo.jpg'
    
    # English labels
    LABELS = {
        'title': 'COMPREHENSIVE FECAL EXAMINATION',
        'patient_name': 'Patient Name',
        'species_age': 'Species & Age',
        'sample_number': 'Sample Number',
        'date_received': 'Date Received',
        'date_analyzed': 'Date Analyzed',
        'performed_by': 'Performed By',
        'requested_by': 'Requested By',
        'microbiome_profile': 'MICROBIOME PROFILE',
        'sequencing_results': 'SEQUENCING RESULTS',
        'phylum': 'PHYLUM',
        'species': 'SPECIES',
        'phylum_distribution': 'Phylum Distribution in Gut Microflora',
        'reference_range': 'Reference Range',
        'dysbiosis_index': 'Dysbiosis Index (DI)',
        'normal_microbiota': 'Normal Microbiota (Healthy)',
        'description': 'DESCRIPTION',
        'important_note': 'IMPORTANT NOTE',
        'microscopic_analysis': 'MICROSCOPIC & BIOCHEMICAL ANALYSIS',
        'biochemical_analysis': 'BIOCHEMICAL ANALYSIS',
        'parasite_analysis': 'PARASITE SCREENING',
        'deviation': 'Deviation from Normal',
        'executive_summary': 'EXECUTIVE SUMMARY',
        'clinical_interpretation': 'CLINICAL INTERPRETATION',
        'recommendations': 'RECOMMENDATIONS',
        'species_distribution': 'Bacterial Species Distribution',
        'percentage': 'Percentage (%)',
        'page': 'Page'
    }
    
    # Reference ranges for phylums
    REFERENCE_RANGES = {
        'Actinomycetota': (0.1, 8),
        'Bacillota': (20, 70),
        'Bacteroidota': (4, 40),
        'Pseudomonadota': (2, 35),
        'Fibrobacterota': (0.1, 5)
    }
    
    # Professional color scheme
    BRAND_COLORS = {
        'primary': colors.HexColor('#1E3A8A'),      # Deep blue
        'secondary': colors.HexColor('#3B82F6'),    # Bright blue
        'accent': colors.HexColor('#10B981'),       # Green
        'header_bg': colors.HexColor('#F3F4F6'),    # Light gray
        'text': colors.HexColor('#1F2937'),         # Dark gray
        'danger': colors.HexColor('#EF4444'),       # Red
        'warning': colors.HexColor('#F59E0B')       # Amber
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
        """Initialize the enhanced report generator."""
        self.csv_file = csv_file
        self.barcode_column = barcode_column
        self.df = self._load_data()
        self.total_count = self.df[self.barcode_column].sum()
        self._verify_assets()
        
    def _verify_assets(self):
        """Verify required assets exist."""
        required_assets = [self.LOGO_PATH, self.DNA_HELIX_PATH]
        missing = [asset for asset in required_assets if not Path(asset).exists()]
        if missing:
            print(f"Warning: Missing assets: {missing}")
            
    def _load_data(self) -> pd.DataFrame:
        """Load and preprocess the CSV data."""
        df = pd.read_csv(self.csv_file)
        df.columns = df.columns.str.strip()
        return df
    
    def _draw_header(self, c: canvas.Canvas, patient_info: Dict, page_num: int = 1):
        """Draw professional header with logo and patient information."""
        # Header background
        c.setFillColor(self.BRAND_COLORS['header_bg'])
        c.rect(0, self.PAGE_HEIGHT - 120, self.PAGE_WIDTH, 120, fill=1, stroke=0)
        
        # Logo
        if Path(self.LOGO_PATH).exists():
            c.drawImage(self.LOGO_PATH, 40, self.PAGE_HEIGHT - 100, 
                       width=150, height=60, preserveAspectRatio=True)
        
        # Title
        c.setFillColor(self.BRAND_COLORS['primary'])
        c.setFont("Helvetica-Bold", 16)
        c.drawString(220, self.PAGE_HEIGHT - 50, self.LABELS['title'])
        
        # Patient info box
        c.setFillColor(self.BRAND_COLORS['text'])
        c.setFont("Helvetica", 10)
        info_x = 400
        info_y = self.PAGE_HEIGHT - 40
        
        # Draw patient information
        c.drawString(info_x, info_y, f"{self.LABELS['sample_number']}: {patient_info.get('sample_number', 'N/A')}")
        c.drawString(info_x, info_y - 15, f"{self.LABELS['patient_name']}: {patient_info.get('name', 'N/A')}")
        c.drawString(info_x, info_y - 30, f"{self.LABELS['species_age']}: {patient_info.get('species', 'Horse')}, {patient_info.get('age', 'N/A')}")
        c.drawString(info_x, info_y - 45, f"{self.LABELS['date_received']}: {patient_info.get('date_received', datetime.now().strftime('%Y-%m-%d'))}")
        
        # Page number
        c.setFont("Helvetica", 9)
        c.drawRightString(self.PAGE_WIDTH - 40, 30, f"{self.LABELS['page']} {page_num}")
        
        # Horizontal line under header
        c.setStrokeColor(self.BRAND_COLORS['primary'])
        c.setLineWidth(2)
        c.line(40, self.PAGE_HEIGHT - 120, self.PAGE_WIDTH - 40, self.PAGE_HEIGHT - 120)
        
    def _draw_footer(self, c: canvas.Canvas, patient_info: Dict):
        """Draw professional footer."""
        c.setStrokeColor(self.BRAND_COLORS['primary'])
        c.setLineWidth(1)
        c.line(40, 60, self.PAGE_WIDTH - 40, 60)
        
        c.setFillColor(self.BRAND_COLORS['text'])
        c.setFont("Helvetica", 8)
        c.drawString(40, 45, f"{self.LABELS['performed_by']}: {patient_info.get('performed_by', 'HippoVet+ Laboratory')}")
        c.drawRightString(self.PAGE_WIDTH - 40, 45, f"{self.LABELS['date_analyzed']}: {datetime.now().strftime('%Y-%m-%d')}")
        
    def _calculate_species_data(self) -> pd.DataFrame:
        """Calculate species percentages for visualization."""
        species_data = self.df[self.df[self.barcode_column] > 0].copy()
        species_data['percentage'] = (species_data[self.barcode_column] / self.total_count * 100)
        species_data = species_data.sort_values('percentage', ascending=False)
        return species_data[['species', 'genus', 'phylum', self.barcode_column, 'percentage']]
    
    def _calculate_phylum_distribution(self) -> Dict[str, float]:
        """Calculate phylum distribution percentages."""
        phylum_data = self.df[self.df[self.barcode_column] > 0].copy()
        phylum_sums = phylum_data.groupby('phylum')[self.barcode_column].sum()
        phylum_percentages = (phylum_sums / self.total_count * 100).to_dict()
        return phylum_percentages
    
    def _create_species_chart(self, species_data: pd.DataFrame, output_path: str):
        """Create horizontal bar chart for species distribution."""
        top_species = species_data.head(15)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create horizontal bars
        y_positions = np.arange(len(top_species))
        bars = ax.barh(y_positions, top_species['percentage'], color=self.BRAND_COLORS['secondary'].rgb())
        
        # Customize appearance
        ax.set_yticks(y_positions)
        ax.set_yticklabels([self._truncate_species_name(name) for name in top_species['species']])
        ax.set_xlabel(self.LABELS['percentage'], fontsize=12)
        ax.set_title(self.LABELS['species_distribution'], fontsize=14, weight='bold', color='#1E3A8A')
        
        # Add percentage labels
        for i, (idx, row) in enumerate(top_species.iterrows()):
            ax.text(row['percentage'] + 0.1, i, f"{row['percentage']:.1f}%", 
                   va='center', fontsize=9)
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_phylum_chart(self, phylum_dist: Dict[str, float], output_path: str):
        """Create phylum distribution chart with reference ranges."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        phylums = list(phylum_dist.keys())
        percentages = list(phylum_dist.values())
        
        # Create bars
        bars = ax.bar(phylums, percentages, color=[self.PHYLUM_COLORS.get(p, '#9E9E9E') for p in phylums])
        
        # Add reference ranges
        for i, phylum in enumerate(phylums):
            if phylum in self.REFERENCE_RANGES:
                min_ref, max_ref = self.REFERENCE_RANGES[phylum]
                ax.plot([i-0.4, i+0.4], [min_ref, min_ref], 'k--', alpha=0.5, linewidth=2)
                ax.plot([i-0.4, i+0.4], [max_ref, max_ref], 'k--', alpha=0.5, linewidth=2)
                ax.fill_between([i-0.4, i+0.4], min_ref, max_ref, alpha=0.2, color='gray')
        
        # Customize
        ax.set_ylabel(self.LABELS['percentage'], fontsize=12)
        ax.set_title(self.LABELS['phylum_distribution'], fontsize=14, weight='bold', color='#1E3A8A')
        ax.set_ylim(0, max(percentages) * 1.2)
        
        # Add value labels
        for bar, pct in zip(bars, percentages):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{pct:.1f}%', ha='center', va='bottom')
        
        # Legend
        ax.text(0.02, 0.98, self.LABELS['reference_range'] + ' (---)', 
               transform=ax.transAxes, va='top', fontsize=10)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    def _truncate_species_name(self, name: str, max_length: int = 40) -> str:
        """Truncate long species names."""
        return name if len(name) <= max_length else name[:max_length-3] + '...'
    
    def _calculate_dysbiosis_index(self, phylum_dist: Dict[str, float]) -> float:
        """Calculate dysbiosis index based on phylum distribution."""
        di_score = 0
        deviations = []
        
        for phylum, percentage in phylum_dist.items():
            if phylum in self.REFERENCE_RANGES:
                min_ref, max_ref = self.REFERENCE_RANGES[phylum]
                if percentage < min_ref:
                    deviation = (min_ref - percentage) / min_ref
                    deviations.append(deviation)
                elif percentage > max_ref:
                    deviation = (percentage - max_ref) / max_ref
                    deviations.append(deviation)
        
        if deviations:
            di_score = sum(deviations) / len(deviations) * 100
            
        return min(di_score, 100)
    
    def _get_clinical_interpretation(self, di_score: float) -> str:
        """Get clinical interpretation based on dysbiosis index."""
        if di_score < 20:
            return "The gut microbiota is well-balanced. Bacterial composition falls within reference ranges."
        elif di_score < 50:
            return "Moderate microbiota imbalance observed. Monitoring recommended with potential dietary modifications."
        else:
            return "Significant gut microbiota dysbiosis detected. Veterinary consultation and therapeutic intervention recommended."
    
    def generate_report(self, output_file: str, patient_info: Dict):
        """Generate the complete enhanced PDF report."""
        c = canvas.Canvas(output_file, pagesize=A4)
        
        # Store temp files for charts
        temp_files = []
        
        try:
            # Page 1: Title page with executive summary
            self._draw_header(c, patient_info, 1)
            self._draw_footer(c, patient_info)
            
            # DNA Helix image
            if Path(self.DNA_HELIX_PATH).exists():
                c.drawImage(self.DNA_HELIX_PATH, 200, 400, width=200, height=200, preserveAspectRatio=True)
            
            # Executive Summary
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(self.BRAND_COLORS['primary'])
            c.drawString(60, 350, self.LABELS['executive_summary'])
            
            # Calculate key metrics
            species_data = self._calculate_species_data()
            phylum_dist = self._calculate_phylum_distribution()
            di_score = self._calculate_dysbiosis_index(phylum_dist)
            
            c.setFont("Helvetica", 11)
            c.setFillColor(self.BRAND_COLORS['text'])
            summary_text = [
                f"Gut microbiome sample analyzed for patient {patient_info.get('name', 'N/A')}.",
                f"Total bacterial species identified: {len(species_data)}",
                f"Dysbiosis Index (DI): {di_score:.1f}/100",
                f"Dominant phylum: {max(phylum_dist, key=phylum_dist.get)} ({phylum_dist[max(phylum_dist, key=phylum_dist.get)]:.1f}%)"
            ]
            
            y_pos = 300
            for line in summary_text:
                c.drawString(60, y_pos, line)
                y_pos -= 20
            
            c.showPage()
            
            # Page 2: Species distribution
            self._draw_header(c, patient_info, 2)
            self._draw_footer(c, patient_info)
            
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(self.BRAND_COLORS['primary'])
            c.drawString(60, self.PAGE_HEIGHT - 160, self.LABELS['microbiome_profile'])
            
            # Create and embed species chart
            species_chart_path = tempfile.mktemp(suffix='.png')
            temp_files.append(species_chart_path)
            self._create_species_chart(species_data, species_chart_path)
            c.drawImage(species_chart_path, 60, 200, width=480, height=400)
            
            c.showPage()
            
            # Page 3: Phylum distribution and clinical interpretation
            self._draw_header(c, patient_info, 3)
            self._draw_footer(c, patient_info)
            
            # Create and embed phylum chart
            phylum_chart_path = tempfile.mktemp(suffix='.png')
            temp_files.append(phylum_chart_path)
            self._create_phylum_chart(phylum_dist, phylum_chart_path)
            c.drawImage(phylum_chart_path, 60, 400, width=480, height=300)
            
            # Clinical interpretation
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(self.BRAND_COLORS['primary'])
            c.drawString(60, 350, self.LABELS['clinical_interpretation'])
            
            c.setFont("Helvetica", 10)
            c.setFillColor(self.BRAND_COLORS['text'])
            interpretation = self._get_clinical_interpretation(di_score)
            lines = self._wrap_text(interpretation, 80)
            y_pos = 320
            for line in lines:
                c.drawString(60, y_pos, line)
                y_pos -= 15
            
            c.showPage()
            
            # Page 4: Biochemical analysis tables
            self._draw_header(c, patient_info, 4)
            self._draw_footer(c, patient_info)
            
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(self.BRAND_COLORS['primary'])
            c.drawString(60, self.PAGE_HEIGHT - 160, self.LABELS['biochemical_analysis'])
            
            # Create analysis table
            self._draw_analysis_table(c, 60, self.PAGE_HEIGHT - 200)
            
            c.showPage()
            
            # Page 5: Recommendations
            self._draw_header(c, patient_info, 5)
            self._draw_footer(c, patient_info)
            
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(self.BRAND_COLORS['primary'])
            c.drawString(60, self.PAGE_HEIGHT - 160, self.LABELS['recommendations'])
            
            # Add recommendations based on DI score
            recommendations = self._get_recommendations(di_score)
            c.setFont("Helvetica", 11)
            c.setFillColor(self.BRAND_COLORS['text'])
            y_pos = self.PAGE_HEIGHT - 200
            for rec in recommendations:
                lines = self._wrap_text(f"• {rec}", 80)
                for line in lines:
                    c.drawString(60, y_pos, line)
                    y_pos -= 20
                y_pos -= 10
            
            # Save the PDF
            c.save()
            
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """Wrap text to specified character limit."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_chars:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _draw_analysis_table(self, c: canvas.Canvas, x: float, y: float):
        """Draw biochemical analysis table."""
        # Table data
        data = [
            ['Parameter', 'Result', 'Reference Range', 'Status'],
            ['pH', '7.2', '6.8 - 7.4', 'Normal'],
            ['Consistency', 'Formed', 'Formed', 'Normal'],
            ['Occult Blood', 'Negative', 'Negative', 'Normal'],
            ['Fat Content', 'Trace', 'None/Trace', 'Normal'],
            ['Protein', 'Negative', 'Negative', 'Normal']
        ]
        
        # Create table
        col_widths = [150, 100, 150, 80]
        row_height = 25
        
        # Draw table headers
        c.setFillColor(self.BRAND_COLORS['primary'])
        c.rect(x, y - row_height, sum(col_widths), row_height, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        
        current_x = x
        for i, header in enumerate(data[0]):
            c.drawString(current_x + 5, y - row_height + 7, header)
            current_x += col_widths[i]
        
        # Draw table rows
        c.setFillColor(self.BRAND_COLORS['text'])
        c.setFont("Helvetica", 10)
        
        for i, row in enumerate(data[1:], 1):
            row_y = y - (i + 1) * row_height
            
            # Alternate row colors
            if i % 2 == 0:
                c.setFillColor(colors.HexColor('#F9FAFB'))
                c.rect(x, row_y, sum(col_widths), row_height, fill=1, stroke=0)
            
            # Draw cell content
            c.setFillColor(self.BRAND_COLORS['text'])
            current_x = x
            for j, cell in enumerate(row):
                c.drawString(current_x + 5, row_y + 7, cell)
                current_x += col_widths[j]
            
            # Draw borders
            c.setStrokeColor(colors.HexColor('#E5E7EB'))
            c.setLineWidth(0.5)
            c.line(x, row_y, x + sum(col_widths), row_y)
        
        # Draw outer border
        c.setStrokeColor(self.BRAND_COLORS['primary'])
        c.setLineWidth(1)
        c.rect(x, y - (len(data) * row_height), sum(col_widths), len(data) * row_height, fill=0, stroke=1)
    
    def _get_recommendations(self, di_score: float) -> List[str]:
        """Get recommendations based on dysbiosis index."""
        if di_score < 20:
            return [
                "Maintain current diet and feeding schedule",
                "Continue regular monitoring with annual check-ups",
                "Ensure access to fresh water and high-quality forage"
            ]
        elif di_score < 50:
            return [
                "Consider probiotic supplementation for 4-6 weeks",
                "Increase dietary fiber content",
                "Reduce concentrated feed portions",
                "Schedule follow-up analysis in 3 months",
                "Monitor stool consistency and appetite"
            ]
        else:
            return [
                "Urgent veterinary consultation recommended",
                "Implement probiotic supplementation protocol",
                "Complete gastroenterological examination advised",
                "Consider comprehensive dietary modification",
                "Rule out intestinal parasites",
                "Follow-up microbiological analysis in 4-6 weeks"
            ]


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(description='Generate enhanced microbiome PDF report')
    parser.add_argument('csv_file', help='Path to the CSV file with microbiome data')
    parser.add_argument('-o', '--output', default='enhanced_microbiome_report.pdf',
                        help='Output PDF file path')
    parser.add_argument('-b', '--barcode', default='barcode59',
                        help='Barcode column to analyze')
    parser.add_argument('--name', default='Patient',
                        help='Patient name')
    parser.add_argument('--species', default='Horse',
                        help='Species')
    parser.add_argument('--age', default='Unknown',
                        help='Patient age')
    parser.add_argument('--sample', default='001',
                        help='Sample number')
    parser.add_argument('--performed-by', default='HippoVet+ Laboratory',
                        help='Who performed the analysis')
    parser.add_argument('--requested-by', default='Attending Veterinarian',
                        help='Who requested the analysis')
    
    args = parser.parse_args()
    
    # Create patient info dictionary
    patient_info = {
        'name': args.name,
        'species': args.species,
        'age': args.age,
        'sample_number': args.sample,
        'date_received': datetime.now().strftime('%Y-%m-%d'),
        'performed_by': args.performed_by,
        'requested_by': args.requested_by
    }
    
    # Generate report
    print(f"Generating enhanced report for {args.csv_file}...")
    generator = EnhancedMicrobiomeReportGenerator(args.csv_file, args.barcode)
    generator.generate_report(args.output, patient_info)
    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()