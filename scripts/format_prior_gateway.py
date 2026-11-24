"""Unapproved, public-format-aware candidate execution boundary."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from neeko_candidate_gateway import CandidateGateway,FormatRejected,receipt_v3,EXTRA
from format_match_v2 import digest
from format_gateway import norm
ENV="RIFTBOUND_FORMAT_PRIOR_IDS"
def prior_ids(gate):
    # Same public format policy as registration; never read either deck.
    return sorted(i for i,c in gate.ids.items()
                  if (c["set"] in gate.sets or i in gate.exempt)
                  and i not in gate.banned and norm(c["name"]) not in gate.banned_names
                  and not c["banned"] and c.get("super_type")!="token")
def prior_text(gate):
    ids=prior_ids(gate)
    if not ids:raise FormatRejected("empty public format identity universe")
    return ",".join(map(str,ids))
def verify_prior(stdout,expected):
    got=re.findall(r"^FORMAT_PRIOR_IDS=(.*)$",stdout,re.M)
    if got!=[expected]:raise FormatRejected("missing or mismatched native format prior receipt")
class FormatPriorGateway(CandidateGateway):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.prior_text=prior_text(self.gate)
    def provenance(self):
        return {**super().provenance(),"public_prior_sha256":digest(self.prior_text.encode()),
                "public_prior_count":len(self.prior_text.split(",")),
                "public_prior_policy":"explicit_registered_identity_allowlist_v1"}
    def _native(self,raws,expected,seed,agent,timeout,forced_start=None):
        if digest(self.engine.read_bytes())!=self.engine_sha:raise FormatRejected("candidate binary changed")
        if type(seed) is not int or seed<=0 or timeout<=0 or not re.fullmatch(r"ismcts:sims=[1-9][0-9]*",agent):
            raise FormatRejected("invalid native parameters")
        if forced_start is not None and (type(forced_start) is not int or forced_start not in (1,2)):
            raise FormatRejected("invalid forced seat")
        env=os.environ.copy();env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
        env[ENV]=self.prior_text
        if forced_start is not None:env["RIFTBOUND_FORCE_STARTING_PLAYER"]=str(forced_start)
        with tempfile.TemporaryDirectory(prefix="rb_neeko_candidate_") as root:
            paths=[Path(root)/f"p{i}.txt" for i in (1,2)]
            for path,raw in zip(paths,raws):path.write_bytes(raw)
            cmd=[str(self.engine),"--deck1",str(paths[0]),"--deck2",str(paths[1]),
                 "--agent1",agent,"--agent2",agent,"--game-mode","match","--seed",str(seed),
                 "--web","off","--render-html","off","--debug"]
            p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=timeout)
        if p.returncode:raise FormatRejected("candidate native execution failed")
        verify_prior(p.stdout,self.prior_text)
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
