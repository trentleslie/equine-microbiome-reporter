# Template Content Modules Breakdown

This document breaks down the actual content modules in the clean report templates for review and feedback.

## Report Structure Overview
- **4 pages total** (Pages 2-5 of final report after title page)
- **Consistent header/footer** on all pages
- **Modular content sections** that can be customized

---

## PAGE 1: SEQUENCING RESULTS
**File:** `templates/clean/page1_sequencing.html`

### Header Module (All Pages)
**Variables Used:**
- `patient.name` - Horse/patient name
- `patient.species` - Species (default: "Equine")
- `patient.sample_number` - Sample ID number
- `patient.date_analyzed` - Analysis date
- `report_date` - Report generation date

### 1.1 Dysbiosis Index Card
**Purpose:** Primary health indicator display
**Variables:**
- `data.dysbiosis_index` - Numerical score (0-100+)
- `data.dysbiosis_category` - Status: "normal", "mild", or "severe"

**Content Logic:**
```
If normal (0-20): "Normal Microbiota" (green)
If mild (21-50): "Mild Dysbiosis" (yellow)
If severe (>50): "Severe Dysbiosis" (red)
```

### 1.2 Species Distribution Chart
**Purpose:** Visual representation of bacterial species
**Variables:**
- `charts.species_distribution` - Bar chart image path
- Shows top 20 species by abundance

### 1.3 Dominant Species Table
**Purpose:** Detailed breakdown of top 10 species
**Columns:**
- Species name
- Abundance percentage
- Phylum classification

**Variables:**
- `data.species_list` - Array of species objects
  - `species.species` - Species name
  - `species.percentage` - Abundance %
  - `species.phylum` - Phylum name

---

## PAGE 2: PHYLUM ANALYSIS
**File:** `templates/clean/page2_phylum.html`

### 2.1 Phylum Distribution Chart
**Purpose:** Pie chart of major bacterial phyla
**Variables:**
- `charts.phylum_distribution` - Pie chart image path

### 2.2 Phylum Comparison Chart
**Purpose:** Patient values vs. reference ranges
**Variables:**
- `charts.phylum_comparison` - Comparison chart image path

### 2.3 Phylum Data Table
**Purpose:** Numerical comparison with reference ranges
**Columns:**
- Phylum name
- Patient percentage
- Normal range
- Status (Normal/Abnormal)

**Variables:**
- `data.phylum_distribution` - Dictionary of phylum percentages
- `config.reference_ranges` - Normal ranges for each phylum

**Reference Ranges (hardcoded):**
- Actinomycetota: 0.1-8.0%
- Bacillota: 20.0-70.0%
- Bacteroidota: 4.0-40.0%
- Pseudomonadota: 2.0-35.0%
- Fibrobacterota: 0.1-20.0%

---

## PAGE 3: CLINICAL INTERPRETATION
**File:** `templates/clean/page3_clinical.html`

### 3.1 Clinical Assessment
**Purpose:** Narrative interpretation of results

**Content Templates by Category:**

**NORMAL:**
> "The microbiome analysis reveals a **healthy and balanced** gut microbial community. The dysbiosis index of [X] falls within the normal range (0-20), indicating optimal microbial diversity and composition. The major bacterial phyla are present in appropriate proportions, supporting proper digestive function and immune homeostasis."

**MILD:**
> "The microbiome analysis indicates **mild dysbiosis** with an index of [X]. This suggests a moderate imbalance in the gut microbial community that may benefit from targeted intervention. While not immediately concerning, this imbalance could impact digestive efficiency and immune function if left unaddressed."

**SEVERE:**
> "The microbiome analysis reveals **severe dysbiosis** with an index of [X]. This indicates a significant imbalance in the gut microbial community requiring immediate attention. The disrupted microbial ecology may compromise digestive function, nutrient absorption, and immune responses."

### 3.2 Key Findings
**Purpose:** Highlight specific abnormalities

**Conditional Findings (shown if true):**
- **Low Bacillota** (<20%): "Associated with reduced fiber fermentation and butyrate production"
- **Low Bacteroidota** (<4%): "May indicate compromised carbohydrate metabolism"
- **Elevated Pseudomonadota** (>35%): "May indicate inflammation or pathogenic overgrowth"
- **Balanced Microbiome** (if normal): "All major phyla within reference ranges"

### 3.3 Clinical Recommendations
**Purpose:** Actionable treatment steps

**NORMAL Recommendations:**
- Maintain current feeding regimen and management practices
- Continue regular monitoring with annual microbiome assessments
- Ensure consistent access to quality forage and clean water

