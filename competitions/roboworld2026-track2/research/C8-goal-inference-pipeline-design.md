# C8: Goal-inference pipeline design. (A) Compliant closed-loop goal inference; (B) privileged offline candidate ranking (permission-gated)

topic_id: `C8-goal-inference-pipeline-design` | 2026-10-24 | research/design agent C8
Abbreviations: `S` = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad`, `EXT` = `S/ext`. My scripts are in `S/c8_scripts/` (run with `python3 -I`). WebSearch was not used, because the budget was exhausted. Everything here rests on local material: the sibling findings A1, A2, B1, B2, B3, B4, B5, B8, B12, C1 and C3, the cloned repos, and three new computations described below.

## 0. Regime map (read first)

The organizer clarification is on the unmerged branch `bohan/clarification-Oct14`. It is treated as binding: at inference the agent may use only the episode ID, initial pose, instruction, GPS+compass, and one forward RGB-D camera. Panoramas must be built by rotating, and those turns count toward the 500-action budget. `human_motion.json` is banned at inference, and HA-R2R val/test may not be used for training. Every component below carries one of these tiers (same tiers as B8 §3 and C3):

| Tier | Meaning | Components in this design |
|---|---|---|
| **T0** compliant | Only the inputs above, inside ONE closed-loop tape | Pipeline **A-ST** (single tape: explore, verify, commit); instruction parsing/condensation of the episode's own text; models trained on train split / external data; own-map shield; contact detection from own pose; physical backtracking |
| **T1** compliant, disclose | Input-compliant engineering choices | Open-weight vs closed-API judges; camera resolution changes of the single forward camera; deterministic seeds |
| **T2** gray, ask in writing | Not addressed by the rules | **A-MR**: many independent local rollouts per test episode, then selecting one tape by self-consistency and pose-detected contact-freeness; prefix truncation of a rollout; "re-drive" using memory from earlier rollouts (= pre-exploration); timing-robustness re-replays; sibling-instruction ensembling; fitting a calibrator on HA-R2R val |
| **PRIV** | Needs explicit organizer permission | Pipeline **B**: test-scan nav graph / mesh / navmesh / `.house` semantics / arbitrary-viewpoint renders / released MP3D features at inference |
| **T3** do not use | Banned or red line | `human_motion.json` at inference (Q11); HA-VLN 1.0 test human annotations (`human_motion_text.json`) at inference; original R2R test instructions (C3 calls this a red line); `collision_num_test.json` at inference; the `sample_room_paths.json` leak of 366 R2R test goals (B12; quarantine); training on val/test; leaderboard probing |

**Bottom line.** Pipeline A comes in two variants. A-ST is the default official entry and is unambiguously T0. A-MR is an upgrade, measured below, that needs an organizer answer before it ships. Pipeline B is designed in full but only goes live if the organizers explicitly permit scene geometry at inference. Even then it must not read human placements, the original R2R instructions, or the test leaks.

## 1. Summary

Goal inference decides the leaderboard. With collision-free execution, each +1 point of SR is worth about +0.8 to +1.0 Score (my projection: +0.79 per point at SR 0.70; B1: +1.03).

**(A) Compliant pipeline.** A closed-loop agent built from a pool of public policies. Each policy is adapted to one forward camera plus rotation-built panoramas, and wrapped in an own-map collision shield that uses depth and exact pose. The agent keeps a per-episode metric and topological memory with captions, person detections and activity captions. Endpoint decisions use comparative VLM judgments over the agent's own observations, plus a Bayes stop.
- **A-ST (T0, single tape).** Uses the absence of any path-length term in the Score: the agent may verify its stop, visit a runner-up endpoint (about 40-60 actions round trip, B5) and backtrack, all inside one tape of at most 500 actions.
- **A-MR (T2, many rollouts).** Runs R = 8-16 independent rollouts per episode (4 policies × variants). All rollouts share the start frame, so stop points are directly comparable in GPS coordinates. Stop points are clustered, the clusters scored by a conditional-logit fusion of votes, judge, speaker and structure features, and a contact-free tape (or a prefix of one) is chosen. Contact is detected exactly from the agent's own pose: a MOVE_FORWARD collided iff |Δp|² + 1e-5 < 0.0625, the habitat-sim 0.1.7 rule (A2).

**New measurement.** On the vln-safe per-episode logs (human-free R2R-CE val_unseen, HA-identical physics), simply taking the first contact-free tape among three depth-guarded agents (ETP-R1, ETPNav, StreamVLN) gives **62.4% clean SR, vs 50.1% for the best single guarded agent**. The contact-free union is 73.4% and the raw union 84.0%. Contact-free tapes are also more often successful (ETP-R1 guarded: P(success | no contact) 0.69 vs 0.49 with contact). So pose-detected contact is both a filter and a goal-quality signal.

**Projected compliant numbers on HA-R2R test (inference):** A-ST 0.55-0.70 SR (Score ~52-63); A-MR 0.65-0.77 (Score ~62-71). The best verified published HA-VLN-CE result is about 22 Score (HCSG).

**(B) Privileged pipeline.** Candidate goals are nav-graph nodes 3-6 hops and 5-25.5 m from the start: 100% recall on 5,798 train/val paths, median 25 per test start, about 8-9 clusters (A1/B1/B12). Path features come from MP3D semantics. The instruction is parsed by an LLM. Scorers: DUET-family follower teacher-forced log-likelihoods, an HA-trained speaker, a fine-tuned Qwen3-VL listwise ranker, a text-only LLM listwise judge, and an entropy-gated frontier VLM comparative judge over renders without humans. These are fused by a log-linear conditional logit fitted on leave-scans-out train folds. The stop is the Bayes-optimal point under the Euclidean 3-D 3 m rule.

**Expected goal-within-3 m accuracy per trajectory:**

| B variant | Accuracy | Score (clean execution) |
|---|---|---|
| Own HA instruction only | 78-86% | ~77 |
| + sibling HA instructions (T2) | 82-89% | ~82 |
| + original R2R instructions (T3 unless allowed) | 85-92% | ~85 |

**New risk quantified.** On val_unseen, 38% of reference routes pass within 0.3 m of an HA 2.0 human position (any frame), yet only 8.6% of trajectories have collision_num > 0. Any human-blind execution would therefore expose up to roughly a third of episodes to collisions. Two cases make execution human-blind: Pipeline B executing on a human-free navmesh, or local runs of A when test-scan humans are not shipped for rendering. Human perception is therefore mandatory in both pipelines.

**Two corrections to sibling findings:**
- NavGPT-3's 76.94 SR VLA uses a 4-camera simultaneous panorama rig and executes waypoints by teleport (`set_agent_state`), not primitives, so it is not directly compliant (corrects B3).
- Group test episodes by ID triple, never by start pose (A1). The topic brief's "group by scan+start pose" would merge different goals for 51% of trajectories.

## 2. New evidence computed for this design

1. **Contact-free tape selection (vln-safe logs)**, `S/c8_scripts/vlnsafe_select.py` over `EXT/sota/vln-safe/results/*/r2r/*/episodes.csv` (1,839 val_unseen episodes, Habitat 0.1.7, radius 0.1 m, sliding; collision_count = previous_step_collided, identical to HA's count):

| Selector (first contact-free tape in priority order) | Clean SR | Contact-free union (oracle selector) | Raw union |
|---|---|---|---|
| ETP-R1 + depth guard alone | 0.501 | 0.501 | 0.638 |
| + StreamVLN guard | 0.593 | 0.664 | 0.792 |
| + ETPNav guard | **0.624** | 0.734 | 0.840 |
| + unguarded ETP-R1/ETPNav/StreamVLN arms | 0.626 | 0.741 | 0.864 |
| + OmniNav (not natively compliant) | 0.632 | 0.773 | 0.911 |
| ETP-R1 + StreamVLN, navmesh-oracle guard (privileged reference) | 0.642 | 0.778 | 0.788 |

   No contact-free tape exists among the 3 guarded agents in 8.3% of episodes, and among 7 arms in 7.0%.

   P(success | contact-free) vs P(success | contact):

| Agent | Contact-free | Contact |
|---|---|---|
| ETP-R1 guarded | 0.694 | 0.494 |
| StreamVLN guarded | 0.630 | 0.436 |
| OmniNav | 0.733 | 0.636 |

   Steps per episode (12-camera rig, no rotation cost):

| Agent | Mean | p90 | p99 |
|---|---|---|---|
| ETP-R1 guarded | 90.5 | 182 | 376 |
| StreamVLN guarded | 86.8 | 132 | 500 |

2. **Human-blind exposure.** `S/c8_scripts/human_blind.py` and `S/c8_scripts/human_goal.py`, over R2R reference polylines (connectivity poses → Habitat (x, z−h, −y)) and `EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json` (all frames, same-floor filter; the frame was checked with `human_frame_check.py`: humans sit a median 1.06 m from their anchor viewpoint, 30.5% within 0.3 m, y ≈ floor + 0.84 m):

| Split | Routes within 0.3 m of a human | 0.45 m | 0.6 m | Trajectories with collision_num > 0 |
|---|---|---|---|---|
| val_unseen | 38.0% | 39.2% | 42.7% | 53/613 = 8.6% |
| val_seen | 34.0% | 40.5% | 44.0% | 20/259 |

   - Only 32 of the 233 exposed val_unseen trajectories have collision_num > 0. Inference: collision_num is the count for a human-aware navmesh follower that routes around human holes, not for a straight route.
   - Distance from the goal viewpoint to the nearest human (val_unseen): within 0.5 m in 3.6%, 1.0 m in 9.6%, 1.5 m in 16.2%, 3 m in 50.1%.
   - Start within 0.5 m of a human: 6.7%.
3. **NavGPT-3 VLA execution model (corrects B3).**
   - `EXT/B3/metacognitionai_NavGPT-3/navgpt/planner/vla_only.py` L60-95: each step calls `observe_pano` (4 simultaneous cameras, 400 px, HFOV 120; `navgpt/environment/r2r.py` L821-849), then `__teleport` to the predicted waypoint.
   - `teleport()` calls `set_agent_state` when the target is navigable, and falls back to one primitive otherwise (r2r.py L1706-1760). The VLA-only config uses `turn_angle_deg: 30` (configs/experiments/vln/vla_8b_r2r.yaml).
   - So 76.94 SR is not a single-camera, primitive-tape number. It needs (a) waypoint → turn/forward quantization (vln-safe's OmniNav precedent: 69.5 → 67.5) and (b) a single-camera mode. `view_num=1` weights exist in agent.py L27-40, but that mode is likely out of distribution. Rotating for 4 views costs about 18-24 turns per VLA step, which cannot be afforded every step.
4. **Score projections**, `S/c8_scripts/score_proj.py` (README formula):

| Scenario | Score |
|---|---|
| CMA | 12.95 |
| HCSG-level | 22.5 |
| A-ST single shielded policy (SR .55) | 52.5 |
| A-ST + verify (SR .60) | 56.9 |
| A-MR contact-free selection (SR .66) | 62.4 |
| A-MR + self-consistency + judge (SR .71) | 66.9 |
| A-MR + re-drive (SR .75) | 70.6 |
| B-1 (acc .82) | 77.6 |
| B-3 (acc .86) | 81.7 |
| B-6 (acc .89) | 84.8 |
| B-1 executed human-blind with 10% human hits | 69.6 |
| Perfect goal | 97.0 |

## 3. Pipeline A: compliant closed-loop goal inference

### 3.1 Architecture

```
instruction ─► [P1 parse] ─► clause list, end condition, human cues, floor change, length prior
            └► [P2 condense] ─► R2R-style 25-40-word rewrite (own text only)
