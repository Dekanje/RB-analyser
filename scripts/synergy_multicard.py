#!/usr/bin/env python3
"""Generate synergy-aware TWO- and THREE-slot MainDeck packages for all 58 Legends.

Printed text/tag synergy is only a search heuristic. Every candidate retains
the registered Legend, chosen Champion, runes, battlefields and Sideboard, and
requires independent native Rule407 BO3 validation before any acceptance.
The historical source decks are never modified.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from optimize_58 import BAN_KEYS, card_score, effective_domains, is_unique, key, registry, stable_seed
from round_robin_58 import load_decks, sha
from sideboard_deck import parse_deck, render_deck
from structural_deck_population import legal_registration

STATUS = "SYNERGY_PACKAGES_UNTESTED_NO_STRENGTH_CLAIM"
DEPTHS = (2, 3)
PER_DEPTH = 3


def printed_pair_synergy(a, b):
    """Auditable proxy signals, NOT verified real card interaction semantics."""
    points, signals = 0.0, []
    tags = {key(t) for t in a.get("tags") or ()} & {key(t) for t in b.get("tags") or ()}
    tags.discard("")
    if tags:
        points += min(len(tags), 2) * 0.35
        signals.append("shared_printed_tag")
    for source, target in ((a, b), (b, a)):
        text = (source.get("ability_text") or "").lower()
        kind = target.get("card_type") or ""
        if ("when you play" in text or "whenever you play" in text or
                "when you cast" in text):
            if kind == "spell" and "spell" in text:
                points += 0.75
                signals.append("printed_spell_play_trigger")
            elif kind == "unit" and "unit" in text:
                points += 0.65
                signals.append("printed_unit_play_trigger")
            elif kind == "gear" and "gear" in text:
                points += 0.65
                signals.append("printed_gear_play_trigger")
        if "draw" in text and "draw" in (target.get("ability_text") or "").lower():
            points += 0.15
            signals.append("printed_draw_theme")
        if "discard" in text and "discard" in (target.get("ability_text") or "").lower():
            points += 0.15
            signals.append("printed_discard_theme")
    return points, tuple(sorted(set(signals)))


def score_state(main, byname, champion_tags, pair_cache):
    solo = sum(n * card_score(byname[name], collections.Counter(), champion_tags)
               for name, n in main.items())
    pair = 0.0
    names = sorted(main)
    for i, name in enumerate(names):
        for other in names[i+1:]:
            k = (name, other)
            if k not in pair_cache:
                pair_cache[k] = printed_pair_synergy(byname[name], byname[other])[0]
            pair += pair_cache[k] * min(main[name], 2) * min(main[other], 2)
    # Softly penalize very high-cost concentrations; never treat as game evidence.
    upper_curve = sum(n for name, n in main.items()
                      if (byname[name].get("energy_cost") or 0) >= 7)
    return solo + 0.22 * pair - 0.18 * max(0, upper_curve - 7) ** 2


def candidate_pool(original, byname, domains, champion_tags, seed):
    options = []
    for name, card in byname.items():
        if (card.get("card_type") not in ("unit", "spell", "gear")
                or card.get("banned") or key(name) in BAN_KEYS
                or "signature" in (card.get("super_type") or "").lower()
                or "token" in (card.get("super_type") or "").lower()
                or "champion" in (card.get("super_type") or "").lower()
                or name == "Neeko, Blending In"
                or not set(card.get("domains") or ()).issubset(domains)
                or original.main.get(name, 0) + original.sideboard.get(name, 0)
                   + int(name == original.champion) >= (1 if is_unique(card) else 3)):
            continue
        base = card_score(card, collections.Counter(), champion_tags)
        proxy = sum(printed_pair_synergy(card, byname[other])[0] * min(n, 2)
                    for other, n in original.main.items() if other != name)
        options.append((name, base, proxy))
    if len(options) < 8:
        raise RuntimeError("Insufficient compiled legal alternatives for synergy packages")
    by_solo = sorted(options, key=lambda x: (-x[1], x[0]))
    by_proxy = sorted(options, key=lambda x: (-x[2], -x[1], x[0]))
    exploration = list(options)
    random.Random(seed).shuffle(exploration)
    names = []
    for group in (by_solo[:18], by_proxy[:22], exploration[:12]):
        for name, _, _ in group:
            if name not in names:
                names.append(name)
    return names


def package_search(original, byname, legend, seed):
    domains = effective_domains(legend, byname)
    champion_tags = set(byname[original.champion].get("tags") or ())
    pool = candidate_pool(original, byname, domains, champion_tags,
                          stable_seed(seed, legend, "synergy_pool"))
    pair_cache = {}
    original_score = score_state(original.main, byname, champion_tags, pair_cache)
    removable = {name for name in original.main
                 if "signature" not in (byname[name].get("super_type") or "").lower()}
    if len(removable) < 2 or sum(original.main[n] for n in removable) < 3:
        raise RuntimeError("Insufficient removable non-signature cards")
    # Each state: (heuristic score, current Counter, ordered atomic moves).
    beam = [(original_score, original.main.copy(), ())]
    outputs = []
    seen_final = set()
    for depth in (1, 2, 3):
        candidates = []
        seen_at_depth = set()
        for _, current, steps in beam:
            previously_added = {x["add"] for x in steps}
            previously_removed = {x["remove"] for x in steps}
            outs = sorted(
                (n for n in removable if current.get(n, 0) > 0 and n not in previously_removed),
                key=lambda n: (card_score(byname[n], collections.Counter(), champion_tags), n)
            )[:12]
            for old in outs:
                for new in pool:
                    if new == old or new in previously_added or new in previously_removed:
                        continue
                    limit = 1 if is_unique(byname[new]) else 3
                    if (current.get(new, 0) + original.sideboard.get(new, 0)
                            + int(new == original.champion)) >= limit:
                        continue
                    changed = current.copy()
                    changed[old] -= 1
                    changed[new] += 1
                    changed += collections.Counter()
                    frozen = tuple(sorted(changed.items()))
                    if frozen in seen_at_depth:
                        continue
                    seen_at_depth.add(frozen)
                    actions = steps + ({"remove": old, "add": new},)
                    heuristic = score_state(changed, byname, champion_tags, pair_cache)
                    candidates.append((heuristic, changed, actions))
        if not candidates:
            raise RuntimeError("Search beam exhausted at depth " + str(depth))
        candidates.sort(key=lambda x: (-x[0], tuple((s["remove"], s["add"]) for s in x[2])))
        # Keep diversity in the new card combinations instead of just the top
        # reordering of the same substitution. This is a search beam, not proof.
        diverse = []
        used_new_sets = set()
        for item in candidates:
            added = tuple(sorted(s["add"] for s in item[2]))
            if added in used_new_sets:
                continue
            diverse.append(item)
            used_new_sets.add(added)
            if len(diverse) == 9:
                break
        beam = diverse
        if depth not in DEPTHS:
            continue
        selected = 0
        for heuristic, changed, steps in diverse:
            frozen = tuple(sorted(changed.items()))
            if frozen in seen_final:
                continue
            seen_final.add(frozen)
            if sum(changed.values()) != 39 or len({s["add"] for s in steps}) != depth:
                raise RuntimeError("Wrong number of coordinated changes")
            variant = original.clone()
            variant.main = changed
            legal_registration(original, variant, byname)
            incoming = [s["add"] for s in steps]
            signals = sorted({label for i, a in enumerate(incoming)
                              for b in incoming[i+1:]
                              for label in printed_pair_synergy(byname[a], byname[b])[1]})
            outputs.append({
                "deck": render_deck(variant), "depth": depth,
                "steps": list(steps),
                "heuristic_delta": round(heuristic-original_score, 6),
                "printed_synergy_signals": signals,
            })
            selected += 1
            if selected == PER_DEPTH:
                break
        if selected != PER_DEPTH:
            raise RuntimeError("Incomplete coordinated package family at depth "+str(depth))
    if len(outputs) != len(DEPTHS)*PER_DEPTH:
        raise RuntimeError("Unexpected package count")
    return outputs


def generate_one(name, source, byname, output, seed):
    original = parse_deck(source.read_text(encoding="utf-8"))
    legal_registration(original, original, byname)
    variants = package_search(original, byname, name, seed)
    folder = output / hashlib.sha256(name.encode()).hexdigest()[:12]
    folder.mkdir(parents=True, exist_ok=True)
    records, distinct = [], {sha(source)}
    for index, candidate in enumerate(variants):
        text = candidate.pop("deck")
        h = hashlib.sha256(text.encode()).hexdigest()
        if h in distinct:
            raise RuntimeError("Duplicate or unchanged candidate: "+name)
        distinct.add(h)
        location = folder / ("package_%02d.txt" % index)
        location.write_text(text, encoding="utf-8")
        records.append({
            "path": str(location.relative_to(output)),
            "sha256": h,
            "kind": "coordinated_main_deck_package",
            "status": STATUS, "native_simulated": False,
            **candidate,
        })
    return {"legend": name, "original_sha256": sha(source),
            "candidates": records, "count": len(records)}


def generate(selected, registry_path, output, seed):
    sources, _ = load_decks(selected)
    byname = registry(registry_path)
    if len(sources) != 58:
        raise RuntimeError("Incomplete frozen 58-Legend roster")
    output.mkdir(parents=True, exist_ok=True)
    records = [generate_one(name, path, byname, output, seed)
               for name, path in sorted(sources.items())]
    manifest = {
        "status": STATUS, "legends": 58, "candidates_per_legend": 6,
        "candidates_total": 348,
        "depths_per_legend": {"2": 3, "3": 3},
        "seed": seed, "registry_sha256": sha(registry_path),
        "source_roster_sha256": hashlib.sha256(json.dumps(
            {n: sha(path) for n, path in sorted(sources.items())},
            sort_keys=True).encode()).hexdigest(),
        "original_decks_modified": False,
        "engine_strength_established": False,
        "records": records,
    }
    if sum(r["count"] for r in records) != 348:
        raise RuntimeError("All 348 packages required")
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("ALL58_SYNERGY_PACKAGE_PROPOSALS_ONLY", 348, flush=True)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected", type=pathlib.Path, required=True)
    p.add_argument("--registry", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--seed", type=int, default=202611282200)
    a = p.parse_args()
    generate(a.selected, a.registry, a.output, a.seed)


if __name__ == "__main__":
    main()