**MILD Recommendations:**
- Increase dietary fiber through additional hay supplementation
- Consider probiotic supplementation (Lactobacillus/Bifidobacterium strains)
- Reduce grain intake if exceeding 0.5% body weight per feeding
- Re-evaluate microbiome in 8-12 weeks after intervention

**SEVERE Recommendations:**
- Immediate dietary modification: Increase forage to 2% body weight daily minimum
- Implement therapeutic probiotic protocol with veterinary guidance
- Eliminate or significantly reduce concentrate feeds temporarily
- Consider prebiotic supplementation (FOS, MOS, or psyllium)
- Re-evaluate microbiome in 4-6 weeks to assess response
- Screen for underlying gastrointestinal pathology if dysbiosis persists

---

## PAGE 4: SUMMARY & GUIDELINES
**File:** `templates/clean/page4_summary.html`

### 4.1 Report Summary Box
**Purpose:** Quick reference of key metrics
**Content:**
- Dysbiosis Index value
- Category (Normal/Mild/Severe)
- Dominant Phylum
- Total Species Identified
- Sample Quality (always "Adequate")
- Analysis Method (always "16S rRNA NGS")

### 4.2 Understanding Dysbiosis Index
**Purpose:** Educational reference
**Static Content:**
- 0-20: Normal, healthy microbiome
- 21-50: Mild dysbiosis requiring dietary adjustment
- >50: Severe dysbiosis requiring intervention

### 4.3 Management Guidelines
**Purpose:** Detailed care instructions

**NORMAL Management:**
- Consistent feeding schedule (2-3 times daily)
- Continuous access to forage (pasture or hay)
- Gradual feed changes over 10-14 days
- Regular dental care and parasite control
- Minimize stress and maintain exercise routine

**MILD Management:**
- Increase forage intake to at least 1.5-2% body weight
- Reduce grain meals to <0.5% body weight per feeding
- Add probiotic supplement (10^9 CFU daily)
- Consider prebiotic fiber sources (beet pulp, psyllium)
- Ensure adequate water intake (30-50L daily)

**SEVERE Management:**
- Immediate dietary restructuring under veterinary guidance
- Maximize forage, minimize concentrates
- Therapeutic probiotic protocol (10^10 CFU daily)
- Consider fecal microbiota transplantation if available
- Monitor for signs of colic or laminitis
- Re-test in 4-6 weeks to assess improvement

### 4.4 Follow-up Testing Table
**Purpose:** Re-testing schedule

| Category | Re-test Timeline | Monitoring Focus |
|----------|-----------------|------------------|
| Normal | 12 months | Annual health screening |
| Mild | 2-3 months | Response to dietary changes |
| Severe | 4-6 weeks | Treatment efficacy |

### 4.5 Contact Information
**Static Content:**
- MEMT Genetics Laboratory
- Email: lab@memtgenetics.com
- Phone: +48 XXX XXX XXX
- Technology: Next-Gen Gut Profiling (NG-GP)

---

## Template Variables Summary

### Patient Information
- `patient.name` - Horse name
- `patient.species` - Species (default: "Equine")
- `patient.sample_number` - Sample ID
- `patient.date_analyzed` - Analysis date

### Microbiome Data
- `data.dysbiosis_index` - Numerical score
- `data.dysbiosis_category` - "normal", "mild", or "severe"
- `data.species_list` - Array of species with percentages
- `data.phylum_distribution` - Dictionary of phylum percentages

### Charts (Generated Images)
- `charts.species_distribution` - Top 20 species bar chart
- `charts.phylum_distribution` - Phylum pie chart
- `charts.phylum_comparison` - Reference range comparison

### Configuration
- `config.reference_ranges` - Normal ranges for each phylum
- `report_date` - Report generation date

---

## Customization Points for Review

1. **Clinical Text Templates** - Are the interpretations appropriate for each severity level?
2. **Recommendation Lists** - Are the treatment recommendations aligned with current veterinary practice?
3. **Reference Ranges** - Do the phylum ranges match your clinical experience?
4. **Management Guidelines** - Are the feeding/supplement recommendations appropriate?
5. **Follow-up Schedules** - Are the re-testing timelines practical?
6. **Contact Information** - Update with actual HippoVet+ details

## Language Considerations

Currently all text is in English. For Polish translation, each text module would need:
- Clinical terminology translation
- Measurement unit localization (if needed)
- Date format adjustments
- Contact information updates