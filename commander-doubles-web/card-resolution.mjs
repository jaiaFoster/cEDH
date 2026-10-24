import { normalizeName } from "./scoring.mjs";

const fold = (name) => normalizeName(name)
  .normalize("NFKD").replace(/\p{M}/gu, "")
  .replace(/æ/g, "ae").replace(/œ/g, "oe").replace(/ß/g, "ss")
  .replace(/[^\p{L}\p{N}]/gu, "");

// Bounded optimal-string-alignment distance, including adjacent transpositions.
function distance(a, b, limit) {
  if (Math.abs(a.length - b.length) > limit) return limit + 1;
  let previousPrevious, previous = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const row = [i];
    for (let j = 1; j <= b.length; j++) {
      row[j] = Math.min(row[j - 1] + 1, previous[j] + 1,
        previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1])
        row[j] = Math.min(row[j], previousPrevious[j - 2] + 1);
    }
    if (Math.min(...row) > limit) return limit + 1;
    previousPrevious = previous;
    previous = row;
  }
  return previous[b.length];
}

export function createCardResolver(cards, named = {}) {
  const ids = new Map(cards.map((c) => [c.oracle_id, c]));
  const canonical = new Map(), aliases = new Map();
  const add = (map, key, card) => {
    if (!map.has(key)) map.set(key, new Map());
    map.get(key).set(card.oracle_id, card);
  };
  for (const c of cards) {
    add(canonical, normalizeName(c.name), c);
    for (const n of [...c.name.split(" // "), ...(c.card_faces || []).map((f) => f.name)])
      add(aliases, normalizeName(n), c);
  }
  // Explicit interchangeable-name mappings are the only intentional canonical overrides.
  for (const [name, id] of Object.entries(named))
    if (ids.has(id)) canonical.set(normalizeName(name), new Map([[id, ids.get(id)]]));
  const candidates = (key) => {
    const all = [...((canonical.get(key) || aliases.get(key))?.values() || [])];
    // Art/token versions must not make playable face names ambiguous.
    const playable = all.filter((c) => ["legal", "banned"].includes(c.legalities?.commander));
    return playable.length ? playable : all;
  };
  const folded = new Map();
  for (const key of new Set([...canonical.keys(), ...aliases.keys()]))
    for (const card of candidates(key)) add(folded, fold(key), card);
  const byLength = new Map();
  for (const entry of folded) {
    if (!byLength.has(entry[0].length)) byLength.set(entry[0].length, []);
    byLength.get(entry[0].length).push(entry);
  }
  const exact = (name) => {
    const found = candidates(normalizeName(name));
    return found.length === 1 ? found[0] : undefined;
  };
  const cache = new Map();
  function match(name) {
    const key = normalizeName(name);
    if (!key || key.length > 150) throw Error("Unknown or ambiguous card: " + key.slice(0, 150));
    const direct = candidates(key);
    if (direct.length === 1) return { card: direct[0], method: "exact" };
    if (direct.length > 1) return ambiguous(name, direct);
    // A- identifies Arena-rebalanced cards. Never guess away that distinction.
    if (key.startsWith("a-")) throw Error("Unknown or ambiguous card: " + name + ". An Arena-rebalanced name cannot be guessed as a paper card.");
    const k = fold(key), normalized = [...(folded.get(k)?.values() || [])];
    if (normalized.length === 1) return { card: normalized[0], method: "normalized" };
    if (normalized.length > 1) return ambiguous(name, normalized);
    if (cache.has(key)) {
      const cached = cache.get(key);
      if (cached.error) throw Error(cached.error);
      return cached;
    }
    const limit = k.length >= 12 ? 2 : k.length >= 5 ? 1 : 0;
    const ranked = new Map(), searchLimit = limit + 1;
    if (limit) for (let length = k.length - searchLimit; length <= k.length + searchLimit; length++)
      for (const [candidate, cs] of byLength.get(length) || []) {
        const d = distance(k, candidate, searchLimit);
        if (d <= searchLimit) for (const c of cs.values()) {
          const old = ranked.get(c.oracle_id);
          if (!old || d < old.distance) ranked.set(c.oracle_id, { card: c, distance: d });
        }
      }
    const ordered = [...ranked.values()].sort((a, b) => a.distance - b.distance || a.card.name.localeCompare(b.card.name));
    // Never auto-pick when another identity is within one edit of the best match.
    const unique = ordered.length && ordered[0].distance <= limit && (!ordered[1] || ordered[1].distance > ordered[0].distance + 1);
    const result = unique ? { card: ordered[0].card, method: "fuzzy" }
      : { error: failure(name, ordered.map((x) => x.card)) };
    if (cache.size >= 256) cache.clear();
    cache.set(key, result);
    if (result.error) throw Error(result.error);
    return result;
  }
  const failure = (name, cs) => "Unknown or ambiguous card: " + name + (cs.length
    ? ". Please use an exact name: " + cs.slice(0, 5).map((c) => c.name).join("; ")
    : ". Check the spelling or whether this card needs a catalog update.");
  function ambiguous(name, cs) { throw Error(failure(name, cs)); }
  return { exact, match };
}
