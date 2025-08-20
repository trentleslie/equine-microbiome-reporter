"""
Automated Layout Analysis and Refinement System
Analyzes HTML/CSS for layout inconsistencies and professional formatting issues
"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    """Analyzes HTML layout for professional formatting issues"""
    
    def __init__(self):
        self.issues = {
            'width_mismatches': [],
            'alignment_problems': [],
            'spacing_irregularities': [],
            'typography_issues': [],
            'css_inconsistencies': []
        }
    
    def analyze_html(self, html_content: str) -> Dict[str, List]:
        """Main analysis function - returns detected issues"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Reset issues for new analysis
        self._reset_issues()
        
        # Run analysis modules
        self._analyze_container_widths(soup)
        self._analyze_pill_alignment(soup)
        self._analyze_spacing_consistency(soup)
        self._analyze_typography(soup)
        self._analyze_css_rules(html_content)
        
        return self.issues
    
    def _reset_issues(self):
        """Reset issues dict for new analysis"""
        for key in self.issues:
            self.issues[key] = []
    
    def _analyze_container_widths(self, soup: BeautifulSoup):
        """Detect width inconsistencies in containers"""
        # Find all content containers
        content_headers = soup.find_all(class_='content-header')
        content_areas = soup.find_all(class_='content-area')
        
        # Check for padding consistency
        for header in content_headers:
            style = header.get('style', '')
            if 'padding' in style and '25mm' in style:
                self.issues['width_mismatches'].append({
                    'element': 'content-header',
                    'issue': 'Uses 25mm padding instead of standard 20mm',
                    'fix': 'Change padding to 15mm 20mm'
                })
        
        # Check page containers
        pages = soup.find_all(class_=re.compile(r'page'))
        page_widths = []
        for page in pages:
            style = page.get('style', '')
            width_match = re.search(r'width:\s*(\d+(?:\.\d+)?(?:mm|px|%))', style)
            if width_match:
                page_widths.append(width_match.group(1))
        
        # Check for width variations
        if len(set(page_widths)) > 1:
            self.issues['width_mismatches'].append({
                'element': 'page containers',
                'issue': f'Inconsistent widths: {set(page_widths)}',
                'fix': 'Standardize all page widths to 210mm'
            })
    
    def _analyze_pill_alignment(self, soup: BeautifulSoup):
        """Check pill box alignment and spacing"""
        # Find pill containers
        pill_containers = soup.find_all('div', style=re.compile(r'display:\s*flex'))
        
        gaps = []
        for container in pill_containers:
            style = container.get('style', '')
            gap_match = re.search(r'gap:\s*(\d+px)', style)
            if gap_match:
                gaps.append(gap_match.group(1))
        
        # Check for gap inconsistencies
        unique_gaps = set(gaps)
        if len(unique_gaps) > 1:
            self.issues['alignment_problems'].append({
                'element': 'pill containers',
                'issue': f'Inconsistent gaps: {unique_gaps}',
                'fix': 'Standardize all gaps to 10px'
            })
        
        # Check for proper centering
        for container in pill_containers:
            style = container.get('style', '')
            if 'justify-content: center' not in style and 'text-align: center' not in style:
                self.issues['alignment_problems'].append({
                    'element': 'pill container',
                    'issue': 'Pills not centered',
                    'fix': 'Add justify-content: center to flexbox'
                })
    
    def _analyze_spacing_consistency(self, soup: BeautifulSoup):
        """Analyze margin and padding consistency"""
        # Find all elements with inline styles
        elements_with_styles = soup.find_all(style=True)
        
        margins = []
        paddings = []
        
        for element in elements_with_styles:
            style = element.get('style', '')
            
            # Extract margin values
            margin_matches = re.findall(r'margin(?:-\w+)?:\s*([\d.]+(?:mm|px|%))', style)
            margins.extend(margin_matches)
            
            # Extract padding values
            padding_matches = re.findall(r'padding(?:-\w+)?:\s*([\d.]+(?:mm|px|%))', style)
            paddings.extend(padding_matches)
        
        # Check for too many unique values (indicates inconsistency)
        unique_margins = set(margins)
        unique_paddings = set(paddings)
        
        if len(unique_margins) > 8:  # Allow some variation but flag excessive diversity
            self.issues['spacing_irregularities'].append({
                'element': 'various',
                'issue': f'Too many unique margin values: {len(unique_margins)}',
                'fix': 'Standardize to common margin scale (2mm, 5mm, 10mm, 15mm)'
            })
    
    def _analyze_typography(self, soup: BeautifulSoup):
        """Check typography consistency"""
        # Extract font sizes
        elements_with_styles = soup.find_all(style=True)
        font_sizes = []
        
        for element in elements_with_styles:
            style = element.get('style', '')
            font_match = re.search(r'font-size:\s*([\d.]+(?:pt|px))', style)
            if font_match:
                font_sizes.append(font_match.group(1))
        
        # Check for reasonable font hierarchy
        unique_sizes = set(font_sizes)
        if len(unique_sizes) > 6:  # Professional designs typically use 3-6 font sizes
            self.issues['typography_issues'].append({
                'element': 'various',
                'issue': f'Too many font sizes: {len(unique_sizes)}',
                'fix': 'Reduce to standard hierarchy: 16pt, 14pt, 12pt, 11pt, 9pt, 8pt'
            })
    
    def _analyze_css_rules(self, html_content: str):
        """Extract and analyze CSS for inconsistencies"""
        # Extract CSS from <style> tag
        style_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
        if not style_match:
            return
        
        css_content = style_match.group(1)
        
        # Check for duplicate/conflicting rules
        # Look for page-break rules
        if 'page-break-after: always' in css_content:
            self.issues['css_inconsistencies'].append({
                'element': '.page class',
                'issue': 'Contains page-break-after: always forcing pagination',
                'fix': 'Remove or make conditional for better content flow'
            })
        
        # Check for inconsistent padding in similar classes
        content_header_padding = re.search(r'\.content-header\s*{[^}]*padding:\s*([^;]+)', css_content)
        content_area_padding = re.search(r'\.content-area\s*{[^}]*padding:\s*([^;]+)', css_content)
        
        if content_header_padding and content_area_padding:
            header_pad = content_header_padding.group(1).strip()
            area_pad = content_area_padding.group(1).strip()
            
            # Extract horizontal padding values
            header_horizontal = re.findall(r'(\d+(?:\.\d+)?mm)', header_pad)
            area_horizontal = re.findall(r'(\d+(?:\.\d+)?mm)', area_pad)
            
            if len(header_horizontal) >= 2 and len(area_horizontal) >= 2:
                if header_horizontal[1] != area_horizontal[0]:  # Compare horizontal paddings
                    self.issues['css_inconsistencies'].append({
                        'element': 'content containers',
                        'issue': f'Mismatched horizontal padding: header={header_horizontal[1]}, area={area_horizontal[0]}',
                        'fix': 'Align horizontal padding values for consistent width'
                    })
    
    def get_summary(self) -> str:
        """Generate human-readable summary of issues"""
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        if total_issues == 0:
            return "✅ Layout analysis: No issues detected - Professional formatting ✅"
        
        summary = f"📊 Layout Analysis: {total_issues} issues detected\n\n"
        
        for category, issues in self.issues.items():
            if issues:
                summary += f"**{category.replace('_', ' ').title()}** ({len(issues)} issues):\n"
                for issue in issues:
                    summary += f"  • {issue['element']}: {issue['issue']}\n"
                    summary += f"    Fix: {issue['fix']}\n"
                summary += "\n"
        
        return summary
    
    def has_critical_issues(self) -> bool:
        """Check if there are critical layout issues"""
        critical_count = (
            len(self.issues['width_mismatches']) + 
            len(self.issues['alignment_problems'])
        )
        return critical_count > 0


