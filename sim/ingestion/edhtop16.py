"""EDHTop16 ingestion adapter (Tier 4, docs/SOURCES.md).

Live API confirmed as a GraphQL endpoint at edhtop16.com/api/graphql
(coverage_backlog INFRA-0001, resolved). This adapter:

1. Pulls the top N commanders by popularity for a given TimePeriod
   (SIX_MONTHS = primary window, ONE_YEAR = secondary window per charter
   "Metagame census" section), filtered to tournaments of minSize+ players
   to focus on genuinely competitive events.
2. For the top `representative_count` of those (by popularity), pulls a
   handful of their highest-standing tournament entries as candidate
   representative decklists (Phase 9).
3. Writes raw snapshots to data/tournament_snapshots/, and a first-pass
   archetype registry to data/archetypes/ conforming to
   data/schemas/archetype.schema.json.

IMPORTANT SCOPE LIMIT: this produces a commander-pairing-level census, not
a fully Phase-8-clustered archetype registry. Per charter, the same
commander pair can support materially different strategic architectures
that deserve separate archetype records (and conversely, trivial flex-slot
differences should NOT be split). Distinguishing those requires reading
primers/recent lists per commander, which this script does not do. Every
archetype record written here is tagged accordingly - do not treat this as
Phase 8-complete.

Usage:
    python3 sim/ingestion/edhtop16.py <output_snapshot_dir> <output_archetype_dir>
"""
import json
import subprocess
import sys
import time
from pathlib import Path

GRAPHQL_URL = "https://edhtop16.com/api/graphql"
REQUEST_DELAY_S = 0.2


def _post_graphql(query: str, variables: dict | None = None) -> dict:
    payload = {"query": query, "variables": variables or {}}
    result = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-H", "Content-Type: application/json",
         "--data", json.dumps(payload), GRAPHQL_URL],
        capture_output=True, text=True, timeout=40,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}): {result.stderr}")
    data = json.loads(result.stdout)
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    time.sleep(REQUEST_DELAY_S)
    return data["data"]


COMMANDERS_QUERY = """
query($first: Int!, $timePeriod: TimePeriod!, $minSize: Int!) {
  commanders(first: $first, timePeriod: $timePeriod, sortBy: POPULARITY, minTournamentSize: 0) {
    edges {
      node {
        id
        name
        colorId
        stats(filters: {timePeriod: $timePeriod, minSize: $minSize}) {
          count
          topCuts
          winRate
          conversionRate
          metaShare
        }
      }
    }
  }
}
"""

ENTRIES_QUERY = """
query($name: String!, $first: Int!) {
  commander(name: $name) {
    entries(first: $first) {
      edges {
        node {
          decklist
          standing
          wins
          losses
          draws
          tournament { name TID tournamentDate size }
          player { name }
        }
      }
    }
  }
}
"""


def fetch_commanders(time_period: str, min_size: int, first: int = 150) -> list[dict]:
    data = _post_graphql(COMMANDERS_QUERY, {"first": first, "timePeriod": time_period, "minSize": min_size})
    return [e["node"] for e in data["commanders"]["edges"]]


def fetch_top_entries(commander_name: str, first: int = 5) -> list[dict]:
    data = _post_graphql(ENTRIES_QUERY, {"name": commander_name, "first": first})
    node = data.get("commander")
    if not node:
        return []
    return [e["node"] for e in node["entries"]["edges"]]


def confidence_tier(count: int) -> str:
    if count >= 300:
        return "high_frequency_deep_model"
    if count >= 50:
        return "moderate_frequency"
    return "low_frequency_shallow_model"


