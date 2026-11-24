#!/usr/bin/env python3
"""Historical compiled identity/evidence inventory; never a legality or mechanics certification."""
import argparse
import ast
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

REGISTRY_SHA = "d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
XML_SHA = "a063b69b50f06a0730bf67c64ac939100b4e1912100d414ed6e0a57c105b9d5c"
EVIDENCE_COMMIT = "c35ceffa290056764df410ea38f97e01f2654031"
BASE_CODES = {f"RAD-{i:03d}/167" for i in range(1, 168)}


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError("historical evidence hash mismatch: " + str(path))
    return raw


def unique(items, key):
    result = {}
    for item in items:
        value = item[key]
        if value in result:
            raise ValueError("duplicate " + key + ": " + str(value))
        result[value] = item
    return result


def executed_tests(raw):
    root = ET.fromstring(raw)
    result = {}
    for case in root.iter("testcase"):
        name = case.attrib["classname"] + "." + case.attrib["name"]
        if name in result:
            raise ValueError("duplicate test ID " + name)
        result[name] = (
            case.get("status") == "run" and case.get("result") == "completed"
            and not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
        )
    return result


def literal_mappings(raw):
    # Do not execute the old ledger; only read its explicit mappings.
    tree = ast.parse(raw.decode("utf-8"))
    mappings = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"WAVE1", "KNOWN_GAPS"}:
                    if target.id in mappings:
                        raise ValueError("duplicate mapping")
                    mappings[target.id] = ast.literal_eval(node.value)
    if set(mappings) != {"WAVE1", "KNOWN_GAPS"}:
        raise ValueError("historical mappings absent")
    return mappings


def explicit_scenarios(mapping, tests, codes):
    result = {}
    for code, row in mapping.items():
        names = row["engine_scenarios"]
        if code not in codes or row["status"] != "accepted" or not names:
            raise ValueError("invalid explicit scenario mapping: " + code)
        if len(names) != len(set(names)) or not all(tests.get(n, False) for n in names):
            raise ValueError("missing, disabled or failed mapped scenario: " + code)
        result[code] = names
    return result


