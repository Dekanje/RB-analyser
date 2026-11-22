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
    # The *actual* --dump-registry serializer writes "card_id", not "id".
    # Require an ID on every compiled row and reject collisions, even for
    # non-Radiance cards: aliasing makes card mechanics untrustworthy.
    assert all(x.get("card_id") is not None for x in compiled), "Compiled card missing card_id"
    engine_ids = [x["card_id"] for x in compiled]
    assert len(engine_ids) == len(set(engine_ids)), "Duplicate compiled engine IDs"

    # RAD-TBomb is the Ziggs Bomb token defined in the pinned implementation,
    # not one of the 219 physical gallery printings. Admit it ONLY if its
    # compiled identity matches that source exactly. Future gameplay tokens
    # need their own documented identity records and strict checks.
    known_tokens = {
        "RAD-TBomb": {
            "card_id": 982, "card_def_id": "rad-bomb-token",
            "name": "Bomb", "set": "RAD", "card_type": "gear",
            "super_type": "token"
        }
    }
    compiled_by_code = {x["public_code"]:x for x in compiled if x.get("public_code")}
    for code, requirements in known_tokens.items():
        row = compiled_by_code.get(code)
        if row is not None:
            assert all(row.get(k) == v for k,v in requirements.items()), (
                f"Unrecognized gameplay token identity for {code}: {row}"
            )
            assert "Bomb" in row.get("tags", []), f"Bomb token missing Bomb tag: {row}"
    unexpected_radiance = sorted(code for code in compiled_codes
                                 if code.startswith("RAD-") and
                                    code not in set(codes) and code not in known_tokens)
    assert not unexpected_radiance, f"Compiled Radiance codes absent from catalog: {unexpected_radiance}"
    by_code = {x["public_code"]: x for x in compiled if x.get("public_code")}
    registered = sorted(bases & by_code.keys())
    missing = sorted(bases - by_code.keys())
    # Do not assume equal artwork/metadata or identical text hashes proves
    # gameplay equivalence. This audit deliberately never marks mechanics verified.
    print(json.dumps({
        "catalog_printings": len(cards),
        "base_identities": len(bases),
        "compiled_registry_size": len(compiled),
        "explicit_non_gallery_token_codes": sorted(set(compiled_codes) & known_tokens.keys()),
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
