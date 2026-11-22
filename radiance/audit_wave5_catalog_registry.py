#!/usr/bin/env python3
"""Fail-closed Radiance catalog/compiled-registry reconciliation.

This is an audit, not a gameplay certification. Variant rules fingerprints
from the gallery are leads, not proof of functional equivalence.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def audit(catalog, registry):
    cards = catalog["cards"]
    compiled = registry["cards"]
    codes = [x["public_code"] for x in cards]
    assert len(cards) == 219, f"Catalog changed: {len(cards)} printings"
    assert len(codes) == len(set(codes)), "Duplicate catalog printing codes"
    bases = {f"RAD-{i:03d}/167" for i in range(1, 168)}
    assert bases <= set(codes), f"Missing numbered catalog IDs: {sorted(bases-set(codes))}"
    compiled_codes = [x.get("public_code") for x in compiled if x.get("public_code")]
    assert len(compiled_codes) == len(set(compiled_codes)), "Duplicate compiled public codes"
    by_code = {x["public_code"]: x for x in compiled if x.get("public_code")}
    registered = sorted(bases & by_code.keys())
    missing = sorted(bases - by_code.keys())
    # Do not assume equal artwork/metadata or identical text hashes proves
    # gameplay equivalence. This audit deliberately never marks mechanics verified.
    print(json.dumps({
        "catalog_printings": len(cards),
        "base_identities": len(bases),
        "compiled_registry_size": len(compiled),
        "registered_base_count": len(registered),
        "missing_base_count": len(missing),
        "missing_base_codes": missing,
        "extra_printings_requiring_rules_equivalence_review":
            sorted(set(codes)-bases),
        "all_mechanics_verified": False
    }, indent=2))
    return bool(missing)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("catalog",type=Path)
    p.add_argument("registry",type=Path)
    p.add_argument("--require-complete",action="store_true")
    a=p.parse_args()
    missing=audit(json.loads(a.catalog.read_text()),
                  json.loads(a.registry.read_text()))
    if a.require_complete and missing:
        raise SystemExit("FAIL_CLOSED: numbered Radiance gameplay coverage incomplete")

if __name__ == "__main__":
    main()
