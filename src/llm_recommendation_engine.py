"""
LLM-powered recommendation engine for equine microbiome reports.

This module provides integration with various LLM providers (OpenAI, Anthropic, Google)
to generate personalized clinical recommendations based on microbiome analysis.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import pickle
from abc import ABC, abstractmethod

from dotenv import load_dotenv

from .clinical_templates import ClinicalTemplate, ClinicalScenario, get_template
from .data_models import MicrobiomeData, PatientInfo
from .template_selector import TemplateSelector

# Load environment variables
load_dotenv()

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
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Load configuration from environment variables"""
        provider = os.getenv('LLM_PROVIDER', 'openai')
        
        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY', '')
            model = os.getenv('OPENAI_MODEL', 'gpt-4')
        elif provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
            model = os.getenv('ANTHROPIC_MODEL', 'claude-3-opus-20240229')
        elif provider == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY', '')
            model = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.3')),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', '1500')),
            timeout=int(os.getenv('LLM_TIMEOUT', '60'))
        )


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate response from the LLM"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def generate(self, prompt: str) -> str:
        """Generate response using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are an expert equine veterinary microbiome specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def generate(self, prompt: str) -> str:
        """Generate response using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system="You are an expert equine veterinary microbiome specialist.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            self.model = genai.GenerativeModel(config.model)
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")
    
    def generate(self, prompt: str) -> str:
        """Generate response using Gemini API"""
        try:
            # Add system prompt to the beginning
            full_prompt = f"""You are an expert equine veterinary microbiome specialist.

{prompt}"""
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class ResponseCache:
    """Simple cache for LLM responses"""
    
    def __init__(self, cache_dir: Path = Path(".cache/llm_responses")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = os.getenv('LLM_CACHE_ENABLED', 'true').lower() == 'true'
        self.ttl = int(os.getenv('LLM_CACHE_TTL', '86400'))  # 24 hours default
    
    def _get_cache_key(self, prompt: str, config: LLMConfig) -> str:
        """Generate cache key from prompt and config"""
        cache_data = f"{prompt}_{config.provider}_{config.model}_{config.temperature}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get(self, prompt: str, config: LLMConfig) -> Optional[str]:
        """Get cached response if available and not expired"""
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(prompt, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Check if cache is expired
                if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.ttl):
                    logger.info(f"Using cached response for key: {cache_key}")
                    return cached_data['response']
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    def set(self, prompt: str, config: LLMConfig, response: str):
        """Cache the response"""
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(prompt, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'response': response,
                    'timestamp': datetime.now()
                }, f)
            logger.info(f"Cached response for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")


