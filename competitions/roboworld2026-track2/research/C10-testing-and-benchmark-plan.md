# C10 — Test and benchmark program (compliant closed-loop track first, privileged oracle/teacher tools second)

Topic id: `C10-testing-and-benchmark-plan` · Date: 2026-10-24 · Author: research agent C10
`$PKG` = `/home/user/open-data-eval/competitions/roboworld2026-track2` (read, not modified).
`$BASE` = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`.
Runnable evidence written by this agent: `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/c10/proposed_tests/test_c10_proposed.py`
(15 pure-Python tests against the current `havln_tools`. 8 pass, and 7 fail on purpose to document defects. Run it with `python3 -I -B test_c10_proposed.py -v`, which writes no bytecode into the package.)

Regime tags used below: **[A]** is the compliant closed-loop agent, which is the submission of record. **[P]** is the privileged tools: the DAgger teacher, the oracle-goal executor, Track-B shadow, and GT evaluation. **[X]** applies to both.
Owners use the workstream ids from `$PKG/briefs/`: W0 ops, W1 data/infra, W2 safety executor, W3 perception/grounding, W4 policies, W5 test-time compute/selection, W6 verification/submission, W7 Track B/report.

---

## 0. TL;DR

1. **There are five test levels, and each one gates the next.**
   - L1: pure-Python unit tests, run on every PR, under 90 s.
   - L2: simulator integration tests inside the pinned image, run nightly.
   - L3: benchmarks with expected values in a results ledger.
   - L4: adversarial human-timing replay, which is a release gate.
   - L5: official calibration on CodaBench, plus an official-mirror CLI fallback.
   - A compliance suite (C-series) runs beside these on every PR and every submission, because the audit risk is in the rules, not in the metric.
2. **This review found defects in the shared scorer and tools.** All 15 existing unit tests pass. The new tests in `test_c10_proposed.py` show the following:
   - (a) **Grouping fallback is wrong on real data.** Grouping by start pose gives 788 groups for the 1,136 test trajectories (sizes 3:556, 6:150, 9:55, 12:22, 15:4, 21:1). On val_unseen it gives 393 groups for 613 trajectories, and those merged groups hold 2–5 *different goals*. Episode-id blocks 3k+1..3k+3 equal the trajectory in 613/613 val_unseen and 1,136/1,136 test blocks. **Fix:** use `trajectory_id`, else id blocks, and check pose only as a consistency test. If sibling voting were run on the pose fallback, different-goal trajectories would be merged.
   - (b) **Success is strict `< 3.0` in habitat-lab 0.1.7** (`habitat/tasks/nav/nav.py:535`). `havln_tools` uses `<= 3.0` (`score.py:69`), and `tests/test_score.py:57` asserts SR=1 at exactly 3.0.
   - (c) **Success requires STOP.** `EpisodeResult` has no `stopped` field, so a 500-action tape that ends within 3 m is scored as a success.
   - (d) **Subset CR is wrong.** `aggregate()` divides a subset's colliding-episode count by the *full-split* βL (1,593), so CR on golden sets, held-out scans and per-scan breakdowns is understated by L/n. The test `test_default_cr_mode_is_human_influenced` currently enshrines this.
   - (e) **The contract gate is looser than it should be.** Integer `episode_id` values pass, and symlink ZIP members are not detected and raise `JSONDecodeError`.
   - (e2) **`write_submission` ZIPs are not byte-reproducible.** Two calls 2.2 s apart give different sha256, because the member mtime is stamped.
   - (f) **Already fixed concurrently:** the default `cr_mode` was "all" at 18:46 and is now "human_influenced" (score.py, 19:26). C10's exhaustive integer search confirms βL is the only denominator that rebuilds the published Scores. val_seen (140, 425, 10679) is the unique fit. val_unseen fits (237, 1090, 32248) or (237, 1090, 32249). With CR/L there is no integer fit.
   - (g) **New:** the W2 brief's "known camera height (1.5 m)" contradicts the habitat-lab 0.1.7 default sensor `POSITION [0, 1.25, 0]` (`habitat/config/default.py:227`, also measured by a competitor). A sensor-parity test (S3) must settle this before any depth→occupancy code is trusted.
3. **Container tests can start before the Matterport3D licence arrives.**
   - `17DRP5sb8fy` is Habitat's freely distributed MP3D example scene (`mp3d_example.zip`, used in habitat-sim CI `.circleci/config.yml:325`). It has **10 humans in `human_motion.json` and 75 R2R-CE train episodes** (25 trajectories, 6 episodes with collision_num > 0).
   - `habitat-test-scenes` gives human-free geometry.
   - Together they are the "HA-mini" fixture for every L2 test, including human insertion, regimes and the GPS contact detector.
4. **Compliant-track specifics that the original brief does not cover:**
   - **(i) Rollout-regime × replay-regime cross-product.** A slow VLM agent sees humans frozen at the last refreshed frame. The fast official replay sees early frames. Every compliant tape is therefore replayed under all timing regimes.
   - **(ii) GPS/pose contact detector.** It must use the 3-D displacement and the identical test `|Δ|² + 1e-5 < 0.0625`. Vertical snapping on stairs is never flagged, so a 2-D test gives false positives.
   - **(iii) Privileged-ablation invariance.** With every privileged file removed from the agent process, the tape must be byte-identical.
   - **(iv) Python audit-hook file-access log.** It is attached to the submission manifest.
5. **Calibration plan.**
   - Before Oct 30, if CodaBench returns, use three cheap Phase-1 probes:
     - STOP-only. It is deterministic and must match exactly, and it decides Euclidean vs geodesic: val_unseen proxy Score 8.473 vs 5.042.
     - A one-wall-bump probe. It decides whether walls count and how the allowance is subtracted, and its Score is low, so it does not look suspicious on the leaderboard.
     - Our CMA export, which must fall inside the local regime envelope.
   - Otherwise, use `havln-score-phase1` as the official mirror. In Phase 2 compare only goal-independent metrics (CR/TCR) against local test replay, with no identical resubmissions and no subset probes.

---

## 1. Verified facts that shape the tests

| # | Fact | Evidence | Conf. |
|---|---|---|---|
| F1 | `havln_tools` now has 15 passing unittest tests. `aggregate()` default is `cr_mode="human_influenced"` (changed 19:26). | `python3 -I -m unittest discover -s tests -t .` in `$PKG` → OK. `$PKG/havln_tools/score.py:118` | high |
| F2 | Only CR = Σmin(e,1)/βL rebuilds the published Scores from integer counts. val_seen gives the unique (SR 140/778, CR 425/682, TCR 10679/778). val_unseen gives (237/1839, 1090/1593, 32248 or 32249/1839). CR/L has no solution. All four published Scores (README 16.509450 / 12.945387, organizer re-eval 15.469585 / 11.944822) are reproduced within 1.1e-6. | C10 exhaustive search over rounding intervals; A4 | high |
| F3 | Start pose does not identify a trajectory. Test: 788 pose groups / 1,136 trajectories. val_unseen: 393 / 613, with 152 merged groups holding 2–5 distinct goals. Id block 3k+1..3k+3 = trajectory, 613/613 and 1,136/1,136. | R2R-CE v1-2 mirror `$BASE/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{test,val_unseen}`; A1 | high |
| F4 | habitat Success = `is_stop_called and distance_to_target < SUCCESS_DISTANCE` (strict). `havln_tools` uses `<=`. | `$BASE/habitat-lab-0.1.7/habitat/tasks/nav/nav.py:532-537`; `$PKG/havln_tools/score.py:69`; `$PKG/tests/test_score.py:57` | high |
| F5 | `aggregate()` divides a subset's CR numerator by `HUMAN_INFLUENCED[split]` regardless of n. | `$PKG/havln_tools/score.py:140-143`; proposed `test_subset_cr_is_scale_invariant` fails | high |
| F6 | `check_rows` str()-casts ids (int ids pass). `validate_submission_zip` ignores `external_attr`, so symlinks are not detected. | `$PKG/havln_tools/contract.py:46,86-92`; proposed tests fail | high |
| F7 | Collision flag = 3-D squared-displacement test, EPS 1e-5 (shortening > 2.0e-5 m). Vertical snapping never flags. Turns, LOOKs and STOP never flag. A turn re-snaps an off-mesh agent. | A2 facts 1-6 (habitat-sim `object_controls.py:68-89`) | high |
| F8 | Human frame per step is wall-clock driven (0.1 s ticks, 120 max, freeze at last refreshed frame). Step 1 always refreshes. A deterministic `FrameScheduler` gives the regimes frozen(k), schedule(S) and all-frames. | A2 (corrected 19:34), C1 §3.2; `HASimulator/environments.py:96-147` | high |
| F9 | Exporter env: `get_config('/app/config/challenge_submission.yaml')`, `TASK.SENSORS=[INSTRUCTION_SENSOR]`, `MEASUREMENTS=[]`, `SHUFFLE False`, `SEED 0`, episodes sorted by int, six-action assertion. | `$BASE/track2/scripts/export_cma_submission.py:104-125` | high |
| F10 | Habitat 0.1.7 sensor defaults: `POSITION [0, 1.25, 0]`, HFOV 90, depth `MIN 0 / MAX 10 / NORMALIZE True`. HA-VLN yaml: RGB 224², depth 256². Challenge TILT 30° (competitor in-image measurement). | `$BASE/habitat-lab-0.1.7/habitat/config/default.py:218-241`; `$BASE/HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml`; `$BASE/competitor-bingchengzhang/project/havln_agent/config.py:23,28` | high (defaults) / medium (challenge yaml unread) |
| F11 | If the `DISTANCE_TO_HUMAN` measure is enabled, it restores agent state each step and undoes LOOK tilts. | A2 fact 30; `HASimulator/measures.py:49-97` | high |
| F12 | Free fixture scene `17DRP5sb8fy`: 10 humans in `human_motion.json`, 75 R2R-CE train episodes / 25 trajectories, 6 with collision_num > 0. Distributed as `http://dl.fbaipublicfiles.com/habitat/mp3d_example.zip`. | C10 count; `$BASE/habitat-sim-0.1.7/.circleci/config.yml:325`; `$BASE/habitat-lab-0.1.7/examples/tutorials/nb_python/Habitat_Lab.py:26` | high (data) / medium (licence terms of the example) |
| F13 | val_unseen on the v1-2 proxy: 1,839 eps / 613 traj / 11 scans. Mean Euclidean start→goal 7.467 m. 3.43 % of starts are within 3 m. STOP-only Score 8.473 Euclidean vs 5.042 geodesic (A4). Rotations differ between v1-2 and v1-3 (A1), so v1-2 is a proxy only. | C10 computation; A1; A4 | high |
| F14 | The image ships `havln-validate`, `havln-score-phase1`, `havln-check-data` and `havln-check-environment`. Two live digests exist: `e1a0544f` (toolkit) and `78a62cd1` (cr-domain-20261004, +33 KB layer). Organizers state "repeat runs can differ". | A8 §0, §2.1 | high |
| F15 | CodaBench has been down since Oct 21. Limits are 5 per UTC day and 100 per phase, per user; failed submissions do not count. The owner sees all own scores to 10 dp via the API. Phase-2 close is probably Nov 30 15:59 UTC. | A12 §0 | high / medium (close time) |
| F16 | The organizers' own two CMA evaluations differ by 1.0 Score on val_unseen (12.945 replay vs 11.945 re-eval), so CMA export reproduction needs a loose band. | A4; A8 §2.1 | high |
| F17 | `havln_tools` and `benchmarks/havln_score_ref.py` agree to 1e-10 on random full splits (differential test passes). | proposed `test_matches_reference_aggregator` | high |
| F18 | `havln_tools` parses under the Python 3.8 grammar (`ast.parse(feature_version=(3,8))`). The image runs Python 3.8; no 3.8 interpreter exists here to execute the tests. | C10 check; C1 §1.1 | medium |

