#!/usr/bin/env python3
"""Versioned sideboard-only registration repair. Never rewrites source evidence."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re

from sideboard_deck import HEADINGS, CARD_ROW, parse_deck

SCHEMA = "sideboard-order-v2"
SOURCE_MANIFEST = "5162e2548f6bbd402aa72569d661e3628ab8cdcec32df83d6958fab81e8b30fb"


def digest(raw):
    return sha256(raw).hexdigest()


def ordered(raw):
    text = raw.decode("utf-8")
    parse_deck(text)
    sections = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith(":") and line[:-1] in HEADINGS:
            sections[line[:-1]] = []
        else:
            match = CARD_ROW.fullmatch(line)
            if not match:
                raise ValueError("invalid card row")
            sections[next(reversed(sections))].extend([match[2]] * int(match[1]))
    return sections


def sideboard_offset(raw):
    matches = list(re.finditer(rb"(?m)^[ \t]*Sideboard:[ \t]*\r?$", raw))
    if len(matches) != 1:
        raise ValueError("expected exactly one sideboard header")
    return matches[0].start()


def require_ordered(original, candidate):
    a, b = ordered(original), ordered(candidate)
    for section in HEADINGS[:-1]:
        if a[section] != b[section]:
            raise ValueError("ordered playable input changed: " + section)
    if Counter(a["Sideboard"]) == Counter(b["Sideboard"]):
        raise ValueError("no sideboard composition change")


def repair(original, candidate):
    a, b = ordered(original), ordered(candidate)
    for section in HEADINGS[:-1]:
        if Counter(a[section]) != Counter(b[section]):
            raise ValueError("playable composition changed: " + section)
    result = original[:sideboard_offset(original)] + candidate[sideboard_offset(candidate):]
    require_ordered(original, result)
    if Counter(ordered(result)["Sideboard"]) != Counter(b["Sideboard"]):
        raise ValueError("candidate sideboard not preserved")
    return result


def prepare(selected, structural, output):
    source = (structural / "structural_manifest.json").read_bytes()
    if digest(source) != SOURCE_MANIFEST:
        raise ValueError("unexpected historical structural manifest")
    manifest = json.loads(source)
    originals = {}
    for path in sorted(selected.glob("*.txt")):
        raw = path.read_bytes()
        h = digest(raw)
        if h in originals:
            raise ValueError("duplicate original")
        originals[h] = path
    if len(originals) != 58:
        raise ValueError("expected 58 original registrations")
    rows = []
    seen = set()
    for record in manifest["records"]:
        original = originals[record["original_sha256"]]
        raw = original.read_bytes()
        candidates = [v for v in record["variants"] if v["kind"] == "sideboard"]
        if len(candidates) != 3:
            raise ValueError("expected three sideboard candidates per legend")
        for variant in candidates:
            relative = Path(variant["path"])
            if relative.is_absolute() or ".." in relative.parts or relative in seen:
                raise ValueError("invalid or duplicate candidate path")
            seen.add(relative)
            prior = (structural / relative).read_bytes()
            if digest(prior) != variant["sha256"]:
                raise ValueError("historical candidate hash mismatch")
            fixed = repair(raw, prior)
            rows.append((relative, fixed, {
                "legend": record["legend"], "original": original.name,
                "original_sha256": digest(raw), "historical_path": str(relative),
                "historical_sha256": digest(prior), "corrected_path": str(relative),
                "corrected_sha256": digest(fixed),
                "reordered_sections": [s for s in HEADINGS[:-1]
                    if ordered(raw)[s] != ordered(prior)[s]],
            }))
    if len(rows) != 174 or len({r[2]["legend"] for r in rows}) != 58:
        raise ValueError("incomplete population")
    # Refuse any existing output namespace; never modify historical inputs.
    output.mkdir(parents=True, exist_ok=False)
    for relative, fixed, _ in rows:
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(fixed)
    result = {"schema": SCHEMA, "source_manifest_sha256": digest(source),
              "registry_sha256": manifest["native_registry_sha256"],
              "legends": 58, "candidates": 174, "native_validated": False,
              "fitness_evaluated": False, "adopted": 0,
              "records": [r[2] for r in rows]}
    (output / "manifest_v2.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("selected", "structural", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    result = prepare(a.selected, a.structural, a.output)
    print(SCHEMA, result["legends"], result["candidates"],
          "reordered", sum(bool(r["reordered_sections"]) for r in result["records"]))


if __name__ == "__main__":
    main()
