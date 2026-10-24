# W1 — Data, image forensics, replay farm

Goal: a deterministic local scorer that mirrors the official replay, plus a fast planning/rendering service.

Day 1 (no MP3D needed): start the container (`docker run ... --gpus all --shm-size 16g` as in the toolkit README), then dump and
read EVERYTHING under `/opt/havln-challenge/` (scoring package `havln_scoring`, `config/six_action_task.yaml`,
`codabench/phase1/reference/public_reference_manifest.json`, any `havln-score-phase1` CLI) and `/app/config/challenge_submission.yaml`.
Diff the image's habitat-lab/habitat_extensions against the public pinned sources (`prepare_cma_sources.py` revisions). Answer:
- Does the scorer count collisions exactly like `habitat_extensions` Collisions (walls + humans)? (Expected yes.)
- Is DistanceToGoal Euclidean (HASimulator override)? Which measurements/sensors are enabled during replay?
- How are human frames advanced during replay (wall clock? configured FPS?) and is the navmesh cache pre-built?
- Is `collision_num_test.json` referenced by the scorer?
Write the answers to `research/image-forensics.md` with file paths and line numbers.

Two live image builds exist (`research/A8-*`): the toolkit pins `sha256:e1a0544f…` (tag v0.1.0-test-5e9ec54a924c; one 6.1 GB
layer + 10 tiny layers ≈ 49 KB) while the HA-VLN README pins `sha256:78a62cd1…` (tag `cr-domain-20261004`) = the same build plus
one 33 KB layer, probably a change to how CR is computed. Pull BOTH digests, diff the small layers (they most likely hold the
`havln_scoring` package), and record which CR definition each implements; ask the organizers which digest CodaBench runs. The image
also ships `havln-score-phase1 --submission <zip> --output-dir <dir> --gpu-ids …` and `havln-check-environment` (documented in the
toolkit README before the Oct 8 cleanup: `git show 2daf3dd:README.md`); use `havln-score-phase1` as the official-mirror scorer on val.

After MP3D arrives: lay out `scene_datasets/mp3d/<scan>/<scan>.glb`; pre-warm the per-frame navmesh cache
(`recompute_navmesh/<scan>/<scan>_<fff>.navmesh`, 120 per scan; single writer per scan, then mount read-only);
run the CMA export (`scripts/export_cma_submission.py`) and reproduce the README table (SR .129 / Score 12.945 on val_unseen
within SR ±0.01, NE ±0.15, Score ±0.5).

Replay scorer and rollout environment (see `research/A3-*`): expose a FrameScheduler so compliant rollouts run on a virtual human clock that matches the fast official replay (early frames), not the slow wall clock of a VLM agent. Same env construction as the exporter (`HAVLNCEDaggerEnv`, `TASK.SENSORS=[INSTRUCTION_SENSOR]`, measurements
DISTANCE_TO_GOAL, SUCCESS, COLLISIONS) with a pluggable human-frame scheduler: `wallclock`, `frozen(k)` for k in {0, 60, 119},
`fast`, `slow`, and `all-frames` (CPU kinematic check against all 121 navmeshes with the exact `collided` test:
`|filter_end-start|² + 1e-5 < |end-start|²`). Output per-episode CSV + `havln_tools.aggregate` Score. Shard by scan, one long-lived
process per GPU slot; target: full 3,408-episode replay in < 30 min.

**Closed-loop runner + compliant sandbox (Track A; day 1; owner W1; bring-up on the public scene `17DRP5sb8fy` before MP3D).**
API, and nothing else: `reset(episode_id) -> EpisodeInput/1 {episode_id, split, instruction, start_pose{position, rotation_xyzw},
budget: 500}` plus the first `Observation/1`; `step(action) -> Observation/1 {step_idx, rgb uint8[224,224,3], depth float32[256,256,1]
(metres), gps, compass, done}`. No `get_state`/`set_state`, no PathFinder, no `trajectory_id`, no `collided` flag (unless issue item 3
says yes), no sim handles. Isolation and audit: the env-server process alone mounts scenes, episodes, `human_motion.json` and navmesh
caches; the agent runs in a separate container with no data mount; `sys.addaudithook` logs `open`/`listdir`/`connect`, and every
`RolloutRecord/1` carries `inputs_used` and the audit hash; agent state is reset per episode (asserted). The human clock is pluggable
(`gen:wall`, `gen:sps:<S>`, `gen:static`). Production mode: a full split (3,408 test episodes) with fixed seeds and a content-addressed
LLM/VLM response cache; per-episode observation logs so any tape can be regenerated; target ≥ 2,000 resets/h/GPU with a stub agent and a
full K=1 test pass ≤ 24 h wall. DoD: C10 C2/C4/C5 and AT-W1-7 green; a red-team test (open `human_motion.json`, import `habitat_sim`,
read `data/test_*`) fails loudly.

**Canonical human-timing ids** (used by W2, W6 and strategy §12): `wall` official wall clock; `wallx:<s>` throttled; `frz:<k>` frozen at
frame k; `step` frame = step index; `sps:<S>` deterministic schedule at S steps/s; `stall` frame 119 from step 1; `static` no humans;
`allf` kinematic check against all 121 navmeshes (evaluator-only). Generation clocks for local rollouts: `gen:wall`, `gen:sps:<S_est>`,
`gen:static`. **CERT-9** = `frz:0, frz:26, frz:119, step, sps:200, sps:3, stall, static, allf`. Release gate on val (DEV, then lockbox at
gates): contact episodes ≤ 1 % in the generation clock; flips (clean in generation, colliding in any CERT-9 regime) ≤ 0.5 %; TCR spread
< 0.005; worst-regime Score ≥ mean − 0.5; privileged teacher: 0 flagged steps under `allf`. **Test ZIPs**: only (a) `havln_tools` and
in-image `havln-validate` PASS, (b) regenerated from the RC tag with identical sha256, (c) agent fingerprint equals the DEV-certified
fingerprint, (d) only if issue item 8 is answered yes, a pose-trajectory reproduction check with collision columns suppressed. No
collision/TCR number computed on test is printed, logged or used for any decision.

Planning/render service (for W2/W7 and training data): expose PathFinder (find_path, snap_point, is_navigable, try_step,
recompute_navmesh with custom radius and optional inserted humans) and `get_observations_at(pose)` RGB-D rendering with humans at
a chosen frame. Content-addressed cache for renders.

Tests: determinism (same tape → identical final pose + collision count in 3 runs under `frozen(k)`); STOP-only tape → collisions 0,
NE = Euclidean start→goal; LOOK actions do not move the agent; a deliberate wall-slide tape yields exactly the predicted count.

Report: `research/image-forensics.md`, throughput table (steps/s per process, navmesh build time), scorer validation table vs README.