---

## 2. Repository layout, markers and CI

```
havln2026/                                   # team code repo (separate from the planning folder $PKG)
  pyproject.toml                             # package metadata; pytest markers; ruff; import-linter contracts
  havln_tools/                               # PURE PYTHON, py3.8-compatible, no numpy required for core
    score.py contract.py grouping.py         # existing (fixes from §3 applied)
    ledger.py manifest.py stats.py fusion.py # new: ledger I/O + schema check; compliance manifest; CIs/bootstrap; fusion/selection math
    schemas/{program,rollout,candidates,ledger_result,ledger_submission,manifest}.schema.json
  synth/                                     # pure-python synthetic world (fixture F-SYN, §4): polygons, kinematics, 2.5-D depth raycaster
  agent/                                     # [A] inference only: perception/ mapping/ executor/ policies/ selection/ io.py (AgentInput)
  oracle/                                    # [P] teacher/, navplan/, trackb/, gt_eval/ — may import anything; never imported by agent/
  sim/                                       # container-only: envfactory.py (exporter-identical), frame_scheduler.py, navstepper.py,
                                             #   replay_scorer.py, rollout_worker.py (agent in separate process), audit.py
  benchmarks/                                # B-xx runners + expected/B-xx.yaml (bands, tolerance, owner)
  tests/
    unit/          # L1, every PR (no marker)
    synth/         # L1, executor/perception logic on the synthetic world, every PR
    compliance/    # C1/C4/C6 static (every PR) + C2/C3/C5/C7 runtime (@pytest.mark.sim, nightly)
    sim/           # L2 @pytest.mark.sim  (container, EGL; HA-mini fixture)
    gpu/           # L2/L3 @pytest.mark.gpu (container + MP3D + GPU)
    official/      # @pytest.mark.official (havln-validate / havln-score-phase1 parity)
    fixtures/      # golden/ (G60 + HA-mini 15), tapes/, synth_scenes/, expected/
  ledger/results.jsonl  ledger/submissions.jsonl  ledger/RESULTS.md (generated, never hand-edited)
  docker/Dockerfile.dev                      # FROM ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f… + pytest/hypothesis/jsonschema
  .github/workflows/pr.yml  nightly.yml  weekly.yml
```

