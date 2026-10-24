# Source-linked research artifacts

- `input_audit.json`: hashes of unchanged earlier research and 94 JSONL records.
- `verification_manifest.json`: freshly retrieved official/Oracle/API sources and access notes.
- `rule-index.json`: current edition and valid rule-reference hashes; no full CR text.
- `oracle_evidence.json`:72 selected current Oracle identities/texts/hashes.
- `verification_ledger.json`: per-entry reference/card evidence, generated.
- `public_export.jsonl`:57 curated source-linked entries, generated.
- `review_queue.json`:10 unresolved/rejected/corrected/duplicate candidates.
- `spellbook_*`: successful bulk discovery provenance and unsuccessful sparse attempts.
- `RESEARCH_REPORT.md`: methodology, corrections, coverage, limitations and terms.

The curated `../../data/rulings/entries.json` and `drafts.json` are authored source data. They can be edited in a reviewed code change for future seed additions; **existing deployed entries are never overwritten by seed changes**. Organizer edits live in PostgreSQL with immutable versions. Use the protected export to retain those later versions.

From the application directory:

```sh
node scripts/verify-rulings.mjs          # regenerate ledger + JSONL
node scripts/verify-rulings.mjs --check  # deterministic consistency check
node scripts/fetch-rulings-evidence.mjs # research-only network refresh; writes evidence + /tmp full sources
python3 -m venv /tmp/spellbook-research
/tmp/spellbook-research/bin/pip install ijson
/tmp/spellbook-research/bin/python scripts/research-spellbook.py
```

A refresh updates evidence, not the substantive authored reasoning or published database. Review diffs before regenerating exports. Bulk versions change over time; exact historical reproduction uses the committed selected evidence/curated data, while fresh retrieval is a new source snapshot. No paid API or Python dependency is required for normal web use or deterministic validation. Downloads are bounded by a request timeout; the optional Spellbook scan streams a large gzip through ijson. Only minimal variant identifiers are retained, with credit links.
