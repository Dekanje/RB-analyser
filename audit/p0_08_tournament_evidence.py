"""Audit frozen historical projections. Never execute native binaries or claim event simulation."""
import argparse,hashlib,itertools,json,math,re,sys,tempfile,zipfile
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from worlds_lineups import rank_lineups
from worlds_robust_lineups import evaluate_robustness
from worlds_swiss_sensitivity import evaluate,swiss_record_tail

PINS={
"14841669639":"986d5dbca90c1dc621c6ee309278790e1cf00dddd4ac592969fb8c8442762fc1",
"14823477036":"1cdf59d8cc2c36dde035a142ad09556ee9323cfdbb836488e0c20bd75c09f872",
"14833662301":"d600355e3a13c8dcbad08bcc67aa995f14b95f51247b09a501d5cc7c89097b99",
"14854411637":"18009f683aeafc88c7209c4581dbc9556b34f23d44c44c2db77bc11702aa4770",
"14843520123":"5785ea6d1c419e52c7adfcb76b21dc3644d608f218eaeb0b2b36dce1f4ea7877",
"14853402315":"37b0c166ccf790a1009e2ee5389c5f9ece750c28477e8f39f68107399dfbc780",
"14858215856":"c6f3ae5e9c4f8c3c8f63cfbe40d0111cb167b7c57ed17db7118ac2fc271d2e4d"}
ENGINE="17dfb633c6936d74596305c35dcbd0b8793a3da0463e7ce932ab5105c66fe5af"
REGISTRY="d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
SCENARIOS="2244555cf69a8fd9996fcb5005d24c45a59181ca3312f6a36ad39d5b64204b3c"
SETS={"OGN","SFD","UNL","VEN","RAD"}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def archive(root,i):
    p=root/f"{i}.zip";require(sha(p.read_bytes())==PINS[str(i)],"archive drift "+str(i));return zipfile.ZipFile(p)
def stable(*p):return int.from_bytes(hashlib.sha256("|".join(map(str,p)).encode()).digest()[:4],"big")&0x7fffffff
def game_score(row):
    wins=[0,0]
    require(type(row["seat"]) is int and row["seat"] in (0,1),"bad seat")
    require(type(row["target_win"]) is bool and row["status"]=="complete" and row["complete"] is True and not row["error"],"invalid series")
    require(len(row["games"]) in (2,3),"invalid game count")
    for i,g in enumerate(row["games"]):
        require(max(wins)<2 and g["game"]==i+1 and g["status"]=="complete" and not g["error"] and type(g["winner_seat"]) is int and g["winner_seat"] in (1,2),"invalid game progression")
        own_first=(row["seat"]+i)%2==0
        wins[0 if (g["winner_seat"]==1)==own_first else 1]+=1
    require(max(wins)==2 and row["target_win"]==(wins[0]==2),"inconsistent series winner")
    return tuple(wins)
def exact_tail(a,b,c,k):
    # Independent enumeration of all 512 binary outcomes, not convolution.
    ps=[a]*3+[b]*3+[c]*3
    return sum(math.prod(p if win else 1-p for p,win in zip(ps,v))
               for v in itertools.product((0,1),repeat=9) if sum(v)>=k)
def format_inventory(decks,cards):
    names=defaultdict(list)
    for c in cards:
        names[c["name"]].append(c)
    domains={};outside=[];ambiguous=[];legend_outside=[]
    for name,raw in decks.items():
        # Historical labels are champion name + legend subtitle.
        hero,title=name.split(", ",1)
        matches=[c for c in cards if c["card_type"]=="legend" and c["name"].removesuffix(" - Starter")==title and hero in c["tags"]]
        if len(matches)!=1:
            # Match same name precedence as existing name-based registry where
            # necessary; do not hide unresolved functional-print ambiguity.
            unique={c["name"]:c for c in reversed(matches)}
            require(len(unique)==1,"unresolved legend "+name)
            chosen=next(iter(unique.values()))
        else:chosen=matches[0]
        domains[name]=set(chosen["domains"]);require(len(domains[name])==2,"bad domains")
        if chosen["set"] not in SETS:legend_outside.append(name)
        section=None
        for line in raw.decode().splitlines():
            if line.endswith(":"):section=line[:-1];continue
            if not line.strip() or line.startswith("#"):continue
            m=re.fullmatch(r"([1-9][0-9]*) (.+)",line)
            require(m is not None,"bad card row")
            if section=="Legend":continue
            possible={c["set"] for c in names[m[2]]}
            require(possible,"unresolved name")
            if not possible&SETS:outside.append({"legend":name,"section":section,"copies":int(m[1]),"possible_sets":sorted(possible)})
            if len(possible)>1:ambiguous.append({"legend":name,"section":section,"possible_sets":sorted(possible)})
    return domains,outside,ambiguous,legend_outside
