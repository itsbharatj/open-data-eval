# C6 — Experiment design and validation protocol (primary track: compliant closed-loop agent)

Topic id: `C6-experiment-design-and-val-protocol` · Date: 2026-10-24 · Author: research agent C6

**Regime.** Unless marked otherwise, everything here assumes **Track A**: the compliant closed-loop agent. Its inputs are the instruction, the start pose, GPS+compass, and forward RGB-D only. It may run many local rollouts and pick one by self-consistency. Privileged information (GT goals, reference paths, navmesh, scene mesh, `human_motion.json`) appears only in two places: (a) the **evaluator**, and (b) **oracle arms that are explicitly labeled** and never submitted. Track B (the privileged planner) figures only as a reference ceiling.

**Paths.**
- `S=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad`.
- Scripts written for this topic:
  - `S/c6work/val_strata.py` (per-scan and per-stratum statistics)
  - `S/c6work/power.py` (clustering, power, best-of-N, ECE noise)
  - `S/c6work/lockbox.py` (lockbox choice, val→test error)
  - `S/c6work/splits_and_targets.py` (ID lists, Score predictions)
- Materialized split file: `S/c6work/c6_splits_val_unseen.json`. All scripts run with `python3 -I`, and only public JSON was read.

**Inputs consumed.**
- Findings: A4 (metric/CR formula), A2 (collision semantics), A3 (animation timing), A8 (scorer/image), B2 (vln-safe clean-SR numbers), B4 (agreement as calibration), B7 (noise, no probing), C3 (rules), C4 (feedback channel).
- The current `01-strategy.md`, which I did not modify.
- WebSearch was not used; its budget was exhausted.

---

## 0. Summary: the ten protocol decisions

1. **Measure a 9-stage ladder, not a single number.** The ladder runs L0 to L8:
   - L0: STOP-only
   - L1: CMA replay
   - L2: privileged oracle executor
   - L3: **compliant executor given the GT goal point**
   - L5: single compliant rollout
   - L6: union-oracle over K rollouts
   - L7: K-rollout plus compliant selection
   - L8: worst human-timing regime

   The differences between stages split the deficit into four parts: **perception tax** (L2−L3), **goal finding** (L3−L6), **selection loss** (L6−L7) and **timing robustness** (L7−L8). Privileged data lives only in the evaluator and in the labeled oracle arms L2, L3 and L6. All of this is in §3.
2. **Splits (materialized, trajectory-level, deterministic).**
   - **dev** = 8 val_unseen scans, 1,413 episodes / 471 trajectories.
   - **lockbox** = 3 scans {8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX}, 426 episodes / 142 trajectories (23.2%). They were chosen to match val_unseen on floor change (15.5% vs 14.2%), path length (9.5 vs 8.9 m), humans on the reference path (62% vs 52%), collision_num>0 (7.7% vs 8.6%) and Airbert difficulty (0.676 vs 0.669). The lockbox gets **at most 4 logged looks**.
   - **quick** = 306 episodes (102 stratified dev trajectories).
   - **smoke** = 60 episodes.
   - Anything that is *fitted* (verifier, calibrator, fusion weights, thresholds tuned by optimization) is fitted on **cross-fitted train-scan folds**, never on val. See §2.
3. **Statistics: paired, cluster-aware comparisons.**
   - Clustering measured on real per-episode outcomes (Airbert vs VLN-BERT on the same R2R-CE val_unseen episodes): trajectory ICC 0.235 (design effect 1.47), scan ICC 0.032, and paired-difference SE inflated ×1.14 by trajectory clustering.
   - Single-system 95% CI on val_unseen SR: ±2.8 pp (clustered).
   - Paired MDE at 80% power on val_unseen: **1.1 / 1.7 / 2.4 / 3.3 pp** at **2 / 5 / 10 / 20%** discordance.
   - **Absolute val→test SR prediction carries a ±8 pp 95% interval** from building heterogeneity alone. Gains transfer much better than absolute levels. See §8.
4. **K = 1 must stand alone as the strict submission.** Selecting among K rollouts uses observations from rollouts that are not in the submitted tape. C3 classes that as "simulator branching" (gray; ask the organizers), and R2R leaderboards report it as a separate "beam search" setting.
   - Every milestone therefore reports K=1 strict next to K>1.
   - The K-scaling curve quantifies what is at stake in the organizer question.
   - Literature selection efficiency η = (selected − single)/(oracle − single) is 0.17–0.32 (FAST 0.17, VLN-BERT vote 0.26, Airbert vote 0.32). Plan for η ≈ 0.3 and treat η ≥ 0.5 as excellent.
5. **Robustness reduces to one question: did human timing differ?**
   - The agent can reproduce Habitat's collision predicate exactly from its 3-D GPS displacement (flagged iff |Δp|² + 1e-5 < 0.0625; A2). A tape with zero detected contacts in local generation is therefore wall-collision-free in official replay by construction. The only residual risks are human-frame mismatch, cross-frame navmesh drift and start re-snapping.
   - A3 shows that fast official replay sits in human frames ~0–26, while a slow local agent sees frames up to ~110–119. Only ~8% of val_unseen episodes (147/1,839) are timing-sensitive.
   - Protocol: generate under G ∈ {wall, virtual-fast, no-humans}, and replay under 9 regimes R0…Rall.
   - Acceptance: **flips ≤ 0.5% of episodes**, worst-regime Score within 0.5 of the mean, and 100% agreement between agent-detected contacts and simulator collisions in the generation regime. See §6.
6. **Phase 1 calibration (must finish by Oct 30; CodaBench has been down since Oct 21).** Four submissions, all with exact predictions and none GT-derived:
   - P1 STOP-only: val_unseen **Score 8.473053**, SR 63/1839, NE 7.466760; val_seen 5.667176. If NE were geodesic, about 5.04.
   - P2 official CMA export: **12.945387** if CR = C/βL vs **13.289348** if C/L. The displayed CR column reads 0.684 vs 0.593, which **settles which of the two image builds CodaBench runs** (A8 found a `cr-domain-20261004` build).
   - P3: our genuine v0 agent tape.
   - P4: P3 resubmitted, to measure scorer nondeterminism (legitimate in Phase 1 only).

   Fallback if CodaBench stays down: run `havln-score-phase1` from the image on the same ZIPs. See §7.
