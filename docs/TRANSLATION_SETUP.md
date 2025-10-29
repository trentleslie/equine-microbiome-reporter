# Translation Setup Guide

## Overview

The Equine Microbiome Reporter now supports multi-language report generation using Google Translate API (both free and paid versions).

## Features

- **Multi-language support**: English, Polish, Japanese, and more
- **Free translation service**: No API key required (uses deep-translator or googletrans)
- **Google Cloud Translation API**: Professional translation with better accuracy (requires API key)
- **Scientific terminology preservation**: Bacterial names and medical terms are preserved
- **HTML structure preservation**: Report formatting remains intact
- **Translation caching**: Reduces API costs and speeds up repeated translations

## Quick Start

### 1. Install Translation Dependencies

```bash
# For free translation service (no API key required)
poetry install --with translation-free

# For Google Cloud Translation API (requires credentials)
poetry install --with translation
```

### 2. Configure Environment Variables

The `.env` file already includes translation settings:

```bash
# Translation service: "free" (no API key) or "google_cloud" (requires credentials)
TRANSLATION_SERVICE=free

# Target languages (comma-separated): pl=Polish, ja=Japanese, de=German, etc.
TRANSLATION_TARGET_LANGUAGES=pl,ja

# Google Cloud Translation (optional, only if using google_cloud service)
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_CLOUD_CREDENTIALS_PATH=

# Translation cache directory
TRANSLATION_CACHE_DIR=translation_cache
```

### 3. Run the Demo

```bash
./demo.sh
```

The demo script will:
1. Check your environment
2. Ask which languages you want to generate reports in
3. Generate reports in all selected languages
4. Display results with file paths

## Usage Examples

### Using the Demo Script (Interactive)

```bash
./demo.sh
```

When prompted for languages:
- Press Enter for English only
- Enter `en,pl` for English and Polish
- Enter `en,pl,ja` for English, Polish, and Japanese

### Programmatic Usage

```python
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

# Create patient info
patient = PatientInfo(
    name="Montana",
    age="10 years",
    species="Equine",
    sample_number="DEMO-001"
)

# Generate English report
generate_clean_report(
    "data/sample_1.csv",
    patient,
    "report_en.pdf",
    language="en"
)

# Generate Polish report
generate_clean_report(
    "data/sample_1.csv",
    patient,
    "report_pl.pdf",
    language="pl"
)

# Generate Japanese report
generate_clean_report(
    "data/sample_1.csv",
    patient,
    "report_ja.pdf",
    language="ja"
)
```

## Supported Languages

The free translation service supports 100+ languages. Common options:

- `en` - English (default, no translation)
- `pl` - Polish
- `ja` - Japanese
- `de` - German
- `es` - Spanish
- `fr` - French
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `zh` - Chinese
- `ko` - Korean

## Translation Services Comparison

### Free Translation Service (Default)

**Pros:**
- No API key required
- No cost
- Easy setup
- Good for demos and testing

**Cons:**
- Slower translation (line-by-line processing)
- May have rate limits
- Less accurate than professional service
- No official support

### Google Cloud Translation API

**Pros:**
- Fast and accurate
- Professional quality
- Batch translation support
- Official Google support
- Custom glossaries available

**Cons:**
- Requires Google Cloud account
- Costs ~$20 per million characters
- Setup requires credentials file

## Setup Google Cloud Translation (Optional)

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable the Cloud Translation API
3. Create a service account and download JSON credentials
4. Update `.env`:

```bash
TRANSLATION_SERVICE=google_cloud
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_CREDENTIALS_PATH=/path/to/credentials.json
```

## Scientific Terminology

The translation service preserves:

- **Bacterial names**: Actinomycetota, Bacillota, Bacteroidota, etc.
- **Medical terms**: dysbiosis, microbiome, pathogen, etc.
- **Technical terms**: 16S rRNA, sequencing, reference range, etc.
- **HTML tags**: All formatting is preserved

See `src/translation_service.py` for the complete glossary.

## Translation Cache

Translations are cached to disk in the `TRANSLATION_CACHE_DIR` directory. This:
- Speeds up repeated translations
- Reduces API costs for Google Cloud service
- Can be safely deleted to clear cache

## Troubleshooting

### "Translation service not available"

**Solution:** Install translation dependencies:
```bash
poetry install --with translation-free
```

### Slow Translation

**Cause:** The free translation service processes HTML line-by-line, which can be slow for large reports.

**Solutions:**
1. Use Google Cloud Translation API (much faster)
2. Translation is cached, so subsequent reports with similar content will be faster
3. Consider translating only the most important languages

### Translation Quality Issues

**Cause:** Free translation services may not be as accurate as professional services.

**Solutions:**
1. Use Google Cloud Translation API for better quality
2. Review and correct translations manually
3. Add domain-specific terms to the glossary in `src/translation_service.py`

### Polish Characters Not Displaying

**Cause:** Font may not support Polish characters (ą, ć, ę, ł, ń, ó, ś, ź, ż).

**Solution:** The report uses standard fonts that support Latin Extended-A characters. If issues persist, check your PDF viewer.

## Output Files

For each language, the script generates:
- `report_[lang].pdf` - Final PDF report (5 pages)
- `report_[lang].html` - HTML version for debugging

Example output structure:
```
demo_output_20250128_123456/
├── clean_report_en.pdf     # English report
├── clean_report_en.html
├── clean_report_pl.pdf     # Polish report
├── clean_report_pl.html
├── clean_report_ja.pdf     # Japanese report
└── clean_report_ja.html
```

## Next Steps

- Add more languages to `TRANSLATION_TARGET_LANGUAGES`
- Customize the scientific glossary in `src/translation_service.py`
- Integrate translation into the full pipeline (`scripts/full_pipeline.py`)
- Create translated versions of templates for perfect translations

## Support

For issues or questions:
1. Check the logs in the output directory
2. Review `src/translation_service.py` for configuration options
3. See `src/translation_service.py` for glossary customization
4. Consult Google Cloud Translation API documentation for advanced features
