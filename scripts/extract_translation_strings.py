#!/usr/bin/env python3
"""
Translation String Extractor for Equine Microbiome Reporter

Extracts all translatable strings from HTML templates and code,
generating a markdown file for translators and a translations.yaml template.

Usage:
    python scripts/extract_translation_strings.py --output-md config/translation_strings.md
    python scripts/extract_translation_strings.py --output-yaml config/translations.yaml
    python scripts/extract_translation_strings.py  # outputs both files
"""

import argparse
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set
from collections import OrderedDict


# Base directory for templates
TEMPLATES_DIR = Path(__file__).parent.parent / 'templates' / 'clean'

# Known translatable strings categorized by section
# These are extracted from manual analysis of templates
TRANSLATION_STRINGS = OrderedDict([
    # Page titles and section headers
    ('titles', OrderedDict([
        ('microbiome_sequencing_results', 'Microbiome Sequencing Results'),
        ('bacterial_species_distribution', 'Bacterial Species Distribution'),
        ('clinical_interpretation', 'Clinical Interpretation'),
        ('summary_management_guidelines', 'Summary & Management Guidelines'),
        ('complete_bacterial_species_list', 'Complete Bacterial Species List'),
    ])),

    # Subsection headers
    ('subsections', OrderedDict([
        ('phylum_distribution_gut', 'Phylum Distribution in Gut Microflora'),
        ('top_20_species', 'Top 20 Bacterial Species by Abundance'),
        ('clinical_assessment', 'Clinical Assessment'),
        ('key_findings', 'Key Findings'),
        ('clinical_recommendations', 'Clinical Recommendations'),
        ('report_summary', 'Report Summary'),
        ('understanding_dysbiosis_index', 'Understanding the Dysbiosis Index'),
        ('management_guidelines', 'Management Guidelines'),
        ('maintaining_healthy_microbiome', 'Maintaining a Healthy Microbiome'),
        ('correcting_mild_dysbiosis', 'Correcting Mild Dysbiosis'),
        ('managing_severe_dysbiosis', 'Managing Severe Dysbiosis'),
        ('follow_up_testing', 'Follow-up Testing'),
    ])),

    # Dysbiosis categories and labels
    ('dysbiosis', OrderedDict([
        ('dysbiosis_index', 'Dysbiosis Index'),
        ('normal_microbiota', 'Normal Microbiota'),
        ('mild_dysbiosis', 'Mild Dysbiosis'),
        ('severe_dysbiosis', 'Severe Dysbiosis'),
        ('normal', 'Normal'),
        ('mild', 'Mild'),
        ('severe', 'Severe'),
    ])),

    # Clinical review status
    ('review_status', OrderedDict([
        ('clinically_reviewed', 'CLINICALLY REVIEWED'),
        ('pending_review', 'PENDING REVIEW'),
        ('clinical_review_completed', 'CLINICAL REVIEW COMPLETED'),
        ('reviewed_by', 'Reviewed by'),
        ('review_date', 'Review date'),
        ('automated_analysis_pending', 'AUTOMATED ANALYSIS - PENDING CLINICAL REVIEW'),
        ('not_yet_reviewed', 'This report has not yet been reviewed by a clinician.'),
    ])),

    # Patient info labels
    ('patient_labels', OrderedDict([
        ('owner', 'Owner'),
        ('collected', 'Collected'),
        ('analyzed', 'Analyzed'),
        ('report', 'Report'),
        ('sample', 'Sample'),
    ])),

    # Table headers
    ('table_headers', OrderedDict([
        ('species', 'Species'),
        ('abundance_percent', 'Abundance (%)'),
        ('phylum', 'Phylum'),
        ('dysbiosis_category', 'Dysbiosis Category'),
        ('retest_timeline', 'Re-test Timeline'),
        ('monitoring_focus', 'Monitoring Focus'),
    ])),

    # Summary labels
    ('summary_labels', OrderedDict([
        ('category', 'Category'),
        ('dominant_phylum', 'Dominant Phylum'),
        ('total_species_identified', 'Total Species Identified'),
        ('sample_quality', 'Sample Quality'),
        ('sample_quality_adequate', 'Adequate'),
        ('analysis_method', 'Analysis Method'),
        ('analysis_method_value', 'Shotgun metagenomic NGS'),
    ])),

    # Key findings text
    ('key_findings_text', OrderedDict([
        ('low_bacillota', 'Low Bacillota'),
        ('low_bacteroidota', 'Low Bacteroidota'),
        ('elevated_pseudomonadota', 'Elevated Pseudomonadota'),
        ('balanced_microbiome', 'Balanced Microbiome'),
        ('bacillota_description', 'Associated with reduced fiber fermentation and butyrate production.'),
        ('bacteroidota_description', 'May indicate compromised carbohydrate metabolism.'),
        ('pseudomonadota_description', 'May indicate inflammation or pathogenic overgrowth.'),
        ('balanced_description', 'All major phyla within reference ranges. Optimal conditions for digestive health.'),
    ])),

    # Clinical assessment text (auto-generated)
    ('clinical_assessment_text', OrderedDict([
        ('healthy_balanced', 'healthy and balanced'),
        ('assessment_normal', 'The microbiome analysis reveals a healthy and balanced gut microbial community. The dysbiosis index of {di} falls within the normal range (0-20), indicating optimal microbial diversity and composition. The major bacterial phyla are present in appropriate proportions, supporting proper digestive function and immune homeostasis.'),
        ('assessment_mild', 'The microbiome analysis indicates mild dysbiosis with an index of {di}. This suggests a moderate imbalance in the gut microbial community that may benefit from targeted intervention. While not immediately concerning, this imbalance could impact digestive efficiency and immune function if left unaddressed.'),
        ('assessment_severe', 'The microbiome analysis reveals severe dysbiosis with an index of {di}. This indicates a significant imbalance in the gut microbial community requiring immediate attention. The disrupted microbial ecology may compromise digestive function, nutrient absorption, and immune responses.'),
    ])),

    # Recommendations (auto-generated)
    ('recommendations_normal', OrderedDict([
        ('rec_normal_1', 'Maintain current feeding regimen and management practices'),
        ('rec_normal_2', 'Continue regular monitoring with annual microbiome assessments'),
        ('rec_normal_3', 'Ensure consistent access to quality forage and clean water'),
    ])),

    ('recommendations_mild', OrderedDict([
        ('rec_mild_1', 'Increase dietary fiber through additional hay supplementation'),
        ('rec_mild_2', 'Consider probiotic supplementation (Lactobacillus/Bifidobacterium strains)'),
        ('rec_mild_3', 'Reduce grain intake if exceeding 0.5% body weight per feeding'),
        ('rec_mild_4', 'Re-evaluate microbiome in 8-12 weeks after intervention'),
    ])),

    ('recommendations_severe', OrderedDict([
        ('rec_severe_1', 'Immediate dietary modification: Increase forage to 2% body weight daily minimum'),
        ('rec_severe_2', 'Implement therapeutic probiotic protocol with veterinary guidance'),
        ('rec_severe_3', 'Eliminate or significantly reduce concentrate feeds temporarily'),
        ('rec_severe_4', 'Consider prebiotic supplementation (FOS, MOS, or psyllium)'),
        ('rec_severe_5', 'Re-evaluate microbiome in 4-6 weeks to assess response'),
        ('rec_severe_6', 'Screen for underlying gastrointestinal pathology if dysbiosis persists'),
    ])),

    # Management guidelines
    ('guidelines_normal', OrderedDict([
        ('guide_normal_1', 'Consistent feeding schedule (2-3 times daily)'),
        ('guide_normal_2', 'Continuous access to forage (pasture or hay)'),
        ('guide_normal_3', 'Gradual feed changes over 10-14 days'),
        ('guide_normal_4', 'Regular dental care and parasite control'),
        ('guide_normal_5', 'Minimize stress and maintain exercise routine'),
    ])),

    ('guidelines_mild', OrderedDict([
        ('guide_mild_1', 'Increase forage intake to at least 1.5-2% body weight'),
        ('guide_mild_2', 'Reduce grain meals to <0.5% body weight per feeding'),
        ('guide_mild_3', 'Add probiotic supplement (10^9 CFU daily)'),
        ('guide_mild_4', 'Consider prebiotic fiber sources (beet pulp, psyllium)'),
        ('guide_mild_5', 'Ensure adequate water intake (30-50L daily)'),
    ])),

    ('guidelines_severe', OrderedDict([
        ('guide_severe_1', 'Immediate dietary restructuring under veterinary guidance'),
        ('guide_severe_2', 'Maximize forage, minimize concentrates'),
        ('guide_severe_3', 'Therapeutic probiotic protocol (10^10 CFU daily)'),
        ('guide_severe_4', 'Consider fecal microbiota transplantation if available'),
        ('guide_severe_5', 'Monitor for signs of colic or laminitis'),
        ('guide_severe_6', 'Re-test in 4-6 weeks to assess improvement'),
    ])),

    # Follow-up table
    ('followup', OrderedDict([
        ('followup_normal_timeline', '12 months'),
        ('followup_normal_focus', 'Annual health screening'),
        ('followup_mild_timeline', '2-3 months'),
        ('followup_mild_focus', 'Response to dietary changes'),
        ('followup_severe_timeline', '4-6 weeks'),
        ('followup_severe_focus', 'Treatment efficacy'),
    ])),

    # Dysbiosis index explanation
    ('dysbiosis_explanation', OrderedDict([
        ('di_explanation_intro', 'The Dysbiosis Index (DI) quantifies the degree of microbial imbalance in the gut:'),
        ('di_range_normal', '0-20: Normal, healthy microbiome'),
        ('di_range_mild', '21-50: Mild dysbiosis requiring dietary adjustment'),
        ('di_range_severe', '>50: Severe dysbiosis requiring intervention'),
    ])),

    # Footer
    ('footer', OrderedDict([
        ('lab_name', 'MIMT Genetics Laboratory'),
        ('page_x_of_y', 'Page {current} of {total}'),
        ('end_of_report', 'End of Report'),
    ])),

    # Contact info
    ('contact', OrderedDict([
        ('questions_contact', 'For questions regarding this report, please contact:'),
        ('report_generated_using', 'Report generated using Next-Gen Gut Profiling (NG-GP) technology'),
    ])),

    # Chart labels (from chart_generator.py)
    ('chart_labels', OrderedDict([
        ('percentage', 'Percentage (%)'),
        ('species_title', 'MICROBIOTIC PROFILE - Top Species Distribution'),
        ('phylum_title', 'PHYLUM DISTRIBUTION IN GUT MICROFLORA'),
        ('reference_legend', 'Gray bars indicate reference ranges'),
        ('ref', 'Ref'),
    ])),
])