class LayoutOptimizer:
    """Applies automated fixes to layout issues"""
    
    def __init__(self):
        self.fixes_applied = []
    
    def fix_issues(self, issues: Dict[str, List], html_content: str) -> str:
        """Apply automated fixes to HTML content"""
        fixed_html = html_content
        self.fixes_applied = []
        
        # Apply width consistency fixes
        for issue in issues.get('width_mismatches', []):
            if 'padding' in issue['issue'] and '25mm' in issue['issue']:
                fixed_html = self._fix_content_header_padding(fixed_html)
        
        # Apply alignment fixes
        for issue in issues.get('alignment_problems', []):
            if 'gap' in issue['issue']:
                fixed_html = self._standardize_gaps(fixed_html)
        
        return fixed_html
    
    def _fix_content_header_padding(self, html_content: str) -> str:
        """Fix content-header padding inconsistency"""
        # Replace 25mm with 20mm in content-header padding
        fixed = re.sub(
            r'(\.content-header\s*{[^}]*padding:\s*\d+(?:\.\d+)?mm\s+)25mm',
            r'\g<1>20mm',
            html_content
        )
        
        if fixed != html_content:
            self.fixes_applied.append("Fixed content-header padding: 25mm → 20mm")
        
        return fixed
    
    def _standardize_gaps(self, html_content: str) -> str:
        """Standardize all flexbox gaps to 10px"""
        # Replace various gap values with 10px
        fixed = re.sub(r'gap:\s*\d+px', 'gap: 10px', html_content)
        
        if fixed != html_content:
            self.fixes_applied.append("Standardized all flexbox gaps to 10px")
        
        return fixed


def analyze_and_optimize_layout(html_content: str) -> Tuple[str, Dict[str, Any]]:
    """
    Main function to analyze and optimize HTML layout
    Returns: (optimized_html, analysis_report)
    """
    analyzer = LayoutAnalyzer()
    optimizer = LayoutOptimizer()
    
    # Analyze current layout
    issues = analyzer.analyze_html(html_content)
    
    # Apply automated fixes
    optimized_html = optimizer.fix_issues(issues, html_content)
    
    # Re-analyze to check improvements
    final_issues = analyzer.analyze_html(optimized_html)
    
    report = {
        'initial_issues': issues,
        'fixes_applied': optimizer.fixes_applied,
        'remaining_issues': final_issues,
        'summary': analyzer.get_summary(),
        'is_professional': not analyzer.has_critical_issues()
    }
    
    return optimized_html, report


if __name__ == "__main__":
    # Quick test with sample HTML
    test_html = '''
    <div class="content-header" style="padding: 15mm 25mm;">Test</div>
    <div style="display: flex; gap: 8px;">Pills</div>
    '''
    
    optimized, report = analyze_and_optimize_layout(test_html)
    print("Analysis Report:")
    print(report['summary'])
    print("\nFixes Applied:")
    for fix in report['fixes_applied']:
        print(f"  • {fix}")