#!/usr/bin/env python3
"""Reproducible, conservative decklist hill-climb using real AlphaRune games.

Original source decks are immutable. This tests legal single-card substitutions
using hidden-information ISMCTS and paired baseline/holdout games. It never
relabels timeouts as losses or claims fixed-deck results are tournament BO3.
"""
import argparse, collections, concurrent.futures, hashlib, json, os, pathlib, random, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_actual_games import decode, header
from legal_candidate import make_legal_candidate

BANNED = {"Riven, Broken Blade", "Zhonya's Hourglass", "Stellacorn Herder",
 "Nocturne, Horrifying", "Rhasa the Sunderer", "Brynhir Thundersong",
 "Dazzling Aurora", "Baited Hook", "Emperor's Dais", "Star Spring",
 "Called Shot", "Ekko, Recurrent", "Draven, Vanquisher", "Fight or Flight",
 "Scrapheap", "Stealthy Pursuer", "Stacked Deck", "The Arena's Greatest",
 "Aspirant's Climb", "Dreaming Tree", "Obelisk of Power", "Reaver's Row"}
TOP = ["Rek'Sai, Void Burrower", "Ambessa, Matriarch of War", "Annie, Dark Child",
       "Darius, Hand of Noxus", "Rengar, Pridestalker", "Draven, Glorious Executioner",
       "Volibear, Relentless Storm", "Lucian, Purifier", "Master Yi, Wuju Bladesman",
       "LeBlanc, Deceiver", "Mordekaiser, Iron Revenant", "Ziggs, Hexplosives Expert"]

def key(s):
    s=re.sub(r"[^a-z0-9]+", " ",s.replace('’',"'").casefold()).strip()
    return s[4:] if s.startswith('the ') else s

BAN_KEYS = {key(x) for x in BANNED}

def stable_seed(*parts):
    raw='|'.join(str(x) for x in parts).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], 'big') & 0x7fffffff

def file_sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def parse_deck(path):
    text=path.read_text(encoding='utf-8'); lines=text.splitlines()
    i=lines.index('MainDeck:')+1; j=lines.index('Battlefields:')
    main=collections.Counter()
    for line in lines[i:j]:
        if not line.strip(): continue
        m=re.fullmatch(r'\s*(\d+) (.+)',line)
        if not m: raise ValueError('Malformed deck row: '+line)
        main[m.group(2)]+=int(m.group(1))
    assert sum(main.values())==39, path
    k=lines.index('Sideboard:')+1
    side=collections.Counter()
    for line in lines[k:]:
        m=re.fullmatch(r'\s*(\d+) (.+)',line)
        if m: side[m.group(2)]+=int(m.group(1))
    return text,main,side

def render_deck(original_text, main):
    lines=original_text.splitlines()
    i=lines.index('MainDeck:')+1; j=lines.index('Battlefields:')
    updated=lines[:i] + [f'{main[n]} {n}' for n in sorted(main) if main[n]>0] + [''] + lines[j:]
    return '\n'.join(updated).rstrip()+'\n'

def registry(path):
    raw=json.loads(path.read_text(encoding='utf-8'))
    names={}
    for c in raw['cards']:
        if c['name'] not in names: names[c['name']]=c
    return names

def effective_domains(name,byname):
    subtitle=key(name.split(', ',1)[-1])
    hero=key(name.split(', ',1)[0])
    legends=[c for c in byname.values() if c['card_type']=='legend']
    hits=[c for c in legends if subtitle in key(c['name'])]
    if len(hits)!=1:
        hits=[c for c in legends if key(c['name'])==subtitle]
    if len(hits)!=1:
        hits=[c for c in legends if any(key(tag)==hero for tag in c.get('tags') or [])]
    if len(hits)!=1:
        raise ValueError(f'Could not unambiguously resolve legend domain: {name}, {[c["name"] for c in hits]}')
    return set(hits[0]['domains'])