def generate_markdown(output_path: Path):
    """Generate markdown file with all translation strings for translators."""

    lines = [
        '# Translation Strings for Equine Microbiome Reporter',
        '',
        'This file contains all translatable strings extracted from HTML templates and code.',
        'Please provide translations for Polish (PL) and German (DE) in the table below.',
        '',
        '**Instructions:**',
        '1. Fill in the Polish and German columns',
        '2. Keep placeholders like `{di}`, `{current}`, `{total}` unchanged',
        '3. Do NOT translate Latin scientific terms (species names, phylum names)',
        '4. Return completed file for integration',
        '',
        '---',
        '',
    ]

    total_strings = 0

    for category, strings in TRANSLATION_STRINGS.items():
        category_title = category.replace('_', ' ').title()
        lines.append(f'## {category_title}')
        lines.append('')
        lines.append('| Key | English | Polish | German |')
        lines.append('|-----|---------|--------|--------|')

        for key, value in strings.items():
            # Escape pipe characters in values
            escaped_value = value.replace('|', '\\|')
            lines.append(f'| `{key}` | {escaped_value} |  |  |')
            total_strings += 1

        lines.append('')

    lines.append('---')
    lines.append(f'**Total strings: {total_strings}**')
    lines.append('')
    lines.append('*Generated by `scripts/extract_translation_strings.py`*')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Generated markdown file: {output_path}")
    print(f"Total strings: {total_strings}")


