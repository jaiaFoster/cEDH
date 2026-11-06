"""Read the permitted bulk locally; retain identifiers/links only, not combo prose."""
import gzip,json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1];p=pathlib.Path('/tmp/commander-compositions-spellbook.json.gz');raw=p.read_bytes();data=json.loads(gzip.decompress(raw))
wanted={'zirda-basalt':{'Zirda, the Dawnwaker','Basalt Monolith'},'kraj-kiki-pestermite':{'Experiment Kraj','Kiki-Jiki, Mirror Breaker','Pestermite'},'lavinia-pool':{'Lavinia, Azorius Renegade','Knowledge Pool'},'najeela-derevi':{'Najeela, the Blade-Blossom','Derevi, Empyrial Tactician'},'donated-coil':{'Zedruu the Greathearted','Immortal Coil','Rest in Peace'}}
found={}
for v in data['variants']:
 names={u['card']['name'] for u in v['uses']}
 for label,ws in wanted.items():
  if names==ws:found.setdefault(label,{'id':v['id'],'url':'https://commanderspellbook.com/combo/'+v['id']+'/','cards':sorted(names),'use':'Ordinary combo membership only; split-controller functionality independently reviewed. No descriptions imported.'})
report={'retrieved_on':'2026-11-05','source_url':'https://json.commanderspellbook.com/variants.json.gz','sha256':hashlib.sha256(raw).hexdigest(),'metadata':{k:data[k] for k in ['timestamp','version']},'variants_examined':len(data['variants']),'requested':{k:sorted(v) for k,v in wanted.items()},'matches':found,'unmatched':[k for k in wanted if k not in found],'license_scope':'Backend software licensing does not automatically establish a blanket data license. Only linked factual IDs/card membership retained with attribution; no upstream combo instructions or full database redistributed.','ongoing_dependency':False}
(root/'research/compositions/spellbook-selected.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'examined':report['variants_examined'],'matches':list(found),'unmatched':report['unmatched']}))