- **PR CI (`pr.yml`, GitHub-hosted, required to merge).** The matrix is Python 3.8 and 3.11.
  - `pip install -e .[test]`, where test = pytest, hypothesis, jsonschema, numpy.
  - `pytest -m "not sim and not gpu and not official" --timeout 120`.
  - `lint-imports`. Contracts: `agent` must not import `oracle`, `sim.privileged`, `habitat`, or `habitat_sim`. Agent code talks to the sim only through `agent/io.py`.
  - `python -m havln_tools.ledger --check ledger/*.jsonl`.
  - `ruff`.
  - Wall-clock budget is 90 s.
- **Nightly (`nightly.yml`, self-hosted GPU runner with Docker and data mounts).**
  - Pull the image by digest and verify the digest.
  - `docker run … pytest -m sim`, then `-m gpu`, then `-m official`.
  - Golden-set regression G60 under frozen(0)/frozen(119)/schedule(20).
  - Adversarial replay (L4) of the current best candidate tape.
  - Benchmark smoke: B0 full, and B2/B3 on 100 episodes.
  - Each result is appended to the ledger. If any metric leaves its band, open an issue tagged with the owner workstream.
- **Weekly and on-demand (`weekly.yml`).** Full val_unseen B1–B7 and the runtime benchmark B8. The holdout scans are used only at gates G7 and G8.

---

## 3. Level 1 — pure-Python unit tests (every PR)

Status key: ✅ exists and passes · 🔧 exists but must change · 🆕 new · ❌ new and currently failing (defect documented in `test_c10_proposed.py`).

| ID | Test | Owner | Definition of done |
|---|---|---|---|
| U1 🔧 | **Score formula exact.** Rebuild all four published Scores from integer counts within 2e-6 (README val_seen 16.509450, val_unseen 12.945387; re-eval 15.469585, 11.944822). Replace the `delta=0.06` / `0.002` tests (`test_score.py:20-34`). | W6 | `test_formula_reproduces_published_scores_to_2e6` merged; 3-decimal rounding test kept only as documentation |
| U2 ✅ | Show that CR/L *cannot* reproduce the published Score (difference > 0.3) | W6 | merged |
| U3 ✅ | Aggregate over synthetic per-episode rows built from the CMA integer counts **with the real `collision_num_{split}.json` allowances** must equal the published Score to 2e-6, in default mode. | W6 | passes (proposed `test_aggregate_*`) |
| U4 ✅ | Differential test: `havln_tools.aggregate` == `benchmarks/havln_score_ref.aggregate` on random full splits (val_seen, val_unseen, test), 1e-10 | W6 | passes today. Then delete one of the two implementations, or keep the second as the oracle |
| U5 ❌ | **Success strictly < 3.0 m** (nav.py:535). Fix `success_geom` to `<` and flip `test_score.py:57`. | W6 | test green |
| U6 ❌ | **Success requires STOP.** Add `stopped: bool` to `EpisodeResult` (default True for back-compat; the replay scorer always fills it). A 500-action, no-STOP row gives SR=0. | W6 + W1 | test green; replay scorer writes `stopped` |
| U7 ❌ | **Subset CR.** For n ≠ L use denominator n·βL/L, and record `cr_mode="human_influenced_scaled"` in the result. Full-split results are unchanged. Fix `test_default_cr_mode_is_human_influenced`, which enshrines 10/1593 for 100 rows. | W6 | subset CR within 0.01 of full CR on uniform data; per-scan tables use scaled CR |
| U8 ✅ | Per-episode adjustment rules: allowance subtraction, CR=min(TCR,1), SR gated by TCR==0 (existing `test_episode_adjustment_rules`) | W6 | kept |
| U9 ✅ | Released baselines: sizes 778/1,839/3,408, non-negative ints. Also pin sha256 of the val files to the toolkit `resources.json` values and record the unpinned test-file sha. | W1 | sha pinned |
| U10 ✅🔧 | **Contract** (existing four tests) plus: 500 without STOP OK; 499 without STOP rejected; string-for-list rejected; duplicate split; `format_version` ≠ 1; extra root file allowed; a JSON without `split` ignored | W6 | all green |
| U11 ❌ | **Strict contract mode** (our gate must be at least as strict as `havln-validate`): reject non-str `episode_id`, symlink/dir/absolute/`..`/backslash members, NaN/Infinity, BOM, duplicate JSON keys, actions with whitespace or lower case, extra per-episode keys (warn) | W6 | proposed tests green; matrix V1–V22 from A8 §7.3 encoded as table-driven test |
| U12 ❌ | `write_submission` determinism: same predictions → byte-identical ZIP (fixed member order, fixed `date_time`, DEFLATE). Verified today: two calls 2.2 s apart give different sha256, because `ZipFile.write` stamps the file mtime. Use `ZipInfo(date_time=(1980,1,1,0,0,0))` + `writestr`. Needed so that G5 (no identical resubmission) and the reproducibility pack can compare by sha. | W6 | sha256 stable across two runs |
| U13 ❌ | **Grouping.** With `trajectory_id`: 1,136×3 on test and 613×3 on val_unseen (passes). Without it: the fallback must use id blocks 3k+1..3k+3 checked by identical scene + start pose, and raise if a block is inconsistent. Fixture: R2R-CE v1-2 files, or the slimmer `$PKG/data/test_episode_index.json`. | W5 (owner of sibling use) + W6 | `test_fallback_without_trajectory_id` green |
| U14 🆕 | **Kinematics mirror** (pure Python, float32, used by `synth/` and by the NavStepper reference):<br>- quaternion `[0, sin(t/2), 0, cos(t/2)]` ↔ yaw t;<br>- MOVE_FORWARD = 0.25 m along body −Z;<br>- TURN = ±15° about +Y with renormalisation; 24 turns return to the start yaw within 1e-5 rad; 500 random turns drift < 1e-4 rad;<br>- LOOK = ±30° pitch, body unchanged;<br>- collided iff `|Δ|²+1e-5 < 0.0625` (3-D): boundary cases at shortening of 1.9e-5 m (not flagged) and 2.1e-5 m (flagged). | W2 | tests green; same module imported by `sim/navstepper.py` (no duplicate maths) |
| U15 🆕 | **GPS/pose contact detector**: same 3-D test as U14. On the `ramp_stairs` synthetic scene, 0 false positives for vertical snapping. Masking case (small horizontal shortening hidden by dy) documented. | W2 | precision = recall = 1.0 on 10⁵ synthetic steps |
| U16 🆕 | **Budget/STOP invariants of the agent wrapper** (property-based, hypothesis): any policy output stream is turned into a tape that passes `check_actions`. STOP appears exactly once and last when length < 500. The reserve logic triggers STOP before step 500 − reserve. Panorama sweeps are counted as TURNs in the tape. | W4 + W2 | 10⁴ hypothesis examples pass |
| U17 🆕 | **Instruction-parser schema** (`program.schema.json`, draft 2020-12):<br>- required `steps[] {verb ∈ closed set, landmark?, direction?, until?}`, `end {region ∈ MP3D region vocabulary (closed list), object?, human_activity?}`, `human_mentions[] {text, role ∈ {start, during, end}}`;<br>- no numeric coordinates allowed (text-only output);<br>- determinism: same instruction + model + prompt hash → identical JSON from cache;<br>- fixtures: 30 hand-written HA-R2R-style instructions (112 words, human sentences), 5 adversarial (empty, 600 words, non-ASCII, two STOP clauses, no human mention). | W3 | all fixtures validate; malformed LLM output → repaired or rejected with typed error, never a crash |
| U18 🆕 | **Fusion/selection maths** (`havln_tools/fusion.py`, hypothesis):<br>- (a) fused candidate probabilities sum to 1;<br>- (b) a ranker with weight 0 has no effect;<br>- (c) invariance to adding a constant to one ranker's logits;<br>- (d) product-of-experts over sibling instructions = sum of log-probs (only if Q2 allows sibling use);<br>- (e) stop-point choice maximises P(‖stop−goal‖ < 3) over the reachable set (brute force on a 5 cm grid, tolerance 1e-9);<br>- (f) self-consistency clustering is permutation-invariant with a deterministic tie-break;<br>- (g) a tape with a GPS-detected contact is never selected when a contact-free alternative exists;<br>- (h) calibration helpers: ECE / Brier on synthetic calibrated data ≈ 0 ± 0.01. | W5 (A), W7 (P) | all green |
| U19 🆕 | **Stats helpers**: Wilson CI, cluster bootstrap by trajectory (3 episodes per cluster), paired McNemar. Checked against closed-form values (SR .5, n 1,839 → ±0.0229). | W6 | green |
| U20 🆕 | **Ledger and manifest schema**: every line of `ledger/*.jsonl` validates. The RESULTS.md generator is idempotent. A manifest with `mode=compliant` cannot list privileged inputs. | W6 | green in CI |
| U21 🆕 | **Python-3.8 guard**: `ast.parse(feature_version=(3,8))` over `havln_tools/`, `agent/io.py`, `sim/`; the CI 3.8 job runs the whole L1 suite | W6 | green on 3.8 |

