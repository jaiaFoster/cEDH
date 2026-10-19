"""Acquire immutable research snapshots; cached files are never silently refreshed."""
from pathlib import Path
import requests, json, gzip, hashlib, subprocess, datetime, time
from bs4 import BeautifulSoup
ROOT=Path(__file__).parent
RAW=ROOT/'data/raw'; RAW.mkdir(parents=True,exist_ok=True)
SOURCES={
 'kamigawa_erratum':'https://magic.wizards.com/en/news/feature/kamigawa-neon-dynasty-commander-decklists-2022-02-07',
 'foundations':'https://magic.wizards.com/en/news/announcements/foundations-commander-decklists',
 'october_bans':'https://www.magic.wizards.com/en/news/announcements/banned-and-restricted-october-12-2026',
 'bulk_index':'https://api.scryfall.com/bulk-data',
 'mtg_decklist':'https://mtgjson.com/api/v5/DeckList.json',
 'mtg_all_decks':'https://mtgjson.com/downloads/all-decks/',
 'brackets_2025':'https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-october-21-2025',
 'brackets_2026':'https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-february-9-2026',
 'banned':'https://magic.wizards.com/en/banned-restricted-list',
 'two_headed':'https://magic.wizards.com/en/formats/two-headed-giant',
 'rules':'https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt',
 'edhrec_validation':'https://cloudflare.edhrec.com/articles/the-best-commander-precons-of-2024',
 'reddit_validation':'https://www.reddit.com/r/EDH/comments/1eetahl/redhs_best_precon_commanders_of_all_time/',
 'cedh_context':'https://www.reddit.com/r/CompetitiveEDH/comments/1fj7zkd/',
 'spellbook':'https://commanderspellbook.com/about/',
 'topdeck':'https://topdeck.gg/docs/tournaments-v2',
 'moxfield_example':'https://moxfield.com/decks/0GMkJIsGM0qNsSesov9A1g',
}
def fetch(key,url,ext):
 p=RAW/(key+ext)
 if not p.exists():
  r=requests.get(url,headers={'User-Agent':'CommanderLeagueResearch/0.1 (local reproducible study)','Accept':'application/json,text/html,text/plain,*/*'},timeout=120)
  r.raise_for_status(); p.write_bytes(r.content)
 return p
def main():
 if not (ROOT/'data/taw/decks_v2.json').exists():subprocess.run(['git','clone','https://github.com/taw/magic-preconstructed-decks-data.git',str(ROOT/'data/taw')],check=True)
 commit_path=ROOT/'data/taw_commit.txt'
 if (ROOT/'data/taw/.git').exists():commit_path.write_text(subprocess.check_output(['git','-C',str(ROOT/'data/taw'),'rev-parse','HEAD'],text=True).strip())
 commit=commit_path.read_text().strip() if commit_path.exists() else 'unknown_snapshot_commit'
 manifest=[]
 for key,url in SOURCES.items():
  ext='.json' if key in ['bulk_index','mtg_decklist'] else '.txt' if key=='rules' else '.html'
  try:
   p=fetch(key,url,ext)
   status='downloaded'
   if ext=='.html':
    content=BeautifulSoup(p.read_text(),'html.parser').get_text('\n',strip=True)
    (RAW/(key+'.txt')).write_text(content)
    if len(content)<100:status='access_challenge_or_empty'
    elif key=='moxfield_example':status='application_shell_no_deck'
   manifest.append(dict(key=key,url=url,retrieved_at=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status=status))
  except Exception as e:manifest.append(dict(key=key,url=url,status='unavailable',error=str(e)))
 b=json.loads((RAW/'bulk_index.json').read_text());entry=next(x for x in b['data'] if x['type']=='oracle_cards')
 url=entry.get('download_uri') or entry['jsonl_download_uri'];ext='.jsonl.gz' if '.jsonl.gz' in url else '.json'
 p=fetch('oracle_cards',url,ext)
 manifest.append(dict(key='oracle_cards',url=url,updated_at=entry['updated_at'],retrieved_at=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='downloaded'))
 previous=json.loads((RAW/'source_manifest.json').read_text()) if (RAW/'source_manifest.json').exists() else []
 prior_taw=next((s for s in previous if s['key']=='taw'),{})
 manifest.append(dict(key='taw',url='https://github.com/taw/magic-preconstructed-decks-data',commit=commit,path='data/taw/decks_v2.json',sha256=hashlib.sha256((ROOT/'data/taw/decks_v2.json').read_bytes()).hexdigest(),retrieved_at=prior_taw.get('retrieved_at',datetime.datetime.now(datetime.timezone.utc).isoformat())))
 (RAW/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps([{k:v for k,v in m.items() if k in ['key','status','error']} for m in manifest],indent=2))
if __name__=='__main__':main()