class LLMRecommendationEngine:
    """Main recommendation engine with LLM integration"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the recommendation engine"""
        self.config = config or LLMConfig.from_env()
        self.provider = self._create_provider()
        self.cache = ResponseCache()
        self.template_selector = TemplateSelector()
        self.few_shot_examples = self._load_few_shot_examples()
        
        # Check if LLM is enabled
        self.enabled = os.getenv('ENABLE_LLM_RECOMMENDATIONS', 'false').lower() == 'true'
        if not self.enabled:
            logger.warning("LLM recommendations are disabled. Set ENABLE_LLM_RECOMMENDATIONS=true to enable.")
    
    def _create_provider(self) -> LLMProvider:
        """Create the appropriate LLM provider"""
        if self.config.provider == 'openai':
            return OpenAIProvider(self.config)
        elif self.config.provider == 'anthropic':
            return AnthropicProvider(self.config)
        elif self.config.provider == 'gemini':
            return GeminiProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _load_few_shot_examples(self) -> List[Dict]:
        """Load few-shot examples for consistent output"""
        return [
            {
                "input": {
                    "patient": "15-year-old mare",
                    "dysbiosis_index": 35,
                    "main_issue": "Bacteroidota at 2.5% (normal: 4-40%)",
                    "symptoms": "loose stools, poor coat"
                },
                "output": {
                    "primary_concern": "Fiber fermentation deficiency due to low Bacteroidota",
                    "clinical_significance": "Reduced fiber digestion capacity may lead to nutritional deficiencies and digestive upset",
                    "personalized_recommendations": [
                        "Increase timothy hay to 2.5% body weight daily",
                        "Add 500g soaked beet pulp twice daily",
                        "Supplement with Saccharomyces cerevisiae (25g/day)",
                        "Monitor manure consistency daily"
                    ],
                    "expected_timeline": "Improvement expected within 4-6 weeks"
                }
            },
            {
                "input": {
                    "patient": "8-year-old gelding, competition horse",
                    "dysbiosis_index": 65,
                    "main_issue": "Bacillota at 78% (normal: 20-70%)",
                    "symptoms": "mild colic episodes, girthy behavior"
                },
                "output": {
                    "primary_concern": "Starch overload causing Bacillota overgrowth and hindgut acidosis risk",
                    "clinical_significance": "Excessive lactic acid production may damage intestinal lining and trigger colic",
                    "personalized_recommendations": [
                        "Reduce grain to maximum 0.5% body weight per meal",
                        "Switch to low-starch performance feed",
                        "Add hindgut buffer (sodium bicarbonate 50g/day)",
                        "Implement 4 small meals instead of 2 large ones",
                        "Consider gastroscopy to rule out ulcers"
                    ],
                    "expected_timeline": "Critical first 2 weeks, full rebalancing in 6-8 weeks"
                }
            }
        ]
    
    def create_prompt(
        self,
        template: ClinicalTemplate,
        microbiome_data: MicrobiomeData,
        patient_info: PatientInfo,
        additional_context: Optional[str] = None
    ) -> str:
        """Create a structured prompt for the LLM"""
        
        # Load config for reference ranges
        config_path = Path(__file__).parent.parent / "config" / "report_config.yaml"
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        prompt = f"""You are an expert equine veterinary microbiome specialist. Generate personalized clinical recommendations based on the following:

PATIENT INFORMATION:
- Name: {patient_info.name}
- Age: {patient_info.age}
- Species: {patient_info.species}

MICROBIOME ANALYSIS:
- Dysbiosis Index: {microbiome_data.dysbiosis_index}
- Dysbiosis Category: {microbiome_data.dysbiosis_category}
- Total Species Count: {microbiome_data.total_species_count}

PHYLUM DISTRIBUTION:
"""
        for phylum, percentage in microbiome_data.phylum_distribution.items():
            ref_range = config['reference_ranges'].get(phylum, [0, 100])
            status = "NORMAL" if ref_range[0] <= percentage <= ref_range[1] else "ABNORMAL"
            prompt += f"- {phylum}: {percentage:.1f}% ({status}, ref: {ref_range[0]}-{ref_range[1]}%)\n"
        
        prompt += f"\n\nCLINICAL TEMPLATE: {template.title}\n"
        prompt += f"Context: {template.context}\n\n"
        
        if additional_context:
            prompt += f"ADDITIONAL CONTEXT:\n{additional_context}\n\n"
        
        prompt += """Based on this information, provide:
1. A personalized clinical interpretation (2-3 sentences)
2. Specific dietary modifications with exact amounts
3. Supplement recommendations with dosages
4. Management changes tailored to this horse
5. Monitoring parameters and timeline

Format your response as a structured JSON object with the following keys:
- clinical_interpretation
- dietary_modifications (array of strings)
- supplement_protocol (array of strings)
- management_changes (array of strings)
- monitoring_plan (string)
- follow_up (string)
"""
        
        # Add few-shot examples
        prompt += "\n\nEXAMPLES:\n"
        for example in self.few_shot_examples[:2]:
            prompt += f"\nInput: {json.dumps(example['input'], indent=2)}"
            prompt += f"\nOutput: {json.dumps(example['output'], indent=2)}\n"
        
        return prompt
    
    def generate_recommendations(
        self,
        template: ClinicalTemplate,
        microbiome_data: MicrobiomeData,
        patient_info: PatientInfo,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate LLM-powered recommendations"""
        
        if not self.enabled:
            # Return template-based recommendations if LLM is disabled
            return {
                "clinical_interpretation": template.context,
                "dietary_modifications": template.recommendations[:3],
                "supplement_protocol": template.recommendations[3:5] if len(template.recommendations) > 3 else [],
                "management_changes": ["Implement changes gradually over 7-10 days", "Monitor for adverse reactions"],
                "monitoring_plan": template.monitoring_plan,
                "follow_up": template.follow_up_timeline,
                "llm_generated": False
            }
        
        # Create the prompt
        prompt = self.create_prompt(template, microbiome_data, patient_info, additional_context)
        
        # Check cache first
        cached_response = self.cache.get(prompt, self.config)
        if cached_response:
            result = json.loads(cached_response)
            result["llm_generated"] = True
            result["from_cache"] = True
            return result
        
        try:
            # Generate response from LLM
            if os.getenv('LLM_LOG_REQUESTS', 'true').lower() == 'true':
                logger.info(f"Sending request to {self.config.provider} ({self.config.model})")
            
            response = self.provider.generate(prompt)
            
            # Parse JSON response
            # Try to extract JSON from the response
            try:
                # Look for JSON between ```json and ``` markers
                if '```json' in response:
                    json_start = response.find('```json') + 7
                    json_end = response.find('```', json_start)
                    json_str = response[json_start:json_end].strip()
                else:
                    # Assume the entire response is JSON
                    json_str = response.strip()
                
                result = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback: create structured response from text
                logger.warning("Failed to parse LLM response as JSON, using fallback parsing")
                result = self._parse_text_response(response, template)
            
            # Cache the response
            self.cache.set(prompt, self.config, json.dumps(result))
            
            result["llm_generated"] = True
            result["from_cache"] = False
            return result
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to template-based recommendations
            return {
                "clinical_interpretation": template.context + " (LLM unavailable - using template)",
                "dietary_modifications": template.recommendations[:3],
                "supplement_protocol": template.recommendations[3:5] if len(template.recommendations) > 3 else [],
                "management_changes": ["Implement changes gradually", "Monitor response"],
                "monitoring_plan": template.monitoring_plan,
                "follow_up": template.follow_up_timeline,
                "llm_generated": False,
                "error": str(e)
            }
    
    def _parse_text_response(self, response: str, template: ClinicalTemplate) -> Dict[str, Any]:
        """Fallback parser for non-JSON responses"""
        # Simple heuristic parsing - in production, use more sophisticated NLP
        lines = response.split('\n')
        
        result = {
            "clinical_interpretation": "",
            "dietary_modifications": [],
            "supplement_protocol": [],
            "management_changes": [],
            "monitoring_plan": template.monitoring_plan,
            "follow_up": template.follow_up_timeline
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if any(keyword in line.lower() for keyword in ['interpretation', 'clinical assessment']):
                current_section = 'interpretation'
            elif any(keyword in line.lower() for keyword in ['diet', 'feeding', 'nutrition']):
                current_section = 'diet'
            elif any(keyword in line.lower() for keyword in ['supplement', 'probiotic']):
                current_section = 'supplement'
            elif any(keyword in line.lower() for keyword in ['management', 'change']):
                current_section = 'management'
            elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Bullet point
                cleaned_line = line.lstrip('-•* ').strip()
                if current_section == 'diet':
                    result["dietary_modifications"].append(cleaned_line)
                elif current_section == 'supplement':
                    result["supplement_protocol"].append(cleaned_line)
                elif current_section == 'management':
                    result["management_changes"].append(cleaned_line)
            elif current_section == 'interpretation' and not result["clinical_interpretation"]:
                result["clinical_interpretation"] = line
        
        return result
    
    def process_sample(
        self,
        microbiome_data: MicrobiomeData,
        patient_info: PatientInfo,
        clinical_history: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Complete pipeline for generating recommendations"""
        
        # Select appropriate template
        selected_scenario = self.template_selector.select_template(
            microbiome_data,
            patient_info,
            clinical_history
        )
        selected_template = get_template(selected_scenario)
        
        # Calculate confidence
        confidence = self.template_selector.calculate_confidence(
            microbiome_data,
            selected_scenario
        )
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            selected_template,
            microbiome_data,
            patient_info,
            additional_context=str(clinical_history) if clinical_history else None
        )
        
        # Combine all results
        return {
            "patient_info": patient_info.__dict__,
            "microbiome_analysis": {
                "dysbiosis_index": microbiome_data.dysbiosis_index,
                "category": microbiome_data.dysbiosis_category,
                "phylum_distribution": microbiome_data.phylum_distribution,
                "total_species": microbiome_data.total_species_count
            },
            "template_info": {
                "scenario": selected_scenario.value,
                "title": selected_template.title,
                "confidence": confidence
            },
            "recommendations": recommendations
        }


# Convenience function for quick setup
def create_recommendation_engine() -> LLMRecommendationEngine:
    """Create and return a configured recommendation engine"""
    return LLMRecommendationEngine()