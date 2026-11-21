#!/usr/bin/env python3
"""Persist the full Radiance printing index; never mark card effects as playable."""
import json, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
src=root/"radiance_reports"
dest=root/"radiance/data"
dest.mkdir(parents=True,exist_ok=True)
summary=json.loads((src/"summary.json").read_text())
cards=json.loads((src/"radiance_printings.json").read_text())
if summary["numbered_cards_seen"]!=167 or len(cards)!=summary["printings_in_source"]:
    raise SystemExit("Coverage gate failed; refusing to publish partial catalog")
fields=("gallery_id","public_code","display_name","type","supertype","domains",
        "rarity","energy","power","might","alternate_art","signature",
        "overnumbered","base_number","rules_text_sha256","engine_registry_status")
index={
  "schema_version":1,
  "provenance":{"source":"Riot gallery via Dystorted888/riftbound-card-data",
                "source_commit":summary["source_snapshot_commit"],
                "snapshot":summary["source_snapshot_date"]},
  "engine":{"commit":summary["engine_commit"],"mechanics_certified":0,
            "all_radiance_supported":False},
  "summary":{"numbered_card_count":summary["numbered_cards_seen"],
             "printing_count":summary["printings_in_source"],
             "distinct_gameplay_fingerprints":summary["unique_gameplay_fingerprints"],
             "legends_count":summary["legends_count"]},
  "cards":[{field:c.get(field) for field in fields} for c in sorted(cards,key=lambda c:(c["public_code"],c["gallery_id"]))]
}
(dest/"radiance_catalog.json").write_text(json.dumps(index,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf8")
print("INDEX_WRITTEN cards=",len(index["cards"]), "effects_verified=0")
