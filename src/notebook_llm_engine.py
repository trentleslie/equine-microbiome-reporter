"""
Notebook-friendly LLM recommendation engine
Avoids relative import issues for Jupyter notebook usage
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# Load environment variables from project root with multiple strategies
try:
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Try multiple paths to find .env file
    env_paths = []
    
    # Strategy 1: From current working directory's parent (for notebooks)
    cwd = Path.cwd()
    if cwd.name == 'notebooks':
        env_paths.append(cwd.parent / '.env')
    
    # Strategy 2: From this file's location
    current_file = Path(__file__).resolve()
    env_paths.append(current_file.parent.parent / '.env')
    
    # Strategy 3: From current working directory
    env_paths.append(cwd / '.env')
    
    # Try each path until we find one that works
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            break
            
except ImportError:
    # dotenv not available, environment variables should be set by system
    pass

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 1500
    timeout: int = 60

class NotebookLLMEngine:
    """Simplified LLM engine for notebook use"""
    
    def __init__(self, force_reload_env=True):
        # Force reload environment variables if requested
        if force_reload_env:
            self._force_load_env()
            
        self.enabled = os.getenv('ENABLE_LLM_RECOMMENDATIONS', 'false').lower() == 'true'
        self.config = self._load_config() if self.enabled else None
        
        if not self.enabled:
            logger.warning("LLM recommendations are disabled. Set ENABLE_LLM_RECOMMENDATIONS=true to enable.")
        elif not self.config:
            logger.warning("LLM is enabled but configuration is invalid.")
            self.enabled = False
    
    def _force_load_env(self):
        """Force reload environment variables from .env file"""
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Multiple strategies to find .env file
            env_paths = []
            
            # Strategy 1: From current working directory's parent (for notebooks)
            cwd = Path.cwd()
            if cwd.name == 'notebooks':
                env_paths.append(cwd.parent / '.env')
            
            # Strategy 2: From this file's location
            current_file = Path(__file__).resolve()
            env_paths.append(current_file.parent.parent / '.env')
            
            # Strategy 3: From current working directory
            env_paths.append(cwd / '.env')
            
            # Try each path until we find one that works
            for env_path in env_paths:
                if env_path.exists():
                    result = load_dotenv(env_path, override=True)
                    logger.info(f"Environment variables loaded from {env_path} (result: {result})")
                    return
                    
            logger.warning(f"No .env file found. Tried paths: {[str(p) for p in env_paths]}")
                
        except ImportError:
            logger.warning("python-dotenv not available for environment loading")
        except Exception as e:
            logger.error(f"Error force-loading environment: {e}")
    
    def _load_config(self) -> Optional[LLMConfig]:
        """Load LLM configuration from environment variables"""
        try:
            provider = os.getenv('LLM_PROVIDER', 'anthropic').lower()
            
            # Get API key based on provider
            if provider == 'openai':
                api_key = os.getenv('OPENAI_API_KEY')
                model = os.getenv('OPENAI_MODEL', 'gpt-4')
            elif provider == 'anthropic':
                api_key = os.getenv('ANTHROPIC_API_KEY')
                model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
            elif provider == 'gemini':
                api_key = os.getenv('GOOGLE_API_KEY')
                model = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
            else:
                logger.error(f"Unsupported LLM provider: {provider}")
                return None
            
            if not api_key:
                logger.error(f"API key not found for provider: {provider}")
                return None
            
            temperature = float(os.getenv('LLM_TEMPERATURE', '0.3'))
            max_tokens = int(os.getenv('LLM_MAX_TOKENS', '1500'))
            timeout = int(os.getenv('LLM_TIMEOUT', '60'))
            
            return LLMConfig(
                provider=provider,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            
        except Exception as e:
            logger.error(f"Error loading LLM configuration: {e}")
            return None
    
    def generate_recommendations(self, microbiome_data, patient_info) -> List[str]:
        """Generate LLM-powered recommendations"""
        if not self.enabled or not self.config:
            return self._get_enhanced_fallback_recommendations(microbiome_data)
        
        try:
            # Prepare prompt
            prompt = self._create_prompt(microbiome_data, patient_info)
            
            # Call appropriate LLM provider
            if self.config.provider == 'anthropic':
                return self._call_anthropic(prompt)
            elif self.config.provider == 'openai':
                return self._call_openai(prompt)
            elif self.config.provider == 'gemini':
                return self._call_gemini(prompt)
            else:
                logger.error(f"Unsupported provider: {self.config.provider}")
                return self._get_enhanced_fallback_recommendations(microbiome_data)
                
        except Exception as e:
            logger.error(f"LLM recommendation generation failed: {e}")
            # Return enhanced fallback recommendations when LLM fails but is configured
            return self._get_enhanced_fallback_recommendations(microbiome_data)
    
    def _create_prompt(self, microbiome_data, patient_info) -> str:
        """Create prompt for LLM with HippoVet+ clinical context"""
        phylum_text = []
        for phylum, percentage in microbiome_data.phylum_distribution.items():
            phylum_text.append(f"- {phylum}: {percentage:.1f}%")
        
        # Get HippoVet+ template for context
        hippovet_template = self._get_hippovet_template(microbiome_data)
        template_context = ""
        if hippovet_template:
            template_context = f"""
