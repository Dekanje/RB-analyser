"""P0-09 scoped cross-build trace replay against exact previous candidate."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from format_prior_gateway import FormatPriorGateway, ENV, verify_prior
from neeko_candidate_gateway import receipt_v3
from format_match_v2 import digest
from p0_09_toolchain import PIN, require

AGENT="ismcts:sims=24"
SEEDS=(2026112491,2026112492)

def results(raw):
    out={}
    for t in ET.fromstring(raw).iter("testcase"):
        n=t.attrib["classname"]+"."+t.attrib["name"]
        require(n not in out,"duplicate native test")
        if t.get("status")=="run" and t.get("result")=="completed" and not any(t.find(x) is not None for x in ("failure","error","skipped")):
            out[n]="pass"
        elif t.get("status")=="notrun" and t.get("result")=="suppressed":
            out[n]="disabled"
        else:
            out[n]="not_passing"
    require(len(out)==3933 and list(out.values()).count("pass")==3932 and list(out.values()).count("disabled")==1,"unexpected core suite counts")
    return out

def receipt(g, a, b, seed):
    env=os.environ.copy()
    env[ENV]=g.prior_text
    env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
    raws=[a,b]
    expected=[g.gate.validate(x) for x in raws]
    require(digest(g.engine.read_bytes())==g.engine_sha,"binary drift")
    with tempfile.TemporaryDirectory(prefix="rb_p009_") as tmp:
        paths=[Path(tmp)/f"p{i}.txt" for i in (1,2)]
        for p,raw in zip(paths,raws):
            p.write_bytes(raw)
        cmd=[str(g.engine),"--deck1",str(paths[0]),"--deck2",str(paths[1]),
             "--agent1",AGENT,"--agent2",AGENT,"--game-mode","match",
             "--seed",str(seed),"--web","off","--render-html","off","--debug","--trace"]
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=180)
    require(p.returncode==0,"native replay failed: "+p.stderr[-400:])
    verify_prior(p.stdout,g.prior_text)
    observed=receipt_v3(p.stdout,g.definitions)
    require(observed==expected,"ordered native deck mismatch")
    terminal=re.findall(r"^Game over: winner=([12]) \| reason=(.+) \| turns=(\d+)$",p.stdout,re.M)
    trace=[x.strip() for x in p.stdout.splitlines() if x.strip().startswith("[TRC] ")]
    require(len(terminal)==1 and "TOURNAMENT_FORCED_STARTING_PLAYER=" not in p.stdout and any("DRAW_HAND:" in x for x in trace) and any("INTENT:" in x for x in trace),"incomplete native trace")
    w,reason,turns=terminal[0]
    return {"winner":int(w),"reason":reason,"turns":int(turns),
            "trace_lines":len(trace),"trace_sha256":digest("\n".join(trace).encode()),
            "deck_sha256":[digest(x) for x in raws],
            "vector_sha256":[digest(json.dumps(v,sort_keys=True).encode()) for v in observed]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("reference","registry","engine","old_xml","new_xml","decks","output"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    old=a.old_xml.read_bytes()
    require(digest(old)=="27a2b0fdf15dbde33b38b4a2af0438e9676101ab1e0ecd5f5d893938a3c11e53","wrong historical XML")
    require(results(old)==results(a.new_xml.read_bytes()),"core native suite drift")
    require(digest(a.reference.read_bytes())==PIN["reference_engine_sha256"],"wrong reference binary")
    gs=[FormatPriorGateway(x,a.registry,"rulesets/standard-global-2026-11-23.json") for x in (a.engine,a.reference)]
    require(gs[0].prior_text==gs[1].prior_text and digest(gs[0].prior_text.encode())=="0df5c0f231c642f366e7707fb6b60f9e291dc1ff8a65a4266654876c96b564ef","prior drift")
    one,two=[(a.decks/n).read_bytes() for n in ("neeko_b.txt","observer.txt")]
    report={"status":"INCOMPLETE","agent":AGENT,"reference":gs[1].provenance(),"fresh":gs[0].provenance(),
            "old_xml_sha256":digest(old),"new_xml_sha256":digest(a.new_xml.read_bytes()),
            "cases":[],"fitness_evaluated":False,"adopted":0}
    require(not a.output.exists(),"refusing to overwrite receipt")
    try:
        for seed in SEEDS:
            for seat in (1,2):
                x,y=(one,two) if seat==1 else (two,one)
                rows={k:receipt(gs[i],x,y,seed) for k,i in (("fresh",0),("repeat",0),("reference",1))}
                report["cases"].append({"seed":seed,"seat":seat,"receipts":rows})
                require(rows["fresh"]==rows["repeat"]==rows["reference"],"cross-build replay mismatch")
        report["status"]="PASS_SCOPED_CROSS_BUILD_REPLAY"
    except Exception as e:
        report["error"]=str(e)
        raise
    finally:
        a.output.write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":
    main()
