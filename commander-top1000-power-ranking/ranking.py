"""Provisional 2HG sparse ranking. Analyst rubric is policy judgment, not measured strength."""
import collections, gzip, hashlib, json, math, pathlib, re, unicodedata
import numpy as np
import pandas as pd

MAIN_WEIGHTS={"ceiling":5.5,"applicability":2.0,"tempo":1.5,"resilience":1.0}
SPECIALIST_MIN_CEILING=9.5
SPECIALIST_FLOOR=80.
TIER_BANDS=[(5,1),(10,3),(15,5),(20,8),(25,12),(math.inf,20)]
EXCLUDED_OFFENSIVE={"Cleanse","Crusade","Imprison","Invoke Prejudice","Jihad","Pradesh Gypsies","Stone-Throwing Devils"}

PRIOR={"default_rating":60.,"center":35.,"divisor":8.,"ceiling_cap":7.5,"neutral":5.,"command_zone_cap":69.,"command_zone_offset":4.}
DEFAULT_PRIOR=dict(PRIOR)
def validate_tier_bands(bands):
    result=[]
    for upper,points in bands:
        if isinstance(points,bool) or not isinstance(points,int) or points<0:raise ValueError("Tier points must be nonnegative integers")
        if upper is not None and (isinstance(upper,bool) or not isinstance(upper,(int,float)) or not math.isfinite(upper) or upper<=0):raise ValueError("Tier boundaries must be positive finite numbers or final null")
        result.append((math.inf if upper is None else upper,points))
    if not result or not math.isinf(result[-1][0]) or any(a[0]>=b[0] or a[1]>b[1] for a,b in zip(result,result[1:])):raise ValueError("Monotonic tiers ending with null required")
    return result
def configure_model(config):
    global MAIN_WEIGHTS,SPECIALIST_MIN_CEILING,SPECIALIST_FLOOR,TIER_BANDS,PRIOR
    weights=config.get("weights",MAIN_WEIGHTS)
    if set(weights)!=set(MAIN_WEIGHTS) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in weights.values()) or abs(sum(weights.values())-10)>1e-9:
        raise ValueError("Four nonnegative rubric weights must sum to ten")
    MAIN_WEIGHTS=dict(weights)
    SPECIALIST_MIN_CEILING=float(config.get("specialist_min_ceiling",9.5))
    SPECIALIST_FLOOR=float(config.get("specialist_floor",80.))
    if not 0<=SPECIALIST_MIN_CEILING<=10 or not 0<=SPECIALIST_FLOOR<=100:raise ValueError("Specialist policy parameters outside allowed range")
    TIER_BANDS=validate_tier_bands(config.get("tier_bands",[(5,1),(10,3),(15,5),(20,8),(25,12),(None,20)]))
    PRIOR=dict(DEFAULT_PRIOR,**config.get("unreviewed_prior",{}))
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in PRIOR.values()) or PRIOR["divisor"]<=0:raise ValueError("Invalid unreviewed prior parameter")

def name_key(name):
    return unicodedata.normalize("NFC",name).casefold().replace("’","'").strip()
def oracle_text(card):
    return card.get("oracle_text","") or "\n".join(f.get("oracle_text","") for f in card.get("card_faces",[]))
def front(card):
    return card.get("card_faces",[card])[0]
def eligibility(card):
    face=front(card); ty=face.get("type_line",card.get("type_line","")); text=oracle_text(card)
    if "Background" in ty and "Legendary" in ty and "Enchantment" in ty:
        return "conditional_background"
    if "can be your commander" in text.lower():
        return "explicit_text"
    if card["name"]=="Grist, the Hunger Tide":
        return "off_battlefield_creature"
    if "Legendary" in ty and ("Creature" in ty or "Vehicle" in ty):
        return "standalone"
    if "Legendary" in ty and "Spacecraft" in ty and (
        "power" in face and "toughness" in face):
        return "standalone"
    return ""
class OracleIndex:
    def __init__(self,cards):
        self.cards={c["oracle_id"]:c for c in cards if c.get("oracle_id")}
        alias_file=pathlib.Path(__file__).resolve().parent/"data/name_aliases.json"
        self.interchangeable={name_key(k):v for k,v in json.loads(alias_file.read_text())["aliases"].items()} if alias_file.exists() else {}
        self.exact=collections.defaultdict(set)
        for c in self.cards.values():self.exact[name_key(c["name"])].add(c["oracle_id"])
        self.aliases=collections.defaultdict(set)
        for oid,c in self.cards.items():
            self.aliases[name_key(c["name"].split(" // ")[0])].add(oid)
    def resolve(self,name):
        if name in self.cards:return name
        k=name_key(name)
        if k in self.interchangeable:
            oid=self.interchangeable[k]
            if oid not in self.cards:raise KeyError("Alias target absent from Oracle snapshot: "+name)
            return oid
        hits=self.exact.get(k) or self.aliases.get(k,set())
        legal={o for o in hits if self.cards[o].get("legalities",{}).get("commander") in ("legal","banned")}
        if len(legal)==1:return next(iter(legal))
        if len(hits)==1:return next(iter(hits))
        raise KeyError("Unknown or ambiguous card: "+name)
