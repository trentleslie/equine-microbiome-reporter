# MVP Implementation Plan - Week 1 (Revised)

## Gemini's Key Recommendations

### Keep (Strengths):
- ✅ Dataclasses for type safety
- ✅ Separation of layout/data
- ✅ CSV processing pipeline

### Simplify (MVP Focus):
1. **Combine data models** - Use just `PatientInfo` + `MicrobiomeData` instead of 5+ separate classes
2. **Use Jinja2** - Instead of homegrown template constants
3. **Single template** - One master template for now, not multiple variations
4. **Exact match priority** - Get reference PDF working perfectly first

### Recommended Stack:
- **Data**: 2 simple dataclasses
- **Templates**: Jinja2
- **PDF**: ReportLab (already using)
- **Workflow**: CSV → Dataclasses → Jinja2 → ReportLab

## Simplified MVP Architecture

```python
# 1. Simple Data Models
@dataclass
class PatientInfo:
    name: str
    species: str
    age: str
    sample_number: str
    date_received: str
    date_analyzed: str
    performed_by: str
    requested_by: str

@dataclass
class MicrobiomeData:
    # Core results
    species_list: List[Dict]  # [{species, percentage, phylum}, ...]
    phylum_distribution: Dict[str, float]
    dysbiosis_index: float
    
    # Lab results (simplified)
    parasite_results: List[Dict]
    microscopic_results: List[Dict]
    biochemical_results: List[Dict]
    
    # Interpretations
    clinical_interpretation: str
    recommendations: List[str]

# 2. Jinja2 Template (report_template.html or .j2)
"""
<page1>
  <title>{{ title }}</title>
  <patient>{{ patient.name }}</patient>
  <!-- etc -->
</page1>

<page2>
  {% for species in data.species_list[:15] %}
    <species>{{ species.name }}: {{ species.percentage }}%</species>
  {% endfor %}
</page2>
"""

# 3. Simple Generator
def generate_report(csv_file, patient_info, output_pdf):
    # Process CSV
    data = process_microbiome_data(csv_file)
    
    # Render template
    template = jinja_env.get_template('report_template.j2')
    html = template.render(patient=patient_info, data=data)
    
    # Convert to PDF (using ReportLab or WeasyPrint)
    create_pdf_from_template(html, output_pdf)
```

## Benefits of This Approach

1. **Faster Development**: Jinja2 handles all string formatting/conditionals
2. **Easier Maintenance**: Templates are separate files, easy to edit
3. **Translation Ready**: Just swap template files for different languages
4. **Exact Match Focus**: Can precisely match reference PDF layout
5. **Future Flexibility**: Easy to add new report types later

## Week 1 Action Items

1. **Day 1-2**: 
   - Install Jinja2: `poetry add jinja2`
   - Create simplified dataclasses
   - Set up basic Jinja2 template matching Page 1

2. **Day 3-4**:
   - Complete all 5 pages in Jinja2 template
   - Match exact layout from reference PDF
   - Implement pill-shaped boxes, green headers

3. **Day 5**:
   - Test with real data
   - Polish visual matching
   - Prepare demo for client

## What We're NOT Doing (Save for Later)

- Multiple report type variations
- Complex clinical logic
- Advanced templating features
- Extensibility beyond basic needs

## Next Steps After MVP

- Week 2: Add Polish/Japanese translations (just new template files)
- Week 3: Batch processing
- Week 4: More report variations

This approach delivers exactly what's needed for Week 1 while setting up for future growth.