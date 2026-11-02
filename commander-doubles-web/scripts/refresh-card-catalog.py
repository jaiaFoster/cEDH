#!/usr/bin/env python3
"""Build an immutable, checksummed local catalog from Scryfall bulk archives.
Download metadata/archives once, then replay offline. No prices or historical rows are edited.
"""
import re, unicodedata
import argparse, collections, datetime, gzip, hashlib, json, os, pathlib, struct, tempfile, urllib.request, uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--cache", required=True)
p.add_argument("--download", action="store_true")
p.add_argument("--activate", action="store_true")
a = p.parse_args()
cache = pathlib.Path(a.cache)
cache.mkdir(parents=True, exist_ok=True)


def download(url, path):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CommanderDoubles/1.0 (+https://github.com/jaiaFoster/cEDH)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r, open(
        str(path) + ".part", "wb"
    ) as f:
        while b := r.read(1024 * 1024):
            f.write(b)
    os.replace(str(path) + ".part", path)


if a.download:
    download("https://api.scryfall.com/bulk-data", cache / "bulk-metadata.json")
meta = json.loads((cache / "bulk-metadata.json").read_text())
sources = {c["type"]: c for c in meta["data"]}
for k in ("oracle_cards", "all_cards"):
    if a.download:
        download(
            sources[k].get("jsonl_download_uri") or sources[k]["download_uri"],
            cache / (k + ".jsonl.gz"),
        )


