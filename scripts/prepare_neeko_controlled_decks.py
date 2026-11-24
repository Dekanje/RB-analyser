"""Create exact candidate diagnostic registrations, not deck fitness inputs."""
import json
from pathlib import Path
from neeko_candidate_gateway import CandidateGateway,EXTRA
from format_match_v2 import transition,digest
def main():
    root=Path("results")
    g=CandidateGateway("engine_build/riftbound","engine_build/registry.json","rulesets/standard-global-2026-11-23.json")
    selected=root/"selected/selected_decks"
    v=g.gate.validate((selected/"ahri_nine_tailed_fox.txt").read_bytes().replace(b"1 Ahri, Inquisitive\n",b"1 Ahri, Inquisitive #119\n"))
    assert v["Legend"]==[252] and v["Sideboard"].count(56)==1 and v["MainDeck"].count(811)==1
    v["Sideboard"][v["Sideboard"].index(56)]=1131
    v=transition(v,{"swaps":[{"main_out":811,"side_in":1131,"copies":1}]})
    assert v["MainDeck"].count(604)==3 and g.gate.ids[604]["name"]=="Back Off"
    for _ in range(2):v["MainDeck"][v["MainDeck"].index(604)]=1131
    assert v["MainDeck"].count(1131)==3
    cases={"neeko_a":{**v,EXTRA:[249]},"neeko_b":{**v,EXTRA:[254,256,259]},
           "observer":g.gate.validate((selected/"akali_rogue_assassin.txt").read_bytes())}
    directory=root/"controlled_decks";directory.mkdir()
    rows={}
    for name,vec in cases.items():
        raw=g.render(vec)
        assert g.gate.validate(raw)==vec
        (directory/(name+".txt")).write_bytes(raw)
        rows[name]={"deck_sha256":digest(raw),"vector_sha256":digest(json.dumps(vec,sort_keys=True).encode()),"extras":vec[EXTRA]}
    (directory/"manifest.json").write_text(json.dumps({**g.provenance(),"decks":rows,"fitness_evaluated":False,"adopted":0},indent=2))
if __name__=="__main__":main()
