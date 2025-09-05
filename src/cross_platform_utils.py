"""
Cross-platform utilities for Windows/Linux/Mac compatibility.

Handles path operations, executable detection, and platform-specific configurations
for the equine microbiome reporter pipeline.
"""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import subprocess
import logging

logger = logging.getLogger(__name__)


class CrossPlatformPathHandler:
    """Handles cross-platform path operations and executable detection."""
    
    @staticmethod
    def get_platform() -> str:
        """Get normalized platform identifier."""
        system = platform.system().lower()
        if system == 'darwin':
            return 'mac'
        return system  # 'windows', 'linux'
    
    @staticmethod
    def normalize_path(path_str: str) -> Path:
        """
        Normalize path for current platform.
        
        Args:
            path_str: Path string (may contain environment variables)
            
        Returns:
            Normalized Path object
        """
        # Expand environment variables
        expanded = os.path.expandvars(path_str)
        expanded = os.path.expanduser(expanded)
        
        # Convert to Path object and resolve
        return Path(expanded).resolve()
    
    @staticmethod
    def find_executable(executable_name: str, env_var: Optional[str] = None) -> Optional[str]:
        """
        Find executable across platforms with environment variable support.
        
        Args:
            executable_name: Base executable name (e.g., 'kraken2')
            env_var: Environment variable name for explicit path
            
        Returns:
            Path to executable or None if not found
        """
        # Try environment variable first
        if env_var and os.environ.get(env_var):
            env_path = CrossPlatformPathHandler.normalize_path(os.environ[env_var])
            if env_path.exists() and env_path.is_file():
                return str(env_path)
            else:
                logger.warning(f"Executable specified in {env_var} not found: {env_path}")
        
        # Add platform-specific extensions
        platform_name = CrossPlatformPathHandler.get_platform()
        if platform_name == 'windows':
            executable_variants = [f"{executable_name}.exe", f"{executable_name}.bat", executable_name]
        else:
            executable_variants = [executable_name]
        
        # Search in PATH
        for variant in executable_variants:
            path = shutil.which(variant)
            if path:
                return path
        
        # Try common conda locations
        conda_paths = CrossPlatformPathHandler._get_conda_executable_paths(executable_name)
        for conda_path in conda_paths:
            if conda_path.exists():
                return str(conda_path)
        
        return None
    
    @staticmethod
    def _get_conda_executable_paths(executable_name: str) -> List[Path]:
        """Get common conda environment paths for executable."""
        platform_name = CrossPlatformPathHandler.get_platform()
        home_dir = Path.home()
        
        conda_roots = [
            home_dir / "miniconda3",
            home_dir / "anaconda3", 
            Path("/opt/miniconda3"),
            Path("/opt/anaconda3")
        ]
        
        if platform_name == 'windows':
            conda_roots.extend([
                Path("C:/ProgramData/Miniconda3"),
                Path("C:/ProgramData/Anaconda3"),
                home_dir / "AppData/Local/Continuum/miniconda3",
                home_dir / "AppData/Local/Continuum/anaconda3"
            ])
            bin_subdir = "Scripts"
            executable_name = f"{executable_name}.exe"
        else:
            bin_subdir = "bin"
        
        paths = []
        for conda_root in conda_roots:
            # Check base environment
            paths.append(conda_root / bin_subdir / executable_name)
            
            # Check kraken2 environment specifically  
            paths.append(conda_root / "envs/kraken2" / bin_subdir / executable_name)
        
        return paths
    
    @staticmethod
    def get_database_paths() -> Dict[str, Optional[str]]:
        """
        Get Kraken2 database paths from environment with cross-platform support.
        
        Returns:
            Dictionary mapping database names to paths
        """
        db_paths = {}
        
        # Standard database
        standard_path = os.environ.get('KRAKEN2_DB_PATH')
        if standard_path:
            db_paths['standard'] = str(CrossPlatformPathHandler.normalize_path(standard_path))
        
        # SILVA database (optional)
        silva_path = os.environ.get('KRAKEN2_SILVA_DB')
        if silva_path:
            db_paths['silva'] = str(CrossPlatformPathHandler.normalize_path(silva_path))
        
        return db_paths
    
    @staticmethod
    def create_temp_dir(prefix: str = "kraken2_") -> Path:
        """Create platform-appropriate temporary directory."""
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        return temp_dir
    
    @staticmethod
    def validate_kraken2_installation() -> Dict[str, any]:
        """
        Validate Kraken2 installation across platforms.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'platform': CrossPlatformPathHandler.get_platform(),
            'kraken2_found': False,
            'kraken2_path': None,
            'kraken2_build_found': False,
            'kraken2_build_path': None,
            'bracken_found': False,
            'bracken_path': None,
            'databases': {},
            'issues': []
        }
        
        # Check Kraken2 executable
        kraken2_path = CrossPlatformPathHandler.find_executable('kraken2', 'KRAKEN2_EXECUTABLE')
        if kraken2_path:
            results['kraken2_found'] = True
            results['kraken2_path'] = kraken2_path
            
            # Test executable
            try:
                result = subprocess.run([kraken2_path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"Kraken2 version: {result.stdout.strip()}")
                else:
                    results['issues'].append(f"Kraken2 executable found but version check failed")
            except Exception as e:
                results['issues'].append(f"Kraken2 executable test failed: {e}")
        else:
            results['issues'].append("Kraken2 executable not found in PATH or environment variables")
        
        # Check Kraken2-build executable
        build_path = CrossPlatformPathHandler.find_executable('kraken2-build', 'KRAKEN2_BUILD_EXECUTABLE')
        if build_path:
            results['kraken2_build_found'] = True
            results['kraken2_build_path'] = build_path
        else:
            results['issues'].append("kraken2-build executable not found")
        
        # Check Bracken (optional)
        bracken_path = CrossPlatformPathHandler.find_executable('bracken', 'BRACKEN_EXECUTABLE')
        if bracken_path:
            results['bracken_found'] = True
            results['bracken_path'] = bracken_path
        
        # Check databases
        db_paths = CrossPlatformPathHandler.get_database_paths()
        for db_name, db_path in db_paths.items():
            if db_path and Path(db_path).exists():
                results['databases'][db_name] = {
                    'path': db_path,
                    'exists': True,
                    'size_gb': CrossPlatformPathHandler._get_directory_size_gb(Path(db_path))
                }
            else:
                results['databases'][db_name] = {
                    'path': db_path,
                    'exists': False,
                    'size_gb': 0
                }
                if db_path:
                    results['issues'].append(f"Database directory not found: {db_path}")
        
        return results
    
    @staticmethod
    def _get_directory_size_gb(directory: Path) -> float:
        """Get directory size in GB."""
        if not directory.exists():
            return 0.0
        
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (PermissionError, OSError):
            return 0.0
        
        return total_size / (1024**3)  # Convert to GB


def get_platform_specific_config() -> Dict[str, str]:
    """
    Get platform-specific configuration recommendations.
    
    Returns:
        Dictionary with platform-specific settings
    """
    platform_name = CrossPlatformPathHandler.get_platform()
    
    configs = {
        'linux': {
            'conda_install_cmd': 'wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && bash miniconda.sh',
            'kraken2_install_cmd': 'conda create -n kraken2 -c bioconda kraken2 bracken',
            'default_threads': '$(nproc)',
            'path_separator': '/',
            'executable_extension': '',
            'typical_db_location': '/home/$USER/kraken2_databases'
        },
        'windows': {
            'conda_install_cmd': 'Download and run Miniconda3-latest-Windows-x86_64.exe from https://repo.anaconda.com/miniconda/',
            'kraken2_install_cmd': 'conda create -n kraken2 -c bioconda kraken2 bracken',
            'default_threads': '%NUMBER_OF_PROCESSORS%',
            'path_separator': '\\',
            'executable_extension': '.exe',
            'typical_db_location': 'C:\\kraken2_databases'
        },
        'mac': {
            'conda_install_cmd': 'wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -O miniconda.sh && bash miniconda.sh',
            'kraken2_install_cmd': 'conda create -n kraken2 -c bioconda kraken2 bracken',
            'default_threads': '$(sysctl -n hw.ncpu)',
            'path_separator': '/',
            'executable_extension': '',
            'typical_db_location': '/Users/$USER/kraken2_databases'
        }
    }
    
    return configs.get(platform_name, configs['linux'])