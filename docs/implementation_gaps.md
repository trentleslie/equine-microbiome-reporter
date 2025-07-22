# Implementation Gaps - Current vs Reference PDF

## Major Differences to Address

### 1. Page 1 (Title Page)
**Current Implementation:**
- Basic header with gray background
- Regular text fields for patient info
- DNA helix as separate image element
- Standard text layout

**Reference PDF:**
- Full-page DNA helix background
- Pill-shaped boxes for patient information
- Large title text
- Teal decorative element in top-right
- Professional logo placement at bottom

**Required Changes:**
- Implement pill-shaped boxes using rounded rectangles
- Create full-page background with DNA helix
- Add teal decorative diagonal stripes
- Reposition logos to bottom corners

### 2. Page 2 (Sequencing Results)
**Current Implementation:**
- Basic horizontal bar chart
- Simple phylum distribution
- Standard matplotlib colors

**Reference PDF:**
- Green section headers with white text
- Gradient blue bars for species
- Specific color scheme for phylums
- Reference range indicators as vertical marks
- Two-section layout (species + phylum)

**Required Changes:**
- Implement green header bars
- Custom color gradients for charts
- Add reference range visualization
- Adjust chart positioning and sizing

### 3. Page 3 (Clinical Analysis)
**Current Implementation:**
- Single interpretation section
- Basic text layout

**Reference PDF:**
- Multiple distinct sections with green headers
- Parasite and viral profiles
- OPIS and WAŻNE sections
- Structured negative results display

**Required Changes:**
- Add parasite and viral profile sections
- Implement green section headers consistently
- Create WAŻNE (Important) box styling
- Structure the clinical text better

### 4. Page 4 (Laboratory Analysis)
**Current Implementation:**
- Single biochemical table

**Reference PDF:**
- Three distinct sections (parasites, microscopic, biochemical)
- List format for first two sections
- Red arrows for abnormal values
- "Odchylenie od normy" column

**Required Changes:**
- Add parasite screening section
- Add microscopic analysis section
- Implement red arrow indicators
- Restructure table with Polish headers

### 5. Page 5 (Educational Content)
**Current Implementation:**
- Basic recommendations list

**Reference PDF:**
- Educational question header
- Two-column comparison layout
- Microscope images
- Positive vs Pathogenic microbiome
- Dysbiosis explanation

**Required Changes:**
- Complete redesign to educational format
- Implement two-column layout
- Add microscope images
- Create comparison content
- Add dysbiosis explanation section

## Priority Implementation Order (MVP)

1. **Pill-shaped patient info boxes** (Page 1)
2. **Green section headers** (All pages)
3. **Proper logo positioning** (All pages)
4. **Chart color schemes** (Page 2)
5. **Multiple analysis sections** (Pages 3-4)
6. **Educational page redesign** (Page 5) - Could be Phase 2

## Technical Requirements

1. **Rounded Rectangle Function:**
```python
def draw_rounded_rect(c, x, y, width, height, radius):
    """Draw a rounded rectangle (pill shape)"""
    c.roundRect(x, y, width, height, radius, stroke=1, fill=1)
```

2. **Green Header Function:**
```python
def draw_section_header(c, x, y, width, text):
    """Draw green section header with white text"""
    c.setFillColor(colors.HexColor('#10B981'))
    c.rect(x, y, width, 25, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 10, y + 7, text)
```

3. **Color Updates:**
- Teal: #14B8A6
- Green: #10B981
- Blues: Gradient from #1E3A8A to #3B82F6

4. **Font Sizes:**
- Main title: 24pt
- Section headers: 12pt bold
- Body text: 10pt
- Small labels: 8pt