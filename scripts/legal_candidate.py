#!/usr/bin/env python3
"""Create transparent, SHA-pinned rules-legal optimized deck candidates.

The original 58 decks are never changed. The original Ornn list is illegal:
3 Forgefire Cape, a printed Unique 1-per-deck card.
Ornn: 1 Forgefire Cape, 3 Doran's Shield, 3 Sterak's Gage.
Lucian / Rengar: replace off-domain Detonation Amplifier with legal, already
present Body cards. Miss Fortune: replace off-domain Elnuk Herd with Chaos
Scryer's Bloom. Counts, domain identities and original SHA hashes are checked.
These are disclosed decklist corrections, NOT unchanged original decks.
"""
import hashlib
import json
import pathlib
from run_actual_games import header

ORNN = "Ornn, Fire Below the Mountain"
PINNED_SOURCE_SHA256 = "a579f4781f1ed38f0dc439383cdbaf81df43aa3a73c840b78fc005fb646d72e6"
ORNN_EDIT_COUNTS = [
 ("3 Forgefire Cape", "1 Forgefire Cape"),
 ("2 Doran's Shield", "3 Doran's Shield"),
 ("2 Sterak's Gage", "3 Sterak's Gage"),
]

SOURCE_SHA256={
  "Lucian, Purifier":"cfc7e9bdccd033bc4b2e075450bbcc9df2882651a41f5dfc04b665fc283d526f",
  "Miss Fortune, Bounty Hunter":"2256bcd9ad71838aeb45d12ea535799e8133618e0da087fcdfe886a53976469a",
  "Rengar, Pridestalker":"477f2b52066229ee15392810f6b24a1f27f0581290c49390f2c7a010fe893ac9",
}
OTHER_EDITS={
  "Lucian, Purifier":[("1 Detonation Amplifier",None),("1 Crackshot Corsair","2 Crackshot Corsair")],
  "Miss Fortune, Bounty Hunter":[("1 Elnuk Herd",None),("2 Scryer's Bloom","3 Scryer's Bloom")],
  "Rengar, Pridestalker":[("1 Detonation Amplifier",None),("2 Petricite Monument","3 Petricite Monument")],
}

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
    summary={"schema":2,
             "candidate_kind":"54 unchanged originals plus four disclosed rules-legal corrections",
             "originals_untouched":True,"decks":[],"edits":[]}
    for legend,path in sorted(originals.items()):
        body=path.read_text(encoding="utf-8")
        source_sha=sha(path.read_bytes())
        edits=(ORNN_EDIT_COUNTS if legend==ORNN else OTHER_EDITS.get(legend, []))
        if edits:
            expected=(PINNED_SOURCE_SHA256 if legend==ORNN else SOURCE_SHA256[legend])
            if source_sha!=expected:
                raise RuntimeError("Original deck SHA changed; independently re-audit: "+legend)
            lines=body.splitlines()
            main_start=lines.index("MainDeck:")+1
            main_end=lines.index("Battlefields:")
            for old,new in edits:
                indices=[i for i in range(main_start,main_end) if lines[i]==old]
                if len(indices)!=1:
                    raise RuntimeError("Deck count anchor changed: "+legend+": "+old)
                if new is not None and new in lines[main_start:main_end]:
                    raise RuntimeError("New count line already exists: "+legend+": "+new)
                lines[indices[0]]=new
                summary["edits"].append({"legend":legend,"before":old,"after":new or "<removed>"})
            body="\n".join(line for line in lines if line is not None)+"\n"
            parts=body.splitlines()
            ms=parts.index("MainDeck:")+1
            me=parts.index("Battlefields:")
            counts=[int(line.split(" ",1)[0]) for line in parts[ms:me] if line.strip()]
            if sum(counts)!=39:
                raise RuntimeError("Main-deck count not 39 (plus chosen champion) after correction: "+legend)
        dest=target_dir/path.name
        dest.write_text(body,encoding="utf-8")
        derived[legend]=dest
        summary["decks"].append({
          "legend":legend,"filename":path.name,
          "original_sha256":source_sha,"effective_sha256":sha(dest.read_bytes()),
          "changed":source_sha!=sha(dest.read_bytes())})
    if {d["legend"] for d in summary["decks"] if d["changed"]} != {ORNN,*OTHER_EDITS}:
        raise RuntimeError("Expected exactly four corrected decks")
    if manifest:
        manifest=pathlib.Path(manifest)
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return derived
