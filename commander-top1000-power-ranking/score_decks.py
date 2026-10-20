"""Offline candidate league backend. Reuses the v1 Moxfield parser; no network calls."""
import argparse,gzip,json,pathlib,sys
import pandas as pd
from ranking import OracleIndex,configure_model
from backend import SparseBackend
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parent
sys.path.insert(0,str(REPO/"commander-card-power-research-v1"))
from spellbook_integration import parse_decklist

def load_backend(config_path=None):
    config=json.load(open(config_path or HERE/"scoring_config.json"))
    configure_model(config)
    cards=[json.loads(s) for s in gzip.open(REPO/"commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz","rt")]
    scores=pd.read_csv(HERE/"candidate_inventory.csv")
    return SparseBackend(OracleIndex(cards),scores,config)

def load_deck(path,commanders=(),resolve=None):
    d=parse_decklist(pathlib.Path(path).read_text())
    if resolve:
        from collections import Counter
        normalized={}
        for zone,values in d.items():
            counts=Counter()
            for name,quantity in values.items():counts[resolve(name)]+=quantity
            normalized[zone]=dict(counts)
        d=normalized
    for name in commanders:
        if resolve:name=resolve(name)
        # Explicit location only: do not guess the commander from legendary status.
        if name in d["main"]:
            if d["main"][name]!=1:raise ValueError("Explicit commander must occur once")
            del d["main"][name]
        d["commanders"][name]=1
    return d

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck_a");p.add_argument("--deck-b")
    p.add_argument("--commander-a",action="append",default=[])
    p.add_argument("--commander-b",action="append",default=[])
    p.add_argument("--config");p.add_argument("--main-threshold",type=float)
    p.add_argument("--commander-threshold",type=float)
    p.add_argument("--team-cap",type=int);p.add_argument("--individual-cap",type=int)
    p.add_argument("--export",help="Output JSON scored report")
    args=p.parse_args()
    b=load_backend(args.config)
    changes={}
    if args.main_threshold is not None:changes["main_threshold"]=args.main_threshold
    if args.commander_threshold is not None:changes["commander_threshold"]=args.commander_threshold
    if args.team_cap is not None:
        if not args.deck_b:p.error("--team-cap requires --deck-b")
        changes["team_cap"]=args.team_cap
    if args.individual_cap is not None:changes["individual_cap"]=args.individual_cap
    if changes:b=SparseBackend(b.index,pd.read_csv(HERE/"candidate_inventory.csv"),dict(b.config,**changes))
    a=load_deck(args.deck_a,args.commander_a,b.index.resolve)
    result=b.team(a,load_deck(args.deck_b,args.commander_b,b.index.resolve)) if args.deck_b else b.score(a)
    text=json.dumps(result,indent=2,allow_nan=False)
    if args.export:pathlib.Path(args.export).write_text(text+"\n")
    print(text)
if __name__=="__main__":main()