RGB-D + pose ─► Perception: depth+pose TSDF/occupancy (5 cm), person detector+tracker (RGB-D),
                activity captioner (Qwen-VL 7-8B), room-type head, open-vocab objects
            ─► Episode memory: metric map + topological nodes (every waypoint decision / 1.5 m)
Policy pool (proposers, each behind the SHIELD): SimpleVLN-9B | StreamVLN | ETP-R1 (rotation pano) | NavGPT-VLA-8B (adapted)
SHIELD: veto MOVE_FORWARD if predicted end cell is not free in own map (inflate 0.10 m + 0.15-0.25 m margin;
        humans: tracked swept footprint + 0.3-0.5 m); escape by smallest clear turn; GPS check after every forward
A-ST:  drive ─► at policy STOP or progress≈end: 360° sweep (24 TURN) ─► [P4 verifier over memory]
       ─► commit (navigate to Bayes stop node, STOP) | continue (≤N steps on alternative proposal) | backtrack
A-MR:  R rollouts ─► stop-point clusters in start-GPS frame ─► features ─► conditional-logit fusion
       ─► [P3 judge, entropy-gated] ─► Bayes stop ─► choose contact-free tape / prefix ─► (T2) re-drive
```

### 3.2 Policy pool and compliance adaptation

| Policy | Native rig / actions | Compliant adaptation | Extra actions | R2R-CE val_unseen evidence | Expected HA-R2R raw SR after HA fine-tune (inference) |
|---|---|---|---|---|---|
| SimpleVLN Qwen3.5-9B | 1 RGB 640×480 HFOV 90; 0.25 m / 15° action chunks; Habitat 0.3.3 | Native single camera (use the same intrinsics); port the client to the HA 0.1.7 sim and check parity | 0 | 76.7 SR (README; mean over K=4 trials) | 0.60-0.72 |
| StreamVLN | 1 RGB 640×480 HFOV 79; 4 primitives/decision | Native; vln-safe worker | 0 | 56.0 raw / 34.4 clean / 42.5 depth-guard clean | 0.45-0.55 |
| ETP-R1 | 12 RGB-D views at 30°, CWP waypoints, back_algo control (primitives) | Build the 12 views by rotation: 4 views at 90° (18 turns) + homography synthesis of intermediates (pure rotation about the camera axis), or 22 turns for 12 real views; raise max_text_len to 256 or condense the text | ~20-28 per waypoint decision × ~7 decisions ≈ +150-200 (cap 15 decisions) | 64.6 raw / 37.7 clean / 50.1 depth-guard clean | 0.52-0.60 |
| NavGPT VLA-8B | 4 simultaneous RGB views, teleport to 8 predicted waypoints | view_num=1 mode, or refresh side views every k steps by rotation; quantize waypoints into turn+forward primitives | 0 to ~100 | 76.94 SR (teleport, 4-cam) | 0.55-0.70 (wide; measure) |
| OmniNav / NaVILA | 3 cams HFOV 110 / slow 8B | Skip, or use only as an offline-study proposer | – | 67.5 / 54.0 | – |

Fine-tuning data is HA-R2R train (10,819 episodes) plus R2R/RxR/ScaleVLN external data, with privileged teachers on train scans only (Q10/Q11). It covers DAgger and RL with reward = success ∧ TCR==0 (B2/B8).

### 3.3 Data schemas (A)

```jsonc
// EpisodeInput (T0): exactly what the agent may read
{"episode_id":"17","scene_id":"mp3d/<scan>/<scan>.glb",          // scene id only to load the simulator; the agent never opens it
 "start_position":[x,y,z],"start_rotation":[0,s,0,c],"instruction":"<~112 words>"}
