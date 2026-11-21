#!/usr/bin/env python3
"""Make a transparent, separately named rules-legal Ornn candidate.

The original 58 decks are never changed. The original Ornn list is illegal:
3 Forgefire Cape, a printed Unique 1-per-deck card.
Candidate: 1 Forgefire Cape, 3 Doran's Shield, 3 Sterak's Gage.
Two same-domain, non-Unique gear slots replace the two illegal copies.
This is a disclosed decklist correction, NOT an unchanged original deck.
"""
import hashlib
import json
import pathlib
from run_actual_games import header

ORNN = "Ornn, Fire Below the Mountain"
PINNED_SOURCE_SHA256 = "a579f4781f1ed38f0dc439383cdbaf81df43aa3a73c840b78fc005fb646d72e6"
EDIT_COUNTS = [
 ("3 Forgefire Cape", "1 Forgefire Cape"),
 ("2 Doran's Shield", "3 Doran's Shield"),
 ("2 Sterak's Gage", "3 Sterak's Gage"),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def make_legal_candidate(paths, target_dir, manifest=None):
    """Return {legend: derived path}; never touch the originals."""
    target_dir = pathlib.Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    originals={header(path):path for path in paths}
    if len(originals)!=58 or ORNN not in originals:
        raise RuntimeError("Expected exact 58-legend source and original Ornn")
    derived={}
    summary={"schema":1,
             "candidate_kind":"57 exact originals plus 1 disclosed rules-legal Ornn correction",
             "originals_untouched":True,"decks":[],"edits":[]}
    for legend,path in sorted(originals.items()):
        body=path.read_text(encoding="utf-8")
        source_sha=sha(path.read_bytes())
        if legend==ORNN:
            if source_sha!=PINNED_SOURCE_SHA256:
                raise RuntimeError("Original Ornn SHA changed; independently re-audit before correcting")
            for old,new in EDIT_COUNTS:
                lines=body.splitlines()
                if lines.count(old)!=1 or new in lines:
                    raise RuntimeError("Ornn card-count correction anchor changed: "+old)
                body=body.replace(old,new)
                summary["edits"].append({"legend":legend,"before":old,"after":new})
        dest=target_dir/path.name
        dest.write_text(body,encoding="utf-8")
        derived[legend]=dest
        summary["decks"].append({
          "legend":legend,"filename":path.name,
          "original_sha256":source_sha,"effective_sha256":sha(dest.read_bytes()),
          "changed":source_sha!=sha(dest.read_bytes())})
    if sum(d["changed"] for d in summary["decks"])!=1:
        raise RuntimeError("Expected exactly one corrected Ornn source")
    if manifest:
        manifest=pathlib.Path(manifest)
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return derived
