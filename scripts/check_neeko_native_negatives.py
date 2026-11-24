"""Use the pinned accepted guarded candidate binary; no rebuild or game on invalid input."""
import json,subprocess,tempfile
from pathlib import Path
from neeko_candidate_gateway import CandidateGateway,EXTRA
from format_match_v2 import digest
ENGINE="4aab884315a54099afd6e618ae2a64a1323779e35ad6505053d64853e45e7b23"

def main():
    root=Path("results");selected=root/"selected/selected_decks"
    engine=Path("engine_build/riftbound").resolve()
    assert digest(engine.read_bytes())==ENGINE
    g=CandidateGateway(engine,Path("engine_build/registry.json"),Path("rulesets/standard-global-2026-11-23.json"))
    raw=(selected/"ahri_nine_tailed_fox.txt").read_bytes().replace(b"1 Ahri, Inquisitive\n",b"1 Ahri, Inquisitive #119\n")
    v=g.gate.validate(raw)
    assert v["Legend"]==[252] and 56 in v["Sideboard"]
    base=g.render(v)
    v["Sideboard"][v["Sideboard"].index(56)]=1131
    neeko=g.render(v)
    other=g.render(g.gate.validate((selected/"akali_rogue_assassin.txt").read_bytes()))
    def unchecked(raw,ids):
        return raw+("".join("1 "+g.gate.ids[i]["name"]+" #"+str(i)+"\n" for i in ids)).encode()
    tests=[("duplicate",unchecked(neeko,[249,249]),"Neeko legends must all have different names"),
           ("starting",unchecked(neeko,[252]),"Neeko legends must all have different names"),
           ("four",unchecked(neeko,[249,254,256,258]),"Neeko allows at most 3"),
           ("nonlegend",unchecked(neeko,[811]),"Neeko legends must be Legend cards"),
           ("no_neeko",unchecked(base,[249]),"Neeko legends supplied without Neeko")]
    rows=[]
    with tempfile.TemporaryDirectory() as temp:
        a=Path(temp)/"one.txt";b=Path(temp)/"two.txt";b.write_bytes(other)
        for name,deck,error in tests:
            a.write_bytes(deck)
            result=subprocess.run([str(engine),"--deck1",str(a),"--deck2",str(b),"--agent1","ismcts:sims=24","--agent2","ismcts:sims=24","--game-mode","match","--seed","2026112425","--web","off","--render-html","off"],capture_output=True,text=True,timeout=60)
            assert result.returncode==1 and "Deck validation failed." in result.stderr and error in result.stderr and "Game over:" not in result.stdout,(name,result.returncode,result.stderr)
            rows.append({"case":name,"deck_sha256":digest(deck),"opponent_sha256":digest(other),"returncode":result.returncode,"error":error,"terminal_game":False})
    with (root/"neeko_native_negatives.json").open("x") as f:json.dump({**g.provenance(),"cases":rows,"seed":2026112425,"native_games":0,"adopted":0},f,indent=2)
if __name__=="__main__":main()
