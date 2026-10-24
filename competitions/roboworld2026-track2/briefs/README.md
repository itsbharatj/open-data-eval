# Agent briefs — RoboWorld 2026 Track 2

One brief per workstream. Each is self-contained for a fresh coding agent. Read `../00-competition-facts.md` and
`../01-strategy.md` first. Shared rules for every agent:

1. Red lines (C3 PROHIBITED; never in the inference path, never in a submitted tape): human placements or simulator human state;
   simulator save/restore, step-and-revert or rendering from unreached poses; navmesh, PathFinder, scene mesh, MP3D nav-graph or
   `.house` of test buildings; original R2R / R2R-CE / FGR2R test text; `collision_num_test.json` and HA-VLN-1.0 test humans;
   `sample_room_paths.json` (sha256 d15fe5df…); picking or editing test tapes by local replay outcomes; leaderboard probing; any human
   or coding agent inspecting individual test episodes. Enforcement: import-linter (`agent` must not import `oracle`, `sim.privileged`,
   `habitat`, `habitat_sim`), the runtime file-access audit hook, and the privileged-ablation invariance test (C10 C1–C3). `grep` is not
   a compliance check.
2. Every submission ZIP is validated with `havln_tools.validate_submission_zip` and logged in `RESULTS.md` with the git SHA,
   data fingerprint and local metrics.
3. `val_unseen` (1,839 eps, 11 scans) is the only test proxy; hold out 3 scans for final checks; never tune prompts on test text.
4. Report in the brief's "Report" format; numbers with denominators; failures with the episode ids.