def generate_yaml(output_path: Path):
    """Generate YAML file with translation dictionary structure."""

    # Build the translation structure
    translations = OrderedDict()

    # English (complete)
    en = OrderedDict()
    for category, strings in TRANSLATION_STRINGS.items():
        for key, value in strings.items():
            en[key] = value
    translations['en'] = dict(en)

    # Polish (placeholders)
    pl = OrderedDict()
    for category, strings in TRANSLATION_STRINGS.items():
        for key, value in strings.items():
            pl[key] = f"[PL] {value}"  # Placeholder for Gosia to fill
    translations['pl'] = dict(pl)

    # German (placeholders)
    de = OrderedDict()
    for category, strings in TRANSLATION_STRINGS.items():
        for key, value in strings.items():
            de[key] = f"[DE] {value}"  # Placeholder for Gosia to fill
    translations['de'] = dict(de)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# Fixed Translation Dictionary for Equine Microbiome Reporter\n')
        f.write('# Languages: English (en), Polish (pl), German (de)\n')
        f.write('#\n')
        f.write('# Instructions:\n')
        f.write('# 1. Replace [PL] and [DE] placeholders with actual translations\n')
        f.write('# 2. Keep placeholders like {di}, {current}, {total} unchanged\n')
        f.write('# 3. Do NOT translate Latin scientific terms\n')
        f.write('#\n\n')
        yaml.dump(dict(translations), f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Generated YAML file: {output_path}")
    print(f"Languages: en, pl, de")
    print(f"Strings per language: {len(en)}")


def count_strings():
    """Count total unique strings."""
    total = 0
    for category, strings in TRANSLATION_STRINGS.items():
        total += len(strings)
    return total


def main():
    parser = argparse.ArgumentParser(
        description='Extract translation strings from templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--output-md', default='config/translation_strings.md',
                        help='Output markdown file path (default: config/translation_strings.md)')
    parser.add_argument('--output-yaml', default='config/translations.yaml',
                        help='Output YAML file path (default: config/translations.yaml)')
    parser.add_argument('--md-only', action='store_true',
                        help='Only generate markdown file')
    parser.add_argument('--yaml-only', action='store_true',
                        help='Only generate YAML file')
    parser.add_argument('--count', action='store_true',
                        help='Only count strings')

    args = parser.parse_args()

    if args.count:
        print(f"Total translation strings: {count_strings()}")
        return

    base_dir = Path(__file__).parent.parent

    if args.md_only:
        generate_markdown(base_dir / args.output_md)
    elif args.yaml_only:
        generate_yaml(base_dir / args.output_yaml)
    else:
        generate_markdown(base_dir / args.output_md)
        generate_yaml(base_dir / args.output_yaml)
        print("\nGenerated both files. Send translation_strings.md to Gosia for translations.")


if __name__ == '__main__':
    main()
