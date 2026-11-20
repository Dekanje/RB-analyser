#!/usr/bin/env python3
"""Include all 58 legends in a truthful status/matchup matrix.
Unknown Radiance matchups stay UNSIMULATED (no fabricated win rates).
"""
import csv,itertools,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_actual_games import decode,header
OUT=ROOT/"combined_results"
def readcsv(p):
    with p.open(newline="",encoding="utf8") as f:return list(csv.DictReader(f))
def writecsv(p,rows,fields):
    with p.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
    all_decks=decode()
    if len(all_decks)!=58:raise SystemExit("Expected 58 original decklists")
    patched=json.loads((ROOT/"compat/replacement_manifest.json").read_text())
    legend_to_file={header(p):p.name for p in all_decks}
    old=readcsv(OUT/"all_matchups.csv")
    ranking={x["legend"]:x for x in readcsv(OUT/"exploratory_ranking.csv")}
    meta=json.loads((OUT/"metadata.json").read_text())
    expected=49*50//2
    if not meta["complete"] or len(old)!=expected or len(ranking)!=49:
        raise SystemExit(f"Missing/partial 49-deck combined results: matchups={len(old)} rankings={len(ranking)}")
    field={}
    for item in old:
        field[(item["a"],item["b"])]=item
    legends=sorted(legend_to_file)
    statuses=[]
    for legend in legends:
        simulated=legend in ranking
        is_patched=legend_to_file[legend] in patched
        statuses.append({"legend":legend,"filename":legend_to_file[legend],
                        "deck_version":"engine_compatibility_variant" if is_patched else "original",
                        "engine_status":"simulated" if simulated else "unsupported_card_effects",
                        "series_wins":ranking[legend]["series_wins"] if simulated else "",
                        "series_losses":ranking[legend]["series_losses"] if simulated else "",
                        "observed_win_fraction":ranking[legend]["win_fraction"] if simulated else "",
                        "note":"Unplayed: missing Radiance legend/champion/card implementations" if not simulated else
                               "Modified card choices; incomparable to original optimized deck" if is_patched else
                               "Original deck; experimental low-search MCTS results"})
    writecsv(OUT/"all_58_deck_status.csv",statuses,
             ["legend","filename","deck_version","engine_status","series_wins","series_losses","observed_win_fraction","note"])
    cross=[]
    for a,b in itertools.combinations_with_replacement(legends,2):
        match=field.get((a,b))
        result=("simulated_compatible_variants" if legend_to_file[a] in patched or legend_to_file[b] in patched
                else "simulated_original") if match else "unplayed_unimplemented_engine_cards"
        cross.append({"a":a,"b":b,"status":result,
                      "series":2 if match else 0,
                      "a_wins":match["a_wins"] if match else "",
                      "b_wins":match["b_wins"] if match else "",
                      "note":"No sideboard swaps; MCTS10; 3 games per series" if match else
                             "No simulated result; do not use as win rate"})
    writecsv(OUT/"all_1711_pairings_with_status.csv",cross,
             ["a","b","status","series","a_wins","b_wins","note"])
    counts={"legends_total":58,"engine_playable":len(ranking),"revised_decks":10,
            "unimplemented_radiance_decks":9,"pairings_total_including_mirrors":len(cross),
            "pairings_simulated":len(old),"pairings_unplayed":len(cross)-len(old),
            "simulations_card_exact_for_10_revised":False,"tournament_BO3":False,
            "card_swap_manifest":"compat/replacement_manifest.json",
            "results_experimental":True}
    (OUT/"full_58_coverage_summary.json").write_text(json.dumps(counts,indent=2))
    print("ALL_58_COVERAGE "+json.dumps(counts),flush=True)
    return 0 if len(cross)==1711 and len(old)==1225 else 1
if __name__=="__main__":raise SystemExit(main())
