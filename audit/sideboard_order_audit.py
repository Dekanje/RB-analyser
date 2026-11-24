"""Read-only audit of sideboard candidates against original ordered registrations."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from zipfile import ZipFile

PLAYABLE = ("Legend", "Champion", "MainDeck", "Battlefields", "Runes")
SECTIONS = (*PLAYABLE, "Sideboard")


def parse_ordered(raw):
    sections = {}
    current = None
    for line in raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":"):
            current = line[:-1]
            if current not in SECTIONS or current in sections:
                raise ValueError("invalid section: " + current)
            sections[current] = []
            continue
        n, card = line.split(maxsplit=1)
        if current is None or int(n) <= 0:
            raise ValueError("invalid card row")
        sections[current].extend([card] * int(n))
    if tuple(sections) != SECTIONS:
        raise ValueError("missing or out-of-order sections")
    return sections


def changed_order(original, candidate):
    a, b = parse_ordered(original), parse_ordered(candidate)
    for section in PLAYABLE:
        if Counter(a[section]) != Counter(b[section]):
            raise ValueError("playable composition changed: " + section)
    if Counter(a["Sideboard"]) == Counter(b["Sideboard"]):
        raise ValueError("sideboard composition unchanged")
    return tuple(section for section in PLAYABLE if a[section] != b[section])


def audit(original_zip, candidate_zip, screen_zip, holdout_zips=()):
    classes = {}
    training = defaultdict(Counter)
    holdout = defaultdict(Counter)
    with ZipFile(original_zip) as a, ZipFile(candidate_zip) as b, ZipFile(screen_zip) as e:
        originals = {sha256(a.read(n)).hexdigest(): n for n in a.namelist()
                     if n.startswith("selected_decks/") and n.endswith(".txt")}
        manifest = json.loads(b.read("structural_manifest.json"))
        evidence = json.loads(e.read("all_sideboard_policy_evidence.json"))
        for row in manifest["records"]:
            original = a.read(originals[row["original_sha256"]])
            for item in row["variants"]:
                if item["kind"] != "sideboard":
                    continue
                candidate = b.read(item["path"])
                digest = sha256(candidate).hexdigest()
                if digest != item["sha256"] or digest in classes:
                    raise ValueError("invalid or duplicate candidate hash")
                key = "+".join(changed_order(original, candidate)) or "unchanged_playable_order"
                classes[digest] = key
                matches = [p for p in evidence[row["legend"]]["sideboard_proposals"]
                           if p["candidate_sha256"] == digest]
                if len(matches) != 1 or len(matches[0]["paired_receipts"]) != 4:
                    raise ValueError("missing or ambiguous screening evidence")
                if matches[0]["registered_original_sha256"] != row["original_sha256"]:
                    raise ValueError("screen original hash mismatch")
                training[key]["candidates"] += 1
                for receipt in matches[0]["paired_receipts"]:
                    if type(receipt["game1_same_winner"]) is not bool:
                        raise ValueError("invalid receipt")
                    training[key]["pairs"] += 1
                    training[key]["mismatches"] += not receipt["game1_same_winner"]
    seen = set()
    for path in holdout_zips:
        with ZipFile(path) as z:
            row = json.loads(z.read("holdout.json"))
        digest = row["candidate_sha256"]
        if digest in seen or len(row["paired"]) != row["paired_completed"]:
            raise ValueError("duplicate or incomplete holdout")
        seen.add(digest)
        key = classes[digest]
        holdout[key]["candidates"] += 1
        for receipt in row["paired"]:
            if type(receipt["game1_same_winner"]) is not bool:
                raise ValueError("invalid holdout receipt")
            holdout[key]["pairs"] += 1
            holdout[key]["mismatches"] += not receipt["game1_same_winner"]
    return {"training": {k: dict(v) for k, v in training.items()},
            "holdout": {k: dict(v) for k, v in holdout.items()}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_zip")
    p.add_argument("candidate_zip")
    p.add_argument("screen_zip")
    p.add_argument("holdout_zips", nargs="*")
    a = p.parse_args()
    print(json.dumps(audit(a.original_zip, a.candidate_zip, a.screen_zip, a.holdout_zips),
                     indent=2, sort_keys=True))
