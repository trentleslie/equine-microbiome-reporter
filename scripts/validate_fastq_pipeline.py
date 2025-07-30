#!/usr/bin/env python3
"""
FASTQ Pipeline Validation Tool

Validates that FASTQ processing generates CSV files compatible with the PDF generation pipeline.
Tests the complete FASTQ → CSV → PDF workflow and reports any compatibility issues.

Usage:
    python scripts/validate_fastq_pipeline.py [fastq_file] [--barcode BARCODE] [--output OUTPUT_DIR]
    
    fastq_file: Path to FASTQ file to test (default: uses sample data)
    --barcode: Barcode column name to create (default: barcode59)
    --output: Output directory for test files (default: pipeline_validation)
"""

import sys
import os
import argparse
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fastq_converter import FASTQtoCSVConverter
from src.csv_processor import CSVProcessor
from src.report_generator import ReportGenerator
from src.data_models import PatientInfo
import pandas as pd


class FASTQPipelineValidator:
    """Validates FASTQ processing pipeline compatibility"""
    
    def __init__(self, output_dir: str = "pipeline_validation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def validate_csv_format(self, csv_path: str, barcode_column: str) -> Dict:
        """Validate CSV format against specification"""
        print(f"\n📋 Validating CSV format: {csv_path}")
        
        result = {
            "test": "CSV Format Validation",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        try:
            df = pd.read_csv(csv_path)
            
            # Check required columns
            required_columns = ["species", barcode_column, "phylum", "genus", "family", "class", "order"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                result["status"] = "failed"
                result["errors"].append(f"Missing required columns: {missing_columns}")
            else:
                result["details"]["required_columns"] = "✅ All present"
            
            # Check column order
            expected_order = ["species", barcode_column, "phylum", "genus", "family", "class", "order"]
            actual_order = list(df.columns)
            if actual_order == expected_order:
                result["details"]["column_order"] = "✅ Correct"
            else:
                result["details"]["column_order"] = f"❌ Expected {expected_order}, got {actual_order}"
            
            # Check data types
            if barcode_column in df.columns:
                if df[barcode_column].dtype in ["int64", "int32"]:
                    result["details"]["barcode_dtype"] = "✅ Integer"
                else:
                    result["details"]["barcode_dtype"] = f"❌ Expected integer, got {df[barcode_column].dtype}"
            
            # Check phylum names
            if "phylum" in df.columns:
                expected_phyla = ["Actinomycetota", "Bacillota", "Bacteroidota", "Pseudomonadota", "Fibrobacterota"]
                phyla_in_data = set(df["phylum"].unique())
                unexpected_phyla = phyla_in_data - set(expected_phyla)
                
                if unexpected_phyla:
                    result["details"]["phylum_names"] = f"⚠️  Unexpected phyla: {unexpected_phyla}"
                else:
                    result["details"]["phylum_names"] = "✅ All recognized"
            
            # Check data integrity
            if barcode_column in df.columns:
                total_count = df[barcode_column].sum()
                species_count = len(df[df[barcode_column] > 0])
                
                result["details"]["total_abundance"] = f"{total_count:,}"
                result["details"]["species_with_counts"] = f"{species_count}"
                
                if total_count > 0 and species_count >= 5:
                    result["details"]["data_integrity"] = "✅ Sufficient data"
                else:
                    result["details"]["data_integrity"] = f"⚠️  Low data: {species_count} species, {total_count} total"
            
            if result["status"] == "unknown":
                result["status"] = "passed" if not result["errors"] else "failed"
                
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"CSV validation error: {e}")
        
        return result
    
    def validate_csv_processing(self, csv_path: str, barcode_column: str) -> Dict:
        """Validate CSV can be processed by CSVProcessor"""
        print(f"\n🔄 Validating CSV processing: {csv_path}")
        
        result = {
            "test": "CSV Processing Validation",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        try:
            processor = CSVProcessor(csv_path, barcode_column)
            microbiome_data = processor.process()
            
            result["details"]["species_count"] = microbiome_data.total_species_count
            result["details"]["dysbiosis_index"] = f"{microbiome_data.dysbiosis_index:.1f}"
            result["details"]["dysbiosis_category"] = microbiome_data.dysbiosis_category
            result["details"]["phylum_count"] = len(microbiome_data.phylum_distribution)
            
            # Check if phylum distribution was calculated
            if microbiome_data.phylum_distribution:
                main_phyla = [p for p, pct in microbiome_data.phylum_distribution.items() if pct > 1.0]
                result["details"]["main_phyla"] = f"{len(main_phyla)} phyla >1%"
                
                if "Unknown phylum" in microbiome_data.phylum_distribution:
                    result["details"]["unknown_phylum"] = f"⚠️  {microbiome_data.phylum_distribution['Unknown phylum']:.1f}%"
                else:
                    result["details"]["phylum_recognition"] = "✅ All phyla recognized"
            
            # Validate clinical interpretation
            if microbiome_data.clinical_interpretation:
                result["details"]["clinical_interpretation"] = "✅ Generated"
            else:
                result["errors"].append("No clinical interpretation generated")
            
            # Validate recommendations
            if microbiome_data.recommendations:
                result["details"]["recommendations"] = f"✅ {len(microbiome_data.recommendations)} items"
            else:
                result["errors"].append("No recommendations generated")
            
            result["status"] = "passed" if not result["errors"] else "warning"
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"CSV processing error: {e}")
        
        return result
    
    def validate_pdf_generation(self, csv_path: str, barcode_column: str) -> Dict:
        """Validate PDF can be generated from CSV"""
        print(f"\n📄 Validating PDF generation: {csv_path}")
        
        result = {
            "test": "PDF Generation Validation",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        try:
            patient_info = PatientInfo(
                name="Validation Test Horse",
                sample_number="VAL-001",
                age="Test Age",
                performed_by="Validation Lab",
                requested_by="Dr. Validator"
            )
            
            generator = ReportGenerator(language="en")
            pdf_path = self.output_dir / "validation_test_report.pdf"
            
            success = generator.generate_report(
                csv_path=csv_path,
                patient_info=patient_info,
                output_path=str(pdf_path)
            )
            
            if success and pdf_path.exists():
                file_size = pdf_path.stat().st_size
                result["details"]["pdf_generated"] = "✅ Success"
                result["details"]["file_size"] = f"{file_size:,} bytes"
                result["details"]["pdf_path"] = str(pdf_path)
                
                if file_size > 50000:  # Reasonable minimum size for a real report
                    result["details"]["file_size_check"] = "✅ Adequate size"
                else:
                    result["details"]["file_size_check"] = f"⚠️  Small file ({file_size:,} bytes)"
                
                result["status"] = "passed"
            else:
                result["status"] = "failed"
                result["errors"].append("PDF generation failed")
                
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"PDF generation error: {e}")
        
        return result
    
    def validate_fastq_processing(self, fastq_path: str, barcode_column: str) -> Dict:
        """Validate FASTQ file processing"""
        print(f"\n🧬 Validating FASTQ processing: {fastq_path}")
        
        result = {
            "test": "FASTQ Processing Validation",
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        try:
            if not os.path.exists(fastq_path):
                result["status"] = "failed"
                result["errors"].append(f"FASTQ file not found: {fastq_path}")
                return result
            
            converter = FASTQtoCSVConverter()
            
            # Test with different QC parameters
            qc_tests = [
                {"min_quality": 15, "min_length": 100, "name": "lenient"},
                {"min_quality": 20, "min_length": 200, "name": "standard"},
                {"min_quality": 25, "min_length": 300, "name": "strict"}
            ]
            
            best_result = None
            best_count = 0
            
            for qc_params in qc_tests:
                try:
                    df = converter.process_fastq_files(
                        [fastq_path],
                        sample_names=["test"],
                        barcode_column=barcode_column,
                        min_quality=qc_params["min_quality"],
                        min_length=qc_params["min_length"]
                    )
                    
                    species_count = len(df[df[barcode_column] > 0])
                    total_count = df[barcode_column].sum()
                    
                    result["details"][f"qc_{qc_params['name']}"] = f"{species_count} species, {total_count} reads"
                    
                    if species_count > best_count:
                        best_result = df
                        best_count = species_count
                        
                except Exception as e:
                    result["details"][f"qc_{qc_params['name']}"] = f"Failed: {e}"
            
            if best_result is not None and best_count > 0:
                result["details"]["best_qc_result"] = f"{best_count} species processed"
                result["status"] = "passed"
                
                # Save the best result for further testing
                csv_path = self.output_dir / "fastq_converted.csv"
                converter.save_to_csv(best_result, str(csv_path))
                result["details"]["csv_output"] = str(csv_path)
                
            else:
                result["status"] = "warning"
                result["details"]["status"] = "No sequences passed any QC parameters - using mock data"
                
                # Still create CSV with mock data for compatibility testing
                df = converter.process_fastq_files(
                    [fastq_path],
                    sample_names=["test"],
                    barcode_column=barcode_column
                )
                csv_path = self.output_dir / "fastq_converted_mock.csv"
                converter.save_to_csv(df, str(csv_path))
                result["details"]["csv_output"] = str(csv_path)
                
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"FASTQ processing error: {e}")
        
        return result
    
    def run_complete_validation(self, fastq_path: str, barcode_column: str = "barcode59") -> List[Dict]:
        """Run complete validation pipeline"""
        print(f"🚀 Starting FASTQ Pipeline Validation")
        print(f"FASTQ file: {fastq_path}")
        print(f"Barcode column: {barcode_column}")
        print(f"Output directory: {self.output_dir}")
        
        validation_results = []
        
        # Step 1: FASTQ Processing
        fastq_result = self.validate_fastq_processing(fastq_path, barcode_column)
        validation_results.append(fastq_result)
        
        # If FASTQ processing succeeded, get the CSV path
        csv_path = None
        if fastq_result["status"] in ["passed", "warning"] and "csv_output" in fastq_result["details"]:
            csv_path = fastq_result["details"]["csv_output"]
        
        if csv_path and os.path.exists(csv_path):
            # Step 2: CSV Format Validation
            format_result = self.validate_csv_format(csv_path, barcode_column)
            validation_results.append(format_result)
            
            # Step 3: CSV Processing Validation
            processing_result = self.validate_csv_processing(csv_path, barcode_column)
            validation_results.append(processing_result)
            
            # Step 4: PDF Generation Validation
            pdf_result = self.validate_pdf_generation(csv_path, barcode_column)
            validation_results.append(pdf_result)
        else:
            validation_results.append({
                "test": "Pipeline Continuation",
                "status": "failed",
                "details": {},
                "errors": ["Could not proceed - FASTQ processing failed to produce CSV"]
            })
        
        return validation_results
    
    def print_results(self, results: List[Dict]):
        """Print validation results in a readable format"""
        print(f"\n{'='*60}")
        print(f"🔍 FASTQ PIPELINE VALIDATION RESULTS")
        print(f"{'='*60}")
        
        total_tests = len(results)
        passed_tests = len([r for r in results if r["status"] == "passed"])
        warning_tests = len([r for r in results if r["status"] == "warning"])
        failed_tests = len([r for r in results if r["status"] == "failed"])
        
        print(f"\nSUMMARY: {passed_tests} passed, {warning_tests} warnings, {failed_tests} failed ({total_tests} total)")
        
        for result in results:
            status_emoji = {
                "passed": "✅",
                "warning": "⚠️ ",
                "failed": "❌",
                "unknown": "❓"
            }.get(result["status"], "❓")
            
            print(f"\n{status_emoji} {result['test'].upper()}")
            
            # Print details
            for key, value in result["details"].items():
                print(f"  {key}: {value}")
            
            # Print errors
            for error in result["errors"]:
                print(f"  🚨 ERROR: {error}")
        
        # Overall assessment
        print(f"\n{'='*60}")
        if failed_tests == 0:
            if warning_tests == 0:
                print("🎉 ALL VALIDATIONS PASSED! The FASTQ pipeline is fully compatible.")
            else:
                print("✅ VALIDATION SUCCESSFUL with warnings. The pipeline works but may need attention.")
        else:
            print("❌ VALIDATION FAILED. The FASTQ pipeline has compatibility issues that need fixing.")
        
        print(f"{'='*60}")
    
    def save_results(self, results: List[Dict], filename: str = "validation_results.json"):
        """Save results to JSON file"""
        import json
        
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate FASTQ processing pipeline compatibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "fastq_file",
        nargs="?",
        default="data/barcode04/FBC55250_pass_barcode04_168ca027_4fdcf48d_0.fastq.gz",
        help="Path to FASTQ file to test (default: sample data)"
    )
    
    parser.add_argument(
        "--barcode", "-b",
        default="barcode59",
        help="Barcode column name to create (default: barcode59)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="pipeline_validation",
        help="Output directory for test files (default: pipeline_validation)"
    )
    
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Check if FASTQ file exists
    if not os.path.exists(args.fastq_file):
        print(f"❌ FASTQ file not found: {args.fastq_file}")
        print("Available sample files:")
        sample_dirs = ["data/barcode04", "data/barcode05", "data/barcode06"]
        for sample_dir in sample_dirs:
            if os.path.exists(sample_dir):
                files = [f for f in os.listdir(sample_dir) if f.endswith('.fastq.gz')]
                if files:
                    print(f"  {sample_dir}: {len(files)} files")
                    print(f"    Example: {sample_dir}/{files[0]}")
        return 1
    
    # Run validation
    validator = FASTQPipelineValidator(args.output)
    results = validator.run_complete_validation(args.fastq_file, args.barcode)
    
    # Print results
    validator.print_results(results)
    
    # Save results if requested
    if args.save_results:
        validator.save_results(results)
    
    # Return exit code based on results
    failed_tests = len([r for r in results if r["status"] == "failed"])
    return 1 if failed_tests > 0 else 0


if __name__ == "__main__":
    sys.exit(main())