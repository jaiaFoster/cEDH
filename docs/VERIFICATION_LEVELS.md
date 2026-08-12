# Verification levels

Prompted by a real incident (2026-08-12): `INT-0012` was initially recorded
as fully Level 4 "verified" on the strength of (a) solid Comprehensive
Rules citations for the copy mechanism, plus (b) an executable-engine test
that reproduced a *downstream consequence* of the interaction (two literal
Birthing Pod permanents, each independently activatable) rather than the
interaction's own stated transition (Clever Impersonator entering, choosing
to copy Birthing Pod, and becoming a functioning second Pod). User review
caught that these are not the same evidentiary strength, and that
`status: verified` alone doesn't distinguish them. This document formalizes
the distinction as a permanent taxonomy so it doesn't have to be
re-litigated per interaction.

This is a refinement of `docs/CHARTER.md`'s Level 4 exact-line validation
concept, not a replacement for it. `status: candidate` / `status: verified`
in `interactions/*.json` still governs which directory a record lives in
and remains the coarse gate. `verification_level` is the fine-grained field
*inside* a `status: verified` record that states exactly what kind of
evidence backs it.

## The four levels

| Level | What it means | Engine reproduces |
|---|---|---|
| `RULES_VERIFIED` | Comprehensive Rules / Oracle citations establish the interaction is legal and behaves as described. No executable-engine reproduction exists (or was attempted) for any part of it. | Nothing |
| `ENGINE_COMPONENT_VERIFIED` | Rules-verified, **and** at least one necessary sub-transition or downstream consequence of the interaction has been reproduced in an executable engine — but the exact, full transition chain named by the interaction (start to stated result) has not been reproduced end-to-end in one continuous engine run. | A component or consequence, not the full named transition |
| `ENGINE_EXACT_VERIFIED` | Rules-verified, **and** the exact interaction as described — from its stated `prerequisites` through its stated `result` — has been reproduced start-to-finish in a single executable-engine run. This is the charter's original Level 4 standard. | The full named transition, end-to-end |
| `CONDITIONAL` | Verified (at whichever engine tier) only under stated conditions or assumptions that may not always hold in an actual game — most commonly, a required opponent choice (e.g. declining to pay a tax) that this deck does not control. The conditionality must be stated explicitly in `prerequisites.other` or `result.summary`, not left implicit. | Varies; state the engine tier achieved *under* the stated condition |

`RULES_VERIFIED` alone is a legitimate, useful tier — not a lesser or
provisional state. Some interactions (most obviously ones where an
executable-engine substrate doesn't yet exist for every relevant card, or
where the rules question is unambiguous enough that engine reproduction
would only confirm what CR citations already settle) may reasonably stay at
`RULES_VERIFIED` for a long time. What matters is that the field states
plainly which kind of confidence exists, not that everything eventually
reaches `ENGINE_EXACT_VERIFIED`.

## What this changes about "only `interactions/verified/` may be used as
deterministic transitions" (charter non-negotiable rule 1)

That rule still holds at the directory level — `interactions/candidate/`
entries are never usable. Within `interactions/verified/`, the
`verification_level` field now governs *how* an entry may be used:

- **`ENGINE_EXACT_VERIFIED`** may be hardcoded as a fixed hop in a native
  (non-engine-driven) state tracker, exactly as the charter originally
  intended for Level 4 — the interaction's own transition has itself been
  proven to execute correctly, not just something adjacent to it.
- **`ENGINE_COMPONENT_VERIFIED`** may inform an *engine-driven* simulation
  (one where XMage or Forge itself plays out the actual cards, e.g. Clever
  Impersonator really entering and really choosing to copy something) — in
  that mode the real engine handles the untested exact transition live, so
  the gap this tier flags doesn't propagate into the simulation's output.
  It must **not** be hardcoded as a fixed outcome in a native/lightweight
  tracker that would otherwise skip actually resolving the copy — doing so
  would silently promote a rules-verified-plus-component-tested claim into
  an exact-transition claim it hasn't earned.
