def acquire_local(root):
    import json,gzip,collections,re,datetime,pathlib,unicodedata
    base=root/"commander-league-card-point-calibration"
    all_cards=[json.loads(x) for x in gzip.open(base/"data/raw/oracle_cards.jsonl.gz","rt")]
    from ranking import OracleIndex
    index=OracleIndex(all_cards)
    def resolve(name):
     try:return index.cards[index.resolve(name)]["name"]
     except KeyError:return None
    p=root/"data/tournament_snapshots/topdeck"
    manifest=json.load(open(p/"manifest.json"))
    end=datetime.datetime(2026,10,20,tzinfo=datetime.timezone.utc).timestamp()
    split=datetime.datetime(2026,10,1,tzinfo=datetime.timezone.utc).timestamp()
    excluded=collections.Counter(); events=[]; exclusion_records=[]; pools={"cedh_train":[],"cedh_holdout":[],"bracket3_declared":[]}
    def omit(reason,event_id,entry_index=None):
     excluded[reason]+=1;exclusion_records.append({"event_id":event_id,"entry_index":entry_index,"reason":reason})
    unknown=collections.Counter(); frequencies=collections.Counter()
    for tid,record in manifest["events"].items():
     path=p/record["normalized_event"]; d=json.load(open(path)); name=d["name"]
     timestamp=d.get("start_date_unix") or 0
     if timestamp>=end:omit("future_event",tid);continue
     if timestamp<=0:omit("missing_date",tid);continue
     low=unicodedata.normalize("NFKD",name).encode("ascii","ignore").decode().lower()
     declared_b3=bool(re.search(r"bracket\s*3|\bb3\b",low))
     explicit_cedh=bool(re.search(r"c[\s.-]*edh",low))
     if declared_b3:cohort="bracket3_declared"
     elif explicit_cedh and not re.search(r"casual|bracket|pauper|brawl|budget|test|cancel",low):cohort="cedh_train" if timestamp<split else "cedh_holdout"
     else:omit("not_explicit_competitive_or_bracket3",tid);continue
     if d.get("field_size",0)<16:omit("field_below16",tid);continue
     if not d.get("pods") or not any(pod.get("status")=="Completed" for pod in d.get("pods",[])):
      omit("no_completed_pod",tid);continue
     raw=json.load(gzip.open(p/record["raw_snapshot"],"rt"))
     valid=0
     for entry_index,row in enumerate(raw.get("standings",[])):
      obj=row.get("deckObj")
      if not isinstance(obj,dict):omit("entry_without_structured_deck",tid,entry_index);continue
      sections={};has_unknown=False
      for dest,src in [("main","Mainboard"),("commanders","Commanders")]:
       counts=collections.Counter()
       for card_name,entry in (obj.get(src) or {}).items():
        canonical=resolve(card_name)
        if canonical is None:unknown[card_name]+=1;has_unknown=True
        else:counts[canonical]+=int(entry.get("count",1))
       sections[dest]=dict(counts)
      if has_unknown:
       omit("entry_unknown_card",tid,entry_index);continue
      if sum(sections["main"].values())+sum(sections["commanders"].values()) !=100:
       omit("entry_not100",tid,entry_index);continue
      if len(sections["commanders"]) not in(1,2):omit("entry_commander_count",tid,entry_index);continue
      descriptor={"event_id":tid,"event_name":name,"date":d["start_date_utc"],"cohort":cohort,**sections}
      pools[cohort].append(descriptor);valid+=1
      if cohort=="cedh_train": frequencies.update(sections["main"].keys())
     events.append({"id":tid,"cohort":cohort,"valid_decks":valid})
    result={"event_manifest_count":len(manifest["events"]),"eligible_event_count":len(events),"cohort_deck_counts":{k:len(v) for k,v in pools.items()},"exclusions":dict(excluded),"exclusion_records":exclusion_records,"unknown_names":unknown.most_common(15),"training_unique_cards":len(frequencies),"training_top30":frequencies.most_common(30),"events":events,"pools":pools,"frequencies":dict(frequencies)}


    return result,pools,all_cards
