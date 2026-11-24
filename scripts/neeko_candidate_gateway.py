"""Candidate-only regression adapter; NOT an approved simulation entry point.

Only the exact dated profile and accepted corrected registry are usable here.
A newly built CI binary is fingerprinted, not authorized by this module.
Diagnostic native stdout is private to the audit, never given to agents.
"""
import json,os,re,subprocess,tempfile
from pathlib import Path
from format_gateway import FormatGate,FormatRejected,HEADINGS,norm
from format_match_v2 import VerifiedGateway,receipt_vectors,digest,PROFILE_SHA

CANDIDATE_REGISTRY_SHA="0d6165c2ce08b3d60e423a9216150dc15c9527656f9358a6e119d94c6c189e0a"
EXTRA="NeekoLegends"
HEADINGS_V3=HEADINGS+(EXTRA,)
NEEKO=1131

class NeekoGate(FormatGate):
    def validate(self,raw):
        # Keep V2's six-section grammar unchanged; optional seventh section
        # is only permitted as the final section.
        lines=raw.decode("utf-8").splitlines(keepends=True)
        positions=[i for i,l in enumerate(lines) if l.strip()=="NeekoLegends:"]
        if len(positions)>1:raise FormatRejected("duplicate NeekoLegends section")
        split=positions[0] if positions else len(lines)
        v=super().validate("".join(lines[:split]).encode())
        extras=[]
        for line in lines[split+1:]:
            line=line.strip()
            if not line or line.startswith("#"):continue
            m=re.fullmatch(r"1[ \t]+(.+)",line)
            if not m:raise FormatRejected("extra legends require single-card rows")
            c=self.resolve(m[1])
            if c["card_type"]!="legend":raise FormatRejected("extra identity is not a legend")
            extras.append(c["card_id"])
            if len(extras)>3:raise FormatRejected("at most three extra legends")
        names=[norm(self.ids[i]["name"]) for i in v["Legend"]+extras]
        if len(names)!=len(set(names)):raise FormatRejected("duplicate or starting legend name")
        if extras and NEEKO not in v["Champion"]+v["MainDeck"]+v["Sideboard"]:
            raise FormatRejected("extra legends without registered Neeko")
        return {**v,EXTRA:extras}

def receipt_v3(stdout,definitions):
    vectors=receipt_vectors(stdout,definitions)
    extras={};counts={};seat=None
    for line in stdout.splitlines():
        m=re.fullmatch(r"\[DECK\] P([12]) \(.+\):",line.strip())
        if m:
            seat=int(m[1]);extras[seat]=[];continue
        m=re.fullmatch(r"\s*neeko_count ([0-3])",line)
        if m:
            if seat is None or seat in counts:raise FormatRejected("duplicate or misplaced extra receipt count")
            counts[seat]=int(m[1]);continue
        m=re.fullmatch(r"\s*neeko\s+\[([^\]]+)\]\s+.+",line)
        if m:
            if seat not in counts or m[1] not in definitions:
                raise FormatRejected("unrecognized extra receipt")
            extras[seat].append(definitions[m[1]])
    if set(counts)!={1,2} or any(len(extras[i])!=counts[i] for i in (1,2)):
        raise FormatRejected("incomplete Neeko native receipt")
    for i in (1,2):vectors[i-1][EXTRA]=extras[i]
    return vectors

class CandidateGateway(VerifiedGateway):
    """Internal CI smoke executor, no configuration approval or production use."""
    def __init__(self,engine,registry,profile,allowed_sets=("OGN","OGS","SFD","UNL","VEN","RAD")):
        self.engine=Path(engine).resolve()
        p=Path(profile).read_bytes();r=Path(registry).read_bytes()
        if digest(p)!=PROFILE_SHA or digest(r)!=CANDIDATE_REGISTRY_SHA:
            raise FormatRejected("wrong candidate registry or dated profile")
        self.engine_sha=digest(self.engine.read_bytes())
        self.gate=NeekoGate(json.loads(p),json.loads(r),allowed_sets)
        self.definitions={c["card_def_id"]:i for i,c in self.gate.ids.items()}
        if len(self.definitions)!=len(self.gate.ids):raise FormatRejected("ambiguous definition")
    def provenance(self):
        return {"classification":"UNAPPROVED_CI_CORRECTIVE_CANDIDATE",
                "profile_sha256":PROFILE_SHA,"registry_sha256":CANDIDATE_REGISTRY_SHA,
                "engine_sha256":self.engine_sha,"allowed_sets":sorted(self.gate.sets),
                "full_official_legality_certified":False,"production_authorized":False}
    def render(self,v):
        lines=[]
        for h in HEADINGS_V3:
            lines.append(h+":")
            lines.extend("1 "+self.gate.ids[i]["name"]+" #"+str(i) for i in v[h])
        raw=("\n".join(lines)+"\n").encode()
        if self.gate.validate(raw)!=v:raise FormatRejected("registration changed on render")
        return raw
    def _native(self,raws,expected,seed,agent,timeout,forced_start=None):
        if digest(self.engine.read_bytes())!=self.engine_sha:raise FormatRejected("candidate binary changed")
        if type(seed) is not int or seed<=0 or timeout<=0 or not re.fullmatch(r"ismcts:sims=[1-9][0-9]*",agent):
            raise FormatRejected("invalid native parameters")
        if forced_start is not None and (type(forced_start) is not int or forced_start not in (1,2)):
            raise FormatRejected("invalid forced seat")
        env=os.environ.copy();env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
        if forced_start is not None:env["RIFTBOUND_FORCE_STARTING_PLAYER"]=str(forced_start)
        with tempfile.TemporaryDirectory(prefix="rb_neeko_candidate_") as root:
            paths=[Path(root)/f"p{i}.txt" for i in (1,2)]
            for path,raw in zip(paths,raws):path.write_bytes(raw)
            cmd=[str(self.engine),"--deck1",str(paths[0]),"--deck2",str(paths[1]),
                 "--agent1",agent,"--agent2",agent,"--game-mode","match","--seed",str(seed),
                 "--web","off","--render-html","off","--debug"]
            p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=timeout)
        if p.returncode:raise FormatRejected("candidate native execution failed")
        observed=receipt_v3(p.stdout,self.definitions)
        if observed!=expected:raise FormatRejected("candidate ordered vector mismatch")
        terminals=re.findall(r"^Game over: winner=([12]) \| reason=(.+) \| turns=(\d+)$",p.stdout,re.M)
        starts=re.findall(r"TOURNAMENT_FORCED_STARTING_PLAYER=([12])",p.stdout)
        if len(terminals)!=1 or starts!=([] if forced_start is None else [str(forced_start)]):
            raise FormatRejected("terminal or first-player receipt missing")
        w,reason,turns=terminals[0]
        return {**self.provenance(),"status":"complete","winner":int(w),"reason":reason,
                "turns":int(turns),"seed":seed,"agent":agent,"native_ids_verified":True,
                "forced_starting_player":forced_start,"deck_sha256":[digest(r) for r in raws],
                "native_vectors_sha256":[digest(json.dumps(v,sort_keys=True).encode()) for v in observed],
                "native_extra_legend_ids":[v[EXTRA] for v in observed]}
