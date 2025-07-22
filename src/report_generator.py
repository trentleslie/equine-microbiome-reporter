"""
Main report generation orchestrator
Coordinates CSV processing, template rendering, and PDF creation
"""

import yaml
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Optional

from .data_models import PatientInfo, MicrobiomeData
from .csv_processor import CSVProcessor
from .pdf_builder import PDFBuilder

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Main report generation orchestrator"""
    
    def __init__(self, language: str = "en", template_name: str = "report_full.j2"):
        self.language = language
        self.template_name = template_name
        
        # Setup Jinja2 environment
        template_path = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load configuration
        config_path = Path(__file__).parent.parent / "config" / "report_config.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            self.config = self._get_default_config()
        
        logger.info(f"ReportGenerator initialized for language: {language}")
    
    def generate_report(self, csv_path: str, patient_info: PatientInfo, output_path: str) -> bool:
        """
        Generate complete PDF report
        
        Args:
            csv_path: Path to CSV data file
            patient_info: Patient and test information
            output_path: Where to save the generated PDF
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Starting report generation for {patient_info.name}")
            
            # Step 1: Process CSV data
            processor = CSVProcessor(csv_path)
            microbiome_data = processor.process()
            logger.info(f"Processed {microbiome_data.total_species_count} species")
            
            # Step 2: Add enhanced clinical interpretations
            microbiome_data.clinical_interpretation = self._generate_clinical_text(microbiome_data)
            microbiome_data.recommendations = self._get_recommendations(microbiome_data)
            
            # Step 3: Render template
            content = self._render_template(patient_info, microbiome_data)
            
            # Step 4: Build PDF (placeholder for now)
            success = self._build_pdf(content, output_path, patient_info, microbiome_data)
            
            if success:
                logger.info(f"Report successfully generated: {output_path}")
            else:
                logger.error("Report generation failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return False
    
    def _render_template(self, patient_info: PatientInfo, microbiome_data: MicrobiomeData) -> str:
        """Render Jinja2 template with data"""
        try:
            template_path = f"{self.language}/{self.template_name}"
            template = self.env.get_template(template_path)
            
            content = template.render(
                patient=patient_info,
                data=microbiome_data,
                config=self.config,
                lang=self.language
            )
            
            logger.info(f"Template rendered successfully: {template_path}")
            return content
            
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise
    
    def _generate_clinical_text(self, data: MicrobiomeData) -> str:
        """Generate clinical interpretation text"""
        if data.dysbiosis_category == "normal":
            return "Normal microbiota (healthy). Lack of dysbiosis signs; gut microflora is balanced with minor deviations."
        elif data.dysbiosis_category == "mild":
            return "Mild dysbiosis detected. Moderate imbalance in gut microflora composition requiring monitoring."
        else:
            return "Severe dysbiosis detected. Significant imbalance in gut microflora requiring intervention."
    
    def _get_recommendations(self, data: MicrobiomeData) -> list:
        """Get recommendations based on dysbiosis level"""
        if data.dysbiosis_index <= 20:
            return [
                "Continue current feeding regimen",
                "Regular monitoring recommended",
                "Consider prebiotics if stress occurs"
            ]
        elif data.dysbiosis_index <= 50:
            return [
                "Review current diet composition",
                "Consider probiotic supplementation",
                "Monitor for clinical symptoms",
                "Retest in 4-6 weeks"
            ]
        else:
            return [
                "Immediate dietary intervention required",
                "Veterinary consultation recommended",
                "Probiotic therapy indicated",
                "Follow-up testing in 2-3 weeks"
            ]
    
    def _build_pdf(self, content: str, output_path: str, patient_info: PatientInfo, data: MicrobiomeData) -> bool:
        """Build PDF from template content using PDFBuilder"""
        try:
            # Save HTML output for debugging
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Template output saved as HTML: {html_path}")
            
            # Build PDF using PDFBuilder
            builder = PDFBuilder(self.config)
            success = builder.build_from_content(content, output_path, patient_info, data)
            
            return success
            
        except Exception as e:
            logger.error(f"PDF building failed: {e}")
            return False
    
    def _get_default_config(self) -> dict:
        """Default configuration if config file not found"""
        return {
            "reference_ranges": {
                "Actinomycetota": [0.1, 8.0],
                "Bacillota": [20.0, 70.0],
                "Bacteroidota": [4.0, 40.0],
                "Pseudomonadota": [2.0, 35.0],
                "Fibrobacterota": [0.1, 5.0]
            },
            "dysbiosis_thresholds": {
                "normal": 20,
                "mild": 50
            },
            "colors": {
                "primary_blue": "#1E3A8A",
                "green": "#10B981",
                "teal": "#14B8A6"
            },
            "laboratory": {
                "name": "HippoVet Laboratory",
                "accreditation": "ISO 15189"
            }
        }