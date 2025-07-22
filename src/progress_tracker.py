"""
Progress tracking utilities for batch processing.

This module provides progress tracking functionality for use in Jupyter notebooks
and command-line interfaces.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd


class ProgressTracker:
    """Base class for progress tracking."""
    
    def __init__(self):
        """Initialize progress tracker."""
        self.total = 0
        self.current = 0
        self.start_time = None
        self.messages = []
        
    def start(self, total: int):
        """Start tracking progress."""
        self.total = total
        self.current = 0
        self.start_time = datetime.now()
        self.messages = []
        
    def update(self, increment: int = 1, message: Optional[str] = None):
        """Update progress."""
        self.current += increment
        if message:
            self.messages.append({
                'timestamp': datetime.now(),
                'progress': self.current,
                'message': message
            })
            
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
        
    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
        
    def get_estimated_time_remaining(self) -> float:
        """Get estimated time remaining in seconds."""
        if self.current == 0 or not self.start_time:
            return 0.0
            
        elapsed = self.get_elapsed_time()
        rate = self.current / elapsed
        remaining = self.total - self.current
        
        return remaining / rate if rate > 0 else 0.0


class NotebookProgressTracker(ProgressTracker):
    """Progress tracker for Jupyter notebooks with widget support."""
    
    def __init__(self):
        """Initialize notebook progress tracker."""
        super().__init__()
        self.progress_bar = None
        self.status_output = None
        self.widgets_available = False
        
        # Try to import widgets
        try:
            import ipywidgets as widgets
            from IPython.display import display, HTML, clear_output
            self.widgets = widgets
            self.display = display
            self.HTML = HTML
            self.clear_output = clear_output
            self.widgets_available = True
        except ImportError:
            pass
            
    def create_progress_display(self, total: int, description: str = "Progress"):
        """Create interactive progress display for notebooks.
        
        Args:
            total: Total number of items to process
            description: Description for progress bar
            
        Returns:
            Update function to call with progress updates
        """
        if not self.widgets_available:
            print(f"Processing {total} items...")
            return lambda current, total: print(f"{current}/{total} completed")
            
        self.start(total)
        
        # Create widgets
        self.progress_bar = self.widgets.IntProgress(
            value=0,
            min=0,
            max=total,
            description=description,
            bar_style='info',
            style={'bar_color': '#1E3A8A'},
            orientation='horizontal'
        )
        
        progress_label = self.widgets.Label(value=f"0/{total} files processed")
        time_label = self.widgets.Label(value="Elapsed: 0s | Remaining: calculating...")
        
        self.status_output = self.widgets.Output()
        
        # Display widgets
        self.display(self.widgets.VBox([
            self.progress_bar,
            progress_label,
            time_label,
            self.status_output
        ]))
        
        def update_progress(current: int, total: int, message: Optional[str] = None):
            """Update progress display."""
            self.current = current
            self.progress_bar.value = current
            progress_label.value = f"{current}/{total} files processed"
            
            elapsed = self.get_elapsed_time()
            remaining = self.get_estimated_time_remaining()
            
            time_label.value = f"Elapsed: {elapsed:.1f}s | Remaining: {remaining:.1f}s"
            
            if message:
                self.update_status(message)
                
        return update_progress
        
    def update_status(self, message: str, message_type: str = "info"):
        """Update status message in notebook.
        
        Args:
            message: Status message to display
            message_type: Type of message (info, success, error, warning)
        """
        if not self.widgets_available or not self.status_output:
            print(f"[{message_type.upper()}] {message}")
            return
            
        with self.status_output:
            self.clear_output(wait=True)
            color = {
                "info": "#1E3A8A",
                "success": "#10B981",
                "error": "#EF4444",
                "warning": "#F59E0B"
            }.get(message_type, "#6B7280")
            
            self.display(self.HTML(f'<p style="color: {color};">{message}</p>'))


class ConsoleProgressTracker(ProgressTracker):
    """Progress tracker for console/terminal output."""
    
    def __init__(self, use_tqdm: bool = True):
        """Initialize console progress tracker.
        
        Args:
            use_tqdm: Whether to use tqdm for progress bars
        """
        super().__init__()
        self.use_tqdm = use_tqdm
        self.pbar = None
        
        if use_tqdm:
            try:
                from tqdm import tqdm
                self.tqdm = tqdm
            except ImportError:
                self.use_tqdm = False
                
    def create_progress_bar(self, total: int, description: str = "Processing"):
        """Create console progress bar.
        
        Args:
            total: Total number of items
            description: Description for progress bar
            
        Returns:
            Update function for progress
        """
        self.start(total)
        
        if self.use_tqdm:
            self.pbar = self.tqdm(total=total, desc=description)
            
            def update_progress(current: int, total: int, message: Optional[str] = None):
                increment = current - self.current
                self.current = current
                self.pbar.update(increment)
                if message:
                    self.pbar.set_postfix_str(message)
                    
            return update_progress
        else:
            def update_progress(current: int, total: int, message: Optional[str] = None):
                self.current = current
                percentage = self.get_progress_percentage()
                bar_length = 50
                filled = int(bar_length * current / total)
                bar = '█' * filled + '-' * (bar_length - filled)
                
                msg = f"\r{description}: |{bar}| {percentage:.1f}% ({current}/{total})"
                if message:
                    msg += f" - {message}"
                    
                print(msg, end='', flush=True)
                if current == total:
                    print()  # New line when complete
                    
            return update_progress
            
    def close(self):
        """Close progress bar."""
        if self.pbar:
            self.pbar.close()


def generate_quality_report(results: List[Dict], output_path: Optional[str] = None) -> pd.DataFrame:
    """Generate a quality control report from batch processing results.
    
    Args:
        results: List of processing results
        output_path: Optional path to save report CSV
        
    Returns:
        DataFrame with quality report
    """
    if not results:
        return pd.DataFrame()
        
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Calculate statistics
    stats = {
        'total_files': len(df),
        'successful': df['success'].sum() if 'success' in df else 0,
        'failed': (~df['success']).sum() if 'success' in df else 0,
        'success_rate': df['success'].mean() * 100 if 'success' in df else 0,
        'validation_passed': df['validation_passed'].sum() if 'validation_passed' in df else 0,
        'validation_failed': (~df['validation_passed']).sum() if 'validation_passed' in df else 0,
    }
    
    # Processing time statistics
    if 'processing_time' in df:
        stats.update({
            'total_time': df['processing_time'].sum(),
            'mean_time': df['processing_time'].mean(),
            'min_time': df['processing_time'].min(),
            'max_time': df['processing_time'].max(),
        })
    
    # Create summary DataFrame
    summary_df = pd.DataFrame([stats])
    
    # Save if path provided
    if output_path:
        # Save detailed results
        df.to_csv(output_path, index=False)
        
        # Save summary
        summary_path = Path(output_path).parent / f"summary_{Path(output_path).name}"
        summary_df.to_csv(summary_path, index=False)
    
    return df


def create_manifest_template(output_path: str, sample_files: Optional[List[str]] = None):
    """Create a template manifest CSV file.
    
    Args:
        output_path: Path to save manifest template
        sample_files: Optional list of sample filenames to include
    """
    if sample_files is None:
        sample_files = ['sample_1.csv', 'sample_2.csv', 'sample_3.csv']
        
    manifest_data = []
    for i, filename in enumerate(sample_files, 1):
        manifest_data.append({
            'csv_file': filename,
            'patient_name': f'Patient {i}',
            'species': 'Horse',
            'age': 'Unknown',
            'sample_number': f'{i:03d}',
            'performed_by': 'Laboratory Staff',
            'requested_by': 'Veterinarian'
        })
    
    df = pd.DataFrame(manifest_data)
    df.to_csv(output_path, index=False)
    
    return df