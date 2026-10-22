# Conditional turn demonstrations

Read opening_examples.json for exact own-player seven-card hands, optional additional draws and sequenced costs. These are existence examples, not measured goldfish frequencies. No mulligan simulation or paired game was run.

- G1 can deploy Bloodletter onT2 with Ritual and cast Pox onT3. Both players still face interaction and friendly resource loss. G2 must choose between keeping protection up for this and casting its own Test onT3.
- G2's ordinary3-land/Signet Test line wins onT4 upkeep if>=50 twice. It is invalid if G1 Pox has reduced the pool below50.
- H2 can resolve Aluren onT3 from3lands and mana dorks; H1's own Acererak then supplies a complete repeated-dungeon win. Its own protection resources are specified separately.
- H2 can alternatively deploy Chulane onT3, Aluren onT4 and draw through Drake. Lab Maniac timing is explicitly checked before the library empties.
- I1's illustratedT3 Gitrog/Imp/Dakmor is an engine deployment, not a claimedT3 deterministic kill. A separate fixed-state Woodland/Analyst proof avoids unknown library order.
- I2'sT4 Basalt/Rings requires a fourth land drawn byT4 in addition to its opening7. Starting mana for the first copy activation is explicitly counted.

For mulligans, prefer colored development plus an engine or genuine interaction. Do not keep a nominal two-land hand merely because the total includes colorless utility lands. Coordinate keeps but never transfer cards or mana. Starting team skips its first draw step; none of the7-card-only demonstrations quietly assumes aT1draw.
