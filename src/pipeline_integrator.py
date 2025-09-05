"""
Pipeline Integration Module

TDD GREEN Phase: Enhanced with Kraken2 integration support.
Integrates FASTQ processing with existing PDF report generation system.
Provides complete workflow from FASTQ files to final PDF reports with Kraken2 classification.
"""

import pandas as pd
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from .fastq_qc import FASTQQualityControl
from .fastq_converter import FASTQtoCSVConverter
from .report_generator import ReportGenerator
from .data_models import PatientInfo

# Import Kraken2 components for integration
try:
    from .kraken2_classifier import Kraken2FallbackManager, Kraken2Classifier
    KRAKEN2_AVAILABLE = True
except ImportError:
    KRAKEN2_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.info("Kraken2 classifier not available, using existing pipeline only")


class MicrobiomePipelineIntegrator:
    """Integrate FASTQ processing with PDF report generation"""
    
    def __init__(self, output_dir: str = "pipeline_output",
                 # TDD GREEN: Add Kraken2 integration parameters
                 use_kraken2: bool = False,
                 kraken2_db_path: Optional[str] = None,
                 kraken2_threads: int = 4,
                 kraken2_confidence: float = 0.1,
                 auto_detect_kraken2: bool = False):
        """
        Initialize pipeline integrator with optional Kraken2 support.
        
        TDD GREEN Phase: Enhanced constructor for integration tests.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.qc_dir = self.output_dir / "qc_reports"
        self.csv_dir = self.output_dir / "csv_files"
        self.pdf_dir = self.output_dir / "pdf_reports"
        
        for dir in [self.qc_dir, self.csv_dir, self.pdf_dir]:
            dir.mkdir(exist_ok=True)
        
        # TDD GREEN: Kraken2 configuration
        self.kraken2_db_path = kraken2_db_path
        self.kraken2_threads = kraken2_threads
        self.kraken2_confidence = kraken2_confidence
        self.use_kraken2 = use_kraken2 and KRAKEN2_AVAILABLE
        
        # Auto-detection of Kraken2 availability
        if auto_detect_kraken2:
            self.kraken2_available = self._detect_kraken2_availability()
        else:
            self.kraken2_available = self.use_kraken2
        
        # Validate Kraken2 configuration if enabled
        if self.use_kraken2:
            self._validate_kraken2_setup()
    
    def _detect_kraken2_availability(self) -> bool:
        """Detect if Kraken2 is available and properly configured."""
        if not KRAKEN2_AVAILABLE:
            return False
        
        if not self.kraken2_db_path:
            return False
        
        try:
            classifier = Kraken2Classifier(self.kraken2_db_path)
            return classifier.validate_database()
        except Exception:
            return False
    
    def _validate_kraken2_setup(self) -> None:
        """Validate Kraken2 configuration and disable if invalid."""
        if not self.kraken2_db_path:
            logging.warning("Kraken2 enabled but no database path provided")
            self.use_kraken2 = False
            return
        
        db_path = Path(self.kraken2_db_path)
        if not db_path.exists():
            logging.warning(f"Kraken2 database path does not exist: {db_path}")
            self.use_kraken2 = False
            return
    
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
        
        # Step 2: Taxonomic Classification (Kraken2 or BioPython)
        print(f"\n{'='*50}")
        print(f"Step 2: Taxonomic Classification")
        print(f"{'='*50}")
        
        # TDD GREEN: Add timing and integration tracking
        start_time = time.time()
        
        # Determine which classifier to use
        use_kraken2_method = self.use_kraken2 and self._should_use_kraken2()
        
        if use_kraken2_method:
            print("Using Kraken2 for taxonomic classification...")
            try:
                df = self._process_with_kraken2([fastq_file], barcode_column)
                results["classification_method"] = "kraken2"
                results["kraken2_used"] = True
            except Exception as e:
                print(f"Kraken2 processing failed: {e}")
                print("Falling back to existing pipeline...")
                df = self._classify_with_biopython([fastq_file], sample_name, barcode_column)
                results["classification_method"] = "biopython_fallback"
                results["kraken2_used"] = False
                results["fallback_reason"] = str(e)
        else:
            print("Using existing pipeline for taxonomic classification...")
            df = self._classify_with_biopython([fastq_file], sample_name, barcode_column)
            results["classification_method"] = "biopython"
            results["kraken2_used"] = False
        
        # Record processing time
        end_time = time.time()
        results["processing_time_seconds"] = end_time - start_time
        
        # Save CSV
        csv_path = self.csv_dir / f"{sample_name}_abundance.csv"
        df.to_csv(csv_path, index=False)
        results["csv_path"] = csv_path
        
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
    
    @classmethod
    def from_environment(cls) -> 'MicrobiomePipelineIntegrator':
        """
        Create integrator from environment configuration.
        
        TDD GREEN Phase: Environment-based configuration loading.
        """
        # Load Kraken2 configuration from environment
        kraken2_db_path = os.environ.get('KRAKEN2_DB_PATH')
        use_kraken2 = os.environ.get('USE_KRAKEN2', 'false').lower() == 'true'
        
        # Parse numeric environment variables with defaults
        try:
            kraken2_threads = int(os.environ.get('KRAKEN2_THREADS', '4'))
        except ValueError:
            kraken2_threads = 4
            
        try:
            kraken2_confidence = float(os.environ.get('KRAKEN2_CONFIDENCE', '0.1'))
        except ValueError:
            kraken2_confidence = 0.1
        
        return cls(
            use_kraken2=use_kraken2,
            kraken2_db_path=kraken2_db_path,
            kraken2_threads=kraken2_threads,
            kraken2_confidence=kraken2_confidence
        )
    
    def _process_with_kraken2(self, fastq_files: List[str], barcode_column: str) -> pd.DataFrame:
        """
        Process FASTQ files using Kraken2 with fallback management.
        
        TDD GREEN Phase: Kraken2 processing integration.
        """
        if not KRAKEN2_AVAILABLE:
            raise RuntimeError("Kraken2 not available")
        
        # Create fallback manager
        fallback_manager = Kraken2FallbackManager(
            kraken2_db_path=self.kraken2_db_path or "/test/kraken2/db",  # Default for testing
            fallback_processor_class=FASTQtoCSVConverter()
        )
        
        # Process with Kraken2 or fallback
        result_df = fallback_manager.process_fastq(fastq_files, barcode_column)
        
        return result_df
    
    def _validate_csv_format_compatibility(self, df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame matches expected CSV format.
        
        TDD GREEN Phase: CSV format validation for compatibility.
        """
        # Check required columns exist
        required_columns = ['species', 'phylum', 'genus']
        barcode_columns = [col for col in df.columns if col.startswith('barcode')]
        
        if len(barcode_columns) < 1:
            return False
        
        for col in required_columns:
            if col not in df.columns:
                return False
        
        return True
    
    def _should_use_kraken2(self) -> bool:
        """Determine if Kraken2 should be used for classification"""
        if not KRAKEN2_AVAILABLE:
            print("Kraken2 not available - falling back to BioPython")
            return False
        
        # Check if Kraken2 is enabled via environment
        kraken2_enabled = os.getenv('ENABLE_KRAKEN2_CLASSIFICATION', 'false').lower() == 'true'
        if not kraken2_enabled:
            print("Kraken2 disabled via ENABLE_KRAKEN2_CLASSIFICATION - using BioPython")
            return False
        
        # Check if database exists
        db_path = os.getenv('KRAKEN2_DB_PATH')
        if not db_path or not Path(db_path).exists():
            print(f"Kraken2 database not found at {db_path} - falling back to BioPython")
            return False
        
        return True
    
    def _classify_with_kraken2(self, 
                              fastq_files: List[str], 
                              sample_name: str, 
                              barcode_column: str) -> Tuple[pd.DataFrame, Dict]:
        """Perform Kraken2 classification"""
        try:
            # Create Kraken2 classifier
            classifier = Kraken2Classifier()
            
            # Run classification
            df, stats = classifier.classify_fastq(
                fastq_files=fastq_files,
                sample_name=barcode_column.replace("barcode", ""),
                output_dir=str(self.csv_dir)
            )
            
            # Check if fallback is needed
            fallback_manager = Kraken2FallbackManager()
            if fallback_manager.should_fallback(stats):
                print("Kraken2 classification quality low - falling back to BioPython")
                df = self._classify_with_biopython(fastq_files, sample_name, barcode_column)
                stats['fallback_used'] = True
            else:
                stats['fallback_used'] = False
            
            return df, stats
            
        except Exception as e:
            print(f"Kraken2 classification failed: {e}")
            print("Falling back to BioPython classification")
            df = self._classify_with_biopython(fastq_files, sample_name, barcode_column)
            return df, {"error": str(e), "fallback_used": True}
    
    def _classify_with_biopython(self, 
                                fastq_files: List[str], 
                                sample_name: str, 
                                barcode_column: str) -> pd.DataFrame:
        """Fallback BioPython classification (existing method)"""
        converter = FASTQtoCSVConverter()
        df = converter.process_fastq_files(
            fastq_files,
            sample_names=[barcode_column.replace("barcode", "")],
            barcode_column=barcode_column
        )
        return df