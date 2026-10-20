"""Offline season0-proposed backend. Construction points and gameplay review are separate.
Reuses the prior Oracle resolver, Commander legality checks and Moxfield parser.
"""
import argparse,collections,gzip,json,math,pathlib,sys
from fractions import Fraction
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/"commander-top1000-power-ranking"))
sys.path.insert(0,str(ROOT/"commander-card-power-research-v1"))
import pandas as pd
from ranking import OracleIndex,eligibility,price,oracle_text
from backend import SparseBackend
from spellbook_integration import parse_decklist

def proposed_price(score,cutoff=75,curve="nonlinear",scale=15,power=1.5,fine_scale=.6):
    if score is None or pd.isna(score) or float(score)<=cutoff:return 0
    gap=max(0,float(score)-cutoff)
    if curve=="existing_tiers":return price(float(score),cutoff,"tiered")
    if curve=="fine_integer":return int(math.ceil(gap*fine_scale))
    if curve=="nonlinear":return int(math.ceil(scale*(gap/25)**power))
    raise ValueError("Unknown price curve")

class AuditBackend(SparseBackend):
    def __init__(self,index,frame,config,combos=None,anchors=None):
        self.audit_config=dict(config)
        cutoff=config.get("cutoff",75)
        if isinstance(cutoff,bool) or not isinstance(cutoff,(int,float)) or not math.isfinite(cutoff) or not 0<=cutoff<=100:
            raise ValueError("Cutoff must be finite and within 0..100")
        curve=config.get("price_curve","nonlinear")
        if curve not in ("existing_tiers","fine_integer","nonlinear"):raise ValueError("Unknown curve")
        for field in ("nonlinear_scale","nonlinear_power","fine_scale"):
            value=config.get(field,{"nonlinear_scale":15,"nonlinear_power":1.5,"fine_scale":.6}[field])
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError("Invalid price coefficient")
        def value(score):return proposed_price(score,cutoff,curve,config.get("nonlinear_scale",15),config.get("nonlinear_power",1.5),config.get("fine_scale",.6))
        overrides={}
        for row in frame.to_dict("records"):
            oid=row["oracle_id"]
            overrides[oid]={"main_deck_points":value(row.get("main_deck_impact")),
                            "command_zone_points":value(row.get("command_zone_impact")) if eligibility(index.cards[oid]) else 0}
        for oid,fields in config.get("overrides",{}).items():
            overrides.setdefault(oid,{}).update(fields)
        super().__init__(index,frame,{"version":config["version"],"overrides":overrides,
                                    "team_cap":config.get("team_cap"),"individual_cap":config.get("individual_cap")})
        self.combos=list(combos or [])
        self.anchors=list(anchors or [])
        for a in self.anchors:
            value=self.card_price(index.resolve(a["card_name"]),a["zone"])
            ranges={0:(0,0),1:(1,2),2:(3,4),3:(5,7),4:(8,10),5:(11,15)}
            low,high=ranges[a["tier"]]
            if not low<=value<=high:raise ValueError("Human tier conflict: "+a["card_name"])
        self.policy=self._policy(config)
    @staticmethod
    def _policy(config):
        p={k:config.get(k) for k in ("team_cap","individual_cap","individual_reference")}
        for field,val in p.items():
            if val is not None and (isinstance(val,bool) or not isinstance(val,int) or val<0):raise ValueError("Invalid "+field)
        fraction=config.get("transfer_fraction",.2)
        if isinstance(fraction,bool) or not isinstance(fraction,(int,float)) or not math.isfinite(fraction) or not 0<=fraction<=1:
            raise ValueError("Transfer fraction must be within 0..1")
        p["transfer_fraction"]=fraction
        return p
    def score(self,deck):
        r=super().score(deck)
        ids={self.index.resolve(n) for z in ("main","commanders") for n in deck.get(z,{})}
        r["rules_risk_flags"]=[]
        if any("rulebreaker" in oracle_text(self.index.cards[o]).lower() for o in ids):
            r["rules_risk_flags"].append("rulebreaker_deck_construction_requires_manual_adjudication")
            r["officially_legal"]=False
            r["legality_issues"].append("unsupported_rulebreaker_permission_requires_manual_review")
        for a in self.anchors:
            if a["zone"]=="commanders" and a["tier"]==0 and self.index.resolve(a["card_name"]) in {self.index.resolve(n) for n in deck.get("commanders",{})}:
                r["rules_risk_flags"].append("organizer_free_commander_requires_strategy_review:"+a["card_name"])
        r["submitted_deck"]={z:{self.index.cards[self.index.resolve(n)]["name"]:q for n,q in deck.get(z,{}).items()} for z in ("main","commanders")}
        r["experimental_unbans_activated"]=False
        r["automatic_combo_certification"]=False
        return r
    def pairing_review(self,a,b):
        def names(d):return {self.index.cards[self.index.resolve(n)]["name"] for z in ("main","commanders") for n in d.get(z,{})}
        aa,bb=names(a),names(b);out=[]
        for c in self.combos:
            for orientation,left,right in (("as_listed",aa,bb),("reversed",bb,aa)):
                if set(c["cards_A"])<=left and set(c["cards_B"])<=right:
                    out.append({"id":c["id"],"orientation":orientation,"known_controller_assessment":c["status"],
                                "component_match_only":True,"requires_manual_state_and_controller_verification":True,
                                "outcome_if_prerequisites_hold":c["outcome"],"points_adjustment":0})
                    break
        return out
    def team(self,a,b,team_cap=None,individual_cap=None,individual_reference=None,transfer_fraction=None):
        cfg=dict(self.audit_config)
        for k,v in (("team_cap",team_cap),("individual_cap",individual_cap),("individual_reference",individual_reference),("transfer_fraction",transfer_fraction)):
            if v is not None:cfg[k]=v
        p=self._policy(cfg)
        r=super().team(a,b,p["team_cap"],p["individual_cap"])
        reference=p["individual_reference"]
        if reference is None:excess=0;limit=None;transfer_ok=True
        else:
            excess=max(0,r["a"]["total"]-reference,r["b"]["total"]-reference)
            limit=int(reference*Fraction(str(p["transfer_fraction"])))
            unused=max(0,reference-min(r["a"]["total"],r["b"]["total"]))
            transfer_ok=excess<=limit and excess<=unused
        for who in ("a","b"):r[who]["within_individual_cap"]=p["individual_cap"] is None or r[who]["total"]<=p["individual_cap"]
        r["submitted_decks"]={who:r[who]["submitted_deck"] for who in ("a","b")}
        r.update({"version":cfg["version"],"individual_reference":reference,"transfer_limit":limit,
                  "points_transferred":excess,"within_transfer_policy":transfer_ok,
                  "budget_compliant":r["within_team_cap"] and r["within_individual_cap"] and transfer_ok,
                  "combo_review_candidates":self.pairing_review(a,b),
                  "gameplay_legality_approved":False,
                  "review_note":"Point compliance never certifies combo execution or league gameplay legality."})
        return r

