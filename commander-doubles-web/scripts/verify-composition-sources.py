"""Fetch primary rules for verification; persist hashes, never a rulebook mirror."""
import pathlib,json,re,hashlib,urllib.request,urllib.parse
root=pathlib.Path(__file__).resolve().parents[1];out=root/'research/compositions'
def get(u):
 u=urllib.parse.quote(u,safe=':/?%=&')
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CommanderDoubles-CompositionResearch/1.0 (+https://github.com/jaiaFoster/cEDH)','Accept':'*/*'}),timeout=60) as r:
  b=r.read();sources.append({'url':u,'status':r.status,'sha256':hashlib.sha256(b).hexdigest()});return b
sources=[]
landing=get('https://magic.wizards.com/en/rules').decode();url=re.search(r'href="(https:[^"]+MagicCompRules[^"]+\.txt)"',landing)[1]
latest_url=url
url='https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt'
body=get(url).decode();preview=get(latest_url).decode() if latest_url!=url else body
get('https://magic.wizards.com/en/formats/two-headed-giant')
latest_edition=re.search(r'effective as of ([^.]+)',preview)[1]
if latest_edition not in ['September 25, 2026','November 6, 2026']:raise ValueError('Unexpected rules edition; review before publication')
entries=json.loads((root/'data/compositions/entries.json').read_text());refs=set(r for p in entries for r in p['rule_references']);found={}
for m in re.finditer(r'^(\d{3}\.\d+[a-z]?)[.]? ([^\r\n]+)(?:\r?\n(?!\d{3}\.)([^\r\n]+))?',body,re.M):
 if m[1] in refs:found[m[1]]={'sha256':hashlib.sha256(m[0].encode()).hexdigest()}
assert set(found)==refs,sorted(refs-set(found))
old=json.loads((root/'research/rulings/rule-index.json').read_text())
for k,v in found.items():assert old['rules'][k]['sha256']==v['sha256'],k
preview_refs={m[1]:hashlib.sha256(' '.join(m[0].split()).encode()).hexdigest() for m in re.finditer(r'^(\d{3}\.\d+[a-z]?)[.]? ([^\r\n]+)(?:\r?\n(?!\d{3}\.)([^\r\n]+))?',preview,re.M) if m[1] in refs}
current_normalized={m[1]:hashlib.sha256(' '.join(m[0].split()).encode()).hexdigest() for m in re.finditer(r'^(\d{3}\.\d+[a-z]?)[.]? ([^\r\n]+)(?:\r?\n(?!\d{3}\.)([^\r\n]+))?',body,re.M) if m[1] in refs}
changed=[r for r in refs if preview_refs.get(r)!=current_normalized.get(r)]
if set(changed)-{'109.5','113.8'}:raise ValueError('Unreviewed referenced-rule changes: '+str(changed))
for ref in changed:
 pattern=r'^'+re.escape(ref)+r'\.? .*?(?=^\d{3}\.\d|\Z)'
 a=' '.join(re.search(pattern,body,re.M|re.S)[0].split())
 b=' '.join(re.search(pattern,preview,re.M|re.S)[0].split()).replace('603.7d–g','603.7d–f')
 if a!=b:raise ValueError('Operative controller wording changed: '+ref)
report={'latest_posted_edition':latest_edition,'latest_posted_url':urllib.parse.quote(latest_url,safe=':/?%=&'),'client_date':'2026-11-05','latest_posted_cited_rules_unchanged':not changed,'reviewed_cross_reference_changes':changed,'latest_posted_operative_interpretations_unchanged':True,'manual_change_analysis':'109.5 and 113.8 extend a delayed-trigger cross-reference from 603.7d–f to 603.7d–g; operative you/controller wording is unchanged. New 603.7g handles delayed triggers created by static action permissions; it does not change these reviewed configurations.','comparison':'Whitespace-normalized text; raw source hashes differ because document line endings differ','latest_posted_normalized_references':preview_refs,'verified_on':'2026-11-05','rules_edition':'September 25, 2026','sources':sources,'rule_references':found,'full_rules_republished':False,'scryfall_bulk_source':'bulk-source.json','scope':'Card text is checked against the hash-pinned full Oracle bulk; exact controller reasoning is editorial review, not proven by regex.'}
(out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'official_sources':len(sources),'rules':len(found),'current_rule_url':url}))
