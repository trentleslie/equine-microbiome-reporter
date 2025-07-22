"""
Clinical templates for equine microbiome analysis recommendations.

This module provides 8 standardized clinical templates covering different
dysbiosis scenarios for consistent LLM-powered recommendations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class DysbiosisLevel(Enum):
    """Dysbiosis severity levels"""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ClinicalScenario(Enum):
    """Clinical scenarios for template selection"""
    HEALTHY_MAINTENANCE = "healthy_maintenance"
    MILD_IMBALANCE = "mild_imbalance"
    BACTEROIDOTA_DEFICIENCY = "bacteroidota_deficiency"
    BACILLOTA_EXCESS = "bacillota_excess"
    PSEUDOMONADOTA_EXCESS = "pseudomonadota_excess"
    ACUTE_DYSBIOSIS = "acute_dysbiosis"
    CHRONIC_DYSBIOSIS = "chronic_dysbiosis"
    POST_ANTIBIOTIC = "post_antibiotic"


@dataclass
class ClinicalTemplate:
    """Structure for clinical recommendation templates"""
    scenario: ClinicalScenario
    title: str
    context: str
    key_findings: List[str]
    recommendations: List[str]
    monitoring_plan: str
    follow_up_timeline: str


# Define the 8 standardized clinical templates
CLINICAL_TEMPLATES = {
    ClinicalScenario.HEALTHY_MAINTENANCE: ClinicalTemplate(
        scenario=ClinicalScenario.HEALTHY_MAINTENANCE,
        title="Healthy Gut Microbiome - Maintenance Protocol",
        context="The microbiome analysis shows a well-balanced bacterial community within normal reference ranges.",
        key_findings=[
            "Balanced phylum distribution",
            "Normal species diversity",
            "No pathogenic overgrowth detected"
        ],
        recommendations=[
            "Continue current feeding regimen",
            "Maintain regular turnout schedule",
            "Consider seasonal probiotic support during stress periods",
            "Monitor for changes during feed transitions"
        ],
        monitoring_plan="Annual microbiome screening recommended",
        follow_up_timeline="12 months"
    ),
    
    ClinicalScenario.MILD_IMBALANCE: ClinicalTemplate(
        scenario=ClinicalScenario.MILD_IMBALANCE,
        title="Mild Dysbiosis - Early Intervention",
        context="Minor imbalances detected that may benefit from dietary adjustment.",
        key_findings=[
            "Slight deviation from optimal ranges",
            "Maintained species diversity",
            "Early dysbiosis indicators"
        ],
        recommendations=[
            "Increase hay quality and variety",
            "Add prebiotic supplement (10g daily)",
            "Reduce concentrate feeds by 20%",
            "Ensure adequate water access",
            "Consider digestive support supplement"
        ],
        monitoring_plan="Re-test in 3 months to assess improvement",
        follow_up_timeline="3 months"
    ),
    
    ClinicalScenario.BACTEROIDOTA_DEFICIENCY: ClinicalTemplate(
        scenario=ClinicalScenario.BACTEROIDOTA_DEFICIENCY,
        title="Bacteroidota Deficiency - Fiber Processing Support",
        context="Low Bacteroidota levels indicate reduced fiber fermentation capacity.",
        key_findings=[
            "Bacteroidota below 4% threshold",
            "Potential fiber digestion compromise",
            "Risk of hindgut acidosis"
        ],
        recommendations=[
            "Increase long-stem forage intake",
            "Add beet pulp or soy hulls as fiber sources",
            "Supplement with Bacteroidota-specific probiotic",
            "Reduce grain meals to < 2kg per feeding",
            "Consider yeast culture supplementation"
        ],
        monitoring_plan="Monthly fecal pH monitoring, re-test microbiome in 6 weeks",
        follow_up_timeline="6 weeks"
    ),
    
    ClinicalScenario.BACILLOTA_EXCESS: ClinicalTemplate(
        scenario=ClinicalScenario.BACILLOTA_EXCESS,
        title="Bacillota Overgrowth - Starch Reduction Protocol",
        context="Elevated Bacillota suggests excessive starch fermentation.",
        key_findings=[
            "Bacillota exceeding 70% threshold",
            "Lactic acid bacteria overgrowth risk",
            "Potential for hindgut acidosis"
        ],
        recommendations=[
            "Immediate 50% reduction in grain feeding",
            "Transition to low-starch feed alternatives",
            "Add hindgut buffer supplement",
            "Increase feeding frequency to 4-5 small meals",
            "Monitor for signs of laminitis"
        ],
        monitoring_plan="Weekly clinical assessment, re-test in 4 weeks",
        follow_up_timeline="4 weeks"
    ),
    
    ClinicalScenario.PSEUDOMONADOTA_EXCESS: ClinicalTemplate(
        scenario=ClinicalScenario.PSEUDOMONADOTA_EXCESS,
        title="Pseudomonadota Elevation - Inflammatory Response Management",
        context="High Pseudomonadota may indicate gut inflammation or pathogen presence.",
        key_findings=[
            "Pseudomonadota above 35% threshold",
            "Potential inflammatory response",
            "Dysbiosis with pathogenic risk"
        ],
        recommendations=[
            "Veterinary examination for underlying conditions",
            "Anti-inflammatory support (omega-3 supplementation)",
            "Gut healing protocol with L-glutamine",
            "Temporary elimination of processed feeds",
            "Consider antimicrobial herbs (oregano, garlic)"
        ],
        monitoring_plan="Bi-weekly veterinary check, inflammatory markers assessment",
        follow_up_timeline="2 weeks"
    ),
    
    ClinicalScenario.ACUTE_DYSBIOSIS: ClinicalTemplate(
        scenario=ClinicalScenario.ACUTE_DYSBIOSIS,
        title="Acute Severe Dysbiosis - Intensive Intervention",
        context="Severe microbiome disruption requiring immediate intervention.",
        key_findings=[
            "Multiple phyla outside reference ranges",
            "Dysbiosis index > 50",
            "High risk of clinical symptoms"
        ],
        recommendations=[
            "Immediate veterinary consultation",
            "Complete diet overhaul to hay-only",
            "Intensive probiotic therapy (multi-strain)",
            "Electrolyte and hydration support",
            "Daily monitoring of vital signs",
            "Consider fecal transplant therapy"
        ],
        monitoring_plan="Daily clinical monitoring, weekly microbiome assessment",
        follow_up_timeline="1 week"
    ),
    
    ClinicalScenario.CHRONIC_DYSBIOSIS: ClinicalTemplate(
        scenario=ClinicalScenario.CHRONIC_DYSBIOSIS,
        title="Chronic Dysbiosis - Long-term Management",
        context="Persistent microbiome imbalance requiring sustained intervention.",
        key_findings=[
            "Long-standing dysbiosis pattern",
            "Reduced microbial diversity",
            "Chronic digestive issues"
        ],
        recommendations=[
            "Comprehensive dietary reconstruction",
            "Long-term probiotic/prebiotic protocol",
            "Stress reduction management",
            "Environmental enrichment",
            "Regular therapeutic grooming",
            "Consider complementary therapies"
        ],
        monitoring_plan="Monthly progress assessments, quarterly microbiome analysis",
        follow_up_timeline="1 month"
    ),
    
    ClinicalScenario.POST_ANTIBIOTIC: ClinicalTemplate(
        scenario=ClinicalScenario.POST_ANTIBIOTIC,
        title="Post-Antibiotic Recovery - Microbiome Restoration",
        context="Microbiome disruption following antibiotic treatment.",
        key_findings=[
            "Antibiotic-associated dysbiosis",
            "Reduced bacterial diversity",
            "Opportunistic pathogen risk"
        ],
        recommendations=[
            "High-dose probiotic therapy (100 billion CFU/day)",
            "Prebiotic fiber supplementation",
            "Fermented feed additions (if tolerated)",
            "Gradual feed reintroduction protocol",
            "Immune support supplementation",
            "Avoid stress and diet changes"
        ],
        monitoring_plan="Weekly assessment for 4 weeks, then monthly",
        follow_up_timeline="1 week"
    )
}


def get_template(scenario: ClinicalScenario) -> ClinicalTemplate:
    """Get a clinical template by scenario"""
    return CLINICAL_TEMPLATES[scenario]


def get_all_templates() -> dict:
    """Get all clinical templates"""
    return CLINICAL_TEMPLATES