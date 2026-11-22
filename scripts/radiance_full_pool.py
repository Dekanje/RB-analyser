#!/usr/bin/env python3
"""Audit the full printed Radiance pool against 58 legal baseline decks.

Catalog data is a SHA-pinned community mirror of Riot's public card gallery.
Output candidate substitutions are SEARCH PROPOSALS, not optimized or verified wins.
Never simulate an uncompiled card or claim text-only imports implement its abilities.
"""
import argparse,collections,csv,hashlib,json,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_actual_games import decode
from legal_candidate import make_legal_candidate
from optimize_58 import parse_deck,render_deck,effective_domains,key,BAN_KEYS,card_score

SOURCE_COMMIT='8a10812968506363a373f36a8bb7cf4d94d02694'
SOURCE_URL='https://github.com/Dystorted888/riftbound-card-data/tree/'+SOURCE_COMMIT

def official_catalog(path):
    obj=json.loads(path.read_text(encoding='utf-8'))
    assert obj.get('source',{}).get('name')=='Riot public card gallery'
    numbered={}
    for c in obj['cards']:
        m=re.fullmatch(r'RAD-(\d{3})/167',c.get('public_code',''))
        if not m or int(m.group(1))>167:continue
        if any(c.get('printing',{}).get(n) for n in ('alternate_art','signature','overnumbered')):continue
        n=int(m.group(1))
        if n in numbered:
            raise RuntimeError(f'Duplicate base Radiance collector number {n}')
        numbered[n]=c
    missing=set(range(1,168))-set(numbered)
    if missing:raise RuntimeError('Incomplete Radiance catalog: '+str(sorted(missing)))
    if len(numbered)!=167:raise RuntimeError('Non-167 full Radiance numbered catalog')
    return numbered

