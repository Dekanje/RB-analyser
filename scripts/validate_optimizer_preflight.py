#!/usr/bin/env python3
"""Validate the pinned AlphaRune registry for experimental optimization.

A Radiance printing uses a set_code that need not be 'RAD' even when its
exact public_code is registered. Never count matching set_code values as
evidence that the correct card abilities are implemented.
"""
import argparse
import json
import pathlib

REQUIRED_RADIANCE_IDS = (
    "RAD-149/167",  # Riven Legend
    "RAD-086/167",  # K'Sante chosen champion
    "RAD-153/167",  # Evelynn Legend
    "RAD-150/167",  # Riven signature
    "RAD-148/167",  # K'Sante signature
    "RAD-041/167",  # Hush
    "RAD-105/167",  # Reckless Innovator
    "RAD-014/167",  # Shimmering Swimmer
)

def validate_registry(path, *, expected_count=988, required=REQUIRED_RADIANCE_IDS):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    cards = data.get("cards") if isinstance(data, dict) else None
    if not isinstance(cards, list):
        raise ValueError("Engine registry must be a JSON object with a cards list")
    if len(cards) != expected_count:
        raise ValueError(f"Expected {expected_count} compiled cards, found {len(cards)}")
    codes = [card.get("public_code") for card in cards]
    if not all(isinstance(code, str) and code for code in codes):
        raise ValueError("Missing compiled public_code in registry")
    if len(set(codes)) != len(codes):
        raise ValueError("Duplicate public_code in compiled registry")
    missing = sorted(set(required) - set(codes))
    if missing:
        raise ValueError(f"Missing pinned Radiance implementations: {missing}")
    # The registered ID is a necessary but not sufficient mechanics check.
    return {"compiled_card_definitions": len(cards),
            "required_radiance_ids": len(required),
            "mechanics_certified": False,
            "full_radiance_supported": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=pathlib.Path)
    args = parser.parse_args()
    print("OPTIMIZER_REGISTRY_PREFLIGHT_PASS",
          json.dumps(validate_registry(args.registry)), flush=True)