HippoVet+ Clinical Assessment: {hippovet_template['clinical_significance']}
Recommended Protocol: {hippovet_template['scenario']}
"""
        
        prompt = f"""
You are a veterinary microbiome specialist working with HippoVet+ laboratory protocols. Based on the following equine gut microbiome analysis, provide specific clinical recommendations following HippoVet+ standards:

Patient: {patient_info.name} ({patient_info.species}, {patient_info.age})
Dysbiosis Index: {microbiome_data.dysbiosis_index:.1f}
Category: {microbiome_data.dysbiosis_category}

Phylum Distribution (HippoVet+ Reference Ranges):
{chr(10).join(phylum_text)}

Reference Ranges:
- Actinomycetota: 0.1-8% (fiber digestion)
- Bacillota: 20-70% (starch/carbohydrate processing)  
- Bacteroidota: 4-40% (protein/fiber breakdown)
- Pseudomonadota: 2-35% (fat/protein fermentation)

Total Species: {microbiome_data.total_species_count}
{template_context}

HippoVet+ Approved Supplements:
- Hefekultur: Prebiotic for beneficial bacteria support
- SemiColon: Digestive support and pH balance
- Robusan: Digestive enzyme support
- Medigest: Carbohydrate processing improvement

Please provide 4-5 specific, actionable recommendations following HippoVet+ protocols:
1. Clinical interpretation based on phylum imbalances
2. Specific dietary modifications (hay vs grain ratios)
3. HippoVet+ supplement recommendations with protocols
4. Monitoring timeline and follow-up testing
5. Management practices for optimal gut health

