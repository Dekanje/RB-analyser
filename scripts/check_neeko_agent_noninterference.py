"""Cached native ISMCTS behavioral screening; omniscient traces are audit-only."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from neeko_candidate_gateway import CandidateGateway,EXTRA
from format_match_v2 import transition,digest

ENGINE="55b01acfd2b5fdb723ee5325191339a0b1573c54a8ce8924efb1fef744855f4a"
SEEDS=(2026112441,2026112442,2026112443,2026112444)
AGENT="ismcts:sims=24,world=sampled"
OWNER="random-player:pass=0"
MARK="MODE_PROMPT: Neeko: choose a legend"
PICK="MODE_PICKED: Neeko: choose a legend"
def analyze(stdout,observer):
    # Full trace, including private events, is an offline audit. The engine
    # never receives this text as input. Compare only before owner's first
    # private legend choice, as afterwards real gameplay may legitimately differ.
    trace=[l.strip() for l in stdout.splitlines() if l.lstrip().startswith("[TRC]")]
    cut=next((i for i,l in enumerate(trace) if MARK in l),len(trace))
    prefix=trace[:cut]
    choices=[l for l in prefix if "CHOSE: ["+observer+"]" in l]
    multi=[l for l in prefix if re.search(r"DECISION #\d+ \("+observer+r"\): ([2-9]|[1-9]\d+) legal actions",l)]
    picked=next((l.split(PICK,1)[1] for l in trace[cut:] if PICK in l),None)
    return prefix,len(choices),len(multi),cut<len(trace),picked

def main():
    root=Path("results");selected=root/"selected/selected_decks"
    engine=Path("engine_build/riftbound").resolve()
    assert digest(engine.read_bytes())==ENGINE
    g=CandidateGateway(engine,Path("engine_build/registry.json"),Path("rulesets/standard-global-2026-11-23.json"))
    raw=(selected/"ahri_nine_tailed_fox.txt").read_bytes().replace(b"1 Ahri, Inquisitive\n",b"1 Ahri, Inquisitive #119\n")
    v=g.gate.validate(raw)
    assert v["Legend"]==[252] and 56 in v["Sideboard"] and 811 in v["MainDeck"]
    v["Sideboard"][v["Sideboard"].index(56)]=1131
    v=transition(v,{"swaps":[{"main_out":811,"side_in":1131,"copies":1}]})
    # Diagnostic exposure fixture: replace two Back Off copies with Neeko.
    assert g.gate.ids[604]['name']=='Back Off' and v['MainDeck'].count(604)==3
    assert v['MainDeck'].count(1131)==1 and 1131 not in v['Sideboard']
    for _ in range(2):v['MainDeck'][v['MainDeck'].index(604)]=1131
    assert v['MainDeck'].count(1131)==3 and len(v['MainDeck'])==39
    other=g.render(g.gate.validate((selected/"akali_rogue_assassin.txt").read_bytes()))
    pools=([249],[254,256,259])
    expected_names={249:"Loose Cannon",254:"Blind Monk",256:"Unforgiven",259:"Swift Scout"}
    for i,name in expected_names.items():
        assert (g.gate.ids[i]["card_type"],g.gate.ids[i]["name"])==("legend",name),i
    assert not set(pools[0]) & set(pools[1])
    variants=[g.render({**v,EXTRA:list(ids)}) for ids in pools]
    rows=[];report={**g.provenance(),"status":"FAILED_OR_INCOMPLETE","cases":rows,
                   "owner_agent":OWNER,"observer_agent":AGENT,"seeds":list(SEEDS),
                   "extra_pools":[list(p) for p in pools],"extra_names":expected_names,
                   "fixture":"three_neeko_active_copies","fixture_replaced_main_ids":[604,604],"fitness_evaluated":False,"adopted":0}
    path=root/"neeko_agent_noninterference_v2.json"
    def run(raw,seat,seed,tmp):
        a,b=Path(tmp)/"one.txt",Path(tmp)/"two.txt"
        a.write_bytes(raw if seat==1 else other);b.write_bytes(other if seat==1 else raw)
        agents=(OWNER,AGENT) if seat==1 else (AGENT,OWNER)
        env=os.environ.copy();env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
        # Check the native sampler's existing invariants at actual search calls.
        env["RIFTBOUND_ISMCTS_CHECK_WORLDS"]="1"
        cmd=[str(engine),"--deck1",str(a),"--deck2",str(b),"--agent1",agents[0],"--agent2",agents[1],
             "--game-mode","match","--seed",str(seed),"--web","off","--render-html","off","--trace"]
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=180)
        if p.returncode:raise RuntimeError("native failed: "+p.stderr[-1000:])
        terminal=re.findall(r"^Game over: winner=([12]) \| reason=(.+) \| turns=(\d+)$",p.stdout,re.M)
        if len(terminal)!=1:raise RuntimeError("missing terminal")
        from neeko_candidate_gateway import receipt_v3
        observed=receipt_v3(p.stdout,g.definitions)
        if observed!=[g.gate.validate(a.read_bytes()),g.gate.validate(b.read_bytes())]:
            raise RuntimeError("registration receipt mismatch")
        prefix,choices,multi,reached,picked=analyze(p.stdout,"P"+str(3-seat))
        mentions=[l.strip() for l in p.stdout.splitlines() if l.lstrip().startswith("[TRC]") and "Neeko" in l]
        return prefix,{"native_vectors_sha256":[digest(json.dumps(x,sort_keys=True).encode()) for x in observed],
                       "native_extra_legend_ids":[x[EXTRA] for x in observed],
                       "neeko_trace_count":len(mentions),"neeko_trace_sample":mentions[:16],
                       "deck_sha256":[digest(a.read_bytes()),digest(b.read_bytes())],
                       "prefix_sha256":digest("\n".join(prefix).encode()),"trace_lines":len(prefix),
                       "observer_choice_lines":choices,"observer_multi_action_main_decisions":multi,
                       "prompt_reached":reached,"picked":picked,"terminal":terminal[0],
                       "stdout_sha256":digest(p.stdout.encode())}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for seat in (1,2):
                for seed in SEEDS:
                    # Repeat first variant as deterministic control, then perturb.
                    a,ra=run(variants[0],seat,seed,tmp)
                    b,rb=run(variants[1],seat,seed,tmp)
                    row={"owner_seat":seat,"seed":seed,"variants":[ra,rb],
                         "same_pre_choice_trace":a==b,"sensitivity":ra["prompt_reached"] and rb["prompt_reached"] and ra["picked"] is not None and rb["picked"] is not None and ra["picked"]!=rb["picked"]}
                    rows.append(row)
                    if a!=b:
                        first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
                        row["first_divergence_index"]=first
                        row["first_divergence"]=[a[first] if first<len(a) else None,b[first] if first<len(b) else None]
                    if seed==SEEDS[0]:
                        c,rc=run(variants[0],seat,seed,tmp)
                        row["repeat_control"]={"same_prefix":a==c,"receipt":rc}
        report["pairs"]=len(rows)
        report["same_prefix_pairs"]=sum(r["same_pre_choice_trace"] for r in rows)
        report["sensitive_pairs"]=sum(r["sensitivity"] for r in rows)
        report["observer_multi_action_main_decisions"]=sum(r["variants"][0]["observer_multi_action_main_decisions"] for r in rows)
        assert len(rows)==8 and all(r["same_pre_choice_trace"] for r in rows)
        assert all(r["repeat_control"]["same_prefix"] for r in rows if "repeat_control" in r)
        assert all(any(r["owner_seat"]==s and r["sensitivity"] for r in rows) for s in (1,2)), "no positive selection sensitivity for one or both seats"
        assert all(sum(r["variants"][0]["observer_multi_action_main_decisions"] for r in rows if r["owner_seat"]==s)>0 for s in (1,2)), "no observed multi-action main decisions"
        report["status"]="PASS_SCOPED_BEHAVIORAL_SCREEN"
    finally:
        path.write_text(json.dumps(report,indent=2))
if __name__=="__main__":main()