// InstructionParse (P1 output; cached by sha256(instruction)+prompt_version+model)
{"clauses":[{"i":1,"act":"exit|walk|turn|pass|enter|climb|descend|stop","dir":"left|right|straight|around|up|down|null",
   "landmark":{"text":"double doors","cat":"door","region":"hallway|null"},"count":null,"dist_hint_m":null,
   "human":{"activity":"person vacuuming","implied_region":"hallway","relation":"pass|near|avoid|null"}}],
 "end":{"region":"bedroom","object":"bed","relation":"in front of|inside|next to","ordinal":null,"human":null},
 "floor_change":"up|down|none|unknown","n_turns":2,"length_prior_m":[6,14],
 "decorative_or_doubtful":["framed pictures along the walls"],"r2r_style":"Walk down the hall ... stop at the foot of the bed."}
// StepLog (per primitive; stored compressed)
{"t":37,"a":"MOVE_FORWARD","p":[x,y,z],"yaw":1.57,"collided":false,      // collided computed from pose (formula §3.6)
 "policy":"etpr1","stop_prob":0.12,"progress":0.55,"min_clear_m":0.41,"human_min_dist_m":2.3,"frame_ref":"blob:..."}
// MemoryNode (topological; every waypoint decision or ≥1.5 m)
{"node":12,"p":[x,y,z],"t":64,"keyframes":["blob:..."],"sweep":true,"room":{"bedroom":0.71,"hallway":0.2},
 "objects":["bed","lamp"],"people":[{"track":3,"activity":"folding laundry","p":[...],"conf":0.8}],
 "clause_progress":[1,1,1,0.4,0],"stop_score":{"etpr1":0.33,"simplevln":0.61}}
// RolloutRecord (A-MR)
{"episode_id":"17","rollout":"simplevln-9b/seed2/condensed","actions":"FFLLF...S","n_actions":143,
 "stop_p":[x,y,z],"n_contacts":0,"contact_steps":[],"path_len_m":11.2,"dy_m":0.0,
 "nodes":[MemoryNode...],"end_sweep":true,"policy_conf":0.58}
// ClusterCandidate (A-MR)
{"cluster":"k3","x":[x,y,z],"members":["r1","r5","r9"],"prefix_members":[["r2",88]],
 "phi":{"vote":2.1,"n_policies":3,"pass_mass":0.6,"stop_conf":0.55,"judge_borda":0.83,"speaker_ll":-1.9,
        "ranker":0.71,"room_match":0.8,"floor_match":1,"turn_seq_match":0.67,"human_cue_match":0.5,"len_fit":0.9},
 "P":0.64,"contact_free_tapes":["r5"]}
// Decision / submission row
{"episode_id":"17","tier":"T0|T2","tape_source":"r5|prefix(r2,88)|redrive","actions":[...],
 "selected_cluster":"k3","P_top":0.64,"margin":0.31,"judge_called":true,"audit":{"files_read":[...],"hashes":[...]}}
