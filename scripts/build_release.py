#!/usr/bin/env python3
"""Create a deterministic local ZIP; never copy runtime state or unknown files."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {"scripts", "references", "sources", "examples", "tests", "agents"}
EXTENSIONS = {".py", ".md", ".json", ".yaml"}

def files():
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        name = p.relative_to(ROOT)
        if name.parts[0] not in DIRECTORIES and name.as_posix() not in {"SKILL.md", "README.md"}:
            continue
        if p.suffix not in EXTENSIONS or "__pycache__" in name.parts:
            continue
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT):
            raise ValueError("package symlink outside source: " + name.as_posix())
        if p.name in {"state.json", "approval.json"} or p.name.startswith("check-"):
            raise ValueError("runtime evidence found inside release tree: " + name.as_posix())
        yield p

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if out.is_relative_to(ROOT):
        raise ValueError("ZIP must be outside the source tree")
    payload = {}
    for p in files():
        data = p.read_bytes()
        value = data.decode("utf-8")
        if re.search(r"C:[\\/]Users[\\/]|/home/[A-Za-z0-9_.-]+/|sk-[A-Za-z0-9_-]{20,}", value, re.I):
            raise ValueError("possible private path/secret in " + p.relative_to(ROOT).as_posix())
        payload[p.relative_to(ROOT).as_posix()] = data
    manifest = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in payload.items()}
    payload["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo("review-judgment-suite/" + name, (2026, 11, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        for name, data in payload.items():
            assert archive.read("review-judgment-suite/" + name) == data
    print(json.dumps({"file": out.name, "entries": len(payload), "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))

if __name__ == "__main__":
    main()
