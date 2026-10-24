# W7 — Track B shadow planner, oracle analysis, technical report

Goal: (1) know our ceiling and failure modes with privileged information; (2) have a privileged offline planner ready in case the
organizers explicitly allow it; (3) write the technical report.

Shadow planner (all in `oracle/`): candidate goals from the MP3D connectivity graphs (nodes 3–6 hops, 5–25 m from the start;
graphs for all 90 scans are in the HA-VLN repo), discrete proposers with public checkpoints and precomputed features for the test
scans (ScaleVLN CLIP-H/14 80/70 test, SRDF ~85 SR, NavGPT-2 XXL 71.8, MAGIC-L 77), beam/exhaustive search with speaker reranking,
VLM judge on rendered panoramas, human anchors from category strings, ensemble over sibling instructions; swept-volume navmesh
planner; kinematic verification against all 121 navmeshes. Evaluate goal top-1 within 3 m on val_unseen.

Oracle analysis for Track A: for every Track A failure on val_unseen, classify: wrong goal (which candidate was chosen vs GT),
executor contact, budget, stairs/multi-floor, human-at-start. Feed to W2–W5 weekly.

Technical report: method framed as "socially-safe egocentric navigation with map-free collision guarantees and test-time
self-consistency"; disclose every input used at inference; ablations on val_unseen; reproducibility pack (tapes, seeds, scorer
hashes). Draft by Nov 25.
Report: candidate-set statistics, proposer accuracies, failure taxonomy, report draft.
