#!/usr/bin/env python3
"""Pinned-format native receipt verification and declared tournament BO3 adapter."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import subprocess
import tempfile

from format_gateway import FormatGate, FormatRejected, HEADINGS, ENGINE_SHA
from optimize_58 import stable_seed

PROFILE_SHA = "5525a697ec86e792d86fe7f8f418d7ff7dad95b3ee5912ac5efaea344fb790b4"
REGISTRY_SHA = "d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
ZONES = dict(zip(("legend","champion","main","bf","rune","side"),HEADINGS))


def digest(raw):
    return sha256(raw).hexdigest()


def receipt_vectors(stdout, by_definition):
    """Parse actual ordered native DeckSubmission debug dump, not predicted IDs."""
    seats = {}
    seat = None
    for line in stdout.splitlines():
        m = re.fullmatch(r"\[DECK\] P([12]) \(.+\):",line.strip())
        if m:
            seat = int(m[1])
            if seat in seats:
                raise FormatRejected("duplicate native deck header")
            seats[seat] = {s:[] for s in HEADINGS}
            continue
        row = re.fullmatch(r"\s*(legend|champion|main|bf|rune|side)\s+\[([^\]]+)\]\s+.+",line)
        if row and seat is not None:
            if row[2] not in by_definition:
                raise FormatRejected("unknown native definition: "+row[2])
            seats[seat][ZONES[row[1]]].append(by_definition[row[2]])
    if set(seats) != {1,2}:
        raise FormatRejected("missing native deck receipts")
    return [seats[i] for i in (1,2)]


def pool(v):
    return Counter(v["Champion"]+v["MainDeck"]+v["Sideboard"])


def transition(v, plan):
    if not isinstance(plan,dict) or set(plan)-{"swaps","chosen_champion"}:
        raise FormatRejected("unexpected plan keys")
    out = {k:list(x) for k,x in v.items()}
    swaps = plan.get("swaps",[])
    if not isinstance(swaps,list):
        raise FormatRejected("invalid swap list")
    # All swaps are simultaneous with respect to the original registration.
    remove, add = Counter(),Counter()
    for s in swaps:
        if not isinstance(s,dict) or set(s)!={"main_out","side_in","copies"}:
            raise FormatRejected("invalid swap row")
        a,b,n=s["main_out"],s["side_in"],s["copies"]
        if any(type(x) is not int or x<=0 for x in (a,b,n)) or a==b:
            raise FormatRejected("invalid swap values")
        remove[a]+=n;add[b]+=n
    if remove & add or remove-Counter(v["MainDeck"]) or add-Counter(v["Sideboard"]):
        raise FormatRejected("swap exceeds registered zone or overlaps")
    def replace(src, take, insert):
        remaining = take.copy()
        dst=[]
        for i in src:
            if remaining[i]:
                remaining[i]-=1
            else:
                dst.append(i)
        return dst+list(insert.elements())
    out["MainDeck"]=replace(v["MainDeck"],remove,add)
    out["Sideboard"]=replace(v["Sideboard"],add,remove)
    chosen=plan.get("chosen_champion",v["Champion"][0])
    if type(chosen) is not int:
        raise FormatRejected("champion ID must be integer")
    if chosen!=v["Champion"][0]:
        old=v["Champion"][0]
        for zone in ("MainDeck","Sideboard"):
            if chosen in out[zone]:
                out[zone][out[zone].index(chosen)]=old
                out["Champion"]=[chosen]
                break
        else:
            raise FormatRejected("champion not in registered pool")
    if pool(out)!=pool(v):
        raise FormatRejected("registered pool changed")
    return out


class VerifiedGateway:
    def __init__(self,engine,registry,profile,allowed_sets,exempt_ids=()):
        self.engine=Path(engine).resolve()
        p=Path(profile).read_bytes();r=Path(registry).read_bytes()
        if digest(p)!=PROFILE_SHA or digest(r)!=REGISTRY_SHA:
            raise FormatRejected("unapproved profile or registry hash")
        if digest(self.engine.read_bytes())!=ENGINE_SHA:
            raise FormatRejected("wrong engine hash")
        self.gate=FormatGate(json.loads(p),json.loads(r),allowed_sets,exempt_ids)
        self.definitions={c["card_def_id"]:i for i,c in self.gate.ids.items()}
        if len(self.definitions)!=len(self.gate.ids):
            raise FormatRejected("ambiguous definition ID")

    def provenance(self):
        return {"profile_id":"standard-global-2026-11-23","profile_sha256":PROFILE_SHA,
                "registry_sha256":REGISTRY_SHA,"engine_sha256":ENGINE_SHA,
                "allowed_sets":sorted(self.gate.sets),"rune_exempt_ids":sorted(self.gate.exempt),
                "full_official_legality_certified":False}

    def render(self,v):
        lines=[]
        for h in HEADINGS:
            lines.append(h+":")
            # Do not group separated repeats or reorder any vector.
            lines.extend("1 "+self.gate.ids[i]["name"]+" #"+str(i) for i in v[h])
        raw=("\n".join(lines)+"\n").encode()
        if self.gate.validate(raw)!=v:
            raise FormatRejected("rendered registration differs")
        return raw

    def _native(self,raws,expected,seed,agent,timeout,forced_start=None):
        # Internal diagnostic executor; production game() requires strict preflight.
        if digest(self.engine.read_bytes())!=ENGINE_SHA:
            raise FormatRejected("engine changed")
        if type(seed) is not int or seed<=0 or timeout<=0 or not re.fullmatch(r"ismcts:sims=[1-9][0-9]*",agent):
            raise FormatRejected("invalid native execution parameters")
        if forced_start is not None and forced_start not in (1,2):
            raise FormatRejected("invalid forced seat")
        env=os.environ.copy()
        env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
        if forced_start is not None:
            env["RIFTBOUND_FORCE_STARTING_PLAYER"]=str(forced_start)
        with tempfile.TemporaryDirectory(prefix="rb_format_v2_") as root:
            paths=[Path(root)/f"p{i}.txt" for i in (1,2)]
            for p,raw in zip(paths,raws):
                p.write_bytes(raw)
            cmd=[str(self.engine),"--deck1",str(paths[0]),"--deck2",str(paths[1]),
                 "--agent1",agent,"--agent2",agent,"--game-mode","match","--seed",str(seed),
                 "--web","off","--render-html","off","--debug"]
            p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=timeout)
        if p.returncode:
            raise FormatRejected("native validation/execution failed: "+p.stderr[-500:])
        observed=receipt_vectors(p.stdout,self.definitions)
        if observed!=expected:
            raise FormatRejected("native resolved ordered vectors mismatch")
        terminals=re.findall(r"^Game over: winner=([12]) \| reason=(.+) \| turns=(\d+)$",p.stdout,re.M)
        starts=re.findall(r"TOURNAMENT_FORCED_STARTING_PLAYER=([12])",p.stdout)
        if len(terminals)!=1 or (starts!=[] if forced_start is None else starts!=[str(forced_start)]):
            raise FormatRejected("missing/incorrect native terminal or first-player receipt")
        w,reason,turns=terminals[0]
        return {**self.provenance(),"status":"complete","winner":int(w),"reason":reason,
                "turns":int(turns),"seed":seed,"agent":agent,"native_ids_verified":True,
                "forced_starting_player":forced_start,
                "deck_sha256":[digest(x) for x in raws],
                "native_vectors_sha256":[digest(json.dumps(v,sort_keys=True).encode()) for v in observed]}

    def game(self,raw1,raw2,seed,agent="ismcts:sims=24",timeout=180,*,forced_start=None):
        raws=(bytes(raw1),bytes(raw2))
        expected=[self.gate.validate(r) for r in raws]
        return self._native(raws,expected,seed,agent,timeout,forced_start)

    def declared_bo3(self,one,two,policy,seed,agent="ismcts:sims=24",timeout=180):
        # Freeze source files and plans once; never re-read them between games.
        raws=(Path(one).read_bytes(),Path(two).read_bytes())
        registrations=[self.gate.validate(r) for r in raws]
        policy=json.loads(json.dumps(policy))
        if not isinstance(policy,dict) or set(policy)-{"game2","game3"}:
            raise FormatRejected("policy must contain only game2/game3")
        prepared={1:(raws,False,"self")}
        for i in (2,3):
            plan=policy.get(f"game{i}",{})
            if not isinstance(plan,dict) or set(plan)-{"p1","p2","loser_chooses_start"}:
                raise FormatRejected("invalid game policy")
            choice=plan.get("loser_chooses_start","self")
            if choice not in ("self","opponent"):
                raise FormatRejected("invalid loser choice")
            vectors=[transition(v,plan.get(f"p{j}",{})) for j,v in enumerate(registrations,1)]
            # Recheck every active registration against same frozen profile.
            active=tuple(raws[j] if v==registrations[j] else self.render(v)
                         for j,v in enumerate(vectors))
            for r in active:
                self.gate.validate(r)
            prepared[i]=(active,i==2,choice)
        games=[];wins=[0,0];previous=None
        for i in (1,2,3):
            active,flip,choice=prepared[i]
            identity=None if i==1 else (3-previous if choice=="self" else previous)
            forced=None if identity is None else (3-identity if flip else identity)
            result=self.game(*(active[::-1] if flip else active),
                             stable_seed(seed,"format_declared_bo3_v2",i) or 1,
                             agent,timeout,forced_start=forced)
            previous=3-result["winner"] if flip else result["winner"]
            wins[previous-1]+=1
            games.append({**result,"game":i,"winner_identity":previous,
                          "first_player_identity":identity,"seat_flipped":flip})
            if max(wins)==2:
                break
        return {**self.provenance(),"status":"complete_declared_bo3","winner":wins.index(2)+1,
                "score":wins,"registered_sha256":[digest(r) for r in raws],"games":games,
                "sideboarding_applied":any(prepared[g["game"]][0]!=raws for g in games[1:]),
                "round_clock_modeled":False,"adaptive_sideboarding":False}