def reg_cards(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    assert len(data['cards'])>=988
    byname={}
    for card in data['cards']:
        # Prefer the new Radiance definition where a reprint name is duplicated.
        name=key(card['name'])
        if name not in byname or card.get('set')=='RAD':byname[name]=card
    return data,byname

def ctype(card):
    return (card.get('type') or '').lower()

def converted(card, card_type):
    energy=card.get('attributes',{}).get('energy')
    power=card.get('attributes',{}).get('power')
    # The community gallery uses the symbol string for some card costs.
    return {'name':card['name'],'card_type':card_type,'energy_cost':energy if isinstance(energy,int) else 0,
            'power_cost':power if isinstance(power,int) else 0,
            'might':card.get('attributes',{}).get('might') or 0,
            'ability_text':card.get('text',{}).get('plain') or '',
            'tags':card.get('tags') or [],'features':{},
            'domains':[x.lower() for x in card.get('domains') or []],
            'super_type':(card.get('supertype') or '').lower()}

def unique(c):
    return '[unique]' in (c.get('text',{}).get('plain') or '').lower()

def to_write(path,rows,columns):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as out:
        w=csv.DictWriter(out,fieldnames=columns);w.writeheader();w.writerows(rows)

def main(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    all_cards=official_catalog(args.gallery)
    registry,byname=reg_cards(args.registry)
    # Keep the 54 original lists + four separately disclosed legality corrections.
    baseline=make_legal_candidate(decode(),out/'baselines',out/'baseline_manifest.json')
    if len(baseline)!=58:raise RuntimeError('Expected 58 baseline decks')
    usage=collections.Counter()
    for path in baseline.values():
        _,main,_=parse_deck(path);usage.update(main)
    rad=[]
    for number,c in sorted(all_cards.items()):
        rec=byname.get(key(c['name']))
        compiled=bool(rec and rec.get('card_type') in ('unit','gear','spell','legend','battlefield','rune'))
        # A card being in compiled registry does not certify its implemented rule effects.
        card_type=ctype(c) or (rec.get('card_type') if rec else '')
        rad.append({'number':number,'card':c,'registry':rec,
                    'type':card_type,'compiled_name_match':compiled})
    unknown=[c['card']['public_code'] for c in rad if not c['type']]
    rows=[];summary=[]
    for legend,path in sorted(baseline.items()):
        original,main,side=parse_deck(path)
        domains=effective_domains(legend, {c['name']:c for c in registry['cards']})
        domain_names={str(d).lower() for d in domains}
        possibilities=[]
        for item in rad:
            c=item['card'];t=item['type']
            if t not in ('unit','gear','spell'):continue
            if key(c['name']) in BAN_KEYS:continue
            if not set(x.lower() for x in c.get('domains') or []).issubset(domain_names):continue
            if (c.get('supertype') or '').lower() in ('signature','champion','token'):continue
            if c['name'] in main or c['name'] in side:
                limit=1 if unique(c) else 3
                if main[c['name']]+side[c['name']]>=limit:continue
            record=converted(c,t)
            for old_name,count in main.items():
                old=byname.get(key(old_name))
                if not old or old.get('card_type')!=t:continue
                if (old.get('super_type') or '').lower() in ('signature','champion'):continue
                old_power=old.get('power_cost') or 0
                if abs((record['energy_cost'] or 0)-(old.get('energy_cost') or 0))>2:continue
                if abs((record['power_cost'] or 0)-old_power)>1:continue
                # No mechanically unsupported three-plus-copy or Unique replacements.
                if main[c['name']]+side[c['name']]+1 > (1 if unique(c) else 3):continue
                gain=round(card_score(record,usage,set())-card_score(old,usage,set()),3)
                possibilities.append((gain,old_name,item))
        possibilities.sort(key=lambda x:(-x[0],x[1],x[2]['card']['public_code']))
        # At most one proposal per incoming RAD card; multiple different proposals retained.
        selected=[];seen=set()
        for gain,old,item in possibilities:
            c=item['card']
            if c['name'] in seen:continue
            seen.add(c['name'])
            selected.append({'legend':legend,'remove':old,'add':c['name'],
                             'add_code':c['public_code'],'add_domains':','.join(c.get('domains') or []),
                             'add_type':item['type'],
                             'compiled_name_match':item['compiled_name_match'],
                             'score_difference_heuristic':gain,
                             'status':'ENGINE_CANDIDATE_UNTESTED' if item['compiled_name_match'] else 'UNIMPLEMENTED_NO_SIMULATION'})
            if len(selected)>=args.candidates:break
        playable=0;unimplemented=0
        for s in selected:
            row={**s,'baseline_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            rows.append(row)
            if s['compiled_name_match']:
                playable+=1
            else:unimplemented+=1
        summary.append({'legend':legend,'domain_identity':','.join(sorted(domain_names)),
                        'radiance_proposals':len(selected),'compiled_proposals':playable,
                        'unimplemented_proposals':unimplemented})
    cols=['legend','remove','add','add_code','add_domains','add_type','compiled_name_match',
          'score_difference_heuristic','status','baseline_sha256']
    to_write(out/'all_58_radiance_proposals.csv',rows,cols)
    to_write(out/'legend_coverage.csv',summary,list(summary[0]))
    defined=[x for x in rad if x['compiled_name_match']]
    report={'mode':'RADIANCE_FULL_PRINTED_POOL_AUDIT_NOT_OPTIMIZED_DECKS',
            'source_url':SOURCE_URL,'source_gallery_updated_at':json.loads(args.gallery.read_text()).get('fetched_at'),
            'radiance_numbered_cards':len(rad),'compiled_radiance_name_matches':len(defined),
            'uncompiled_radiance_cards':len(rad)-len(defined),
            'unknown_types':unknown,'legends':len(baseline),
            'total_unverified_proposals':len(rows),
            'compiled_proposals':sum(x['compiled_proposals'] for x in summary),
            'no_improvement_claim':True,
            'rules_note':'Name-compatible engine cards are not independently certified; unsupported cards must not be simulated.'}
    (out/'coverage_report.json').write_text(json.dumps(report,indent=2))
    print('RADIANCE_FULL_POOL_AUDIT',json.dumps(report),flush=True)
    for row in summary:
        print('LEGEND_RAD_COVERAGE',row['legend'],row['radiance_proposals'],row['compiled_proposals'],flush=True)
    if not all(x['radiance_proposals']>0 for x in summary):
        print('WARNING: Some legal decks have zero RAD candidates at this cost-matched search depth.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--gallery',type=pathlib.Path,required=True)
    p.add_argument('--registry',type=pathlib.Path,required=True)
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'results/full_radiance_pool')
    p.add_argument('--candidates',type=int,default=30)
    a=p.parse_args()
    if not 1<=a.candidates<=100:p.error('--candidates 1-100')
    main(a)
