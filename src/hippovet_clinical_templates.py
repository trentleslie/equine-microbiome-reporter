"""
HippoVet+ Clinical Templates for Equine Microbiome Analysis

This module integrates the specific clinical knowledge and protocols from HippoVet+
veterinary laboratory for accurate, professional recommendations based on the
official interpretation guidelines.

Based on:
- Genetic Fecal Examination Hippovet - Results Interpretation (2) copy.txt
- NGS Horse - Standard descriptions of individual sections for all parameters within the norm copy.txt
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class DysbiosisLevel(Enum):
    """HippoVet+ Dysbiosis severity levels"""
    NORMAL = "normal"
    SLIGHTLY_DISRUPTED = "slightly_disrupted"
    DISRUPTED = "disrupted"
    HIGHLY_DISRUPTED = "highly_disrupted"


class ClinicalScenario(Enum):
    """HippoVet+ Clinical scenarios for template selection"""
    HEALTHY_MAINTENANCE = "healthy_maintenance"
    ACTINOMYCETOTA_EXCESS = "actinomycetota_excess"
    ACTINOMYCETOTA_DEFICIENCY = "actinomycetota_deficiency"
    BACILLOTA_EXCESS = "bacillota_excess"
    BACILLOTA_DEFICIENCY = "bacillota_deficiency"
    BACTEROIDOTA_EXCESS = "bacteroidota_excess"
    BACTEROIDOTA_DEFICIENCY = "bacteroidota_deficiency"
    PSEUDOMONADOTA_EXCESS = "pseudomonadota_excess"
    PSEUDOMONADOTA_DEFICIENCY = "pseudomonadota_deficiency"
    SEVERE_DYSBIOSIS = "severe_dysbiosis"


@dataclass
class HippoVetClinicalTemplate:
    """HippoVet+ Clinical recommendation template structure"""
    scenario: ClinicalScenario
    title: str
    dysbiosis_level: DysbiosisLevel
    clinical_significance: str
    key_findings: List[str]
    possible_symptoms: List[str]
    dietary_modifications: List[str]
    supplement_protocol: List[str]
    management_changes: List[str]
    monitoring_plan: str
    follow_up_timeline: str
    clinical_notes: str


# HippoVet+ Reference Ranges
HIPPOVET_REFERENCE_RANGES = {
    "Actinomycetota": (0.1, 8.0),
    "Bacillota": (20.0, 70.0),
    "Bacteroidota": (4.0, 40.0),
    "Pseudomonadota": (2.0, 35.0)
}

# HippoVet+ Supplement Protocols
HIPPOVET_SUPPLEMENTS = {
    "prebiotics": ["Hefekultur", "inulin", "FOS (fructooligosaccharides)"],
    "probiotics": ["Bifidobacterium", "Lactobacillus", "SemiColon"],
    "postbiotics": ["Robusan", "Semicolon"],
    "digestive_support": ["Medigest", "Medigest Forte"],
    "liver_support": ["EQUIMEB Hepa", "Brandon Hepatic Protect"],
    "immune_support": ["Hippomun forte", "black seed oil"],
    "electrolytes": ["Electrolyte HIPPOVIT"],
    "anti_laminitis": ["Glucogard"],
    "gut_healing": ["Brandon GastroBalsam", "Brandon Colongard", "Brandon Gastrointestinal"],
    "sand_clearance": ["Brandon C-Mash", "plantain", "LinuStar"]
}


# Define HippoVet+ Clinical Templates
HIPPOVET_CLINICAL_TEMPLATES = {
    ClinicalScenario.HEALTHY_MAINTENANCE: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.HEALTHY_MAINTENANCE,
        title="Normal Microbiota - Maintenance Protocol",
        dysbiosis_level=DysbiosisLevel.NORMAL,
        clinical_significance="Indicates proper fermentation, digestion, and intestinal immunity. Diverse, stable bacterial flora with proper proportion of probiotic bacteria.",
        key_findings=[
            "All phyla within normal ranges",
            "Diverse bacterial flora",
            "No excessive pathogenic bacteria",
            "Proper fermentation indicators"
        ],
        possible_symptoms=[
            "Normal, well-formed stool",
            "Good appetite and condition",
            "Stable digestive health"
        ],
        dietary_modifications=[
            "Continue current feeding regimen",
            "Maintain good quality bulk feed (hay, haylage)",
            "Ensure balanced fiber to concentrate ratio",
            "Monitor feed quality and storage"
        ],
        supplement_protocol=[
            "No immediate supplementation required",
            "Consider seasonal prebiotic support during stress",
            "Maintain electrolyte balance during work periods"
        ],
        management_changes=[
            "Continue current management practices",
            "Monitor for dietary changes or stress factors",
            "Maintain regular turnout and exercise"
        ],
        monitoring_plan="Annual microbiome screening recommended to maintain baseline health status",
        follow_up_timeline="12 months or if clinical signs develop",
        clinical_notes="Normal microbiota indicates optimal gut health. Focus on maintaining current successful management."
    ),

    ClinicalScenario.ACTINOMYCETOTA_EXCESS: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.ACTINOMYCETOTA_EXCESS,
        title="Actinomycetota Excess - Fiber Fermentation Imbalance",
        dysbiosis_level=DysbiosisLevel.SLIGHTLY_DISRUPTED,
        clinical_significance="Overgrowth of fiber-fermenting bacteria, potentially due to high-fiber, low-energy diet causing excessive gas production and digestive imbalances.",
        key_findings=[
            "Actinomycetota >8% (above normal range)",
            "Excessive cellulose fermentation activity",
            "Potential for gas production increase"
        ],
        possible_symptoms=[
            "Excessive gas production",
            "Bloating",
            "Reduced ability to digest other food components",
            "Potential digestive disorders over time"
        ],
        dietary_modifications=[
            "Decrease intake of fiber-rich feeds",
            "Increase energy-dense feeds (whole grains) in controlled amounts",
            "Balance starch content carefully",
            "Reduce bulk feed temporarily"
        ],
        supplement_protocol=[
            "Digestive enzyme support if needed",
            "Monitor for improved balance before adding supplements"
        ],
        management_changes=[
            "Gradual dietary transition over 7-14 days",
            "Monitor stool consistency during changes",
            "Ensure adequate water access"
        ],
        monitoring_plan="Re-evaluate microbiome in 6-8 weeks to assess dietary modifications",
        follow_up_timeline="6-8 weeks",
        clinical_notes="Focus on rebalancing fiber fermentation through careful dietary management."
    ),

    ClinicalScenario.ACTINOMYCETOTA_DEFICIENCY: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.ACTINOMYCETOTA_DEFICIENCY,
        title="Actinomycetota Deficiency - Compromised Fiber Digestion",
        dysbiosis_level=DysbiosisLevel.SLIGHTLY_DISRUPTED,
        clinical_significance="Deficiency in fiber-digesting bacteria leading to problems with cellulose breakdown and inadequate SCFA production.",
        key_findings=[
            "Actinomycetota <0.1% (below normal range)",
            "Compromised fiber digestion capability",
            "Reduced SCFA production"
        ],
        possible_symptoms=[
            "Constipation",
            "Problems with fiber digestion",
            "Inadequate short-chain fatty acid production",
            "Gut microbiota imbalance"
        ],
        dietary_modifications=[
            "Increase bulk feed intake (hay, haylage, chopped forage)",
            "Improve forage quality",
            "Gradual increase in fiber content",
            "Ensure adequate long-stem fiber"
        ],
        supplement_protocol=[
            "Prebiotics: Hefekultur",
            "Consider fiber-fermenting bacterial supplements",
            "Support with digestive aids if needed"
        ],
        management_changes=[
            "Increase turnout time on quality pasture",
            "Provide multiple feeding times for better fiber utilization",
            "Monitor water intake"
        ],
        monitoring_plan="Monitor stool quality and re-test microbiome in 4-6 weeks",
        follow_up_timeline="4-6 weeks",
        clinical_notes="Focus on rebuilding fiber-fermenting bacterial populations through increased quality bulk feed."
    ),

    ClinicalScenario.BACILLOTA_EXCESS: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.BACILLOTA_EXCESS,
        title="Bacillota Excess - Starch Fermentation Overload",
        dysbiosis_level=DysbiosisLevel.DISRUPTED,
        clinical_significance="Overgrowth of starch-fermenting bacteria leading to intestinal acidosis, increased lactic and acetic acid production, and pH disruption in large intestine.",
        key_findings=[
            "Bacillota >70% (above normal range)",
            "Excessive starch fermentation",
            "Risk of intestinal acidosis",
            "Disrupted pH balance in large intestine"
        ],
        possible_symptoms=[
            "Loose stool",
            "Intestinal acidosis",
            "Gas production",
            "Mucus in stool",
            "Diarrhea episodes",
            "Poor coat quality",
            "Weight loss",
            "Irritability"
        ],
        dietary_modifications=[
            "Immediately reduce starch content in diet",
            "Limit concentrated feeds and grains",
            "Increase hay and haylage intake",
            "Increase bulk feeds",
            "Feed smaller, more frequent meals"
        ],
        supplement_protocol=[
            "Prebiotics to restore balance",
            "Probiotics: SemiColon, Bifidobacterium",
            "Postbiotics: Robusan, Semicolon",
            "Consider pH buffers if acidosis suspected"
        ],
        management_changes=[
            "Immediate dietary changes",
            "Increased monitoring of stool quality",
            "Stress reduction measures",
            "Gradual exercise if horse is comfortable"
        ],
        monitoring_plan="Weekly stool monitoring, re-test microbiome in 3-4 weeks",
        follow_up_timeline="3-4 weeks",
        clinical_notes="Priority on reducing starch fermentation and restoring pH balance. Monitor for signs of acidosis."
    ),

    ClinicalScenario.BACTEROIDOTA_DEFICIENCY: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.BACTEROIDOTA_DEFICIENCY,
        title="Bacteroidota Deficiency - Protein and Fiber Processing Impairment",
        dysbiosis_level=DysbiosisLevel.SLIGHTLY_DISRUPTED,
        clinical_significance="Deficiency in bacteria responsible for protein and fiber breakdown, leading to reduced SCFA production and compromised toxin elimination.",
        key_findings=[
            "Bacteroidota <4% (below normal range)",
            "Compromised protein and fiber digestion",
            "Reduced SCFA production",
            "Impaired toxin elimination"
        ],
        possible_symptoms=[
            "Problems with protein digestion",
            "Reduced fiber utilization",
            "Compromised gut health",
            "Potential toxin accumulation"
        ],
        dietary_modifications=[
            "Increase plant fiber content from bulk feeds",
            "Add quality hay and grass",
            "Include plant protein sources like lucerne (alfalfa)",
            "Ensure variety in forage sources"
        ],
        supplement_protocol=[
            "Prebiotics to support Bacteroidota growth",
            "Consider targeted probiotic supplementation",
            "Support with digestive enzymes if needed"
        ],
        management_changes=[
            "Increase pasture access for diverse plant intake",
            "Monitor protein quality in feed",
            "Ensure adequate fiber intake"
        ],
        monitoring_plan="Monitor protein utilization and re-test in 6 weeks",
        follow_up_timeline="6 weeks",
        clinical_notes="Focus on rebuilding protein and fiber processing capacity through targeted nutrition."
    ),

    ClinicalScenario.PSEUDOMONADOTA_EXCESS: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.PSEUDOMONADOTA_EXCESS,
        title="Pseudomonadota Excess - Fat Processing Imbalance",
        dysbiosis_level=DysbiosisLevel.SLIGHTLY_DISRUPTED,
        clinical_significance="Excessive fat-fermenting bacteria leading to issues with fat digestion and overproduction of fatty acids, interfering with nutrient absorption.",
        key_findings=[
            "Pseudomonadota >35% (above normal range)",
            "Excessive fat fermentation activity",
            "Potential nutrient absorption interference"
        ],
        possible_symptoms=[
            "Issues with fat digestion",
            "Overproduction of fatty acids",
            "Interference with absorption of other nutrients"
        ],
        dietary_modifications=[
            "Reduce fat content in diet",
            "Decrease protein and simple sugar intake",
            "Increase high-fiber diet",
            "Focus on quality forage"
        ],
        supplement_protocol=[
            "Prebiotics: Bifidobacterium or Lactobacillus",
            "Probiotics to restore microbial balance",
            "Digestive support if needed"
        ],
        management_changes=[
            "Monitor fat content in all feeds",
            "Gradual dietary transition",
            "Increase fiber-based feeding"
        ],
        monitoring_plan="Monitor fat utilization and re-test in 4-6 weeks",
        follow_up_timeline="4-6 weeks",
        clinical_notes="Balance fat-processing bacteria through reduced fat intake and increased fiber."
    ),

    ClinicalScenario.PSEUDOMONADOTA_DEFICIENCY: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.PSEUDOMONADOTA_DEFICIENCY,
        title="Pseudomonadota Deficiency - Pathogen Protection Compromise",
        dysbiosis_level=DysbiosisLevel.SLIGHTLY_DISRUPTED,
        clinical_significance="Deficiency in protective bacteria may lead to pathogen development, as these bacteria play crucial role in preventing harmful microorganisms.",
        key_findings=[
            "Pseudomonadota <2% (below normal range)",
            "Compromised pathogen protection",
            "Risk of harmful microorganism growth"
        ],
        possible_symptoms=[
            "Increased susceptibility to pathogens",
            "Compromised gut defense mechanisms",
            "Potential for opportunistic infections"
        ],
        dietary_modifications=[
            "Increase high-quality plant-based fats (controlled quality)",
            "Increase consumption of high-quality plant fiber",
            "Add fermented feeds (grass silage)"
        ],
        supplement_protocol=[
            "Prebiotics: inulin and FOS (fructooligosaccharides)",
            "Support Pseudomonadota growth with targeted prebiotics",
            "Consider immune support: Hippomun forte"
        ],
        management_changes=[
            "Improve feed quality control",
            "Monitor for signs of opportunistic infections",
            "Maintain good hygiene practices"
        ],
        monitoring_plan="Monitor for pathogen indicators and re-test in 4-6 weeks",
        follow_up_timeline="4-6 weeks",
        clinical_notes="Priority on rebuilding protective bacterial populations to prevent pathogen overgrowth."
    ),

    ClinicalScenario.SEVERE_DYSBIOSIS: HippoVetClinicalTemplate(
        scenario=ClinicalScenario.SEVERE_DYSBIOSIS,
        title="Highly Disrupted Microbiota - Emergency Protocol",
        dysbiosis_level=DysbiosisLevel.HIGHLY_DISRUPTED,
        clinical_significance="Pathogen dominance with significant reduction in beneficial bacteria diversity. Risk of toxin production, intestinal inflammation, and endotoxemia.",
        key_findings=[
            "Pathogen dominance",
            "Significant reduction in beneficial bacteria",
            "Potential presence of Clostridium, Salmonella",
            "Loss of SCFA-producing bacteria"
        ],
        possible_symptoms=[
            "Chronic or acute diarrhea",
            "Dehydration",
            "Risk of laminitis",
            "Intestinal inflammation",
            "Colic episodes",
            "Severe immune system decline"
        ],
        dietary_modifications=[
            "Implement elimination diet immediately",
            "Provide only high-quality hay initially",
            "Remove all concentrates temporarily",
            "Ensure clean, fresh water access"
        ],
        supplement_protocol=[
            "Prebiotics, probiotics, postbiotics: Robusan, Semicolon",
            "Digestive support: Medigest, Medigest Forte",
            "Anti-laminitis support: Glucogard if at risk",
            "Electrolyte support: Electrolyte HIPPOVIT",
            "Immune support: Hippomun forte"
        ],
        management_changes=[
            "Immediate veterinary consultation required",
            "Strict dietary management",
            "Close monitoring for complications",
            "Stress reduction critical"
        ],
        monitoring_plan="Daily clinical monitoring, weekly microbiome assessment until stable",
        follow_up_timeline="1-2 weeks initially, then monthly",
        clinical_notes="CRITICAL: Veterinary consultation recommended. May require pharmacological treatment alongside nutritional intervention."
    )
}


def get_hippovet_template(scenario: ClinicalScenario) -> HippoVetClinicalTemplate:
    """Get HippoVet+ clinical template for specific scenario"""
    return HIPPOVET_CLINICAL_TEMPLATES.get(scenario)


def select_hippovet_scenario(phylum_distribution: Dict[str, float], 
                           dysbiosis_index: float) -> ClinicalScenario:
    """
    Select appropriate HippoVet+ clinical scenario based on microbiome data
    
    Args:
        phylum_distribution: Dictionary of phylum percentages
        dysbiosis_index: Calculated dysbiosis index
        
    Returns:
        Most appropriate clinical scenario
    """
    # Check for severe dysbiosis first
    if dysbiosis_index > 60:
        return ClinicalScenario.SEVERE_DYSBIOSIS
    
    # Check individual phylum imbalances
    actino = phylum_distribution.get("Actinomycetota", 0)
    bacillota = phylum_distribution.get("Bacillota", 0)
    bacteroidota = phylum_distribution.get("Bacteroidota", 0)
    pseudo = phylum_distribution.get("Pseudomonadota", 0)
    
    # Check for significant deviations
    if bacillota > 70:
        return ClinicalScenario.BACILLOTA_EXCESS
    elif bacillota < 20:
        return ClinicalScenario.BACILLOTA_DEFICIENCY
    elif bacteroidota < 4:
        return ClinicalScenario.BACTEROIDOTA_DEFICIENCY
    elif bacteroidota > 40:
        return ClinicalScenario.BACTEROIDOTA_EXCESS
    elif actino > 8:
        return ClinicalScenario.ACTINOMYCETOTA_EXCESS
    elif actino < 0.1:
        return ClinicalScenario.ACTINOMYCETOTA_DEFICIENCY
    elif pseudo > 35:
        return ClinicalScenario.PSEUDOMONADOTA_EXCESS
    elif pseudo < 2:
        return ClinicalScenario.PSEUDOMONADOTA_DEFICIENCY
    else:
        return ClinicalScenario.HEALTHY_MAINTENANCE


def generate_hippovet_context_prompt(template: HippoVetClinicalTemplate, 
                                   patient_name: str = "the horse") -> str:
    """
    Generate context prompt for LLM based on HippoVet+ template
    
    Args:
        template: Selected HippoVet clinical template
        patient_name: Name of the horse
        
    Returns:
        Formatted prompt for LLM
    """
    return f"""
You are a veterinary nutritionist from HippoVet+ laboratory providing clinical recommendations 
for equine microbiome analysis. Based on the following clinical assessment:

CLINICAL SCENARIO: {template.title}
DYSBIOSIS LEVEL: {template.dysbiosis_level.value}

CLINICAL SIGNIFICANCE:
{template.clinical_significance}

KEY FINDINGS:
{chr(10).join(f'• {finding}' for finding in template.key_findings)}

Please provide personalized recommendations for {patient_name} following HippoVet+ protocols:

1. DIETARY MODIFICATIONS: Focus on specific feed changes, ratios, and quality requirements
2. SUPPLEMENT PROTOCOL: Recommend specific HippoVet+ approved supplements with dosages
3. MANAGEMENT CHANGES: Practical changes to daily care routine
4. MONITORING PLAN: How to track improvement and what to watch for
5. FOLLOW-UP: Timeline for re-assessment

Use professional veterinary language appropriate for horse owners and veterinarians.
Base recommendations on the provided clinical template but personalize for the specific case.
"""