# Testing the Fixed Report

## Quick Start Guide

This guide helps you generate a new PDF report with all the fixes applied.

---

## Method 1: Using Demo Script (Recommended)

```bash
# Run the existing demo script
./demo.sh

# This will automatically:
# - Use the fixed code
# - Generate a clean report
# - Show you the results
```

---

## Method 2: Python Script (For barcode67 specifically)

Create a test script `test_barcode67.py`:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from src.data_models import PatientInfo
from scripts.generate_clean_report import generate_clean_report

# Patient info matching the original report
patient = PatientInfo(
    name='Sample_barcode67',
    age='Unknown',
    species='Horse',
    sample_number='barcode67',
    case_number='CASE-BC67-2025',  # NEW: Optional case number
    date_received='2025-09-26',
    date_analyzed='2025-09-26',
    performed_by='MIMT Genetics Lab',
    requested_by='Veterinarian'
)

# Generate the fixed report
success = generate_clean_report(
    csv_path='data/25_04_23 bact.csv',
    patient=patient,
    output_path='barcode67_report_FIXED.pdf'
)

if success:
    print('✅ Fixed report generated: barcode67_report_FIXED.pdf')
    print('\nPlease review:')
    print('  - No eukaryotes in species list')
    print('  - No numbering on species names')
    print('  - No square brackets in names')
    print('  - Complete species list (not just top 10)')
    print('  - MIMT (not MEMT) everywhere')
    print('  - "Shotgun metagenomic NGS" on page 4')
    sys.exit(0)
else:
    print('❌ Failed to generate report')
    sys.exit(1)
```

Then run:
```bash
python test_barcode67.py
```

---

## Method 3: Manual Comparison

### Step 1: Compare Before/After

Open both PDFs side by side:
```bash
# Old report (with issues)
barcode67_report.pdf

# New report (fixed)
barcode67_report_FIXED.pdf
```

### Step 2: Check Each Page

#### Page 1 - Species Distribution
- ✅ **Chart**: No numbers before species names
- ✅ **Chart**: Species names clean (no brackets)
- ✅ **Table**: Shows ALL species, not just 10
- ✅ **Table**: No "Homo sapiens" or "Papaver somniferum"
- ✅ **Footer**: Says "MIMT Genetics Laboratory"

#### Page 2 - Phylum Analysis
- ✅ **Two charts only** (no redundant table)
- ✅ **Percentages**: Should be different (bacteria-only calculation)
- ✅ **Footer**: Says "MIMT Genetics Laboratory"

#### Page 3 - Clinical Interpretation
- ✅ **Footer**: Says "MIMT Genetics Laboratory"
- ⚠️ **Clinical text**: Should still make sense with new percentages

#### Page 4 - Summary
- ✅ **Analysis Method**: "Shotgun metagenomic NGS"
- ✅ **Contact**: "MIMT Genetics Laboratory"
- ✅ **Email**: lab@mimtgenetics.com
- ✅ **Footer**: Says "MIMT Genetics Laboratory"

---

## Validation Checklist

Print this out and check each item:

### Data Quality
- [ ] No eukaryotic species in any list
- [ ] All species names are clean (no brackets)
- [ ] Species percentages sum to ~100%
- [ ] All bacterial species are included

### Formatting
- [ ] No numbering prefixes on chart labels
- [ ] Species names are readable
- [ ] Charts look professional
- [ ] Tables are complete

### Metadata
- [ ] Laboratory name: "MIMT" everywhere
- [ ] Email: lab@mimtgenetics.com
- [ ] Analysis method: "Shotgun metagenomic NGS"
- [ ] Page numbers: 1 of 4, 2 of 4, 3 of 4, 4 of 4

### Layout
- [ ] Page 1: Chart + Complete table
- [ ] Page 2: Two charts (no table)
- [ ] Page 3: Clinical info
- [ ] Page 4: Summary + guidelines

---

## Expected Differences from Old Report

### Species List
**Before**: 13 species (including Homo sapiens, Papaver)
**After**: ~10-11 species (only bacteria)

### Percentages
**Before**: Calculated with eukaryotes in denominator
**After**: Calculated with only bacteria

Example:
- Before: Bifidobacterium longum = 3.85% of total (including eukaryotes)
- After: Bifidobacterium longum = 7.7% of bacteria only

### Visual Changes
**Before**: "13. Humulus lupulus"
**After**: "Humulus lupulus"

**Before**: "[Clostridium] innocuum"
**After**: "Clostridium innocuum"

---

## Troubleshooting

### If report generation fails:

1. **Check Python environment**:
   ```bash
   python --version  # Should be 3.8+
   python -c "import matplotlib; print('OK')"
   ```

2. **Check dependencies**:
   ```bash
   # If using poetry
   poetry install

   # Or check manually
   pip list | grep -E "(matplotlib|pandas|weasyprint|jinja2)"
   ```

3. **Check file paths**:
   ```bash
   ls data/25_04_23\ bact.csv
   ls templates/clean/*.html
   ```

4. **Run validation**:
   ```bash
   python validate_fixes.py
   ```

### If PDF looks wrong:

1. Check the HTML output first:
   ```bash
   # The script saves .html version
   ls *.html
   # Open in browser to debug
   ```

2. Verify CSV data:
   ```bash
   head -5 data/25_04_23\ bact.csv
   ```

3. Check logs for errors:
   ```bash
   # Script outputs detailed logs
   # Look for ERROR or WARNING messages
   ```

---

## Contact

For questions about these fixes:
- See: `FIXES_SUMMARY.md` for technical details
- Run: `python validate_fixes.py` for automated checks

---

**Ready to test!** 🚀

Choose Method 1 (demo.sh) for the easiest path, or Method 2 (Python script) for full control.