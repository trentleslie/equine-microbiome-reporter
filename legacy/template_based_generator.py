#!/usr/bin/env python3
"""
Template-Based Microbiome PDF Report Generator
Uses a template structure with dynamic data injection
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from datetime import datetime
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
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
matplotlib.use('Agg')
import os
import tempfile
from enum import Enum


# Data Models for Report Content
@dataclass
class PatientInfo:
    """Patient information data model"""
    name: str = "Unknown"
    species: str = "Horse"
    age: str = "Unknown"
    sample_number: str = "001"
    date_received: str = ""
    date_analyzed: str = ""
    performed_by: str = "Laboratory Staff"
    requested_by: str = "Veterinarian"


@dataclass
class SpeciesData:
    """Bacterial species data"""
    species: str
    genus: str
    phylum: str
    count: int
    percentage: float


@dataclass
class PhylumData:
    """Phylum distribution data"""
    name: str
    percentage: float
    reference_min: float
    reference_max: float


@dataclass
class ParasiteResult:
    """Parasite screening result"""
    name: str
    result: str
    abnormal: bool = False


@dataclass
class MicroscopicResult:
    """Microscopic examination result"""
    parameter: str
    result: str
    abnormal: bool = False


@dataclass
class BiochemicalResult:
    """Biochemical test result"""
    parameter: str
    result: str
    reference: str
    status: str
    abnormal: bool = False


@dataclass
class ClinicalInterpretation:
    """Clinical interpretation sections"""
    dysbiosis_index: float
    dysbiosis_description: str
    parasite_profile: str
    viral_profile: str
    main_description: str
    important_note: str
    microscopic_description: str
    parasite_description: str
    biochemical_description: str


# Template Text Constants
class ReportTemplates:
    """All template text for the report"""
    
    # Page 1 - Title Page
    MAIN_TITLE = "COMPREHENSIVE FECAL EXAMINATION"
    
    # Field Labels
    LABELS = {
        'patient_name': 'Patient Name:',
        'species_age': 'Species and Age:',
        'sample_number': 'Examination Number:',
        'date_received': 'Date Material Received:',
        'date_analyzed': 'Date of Analysis:',
        'performed_by': 'Performed by:',
        'requested_by': 'Requested by:',
    }
    
    # Page 2 - Headers
    SEQUENCING_RESULTS = "SEQUENCING RESULTS"
    MICROBIOTIC_PROFILE = "MICROBIOTIC PROFILE"
    PHYLUM_DISTRIBUTION = "Phylum Distribution in Gut Microflora"
    
    # Page 3 - Section Headers
    DYSBIOSIS_INDEX = "Dysbiosis Index (DI)"
    PARASITE_PROFILE = "UNICELLULAR PARASITE PROFILE"
    VIRAL_PROFILE = "VIRAL PROFILE"
    DESCRIPTION = "DESCRIPTION"
    IMPORTANT = "IMPORTANT"
    MICROSCOPIC_ANALYSIS = "MICROSCOPIC-BIOCHEMICAL ANALYSIS"
    
    # Page 4 - Section Headers
    PARASITE_SCREENING = "PARASITE SCREENING"
    MICROSCOPIC_EXAM = "MICROSCOPIC EXAMINATION"
    BIOCHEMICAL_EXAM = "BIOCHEMICAL EXAMINATION"
    DEVIATION_FROM_NORMAL = "Deviation from normal"
    
    # Page 5 - Educational Content
    EDUCATIONAL_HEADER = "What is the purpose of genetic examination of gut microflora?"
    POSITIVE_MICROBIOME = "Positive Gut Microbiome"
    PATHOGENIC_MICROBIOME = "Pathogenic Gut Microbiome"
    DYSBIOSIS_QUESTION = "What is Gut Dysbiosis?"
    
    # Clinical Interpretations (templates with placeholders)
    DYSBIOSIS_INTERPRETATIONS = {
        'normal': "Normal microbiota (healthy). Lack of dysbiosis signs; gut microflora is balanced with minor deviations.",
        'mild': "Mild dysbiosis detected. Moderate imbalance in gut microflora composition requiring monitoring.",
        'severe': "Severe dysbiosis detected. Significant imbalance in gut microflora requiring intervention."
    }
    
    # Default clinical descriptions
    DEFAULT_PARASITE_NEGATIVE = "No unicellular parasite genome identified in the sample"
    DEFAULT_VIRAL_NEGATIVE = "No viral genome identified in the sample"
    
    # Educational content
    EDUCATIONAL_INTRO = """Genetic examination of gut microflora is performed for comprehensive analysis of bacterial flora of 