---

## 4. Fixtures

**F-SYN — synthetic world, pure Python, runs on every PR.** `synth/` implements:
- **Navigable region.** Polygons with holes on a plane. 2.5-D floor heights per polygon (for ramps/stairs of 0.17 m risers within walkableClimb 0.2 m).
- **Kinematics.** Taken from U14.
- **`try_step` with Detour-like sliding.** If the target is outside the region, return the closest boundary point reachable from the start. This approximates `moveAlongSurface(allowSliding=true)`; exactness is checked only in L2 (S8).
- **`is_navigable` and `distance_to_closest_obstacle`.**
- **Depth raycaster.** 256×256, HFOV 90, camera at a configurable height (default 1.25 m until S3 says otherwise), tilt ±30°. Walls are 2.5 m extrusions. Humans are cylinders r 0.25 m, h 1.7 m, with an optional 120-frame trajectory. Output is normalised by 10 m.
- **RGB.** Flat-shaded, with humans in a distinct colour so a trivial "person detector" stub works.

Scene library (each scene ships the expected outcome for the executor):

| Scene | Purpose | Expected (W2 executor with GT goal) |
|---|---|---|
| `corridor_1m` 10 m | centring, heading alignment | 0 contacts; stops < 0.5 m from target; ≤ 60 actions |
| `corridor_0p7m` | tight but passable (navmesh erosion 0.1 m → 0.5 m free) | 0 contacts, with the adaptive inflation step-down logged |
| `door_0p8m`, `door_0p55m` | adaptive inflation; closed door | pass / refuse and re-plan (never bump) |
| `L_turn`, `T_junction` | 15° quantisation drift at corners | 0 contacts |
| `start_inside_human` | rule: first action TURN | action[0] ∈ {TURN_LEFT, TURN_RIGHT}; 0 contacts |
| `human_crossing` (cylinder sweeping 1.2 m over 120 frames) | timing robustness | 0 contacts for frames {0, 60, 119} and the swept union |
| `ramp_stairs` | 3-D contact test, no false positives | GPS detector 0 FP |
| `dead_end`, `far_goal` (needs > 400 actions) | budget reserve, STOP issued | tape ≤ 500, STOP last |
| `unknown_space` | unobserved cells treated as blocked; observe-turns first | no MOVE_FORWARD into cells never seen in depth |
| `cluttered_room_seed{0..9}` | randomised regression | 0 contacts on all seeds |

**F-SIM — free Habitat scenes, container only, available before MP3D approval.**
- `habitat-test-scenes` (van-gogh-room, skokloster-castle, apartment_1): human-free geometry for S5–S8 and S12.
- **HA-mini = `17DRP5sb8fy`** (from `mp3d_example.zip`) plus its 10 humans from `human_motion.json`, the HAPS2_0 assets for their motions, and its 75 HA-R2R train episodes (instructions from the HF train file). This is the first scan to warm the 120-frame navmesh cache and the default scan for every human-related L2 test.
- Licence note (medium): the example scene is distributed publicly by Meta for testing. Still keep it inside the team's MP3D compliance scope.

**F-GOLD — golden regression set.**
- **G60:** 60 val_unseen episodes (20 trajectories × 3) from the *development* scans, stratified: 5 trajectories with a human within 0.5 m of the start, 4 with collision_num > 0, 3 multi-floor/stairs, 3 narrow-door, 5 random.
- Plus 15 HA-mini train episodes (5 trajectories).
- Stored: per-step pose and collision flags for each regime frozen(0)/frozen(119)/schedule(20), the expected aggregate, and sha256s.
- Any diff fails nightly CI (C1 T6).
- **Holdout scans (proposal; C6 owns the final choice):** `oLBMNvg9in8` (177 eps, 13 humans), `X7HyMhZNoso` (141, 8), `EU6Fwq7SyZv` (132, 10) = 450 episodes / 150 trajectories, run only at G7 and G8. Development scans = the other 8 (1,389 eps).

**F-TAPES — canonical tapes** (stored as submission-format JSON plus local expected results):
- STOP-only.
- Our CMA export (val_seen + val_unseen).
- Wall-slide tape: align to a wall, then 20× MOVE_FORWARD.
- Head-on bump tape.
- LOOK-heavy tape: alternating LOOK_UP/DOWN × 100 + STOP.
- 500 × TURN_LEFT without STOP.
- Privileged-teacher tape.
- One-bump calibration tape (K2).

---

## 5. Level 2 — simulator integration tests (pinned image, nightly)