7. **Calibration is a first-class deliverable.**
   - The selector emits p̂ = P(clean success).
   - Report a reliability diagram, ECE, Brier score, the risk–coverage curve and agreement buckets.
   - ECE noise floor for a *perfectly* calibrated predictor: 0.024 at n = 1,839 and 0.042 at n = 613 trajectories. So dev ECE ≤ 0.035 means "calibrated".
   - A calibrated p̂ gives a **label-free estimate of test SR** (mean p̂ on test) and a covariate-shift alarm. Both are legitimate because they use no test labels or feedback.
8. **Leakage controls with automated tests.**
   - Inference firewall: separate process; the observation whitelist is {rgb, depth, gps, compass, instruction, episode_id, start_pose, step}; the info dict is stripped; file opens are audited.
   - **Goal-poisoning test**: move val goals by 100 m and the generated tapes must be bit-identical.
   - Grep test: no test-instruction text in any prompt or few-shot file.
   - No reading of test instructions by people.
   - Lockbox look budget.
   - No Phase-2 per-subset selection. This **rejects C2's "disjoint-subset A/B" submission plan**.
   - One account; ≤ 20–30 Phase-2 uploads.
9. **One record format for every experiment.** Each run writes a manifest with a sha256 fingerprint over code, config, checkpoints, prompts, LLM ids, docker digest, data hashes, regime and seeds. It also stores integer counts (k, C, Σe, L, βL) alongside the floats, cluster-bootstrap CIs, a per-regime block, a per-stratum block, a calibration block, a cost block and a 50-column per-episode table. Records go to an append-only ledger, plus 11 dashboards. See §10–11.
10. **What a healthy project looks like (Track A, dev, inference; medium/low confidence).**

| Stage | Target |
|---|---|
| L0 STOP-only | exact (8.473) |
| L1 CMA replay | 12.945 ± 0.3 |
| L2 privileged oracle executor | SR 0.97–0.995, all-regime TCR 0, Score ≈ 93–96 |
| **L3 compliant executor + GT goal** | clean SR ≥ 0.90 (Nov 1) → ≥ 0.94 (Nov 13), contact episodes ≤ 3% → ≤ 1% |
| L5 K=1 strict | raw SR 0.55–0.68, **clean SR 0.50–0.62** |
| L6 union K=8 | 0.72–0.85 |
| L7 K-selection | **0.58–0.70** |
| L8 flips | ≤ 0.5% |
| Final dev Score (K=1 strict) | **53–60** |
| Final dev Score (gated K) | **60–66** |

   Expected test Score = dev − 0…3 points, with a ±6.5-point 95% interval from building effects. The brief's numbers (goal top-1 0.65→0.85, Score 70–85) describe Track B, which is not the submission of record.

---

## 1. Data-access matrix: what may touch what

| Item | Track-A inference (agent process) | Training (train split only) | Evaluator / labeled oracle arms |
|---|---|---|---|
| Instruction, episode id, start pose | yes | yes | yes |
| GPS+compass (3-D position, heading) | yes (Q9) | yes | yes |
| Forward RGB-D (224² RGB / 256² depth, HFOV 90; `HAVLNCE_R2R_task.yaml` L17-24) | yes; panoramas only by counted turns (Q8) | yes | yes |
| Contact derived from GPS delta | yes (exact predicate; see §6) | yes | yes |
| `previous_step_collided`, `info{distance_to_goal, success, collisions}` | **no** (C3 T2b) | yes | yes |
| GT goal, reference path, `*_gt.json` | **no** | yes (labels, DAgger teacher) | yes (L2/L3/L6 oracle arms) |
| Navmesh, scene mesh, pathfinder, top-down map | **no** (C3 T2d) | yes (teacher, data generation) | yes (L2, regime certificate, attribution) |
| `human_motion.json` | **no** (Q11; it is used only by the *renderer*) | yes (privileged supervision; Q11) | yes (regimes, wall/human attribution) |
| Sibling instructions of the same trajectory | gated: measured as arm AB8, not submitted until allowed | yes | yes |
| R2R_test.json originals, HA-VLN-1.0 test human annotations, test connectivity | **never** (C3 red lines T8/T9) | no | no (quarantined, not mounted) |
| collision_num (public) | no | yes | yes (official TCR adjustment) |
| HA-R2R val_seen / val_unseen / test episodes | inference only | **never** (Q10) | val: evaluation only |
| Phase-2 official scores | no per-episode or per-subset use | no | whole-system variant choice only (≤ 20–30 uploads) |

Enforcement:
- The simulator runs in an **env server** process that holds the data mounts.
- The agent runs in a separate container. It has no MP3D/HA data mount and talks to the env server over a JSON/shm socket that carries only whitelisted keys.
- Every `open()` in the agent container is audit-logged, and the log hash goes into the experiment manifest.
- The env-server measurement list must equal the scorer's. Do **not** enable `DISTANCE_TO_HUMAN`: it executes and undoes a MOVE_FORWARD every step and resets camera tilt, so a generation run with it would see different LOOK observations than the replay (A2 fact 25).

---

## 2. Splits (val_unseen = the only test proxy; 11 unseen scans, 613 trajectories)

Materialized in `S/c6work/c6_splits_val_unseen.json` (seed 20261024). Selection is at the trajectory level, so the 3 instructions of a trajectory are never split across subsets.

| Split | Scans | Episodes / traj | Floor change >1 m | Mean geodesic | Human ≤1 m of ref path | collision_num>0 | STOP-only SR / NE | Use |
|---|---|---|---|---|---|---|---|---|
| val_unseen (all) | 11 | 1,839 / 613 | 14.2% | 8.90 m | 52.0% | 8.6% | .0343 / 7.467 | Phase-1 calibration only |
| **dev** | 8 | **1,413 / 471** | 13.8% | 8.71 m | 49.0% | 8.9% | .0403 / 7.225 | all model selection |
| **lockbox** | 8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX | **426 / 142** | 15.5% | 9.52 m | 62.0% | 7.7% | .0141 / 8.268 | ≤4 logged looks: G5, G6, G7, final |
| quick | 8 (dev) | 306 / 102 | 15.7% | 8.60 m | 49.0% | 6.9% | .0392 / 7.248 | daily iteration; detects only effects ≥4–6 pp |
| smoke | 7 (dev) | 60 / 20 | 25.0% | 8.29 m | 55.0% | 10.0% | .05 / 6.61 | CI on every PR; crash and contract checks only |
| val_seen | 53 (train scans) | 778 / 259 (incl. the 4-instruction traj, ids 64–67) | 5.8% | 9.58 m | — | 7.7% | .0039 / 8.197 | seen–unseen gap (scene memorization alarm) |
| train folds | 61 scans → 2 scan-disjoint folds (+6 folds for small fitted models) | 10,819 | — | — | — | — | — | cross-fitting of verifier, calibrator, fusion |