Focus on evidence-based equine veterinary practice following HippoVet+ laboratory standards.
"""
        return prompt
    
    def _call_anthropic(self, prompt: str) -> List[str]:
        """Call Anthropic Claude API"""
        try:
            import anthropic
            
            # Create client with minimal configuration to avoid proxy issues
            client = anthropic.Anthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            
            response = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response into list of recommendations
            content = response.content[0].text
            recommendations = [line.strip() for line in content.split('\n') 
                             if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•') or line.strip()[0].isdigit())]
            
            return recommendations[:5] if recommendations else self._get_fallback_recommendations(None)
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def _call_openai(self, prompt: str) -> List[str]:
        """Call OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.config.api_key)
            
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            content = response.choices[0].message.content
            recommendations = [line.strip() for line in content.split('\n') 
                             if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•') or line.strip()[0].isdigit())]
            
            return recommendations[:5] if recommendations else self._get_fallback_recommendations(None)
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _call_gemini(self, prompt: str) -> List[str]:
        """Call Google Gemini API"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model)
            
            response = model.generate_content(prompt)
            content = response.text
            
            recommendations = [line.strip() for line in content.split('\n') 
                             if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•') or line.strip()[0].isdigit())]
            
            return recommendations[:5] if recommendations else self._get_fallback_recommendations(None)
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _get_fallback_recommendations(self, microbiome_data) -> List[str]:
        """Fallback recommendations when LLM is not available"""
        return [
            "Continue current feeding regimen and monitor digestive health",
            "Consider probiotic supplementation if digestive issues arise", 
            "Ensure adequate fiber intake to support beneficial bacteria",
            "Monitor for clinical signs of digestive distress or colic",
            "Schedule follow-up microbiome testing in 3-6 months"
        ]
    
    def _get_enhanced_fallback_recommendations(self, microbiome_data) -> List[str]:
        """Enhanced recommendations based on HippoVet+ clinical protocols"""
        recommendations = []
        
        # Get HippoVet+ clinical template based on microbiome data
        template = self._get_hippovet_template(microbiome_data)
        
        if template:
            # Use professional HippoVet+ recommendations with full clinical context
            clinical_intro = f"**{template['scenario']}**: {template['clinical_significance']}"
            
            # Primary dietary recommendation
            dietary_rec = f"Dietary Protocol: {template['dietary_modifications'][0] if template.get('dietary_modifications') else 'Continue current feeding regimen'}"
            
            # Supplement protocol with specific HippoVet+ products
            if template.get('supplement_protocol'):
                supplement_rec = f"HippoVet+ Supplement Protocol: {template['supplement_protocol'][0]}"
                if len(template['supplement_protocol']) > 1:
                    supplement_rec += f" and {template['supplement_protocol'][1]}"
            else:
                supplement_rec = "Supplement Protocol: Monitor and reassess based on clinical response"
            
            # Monitoring plan
            monitoring_rec = f"Monitoring Plan: {template.get('monitoring_plan', 'Follow-up testing in 4-6 weeks to assess improvement')}"
            
            # Management changes
            if template.get('management_changes'):
                management_rec = f"Management Changes: {template['management_changes'][0]}"
            else:
                management_rec = "Management: Continue current practices with increased monitoring"
            
            recommendations = [
                clinical_intro,
                dietary_rec,
                supplement_rec,
                monitoring_rec,
                management_rec
            ]
        else:
            # Enhanced fallback using general HippoVet+ principles when template matching fails
            phylum_dist = getattr(microbiome_data, 'phylum_distribution', {})
            dysbiosis_cat = getattr(microbiome_data, 'dysbiosis_category', 'unknown')
            
            if dysbiosis_cat in ['mild', 'moderate']:
                recommendations = [
                    f"Clinical Assessment: Microbiome shows {dysbiosis_cat} dysbiosis requiring targeted intervention",
                    "Dietary Protocol: Review fiber-to-concentrate ratio, ensure quality bulk feed availability",
                    "HippoVet+ Protocol: Consider Hefekultur prebiotic support and SemiColon for digestive balance",
                    "Monitoring Plan: Weekly stool quality assessment, retest microbiome in 4-6 weeks",
                    "Management: Maintain consistent feeding schedule, monitor for digestive changes"
                ]
            elif dysbiosis_cat == 'severe':
                recommendations = [
                    "Clinical Assessment: Severe dysbiosis detected - veterinary consultation recommended",
                    "Emergency Protocol: Immediate dietary review, remove concentrates temporarily",
                    "HippoVet+ Critical Support: Robusan + SemiColon combination for gut stabilization",
                    "Urgent Monitoring: Daily clinical observation, weekly microbiome assessment",
                    "Veterinary Action: Professional evaluation required for potential complications"
                ]
            else:
                # Normal/healthy maintenance
                recommendations = [
                    "Clinical Assessment: Microbiome within acceptable parameters for maintenance care",
                    "Dietary Protocol: Continue current feeding regimen with quality bulk feed foundation", 
                    "HippoVet+ Maintenance: Periodic Hefekultur support during stress or seasonal changes",
                    "Monitoring Plan: Annual microbiome screening to maintain baseline health status",
                    "Management: Maintain consistent routines, monitor for any digestive changes"
                ]
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _get_hippovet_template(self, microbiome_data) -> Optional[Dict]:
        """Get appropriate HippoVet+ clinical template based on microbiome analysis using official protocols"""
        try:
            if not hasattr(microbiome_data, 'phylum_distribution'):
                return None
                
            phylum_dist = microbiome_data.phylum_distribution
            dysbiosis_index = getattr(microbiome_data, 'dysbiosis_index', 0)
            
            # HippoVet+ Reference Ranges from official documentation
            actinomycetota_pct = phylum_dist.get('Actinomycetota', 0)
            bacillota_pct = phylum_dist.get('Bacillota', 0)
            bacteroidota_pct = phylum_dist.get('Bacteroidota', 0)
            pseudomonadota_pct = phylum_dist.get('Pseudomonadota', 0)
            
            # Check for severe dysbiosis first (>60 dysbiosis index or extreme imbalances)
            if dysbiosis_index > 60 or any([
                bacillota_pct > 80, bacteroidota_pct > 50, 
                actinomycetota_pct > 15, pseudomonadota_pct > 45
            ]):
                return {
                    'scenario': 'HIGHLY_DISRUPTED_MICROBIOTA',
                    'clinical_significance': 'Pathogen dominance with significant reduction in beneficial bacteria diversity. Risk of toxin production, intestinal inflammation, and endotoxemia.',
                    'key_findings': [
                        'Pathogen dominance detected',
                        'Significant reduction in beneficial bacteria',
                        'Loss of SCFA-producing bacteria'
                    ],
                    'possible_symptoms': [
                        'Chronic or acute diarrhea', 'Dehydration', 'Risk of laminitis',
                        'Intestinal inflammation', 'Colic episodes'
                    ],
                    'dietary_modifications': [
                        'Implement elimination diet immediately - provide only high-quality hay initially',
                        'Remove all concentrates temporarily',
                        'Ensure clean, fresh water access'
                    ],
                    'supplement_protocol': [
                        'Prebiotics, probiotics, postbiotics: Robusan, Semicolon',
                        'Digestive support: Medigest, Medigest Forte',
                        'Anti-laminitis support: Glucogard if at risk',
                        'Electrolyte support: Electrolyte HIPPOVIT'
                    ],
                    'management_changes': [
                        'Immediate veterinary consultation required',
                        'Strict dietary management',
                        'Close monitoring for complications'
                    ],
                    'monitoring_plan': 'Daily clinical monitoring, weekly microbiome assessment until stable'
                }
            
            # Bacillota excess (>70%) - starch fermentation overload
            elif bacillota_pct > 70:
                return {
                    'scenario': 'BACILLOTA_EXCESS',
                    'clinical_significance': 'Overgrowth of starch-fermenting bacteria leading to intestinal acidosis, increased lactic and acetic acid production, and pH disruption in large intestine.',
                    'key_findings': ['Bacillota >70% (above normal range)', 'Excessive starch fermentation', 'Risk of intestinal acidosis'],
                    'possible_symptoms': ['Loose stool', 'Intestinal acidosis', 'Gas production', 'Mucus in stool', 'Diarrhea episodes'],
                    'dietary_modifications': [
                        'Immediately reduce starch content in diet',
                        'Limit concentrated feeds and grains',
                        'Increase hay and haylage intake',
                        'Feed smaller, more frequent meals'
                    ],
                    'supplement_protocol': [
                        'Prebiotics to restore balance',
                        'Probiotics: SemiColon, Bifidobacterium',
                        'Postbiotics: Robusan, Semicolon'
                    ],
                    'management_changes': [
                        'Immediate dietary changes',
                        'Increased monitoring of stool quality',
                        'Stress reduction measures'
                    ],
                    'monitoring_plan': 'Weekly stool monitoring, re-test microbiome in 3-4 weeks'
                }
            
            # Bacillota deficiency (<20%) - carbohydrate digestion problems
            elif bacillota_pct < 20:
                return {
                    'scenario': 'BACILLOTA_DEFICIENCY',
                    'clinical_significance': 'Deficiency leads to disruptions in carbohydrate digestion, resulting in carbohydrate metabolism problems and gut dysbiosis development.',
                    'key_findings': ['Bacillota <20% (below normal range)', 'Compromised carbohydrate digestion'],
                    'possible_symptoms': ['Carbohydrate metabolism problems', 'Gut dysbiosis development'],
                    'dietary_modifications': [
                        'Increase intake of starch-rich feeds (e.g., grains, oats)',
                        'Add easily fermentable carbohydrates in controlled amounts',
                        'Gradual dietary transition over 7-14 days'
                    ],
                    'supplement_protocol': [
                        'Robusan for digestive enzyme support',
                        'Medigest to improve carbohydrate processing'
                    ],
                    'management_changes': [
                        'Monitor stool consistency during dietary changes',
                        'Ensure adequate water access'
                    ],
                    'monitoring_plan': 'Re-evaluate microbiome in 4-6 weeks to assess dietary modifications'
                }
            
            # Bacteroidota deficiency (<4%) - protein and fiber processing impairment
            elif bacteroidota_pct < 4:
                return {
                    'scenario': 'BACTEROIDOTA_DEFICIENCY',
                    'clinical_significance': 'Deficiency in bacteria responsible for protein and fiber breakdown, leading to reduced SCFA production and compromised toxin elimination.',
                    'key_findings': ['Bacteroidota <4% (below normal range)', 'Compromised protein and fiber digestion'],
                    'possible_symptoms': ['Problems with protein digestion', 'Reduced fiber utilization', 'Potential toxin accumulation'],
                    'dietary_modifications': [
                        'Increase plant fiber content from bulk feeds - hay and grass',
                        'Include plant protein sources like lucerne (alfalfa)',
                        'Ensure variety in forage sources'
                    ],
                    'supplement_protocol': [
                        'Prebiotics to support Bacteroidota growth',
                        'Consider targeted probiotic supplementation'
                    ],
                    'management_changes': [
                        'Increase pasture access for diverse plant intake',
                        'Monitor protein quality in feed'
                    ],
                    'monitoring_plan': 'Monitor protein utilization and re-test in 6 weeks'
                }
            
            # Bacteroidota excess (>40%) - protein fermentation imbalance
            elif bacteroidota_pct > 40:
                return {
                    'scenario': 'BACTEROIDOTA_EXCESS',
                    'clinical_significance': 'Overgrowth can lead to excessive production of fatty acids, causing intestinal imbalances and reduced nutrient absorption.',
                    'key_findings': ['Bacteroidota >40% (above normal range)', 'Excessive fatty acid production'],
                    'possible_symptoms': ['Imbalances in intestines', 'Reduced absorption of nutrients'],
                    'dietary_modifications': [
                        'Decrease intake of bulk feeds (e.g., hay)',
                        'Reduce fiber in diet temporarily',
                        'Increase consumption of starch and easily digestible carbohydrates'
                    ],
                    'supplement_protocol': [
                        'SemiColon for digestive balance',
                        'Monitor and reassess in 3-4 weeks'
                    ],
                    'management_changes': [
                        'Gradual dietary transition',
                        'Monitor nutrient absorption indicators'
                    ],
                    'monitoring_plan': 'Re-evaluate in 4-6 weeks with focus on nutrient utilization'
                }
            
            # Actinomycetota excess (>8%) - fiber fermentation overload
            elif actinomycetota_pct > 8:
                return {
                    'scenario': 'ACTINOMYCETOTA_EXCESS',
                    'clinical_significance': 'Overgrowth of fiber-fermenting bacteria, potentially due to high-fiber, low-energy diet causing excessive gas production and digestive imbalances.',
                    'key_findings': ['Actinomycetota >8% (above normal range)', 'Excessive cellulose fermentation activity'],
                    'possible_symptoms': ['Excessive gas production', 'Bloating', 'Reduced ability to digest other food components'],
                    'dietary_modifications': [
                        'Decrease intake of fiber-rich feeds',
                        'Increase energy-dense feeds (whole grains) in controlled amounts',
                        'Balance starch content carefully'
                    ],
                    'supplement_protocol': [
                        'Digestive enzyme support if needed',
                        'Monitor for improved balance before adding supplements'
                    ],
                    'management_changes': [
                        'Gradual dietary transition over 7-14 days',
                        'Monitor stool consistency during changes'
                    ],
                    'monitoring_plan': 'Re-evaluate microbiome in 6-8 weeks to assess dietary modifications'
                }
            
            # Actinomycetota deficiency (<0.1%) - compromised fiber digestion
            elif actinomycetota_pct < 0.1:
                return {
                    'scenario': 'ACTINOMYCETOTA_DEFICIENCY',
                    'clinical_significance': 'Deficiency in fiber-digesting bacteria leading to problems with cellulose breakdown and inadequate SCFA production.',
                    'key_findings': ['Actinomycetota <0.1% (below normal range)', 'Compromised fiber digestion capability'],
                    'possible_symptoms': ['Constipation', 'Problems with fiber digestion', 'Inadequate SCFA production'],
                    'dietary_modifications': [
                        'Increase bulk feed intake (hay, haylage, chopped forage)',
                        'Improve forage quality',
                        'Gradual increase in fiber content'
                    ],
                    'supplement_protocol': [
                        'Prebiotics: Hefekultur',
                        'Consider fiber-fermenting bacterial supplements'
                    ],
                    'management_changes': [
                        'Increase turnout time on quality pasture',
                        'Provide multiple feeding times for better fiber utilization'
                    ],
                    'monitoring_plan': 'Monitor stool quality and re-test microbiome in 4-6 weeks'
                }
            
            # Pseudomonadota excess (>35%) - fat processing imbalance
            elif pseudomonadota_pct > 35:
                return {
                    'scenario': 'PSEUDOMONADOTA_EXCESS',
                    'clinical_significance': 'Excessive fat-fermenting bacteria leading to issues with fat digestion and overproduction of fatty acids, interfering with nutrient absorption.',
                    'key_findings': ['Pseudomonadota >35% (above normal range)', 'Excessive fat fermentation activity'],
                    'possible_symptoms': ['Issues with fat digestion', 'Overproduction of fatty acids'],
                    'dietary_modifications': [
                        'Reduce fat content in diet',
                        'Decrease protein and simple sugar intake',
                        'Increase high-fiber diet'
                    ],
                    'supplement_protocol': [
                        'Prebiotics: Bifidobacterium or Lactobacillus',
                        'Probiotics to restore microbial balance'
                    ],
                    'management_changes': [
                        'Monitor fat content in all feeds',
                        'Gradual dietary transition'
                    ],
                    'monitoring_plan': 'Monitor fat utilization and re-test in 4-6 weeks'
                }
            
            # Pseudomonadota deficiency (<2%) - pathogen protection compromise
            elif pseudomonadota_pct < 2:
                return {
                    'scenario': 'PSEUDOMONADOTA_DEFICIENCY',
                    'clinical_significance': 'Deficiency may lead to pathogen development, as these bacteria play crucial role in preventing harmful microorganisms.',
                    'key_findings': ['Pseudomonadota <2% (below normal range)', 'Compromised pathogen protection'],
                    'possible_symptoms': ['Increased susceptibility to pathogens', 'Compromised gut defense mechanisms'],
                    'dietary_modifications': [
                        'Increase high-quality plant-based fats (controlled quality)',
                        'Increase consumption of high-quality plant fiber',
                        'Add fermented feeds (grass silage)'
                    ],
                    'supplement_protocol': [
                        'Prebiotics: inulin and FOS (fructooligosaccharides)',
                        'Support Pseudomonadota growth with targeted prebiotics',
                        'Consider immune support: Hippomun forte'
                    ],
                    'management_changes': [
                        'Improve feed quality control',
                        'Monitor for signs of opportunistic infections'
                    ],
                    'monitoring_plan': 'Monitor for pathogen indicators and re-test in 4-6 weeks'
                }
            
            # Normal ranges - healthy maintenance protocol
            else:
                return {
                    'scenario': 'HEALTHY_MAINTENANCE',
                    'clinical_significance': 'Indicates proper fermentation, digestion, and intestinal immunity. Diverse, stable bacterial flora with proper proportion of probiotic bacteria.',
                    'key_findings': ['All phyla within normal ranges', 'Diverse bacterial flora', 'No excessive pathogenic bacteria'],
                    'possible_symptoms': ['Normal, well-formed stool', 'Good appetite and condition', 'Stable digestive health'],
                    'dietary_modifications': [
                        'Continue current feeding regimen',
                        'Maintain good quality bulk feed (hay, haylage)',
                        'Ensure balanced fiber to concentrate ratio'
                    ],
                    'supplement_protocol': [
                        'No immediate supplementation required',
                        'Consider seasonal prebiotic support during stress'
                    ],
                    'management_changes': [
                        'Continue current management practices',
                        'Monitor for dietary changes or stress factors'
                    ],
                    'monitoring_plan': 'Annual microbiome screening recommended to maintain baseline health status'
                }
                
        except Exception as e:
            logger.error(f"Error selecting HippoVet+ template: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current LLM engine status"""
        return {
            'enabled': self.enabled,
            'provider': self.config.provider if self.config else None,
            'api_key_configured': bool(self.config and self.config.api_key) if self.config else False,
            'model': self.config.model if self.config else None
        }