def run(root):
    with archive(root,14823477036) as z:
        trials=json.loads(z.read("all_58_trials.json"))
        byhash={sha(z.read(n)):z.read(n) for n in z.namelist() if n.startswith("selected_decks/") and n.endswith(".txt")}
        decks={r["legend"]:byhash[r["effective_sha256"]] for r in trials}
    require(len(decks)==len(byhash)==58,"incomplete roster")
    with archive(root,14833662301) as z:
        registry=z.read("registry.json");require(sha(registry)==REGISTRY and sha(z.read("riftbound"))==ENGINE,"historical source drift")
    with archive(root,14854411637) as z:
        require(z.read("registry.json")==registry,"projection registry differs")
    domains,outside,ambiguous,legend_outside=format_inventory(decks,json.loads(registry)["cards"])
    with archive(root,14841669639) as z:
        raw=z.read("scenarios.json");require(sha(raw)==SCENARIOS,"scenario drift");rows=json.loads(raw)
        meta=json.loads(z.read("summary.json"));standings=json.loads(z.read("standings.json"))
    require(meta["engine_sha256"]==ENGINE and meta["agent"]=="ismcts:sims=128" and meta["sideboarding"] is False and meta["all_games_complete"] is True and meta["completed_bo3_series"]==1140,"source metadata")
    anchors=sorted({r["anchor"] for r in rows});require(len(anchors)==10 and set(anchors)<=set(decks),"anchor roster")
    expected={(n,a,s,0) for n in decks for a in anchors if n!=a for s in (0,1)}
    seen=set();seeds=set();counts=Counter();wins=Counter();games=Counter();outcomes=defaultdict(list)
    for r in rows:
        k=(r["target"],r["anchor"],r["seat"],r["repetition"])
        require(k in expected and k not in seen,"schedule mismatch");seen.add(k)
        seed=stable(202611240102,"WORLD_PRE_LEGACY_ELITE_ANCHOR_V1",*k)
        require(r["seed"]==seed and seed not in seeds,"seed mismatch");seeds.add(seed)
        n,a=k[:2]
        require(r["target_sha256"]==sha(decks[n]) and r["anchor_sha256"]==sha(decks[a]),"deck drift")
        score=game_score(r);games[len(r["games"])]+=1
        counts[n]+=1;wins[n]+=r["target_win"];outcomes[n,a].append(r["target_win"])
    require(seen==expected and len(rows)==1140,"incomplete matrix")
    require(len(standings)==58 and {r["legend"] for r in standings}==set(decks),"standings mismatch")
    for i,r in enumerate(standings,1):
        n=r["legend"];require(r["exploratory_elite_rank"]==i and r["wins"]==wins[n] and r["series"]==counts[n] and r["deck_sha256"]==sha(decks[n]) and r["win_rate"]==round(wins[n]/counts[n],6),"standings tally")
    require(standings==sorted(standings,key=lambda x:(-x["win_rate"],x["legend"])),"standing sort")
    data={(n,a):.5 if n==a else sum(outcomes[n,a])/2 for n in decks for a in anchors}
    triples={t for t in itertools.combinations(sorted(decks),3) if len(set.union(*(domains[n] for n in t)))==6}
    require(len(triples)==919,"lineup count")
    with archive(root,14843520123) as z:
        line=json.loads(z.read("lineups.json"))
    with archive(root,14853402315) as z:
        robust=json.loads(z.read("all_919_robust.json"));rm=json.loads(z.read("robust_lineups.json"))
    with archive(root,14858215856) as z:
        swiss=json.loads(z.read("all919_swiss_thresholds.json"));sm=json.loads(z.read("swiss_threshold_sensitivity.json"))
    require(line["worlds_win_probability_estimated"] is False and rm["result_is_worlds_win_probability"] is False and sm["actual_worlds_win_probability_estimated"] is False,"mislabelled claims")
    require(rm["source_sha256"]==sm["source_sha256"]==SCENARIOS and rm["source_engine_sha256"]==ENGINE,"projection source drift")
    require(rank_lineups(data,domains,anchors,500,202611240404)[:20]==line["top_20"],"lineup replay differs")
    require(evaluate_robustness(data,domains,anchors,600,1.,202611240900)==robust,"robust replay differs")
    require(evaluate(data,domains,anchors,600,1.,202611251100)==swiss,"Swiss projection replay differs")
    require(rm["top20_robust"]==robust[:20] and sm["top20"]==swiss[:20],"report mismatch")
    for rs in (robust,swiss):
        require(len(rs)==919 and {tuple(r["lineup"]) for r in rs}==triples,"lineup coverage")
    for r in swiss:
        for metric in ("mean","p10","p90"):
            v=[r[f"model_probability_at_least_{k}_wins_{metric}"] for k in (6,7,8)]
            require(1>=v[0]>=v[1]>=v[2]>=0,"tail monotonicity")
        for k in (6,7,8):
            p=f"model_probability_at_least_{k}_wins_"
            require(0<=r[p+"p10"]<=r[p+"p90"]<=1,"invalid interval")
    cases=0
    for a,b,c in itertools.product((0.,.2,.5,.8,1.),repeat=3):
        for k in range(10):
            require(math.isclose(exact_tail(a,b,c,k),swiss_record_tail(a,b,c,k),abs_tol=1e-12),"independent PMF mismatch");cases+=1
    return {"status":"PASS_HISTORICAL_PROJECTION_AUDIT_ONLY","historical_engine_sha256":ENGINE,"registry_sha256":REGISTRY,
            "source_scenarios_sha256":SCENARIOS,"series_receipts":len(rows),"reported_game_records":sum(k*v for k,v in games.items()),
            "series_game_count_distribution":dict(games),"distinct_series_seeds":len(seeds),"lineups":len(triples),
            "replayed_top20":20,"replayed_robust_rows":len(robust),"replayed_swiss_rows":len(swiss),
            "independent_probability_checks":cases,"declared_five_set_format_nonlegend_outside_rows":outside,
            "declared_five_set_format_outside_legend_names":legend_outside,"cross_set_name_ambiguities":ambiguous,
            "source_format_certified":False,"actual_swiss_pairings":0,"completed_tournaments":0,
            "new_native_games":0,"production_authorized":False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--archives",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=run(a.archives);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:json.dump(r,f,indent=2,sort_keys=True);f.write("\n")
    print(r["status"],r["series_receipts"],r["reported_game_records"],r["independent_probability_checks"])
if __name__=="__main__":main()