**Per-scan heterogeneity is large.** Floor-change share ranges 0–57.6%: oLBMNvg9in8 57.6%, 8194nk5LbLH 53.8%, EU6Fwq7SyZv 34.1%, and five scans 0%. Airbert SR ranges 0.33–0.80 across scans. The lockbox therefore deliberately contains two multi-floor buildings and one long-path building. The dev split keeps oLBMNvg9in8, the hardest multi-floor scan, for development.

**Cross-fitting rule** (it avoids training the selector on val and avoids in-sample policy rollouts):
- Fine-tune the policy twice, on train fold A and on train fold B.
- Generate verifier and selector training rollouts on the *opposite* fold.
- Train the verifier and calibrator on those out-of-fold rollouts.
- The submitted policy is trained on all of train.
- Evaluate everything on dev.

This roughly doubles fine-tune cost but is the only way to get an unbiased p̂. B3 proposes fitting the calibrator on val_unseen; that conflicts with Q10 and B4 (§13).

Dev-strata sizes (counts in dev):

| Stratum | Counts |
|---|---|
| Geodesic length, m (<7 / 7–9 / 9–11 / 11–14 / ≥14) | 396 / 465 / 306 / 186 / 60 |
| Floor change | 195 |
| Humans ≤1 m of reference path (0 / 1 / 2 / 3+) | 720 / 351 / 129 / 213 |
| Human ≤3 m of goal | 765 |
| Human ≤1 m of start | 192 |
| collision_num>0 | 126 |

---

## 3. The experiment ladder (Track A) and expected numbers

All rows are scored on dev unless noted. Score always uses the official aggregation: SR, NE and TCR over L; CR = #episodes with e ≥ 1 over βL, where βL = 1,593 for val_unseen and dev uses 1,413·(1593/1839) = 1,224. Report the integer counts with every row.

| Id | Arm (privileged parts) | What it isolates | Healthy target | Red flag | Confidence |
|---|---|---|---|---|---|
| L0 | STOP-only tape (none) | coordinates, distance definition, coverage, scorer wiring | val_unseen exact: k = 63, SR .034258, NE 7.466760, CR = TCR = 0, **Score 8.473053**; val_seen 3/778, 8.196761, **5.667176** | any deviation > 1e-6 | high |
| L1 | Official CMA export replay (none) | replay harness parity, wall-clock noise | 237/1839, C = 1090, TCR 17.54, Score 12.945387 (±5 episodes, ±0.3 TCR) | Score off by > 0.3 | high |
| L2 | **Oracle executor**: Track-B planner on the swept-volume inflated navmesh to the GT goal (goal + navmesh + humans, labeled oracle) | metric ceiling; irreducible failures (unreachable goals, islands, start inside a human, narrow doors) | SR 0.97–0.995, 0 collisions under all regimes, Score ≈ 93–96 | SR < 0.95 → scorer or coordinate bug; fix before anything else | high (B2/C7 reasoning) |
| L3 | **Compliant executor + GT goal point**: own depth+GPS occupancy map, person detector, safety executor; the navmesh is used only by the evaluator (labeled oracle: goal) | perception tax = L2 − L3: near-field blind spot (camera at 1.25 m, habitat-lab `default.py` L227; VFOV 90° on the square depth image → floor first visible ~1.25 m ahead; MAX_DEPTH 10 m, L240), stairs, thin/low obstacles, doors, moving people | clean SR ≥ 0.90 by Nov 1, ≥ 0.94 by Nov 13; contact episodes ≤ 3% → ≤ 1%; floor-change stratum ≥ 0.80 | contact episodes > 5% or clean/raw < 0.95 | medium (vln-safe: a simple depth guard leaves 27.7% contact episodes; a navmesh oracle 7.8%; a real occupancy planner must beat both) |
| L4 | (optional) compliant executor following GT reference-path waypoints | route following vs goal finding | ≥ L3 − 1 pp | — | medium |
| L5 | **K = 1 strict compliant agent** (none) | the submission that is unambiguously allowed | raw SR (stop < 3 m) 0.55–0.68; OSR 0.70–0.82; **clean SR 0.50–0.62**; contact episodes ≤ 3% | OSR − raw > 15 pp → the stop decision is the bottleneck; clean/raw < 0.85 → safety layer | medium-low (NavGPT-3 raw 76.9 on R2R-CE minus HA language/human/collision penalties) |
| L6 | **Union oracle over K rollouts** (GT used by the evaluator only) | ceiling for selection; rollout diversity | pass@K-clean: K=8 0.72–0.85, K=32 0.78–0.90 | union(K=8) − L5 < 8 pp → rollouts are not diverse | medium (B2: union of 3 public agents 87.2% raw on human-free R2R-CE; 77.8% clean for 2 oracle-guarded agents) |
| L7 | **K rollouts + compliant selection** (none; gated by the organizer ruling) | selection efficiency η = (L7 − L5)/(L6 − L5) | **clean SR 0.58–0.70**, η ≥ 0.30 (≥ 0.5 excellent), ≥ +5 pp over L5 (strategy W5) | η < 0.2 → spend on the verifier, not on more K | medium-low |
| L8 | L7 tape under the worst replay regime (evaluator: human_motion) | timing robustness | loss ≤ 0.5 pp SR; flips ≤ 0.5% of episodes; worst-regime Score ≥ mean − 0.5 | flips > 0.5% | medium (A3: 8.0% of episodes timing-sensitive) |
| Lk | Lockbox look (L5 and L7 configs frozen) | dev overfitting | within ±5.7 pp (95%, clustered) of the dev value, plus a scan term | dev − lockbox > 6 pp | — |

**Waterfall reported weekly:** Score(L2) → Score(L3) → Score(L6 at the deployed K) → Score(L7) → Score(L8). Each bar shows its paired cluster-bootstrap CI. The largest bar gets the next sprint's agents.

Score mapping at zero collisions (A4: Score = 80·SR + 60/(3+NE)), computed in `splits_and_targets.py` with official CR over βL:

