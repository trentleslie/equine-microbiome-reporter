"""
PDF Builder - Uses WeasyPrint to convert HTML/CSS templates to professional PDFs
Integrates with Matplotlib chart generation for data visualization
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from .data_models import PatientInfo, MicrobiomeData
from .chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class PDFBuilder:
    """Build PDF from HTML templates using WeasyPrint"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.chart_generator = ChartGenerator()
        self.font_config = FontConfiguration()
        
        logger.info("PDFBuilder (WeasyPrint) initialized")
    
    def build_from_content(self, content: str, output_path: str, 
                          patient_info: PatientInfo, data: MicrobiomeData) -> bool:
        """
        Convert HTML content to PDF using WeasyPrint
        
        Args:
            content: Rendered HTML content from Jinja2 templates
            output_path: Where to save the generated PDF
            patient_info: Patient information (not used directly here)
            data: Microbiome data (not used directly here)
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Building PDF with WeasyPrint: {output_path}")
            
            # Get the base URL for resolving relative paths
            template_dir = Path(__file__).parent.parent / "templates"
            assets_dir = Path(__file__).parent.parent / "assets"
            
            # Create base URL for WeasyPrint
            base_url = f"file://{str(template_dir.absolute())}/"
            
            # Generate the PDF
            html = HTML(string=content, base_url=base_url)
            
            # Add custom CSS if needed
            css = CSS(string=self._get_print_css(), font_config=self.font_config)
            
            # Write PDF
            html.write_pdf(output_path, stylesheets=[css], font_config=self.font_config)
            
            logger.info(f"PDF successfully created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF building failed: {e}", exc_info=True)
            return False
    
    def build_with_charts(self, template_content: str, output_path: str,
                         patient_info: PatientInfo, data: MicrobiomeData) -> bool:
        """
        Generate charts and build PDF with embedded visualizations
        
        Args:
            template_content: HTML template with placeholders for charts
            output_path: Where to save the generated PDF
            patient_info: Patient information
            data: Microbiome data for chart generation
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info("Generating charts for PDF")
            
            # Generate all charts
            chart_paths = self.chart_generator.generate_all_charts(data)
            
            # Replace chart placeholders in template
            html_content = template_content
            for chart_name, chart_path in chart_paths.items():
                placeholder = f"{{{{ charts.{chart_name} }}}}"
                html_content = html_content.replace(placeholder, chart_path)
            
            # Build PDF
            success = self.build_from_content(html_content, output_path, patient_info, data)
            
            # Note: Don't cleanup charts here as they're generated externally
            # and might be needed for the conversion process
            
            return success
            
        except Exception as e:
            logger.error(f"PDF building with charts failed: {e}", exc_info=True)
            return False
    
    def _get_print_css(self) -> str:
        """Additional CSS for print optimization"""
        return """
        /* Print-specific CSS */
        @page {
            size: A4;
            margin: 0;
        }
        
        /* Ensure pages don't break in the middle of content */
        .page {
            page-break-after: always;
            page-break-inside: avoid;
        }
        
        /* High-quality image rendering */
        img {
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
            max-width: 100%;
            height: auto;
        }
        
        /* Force color printing */
        * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            color-adjust: exact !important;
        }
        
        /* Ensure backgrounds print */
        body {
            background-color: white !important;
        }
        
        .section-header {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        """