| ID | Test | Regime | Owner | Definition of done |
|---|---|---|---|---|
| S1 | **Image fingerprint.** The pulled digest equals the pin (`e1a0544f…`). Record sha256 of `/app/config/challenge_submission.yaml`, `six_action_task.yaml`, `havln_scoring/**`, `habitat_simulator.py`. Fail on change (detects a Phase-2 image). Run once under `78a62cd1` and archive the diff (cr-domain). | – | W1 | `ledger/fingerprints/<digest>.json` committed; alert path tested |
| S2 | **Env-construction parity.** `sim.envfactory.make_env(split, ids, regime, mode)` → `config.dump()` equals the exporter's config (F9) except a whitelisted diff: `MEASUREMENTS += [DISTANCE_TO_GOAL, SUCCESS, COLLISIONS, COLLISIONS_DETAIL]`, the scheduler, and in rollout mode GPS/compass sensors. `DISTANCE_TO_HUMAN` must be absent (F11). | – | W1 | golden YAML diff = whitelist only |
| S3 | **Sensor parity.** Obs shapes RGB 224×224×3, depth 256×256×1. HFOV 90. Camera height read from config and checked against the rendered floor-plane depth on HA-mini (fit plane → height ±2 cm). LOOK_DOWN changes pitch by the configured TILT (expected 30°). Depth max 10 m normalised. **Write the measured values into `agent/io.py` constants**; this replaces the brief's "1.5 m". | frozen(0) | W1 + W2 | constants file generated from the image; W2/W3 import it |
| S4 | **Measure registry.** `distance_to_goal` resolves to the HASimulator Euclidean class. Success is strict `< 3.0` and requires STOP. Collisions counts `previous_step_collided`. 500 actions without STOP → success 0. | – | W1 | assertions pass in image |
| S5 | **Determinism.** The same tape under frozen(k) for k ∈ {0, 60, 119} and schedule(20) gives byte-identical per-episode rows (final pose to 1e-6, collision step list) across 3 runs, 2 GPUs and 2 worker counts. | R2, R3 | W1 | 0 diffs over G60 + HA-mini |
| S6 | **Action invariants.** LOOK_UP/DOWN never change body position or yaw and never set `collided`. 4× LOOK_UP (120°, no clamp in v1) behaviour is recorded. TURN changes yaw by exactly 15° with `collided` False. STOP ends the episode and clears the flag. Observations change after LOOK. | any | W1 | 10⁴ random actions on HA-mini, 0 violations |
| S7 | **Collision semantics.** The wall-slide tape count equals the NavStepper prediction exactly. A head-on bump flags exactly the steps predicted. The `collision_num` allowance subtraction matches U8 on HA-mini episodes with cn > 0. | frozen(0) | W1 | exact |
| S8 | **NavStepper ↔ Simulator equivalence.** 1,000 random tapes × 3 scans (HA-mini + 2 test-scenes) × frames {0, 60, 119}: identical collision flags; final positions within 1e-4 m. | R2 | W1 | mismatch rate 0; > 0.1 % blocks release |
| S9 | **Human insertion changes the navmesh as expected.** For each human and frame: the human's floor-projected translation is non-navigable on the frame-k navmesh (navigable on base unless already an obstacle). Navigable area drops by 0.1–2.0 m² per human. `.navmesh` is deterministic: rebuilding 3 random frames reproduces the sha. | – | W1 | all humans on HA-mini, then all 72 public scans |
| S10 | **Inflation ⇒ zero collisions.** [P] Routes planned on the swept-volume navmesh (all 120 frames inserted, r = 0.30) and replayed on the official r = 0.1 navmeshes of all 120 frames + base: 0 flagged steps. | R4 | W2 (P-planner) / W1 | 0 flags on ≥ 1,000 HA-mini routes; then on every val_unseen oracle route |
| S11 | **Cache integrity.** Every cached navmesh loads, its sha matches MANIFEST, there are no `.partial` files, and navigable area is within ±5 % of frame 0 (C1 T5). | – | W1 | green nightly |
| S12 | **GPS contact detector parity** [A]. The pose-delta detector (3-D, identical EPS test) equals `previous_step_collided` on ≥ 10⁵ random steps including stairs scans. | R2 | W2 | precision = recall = 1.0 |
| S13 | **Rollout ↔ replay consistency** [A]. The tape executed in a closed-loop rollout, replayed under the same regime, gives identical final pose and collision steps. | R2 | W1 + W4 | 0 diffs on G60 |
| S14 | **Rollout determinism** [A]. With fixed seeds and the VLM/LLM response cache, two rollouts under frozen(k) produce byte-identical tapes. Cache hit rate on rerun is 100 %. | R2 | W4 + W5 | identical sha on G60 |
| S15 | **Official CLI parity.** `havln-score-phase1` vs our scorer: STOP-only tape identical (deterministic); CMA tape per episode within the R0 run-to-run spread; output schema documented. | R0 | W1 + W6 | report in `research/image-forensics.md` |
| S16 | **Validator parity fuzz.** Cases V1–V22 (A8 §7.3) through `havln-validate` and through ours. Every official REJECT is also our REJECT. Every official PASS is our PASS or a documented strict-mode REJECT. | – | W6 | 22/22 consistent |
| S17 | **Phase-2 bundle intake (Oct 30).** Test ids 1..3408 equal `$PKG/data/test_episode_index.json`. Scene and start position match within 1e-4 m (3,408/3,408). `trajectory_id` is present. Instruction count matches. `human_motion.json` covers the 18 test scans (or absence is recorded). `havln-check-data` passes. The test-scan navmesh cache is warmed. | – | W1 + W0 | intake report within 2 h of release |

---

## 6. Level 3 — benchmarks with expected values (ledger-tracked)

Primary benchmark split: val_unseen development scans (1,389 eps). Full val_unseen (1,839) is used for comparison with published numbers, and the holdout (450) only at G7/G8. Regime for headline numbers is schedule(20); the L4 envelope is always reported alongside.