def build_archetype_record(node: dict, window_label: str, total_entries_window: int,
                            representative_entries: list[dict], registry_version: str) -> dict:
    slug = node["name"].lower().replace(" // ", "_").replace(" / ", "_")
    slug = "".join(c if c.isalnum() else "_" for c in slug).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")

    reps = []
    for e in representative_entries[:3]:
        if not e.get("decklist"):
            continue
        t = e.get("tournament") or {}
        reps.append({
            "source": "edhtop16",
            "reference": e["decklist"],
            "date": t.get("tournamentDate") or window_label,
            "notable_variance": (
                f"Standing {e.get('standing')} of tournament '{t.get('name')}' "
                f"(size {t.get('size')}); record {e.get('wins')}-{e.get('losses')}-{e.get('draws')}."
            ),
        })
    if not reps:
        reps = [{
            "source": "edhtop16",
            "reference": f"https://edhtop16.com/commander/{node['id']}",
            "date": window_label,
            "notable_variance": "No individual decklist links returned by EDHTop16 for this commander in this pull; representative_lists points at the commander's aggregate EDHTop16 page instead.",
        }]

    return {
        "archetype_id": f"edhtop16-{slug}",
        "commanders": node["name"].split(" // ") if " // " in node["name"] else node["name"].split(" / "),
        "strategic_architecture": (
            "NOT YET CLASSIFIED (Phase 8 pending) - this record represents a commander "
            "pairing as reported by EDHTop16, not a strategy-clustered archetype. The same "
            "commander(s) may span multiple materially different architectures; conversely "
            "this pairing should not be assumed to be a single coherent strategy until a "
            "primer/recent-decklist review is done."
        ),
        "split_from": None,
        "prevalence": {
            "tournament_window": window_label,
            "entry_count": node["stats"]["count"],
            "total_entries_in_window": total_entries_window,
            "source": "edhtop16",
        },
        "representative_lists": reps,
        "policy_ref": None,
        "confidence_tier": confidence_tier(node["stats"]["count"]),
        "registry_version": registry_version,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    snapshot_dir = Path(sys.argv[1])
    archetype_dir = Path(sys.argv[2])
    min_size = 32
    representative_count = 20  # pull decklists for the top N by popularity only

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    archetype_dir.mkdir(parents=True, exist_ok=True)

    for time_period, window_label, registry_version in [
        ("SIX_MONTHS", "edhtop16-SIX_MONTHS-pulled-2026-08-12", "archetypes-2026-02-12_2026-08-12"),
        ("ONE_YEAR", "edhtop16-ONE_YEAR-pulled-2026-08-12", "archetypes-2025-08-12_2026-08-12"),
    ]:
        print(f"Fetching commanders: {time_period} (minSize={min_size})", file=sys.stderr)
        commanders = fetch_commanders(time_period, min_size)
        print(f"  {len(commanders)} commander entries returned", file=sys.stderr)

        (snapshot_dir / f"commanders_{time_period}.json").write_text(json.dumps({
            "pulled_at": "2026-08-12",
            "time_period": time_period,
            "min_tournament_size": min_size,
            "source": "https://edhtop16.com/api/graphql",
            "commanders": commanders,
        }, indent=2) + "\n")

        total_entries = sum(c["stats"]["count"] for c in commanders if c["stats"]["count"])

        out_subdir = archetype_dir / registry_version
        out_subdir.mkdir(parents=True, exist_ok=True)
        for i, node in enumerate(commanders):
            if node["stats"]["count"] is None:
                continue
            reps = []
            if i < representative_count:
                print(f"  [{i + 1}/{representative_count}] entries for {node['name']}", file=sys.stderr)
                try:
                    reps = fetch_top_entries(node["name"], first=3)
                except RuntimeError as e:
                    print(f"    entries fetch failed: {e}", file=sys.stderr)
            record = build_archetype_record(node, window_label, total_entries, reps, registry_version)
            (out_subdir / f"{record['archetype_id']}.json").write_text(json.dumps(record, indent=2) + "\n")

        print(f"  wrote {len(commanders)} archetype records to {out_subdir}", file=sys.stderr)


if __name__ == "__main__":
    main()