```

### 3.4 Prompt skeletons (A; open-weight first, Q12)

**P1 instruction parse.** Qwen3-32B/Qwen3.5 local, or Opus 5.5 at effort high with structured output; no temperature (Claude rejects sampling params since 2026-10-21).
```text
SYSTEM: You convert a long, LLM-rewritten navigation instruction into a strict execution plan.
The text mixes route directions with descriptions of people and decorative scene details.
Keep every route clause IN ORDER. Mark details that are decorative or could be hallucinated
(e.g. "you might notice", "framed pictures") under decorative_or_doubtful. For each person mentioned,
give the activity and the room type the activity implies (cooking→kitchen, showering→bathroom,
sleeping→bedroom, watching TV→living room/tv room) and whether the route passes them, ends near them,
or starts near them. The END is a position on the route next to the last landmark, not the landmark itself.
OUTPUT: JSON matching InstructionParse.
USER: <instruction>
```
**P2 condensation (T0).** "Rewrite as a 25-40-word R2R-style instruction that keeps every turn, door, staircase and the final stop landmark; drop all descriptions of people unless a person is the stop landmark." Validate on val by checking that the policy's SR on the condensed text is ≥ its SR on the raw text, per policy.

**P3 A-MR endpoint judge** (comparative; own observations only):
```text
SYSTEM: A robot followed the instruction several times from the same start. Each candidate below is a
place where at least one run stopped or slowed down. You see, for each candidate (A..K): forward camera
frames along the route that reached it (labels burned in: step, metres walked, turn angle since last frame,
floor change), a 360° sweep at the candidate, an observed-only top-down map with all candidates marked,
and text: room-type estimate, objects, people with activities seen near the route.
Execute the clauses IN ORDER against each candidate route. Rules: the endpoint is a position on the route
near the last landmark; buildings repeat rooms and doors, so count instances when the last clause reuses a word;
not seeing a small landmark is not evidence against a route; people are context near the route, rarely the goal;
a candidate the robot only passed may still be the right stop (overshoot is the most common error).
Compare candidates; do not score them in isolation.
OUTPUT JSON: {"clause_alignment":{"A":[..],...},"ranking":["C","A",...],"best":"C","confidence":"low|med|high"}
USER: <P1 parse + raw instruction> <candidate blocks in permuted order>
```
Run 4 permutations and aggregate by Borda. Skip the judge when the fused P_top ≥ 0.8 and the margin is ≥ 0.3. B4: when 3/3 votes agree, accuracy is 89.7%.

**P4 A-ST in-tape verifier** (NavGPT-3 planner framing; B3 fact 8). Inputs: the memory nodes, the current 360° sweep, the instruction parse and the remaining action budget. Output: `{"decision":"commit|continue|backtrack|visit_runner_up","target_node":12,"why":...}`. The rules match P3, plus "justify both staying and going back" and "never exceed budget_remaining − return_cost".

### 3.5 Online loop A-ST (T0)

1. t=0: a 24-turn sweep gives the initial panorama, P1/P2 run, and the start-room estimate is checked against `start_context`. TURN actions are never collision-flagged (A2 fact 4) and only cost budget.
2. The primary policy (SimpleVLN-9B, or ETP-R1 with rotation panoramas) drives behind the shield. Memory nodes are written every waypoint decision or every 1.5 m.
3. When the policy emits STOP, or clause progress reaches the last clause: run a sweep, then P4.
   - **commit**: navigate on the own map to the Bayes stop node (§3.7) and STOP.
   - **visit_runner_up**: B5 estimates about 40-60 actions round trip to a sibling branch. Use it if the margin is below 0.15 and ≥100 actions remain.
   - **continue**: hand control to the secondary policy for at most N = 30 steps, then re-verify.
4. Budget manager: always keep return-to-best-node cost + 10 actions in reserve, and STOP before 500. Q13 allows omitting STOP at 500, but STOP-gated success is safer.
5. Overshoot fix: if P4 prefers an earlier node, backtrack physically. NavGPT-3 reports that most failures end FURTHER from the goal than a point already visited, and the OSR-SR gap is 5.5-8 points.

### 3.6 Multi-rollout A-MR (T2; ask organizers first)

1. **Rollouts.** R = 8-16 per episode: {SimpleVLN-9B × 3 seeds at the README temperature 0.3, StreamVLN × 2, ETP-R1 × 2, NavGPT-VLA × 2} × {raw, condensed}, plus the A-ST agent itself. Every rollout ends with a 24-turn sweep before STOP, so endpoint evidence exists for P3.
2. **Pose-detected contact (exact).** For each MOVE_FORWARD at step t: `collided_t = (‖p_{t+1} − p_t‖² + 1e-5 < 0.0625)`, using the 3-D agent position from the pose sensor. This is habitat-sim 0.1.7 object_controls.py:80-87 (A2 facts 1-2). TURN/LOOK/STOP never count, so n_contacts equals HA's collisions.count for that local run.
3. **Candidates.** Stop points s_r, plus prefix candidates: nodes on a rollout where the policy's stop probability was a local maximum above 0.3, or where clause progress reached the last clause. Agglomerative clustering in 3-D (single link 2.0 m, cluster diameter ≤ 3 m). All rollouts share the start pose, so GPS coordinates are comparable.
4. **Fusion.** See §3.7.
5. **Tape choice.**
   - Among contact-free rollouts whose endpoint or prefix node lies within ρ = 2.5 m of the Bayes stop x*, pick the one with the largest minimum clearance to detected people (from own depth/tracks), then the smallest |s − x*|.
   - Prefix truncation: submit `a_r[1..t] + STOP`. A prefix is never dirtier than its parent tape.
   - If no contact-free tape reaches x*: (i) re-run the policies that ended there with a stricter shield (margin +0.1 m) and new seeds, up to M = 4 times; (ii) re-drive, a point-goal rollout to x* on the union map from earlier rollouts (pre-exploration memory, T2); (iii) fall back to the next cluster.
6. **Timing robustness.** Humans animate on wall clock (CONTEXT fact 4; A3). Re-replay the chosen tape under C1's deterministic frame schedules S ∈ {5, 20, 100, ∞ steps/s}, and on a contact prefer a tape with larger human clearance. Human motion is small (median extent 0.03 m, p90 0.8 m), so a 0.3-0.5 m human margin in the shield already covers most cases.

### 3.7 Fusion and stop math (A)

Each cluster j has a feature vector φ_j:
- **vote** = Σ_r α_{π(r)} · exp(−|s_r − x_j|² / 2σ²), with σ = 1.25 m and α_π = logit of policy π's dev-set stop accuracy (Dawid-Skene-style reliability).
- **n_policies**: the number of distinct policies that stopped in the cluster.
- **pass_mass**: the share of rollouts passing within 1.5 m.
- **stop_conf**: mean policy stop probability at x_j.
- **judge_borda** ∈ [0,1], with "judged" as an indicator.
- **speaker_ll** = log p(I | route keyframes to x_j) / |I|, from an HA-trained Qwen3-VL-8B speaker via vLLM prompt logprobs.
- **ranker**: a fine-tuned listwise Qwen3-VL-8B over own-observation route summaries, trained on HA-R2R train rollouts.
- Structural matches: room_match (end region), floor_match (Δy vs. stairs words), turn_seq_match (heading changes vs. parsed turns), human_cue_match (activity captions vs. human clauses), and len_fit (path length vs. length prior).

**Model.** Conditional logit with a null option: P(j | e) = exp(w·φ_j) / (exp(b_null) + Σ_k exp(w·φ_k)). It is trained by maximizing Σ_e log Σ_{j: |x_j − g_e| ≤ 3} P(j | e) under L2 regularization, with ≤25 parameters, followed by temperature scaling. P(null) estimates "no cluster is right". It gates re-drive, extra rollouts and the frontier judge.

**Bayes stop.** x* = argmax_{x ∈ reachable own-map points} Σ_j P(j) · [0.8 · 1(|x − x_j| ≤ ρ) + 0.2 · 3/(3 + |x − x_j|)]. Use ρ = 2.5-2.8 m to absorb goal-position uncertainty. Distance is 3-D Euclidean, as in the scorer (HASimulator/measures.py), so off-floor points count. When two clusters lie less than 5 m apart and P is split, x* lands between them and covers both.

**Q10 caveat.** Fitting even this small calibrator on HA-R2R val may count as "training on val". Instead, fit on leave-scans-out folds of HA-R2R TRAIN, with our fine-tuned components retrained without those scans (B4 §8), and optionally on R2R-CE val_unseen with original instructions, which is an external dataset. Use HA val_unseen only for evaluation and model selection, and disclose it.

### 3.8 Compute and API cost (A, per test pass of 3,408 episodes)

| Item | Unit cost (evidence) | R=1 (A-ST) | R=16 (A-MR) |
|---|---|---|---|
| ETP-R1 rollouts | ~4.5 s/episode at 45 ms/primitive (vln-safe) + rotation renders ~1 s | ~5 GPU-h | ~20 GPU-h (×4) |
| StreamVLN | 0.42 s per 4-action decision + 3.8 s first (vln-safe) → ~13 s/ep | 12 GPU-h | ~50 GPU-h |
| SimpleVLN-9B (vLLM) | ~0.3 s/decision × ~25 (assumed) → ~8 s/ep | 8 GPU-h | ~100 GPU-h (×12 with seeds/variants) |
| NavGPT-VLA-8B | 0.5-1 s/step (NavGPT-3 abstract: 1-2 Hz) → 30-45 s/ep | 30-45 GPU-h | ~90 GPU-h |
| Perception (detector + 7B captioner on keyframes) | ~0.1-0.3 s/keyframe | ~5 GPU-h | ~40 GPU-h |
| Local judge Qwen3-VL-32B, 4 permutations, ~60 images × ~334 tokens | ~72k prefill tokens/episode | – | ~10 GPU-h |
| Optional Opus 5.5 judge (escalation) | ~24k in / 3k out per call × 4 = $0.62/episode standard, $0.31 batch | – | gated at ~40-60% → $0.4-1.3k |
| P1/P2 parse (open-weight local) | ~1k in / 0.8k out | <1 GPU-h | <1 GPU-h |

A-MR totals about 300-350 GPU-h per test pass, or about 5-6 h on 64 GPUs. The simulator side is the RGB-D official-mirror worker at 100-300 steps/s/process (C1). Claude prices (claude-api skill, cached 2026-10-06): Opus 5.5 $4/$20 per MTok, cache reads $0.20, batch −50%, about w·h/784 image tokens (512² ≈ 334), no sampling parameters, no logprobs. The organizers discourage reliance on closed APIs (Q12), so the official entry uses open-weight judges, and Opus 5.5 is kept as an ablation/escalation reported in the paper.

### 3.9 Expected accuracies, stage by stage (HA-R2R val_unseen, with humans; inference unless marked measured)

| Stage | Metric | Expected | Evidence |
|---|---|---|---|
| A1 best single compliant-native policy, HA fine-tuned | raw goal-hit (≤3 m) | 0.60-0.72 | SimpleVLN 76.7 / NavGPT-VLA 76.9 on R2R-CE; HA text shift −5 to −15 (GSA-R2R style rewrite costs a few points; HA-VLN-DE NE +1.5-2.2 m); fine-tune recovers part |
| A2 + own-map shield | clean SR | 0.52-0.66 | Retention of successes after shielding: depth guard 0.785 (ETP-R1 50.1/63.8, measured), navmesh oracle 0.98 (61.3/62.6); an accumulated depth+pose map with human margins sits between them (target 0.88-0.95) |
| A3 A-ST verify / backtrack / runner-up visit | clean SR | +2 to +5 → 0.55-0.70 | NavGPT-3 planner +2.07 (Opus 5) / +4.57 (Astra); OSR−SR gap 5.5-8 |
| A4 A-MR first contact-free tape over 3-4 policies | clean SR | 0.60-0.72 | **measured +12.3 (50.1 → 62.4)** with weaker agents; the gain shrinks as base strength rises |
| A5 + clusters + fused calibrator + judge + prefix stop | clean SR | 0.65-0.77 | Raw union 84-91% (measured); agreement calibration (B4: 89.7 / 69.0 / 34.8% for 3/3, 2/3, none); assumed capture of 35-55% of the union headroom |
| A6 + re-drive (T2) | clean SR | 0.68-0.80 | Measured gap between contact-free union (73.4) and raw union (84.0) is 10.6 points; assume half is recovered |
| A, test-scan humans not rendered locally | clean SR penalty | −10 to −30 points | 38% of routes within 0.3 m of a human (measured proxy); only reference-path-like collisions are covered by collision_num |

## 4. Pipeline B: privileged offline candidate ranking (PRIV; only with explicit permission)

### 4.1 Permission items and what each buys

| Item to ask for | Needed by | Value |
|---|---|---|
| G: test-scan nav graph + mesh/navmesh + `.house` semantics (or public REVERIE BBoxes / niessner room labels) at inference | Candidates, path features, renders, planner | Core of B (B-1: 78-86% vs A 0.65-0.77) |
| R: arbitrary-viewpoint rendering of test scenes (no humans) | VLM judge, re-rendered features | +2-4 (judge) |
| S: sibling HA instructions of the same trajectory (ID triple) | Product of experts over 3 texts | +3-6 (B4 measured +5.9/+7.1 at weaker bases) |
| O: original R2R test instructions | 6-instruction ensemble | +3 more; C3/B8 red line, assume NO |
| H: human placements for planning | Human-aware planning | Q11 says NO; execution must perceive humans instead |

Even with every permission granted, `sample_room_paths.json` (B12), `collision_num_test.json` and HA-VLN 1.0 test annotations stay quarantined.

### 4.2 Candidate generation
- C(e) = included nav-graph nodes whose weighted-shortest path from the start viewpoint has 3-6 edges and 5-25.5 m length. Recall is 100% on 5,798 train/val paths. On ported test starts the set has mean 28.9, median 25, p90 54, max 89 nodes, and about 8.3 three-metre clusters (A1/B1/B12).
- The start viewpoint is the node nearest the start position (1,135/1,136 trajectories, B1). The continuous goal is the node's floor point (x, z − h, −y) (xz offset p99 0.02 m, B1).
- Add navmesh hedge points: a 0.5 m grid within 3 m of the top-5 nodes, used only by the Bayes stop.
- Group by ID triple {3k+1, 3k+2, 3k+3} / trajectory_id. NEVER group by start pose: 580/1,136 trajectories share a start pose with other trajectories (A1). This corrects the topic brief.

### 4.3 Per-candidate features (schema)
```jsonc
{"traj":"k=41","cand":"<vp_id>","x":[x,y,z],"hops":5,"geo_m":10.8,"euclid_m":7.9,"dz_m":0.0,
 "path":["vp0","vp1",...],"turns":["straight","left~90","right~45"],          // heading change at each node vs incoming edge (start yaw from episode)
 "regions":["hallway","bedroom"],                                            // .house panorama→region (or niessner labels, 76% coverage)
 "objects_seen":[["door",1],["bed",4]],                                      // mpcat40 within 3 m per node (.house O / REVERIE BBox, 100% coverage)
 "doors_crossed":2,"stairs":false,"floor_change":"none","end_region":"bedroom","end_objects":["bed","lamp"],
 "prior":{"hop_len":0.21,"density":5},                                       // train histogram; # candidates within 3 m (central-node prior 48.4%, B5)
 "renders":{"forward":["blob:..."],"end_sweep":["blob:..."],"topdown":"blob:..."},  // human-free renders (H not permitted)
 "scores":{"fol_scalevln_h14":-3.2,"fol_srdf":-2.9,"stop_lp":-0.4,"spk_ha":-1.7,"ranker_qwen3vl8b":0.66,"llm_text_rank":2,"judge_borda":0.8}}
