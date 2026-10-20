from ranking import *

class SparseBackend:
    def __init__(self,index,rankings,config=None):
        self.index=index
        self.ratings=rankings.set_index("oracle_id").to_dict("index")
        self.config={"main_threshold":75.,"commander_threshold":75.,"curve":"tiered","version":"top1000-v0.1-candidate","overrides":{},"tier_bands":[[5,1],[10,3],[15,5],[20,8],[25,12],[None,20]]}
        if config:self.config.update(config)
        validate_tier_bands(self.config["tier_bands"])
        for field in ("main_threshold","commander_threshold"):
            value=self.config[field]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100:raise ValueError("Cutoff must be finite and within 0..100")
        if self.config["curve"] not in ("linear","tiered","quadratic"):raise ValueError("Unsupported price curve")
        for field in ("team_cap","individual_cap"):
            cap=self.config.get(field)
            if cap is not None and (isinstance(cap,bool) or not isinstance(cap,int) or cap<0):raise ValueError("Caps must be nonnegative integers or null")
        for oid,entry in self.config["overrides"].items():
            if oid not in self.index.cards:raise KeyError("Unknown override Oracle ID: "+oid)
            if not isinstance(entry,dict):raise ValueError("Overrides must have zone-specific fields")
            for zone,value in entry.items():
                if zone not in ("main_deck_points","command_zone_points"):raise ValueError("Unknown override field")
                if not isinstance(value,int) or isinstance(value,bool) or value<0:raise ValueError("Nonnegative integer override required")
                if zone=="command_zone_points" and value>0 and not eligibility(self.index.cards[oid]):raise ValueError("Nonzero command-zone override requires commander eligibility")
    def card_price(self,oid,zone):
        if zone not in ("main","commanders"):raise ValueError("Unknown construction zone")
        if oid not in self.index.cards:raise KeyError(oid)
        field="command_zone_points" if zone=="commanders" else "main_deck_points"
        if field in self.config["overrides"].get(oid,{}):return self.config["overrides"][oid][field]
        row=self.ratings.get(oid)
        if row is None:return 0
        value=row.get("command_zone_impact" if zone=="commanders" else "main_deck_impact")
        if value is None or (isinstance(value,float) and math.isnan(value)):return 0
        return point_price(oid,zone,value,self.config)
    def score(self,deck):
        normalized={}
        for zone in ("main","commanders"):
            counts=collections.Counter()
            for name,quantity in deck.get(zone,{}).items():
                if not isinstance(quantity,int) or isinstance(quantity,bool) or quantity<1:raise ValueError("Positive integer quantities required")
                counts[self.index.resolve(name)]+=quantity
            normalized[zone]=counts
        issues=[];cmds=normalized["commanders"];main=normalized["main"]
        allcards=main+cmds
        if sum(allcards.values())!=100:issues.append("deck_size_not100")
        if len(cmds) not in (1,2) or any(v!=1 for v in cmds.values()):issues.append("invalid_commander_count")
        for oid in cmds:
            if not eligibility(self.index.cards[oid]):issues.append("ineligible_commander:"+self.index.cards[oid]["name"])
        if len(cmds)==1 and eligibility(self.index.cards[next(iter(cmds))])=="conditional_background":issues.append("background_requires_pair")
        if len(cmds)==2 and not pair_legal(*(self.index.cards[o] for o in cmds)):issues.append("incompatible_commander_pair")
        identity=set().union(*(set(self.index.cards[o].get("color_identity",[])) for o in cmds)) if cmds else set()
        for oid,q in allcards.items():
            c=self.index.cards[oid];name=c["name"];text=oracle_text(c)
            if c.get("legalities",{}).get("commander")!="legal":issues.append("official_commander_illegal:"+name)
            if name.startswith("Erayo, Soratami Ascendant"):issues.append("two_hg_constructed_ban:"+name)
            if not set(c.get("color_identity",[]))<=identity:issues.append("outside_commander_color_identity:"+name)
            basic="Basic" in c.get("type_line","") and "Land" in c.get("type_line","")
            for landtype,color in {"Plains":"W","Island":"U","Swamp":"B","Mountain":"R","Forest":"G"}.items():
                if "Land" in c.get("type_line","") and landtype in c.get("type_line","") and color not in identity:issues.append("basic_land_type_outside_identity:"+name)
            unlimited="A deck can have any number of cards named" in text
            if q>1 and not basic and not unlimited:
                limit=1
                match=re.search(r"A deck can have up to (\w+) cards named",text)
                if match:limit={"seven":7,"nine":9}.get(match[1],1)
                if q>limit:issues.append("singleton_limit:"+name)
            if oid in cmds and ("choose a color" in text.lower() and "color identity" in text.lower()):
                issues.append("unresolved_pregame_color_choice:"+name)
        records=[]
        for zone,counts in normalized.items():
            for oid,q in counts.items():
                records.append({"oracle_id":oid,"card_name":self.index.cards[oid]["name"],"zone":zone,"quantity":q,
                    "points_each":self.card_price(oid,zone),"total":q*self.card_price(oid,zone),
                    "rating_evidence":("point_override" if ("command_zone_points" if zone=="commanders" else "main_deck_points") in self.config["overrides"].get(oid,{}) else "reviewed_judgment" if self.ratings.get(oid,{}).get("command_zone_manually_assessed" if zone=="commanders" else "manually_assessed") else "known_unpointed_or_low_confidence"),
                    "experimental_banned":self.index.cards[oid].get("legalities",{}).get("commander")=="banned"})
        records.sort(key=lambda row:(-row["total"],row["card_name"]))
        total=sum(r["total"] for r in records)
        cap=self.config.get("individual_cap")
        return {"version":self.config["version"],"total":total,"within_individual_cap":cap is None or total<=cap,
                "command_zone_total":sum(r["total"] for r in records if r["zone"]=="commanders"),
                "officially_legal":not issues,"legality_issues":sorted(set(issues)),"rows":records}
    def team(self,a,b,team_cap=None,individual_cap=None):
        if team_cap is None:team_cap=self.config.get("team_cap")
        if individual_cap is None:individual_cap=self.config.get("individual_cap")
        for cap in (team_cap,individual_cap):
            if cap is not None and (isinstance(cap,bool) or not isinstance(cap,int) or cap<0):raise ValueError("Caps must be nonnegative integers or null")
        ra,rb=self.score(a),self.score(b)
        total=ra["total"]+rb["total"]
        return {"a":ra,"b":rb,"total":total,"teammate_synergy_adjustment":0,
                "within_team_cap":team_cap is None or total<=team_cap,
                "within_individual_cap":individual_cap is None or max(ra["total"],rb["total"])<=individual_cap,
                "both_decks_legal":ra["officially_legal"] and rb["officially_legal"]}
