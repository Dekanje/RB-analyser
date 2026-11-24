"""Audit both broad mutation populations and the historical two-legend holdout."""
import argparse,itertools,json,math
from collections import Counter
from pathlib import Path
from p0_06_shard_diversity import parse,changed,key,distance,open_pin,require,sha

PINS={
"14823477036":"1cdf59d8cc2c36dde035a142ad09556ee9323cfdbb836488e0c20bd75c09f872",
"14842711299":"1d325903a31fdd711e6975c5cdd8855c5072b63db18e3126a138438f05248b2e",
"14849185083":"4fd4265815519b496448de05ac17311424086532f0a7aefec482ea5db27d375f",
"14843051242":"a684875638c4798e510e598815dd15e08e0869fbe3eb69671cd6251f4359f8a6",
"14845061918":"a984ef53d1fb13993a4dbdd96df8e2da91dd1fae32a9b57d9e7b322297156c2d"}
ENGINE="17dfb633c6936d74596305c35dcbd0b8793a3da0463e7ce932ab5105c66fe5af"
NAMES={"Draven, Glorious Executioner","Rek'Sai, Void Burrower"}

def population(root,i,selected):
    with open_pin(root,i,PINS) as z:
        m=json.loads(z.read("manifest.json"));ds=Counter();pair=Counter();adds=set();removes=set();unique=0;rows={};paths=set();extras=0
        require(m["candidate_count"]==2320 and m["legend_count"]==58 and m["mutation_range"]==[3,8] and len(m["records"])==58,"population metadata")
        for r in m["records"]:
            n=r["legend"];require(n not in rows and n in selected and r["source_sha256"]==sha(selected[n]),"source mismatch")
            orig=parse(selected[n]);vs=[];rows[n]=[]
            require(r["generated"]==r["requested"]==len(r["candidates"])==40,"population count")
            for p in r["candidates"]:
                path=p["path"];require(path not in paths,"duplicate path");paths.add(path)
                raw=z.read(path);require(sha(raw)==p["sha256"] and p["engine_simulated"] is False,"candidate hash/status")
                parts=raw.split(b"\nNeekoLegends:\n")
                require(len(parts)<=2,"duplicate extra section")
                core=parts[0];v=parse(core)
                extra=[]
                if len(parts)==2:
                    extra=[l[2:].decode() for l in parts[1].splitlines() if l]
                    require(len(extra)==len(set(extra))==3 and all(l.startswith(b"1 ") for l in parts[1].splitlines() if l),"extra legend structure")
                    extras+=1
                require(extra==p.get("neeko_additional_legends",[]) and (not extra or v["MainDeck"]["Neeko, Blending In"]>0),"extra manifest mismatch")
                require(v==changed(orig,p["mutation_steps"]),"mutation mismatch")
                d=distance(orig["MainDeck"],v["MainDeck"])
                require(d==p["changed_main_slots"]==len(p["mutation_steps"]) and 3<=d<=8,"distance mismatch")
                ds[d]+=1;vs.append(v);adds.update(x["add"] for x in p["mutation_steps"]);removes.update(x["remove"] for x in p["mutation_steps"])
                rows[n].append({"path":path,"sha256":p["sha256"],"core":key(v),"extra":extra,"distance":d})
            unique+=len({key(v) for v in vs});pair.update(distance(a["MainDeck"],b["MainDeck"]) for a,b in itertools.combinations(vs,2))
        require(set(rows)==set(selected) and paths=={n for n in z.namelist() if n.endswith(".txt")} and len(paths)==2320,"population coverage")
        return rows,{"artifact":i,"count":len(paths),"unique_name_multisets_per_legend":unique,"distance":dict(ds),
                     "pairwise_distance":dict(pair),"added_names":len(adds),"removed_names":len(removes),"extra_legend_files":extras}

def verify_pairs(e,expected):
    rows=e["scenarios"];require(len(rows)==expected==e["completed"]==e["expected"] and e["incomplete"]==0,"incomplete pairs")
    seen=set();counts=Counter();schedule=set()
    for r in rows:
        k=(r["opponent"],r["seat"],r["repetition"])
        require(k not in seen and r["seat"] in (0,1) and r["repetition"]==0 and type(r["seed"]) is int and r["seed"]>0,"pair schedule")
        seen.add(k);schedule.add((*k,r["seed"]))
        require(r["both_complete"] is True and r["baseline_status"]==r["candidate_status"]=="complete" and r["baseline_win"] in (0,1) and r["candidate_win"] in (0,1),"invalid outcome")
        counts[r["baseline_win"],r["candidate_win"]]+=1
    opponents={r[0] for r in seen}
    require(seen=={(n,s,0) for n in opponents for s in (0,1)},"incomplete seats")
    b=counts[1,0]+counts[1,1];c=counts[0,1]+counts[1,1];x,y=counts[1,0],counts[0,1];d=x+y
    p=min(1.,2*sum(math.comb(d,i) for i in range(min(x,y)+1))/2**d)
    require((b,c,x,y,c-b)==tuple(e[k] for k in ("baseline_wins","candidate_wins","baseline_only_wins","candidate_only_wins","candidate_minus_baseline")) and math.isclose(e["mcnemar_p"],p,abs_tol=1e-9),"paired statistic drift")
    return schedule,opponents,p