| Scenario (val_unseen) | SR | NE | Colliding episodes | Score |
|---|---|---|---|---|
| K=1 single rollout | 0.55 | 3.0 | 3% | 53.4 |
| K=1 good | 0.62 | 2.6 | 2% | 59.9 |
| K-selection | 0.62 | 2.5 | 1.5% | 60.2 |
| K-selection good | 0.68 | 2.2 | 1% | 65.7 |
| Compliant executor + GT goal | 0.92 | 1.3 | 3% | 86.6 |
| Privileged oracle executor | 0.98 | 1.0 | 0% | 93.4 |
| Stretch | 0.72 | 2.0 | 0.5% | 69.5 |

**Track B shadow reference (not for submission; from B4/B2).**
- Goal top-1 within 3 m: 0.65 → 0.85 with ensembling and 3-instruction product-of-experts.
- Score 70–85.
- The oracle-goal SR of 0.97 is L2.

---

## 4. Metrics and strata

### 4.1 Per-episode metrics

**Official metrics:**
- success: STOP and 3-D Euclidean d < 3.0 m
- collisions.count, e = max(0, count − cn), CR_ep, SR_ep
- final d (NE)

**Diagnostic metrics (evaluator side):**
- **raw stop-within-3 m** (ignores collisions)
- **OSR** (min d along the trajectory < 3 m)
- **clean** (e = 0)
- geodesic final distance
- first-contact step
- **wall vs human attribution of every flagged step**: the step is legal on the base navmesh but flagged on the active human navmesh → human; otherwise wall/furniture
- `timing_sensitive` flag (A3 definition)
- per-regime counts

**Agent-side metrics (also available on test):**
- GPS-detected contacts (must equal collisions.count in the generation run)
- actions / forwards / turns / looks / sweeps
- hit-500 flag
- number of persons detected
- K, number of stop clusters, top-cluster support
- verifier score, p̂
- model calls, tokens, wall time

### 4.2 Goal-inference metrics in closed loop

These replace the brief's "top-1 within 3 m" for Track A:
- **Selected-stop accuracy**: the selected tape's stop is within 3 m (= raw SR of L7).
- **Top-k cluster recall**: any of the k highest-support 3 m stop clusters across K rollouts is within 3 m of the goal. Report k = 1, 2, 3, 5. This is the ceiling for a reranker that sees k candidates.
- **Mean and median distance error** of the selected stop, plus a histogram split at 3 m / 5 m / 10 m.
- **Stop precision**: P(stopped within 3 m | trajectory passed within 3 m) = raw SR / OSR. **Overshoot/undershoot share**: among OSR-but-failed episodes, whether the stop came after or before the closest approach.

### 4.3 Calibration

- p̂ comes from cluster support × verifier, calibrated by isotonic regression or Platt scaling on the cross-fitted train folds.
- Report:
  - a 10-bin reliability diagram
  - ECE (noise floor for a perfectly calibrated predictor: 0.042 at n = 613, 0.024 at 1,839, 0.018 at 3,408; p95 0.060 / 0.035 / 0.026)
  - Brier score
  - AURC and the selective-accuracy curve
  - **agreement buckets**: all K stops within 3 m / majority / no majority, with accuracy and share of each. The B4 discrete analogue with 3 instructions is 51% at 89.7%, 37.5% at 69.0% and 11.4% at 34.8%.
- Uses:
  - adaptive compute: spend more K or System-2 calls on low-p̂ episodes;
  - label-free test SR estimate: mean p̂ on test;
  - covariate-shift alarm: |mean p̂_test − mean p̂_dev| > 3 pp, or KS tests on agent-side statistics.

### 4.4 Strata for every report

| Stratum | val_unseen counts |
|---|---|
| Geodesic length, m (<7, 7–9, 9–11, 11–14, ≥14) | 477 / 600 / 393 / 276 / 93 |
| Floor change \|Δy\| > 1 m | 14.2%; > 2 m 9.5% |
| Humans within 1 m of the reference path (0 / 1 / 2 / 3+) | 882 / 516 / 180 / 261 |
| Human within 3 m of goal (end-anchor proxy) | 1,014 |
| Human within 1 m of start | 225 (A2: 75 within 0.3 m → begin with a TURN) |
| collision_num > 0 | 159 |
| timing_sensitive (A3) | 147 |
| Scan | 11 |
| instruction index (0/1/2), instruction length in words, number of human-activity mentions (LLM/regex parse once the HA-R2R text is on disk; the local R2R-CE file has the original text only) | — |
| failure label | see D9 |

---

## 5. Ablation plan (Track A; all paired on the same dev episodes, seeds and generation regime)

**Decision rule** (pre-registered in the manifest before the run). Adopt a change if all four hold:
- paired Δ clean SR > max(the MDE for its observed discordance, 1 pp);
- no stratum with ≥ 100 episodes regresses by more than 2 of its SEs;
- flips are not worse;
- cost fits the budget.

Within a family of more than 5 arms, require paired bootstrap p < 0.01.

| Family | Arms | Primary metric | Notes |
|---|---|---|---|
| AB1 backbone | NavGPT-3 8B mono / SimpleVLN-Qwen3.5-9B / ETP-R1 + rotation sweeps / StreamVLN; zero-shot vs HA-R2R fine-tuned | clean SR at K=1, OSR, actions used | sweeps cost 24–28 turns each; budget ≤ 6 |
| AB2 safety layer | none / vln-safe depth guard / occupancy planner with wall inflation 0.15, 0.20, 0.25, 0.30 m / per-forward check on/off / LOOK_DOWN near-field check on/off | contact episodes, clean/raw ratio | reference points: guard 27.7% contact episodes, navmesh oracle 7.8% (B2) |
| AB3 humans | person detector on/off; person radius 0.3 / 0.6 / 0.9 m; two-sided motion envelope on/off; soft 1 m proximity cost | human-attributed contacts, flips, SR on the human-on-path stratum | — |
| AB4 language | raw HA-R2R / LLM-condensed route-only / both (alternating across rollouts); token caps raised | raw SR, stop precision | the ETP-R1 150-token and ETPNav 80-token caps truncate the stop clause (B2) |
| AB5 human anchors | instruction human mentions matched to detected people as landmarks and stop anchors: on/off | SR on the human-within-3 m-of-goal stratum; mention→detection match ≥ 0.8 (W3) | — |
| AB6 System 2 | none / open 7B Qwen-VL / frontier API (cached) | SR, cost per episode | Q12 prefers open models; API temperature is unsupported (B3), so diversity must come from prompts, and all calls are cached for reproducibility |
| AB7 test-time compute | K ∈ {1, 2, 4, 8, 16, 32}; selection = largest 3 m stop cluster / support × verifier / contact-free filter first / verifier only | SR(K), union(K), η(K), cost(K) | **K=1 strict is always reported** |
| AB8 gated inputs (not submitted) | sibling-instruction joint inference (3 instructions of one trajectory); cross-episode scene memory | Δ SR | only to size the organizer question; B4 measured +6–7 SR in discrete VLN for the 3-instruction vote |
| AB9 generation clock | wall clock (slow agent → late frames) vs virtual fast clock (frame = f(step) emulating fast replay; A3) vs humans off | flips under the R-regimes | — |
| AB10 training | IL only / DAgger with a privileged collision-free teacher / + RL with reward = success ∧ zero contacts | clean SR, contact episodes | SimpleVLN: RL +7.5–10 SR on R2R-CE (B2) |

