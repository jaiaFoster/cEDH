"""Research-only bulk acquisition; never changes the league scoring catalog."""
import urllib.request,json,pathlib,hashlib,datetime,sys,gzip
root=pathlib.Path(__file__).resolve().parents[1]; dest=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/commander-compositions-oracle.jsonl.gz')
headers={'User-Agent':'CommanderDoubles-CompositionResearch/1.0 (+https://github.com/jaiaFoster/cEDH)','Accept':'application/json'}
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers=headers),timeout=120) as r:return r.read()
meta=json.loads(get('https://api.scryfall.com/bulk-data/oracle-cards'))
previous=root/'research/compositions/bulk-source.json'
prior=json.loads(previous.read_text()) if previous.exists() else {}
if not dest.exists() or prior.get('bulk',{}).get('updated_at')!=meta['updated_at'] or hashlib.sha256(dest.read_bytes()).hexdigest()!=prior.get('sha256'):
 dest.write_bytes(get(meta.get('jsonl_download_uri') or meta['download_uri']))
b=dest.read_bytes(); raw=gzip.decompress(b) if b[:2]==b"\x1f\x8b" else b
cards=[json.loads(line) for line in raw.splitlines() if line.strip()] if meta.get("jsonl_download_uri") else json.loads(raw)
report={'retrieved_on':'2026-11-05','bulk':meta,'sha256':hashlib.sha256(b).hexdigest(),'cards':len(cards),'source':'https://api.scryfall.com/bulk-data/oracle-cards','local_path_not_committed':True}
(root/'research/compositions/bulk-source.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cards':len(cards),'updated_at':meta['updated_at'],'sha256':report['sha256']}))
