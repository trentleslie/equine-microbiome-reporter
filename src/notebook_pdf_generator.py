"""
Notebook-friendly PDF generator using Jinja2 templates
Avoids relative import issues for Jupyter notebook usage
"""

import os
import sys
import yaml
import logging
import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

# Load environment variables from project root
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    load_dotenv(env_path)
except ImportError:
    # dotenv not available, environment variables should be set by system
    pass

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the official data models instead of defining locally
try:
    from data_models import MicrobiomeData, PatientInfo
except ImportError:
    # Fallback for notebook usage - try alternative import
    try:
        from notebook_interface import PatientInfo
        from data_models import MicrobiomeData
    except ImportError:
        import sys
        from pathlib import Path
        src_path = Path(__file__).parent
        sys.path.insert(0, str(src_path))
        from data_models import MicrobiomeData, PatientInfo

class NotebookPDFGenerator:
    """Jinja2-based PDF generator for notebook use"""
    
    def __init__(self, language: str = "en", template_name: str = "report_full.j2"):
        self.language = language
        self.template_name = template_name
        self.logger = logging.getLogger(__name__)
        
        # Setup paths relative to project root
        project_root = current_dir.parent
        template_path = project_root / "templates"
        config_path = project_root / "config" / "report_config.yaml"
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load configuration
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
            self.config = self._get_default_config()
        
        self.logger.info(f"NotebookPDFGenerator initialized for language: {language}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is missing"""
        return {
            'reference_ranges': {
                'Actinomycetota': [0.1, 8.0],
                'Bacillota': [20.0, 70.0],
                'Bacteroidota': [4.0, 40.0],
                'Pseudomonadota': [2.0, 35.0],
                'Fibrobacterota': [0.1, 5.0]
            },
            'dysbiosis_thresholds': {
                'normal': 20,
                'mild': 50
            },
            'laboratory': {
                'name': 'Equine Microbiome Laboratory',
                'address': 'Research Facility',
                'phone': '+1-XXX-XXX-XXXX'
            }
        }
    
    def process_csv_data(self, csv_path: str, barcode_column: str = None) -> MicrobiomeData:
        """
        Process CSV data to create MicrobiomeData object
        
        Args:
            csv_path: Path to CSV file
            barcode_column: Specific barcode column to process (optional)
            
        Returns:
            MicrobiomeData object
        """
        df = pd.read_csv(csv_path)
        
        # If specific barcode column specified, filter for that sample
        if barcode_column and barcode_column in df.columns:
            # Create a view focused on this barcode
            sample_data = df[df[barcode_column] > 0].copy()
            if len(sample_data) == 0:
                sample_data = df.copy()  # Fallback to all data
        else:
            sample_data = df.copy()
        
        # Prepare species list - match ChartGenerator expectations
        species_list = []
        for _, row in sample_data.iterrows():
            species_data = {
                'species': row['species'],  # Use 'species' key to match ChartGenerator
                'percentage': (row['total'] / sample_data['total'].sum()) * 100 if sample_data['total'].sum() > 0 else 0,
                'phylum': row.get('phylum', 'Unknown'),
                'genus': row.get('genus', 'Unknown'),
                'reads': row['total']
            }
            species_list.append(species_data)
        
        # Sort by percentage for top species charts
        species_list.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Calculate phylum distribution
        if 'phylum' in sample_data.columns:
            phylum_totals = sample_data.groupby('phylum')['total'].sum()
            total_reads = phylum_totals.sum()
            phylum_distribution = {}
            for phylum, count in phylum_totals.items():
                phylum_distribution[phylum] = (count / total_reads) * 100 if total_reads > 0 else 0
        else:
            phylum_distribution = {}
        
        # Calculate dysbiosis index (simplified)
        dysbiosis_index = self._calculate_dysbiosis_index(phylum_distribution)
        
        # Determine dysbiosis category
        if dysbiosis_index < self.config['dysbiosis_thresholds']['normal']:
            dysbiosis_category = "Normal"
        elif dysbiosis_index < self.config['dysbiosis_thresholds']['mild']:
            dysbiosis_category = "Mild Dysbiosis"
        else:
            dysbiosis_category = "Severe Dysbiosis"
        
        # Generate clinical interpretation
        clinical_interpretation = self._generate_clinical_interpretation(phylum_distribution, dysbiosis_category)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dysbiosis_category, phylum_distribution)
        
        return MicrobiomeData(
            species_list=species_list,
            phylum_distribution=phylum_distribution,
            dysbiosis_index=dysbiosis_index,
            total_species_count=len(species_list),
            dysbiosis_category=dysbiosis_category,
            clinical_interpretation=clinical_interpretation,
            recommendations=recommendations
        )
    
    def _calculate_dysbiosis_index(self, phylum_distribution: Dict[str, float]) -> float:
        """Calculate dysbiosis index based on phylum distribution"""
        dysbiosis_score = 0.0
        reference_ranges = self.config['reference_ranges']
        
        for phylum, percentage in phylum_distribution.items():
            if phylum in reference_ranges:
                min_val, max_val = reference_ranges[phylum]
                if percentage < min_val:
                    dysbiosis_score += (min_val - percentage) / min_val * 100
                elif percentage > max_val:
                    dysbiosis_score += (percentage - max_val) / max_val * 100
            else:
                # Unknown phylum contributes to dysbiosis
                dysbiosis_score += percentage * 0.1
        
        return dysbiosis_score
    
    def _generate_clinical_interpretation(self, phylum_distribution: Dict[str, float], category: str) -> str:
        """Generate clinical interpretation text"""
        interpretations = []
        
        if category == "Normal":
            interpretations.append("The microbiome analysis shows a balanced bacterial community with phylum distributions within normal ranges.")
        elif category == "Mild Dysbiosis":
            interpretations.append("The analysis indicates mild dysbiosis with some bacterial imbalances detected.")
        else:
            interpretations.append("Significant dysbiosis detected with notable bacterial community imbalances.")
        
        # Add phylum-specific interpretations
        for phylum, percentage in phylum_distribution.items():
            if phylum in self.config['reference_ranges']:
                min_val, max_val = self.config['reference_ranges'][phylum]
                if percentage < min_val:
                    interpretations.append(f"{phylum} levels are below normal range ({percentage:.1f}% vs {min_val}-{max_val}%).")
                elif percentage > max_val:
                    interpretations.append(f"{phylum} levels are above normal range ({percentage:.1f}% vs {min_val}-{max_val}%).")
        
        return " ".join(interpretations)
    
    def _generate_recommendations(self, category: str, phylum_distribution: Dict[str, float]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if category == "Normal":
            recommendations.extend([
                "Continue current feeding regimen",
                "Monitor for any digestive changes",
                "Consider periodic follow-up testing"
            ])
        elif category == "Mild Dysbiosis":
            recommendations.extend([
                "Consider probiotic supplementation",
                "Review current diet and feeding practices",
                "Monitor closely for clinical symptoms",
                "Retest in 4-6 weeks"
            ])
        else:  # Severe Dysbiosis
            recommendations.extend([
                "Immediate veterinary consultation recommended",
                "Consider targeted probiotic therapy",
                "Review and modify feeding regimen",
                "Monitor for clinical signs of digestive distress",
                "Retest in 2-4 weeks to assess improvement"
            ])
        
        # Add specific recommendations based on phylum imbalances
        if 'Bacillota' in phylum_distribution:
            bacillota_pct = phylum_distribution['Bacillota']
            if bacillota_pct > 70:
                recommendations.append("Consider reducing grain intake to balance Bacillota levels")
            elif bacillota_pct < 20:
                recommendations.append("Consider fiber supplementation to support Bacillota growth")
        
        return recommendations
    
    def _generate_charts(self, microbiome_data: MicrobiomeData) -> Dict[str, str]:
        """Generate charts for the report using inline matplotlib"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np
            from pathlib import Path
            
            # Create temp directory
            temp_dir = Path("temp_charts")
            temp_dir.mkdir(exist_ok=True)
            
            chart_paths = {}
            
            # Generate species distribution chart
            if microbiome_data.species_list:
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Get top 20 species
                top_species = microbiome_data.species_list[:20]
                species_names = [s['species'][:40] + '...' if len(s['species']) > 40 else s['species'] for s in top_species]
                percentages = [s['percentage'] for s in top_species]
                
                # Create horizontal bar chart
                y_pos = np.arange(len(species_names))
                bars = ax.barh(y_pos, percentages, color='#14B8A6', alpha=0.8)
                
                # Add percentage labels
                for i, (bar, pct) in enumerate(zip(bars, percentages)):
                    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                           f'{pct:.2f}%', va='center', fontsize=9)
                
                ax.set_yticks(y_pos)
                ax.set_yticklabels([f"{i+1}. {name}" for i, name in enumerate(species_names)], fontsize=9)
                ax.set_xlabel('Percentage (%)')
                ax.set_title('MICROBIOTIC PROFILE - Top Species Distribution', fontweight='bold', pad=20)
                ax.grid(axis='x', alpha=0.3)
                
                plt.tight_layout()
                species_chart_path = temp_dir / "species_distribution.png"
                plt.savefig(species_chart_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                chart_paths['species_distribution'] = str(species_chart_path.absolute())
            
            # Generate phylum distribution chart
            if microbiome_data.phylum_distribution:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                phyla = list(microbiome_data.phylum_distribution.keys())
                percentages = list(microbiome_data.phylum_distribution.values())
                
                # Color scheme
                colors = ['#14B8A6', '#10B981', '#3B82F6', '#8B5CF6', '#06B6D4', '#94A3B8']
                
                y_pos = np.arange(len(phyla))
                bars = ax.barh(y_pos, percentages, height=0.6, 
                              color=[colors[i % len(colors)] for i in range(len(phyla))], alpha=0.8)
                
                # Add percentage labels
                for i, (bar, pct) in enumerate(zip(bars, percentages)):
                    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                           f'{pct:.1f}%', va='center', fontweight='bold')
                
                ax.set_yticks(y_pos)
                ax.set_yticklabels(phyla, fontsize=11, fontweight='bold')
                ax.set_xlabel('Percentage (%)', fontsize=12)
                ax.set_title('PHYLUM DISTRIBUTION IN GUT MICROFLORA', fontweight='bold', fontsize=14, pad=20)
                ax.grid(axis='x', alpha=0.3)
                ax.set_xlim(0, 100)
                
                plt.tight_layout()
                phylum_chart_path = temp_dir / "phylum_distribution.png"
                plt.savefig(phylum_chart_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                chart_paths['phylum_distribution'] = str(phylum_chart_path.absolute())
            
            self.logger.info(f"Generated {len(chart_paths)} charts successfully")
            return chart_paths
            
        except Exception as e:
            self.logger.error(f"Chart generation failed: {e}")
            import traceback
            traceback.print_exc()
            # Return empty paths if chart generation fails - templates will handle missing charts gracefully
            return {
                'species_distribution': '',
                'phylum_distribution': '',
                'phylum_comparison': ''
            }
    
    def _cleanup_charts(self):
        """Clean up temporary chart files"""
        try:
            chart_dir = Path("temp_charts")
            if chart_dir.exists():
                for file in chart_dir.glob("*.png"):
                    file.unlink()
                if not list(chart_dir.iterdir()):
                    chart_dir.rmdir()
            self.logger.info("Temporary chart files cleaned up")
        except Exception as e:
            self.logger.warning(f"Error cleaning up chart files: {e}")
    
    def generate_report(self, csv_path: str, patient_info: PatientInfo, output_path: str, 
                       barcode_column: str = None, include_llm_recommendations: bool = True) -> bool:
        """
        Generate complete PDF report using Jinja2 templates
        
        Args:
            csv_path: Path to CSV data file
            patient_info: Patient information
            output_path: Where to save the generated PDF
            barcode_column: Specific barcode column to process
            include_llm_recommendations: Whether to include AI-powered recommendations
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting report generation for {patient_info.name}")
            
            # Process CSV data
            microbiome_data = self.process_csv_data(csv_path, barcode_column)
            self.logger.info(f"Processed {microbiome_data.total_species_count} species")
            
            # Generate charts for the report
            chart_paths = self._generate_charts(microbiome_data)
            self.logger.info(f"Generated {len(chart_paths)} charts")
            
            # Generate LLM recommendations if enabled
            if include_llm_recommendations:
                try:
                    from notebook_llm_engine import NotebookLLMEngine
                    llm_engine = NotebookLLMEngine()
                    
                    if llm_engine.enabled:
                        llm_recommendations = llm_engine.generate_recommendations(microbiome_data, patient_info)
                        microbiome_data.recommendations.extend(llm_recommendations)
                        self.logger.info(f"Added {len(llm_recommendations)} LLM-powered recommendations")
                    else:
                        status = llm_engine.get_status()
                        self.logger.info(f"LLM Enabled: {status['enabled']}")
                        self.logger.info(f"LLM Provider: {status['provider']}")
                        self.logger.info(f"API Key Configured: {status['api_key_configured']}")
                        if not status['enabled']:
                            self.logger.warning("⚠️  LLM is disabled. Set ENABLE_LLM_RECOMMENDATIONS=true in .env to enable.")
                        
                except ImportError as e:
                    self.logger.warning(f"LLM recommendations unavailable: {e}")
                except Exception as e:
                    self.logger.error(f"LLM recommendation generation failed: {e}")
            
            # Prepare template context
            template_context = {
                'patient': patient_info,
                'data': microbiome_data,  # Match the main ReportGenerator naming
                'microbiome_data': microbiome_data,  # Keep for backwards compatibility
                'config': self.config,
                'charts': chart_paths,  # Add charts to context
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'analysis_summary': {
                    'total_species': microbiome_data.total_species_count,
                    'dysbiosis_index': microbiome_data.dysbiosis_index,
                    'dysbiosis_category': microbiome_data.dysbiosis_category,
                    'dominant_phylum': max(microbiome_data.phylum_distribution.items(), 
                                         key=lambda x: x[1])[0] if microbiome_data.phylum_distribution else 'Unknown'
                }
            }
            
            # Load and render template
            template_file = f"{self.language}/{self.template_name}"
            try:
                template = self.env.get_template(template_file)
            except TemplateNotFound:
                self.logger.error(f"Template not found: {template_file}")
                return False
            
            # Render HTML content
            html_content = template.render(**template_context)
            
            # Convert HTML to PDF using weasyprint
            try:
                import weasyprint
                weasyprint.HTML(string=html_content).write_pdf(output_path)
                self.logger.info(f"PDF report generated: {output_path}")
                
                # Clean up temporary chart files
                self._cleanup_charts()
                return True
            except ImportError:
                self.logger.error("weasyprint not available, falling back to simple HTML output")
                # Save as HTML file instead
                html_output_path = output_path.replace('.pdf', '.html')
                with open(html_output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"HTML report generated: {html_output_path}")
                
                # Clean up temporary chart files
                self._cleanup_charts()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_batch_reports(self, csv_path: str, patients: List[PatientInfo], 
                             output_dir: str, barcode_columns: List[str] = None) -> List[bool]:
        """
        Generate reports for multiple patients
        
        Args:
            csv_path: Path to CSV data file
            patients: List of patient information
            output_dir: Directory for output files
            barcode_columns: List of barcode columns matching patients
            
        Returns:
            List of success status for each report
        """
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, patient in enumerate(patients):
            barcode_col = barcode_columns[i] if barcode_columns and i < len(barcode_columns) else None
            pdf_filename = f"report_{patient.name}_{patient.sample_number}.pdf"
            pdf_path = output_path / pdf_filename
            
            self.logger.info(f"Generating report {i+1}/{len(patients)}: {patient.name}")
            success = self.generate_report(csv_path, patient, str(pdf_path), barcode_col)
            results.append(success)
        
        return results