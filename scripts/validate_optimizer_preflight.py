#!/usr/bin/env python3
"""Validate exact engine card identities without assuming all cards have print codes."""
import argparse
import collections
import json
import pathlib

REQUIRED_RADIANCE_IDS = (
    "RAD-149/167", "RAD-086/167", "RAD-153/167", "RAD-150/167",
    "RAD-148/167", "RAD-041/167", "RAD-105/167", "RAD-014/167",
)

def validate_registry(path, *, expected_count=988, required=REQUIRED_RADIANCE_IDS):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    cards = data.get("cards") if isinstance(data, dict) else None
    if not isinstance(cards, list):
        raise ValueError("Engine registry must be a JSON object with a cards list")
    if len(cards) != expected_count:
        raise ValueError(f"Expected {expected_count} compiled cards, found {len(cards)}")
    if any(not isinstance(card, dict) for card in cards):
        raise ValueError("Every registry entry must be a card object")
    # AlphaRune includes cards without an individual printing code (for example,
    # game-defined objects). Missing/duplicate *unrelated* print codes are not
    # evidence that any required Radiance implementation is absent.
    codes = collections.Counter(
        code.strip() for card in cards
        if isinstance((code := card.get("public_code")), str) and code.strip()
    )
    missing = sorted(set(required) - codes.keys())
    if missing:
        raise ValueError(f"Missing pinned Radiance implementations: {missing}")
    duplicated_required = sorted(code for code in required if codes[code] != 1)
    if duplicated_required:
        raise ValueError(f"Ambiguous pinned Radiance print identifiers: {duplicated_required}")
    return {
        "compiled_card_definitions": len(cards),
        "registered_print_codes": sum(codes.values()),
        "definitions_without_print_code": len(cards) - sum(codes.values()),
        "required_radiance_ids": len(required),
        "mechanics_certified": False,
        "full_radiance_supported": False,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=pathlib.Path)
    args = parser.parse_args()
    print("OPTIMIZER_REGISTRY_PREFLIGHT_PASS", json.dumps(validate_registry(args.registry)), flush=True)