---

## 6. Collision-robustness protocol (human timing)

**Why it is tractable.**
- Habitat flags a MOVE_FORWARD iff its filtered 3-D displacement d satisfies d² + 1e-5 < 0.0625, i.e. d < 0.249980 m (A2). The agent sees its 3-D position, so it can compute the identical predicate.
- **Test T-contact-parity:** in every generation run, the agent's detected contacts must equal `collisions.count` on 100% of episodes and steps. Any mismatch is a bug.
- Walls are static, so a zero-contact local tape can only collide officially through four channels:
  - (i) a different human frame;
  - (ii) Recast differences between per-frame navmeshes far from humans (contour simplification ≤ ~6.5 cm; A2 open question);
  - (iii) start-pose re-snapping that depends on which navmesh is active;
  - (iv) scorer differences.

**Generation regimes (G).**
- G-wall: the default slow agent. Humans run through all frames and freeze at ~110–119 (A3 measured 117 at 0.3 s/step and 110 at 1 s/step).
- G-fast: a virtual clock that emulates fast official replay. At ~5 ms/step, a 500-action episode reaches only frame ~26.
- G-none: humans absent. This emulates a Phase-2 bundle without test-scan human placements; the simulator tolerates a missing scan entry (A1).

**Replay regimes (R).** Kinematic `try_step` replay against per-frame navmeshes on CPU for all episodes, plus a real docker replay for a 300-episode subset:
- R0 frozen at frame 0
- R26 frozen at frame 26
- R119 frozen at frame 119
- Rstep: frame = step index (cold cache)
- Rfast: real clock at 5 ms/step
- Rslow: real clock at 0.3 s/step
- Rstall: frame 119 at the first step after a stall, then frozen (queue cap; A3)
- Rbase: base navmesh, no humans
- Rall: the all-frames certificate, i.e. collision-free on all 121 navmeshes at every step (evaluator-only on val)

**Metrics per (G, R):** SR, CR over βL, TCR, Score. The flip set F = episodes clean under G but colliding under some R. Also worst-case Score, mean − worst, and the list of flipped episodes with wall/human attribution.

**Acceptance (dev):**
- |F| ≤ 0.5% of episodes (≤ 7 of 1,413);
- zero flips outside the timing-sensitive set;
- worst-regime Score ≥ mean − 0.5;
- TCR spread across regimes < 0.005 (C10);
- T-contact-parity = 100%.

**Power:**
- 0 flips in 1,839 episodes → 95% upper bound of 0.16%; in 500 → 0.6%.
- Oversample the 147 timing-sensitive episodes with 30 random monotone frame schedules each.

**Cost of failure on test** (computed): 10 / 34 / 68 flipped successes (0.3 / 1 / 2% of episodes) cost **−0.31 / −1.04 / −2.07 Score**.

**On test.** The compliant agent **cannot** certify its own tapes against `human_motion.json`; that would be inference use under Q11. The val-measured flip rate is therefore the estimate of the test loss. Local test replay is used only for format and determinism (C3 T13), and the harness must refuse to report test collision counts.

---

## 7. Phase-1 calibration (official vs local; deadline Oct 30)

**Facts.**
- Phase 1 scores val_seen and val_unseen per submission: 5 per day, best retained, ranked by val_unseen.
- CodaBench has been down since ~Oct 21.
- Q5: local results are not official.
- A8: two image builds exist; `cr-domain-20261004` probably changes the CR domain.

| # | Submission | Prediction (exact) | Resolves |
|---|---|---|---|
| P1 | STOP-only on all 2,617 episodes | val_unseen k = 63, NE 7.466760, CR = TCR = 0, Score **8.473053**; val_seen k = 3, NE 8.196761, **5.667176**. A geodesic scorer would give ≈ 5.04 / 4.77 | Euclidean vs geodesic; coordinates; coverage; distance-measure override active |
| P2 | Official CMA export (`scripts/export_cma_submission.py`) | CR column **0.684 / 0.623** (C/βL) vs **0.593 / 0.546** (C/L); Score **12.945387 / 16.509450** vs **13.289348 / 16.871068** | which build or CR domain CodaBench runs; replay parity (±5 episodes, ±0.3 TCR) |
| P3 | Our first genuine end-to-end tape (v0; even a zero-shot backbone + guard). Never a GT-derived tape (C3/B7) | the local mirror's per-split metrics | per-split |ΔSR| ≤ 0.5 pp, |ΔNE| ≤ 0.02 m, |ΔScore| ≤ 0.3; collision deltas only within the flip set |
| P4 | P3 resubmitted unchanged (Phase 1 only; never in Phase 2) | Δ between two official runs | scorer nondeterminism from wall-clock humans |
| P5 (optional) | A newer v0.x tape | — | trend parity |

**Schedule if CodaBench returns:**
- Day 1: P1 + P2.
- Day 2: P3 + P4.
- Later: one update per day; always keep ≥ 1 slot per day unused.
- Never upload in the last 2 h of a UTC day.

**If it stays down past Oct 29:**
- Run `havln-score-phase1 --submission X.zip --output-dir R --gpu-ids …` (in the image; A8) on P1–P3 as the "official-code local" reference.
- Email the organizers for a calibration run.
- In Phase 2, the first upload (the real K=1 v1 agent after `havln-validate` PASS) is compared with our **label-free prediction** (mean p̂ on test). That is the only external check left.

**Stop rule.** If P1 or P2 deviates from prediction beyond tolerance, freeze all model work until the local mirror is fixed. Every downstream number depends on it.

---

## 8. Statistical power (computed in `power.py` / `lockbox.py`)

**Measured clustering** (Airbert vs VLN-BERT released predictions on the 1,839 R2R-CE val_unseen episodes; success = final node within 3 m):

