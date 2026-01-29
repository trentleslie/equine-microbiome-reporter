# Translation Strings for Equine Microbiome Reporter

This file documents all translatable strings used in the report templates.
Translations are defined in `config/translations.yaml` (EN/PL/DE).

**Note:** Clinical assessment, recommendations, and management guidelines are
entered manually by the clinician via manifest CSV — they are NOT auto-generated
and do NOT need translation strings.

---

## Page Titles

| Key | English |
|-----|---------|
| `microbiome_sequencing_results` | Microbiome Sequencing Results |
| `bacterial_species_distribution` | Bacterial Species Distribution |
| `clinical_interpretation` | Clinical Interpretation |
| `summary_management_guidelines` | Summary & Management Guidelines |
| `complete_bacterial_species_list` | Complete Bacterial Species List |

## Subsection Titles

| Key | English |
|-----|---------|
| `phylum_distribution_gut` | Phylum Distribution in Gut Microflora |
| `top_20_species` | Top 20 Bacterial Species by Abundance |
| `clinical_assessment` | Clinical Assessment |
| `key_findings` | Key Findings |
| `clinical_recommendations` | Clinical Recommendations |
| `report_summary` | Report Summary |
| `understanding_dysbiosis_index` | Understanding the Dysbiosis Index |
| `management_guidelines` | Management Guidelines |
| `follow_up_testing` | Follow-up Testing |

## Dysbiosis Labels

| Key | English |
|-----|---------|
| `dysbiosis_index` | Dysbiosis Index |
| `normal_microbiota` | Normal Microbiota |
| `mild_dysbiosis` | Mild Dysbiosis |
| `severe_dysbiosis` | Severe Dysbiosis |
| `normal` | Normal |
| `mild` | Mild |
| `severe` | Severe |

## Review Status

| Key | English |
|-----|---------|
| `clinically_reviewed` | CLINICALLY REVIEWED |
| `pending_review` | PENDING REVIEW |
| `clinical_review_completed` | CLINICAL REVIEW COMPLETED |
| `reviewed_by` | Reviewed by |
| `review_date` | Review date |
| `automated_analysis_pending` | AUTOMATED ANALYSIS - PENDING CLINICAL REVIEW |
| `not_yet_reviewed` | This report has not yet been reviewed by a clinician. |
| `pending_clinical_review` | Pending clinical review |

## Patient Labels

| Key | English |
|-----|---------|
| `owner` | Owner |
| `collected` | Collected |
| `analyzed` | Analyzed |
| `report` | Report |
| `sample` | Sample |

## Table Headers

| Key | English |
|-----|---------|
| `species` | Species |
| `abundance_percent` | Abundance (%) |
| `phylum` | Phylum |
| `dysbiosis_category` | Dysbiosis Category |
| `retest_timeline` | Re-test Timeline |
| `monitoring_focus` | Monitoring Focus |

## Summary Labels

| Key | English |
|-----|---------|
| `category` | Category |
| `dominant_phylum` | Dominant Phylum |
| `total_species_identified` | Total Species Identified |
| `sample_quality` | Sample Quality |
| `sample_quality_adequate` | Adequate |
| `analysis_method` | Analysis Method |
| `analysis_method_value` | Shotgun metagenomic NGS |

## Key Findings Text

| Key | English |
|-----|---------|
| `low_bacillota` | Low Bacillota |
| `low_bacteroidota` | Low Bacteroidota |
| `elevated_pseudomonadota` | Elevated Pseudomonadota |
| `balanced_microbiome` | Balanced Microbiome |
| `bacillota_description` | Associated with reduced fiber fermentation and butyrate production. |
| `bacteroidota_description` | May indicate compromised carbohydrate metabolism. |
| `pseudomonadota_description` | May indicate inflammation or pathogenic overgrowth. |
| `balanced_description` | All major phyla within reference ranges. Optimal conditions for digestive health. |

## Follow-up Table

| Key | English |
|-----|---------|
| `followup_normal_timeline` | 12 months |
| `followup_normal_focus` | Annual health screening |
| `followup_mild_timeline` | 2-3 months |
| `followup_mild_focus` | Response to dietary changes |
| `followup_severe_timeline` | 4-6 weeks |
| `followup_severe_focus` | Treatment efficacy |

## Dysbiosis Explanation

| Key | English |
|-----|---------|
| `di_explanation_intro` | The Dysbiosis Index (DI) quantifies the degree of microbial imbalance in the gut: |
| `di_range_normal` | 0-20: Normal, healthy microbiome |
| `di_range_mild` | 21-50: Mild dysbiosis requiring dietary adjustment |
| `di_range_severe` | >50: Severe dysbiosis requiring intervention |

## Footer & Contact

| Key | English |
|-----|---------|
| `lab_name` | MIMT Genetics Laboratory |
| `page_x_of_y` | Page {current} of {total} |
| `end_of_report` | End of Report |
| `questions_contact` | For questions regarding this report, please contact: |
| `report_generated_using` | Report generated using Next-Gen Gut Profiling (NG-GP) technology |

## Chart Labels

| Key | English |
|-----|---------|
| `percentage` | Percentage (%) |
| `species_title` | MICROBIOTIC PROFILE - Top Species Distribution |
| `phylum_title` | PHYLUM DISTRIBUTION IN GUT MICROFLORA |
| `reference_legend` | Gray bars indicate reference ranges |
| `ref` | Ref |

---
**Total strings: ~80** (reduced from 110 after removing auto-generated clinical text)

*See `config/translations.yaml` for the full translation dictionary with PL/DE columns.*
