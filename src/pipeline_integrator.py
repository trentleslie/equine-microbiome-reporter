"""
Pipeline Integration Module

Integrates FASTQ processing with the existing PDF report generation system.
Provides a complete workflow from FASTQ files to final PDF reports.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from .fastq_qc import FASTQQualityControl
from .fastq_converter import FASTQtoCSVConverter
from .report_generator import ReportGenerator
from .data_models import PatientInfo


class MicrobiomePipelineIntegrator:
    """Integrate FASTQ processing with PDF report generation"""
    
    def __init__(self, output_dir: str = "pipeline_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.qc_dir = self.output_dir / "qc_reports"
        self.csv_dir = self.output_dir / "csv_files"
        self.pdf_dir = self.output_dir / "pdf_reports"
        
        for dir in [self.qc_dir, self.csv_dir, self.pdf_dir]:
            dir.mkdir(exist_ok=True)
    
    def process_sample(self, 
                      fastq_file: str, 
                      patient_info: Dict,
                      barcode_column: str = "barcode59",
                      run_qc: bool = True,
                      generate_pdf: bool = True,
                      language: str = "en") -> Dict:
        """
        Complete pipeline: FASTQ -> QC -> CSV -> PDF
        
        Args:
            fastq_file: Path to FASTQ file
            patient_info: Dictionary with patient information
            barcode_column: Column name for this sample in CSV
            run_qc: Whether to run quality control
            generate_pdf: Whether to generate PDF report
            language: Language for PDF report (en, pl, jp)
            
        Returns:
            Dictionary with paths to generated files
        """
        sample_name = Path(fastq_file).stem
        results = {"sample_name": sample_name}
        
        # Step 1: Quality Control
        if run_qc:
            print(f"\n{'='*50}")
            print(f"Step 1: Running Quality Control for {sample_name}")
            print(f"{'='*50}")
            
            qc = FASTQQualityControl(fastq_file)
            qc_results = qc.run_qc()
            qc.print_summary()
            
            # Save QC plots
            qc_plot_path = self.qc_dir / f"{sample_name}_qc_report.png"
            qc.plot_quality_metrics(save_path=str(qc_plot_path))
            results["qc_plot"] = qc_plot_path
            results["qc_summary"] = qc.get_qc_summary()
        
        # Step 2: FASTQ to CSV Conversion
        print(f"\n{'='*50}")
        print(f"Step 2: Converting FASTQ to CSV")
        print(f"{'='*50}")
        
        converter = FASTQtoCSVConverter()
        df = converter.process_fastq_files(
            [fastq_file],
            sample_names=[barcode_column.replace("barcode", "")],
            barcode_column=barcode_column
        )
        
        # Save CSV
        csv_path = self.csv_dir / f"{sample_name}_abundance.csv"
        converter.save_to_csv(df, str(csv_path))
        results["csv_path"] = csv_path
        results["processing_stats"] = converter.get_processing_stats()
        
        # Step 3: Generate PDF Report
        if generate_pdf:
            print(f"\n{'='*50}")
            print(f"Step 3: Generating PDF Report")
            print(f"{'='*50}")
            
            # Create patient info object
            patient = PatientInfo(
                name=patient_info.get('name', 'Unknown'),
                age=patient_info.get('age', 'Unknown'),
                sample_number=patient_info.get('sample_number', '001'),
                performed_by=patient_info.get('performed_by', 'Laboratory Staff'),
                requested_by=patient_info.get('requested_by', 'Veterinarian')
            )
            
            # Generate report
            generator = ReportGenerator(language=language)
            pdf_path = self.pdf_dir / f"{sample_name}_report_{language}.pdf"
            
            success = generator.generate_report(
                csv_path=str(csv_path),
                patient_info=patient,
                output_path=str(pdf_path)
            )
            
            if success:
                print(f"✅ PDF report generated successfully: {pdf_path}")
                results["pdf_path"] = pdf_path
            else:
                print(f"❌ Failed to generate PDF report")
        
        print(f"\n{'='*50}")
        print(f"Pipeline Complete for {sample_name}!")
        print(f"{'='*50}")
        
        return results
    
    def batch_process(self, sample_manifest: pd.DataFrame) -> List[Dict]:
        """
        Process multiple samples from a manifest file
        
        Args:
            sample_manifest: DataFrame with columns:
                - fastq_path: Path to FASTQ file
                - sample_name: Sample identifier
                - patient_name: Patient name
                - patient_age: Patient age
                - other patient info columns...
                
        Returns:
            List of result dictionaries for each sample
        """
        results = []
        
        for idx, row in sample_manifest.iterrows():
            print(f"\n\n{'#'*60}")
            print(f"Processing sample {idx + 1}/{len(sample_manifest)}: {row['sample_name']}")
            print(f"{'#'*60}")
            
            patient_info = {
                'name': row.get('patient_name', 'Unknown'),
                'age': row.get('patient_age', 'Unknown'),
                'sample_number': row.get('sample_name', f'S{idx+1}'),
                'performed_by': row.get('performed_by', 'Laboratory Staff'),
                'requested_by': row.get('requested_by', 'Veterinarian')
            }
            
            result = self.process_sample(
                fastq_file=row['fastq_path'],
                patient_info=patient_info,
                barcode_column=f"barcode{row.get('barcode_num', 59)}",
                language=row.get('language', 'en')
            )
            
            results.append(result)
        
        # Generate summary report
        self._generate_batch_summary(results)
        
        return results
    
    def _generate_batch_summary(self, results: List[Dict]):
        """Generate summary report for batch processing"""
        summary_path = self.output_dir / "batch_summary.txt"
        
        with open(summary_path, "w") as f:
            f.write("Batch Processing Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total samples processed: {len(results)}\n\n")
            
            for result in results:
                f.write(f"Sample: {result['sample_name']}\n")
                if 'qc_summary' in result:
                    qc = result['qc_summary']
                    f.write(f"  - QC: Mean Q{qc['mean_quality']}, {qc['total_reads']} reads\n")
                    f.write(f"  - Q20: {qc['q20_percentage']:.1f}%, Q30: {qc['q30_percentage']:.1f}%\n")
                if 'processing_stats' in result:
                    stats = result['processing_stats']
                    f.write(f"  - Sequences: {stats['total_sequences']} total, {stats['unique_sequences']} unique\n")
                if 'csv_path' in result:
                    f.write(f"  - CSV: {result['csv_path'].name}\n")
                if 'pdf_path' in result:
                    f.write(f"  - PDF: {result['pdf_path'].name}\n")
                f.write("\n")
        
        print(f"\nBatch summary saved to: {summary_path}")
    
    @staticmethod
    def create_manifest_template(output_path: str = "manifest_template.csv"):
        """Create a template manifest file for batch processing"""
        template_data = {
            'fastq_path': [
                'path/to/sample1.fastq.gz',
                'path/to/sample2.fastq.gz',
                'path/to/sample3.fastq.gz'
            ],
            'sample_name': ['S001', 'S002', 'S003'],
            'patient_name': ['Thunder', 'Lightning', 'Storm'],
            'patient_age': ['15 years', '10 years', '8 years'],
            'barcode_num': [59, 60, 61],
            'performed_by': ['Dr. Smith', 'Dr. Smith', 'Dr. Jones'],
            'requested_by': ['Dr. Johnson', 'Dr. Johnson', 'Dr. Williams'],
            'language': ['en', 'en', 'en']
        }
        
        df = pd.DataFrame(template_data)
        df.to_csv(output_path, index=False)
        print(f"Created manifest template: {output_path}")
        
        return df