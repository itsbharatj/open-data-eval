# W4 — Closed-loop policies (compliant) and training data

Goal: the strongest egocentric policy that fits the rules, fine-tuned on HA-R2R train with collision-free experts.

Candidates (see `research/B2-vlnce-sota-2023-2026.md`): SimpleVLN Qwen3.5-9B RL (R2R-CE val unseen SR 76.7, weights public,
served by vLLM, Habitat 0.3.3 eval → build a side-environment or bridge to the 0.1.7 HA scenes with humans inserted);
ETP-R1 (65.3; Habitat 0.1.7-native; needs 12 views → replace cameras with in-place rotation sweeps at decision points and set
`back_algo: control`, no teleport); StreamVLN (56.9; Habitat 0.2.4); NaVILA (54.0). Monocular VLAs are budget-friendly (no sweeps).

Rules: one forward RGB-D camera; panoramas only by TURN actions that go into the tape; GPS+compass allowed; no
`human_motion.json` at inference; pretrained models and external data allowed; no training on val/test.

Training data (allowed): privileged expert = shortest path to the GT goal on a navmesh inflated to radius 0.30 with all 120 human
frames inserted (W1 planning service), converted to actions with the W2 executor logic; DAgger with the student in the loop;
reward for RL = success ∧ zero contacts (GPS-detected). 10,819 train episodes; also ScaleVLN/VLN-CE conversions as extra data.

Integration: policies consume `program.json` (W3) and the executor (W2) is the only thing that emits MOVE_FORWARD. Policies propose
waypoints/sub-goals and STOP; the executor guarantees safety.

Milestones: Nov 3 — one ported policy running closed-loop on val_unseen with the guard: SR ≥ 0.30, TCR ≤ 0.05;
Nov 13 — fine-tuned: SR ≥ 0.45, TCR ≤ 0.02.
Report: val_unseen SR/NE/CR/TCR/Score (challenge metric via `havln_tools`), action-count histogram, GPU-hours used.
