#!/usr/bin/env python3
"""Independent blind-seed BO3 validation of accepted Radiance deck substitutions.

Keep baseline and selected list fixed; use new seeds not consulted by the
candidate-selection workflow. Every game is real AlphaRune ISMCTS-vs-ISMCTS.
Incomplete series are excluded from decision and never assigned fake wins.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_radiance_ismcts import engine_bo3
from optimize_58 import stable_seed
from run_actual_games import header

OPPONENTS=[
    "Rek'Sai, Void Burrower",
    "LeBlanc, Deceiver",
    "Annie, Dark Child",
    "Draven, Glorious Executioner",
    "Volibear, Relentless Storm",
    "Lucian, Purifier",
]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def mcnemar_two_sided(candidate_only,baseline_only):
    n=candidate_only+baseline_only
    if n==0:return 1.0
    smaller=min(candidate_only,baseline_only)
    return min(1.0,2*sum(math.comb(n,k) for k in range(smaller+1))/(2**n))

def main(args):
    chosen=json.loads((args.selected/'full_trials.json').read_text(encoding='utf8'))
    changed=[x for x in chosen if x['changed']]
    if args.legend_prefix:
        changed=[x for x in changed if x['legend'].casefold().startswith(args.legend_prefix.casefold())]
    if not changed:raise RuntimeError('No selected upgrades to verify')
    originals={header(p):p for p in (args.baselines/'baselines').glob('*.txt')}
    selected={header(p):p for p in (args.selected/'selected_decks').glob('*.txt')}
    assert len(originals)==len(selected)==58
    opponents=sorted(originals) if args.all_opponents else OPPONENTS
    scenarios=[]
    for entry in changed:
        legend=entry['legend']
        base=originals[legend];candidate=selected[legend]
        assert digest(base)==entry['original_sha256']
        assert digest(candidate)==entry['selected_sha256']
        assert digest(base)!=digest(candidate)
        for op_name in opponents:
            if op_name==legend:continue
            for seat in (0,1):
                for repeat in range(args.repetitions):
                    seed=stable_seed(args.seed,legend,op_name,seat,repeat,'INDEPENDENT_BLIND')
                    scenarios.append((legend,base,candidate,op_name,originals[op_name],seat,repeat,seed))
    def eval_one(legend,base,candidate,op_name,opp,seat,repeat,seed):
        a=engine_bo3(args.engine,base,opp,seat,seed,args.agent,args.timeout,os.environ.copy())
        b=engine_bo3(args.engine,candidate,opp,seat,seed,args.agent,args.timeout,os.environ.copy())
        return {'legend':legend,'opponent':op_name,'seat':seat,'repeat':repeat,'seed':seed,
                'baseline_status':a['status'],'candidate_status':b['status'],
                'baseline_win':a['status']=='complete' and a['winner']==seat+1,
                'candidate_win':b['status']=='complete' and b['winner']==seat+1,
                'baseline_games':a['games'],'candidate_games':b['games'],
                'baseline_error':a.get('error',''),'candidate_error':b.get('error','')}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(eval_one,*s) for s in scenarios]
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            row=f.result()
            results.append(row)
            if i%8==0:print('BLIND_PROGRESS',i,len(scenarios),flush=True)
    results.sort(key=lambda x:(x['legend'],x['opponent'],x['seat'],x['repeat']))
    summary=[]
    for entry in changed:
        legend=entry['legend']
        rows=[r for r in results if r['legend']==legend]
        complete=[r for r in rows if r['baseline_status']==r['candidate_status']=='complete']
        candidate_only=sum(r['candidate_win'] and not r['baseline_win'] for r in complete)
        baseline_only=sum(r['baseline_win'] and not r['candidate_win'] for r in complete)
        base_wins=sum(r['baseline_win'] for r in complete)
        cand_wins=sum(r['candidate_win'] for r in complete)
        pval=mcnemar_two_sided(candidate_only,baseline_only)
        passed=len(complete)==len(rows) and cand_wins>base_wins and pval<.05
        record={'legend':legend,'expected_scenarios':len(rows),
                'completed_paired_scenarios':len(complete),
                'incomplete_paired_scenarios':len(rows)-len(complete),
                'baseline_wins':base_wins,'candidate_wins':cand_wins,
                'candidate_only_wins':candidate_only,'baseline_only_wins':baseline_only,
                'difference_pp':round(100*(cand_wins-base_wins)/len(complete),2) if complete else None,
                'mcnemar_exact_two_sided_p':round(pval,6),
                'blind_supported_at_5pct_unadjusted':passed,
                'status':('SUPPORTED_EXPLORATORY_NOT_MULTIPLE_TEST_ADJUSTED'
                          if passed else 'INCONCLUSIVE_OR_UNSUPPORTED'),
                'baseline_sha256':entry['original_sha256'],
                'candidate_sha256':entry['selected_sha256']}
        summary.append(record)
        print('RAD_BLIND_RESULT',json.dumps(record),flush=True)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'blind_scenarios.json').write_text(json.dumps(results,indent=2))
    (args.output/'blind_summary.json').write_text(json.dumps({
        'schema':1,'seed':args.seed,'agent':args.agent,'mode':'NO_SIDEBOARD_FIXED_DECK_BO3',
        'opponents':opponents,'multiple_testing_adjusted':False,
        'all_scenarios_complete':all(x['incomplete_paired_scenarios']==0 for x in summary),
        'decisions':summary},indent=2))
    with (args.output/'blind_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--selected',type=pathlib.Path,default=pathlib.Path('results/radiance_58_ismcts'))
    p.add_argument('--baselines',type=pathlib.Path,default=pathlib.Path('results/full_radiance_pool'))
    p.add_argument('--engine',type=pathlib.Path,default=pathlib.Path('alpharune/build/riftbound'))
    p.add_argument('--output',type=pathlib.Path,default=pathlib.Path('results/radiance_blind'))
    p.add_argument('--seed',type=int,default=202611249121)
    p.add_argument('--agent',default='ismcts:sims=24')
    p.add_argument('--timeout',type=int,default=75)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--repetitions',type=int,default=2)
    p.add_argument('--all-opponents',action='store_true',help='Cover every other legend (57)')
    p.add_argument('--legend-prefix',default='',help='Optional single tested legend name prefix')
    args=p.parse_args()
    if args.workers not in range(1,9) or args.repetitions not in range(1,11):
        p.error('Invalid workers or repetitions')
    raise SystemExit(main(args))