def impact(row,ceiling_floor=False):
    if any(isinstance(row[k],bool) or not isinstance(row[k],(int,float)) or not math.isfinite(row[k]) or not 0<=row[k]<=10 for k in MAIN_WEIGHTS):raise ValueError("Rubric dimensions must be finite numbers in 0..10")
    total=sum(MAIN_WEIGHTS[k]*row[k] for k in MAIN_WEIGHTS)+row.get("two_hg_adjustment",0)
    # Explicit specialist policy safeguard, not evidence of an empirical discontinuity.
    if ceiling_floor and row["ceiling"]>=SPECIALIST_MIN_CEILING: total=max(total,SPECIALIST_FLOOR)
    return min(100.,max(0.,round(total,4)))
def price(score,threshold,curve="tiered",tier_bands=None):
    if score<=threshold:return 0
    gap=score-threshold
    if curve=="linear":return max(1,math.ceil(gap))
    if curve=="quadratic":return max(1,math.ceil(20*(gap/(100-threshold))**2))
    if curve=="tiered":
        # Same thresholds relative to cutoff in both zones; top-price sensitivity is explicit.
        bands=TIER_BANDS if tier_bands is None else [(math.inf if upper is None else upper,points) for upper,points in tier_bands]
        return next(points for upper,points in bands if gap<=upper)
    raise ValueError("Unknown curve")
def point_price(oid,zone,score,config,threshold=None,curve=None):
    key="command_zone_points" if zone=="commanders" else "main_deck_points"
    override=config.get("overrides",{}).get(oid,{})
    if key in override:return override[key]
    if score is None or pd.isna(score):return 0
    if threshold is None:threshold=config["commander_threshold" if zone=="commanders" else "main_threshold"]
    return price(score,threshold,curve or config["curve"],config.get("tier_bands"))
def price_boundaries(threshold,curve="tiered"):
    if curve=="linear":return [threshold]+[threshold+i for i in range(1,101) if threshold+i<=100]
    if curve=="quadratic":return [threshold]+[threshold+(100-threshold)*math.sqrt(i/20) for i in range(1,21)]
    return [threshold]+[threshold+upper for upper,_ in TIER_BANDS if math.isfinite(upper) and threshold+upper<=100]
def pair_legal(a,b):
    def parts(c):
        text=oracle_text(c)
        lines=[l.strip() for l in text.splitlines()]
        plain=any(re.match(r"^Partner(?:\s*\(|$)",l) for l in lines)
        family=re.findall(r"Partner\s*[—–-]\s*([^(.\n]+)",text,re.I)
        if "Friends forever" in text:family.append("Friends forever")
        named=re.findall(r"Partner with ([^(.\n]+)",text)
        background="Choose a Background" in text
        companion="Doctor's companion" in text or "Doctor’s companion" in text
        return plain,{name_key(x) for x in family},[name_key(x) for x in named],background,companion
    pa,fa,na,ba,da=parts(a);pb,fb,nb,bb,db=parts(b)
    if pa and pb:return True
    if fa & fb:return True
    if name_key(b["name"].split(" // ")[0]) in na and name_key(a["name"].split(" // ")[0]) in nb:return True
    ea,eb=eligibility(a),eligibility(b)
    if ba and eb=="conditional_background" or bb and ea=="conditional_background":return True
    def doctor(c):
        face=front(c);ty=face.get("type_line","")
        return "Legendary" in ty and "Creature" in ty and ty.split("—")[-1].strip()=="Time Lord Doctor"
    return da and doctor(b) or db and doctor(a)
