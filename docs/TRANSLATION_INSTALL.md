# Installing Translation Support

This guide explains how to enable multilingual report generation in the Equine Microbiome Reporter.

## Overview

The system supports generating reports in multiple languages:
- English (en) - default
- Polish (pl)
- Japanese (ja)
- Spanish (es)
- German (de)
- French (fr)
- And more...

Translation is powered by free services (no API key required):
- `deep-translator` (primary)
- `googletrans` (fallback)
- `translatepy` (backup)

## Installation Methods

### Method 1: Update Existing Conda Environment (Recommended)

If you already have the `equine-microbiome` conda environment set up:

```bash
# Activate the environment
conda activate equine-microbiome

# Install translation dependencies via pip
pip install deep-translator==1.11.4 googletrans==4.0.0rc1 translatepy==2.3

# Verify installation
python -c "import deep_translator, googletrans, translatepy; print('✓ Translation dependencies installed')"
```

### Method 2: Rebuild Environment from Scratch

If you want to rebuild the environment with all dependencies:

```bash
# Remove old environment (if exists)
conda deactivate
conda env remove -n equine-microbiome

# Create new environment from environment.yml
conda env create -f environment.yml

# Activate the new environment
conda activate equine-microbiome

# Verify translation support
python -c "import deep_translator, googletrans, translatepy; print('✓ Translation ready')"
```

### Method 3: Update Environment from YAML

If you've updated `environment.yml` and want to update your existing environment:

```bash
# Activate environment
conda activate equine-microbiome

# Update from YAML file
conda env update -f environment.yml --prune

# Verify installation
python -c "import deep_translator, googletrans, translatepy; print('✓ Translation updated')"
```

## Verification

To verify translation is working correctly:

```bash
# Activate environment
conda activate equine-microbiome

# Run a quick test
python << EOF
from scripts.translate_report_content import HTMLContentTranslator

translator = HTMLContentTranslator()
test = translator.translate_html_content("<p>Hello World</p>", "pl")
print("✓ Translation test successful")
print(f"Test output: {test}")
EOF
```

Expected output should contain Polish text like "Witaj świecie" (Hello World in Polish).

## Using Translation in demo.sh

Once dependencies are installed, run the demo script:

```bash
./demo.sh
```

When prompted for languages, enter:
- `en` for English only
- `pl` for Polish only
- `en,pl` for both English and Polish
- `en,pl,ja` for English, Polish, and Japanese

The script will automatically check for translation dependencies and provide installation instructions if they're missing.

## Troubleshooting

### Issue: "Translation dependencies not found"

**Solution**: Install the packages manually:
```bash
conda activate equine-microbiome
pip install deep-translator googletrans translatepy
```

### Issue: "ImportError: No module named 'deep_translator'"

**Solution**: Ensure you're in the correct conda environment:
```bash
conda activate equine-microbiome
which python  # Should show path to conda environment
pip list | grep translator  # Should show deep-translator
```

### Issue: Translation takes a long time

**Explanation**: Free translation services process content in chunks (4500 characters per request). A full 5-page report takes approximately 10-15 seconds to translate.

### Issue: Some text remains in English

**Expected behavior**: Scientific terms (bacterial names like "Actinomycetota", "Bacillota") and technical terminology are preserved in English to maintain accuracy and standardization.

### Issue: "Text length need to be between 0 and 5000 characters"

**Solution**: This has been fixed with automatic chunking. If you still see this error, ensure you have the latest version of `scripts/translate_report_content.py` with the chunking logic (lines 58-99).

## Technical Details

### Translation Process

1. **HTML Generation**: Report is generated in English with Jinja2 templates
2. **Tag Extraction**: HTML tags are replaced with placeholders (e.g., `@@HTML_0@@`)
3. **Chunking**: Large content (>4500 chars) is split into chunks
4. **Translation**: Each chunk is translated via free services
5. **Reassembly**: Chunks are rejoined and HTML tags restored
6. **PDF Generation**: Translated HTML is converted to PDF with WeasyPrint

### Character Limits

- Free translation services: ~5000 characters per request
- Our implementation: 4500 character chunks (safety buffer)
- Typical report size: ~21,000 characters (5 chunks)

### Glossary Preservation

The following terms are preserved in English:
- Bacterial phyla: Actinomycetota, Bacillota, Bacteroidota, Pseudomonadota, Fibrobacterota
- Medical terms: dysbiosis, microbiome, sequencing
- Veterinary terms: forage, hindgut, pathogen
- Technical terms: NGS, 16S rRNA, taxonomy

See `src/translation_service.py` for the complete glossary.

## Support

For issues or questions:
1. Check `TRANSLATION_SETUP.md` for general translation information
2. Review error messages from `demo.sh` (they include installation commands)
3. Verify conda environment: `conda list | grep translator`
4. Test imports manually: `python -c "import deep_translator"`

## Version Information

- deep-translator: 1.11.4
- googletrans: 4.0.0rc1
- translatepy: 2.3

Last updated: 2025-10-28
