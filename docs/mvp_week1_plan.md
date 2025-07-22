# Week 1 MVP Implementation Plan - Professional PDF Formatting

## Overview
Focus on delivering a working professional PDF report with minimal complexity, using existing reportlab implementation as the foundation.

## Current State
- ✅ Basic PDF generation with reportlab
- ✅ Matplotlib charts integration
- ✅ Polish language support
- ⚠️ Missing: Professional header, branding, multi-page structure

## Week 1 MVP Deliverables

### 1. Professional Header (Day 1-2)
**Implementation:**
- Create `assets/` directory for logo and DNA helix image
- Use reportlab's canvas.drawImage() for direct placement
- Simple text placement for patient info using drawString()

**Required Assets:**
- HippoVet+ logo (PNG/JPG, ~300x100px)
- DNA helix stock image (PNG/JPG, ~200x200px)
- Both should be royalty-free or client-provided

**Code Structure:**
```python
def draw_header(canvas, patient_info, page_num=1):
    # Logo placement
    canvas.drawImage('assets/logo.png', 50, 750, width=150, height=50)
    
    # Patient info box
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(350, 780, f"Nr badania: {patient_info['sample_number']}")
    canvas.drawString(350, 760, f"Data: {patient_info['date_received']}")
    
    # Page number
    canvas.drawString(520, 30, f"Strona {page_num}")
```

### 2. Multi-Page Structure (Day 2-3)
**Page Layout:**
- Page 1: Header + Patient Info + Executive Summary
- Page 2: Species Distribution Chart + Analysis
- Page 3: Phylum Distribution + Clinical Interpretation
- Page 4: Biochemical Analysis Tables
- Page 5: Recommendations + Footer

**Implementation:**
- Use canvas.showPage() for clean page breaks
- Create separate functions for each section
- Maintain consistent header/footer across pages

### 3. Enhanced Charts (Day 3-4)
**Current:** Basic matplotlib charts
**Enhancement:** 
- Ensure horizontal bar charts for species
- Add reference range indicators to phylum chart
- Export as high-quality images for PDF embedding
- Consistent color scheme matching branding

### 4. Clinical Tables (Day 4-5)
**Implementation:**
- Use reportlab's Table and TableStyle
- Create standardized table templates
- Polish headers and formatting
- Include reference ranges where applicable

## File Structure Updates
```
equine-microbiome-reporter/
├── assets/
│   ├── logo.png          # HippoVet+ logo
│   ├── dna_helix.png     # DNA helix image
│   └── fonts/            # Custom fonts if needed
├── enhanced_pdf_generator.py  # Week 1 enhanced version
└── templates/
    └── clinical_text.py   # Polish clinical text templates
```

## Implementation Priority
1. **Day 1:** Set up assets folder, obtain logo and DNA helix image
2. **Day 2:** Implement professional header function
3. **Day 3:** Create multi-page structure with consistent headers
4. **Day 4:** Enhance chart styling and embed in pages
5. **Day 5:** Add clinical tables and final polish

## Code Modifications Needed

### 1. Enhance Current Generator
- Add header drawing function
- Implement page management system
- Create consistent styling helpers

### 2. Asset Management
```python
class AssetManager:
    LOGO_PATH = 'assets/logo.png'
    DNA_HELIX_PATH = 'assets/dna_helix.png'
    
    @staticmethod
    def verify_assets():
        """Check all required assets exist"""
        required = [AssetManager.LOGO_PATH, AssetManager.DNA_HELIX_PATH]
        missing = [f for f in required if not Path(f).exists()]
        if missing:
            raise FileNotFoundError(f"Missing assets: {missing}")
```

### 3. Page Layout Helper
```python
class PageLayout:
    # A4 dimensions in points
    PAGE_WIDTH = 595
    PAGE_HEIGHT = 842
    MARGIN = 50
    
    @staticmethod
    def draw_page_frame(canvas):
        """Draw consistent page frame/borders"""
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.rect(MARGIN, MARGIN, 
                   PAGE_WIDTH - 2*MARGIN, 
                   PAGE_HEIGHT - 2*MARGIN)
```

## Testing Strategy
1. Generate test PDF with sample data
2. Verify all 5 pages render correctly
3. Check Polish text encoding
4. Validate image quality
5. Ensure consistent formatting

## Deliverable Checklist
- [ ] Professional header with logo on all pages
- [ ] DNA helix imagery integrated
- [ ] 5-page report structure
- [ ] Horizontal bar charts for species
- [ ] Clinical findings tables
- [ ] Polish language throughout
- [ ] Consistent branding/colors
- [ ] Sample PDF demonstrating all features

## Next Steps After Week 1
- Week 2: Multi-language support (EN/JP)
- Week 3: Batch processing notebook
- Week 4: Testing and documentation