| ID | Benchmark | Mode | Expected / acceptance | Owner | When |
|---|---|---|---|---|---|
| B0 | **STOP-only** | [X] | CR = TCR = 0 exactly. SR = share of Euclidean start→goal < 3 m (v1-2 proxy 0.0343). NE = mean Euclidean (proxy 7.467 m). Score proxy 8.473 val_unseen / 5.667 val_seen (A4). Our scorer = `havln-score-phase1` to 1e-6. | W1 | M2 (Oct 28) |
| B1 | **CMA baseline export** (`export_cma_submission.py`, then replay) | [X] | val_unseen: SR 0.129 ± 0.015, NE 6.39 ± 0.25, CR 0.684 ± 0.04, TCR 17.5 ± 2.5, **Score 12.95 ± 1.0**. val_seen: SR 0.180 ± 0.02, Score 16.51 ± 1.0. The band is ±2 SE on SR, plus the organizers' own 1.0-point spread (F16). Report R0 ×3 and the R2/R3 envelope. | W1 | M2 |
| B2 | **Privileged teacher / oracle-goal executor** (swept navmesh r 0.30, GT goal) | [P] | val_unseen: SR ≥ 0.97; **TCR = CR = 0 in every regime including R4**; mean NE ≤ 1.0 m; 100 % of tapes ≤ 500 with STOP; p99 actions ≤ 400; ≤ 2 s/episode CPU. Train (10,819): SR ≥ 0.97. **Perturbed-start test:** from 1,000 student-like states (lateral offset 0.1–1.0 m, yaw ±45°), a collision-free plan for ≥ 99 % (DAgger label quality). Failures by category: stairs, island, human-at-start, narrow door. | W2 (+W7) | M3 (Oct 29) |
| B3 | **Compliant executor with GT goal** (only privilege = goal xyz; map from depth + pose) | [A]-component | SR ≥ 0.92 (target 0.95 = W2 DoD); TCR ≤ 0.005 and CR ≤ 0.003 across L4 regimes; GPS-detected contacts in ≤ 0.5 % of episodes; failure taxonomy with episode ids | W2 | Nov 1 |
| B4 | **Contact detector** (S12 at scale) | [A]-component | precision = recall = 1.0 on all val_unseen B3 rollouts | W2 | Nov 1 |
| B5 | **Compliant single-rollout agent** (policy + guard, K = 1) | [A] | Nov 3: SR ≥ 0.30, TCR ≤ 0.05. Nov 13: SR ≥ 0.45, TCR ≤ 0.02. Also report OSR (passed within 3 m), stop precision SR/OSR, NE, Score, mean/p95 actions, LLM tokens/episode. | W4 | weekly |
| B6 | **Test-time compute** (K rollouts + selection) | [A] | SR(K) for K ∈ {1, 2, 4, 8, 16, 32}. Oracle-of-K upper bound (strategy v1.1: one of 3 agents within 3 m in 87 %). **Selected SR ≥ SR(1) + 0.05 at K ≤ 16**. Selected tapes 0 detected contacts. Verifier AUROC ≥ 0.80, ECE ≤ 0.05. | W5 | Nov 8 |
| B7 | **End-to-end Score** (dev scans; holdout at gates) | [A] | G6 ≥ 50, G7 ≥ 58 (strategy). The holdout Score must sit inside the dev Score's 95 % cluster-bootstrap CI; otherwise investigate overfitting. | W5 + W6 | G6/G7/G8 |
| B8 | **Runtime** | [X] | Scorer: RGB-D 100–300 steps/s/proc and 2×2-depth 300–800 (C1 estimates, to be measured). NavStepper ≥ 20 k steps/s/core. Full test replay < 30 min on 24 procs. R4 sweep of test < 1 h CPU. Agent: s/episode and GPU-s/episode. **Full-test inference wall ≈ 3,408·K·D·t / P must be ≤ 24 h** (D decisions/episode, t s/decision, P parallel streams; e.g. K 8, D 150, t 1.5 s → 1,704 stream-h → P ≥ 71). | W1 + W4 | M2, then weekly |
| B9 | **Track-B goal inference** (shadow) | [P] | Per ranker on val_unseen: top-1 within 3 m with Wilson CI; recall@{1, 3, 5, 10}; fused top-1 ≈ 0.85 (0.78–0.90; strategy v1.1); stop-medoid gain vs top-1. Never submitted unless the organizers allow it in writing. | W7 | Nov 6 |
| B10 | **Grounding** | [A]-component | Human-mention → detected-person matching P/R ≥ 0.8. End-region accuracy reported. | W3 | Oct 29 |

Statistical rules (W6 enforces them in the ledger):
- Report SR with a Wilson 95 % CI. On 1,839 episodes this is ±0.023 at SR 0.5; on 3,408 it is ±0.017; on the 450 holdout it is ±0.046.
- Compare systems paired, with a cluster bootstrap over trajectories (3 correlated episodes each) and McNemar on episodes. The minimum detectable SR difference on 1,839 episodes at 10 % discordance is 0.021 (5 %: 0.015). On the 450-episode holdout it is about 0.042.
- Adopt a change only if P(ΔScore > 0) ≥ 0.95 on the dev scans.
- Never tune on the holdout or on test text.

---

## 7. Level 4 — adversarial replay (human-timing robustness, release gate)

**Replay regimes** (C1 §3.2 FrameScheduler; A2 rule 8 treats frames as adversarial in [0, 119]):

| Regime | Description |
|---|---|
| R0 | Official class, wall-clock; 3 repeats |
| R1 | Wall-clock with throttling: t_step ∈ {0.01, 0.05, 0.2} s |
| R2 | frozen(k), k ∈ {0, 30, 60, 90, 119} |
| R3 | schedule(S): S ∈ {10, 20, 50, 100, 200} steps/s |
| R4 | All-frames CPU sweep against 121 navmeshes (base + 120 frames); reports the union of flagged steps |

**Rollout regimes [A]:** the compliant agent's rollouts are generated under ρ ∈ {natural wall-clock at agent speed, frozen(0), frozen(119)}. Each resulting tape is replayed under R0–R4. This cross-product is the compliant-track specific part: the agent may have *seen* a human at frame 119 and be *scored* against frame 5.

**Acceptance thresholds (gate G3, applied per candidate submission on full val_unseen and on the test split if test humans are shipped):**

| Quantity (across R0–R3) | Compliant [A] | Privileged [P] | Meaning on val_unseen / test |
|---|---|---|---|
| TCR spread (max − min) | < 0.005 | 0 | < 9.2 / < 17 collision steps in total |
| TCR max | ≤ 0.02 | 0 | |
| CR spread | ≤ 0.002 | 0 | ≤ 3.2 / 5.7 episodes |
| SR spread | ≤ 0.003 | ≤ 0.001 | ≤ 5 / 10 episodes |
| Score spread | ≤ 0.15 | ≤ 0.05 | Score cost of TCR +0.005 and CR +0.002 at SR .6 / NE 2.5 is about 0.05 |
| R4: episodes with any flagged step | ≤ 0.5 % | 0 | "fragile" list reviewed by W2 |
| Rollout-regime spread of SR (ρ) | ≤ 0.01 | n/a | the agent's behaviour must not hinge on which human frame it saw |

- The brief's "TCR variance < 0.005" is implemented as the stricter **spread** criterion.
- One success is worth +0.0435 Score on val_unseen and +0.0235 on test, so these thresholds keep timing noise well below one success.
- If test human placements are not shipped, the test-split L4 run is human-free (walls only). The human margin then relies on B3/L4 results from the val scans, and a "humans unknown" flag goes into the submission manifest.

---

## 8. Level 5 — CodaBench calibration

Phase 1 (val; ends Oct 30, possibly 15:59 UTC). Only if CodaBench is up. Each probe uses 1 of 5 daily slots from the single submitting account.

| ID | Submission | Local prediction | Acceptance / what it decides | Owner |
|---|---|---|---|---|
| K1 | STOP-only ZIP (val_seen + val_unseen) | Exact integers: SR·L, CR = TCR = 0, NE to 1e-6 (API returns 10 dp) | Exact match → scorer, episode set and coordinates identical. NE matching Euclidean (proxy Score 8.473 val_unseen) rather than geodesic (5.042) **settles F-success semantics.** | W6 + W0 |
| K2 | One-wall-bump tape: head-on bump ≥ 3 m from any human, then STOP | TCR = mean(max(0, 1 − cn)) = 718/778 = 0.923 (val_seen) and 1680/1839 = 0.914 (val_unseen). **CR = #(cn = 0)/βL = 718/682 = 1.053 and 1680/1593 = 1.055, so CR > 1 if unclipped.** All values computed exactly locally from the tape (A2 probe A). | Exact → walls count, the allowance is subtracted, and CR is unclipped with an all-episode numerator. CR = 1.000 → the scorer clips. TCR ≈ 0 → the scorer filters to human contacts; then relax wall margins (a strategy change). Low Score, so not a suspicious leaderboard entry. | W6 + W1 |
| K3 | Our CMA export ZIP (the B1 file) | Local R0 ×3 and R1/R3 envelope | Official SR/NE/CR/TCR inside the envelope ± 2 SE. Also compare CR under image `e1a0544f` vs `78a62cd1` locally to identify which build CodaBench runs. | W6 |
| K4 (opt.) | K3 resubmitted identically | – | Measures official run-to-run variance. Allowed in Phase 1 only. | W6 |