def load_backend(root=ROOT,config_path=None,overrides_path=None):
    root=pathlib.Path(root);here=root/"commander-doubles-final-audit"
    config=json.loads(pathlib.Path(config_path).read_text()) if config_path else json.loads((here/"scoring_config.json").read_text())
    if overrides_path:
        incoming=json.loads(pathlib.Path(overrides_path).read_text())
        if not isinstance(incoming,dict):raise ValueError("Overrides must be Oracle-ID map")
        config["overrides"]={**config.get("overrides",{}),**incoming}
    inputs=json.loads((here/"audit_inputs.json").read_text())
    index=OracleIndex([json.loads(l) for l in gzip.open(root/"commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz","rt")])
    return AuditBackend(index,pd.read_csv(root/"commander-top1000-power-ranking/candidate_inventory.csv"),config,inputs["combos"],inputs["anchors"])

def load_deck(path,which="a"):
    text=pathlib.Path(path).read_text()
    data=json.loads(text) if str(path).endswith(".json") else parse_decklist(text)
    if isinstance(data,dict) and "submitted_decks" in data:data=data["submitted_decks"][which]
    elif isinstance(data,dict) and "submitted_deck" in data:data=data["submitted_deck"]
    if not isinstance(data,dict) or set(data)-{"main","commanders"}:raise ValueError("Deck JSON requires main/commanders maps only")
    for z in ("main","commanders"):
        if not isinstance(data.get(z,{}),dict):raise ValueError("Deck sections must be objects")
    return data

def cli():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck_a");p.add_argument("--deck-b");p.add_argument("--config")
    p.add_argument("--team-cap",type=int);p.add_argument("--individual-cap",type=int)
    p.add_argument("--individual-reference",type=int);p.add_argument("--transfer-fraction",type=float)
    p.add_argument("--export");p.add_argument("--overrides");p.add_argument("--export-overrides")
    args=p.parse_args()
    b=load_backend(config_path=args.config,overrides_path=args.overrides);a=load_deck(args.deck_a)
    imported_team=None
    if str(args.deck_a).endswith(".json"):
        incoming=json.loads(pathlib.Path(args.deck_a).read_text())
        if isinstance(incoming,dict) and "submitted_decks" in incoming:imported_team=load_deck(args.deck_a,"b")
    if args.export_overrides:pathlib.Path(args.export_overrides).write_text(json.dumps(b.audit_config["overrides"],indent=2)+"\n")
    if args.deck_b or imported_team:
        result=b.team(a,load_deck(args.deck_b) if args.deck_b else imported_team,args.team_cap,args.individual_cap,args.individual_reference,args.transfer_fraction)
    else:
        if any(v is not None for v in (args.team_cap,args.individual_reference,args.transfer_fraction)):
            p.error("Team/transfer options require --deck-b")
        if args.individual_cap is not None:
            if args.individual_cap<0:p.error("Negative individual cap")
            b.config["individual_cap"]=args.individual_cap
        result=b.score(a)
    text=json.dumps(result,indent=2,sort_keys=True)
    if args.export:pathlib.Path(args.export).write_text(text+"\n")
    print(text)
if __name__=="__main__":cli()