def is_unique(card): return '[Unique]' in (card.get('ability_text') or '')

def eligible(card, domains, current_counts, side, champion_tags):
    if card['card_type'] not in ('unit','gear','spell') or card.get('banned'): return False
    if key(card['name']) in BAN_KEYS: return False
    if not set(card['domains']).issubset(domains): return False
    if (card.get('super_type') or '').lower()=='signature': return False
    # Don't introduce a second Chosen Champion or a token into the main deck.
    if 'token' in (card.get('super_type') or '').lower(): return False
    copies=current_counts.get(card['name'],0)+side.get(card['name'],0)
    if copies >= (1 if is_unique(card) else 3): return False
    return True

def card_score(card, totals, leader):
    cost=max(1,card.get('energy_cost',0) or 0) + 1.8*(card.get('power_cost',0) or 0)
    might=card.get('might') or card.get('might_bonus') or 0
    feats=card.get('features') or {}
    text=(card.get('ability_text') or '').lower()
    utility=sum(0.55 for word in ('draw','kill','buff','ready','move','stun','deal damage','reduce') if word in text)
    utility+=sum(0.4 for word in ('[reaction]','[accelerate]','[assault]','[shield]','[ganking]') if word in text)
    ally=set(card.get('tags') or ())
    tribal=0.8*len(ally & leader)
    popularity=min(1.5,totals.get(card['name'],0)*0.075)
    return (max(0,might)*0.62+utility+tribal+popularity)/(1+cost*0.19)

