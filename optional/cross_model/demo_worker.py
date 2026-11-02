#!/usr/bin/env python3
"""Transport fixture only. Never use this synthetic report as an actual review."""
import json
import sys

request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
json.dump({"snapshot": request["snapshot"], "reviewer": "synthetic-transport-fixture",
           "independent": True, "dimensions": ["correctness", "security", "end-to-end", "conventions"],
           "findings": [], "verified_fixed": [],
           "limitations": "Synthetic transport test; no model was called and no semantic review performed."}, sys.stdout)
