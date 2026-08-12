**Four-player probe v2** — rerun after the `INFRA-0008` hand-dealing fix.
10 requested (seeds 1-10, skill 10, max turn 8), 8 completed OK, 2 lost to
a chunk timeout (real 4-player hands are dramatically more expensive for
the AI's simulation search — mean 72s/game here vs. v1's ~6-12s — the
last game in each 5-game chunk ran past the 250s chunk timeout). Both
losses are recorded as `status: CHUNK_LOST`, not silently dropped.

0 exceptions, 0 engine errors across all 8 completed games. Per-seat
activity is now much more balanced: 33/41/35/33 total actions across the
4 seats over 6 fully-parsed games (previously 50/25/32/33 across 20 games
with several seats showing zero actions in a given game) — real hands
substantially improve 4-player activity on top of the `skill=10` fix from
`INFRA-0006`'s original investigation. Small sample (n=6-8); a larger
follow-up run would need either a longer per-chunk timeout or smaller
chunks to avoid losing the tail game in each chunk.
