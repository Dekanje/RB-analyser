"""Fresh, pinned 58-legend candidate certification. No optimization or adoption."""
import argparse,json,os,re,subprocess,tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from format_prior_gateway import FormatPriorGateway,ENV
from format_roster_v2 import load_roster,MANIFEST_REPORT_SHA,AGENT
from format_match_v2 import digest,FormatRejected
from optimize_58 import stable_seed
ENGINE="bd3b0abbeba26b87223e407a5317eba91e5d459bf36fd842a7371afa695f5287"
PRIOR="0df5c0f231c642f366e7707fb6b60f9e291dc1ff8a65a4266654876c96b564ef"
SEED=2026112460
SETS=("OGN","OGS","SFD","UNL","VEN","RAD")
def schedule(names):
    names=sorted(names)
    if len(names)!=58 or len(set(names))!=58:raise FormatRejected("expected 58 distinct registrations")
    rows=[]
    for i in range(0,58,2):
        a,b=names[i:i+2]
        seed=stable_seed(SEED,"format_prior_roster_v1",a,b) or 1
        for x,y in ((a,b),(b,a)):
            rows.append({"index":len(rows),"one":x,"two":y,"seed":seed})
    return rows
def verify(rows,manifest,provenance):
    expected=schedule(manifest)
    if len(rows)!=58 or {r["index"] for r in rows}!=set(range(58)):
        raise FormatRejected("incomplete or duplicate receipt set")
    for row in rows:
        case=expected[row["index"]]
        if any(row[k]!=v for k,v in case.items()):raise FormatRejected("schedule drift")
        r=row["receipt"]
        a,b=manifest[row["one"]],manifest[row["two"]]
        if (any(r.get(k)!=v for k,v in provenance.items()) or
            r.get("status")!="complete" or r.get("native_ids_verified") is not True or
            r.get("winner") not in (1,2) or type(r.get("turns")) is not int or r["turns"]<=0 or
            not r.get("reason") or r.get("seed")!=row["seed"] or r.get("agent")!=AGENT or
            r.get("forced_starting_player") is not None or
            r.get("deck_sha256")!=[a["deck_sha256"],b["deck_sha256"]] or
            r.get("native_vectors_sha256")!=[a["vector_sha256"],b["vector_sha256"]] or
            r.get("native_extra_legend_ids")!=[a["extras"],b["extras"]]):
            raise FormatRejected("native receipt mismatch: "+str(row["index"]))
    for seat in ("one","two"):
        if Counter(r[seat] for r in rows)!=Counter(manifest.keys()):
            raise FormatRejected("seat coverage mismatch")
def direct_negatives(g,roster):
    # Deliberately bypass Python registration preflight for native boundary tests.
    a,b=sorted(roster)[:2]
    vec=g.gate.validate(roster[a])
    ids=list(map(int,g.prior_text.split(",")))
    controls=[("malformed","249,","invalid public format identity list"),
              ("unknown","999999999","unknown, native-banned or token format identity"),
              ("native_ban","110","unknown, native-banned or token format identity")]
    for heading in ("Legend","Champion","MainDeck","Battlefields","Runes","Sideboard"):
        if not vec[heading]:continue
        omitted=vec[heading][0]
        policy=",".join(str(i) for i in ids if i!=omitted)
        controls.append(("omit_"+heading,policy,"registered identity outside public format prior"))
    out=[]
    with tempfile.TemporaryDirectory() as tmp:
        p,q=Path(tmp)/"p1.txt",Path(tmp)/"p2.txt"
        p.write_bytes(roster[a]);q.write_bytes(roster[b])
        for label,policy,expected in controls:
            env=os.environ.copy();env[ENV]=policy;env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
            cmd=[str(g.engine),"--deck1",str(p),"--deck2",str(q),"--agent1",AGENT,"--agent2",AGENT,
                 "--game-mode","match","--seed","2026112461","--web","off","--render-html","off","--debug"]
            r=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=90)
            row={"label":label,"policy_sha256":digest(policy.encode()),"returncode":r.returncode,
                 "expected":expected,"error":r.stderr[-2000:],"terminal_detected":bool(re.search(r"^Game over:",r.stdout,re.M)),
                 "deck_sha256":[digest(roster[a]),digest(roster[b])]}
            out.append(row)
            if r.returncode!=1 or expected not in r.stderr or row["terminal_detected"]:
                raise FormatRejected("native format rejection failed: "+label)
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","selected","prior","output"):
        p.add_argument("--"+n,type=Path,required=True)
    p.add_argument("--workers",type=int,default=2,choices=(1,2,3,4))
    a=p.parse_args()
    g=FormatPriorGateway(a.engine,a.registry,a.profile,SETS)
    if g.engine_sha!=ENGINE or g.provenance()["public_prior_sha256"]!=PRIOR:
        raise FormatRejected("wrong accepted candidate engine or format")
    roster=load_roster(g,a.selected,a.prior)
    # Historical roster already legal under the six-set registration gate.
    # Keep original ordered bytes; verify every distinct actual legend identity.
    vectors={name:g.gate.validate(raw) for name,raw in roster.items()}
    expected_legends={i for i in map(int,g.prior_text.split(",")) if g.gate.ids[i]["card_type"]=="legend"}
    if len(expected_legends)!=58 or {v["Legend"][0] for v in vectors.values()}!=expected_legends:
        raise FormatRejected("legend inventory mismatch")
    manifest={n:{"deck_sha256":digest(raw),"vector_sha256":digest(json.dumps(vectors[n],sort_keys=True).encode()),
                 "legend_id":vectors[n]["Legend"][0],"extras":vectors[n]["NeekoLegends"]} for n,raw in roster.items()}
    report={**g.provenance(),"status":"FAILED_OR_INCOMPLETE","manifest":manifest,
            "source_manifest_report_sha256":MANIFEST_REPORT_SHA,"agent":AGENT,"schedule_seed":SEED,
            "games":[],"native_negative_controls":[],"adopted":0,"fitness_evaluated":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        report["native_negative_controls"]=direct_negatives(g,roster)
        # A conflicting ambient prior must be replaced by the gateway.
        os.environ[ENV]="invalid-ambient-value"
        def run(row):
            try:r=g.game(roster[row["one"]],roster[row["two"]],row["seed"],AGENT)
            except Exception as exc:r={"status":"error","error":str(exc)}
            return {**row,"receipt":r}
        with ThreadPoolExecutor(max_workers=a.workers) as executor:
            report["games"]=list(executor.map(run,schedule(roster)))
        report["native_games_completed"]=sum(r["receipt"].get("status")=="complete" for r in report["games"])
        verify(report["games"],manifest,g.provenance())
        report["status"]="PASS_SCOPED_FORMAT_PRIOR_ROSTER"
    finally:
        a.output.write_text(json.dumps(report,indent=2))
    print(report["status"],report["native_games_completed"])
if __name__=="__main__":main()
