"""Research-only, guarded mixed-budget sampled ISMCTS baseline measurement."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from collections import Counter

from format_prior_gateway import FormatPriorGateway, ENV, verify_prior
from neeko_candidate_gateway import receipt_v3, EXTRA
from format_roster_v2 import load_roster
from format_match_v2 import digest, FormatRejected
from optimize_58 import stable_seed

ENGINE="bd3b0abbeba26b87223e407a5317eba91e5d459bf36fd842a7371afa695f5287"
PRIOR="0df5c0f231c642f366e7707fb6b60f9e291dc1ff8a65a4266654876c96b564ef"
ROSTER="4b4436fe8c8e420aefe868dc1ff006c54c82727df383626efcb1e4d67ae7d68a"
SETS=("OGN","OGS","SFD","UNL","VEN","RAD")
PANEL=tuple(n+".txt" for n in ("ambessa_matriarch_of_war","draven_glorious_executioner",
    "leblanc_deceiver","master_yi_wuju_bladesman","rek_sai_void_burrower","rengar_pridestalker"))
MASTER=202611241905
BASE="ismcts:sims=24"
HIGH="ismcts:sims=128"

def require(ok,msg):
    if not ok:raise FormatRejected(msg)

def schedule():
    rows=[]
    for name in PANEL:
        for rep in range(2):
            seed=stable_seed(MASTER,"p0_05_current_v1",name,rep) or 1
            for seat in (1,2):
                rows.append({"index":len(rows),"deck":name,"rep":rep,"seed":seed,"challenger_seat":seat,
                             "agents":[HIGH,BASE] if seat==1 else [BASE,HIGH]})
    require(len({r["seed"] for r in rows})==12,"seed collision")
    return rows

def vector_hash(v):
    return digest(json.dumps(v,sort_keys=True).encode())

def native_result(stdout,returncode,g,vec,case):
    require(returncode==0,"native execution failed")
    verify_prior(stdout,g.prior_text)
    require(receipt_v3(stdout,g.definitions)==[vec,vec],"ordered native vector mismatch")
    lines=[x for x in stdout.splitlines() if x.startswith("Game over:")]
    require(len(lines)==1,"missing or duplicate terminal")
    m=re.fullmatch(r"Game over: winner=([12]) \| reason=(P[12] reached 8 points) \| turns=([1-9][0-9]*)",lines[0])
    require(m is not None and m[2][1]==m[1],"unsupported or inconsistent terminal")
    require("TOURNAMENT_FORCED_STARTING_PLAYER=" not in stdout,"unexpected forced seat")
    trace=[x.strip() for x in stdout.splitlines() if x.strip().startswith("[TRC] ")]
    require(any("DRAW_HAND:" in x for x in trace) and any("INTENT:" in x for x in trace),"missing gameplay trace")
    return {"status":"complete","winner":int(m[1]),"reason":m[2],"turns":int(m[3]),
            "challenger_win":int(m[1])==case["challenger_seat"],"native_ids_verified":True,
            "trace_lines":len(trace),"trace_sha256":digest("\n".join(trace).encode()),
            "native_vectors_sha256":[vector_hash(vec)]*2}

def native(g,raw,case):
    require(digest(g.engine.read_bytes())==ENGINE,"binary drift")
    vec=g.gate.validate(raw)
    # Whitelist process environment: exclude arbitrary RIFTBOUND_* flags.
    env={k:v for k,v in os.environ.items() if not k.startswith("RIFTBOUND_")}
    env[ENV]=g.prior_text
    env["RIFTBOUND_ISMCTS_CHECK_WORLDS"]="1"
    with tempfile.TemporaryDirectory(prefix="rb_p005_") as tmp:
        paths=[Path(tmp)/f"p{i}.txt" for i in (1,2)]
        for p in paths:p.write_bytes(raw)
        cmd=[str(g.engine),"--deck1",str(paths[0]),"--deck2",str(paths[1]),
             "--agent1",case["agents"][0],"--agent2",case["agents"][1],
             "--game-mode","match","--seed",str(case["seed"]),"--web","off","--render-html","off","--debug","--trace"]
        start=time.monotonic()
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=300)
    try:
        receipt=native_result(p.stdout,p.returncode,g,vec,case)
    except FormatRejected as e:
        # Do not export private debug output; stderr may contain hidden state.
        raise FormatRejected(str(e)+"; native exit="+str(p.returncode)+
                             "; stderr_sha256="+digest(p.stderr.encode())) from None
    return {**receipt,"deck_sha256":[digest(raw)]*2,"seconds":round(time.monotonic()-start,3),
            "world_check_enabled":True}

def summarize(rows,manifest):
    expected=schedule()
    require(len(rows)==len(expected),"incomplete schedule")
    pairs={}
    for case,row in zip(expected,rows):
        require(all(row.get(k)==v for k,v in case.items()),"schedule drift")
        r=row["receipt"];d=manifest[case["deck"]]
        require(r.get("status")=="complete" and r.get("native_ids_verified") is True and
                r.get("world_check_enabled") is True and type(r.get("winner")) is int and r["winner"] in (1,2) and
                r.get("challenger_win") is (r["winner"]==case["challenger_seat"]) and
                r.get("deck_sha256")==[d["deck_sha256"]]*2 and r.get("native_vectors_sha256")==[d["vector_sha256"]]*2,
                "invalid native receipt")
        require(r.get("reason")==f'P{r["winner"]} reached 8 points' and type(r.get("turns")) is int and r["turns"]>0 and
                type(r.get("trace_lines")) is int and r["trace_lines"]>0 and
                re.fullmatch("[0-9a-f]{64}",r.get("trace_sha256","")) and
                type(r.get("seconds")) in (int,float) and math.isfinite(r["seconds"]) and r["seconds"]>=0,
                "invalid terminal/trace/time")
        key=(case["deck"],case["rep"])
        pairs[key]=pairs.get(key,0)+int(r["challenger_win"])
    counts=Counter(pairs.values())
    n=counts[0]+counts[2]
    p=min(1.,2*sum(math.comb(n,k) for k in range(min(counts[0],counts[2])+1))/2**n)
    wins=sum(pairs.values())
    return {"games":len(rows),"pairs":len(pairs),"challenger_wins":wins,"win_rate":wins/len(rows),
            "pair_0_1_2_wins":[counts[i] for i in range(3)],
            "deck_wins":{d:sum(v for (name,_),v in pairs.items() if name==d) for d in PANEL},
            "conditional_pair_sign_p_two_sided":p,
            "assumption":"independent exchangeable non-tied seed pairs; not established across repeated decks",
            "seconds_sum":round(sum(r["receipt"]["seconds"] for r in rows),3),
            "strength_certified":False,"production_authorized":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","selected","prior","roster","output"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    g=FormatPriorGateway(a.engine,a.registry,a.profile,SETS)
    require(g.engine_sha==ENGINE and g.provenance()["public_prior_sha256"]==PRIOR,"wrong candidate")
    roster=load_roster(g,a.selected,a.prior)
    raw=a.roster.read_bytes()
    require(digest(raw)==ROSTER,"wrong native roster evidence")
    source=json.loads(raw)
    require(source["status"]=="PASS_SCOPED_FORMAT_PRIOR_ROSTER" and source["native_games_completed"]==58 and
            all(source.get(k)==v for k,v in g.provenance().items()),"roster provenance mismatch")
    manifest={n:{"deck_sha256":digest(r),"vector_sha256":vector_hash(g.gate.validate(r)),
                 "legend_id":g.gate.validate(r)["Legend"][0],"extras":g.gate.validate(r)[EXTRA]} for n,r in roster.items()}
    require(manifest==source["manifest"],"roster identity drift")
    cases=schedule()
    report={**g.provenance(),"status":"FAILED_OR_INCOMPLETE","source_roster_sha256":ROSTER,
            "master_seed":MASTER,"panel":list(PANEL),"manifest":{n:manifest[n] for n in PANEL},
            "schedule":cases,"games":[],"adopted":0,"fitness_evaluated":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as out:
        def one(case):
            try:r=native(g,roster[case["deck"]],case)
            except subprocess.TimeoutExpired:r={"status":"timeout"}
            except Exception as exc:r={"status":"error","error":str(exc)}
            print("P005_GAME",case["index"],r["status"],flush=True)
            return {**case,"receipt":r}
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                report["games"]=list(pool.map(one,cases))
            report["summary"]=summarize(report["games"],report["manifest"])
            report["status"]="PASS_SCOPED_AGENT_CALIBRATION"
        finally:
            json.dump(report,out,indent=2)
    print(report["status"])

if __name__=="__main__":main()
