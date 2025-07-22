"""
Report Templates and Content Structure
Separates static template content from dynamic data
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


# Template content organized by page and section
class ReportContent:
    """Organized template content for the entire report"""
    
    # Page 1 - Title Page
    PAGE_1 = {
        'title': 'COMPREHENSIVE FECAL EXAMINATION',
        'fields': {
            'patient_name': {'label': 'Patient Name:', 'pill': True},
            'species_age': {'label': 'Species and Age:', 'pill': True},
            'sample_number': {'label': 'Examination Number:', 'pill': True},
            'date_received': {'label': 'Date Material Received:', 'pill': True},
            'date_analyzed': {'label': 'Date of Analysis:', 'pill': True},
            'performed_by': {'label': 'Performed by:', 'pill': True},
            'requested_by': {'label': 'Requested by:', 'pill': True},
        }
    }
    
    # Page 2 - Sequencing Results
    PAGE_2 = {
        'header': 'SEQUENCING RESULTS',
        'sections': {
            'microbiotic_profile': {
                'title': 'MICROBIOTIC PROFILE',
                'chart_title': 'Bacterial Species Distribution',
                'chart_type': 'horizontal_bar',
                'data_source': 'species_list',
            },
            'phylum_distribution': {
                'title': 'Phylum Distribution in Gut Microflora',
                'chart_type': 'vertical_bar_with_reference',
                'data_source': 'phylum_list',
                'reference_note': 'Reference Range',
                'scale_note': 'Scale: 0-5 normobiotic; 20 slight dysbiosis; 21-50 moderate; >50 severe dysbiosis microbiota'
            }
        }
    }
    
    # Page 3 - Clinical Analysis
    PAGE_3 = {
        'sections': [
            {
                'id': 'dysbiosis_index',
                'title': 'Dysbiosis Index (DI): {value}',
                'content_type': 'dynamic_text',
                'data_field': 'dysbiosis_description'
            },
            {
                'id': 'parasite_profile',
                'title': 'UNICELLULAR PARASITE PROFILE',
                'content_type': 'static_text',
                'data_field': 'parasite_profile'
            },
            {
                'id': 'viral_profile', 
                'title': 'VIRAL PROFILE',
                'content_type': 'static_text',
                'data_field': 'viral_profile'
            },
            {
                'id': 'description',
                'title': 'DESCRIPTION',
                'content_type': 'dynamic_text',
                'data_field': 'main_description'
            },
            {
                'id': 'important',
                'title': 'IMPORTANT',
                'content_type': 'static_text',
                'data_field': 'important_note'
            }
        ]
    }
    
    # Page 4 - Laboratory Analysis
    PAGE_4 = {
        'sections': [
            {
                'id': 'parasite_screening',
                'title': 'PARASITE SCREENING',
                'subtitle': 'Deviation from normal',
                'content_type': 'list',
                'data_source': 'parasite_results',
                'format': '{name}: {result}',
                'show_abnormal': True
            },
            {
                'id': 'microscopic_exam',
                'title': 'MICROSCOPIC EXAMINATION',
                'subtitle': 'Deviation from normal',
                'content_type': 'list',
                'data_source': 'microscopic_results',
                'format': '{parameter}: {result}',
                'show_abnormal': True
            },
            {
                'id': 'biochemical_exam',
                'title': 'BIOCHEMICAL EXAMINATION',
                'content_type': 'table',
                'data_source': 'biochemical_results',
                'columns': ['Parameter', 'Result', 'Reference Range', 'Status'],
                'show_abnormal': True
            }
        ]
    }
    
    # Page 5 - Educational Content
    PAGE_5 = {
        'header': 'What is the purpose of genetic examination of gut microflora?',
        'intro': """Genetic examination of gut microflora is performed for comprehensive analysis of bacterial flora of 
the digestive tract, identification of dysbiosis disorders, and assessment of their impact on the 
animal's health...""",
        'two_column': {
            'left': {
                'title': 'Positive Gut Microbiome',
                'description': 'Positive bacteria supporting digestion...',
                'examples': [
                    'Faecalibacterium spp.',
                    'Fusicatenifer spp.',
                    'Bifidobacterium spp.',
                    'Blautia spp.',
                    'Ruminococcus hominins',
                    'Subdoligranulum spp.',
                    'Eubacterium spp.'
                ]
            },
            'right': {
                'title': 'Pathogenic Gut Microbiome',
                'description': 'Excess of pathogenic microorganisms...',
                'examples': [
                    'Clostridium perfringens',
                    'Escherichia coli',
                    'Campylobacter spp.',
                    'Salmonella spp.',
                    'Staphylococcus aureus',
                    'Listeria monocytogenes',
                    'Staphylococcus pseudintermedius'
                ]
            }
        },
        'dysbiosis_section': {
            'title': 'What is Gut Dysbiosis?',
            'content': 'Gut microbiome imbalance among positive and pathogenic microorganisms...'
        }
    }


