# Interactions

`verified/` and `candidate/` per `docs/CHARTER.md` Layer 2 and
`docs/ARCHITECTURE.md`. Files conform to `data/schemas/interaction.schema.json`.

Both are empty — they populate once the subject decklist arrives and the
interaction discovery pass runs (charter section "Interaction discovery
pass"). **Only `verified/` may back a deterministic transition in
simulation; `candidate/` entries are never treated as guaranteed, no matter
how strong their source (including Commander Spellbook) looks.**
