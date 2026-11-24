"""Read-only historical agent calibration audit; never a promotion gate."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import zipfile

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def stable_seed(master, name, rep):
    return int.from_bytes(hashlib.sha256(
        f"AGENT_BENCH_V1|{master}|{name}|{rep}".encode()).digest()[:4],"big") & 0x7fffffff

def audit(rows, decks, master, expected_names, repetitions):
    pairs=defaultdict(dict)
    for row in rows:
        name,rep,seat=row["deck_file"],row["repetition"],row["challenger_first"]
        require(name in expected_names and type(rep) is int and 0<=rep<repetitions and type(seat) is bool,"unexpected schedule")
        require(row["deck_sha256"]==decks[name],"deck hash mismatch")
        require(row["seed"]==stable_seed(master,name,rep) and row["seed"]>0,"seed mismatch")
        require(row["status"]=="complete" and type(row["winner_seat"]) is int and row["winner_seat"] in (1,2),"incomplete or invalid game")
        win=row["winner_seat"]==(1 if seat else 2)
        require(row["challenger_win"] is win,"winner mismatch")
        require(seat not in pairs[name,rep],"duplicate seat")
        require(type(row["seconds"]) in (int,float) and math.isfinite(row["seconds"]) and row["seconds"]>=0,"invalid duration")
        pairs[name,rep][seat]=win
    require(set(pairs)=={(n,i) for n in expected_names for i in range(repetitions)} and all(set(v)=={True,False} for v in pairs.values()),"incomplete pair schedule")
    wins=Counter(sum(v.values()) for v in pairs.values())
    by_deck={n:sum(sum(v.values()) for (d,_),v in pairs.items() if d==n) for n in sorted(expected_names)}
    non_ties=wins[0]+wins[2]
    p=min(1,2*sum(math.comb(non_ties,k) for k in range(min(wins[0],wins[2])+1))/2**non_ties)
    return {"games":len(rows),"pairs":len(pairs),"wins":sum(by_deck.values()),"win_rate":sum(by_deck.values())/len(rows),
        "pair_0_1_2_wins":[wins[i] for i in range(3)],
        "conditional_pair_sign_p_two_sided":p,
        "pair_sign_assumption":"independent exchangeable non-tied seed pairs; not established across repeated decks",
        "deck_wins":by_deck,"seconds_sum":round(sum(r["seconds"] for r in rows),3),
        "seat_wins":{"challenger_p1":sum(v[True] for v in pairs.values()),"challenger_p2":sum(v[False] for v in pairs.values())}}

def load(root, artifact, pins):
    path=root/(str(artifact)+".zip")
    require(sha(path.read_bytes())==pins[str(artifact)],"archive hash mismatch: "+str(artifact))
    return zipfile.ZipFile(path)

PILOT=("ahri_nine_tailed_fox.txt","akali_rogue_assassin.txt","ambessa_matriarch_of_war.txt")
PANEL=tuple(x+".txt" for x in ("ambessa_matriarch_of_war","rek_sai_void_burrower","volibear_relentless_storm",
    "leblanc_deceiver","draven_glorious_executioner","master_yi_wuju_bladesman","kai_sa_daughter_of_the_void",
    "rengar_pridestalker","darius_hand_of_noxus","kennen_heart_of_the_tempest","annie_dark_child",
    "miss_fortune_bounty_hunter","orianna_lady_of_clockwork","ziggs_hexplosives_expert","teemo_swift_scout","fiora_grand_duelist"))
SIX=tuple(x+".txt" for x in ("draven_glorious_executioner","leblanc_deceiver","master_yi_wuju_bladesman",
    "miss_fortune_bounty_hunter","rek_sai_void_burrower","ambessa_matriarch_of_war"))

def execute(root,pins):
    with load(root,14823477036,pins) as z:
        decks={Path(n).name:sha(z.read(n)) for n in z.namelist() if n.startswith("selected_decks/") and n.endswith(".txt")}
    require(len(decks)==58,"wrong source roster")
    engines={}
    for aid,expected in ((14833662301,"17dfb633c6936d74596305c35dcbd0b8793a3da0463e7ce932ab5105c66fe5af"),
                         (14854411637,"58dbebe75c3a55c354056867cfa885cc6a8a589aa511c0984ca524a754ad0807")):
        with load(root,aid,pins) as z:
            engines[aid]=sha(z.read("riftbound"))
        require(engines[aid]==expected,"engine binary mismatch")
    campaigns=[]
    for label,ids,member,names,reps,master,engine,base,challenger in (
        ("pilot",[14839198370],"pilot.json",PILOT,1,20261123,14833662301,24,128),
        ("panel",[14841005482],"expanded-panel.json",PANEL,3,20261123,14833662301,24,128),
        ("512_calibration",[14857800869,14858091240,14857665884,14858730345,14855454553,14858910569],
         "strength.json",SIX,2,202611250900,14854411637,128,512)):
        rows=[]
        hashes={}
        for aid in ids:
            with load(root,aid,pins) as z:
                raw=z.read(member)
            hashes[str(aid)]=sha(raw)
            d=json.loads(raw)
            s=d["summary"]
            require(s["engine_sha256"]==engines[engine] and s["baseline_agent"]==f"ismcts:sims={base}" and s["challenger_agent"]==f"ismcts:sims={challenger}","agent/engine mismatch")
            require(s["identical_deck_on_both_sides"] is True and s["mirrored_agent_seating"] is True and s["failed_games"]==0 and s["completed_games"]==len(d["games"]),"historical summary mismatch")
            require(s["challenger_wins"]==sum(r["challenger_win"] for r in d["games"]),"historical wins mismatch")
            rows.extend(d["games"])
        out=audit(rows,decks,master,names,reps)
        campaigns.append({"label":label,"engine_sha256":engines[engine],"agent_budgets":[base,challenger],"master_seed":master,
                          "report_hashes":hashes,**out})
    with load(root,14859210516,pins) as z:
        agg=json.loads(z.read("agent512_strength_decision.json"))
    cal=campaigns[-1]
    require(agg["512_wins"]==cal["wins"] and agg["completed_real_engine_games"]==cal["games"] and
            agg["full_cpp_407_engine_sha256"]==cal["engine_sha256"],"512 aggregate mismatch")
    require({r["deck"]:r["challenger_wins"] for r in agg["results_by_deck"]}==cal["deck_wins"] and
            all(r["deck_sha256"]==decks[r["deck"]] for r in agg["results_by_deck"]),"512 per-deck mismatch")
    # The pilot and panel overlap on Ambessa repetition zero. Do not
    # pool repeated seed/seat conditions or incompatible engine revisions.
    overlap=set(PILOT)&set(PANEL)
    return {"status":"PASS_HISTORICAL_RECEIPT_AUDIT_ONLY","campaigns":campaigns,
            "historical_game_records":sum(c["games"] for c in campaigns),
            "pilot_panel_overlapping_decks":sorted(overlap),
            "pilot_panel_repeated_seed_seat_conditions":2*len(overlap),
            "current_candidate_strength_certified":False,"fitness_evaluated":False,"adopted":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archives",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    pins=json.loads(Path(__file__).with_name("p0_05_agent_archive_pins.json").read_text())
    report=execute(a.archives,pins)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write("\n")
    print(report["status"],report["historical_game_records"])

if __name__=="__main__":
    main()