def propose(name,path,byname,total_pop,n,seed):
    original,main,side=parse_deck(path)
    domains=effective_domains(name,byname)
    chosen=re.search(r'^ChosenChampion:\s*\n1 (.+)
    chosen_card=byname.get(chosen.group(1)) if chosen else None
    leader_tags=set(chosen_card.get('tags') or ()) if chosen_card else set()
    # Require a known, already compiled card before considering a substitution.
    oldcards=[byname[x] for x in main if x in byname]
    pool=[x for x in byname.values() if eligible(x,domains,main,side,leader_tags)]
    scored=[]
    for old in oldcards:
        if (old.get('super_type') or '').lower()=='signature':continue
        old_score=card_score(old,total_pop,leader_tags)
        candidates=[x for x in pool if x['card_type']==old['card_type'] and
                    abs((x.get('energy_cost') or 0)-(old.get('energy_cost') or 0))<=2 and
                    abs((x.get('power_cost') or 0)-(old.get('power_cost') or 0))<=1 and
                    x['name']!=old['name']]
        scored.extend((card_score(new,total_pop,leader_tags)-old_score,old['name'],new['name']) for new in candidates)
    rng=random.Random(stable_seed(seed,name,'proposal'))
    scored.sort(key=lambda q:(-q[0],q[1],q[2]))
    # Mix top scoring swaps with exploration; never declare these scores win rates.
    strong=scored[:min(80,len(scored))]
    rng.shuffle(strong)
    selected=[]; used=set()
    for _,old,new in strong + scored[:min(250,len(scored))]:
        if (old,new) in used or any(p['remove']==old or p['add']==new for p in selected):continue
        used.add((old,new))
        changed=main.copy();changed[old]-=1;changed[new]+=1
        if changed[old]<=0:del changed[old]
        if sum(changed.values())!=39:raise AssertionError('Mutation changed total')
        # Apply full main + sideboard Unique and copy-limit checks.
        if any(c+side.get(x,0)>(1 if is_unique(byname[x]) else 3) for x,c in changed.items() if x in byname):continue
        selected.append({'remove':old,'add':new,'text':render_deck(original,changed)})
        if len(selected)==n:break
    return selected

def benchmark(exe,deck1,deck2,seed,agent,timeout,env):
    cmd=[str(exe.absolute()),'--deck1',str(deck1.absolute()),'--deck2',str(deck2.absolute()),
         '--agent1',agent,'--agent2',agent,'--game-mode','match','--seed',str(seed),
         '--web','off','--render-html','off']
    start=time.monotonic()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(status='timeout',winner=None,seconds=round(time.monotonic()-start,3))
    hit=re.search(r'Game over:\s*winner\s*=\s*([012])',p.stdout)
    status='complete' if p.returncode==0 and hit and int(hit.group(1)) in (1,2) else 'error'
    return dict(status=status,winner=int(hit.group(1)) if hit else None,
                seconds=round(time.monotonic()-start,3),error=p.stderr[-250:] if status=='error' else '')

def main(args):
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    original=decode()
    sources=make_legal_candidate(original,output/'legal_inputs',output/'legal_source_manifest.json')
    byname=registry(args.registry)
    total_pop=collections.Counter()
    for p in sources.values():
        _,main,_=parse_deck(p);total_pop.update(main)
    legends=sorted(sources)
    if args.legends:
        requested={key(x) for x in args.legends}
        names=[name for name in legends if key(name) in requested]
        if len(names)!=len(requested):
            missing=sorted(requested-{key(name) for name in names})
            raise ValueError('Missing exact legends in --legends: '+', '.join(missing))
    else:names=legends
    if args.max_legends:names=names[:args.max_legends]
    exe=args.engine.resolve()
    env=os.environ.copy()
    if args.ld_library_path:env['LD_LIBRARY_PATH']=str(args.ld_library_path)
    results=[]
    game_cache={}
    executor=concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)
    start=time.monotonic()
    try:
      for ix,name in enumerate(names):
        source_text,main,side=parse_deck(sources[name])
        baseline_path=sources[name]
        rounds=[]
        for round_ix in range(args.rounds):
          proposed=propose(name,baseline_path,byname,total_pop,args.candidates,
                           args.seed+round_ix*21911)
          candidates=[]
          for pidx,p in enumerate(proposed):
              dest=output/'proposals'/f'{ix:02d}_round{round_ix+1}_{pidx:02d}.txt'
              dest.parent.mkdir(parents=True,exist_ok=True)
              dest.write_text(p['text'],encoding='utf-8')
              candidates.append({**p,'path':dest})
          eligible_top=[n for n in TOP if n in sources and n!=name]
          r=random.Random(stable_seed(args.seed,name,round_ix,'opponents'))
          opponents=r.sample(eligible_top,min(args.opponents,len(eligible_top)))
          def compare(candidate_path, phase, samples, agent_override=None):
              play_agent=agent_override or args.agent
              schedule=[]
              for op in opponents:
                for iteration in range(samples):
                  seat=iteration%2
                  seed=stable_seed(args.seed,name,op,round_ix,phase,iteration)
                  schedule.append((op,seat,seed))
              def single(deck,op,seat,seed):
                  a,b=(deck,sources[op]) if seat==0 else (sources[op],deck)
                  game_key=(file_sha(a),file_sha(b),seed,play_agent)
                  if game_key not in game_cache:
                      game_cache[game_key]=executor.submit(benchmark,exe,a,b,seed,play_agent,args.timeout,env)
                  game=game_cache[game_key].result()
                  return game, int(game['winner']==seat+1) if game['status']=='complete' else None
              for op,seat,seed in schedule:
                  for deck in (baseline_path,candidate_path):
                      a,b=(deck,sources[op]) if seat==0 else (sources[op],deck)
                      game_key=(file_sha(a),file_sha(b),seed,play_agent)
                      if game_key not in game_cache:
                          game_cache[game_key]=executor.submit(benchmark,exe,a,b,seed,play_agent,args.timeout,env)
              baseline=[];challenger=[];errors=[]
              for op,seat,seed in schedule:
                  for deck,out in [(baseline_path,baseline),(candidate_path,challenger)]:
                      game,win=single(deck,op,seat,seed)
                      if win is None:errors.append({'opponent':op,'seed':seed,'status':game['status'],'error':game.get('error','')})
                      else:out.append(win)
              return {'baseline_wins':sum(baseline),'candidate_wins':sum(challenger),
                      'total':len(schedule),'valid':len(baseline)==len(challenger)==len(schedule),
                      'errors':errors}
          # Fast random-agent prefilter is only a screening step. Final acceptance
          # requires independent ISMCTS training and held-out comparisons.
          pretrial=[]
          for cand in candidates:
              screening=compare(cand['path'],'prefilter',args.prefilter_samples,agent_override='random')
              pretrial.append({'remove':cand['remove'],'add':cand['add'],
                               'file':str(cand['path'].relative_to(output)),
                               'prefilter':screening,
                               'delta_prefilter':screening['candidate_wins']-screening['baseline_wins']})
          pretrial.sort(key=lambda x:(-x['delta_prefilter'],x['remove'],x['add']))
          trials=[]
          for screen in [x for x in pretrial if x['prefilter']['valid']][:args.shortlist]:
              train=compare(output/screen['file'],'training',args.samples)
              trials.append({**screen,'train':train,
                             'delta_train':train['candidate_wins']-train['baseline_wins']})
          trials.sort(key=lambda x:(-x['delta_train'],x['remove'],x['add']))
          selected=None;heldout=None
          if trials and trials[0]['train']['valid'] and trials[0]['delta_train']>=args.min_gain:
              best=trials[0]; heldout=compare(output/best['file'],'holdout',args.holdout)
              if heldout['valid'] and heldout['candidate_wins']-heldout['baseline_wins']>=args.min_gain:
                  selected=best
          rounds.append({'round':round_ix+1,'prefilter':pretrial,'trials':trials,'selected':selected,
                         'holdout':heldout,'opponents':opponents})
          print('OPTIMIZE',ix+1,'/',len(names),name,'round',round_ix+1,
                'selected',bool(selected),'best_delta',trials[0]['delta_train'] if trials else None,
                'holdout',((heldout['candidate_wins']-heldout['baseline_wins']) if heldout else None),
                'elapsed',round(time.monotonic()-start,1),flush=True)
          if not selected:break
          baseline_path=output/selected['file']
        destination=output/'selected_decks'/sources[name].name;destination.parent.mkdir(exist_ok=True)
        destination.write_text(baseline_path.read_text(encoding='utf-8'),encoding='utf-8')
        report={'legend':name,'original_sha256':file_sha(sources[name]),
                'effective_sha256':file_sha(destination),'selected':file_sha(sources[name])!=file_sha(destination),
                'selected_swaps':[{'round':r['round'],'remove':r['selected']['remove'],'add':r['selected']['add']}
                                  for r in rounds if r['selected']],
                'rounds':rounds,'agent':args.agent,'samples':args.samples,
                'holdout_samples':args.holdout,
                'rule':'Accept only if training AND independent holdout gain >= threshold; no synthetic wins.'}
        results.append(report)
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    finally: executor.shutdown(wait=True)
    summary={'legends_tested':len(results),'improved':sum(r['selected'] for r in results),
             'failed':len(results)-len(names),'agent':args.agent,'seed':args.seed,
             'simulations':len(game_cache),'seconds':round(time.monotonic()-start,2),
             'note':'Exploratory holdout-gated changes only; not proof of globally optimal decks.'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('OPTIMIZATION_SUMMARY',json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--engine',type=pathlib.Path,default=ROOT/'alpharune/build/riftbound')
    p.add_argument('--registry',type=pathlib.Path,default=ROOT/'radiance/engine_overlay/compiled_registry.json')
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'optimization/results')
    p.add_argument('--agent',default='ismcts:sims=24')
    p.add_argument('--legends',nargs='*',default=[])
    p.add_argument('--max-legends',type=int,default=0)
    p.add_argument('--candidates',type=int,default=3)
    p.add_argument('--shortlist',type=int,default=2)
    p.add_argument('--prefilter-samples',type=int,default=2)
    p.add_argument('--rounds',type=int,default=2)
    p.add_argument('--opponents',type=int,default=4)
    p.add_argument('--samples',type=int,default=2)
    p.add_argument('--holdout',type=int,default=3)
    p.add_argument('--min-gain',type=int,default=2)
    p.add_argument('--workers',type=int,default=6)
    p.add_argument('--timeout',type=int,default=60)
    p.add_argument('--seed',type=int,default=20261121)
    p.add_argument('--ld-library-path',type=pathlib.Path)
    a=p.parse_args()
    if not (1<=a.shortlist<=a.candidates and 1<=a.prefilter_samples<=40 and 1<=a.rounds<=8 and 1<=a.candidates<=30 and 1<=a.opponents<=12 and 1<=a.samples<=50 and 1<=a.holdout<=50 and 1<=a.min_gain and 1<=a.workers<=32):p.error('Invalid search budget')
    main(a),original,re.M)
    chosen_card=byname.get(chosen.group(1)) if chosen else None
    leader_tags=set(chosen_card.get('tags') or ()) if chosen_card else set()
    # Require a known, already compiled card before considering a substitution.
    oldcards=[byname[x] for x in main if x in byname]
    pool=[x for x in byname.values() if eligible(x,domains,main,side,leader_tags)]
    scored=[]
    for old in oldcards:
        if (old.get('super_type') or '').lower()=='signature':continue
        old_score=card_score(old,total_pop,leader_tags)
        candidates=[x for x in pool if x['card_type']==old['card_type'] and
                    abs((x.get('energy_cost') or 0)-(old.get('energy_cost') or 0))<=2 and
                    abs((x.get('power_cost') or 0)-(old.get('power_cost') or 0))<=1 and
                    x['name']!=old['name']]
        scored.extend((card_score(new,total_pop,leader_tags)-old_score,old['name'],new['name']) for new in candidates)
    rng=random.Random(stable_seed(seed,name,'proposal'))
    scored.sort(key=lambda q:(-q[0],q[1],q[2]))
    # Mix top scoring swaps with exploration; never declare these scores win rates.
    strong=scored[:min(80,len(scored))]
    rng.shuffle(strong)
    selected=[]; used=set()
    for _,old,new in strong + scored[:min(250,len(scored))]:
        if (old,new) in used or any(p['remove']==old or p['add']==new for p in selected):continue
        used.add((old,new))
        changed=main.copy();changed[old]-=1;changed[new]+=1
        if changed[old]<=0:del changed[old]
        if sum(changed.values())!=39:raise AssertionError('Mutation changed total')
        # Apply full main + sideboard Unique and copy-limit checks.
        if any(c+side.get(x,0)>(1 if is_unique(byname[x]) else 3) for x,c in changed.items() if x in byname):continue
        selected.append({'remove':old,'add':new,'text':render_deck(original,changed)})
        if len(selected)==n:break
    return selected

