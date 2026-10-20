"""Validate saved artifacts against frozen sources and the offline backend."""
import gzip,hashlib,json,pathlib
import pandas as pd
from ranking import OracleIndex
from backend import SparseBackend
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
required=["top_1000_main_deck_cards.csv","top_commanders.csv","candidate_inventory.csv","point_cutoff_analysis.md","cutoff_comparison.csv","proposed_point_schedule.csv","card_ranking_methodology.md","manual_review_queue.csv","precon_cutoff_benchmarks.csv","ranking_visualizations.png","experimental_unban_ranking.csv","scoring_config.json","README.md"]
for name in required:assert (HERE/name).is_file(),name
frame=pd.read_csv(HERE/"candidate_inventory.csv")
top=pd.read_csv(HERE/"top_1000_main_deck_cards.csv")
assert len(top)==1000 and top.oracle_id.is_unique
assert frame.oracle_id.is_unique and frame.main_deck_impact.is_monotonic_decreasing
assert top.oracle_id.tolist()==frame.oracle_id.head(1000).tolist()
assert (frame[["main_deck_points","command_zone_points"]]>=0).all().all()
assert ((frame[["main_deck_points","command_zone_points"]]%1)==0).all().all()
cards=[json.loads(l) for l in gzip.open(ROOT/"commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz","rt")]
index=OracleIndex(cards);config=json.load(open(HERE/"scoring_config.json"));b=SparseBackend(index,frame,config)
for row in frame.to_dict("records"):
    assert b.card_price(row["oracle_id"],"main")==row["main_deck_points"]
    assert b.card_price(row["oracle_id"],"commanders")==row["command_zone_points"]
precons=json.load(open(ROOT/"commander-league-card-point-calibration/data/clean/precons.json"))
bench=pd.read_csv(HERE/"precon_cutoff_benchmarks.csv")
assert (bench.groupby("policy").size()==174).all()
active=bench[bench.policy=="configured_policy"].set_index("deck_name")
assert len(active)==174
for d in precons:
    assert sum(d["counts"].values())==100
    assert set(d["counts"])<=set(index.cards)
    cmd=set(d["commander_ids"])
    report=b.score({"main":{o:q for o,q in d["counts"].items() if o not in cmd},"commanders":{o:q for o,q in d["counts"].items() if o in cmd}})
    assert report["total"]==active.loc[d["name"],"total_points"],d["name"]
    assert report["command_zone_total"]==active.loc[d["name"],"command_zone_points"],d["name"]
legal=pd.read_csv(HERE/"proposed_legal_point_schedule.csv")
assert (legal.commander_legality=="legal").all() and not legal.two_hg_specific_ban.any()
bans=pd.read_csv(HERE/"experimental_unban_ranking.csv")
assert len(bans)==42 and not bans.legalized.any()
assert (bans.commander_legality=="banned").all()
can=json.load(open(ROOT/"commander-card-power-research-v1/data/benchmark_inputs.json"))["canlander"]
assert {index.resolve(n) for n in can}<={*frame.oracle_id}
assert frame.loc[(frame.canadian_highlander_points>0)|frame.game_changer,"manually_assessed"].all()
manifest=json.load(open(HERE/"source_provenance.json"))
for name,value in manifest.items():
    if isinstance(value,dict) and "sha256" in value:assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value["sha256"],name
for name,digest in manifest["implementation_sha256"].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
print(json.dumps({"required_deliverables":len(required),"ranked_cards":len(top),"candidate_cards":len(frame),"precons_verified":len(active),"cutoff_policies":bench.policy.nunique(),"legal_pointed_identities":len(legal),"named_bans_remain_banned":len(bans),"source_hashes":"verified"},indent=2))