the digestive tract, identification of dysbiosis disorders, and assessment of their impact on the 
animal's health. It allows for precise determination of system dysfunction, which may lead to 
problems with digestion, metabolism, and even behavioral problems."""
    
    POSITIVE_MICROBIOME_DESC = """Positive bacteria supporting digestion, producing substances nourishing intestinal epithelium and 
supporting proper metabolism growth and animal's overall condition between positive and pathogenic 
flora is maintained."""
    
    PATHOGENIC_MICROBIOME_DESC = """Excess of pathogenic microorganisms causes disorders of normal intestinal function in the body, 
inflammatory conditions and disrupts nutrient absorption, leading to worsening of the animal's 
condition."""
    
    DYSBIOSIS_EXPLANATION = """Gut microbiome imbalance among positive and pathogenic microorganisms. It is a condition where 
pathogenic bacteria multiply excessively, and their pathogenic products change microbiome 
composition, gut microbiome condition is disturbed. Gut microbiome imbalance is a basic cause 
of many inflammatory conditions - including inflammatory bowel diseases, diarrhea, and colic."""


class TemplateBasedReportGenerator:
    """Template-based PDF report generator"""
    
    # Page dimensions
    PAGE_WIDTH = A4[0]
    PAGE_HEIGHT = A4[1]
    MARGIN = 50
    
    # Asset paths
    LOGO_PATH = 'assets/hippovet_logo.png'
    DNA_HELIX_PATH = 'assets/dna_stock_photo.jpg'
    
    # Professional color scheme (from reference)
    COLORS = {
        'primary_blue': colors.HexColor('#1E3A8A'),
        'teal': colors.HexColor('#14B8A6'),
        'green': colors.HexColor('#10B981'),
        'light_gray': colors.HexColor('#F3F4F6'),
        'text': colors.HexColor('#1F2937'),
        'white': colors.white,
        'danger': colors.HexColor('#EF4444'),
        'chart_blue': colors.HexColor('#3B82F6'),
    }
    
    # Reference ranges for phylums
    REFERENCE_RANGES = {
        'Actinomycetota': (0.1, 8),
        'Bacillota': (20, 70),
        'Bacteroidota': (4, 40),
        'Pseudomonadota': (2, 35),
        'Fibrobacterota': (0.1, 5)
    }
    
    def __init__(self, csv_file: str, barcode_column: str = 'barcode59'):
        """Initialize the generator with data source"""
        self.csv_file = csv_file
        self.barcode_column = barcode_column
        self.df = self._load_data()
        self.total_count = self.df[self.barcode_column].sum()
        self._verify_assets()
        
    def _verify_assets(self):
        """Verify required assets exist"""
        required_assets = [self.LOGO_PATH, self.DNA_HELIX_PATH]
        missing = [asset for asset in required_assets if not Path(asset).exists()]
        if missing:
            print(f"Warning: Missing assets: {missing}")
            
    def _load_data(self) -> pd.DataFrame:
        """Load and preprocess the CSV data"""
        df = pd.read_csv(self.csv_file)
        df.columns = df.columns.str.strip()
        return df
    
    def _process_microbiome_data(self) -> Tuple[List[SpeciesData], List[PhylumData]]:
        """Process CSV data into structured format"""
        # Calculate species data
        species_list = []
        species_data = self.df[self.df[self.barcode_column] > 0].copy()
        species_data['percentage'] = (species_data[self.barcode_column] / self.total_count * 100)
        species_data = species_data.sort_values('percentage', ascending=False)
        
        for _, row in species_data.iterrows():
            species_list.append(SpeciesData(
                species=row['species'],
                genus=row.get('genus', ''),
                phylum=row.get('phylum', ''),
                count=row[self.barcode_column],
                percentage=row['percentage']
            ))
        
        # Calculate phylum distribution
        phylum_dict = {}
        for species in species_list:
            if species.phylum not in phylum_dict:
                phylum_dict[species.phylum] = 0
            phylum_dict[species.phylum] += species.percentage
        
        phylum_list = []
        for phylum, percentage in phylum_dict.items():
            ref_range = self.REFERENCE_RANGES.get(phylum, (0, 100))
            phylum_list.append(PhylumData(
                name=phylum,
                percentage=percentage,
                reference_min=ref_range[0],
                reference_max=ref_range[1]
            ))
        
        return species_list, phylum_list
    
    def _calculate_dysbiosis_index(self, phylum_data: List[PhylumData]) -> float:
        """Calculate dysbiosis index based on phylum distribution"""
        di_score = 0
        deviations = []
        
        for phylum in phylum_data:
            if phylum.percentage < phylum.reference_min:
                deviation = (phylum.reference_min - phylum.percentage) / phylum.reference_min
                deviations.append(deviation)
            elif phylum.percentage > phylum.reference_max:
                deviation = (phylum.percentage - phylum.reference_max) / phylum.reference_max
                deviations.append(deviation)
        
        if deviations:
            di_score = sum(deviations) / len(deviations) * 100
            
        return min(di_score, 100)
    
    def _generate_clinical_interpretation(self, species_data: List[SpeciesData], 
                                        phylum_data: List[PhylumData], 
                                        di_score: float) -> ClinicalInterpretation:
        """Generate clinical interpretation based on data"""
        # Determine dysbiosis level
        if di_score < 20:
            dysbiosis_desc = ReportTemplates.DYSBIOSIS_INTERPRETATIONS['normal']
        elif di_score < 50:
            dysbiosis_desc = ReportTemplates.DYSBIOSIS_INTERPRETATIONS['mild']
        else:
            dysbiosis_desc = ReportTemplates.DYSBIOSIS_INTERPRETATIONS['severe']
        
        # Generate main description based on findings
        dominant_species = species_data[0] if species_data else None
        main_desc = f"Molecular examination revealed gut microflora properly balanced with minor deviations. "
        
        if dominant_species and dominant_species.percentage > 20:
            main_desc += f"High percentage of {dominant_species.species} ({dominant_species.percentage:.1f}%) "
            main_desc += "may indicate adaptations of microflora to environmental changes or to animal's current diet. "
        
        main_desc += "No genetic material from unicellular parasites or viruses was identified."
        
        # Create interpretation object
        return ClinicalInterpretation(
            dysbiosis_index=di_score,
            dysbiosis_description=dysbiosis_desc,
            parasite_profile=ReportTemplates.DEFAULT_PARASITE_NEGATIVE,
            viral_profile=ReportTemplates.DEFAULT_VIRAL_NEGATIVE,
            main_description=main_desc,
            important_note="According to applied methodology, it is possible that negative results were obtained despite presence of some genomes.",
            microscopic_description="In the macroscopic examination, dark brown color, normal consistency, and neutral odor of fecal material were observed.",
            parasite_description="In the microscopic examination of fecal material, no parasite eggs or larvae were observed.",
            biochemical_description="Biochemical parameters within normal limits."
        )
    
    def _generate_lab_results(self) -> Tuple[List[ParasiteResult], List[MicroscopicResult], List[BiochemicalResult]]:
        """Generate laboratory test results (can be customized based on actual tests)"""
        # Default parasite screening results
        parasites = [
            ParasiteResult("Anoplocephala perfoliata", "Not observed"),
            ParasiteResult("Oxyuris equi", "Not observed"),
            ParasiteResult("Parascaris equorum", "Not observed"),
            ParasiteResult("Strongylidae", "Not observed"),
        ]
        
        # Default microscopic results
        microscopic = [
            MicroscopicResult("Leukocytes", "Not observed"),
            MicroscopicResult("Erythrocytes", "Not observed"),
            MicroscopicResult("Yeast cells", "Not observed"),
            MicroscopicResult("Rhabditiform nematodes", "Not observed"),
            MicroscopicResult("Plant fibers", "Present"),
            MicroscopicResult("Cereal grains", "Not observed"),
        ]
        
        # Default biochemical results
        biochemical = [
            BiochemicalResult("pH", "7.2", "6.8 - 7.4", "Normal"),
            BiochemicalResult("Consistency", "Formed", "Formed", "Normal"),
            BiochemicalResult("Occult Blood", "Negative", "Negative", "Normal"),
            BiochemicalResult("Fat Content", "Trace", "None/Trace", "Normal"),
            BiochemicalResult("Protein", "Negative", "Negative", "Normal"),
        ]
        
        return parasites, microscopic, biochemical
    
    def _draw_rounded_rect(self, c: canvas.Canvas, x: float, y: float, width: float, height: float, radius: float):
        """Draw a rounded rectangle (pill shape)"""
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor('#E5E7EB'))
        c.roundRect(x, y, width, height, radius, stroke=1, fill=1)
        c.restoreState()
    
    def _draw_section_header(self, c: canvas.Canvas, x: float, y: float, width: float, text: str):
        """Draw green section header with white text"""
        c.saveState()
        c.setFillColor(self.COLORS['green'])
        c.rect(x, y, width, 25, fill=1, stroke=0)
        c.setFillColor(self.COLORS['white'])
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x + 10, y + 7, text)
        c.restoreState()
    
    def _draw_page_1(self, c: canvas.Canvas, patient_info: PatientInfo):
        """Draw title page with patient information"""
        # Background DNA helix
        if Path(self.DNA_HELIX_PATH).exists():
            c.drawImage(self.DNA_HELIX_PATH, 0, 0, width=self.PAGE_WIDTH, height=self.PAGE_HEIGHT, 
                       preserveAspectRatio=False, mask='auto')
        
        # Add teal decoration in top right
        c.saveState()
        c.setFillColor(self.COLORS['teal'])
        c.setStrokeColor(self.COLORS['teal'])
        # Draw diagonal stripes
        for i in range(5):
            x_start = self.PAGE_WIDTH - 100 + (i * 20)
            c.line(x_start, self.PAGE_HEIGHT, self.PAGE_WIDTH, self.PAGE_HEIGHT - 100 + (i * 20))
        c.restoreState()
        
        # Main title
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(self.COLORS['primary_blue'])
        c.drawString(60, self.PAGE_HEIGHT - 100, ReportTemplates.MAIN_TITLE)
        
        # Patient info pills
        pill_y = self.PAGE_HEIGHT - 200
        pill_spacing = 15
        pill_height = 35
        
        # Row 1: Name, Species/Age, Sample Number
        self._draw_rounded_rect(c, 60, pill_y, 120, pill_height, 17)
        c.setFillColor(self.COLORS['text'])
        c.setFont("Helvetica", 10)
        c.drawCentredString(120, pill_y + 12, patient_info.name)
        
        self._draw_rounded_rect(c, 200, pill_y, 120, pill_height, 17)
        c.drawCentredString(260, pill_y + 12, f"{patient_info.species}, {patient_info.age}")
        
        self._draw_rounded_rect(c, 340, pill_y, 120, pill_height, 17)
        c.drawCentredString(400, pill_y + 12, patient_info.sample_number)
        
        # Row 2: Dates
        pill_y -= (pill_height + pill_spacing)
        self._draw_rounded_rect(c, 60, pill_y, 140, pill_height, 17)
        c.drawCentredString(130, pill_y + 12, patient_info.date_received)
        
        self._draw_rounded_rect(c, 220, pill_y, 140, pill_height, 17)
        c.drawCentredString(290, pill_y + 12, patient_info.date_analyzed)
        
        # Row 3: Personnel
        pill_y -= (pill_height + pill_spacing)
        self._draw_rounded_rect(c, 60, pill_y, 140, pill_height, 17)
        c.drawCentredString(130, pill_y + 12, patient_info.performed_by)
        
        self._draw_rounded_rect(c, 220, pill_y, 140, pill_height, 17)
        c.drawCentredString(290, pill_y + 12, patient_info.requested_by)
        
        # Logos at bottom
        if Path(self.LOGO_PATH).exists():
            c.drawImage(self.LOGO_PATH, 40, 40, width=120, height=50, preserveAspectRatio=True)
        
        # MEMT Laboratory text (as we don't have the logo)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(self.COLORS['primary_blue'])
        c.drawRightString(self.PAGE_WIDTH - 40, 50, "MEMT")
        c.setFont("Helvetica", 10)
        c.drawRightString(self.PAGE_WIDTH - 40, 35, "LABORATORY")
    
    def generate_report(self, output_file: str, patient_info: PatientInfo):
        """Generate the complete PDF report"""
        # Process data
        species_data, phylum_data = self._process_microbiome_data()
        di_score = self._calculate_dysbiosis_index(phylum_data)
        clinical_interp = self._generate_clinical_interpretation(species_data, phylum_data, di_score)
        parasites, microscopic, biochemical = self._generate_lab_results()
        
        # Create PDF
        c = canvas.Canvas(output_file, pagesize=A4)
        
        # Page 1: Title page
        self._draw_page_1(c, patient_info)
        c.showPage()
        
        # Additional pages would follow the same pattern...
        # For now, let's save what we have
        c.save()
        
        print(f"Template-based report saved to {output_file}")


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='Generate template-based microbiome PDF report')
    parser.add_argument('csv_file', help='Path to the CSV file with microbiome data')
    parser.add_argument('-o', '--output', default='template_report.pdf',
                        help='Output PDF file path')
    parser.add_argument('-b', '--barcode', default='barcode59',
                        help='Barcode column to analyze')
    
    # Patient info arguments
    parser.add_argument('--name', default='Patient', help='Patient name')
    parser.add_argument('--species', default='Horse', help='Species')
    parser.add_argument('--age', default='Unknown', help='Patient age')
    parser.add_argument('--sample', default='001', help='Sample number')
    parser.add_argument('--date-received', help='Date received (YYYY-MM-DD)')
    parser.add_argument('--date-analyzed', help='Date analyzed (YYYY-MM-DD)')
    parser.add_argument('--performed-by', default='Laboratory Staff', help='Who performed the analysis')
    parser.add_argument('--requested-by', default='Veterinarian', help='Who requested the analysis')
    
    args = parser.parse_args()
    
    # Create patient info
    patient_info = PatientInfo(
        name=args.name,
        species=args.species,
        age=args.age,
        sample_number=args.sample,
        date_received=args.date_received or datetime.now().strftime('%Y-%m-%d'),
        date_analyzed=args.date_analyzed or datetime.now().strftime('%Y-%m-%d'),
        performed_by=args.performed_by,
        requested_by=args.requested_by
    )
    
    # Generate report
    generator = TemplateBasedReportGenerator(args.csv_file, args.barcode)
    generator.generate_report(args.output, patient_info)


if __name__ == "__main__":
    main()