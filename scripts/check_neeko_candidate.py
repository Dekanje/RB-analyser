"""CI-only native registration smoke and BO3, never fitness or adoption."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from neeko_candidate_gateway import CandidateGateway,FormatRejected,EXTRA
from format_match_v2 import transition,digest

def main():
    root=Path("results");selected=root/"selected/selected_decks"
    g=CandidateGateway(Path("engine_build/riftbound"),Path("engine_build/registry.json"),
                       Path("rulesets/standard-global-2026-11-23.json"))
    raw=(selected/"ahri_nine_tailed_fox.txt").read_bytes().replace(b"1 Ahri, Inquisitive\n",b"1 Ahri, Inquisitive #119\n")
    v=g.gate.validate(raw)
    assert v["Legend"]==[252] and 56 in v["Sideboard"] and 811 in v["MainDeck"]
    v["Sideboard"][v["Sideboard"].index(56)]=1131
    other=g.render(g.gate.validate((selected/"akali_rogue_assassin.txt").read_bytes()))
    extras=[249,254,256]
    results=[]
    for n in range(4):
        a={k:list(ids) for k,ids in v.items()};a[EXTRA]=extras[:n]
        active=transition(a,{"swaps":[{"main_out":811,"side_in":1131,"copies":1}]})
        receipt=g.game(g.render(active),other,2026112420+n)
        assert receipt["native_extra_legend_ids"]==[extras[:n],[]]
        results.append({"n":n,"receipt":receipt})
    v[EXTRA]=[256,249,254] # non-sorted order deliberate
    with TemporaryDirectory() as tmp:
        p1=Path(tmp)/"one.txt";p2=Path(tmp)/"two.txt"
        p1.write_bytes(g.render(v));p2.write_bytes(other)
        plan={"game2":{"p1":{"swaps":[{"main_out":811,"side_in":1131,"copies":1}]}},
              "game3":{"p1":{"swaps":[{"main_out":811,"side_in":1131,"copies":1}]}}}
        bo3=g.declared_bo3(p1,p2,plan,2026112424)
        assert bo3["sideboarding_applied"]
        for r in bo3["games"]:
            expected=[[],v[EXTRA]] if r["seat_flipped"] else [v[EXTRA],[]]
            assert r["native_extra_legend_ids"]==expected
    neg=[]
    for label,ids in [("duplicate",[249,249]),("starting",[252]),("four",[249,254,256,258]),("nonlegend",[811])]:
        bad={**v,EXTRA:ids}
        try:g.render(bad)
        except FormatRejected:neg.append(label)
        else:raise AssertionError(label+" not rejected")
    report={**g.provenance(),"status":"PASS_CANDIDATE_ONLY","single_games":results,
            "bo3":bo3,"negative_preflight":neg,"fitness_evaluated":False,"adopted":0}
    with (root/"rule407/neeko_registration.json").open("x") as out:json.dump(report,out,indent=2)
if __name__=="__main__":main()
