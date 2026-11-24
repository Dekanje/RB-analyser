"""Bounded points-only declared BO3 for the pinned research candidate.

Not a tournament clock, adaptive policy, or production gateway. Preserve
historical adapters; reject unsupported terminal reasons instead of assigning wins.
"""
import json,os,re,subprocess,tempfile,math
from pathlib import Path
from format_prior_gateway import FormatPriorGateway,ENV,verify_prior
from neeko_candidate_gateway import receipt_v3,EXTRA
from format_match_v2 import transition,pool,digest,FormatRejected
from optimize_58 import stable_seed
ENGINE="bd3b0abbeba26b87223e407a5317eba91e5d459bf36fd842a7371afa695f5287"
PRIOR="0df5c0f231c642f366e7707fb6b60f9e291dc1ff8a65a4266654876c96b564ef"
AGENT="ismcts:sims=24"
def require(ok,message):
    if not ok:raise FormatRejected(message)
def vector_hash(v):return digest(json.dumps(v,sort_keys=True).encode())
def strict_terminal(stdout,forced):
    lines=[s for s in stdout.splitlines() if s.startswith("Game over:")]
    require(len(lines)==1,"missing or duplicate terminal")
    m=re.fullmatch(r"Game over: winner=([12]) \| reason=P([12]) reached 8 points \| turns=([1-9][0-9]*)",lines[0])
    require(m is not None and m[1]==m[2],"unsupported or inconsistent terminal")
    starts=[s for s in stdout.splitlines() if s.startswith("TOURNAMENT_FORCED_STARTING_PLAYER=")]
    require(starts==([] if forced is None else [f"TOURNAMENT_FORCED_STARTING_PLAYER={forced}"]),"forced start mismatch")
    return int(m[1]),f"P{m[1]} reached 8 points",int(m[3])
class GuardedBO3(FormatPriorGateway):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        require(self.engine_sha==ENGINE and self.provenance()["public_prior_sha256"]==PRIOR,"wrong pinned candidate")
    def _native(self,raws,expected,seed,agent,timeout,forced_start=None):
        require(digest(self.engine.read_bytes())==ENGINE,"candidate drift")
        require(type(seed) is int and 0<seed<=2147483647 and agent==AGENT and type(timeout) in (int,float) and math.isfinite(timeout) and timeout>0,"invalid game parameters")
        require(forced_start is None or type(forced_start) is int and forced_start in (1,2),"invalid forced start")
        env={k:v for k,v in os.environ.items() if not k.startswith("RIFTBOUND_")}
        env[ENV]=self.prior_text
        env["RIFTBOUND_ISMCTS_CHECK_WORLDS"]="1"
        if forced_start is not None:env["RIFTBOUND_FORCE_STARTING_PLAYER"]=str(forced_start)
        with tempfile.TemporaryDirectory(prefix="rb_p007_") as root:
            paths=[Path(root)/f"p{i}.txt" for i in (1,2)]
            for path,raw in zip(paths,raws):path.write_bytes(raw)
            cmd=[str(self.engine),"--deck1",str(paths[0]),"--deck2",str(paths[1]),"--agent1",agent,"--agent2",agent,
                 "--game-mode","match","--seed",str(seed),"--web","off","--render-html","off","--debug","--trace"]
            p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=timeout)
        require(p.returncode==0,"native failure; exit="+str(p.returncode)+" stderr_sha256="+digest(p.stderr.encode()))
        verify_prior(p.stdout,self.prior_text)
        observed=receipt_v3(p.stdout,self.definitions)
        require(observed==expected,"native ordered registration mismatch")
        winner,reason,turns=strict_terminal(p.stdout,forced_start)
        trace=[s.strip() for s in p.stdout.splitlines() if s.strip().startswith("[TRC] ")]
        require(any("DRAW_HAND:" in s for s in trace) and any("INTENT:" in s for s in trace),"missing gameplay trace")
        return {**self.provenance(),"status":"complete","winner":winner,"reason":reason,"turns":turns,"seed":seed,
                "agent":agent,"native_ids_verified":True,"forced_starting_player":forced_start,
                "deck_sha256":[digest(r) for r in raws],"native_vectors_sha256":[vector_hash(v) for v in observed],
                "native_extra_legend_ids":[v[EXTRA] for v in observed],"world_check_enabled":True,
                "trace_lines":len(trace),"trace_sha256":digest("\n".join(trace).encode())}
    def declared_bo3(self,one,two,policy,seed,agent=AGENT,timeout=180):
        return series(self,(Path(one).read_bytes(),Path(two).read_bytes()),policy,seed,agent,timeout)
