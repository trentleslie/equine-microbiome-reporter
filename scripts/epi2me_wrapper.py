#!/usr/bin/env python3
"""
Epi2Me Wrapper for Automatic Clinical Filtering

Monitors Epi2Me output directories and automatically triggers clinical filtering
when Kraken2 analysis completes. Designed for seamless integration with the
existing wf-metagenomics pipeline.

Usage:
    python epi2me_wrapper.py --watch /path/to/epi2me/instances [--auto-process]
"""

import os
import sys
import time
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from clinical_filter import ClinicalFilter
from curation_interface import CurationInterface
from cross_platform_utils import CrossPlatformPathHandler


class Epi2MeMonitor(FileSystemEventHandler):
    """Monitor Epi2Me output directories for completion."""
    
    def __init__(self, watch_dir: Path, auto_process: bool = False,
                 databases: List[str] = None, output_dir: Path = None):
        """
        Initialize Epi2Me monitor.
        
        Args:
            watch_dir: Directory to monitor (Epi2Me instances folder)
            auto_process: Automatically process on completion
            databases: List of databases to process
            output_dir: Output directory for results
        """
        self.watch_dir = Path(watch_dir)
        self.auto_process = auto_process
        self.databases = databases or ["PlusPFP-16"]
        self.output_dir = output_dir or Path("/mnt/c/Users/hippovet/Desktop/filtered_results")
        self.processed_runs = self._load_processed_runs()
        self.filter = ClinicalFilter()
        self.curator = CurationInterface(output_dir=self.output_dir / "curation")
        
    def _load_processed_runs(self) -> set:
        """Load list of already processed runs."""
        cache_file = Path.home() / ".epi2me_processed.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_processed_runs(self) -> None:
        """Save list of processed runs."""
        cache_file = Path.home() / ".epi2me_processed.json"
        with open(cache_file, 'w') as f:
            json.dump(list(self.processed_runs), f)
    
    def _get_run_id(self, path: Path) -> str:
        """Generate unique ID for a run."""
        return hashlib.md5(str(path).encode()).hexdigest()[:8]
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            # Check if this is a completion marker
            if "wf-metagenomics-report.html" in event.src_path:
                run_dir = Path(event.src_path).parent
                self._handle_completed_run(run_dir)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            # Check for Kraken2 report files
            if ".kreport" in event.src_path or ".kreport2" in event.src_path:
                print(f"Kraken2 report detected: {event.src_path}")
    
    def _handle_completed_run(self, run_dir: Path) -> None:
        """
        Handle a completed Epi2Me run.
        
        Args:
            run_dir: Directory containing completed run
        """
        run_id = self._get_run_id(run_dir)
        
        if run_id in self.processed_runs:
            print(f"Run already processed: {run_dir.name}")
            return
        
        print(f"\n{'='*60}")
        print(f"New Epi2Me run completed: {run_dir.name}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        if self.auto_process:
            self.process_run(run_dir)
        else:
            print(f"Run ready for processing: {run_dir}")
            print("To process, run:")
            print(f"  python epi2me_wrapper.py --process {run_dir}")
    
    def process_run(self, run_dir: Path) -> Dict:
        """
        Process an Epi2Me run with clinical filtering.
        
        Args:
            run_dir: Directory containing Epi2Me output
            
        Returns:
            Processing results dictionary
        """
        results = {
            'run_dir': str(run_dir),
            'timestamp': datetime.now().isoformat(),
            'databases_processed': [],
            'files_created': [],
            'errors': []
        }
        
        # Find Kraken2 reports
        kraken_reports = self._find_kraken_reports(run_dir)
        
        if not kraken_reports:
            error_msg = f"No Kraken2 reports found in {run_dir}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
            return results
        
        print(f"Found {len(kraken_reports)} Kraken2 reports")
        
        # Process each database
        for database in self.databases:
            print(f"\n📊 Processing {database} database...")
            
            try:
                # Process with clinical filter
                processed_data = self._process_database(kraken_reports, database)
                
                # Generate Excel for review
                excel_path = self._export_for_review(processed_data, database, run_dir.name)
                results['files_created'].append(str(excel_path))
                
                # Generate summary report
                summary_path = self._generate_summary(processed_data, database, run_dir.name)
                results['files_created'].append(str(summary_path))
                
                results['databases_processed'].append(database)
                print(f"✅ {database} processing complete")
                
            except Exception as e:
                error_msg = f"Failed to process {database}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Mark run as processed
        run_id = self._get_run_id(run_dir)
        self.processed_runs.add(run_id)
        self._save_processed_runs()
        
        # Send notification if configured
        if results['databases_processed']:
            self._send_notification(results)
        
        return results
    
    def _find_kraken_reports(self, run_dir: Path) -> Dict[str, Path]:
        """Find Kraken2 report files in run directory."""
        reports = {}
        
        # Check standard locations
        kraken_dir = run_dir / "kraken2-classified"
        if kraken_dir.exists():
            for report_file in kraken_dir.glob("*.kreport*"):
                barcode = report_file.stem.split('.')[0]
                reports[barcode] = report_file
        
        # Also check output directory
        output_dir = run_dir / "output"
        if output_dir.exists():
            for report_file in output_dir.glob("**/*.kreport*"):
                barcode = report_file.stem.split('.')[0]
                if barcode not in reports:
                    reports[barcode] = report_file
        
        return reports
    
    def _process_database(self, kraken_reports: Dict[str, Path], 
                         database: str) -> pd.DataFrame:
        """Process Kraken reports with clinical filtering."""
        import pandas as pd
        
        all_results = []
        
        for barcode, report_path in kraken_reports.items():
            # Parse Kraken2 report
            df = self._parse_kraken_report(report_path)
            
            # Apply clinical filtering
            df_filtered = self.filter.process_results(df, database, auto_exclude=True)
            
            # Add barcode column
            df_filtered['barcode'] = barcode
            all_results.append(df_filtered)
        
        # Combine all barcodes
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def _parse_kraken_report(self, report_path: Path) -> pd.DataFrame:
        """Parse a Kraken2 report file."""
        import pandas as pd
        
        data = []
        with open(report_path, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 6:
                        percentage = float(parts[0])
                        reads_covered = int(parts[1])
                        reads_assigned = int(parts[2])
                        rank = parts[3]
                        taxid = int(parts[4])
                        name = parts[5].strip()
                        
                        # Only include species-level classifications
                        if rank == 'S':
                            data.append({
                                'species': name,
                                'percentage': percentage,
                                'abundance_reads': reads_assigned,
                                'taxid': taxid
                            })
        
        return pd.DataFrame(data)
    
    def _export_for_review(self, df: pd.DataFrame, database: str, 
                           run_name: str) -> Path:
        """Export processed data for Excel review."""
        if df.empty:
            return Path()
        
        # Create descriptive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{database}_{run_name}_{timestamp}.xlsx"
        excel_path = self.output_dir / "curation" / filename
        
        # Use curator to export
        excel_path = self.curator.export_for_excel_review(df, f"{database}_{run_name}")
        
        print(f"  📝 Excel review file: {excel_path.name}")
        return excel_path
    
    def _generate_summary(self, df: pd.DataFrame, database: str, 
                         run_name: str) -> Path:
        """Generate summary report of processing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = self.output_dir / f"summary_{database}_{run_name}_{timestamp}.txt"
        
        with open(summary_path, 'w') as f:
            f.write(f"Clinical Filtering Summary\n")
            f.write(f"{'='*40}\n")
            f.write(f"Database: {database}\n")
            f.write(f"Run: {run_name}\n")
            f.write(f"Processed: {timestamp}\n\n")
            
            if not df.empty:
                # Count by relevance
                if 'clinical_relevance' in df.columns:
                    relevance_counts = df['clinical_relevance'].value_counts()
                    f.write("Species by Clinical Relevance:\n")
                    for relevance, count in relevance_counts.items():
                        f.write(f"  {relevance}: {count}\n")
                
                # Count by barcode
                if 'barcode' in df.columns:
                    barcode_counts = df['barcode'].value_counts()
                    f.write(f"\nTotal Barcodes: {len(barcode_counts)}\n")
                    f.write("Species per Barcode:\n")
                    for barcode, count in barcode_counts.items():
                        f.write(f"  {barcode}: {count}\n")
                
                f.write(f"\nTotal Species: {len(df)}\n")
            else:
                f.write("No species found after filtering\n")
        
        print(f"  📊 Summary report: {summary_path.name}")
        return summary_path
    
    def _send_notification(self, results: Dict) -> None:
        """Send notification of completed processing."""
        # Create notification file on Desktop
        desktop_path = Path("/mnt/c/Users/hippovet/Desktop")
        if desktop_path.exists():
            notification_file = desktop_path / "PROCESSING_COMPLETE.txt"
            with open(notification_file, 'w') as f:
                f.write("Clinical Filtering Complete!\n")
                f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Run: {Path(results['run_dir']).name}\n")
                f.write(f"Databases: {', '.join(results['databases_processed'])}\n")
                f.write(f"\nFiles created:\n")
                for file_path in results['files_created']:
                    f.write(f"  - {Path(file_path).name}\n")
                f.write(f"\nCheck folder: {self.output_dir}\n")


class Epi2MeWrapper:
    """Main wrapper class for Epi2Me integration."""
    
    def __init__(self):
        """Initialize wrapper with configuration."""
        self.config = self._load_configuration()
        self.path_handler = CrossPlatformPathHandler()
        
    def _load_configuration(self) -> Dict:
        """Load configuration from file or defaults."""
        config_path = Path.home() / ".epi2me_wrapper_config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "epi2me_instances": "/mnt/c/Users/hippovet/epi2melabs/instances",
            "output_dir": "/mnt/c/Users/hippovet/Desktop/filtered_results",
            "databases": ["PlusPFP-16", "EuPathDB", "Viral"],
            "auto_process": False,
            "check_interval": 60  # seconds
        }
    
    def watch(self, watch_dir: Path = None, auto_process: bool = False) -> None:
        """
        Watch Epi2Me directory for new runs.
        
        Args:
            watch_dir: Directory to watch
            auto_process: Automatically process new runs
        """
        watch_dir = watch_dir or Path(self.config["epi2me_instances"])
        
        if not watch_dir.exists():
            print(f"Error: Watch directory does not exist: {watch_dir}")
            return
        
        print(f"Watching directory: {watch_dir}")
        print(f"Auto-process: {'Enabled' if auto_process else 'Disabled'}")
        print(f"Databases: {', '.join(self.config['databases'])}")
        print("\nPress Ctrl+C to stop monitoring\n")
        
        # Create event handler and observer
        event_handler = Epi2MeMonitor(
            watch_dir=watch_dir,
            auto_process=auto_process,
            databases=self.config['databases'],
            output_dir=Path(self.config['output_dir'])
        )
        
        observer = Observer()
        observer.schedule(event_handler, str(watch_dir), recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(self.config['check_interval'])
                # Periodic check for completed runs
                self._check_for_completed_runs(watch_dir, event_handler)
        except KeyboardInterrupt:
            observer.stop()
            print("\nMonitoring stopped")
        
        observer.join()
    
    def _check_for_completed_runs(self, watch_dir: Path, handler: Epi2MeMonitor) -> None:
        """Periodically check for completed runs."""
        for instance_dir in watch_dir.glob("wf-metagenomics_*"):
            output_dir = instance_dir / "output"
            report_file = output_dir / "wf-metagenomics-report.html"
            
            if report_file.exists():
                run_id = handler._get_run_id(output_dir)
                if run_id not in handler.processed_runs:
                    handler._handle_completed_run(output_dir)
    
    def process_single(self, run_dir: Path, databases: List[str] = None) -> None:
        """
        Process a single Epi2Me run.
        
        Args:
            run_dir: Directory containing Epi2Me output
            databases: List of databases to process
        """
        databases = databases or self.config['databases']
        
        print(f"Processing run: {run_dir}")
        print(f"Databases: {', '.join(databases)}")
        
        monitor = Epi2MeMonitor(
            watch_dir=run_dir.parent,
            auto_process=True,
            databases=databases,
            output_dir=Path(self.config['output_dir'])
        )
        
        results = monitor.process_run(run_dir)
        
        if results['databases_processed']:
            print(f"\n✅ Processing complete!")
            print(f"Files created: {len(results['files_created'])}")
        else:
            print(f"\n❌ Processing failed")
            for error in results['errors']:
                print(f"  - {error}")
    
    def batch_process(self, instances_dir: Path = None) -> None:
        """
        Process all unprocessed runs in batch.
        
        Args:
            instances_dir: Epi2Me instances directory
        """
        instances_dir = instances_dir or Path(self.config['epi2me_instances'])
        
        monitor = Epi2MeMonitor(
            watch_dir=instances_dir,
            auto_process=True,
            databases=self.config['databases'],
            output_dir=Path(self.config['output_dir'])
        )
        
        # Find all runs
        runs = list(instances_dir.glob("wf-metagenomics_*/output"))
        unprocessed = [r for r in runs if monitor._get_run_id(r) not in monitor.processed_runs]
        
        print(f"Found {len(runs)} total runs")
        print(f"Unprocessed: {len(unprocessed)}")
        
        if not unprocessed:
            print("All runs already processed")
            return
        
        for i, run_dir in enumerate(unprocessed, 1):
            print(f"\n[{i}/{len(unprocessed)}] Processing {run_dir.parent.name}")
            monitor.process_run(run_dir)
        
        print(f"\n✅ Batch processing complete")
        print(f"Processed {len(unprocessed)} runs")


def main():
    """Main entry point for Epi2Me wrapper."""
    parser = argparse.ArgumentParser(
        description="Epi2Me wrapper for automatic clinical filtering"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Monitor Epi2Me directory')
    watch_parser.add_argument(
        '--dir',
        type=Path,
        help='Directory to watch (default: from config)'
    )
    watch_parser.add_argument(
        '--auto-process',
        action='store_true',
        help='Automatically process new runs'
    )
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a single run')
    process_parser.add_argument(
        'run_dir',
        type=Path,
        help='Epi2Me run directory'
    )
    process_parser.add_argument(
        '--databases',
        nargs='+',
        choices=['PlusPFP-16', 'EuPathDB', 'Viral'],
        help='Databases to process'
    )
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process all unprocessed runs')
    batch_parser.add_argument(
        '--dir',
        type=Path,
        help='Epi2Me instances directory'
    )
    
    args = parser.parse_args()
    
    wrapper = Epi2MeWrapper()
    
    if args.command == 'watch':
        wrapper.watch(watch_dir=args.dir, auto_process=args.auto_process)
    elif args.command == 'process':
        wrapper.process_single(args.run_dir, args.databases)
    elif args.command == 'batch':
        wrapper.batch_process(instances_dir=args.dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()