def rows(path):
    # Current Scryfall JSONL bulk archives; fail clearly if an older JSON-array URI is supplied.
    with gzip.open(path, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(1024 * 1024):
            h.update(b)
    return h.hexdigest()


version = (
    "scryfall-"
    + sources["oracle_cards"]["updated_at"][:10]
    + "-v2-"
    + sha(cache / "all_cards.jsonl.gz")[:10]
)
base = ROOT / "data/catalogs"
base.mkdir(exist_ok=True)
dest = base / version
fields = (
    "oracle_id",
    "name",
    "mana_cost",
    "cmc",
    "type_line",
    "oracle_text",
    "power",
    "toughness",
    "color_identity",
    "legalities",
    "games",
    "digital",
    "layout",
    "colors",
    "scryfall_uri",
    "card_faces",
    "released_at",
)
cards = sorted(
    (
        {k: c[k] for k in fields if k in c}
        for c in rows(cache / "oracle_cards.jsonl.gz")
        if c.get("oracle_id")
    ),
    key=lambda c: c["oracle_id"],
)
for c in cards:
    if c.get("card_faces"):
        c["card_faces"] = [
            {
                k: f[k]
                for k in (
                    "name",
                    "mana_cost",
                    "oracle_text",
                    "type_line",
                    "colors",
                    "power",
                    "toughness",
                    "color_indicator",
                )
                if k in f
            }
            for f in c["card_faces"]
        ]
ids = {c["oracle_id"]: i for i, c in enumerate(cards)}
assert len(ids) == len(cards) > 38000
aliases = collections.defaultdict(set)
prints = []
setcn = collections.defaultdict(set)
languages = collections.Counter()
fixtures = []
seen_fixtures = set()
equivalents = collections.defaultdict(set)
n = 0
for c in rows(cache / "all_cards.jsonl.gz"):
    oid = c.get("oracle_id")
    if oid not in ids:
        continue
    i = ids[oid]
    n += 1
    languages[c.get("lang", "?")] += 1
    prints.append(uuid.UUID(c["id"]).bytes + struct.pack(">I", i))
    setcn[c["set"].lower() + "/" + c["collector_number"].lower()].add(i)
    names = []
    for obj in [c] + c.get("card_faces", []):
        for key in ("name", "printed_name", "flavor_name"):
            if obj.get(key):
                names.append(obj[key])
    if c.get("card_faces"):
        names.append(
            " // ".join(f.get("printed_name", f["name"]) for f in c["card_faces"])
        )
    for name in names:
        aliases[name].add(i)
    if (
        c.get("lang") == "en"
        and c.get("printed_name")
        and c["printed_name"] != cards[i]["name"]
    ):
        equivalents[oid].add(c["printed_name"])
    # Actual printing examples, not hand-authored translations.
    tag = (cards[i]["name"], c.get("lang"), bool(c.get("flavor_name")))
    if (
        cards[i]["name"]
        in (
            "Sylvan Library",
            "Sol Ring",
            "Swords to Plowshares",
            "Lightning Bolt",
            "Rick, Steadfast Leader",
            "Greymond, Avacyn's Stalwart",
            "Godzilla, King of the Monsters",
            "Zilortha, Strength Incarnate",
            "Delver of Secrets // Insectile Aberration",
            "Cecily, Haunted Mage",
        )
        and tag not in seen_fixtures
    ):
        fixtures.append(
            {
                k: c[k]
                for k in (
                    "id",
                    "oracle_id",
                    "name",
                    "printed_name",
                    "flavor_name",
                    "lang",
                    "set",
                    "collector_number",
                    "scryfall_uri",
                    "card_faces",
                )
                if k in c
            }
        )
        seen_fixtures.add(tag)
assert n > 300000 and languages["es"] > 10000 and len(aliases) > 100000
with tempfile.TemporaryDirectory(dir=base) as tmp:
    tmp = pathlib.Path(tmp)

    def gz(name, obj, lines=False):
        data = (
            "\n".join(
                json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in obj
            )
            + "\n"
            if lines
            else json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode()
        (tmp / name).write_bytes(gzip.compress(data, mtime=0))

    gz("oracle.jsonl.gz", cards, True)
    gz("set-collector.json.gz", {k: sorted(v) for k, v in sorted(setcn.items())})

    def norm(s):
        return (
            re.sub(
                r"\s+",
                " ",
                unicodedata.normalize("NFKC", s).replace("’", "'").replace("‘", "'"),
            )
            .strip()
            .lower()
        )

    def fold(s):
        s = unicodedata.normalize("NFKD", norm(s))
        s = (
            "".join(c for c in s if not unicodedata.category(c).startswith("M"))
            .replace("æ", "ae")
            .replace("œ", "oe")
            .replace("ß", "ss")
        )
        return "".join(c for c in s if unicodedata.category(c)[0] in ("L", "N"))

    for filename, fn in [("names-exact.bin.gz", norm), ("names-folded.bin.gz", fold)]:
        entries = collections.defaultdict(set)
        for name, indexes in aliases.items():
            entries[fn(name)].update(indexes)
        content = b"".join(
            key.encode("utf8")
            + b"\t"
            + ",".join(map(str, sorted(value))).encode()
            + b"\n"
            for key, value in sorted(
                entries.items(), key=lambda kv: kv[0].encode("utf8")
            )
        )
        (tmp / filename).write_bytes(gzip.compress(content, mtime=0))

    (tmp / "printings.bin.gz").write_bytes(
        gzip.compress(b"".join(sorted(prints)), mtime=0)
    )
    (tmp / "printing-examples.json").write_text(
        json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n"
    )
    (tmp / "equivalent-names.json").write_text(
        json.dumps(
            {k: sorted(v) for k, v in sorted(equivalents.items())},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    manifest = {
        "version": version,
        "source": "https://scryfall.com/docs/api/bulk-data",
        "updated_at": {
            k: sources[k]["updated_at"] for k in ("oracle_cards", "all_cards")
        },
        "archives": {
            k: {
                "url": sources[k].get("jsonl_download_uri")
                or sources[k]["download_uri"],
                "sha256": sha(cache / (k + ".jsonl.gz")),
            }
            for k in ("oracle_cards", "all_cards")
        },
        "cards": len(cards),
        "printings": n,
        "aliases": len(aliases),
        "languages": dict(sorted(languages.items())),
        "files": {f.name: sha(f) for f in sorted(tmp.iterdir())},
    }
    (tmp / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if dest.exists():
        assert (dest / "manifest.json").read_bytes() == (
            tmp / "manifest.json"
        ).read_bytes(), "Existing version differs; refusing overwrite"
    else:
        os.rename(tmp, dest)
if a.activate:
    pointer = ROOT / "data/active-catalog.json"
    temp = pointer.with_suffix(".tmp")
    temp.write_text(
        json.dumps(
            {"version": version, "manifest_sha256": sha(dest / "manifest.json")},
            indent=2,
        )
        + "\n"
    )
    os.replace(temp, pointer)
print(
    json.dumps(
        {
            "version": version,
            "cards": len(cards),
            "printings": n,
            "aliases": len(aliases),
            "activated": a.activate,
        }
    )
)