def prepare(g,raws,policy):
    regs=[g.gate.validate(r) for r in raws]
    require(type(policy) is dict and not set(policy)-{"game2","game3"},"invalid policy")
    policy=json.loads(json.dumps(policy,allow_nan=False))
    result=[(raws,regs,None)]
    for i in (2,3):
        p=policy.get(f"game{i}",{})
        require(type(p) is dict and not set(p)-{"p1","p2","loser_chooses_start"},"invalid game policy")
        choice=p.get("loser_chooses_start","self")
        require(choice in ("self","opponent"),"invalid loser choice")
        vs=[transition(v,p.get(f"p{j}",{})) for j,v in enumerate(regs,1)]
        for original,active in zip(regs,vs):
            require(pool(original)==pool(active) and all(original[h]==active[h] for h in ("Legend","Battlefields","Runes",EXTRA)),"registered pool changed")
        active=tuple(raw if v==o else g.render(v) for raw,v,o in zip(raws,vs,regs))
        require([g.gate.validate(r) for r in active]==vs,"rendered vector drift")
        result.append((active,vs,choice))
    return result
def series(g,raws,policy,seed,agent=AGENT,timeout=180):
    require(type(seed) is int and 0<seed<=2147483647 and agent==AGENT,"invalid series parameters")
    require(type(timeout) in (int,float) and math.isfinite(timeout) and timeout>0,"invalid timeout")
    raws=tuple(bytes(r) for r in raws)
    prepared=prepare(g,raws,policy)
    seeds=[stable_seed(seed,"p0_07_points_bo3_v1",i) or 1 for i in (1,2,3)]
    require(len(set(seeds))==3,"seed collision")
    games=[];wins=[0,0];prev=None
    for i,(active,vs,choice) in enumerate(prepared,1):
        flip=i==2
        start=None if i==1 else (3-prev if choice=="self" else prev)
        forced=None if start is None else (3-start if flip else start)
        ordered=active[::-1] if flip else active;ordered_v=vs[::-1] if flip else vs
        try:
            r=g.game(*ordered,seeds[i-1],agent,timeout,forced_start=forced)
            require(r.get("status")=="complete" and type(r.get("winner")) is int and r["winner"] in (1,2) and
                    r.get("reason")==f'P{r["winner"]} reached 8 points' and type(r.get("turns")) is int and r["turns"]>0 and
                    r.get("native_ids_verified") is True and r.get("world_check_enabled") is True and
                    r.get("seed")==seeds[i-1] and r.get("agent")==agent and r.get("forced_starting_player")==forced and
                    r.get("deck_sha256")==[digest(x) for x in ordered] and r.get("native_vectors_sha256")==[vector_hash(v) for v in ordered_v] and
                    r.get("native_extra_legend_ids")==[v[EXTRA] for v in ordered_v] and
                    type(r.get("trace_lines")) is int and r["trace_lines"]>0 and re.fullmatch("[0-9a-f]{64}",r.get("trace_sha256","")) and
                    all(r.get(k)==v for k,v in g.provenance().items()),"invalid game receipt")
        except (FormatRejected,subprocess.TimeoutExpired) as e:
            # Never credit a winner for an invalid/incomplete series.
            return {**g.provenance(),"status":"incomplete","winner":None,"score":wins,"games":games,
                    "failed_game":i,"error":str(e),"registered_sha256":[digest(x) for x in raws],
                    "round_clock_modeled":False,"adaptive_sideboarding":False}
        w=3-r["winner"] if flip else r["winner"]
        games.append({**r,"game":i,"seat_flipped":flip,"winner_identity":w,"previous_loser_identity":None if prev is None else 3-prev,
                      "loser_choice":choice,"first_player_identity":start,"active_identity_sha256":[digest(x) for x in active]})
        wins[w-1]+=1;prev=w
        if max(wins)==2:break
    return {**g.provenance(),"status":"complete_declared_points_bo3","winner":wins.index(2)+1,"score":wins,"games":games,
            "registered_sha256":[digest(x) for x in raws],"sideboarding_applied":any(x["active_identity_sha256"]!=[digest(r) for r in raws] for x in games[1:]),
            "round_clock_modeled":False,"adaptive_sideboarding":False,"draws_supported":False}
