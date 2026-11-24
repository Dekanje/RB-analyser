#!/usr/bin/env python3
"""Compare an explicit dated ban snapshot with compiled registry and registrations.

This is a ban-only audit, not a complete deck validator or a current legality oracle.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata


def normalize(name):
    return unicodedata.normalize("NFKC", name).replace("’", "'").strip().casefold()


def indexes(profile, registry):
    if profile["schema_version"] != 1:
        raise ValueError("unsupported profile schema")
    cards = registry["cards"]
    codes = {}
    for card in cards:
        code = card.get("public_code")
        if code:
            if code in codes:
                raise ValueError("duplicate public code: " + code)
            codes[code] = card
    names, ids = {}, set()
    for entry in profile["ban_entries"]:
        c = codes.get(entry["code"])
        if c is None or (c["card_id"], c["name"], c["card_type"]) != (
                entry["engine_id"], entry["name"], entry["type"]):
            raise ValueError("profile-to-registry mapping failed: " + entry["code"])
        if c["card_id"] in ids:
            raise ValueError("duplicate banned identity")
        ids.add(c["card_id"])
        for name in [entry["name"], *entry["aliases"]]:
            key = normalize(name)
            if key in names and names[key] != entry["code"]:
                raise ValueError("ambiguous ban alias: " + name)
            names[key] = entry["code"]
    return names, ids


def scan_registration(text, banned_names):
    headings = ("Legend", "Champion", "MainDeck", "Battlefields", "Runes", "Sideboard")
    seen = []
    violations = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":"):
            section = line[:-1]
            if len(seen) >= len(headings) or section != headings[len(seen)]:
                raise ValueError("invalid registration section: " + section)
            seen.append(section)
            continue
        m = re.fullmatch(r"(\d+)\s+(.+)", line)
        if not seen or not m or int(m[1]) <= 0:
            raise ValueError("invalid registration row: " + line)
        name = re.sub(r" #\d+$", "", m[2])
        code = banned_names.get(normalize(name))
        if code:
            violations.append({"section": seen[-1], "code": code, "copies": int(m[1])})
    if tuple(seen) != headings:
        raise ValueError("missing registration sections")
    return violations


def audit(profile, registry, registrations):
    names, ids = indexes(profile, registry)
    native = {c["card_id"] for c in registry["cards"] if c["banned"]}
    by_id = {c["card_id"]: c for c in registry["cards"]}
    def describe(values):
        return [{"engine_id": i, "name": by_id[i]["name"],
                 "code": by_id[i].get("public_code")} for i in sorted(values)]
    findings = []
    counts = Counter()
    for label, paths in registrations.items():
        counts[label] = len(paths)
        for path in paths:
            for row in scan_registration(path.read_text(encoding="utf-8"), names):
                findings.append({"group": label, "file": path.name, **row})
    return {"profile_id": profile["profile_id"], "profile_banned_count": len(ids),
            "compiled_banned_count": len(native),
            "missing_native_bans": describe(ids-native),
            "extra_native_bans": describe(native-ids),
            "registration_counts": dict(counts), "ban_hits": findings,
            "complete_legality_verified": False,
            "native_enforcement_matches": native == ids}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("profile", "registry", "selected", "structural", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    raw = a.registry.read_bytes()
    profile = json.loads(a.profile.read_bytes())
    if sha256(raw).hexdigest() != profile["registry_reference_sha256"]:
        raise ValueError("wrong historical registry")
    groups = {"selected": sorted(a.selected.glob("*.txt")),
              "structural": sorted(a.structural.rglob("*.txt"))}
    if {k: len(v) for k,v in groups.items()} != {"selected":58,"structural":580}:
        raise ValueError("unexpected historical registration counts")
    result = audit(profile, json.loads(raw), groups)
    result["profile_sha256"] = sha256(a.profile.read_bytes()).hexdigest()
    result["registry_sha256"] = sha256(raw).hexdigest()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
