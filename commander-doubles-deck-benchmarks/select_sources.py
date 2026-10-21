"""Freeze factual, attributed foundations; no copied full primer prose/images."""
import collections,gzip,hashlib,json,pathlib
from fetch_primers import SOURCES
HERE=pathlib.Path(__file__).resolve().parent
SELECTION={
'A1':[('guardian-games-cedh-monthly-pdx','Eric V - Tap For Hope'),('3-path-to-exile-national-european-qualifier-copy','Tanya Krumm [SNAP]')],
'A2':[('wz-carnival-buban-261017','jumping'),('level-7s-first-of-the-season-1k','Alex Chippas')],
'B1':[('2-rock-2-salt','John Hasara [SALT] '),('2do-clasificatorio-nacional-cedh-stack-surfers','Patricio Allende')],
'B2':[('trigger-on-the-stack-cedh-cedh-for-mox-diamond-volcanic','Biscuit'),('north-stars-monthly-cedh','Dominic Dixon')],
'C1':[('cardart-weekly-71','Nathaniel Crossman'),('tap-that-tundra-eu-championship-qualifier','Julien Vlaminck')],
'C2':[('cedh-nm-2026','Stian Johansen'),('naus-am-rathaus-cedh-tournament-2','Sebbeth')],
}
KEYS={'A1':'blue_farm','A2':'dawnwaker','B1':'najeela','B2':'derevi','C1':'yuriko_tempo','C2':'yuriko_combo'}
def freeze():
 candidates=json.loads((HERE/'batch1/source_candidate_registrations.json').read_text());out=[]
 for head,queries in SELECTION.items():
  for n,(event,player) in enumerate(queries,1):
   matches=[r for r in candidates if r['event_id']==event and r['registered_player']==player];assert len(matches)==1,(head,event,player,len(matches));r=matches[0];row=r['raw_row'];assert row['id']==r['normalized_entry']['player_id'];assert row['name']==r['registered_player']
   counts={zone:{name:int(v.get('count',1)) for name,v in row['deckObj'][src].items()} for zone,src in [('main','Mainboard'),('commanders','Commanders')]}
   out.append({'id':head+'_T'+str(n),'head':head,'source_type':'registered_tournament_deck','url':'https://topdeck.gg/bracket/'+event,'decklist_url':'https://topdeck.gg/bracket/'+event,'author':player,'author_role':'registered pilot; original designer not established','event_name':r['event_name'],'event_id':event,'event_date':r['event_date'],'standing':r['standing'],'field_size':r['field_size'],'observed_record':f"{r['wins']}-{r['losses']}-{r['draws']} wins-losses-draws as stored; not a calculated win rate",'archival_capture':r['snapshot_date'],'retrieval_date':'2026-10-20','local_source':r['raw_source'],'source_sha256':r['source_sha256'],'player_id_locator':row['id'],'deck':counts,'use':'Concrete primary registration, exact kept/cut/point-cost comparison. This result belongs to original ordinary Commander list, not new 2HG adaptation.','trust':'primary archived registration; standings verified in normalized/raw records; not 2HG outcomes'})
 for head,key in KEYS.items():
  p=HERE/'local_research'/(key+'.json.gz');raw=gzip.decompress(p.read_bytes());d=json.loads(raw)
  counts={}
  for zone,src in [('main','mainboard'),('commanders','commanders')]:
   counts[zone]=dict(collections.Counter({v['card']['name']:int(v['quantity']) for v in d['boards'][src]['cards'].values()}))
  out.append({'id':head+'_M1','head':head,'source_type':'published_moxfield_list','url':'https://moxfield.com/decks/'+SOURCES[key],'decklist_url':'https://moxfield.com/decks/'+SOURCES[key],'api_url':'https://api2.moxfield.com/v3/decks/all/'+SOURCES[key],'author':'; '.join(a['userName'] for a in d.get('authors',[])) or d['createdByUser']['userName'],'author_role':'Moxfield-listed author(s)','title':d['name'],'created_at':d['createdAtUtc'],'updated_at':d['lastUpdatedAtUtc'],'retrieval_date':'2026-10-20','source_sha256':hashlib.sha256(raw).hexdigest(),'deck':counts,'use':'Factual decklist and short description inspected; full primer prose not retrieved by deck endpoint. Title/old dates/outdated warning retained.','trust':'primary public list; no tournament result attached without an independent registration match','primer_prose_access':'HTML loading only; public v3 deck endpoint yields list/metadata; tested primer endpoint404. No full primer prose claimed.'})
 p=HERE/'batch1/research/foundations.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print([(r['id'],r['author'],sum(sum(x.values()) for x in r['deck'].values())) for r in out])
if __name__=='__main__':freeze()
