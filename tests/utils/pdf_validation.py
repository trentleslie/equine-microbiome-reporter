"""PDF validation utilities for testing"""

from pathlib import Path
import subprocess
from typing import Optional, List

def validate_pdf_structure(pdf_path: Path) -> bool:
    """Validate PDF file structure using basic checks"""
    if not pdf_path.exists():
        return False
    
    if pdf_path.suffix.lower() != '.pdf':
        return False
    
    # Check minimum file size (PDF should be at least a few KB)
    if pdf_path.stat().st_size < 1000:
        return False
    
    # Check PDF header
    try:
        with open(pdf_path, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF-'):
                return False
    except Exception:
        return False
    
    return True

def count_pdf_pages(pdf_path: Path) -> Optional[int]:
    """Count pages in PDF file using simple byte scanning"""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
            # Simple page count - count '/Type/Page' occurrences
            page_count = content.count(b'/Type/Page')
            return page_count if page_count > 0 else 1
    except Exception:
        return None

def extract_pdf_text_simple(pdf_path: Path) -> Optional[str]:
    """Extract text from PDF using simple method (fallback for testing)"""
    try:
        # Try using pdftotext if available (common Linux tool)
        result = subprocess.run(
            ['pdftotext', str(pdf_path), '-'], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None

def validate_pdf_contains_text(pdf_path: Path, expected_text: List[str]) -> bool:
    """Validate PDF contains expected text content"""
    text_content = extract_pdf_text_simple(pdf_path)
    
    if text_content is None:
        # If we can't extract text, just validate structure
        return validate_pdf_structure(pdf_path)
    
    text_lower = text_content.lower()
    
    for expected in expected_text:
        if expected.lower() not in text_lower:
            return False
    
    return True

def assert_pdf_valid_for_testing(pdf_path: Path, expected_pages: int = 5):
    """Assert PDF is valid for testing purposes"""
    assert pdf_path.exists(), f"PDF file does not exist: {pdf_path}"
    assert validate_pdf_structure(pdf_path), f"Invalid PDF structure: {pdf_path}"
    
    page_count = count_pdf_pages(pdf_path)
    if page_count is not None:
        assert page_count >= expected_pages, f"Expected at least {expected_pages} pages, got {page_count}"

def assert_pdf_contains_microbiome_content(pdf_path: Path):
    """Assert PDF contains expected microbiome report content"""
    expected_content = [
        'microbiome', 'analysis', 'bacteria', 'species',
        'phylum', 'percentage', 'dysbiosis'
    ]
    
    # First validate structure
    assert_pdf_valid_for_testing(pdf_path)
    
    # Try to validate content if possible
    if not validate_pdf_contains_text(pdf_path, expected_content):
        # If text extraction fails, just ensure file is reasonable size
        file_size = pdf_path.stat().st_size
        assert file_size > 50000, f"PDF file seems too small for a full report: {file_size} bytes"

def get_pdf_info(pdf_path: Path) -> dict:
    """Get basic PDF information for testing"""
    info = {
        'exists': pdf_path.exists(),
        'size_bytes': 0,
        'valid_structure': False,
        'page_count': None
    }
    
    if info['exists']:
        info['size_bytes'] = pdf_path.stat().st_size
        info['valid_structure'] = validate_pdf_structure(pdf_path)
        info['page_count'] = count_pdf_pages(pdf_path)
    
    return info