def benchmark(exe,deck1,deck2,seed,agent,timeout,env):
    cmd=[str(exe.absolute()),'--deck1',str(deck1.absolute()),'--deck2',str(deck2.absolute()),
         '--agent1',agent,'--agent2',agent,'--game-mode','match','--seed',str(seed),
         '--web','off','--render-html','off']
    start=time.monotonic()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(status='timeout',winner=None,seconds=round(time.monotonic()-start,3))
    hit=re.search(r'Game over:\s*winner\s*=\s*([012])',p.stdout)
    status='complete' if p.returncode==0 and hit and int(hit.group(1)) in (1,2) else 'error'
    return dict(status=status,winner=int(hit.group(1)) if hit else None,
                seconds=round(time.monotonic()-start,3),error=p.stderr[-250:] if status=='error' else '')

def main(args):
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    original=decode()
    sources=make_legal_candidate(original,output/'legal_inputs',output/'legal_source_manifest.json')
    byname=registry(args.registry)
    total_pop=collections.Counter()
    for p in sources.values():
        _,main,_=parse_deck(p);total_pop.update(main)
    legends=sorted(sources)
    if args.legends:
        names=[name for name in legends if any(key(x) in key(name) for x in args.legends)]
        if not names:raise ValueError('No legends matched --legends')
    else:names=legends
    if args.max_legends:names=names[:args.max_legends]
    exe=args.engine.resolve()
    env=os.environ.copy()
    if args.ld_library_path:env['LD_LIBRARY_PATH']=str(args.ld_library_path)
    results=[]
    game_cache={}
    executor=concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)
    start=time.monotonic()
    try:
      for ix,name in enumerate(names):
        source_text,main,side=parse_deck(sources[name])
        baseline_path=sources[name]
        rounds=[]
        for round_ix in range(args.rounds):
          proposed=propose(name,baseline_path,byname,total_pop,args.candidates,
                           args.seed+round_ix*21911)
          candidates=[]
          for pidx,p in enumerate(proposed):
              dest=output/'proposals'/f'{ix:02d}_round{round_ix+1}_{pidx:02d}.txt'
              dest.parent.mkdir(parents=True,exist_ok=True)
              dest.write_text(p['text'],encoding='utf-8')
              candidates.append({**p,'path':dest})
          eligible_top=[n for n in TOP if n in sources and n!=name]
          r=random.Random(stable_seed(args.seed,name,round_ix,'opponents'))
          opponents=r.sample(eligible_top,min(args.opponents,len(eligible_top)))
          def compare(candidate_path, phase, samples, agent_override=None):
              play_agent=agent_override or args.agent
              schedule=[]
              for op in opponents:
                for iteration in range(samples):
                  seat=iteration%2
                  seed=stable_seed(args.seed,name,op,round_ix,phase,iteration)
                  schedule.append((op,seat,seed))
              def single(deck,op,seat,seed):
                  a,b=(deck,sources[op]) if seat==0 else (sources[op],deck)
                  game_key=(file_sha(a),file_sha(b),seed,play_agent)
                  if game_key not in game_cache:
                      game_cache[game_key]=executor.submit(benchmark,exe,a,b,seed,play_agent,args.timeout,env)
                  game=game_cache[game_key].result()
                  return game, int(game['winner']==seat+1) if game['status']=='complete' else None
              for op,seat,seed in schedule:
                  for deck in (baseline_path,candidate_path):
                      a,b=(deck,sources[op]) if seat==0 else (sources[op],deck)
                      game_key=(file_sha(a),file_sha(b),seed,play_agent)
                      if game_key not in game_cache:
                          game_cache[game_key]=executor.submit(benchmark,exe,a,b,seed,play_agent,args.timeout,env)
              baseline=[];challenger=[];errors=[]
              for op,seat,seed in schedule:
                  for deck,out in [(baseline_path,baseline),(candidate_path,challenger)]:
                      game,win=single(deck,op,seat,seed)
                      if win is None:errors.append({'opponent':op,'seed':seed,'status':game['status'],'error':game.get('error','')})
                      else:out.append(win)
              return {'baseline_wins':sum(baseline),'candidate_wins':sum(challenger),
                      'total':len(schedule),'valid':len(baseline)==len(challenger)==len(schedule),
                      'errors':errors}
          # Fast random-agent prefilter is only a screening step. Final acceptance
          # requires independent ISMCTS training and held-out comparisons.
          pretrial=[]
          for cand in candidates:
              screening=compare(cand['path'],'prefilter',args.prefilter_samples,agent_override='random')
              pretrial.append({'remove':cand['remove'],'add':cand['add'],
                               'file':str(cand['path'].relative_to(output)),
                               'prefilter':screening,
                               'delta_prefilter':screening['candidate_wins']-screening['baseline_wins']})
          pretrial.sort(key=lambda x:(-x['delta_prefilter'],x['remove'],x['add']))
          trials=[]
          for screen in [x for x in pretrial if x['prefilter']['valid']][:args.shortlist]:
              train=compare(output/screen['file'],'training',args.samples)
              trials.append({**screen,'train':train,
                             'delta_train':train['candidate_wins']-train['baseline_wins']})
          trials.sort(key=lambda x:(-x['delta_train'],x['remove'],x['add']))
          selected=None;heldout=None
          if trials and trials[0]['train']['valid'] and trials[0]['delta_train']>=args.min_gain:
              best=trials[0]; heldout=compare(output/best['file'],'holdout',args.holdout)
              if heldout['valid'] and heldout['candidate_wins']-heldout['baseline_wins']>=args.min_gain:
                  selected=best
          rounds.append({'round':round_ix+1,'prefilter':pretrial,'trials':trials,'selected':selected,
                         'holdout':heldout,'opponents':opponents})
          print('OPTIMIZE',ix+1,'/',len(names),name,'round',round_ix+1,
                'selected',bool(selected),'best_delta',trials[0]['delta_train'] if trials else None,
                'holdout',((heldout['candidate_wins']-heldout['baseline_wins']) if heldout else None),
                'elapsed',round(time.monotonic()-start,1),flush=True)
          if not selected:break
          baseline_path=output/selected['file']
        destination=output/'selected_decks'/sources[name].name;destination.parent.mkdir(exist_ok=True)
        destination.write_text(baseline_path.read_text(encoding='utf-8'),encoding='utf-8')
        report={'legend':name,'original_sha256':file_sha(sources[name]),
                'effective_sha256':file_sha(destination),'selected':file_sha(sources[name])!=file_sha(destination),
                'selected_swaps':[{'round':r['round'],'remove':r['selected']['remove'],'add':r['selected']['add']}
                                  for r in rounds if r['selected']],
                'rounds':rounds,'agent':args.agent,'samples':args.samples,
                'holdout_samples':args.holdout,
                'rule':'Accept only if training AND independent holdout gain >= threshold; no synthetic wins.'}
        results.append(report)
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    finally: executor.shutdown(wait=True)
    summary={'legends_tested':len(results),'improved':sum(r['selected'] for r in results),
             'failed':len(results)-len(names),'agent':args.agent,'seed':args.seed,
             'simulations':len(game_cache),'seconds':round(time.monotonic()-start,2),
             'note':'Exploratory holdout-gated changes only; not proof of globally optimal decks.'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('OPTIMIZATION_SUMMARY',json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--engine',type=pathlib.Path,default=ROOT/'alpharune/build/riftbound')
    p.add_argument('--registry',type=pathlib.Path,default=ROOT/'radiance/engine_overlay/compiled_registry.json')
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'optimization/results')
    p.add_argument('--agent',default='ismcts:sims=24')
    p.add_argument('--legends',nargs='*',default=[])
    p.add_argument('--max-legends',type=int,default=0)
    p.add_argument('--candidates',type=int,default=3)
    p.add_argument('--shortlist',type=int,default=2)
    p.add_argument('--prefilter-samples',type=int,default=2)
    p.add_argument('--rounds',type=int,default=2)
    p.add_argument('--opponents',type=int,default=4)
    p.add_argument('--samples',type=int,default=2)
    p.add_argument('--holdout',type=int,default=3)
    p.add_argument('--min-gain',type=int,default=2)
    p.add_argument('--workers',type=int,default=6)
    p.add_argument('--timeout',type=int,default=60)
    p.add_argument('--seed',type=int,default=20261121)
    p.add_argument('--ld-library-path',type=pathlib.Path)
    a=p.parse_args()
    if not (1<=a.shortlist<=a.candidates and 1<=a.prefilter_samples<=40 and 1<=a.rounds<=8 and 1<=a.candidates<=30 and 1<=a.opponents<=12 and 1<=a.samples<=50 and 1<=a.holdout<=50 and 1<=a.min_gain and 1<=a.workers<=32):p.error('Invalid search budget')
    main(a)