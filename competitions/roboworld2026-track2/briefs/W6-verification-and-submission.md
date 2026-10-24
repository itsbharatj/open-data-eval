# W6 — Verification, packaging, submission ledger

Goal: no invalid, unsafe or unmeasured ZIP ever leaves the team.

Pipeline: tapes → `havln_tools.write_submission` (contract checks: coverage, six actions, STOP rules, ≤ 500) → ZIP →
`havln-validate` inside the container → local replay under 4 human-timing regimes (W1 scorer) → aggregate Score with
`havln_tools.aggregate` → entry in `RESULTS.md` (git SHA, data fingerprint, metrics per regime, who/when) → upload.

Policies: aggregate metrics only from GT-based replay (no per-episode patching of tapes using GT); compliance manifest per
submission (which inputs the inference used); keep the best-known ZIP always ready; Phase 2 upload #1 = STOP-only anchor.

Tests: the `tests/` suite here (13 passing); container tests nightly (determinism, LOOK no-move, wall-slide count).
Report: `RESULTS.md` ledger and a weekly chart of official vs local Score.
