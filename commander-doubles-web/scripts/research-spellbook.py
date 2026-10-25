"""Optional research refresh: pip install ijson. Never seeds third-party descriptions."""
import urllib.request,gzip,hashlib,json,datetime,pathlib
import ijson
url='https://json.commanderspellbook.com/variants.json.gz'
p=pathlib.Path('/tmp/commander-rulings-spellbook.json.gz');h=hashlib.sha256();n=0
req=urllib.request.Request(url,headers={'User-Agent':'CommanderDoubles-RulingsResearch/1.0','Accept-Encoding':'identity'})
with urllib.request.urlopen(req,timeout=90) as r,p.open('wb') as f:
 while b:=r.read(1024*1024):f.write(b);h.update(b);n+=len(b)
with gzip.open(p,'rb') as f:
 parser=ijson.parse(f);meta={}
 for prefix,event,value in parser:
  if prefix in ('timestamp','version') and event in ('string','number'):meta[prefix]=str(value)
  if prefix=='variants' and event=='start_array':break
pairs=[{'Aluren','Acererak the Archlich'},{'Rest in Peace','Helm of Obedience'},{'Mindcrank','Bloodchief Ascension'},{'Sanguine Bond','Exquisite Blood'},{'Najeela, the Blade-Blossom','Derevi, Empyrial Tactician'}];found={};count=0
with gzip.open(p,'rb') as f:
 for v in ijson.items(f,'variants.item'):
  count+=1; names={u['card']['name'] for u in v.get('uses',[]) if isinstance(u.get('card'),dict)}
  for pair in pairs:
   key=' + '.join(sorted(pair))
   if pair<=names and key not in found:found[key]={'id':v['id'],'cards':sorted(names),'url':'https://commanderspellbook.com/combo/'+v['id']+'/','description_imported':False,'note':'Ordinary-controller combo membership only; cross-team functionality independently assessed.'}
result={'source_url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':h.hexdigest(),'bytes':n,'metadata':meta,'variants_examined':count,'requested_pairs':len(pairs),'matches':found,'terms':'Bulk advised by official API docs. Backend MIT does not establish blanket data license. Store only minimal identifiers and attribution; no variant narratives redistributed.'}
pathlib.Path('research/rulings/spellbook_bulk_provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