| Quantity | Value |
|---|---|
| SR Airbert / VLN-BERT | 0.669 / 0.570 |
| Trajectory ICC | 0.235 (design effect 1 + 2·0.235 = 1.47; cluster-bootstrap SE inflation ×1.21) |
| Scan ICC | 0.032; observed per-scan SR SD 0.137, of which ~0.088 is true between-scan SD |
| Paired discordance between two *different* systems | 31.5% |
| Paired SE | iid 1.29 pp / trajectory-bootstrap 1.46 pp / scan-bootstrap 1.65 pp (×1.14 and ×1.28 vs iid) |

**Single-system 95% CI half-widths for SR at p = 0.5** (p = 0.3 or 0.7 in brackets):

| Split | iid | trajectory-clustered |
|---|---|---|
| val_unseen 1,839 | ±2.29 (2.09) | ±2.77 (2.54) |
| dev 1,413 | ±2.61 (2.39) | ±3.17 (2.90) |
| lockbox 426 | ±4.72 (4.32) | ±5.71 (5.24) |
| test 3,408 | ±1.68 (1.54) | ±2.03 (1.86); B7: 0.9–1.5 pp SE |

**Paired MDE** (two-sided α = .05, power .8, trajectory-clustered):

| Discordance | val_unseen | dev | test | quick (306) | 95% significance threshold, val_unseen |
|---|---|---|---|---|---|
| 2% | 1.05 pp | 1.20 | 0.77 | ~2.6 | 0.73 |
| 5% | 1.66 | 1.90 | 1.22 | ~4.1 | 1.16 |
| 10% | 2.35 | 2.68 | 1.72 | ~5.7 | 1.64 |
| 20% | 3.32 | 3.79 | 2.44 | ~8.1 | 2.32 |
| 30% | 4.06 | 4.64 | 2.98 | ~10.0 | 2.84 |

Small ablations (a margin or prompt tweak) typically change 2–10% of episodes, so 1–2.5 pp effects are resolvable on dev. The quick split only catches bugs and large effects. In Score units at zero collisions, 1 pp SR ≈ 0.8 Score.

**Val→test absolute prediction.** The scan-effect SE of the mean SR is 2.99 pp for val_unseen (n_eff 8.6 scans) and 2.27 pp for test (n_eff 14.9 scans). For a fixed system, SE(test − val) ≈ 4.1 pp, so the **95% prediction interval is ±8.1 pp SR (≈ ±6.5 Score)**. Historical val→test gaps of −1…−3 (B4) are means, not bounds. Consequences:
- Never promise an absolute test number.
- Report forecasts as "dev − selection optimism ± 8 pp".
- Treat lockbox agreement as a sanity check, not a forecast.

**Best-of-N optimism** (N variants with equal true SR, judged on val_unseen; ×1.14 for clustering):

| N | Discordance 10% | Discordance 20% |
|---|---|---|
| 2 | +0.3 pp | +0.4 pp |
| 5 | +0.6 | +0.9 |
| 10 | +0.8 | +1.1 |
| 20 | +1.0 | +1.4 |
| 50 | +1.2 | +1.7 |

The ledger counts N, the number of dev looks per decision family, and subtracts this optimism in forecasts. The lockbox (≤ 4 looks) is the unbiased check.

---

## 9. Leakage and self-deception controls (each has an automated test)

