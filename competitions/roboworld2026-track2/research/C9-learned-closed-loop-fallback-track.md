# C9: Bring-up plan for the PRIMARY compliant closed-loop agent (HA-VLN Track 2)

Topic id: `C9-learned-closed-loop-fallback-track` · Date: 2026-10-24 · Author: research agent C9

**Regime.** Everything here assumes the **compliant regime** in the organizers' clarification branch (JostarXiong/track2 `bohan/clarification-Oct14`). That means:
- inference inputs are the episode start pose, the instruction, GPS+compass, and sequential RGB-D from ONE forward camera at the official spec;
- panoramas come only from in-place TURNs, and those turns count toward the 500-action budget;
- no `human_motion.json`, navmesh, pathfinder or scene mesh at inference;
- no cross-episode memory and no simulator branching.

Privileged simulator, scene and human data are used only for TRAINING (teachers, labels), local evaluation on val, and upper bounds. Items that need an explicit organizer ruling are marked **[gray]**. This matches C3's CLEAN-1 spec.

**Method note.** The shared WebSearch budget was exhausted, so I did no web searches. Everything comes from local clones:
- `ext/sota/{SimpleVLN,ETP-R1,vln-safe,OmniNav,HCSG,...}`, `ext/B3/metacognitionai_NavGPT-3`, `ext/HA-VLN`, `ext/jostar-track2`, `ext/habitat-lab-0.1.7`;
- the sibling findings B2, B3, A2, A6, A11, C1, C2 and C3;
- two scripts I wrote: `scratchpad/work/c9/budget.py` (it re-analyses vln-safe's per-episode logs) and `scratchpad/work/c9/score.py` (the official Score formula; it reproduces the README CMA Score of 12.9).

HF weight availability and paper numbers come from the repos' READMEs and could not be re-verified online.

---

## 1. Summary (decision-relevant)

1. **Port SimpleVLN first; ETP-R1 second; do NOT build the compliant track on NavGPT-3.**
   - **SimpleVLN.** Qwen3.5-4B/9B-RL or Qwen3-VL-8B-RL; R2R-CE val-unseen SR 76.3 / 76.7 / 74.4. It is the only top-tier open policy that is natively compliant: one forward RGB camera at HFOV 90, and the exact challenge action set of 0.25 m and 15° as text action chunks. Its client is about 300 lines of OpenAI-API code (vLLM-served).
   - **ETP-R1.** R2R-CE val-unseen SR 65.3. Its 12-view rig equals the official sensor (RGB 224² / depth 256² at HFOV 90, one optical centre), so in-place sweeps reproduce its inputs exactly, at about 22 TURNs per decision. Full DAgger and GRPO training code is released.
   - **NavGPT-3 VLA** (76.9 SR) is non-compliant as released, for two reasons:
     - it consumes **4 simultaneous 400×400 HFOV-120 cameras** at every step;
     - it executes each step by **teleporting** to its 0.25 m waypoint.

     Rebuilding its 4 views by rotation would cost ≥18 TURNs per 0.25 m of travel, and no training code exists to re-train it for a single camera. Use it only in the privileged/secondary track.
2. **Collision handling decides the compliant score, not backbone raw SR.** Under HA-VLN physics (human-free R2R-CE), ETP-R1's raw SR is 64.6 but its zero-collision SR is 37.7. The training-free depth+stall guard lifts it to 50.1. The navmesh-oracle guard reaches 61.3, but it is **privileged, i.e. not allowed at inference**; it serves only as an upper bound and as a label source. The plan is a learned, compliant "Guard v2" trained on privileged navmesh labels, aiming to close 50–75% of the 50.1→61.3 gap (inference).
3. **Panorama budget math.** With a 90° HFOV camera, a full 360° sweep needs ≥270° of rotation, i.e. ≥18 TURNs. ETP-R1's native 12×30° ring costs 22 TURNs.
   - From vln-safe logs, ETP-R1 uses 91.7 primitives per episode on average (p50 63, p90 201, p99 400), over an estimated 6–8 decisions (cap 15).
   - With sweeps the episode costs about 225–270 actions on average and about 420–470 at p90. A budget-aware sweep/STOP policy is therefore mandatory.
   - SimpleVLN needs no sweeps.
4. **Training with privileged teachers is allowed (Q11) and is the main lever after the guard.**
   - **Clearance teacher:** plan on a navmesh rebuilt with all 120 frames of every human as static objects at agent radius 0.25–0.30 m, discretise into rotate-then-forward primitives, and verify against the base navmesh plus all 120 frame navmeshes.
   - **Training data:** HA-R2R train (10,819 episodes) plus R2R-CE and RxR-CE train, rendered at the **official 224² camera** with humans present.
   - **Training stages:** expert SFT → 3 DAgger rounds → rejection-sampling fine-tuning (RFT), using reward = success ∧ 0 collisions. Optional GRPO comes after that.
   - The HA-VLN `DaggerTrainer` fits recurrent CMA-class policies only, so the VLM and graph policies get their own DAgger drivers.
5. **Self-consistency must stay within one episode to be compliant.**
   - **Allowed:** K-sample and multi-model voting per decision, a stop supermajority, and a rotation-based stop verifier (turns counted).
   - **[gray] Restart-and-select:** K full rollouts per episode with environment resets, then selection. This is simulator branching (C3 T3). It is worth maybe +6–10 SR, but only if the organizers permit it.
   - **[gray] Sibling-instruction consensus:** the 3 instructions per trajectory share a goal. Asking the organizers is required.
6. **Expected compliant HA-R2R test results** (inference; Score uses the official formula with CR normalised by the 2,859 influenced episodes):

   | Stage | SR | Score |
   |---|---|---|
   | Zero-shot SimpleVLN + Guard v1 (Nov 2) | 0.28–0.36 | 25–32 |
   | + Guard v2 + HA SFT (Nov 9) | 0.40–0.47 | 36–43 |
   | + DAgger + voting (Nov 16) | 0.46–0.54 | 42–50 |
   | + RFT/GRPO + stop verifier (frozen Nov 20–24) | 0.50–0.60 | 46–55 |

   For comparison, the best verified published HA-VLN-CE result is HCSG at about Score 22, and the CMA baseline is 12.9.
7. **The hard dependencies are external.**
   - **MP3D scenes.** Without them no compliant agent can run, because observations must be rendered.
   - **The 18 test scans' human placements in the Phase 2 bundle.** Without them the local simulation renders no test humans, the agent cannot see them, and the replay will contain them. That costs an estimated 0.05–0.12 SR.
   - **An organizer ruling on camera resolution.** SimpleVLN was trained at 640×480; vln-safe notes that StreamVLN "degrades at any other camera".

---

## 2. Backbone compliance matrix (one forward RGB-D camera, official spec RGB 224×224 / depth 256×256, HFOV 90, height 1.25 m)

| Backbone | R2R-CE val-unseen raw SR | Native observation | Native execution | Compliant? | Cost to make compliant | Training code |
|---|---|---|---|---|---|---|
| **SimpleVLN** Qwen3.5-9B-RL / 4B-RL / Qwen3-VL-8B-RL | 76.7 / 76.3 / 74.4 | 1 forward RGB 640×480 HFOV 90 + history (8 uniformly sampled from ≤200 frames) | text chunks, ≤2 sub-actions × ≤3 primitives, 0.25 m / 15° | **Yes** (single camera); resolution 224 vs 640×480 [gray: ask] | none; fine-tune at 224² | eval only; native Qwen ckpt → generic SFT |
| **ETP-R1** (ETPNav family, GRPO) | 65.3 (vln-safe re-run 64.6) | 12 views RGB 224² + depth 256² HFOV 90, single optical centre | waypoint → rotate+forward primitives (`back_algo control`) | **Yes via sweeps** | 22 TURNs per decision; budget-aware | **full** (pretrain, DAgger, GRPO) |
| ETPNav / BEVBert-CE / g3D-LF | 57 / 59 / 61 | same 12-view rig | same | yes via sweeps | same | full |
| StreamVLN | 56.4 | 1 RGB 640×480 HFOV 79 | 4-primitive chunks | yes (crop 90°→79° = 184 px of 224) | resolution and FOV shift | DAgger collection code |
| NaVILA | 54.0 | 1 RGB 512² HFOV 90 | 25/50/75 cm, 15/30/45° | yes | resolution shift; slow (0.6 s/step) | SFT scripts |
| NaVid | 41.9 (ckpt) | 1 RGB 640×480 HFOV 90 | turn 30° → 2×15° | yes | low ceiling | partial |
| Uni-NaVid | 51.8 (ckpt) | 1 RGB HFOV **120** | turn 30° | **no** (HFOV 120 cannot come from an HFOV-90 camera without outpainting) | — | stage-2 scripts |
| **NavGPT VLA 8B (NavGPT-3)** | 76.94 | **4 simultaneous** RGB 400² HFOV **120** (F/R/B/L) every step | **teleport** to waypoint 1 (0.25 m point on a 0.125 m grid, continuous heading); never emits STOP | **no** | 4-view by rotation ≥18 TURNs per 0.25 m step ⇒ infeasible; single-view retrain has no training code | none |
| OmniNav | 69.5 (primitive re-run 67.5) | **3 simultaneous** RGB 720×640 HFOV **110** | waypoint teleport (vln-safe quantised it) | **no** | HFOV 110 unavailable; sweeps of about 24 TURNs per decision | training code |

Sources: SimpleVLN `eval/vln/eval.py` L36, L157, L329, L351-359; `eval/config/vln_r2r.yaml`; `eval/scripts/eval.sh` (MAX_ACTION_HISTORY 200, PASS_K 4); README L97-99. ETP-R1 `run_r2r/r2r_vlnce.yaml`, `iter_train.yaml` L61-62, `main_server.bash` L25-96. NavGPT-3 `navgpt/environment/r2r.py` L85, L98, L823 ("Four SIMULTANEOUS cameras"), L1360 ("Costs ZERO simulator steps"), L1706 (`teleport`); `navgpt/planner/vla_only.py` L69, L89; `navgpt/planner/tools/vla_client.py` L1-30; `navgpt/vla/api.py` L132 (`view_num=4`); `configs/experiments/vln/vla_8b_r2r.yaml` (turn_angle_deg 30, panorama_view_px 400). vln-safe `docs/agent_notes/omninav.md` L25, `configs/agents/{streamvln,navila}.yaml`. A6 §6.6 (NaVid/Uni-NaVid HFOV).

**Port order.**
1. **(P1, day 0–2)** SimpleVLN client into the HA env with three checkpoints: Qwen3.5-4B-RL (throughput workhorse), Qwen3.5-9B-RL (accuracy), Qwen3-VL-8B-RL (fallback in case the training toolchain cannot handle Qwen3.5; it is also the organizers' encouraged "~7B Qwen-VL" class).
2. **(P2, day 0–5)** ETP-R1 through vln-safe's `etpnav_worker` (py3.6, torch 1.10.2), with HA human insertion and a rotation-sweep observation adapter.
3. **(P3, optional)** NaVILA or StreamVLN, only as ensemble members if they beat P1/P2 on clean SR; not before Nov 9.

---

## 3. Panoramas within the one-forward-camera rule: budget math

| Sweep | TURNs | Views obtained | Coverage | Use |
|---|---|---|---|---|
| Minimum full ring (4 × 90°) | 18 | 4 (+ free intermediates every 15°) | 360°, no overlap | lower bound for any 360° view with HFOV 90 |
| ETP rig (12 × 30°) | 22 | 12 (23 if every 15° stop is kept) | 360°, 60° overlap | ETP-R1 decisions (in-distribution) |
| Front half (±90°) | 9–12 | 3–5 | front 180° | budget-saver at short hops; rear features from the previous node |
| Stop verification | 18–22 | 4–12 | 360° | once or twice per episode, before a STOP |
| NavGPT VLA per step | ≥18 per 0.25 m | — | — | infeasible (500 actions ≈ 6 m of travel) |

The views are exact. ETPNav's rig consists of deep copies of the single sensor with only the orientation changed (`ss_trainer_ETP.py` L97-111 per A6), and TURNs rotate the body about the camera's vertical axis. A rotation sweep therefore reproduces the rig views bit-for-bit, except that human animation frames can differ.

Each TURN can never collide (A2 fact 4). After 11 two-turn steps to the right (330°), the agent faces 30° left of its starting heading, so the alignment turns to the chosen waypoint cost the same on average as without a sweep. The marginal cost is about 22 TURNs per decision.

**ETP-R1 episode budget.** Navigation primitives come from the vln-safe ETP-R1 slide arm: mean 91.7, p50 63, p90 201, p99 400 (my recomputation, `work/c9/budget.py`). Add 22 × D, where D is the number of decisions (`max_traj_len` 15; the released logs do not record D, so 6–8 is my estimate from about 12.8 m of path at about 2 m per hop):

| Percentile | Budget |
|---|---|
| Mean | about 225–270 |
| p90 | about 420–470 |
| Worst case | > 500 |

Required rules:
- (i) Reserve the last action for STOP. Success requires `is_stop_called` (A2 fact 24), so ending at 500 actions without STOP always fails.
- (ii) Once remaining < 22 × (expected remaining decisions) + 40, switch to front-half sweeps, or skip the sweep for hops < 1 m.
- (iii) Force a STOP decision at ≥ 470 actions.

My estimated SR loss from budget truncation is ≤1–2 points (inference: the over-budget tail is mostly backtracking failures already).

**SimpleVLN budget.** No sweeps. Monocular VLAs in vln-safe used 87–98 primitives per episode (StreamVLN; 3–6% of episodes hit the cap). SimpleVLN's own eval cap is 400. Set a hard STOP at 490.

---

## 4. Collision-guard integration (compliant)

The guard sits between the policy and the environment. It checks every primitive, including those inside chunks, because contacts happen mid-chunk (vln-safe `guard.py` docstring).

**Guard v1 (day 1–3): port vln-safe `stall-mem1`.**
- Depth veto when the projected clearance is < 0.05 m, with 1-frame memory.
- Stall veto: never repeat a forward from a pose where an earlier forward moved < 0.01 m.
- Escape by the smallest clear turn (≤ 90°) plus one forward; caps of 3 consecutive and 12 per episode.
- About 8.5 ms per step; pure numpy and py3.6-compatible.

Measured on R2R-CE without humans: ETP-R1 clean SR 37.7→50.1, StreamVLN 34.4→42.5, ETPNav 34.0→45.4. Raw SR is essentially unchanged (B2 Table A). Collisions are detected after the fact from the GPS pose delta (a forward that moved < 0.2499 m), which is allowed under Q9. The simulator's collided flag is not needed.

**Guard v2 (days 3–14): learned, still compliant.** Components:
1. **Episodic egocentric occupancy map.** 5 cm cells, height band 0.2–1.6 m (matching the navmesh's walkableClimb 0.2 m and walkableHeight 1.6 m), built from every depth frame and registered by exact GPS+compass. The camera at 1.25 m with a 90° vertical FOV sees the floor only beyond about 1.25 m, so near-field obstacles must come from memory. An optional LOOK_DOWN/LOOK_UP glance (2 actions, never a collision) can refresh the near field when it is unobserved.
2. **Learned step-collision predictor.**
   - Output: P(flag | pose, heading) for all 24 headings.
   - Model: a small CNN on (current depth, crop of the occupancy map).
   - Labels: privileged, from `try_step` on the 61 train scans. The label is "flagged on the base navmesh OR any of the 120 human-frame navmeshes" (conservative with respect to human timing).
   - Data: about 10–50 M states sampled along policy and DAgger rollouts.
   - Calibration: recall ≥ 0.995, because one flagged step fails the episode while a false veto only costs actions.
3. **Person keep-out.** GroundingDINO is already wired in `HASimulator/detector.py`; YOLO-seg is an alternative. Fine-tune it on auto-labelled HAPS renders from train scans (a depth difference with and without humans gives the masks; this is allowed under Q11 for training). Back-project the detections with depth and keep out a radius of 0.5 m plus the tracked motion envelope.
4. **Veto response.** Run A* on the inflated own map (0.15–0.25 m) towards the endpoint of the vetoed chunk, discretise to 15° / 0.25 m, check every forward with (2), then re-query the policy.
5. **Hard rule.** No navmesh, pathfinder or scene-mesh call at inference. Enforce it with an import-time guard and an `openat` provenance log (C3 §5).

**Expected effect (inference).** Close 50–75% of the gap between the depth guard and the oracle. That puts ETP-R1 at about 55–58 clean SR on human-free R2R-CE (vs 50.1 depth / 61.3 oracle), and SimpleVLN at about 0.80–0.88 × its raw SR (vs ETP-R1's 0.785 with depth and 0.98 with the oracle). The navmesh-oracle guard stays an upper-bound and label tool only.

**Human-timing robustness.** In local runs, VLM latency makes the wall-clock human animation freeze at about frame 119 within 12 s. The official replay will instead run at an unknown S steps/s and show earlier frames (C1). Two measures, both environment-side or agent-side and compliant:
- (a) Drive the local simulator's human clock with C1's deterministic `schedule(S)` (frame = min(119, ⌊i/(0.1·S)⌋)), calibrated to the measured replay speed of the official image. This is environment fidelity, not agent input.
- (b) Keep-out margins larger than the observed motion.

Measure local vs official-replay deltas on val tapes with `havln-score-phase1` in four modes. Never edit a test tape based on its replay result (C3 T13).

---

## 5. Fine-tuning on HA-R2R train with privileged collision-free experts

**Clearance teacher (allowed per Q11).**
- Plan on a navmesh rebuilt per train scan with all 120 frames of every human loaded as STATIC objects at agent_radius 0.25–0.30 m. Fall back to 0.20 m where it disconnects (A2 rule 2). Plan the geodesic path to the goal.
- Emit rotate-then-forward primitives: align within ±7.5° before straight runs and stay centred in corridors.
- Verify zero flags by kinematic `try_step` replay on the base navmesh plus the 120 frame navmeshes at r = 0.1.
- STOP at the reachable point nearest the goal, outside any human keep-out.
- Because it is a planner, it labels any off-route DAgger state.

It replaces the toolkit expert. That expert is a `GreedyGeodesicFollower` on a 0.1 m-eroded navmesh that accepts sliding steps (A6 §2).

**Training data** (official camera 224² RGB / 256² depth, HFOV 90, humans inserted):
- HA-R2R train: 10,819 episodes over 61 scans; `train.json.gz` sha256 `568f966e…`, from A11;
- R2R-CE train with original instructions on the same paths;
- RxR-CE English train;
- optionally EnvDrop/ScaleVLN instructions rewritten in HA style with the organizers' prompt.

HA-R2R val and test are never used for training (Q10). Val_unseen is used only for model selection.

**SimpleVLN SFT/DAgger.** No SimpleVLN training code is released, so use generic Qwen-VL SFT tooling (ms-swift, LLaMA-Factory or TRL).
- Reconstruct the single-turn prompt exactly from `eval.py`: system prompt "You are a visual language navigation model."; history = 8 uniformly sampled frames plus the current frame; the instruction template at L161-164.
- Targets are the chunk strings the inference parser expects: ≤2 sub-actions, each 25–75 cm or 15–45°, split on ", ", or "stop". Copy the exact output format from logged zero-shot generations before training.
- Schedule: round 0 = expert-only SFT; rounds 1–3 = DAgger with β_k = 0.5^k (as in HA-VLN's `p = 0.5`), aggregating all rounds.
- Expected per round (inference): about 325 k decision samples, about 1–3 B tokens, about 6–11 h on 8×H100 for 8–9B (about half that for 4B).

**RFT (preferred over full GRPO for the timeline).**
- For each train episode, sample K = 4–8 rollouts at T = 0.7.
- Keep those with success ∧ 0 collisions, evaluated on the conservative union navmesh.
- SFT on them together with the expert data.

SimpleVLN reports +7.5–10.2 SR from RL with a binary success reward on R2R-CE. RFT is the cheap proxy; I expect +3–6 SR (inference). Stretch goal: GRPO with reward = 1[success ∧ collisions = 0] + 0.2·3/(3+NE) − 0.05·collision_steps.

**ETP-R1.** Reuse its own `SS-ETP-R1` DAgger trainer (upstream: 30 k iterations, 4 GPUs × 8 envs, sample_ratio 0.75) and its `GRPO-R1` trainer (500 iterations, 8 samples per episode). Changes:
- (a) Replace the reward. It is currently SPL + success@1.5 m + (1 − d/6) with no collision term (`GRPO_trainer_ETP_R1.py` L1095-1096); use the challenge objective above.
- (b) Raise `max_text_len` from 150 to 320 (XLM-R has 514 positions).
- (c) Use an env wrapper that calls HAVLNCE human insertion (`_handle_signals()` before each step, exactly like `HAVLNCEDaggerEnv`, `vlnce_baselines/common/environments.py` L48-74).
- (d) Use `back_algo control` in training rollouts as well.
- (e) Train with the simultaneous 12-camera rig for speed (its views equal the sweep's), and run inference with sweeps.
- (f) Retrain the CWP waypoint predictor on human-inserted navmeshes so ghost nodes avoid people (HCSG-style).

**How a new policy plugs into the toolkit's `DaggerTrainer`** (`dagger_trainer.py`, `base_il_trainer.py`). It provides the scaffolding below, which only fits small recurrent policies (CMA/Seq2Seq). Use it solely to reproduce and calibrate CMA.
- `_initialize_policy` builds `baseline_registry.get_policy(MODEL.policy_name)`. The policy must expose `act(batch, rnn_states, prev_actions, masks, deterministic)`, `build_distribution`, `net.num_recurrent_layers` and `net.instruction_encoder` (base_il_trainer L65-110).
- The expert is the `SHORTEST_PATH_SENSOR` observation uuid, mixed in with probability β = p^it (L285-292, L413-417).
- RGB and depth encoder outputs are cached to LMDB through forward hooks (L294-351).
- The whole lmdb is retrained 4 epochs per round (A6).

---

## 6. Multi-rollout self-consistency (tiered by compliance)

| Tier | Mechanism | Compliance | Expected gain (inference) | Cost |
|---|---|---|---|---|
| T1a | Per decision: K = 5 samples (T 0.3–0.7) from one model, majority vote on the first sub-action (type + magnitude) | compliant (ensemble policy, no reset) | +1–3 SR | K× VLM calls |
| T1b | Multi-model vote (SimpleVLN-4B / 9B / Qwen3-VL-8B; ETP-R1 graph as a waypoint prior) | compliant | +1–3 SR | |
| T1c | STOP needs ≥ 60% of the K votes; otherwise continue with the majority non-stop action | compliant | +1–2 SR (fewer early stops) | |
| T1d | Stop verifier: when STOP is voted, sweep 18–22 TURNs and let a VLM judge "does this place satisfy the last clause?"; on a confident no, continue. Sweep frames are excluded from the VLA's history | compliant (turns counted; no SPL term) | +1–3 SR | ≤ 2 sweeps per episode |
| T2 [gray] | K full rollouts per episode with environment resets; choose by stop-location consensus and a learned success/collision critic over the agent's own observations | simulator branching (C3 T3): use only if organizers allow | +6–10 SR (B2: union of 2–3 agents' stops is within 3 m in 82.7–87.2% of episodes vs 67.5% for the best single agent) | K× |
| T3 [gray] | Consensus across the 3 sibling instructions of a trajectory (ids 3k+1..3k+3 share start and goal) | cross-episode use of test inputs: ask | unknown, likely +3–6 SR | |
| forbidden | GPS-rewind (reset and replay a prefix to dodge a detected collision); reading replay collision results to edit test tapes | non-compliant (A6 §8.6, C3 T13) | — | — |

---

## 7. GPU and agent plan

| Pool | Hardware | Jobs |
|---|---|---|
| A: simulation | 4 nodes × 8 GPUs (24–48 GB), EGL | challenge image (py3.8, habitat 0.1.7 + HASimulator) env servers, 8–16 processes per GPU; navmesh caches (train 61 + val_unseen 11 + test 18 scans × 120 frames) |
| B: VLM serving | 16–32 × H100/A100-80G | vLLM 0.18 replicas of SimpleVLN 4B/9B (1 GPU each), VLM stop verifier, person detector |
| C: training | 16–32 × H100 | SFT/DAgger/RFT jobs (8 GPUs each, ZeRO-3); ETP-R1 DAgger/GRPO (4–8 GPUs); Guard v2 CNN (1 GPU) |
| D: CPU | 2 × 64-core | privileged label generation (`try_step` on 121 navmeshes, 20–60 k steps/s/core per C1), expert planning |

**Throughput (inference).**
- val_unseen pass (1,839 episodes × about 30 decisions): < 30 min at K = 1 and about 1–2 h at K = 5 on 16 replicas plus 128 env processes.
- test pass (3,408 episodes): about 1.9× val.
- Expert data generation (about 2.5 M frames): minutes.
- DAgger collection round: < 1 h.
- RFT collection (K = 4 on 10.8 k episodes, about 1.3 M decisions): 1–2 h on 32 replicas.

Total to Nov 30 is about 5–10 k GPU-h, far below "unlimited". The bottleneck is bring-up, not FLOPs.

**Coding agents (about 12–14).**

| Work package | Agents | Scope |
|---|---|---|
| WP-ENV | 2 | env server, sandbox, tape writer, `schedule(S)` human clock, official replay checks |
| WP-VLA | 2 | SimpleVLN client, vLLM serving, voting, stop verifier |
| WP-GUARD | 3 | occupancy map, learned step predictor, person keep-out, escape planner |
| WP-EXPERT | 2 | clearance teacher, data generation, DAgger driver |
| WP-TRAIN | 2 | SFT, RFT, optional GRPO |
| WP-ETP | 2 | ETP-R1 HA port, sweep adapter, GRPO reward |
| WP-EVAL | 1 | metrics, ablations, report |

---

## 8. Dated milestones (compliant track; SR/Score = expected on HA-R2R test, inference)

| Date | Milestone / gate | Contents | Expected SR | Expected Score |
|---|---|---|---|---|
| Sat Oct 24 – Mon Oct 26 | **G-A bring-up** | env server in the challenge image on public scene 17DRP5sb8fy (10 humans; R2R train and val_seen, per A11); SimpleVLN client + vLLM (3 checkpoints); vln-safe ETP worker env; Guard v1 port; tape writer; tape replays identically in `havln-score-phase1`; MP3D requests chased | — | — |
| Tue Oct 27 – Fri Oct 30 | **M1** (needs MP3D) | val_unseen zero-shot: SimpleVLN ×3 checkpoints × {no guard, Guard v1} at 224²; ETP-R1 with sweeps; Guard v2 label generation started; a genuine Phase-1 submission if CodaBench is up (calibration only) | val_unseen 0.28–0.38 | 25–34 |
| Sat Oct 31 – Mon Nov 2 | **M1-test**: first compliant test submission | Phase 2 bundle inventory (test human placements?); test navmesh cache; best zero-shot + Guard v1 | 0.28–0.36 | 25–32 |
| Tue Nov 3 – Mon Nov 9 | **M2** | expert SFT round 0 → DAgger round 1 (SimpleVLN-4B/9B); Guard v2 integrated; person keep-out; ETP-R1 HA SFT; **choose the primary backbone by val_unseen Score on Nov 9** | 0.40–0.47 | 36–43 |
| Tue Nov 10 – Mon Nov 16 | **M3** | DAgger rounds 2–3; T1a–d voting and stop verifier; human-timing robustness (4-mode replay deltas); budget logic | 0.46–0.54 | 42–50 |
| Tue Nov 17 – Fri Nov 20 | **M4 = architecture freeze (Nov 20)** | one RFT round (or GRPO if infrastructure is ready); final guard thresholds; ablation table | 0.50–0.60 | 46–55 |
| Sat Nov 21 – Tue Nov 24 | final run | hyper-parameters chosen on val_unseen only; full test inference at K = 5 (about 3–6 h); format, ≤500 and STOP checks; upload | 0.50–0.60 | 46–55 |
| Wed Nov 25 – Fri Nov 27 | **G8** | final candidate confirmed scored; 2 reserve uploads | | |
| Sat Nov 28 – Mon Nov 30 | buffer | no new experiments | | |
| Dec 1 – Dec 12 | report | disclosure template (C3 §11), ablations, provenance log | | |

**Stretch.** If the organizers publicly permit T2 multi-rollout selection: SR 0.62–0.68, Score about 58–62.

**Slip rules.**
- MP3D after Nov 1: shift M1–M2 one-for-one and drop ETP-R1 GRPO.
- MP3D after Nov 7: SimpleVLN + Guard v2 + one SFT round only, for an expected Score of about 33–40.
- No MP3D at all: the compliant track is impossible.

---

## 9. Minimum viable version (7–10 days, 3–4 agents)

**MVP-1** = SimpleVLN (Qwen3.5-9B-RL or 4B-RL, zero-shot, official 224² camera) + vln-safe Guard v1 (depth + stall) + depth-only person keep-out + budget and STOP rules, in the official env. Staffing:
- agent 1: env server + tape writer + official replay;
- agent 2: SimpleVLN client + vLLM + guard port;
- agent 3: evaluation and metrics;
- agent 4 (optional): ETP-R1 sweep port as a parallel alternative.

Expected test SR is 0.28–0.36 (Score 25–32). That is already above every verified published HA-VLN-CE number (HCSG SR 0.24, about Score 22).

---

## 10. Facts (verified from local code; confidence)

1. **[high]** NavGPT-3's VLA-only evaluation calls `observe_pano` (4 simultaneous RGB-D cameras at 400×400, HFOV 120, yaws 0/90/180/270; "Costs ZERO simulator steps") and then `teleport` to the VLA's waypoint 1. The service is built with `view_num=4`, and the client requires all four views. Evidence: `navgpt/planner/vla_only.py` L66-95; `navgpt/environment/r2r.py` L98, L821-856, L1357-1361, L1706-1780; `navgpt/vla/api.py` L132; `navgpt/planner/tools/vla_client.py` L1-30, L181-246.
2. **[high]** NavGPT VLA outputs 8 cumulative agent-relative (x, y, θ) waypoints on a 0.125 m grid and never emits STOP. Stopping is a client heuristic: two consecutive collapsed horizons, with the last waypoint < 0.25 m and |θ| < 30°. The VLA configs set `turn_angle_deg: 30` ("used only by blocked-step turns"). A teleport to a navigable target never increments collisions. Evidence: `vla_client.py` L14-24, L36-45, L116-135; `configs/experiments/vln/vla_8b_r2r.yaml`; `r2r.py` L76-85, L1727-1760.
3. **[high]** SimpleVLN inference works as follows:
   - system prompt "You are a visual language navigation model.";
   - 8 uniformly sampled history frames plus the current RGB frame;
   - temperature 0.3, top-p 0.95;
   - it keeps the first 2 sub-actions of each generation and expands each into ≤3 primitives of 0.25 m / 15°;
   - eval camera RGB 640×480 HFOV 90, max 400 steps; history window 200 frames; pass@4 in the launcher.

   Evidence: `eval/vln/eval.py` L36, L136-160, L296-380; `eval/config/vln_r2r.yaml`; `eval/scripts/eval.sh`.
4. **[high]** SimpleVLN R2R-CE val-unseen SR/SPL after RL: Qwen3.5-9B 76.7/72.6, Qwen3.5-4B 76.3/72.3, Qwen3-VL-8B 74.4/69.5. Before RL: 69.2/61.2, 67.1/59.2 and 64.2/57.0. Weights are on HF `honglyhly/SimpleVLN_*`. No training code is released. Evidence: `SimpleVLN/README.md` L81-114.
5. **[high]** ETP-R1's R2R rig is RGB 224×224 HFOV 90 plus depth 256×256 HFOV 90, 0.25 m / 15°, sliding, matching the official `HAVLNCE_R2R_task.yaml`. Settings: `max_traj_len` 15, `max_text_len` 150. Training: DAgger 30 k iterations on 4 GPUs × 8 envs, then GRPO 500 iterations with sample_num 8; eval uses `IL.back_algo control`. Evidence: `ETP-R1/run_r2r/r2r_vlnce.yaml`; `iter_train.yaml` L61-62; `main_server.bash` L25-96; `HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml` L16-25.
6. **[high]** ETP-R1's GRPO reward for R2R is SPL + success (≤1.5 m) + (1 − d/6). It has no collision term. Evidence: `ETP-R1/vlnce_baselines/GRPO_trainer_ETP_R1.py` L1090-1096.
7. **[high]** Official camera: RGB 224×224, depth 256×256, HFOV 90 (habitat-lab default), sensor position [0, 1.25, 0], depth 0–10 m normalised. The clarification says "One forward-facing RGB-D camera … panoramic views must be acquired by rotating in place (rotation actions count toward the action budget)". It does not state whether resolution may change. Evidence: `HAVLNCE_R2R_task.yaml` L16-25; `habitat-lab-0.1.7/habitat/config/default.py` L226-241; `jostar-track2` `git diff origin/main origin/bohan/clarification-Oct14 -- README.md` (Sensor Setup row, Q8).
8. **[high]** vln-safe per-episode logs for R2R-CE val_unseen (my recomputation):

   | Arm | Raw SR | Clean SR | Mean steps | p50 | p90 | p99 |
   |---|---|---|---|---|---|---|
   | ETP-R1 slide | 64.6 | 37.7 | 91.7 | 63 | 201 | 400 |
   | ETP-R1 + stall-mem1 guard | 63.8 | 50.1 | 90.5 | — | — | — |
   | ETP-R1 + oracle guard (block) | 62.6 | 61.3 | — | — | — | — |
   | StreamVLN slide | 56.0 | 34.4 | 97.5 | — | — | — |
   | StreamVLN + guard | 56.7 | 42.5 | — | — | — | — |

   StreamVLN slide hits the 500-step cap in 117 of 1,839 episodes. Evidence: `work/c9/budget.py` over `ext/sota/vln-safe/results/*/r2r/*/episodes.csv`.
9. **[high]** vln-safe's guard checks every executed primitive, including primitives inside chunks. stall-mem1 settings: threshold 0.05 m, memory 1 frame, stall 0.01 m, escape ≤ 90°, caps 3 consecutive / 12 per episode. The oracle variant uses the navmesh, i.e. "simulator state no deployed agent has". Evidence: `vlnsafe/guard.py` L1-60; `configs/guard/stall-mem1.yaml`, `oracle-mem1.yaml`.
10. **[high]** The HA-VLN `DaggerTrainer` plug-in contract is a registry policy with `act` / `build_distribution` / recurrent states, plus an expert from the `SHORTEST_PATH_SENSOR` uuid mixed in with β = p^it, plus LMDB feature caching through forward hooks. `HAVLNCEDaggerEnv` inserts humans by calling `havlnce_tool._handle_signals()` before each step. Evidence: `dagger_trainer.py` L248-300, L405-445; `base_il_trainer.py` L65-110; `common/environments.py` L48-74.
11. **[high]** HASimulator ships a GroundingDINO detector wrapper (`HASimulator/detector.py`) usable for person detection.
12. **[medium-high]** C3's CLEAN-1 spec allows forward RGB-D at the official resolution, GPS+compass and per-step compute. It excludes the navmesh/pathfinder, human files, cross-episode memory, pre-exploration and simulator branching. Evidence: `findings/C3-rules-ethics-and-defensibility.md` L98, L139-160.

## 11. Key numbers

| What | Value | Source |
|---|---|---|
| Minimum TURNs for a 360° view with an HFOV-90 camera | 18 (270° / 15°) | geometry |
| TURNs for ETP-R1's 12 × 30° ring | 22 | rig spec + 15° turns |
| ETP-R1 primitives per episode (mean / p50 / p90 / p99) | 91.7 / 63 / 201 / 400 | vln-safe logs (budget.py) |
| ETP-R1 projected actions with sweeps (mean / p90) | ≈ 225–270 / 420–470 (D = 6–8 estimated) | inference |
| Clean SR, R2R-CE human-free: ETP-R1 unguarded / depth guard / oracle | 37.7 / 50.1 / 61.3 | vln-safe logs |
| SimpleVLN R2R-CE SR: 9B / 4B / Qwen3-VL-8B (after RL) | 76.7 / 76.3 / 74.4 | SimpleVLN README |
| NavGPT VLA 8B R2R-CE SR (4 cameras, HFOV 120, teleport) | 76.94 | NavGPT-3 README |
| Score check: CMA val_unseen | 12.9 (README 12.945) | score.py |
| Expected test Score by milestone (Nov 2 / 9 / 16 / final) | 25–32 / 36–43 / 42–50 / 46–55 | score.py, inference |
| Score sensitivity at SR 0.5 | +0.77 per +0.01 SR; +1.25 per −1 m NE; +2.8 for colliding-episode share 0.20→0.05 | score.py |
| Guard compute | 8.5 ms per step | vln-safe runtime.json (B2) |
| GPU-h to Nov 30 (plan) | ≈ 5–10 k | inference |

## 12. Corrections and flags vs sibling findings

- **B3**: "NavGPT-3 … runs with the challenge's own 0.25 m / 15° action space … directly runnable on HA scenes" is wrong for the VLA path. Its SR comes from 4 simultaneous HFOV-120 cameras plus teleport execution, so it is neither compliant nor primitive-replayable as released. Its collision semantics are not comparable: teleports never count collisions.
- **B2 / A6**: the navmesh-oracle guard ("privileged, legal in offline replay") is NOT allowed at inference under the clarification. Use it only for labels, teachers and upper bounds.
- **A6**: Uni-NaVid's HFOV 120 cannot come from the official HFOV-90 camera, so drop it from the "lowest integration risk" option. NaVid at HFOV 90 remains feasible.
- **OmniNav**: also non-compliant natively (3 simultaneous HFOV-110 cameras).
- **B2**: the ensemble union recall of 87% requires several rollouts per episode, which is [gray] (simulator branching) in the compliant regime.
- No contradiction with CONTEXT facts 1–8.

## 13. Implications

- The compliant leaderboard will probably be decided at SR 0.3–0.6. Every point of zero-collision execution is worth about as much as a point of language grounding: about 0.77 Score per 0.01 SR.
- Under the one-camera rule the strongest raw-SR open models (NavGPT VLA, OmniNav) are unusable. The usable frontier is SimpleVLN (monocular) and ETPNav-family graph agents with sweeps.
- Privileged information remains very valuable, but only through training: clearance teachers, navmesh-labelled collision predictors, auto-labelled person detectors, and RFT/GRPO rewards computed on union-of-frames navmeshes.
- Without test-scan human placements in the Phase 2 bundle, no compliant agent can avoid test humans. This is the top organizer question, shared with C2 R2.

## 14. Recommendations

1. Today, start WP-ENV (env server on 17DRP5sb8fy in the challenge image) and WP-VLA (SimpleVLN 3 checkpoints on vLLM) in parallel. Port vln-safe Guard v1 as-is.
2. Treat the official 224² camera as binding. Ask the organizers whether rendering the same forward camera at 640×480 is allowed, and keep a config switch.
3. Bring up ETP-R1 with sweeps in parallel. On Nov 9 decide on val_unseen Score which backbone gets the RFT/GRPO budget, and keep the other as a fallback.
4. Build Guard v2 (learned step predictor on privileged navmesh labels plus a person keep-out) before any language fine-tuning. It is the largest single lever.
5. Replace the toolkit expert with the union-of-frames clearance teacher for all DAgger/SFT data. Render at the official camera with humans present.
6. Use only T1 self-consistency. File the T2/T3 questions with the organizers (C3's issue draft), and keep both disabled unless permitted publicly.
7. Never touch the navmesh, pathfinder, human files or R2R_test.json at inference. Enforce this with a sandbox and a provenance log.
8. Freeze the architecture on Nov 20, upload the final candidate by Nov 24–25, and confirm G8 by Nov 27.

## 15. Open questions

- Will the Phase 2 bundle contain human placements for the 18 test scans? Without them, local closed-loop runs cannot render test humans.
- May the single forward camera be rendered at a different resolution or aspect (640×480) than 224²?
- Are multi-rollout selection (T2) and sibling-instruction consensus (T3) permitted?
- SimpleVLN's zero-shot clean SR at 224² with HA instructions and humans. This is the first measurement to make, around Oct 27–29.
- The actual decision count per episode of ETP-R1 (needed for the exact sweep budget). Measure it in bring-up.
- How fast does the official replay run (S steps/s)? It sets which human frames the scorer shows. Calibrate with `havln-score-phase1`.
- Does current Qwen-VL SFT tooling support Qwen3.5 checkpoints? (Unverified; fall back to Qwen3-VL-8B.)
- License terms for SimpleVLN and NavGPT-3 weights (not visible locally).

## 16. Sources

- `ext/sota/SimpleVLN/{README.md, eval/vln/eval.py, eval/config/vln_r2r.yaml, eval/scripts/eval.sh}`; arXiv 2610.23203
- `ext/B3/metacognitionai_NavGPT-3/{README.md, navgpt/environment/r2r.py, navgpt/planner/vla_only.py, navgpt/planner/tools/vla_client.py, navgpt/vla/agent.py, navgpt/vla/api.py, configs/experiments/vln/vla_8b_r2r.yaml}`; arXiv 2610.10787
- `ext/sota/ETP-R1/{README.md, run_r2r/r2r_vlnce.yaml, run_r2r/iter_train.yaml, run_r2r/main_server.bash, vlnce_baselines/GRPO_trainer_ETP_R1.py, vlnce_baselines/common/environments.py}`; arXiv 2512.20940
- `ext/sota/vln-safe/{vlnsafe/guard.py, configs/guard/*.yaml, docs/agent_notes/{etpr1,omninav}.md, configs/agents/*.yaml, results/*/r2r/*/episodes.csv}`; arXiv 2610.14682
- `ext/sota/HCSG/README.md` (code unreleased); `ext/sota/OmniNav/README.md`
- `ext/HA-VLN/{HASimulator/config/HAVLNCE_R2R_task.yaml, HASimulator/detector.py, HASimulator/environments.py, agent/VLN-CE/vlnce_baselines/dagger_trainer.py, common/base_il_trainer.py, common/environments.py, habitat_extensions/sensors.py}`
- `ext/habitat-lab-0.1.7/habitat/config/default.py`
- `ext/jostar-track2` (branch `bohan/clarification-Oct14`, README diff)
- Findings: B2, B3, A2, A6, A11, C1, C2 and C3 under `scratchpad/findings/`
- Scripts: `scratchpad/work/c9/budget.py`, `scratchpad/work/c9/score.py`
- WebSearch budget exhausted. No online verification of HF weights or licences was possible.
