"""Explicit online refresh. Default recalibration is offline against pinned snapshots."""
import gzip,hashlib,json,pathlib,requests
HERE=pathlib.Path(__file__).resolve().parent
URLS={'rules_landing':'https://magic.wizards.com/en/rules','comprehensive_rules':'https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt','two_hg_format':'https://magic.wizards.com/en/formats/two-headed-giant','banned_list':'https://magic.wizards.com/en/banned-restricted-list','october_bulletin':'https://magic.wizards.com/en/news/announcements/mystery-booster-commander-edition-update-bulletin'}
def refresh():
 d=HERE/'data';d.mkdir(exist_ok=True);s=requests.Session();s.headers.update({'User-Agent':'CommanderDoublesResearch/1.0 (noncommercial local audit)'})
 meta=s.get('https://api.scryfall.com/bulk-data',timeout=60);meta.raise_for_status();(d/'bulk_metadata.json').write_text(json.dumps(meta.json(),indent=2)+'\n')
 record=next(x for x in meta.json()['data'] if x['type']=='oracle_cards');url=record.get('jsonl_download_uri') or record['download_uri'];r=s.get(url,timeout=120);r.raise_for_status()
 raw=r.content
 cards=[json.loads(l) for l in gzip.decompress(raw).decode().splitlines()] if url.endswith('.jsonl.gz') else r.json()
 # Retain current identity/Oracle/rules/legality fields, not images, prices or redundant print metadata.
 fields=['id','oracle_id','name','oracle_text','card_faces','type_line','color_identity','mana_cost','cmc','power','toughness','legalities','layout','set_type','games','digital','released_at','keywords']
 normalized=''.join(json.dumps({k:c[k] for k in fields if k in c},sort_keys=True,ensure_ascii=False)+'\n' for c in cards).encode()
 (d/'oracle_current.jsonl.gz').write_bytes(gzip.compress(normalized,mtime=0));provenance={'as_of':'2026-10-20','oracle_bulk':{'url':url,'updated_at':record['updated_at'],'download_sha256':hashlib.sha256(raw).hexdigest(),'normalized_sha256':hashlib.sha256(normalized).hexdigest(),'records':len(cards)},'official':{}}
 for key,url in URLS.items():
  rr=s.get(url,timeout=60);rr.raise_for_status();body=rr.content
  # pin compressed source snapshots for repeatable citation checks
  (d/(key+'.gz')).write_bytes(gzip.compress(body,mtime=0));provenance['official'][key]={'url':url,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
 (d/'source_snapshot_manifest.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n');print(json.dumps({'oracle_records':len(cards),'official_sources':len(URLS)}))
if __name__=='__main__':refresh()
