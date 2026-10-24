# W6 — Verification, packaging, submission ledger

Goal: no invalid, unsafe or unmeasured ZIP ever leaves the team.

Pipeline: tapes → `havln_tools.write_submission` (contract checks: coverage, six actions, STOP rules, ≤ 500) → ZIP →
`havln-validate` inside the container → for **val** release candidates: CERT-9 replay (W1 canonical timing ids) → aggregate Score with
`havln_tools.aggregate`; for **test** ZIPs: checks (a)–(d) from the W1 brief only → entry in `RESULTS.md` (git SHA, data fingerprint, metrics per regime, who/when) → upload.

Phase 1 calibration set (`research/C6-*`, if CodaBench returns before Oct 30): STOP-only tape (exact predicted Score), the official CMA export (its CR column reveals which image build runs), our genuine v0 tape, and the same tape resubmitted for scorer noise. Never upload disjoint-subset A/B variants on test (that is probing).

Policies: aggregate metrics only from GT-based replay (no per-episode patching of tapes using GT); compliance manifest per
submission (which inputs the inference used); keep the best-known ZIP always ready; Phase 2 upload #1 = STOP-only anchor.

Tests: the `tests/` suite here (13 passing); container tests nightly (determinism, LOOK no-move, wall-slide count).
Report: `RESULTS.md` ledger and a weekly chart of official vs local Score.