# Clinical interpretation templates based on dysbiosis levels
CLINICAL_INTERPRETATIONS = {
    'normal': {
        'dysbiosis_text': 'Normal microbiota (healthy). Lack of dysbiosis signs; gut microflora is balanced with minor deviations.',
        'main_description': """Molecular examination revealed gut microflora properly balanced with minor deviations. 
The bacterial composition falls within expected reference ranges for equine gut microbiota. 
No genetic material from unicellular parasites or viruses was identified.""",
        'recommendations': [
            'Maintain current diet and feeding schedule',
            'Continue regular monitoring with annual check-ups',
            'Ensure access to fresh water and high-quality forage'
        ]
    },
    'mild': {
        'dysbiosis_text': 'Mild dysbiosis detected. Moderate imbalance in gut microflora composition requiring monitoring.',
        'main_description': """Molecular examination revealed mild dysbiosis with moderate deviations from normal microflora. 
Some bacterial populations show imbalanced proportions that may impact digestive efficiency. 
Dietary adjustments and probiotic supplementation may be beneficial.""",
        'recommendations': [
            'Consider probiotic supplementation for 4-6 weeks',
            'Increase dietary fiber content',
            'Reduce concentrated feed portions',
            'Schedule follow-up analysis in 3 months',
            'Monitor stool consistency and appetite'
        ]
    },
    'severe': {
        'dysbiosis_text': 'Severe dysbiosis detected. Significant imbalance in gut microflora requiring intervention.',
        'main_description': """Molecular examination revealed severe dysbiosis with significant deviations from normal microflora. 
Multiple bacterial populations show substantial imbalances that likely impact digestive health and overall wellbeing. 
Immediate veterinary intervention is recommended.""",
        'recommendations': [
            'Urgent veterinary consultation recommended',
            'Implement probiotic supplementation protocol',
            'Complete gastroenterological examination advised',
            'Consider comprehensive dietary modification',
            'Rule out intestinal parasites',
            'Follow-up microbiological analysis in 4-6 weeks'
        ]
    }
}


# Default negative results
DEFAULT_RESULTS = {
    'parasite_negative': 'No unicellular parasite genome identified in the sample',
    'viral_negative': 'No viral genome identified in the sample',
    'parasites': [
        {'name': 'Anoplocephala perfoliata', 'result': 'Not observed'},
        {'name': 'Oxyuris equi', 'result': 'Not observed'},
        {'name': 'Parascaris equorum', 'result': 'Not observed'},
        {'name': 'Strongylidae', 'result': 'Not observed'}
    ],
    'microscopic': [
        {'parameter': 'Leukocytes', 'result': 'Not observed'},
        {'parameter': 'Erythrocytes', 'result': 'Not observed'},
        {'parameter': 'Yeast cells', 'result': 'Not observed'},
        {'parameter': 'Rhabditiform nematodes', 'result': 'Not observed'},
        {'parameter': 'Plant fibers', 'result': 'Present'},
        {'parameter': 'Cereal grains', 'result': 'Not observed'}
    ],
    'biochemical': [
        {'parameter': 'pH', 'result': '7.2', 'reference': '6.8 - 7.4', 'status': 'Normal'},
        {'parameter': 'Consistency', 'result': 'Formed', 'reference': 'Formed', 'status': 'Normal'},
        {'parameter': 'Occult Blood', 'result': 'Negative', 'reference': 'Negative', 'status': 'Normal'},
        {'parameter': 'Fat Content', 'result': 'Trace', 'reference': 'None/Trace', 'status': 'Normal'},
        {'parameter': 'Protein', 'result': 'Negative', 'reference': 'Negative', 'status': 'Normal'}
    ]
}


class DynamicContentGenerator:
    """Generates dynamic content based on analysis results"""
    
    @staticmethod
    def generate_species_description(top_species: List[Dict[str, Any]]) -> str:
        """Generate description based on dominant species"""
        if not top_species:
            return "Bacterial composition analysis shows balanced distribution."
        
        dominant = top_species[0]
        desc = f"High percentage of {dominant['species']} ({dominant['percentage']:.1f}%) "
        
        if dominant['percentage'] > 25:
            desc += "indicates significant dominance in the microbiome. "
        elif dominant['percentage'] > 15:
            desc += "shows moderate presence in the microbiome. "
        else:
            desc += "is within expected ranges. "
        
        # Add information about beneficial bacteria if present
        beneficial = ['Fibrobacter', 'Ruminococcus', 'Lachnospira', 'Roseburia']
        found_beneficial = [s for s in top_species[:5] if any(b in s['species'] for b in beneficial)]
        
        if found_beneficial:
            desc += f"Beneficial fermentation bacteria including {', '.join([s['species'] for s in found_beneficial])} "
            desc += "support efficient digestion of complex carbohydrates."
        
        return desc
    
    @staticmethod
    def get_dysbiosis_category(di_score: float) -> str:
        """Determine dysbiosis category based on score"""
        if di_score < 20:
            return 'normal'
        elif di_score < 50:
            return 'mild'
        else:
            return 'severe'
    
    @staticmethod
    def format_date_polish(date_str: str) -> str:
        """Format date in Polish style (DD.MM.YYYY r.)"""
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%d.%m.%Y r.')
        except:
            return date_str