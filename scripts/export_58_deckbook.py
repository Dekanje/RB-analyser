#!/usr/bin/env python3
"""Export the 58 SHA-preserved post-ban legal baseline decklists and possible set matches."""
import argparse,csv,hashlib,json,pathlib,re,sys,collections,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_actual_games import decode
from legal_candidate import make_legal_candidate
from optimize_58 import parse_deck,key,BAN_KEYS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_csv(p,rows):
 with p.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sections(p):
 section=None
 for raw in p.read_text(encoding='utf8').splitlines():
  s=raw.strip()
  if s.endswith(':') and s[:-1] in ('Legend','Champion','MainDeck','Battlefields','Runes','Sideboard'):
   section=s[:-1];continue
  m=re.fullmatch(r'(\d+)\s+(.+)',s)
  if m:
   if not section:raise ValueError('Unknown section in '+p.name)
   yield section,int(m.group(1)),m.group(2)
def main(args):
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 decks=make_legal_candidate(decode(),out/'decks',out/'manifest.json')
 assert len(decks)==58
 reg=collections.defaultdict(set)
 if args.registry:
  for c in json.loads(args.registry.read_text(encoding='utf8'))['cards']:
   n=key(c.get('name',''))
   if n:reg[n].add((c.get('set_code') or c.get('set') or '',c.get('public_code') or c.get('def_id') or ''))
 roster=[];details=[];md=['# Riftbound — 58 evidenced legal baseline decks','','Global Standard bans effective 23 November 2026 are applied in the source audit.','This is NOT proof of global competitive optimality: Radiance effects and BO3 sideboarding are incomplete.','Card set codes are possible engine name matches, not verified original printings.','']
 for legend,p in sorted(decks.items()):
  _,main_cards,side=parse_deck(p)
  assert sum(main_cards.values())==39
  src=ROOT/'decks'/p.name;changed=sha(src)!=sha(p)
  roster.append(dict(legend=legend,file=p.name,main_cards=39,sideboard_cards=sum(side.values()),
    source_sha256=sha(src),selected_sha256=sha(p),legality_correction=changed,
    selection='LEGAL_BASELINE_NO_BLIND_VERIFIED_RADIANCE_UPGRADE'))
  entries=list(sections(p))
  if any(key(card) in BAN_KEYS for _,_,card in entries):
   raise AssertionError('Banned card in '+legend)
  md+=['## '+legend,'','Legality correction: '+('yes' if changed else 'no'),'Selected SHA-256: '+sha(p),'','~~~text',
       p.read_text(encoding='utf8').strip(),'~~~','']
  for sec,count,name in entries:
   codes=sorted(reg.get(key(name),set()))
   sets='|'.join(sorted(set(s for s,_ in codes if s))) or 'UNRESOLVED'
   printings='|'.join(sorted(set(c for _,c in codes if c))) or 'UNRESOLVED'
   details.append(dict(legend=legend,section=sec,quantity=count,card=name,
      possible_compiled_sets=sets,possible_compiled_codes=printings,
      attribution='NAME_MATCH_NOT_VERIFIED_PRINTING' if codes else 'UNRESOLVED'))
 assert sum(r['legality_correction'] for r in roster)==4
 write_csv(out/'roster_58.csv',roster)
 write_csv(out/'all_card_lines_possible_sets.csv',details)
 (out/'all_58_decklists.md').write_text('\n'.join(md),encoding='utf8')
 with zipfile.ZipFile(out/'ALL_58_LEGAL_DECKS.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in sorted((out/'decks').glob('*.txt')):z.write(p,'decks/'+p.name)
 result=dict(legends=len(roster),card_lines=len(details),legal_corrections=4,
     verified_new_radiance_swaps=0,source_immutable=True,
     no_global_optimum_claim=True,unresolved_card_lines=sum(x['attribution']=='UNRESOLVED' for x in details))
 (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print('ALL_58_DECKBOOK',json.dumps(result),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser()
 ap.add_argument('--output',type=pathlib.Path,default=ROOT/'results/deckbook_58')
 ap.add_argument('--registry',type=pathlib.Path)
 main(ap.parse_args())
