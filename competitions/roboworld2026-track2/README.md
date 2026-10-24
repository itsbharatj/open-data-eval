# RoboWorld 2026 · Track 2 (HA-VLN 2.0) — strategy package

Hand-off package for a team of autonomous coding agents. Start here, in this order:

1. `00-competition-facts.md` — verified rules, metrics, timeline, data facts (read first, every agent).
2. `01-strategy.md` — thesis, compliance tiers, two tracks, architecture, workstreams, gates, risks, assets, measurement ladder.
3. `03-organizer-questions.md` — the GitHub issue and private email to send on day 0 (rules clarification is open PR #2; a public R2R
   test-path file exists and must not be used).
4. `briefs/` — one self-contained brief per workstream W0–W7 (inputs, outputs, tests, definition of done).
5. `02-research-digest.md` — one screen per research topic; full reports with evidence in `research/` (33 topics).
6. `havln_tools/` — official Score formula (reproduces the published baseline Scores from integer counts), submission-contract
   validator, trajectory grouping; `tests/` (20 passing: `python3 -m unittest discover -s tests`); `benchmarks/score_landscape.py`.
7. `data/` — test-episode index (scene, start pose, R2R start viewpoint, original instruction for all 3,408 test episodes), per-trajectory
   goal-candidate table with room labels, decoded MP3D test-scan room labels, released collision allowances, val_unseen dev/lockbox splits.
   Everything about the 18 test scans is privileged at inference under the Oct-14 rules: Track B / oracle use only.

Repo hygiene for agents: never import privileged data outside an `oracle/` package; validate every ZIP with `havln_tools`; log every
experiment in `RESULTS.md` with the git SHA and data fingerprint; `val_unseen` is the only test proxy (3 lockbox scans, ≤ 4 looks).
