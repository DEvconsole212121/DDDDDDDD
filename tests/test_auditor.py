import tempfile
import unittest
from pathlib import Path
from bidisite_audit.auditor import audit_html, audit_path
from bidisite_audit.__main__ import sarif, main

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.html = Path(self.tmp.name) / "index.html"

    def rules(self, source):
        self.html.write_text(source, encoding="utf-8")
        return {f.rule for f in audit_html(self.html)}

    def test_clean_bilingual(self):
        self.assertFalse(self.rules('<html lang="fr"><head><title>Bonjour</title><meta name="viewport" content="width=device-width"></head><body><span lang="ar" dir="rtl">مرحبا</span><label for="x">Email</label><input id="x"></body></html>'))

    def test_missing_lang(self):
        self.assertIn("html-lang", self.rules("<html><head><title>Test</title></head></html>"))

    def test_missing_alt(self):
        self.assertIn("img-alt", self.rules('<html lang="fr"><img src="x"></html>'))

    def test_missing_form_label(self):
        self.assertIn("form-control-name", self.rules('<html lang="fr"><input id="x"></html>'))

    def test_implicit_form_label(self):
        self.assertNotIn("form-control-name", self.rules('<html lang="fr"><label>Nom<input></label></html>'))

    def test_aria_label(self):
        self.assertNotIn("form-control-name", self.rules('<html lang="fr"><input aria-label="Recherche"></html>'))

    def test_missing_aria_ref(self):
        self.assertIn("form-control-name", self.rules('<html lang="fr"><input aria-labelledby="missing"></html>'))

    def test_duplicate_id(self):
        self.assertIn("duplicate-id", self.rules('<html lang="fr"><p id="x"></p><p id="x"></p></html>'))

    def test_arabic_context(self):
        self.assertIn("arabic-text-direction", self.rules('<html lang="fr"><p>مرحبا</p></html>'))

    def test_arabic_document(self):
        self.assertNotIn("arabic-document-direction", self.rules('<html lang="ar" dir="rtl"><p>مرحبا</p></html>'))

    def test_invalid_dir(self):
        self.assertIn("invalid-dir", self.rules('<html lang="fr" dir="sideways"></html>'))

    def test_missing_title(self):
        self.assertIn("document-title", self.rules('<html lang="fr"></html>'))

    def test_empty_dir(self):
        with self.assertRaises(ValueError):
            audit_path(Path(self.tmp.name))

    def test_sarif(self):
        self.html.write_text('<html><img src="x"></html>')
        self.assertEqual(sarif(audit_html(self.html))["version"], "2.1.0")

if __name__ == "__main__":
    unittest.main()
