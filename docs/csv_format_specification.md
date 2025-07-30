# CSV Format Specification for Microbiome Data

## Overview
This document specifies the exact CSV format required for the Equine Microbiome Reporter system. The system supports two CSV formats:
1. **Full Analysis Format** - Contains all barcode columns and complete taxonomic data
2. **Simplified Format** - Contains single barcode column with essential taxonomic data

## Required Columns

### Full Analysis Format (Primary Reference: `data/25_04_23 bact.csv`)

#### Essential Columns
- `species` - Scientific name of the bacterial species (e.g., "Streptomyces albidoflavus")
- `barcode[N]` - Multiple columns containing abundance counts for each barcode (e.g., barcode45, barcode46, etc.)
- `phylum` - Taxonomic phylum classification (must match reference ranges exactly)
- `genus` - Taxonomic genus classification
- `family` - Taxonomic family classification
- `class` - Taxonomic class classification
- `order` - Taxonomic order classification

#### Optional Columns (if present, will be used)
- `total` - Sum of all barcode counts
- `superkingdom` - Always "Bacteria"
- `kingdom` - Typically "Bacteria_none"
- `tax` - Full taxonomic lineage

### Simplified Format (e.g., `data/sample_1.csv`)

#### Required Columns
- `species` - Scientific name of the bacterial species
- `barcode[N]` - Single barcode column with abundance counts (e.g., barcode59)
- `phylum` - Taxonomic phylum classification
- `genus` - Taxonomic genus classification
- `family` - Taxonomic family classification
- `class` - Taxonomic class classification
- `order` - Taxonomic order classification

## Data Requirements

### Column Names
- **Case Sensitivity**: Column names are case-sensitive in the CSVProcessor
  - The processor looks for: 'Species', 'Genus', 'Phylum' (capitalized)
  - CSV files may use lowercase: 'species', 'genus', 'phylum'
  - The processor uses `.get()` method to handle missing keys gracefully

### Phylum Names
Must match the reference ranges exactly:
- `Actinomycetota` (0.1-8.0%)
- `Bacillota` (20.0-70.0%)
- `Bacteroidota` (4.0-40.0%)
- `Pseudomonadota` (2.0-35.0%)
- `Fibrobacterota` (0.1-5.0%)

### Species Names
- Must be in scientific nomenclature format
- Can include strain identifiers (e.g., "Arthrobacter sp. FB24")
- No special characters except spaces, periods, and hyphens

### Barcode Columns
- Named as `barcode` followed by a number (e.g., barcode45, barcode59)
- Contains integer values representing abundance counts
- Zero values are allowed and will be filtered during processing
- At least one barcode column must have non-zero values

### Data Types
- `species`: String
- `barcode[N]`: Integer (abundance counts)
- `phylum`, `genus`, `family`, `class`, `order`: String (taxonomic classifications)
- `total`: Integer (if present)

## Validation Rules

### Required Validations
1. **File Structure**
   - Must be valid UTF-8 encoded CSV
   - Must have header row with column names
   - No empty rows between data

2. **Essential Columns**
   - Must contain at least: species, one barcode column, phylum, genus
   - Barcode column must match pattern: `barcode\d+`

3. **Data Integrity**
   - Barcode values must be non-negative integers
   - At least 10 species recommended for meaningful analysis
   - Total count (sum of barcode column) must be > 0

4. **Taxonomic Consistency**
   - Phylum names must be consistent throughout the file
   - Each species should have complete taxonomic classification

### Processing Logic
1. CSVProcessor reads the specified barcode column
2. Filters out species with zero counts
3. Calculates percentages based on total count
4. Aggregates by phylum for dysbiosis calculation
5. Sorts species by abundance (descending)

## Example Formats

### Full Analysis Format
```csv
species,barcode45,barcode46,barcode47,barcode48,barcode50,barcode51,barcode52,barcode53,barcode54,barcode55,barcode56,barcode58,barcode59,barcode60,barcode61,barcode62,barcode63,barcode64,barcode66,barcode67,barcode68,barcode69,barcode70,barcode71,barcode72,barcode74,barcode75,barcode76,barcode77,barcode78,total,superkingdom,kingdom,phylum,class,order,family,genus,tax
Streptomyces albidoflavus,0,0,0,0,0,0,0,0,0,0,0,19,27,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,46,Bacteria,Bacteria_none,Actinomycetota,Actinomycetes,Kitasatosporales,Streptomycetaceae,Streptomyces,Bacteria,Bacteria_none,Actinomycetota,Actinomycetes,Kitasatosporales,Streptomycetaceae,Streptomyces,Streptomyces albidoflavus
Lysinibacillus sp. 2017,26,0,38,0,14,11,43,0,0,53,31,6,14,0,6,6,15,13,51,0,6,0,51,44,10,0,0,6,0,14,458,Bacteria,Bacteria_none,Bacillota,Bacilli,Bacillales,Bacillaceae,Lysinibacillus,Bacteria,Bacteria_none,Bacillota,Bacilli,Bacillales,Bacillaceae,Lysinibacillus,Lysinibacillus sp. 2017
```

### Simplified Format
```csv
species,barcode59,phylum,genus,family,class,order
Brachybacterium sp. Z12,2,Actinomycetota,Brachybacterium,Dermabacteraceae,Actinomycetes,Micrococcales
Lysinibacillus sp. 2017,43,Bacillota,Lysinibacillus,Bacillaceae,Bacilli,Bacillales
Kurthia zopfii,9,Bacillota,Kurthia,Planococcaceae,Bacilli,Bacillales
```

## Common Issues and Solutions

### Issue: Column Name Case Mismatch
- **Problem**: CSVProcessor expects capitalized column names but CSV has lowercase
- **Solution**: The processor uses `.get()` method with fallback, so both cases work

### Issue: Missing Phylum in Reference Ranges
- **Problem**: CSV contains phyla not in the reference ranges
- **Solution**: These phyla are included in analysis but not used for dysbiosis calculation

### Issue: Zero Abundance Species
- **Problem**: Species with zero counts in selected barcode
- **Solution**: Automatically filtered out during processing

### Issue: Special Characters in Species Names
- **Problem**: Non-standard characters in species names
- **Solution**: Use standard scientific nomenclature only

## FASTQ to CSV Conversion Requirements

When converting FASTQ files to CSV format, ensure:
1. Taxonomic classification is performed to obtain phylum, genus, family, class, order
2. Abundance counts are properly aggregated by species
3. Column names match exactly as specified above
4. Phylum names are standardized to match reference ranges
5. Output includes all required columns in correct order

## Testing Checklist

- [ ] CSV loads successfully with pandas
- [ ] All required columns present
- [ ] Barcode column contains valid integers
- [ ] At least 10 species with non-zero counts
- [ ] Phylum names match reference ranges
- [ ] No empty rows or malformed data
- [ ] UTF-8 encoding confirmed
- [ ] CSVProcessor successfully processes file
- [ ] Dysbiosis index calculates correctly
- [ ] PDF report generates without errors