```

### 4.4 Scorers
- **(a) Follower likelihood (zero training).** ScaleVLN DUET CLIP-H/14+EnvEdit (80 test SR on original R2R instructions) and SRDF (fine-tune from the released pretrained model, ~85). Run teacher forcing along each candidate's shortest path; record Σ log p(path) + log p(STOP at end) and the length-normalized variant. Use max_instr_len 256-320 or left truncation, because DUET truncation drops the stop clause (B1 fact 12). Feed both the raw HA text and the P2 condensation. Fine-tune on HA-R2R train paired with R2R viewpoint paths via shared IDs (10,819 pairs).
- **(b) Speaker.** Qwen3-VL-8B LoRA trained on HA-R2R train (route keyframes + verbalized path → HA instruction). Score with PMI: log p(I | c) − log p(I). Weak alone (FAST speaker-only 43.7) but the best complement (+10.9 in Speaker-Follower; β = 0.94 in VLN-BERT fusion, B4).
- **(c) Trained compatibility ranker.** Listwise Qwen3-VL-8B, or a DUET-encoder cross-encoder (B4 S2/B5), with exhaustive candidates as negatives plus shuffled-path, left/right-swap and human-activity-swap negatives. The Airbert analogue reached 68.7 val_unseen with a 2021 backbone.
- **(d) Discrete proposers.** Free-running greedy rollouts of the (a) models. Each contributes a vote for the cluster containing its stop.
- **(e) Text-only LLM listwise judge (P5)** over verbalized candidates, batches of ≤25, 4 permutations.
- **(f) Frontier VLM comparative judge (P6)** over the top-5 with human-free renders. Entropy-gated.

**P5 text listwise judge:**
```text
SYSTEM: You choose where a route ends in a known building. Each candidate is the shortest walk from the same start.
For each candidate you get: hop count, length, the turn sequence relative to the start heading, the rooms passed in order,
doors/stairs, objects near each waypoint, and the end room with its objects. Execute the instruction's clauses IN ORDER
against each candidate. The endpoint is a position near the last landmark. People in the instruction are context;
use the room type their activity implies (cooking→kitchen) as soft evidence. Ignore details marked doubtful.
OUTPUT JSON: {"top5":[ids best→worst],"best":id,"confidence":"low|med|high","decisive_clause":i}
USER: <P1 parse> <instruction> <candidate table in permuted order>
```
**P6 visual judge.** Use the B3 §4 skeleton, adapted to the default of the episode's OWN instruction only (siblings only if S is granted, original R2R never). Each candidate gets: forward renders at every node facing the next node (512 px, HFOV 90, step/turn/metres/floor labels burned in), a 4-view endpoint sweep, and a top-down map with the route. Structured output, 4-8 permutations, Borda count.

### 4.5 Fusion and calibration (B)
- **Per instruction i:** u_i(c) = Σ_m w_m · z_m(c, i), with z-scored features. The fixed priors v · ψ(c) enter once.
- **Instructions combine as a product of experts:** log P(c | e) = Σ_{i ∈ I} u_i(c) + v · ψ(c) − log Z. Here I = {own} by default, or the ID triple if S is granted.
- **Initialization.** Follower/speaker weights are set to VLN-BERT's α = 0.63, β = 0.94 (B4), then learned.
- **Objective.** Multi-positive conditional-logit likelihood over candidates within 3 m of the goal, fitted on 6 leave-scans-out folds of HA-R2R train (≈10 scans each), with our fine-tuned scorers retrained per fold (Q10). It is evaluated, not fit, on val_unseen.
- **Calibration and stop.** Temperature-scale the posterior. The Bayes stop is as in §3.7, over the nodes plus hedge points.
- **Gating:**
  - if P_top ≥ 0.85, skip (f);
  - if the margin is below 0.15 or the entropy exceeds h, run (f) with Opus 5.5 (effort high);
  - if (f) disagrees with the fused top-1 and its confidence is high, escalate once to Fable 5.1.

### 4.6 Execution hand-off (B)
- Run a global shortest path on a navmesh inflated by 0.25-0.30 m to x*, then convert it to primitives (A5/C7).
- Run it **closed-loop in the local sim with humans rendered**, using the A shield and RGB-D person tracking, to dodge humans. They cannot be read (Q11), and planning human-blind exposes up to ~38% of routes (§2.2).
- Verify contact-freeness from pose. Re-replay under C1 timing schedules (needs permission G as well).
- This hybrid executor makes B robust to H being refused.

### 4.7 Caching, cost, latency (B)
- **Cache keys:**

| Cache | Key |
|---|---|
| Renders | (scan, viewpoint, heading_bin, hfov, res, human_frame∈{none}) |
| Path features | (scan, start_vp, cand_vp) |
| Scorer outputs | (model_sha, instruction_sha, cand_vp) |
| Judge calls | (episode_id, candidate-set hash, permutation, prompt_version, model, effort) |

  The 1,136 trajectories have only 788 distinct starts, so path features and renders are shared across trajectories with a common start.
- **Compute per test pass:**
  - Renders: unique (viewpoint, heading) pairs over the 1,971 test viewpoints ≈ 16k views. Under 1 GPU-h.
  - Teacher forcing: 3,408 × ~29 candidates ≈ 99k passes per follower, under 1 GPU-h.
  - Qwen3-VL-8B ranker: ~100k pairs × ~3k tokens ≈ 300M prefill tokens, ~5-8 GPU-h.
  - Speaker: similar to the ranker.
- **API cost per test pass (Opus 5.5):**

| Judge | Per episode | Per test pass |
|---|---|---|
| P5 text listwise (~8k in / 2k out × 4) | $0.29 | ~$1.0k standard / $0.5k batch |
| P6 visual (top-6 × 11 images ≈ 23k in / 4k out × 4) | $0.69 | ~$2.35k standard / $1.2k batch; gated at 50% → $0.6-1.2k |

  With S granted, judge per trajectory instead (1,136 × 8 calls ≈ $1.6k standard, B3).
- **Latency.** Not binding (offline), but one full pass must fit well under 24 h. Target under 8 h end to end on 32-64 GPUs plus batch API.

### 4.8 Expected accuracies, stage by stage (B, per trajectory, goal within 3 m Euclid; val_unseen)

| Stage | Expected | Evidence |
|---|---|---|
| Candidate recall (oracle) | 100% | 783/783 val_unseen (B1); median 24-27 candidates |
| Instruction-blind prior (central node) | 43.7-48.4% | B12 / B5 (Euclid); random 26-28% |
| (e) text-only frontier listwise alone | 50-65% (low confidence) | No direct literature; online text agents 34-48 (B3); offline with full candidates should be higher |
| (a) best follower LL alone, HA text, HA fine-tuned | 70-78% | 80/85 single-run test on original instructions minus 5-10 for the HA shift |
| (b) speaker alone | 40-50% | FAST speaker-only 43.7 |
| (c) fine-tuned ranker alone | 70-80% | Airbert 68.7 (2021 backbone, 30 beams) |
| Fusion of (a)-(d) + priors | 76-83% | +3-5 over the best single (FAST +5.3; Airbert/VLN-BERT ensembles) |
| + (f) gated comparative VLM judge | +2-4 | NavGPT-3 planner +2-4.6; C2Nav comparative ≫ absolute |
| + Bayes stop | +0.5-2 | Euclid 3 m ball holds a median of 8 nodes (B1) |
| **B-1 own instruction** | **78-86%** | – |
| B-3 + siblings (S) | 82-89% | B4: 3-vote +5.9/+7.1 measured at 59-69 bases; smaller at an 80 base |
| B-6 + original R2R (O) | 85-92% | B4/B3 estimates; C3 red line |
| Execution conversion (clean) | 97-99% of goal hits | B2: perfect-goal SR 0.97-1.0 with navmesh planner; human-aware closed-loop executor |

### 4.9 Contingencies
- **Test-scan humans not released for rendering.**
  - **A:** local rollouts are human-blind, while official replay has humans. The shield cannot help, and up to ~38% of routes pass within 0.3 m of a human, though not all would collide. collision_num slack covers only reference-follower collisions.
  - **A mitigations:** (1) press the organizers. Q11 says the agent "should infer human positions … from its camera observations", which presupposes rendered test humans, so this argument is strong. (2) Prefer tapes with larger corridor clearance from the own depth map (T0). (3) Score-aware stop with a human-blind margin: stop 1-1.5 m short of the end landmark along the approach. 9.6% of goals have a human within 1 m, and the 3 m success ball allows the margin. (4) Never use HA-VLN 1.0 test annotations to insert proxy humans (T3).
  - **B:** goal inference is unaffected, because human-activity text still maps to region priors and needs no positions. Execution has the same human-blind penalty as A, with the same mitigations.
- **Bundle gives only start + instruction** (no trajectory_id, no humans, no grouping).
  - The scene_id must exist, or the simulator cannot load the episode. If it does not, match the start position to the A1 index (exact floats; 788 distinct starts) to recover the scan.
  - **A:** unaffected, since it never needs trajectory_id.
  - **B:** candidates and semantics still come from MP3D via the start's nearest viewpoint. Only S (siblings) is lost; it can be recovered by ID triple if IDs keep the R2R-CE order (A1: 0.9-0.95 likely).
- **trajectory_id re-keyed.** Use the A1 bundle-day validation (scene, start_position, yaw, text similarity).

## 5. Evaluation plan (val_unseen = 1,839 episodes / 613 trajectories / 11 scans; val_seen as a check)

1. **Harness.** Run the official image `havln-score-phase1` for parity, plus C1's deterministic scorer under timing schedules S ∈ {5, 20, 100, ∞}. Report SR, NE, CR, TCR and Score per episode and per trajectory, with a scan-bootstrap 95% CI (expect about ±4 points; Airbert's 0.639-0.726).
2. **Oracle ladder** (B2 §Rec):
   - (a) GT goal + executor (gate: SR ≥ 0.97);
   - (b) single policy + shield;
   - (c) union oracle of the A-MR pool, raw and contact-free;
   - (d) each selector;
   - (e) B candidates with the oracle-best candidate, i.e. the pure ranking ceiling.

   The gaps (c)-(d) and (e)-B tell where to spend.
3. **Ablations (A):**
   - R ∈ {1, 2, 4, 8, 16};
   - policy subsets;
   - raw vs condensed instruction;
   - shield margins;
   - selectors: priority contact-free, cluster vote, + calibrator, + judge, + prefix stop, + re-drive;
   - judge: Qwen3-VL-8B fine-tuned vs Qwen3-VL-32B zero-shot vs Opus 5.5 (effort medium/high);
   - A-ST verifier on/off; budget-cap sensitivity;
   - humans rendered vs removed (human-blind penalty measured directly).
4. **Ablations (B):**
   - each scorer alone;
   - fusion with and without each scorer;
   - K ∈ {3, 5, 8} for the judge; permutations 1/4/8;
   - Bayes stop vs argmax;
   - instruction sets {own, + siblings};
   - raw vs condensed;
   - text vs visual vs both;
   - candidate sets {3-6 & 5-25.5 m, 4-6 & 5-20 m}.
5. **Calibration diagnostics.** ECE of P_top; selective accuracy vs coverage; gate thresholds chosen on train folds.
6. **Hygiene.**
   - Freeze recipes before each val_unseen look and log every look.
   - Fit nothing on val (Q10).
   - Expect test ≈ val_unseen − 1 to 3 points (B4).
   - Keep an audit manifest of files read by the inference process (B8/C3).
7. **Gates (suggested).**
   - Nov 8: A-ST ≥ 0.50 clean SR on val_unseen.
   - Nov 15: A-MR ≥ 0.62.
   - Nov 22: final selector frozen.
   - B gate: top-1 ≥ 0.80 on val_unseen before any permission-dependent submission.

## 6. Implications
- The decisive quantity is goal-selection quality. Execution must be collision-free and human-aware in BOTH pipelines, because humans sit on or near 38% of routes and 50% of goals have a human within 3 m.
- In the compliant regime the Score has no path-length term. Exploring, verifying and backtracking inside one tape is free except for collision risk and the 500-action budget. A-ST is therefore the principled compliant analogue of beam search and path ranking, and B5's 40-60-action runner-up visit is the main lever.
- Multi-rollout selection (A-MR) is worth about +10 SR (measured +12.3 on weaker agents) but sits in an unaddressed rules area. It must be asked about and disclosed, and should never be the only submitted variant.
- Pose-detected contact is exact and compliant to compute. As a selection criterion it also improves goal accuracy, because contact correlates with failure.
- NavGPT-3, the strongest public VLA, is not a drop-in compliant policy: it uses 4 cameras and teleport execution. SimpleVLN (single RGB, primitive chunks) is the strongest natively compliant proposer, and ETP-R1 is compliant with ~150-200 extra rotation actions.
- Pipeline B's advantage over A is about +10-15 points of goal accuracy (B-1 78-86% vs A-MR 65-77%), not the +30 sometimes assumed. Once siblings and original instructions are excluded, the gap is modest, which strengthens the case for leading with A.

## 7. Recommendations
1. [T0] Build A-ST first:
   - SimpleVLN-9B as primary (port to the HA 0.1.7 sim), ETP-R1 with rotation panoramas as secondary;
   - an own-map shield with exact pose-based contact detection;
   - the memory schema of §3.3;
   - P1/P2/P4 on open-weight models;
   - Bayes stop and runner-up visits.
2. [T0] Train an HA speaker (Qwen3-VL-8B) and a listwise ranker on HA-R2R TRAIN rollouts of our own policies (hard negatives = other clusters). They serve both A (own observations) and B (renders).
3. [T2] Implement A-MR behind a config switch and measure it on val_unseen. File the organizer question now, per C3/B8: may we run many local rollouts and choose by pose-detected contact and self-consistency, and may we truncate or re-drive? Submit the A-ST variant regardless.
4. [PRIV] Build B only as an analysis harness and permission-gated variant: candidates, features, scorers, fusion, Bayes stop. Report its ceiling in the technical report as the "privileged-map" oracle row. Never feed it O, H, the B12 leak or collision_num_test.
5. [Both] Make the executor human-perceiving (RGB-D person tracking + 0.3-0.5 m swept margins). Measure the human-blind penalty on val by removing humans locally while scoring with humans.
6. [Both] Fit calibrators on leave-scans-out train folds, not on val (Q10). Choose gate thresholds the same way.
7. [Both] Group by ID triple. Cache by content hash. Keep an audit manifest. Prefer open-weight judges, with Opus 5.5 kept as an ablation and escalation that is disclosed.

## 8. Open questions
- Will the organizers allow multi-rollout selection, prefix truncation, re-drive (pre-exploration), sibling instructions, or scene geometry at inference? Each changes which variant is submitted.
- Will the Phase-2 bundle include test-scan `human_motion.json` for rendering? Without it every pipeline is human-blind locally.
- Measured compliant performance of SimpleVLN-9B on the HA 0.1.7 simulator (parity with its Habitat 0.3.3 numbers) and of NavGPT-VLA in single-camera, primitive-quantized mode.
- Actual capture rate of the fused selector (35-55% assumed) and the real gain from P3 judges over own observations. No published number exists.
- How collision_num was computed. The 38% vs 8.6% mismatch suggests a human-aware navmesh follower; confirm from organizer code or the paper.
- Whether a ≤25-parameter calibrator fit on val counts as "training" under Q10.

## 9. Sources
- Sibling findings (`S/findings/`):
  - A1-episode-format-and-test-split.md (triples, candidate counts, grouping correction)
  - A2-collision-semantics-habitat017.md (collision formula)
  - B1-discrete-r2r-sota-and-transfer.md (candidate oracle, discrete SOTA, Score sensitivity)
  - B2-vlnce-sota-2023-2026.md (vln-safe tables, union recall, policy costs)
  - B3-llm-vlm-zero-shot-planners.md (NavGPT-3, C2Nav, judge skeleton, costs)
  - B4-pre-exploration-beam-search-path-ranking.md (3-instruction vote, agreement calibration, fusion recipe)
  - B5-instruction-path-compatibility-models.md (compliant touring cost 792 actions, central-node 48.4%, runner-up visit)
  - B8-world-models-innovation-angle-and-organizer-taste.md (tiers, organizer taste)
  - B12-r2r-test-knowledge-and-candidate-bounds.md (leak quarantine, candidate grid)
  - C1-infra-and-replay-farm.md (timing schedules, throughput)
  - C3-rules-ethics-and-defensibility.md (red lines)
- `EXT/jostar-track2`, branch origin/bohan/clarification-Oct14, README (Input row, Q8-Q13)
- `EXT/sota/vln-safe/results/*/r2r/*/episodes.csv` (https://github.com/dinhieufam/vln-safe)
- `EXT/B3/metacognitionai_NavGPT-3`: navgpt/planner/vla_only.py, navgpt/environment/r2r.py, navgpt/vla/agent.py, configs/experiments/vln/vla_8b_r2r.yaml (https://github.com/metacognitionai/NavGPT-3)
- `EXT/sota/SimpleVLN`: README.md, eval/config/vln_r2r.yaml (https://github.com/simplevln/SimpleVLN)
- `EXT/sota/ETP-R1/run_r2r/iter_train.yaml` (max_traj_len 15, max_text_len 150, NUM_ANGLES 12)
- `EXT/HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml` (RGB 224 HFOV 90, depth 256, 0.25 m / 15°, sliding)
- `EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`, Data/HA-R2R-tools/collision_num_*.json, HASimulator/HA-DE/connectivity, tasks/R2R/data
- `EXT/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{val_seen,val_unseen}`
- claude-api skill (cached 2026-10-06): model IDs, pricing, batch, cache-read, sampling-parameter removal
- Scripts written for this design: `S/c8_scripts/vlnsafe_select.py`, `S/c8_scripts/human_blind.py`, `S/c8_scripts/human_goal.py`, `S/c8_scripts/human_frame_check.py`, `S/c8_scripts/score_proj.py`
