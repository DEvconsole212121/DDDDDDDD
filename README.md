# BidiSite Audit

**An open-source, offline HTML linter for French/Arabic and right-to-left websites.** It helps developers detect concrete internationalization and basic accessibility problems before publishing a site.

> Early project (v0.1.0). No existing user base, download count, external contributor base, or impact is claimed. This is not a WCAG, SEO or security certification.

## The problem

French/Arabic websites mix left-to-right and right-to-left text. Missing `lang` and `dir` annotations can lead to confusing presentation and assistive-technology behavior. Missing image alternatives and unnamed form fields create practical accessibility barriers. Developers need a small tool they can run offline and integrate into tests.

## Install

Python 3.10+:

```bash
python -m pip install -e .
```

## Run

```bash
bidisite-audit examples/fr-ar.html
bidisite-audit examples/intentional-issues.html --format json
bidisite-audit examples/intentional-issues.html --format sarif --fail-on none > findings.sarif
bidisite-audit ./my-static-site --fail-on warning
```

The deliberately broken example reports five findings. The clean example has no findings. Error findings cause exit code 1 by default; use `--fail-on none` for reporting-only runs.

## Checks

| Rule | What it catches |
| --- | --- |
| html-lang | HTML page missing a language |
| arabic-document-direction | Arabic document without RTL direction |
| arabic-text-lang | Arabic text without a matching inherited language |
| arabic-text-direction | Arabic text without RTL or auto direction |
| invalid-dir | Invalid direction attribute |
| img-alt | Image missing an alt attribute |
| image-input-alt | Image submit button missing alt text |
| form-control-name | Form field lacking a detectable name |
| duplicate-id | Duplicate element identifiers |
| external-link-noopener | New-tab link without noopener |
| viewport | Missing responsive viewport |
| document-title | Missing or empty document title |
| html-element | Missing html element |

Checks are intentionally heuristic. False positives and false negatives are possible, especially in JavaScript-generated pages and complex form structures. The tool does not crawl public URLs, execute JavaScript, or test rendered browsers.

## Tests & GitHub Actions

```bash
python -m unittest discover -s tests -v
```

A GitHub Actions workflow tests Python 3.10 and 3.13 and checks both example files.

## Documentation / multilingual

**Français :** Un analyseur HTML open source pour les pages français/arabe. Détecte certaines erreurs de direction RTL, de langue, d'images et de formulaires. Ne remplace pas un audit complet.

**العربية:** أداة مفتوحة المصدر تفحص ملفات HTML محلياً للمساعدة في كشف أخطاء اتجاه الكتابة العربية واللغة وتسميات الصور والنماذج. لا تغني عن فحص إمكانية الوصول الشامل.

See [Contributing](CONTRIBUTING.md), [Security](SECURITY.md), [Roadmap](docs/ROADMAP.md) and the [MIT license](LICENSE).

## References

- [W3C: Structural markup and right-to-left text](https://www.w3.org/International/questions/qa-html-dir.en.html)
- [W3C WAI: Form labels](https://www.w3.org/WAI/tutorials/forms/labels/)

Real user reports, third-party reviews and community-maintainer contributions are welcome. Usage statistics will be published only when verifiable.
