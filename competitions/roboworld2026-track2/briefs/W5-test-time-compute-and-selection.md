# W5 — Test-time compute: rollouts, self-consistency, verifier

Goal: convert unlimited compute into SR without touching GT.

For each trajectory (3 sibling episodes share the start pose — group with `havln_tools.group_by_path`): run K rollouts (K = 8–32)
varying seed, policy (W4 variants), prompt phrasing, and sweep schedule. For each rollout record the tape, stop position, GPS-detected
contacts, and the agent's own confidence. Selection: discard tapes with any detected contact; cluster stop positions (3 m radius);
pick the largest cluster's medoid tape; tie-break with a success verifier trained on train-split rollouts (features: observations,
program progress, contact count) — never with GT.

If organizers allow sibling-instruction sharing: condition the rollouts on all three instructions (and the public R2R
instruction when matched by start pose + text); otherwise run per episode and only share the executor's map.

Evaluate on val_unseen: SR single-rollout vs K-rollout selection; calibration of the verifier; budget distribution.
Target: +5 SR over single rollout; 0 contacts in selected tapes.
Report: curves SR vs K; selection ablations; compute cost per episode.
