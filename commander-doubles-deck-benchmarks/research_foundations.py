"""Select attributed registrations from existing authorized TopDeck snapshots.
No new bulk request. Source registrations are observations, not 2HG results.
"""
import collections,datetime,gzip,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent;HERE=ROOT/'commander-doubles-deck-benchmarks'
COMMANDERS={'blue_farm':{"Tymna the Weaver","Kraum, Ludevic's Opus"},'dawnwaker':{'Thrasios, Triton Hero','Bruse Tarl, Boorish Herder'},'najeela':{'Najeela, the Blade-Blossom'},'derevi':{'Derevi, Empyrial Tactician'},'yuriko':{"Yuriko, the Tiger's Shadow"}}
def scan():
 base=ROOT/'data/tournament_snapshots/topdeck';manifest=json.loads((base/'manifest.json').read_text());results=[]
 for tid,record in manifest['events'].items():
  norm=json.loads((base/record['normalized_event']).read_text())
  if not 0<norm.get('start_date_unix',0)<1792454400:continue # 2026-10-20 UTC
  if norm.get('field_size',0)<16:continue
  if not any(p.get('status')=='Completed' for p in norm.get('pods',[])):continue
  raw=json.load(gzip.open(base/record['raw_snapshot'],'rt'))
  for i,r in enumerate(raw.get('standings',[])):
   obj=r.get('deckObj');cmd=set((obj or {}).get('Commanders',{}))
   if not obj or cmd not in COMMANDERS.values():continue
   ar=next(k for k,v in COMMANDERS.items() if v==cmd)
   entry=next((x for x in norm['entries'] if x.get('player_id')==r.get('id')),norm['entries'][i] if i<len(norm['entries']) else {})
   results.append({'archetype':ar,'event_id':tid,'event_name':norm['name'],'event_date':norm['start_date_utc'],'field_size':norm['field_size'],'standing':entry.get('standing'),'registered_player':entry.get('player_name',r.get('name')),'wins':entry.get('wins'),'draws':entry.get('draws'),'losses':entry.get('losses'),'raw_row':r,'normalized_entry':entry,'raw_source':str((base/record['raw_snapshot']).relative_to(ROOT)),'source_sha256':record['content_hash'],'snapshot_date':record['captured_at']})
 (HERE/'batch1/source_candidate_registrations.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
 print('counts',dict(collections.Counter(r['archetype'] for r in results)))
 for ar in COMMANDERS:
  rr=sorted([r for r in results if r['archetype']==ar],key=lambda r:(r['standing'] if r['standing'] is not None else 999,-r['field_size'],r['event_date']))
  for r in rr[:4]:print(json.dumps({k:v for k,v in r.items() if k not in ('raw_row','normalized_entry')},ensure_ascii=False));print('ROW',str(r['raw_row'])[:450])
if __name__=='__main__':scan()
