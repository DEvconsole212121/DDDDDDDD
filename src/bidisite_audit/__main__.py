import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .auditor import audit_path

def sarif(findings):
    return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [{"tool": {"driver": {"name": "BidiSite Audit", "version": __version__,
                      "rules": [{"id": r} for r in sorted({f.rule for f in findings})]}},
                      "results": [{"ruleId": f.rule, "level": f.severity,
                         "message": {"text": f.message},
                         "locations": [{"physicalLocation": {"artifactLocation": {"uri": f.file.replace(chr(92), "/")},
                                        "region": {"startLine": max(1, f.line)}}}]} for f in findings]}]}

def main(argv=None):
    p = argparse.ArgumentParser(description="Offline HTML accessibility and bilingual direction checks")
    p.add_argument("path", type=Path)
    p.add_argument("--format", choices=["text", "json", "sarif"], default="text")
    p.add_argument("--fail-on", choices=["none", "warning", "error"], default="error")
    p.add_argument("--version", action="version", version=__version__)
    a = p.parse_args(argv)
    try:
        findings = audit_path(a.path)
    except (ValueError, FileNotFoundError) as e:
        p.error(str(e))
    if a.format == "sarif":
        print(json.dumps(sarif(findings), ensure_ascii=False, indent=2))
    elif a.format == "json":
        print(json.dumps({"count": len(findings), "findings": [f.to_dict() for f in findings]}, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"{f.file}:{f.line}: {f.severity}: {f.rule}: {f.message}")
        print(f"{len(findings)} finding(s)")
    return int(a.fail_on != "none" and any(f.severity == "error" or a.fail_on == "warning" for f in findings))

if __name__ == "__main__":
    sys.exit(main())
