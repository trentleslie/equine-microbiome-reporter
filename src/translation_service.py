"""
Translation service for multi-language template support.
Handles translation of Jinja2 templates while preserving scientific terminology.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Handle imports based on available packages
try:
    from google.cloud import translate_v3 as translate
    from google.oauth2 import service_account
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False

try:
    from googletrans import Translator as GoogleTransFree
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator as DeepGoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


@dataclass
class GlossaryEntry:
    """Represents a term in the scientific glossary"""
    english: str
    polish: str
    japanese: str
    category: str  # bacterial_name, medical_term, veterinary_term, etc.
    preserve_original: bool = False  # If True, don't translate


class ScientificGlossary:
    """Manages scientific terminology for accurate translation"""
    
    def __init__(self):
        self.entries: List[GlossaryEntry] = []
        self._load_default_glossary()
    
    def _load_default_glossary(self):
        """Load default veterinary microbiome terminology"""
        # Bacterial phyla (usually kept in Latin)
        bacterial_phyla = [
            GlossaryEntry("Actinomycetota", "Actinomycetota", "アクチノマイセータ門", "bacterial_name", True),
            GlossaryEntry("Bacillota", "Bacillota", "バシロータ門", "bacterial_name", True),
            GlossaryEntry("Bacteroidota", "Bacteroidota", "バクテロイドータ門", "bacterial_name", True),
            GlossaryEntry("Pseudomonadota", "Pseudomonadota", "シュードモナドータ門", "bacterial_name", True),
            GlossaryEntry("Fibrobacterota", "Fibrobacterota", "フィブロバクテロータ門", "bacterial_name", True),
            GlossaryEntry("Spirochaetota", "Spirochaetota", "スピロヘータ門", "bacterial_name", True),
            GlossaryEntry("Verrucomicrobiota", "Verrucomicrobiota", "ウェルコミクロビオータ門", "bacterial_name", True),
        ]
        
        # Medical terms
        medical_terms = [
            GlossaryEntry("dysbiosis", "dysbioza", "ディスバイオシス", "medical_term"),
            GlossaryEntry("microbiome", "mikrobiom", "マイクロバイオーム", "medical_term"),
            GlossaryEntry("microbiota", "mikrobiota", "微生物叢", "medical_term"),
            GlossaryEntry("microflora", "mikroflora", "微生物叢", "medical_term"),
            GlossaryEntry("pathogen", "patogen", "病原体", "medical_term"),
            GlossaryEntry("gut flora", "flora jelitowa", "腸内細菌叢", "medical_term"),
            GlossaryEntry("bacterial abundance", "liczebność bakterii", "細菌の存在量", "medical_term"),
            GlossaryEntry("phylum", "typ", "門", "medical_term"),
            GlossaryEntry("genus", "rodzaj", "属", "medical_term"),
            GlossaryEntry("species", "gatunek", "種", "medical_term"),
            GlossaryEntry("16S rRNA", "16S rRNA", "16S rRNA", "medical_term", True),
            GlossaryEntry("sequencing", "sekwencjonowanie", "シーケンシング", "medical_term"),
            GlossaryEntry("reference range", "zakres referencyjny", "基準範囲", "medical_term"),
            GlossaryEntry("clinical interpretation", "interpretacja kliniczna", "臨床的解釈", "medical_term"),
        ]
        
        # Veterinary terms
        veterinary_terms = [
            GlossaryEntry("equine", "koński", "馬の", "veterinary_term"),
            GlossaryEntry("horse", "koń", "馬", "veterinary_term"),
            GlossaryEntry("fecal sample", "próbka kału", "糞便サンプル", "veterinary_term"),
            GlossaryEntry("gut health", "zdrowie jelit", "腸の健康", "veterinary_term"),
            GlossaryEntry("intestinal", "jelitowy", "腸の", "veterinary_term"),
            GlossaryEntry("gastrointestinal", "żołądkowo-jelitowy", "胃腸の", "veterinary_term"),
        ]
        
        # Report-specific terms
        report_terms = [
            GlossaryEntry("normal", "prawidłowy", "正常", "report_term"),
            GlossaryEntry("mild", "łagodny", "軽度", "report_term"),
            GlossaryEntry("moderate", "umiarkowany", "中等度", "report_term"),
            GlossaryEntry("severe", "ciężki", "重度", "report_term"),
            GlossaryEntry("patient", "pacjent", "患者", "report_term"),
            GlossaryEntry("sample", "próbka", "サンプル", "report_term"),
            GlossaryEntry("analysis", "analiza", "分析", "report_term"),
            GlossaryEntry("results", "wyniki", "結果", "report_term"),
            GlossaryEntry("recommendations", "zalecenia", "推奨事項", "report_term"),
        ]

        # Technical/methodology terms (preserve in English - per Gosia's feedback)
        technical_terms = [
            GlossaryEntry("shotgun", "shotgun", "shotgun", "technical_term", True),
            GlossaryEntry("NGS", "NGS", "NGS", "technical_term", True),
            GlossaryEntry("metagenomic", "metagenomic", "metagenomic", "technical_term", True),
            GlossaryEntry("metagenomics", "metagenomics", "metagenomics", "technical_term", True),
            GlossaryEntry("amplicon", "amplicon", "amplicon", "technical_term", True),
            GlossaryEntry("DNA", "DNA", "DNA", "technical_term", True),
            GlossaryEntry("RNA", "RNA", "RNA", "technical_term", True),
            GlossaryEntry("PCR", "PCR", "PCR", "technical_term", True),
            GlossaryEntry("qPCR", "qPCR", "qPCR", "technical_term", True),
            GlossaryEntry("OTU", "OTU", "OTU", "technical_term", True),
            GlossaryEntry("ASV", "ASV", "ASV", "technical_term", True),
            GlossaryEntry("Illumina", "Illumina", "Illumina", "technical_term", True),
            GlossaryEntry("MinION", "MinION", "MinION", "technical_term", True),
            GlossaryEntry("Nanopore", "Nanopore", "Nanopore", "technical_term", True),
            GlossaryEntry("EPI2ME", "EPI2ME", "EPI2ME", "technical_term", True),
            GlossaryEntry("Kraken2", "Kraken2", "Kraken2", "technical_term", True),
            GlossaryEntry("bioinformatics", "bioinformatics", "bioinformatics", "technical_term", True),
        ]

        self.entries.extend(bacterial_phyla + medical_terms + veterinary_terms + report_terms + technical_terms)
    
    def get_term_translation(self, term: str, target_language: str) -> Optional[str]:
        """Get translation for a specific term"""
        for entry in self.entries:
            if entry.english.lower() == term.lower():
                if entry.preserve_original:
                    return entry.english
                elif target_language == "pl":
                    return entry.polish
                elif target_language == "ja":
                    return entry.japanese
        return None
    
    def export_to_dict(self, target_language: str) -> Dict[str, str]:
        """Export glossary as dictionary for quick lookup"""
        glossary_dict = {}
        for entry in self.entries:
            if entry.preserve_original:
                glossary_dict[entry.english.lower()] = entry.english
            elif target_language == "pl":
                glossary_dict[entry.english.lower()] = entry.polish
            elif target_language == "ja":
                glossary_dict[entry.english.lower()] = entry.japanese
        return glossary_dict


class Jinja2TemplateParser:
    """Handles extraction and restoration of Jinja2 syntax during translation"""
    
    def __init__(self):
        # Patterns for different Jinja2 elements
        self.patterns = {
            'variable': re.compile(r'{{.*?}}'),
            'block': re.compile(r'{%.*?%}'),
            'comment': re.compile(r'{#.*?#}'),
        }
        self.placeholder_map = {}
        self.placeholder_counter = 0
    
    def extract_jinja2_elements(self, text: str) -> str:
        """Replace Jinja2 elements with placeholder tokens"""
        self.placeholder_map = {}
        self.placeholder_counter = 0
        
        for pattern_type, pattern in self.patterns.items():
            text = pattern.sub(self._create_placeholder, text)
        
        return text
    
    def _create_placeholder(self, match):
        """Create a unique placeholder for a Jinja2 element"""
        placeholder = f"@@JINJA_{self.placeholder_counter}@@"
        self.placeholder_map[placeholder] = match.group(0)
        self.placeholder_counter += 1
        return placeholder
    
    def restore_jinja2_elements(self, text: str) -> str:
        """Restore original Jinja2 elements from placeholders"""
        for placeholder, original in self.placeholder_map.items():
            text = text.replace(placeholder, original)
        return text


class TranslationService:
    """Base class for translation services"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.glossary = ScientificGlossary()
        self.parser = Jinja2TemplateParser()
        self.cache_dir = cache_dir or Path("translation_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        """Load translation cache from disk"""
        cache_file = self.cache_dir / "translation_cache.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return defaultdict(dict)
    
    def _save_cache(self):
        """Save translation cache to disk"""
        cache_file = self.cache_dir / "translation_cache.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _get_cache_key(self, text: str, target_language: str) -> str:
        """Generate a cache key for a text and target language"""
        return hashlib.md5(f"{text}:{target_language}".encode()).hexdigest()
    
    def _apply_glossary(self, text: str, target_language: str) -> Tuple[str, Dict[str, str]]:
        """Apply glossary replacements and return text with placeholders"""
        term_placeholders = {}
        glossary_dict = self.glossary.export_to_dict(target_language)
        
        # Sort by length to replace longer terms first
        sorted_terms = sorted(glossary_dict.keys(), key=len, reverse=True)
        
        for i, term in enumerate(sorted_terms):
            # Case-insensitive search with word boundaries
            pattern = rf'\b{re.escape(term)}\b'
            if re.search(pattern, text, re.IGNORECASE):
                placeholder = f"@@TERM_{i}@@"
                text = re.sub(pattern, placeholder, text, flags=re.IGNORECASE)
                term_placeholders[placeholder] = glossary_dict[term]
        
        return text, term_placeholders
    
    def _restore_glossary_terms(self, text: str, term_placeholders: Dict[str, str]) -> str:
        """Restore glossary terms from placeholders"""
        for placeholder, term in term_placeholders.items():
            text = text.replace(placeholder, term)
        return text
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text - to be implemented by subclasses"""
        raise NotImplementedError
    
    def translate_template(self, template_path: Path, target_language: str) -> str:
        """Translate an entire template file"""
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Split template into lines for better translation context
        lines = template_content.split('\n')
        translated_lines = []
        
        for line in lines:
            if line.strip():  # Only translate non-empty lines
                translated_line = self.translate_text(line, target_language)
                translated_lines.append(translated_line)
            else:
                translated_lines.append(line)
        
        return '\n'.join(translated_lines)


class GoogleCloudTranslationService(TranslationService):
    """Translation service using Google Cloud Translation API"""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None, 
                 cache_dir: Optional[Path] = None):
        super().__init__(cache_dir)
        
        if not GOOGLE_TRANSLATE_AVAILABLE:
            raise ImportError("Google Cloud Translation API not available. "
                            "Install with: poetry install --with translation")
        
        self.project_id = project_id
        self.location = "global"
        
        # Initialize client
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = translate.TranslationServiceClient(credentials=credentials)
        else:
            self.client = translate.TranslationServiceClient()
        
        self.parent = f"projects/{project_id}/locations/{self.location}"
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text using Google Cloud Translation API"""
        # Check cache first
        cache_key = self._get_cache_key(text, target_language)
        if cache_key in self.cache.get(target_language, {}):
            return self.cache[target_language][cache_key]
        
        # Extract Jinja2 elements
        processed_text = self.parser.extract_jinja2_elements(text)
        
        # Apply glossary
        processed_text, term_placeholders = self._apply_glossary(processed_text, target_language)
        
        # Prepare translation request
        request = {
            "parent": self.parent,
            "contents": [processed_text],
            "source_language_code": "en",
            "target_language_code": target_language,
            "mime_type": "text/plain",
        }
        
        # Translate
        try:
            response = self.client.translate_text(request=request)
            translated_text = response.translations[0].translated_text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
        
        # Restore glossary terms
        translated_text = self._restore_glossary_terms(translated_text, term_placeholders)
        
        # Restore Jinja2 elements
        final_text = self.parser.restore_jinja2_elements(translated_text)
        
        # Cache the result
        if target_language not in self.cache:
            self.cache[target_language] = {}
        self.cache[target_language][cache_key] = final_text
        self._save_cache()
        
        return final_text


class FreeTranslationService(TranslationService):
    """Translation service using free translation libraries"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        super().__init__(cache_dir)
        
        # Prefer deep-translator as it's more reliable
        if DEEP_TRANSLATOR_AVAILABLE:
            self.translator_type = "deep_translator"
            print("Using deep-translator for free translation service")
        elif GOOGLETRANS_AVAILABLE:
            self.translator_type = "googletrans"
            self.translator = GoogleTransFree()
            print("Using googletrans for free translation service")
        else:
            raise ImportError("No free translation library available. "
                            "Install with: poetry install --with translation-free")
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text using available free translation service"""
        # Check cache first
        cache_key = self._get_cache_key(text, target_language)
        if cache_key in self.cache.get(target_language, {}):
            return self.cache[target_language][cache_key]
        
        # Extract Jinja2 elements
        processed_text = self.parser.extract_jinja2_elements(text)
        
        # Apply glossary
        processed_text, term_placeholders = self._apply_glossary(processed_text, target_language)
        
        # Translate using appropriate service
        try:
            if self.translator_type == "deep_translator":
                # Use deep-translator (more reliable)
                translator = DeepGoogleTranslator(source='en', target=target_language)
                translated_text = translator.translate(processed_text)
            else:
                # Use googletrans (fallback)
                result = self.translator.translate(processed_text, src='en', dest=target_language)
                
                # Handle both sync and async results
                if hasattr(result, 'text'):
                    translated_text = result.text
                elif hasattr(result, 'result'):
                    translated_text = result.result
                else:
                    # Fallback: return original text if translation fails
                    print(f"Translation warning: Unexpected result format, returning original text")
                    translated_text = processed_text
                
        except Exception as e:
            print(f"Translation error: {e}")
            return text
        
        # Restore glossary terms
        translated_text = self._restore_glossary_terms(translated_text, term_placeholders)
        
        # Restore Jinja2 elements
        final_text = self.parser.restore_jinja2_elements(translated_text)
        
        # Cache the result
        if target_language not in self.cache:
            self.cache[target_language] = {}
        self.cache[target_language][cache_key] = final_text
        self._save_cache()
        
        return final_text


class GeminiTranslationService(TranslationService):
    """Translation service using Google Gemini API (free tier)"""

    # Language name mapping for natural prompts
    LANGUAGE_NAMES = {
        'pl': 'Polish',
        'ja': 'Japanese',
        'de': 'German',
        'es': 'Spanish',
        'fr': 'French',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ko': 'Korean',
    }

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        super().__init__(cache_dir)

        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini API not available. "
                            "Install with: poetry install --with llm")

        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable, "
                           "or pass api_key parameter.")

        # Configure the API
        genai.configure(api_key=self.api_key)

        # Use gemini-2.0-flash-lite for free tier (lighter model, higher rate limits)
        # Alternative models: gemini-2.0-flash, gemini-2.5-flash
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-lite')
        self.model = genai.GenerativeModel(model_name)
        print(f"Using {model_name} for translation service")

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text using Google Gemini API"""
        # Check cache first
        cache_key = self._get_cache_key(text, target_language)
        if cache_key in self.cache.get(target_language, {}):
            return self.cache[target_language][cache_key]

        # Extract Jinja2 elements
        processed_text = self.parser.extract_jinja2_elements(text)

        # Apply glossary
        processed_text, term_placeholders = self._apply_glossary(processed_text, target_language)

        # Get language name for prompt
        lang_name = self.LANGUAGE_NAMES.get(target_language, target_language.upper())

        # Create translation prompt with instructions to preserve formatting
        prompt = f"""Translate the following text from English to {lang_name}.

IMPORTANT RULES:
1. Preserve ALL placeholders exactly as they appear (e.g., @@X7TBL000X7@@, @@TERM_0@@, @@JINJA_0@@)
2. Preserve ALL HTML tags exactly as they appear
3. Do NOT translate scientific names (Latin species names like "Lactobacillus acidophilus")
4. Do NOT translate technical abbreviations (DNA, RNA, PCR, NGS, etc.)
5. Use proper {lang_name} grammar and formal/professional tone suitable for a medical report
6. Only output the translated text, nothing else

Text to translate:
{processed_text}"""

        # Retry with exponential backoff for rate limits
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                translated_text = response.text.strip()
                break
            except Exception as e:
                error_str = str(e)
                if '429' in error_str and attempt < max_retries - 1:
                    # Rate limited - wait and retry
                    wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s
                    print(f"Rate limited, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    print(f"Gemini translation error: {e}")
                    return text
        else:
            # All retries failed
            print("All Gemini retries failed, returning original text")
            return text

        # Restore glossary terms
        translated_text = self._restore_glossary_terms(translated_text, term_placeholders)

        # Restore Jinja2 elements
        final_text = self.parser.restore_jinja2_elements(translated_text)

        # Cache the result
        if target_language not in self.cache:
            self.cache[target_language] = {}
        self.cache[target_language][cache_key] = final_text
        self._save_cache()

        return final_text


def get_translation_service(service_type: str = "free", **kwargs) -> TranslationService:
    """Factory function to get appropriate translation service

    Args:
        service_type: One of "free", "gemini", or "google_cloud"
        **kwargs: Additional arguments passed to the service constructor

    Returns:
        TranslationService instance
    """
    if service_type == "google_cloud":
        if not kwargs.get("project_id"):
            raise ValueError("project_id required for Google Cloud Translation")
        return GoogleCloudTranslationService(**kwargs)
    elif service_type == "gemini":
        return GeminiTranslationService(**kwargs)
    elif service_type == "free":
        return FreeTranslationService(**kwargs)
    else:
        raise ValueError(f"Unknown service type: {service_type}. Use 'free', 'gemini', or 'google_cloud'")