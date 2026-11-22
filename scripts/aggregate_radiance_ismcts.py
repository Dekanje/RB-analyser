#!/usr/bin/env python3
"""Merge 58-legends Radiance ISMCTS candidate runs; fail on missing shards/decks.

This is a bounded search of compiled Radiance cards, NOT full Radiance
rule implementation. The roster is provisional and preserves source lists.
"""
import argparse
import collections
import csv
import hashlib
import json
import pathlib

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=pathlib.Path,default=pathlib.Path('results/shards'))
    p.add_argument('--output',type=pathlib.Path,default=pathlib.Path('results/radiance_58_ismcts'))
    p.add_argument('--expected-shards',type=int,default=16)
    args=p.parse_args()
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    shards=sorted(args.source.glob('radiance-ismcts-shard-*'))
    if len(shards)!=args.expected_shards:
        raise SystemExit(f'Expected {args.expected_shards} shard archives; found {len(shards)}')
    reports=[]
    deck_paths={}
    failures=[]
    shard_meta=[]
    for i,folder in enumerate(shards):
        ss=folder/'summary.json'
        rs=folder/'shard_results.json'
        if not ss.is_file() or not rs.is_file():
            failures.append(f'Incomplete artifact: {folder}')
            continue
        summary=json.loads(ss.read_text(encoding='utf8'))
        trials=json.loads(rs.read_text(encoding='utf8'))
        if summary['shard'] in [x['shard'] for x in shard_meta]:
            failures.append('Duplicate shard '+str(summary['shard']))
        if summary['shards']!=args.expected_shards or summary['legends']!=summary['legends_completed']:
            failures.append('Incomplete shard '+str(summary['shard']))
        if len(trials)!=summary['legends']:
            failures.append('Mismatch trial rows '+str(summary['shard']))
        shard_meta.append(summary)
        for record in trials:
            legend=record['legend']
            if legend in deck_paths:
                failures.append('Duplicate legend '+legend)
                continue
            # Original deck names do not equal legend names, so detect files by
            # their exact header without depending on slugs.
            decks=list((folder/'selected_decks').glob('*.txt'))
            for d in decks:
                header=next((line[len('Legend:'):].strip() for line in d.read_text().splitlines()
                             if line.startswith('Legend:') and line.strip()!='Legend:'),None)
                if header is None:
                    lines=d.read_text().splitlines()
                    if 'Legend:' in lines:
                        j=lines.index('Legend:')
                        header=lines[j+1].strip() if len(lines)>j+1 else None
                        if header and header.startswith('1 '):
                            header=header[2:]
                if header == legend.split(', ',1)[1] or header==legend:
                    deck_paths[legend]=d
                    break
            if legend not in deck_paths:
                failures.append('Missing selected deck for '+legend)
            reports.append(record)
    if set(x['shard'] for x in shard_meta)!=set(range(args.expected_shards)):
        failures.append('Missing shard index')
    if len(reports)!=58 or len(deck_paths)!=58:
        failures.append(f'Not 58 legends: reports={len(reports)} decks={len(deck_paths)}')
    rows=[]
    for record in sorted(reports,key=lambda x:x['legend']):
        legend=record['legend']
        selected=deck_paths.get(legend)
        if selected and digest(selected)!=record['selected_sha256']:
            failures.append('Content SHA mismatch '+legend)
        for tr in record['trials']:
            if tr['accepted'] and (
                not tr['train']['complete'] or tr['holdout'] is None
                or not tr['holdout']['complete']):
                failures.append('Accepted unverified trial '+legend)
        rows.append({
            'legend':legend,
            'original_sha256':record['original_sha256'],
            'selected_sha256':record['selected_sha256'],
            'changed':record['changed'],
            'radiance_swaps_attempted':record['radiance_swaps_attempted'],
            'change_details':'; '.join(t['from']+' -> '+t['to']+' ('+t['code']+')'
                                       for t in record['trials'] if t['accepted']),
            'engine_game_comparison_complete':all(t['train']['complete'] and
                            (t['holdout'] is None or t['holdout']['complete'])
                            for t in record['trials']),
        })
    csv_path=out/'all_58_radiance_ismcts_comparison.csv'
    with csv_path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['legend'])
        w.writeheader()
        w.writerows(rows)
    roster=out/'selected_decks'
    roster.mkdir(exist_ok=True)
    for _,path in deck_paths.items():
        (roster/path.name).write_bytes(path.read_bytes())
    (out/'full_trials.json').write_text(json.dumps(reports,indent=2,ensure_ascii=False))
    summary={
        'source':'full 167-card Radiance catalog audited; only compiled and engine-supported cards were playtested',
        'radiance_full_set_implemented':False,
        'experiment':'fixed-deck BO3; ISMCTS versus ISMCTS; no sideboarding',
        'shards_received':len(shards),
        'legends_reported':len(reports),
        'decks_collected':len(deck_paths),
        'verified_candidate_improvements':sum(bool(r['changed']) for r in reports),
        'candidate_trials':sum(len(r['trials']) for r in reports),
        'failures':failures,
        'complete':not failures and len(reports)==len(deck_paths)==58
    }
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print('RADIANCE_58_ISMCTS_AGGREGATE',json.dumps(summary),flush=True)
    return 0 if summary['complete'] else 1

if __name__=='__main__':
    raise SystemExit(main())
