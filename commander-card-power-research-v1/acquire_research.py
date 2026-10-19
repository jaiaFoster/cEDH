"""Download versioned, permitted research inputs; never scrape EDHREC."""
import datetime
import hashlib
import io
import json
import pathlib
import pickle
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "data/raw"
HEADERS = {"User-Agent": "CommanderLeagueResearch/1.0 (github.com/jaiaFoster/cEDH)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as response:
        return response.read()


class DataOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError("Executable pickle globals are prohibited")

    def persistent_load(self, pid):
        raise pickle.UnpicklingError("Persistent references are prohibited")


def read_cache(raw):
    value = DataOnlyUnpickler(io.BytesIO(raw)).load()
    assert isinstance(value, dict)
    for name, entry in value.items():
        assert isinstance(name, str) and isinstance(entry, dict)
        assert set(entry) <= {"h", "p"}
        assert isinstance(entry.get("h"), str)
        assert isinstance(entry.get("p"), (int, float)) and 0 <= entry["p"] <= 100
    return value


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = []
    repos = {
        "zarzak": ("zarzak/mtg-deck-builder", "main", [
            "card_power_cache/power_claude-sonnet-4-6.pkl", "README.md", "LICENSE",
            "mtg_deck_builder/card_power_scorer.py", "mtg_deck_builder/models.py"]),
        "xmage": ("magefree/mage", "master", ["LICENSE.txt",
            "Mage.Server.Plugins/Mage.Deck.Constructed/src/mage/deck/AbstractCommander.java"]),
        "creature": ("AgentSamSA/mtg-mechanics-parser", "main", [
            "README.md", "LICENSE", "data/processed/combined_points_cleaned.csv"]),
        "spellbook": ("SpaceCowMedia/commander-spellbook-backend", "master", [
            "LICENSE", "backend/spellbook/views/find_my_combos.py",
            "backend/spellbook/views/utils.py", "backend/spellbook/serializers/variant_serializer.py"]),
    }
    for label, (repo, ref, paths) in repos.items():
        sha = json.loads(get(f"https://api.github.com/repos/{repo}/commits/{ref}"))["sha"]
        for path in paths:
            url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
            try:
                content = get(url)
            except Exception as error:
                manifest.append({"url": url, "status": "unavailable", "error": str(error),
                    "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
                continue
            destination = RAW / label / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            manifest.append({"url": url, "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
                "path": str(destination.relative_to(ROOT)), "git_commit": sha})
    cache_path = RAW / "zarzak/card_power_cache/power_claude-sonnet-4-6.pkl"
    cache = read_cache(cache_path.read_bytes())
    (ROOT / "data/zarzak_cache.json").write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    (ROOT / "data/acquisition_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"downloaded_files": len(manifest), "cached_card_names": len(cache)}))


if __name__ == "__main__":
    acquire()
