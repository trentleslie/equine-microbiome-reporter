"""
PDF Builder - Converts template output to professional PDF using ReportLab
Handles the conversion from Jinja2 template output to styled PDF documents
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import xml.etree.ElementTree as ET
from html import unescape

from .data_models import PatientInfo, MicrobiomeData

logger = logging.getLogger(__name__)


class PDFBuilder:
    """Build PDF from template-generated content"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.width, self.height = A4
        self.config = config or {}
        
        # Color scheme
        self.colors = {
            'primary_blue': colors.HexColor('#1E3A8A'),
            'green': colors.HexColor('#10B981'),
            'teal': colors.HexColor('#14B8A6'),
            'header_bg': colors.HexColor('#F8FAFC'),
            'text_dark': colors.HexColor('#1F2937'),
            'text_light': colors.HexColor('#6B7280'),
            'white': colors.white,
            'border_gray': colors.HexColor('#E5E7EB')
        }
        
        # Layout constants
        self.margin = 25 * mm
        self.header_height = 120
        self.footer_height = 50
        
        logger.info("PDFBuilder initialized")
    
    def build_from_content(self, content: str, output_path: str, 
                          patient_info: PatientInfo, data: MicrobiomeData) -> bool:
        """
        Parse template output and create PDF
        
        Args:
            content: Rendered template content (HTML)
            output_path: Where to save the PDF
            patient_info: Patient information for headers
            data: Microbiome data for charts and content
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Building PDF: {output_path}")
            
            # For MVP, create a basic PDF with ReportLab directly
            # TODO: Implement full HTML parsing in future iterations
            c = canvas.Canvas(output_path, pagesize=A4)
            
            # Generate 5 pages as per reference design
            self._draw_page_1(c, patient_info, data)
            c.showPage()
            
            self._draw_page_2(c, patient_info, data)
            c.showPage()
            
            self._draw_page_3(c, patient_info, data)
            c.showPage()
            
            self._draw_page_4(c, patient_info, data)
            c.showPage()
            
            self._draw_page_5(c, patient_info, data)
            
            c.save()
            logger.info(f"PDF successfully created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF building failed: {e}", exc_info=True)
            return False
    
    def _draw_page_1(self, c: canvas.Canvas, patient: PatientInfo, data: MicrobiomeData):
        """Draw Page 1: Title Page"""
        self._draw_header(c, patient, 1)
        
        # Main title
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(self.colors['text_dark'])
        c.drawCentredString(self.width/2, self.height - 200, "COMPREHENSIVE FECAL EXAMINATION")
        
        c.setFont("Helvetica", 18)
        c.drawCentredString(self.width/2, self.height - 230, "DNA sequencing")
        
        # DNA imagery placeholder
        c.setFillColor(self.colors['teal'])
        c.rect(self.width/2 - 100, self.height - 350, 200, 80, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 12)
        c.drawCentredString(self.width/2, self.height - 315, "DNA Helix Image")
        
        # Sample information
        y_pos = self.height - 450
        c.setFillColor(self.colors['text_dark'])
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.margin, y_pos, "Sample Information:")
        
        info_items = [
            f"Patient Name: {patient.name}",
            f"Species: {patient.species}",
            f"Age: {patient.age}",
            f"Sample Number: {patient.sample_number}"
        ]
        
        c.setFont("Helvetica", 12)
        for i, item in enumerate(info_items):
            c.drawString(self.margin + 20, y_pos - 30 - (i * 25), item)
        
        self._draw_footer(c, 1)
    
    def _draw_page_2(self, c: canvas.Canvas, patient: PatientInfo, data: MicrobiomeData):
        """Draw Page 2: Sequencing Results"""
        self._draw_header(c, patient, 2)
        
        # Green header
        self._draw_section_header(c, "DNA SEQUENCING RESULTS", self.height - 200)
        
        # Top species distribution (simplified)
        y_pos = self.height - 250
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin, y_pos, "Top Species Distribution:")
        
        c.setFont("Helvetica", 10)
        for i, species in enumerate(data.species_list[:10]):
            y = y_pos - 30 - (i * 20)
            species_name = species.get('species', 'Unknown')[:40]  # Truncate long names
            percentage = species.get('percentage', 0)
            
            # Species name
            c.drawString(self.margin, y, f"{i+1}. {species_name}")
            
            # Percentage bar (simple rectangle)
            bar_width = min(200, percentage * 4)  # Scale for visibility
            c.setFillColor(self.colors['green'])
            c.rect(self.margin + 300, y - 5, bar_width, 15, fill=1, stroke=0)
            
            # Percentage text
            c.setFillColor(self.colors['text_dark'])
            c.drawString(self.margin + 520, y, f"{percentage:.2f}%")
        
        # Dysbiosis Index
        self._draw_section_header(c, "DYSBIOSIS INDEX", self.height - 500)
        
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(self.colors['primary_blue'])
        c.drawString(self.margin, self.height - 540, f"Dysbiosis Index: {data.dysbiosis_index:.1f}")
        
        c.setFont("Helvetica", 12)
        c.setFillColor(self.colors['text_dark'])
        c.drawString(self.margin, self.height - 565, f"Category: {data.dysbiosis_category.title()}")
        
        self._draw_footer(c, 2)
    
    def _draw_page_3(self, c: canvas.Canvas, patient: PatientInfo, data: MicrobiomeData):
        """Draw Page 3: Clinical Analysis"""
        self._draw_header(c, patient, 3)
        
        # Clinical interpretation
        self._draw_section_header(c, "DYSBIOSIS INDEX INTERPRETATION", self.height - 200)
        
        c.setFont("Helvetica", 11)
        c.setFillColor(self.colors['text_dark'])
        
        # Wrap text for clinical interpretation
        interpretation_lines = self._wrap_text(data.clinical_interpretation, 70)
        y_pos = self.height - 240
        for line in interpretation_lines:
            c.drawString(self.margin, y_pos, line)
            y_pos -= 15
        
        # Recommendations
        self._draw_section_header(c, "RECOMMENDATIONS", self.height - 350)
        
        y_pos = self.height - 390
        for recommendation in data.recommendations:
            rec_lines = self._wrap_text(f"• {recommendation}", 70)
            for line in rec_lines:
                c.drawString(self.margin, y_pos, line)
                y_pos -= 15
            y_pos -= 5  # Extra spacing between recommendations
        
        self._draw_footer(c, 3)
    
    def _draw_page_4(self, c: canvas.Canvas, patient: PatientInfo, data: MicrobiomeData):
        """Draw Page 4: Laboratory Results"""
        self._draw_header(c, patient, 4)
        
        # Parasitological examination
        self._draw_section_header(c, "PARASITOLOGICAL EXAMINATION", self.height - 200)
        
        y_pos = self.height - 240
        c.setFont("Helvetica", 10)
        for parasite in data.parasite_results:
            c.drawString(self.margin, y_pos, f"{parasite['name']}: {parasite['result']}")
            y_pos -= 20
        
        # Microscopic examination
        self._draw_section_header(c, "MICROSCOPIC EXAMINATION", self.height - 350)
        
        y_pos = self.height - 390
        for result in data.microscopic_results:
            c.drawString(self.margin, y_pos, 
                        f"{result['parameter']}: {result['result']} (Ref: {result['reference']})")
            y_pos -= 20
        
        self._draw_footer(c, 4)
    
    def _draw_page_5(self, c: canvas.Canvas, patient: PatientInfo, data: MicrobiomeData):
        """Draw Page 5: Educational Content"""
        self._draw_header(c, patient, 5)
        
        self._draw_section_header(c, "UNDERSTANDING THE EQUINE MICROBIOME", self.height - 200)
        
        educational_text = [
            "The equine gut microbiome consists of trillions of microorganisms that play crucial roles in:",
            "• Digestion: Breaking down complex carbohydrates and fiber",
            "• Immunity: Supporting immune system development and function", 
            "• Metabolism: Producing essential vitamins and metabolites",
            "• Health: Protecting against pathogenic bacteria"
        ]
        
        c.setFont("Helvetica", 10)
        c.setFillColor(self.colors['text_dark'])
        y_pos = self.height - 240
        
        for line in educational_text:
            text_lines = self._wrap_text(line, 80)
            for wrapped_line in text_lines:
                c.drawString(self.margin, y_pos, wrapped_line)
                y_pos -= 15
            y_pos -= 5
        
        self._draw_footer(c, 5)
    
    def _draw_header(self, c: canvas.Canvas, patient: PatientInfo, page_num: int):
        """Draw professional header with logo and patient information"""
        # Header background
        c.setFillColor(self.colors['header_bg'])
        c.rect(0, self.height - 120, self.width, 120, fill=1, stroke=0)
        
        # Logo placeholder
        c.setFillColor(self.colors['primary_blue'])
        c.rect(self.margin, self.height - 100, 80, 60, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(self.margin + 40, self.height - 75, "HIPPOVET")
        c.drawCentredString(self.margin + 40, self.height - 85, "LOGO")
        
        # Patient info pill boxes
        pill_y = self.height - 90
        pill_boxes = [
            patient.name,
            patient.species,
            patient.age,
            f"Sample: {patient.sample_number}"
        ]
        
        x_start = self.margin + 120
        for i, text in enumerate(pill_boxes):
            x = x_start + (i * 120)
            self._draw_pill_box(c, x, pill_y, 110, 25, text)
        
        # Accreditation info (right side)
        c.setFillColor(self.colors['text_dark'])
        c.setFont("Helvetica", 8)
        c.drawRightString(self.width - self.margin, self.height - 45, f"Received: {patient.date_received}")
        c.drawRightString(self.width - self.margin, self.height - 55, f"Analyzed: {patient.date_analyzed}")
        c.drawRightString(self.width - self.margin, self.height - 65, f"Performed by: {patient.performed_by}")
        c.drawRightString(self.width - self.margin, self.height - 75, f"Requested by: {patient.requested_by}")
    
    def _draw_footer(self, c: canvas.Canvas, page_num: int):
        """Draw professional footer"""
        # Footer background
        c.setFillColor(self.colors['header_bg'])
        c.rect(0, 0, self.width, 50, fill=1, stroke=0)
        
        # Laboratory info
        c.setFillColor(self.colors['text_dark'])
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.margin, 30, "HippoVet Laboratory")
        c.setFont("Helvetica", 7)
        c.drawString(self.margin, 20, "Veterinary Microbiome Analysis Center")
        c.drawString(self.margin, 10, "Accredited Laboratory - ISO 15189")
        
        # Contact info (center)
        c.drawString(self.width/2 - 50, 30, "Tel: +48 123 456 789")
        c.drawString(self.width/2 - 50, 20, "Email: lab@hippovet.com")
        c.drawString(self.width/2 - 50, 10, "www.hippovet.com")
        
        # Page number (right)
        c.drawRightString(self.width - self.margin, 20, f"Page {page_num} of 5")
    
    def _draw_pill_box(self, c: canvas.Canvas, x: float, y: float, width: float, height: float, text: str):
        """Draw rounded rectangle with text (pill-shaped box)"""
        radius = height / 2
        
        # Background
        c.setFillColor(colors.white)
        c.setStrokeColor(self.colors['border_gray'])
        c.roundRect(x, y, width, height, radius, stroke=1, fill=1)
        
        # Text
        c.setFillColor(self.colors['text_dark'])
        c.setFont("Helvetica", 8)
        text_width = c.stringWidth(text, "Helvetica", 8)
        if text_width > width - 10:  # Truncate if too long
            text = text[:int(len(text) * (width - 10) / text_width)] + "..."
        c.drawCentredString(x + width/2, y + height/3, text)
    
    def _draw_section_header(self, c: canvas.Canvas, title: str, y: float):
        """Draw green section header"""
        # Green background
        c.setFillColor(self.colors['green'])
        c.rect(self.margin, y - 5, self.width - 2*self.margin, 25, fill=1, stroke=0)
        
        # White text
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin + 10, y + 5, title)
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """Simple text wrapping"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines