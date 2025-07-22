# Reference PDF Specification - HippoVet+ Laboratory Report

## Overall Design Elements

### Color Palette
- Primary Blue: #1E3A8A (Dark blue for headers and titles)
- Teal Accent: #14B8A6 (Top right corner decoration, some charts)
- Green Headers: #10B981 (Section headers)
- Light Gray Background: #F3F4F6 (Header sections)
- Text: #1F2937 (Dark gray for body text)

### Typography
- Main Title: Bold, sans-serif, ~24pt
- Section Headers: Bold, white text on green background, ~14pt
- Body Text: Regular, ~10pt
- Data Labels: Regular, ~9pt

### Logo Placement
- Bottom left: HippoVet logo (all pages)
- Bottom right: MEMT Laboratory logo (all pages)
- Page numbers: Center bottom (e.g., "2/5")

## Page-by-Page Specifications

### Page 1: Title Page
**Background:** Full-page DNA helix image with teal overlay effect

**Layout:**
```
┌─────────────────────────────────────┐
│ KOMPLEKSOWE                    ╱╱╱╱╱│ (Teal decoration)
│ BADANIE                       ╱╱╱╱╱╱│
│ KAŁU                         ╱╱╱╱╱╱╱│
│                                     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │Montana  │ │Koń,20lat│ │  506    ││ (Patient info pills)
│ └─────────┘ └─────────┘ └─────────┘│
│                                     │
│ ┌──────────┐ ┌──────────┐          │
│ │07.05.2025│ │12.05.2025│          │ (Date pills)
│ └──────────┘ └──────────┘          │
│                                     │
│ ┌──────────┐ ┌──────────┐          │
│ │J.Kończak │ │A.Matusiak│          │ (Personnel pills)
│ └──────────┘ └──────────┘          │
│                                     │
│ [DNA HELIX BACKGROUND IMAGE]        │
│                                     │
│ HippoVet                    MEMT    │
└─────────────────────────────────────┘
```

**Pill Styling:**
- White background with subtle shadow
- Rounded corners (border-radius: ~20px)
- Padding: ~10px horizontal, ~5px vertical
- Font: Regular, dark gray text

### Page 2: Sequencing Results
**Header Section:**
- Green bar with "WYNIK SEKWENCJONOWANIA"
- Subtitle: "PROFIL MIKROBIOTYCZNY"

**Species Distribution Chart:**
- Horizontal bar chart
- Top 15-20 species
- Bars in gradient from dark to light blue
- Species names on left, percentages on right
- Values displayed at end of each bar

**Phylum Distribution:**
- Bottom section with 4 phylum bars
- Reference ranges shown as vertical marks
- Legend showing percentage ranges
- Color coding: Actinomycetota (teal), Bacillota (green), Bacteroidota (blue), Pseudomonadota (teal)

### Page 3: Clinical Analysis
**Sections:**
1. Dysbiosis Index (DI)
   - Value displayed prominently
   - Interpretation text below

2. Green header sections:
   - PROFIL JEDNOKOMÓRKOWYCH PASOŻYTÓW
   - PROFIL WIRUSOWY
   - Each with negative results

3. OPIS section:
   - Multi-paragraph clinical interpretation
   - Justified text alignment

4. WAŻNE box:
   - Important notes section
   - May have different background or border

### Page 4: Laboratory Analysis
**Three main sections with green headers:**

1. BADANIE OBECNOŚCI PASOŻYTÓW
   - List format with species names
   - "Nie zaobserwowano" (Not observed) results
   - Red arrow indicators for abnormal results

2. BADANIE MIKROSKOPOWE
   - Similar list format for microscopic findings

3. BADANIE BIOCHEMICZNE
   - Table-like format
   - Parameters, results, and reference ranges
   - "Odchylenie od normy" (Deviation from normal) column

### Page 5: Educational Content
**Layout:** Two-column comparison

**Header:** Question about genetic testing purpose

**Two columns:**
1. Pozytywny mikrobiom jelitowy (Positive)
   - Green header
   - Bullet points with beneficial bacteria
   - Circular microscope image

2. Patogenny mikrobiom jelitowy (Pathogenic)
   - Green header
   - List of pathogenic bacteria
   - Circular microscope image

**Bottom section:**
- "Czym jest dysbioza jelit?" explanation
- Educational text about dysbiosis

## Key Implementation Notes

1. **Pill-shaped elements** for patient data (not rectangular boxes)
2. **Green section headers** with white text
3. **Consistent logo placement** on every page
4. **Page numbering** in format "X/5"
5. **Teal decorative elements** on title page
6. **Professional spacing** and margins throughout
7. **Charts use specific color scheme** (not generic matplotlib colors)
8. **Red arrows** (↑) to indicate abnormal values
9. **Two-column layout** where specified
10. **Microscope images** on educational page