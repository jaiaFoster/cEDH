# Controller-checked interaction audit

| id | cards_A | cards_B | status | outcome | rules_citations |
| --- | --- | --- | --- | --- | --- |
| C01 | ['Chain of Smog'] | ['Witherbloom Apprentice'] | verified_cross_team | Repeatable team drain; 30 B-copy triggers drain 60 opponent shared life. | 109.5; 603.2; 707.10; 810.8a; 810.9 |
| C02 | ['Dualcaster Mage'] | ['Twinflame', 'Memnite'] | verified_cross_team | Arbitrarily many hasty Dualcaster tokens controlled by A. | 109.5; 707.10; 707.10c; 805.10 |
| C03 | ['Rest in Peace'] | ['Helm of Obedience'] | verified_cross_team | Empty one opposing library; failed draw eliminates its whole team. | 614.6; 701.17; 704.5b; 810.8a |
| C04 | ['Leyline of the Void'] | ['Helm of Obedience'] | verified_cross_team | Same opposing-library conversion as C03. | 109.5; 614; 704.5b; 810.8a |
| C05 | ['Dauthi Voidwalker'] | ['Helm of Obedience'] | verified_cross_team | Opposing-library conversion, with void counters. | 109.5; 614; 704.5b; 810.8a |
| C06 | ["Painter's Servant"] | ['Grindstone'] | verified_cross_team | Empty targeted library; failed draw wins team game. | 105.3; 614; 704.5b; 810.8a |
| C07 | ['Mindcrank'] | ['Bloodchief Ascension'] | verified_cross_team | Deterministic mill/life-loss chain to opposing team loss. | 603; 109.5; 810.9; 810.8a |
| C08 | ['Drannith Magistrate'] | ['Knowledge Pool'] | verified_cross_team | Opponent hand-spell/nonhand-casting lock; not a total rules lock. | 101.2; 601.2; 805.5; 109.5 |
| C09 | ['Drannith Magistrate'] | ['Possibility Storm'] | verified_cross_team | Opponents' spells from hand are exiled without permitted replacement spell. | 101.2; 601.2; 109.5 |
| C10 | ['Teferi, Mage of Zhalfir'] | ['Knowledge Pool'] | verified_cross_team | Opponent hand-spell timing lock. | 101.2; 117; 601.2; 109.5 |
| C11 | ['Intruder Alarm'] | ['Steward of Solidarity'] | verified_cross_team | Arbitrarily many Warrior tokens; later combat or ETB payoff needed. | 302.6; 701.43a,b; 603; 109.5 |
| C12 | ['Intruder Alarm'] | ['Presence of Gond', 'Llanowar Elves'] | verified_cross_team | Arbitrarily many Elf tokens. | 109.5; 302.6; 603 |
| C13 | ['Eldrazi Displacer'] | ['Peregrine Drake'] | verified_cross_team | Arbitrarily much A mana with appropriate A lands. | 109.5; 603.3a; 810.5; Oracle target up to five lands |
| C14 | ['Bloom Tender'] | ['Freed from the Real'] | false_split_resource_loop | Split setup is finite support, not self-funding infinite mana. | 109.5; 602.2; 810.5 |
| C15 | ['Sanguine Bond'] | ['Exquisite Blood'] | false_split_life_loop | Opponent loss gives B life, which does not trigger A Bond. | 109.5; 603.2; 810.9 |
| C16 | ['Heliod, Sun-Crowned'] | ['Walking Ballista'] | false_split_life_loop | No free self-sustaining counters across split controllers. | 109.5; 702.15; 810.9 |
| C17 | ['Kinnan, Bonder Prodigy'] | ['Basalt Monolith'] | false_split_mana_loop | No extra mana from teammate's Monolith. | 109.5; 810.5 |
| C18 | ["Thassa's Oracle"] | ['Demonic Consultation'] | false_split_library_win | Consultation empties B library while A Oracle checks A library. | 109.5; 810.5; 810.8a |
| C19 | ['Deadeye Navigator'] | ['Peregrine Drake'] | false_split_soulbond | Soulbond cannot pair across controllers. | 702.95a,c; 109.5 |
| C20 | ['Tivit, Seller of Secrets'] | ['Time Sieve'] | false_split_sacrifice | B cannot sacrifice A's Clues/Treasures to B Sieve. | 109.5; 701.21a; 810.5 |
| C21 | ['Pir, Imaginative Rascal'] | ['Toothy, Imaginary Friend'] | verified_team_support | Pir enhances teammate Toothy counters; no automatic infinite draw. | 109.5; 614; 810.5; explicit Oracle team wording |
| C22 | ['Silence'] | ["Thassa's Oracle", 'Demonic Consultation'] | verified_team_support | A protects B's own-library win against both opposing spell casters. | 109.5; 805.5; 810.8a |
| C23 | ['Grand Abolisher'] | ["Thassa's Oracle", 'Demonic Consultation'] | verified_team_support | Shared-turn asymmetric protection supports teammate win. | 805.4; 805.5; 109.5 |
| C24 | ["Angel's Grace"] | ['Heartless Hidetsugu'] | verified_cross_team | At even60 opposing team can take30+30 and lose; friendly cannot-lose applies teamwide. | 810.8a; 810.9; 704.5; 302.6 |
| C25 | ["Teferi's Protection"] | ['Heartless Hidetsugu'] | verified_cross_team | Friendly shared pool cannot change, while B remains available to activate lethal damage. | 810.9h; 810.9; 810.8a |
| C26 | ['Hive Mind'] | ["Summoner's Pact"] | conditional_cross_team | Opponent upkeep losses if either cannot pay; friendly Pact copies also incur debts. | 707.10; 603.7; 805.8; 810.8a |
| C27 | ['Consecrated Sphinx'] | ['Consecrated Sphinx'] | false_friendly_draw_loop | Friendly Sphinx draws do not trigger each other. | 109.5; 810.1; Oracle opponent |
| C28 | ['Notion Thief'] | ['Notion Thief'] | false_friendly_draw_loop | Friendly Thieves do not bounce draws back and forth. | 614; 616.1; 109.5 |
| C29 | ['Dovescape'] | ['Guile'] | false_split_replacement | B Guile does not replace A Dovescape's counter. | 109.5; 603.3a; 614 |
| C30 | ['Isochron Scepter'] | ['Dramatic Reversal'] | false_split_untap | B Reversal untaps only B nonland permanents, not A Scepter. | 109.5; 810.5; Oracle you control |
| C31 | ['Heartbeat of Spring'] | ['Mana Flare'] | verified_team_support | Both friendly players get extra mana, as do opponents; additive extra-mana triggers. | 106; 603; 810.5; Oracle additional mana |
| C32 | ['Laboratory Maniac'] | ['Kenrith, the Returned King'] | verified_cross_team | B pays2U to make A draw from empty library; A's replacement wins friendly team. | 109.5; 810.8a; 614 |
| C33 | ['Narset, Parter of Veils'] | ['Windfall'] | verified_team_support | Both opposing players restricted to at most one draw each shared turn; friendly draw unrestricted. | 109.5; 805.6a; 810.5 |
| C34 | ['Najeela, the Blade-Blossom'] | ['Derevi, Empyrial Tactician'] | conditional_cross_team | B combat-damage triggers can untap A WUBRG lands; A Najeela refreshes both sets of attackers. | 805.8; 109.5; 603 |
| C35 | ['Inalla, Archmage Ritualist'] | ['Spellseeker'] | false_split_eminence | A eminence does not trigger from B's Wizard entering. | 109.5; 603.3a |
| C36 | ["Yuriko, the Tiger's Shadow"] | ['Noxious Revival'] | verified_team_support | B can place an A-owned high-mana-value graveyard card atop A library before A Yuriko trigger resolves. | 109.5; 810.9; Oracle owner's library |
| C37 | ['Platinum Angel'] | ['Pact of Negation'] | verified_team_support | A's cannot-lose protects team from B's unpaid Pact loss. | 810.8a; 603.7 |
| C38 | ["Angel's Grace"] | ['Final Fortune'] | conditional_cross_team | Grace during extra shared turn can prevent B's scheduled loss. | 805.8; 810.8a; 603.7 |
| C39 | ['Seedborn Muse'] | ['Stasis'] | false_skipped_untap | Muse does not untap through a skipped untap step. | 805.8; Oracle instead of each untap step |
| C40 | ['Arcum Dagsson'] | ['Ornithopter'] | verified_cross_team | A Arcum can target B artifact creature; B sacrifices and searches B library for noncreature artifact. | 701.21a; 109.5; 302.6 |
| C41 | ['Coalition Victory'] | ['Transguild Courier'] | false_split_board_aggregation | B's five-color creature does not satisfy A's controlled-creature requirement. | 109.5 |
| C42 | ['High Tide'] | ['Island'] | verified_team_support | B Islands generate extra B mana; opposing Islands also benefit. | 106; 810.5 |

A/B are teammates; C/D opponents. CSV records required state, exact controller split, investment, sequence, disruption, confidence and stable identities. Verified means the stated conditional interaction follows text, not that deck union establishes state or a guaranteed win. No source supplies measured2HG combo win rates.

Rest in Peace A plus Helm B works because replacement is global. X>=1 mills through library without putting cards in graveyard; it still needs failed draw. Bond A plus Blood B does not loop: B gains life, not A. Similarly split Kinnan/Basalt, Oracle/Consultation, Heliod/Ballista, Tivit/Sieve, Deadeye/Drake and friendly Sphinx loops fail. Displacer A plus Drake B CAN work because Drake targets any five lands; B untaps A's mana sources, and returned Drake still belongs to B.

Prior Spellbook union fixture690-3966 is now explicitly a false positive under the ownership split. Prior live API responses are preserved, not silently reclassified as executed games. New variants query was inaccessible through the web tool; no new API response or bulk download is claimed. Reuse official client for permitted queries; do not bulk-export unverified licensed data. See original spellbook_integration_report.md and API docs.
