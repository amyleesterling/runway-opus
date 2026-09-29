# Cut archive

| Version | Date | Runtime | Where | Notes |
|---|---|---|---|---|
| v1 — original | 2026-09-29 | 4:33 | commit `291d8be`, `goat/film/THE_GOAT_1080p.mp4` (merged in #1) | first cut |
| v2 — flametastic | 2026-09-29 | 4:33 | commit `6fdbffa`, `goat/film/THE_GOAT_1080p.mp4`; edit script `goat/edit_v2.py` | Runway fire plates, particle fire, credits |
| v3 — re-cut | 2026-09-29 | 1:52 | commit `9c87c16`; edit script `goat/edit_v3.py` | motion-graphics explainer (why the goat exists), 60-goat grid, GNN news package, every clip used once, no new Runway credits spent |
| v4 — myth & reveal | 2026-09-29 | 2:07 | commit `aded2f5`; assets `goat/v4.py` | Norse-myth opening (why a goat), satirical puppet unmasking + Naruto run; 2001 section cut |
| v5 — unmasked | 2026-09-29 | 2:08 | commit `00c62f3`; edit script `goat/edit_v5.py` | continuous unmasking (Hailuo re-mask clip played in reverse); Veo, Seedance 2/2.5, H3 and Gemini Omni all refused the keyframe unmask |
| v6 — narrated | 2026-09-29 | 2:30 | see the commit that adds this row; assets `goat/v6.py` | one Swedish-accented narrator (ElevenLabs v3 + Seed Audio clone after the daily cap), 13 destructions, Santa aims at the goat, more fire; no survival section |

Retrieve an old cut: `git show <commit>:goat/film/THE_GOAT_1080p.mp4 > cut.mp4`

Producer notes on v2 (to fix in v3): too long; the intro never explains why the goat exists; clips repeat;
comedic timing; wants much more motion graphics; mask-pull reveal at the end.
