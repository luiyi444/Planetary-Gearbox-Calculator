"""Tests for the translation table. Standard library only.

Run with:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

import i18n


class TranslationTableTests(unittest.TestCase):
    def test_every_key_exists_in_every_language(self) -> None:
        for key, entry in i18n.MESSAGES.items():
            with self.subTest(key=key):
                for language in i18n.LANGUAGES:
                    self.assertIn(language, entry, f"{key} lacks {language}")
                    self.assertTrue(entry[language].strip(), f"{key}/{language} is empty")

    def test_supported_languages_are_english_and_spanish(self) -> None:
        self.assertEqual(i18n.LANGUAGES, ("en", "es"))

    def test_missing_key_raises_instead_of_showing_raw_identifiers(self) -> None:
        with self.assertRaises(KeyError):
            i18n.tr("en", "ui.does_not_exist")

    def test_unknown_language_falls_back_to_the_reference_wording(self) -> None:
        """An unsupported code degrades to English, not to another translation."""
        self.assertEqual(i18n.normalize_language("de"), i18n.FALLBACK_LANGUAGE)
        self.assertEqual(i18n.normalize_language(None), i18n.FALLBACK_LANGUAGE)

    def test_the_interface_default_language_is_spanish(self) -> None:
        """No choice yet means the app default, which is a separate decision."""
        self.assertEqual(i18n.DEFAULT_LANGUAGE, "es")
        self.assertEqual(i18n.app_language(None), "es")
        self.assertEqual(i18n.app_language("en"), "en")
        self.assertEqual(i18n.app_language("de"), "en")

    def test_language_names_are_short_upper_case_labels(self) -> None:
        self.assertEqual(i18n.language_name("en"), "EN")
        self.assertEqual(i18n.language_name("es"), "ES")

    def test_placeholders_are_formatted_in_both_languages(self) -> None:
        for language in i18n.LANGUAGES:
            with self.subTest(language=language):
                text = i18n.tr(
                    language, "ui.caption.deviation", value="+0.00%"
                )
                self.assertIn("+0.00%", text)

    def test_a_formatted_message_matches_its_placeholders(self) -> None:
        """Every placeholder a key uses must be supplied, in both languages."""
        english = i18n.tr(
            "en", "core.sugg.planets", n=4, old=3, zs=18, zp=18, zr=54, i=4.0, d_ext=113.0
        )
        spanish = i18n.tr(
            "es", "core.sugg.planets", n=4, old=3, zs=18, zp=18, zr=54, i=4.0, d_ext=113.0
        )
        self.assertIn("N=4", english)
        self.assertIn("N=4", spanish)
        self.assertIn("en lugar de 3", spanish)


class DictionaryCoverageTests(unittest.TestCase):
    """Guard the drift that hurts most: a key the interface never uses, or worse."""

    def test_translations_are_not_identical_by_accident_for_prose_keys(self) -> None:
        """Sentences must differ between languages; formulas and tokens may not."""
        allowed_identical = {
            key
            for key, entry in i18n.MESSAGES.items()
            if "formula" in key or key.startswith("ui.table.") or "legend" in key
        }
        identical = [
            key
            for key, entry in i18n.MESSAGES.items()
            if entry["en"] == entry["es"] and key not in allowed_identical
        ]
        self.assertEqual(identical, [])


if __name__ == "__main__":
    unittest.main()