def build_candidates(cards,external,main_rows,command_rows,canlander,frequencies,overrides=None):
    idx=OracleIndex(cards)
    overrides=overrides or {}
    if set(overrides)-set(idx.cards):raise KeyError("Unknown override Oracle ID")
    main={idx.resolve(r["name"]):r for r in main_rows}
    if len(main)!=len(main_rows):raise ValueError("Duplicate canonical main-deck assessment")
    commanders={}
    rejected=[]
    for r in command_rows:
        try:o=idx.resolve(r["name"])
        except KeyError:
            rejected.append({"name":r["name"],"reason":"unknown commander assessment name"});continue
        if not eligibility(idx.cards[o]):
            rejected.append({"name":r["name"],"reason":"not command-zone eligible"});continue
        commanders[o]=r
    if len(commanders)+len(rejected)!=len(command_rows):raise ValueError("Duplicate canonical command-zone assessment")
    cache={name_key(n):v["p"] for n,v in external.items()}
    records=[]
    for oid,c in idx.cards.items():
        legal=c.get("legalities",{}).get("commander","not_legal")
        if legal not in ("legal","banned") or c["name"] in EXCLUDED_OFFENSIVE:continue
        # Oracle bulk chooses one representative printing, sometimes MTGO-only.
        # games/digital/set_type/released_at of that printing cannot exclude the Oracle card.
        if "Conspiracy" in c.get("type_line","") or re.search(r"\bante\b",oracle_text(c),re.I):continue
        if c.get("layout") in ("token","double_faced_token","emblem","art_series","vanguard","scheme","planar"):continue
        raw=cache.get(name_key(c["name"]))
        if raw is None:raw=cache.get(name_key(c["name"].split(" // ")[0]))
        can=canlander.get(c["name"],canlander.get(c["name"].split(" // ")[0],0))
        nom=[]
        if oid in overrides:nom.append("explicit_point_override")
        if oid in main:nom.append("analyst_functional_review")
        if oid in commanders:nom.append("analyst_commander_review")
        if can:nom.append("canadian_highlander_pointed")
        if c.get("game_changer"):nom.append("official_game_changer")
        if legal=="banned":nom.append("banned_hypothetical_only")
        observed=frequencies.get(c["name"],0)
        if observed:nom.append("observed_competitive_registration")
        if raw is not None and raw>=75:nom.append("external_intrinsic_candidate")
        eligible=eligibility(c)
        if eligible:nom.append("commander_eligible")
        if not nom:continue
        r=main.get(oid)
        if r is None:
            # Explicit low-confidence tail prior, never exceptional-price evidence by itself.
            C=max(0,min(PRIOR["ceiling_cap"],((raw if raw is not None else PRIOR["default_rating"])-PRIOR["center"])/PRIOR["divisor"]))
            r={"ceiling":C,"applicability":PRIOR["neutral"],"tempo":PRIOR["neutral"],"resilience":PRIOR["neutral"],"two_hg_adjustment":0,
               "category":"unreviewed_prior","explanation":"Low-confidence source prior; applicability/tempo/resilience unassessed (neutral placeholders), not inferred from popularity."}
        base=impact(r,True);raw_base=impact(r,False)
        if "Basic" in c.get("type_line","") and "Land" in c.get("type_line",""):base=0;raw_base=0
        cr=commanders.get(oid)
        # No automatic 'base plus premium'. Unreviewed command-zone values remain uncertain.
        cz=impact(cr) if cr else (min(PRIOR["command_zone_cap"],base+PRIOR["command_zone_offset"]) if eligible else None)
        records.append({"oracle_id":oid,"card_name":c["name"],"main_deck_impact":base,"raw_main_deck_impact":raw_base,"specialist_floor_delta":base-raw_base,
            "command_zone_eligibility":eligible or "ineligible","command_zone_impact":cz,
            "command_zone_competitive_ceiling":cr["ceiling"] if cr else None,
            "command_zone_general_applicability":cr["applicability"] if cr else None,
            "command_zone_tempo_efficiency":cr["tempo"] if cr else None,
            "command_zone_resilience":cr["resilience"] if cr else None,
            "command_zone_two_hg_adjustment":cr["two_hg_adjustment"] if cr else None,
            "command_zone_confidence":"provisional_judgment" if cr else "low_unreviewed" if eligible else "ineligible",
            "general_applicability":r["applicability"],"competitive_ceiling":r["ceiling"],
            "tempo_efficiency":r["tempo"],"resilience":r["resilience"],
            "two_hg_adjustment":r["two_hg_adjustment"],"two_hg_considerations":r["explanation"],
            "canadian_highlander_points":can,"game_changer":bool(c.get("game_changer")),
            "commander_legality":legal,"two_hg_specific_ban":c["name"].startswith("Erayo, Soratami Ascendant"),
            "external_published_rating":raw,"competitive_registration_count":observed,
            "category":r["category"],"nomination_reasons":";".join(nom),
            "manually_assessed":oid in main,"command_zone_manually_assessed":cr is not None,
            "valuation_explanation":r["explanation"],"command_zone_explanation":cr["explanation"] if cr else "Unreviewed command-zone prior; not guaranteed-access calibration.",
            "confidence":"provisional_judgment" if oid in main else "low_unreviewed",
            "manual_review_priority":"high" if oid not in main or legal=="banned" else "routine",
            "color_identity":"".join(c.get("color_identity",[])),
            "source_references":"https://scryfall.com/docs/api/bulk-data;analyst_assessments.json;"+("https://canadianhighlander.ca/points-list/;" if can else "")+("https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-february-9-2026;" if c.get("game_changer") else "")+("https://github.com/zarzak/mtg-deck-builder/tree/2ccb39f3e0fa08d91e848c2c98851effa8fa1fb2;" if raw is not None else "")+("https://topdeck.gg;repository/data/tournament_snapshots/topdeck/manifest.json;" if observed else "")})
    df=pd.DataFrame(records).sort_values(["main_deck_impact","card_name"],ascending=[False,True]).reset_index(drop=True)
    df["main_deck_rank"]=np.arange(1,len(df)+1)
    cmd=df[df.command_zone_impact.notna()].sort_values(["command_zone_impact","card_name"],ascending=[False,True]).copy()
    cmd["command_zone_rank"]=np.arange(1,len(cmd)+1)
    return idx,df,cmd,rejected
