#!/usr/bin/env python3
"""Strict crash/error census across GitHub matrix shards: no synthetic scores."""
import argparse,collections,glob,json,pathlib
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--inputs',required=True)
 p.add_argument('--output',type=pathlib.Path,required=True)
 p.add_argument('--shards',type=int,default=64)
 p.add_argument('--series-per-pair',type=int,default=20)
 a=p.parse_args()
 paths=sorted(glob.glob(a.inputs))
 counts=collections.Counter()
 causes=collections.Counter()
 pairs=collections.Counter()
 fails=[]
 seen=set()
 ids=set()
 for path in paths:
  try:
   d=json.load(open(path,encoding='utf8'))
   ids.add(d['shard'])
   for row in d.get('results',[]):
    key=(row['legend_a'],row['legend_b'],row['instance'])
    if key in seen:raise ValueError('duplicate series '+str(key))
    seen.add(key)
    counts[row['status']]+=1
    if row['status']!='complete':
     game=row['games'][-1] if row.get('games') else {}
     causes[(game.get('returncode'),game.get('status'))]+=1
     pairs[(row['legend_a'],row['legend_b'])]+=1
     fails.append({'a':row['legend_a'],'b':row['legend_b'],
       'instance':row['instance'],'seed':game.get('seed'),
       'game_number':game.get('number'),'status':game.get('status'),
       'returncode':game.get('returncode'),
       'stderr_tail':game.get('stderr_tail','')[-750:]})
  except Exception as ex:
   fails.append({'input_path':path,'parse_error':str(ex)})
 expect=1711*a.series_per_pair
 report={'shards_found':len(paths),'distinct_shards':sorted(ids),'shards_expected':a.shards,
  'unique_series':len(seen),'expected_series':expect,
  'series_status':dict(counts),'errors_by_kind':{str(k):v for k,v in causes.items()},
  'affected_matchups':len(pairs),
  'most_affected':[{'a':q[0],'b':q[1],'incomplete':n} for q,n in pairs.most_common(70)],
  'failed_series':fails,
  'strictly_complete':len(paths)==a.shards and len(ids)==a.shards and len(seen)==expect and not fails}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 print('ISMCTS_MATRIX_POSTMORTEM',json.dumps({k:v for k,v in report.items() if k not in ('failed_series','most_affected')}),flush=True)
 for x in fails[:16]:print('FAILED_SERIES',json.dumps(x),flush=True)
if __name__=='__main__':main()
