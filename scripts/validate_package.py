#!/usr/bin/env python3
"""Check local documentation links and unchanged source snapshot hashes."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def main():
    checked = 0
    errors = []
    for file in ROOT.rglob("*.md"):
        # Snapshots preserve originals, including historical owner references.
        if "sources" in file.relative_to(ROOT).parts:
            continue
        content = file.read_text(encoding="utf-8")
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            if link.startswith(("https://", "http://", "mailto:")):
                continue
            target, _, fragment = link.partition("#")
            resolved = (file.parent / target).resolve() if target else file
            checked += 1
            if not resolved.exists() or not resolved.is_relative_to(ROOT):
                errors.append(f"{file.name}: invalid local link {link}")
            elif fragment:
                value = resolved.read_text(encoding="utf-8")
                if 'id="' + fragment + '"' not in value:
                    errors.append(f"{file.name}: missing explicit anchor {fragment}")
    manifest = json.loads((ROOT / "sources/manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        data = (ROOT / name).read_bytes()
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            errors.append("source drift: " + name)
    print(json.dumps({"local_links": checked, "source_snapshots": len(manifest), "errors": errors}))
    return int(bool(errors))

if __name__ == "__main__":
    raise SystemExit(main())