def run(root):
    with open_pin(root,14823477036,PINS) as z:
        records=json.loads(z.read("all_58_trials.json"));byhash={sha(z.read(n)):z.read(n) for n in z.namelist() if n.startswith("selected_decks/") and n.endswith(".txt")}
        selected={r["legend"]:byhash[r["effective_sha256"]] for r in records}
    old,a=population(root,14842711299,selected);new,b=population(root,14849185083,selected)
    modified=0
    for n in old:
        for x,y in zip(old[n],new[n]):
            require((x["path"],x["core"],x["distance"])==(y["path"],y["core"],y["distance"]),"unexpected population change")
            if x["sha256"]!=y["sha256"]:
                require(not x["extra"] and len(y["extra"])==3,"non-extra change")
                modified+=1
    with open_pin(root,14843051242,PINS) as z:
        shortlist=json.loads(z.read("shortlists.json"));screen=json.loads(z.read("full_screening.json"))
    require(set(screen)==set(shortlist["shortlists"])==NAMES and shortlist["engine_sha256"]==ENGINE,"screen metadata")
    schedules={};fields={};bycandidate={};screenpairs=0
    for n,rows in screen.items():
        require(len(rows)==40 and {r["candidate_index"] for r in rows}==set(range(40)),"screen coverage")
        for r in rows:
            i=r["candidate_index"];c=old[n][i]
            require(r["candidate_path"]==c["path"] and r["changed_main_slots"]==c["distance"],"screen candidate mismatch")
            s,o,p=verify_pairs(r["evaluation"],6);screenpairs+=6
            require(n not in schedules or schedules[n]==s,"screen schedule mismatch")
            schedules[n]=s;fields[n]=o;bycandidate[n,i]=r["evaluation"]
    short={}
    for n,rows in shortlist["shortlists"].items():
        require(len(rows)==5,"shortlist count")
        for r in rows:
            i=r["candidate_index"];c=old[n][i];ev=bycandidate[n,i]
            require(r["sha256"]==c["sha256"] and r["candidate_path"]==c["path"] and
                    r["paired_win_delta"]==ev["candidate_minus_baseline"],"shortlist mismatch")
            short[n,i]=c["sha256"]
    require(len(short)==10,"shortlist duplication")
    with open_pin(root,14845061918,PINS) as z:
        summary=json.loads(z.read("holdout_summary.json"));holdout=json.loads(z.read("raw_holdout.json"))
    require(summary["engine_sha256"]==ENGINE and summary["tested_candidates"]==10 and summary["any_confirmed"] is False,"holdout metadata")
    result={(r["legend"],r["candidate_index"]):r for r in summary["results"]}
    require(len(result)==10 and set(result)==set(short),"holdout summary coverage")
    hs={};seen=set();pairs=0;rawps=[]
    for r in holdout:
        n,i=r["legend"],r["candidate_index"];k=(n,i)
        require(k not in seen and r["candidate_sha256"]==short[k] and r["source_sha256"]==sha(selected[n]) and r["engine_sha256"]==ENGINE and r["agent"]=="ismcts:sims=128","holdout pin drift");seen.add(k)
        s,o,p=verify_pairs(r["outcomes"],12);pairs+=12;rawps.append(p)
        require(set(r["training_opponents"])==fields[n] and set(r["holdout_opponents"])==o and not fields[n]&o and
                not {q[3] for q in schedules[n]}&{q[3] for q in s},"holdout overlap")
        require(n not in hs or hs[n]==s,"holdout schedule drift");hs[n]=s
        v=result[k];e=r["outcomes"]
        require(v["candidate_sha256"]==short[k] and v["holdout_candidate_wins"]==e["candidate_wins"] and v["holdout_baseline_wins"]==e["baseline_wins"] and v["holdout_delta"]==e["candidate_minus_baseline"] and
                math.isclose(v["mcnemar_p_raw"],p,abs_tol=1e-9) and math.isclose(v["bonferroni_adjusted_p"],min(1.,10*p),abs_tol=1e-9) and v["holdout_confirmed_after_10_comparisons"] is False,"holdout result drift")
    require(seen==set(short),"missing holdout")
    return {"status":"PASS_HISTORICAL_BROAD_EVIDENCE_ONLY","population_versions":[a,b],"changed_extra_legend_files":modified,
            "screened_legends":2,"screened_candidates":80,"screen_paired_comparisons":screenpairs,
            "holdout_candidates":10,"holdout_paired_comparisons":pairs,"minimum_raw_holdout_p":min(rawps),
            "minimum_bonferroni_p":min(1.,10*min(rawps)),"confirmed":0,
            "limitations":["historical fixed-deck BO3 paired aggregates; not per-game native receipts",
                           "different historical engine, not current candidate",
                           "name-level diversity, not proof of independent archetypes or official legality"],
            "new_games":0,"adopted":0}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--archives",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=run(a.archives);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:json.dump(r,f,indent=2,sort_keys=True);f.write("\n")
    print(r["status"],r["screen_paired_comparisons"],r["holdout_paired_comparisons"])
if __name__=="__main__":main()