- **`RULES_VERIFIED`** alone (no engine evidence at all) should be treated
  the same way as `ENGINE_COMPONENT_VERIFIED` for this purpose: safe to
  inform an engine-driven simulation, not safe to hardcode into a native
  tracker without further work.
- **`CONDITIONAL`** entries may be used only when the simulation can itself
  represent the stated condition (e.g. an actual opponent-choice model that
  may or may not satisfy it) — never as an unconditional deterministic hop.

## Where the field lives

`verification_level` is a required sibling of `verification` on any
`status: verified` record in `data/schemas/interaction.schema.json`.
`verification.executable_engine_check` additionally carries an
`exact_reproduction` boolean: `true` only if that specific engine run
reproduced the interaction's full stated transition end-to-end (the
`ENGINE_EXACT_VERIFIED` case); `false` if it reproduced a component or
downstream consequence instead (the `ENGINE_COMPONENT_VERIFIED` case). This
keeps the distinction machine-checkable, not just prose in `notes`.

## Retroactive classification (2026-08-12)

Every interaction promoted to `interactions/verified/` before this document
existed was reviewed and classified:

| ID | Level | Why |
|---|---|---|
| `INT-0002` | `ENGINE_EXACT_VERIFIED` | The exact Devoted Druid + Swift Reconfiguration loop was reproduced end-to-end. |
| `INT-0007` | `ENGINE_EXACT_VERIFIED` | The exact doubled Orcish Bowmasters trigger (casting it, both instances resolving) was reproduced end-to-end. |
| `INT-0008` | `ENGINE_EXACT_VERIFIED` | The exact doubled Esper Sentinel trigger (casting the opposing spell, both pay-or-decline instances) was reproduced end-to-end. |
| `INT-0009` | `ENGINE_EXACT_VERIFIED` | The exact doubled Runic Armasaur trigger was reproduced end-to-end. |
| `INT-0010` | `ENGINE_EXACT_VERIFIED` | The exact doubled Spellseeker ETB (casting it, both independently-targeted searches) was reproduced end-to-end. |
| `INT-0011` | `ENGINE_EXACT_VERIFIED` | *For the single-attacker case only* (as the record's `result.summary` explicitly scopes it) — that exact sequence (tap Cradle, attack, trigger, untap, retap) was reproduced end-to-end. The multi-attacker scaling extension is untested and intentionally excluded from this record's claim (`coverage_backlog` `SIM-0012`). |
| `INT-0012` | `ENGINE_COMPONENT_VERIFIED` | The copy mechanism (Clever Impersonator entering, choosing to copy Birthing Pod) was **not** reproduced — an XMage harness limitation (cost-payment choices for that `activateAbility()` call shape route through an internal AI fallback, not test commands) prevented a stable fixture. What *was* reproduced end-to-end is the downstream consequence: two Birthing-Pod-functioning permanents can each be independently activated in one turn. Rules-verified via CR 707.1/707.2 that a copy acquires the original's activated abilities and card types. |
| `INT-0013` | `ENGINE_EXACT_VERIFIED` | The exact doubled Kinnan trigger (tap a nonland source, both instances) was reproduced end-to-end for both the 1-mana and 2-mana cases. |
| `INT-0014` | `ENGINE_EXACT_VERIFIED` | The exact doubled Archivist of Oghma trigger was reproduced end-to-end. |

So, depending on how the count is framed: **8 of 9** `interactions/verified/`
entries are `ENGINE_EXACT_VERIFIED`; **1** (`INT-0012`) is
`ENGINE_COMPONENT_VERIFIED`. Both are legitimately `status: verified` —
`ENGINE_COMPONENT_VERIFIED` is not a lesser directory placement, it's a
precisely-labeled evidentiary tier within the same directory, exactly
matching this document's design.
