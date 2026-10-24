# W5 — Test-time compute and selection

## W5-S (default; ships in the clean configuration)
Goal: turn per-step compute into SR inside ONE closed-loop run. Levers (`research/B10` P4–P7, `B5` §7.8, `C8` §7.1):
1. Stop verifier + return-to-best-visited-node. A Qwen3-VL-8B judge P(goal within 3 m | instruction, own keyframes, policy stop
   logit), trained on rollouts of OUR policies on TRAIN scans in 4 scan-disjoint folds. At each STOP proposal compare the current
   node with the visited nodes; if a visited node wins by margin τ, W2 drives back and stops there.
2. Per-step ensemble. Average action/waypoint logits of 3–5 snapshots/seeds of the same architecture; heterogeneous policies vote on
   the next sub-goal position (cluster medoid); the verifier breaks ties. No extra environment steps.
3. Instruction TTA on the episode's own text: raw HA text + condensed route-only paraphrase + ordered sub-instruction list; fuse per step.
4. Uncertainty-gated look-ahead. If the verifier's top-2 margin < τ2 and ≥ 100 actions remain, physically visit the runner-up endpoint
   (≤ 15 m extra travel; skip within 1 m of detected people), then return. All of these actions are in the tape.

Consumes: `Observation/1`, `InstructionProgram/1`, `SubgoalProposal/1` (from each W4 policy). Produces: one fused `SubgoalProposal/1`
(+ stop_belief) for W2, and a `SelectionRecord/1` log.
Never: discarded rollouts; contact information from other runs; sibling instructions; original R2R text; trajectory_id; simulator save/restore.
DoD: paired DEV SR ≥ +3 pp over the best single backbone (trajectory-cluster bootstrap, p < 0.05); verifier ECE ≤ 0.05 on DEV with the
manifest proving train-fold-only training; contact-episode rate not worse by > 0.2 pp; 100 % of tapes ≤ 500 actions with STOP.
Tests: U18 (fusion maths) and U19 (stats) from `research/C10`; S14 rollout determinism with the LLM cache.

## W5-M (flag `rollouts_k`, default OFF; val ablation only until organizer issue item 4 is answered YES in writing)
K = 8–32 rollouts per episode (seeds/policies/prompts). Selection features: stop-cluster support + verifier score over each run's own
observations. Pose-detected contacts are logged but are NOT a feature unless item 4(d) is answered yes. Always report K=1 next to K>1.

## Sibling fusion (flag `sibling_fusion`, default OFF; issue item 6)
Joint conditioning on the 3 HA instructions only. Never the original R2R text (C3 T10). With the flag OFF nothing crosses episodes,
not even the executor's map (that would be cross-episode memory, T07).