def inventory(registry, catalog, acceptance, mappings, tests):
    cards = registry["cards"]
    by_id = unique(cards, "card_id")
    unique(cards, "card_def_id")
    by_code = unique([c for c in cards if c.get("public_code")], "public_code")
    printings = unique(catalog["cards"], "public_code")
    unique(catalog["cards"], "gallery_id")
    if registry["num_cards"] != len(cards) or len(cards) != 1123:
        raise ValueError("unexpected historical registry size")
    if not BASE_CODES <= by_code.keys() or not BASE_CODES <= printings.keys():
        raise ValueError("numbered Radiance identity missing")
    if len(printings) != 219 or len(acceptance["cards"]) != 64:
        raise ValueError("unexpected historical coverage inputs")
    explicit = explicit_scenarios(acceptance["cards"], tests, by_code)
    gaps = mappings["KNOWN_GAPS"]
    if len(gaps) != 37 or not set(gaps) <= BASE_CODES:
        raise ValueError("unexpected historical gaps")
    wave = mappings["WAVE1"]
    names = {}
    for full, passed in tests.items():
        if passed:
            names.setdefault(full.rsplit(".", 1)[-1], []).append(full)
    entries = []
    for i, card in sorted(by_id.items()):
        code = card.get("public_code") or None
        links = []
        for short in wave.get(code, []):
            candidates = names.get(short, [])
            links.append({"historical_name": short, "enabled_test_matches": sorted(candidates),
                          "unambiguous": len(candidates) == 1})
        token = card.get("super_type") == "token"
        entries.append({
            "engine_id": i, "functional_id": card["card_def_id"],
            "identity_semantics": "compiled_definition_not_print_equivalence",
            "print_ids": [code] if code else [], "name": card["name"],
            "set": card["set"], "type": card["card_type"], "token": token,
            "compiled_banned": bool(card["banned"]),
            "legal_status": "not_registered_deck_material" if token else "official_legality_unverified",
            "effect_implementation": "registered_not_exhaustively_verified",
            "scenario_test_ids": explicit.get(code, []), "interaction_test_ids": [],
            "historical_test_name_links": links,
            "evidence_commit": EVIDENCE_COMMIT,
            "ruleset_id": "historical_compiled_registry_unverified_official_format",
            "verification_status": "scenario_verified" if code in explicit else "implemented_unverified",
            "known_gaps": gaps.get(code, []),
        })
    variant_rows = []
    for code, row in sorted(printings.items()):
        if code in BASE_CODES:
            continue
        letter = re.fullmatch(r"RAD-(\d{3})[A-Za-z]/167", code)
        base = f"RAD-{letter[1]}/167" if letter else None
        base_row = printings.get(base)
        metadata = ("type", "domains", "energy", "power", "might")
        equal = (all(row.get(k) == base_row.get(k) for k in metadata)
                 if base_row else None)
        rules_equal = (row.get("rules_text_sha256") == base_row.get("rules_text_sha256")
                       if base_row else None)
        variant_rows.append({
            "code": code, "gallery_id": row["gallery_id"], "candidate_base_code": base,
            "exact_compiled_identity": code in by_code,
            "metadata_equal": equal, "raw_rules_hash_equal": rules_equal,
            "equivalence_status": "unresolved",  # equality alone is not certification
            "category": "letter_variant" if letter else
                        "overnumbered" if row.get("overnumbered") else "special_or_rune",
        })
    return {
        "schema_version": 2, "coverage_is_complete": False,
        "official_legal_pool_verified": False, "variant_equivalence_verified": False,
        "evidence_commit": EVIDENCE_COMMIT,
        "registry_sha256": REGISTRY_SHA, "qa_xml_sha256": XML_SHA,
        "summary": {
            "compiled_definitions": len(entries), "sets": dict(Counter(x["set"] for x in entries)),
            "types": dict(Counter(x["type"] for x in entries)),
            "tokens": sum(x["token"] for x in entries),
            "compiled_banned": sum(x["compiled_banned"] for x in entries),
            "missing_public_code": sum(not x["print_ids"] for x in entries),
            "duplicate_name_groups": sum(v > 1 for v in Counter(x["name"] for x in entries).values()),
            "numbered_radiance_registered": len(BASE_CODES),
            "radiance_catalog_printings": len(printings),
            "unresolved_nonbase_printings": len(variant_rows),
            "variant_categories": dict(Counter(x["category"] for x in variant_rows)),
            "letter_variant_raw_hash_mismatches": sum(
                x["category"] == "letter_variant" and x["raw_rules_hash_equal"] is False
                for x in variant_rows),
            "explicit_scenario_mapped_cards": len(explicit),
            "explicit_scenario_test_links": sum(map(len, explicit.values())),
            "historical_gap_cards": len(gaps),
            "enabled_passing_tests": sum(tests.values()),
            "nonpassing_or_disabled_tests": sorted(k for k,v in tests.items() if not v),
            "verification_status": dict(Counter(x["verification_status"] for x in entries)),
        },
        "entries": entries, "unresolved_printings": variant_rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("registry", "xml", "catalog", "acceptance", "historical-ledger", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    tests = executed_tests(pinned(a.xml, XML_SHA))
    if len(tests) != 3917 or sum(tests.values()) != 3916:
        raise ValueError("unexpected enabled regression count")
    result = inventory(json.loads(pinned(a.registry, REGISTRY_SHA)),
                       json.loads(a.catalog.read_bytes()), json.loads(a.acceptance.read_bytes()),
                       literal_mappings(a.historical_ledger.read_bytes()), tests)
    result["source_hashes"] = {name: digest(path.read_bytes()) for name, path in
        (("catalog", a.catalog), ("acceptance", a.acceptance), ("historical_ledger", a.historical_ledger))}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
