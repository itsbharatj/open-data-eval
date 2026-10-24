# Agent briefs — RoboWorld 2026 Track 2

One brief per workstream. Each is self-contained for a fresh coding agent. Read `../00-competition-facts.md` and
`../01-strategy.md` first. Shared rules for every agent:

1. Privileged data (scene mesh/navmesh queries, `human_motion.json`, GT goals/paths) lives only in a package named `oracle/`
   and is never imported from inference code. A static check (`grep -r "oracle" agent/`) must return nothing.
2. Every submission ZIP is validated with `havln_tools.validate_submission_zip` and logged in `RESULTS.md` with the git SHA,
   data fingerprint and local metrics.
3. `val_unseen` (1,839 eps, 11 scans) is the only test proxy; hold out 3 scans for final checks; never tune prompts on test text.
4. Report in the brief's "Report" format; numbers with denominators; failures with the episode ids.