1. **Inference firewall**: separate agent container with no data mounts, a whitelisted observation schema, the info dict stripped, and audited `open()` calls. *Test:* fail on any non-whitelisted key or any open of `human_motion.json`, `*_gt.json`, `*.navmesh`, `*.house` or a connectivity file.
2. **Goal-poisoning test**: shift every val goal and reference path by +100 m in the env server's copy. Generated tapes must be **bit-identical** (same seeds). This catches any GT leaking through wrappers, measures or sensors (e.g., `SHORTEST_PATH_SENSOR` and `VLN_ORACLE_PROGRESS_SENSOR` are in the default HA task config, `HAVLNCE_R2R_task.yaml` L28-31; the official exporter strips them with `TASK.SENSORS=['INSTRUCTION_SENSOR']`, `export_cma_submission.py` L117, and our env server must do the same).
3. **Human-file poisoning test**: run the agent with `human_motion.json` unreadable by the agent container but readable by the renderer. The audit log must show zero agent-side opens.
4. **Test-text hygiene**: no person reads test instructions to design prompts. A CI grep test hashes every 8-gram of all 3,408 test instructions (R2R-CE text now, HA-R2R text when it arrives) and fails if any prompt template, few-shot file or training-data file contains one.
5. **No val/test training (Q10)**: fitted components use cross-fitted train folds only. Dev may choose ≤ ~10 scalar hyperparameters per family. A manifest field `fitted_on` is required and validated against the split registry.
6. **Lockbox discipline**: lockbox ids are encrypted at rest (key held by the integrator); ≤ 4 looks, each logged with the frozen config fingerprint; no tuning after a look except a full new pre-registered cycle.
7. **No test-feedback selection**: Phase-2 uploads are whole-system variants only; no per-episode, per-scan or per-subset splicing; **no "disjoint-subset A/B"** (C2's plan; B7 counts per-scan splicing as gray-zone probing); no identical resubmissions in Phase 2; one account; ≤ 20–30 uploads; every upload logged with its ZIP sha256, fingerprint and rationale.
8. **Local test replay quarantine**: on the test split the harness emits only format and determinism results (C3 T13). Collision counts against GT test humans are never shown to the pipeline or to people making decisions.
9. **Quarantined files**: R2R_test.json originals, `human_motion_text.json`, and test-scan connectivity are not mounted anywhere in the inference path (C3 T8/T9).
10. **Pretrained-model contamination register**: list every checkpoint's training data and flag any trained on the 18 MP3D test scans (e.g., "pre-explore" checkpoints). Disclose this in the report.
11. **Determinism**: seeds in the manifest; LLM/VLM calls cached by request hash (APIs reject temperature; B3); one command regenerates the final ZIP with an identical sha256.
12. **Config parity**: the env-server config equals `/app/config/challenge_submission.yaml` plus the exporter overrides. *Test:* replaying a generated tape under the same frozen regime reproduces the generation GPS log to 1e-6 m and the same collision flags.

---

## 10. Standard experiment record

Directory: `runs/<exp_id>/` with `exp_id = <YYYY-MM-DD>_<WS>_<slug>_<fp8>`.

**`manifest.json`** (written before the run starts = pre-registration; completed at the end):

```json
{
  "exp_id": "2026-11-03_W4_navgpt3-ft-occguard_k1_3fa9c2d1",
  "owner": "W4/agent-2", "created_utc": "2026-11-03T10:12:00Z",
  "question": "Does person radius 0.6 m vs 0.3 m reduce human contacts without SR loss?",
  "decision_rule": "adopt if paired dClean >= max(MDE,1pp) and flips not worse",
  "compare_to": "2026-11-02_W4_navgpt3-ft-occguard_k1_77b0e112",
  "regime": {"track": "A-strict|A-gatedK|ORACLE-L2|ORACLE-L3|ORACLE-L6|B-shadow",
             "agent_inputs": ["rgb","depth","gps","compass","instruction","episode_id","start_pose","step"],
             "evaluator_privileged": ["goals","navmesh","human_motion"],
             "generation_clock": "wall|virtual-fast|none", "K": 1, "seeds": [0]},
  "split": {"name": "dev|quick|smoke|lockbox|val_seen|trainfoldA|trainfoldB|test",
            "episode_ids_sha256": "…", "n": 1413, "L_official": 1839, "betaL_scaled": 1224},
  "fingerprint": {"sha256": "3fa9c2d1…", "components": {
      "git_commit": "…", "git_dirty_diff_sha256": "…", "config_sha256": "…",
      "docker_image": "ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f…",
      "checkpoints": {"policy": "sha256:…", "verifier": "sha256:…", "person_det": "sha256:…"},
      "prompts": {"system2": "sha256:…", "condense": "sha256:…"},
      "llm": [{"provider": "open|api", "model": "qwen-vl-7b@rev", "params": {}, "cache_ns": "…"}],
      "data": {"ha_r2r_val_unseen": "sha256:…", "collision_num_val_unseen": "sha256:2c9111b1…",
               "human_motion": "sha256:…", "haps2_tree": "sha256:…", "navmesh_cache_tree": "sha256:…",
               "mp3d_tree": "sha256:…"},
      "scorer": {"impl": "havln_score_ref.py", "sha256": "…", "mode": "A-official-cli|B-mirror"},
      "audit_log_sha256": "…"}},
  "metrics": {
    "overall": {"L": 1413, "k_success": 0, "C_colliding_eps": 0, "sum_e": 0, "SR": 0, "NE": 0, "CR": 0, "TCR": 0,
                "Score": 0, "raw_SR": 0, "OSR": 0, "clean_SR": 0, "contact_eps": 0, "human_contact_eps": 0,
                "ci95_cluster": {"SR": [0, 0], "Score": [0, 0]}},
    "paired_vs_ref": {"d_clean_SR": 0, "ci95": [0, 0], "discordance": 0, "mde": 0, "p": 0},
    "by_regime": {"R0": {}, "R26": {}, "R119": {}, "Rstep": {}, "Rfast": {}, "Rslow": {}, "Rstall": {}, "Rbase": {}, "Rall": {}, "flips": 0},
    "by_stratum": {"geo_bin": {}, "floor_change": {}, "humans_on_path": {}, "human_goal_3m": {}, "scan": {}, "timing_sensitive": {}},
    "k_scaling": [{"K": 1, "SR": 0, "union": 0, "eta": null}],
    "calibration": {"ece": 0, "brier": 0, "aurc": 0, "buckets": []},
    "cost": {"gpu_h": 0, "api_usd": 0, "wall_h": 0, "model_calls": 0}},
  "artifacts": {"per_episode": "per_episode.parquet", "tapes_zip": "tapes.zip", "tapes_zip_sha256": "…", "step_logs": "steps/"},
  "lockbox_look": false, "status": "registered|running|complete|invalid"
}
```

**`per_episode.parquet` (CSV twin) columns:**
- Identity: `episode_id, trajectory_id, instr_idx, scan, split`.
- Strata: `geo_len, geo_bin, floor_change, n_humans_path_1m, human_goal_3m, human_start_1m, cn, timing_sensitive, instr_words, n_human_mentions`.
- Actions: `n_actions, n_forward, n_turn, n_look, n_sweeps, hit_500, stop_called`.
- Outcome: `final_x, final_y, final_z, d_euclid, d_geodesic, osr_min_d, success_official, collisions_count, e_adj, clean`.
- Contacts: `wall_steps, human_steps, agent_contacts, contact_parity_ok, first_contact_step`.
- Selection: `K, selected_rollout, n_clusters, top_support, top2_support, p_hat, verifier_score`.
- Regimes: `regime_counts_json, flip`.
- Cost: `wall_s, model_calls, tok_in, tok_out`.
- Diagnosis and provenance: `failure_label, tape_sha256`.

**Failure labels** (automatic, evaluator-side):
- `NEVER_NEAR` (OSR fail)
- `PASSED_NO_STOP` (OSR ok, stopped > 3 m away; with overshoot or undershoot)
- `WRONG_INSTANCE` (stopped within 3 m of a distractor of the same room type)
- `WALL_CONTACT`
- `HUMAN_CONTACT`
- `BUDGET_500`
- `STUCK` (≥ 20 turns without a forward)
- `FLOOR_CHANGE_FAIL`
- `START_IN_HUMAN`

**Ledgers** (append-only, written by the harness, never hand-typed):
- `RESULTS.jsonl` (one line per manifest), rendered into `RESULTS.md`
- `LOCKBOX_LOOKS.jsonl`
- `SUBMISSIONS.jsonl` (phase, UTC time, ZIP sha256, fingerprint, official SR/NE/CR/TCR/Score, local prediction, Δ)

---

## 11. Dashboards (regenerated from the ledger on every run)

| Id | View | Purpose |
|---|---|---|
| D1 | Experiment leaderboard (dev; filter by WS, track, K) with CIs and integer counts | single source of truth |
| D2 | **Waterfall** L2 → L3 → L6 → L7 → L8 with paired CIs | where to put agents next |
| D3 | Stratum × experiment heatmap of Δ vs reference (cells shaded only if significant) | hidden regressions |
| D4 | Regime matrix: episodes × R-regimes, flip list with attribution | timing robustness |
| D5 | Calibration: reliability diagram, ECE vs noise floor, agreement buckets, risk–coverage | trust in p̂ |
| D6 | K-scaling: SR(K), union(K), η(K), $/episode(K) | test-time compute ROI; size of the gated question |
| D7 | Per-scan forest plot (dev scans; lockbox after a look) | building heterogeneity |
| D8 | Budget: histogram of actions used, sweeps, hit-500 share (target < 0.5%) | budget planner health |
| D9 | Failure taxonomy over time | what moved |
| D10 | Official vs local (Phase 1 P1–P4; every Phase-2 upload vs label-free prediction) | scorer parity |
| D11 | Test label-free monitors: p̂, contact rate, actions, detected persons, test vs dev | covariate shift |

---

## 12. Expected numbers over time (healthy project, Track A; inference, medium-low confidence)

| Date (gate) | Must hold |
|---|---|
| Oct 26 (M1) | L0 exact to 1e-6 on both val splits in the local mirror; contract validator PASS; scorer unit tests reproduce 16.509450 / 12.945387 |
| Oct 28 (M2) | L1 within tolerance; T-contact-parity and config-parity tests pass; goal-poisoning test passes |
| Oct 29–30 (M3) | Phase-1 P1–P4 done or the fallback CLI run done; L2 ≥ 0.97 on dev; L3 ≥ 0.85 on quick |
| Nov 3 | L3 ≥ 0.90 dev with contact episodes ≤ 3%; L5 v1 (zero-shot backbone + safety) clean SR 0.40–0.50 |
| Nov 6 (G5) | L5 clean 0.45–0.55 (dev Score 45–55); first Phase-2 upload = K=1 strict v1, compared with the mean-p̂ prediction; lockbox look 1 |
| Nov 13 (G6) | Fine-tuned + guard: L5 clean 0.52–0.62; L6 (K=8) 0.75–0.85; L7 0.58–0.66 (gated); L3 ≥ 0.94, contact episodes ≤ 1%; flips ≤ 1%; lockbox look 2 |
| Nov 20 (G7) | Architecture freeze; L7 0.60–0.70; flips ≤ 0.5%; ECE ≤ 0.035; lockbox look 3 within ±6 pp of dev; dev Score 58–68 (gated K) / 53–60 (K=1 strict) |
| Nov 27 (G8) | Final ZIP regenerated bit-identically; final lockbox look; submit |

---

## 13. Contradictions and flags (vs other findings and the strategy)

1. **K-rollout selection is not unambiguously compliant.** The strategy (§0.4, §3) calls K = 8–32 with self-consistency "allowed". C3 classes simulator branching (observations not in the tape) as gray, "ask first", and R2R reports it as "beam search", a separate setting. → Keep a K=1 strict submission that can stand alone; report both; ask the organizers.
2. **B2 recommends a navmesh-oracle collision layer and replay verification against GT humans for every closed-loop rollout.** In Track A that is inference use of privileged data (C3 T2d/T4; Q11). It is valid only as the labeled oracle arms L2 and L3, and as a val evaluator.
3. **B3 proposes fitting the fusion calibrator on val_unseen.** That conflicts with Q10 and B4's leave-scans-out advice. → Cross-fit on train folds; val_unseen only *evaluates* calibration.
4. **C2 (Nov 2–6) plans Phase-2 "disjoint-subset A/B" submissions.** That uses test feedback per subset, which B7 and C4 call gray-zone probing. → Do not do it.
5. **Strategy W2 DoD "TCR = 0 under 4 regimes" for the compliant executor** is likely unattainable with perception-only geometry over 1,839 human-populated episodes (vln-safe guards leave 7.8–27.7% contact episodes). → Use contact episodes ≤ 1% plus flips ≤ 0.5% as the DoD, with zero as the stretch goal.
6. **A2 says "humans never injected" after a slow reset; A3 says frame 119 is shown** (queue cap; measured 6/6). → Both cases are covered by Rbase and Rstall.
7. **The topic brief's expected numbers** (goal top-1 0.65 → 0.85, Score 70–85) are Track-B numbers. For the Track-A submission of record, the healthy final dev Score is 53–60 at K=1 strict and 60–66 with gated K.

## 14. Open questions

- Is multi-rollout selection (K > 1 with cross-rollout agreement) allowed? Add this to the organizer question list (the C3 issue draft); it is the largest protocol-dependent lever.
- Which image build, and therefore which CR domain, does CodaBench use? P2 settles it.
- Does the Phase-2 bundle ship test-scan human placements? If not, G-none is the generation regime on test, and the val-measured G-none → R-regime loss is the expected penalty.
- Official scorer speed and FPS: A3 predicts early frames; P4's run-to-run Δ bounds it.
- Do per-frame navmeshes differ away from humans (Recast contour drift)? Measure flips of human-free tapes across all 121 navmeshes in week 1.
- Will the HA-R2R val/test instruction files arrive in time to compute the human-mention strata? The local R2R-CE file has original instructions only.

## 15. Sources

- Local data:
  - `S/ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{val_unseen,val_seen}/*.json.gz` (episodes, goals, reference paths, GT actions; same ids and trajectories as HA-R2R per A1)
  - `S/ext/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`
  - `S/ext/HA-VLN/Data/HA-R2R-tools/collision_num_*.json`
  - `S/ext/HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml` L1-57 (sensors 224²/256², HFOV 90; the SHORTEST_PATH and ORACLE_PROGRESS sensors at L28-31; DISTANCE_TO_HUMAN at L45); `S/ext/habitat-lab-0.1.7/habitat/config/default.py` L218 (TILT 15), L226-227 (HFOV 90, sensor at 1.25 m), L240 (MAX_DEPTH 10); `S/ext/track2/scripts/export_cma_submission.py` L117 (task sensors reduced to INSTRUCTION_SENSOR)
  - `S/ext/b4/airbert-vln_airbert-vln.github.io/assets/data/{airbert,vlnbert}_r2r_results_val_unseen.json` and `R2R_val_unseen.json` (per-episode outcomes for the clustering and power analysis)
  - `S/ext/HA-VLN/HASimulator/HA-DE/connectivity/*.json` (graph distances)
- Rules: `S/ext/jostar-track2`, `git show origin/bohan/clarification-Oct14:README.md` (FAQ Q4, Q5, Q8–Q13).
- Scripts and outputs: `S/c6work/{val_strata.py, power.py, lockbox.py, splits_and_targets.py, power_out.json, val_unseen_strata.json, val_seen_strata.json, c6_splits_val_unseen.json}`.
- Findings used: `S/findings/{A1,A2,A3,A4,A8,B2,B3,B4,B7,C2,C3,C4}*.md`; `/home/user/open-data-eval/competitions/roboworld2026-track2/01-strategy.md` (read only).
- External (via the findings above): vln-safe 'Successful but Unsafe' arXiv 2610.14682 (B2); HA-VLN 2.0 arXiv 2503.14229; FAST notebook; Airbert / VLN-BERT (B4).
