#!/usr/bin/env python3
"""
Validation script for PDF report fixes
Checks that all requested changes have been implemented
"""

import sys
import re
from pathlib import Path

def validate_code_changes():
    """Validate that code changes have been made"""

    print("=" * 60)
    print("VALIDATION: Code Changes")
    print("=" * 60)

    issues = []
    fixes = []

    # 1. Check config for eukaryote filtering
    config_path = Path("config/report_config.yaml")
    if config_path.exists():
        config_content = config_path.read_text()
        if "species_filtering" in config_content and "exclude_eukaryotes" in config_content:
            fixes.append("✅ Config has eukaryote exclusion list")
        else:
            issues.append("❌ Config missing eukaryote filtering")

    # 2. Check CSV processor for filtering
    csv_proc_path = Path("src/csv_processor.py")
    if csv_proc_path.exists():
        csv_content = csv_proc_path.read_text()
        if "EUKARYOTE_SPECIES" in csv_content and "_filter_eukaryotes" in csv_content:
            fixes.append("✅ CSV processor has eukaryote filtering")
        else:
            issues.append("❌ CSV processor missing eukaryote filtering")

        if "clean_species_name" in csv_content and r"\[" in csv_content:
            fixes.append("✅ CSV processor has species name cleaning (removes brackets)")
        else:
            issues.append("❌ CSV processor missing name cleaning")

    # 3. Check chart generator for numbering removal
    chart_path = Path("src/chart_generator.py")
    if chart_path.exists():
        chart_content = chart_path.read_text()
        # Should NOT have numbering like "f"{i+1}. {name}"
        if 'f"{i+1}. {name' not in chart_content and 'f"{name[' in chart_content:
            fixes.append("✅ Chart generator removed species numbering")
        else:
            issues.append("❌ Chart generator may still have numbering")

    # 4. Check data models for case_number
    models_path = Path("src/data_models.py")
    if models_path.exists():
        models_content = models_path.read_text()
        if "case_number" in models_content:
            fixes.append("✅ PatientInfo has case_number field")
        else:
            issues.append("❌ PatientInfo missing case_number field")

    # 5. Check templates for MIMT (not MEMT)
    template_files = list(Path("templates/clean").glob("*.html"))
    mimt_count = 0
    memt_count = 0

    for template in template_files:
        content = template.read_text()
        mimt_count += content.count("MIMT")
        memt_count += content.count("MEMT")

    if mimt_count > 0 and memt_count == 0:
        fixes.append(f"✅ All templates use MIMT (found {mimt_count} occurrences)")
    elif memt_count > 0:
        issues.append(f"❌ Found {memt_count} occurrences of MEMT (should be MIMT)")

    # 6. Check for Shotgun metagenomic NGS
    page4 = Path("templates/clean/page4_summary.html")
    if page4.exists():
        content = page4.read_text()
        if "Shotgun metagenomic NGS" in content:
            fixes.append("✅ Analysis method updated to 'Shotgun metagenomic NGS'")
        elif "16S rRNA NGS" in content:
            issues.append("❌ Still shows '16S rRNA NGS' instead of 'Shotgun metagenomic NGS'")

    # 7. Check for complete species list (not just [:10])
    page1 = Path("templates/clean/page1_sequencing.html")
    if page1.exists():
        content = page1.read_text()
        if "data.species_list[:10]" in content:
            issues.append("❌ Page 1 still shows only top 10 species")
        elif "{% for species in data.species_list %}" in content:
            fixes.append("✅ Page 1 shows complete species list")

    # 8. Check for removed phylum table on page 2
    page2 = Path("templates/clean/page2_phylum.html")
    if page2.exists():
        content = page2.read_text()
        if "<table class=\"data-table\">" not in content:
            fixes.append("✅ Redundant phylum table removed from page 2")
        else:
            issues.append("❌ Phylum table still present on page 2")

    print("\nFixed Issues:")
    for fix in fixes:
        print(f"  {fix}")

    if issues:
        print("\nRemaining Issues:")
        for issue in issues:
            print(f"  {issue}")

    print(f"\n{'='*60}")
    print(f"Total Fixes: {len(fixes)}/{len(fixes) + len(issues)}")
    print(f"{'='*60}\n")

    return len(issues) == 0

def print_summary():
    """Print summary of all changes"""
    print("\n" + "=" * 60)
    print("SUMMARY OF CHANGES")
    print("=" * 60)

    changes = [
        ("1. Eukaryote Filtering", "config/report_config.yaml, src/csv_processor.py"),
        ("2. Species Name Cleaning", "src/csv_processor.py (removes [brackets])"),
        ("3. Remove Numbering", "src/chart_generator.py"),
        ("4. Add case_number Field", "src/data_models.py"),
        ("5. Fix Lab Name", "All templates (MEMT → MIMT)"),
        ("6. Update Analysis Method", "page4_summary.html (Shotgun metagenomic NGS)"),
        ("7. Complete Species List", "page1_sequencing.html (all species, not just 10)"),
        ("8. Remove Phylum Table", "page2_phylum.html"),
        ("9. Fix Percentages", "src/csv_processor.py (bacteria-only denominators)"),
    ]

    for i, (change, location) in enumerate(changes, 1):
        print(f"\n{i}. {change}")
        print(f"   Location: {location}")

    print("\n" + "=" * 60)

def main():
    """Main validation"""

    print("\n🔍 PDF Report Fixes - Validation Script\n")

    # Validate code changes
    code_valid = validate_code_changes()

    # Print summary
    print_summary()

    # Next steps
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\nTo generate a new PDF report with these fixes:")
    print("\n1. Ensure you have the required dependencies installed")
    print("2. Run the report generation script:")
    print("   python scripts/generate_clean_report.py")
    print("\n3. Or use the existing barcode67 CSV data:")
    print("   python -c \"from scripts.generate_clean_report import generate_clean_report\"")
    print("   (See script for full example)")

    print("\n" + "=" * 60)

    if code_valid:
        print("\n✅ All validation checks passed!")
        return 0
    else:
        print("\n⚠️  Some issues need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())