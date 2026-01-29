"""
Tests for the translation system: load_translations(), make_t_function(),
and translations.yaml integrity.

Note: We replicate the translation-loading logic here rather than importing
from scripts.generate_clean_report, because that module imports weasyprint
at module level which can be slow or unavailable in test environments.
"""

import pytest
import yaml
from pathlib import Path


TRANSLATIONS_PATH = Path(__file__).parent.parent / "config" / "translations.yaml"


def load_translations(language: str) -> dict:
    """Mirror of scripts.generate_clean_report.load_translations."""
    with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
        all_translations = yaml.safe_load(f)

    en_strings = all_translations.get("en", {})

    if language == "en":
        return en_strings

    lang_strings = all_translations.get(language, {})
    merged = dict(en_strings)
    merged.update(lang_strings)
    return merged


def make_t_function(translations: dict):
    """Mirror of scripts.generate_clean_report.make_t_function."""
    def t(key: str, **kwargs) -> str:
        value = translations.get(key, key)
        if kwargs:
            try:
                value = value.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return value
    return t


# ---------------------------------------------------------------------------
# load_translations() tests
# ---------------------------------------------------------------------------

class TestLoadTranslations:
    def test_load_english(self):
        result = load_translations("en")
        assert isinstance(result, dict)
        assert len(result) > 0
        assert "dysbiosis_index" in result

    def test_load_polish(self):
        en = load_translations("en")
        pl = load_translations("pl")
        assert isinstance(pl, dict)
        # Fallback should fill gaps — PL must have all EN keys
        for key in en:
            assert key in pl, f"Polish translations missing key: {key}"

    def test_load_german(self):
        en = load_translations("en")
        de = load_translations("de")
        assert isinstance(de, dict)
        for key in en:
            assert key in de, f"German translations missing key: {key}"

    def test_unsupported_language_falls_back(self):
        """load_translations('xx') returns EN strings (no crash)."""
        en = load_translations("en")
        xx = load_translations("xx")
        assert xx == en


# ---------------------------------------------------------------------------
# make_t_function() tests
# ---------------------------------------------------------------------------

class TestMakeTFunction:
    @pytest.fixture()
    def t(self):
        return make_t_function(load_translations("en"))

    def test_simple_lookup(self, t):
        assert t("dysbiosis_index") == "Dysbiosis Index"

    def test_missing_key_returns_key(self, t):
        assert t("nonexistent_key") == "nonexistent_key"

    def test_format_placeholders(self, t):
        result = t("page_x_of_y", current=3, total=5)
        assert result == "Page 3 of 5"

    def test_format_missing_kwarg_no_crash(self, t):
        # Should not raise even when kwargs are missing
        result = t("page_x_of_y")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# translations.yaml integrity tests
# ---------------------------------------------------------------------------

class TestTranslationsYamlIntegrity:
    @pytest.fixture(scope="class")
    def raw_yaml(self):
        with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.fixture(scope="class")
    def en_keys(self, raw_yaml):
        return set(raw_yaml.get("en", {}).keys())

    def test_all_languages_have_same_keys(self, raw_yaml, en_keys):
        """PL and DE key sets must be supersets of EN keys.

        This checks key *existence* only — placeholder values like
        '[PL] Dysbiosis Index' are acceptable.
        """
        for lang in ("pl", "de"):
            lang_keys = set(raw_yaml.get(lang, {}).keys())
            missing = en_keys - lang_keys
            assert not missing, (
                f"Language '{lang}' is missing keys present in EN: {sorted(missing)}"
            )

    def test_chart_label_keys_exist(self, raw_yaml):
        en = raw_yaml.get("en", {})
        for key in ("percentage", "species_title", "phylum_title",
                     "reference_legend", "ref"):
            assert key in en, f"Chart label key '{key}' missing from EN translations"

    def test_pending_clinical_review_key_exists(self, raw_yaml):
        for lang in ("en", "pl", "de"):
            lang_dict = raw_yaml.get(lang, {})
            assert "pending_clinical_review" in lang_dict, (
                f"'pending_clinical_review' missing from '{lang}' translations"
            )

    def test_no_clinical_fallback_keys(self, raw_yaml):
        """Confirm clinical fallback keys were pruned from the YAML."""
        en = raw_yaml.get("en", {})
        for key in ("assessment_normal", "rec_normal_1", "guide_normal_1"):
            assert key not in en, (
                f"Clinical fallback key '{key}' should not exist in EN translations"
            )
