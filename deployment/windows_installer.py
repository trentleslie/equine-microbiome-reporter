#!/usr/bin/env python3
"""
Windows Deployment Installer for HippoVet+ Clinical Filtering System

This script automates the installation and configuration of the clinical
filtering system in a Windows/WSL environment.

Usage:
    python windows_installer.py [--wsl-version 1|2] [--conda-path PATH]
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
import urllib.request
import zipfile


class WindowsInstaller:
    """Automated installer for Windows/WSL environment."""
    
    def __init__(self, wsl_version: int = 1, conda_path: Optional[str] = None):
        """
        Initialize installer with WSL configuration.
        
        Args:
            wsl_version: WSL version (1 or 2)
            conda_path: Path to existing conda installation
        """
        self.wsl_version = wsl_version
        self.conda_path = conda_path
        self.install_dir = Path.home() / "equine-clinical-filter"
        self.is_windows = platform.system() == "Windows"
        self.is_wsl = self._detect_wsl()
        self.installation_log = []
        
    def _detect_wsl(self) -> bool:
        """Detect if running in WSL environment."""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log installation progress."""
        print(f"[{level}] {message}")
        self.installation_log.append(f"[{level}] {message}")
    
    def check_prerequisites(self) -> bool:
        """
        Check system prerequisites for installation.
        
        Returns:
            True if all prerequisites met
        """
        self._log("Checking system prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 9:
            self._log(f"Python 3.9+ required (found {python_version.major}.{python_version.minor})", "ERROR")
            return False
        
        # Check WSL if on Windows
        if self.is_windows and not self.is_wsl:
            self._log("This installer should be run from within WSL", "WARNING")
            
        # Check available disk space
        stat = os.statvfs('/' if self.is_wsl else '.')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        if free_gb < 5:
            self._log(f"Insufficient disk space: {free_gb:.1f}GB (need 5GB)", "ERROR")
            return False
        
        # Check for conda
        if not self.conda_path:
            conda_locations = [
                Path.home() / "miniconda3",
                Path.home() / "anaconda3",
                Path("/opt/miniconda3"),
                Path("/opt/anaconda3")
            ]
            
            for conda_dir in conda_locations:
                if conda_dir.exists():
                    self.conda_path = str(conda_dir)
                    self._log(f"Found conda at: {self.conda_path}")
                    break
        
        if not self.conda_path:
            self._log("Conda not found - will install Miniconda", "WARNING")
            
        return True
    
    def install_miniconda(self) -> bool:
        """
        Install Miniconda if not present.
        
        Returns:
            True if installation successful
        """
        if self.conda_path and Path(self.conda_path).exists():
            self._log("Conda already installed")
            return True
            
        self._log("Installing Miniconda...")
        
        # Download Miniconda installer
        if self.is_wsl or platform.system() == "Linux":
            installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            installer_path = Path.home() / "miniconda_installer.sh"
        else:
            installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
            installer_path = Path.home() / "miniconda_installer.exe"
        
        try:
            # Download installer
            self._log(f"Downloading from {installer_url}")
            urllib.request.urlretrieve(installer_url, installer_path)
            
            # Run installer
            if self.is_wsl or platform.system() == "Linux":
                subprocess.run(
                    ["bash", str(installer_path), "-b", "-p", str(Path.home() / "miniconda3")],
                    check=True
                )
                self.conda_path = str(Path.home() / "miniconda3")
            else:
                self._log("Please run the downloaded installer manually", "WARNING")
                return False
            
            # Clean up installer
            installer_path.unlink()
            
            self._log("Miniconda installed successfully")
            return True
            
        except Exception as e:
            self._log(f"Failed to install Miniconda: {e}", "ERROR")
            return False
    
    def create_conda_environment(self) -> bool:
        """
        Create conda environment with required packages.
        
        Returns:
            True if environment created successfully
        """
        self._log("Creating conda environment...")
        
        conda_exe = Path(self.conda_path) / "bin" / "conda"
        if not conda_exe.exists():
            conda_exe = Path(self.conda_path) / "Scripts" / "conda.exe"
        
        if not conda_exe.exists():
            self._log("Conda executable not found", "ERROR")
            return False
        
        try:
            # Create environment
            subprocess.run([
                str(conda_exe), "create", "-n", "equine-clinical",
                "python=3.9", "-y"
            ], check=True)
            
            # Install packages
            packages = [
                "pandas", "numpy", "matplotlib", "openpyxl",
                "jinja2", "pyyaml", "python-dotenv", "biopython",
                "seaborn", "scipy", "reportlab"
            ]
            
            # Install bioconda packages
            subprocess.run([
                str(conda_exe), "install", "-n", "equine-clinical",
                "-c", "bioconda", "kraken2", "bracken", "-y"
            ], check=True)
            
            # Install conda-forge packages
            subprocess.run([
                str(conda_exe), "install", "-n", "equine-clinical",
                "-c", "conda-forge"] + packages + ["-y"
            ], check=True)
            
            self._log("Conda environment created successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self._log(f"Failed to create conda environment: {e}", "ERROR")
            return False
    
    def install_clinical_filter(self) -> bool:
        """
        Install the clinical filtering system.
        
        Returns:
            True if installation successful
        """
        self._log("Installing clinical filtering system...")
        
        # Create installation directory
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy source files
        source_files = [
            "src/clinical_filter.py",
            "src/curation_interface.py",
            "src/kraken2_classifier.py",
            "src/cross_platform_utils.py",
            "scripts/nextflow_integration.py",
            "config/report_config.yaml"
        ]
        
        for source_file in source_files:
            source_path = Path(source_file)
            if source_path.exists():
                dest_path = self.install_dir / source_file
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                self._log(f"Installed: {source_file}")
            else:
                self._log(f"Warning: {source_file} not found", "WARNING")
        
        return True
    
    def configure_for_wsl(self) -> bool:
        """
        Configure system for WSL environment.
        
        Returns:
            True if configuration successful
        """
        self._log(f"Configuring for WSL{self.wsl_version}...")
        
        # Create WSL-specific configuration
        wsl_config = {
            "wsl_version": self.wsl_version,
            "windows_paths": {
                "databases": "/mnt/c/Users/hippovet/Desktop/databases",
                "sequencing_data": "/mnt/c/Users/hippovet/Desktop/sequencing_data",
                "epi2me_output": "/mnt/c/Users/hippovet/epi2melabs/instances"
            },
            "performance": {
                "max_threads": 4 if self.wsl_version == 1 else 8,
                "chunk_size_mb": 100 if self.wsl_version == 1 else 500,
                "memory_limit_gb": 4 if self.wsl_version == 1 else 8
            }
        }
        
        config_path = self.install_dir / "config" / "wsl_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(wsl_config, f, indent=2)
        
        self._log(f"WSL configuration saved to {config_path}")
        
        # Test Windows filesystem access
        test_path = Path("/mnt/c/")
        if test_path.exists():
            self._log("Windows filesystem access verified")
        else:
            self._log("Cannot access Windows filesystem through /mnt/c/", "WARNING")
        
        return True
    
    def create_shortcuts(self) -> bool:
        """
        Create convenient shortcuts and wrapper scripts.
        
        Returns:
            True if shortcuts created successfully
        """
        self._log("Creating shortcuts and wrapper scripts...")
        
        # Create main launcher script
        launcher_content = f"""#!/bin/bash
# HippoVet+ Clinical Filter Launcher

# Activate conda environment
source {self.conda_path}/bin/activate equine-clinical

# Set working directory
cd {self.install_dir}

# Launch based on argument
case "$1" in
    filter)
        python scripts/nextflow_integration.py "${{@:2}}"
        ;;
    review)
        python -c "from src.curation_interface import CurationInterface; CurationInterface().export_for_excel_review($2, '$3')"
        ;;
    validate)
        python scripts/validate_installation.py
        ;;
    *)
        echo "Usage: clinical-filter [filter|review|validate] [options]"
        echo "  filter: Process Epi2Me output with clinical filtering"
        echo "  review: Export results for Excel review"
        echo "  validate: Run installation validation"
        ;;
esac
"""
        
        launcher_path = self.install_dir / "clinical-filter"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        launcher_path.chmod(0o755)
        
        # Create desktop shortcut for Windows users
        if self.is_wsl:
            desktop_path = Path("/mnt/c/Users") / os.environ.get("USER", "hippovet") / "Desktop"
            if desktop_path.exists():
                shortcut_content = f"""@echo off
wsl.exe bash -c "cd {self.install_dir} && ./clinical-filter %*"
"""
                shortcut_path = desktop_path / "ClinicalFilter.bat"
                with open(shortcut_path, 'w') as f:
                    f.write(shortcut_content)
                self._log(f"Created Windows desktop shortcut: {shortcut_path}")
        
        return True
    
    def validate_installation(self) -> bool:
        """
        Validate the installation is working correctly.
        
        Returns:
            True if validation passes
        """
        self._log("Validating installation...")
        
        validation_script = f"""
import sys
sys.path.append('{self.install_dir}/src')

try:
    from clinical_filter import ClinicalFilter
    from curation_interface import CurationInterface
    from kraken2_classifier import Kraken2Classifier
    print("✅ All modules imported successfully")
    
    # Test basic functionality
    filter_engine = ClinicalFilter()
    curator = CurationInterface()
    print("✅ Core components initialized")
    
    # Test database configurations
    for db in ['PlusPFP-16', 'EuPathDB', 'Viral']:
        config = filter_engine.database_configs.get(db)
        if config:
            print(f"✅ {db} configuration loaded")
    
    print("\\n✅ Installation validation PASSED")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Validation failed: {{e}}")
    sys.exit(1)
"""
        
        # Run validation
        result = subprocess.run(
            [sys.executable, "-c", validation_script],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
    
    def generate_report(self) -> None:
        """Generate installation report."""
        report_path = self.install_dir / "installation_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("HippoVet+ Clinical Filtering System - Installation Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Installation Directory: {self.install_dir}\n")
            f.write(f"Conda Path: {self.conda_path}\n")
            f.write(f"WSL Version: {self.wsl_version if self.is_wsl else 'N/A'}\n")
            f.write(f"Platform: {platform.system()} {platform.release()}\n")
            f.write("\nInstallation Log:\n")
            f.write("-" * 40 + "\n")
            for log_entry in self.installation_log:
                f.write(log_entry + "\n")
        
        self._log(f"Installation report saved to: {report_path}")
    
    def run(self) -> bool:
        """
        Run the complete installation process.
        
        Returns:
            True if installation successful
        """
        print("=" * 60)
        print("HippoVet+ Clinical Filtering System Installer")
        print("=" * 60 + "\n")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Install Miniconda if needed
        if not self.install_miniconda():
            return False
        
        # Create conda environment
        if not self.create_conda_environment():
            return False
        
        # Install clinical filter system
        if not self.install_clinical_filter():
            return False
        
        # Configure for WSL
        if self.is_wsl:
            if not self.configure_for_wsl():
                return False
        
        # Create shortcuts
        if not self.create_shortcuts():
            return False
        
        # Validate installation
        if not self.validate_installation():
            self._log("Installation validation failed", "WARNING")
        
        # Generate report
        self.generate_report()
        
        print("\n" + "=" * 60)
        print("✅ Installation Complete!")
        print("=" * 60)
        print(f"\nInstalled to: {self.install_dir}")
        print("\nTo use the clinical filter:")
        print("  ./clinical-filter filter --input /path/to/epi2me/output --database PlusPFP-16")
        print("\nFor help:")
        print("  ./clinical-filter --help")
        
        return True


def main():
    """Main entry point for installer."""
    parser = argparse.ArgumentParser(
        description="Install HippoVet+ Clinical Filtering System"
    )
    parser.add_argument(
        "--wsl-version",
        type=int,
        choices=[1, 2],
        default=1,
        help="WSL version (default: 1)"
    )
    parser.add_argument(
        "--conda-path",
        help="Path to existing conda installation"
    )
    
    args = parser.parse_args()
    
    installer = WindowsInstaller(
        wsl_version=args.wsl_version,
        conda_path=args.conda_path
    )
    
    success = installer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()