#!/usr/bin/env python3
"""
Simple translation helper for report content.
Translates rendered HTML content while preserving HTML tags and scientific terms.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.translation_service import get_translation_service


class HTMLContentTranslator:
    """Translates HTML content while preserving tags and structure"""

    def __init__(self, service_type="free", **kwargs):
        self.translation_service = get_translation_service(service_type, **kwargs)

    def extract_style_blocks(self, text: str) -> tuple[str, Dict[str, str]]:
        """Extract and protect <style> blocks from translation"""
        style_map = {}
        counter = 0

        # Pattern for <style>...</style> blocks (including content)
        pattern = re.compile(r'<style[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)

        def replace_style(match):
            nonlocal counter
            placeholder = f"@@STYL_{counter}@@"  # Changed from STYLE to STYL to match other placeholders
            style_map[placeholder] = match.group(0)
            counter += 1
            return placeholder

        processed_text = pattern.sub(replace_style, text)
        return processed_text, style_map

    def extract_class_attributes(self, text: str) -> tuple[str, Dict[str, str]]:
        """Extract and protect class attributes from translation"""
        class_map = {}
        counter = 0

        # Pattern for class="..." attributes
        pattern = re.compile(r'class="[^"]*"', re.IGNORECASE)

        def replace_class(match):
            nonlocal counter
            placeholder = f"@@CLASS_{counter}@@"
            class_map[placeholder] = match.group(0)
            counter += 1
            return placeholder

        processed_text = pattern.sub(replace_class, text)
        return processed_text, class_map

    def extract_style_attributes(self, text: str) -> tuple[str, Dict[str, str]]:
        """Extract and protect inline style attributes from translation"""
        style_attr_map = {}
        counter = 0

        # Pattern for style="..." attributes
        pattern = re.compile(r'style="[^"]*"', re.IGNORECASE)

        def replace_style_attr(match):
            nonlocal counter
            placeholder = f"@@STYLEATTR_{counter}@@"
            style_attr_map[placeholder] = match.group(0)
            counter += 1
            return placeholder

        processed_text = pattern.sub(replace_style_attr, text)
        return processed_text, style_attr_map

    def extract_html_tags(self, text: str) -> tuple[str, Dict[str, str]]:
        """Replace HTML tags with placeholders"""
        tag_map = {}
        counter = 0

        # Pattern for HTML tags
        pattern = re.compile(r'<[^>]+>')

        def replace_tag(match):
            nonlocal counter
            placeholder = f"@@HTML_{counter}@@"
            tag_map[placeholder] = match.group(0)
            counter += 1
            return placeholder

        processed_text = pattern.sub(replace_tag, text)
        return processed_text, tag_map

    def restore_placeholders(self, text: str, *maps: Dict[str, str]) -> str:
        """Restore all placeholders from multiple maps"""
        for placeholder_map in maps:
            for placeholder, original in placeholder_map.items():
                text = text.replace(placeholder, original)
        return text

    def translate_html_content(self, html: str, target_language: str) -> str:
        """Translate HTML content while preserving structure"""
        # If target is English, return as-is
        if target_language == "en":
            return html

        # Extract elements in order (most specific to least specific)
        # 1. Style blocks (CSS code)
        processed, style_map = self.extract_style_blocks(html)

        # 2. Class attributes
        processed, class_map = self.extract_class_attributes(processed)

        # 3. Inline style attributes
        processed, style_attr_map = self.extract_style_attributes(processed)

        # 4. HTML tags
        processed, tag_map = self.extract_html_tags(processed)

        # Free translation services have character limits (typically 5000)
        # Chunk the text if needed
        MAX_CHUNK_SIZE = 4500  # Leave buffer for safety

        if len(processed) > MAX_CHUNK_SIZE:
            print(f"Content too large ({len(processed)} chars), chunking for translation...")
            # Split by newlines to keep context together
            lines = processed.split('\n')
            chunks = []
            current_chunk = []
            current_length = 0

            for line in lines:
                line_length = len(line) + 1  # +1 for newline
                if current_length + line_length > MAX_CHUNK_SIZE and current_chunk:
                    # Save current chunk and start new one
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_length = line_length
                else:
                    current_chunk.append(line)
                    current_length += line_length

            # Add final chunk
            if current_chunk:
                chunks.append('\n'.join(current_chunk))

            print(f"Split into {len(chunks)} chunks")

            # Translate each chunk
            translated_chunks = []
            for i, chunk in enumerate(chunks, 1):
                try:
                    print(f"Translating chunk {i}/{len(chunks)} ({len(chunk)} chars)...")
                    translated_chunk = self.translation_service.translate_text(chunk, target_language)
                    translated_chunks.append(translated_chunk)
                except Exception as e:
                    print(f"Translation error on chunk {i}: {e}")
                    translated_chunks.append(chunk)  # Use original on error

            translated = '\n'.join(translated_chunks)
            print(f"Translation complete")
        else:
            # Translate in one go
            try:
                print(f"Translating content to {target_language} ({len(processed)} chars)...")
                translated = self.translation_service.translate_text(processed, target_language)
                print(f"Translation complete")
            except Exception as e:
                print(f"Translation error: {e}")
                return html  # Return original on error

        # Restore all placeholders in reverse order (LIFO - last extracted, first restored)
        result = self.restore_placeholders(translated, tag_map, style_attr_map, class_map, style_map)

        return result


def get_language_name(lang_code: str) -> str:
    """Get full language name from code"""
    names = {
        'en': 'English',
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
    return names.get(lang_code, lang_code.upper())


if __name__ == "__main__":
    # Simple test
    translator = HTMLContentTranslator()

    test_html = """
    <div class="section">
        <h2>Dysbiosis Index</h2>
        <p>The patient shows mild dysbiosis with elevated Actinomycetota levels.</p>
    </div>
    """

    print("Original:")
    print(test_html)

    print("\nTranslated to Polish:")
    translated = translator.translate_html_content(test_html, 'pl')
    print(translated)
