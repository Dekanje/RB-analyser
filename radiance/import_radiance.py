#!/usr/bin/env python3
"""Audit Riot-gallery Radiance card records against a pinned AlphaRune engine.

This is a catalog/coverage pipeline, NOT a card-behavior implementation.
Never reclassify a printed card as implemented because its art, name, or
metadata exists: compiled registration and mechanical certification differ.
"""
import argparse
import csv
import hashlib
import json
import pathlib
import re
from collections import Counter, defaultdict

SOURCE_COMMIT = '8a10812968506363a373f36a8bb7cf4d94d02694'
ENGINE_COMMIT = 'ec90f0fed002aed374d06249fa95e83e3cfbd386'
NUMBERED_COUNT = 167


def normalized(card):
    public = str(card.get('public_code') or '').strip()
    set_value = card.get('set') or {}
    if isinstance(set_value, dict):
        set_id = str(set_value.get('id') or set_value.get('code') or '')
        set_name = str(set_value.get('name') or '')
    else:
        set_id = str(set_value)
        set_name = ''
    if not (public.upper().startswith('RAD-') or set_id.upper() == 'RAD' or set_name.lower() == 'radiance'):
        return None
    printing = card.get('printing') or {}
    attrs = card.get('attributes') or {}
    card_text = card.get('text') or {}
    if not isinstance(card_text, dict): card_text = {'plain': str(card_text)}
    flat_text = str(card_text.get('plain') or card_text.get('text') or '')
    name = str(card.get('name') or '').strip()
    subtitle = str(card.get('subtitle') or '').strip()
    display_name = str(card.get('display_name') or '').strip() or (name + ', ' + subtitle if subtitle else name)
    card_type = str(card.get('type') or '').lower().strip()
    gameplay_fingerprint = hashlib.sha256(json.dumps({
        'display_name': display_name.casefold(),
        'type': card_type,
        'supertype': str(card.get('supertype') or ''),
        'domains': sorted(str(x).lower() for x in (card.get('domains') or [])),
        'energy': attrs.get('energy'), 'power': attrs.get('power'), 'might': attrs.get('might'),
        'rules_text': flat_text.strip(),
    }, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    m = re.fullmatch(r'RAD-(\d+)(?:/167)?', public, re.I)
    base_number = int(m.group(1)) if m and 1 <= int(m.group(1)) <= NUMBERED_COUNT else None
    return {
        'gallery_id': str(card.get('gallery_id') or card.get('id') or ''),
        'public_code': public,
        'name': name,
        'subtitle': subtitle,
        'display_name': display_name,
        'type': card_type,
        'supertype': str(card.get('supertype') or ''),
        'domains': card.get('domains') or [],
        'rarity': str(card.get('rarity') or ''),
        'energy': attrs.get('energy'),
        'power': attrs.get('power'),
        'might': attrs.get('might'),
        'alternate_art': bool(printing.get('alternate_art')),
        'signature': bool(printing.get('signature')),
        'overnumbered': bool(printing.get('overnumbered')),
        'base_number': base_number,
        'rules_text_sha256': hashlib.sha256(flat_text.encode()).hexdigest(),
        'rules_text_length': len(flat_text),
        'gameplay_fingerprint': gameplay_fingerprint,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cards-json', type=pathlib.Path, required=True)
    p.add_argument('--registry-json', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--require-complete-numbered', action='store_true')
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = json.loads(args.cards_json.read_text(encoding='utf-8'))
    engine = json.loads(args.registry_json.read_text(encoding='utf-8'))
    compiled = engine['cards'] if isinstance(engine, dict) else engine
    if not isinstance(compiled, list) or len(compiled) < 900:
        raise SystemExit('Invalid compiled engine registry')
    records = [r for c in source['cards'] if (r := normalized(c)) is not None]
    if not records:
        raise SystemExit('No Radiance cards found in supplied Riot gallery snapshot')
    # Ignore alternate art / overnumbered for unique-gameplay counts, but
    # retain those printings as first-class IDs in the full catalog.
    groups = defaultdict(list)
    for x in records: groups[x['gameplay_fingerprint']].append(x)
    numbered = {r['base_number'] for r in records if r['base_number'] is not None}
    missing_numbered = sorted(set(range(1, NUMBERED_COUNT + 1)) - numbered)
    ids = [r['gallery_id'].casefold() for r in records if r['gallery_id']]
    if len(ids) != len(set(ids)): raise SystemExit('Duplicate Riot gallery IDs')
    if args.require_complete_numbered and missing_numbered:
        raise SystemExit(f'Incomplete Radiance base numbering: {missing_numbered}')
    bycode = defaultdict(list)
    byname = defaultdict(list)
    for c in compiled:
        bycode[str(c.get('public_code') or '').upper()].append(c)
        byname[str(c.get('name') or '').casefold()].append(c)
    for r in records:
        exact = bycode.get(r['public_code'].upper(), [])
        same_name = byname.get(r['display_name'].casefold(), [])
        if not same_name:
            same_name = byname.get(r['name'].casefold(), [])
        if not same_name and r['subtitle']:
            same_name = byname.get(r['subtitle'].casefold(), [])
        # A title match is NOT proof that effects were implemented correctly.
        if exact:
            status = 'EXACT_PRINTING_REGISTERED_EFFECT_UNVERIFIED'
        elif same_name:
            status = 'POTENTIAL_REPRINT_EFFECT_UNVERIFIED'
        else:
            status = 'MISSING_COMPILED_CARD_IMPLEMENTATION'
        r['engine_registry_status'] = status
        r['compiled_candidate_ids'] = [c.get('card_id') for c in (exact or same_name)]
        r['mechanics_verified'] = False
    output = args.output
    (output/'radiance_printings.json').write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    fields = ['public_code','gallery_id','display_name','type','rarity','base_number','rules_text_length','engine_registry_status','mechanics_verified']
    with (output/'radiance_coverage.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(records)
    groups_out = []
    for fingerprint, forms in groups.items():
        primary = min(forms, key=lambda x:(x['alternate_art'] or x['signature'] or x['overnumbered'], x['public_code']))
        groups_out.append({
            'name': primary['display_name'],
            'printings': len(forms),
            'codes': [x['public_code'] for x in forms],
            'gameplay_fingerprint': fingerprint,
            'mechanics_verified': False,
            'status': primary['engine_registry_status'],
        })
    groups_out.sort(key=lambda x:x['name'])
    (output/'unique_gameplay_cards.json').write_text(json.dumps(groups_out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    counts = Counter(r['engine_registry_status'] for r in records)
    legends = sorted(set(r['display_name'] for r in records if 'legend' in r['type']))
    summary = {
        'radiance_source':'Riot official public card gallery, normalized by Dystorted888/riftbound-card-data',
        'source_snapshot_commit':SOURCE_COMMIT,
        'source_snapshot_date':source.get('fetched_at'),
        'engine_commit':ENGINE_COMMIT,
        'numbered_cards_expected':NUMBERED_COUNT,
        'numbered_cards_seen':len(numbered),
        'missing_numbered':missing_numbered,
        'printings_in_source':len(records),
        'unique_gameplay_fingerprints':len(groups),
        'legends_count':len(legends),
        'legends':legends,
        'engine_registry_classification':dict(counts),
        'mechanics_certified':0,
        'all_radiance_cards_supported':False,
        'warning':'Catalog import is not card gameplay implementation. No win rate may be reported for cards with unverified effects.',
    }
    (output/'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('RADIANCE_CATALOG '+json.dumps(summary, ensure_ascii=False), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())