Rules:
- **No GT-derived high-scoring val uploads.** They carry no ranking value and look like cheating (B7 lesson 5).
- If CodaBench is still down on Oct 29, run K1–K4 locally through `havln-score-phase1` on an idle machine (×3) and record "official-mirror only" in the ledger.

Phase 2 (test; final ranking):
- **P2-1: STOP-only anchor.** Validates ids, the pipeline and the upload path. CR = TCR = 0 must be exact. NE_stop is recorded.
- **P2-2: first real compliant submission.** CR and TCR do not depend on goals. If test human placements are shipped, the local test replay envelope predicts them. Acceptance: official CR/TCR inside the envelope. SR cannot be predicted, but it must satisfy SR ≤ the local contact-free-and-stopped fraction.
- **Forbidden:**
  - identical resubmissions;
  - subset or toggle probes;
  - choosing per-episode content from earlier test scores (B7, C4).
- **Ledger:** every Phase-2 upload is logged with its predicted envelope, the official 10-dp values and the delta.

---

## 9. Compliance suite (C-series) [A]

| ID | Test | When | Owner | Definition of done |
|---|---|---|---|---|
| C1 | **Static import/path rules.**<br>- import-linter: `agent` must not import `oracle`, `sim.privileged`, `habitat`, `habitat_sim`.<br>- AST/grep denylist of literals in `agent/`: `human_motion`, `.navmesh`, `.house`, `connectivity`, `_gt.json`, `R2R_test`, `test_episode_index`, `test_trajectory_table`, `mp3d_test_scan_room_labels`, `collision_num_` (pending organizer Q7). | every PR | W6 | CI green |
| C2 | **Runtime file-access audit.** The agent runs in its own process with `sys.addaudithook` logging `open`/`os.listdir`/`socket.connect`. Any denylisted path → fail. Network destinations go on an allowlist (VLM endpoints). The log is attached to the manifest. | nightly + per submission | W6 | 0 violations on G60 and on every candidate run |
| C3 | **Privileged-ablation invariance.** Rerun G60 with the agent process's view of the data root stripped: no `human_motion.json`, navmeshes, `.house` files, connectivity graphs, GT files, or the `$PKG/data` test assets. The simulator process keeps them. The tape must be byte-identical (seeds and VLM cache fixed). | nightly + per submission | W6 + W4 | identical sha |
| C4 | **Observation interface.** `AgentInput` exposes exactly {episode_id, instruction, start_pose, step_idx, rgb, depth, gps, compass}. The agent gets numpy arrays only (no sim handles). One forward camera; any panorama is TURN actions present in the tape. | every PR (unit) + nightly | W4 | green |
| C5 | **Budget and camera rules in rollouts.** Tape ≤ 500; LOOK and TURN counted; no extra sensors in the rollout env config (S2 whitelist). | nightly | W1 | green |
| C6 | **Training-data hygiene.** Every training manifest (IL/DAgger/RL buffers, fine-tune sets) contains no val_seen/val_unseen/test episode ids and no val_unseen/test scans. val_seen scans may appear as scenes, but not their episodes. | per training run | W4 | checker passes; manifest sha in ledger |
| C7 | **Submission manifest.** `mode = compliant`; `inputs_used ⊆ {rgb, depth, gps, compass, instruction, episode_id, start_pose}`; consistent with the C2 audit log; generator git sha; image digest; data fingerprint; external APIs listed (for the report's compliance matrix). | per submission | W6 + W7 | gate G2 |

---

## 10. Results ledger and submission gate

`ledger/results.jsonl` holds one record per (run, split/subset, regime). It is written only by `havln_tools.ledger.append()`, which validates `ledger_result.schema.json`:

```json
{"run_id":"01JB…(ULID)","created_at":"2026-10-28T09:12:00Z","owner":"W2/agent-07","benchmark":"B3",
 "git_sha":"abc1234","dirty":false,"config_hash":"sha256:…","image_digest":"sha256:e1a0544f…",
 "data_fingerprint":{"episodes":"sha256:…","collision_num":"sha256:…","human_motion":"sha256:…","navmesh_manifest":"sha256:…"},
 "mode":"compliant|privileged|oracle_goal","split":"val_unseen","subset":{"name":"dev8","n":1389,"ids_sha":"sha256:…"},
 "rollout_regime":"wallclock","replay_regime":"schedule:20",
 "metrics":{"SR":0.512,"SR_ci95":[0.486,0.538],"NE":2.91,"CR":0.004,"TCR":0.006,"Score":50.3,"OSR":0.71,
            "contact_free_rate":0.996,"stopped_rate":1.0,"actions_mean":143,"actions_p95":310,"cr_mode":"human_influenced_scaled"},
 "expected_band":{"SR":[0.45,1.0],"TCR":[0,0.02]},"pass":true,
 "per_episode":{"path":"results/01JB…/val_unseen.parquet","sha256":"…"},
 "runtime":{"wall_s":5120,"gpu_s":30500,"steps_per_s":212,"episodes_per_h":980},
 "parents":["01JA…"],"notes":"guard v3, inflation 0.30/0.6"}
```

Per-episode file columns:
- episode_id, trajectory_id, scan;
- rollout_regime, replay_regime;
- n_actions, n_forward, n_turn, n_look, stopped;
- final_xyz, final_yaw, distance_to_goal, success;
- collisions, collision_steps, collision_num, TCR_ep, CR_ep, SR_ep;
- frames_seen, gps_contacts, wall_s.

`ledger/submissions.jsonl` holds one record per upload:
- zip sha256, phase, CodaBench submission id, upload time (UTC);
- the run_ids it came from;
- predicted envelope (min/max per metric over L4 regimes), official 10-dp metrics, and the delta;
- gate results G1–G6;
- manifest sha.

`ledger/RESULTS.md` is regenerated by CI: one table per benchmark (latest + best + trend) and a chart of official vs local Score.

**Submission gate (W6, all must pass):**
- **G1** contract PASS (ours, strict mode, and `havln-validate`).
- **G2** compliance C1–C7.
- **G3** L4 thresholds.
- **G4** ledger entry with the predicted envelope.
- **G5** zip sha not previously uploaded in Phase 2.
- **G6** human sign-off.

---

## 11. Checklist with owners, dates and definitions of done

| Date | Item | Owner | Done when |
|---|---|---|---|
| Oct 25 | Repo scaffold (§2), PR CI on 3.8 + 3.11, import-linter contract | W6 | PR pipeline green with current 15 tests |
| Oct 25 | Fix U5, U6, U7, U11, U12, U13 (defects above); replace U1 tolerances | W6 (+W5 for U13) | `test_c10_proposed.py` cases green inside the repo suite |
| Oct 25 | U14/U15 kinematics + contact detector; F-SYN scene library v1 | W2 | U14–U16 green; 10 scenes with expected outcomes |
| Oct 26 (M1) | S1–S4, S16 in image (no MP3D needed); constants file from S3 | W1, W6 | fingerprints committed; validator parity 22/22 |
| Oct 26 | HA-mini fixture (17DRP5sb8fy + humans + HAPS assets + 75 eps) in place; navmesh cache warmed for it | W1 | S5–S9, S11, S12 green on HA-mini |
| Oct 27 | C1, C4 static (PR); C2/C3 harness with stub agent | W6 | stub agent passes C2/C3 |
| Oct 27 | U17 parser schema + fixtures; U18 fusion/selection; U19 stats; U20 ledger | W3, W5/W7, W6 | green |
| Oct 28 (M2) | MP3D → B0, B1, S8 at scale, S10, L4 on the CMA tape; G60 golden files frozen | W1, W2 | ledger entries within bands |
| Oct 28–30 | K1–K3 if CodaBench is up; else the official-mirror substitute | W6, W0 | calibration table in ledger |
| Oct 29 (M3) | B2 teacher SR ≥ 0.97, TCR 0 under R4; B10 grounding v1 | W2/W7, W3 | ledger |
| Oct 30 (M4) | S17 bundle intake; test navmesh cache; P2-1 STOP-only anchor through G1–G6 | W1, W0, W6 | intake report; first Phase-2 upload logged |
| Nov 1 | B3 + B4 (compliant executor with GT goal) | W2 | SR ≥ 0.92, TCR ≤ 0.005 |
| Nov 3 | B5 v1; S13/S14 rollout consistency/determinism; C3 with the real agent | W4 | SR ≥ 0.30, TCR ≤ 0.05; C3 identical |
| Nov 6 (G5) | B9 Track-B shadow numbers; first compliant test submission with P2-2 calibration | W7, W6 | ledger |
| Nov 8 | B6 SR(K) curves; verifier calibration | W5 | +0.05 SR at K ≤ 16 |
| Nov 13 (G6) | B5 v2, B7 ≥ 50 on dev | W4, W5 | ledger |
| Nov 20 (G7) | Architecture freeze; holdout run; full L4 on test (if humans shipped); B8 runtime fits 24 h | all, W6 | holdout inside dev CI |
| Nov 27 (G8) | Final candidate through G1–G6; reproducibility pack (tapes, seeds, VLM cache, ledger, fingerprints) | W6, W7 | uploaded and scored ≥ 3 days before close |

---

## 12. Implications

- The scorer library sits under every decision. Exact-integer, differential and semantic tests (U1–U7) are P0. A tolerance of 0.06 hides real bugs, such as the subset CR error.
- The grouping fallback bug would silently merge different-goal trajectories for 51 % of test paths (580 of 1,136 trajectories sit in 232 shared-pose groups). Any sibling-instruction method (W5, Track B) must depend on U13.
- For the compliant agent, the decisive robustness risk is the gap between the human frame the agent *saw* and the frame it is *scored* against. The rollout × replay cross-product (L4) is the only way to measure it locally.
- The GPS/pose contact detector is legitimate and exact if it copies the simulator's 3-D squared-distance test. That makes "contact-free" a selectable property at test time (W5) without GT.
- Container integration work can start immediately on HA-mini and the test scenes. MP3D latency then blocks only the full-scale benchmarks (B0–B3), not the harness.
- Phase-1 calibration may be impossible because of the CodaBench outage. Parity with `havln-score-phase1` (S15) is then the main external anchor. In Phase 2 only goal-independent metrics can be calibrated, and only if test humans are shipped.

## 13. Recommendations (priority order)

1. W6: land the U5/U6/U7/U11/U12/U13 fixes and the exact U1 tests tomorrow. Gate all ledger entries on `havln_tools` ≥ that version (record the version in the ledger).
2. W1: run S1–S4 on day 1 in the image. Generate `agent/io.py` constants (camera height, tilt, depth range) from the image and retire hand-typed values (the 1.5 m in the W2 brief).
3. W1: build HA-mini (17DRP5sb8fy) now and make it the default scan for every L2 test and the nightly smoke.
4. W2: implement `synth/` and the U14–U16 tests before any Habitat work. Share one kinematics module between `synth/`, NavStepper and the contact detector.
5. W6: wire L4 (R0–R4 × rollout regimes) as gate G3, using the thresholds in §7. Never upload a tape that has not passed G1–G6.
6. W6/W0: prepare K1–K3 ZIPs now so they can be uploaded within minutes of CodaBench returning. Otherwise run them through `havln-score-phase1` ×3.
7. W6 + W7: make the compliance suite (C1–C7) part of the reproducibility pack and the technical report's compliance matrix.
8. All: write every benchmark result through the ledger API with expected bands. RESULTS.md is generated, never edited.

## 14. Open questions

- What are the exact values in `/app/config/challenge_submission.yaml`: camera POSITION, TILT, depth range, enabled measurements? (S3/S4.)
- Does `havln_scoring` count all navmesh contacts and use Euclidean distance? Settled by K1/K2, or by reading the source (A8 §7.2).
- Which image digest does CodaBench run (`e1a0544f` vs `78a62cd1` cr-domain)? It affects CR.
- Will the Phase-2 bundle ship test-scan human placements and `trajectory_id`? Without placements, L4 on test is walls-only.
- What does `havln-validate` do with integer ids, symlinks and extra keys? (S16.)
- What is the official grader's step rate? It is only a risk estimate if L4 passes.
- Is `collision_num_test.json` permitted at inference (Q7)? It is denylisted until answered.
- Are the licence terms for `mp3d_example.zip` compatible with team-wide CI use? The team is applying for MP3D access anyway.

## 15. Sources

- `$PKG/havln_tools/{score,contract,grouping}.py`, `$PKG/tests/*`, `$PKG/benchmarks/{score_landscape.py,havln_score_ref.py}`, `$PKG/01-strategy.md` (v1.1), `$PKG/briefs/*.md`, `$PKG/data/{collision_num_*.json,test_episode_index.json}`
- Findings: `C1-infra-and-replay-farm.md` (§3 regimes, §8 throughput, §10 tests), `A2-collision-semantics-habitat017.md` (19:34 version: rules, probes, corrections), `A4-metric-pipeline-and-score-reproduction.json`, `A8-official-toolkit-scorer-and-docker-image.md` (§0, §2, §7), `A12-codabench-platform-mechanics.md` (§0), `A1-episode-format-and-test-split.md`, `B7-competition-case-studies-and-replay-eval-lessons.md` (lessons 5–8, b.6), `C4-leaderboard-feedback-group-testing-math.json`
- `$BASE/habitat-lab-0.1.7/habitat/tasks/nav/nav.py:525-540`, `habitat/config/default.py:214-241`
- `$BASE/habitat-sim-0.1.7/tests/test_navmesh.py`, `.circleci/config.yml:325`, `README.md:195`
- `$BASE/track2/scripts/export_cma_submission.py:95-175`, `$BASE/HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml`
- `$BASE/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`, `$BASE/HA-VLN/Data/HA-R2R-tools/collision_num_train.json`
- `$BASE/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{train,val_unseen,test}/*.json.gz`
- `$BASE/competitor-bingchengzhang/project/havln_agent/config.py:23-28`
- C10 evidence script: `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/c10/proposed_tests/test_c10_proposed.py`
