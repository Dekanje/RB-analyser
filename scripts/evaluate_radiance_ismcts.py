#!/usr/bin/env python3
"""Real engine paired ISMCTS comparisons for executable Radiance-only swaps.

Reads the exhaustive 167-card catalog audit, but deliberately tests only names
already in the compiled AlphaRune registry. Unimplemented cards are excluded
and retain NO claimed game outcome. Baseline decklists are immutable.
"""
import argparse,collections,csv,hashlib,json,pathlib,sys,concurrent.futures,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from optimize_58 import parse_deck,render_deck,benchmark,stable_seed,TOP,key
from run_actual_games import header

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def read_proposals(path):
    with path.open(encoding='utf8',newline='') as f:rows=list(csv.DictReader(f))
    by=collections.defaultdict(list)
    for row in rows:
        if row['status']=='ENGINE_CANDIDATE_UNTESTED' and row['compiled_name_match']=='True':
            by[row['legend']].append(row)
    return by

def paired(exe,candidate,baseline,opponents,agent,seed,phase,samples,timeout,executor,cache):
    schedule=[]
    for opp_name,opp in opponents:
        for seat in (0,1):
            for iteration in range(samples):
                gameseed=stable_seed(seed,opp_name,phase,seat,iteration)
                schedule.append((opp_name,opp,seat,gameseed))
    def schedule_game(deck,opp,seat,game_seed):
        a,b=(deck,opp) if seat==0 else (opp,deck)
        k=(sha(a),sha(b),game_seed,agent)
        if k not in cache:
            cache[k]=executor.submit(benchmark,exe,a,b,game_seed,agent,timeout,os.environ.copy())
        return cache[k]
    for _,opp,seat,game_seed in schedule:
        schedule_game(baseline,opp,seat,game_seed)
        schedule_game(candidate,opp,seat,game_seed)
    baseline_wins=candidate_wins=0;failures=[]
    for opponent_name,opp,seat,game_seed in schedule:
        a=schedule_game(baseline,opp,seat,game_seed).result()
        b=schedule_game(candidate,opp,seat,game_seed).result()
        if a['status']!='complete' or b['status']!='complete':
            failures.append({'opponent':opponent_name,'seed':game_seed,
                'baseline_status':a['status'],'challenger_status':b['status'],
                'baseline_error':a.get('error',''),'challenger_error':b.get('error','')})
            continue
        baseline_wins+=int(a['winner']==seat+1)
        candidate_wins+=int(b['winner']==seat+1)
    return {'agent':agent,'samples':len(schedule),
            'complete':not failures,'baseline_wins':baseline_wins,
            'candidate_wins':candidate_wins,'difference':candidate_wins-baseline_wins,
            'failures':failures}

def main(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    sources=args.audit/'baselines'
    baselines={header(p):p for p in sources.glob('*.txt')}
    if len(baselines)!=58:raise RuntimeError('Wrong baseline roster: '+str(len(baselines)))
    proposed=read_proposals(args.audit/'all_58_radiance_proposals.csv')
    selected={};reports=[];cache={}
    exe=args.engine.resolve()
    if not exe.exists():raise RuntimeError('Missing AlphaRune compiled binary')
    names=[name for i,name in enumerate(sorted(baselines)) if i%args.shards==args.shard]
    pool=concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)
    try:
        for name in names:
            current=baselines[name]
            text,main,side=parse_deck(current)
            possibilities=proposed.get(name,[])[:args.candidates]
            available=[n for n in TOP if n in baselines and n!=name]
            # Opponent selection is predeclared by fixed seed, not conditioned on outcomes.
            available.sort(key=lambda n:stable_seed(args.seed,name,n))
            opponents=[(n,baselines[n]) for n in available[:args.opponents]]
            trials=[];accepted=False
            for i,p in enumerate(possibilities):
                repl=main.copy()
                if repl[p['remove']]<=0:raise RuntimeError('Missing removal '+p['remove'])
                repl[p['remove']]-=1;repl[p['add']]+=1
                if repl[p['remove']]==0:del repl[p['remove']]
                if sum(repl.values())!=39:raise RuntimeError('Deck size changed')
                dest=out/'candidate_files'/f'{key(name).replace(" ","_")}_{i}.txt'
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text(render_deck(text,repl),encoding='utf8')
                train=paired(exe,dest,current,opponents,args.agent,args.seed+1,'train',args.training_samples,
                             args.timeout,pool,cache)
                holdout=None
                # Never allow failed engine games to count as losses for either side.
                if train['complete'] and train['difference']>=args.min_delta:
                    holdout=paired(exe,dest,current,opponents,args.agent,args.seed+2,'holdout',
                                   args.holdout_samples,args.timeout,pool,cache)
                chosen=(holdout is not None and holdout['complete']
                        and holdout['difference']>=args.min_delta)
                trials.append({'from':p['remove'],'to':p['add'],'code':p['add_code'],
                               'text_based_score_not_win_rate':p['score_difference_heuristic'],
                               'train':train,'holdout':holdout,'accepted':chosen})
                if chosen:
                    current=dest;accepted=True
                    break
            outpath=out/'selected_decks'/baselines[name].name
            outpath.parent.mkdir(parents=True,exist_ok=True)
            outpath.write_bytes(current.read_bytes())
            report={'legend':name,'original_sha256':sha(baselines[name]),
                    'selected_sha256':sha(outpath),'changed':accepted,
                    'radiance_swaps_attempted':len(trials),'trials':trials,
                    'unimplemented_pool_never_simulated':True}
            reports.append(report)
            print('RAD_ISMCTS',name,'accepted',accepted,'attempted',len(trials),
                  'games_cached',len(cache),flush=True)
            (out/'shard_results.json').write_text(json.dumps(reports,indent=2),encoding='utf8')
    finally:
        pool.shutdown(wait=True)
    summary={'shard':args.shard,'shards':args.shards,'legends':len(names),
             'legends_completed':len(reports),'engine_agent':args.agent,
             'accepted':sum(x['changed'] for x in reports),
             'total_game_attempts':len(cache),
             'no_unsupported_cards_simulated':True,
             'source':'full 167-card Radiance catalog, executable compiled-name subset only',
             'limitations':'Pairwise fixed deck games, no between-game sideboarding; exploratory ISMCTS comparisons, not complete BO3 competitive ranking.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print('RAD_ISMCTS_SUMMARY',json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--audit',type=pathlib.Path,default=ROOT/'results/full_radiance_pool')
    p.add_argument('--engine',type=pathlib.Path,default=ROOT/'alpharune/build/riftbound')
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'results/radiance_ismcts_search')
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=8)
    p.add_argument('--agent',default='ismcts:sims=24')
    p.add_argument('--candidates',type=int,default=2)
    p.add_argument('--opponents',type=int,default=3)
    p.add_argument('--training-samples',type=int,default=2)
    p.add_argument('--holdout-samples',type=int,default=2)
    p.add_argument('--min-delta',type=int,default=3)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--timeout',type=int,default=75)
    p.add_argument('--seed',type=int,default=2026112321)
    args=p.parse_args()
    if not(0<=args.shard<args.shards and 1<=args.candidates<=10 and
           1<=args.opponents<=8 and 1<=args.training_samples<=10 and
           1<=args.holdout_samples<=10 and 1<=args.workers<=16):
        p.error('Invalid budget or shard arguments')
    main(args)
