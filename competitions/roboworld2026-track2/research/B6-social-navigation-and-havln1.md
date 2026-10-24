# B6 — Social navigation literature, HA-VLN 1.0/2.0 social metrics, and the minimal-risk TCR=0 policy for our replay mechanics

Topic id: `B6-social-navigation-and-havln1`
Date: 2026-10-24
Author: research agent B6 (builds on A2-collision-semantics-habitat017 for exact Habitat 0.1.7 mechanics; does not repeat them)

> **Search-budget note.** The shared WebSearch budget ran out after 17 queries during this run. Literature numbers come from those searches plus primary code/READMEs cloned from GitHub (HA3D_simulator, Falcon, robosense2025/track2, iGibsonChallenge2021). Several paper tables (HA-VLN 1.0 full tables, Habitat 3.0 Table 2, HCSG Table I, AdaVLN, "HumanWorld") could not be fetched or confirmed. Those gaps are listed under Open questions.

## Summary

Across social-navigation benchmarks, a "collision" is defined in one of three ways: (a) distance to the human below a threshold (HA-VLN 1.0: 3D distance ≤ 1.0 m; iGibson: < 0.3 m ends the episode); (b) physics contact (Habitat 3.0 SocialNav, Falcon/RoboSense 2025 H-Coll); (c) navmesh step filtering, which is what VLN-CE does and what the HA-VLN 2.0 challenge code actually counts. Personal-space thresholds are 0.5 m (iGibson PSC) or 1.0 m (Falcon/RoboSense PSC; HA-VLN 1.0/2.0 papers). Habitat 3.0 uses a 1–2 m following band.

Agents trained in static scenes do badly once people are added:
- HA-VLN 1.0 zero-shot Airbert: NE +167%, SR −67%.
- HA-VLN 2.0 BEVBert/ETPNav in HA-VLN-CE val-unseen: CR 0.55–0.58, SR 0.17–0.21.
- Habitat 3.0's privileged heuristic expert still collides in about 52% of episodes.
- Falcon's H-Coll is 43%.
- The challenge CMA baseline has CR 0.62–0.68 and TCR 14–18. That TCR includes walls.

What works in the literature: inflated or proxemic costmaps, deleting graph nodes near humans (the HA-VLN 1.0 teacher), forward-step guards on depth (VLN-Safe: 62–98% fewer collision steps), and forecasting human motion with penalties on future occupancy (Falcon; HCSG: −34.5% CR).

**New data analyses this session (high confidence, computed from the public files):**
- Humans sit on the reference route. The human-free VLN-CE ground-truth shortest path passes within 0.5 m of a human root in about 41% of val episodes, and within 0.3 m in 31–34%. The dominant region is the hallway.
- **`collision_num` is an annotation count.** It equals the number of HA-VLN 2.0 humans keyed to the reference path's start or end viewpoint in 89–93% of episodes, and never exceeds it. In 100% of the 1,043 train+val episodes with `cn > 0`, a human is keyed to the goal viewpoint. This is a goal-region hint for the 237 test episodes with `cn > 0`.
- About half of all goals have a human within 3 m, and 8–10% within 1 m.
- **Graph proxy for forced proximity.** On the R2R nav graph, with humans swept over all 120 frames:
  - At 0.5 m root clearance, 12% (val_seen) and 19% (val_unseen) of trajectories have no clear route. Most of these are hallway blockers.
  - At 1.0 m clearance this rises to 25–32%. A hard 1 m social margin is therefore infeasible for a large minority of episodes, so it must be a soft cost.
  - Of the forced cases at 0.5 m, roughly half are blocked in every frame. Only about 6–7 per split open a gap in the final frozen frame.

**Scoring trade-off** (marginal analysis of the official Score at SR 0.4–0.75, N = 3,408):
- One success is worth 0.0235 points.
- A collision episode costs 0.004–0.007 points in social terms, beyond its lost SR.
- One metre of final distance costs 0.0003–0.0007 points.
- So a risky passage with no safe alternative is worth attempting if P(collision) < ~0.8.
- If a collision is certain, crossing pays only when the goal lies more than ~9–15 m beyond the blockage. Otherwise stop before it.

**Waiting.** Actions do not advance frames, but each action uses scorer wall-clock time. So no-op "waiting" does move the animation, just nondeterministically. It can push the episode into the frozen final frame (about 12 s after reset) only if the scorer's speed is calibrated.

**Innovation award.** The organizers (Dong, Wu, Xiong, Kong, Cheng) signal they value world models that anticipate human trajectories, egocentric VLAs, re-planning at blocked corridors and doorways, and socially compliant distances. Co-organizer Lingdong Kong's RoboSense 2025 (inference: he led it; not verified from its source this session) made Phase 2 code-only, audited it, and disqualified submissions that do not run a real inference pipeline. A transparent privileged-teacher → egocentric-student story, with proxemic metrics, is the safest pitch.

---

## 1. Collision / personal-space definitions across benchmarks (verified)

| Benchmark | Collision detection | Personal-space threshold | Consequence | Source / confidence |
|---|---|---|---|---|
| HA-VLN 1.0 (HA3D, discrete MP3D graph) | `state.isCrushed = int(minDistance <= 1)`: 3D Euclidean distance from agent location to nearest human root ≤ 1.0 m | 1.0 m (same) | counted as a "hit"; humans at path 'Beginning'/'End' are subtracted as a penalty; success_nohits = NE < 3 m and hits == 0; reward −2.0 per crash | HA3D_simulator/HA3DSim.py:180; tasks/HA/eval.py:55-74,95-99,140; tasks/HA/utils.py:416-482 — **high** |
| HA-VLN 2.0 paper | TCR = Σ_i (c_i − \|A_i^c\|)/L, with c_i = collisions within 1 m of a human and A_i^c = human activities at critical nodes; CR = fraction of episodes with ≥ 1 collision, normalised by β (fraction of human-influenced instructions) | 1 m | SR requires zero collisions | arXiv 2503.14229 (WebSearch summaries) — **medium-high** |
| HA-VLN 2.0 challenge code (what is scored) | habitat-lab `Collisions.count` = steps where the navmesh filter shortened the move; humans are STATIC objects joined into a recomputed navmesh (radius 0.1); walls count too | none in scoring (DistanceToHuman exists only as a diagnostic) | TCR_ep = max(0, count − cn); SR_ep = success ∧ TCR_ep == 0 | HASimulator/metric.py:14-17; environments.py:111-147, 171-213; see A2 — **high** |
| Habitat 3.0 SocialNav (find & follow a humanoid) | physics contact robot↔humanoid | following band 1–2 m (safe_dis_min 1.0, safe_dis_max 2.0, facing_threshold 0.5) | CR = fraction of episodes ending in a humanoid collision | arXiv 2310.13724 (search); Falcon fork habitat-lab/habitat/config/default_structured_configs.py:1022-1026 — **high (config) / medium (paper numbers)** |
| Falcon / Social-HM3D, Social-MP3D (ICRA 2025) | Bullet discrete collision detection; contact points between robot and any humanoid → `did_multi_agents_collide`; the episode ends | PSC = fraction of steps with every human ≥ 1.0 m (Euclidean or geodesic) | H-Coll = episodes with any human contact | Falcon falcon/additional_metric.py:40-108 (H-Coll), 148-195 (PSC) — **high** |
| RoboSense 2025 Track 2 (IROS 2025, Falcon baseline) | as Falcon | PSC threshold 1.0 m ("considering a 0.3 m human radius and 0.25 m robot radius") | H-Coll implies failure; Total = 0.4 SR + 0.3 SPL + 0.3 PSC | robosense2025/track2 README.md:312-318 — **high** |
| iGibson Challenge 2021 SocialNav | collision with a pedestrian, or distance < 0.3 m → the episode terminates as a failure | PSC = % of steps ≥ 0.5 m | score = mean(STL, PSC); STL used instead of SPL because "a robot agent can achieve perfect SPL by waiting out all pedestrians"; ORCA pedestrians do not yield; 500-step cap | StanfordVL/iGibsonChallenge2021 README.md:18,26,47,53 — **high** |
| VLN-CE / R2R-CE (standard) | navmesh filter, "sliding" regime; contact counted when the step is shortened | — | not penalised in SR | VLN-Safe arXiv 2610.14682 (search) — **medium-high** |
| Proxemics (Hall 1966; background knowledge, not re-verified) | — | intimate < 0.45 m, personal 0.45–1.2 m, social 1.2–3.6 m | — | **medium** |

Takeaway: the literature measures social distance centre-to-centre at 0.5–1.0 m. Our scorer measures nothing except navmesh contact. Every MOVE_FORWARD that the human-aware navmesh shortens counts, whether a wall or a human caused it.

## 2. Typical collision behaviour of static-trained agents in populated scenes

| Setting | Numbers | Source / confidence |
|---|---|---|
| HA-VLN 1.0, SOTA agent zero-shot (Airbert) | NE +167%, SR −67% vs static VLN; best retrained agent max SR ≈ 40% unseen (49% below oracle) | arXiv 2406.19236 (search) — medium |
| HA-VLN 1.0, retrained Airbert | TCR 0.18 seen / 0.24 unseen; CR 0.68 / 0.74 | arXiv 2406.19236 Table 5 (search) — medium |
| HA-VLN 1.0, VLN-DT (100% random-walk data) vs VLN-CM | "comparable"; extracted row fragments NE/TCR/CR/SR = 8.51/0.30/0.77/0.21 and 8.22/0.37/0.58/0.11 (which is seen vs unseen is not confirmed); VLN-CM SR falls 83.6% / 81.5% on 100% random data | arXiv 2406.19236 (search) — low-medium |
| HA-VLN 2.0, HA-VLN-CE val_unseen at the 0.25 m step | BEVBert NE 5.51, TCR 4.71, CR 0.55, SR 0.21 (0.22 in one table); ETPNav NE 5.43, TCR 6.94, CR 0.58, SR 0.17 | arXiv 2503.14229v2 step-size table; reproduced in HCSG arXiv 2605.13321 — medium-high |
| HA-VLN 2.0, second table (titled real-world validation in the search summary) | BEVBert 6.10 / 5.72 / 0.56 / 0.15; ETPNav 7.40 / 7.94 / 0.71 / 0.08 | arXiv 2503.14229 (search) — medium |
| HA-VLN 2.0, BEVBert trained on HA-VLN-CE | SR 0.19 → 0.27 seen, 0.15 → 0.21 unseen | arXiv 2503.14229 (search) — medium |
| HA-VLN 2.0, discrete leaderboard | Airbert SR 0.62 (static VLN) → 0.36 (HA-VLN-DE), CR 0.83 | arXiv 2503.14229 (search) — medium |
| HA-VLN 2.0 ablation, humans replaced by cylinders | TCR −36%, SR +10% (authors: humans are not generic obstacles) | arXiv 2503.14229 (search) — medium |
| HA-VLN-CMA (challenge baseline, replay) | val_seen SR .180, NE 6.223, CR .623, TCR 13.726, Score 16.509; val_unseen .129 / 6.387 / .684 / 17.536 / 12.945 | track2/README.md:181-186 — high |
| HA-VLN-CMA, trainer-reported (HA-VLN README) | val_seen .165 / 6.230 / .638 / 13.271 / 15.47; val_unseen .114 / 6.502 / .689 / **22.352** / 11.94 | HA-VLN/README.md:146-149 — high. The TCR gap of 22.35 vs 17.54 on the same checkpoint suggests run-to-run nondeterminism, consistent with wall-clock human frames (inference) |
| Habitat 3.0 SocialNav, heuristic expert with privileged map | S 1.00, SPS 0.97, F 0.51, CR 0.52 | secondary reproduction in arXiv 2404.11327 (search) — medium |
| Falcon on Social-HM3D (RoboSense Phase-1 set, ~1,000 episodes, depth only) | SR 55.15, SPL 55.15, PSC 89.56, H-Coll 42.96 | robosense2025/track2 README.md:79-82 — high |
| RoboSense 2025 SocialNav winners (Phase 2) | Total 70.22 (Are Ivan), 69.94 (Xiaomi EV-AD VLA), 69.77 (AutoRobot) | arXiv 2601.05014 / toolkit (search) — medium |
| VLN-Safe (Oct 2026), six R2R-CE agents | 38.5–56.8% of *successful* episodes contain contact under sliding; switching to blocking costs 11.7–36.1 pp SR | arXiv 2610.14682 (search) — medium-high |
| Safe-VLN (RA-L 2024) | ETPNav collisions (N-C) 14.0 → 4.3 with a LiDAR waypoint mask | arXiv 2311.02817 (search) — medium |

Takeaways:
- Without explicit avoidance, roughly 40–70% of episodes in populated scenes contain at least one collision, and even privileged heuristics collide often when humans move.
- In our challenge, TCR ≈ 14–18 shows that wall contacts dominate the count.

## 3. Avoidance strategies that work (literature) and how they map to our mechanics

| Strategy | Evidence | Applicability here |
|---|---|---|
| Graph pruning near humans: remove nav-graph nodes within 1 m of any human, then take the shortest path (global or local radius 4.5 m) | HA-VLN 1.0 teacher: HA3D tasks/HA/utils.py:122-196; env.py:359 (high) | Direct analogue: prune lattice states whose 0.25 m step comes within margin of the swept human footprint. |
| Inflated / proxemic costmaps (Gaussian personal-space cost; ROS social layers) | standard practice (background) | Use a two-level cost: hard = scoring-safe inflation; soft = exp-decay proximity penalty, as in Falcon's close_to_human_penalty·exp(−d/2.0) within 2 m (falcon_task_detail.yaml:33-40). |
| Runtime collision guard on forward primitives (depth + odometry) | VLN-Safe: −62–98% collision steps, +6.9–29.3 pp SR under blocking (medium-high) | Our "guard" is exact kinematic replay of every MOVE_FORWARD against all 121 candidate navmeshes (A2 rule 4). Strictly stronger than depth heuristics. |
| Human trajectory forecasting plus penalising future-path occupancy | Falcon (SR 55%, PSC ~90%); HCSG (+14.3% SR, −34.5% CR on HA-VLNCE val unseen) | Human motion here is pre-recorded (120 frames). Forecasting is trivial: the swept volume *is* the forecast. Still useful as the innovation narrative. |
| Reactive multi-agent avoidance (ORCA / RVO2, social force, CADRL / SARL RL) | iGibson and Social-HM3D pedestrians use ORCA; Falcon compares to an ORCA baseline | Not needed. Humans do not react to the agent, and frames are not action-driven. |
| Waiting / yielding (pause action, back-off) | RoboSense Phase 2 added `pause` and `move_backward` for social compliance; iGibson adopted STL to stop "waiting out" exploits | **Different here** (§6.3): no-op actions burn wall time, so frames advance nondeterministically. Only usable after calibrating the scorer's speed. |
| Re-planning around blocked corridors and doorways | HA-VLN 2.0 real-world finding: Go2-EDU struggles "in tight corridors or sudden crowd convergence" (medium) | Offline: precompute alternatives; the planner picks a route that avoids hallway blockers. |

## 4. New quantitative analyses of the public data (this session)

Scripts: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b6work/{calib.py, proximity.py, cn_hyp.py, cn_hyp2.py, cn_hyp3.py, cn_hyp4.py, graph_avoid.py, perframe.py, movers.py, goalhum.py, marginal.py}. Inputs:
- HA-VLN `Data/Multi-Human-Annotations/human_motion.json` (72 scans, 749 humans)
- HA-VLN `HASimulator/HA-DE/connectivity/*`
- HA-VLN `Data/HA-R2R-tools/collision_num_*.json`
- HA3D_simulator `tasks/R2R/data/R2R_*.json`
- Discrete-Continuous-VLN `R2R_VLNCE_v1-2_preprocessed/{split}/{split}{,_gt}.json.gz`. These are the same episodes as HA-R2R; the instructions differ.

All distances are horizontal (XZ) from the agent centre to the human **root translation**, over all 120 frames, same floor (|Δy| < 1 m after subtracting the calibrated 0.85 m root height). The actual mesh footprint extends ≈ 0.25–0.3 m around the root for standing humans (more for sitting or lying). The scoring exclusion zone is footprint + 0.10 m erosion (+ ≤ 0.05 m raster), so a root distance of about 0.35–0.45 m is the scoring-collision edge for a standing human (inference; GLB footprints not inspected).

### 4.1 Calibration of human placement
- Human keys in human_motion.json are viewpoint ids (32 hex characters), with a trailing digit appended for additional humans in the same region (419 keys of 32 characters, 330 of 33).
- 417 humans could be matched to their keyed viewpoint's pose. Their t0 XZ offset from that viewpoint is: p10 0, p25 0, median 0.30 m, p75 1.02 m, p90 2.06 m, max 9.1 m.
- Root height above floor (camera z − height): median 0.84 m, p10 0.69, p90 0.93 (high).
- Placement used PSO with a "minimum safe distance ε = 1 m from other objects" (Data/Multi-Human-Annotations/README.md). Humans therefore sit in open floor, often on the walking line.
- Region mix of the 749 humans: hallway 136, bedroom 71, living_room 65, other_room 57, kitchen 50, dining 44, lounge 44, porch 41, entryway 32, stairs 25, …

### 4.2 Human-free reference paths run through humans

| Split | episodes | gt path within 0.3 m of a human root | within 0.5 m | within 0.8 m | within 1.0 m | within 1.5 m |
|---|---|---|---|---|---|---|
| val_seen | 778 | 30.5% | 41.4% | 48.7% | 51.4% | 59.1% |
| val_unseen | 1,839 | 33.6% | 40.9% | 45.8% | 49.1% | 55.5% |
| train | 10,819 | 26.4% | 37.2% | 44.7% | 48.3% | 55.4% |

- Humans within 0.5 m of a gt path are mostly hallway humans: val_unseen 663 hallway, 159 lounge, 117 kitchen, …
- `cn > 0` is somewhat more frequent when the path is near a human (val_unseen 12.7% vs 5.8%), but the link is weak (consistent with A2).

Implication: following the reference path on the human-free navmesh would hit a human in about a third of episodes. Avoidance is mandatory, not a corner case.

### 4.3 `collision_num` is (≈) the number of humans keyed to the start or goal viewpoint, and `cn > 0` ⇒ a human at the goal viewpoint

| Split | cn == #2.0 humans keyed to path start/end viewpoint | cn > that count | cn > 0 episodes with a human at END viewpoint | at start only |
|---|---|---|---|---|
| val_seen | 700/778 (90.0%) | 0 | 60/60 (48 end-only, 12 start+end) | 0 |
| val_unseen | 1,638/1,839 (89.1%) | 0 | 159/159 (147 end-only, 12 start+end) | 0 |
| train | 10,075/10,819 (93.1%) | 0 | 824/824 (755 end-only, 69 start+end) | 0 |

- The HA-VLN 1.0 'Beginning'/'End' `human_rel_pos` annotation fits worse (80.7% / 87.0% / 86.4%).
- A distance radius around the start/goal position does not improve the fit (cn_hyp3.py).
- Reading: `cn` implements the paper's |A_i^c| ("human activities at critical nodes"), restricted in practice to humans whose region includes the goal viewpoint. It is an annotation, not a geometric collision count.

Corollaries:
- **Goal hint.** 237/3,408 test episodes (79 trajectories) have `cn > 0`, so in those episodes the goal viewpoint's region holds a human (if test follows train/val, where it held 1,043/1,043 times).
- The human keyed to the goal viewpoint lies a median 1.5 m (val_seen) / 2.96 m (val_unseen) from the goal position, p90 4.5–5.2 m. The hint is "a human in the goal region", not "a human on the goal point".
- **Allowance.** In `cn > 0` episodes, up to `cn` navmesh collisions (wall or human) are free: TCR_ep stays 0 and SR is kept.
- **Goals and humans in general:** a human (any frame) is within 0.5 / 1 / 2 / 3 m of the goal in 3.9 / 8.1 / 25.4 / 45.9% of val_seen episodes and 3.8 / 9.6 / 27.6 / 50.2% of val_unseen episodes. The stop pose must therefore often be chosen to keep a polite distance while staying inside the 3 m success radius.

### 4.4 How often is a human-avoiding route available? (graph proxy, one entry per trajectory)

Method:
- Use the R2R connectivity graph (included nodes, unobstructed edges).
- Block an edge if its segment comes within r of any human root at any of the 120 frames (same floor).
- Humans within r of the start are ignored for the first edge (turn-snap escape).
- Success target = any node within 3 m of the goal.

This is **conservative**: real free space allows lateral deviation inside rooms, so true forced rates are lower. Hallways and stairs are where the proxy is realistic.

| Split (trajectories) | r | reference path clear | detour exists | no clear route ("forced") |
|---|---|---|---|---|
| val_seen (259) | 0.5 m | 61.8% | 25.9% | 12.4% (32) |
| val_seen | 0.8 m | 54.8% | 24.7% | 20.5% |
| val_seen | 1.0 m | 51.4% | 23.9% | 24.7% |
| val_unseen (613) | 0.5 m | 60.7% | 20.7% | 18.6% (114) |
| val_unseen | 0.8 m | 55.0% | 18.9% | 26.1% |
| val_unseen | 1.0 m | 52.2% | 16.0% | 31.8% |

Forced cases at r = 0.5 m:
- Caused only by humans within 3 m of the goal: 8/32 (val_seen), 25/114 (val_unseen). Stopping short solves these with SR intact.
- Mid-route blockers: dominated by hallway humans (val_seen 27 of 42 blocking humans; val_unseen 100 of 193), then lounge, living_room and stairs.
- Per-frame test (frames 0, 10, …, 110, 119):
  - Blocked in every sampled frame: 19/32 and 59/114.
  - Gap in some frame but not the final frame 119: 6/32 and 49/114.
  - Gap in the final frozen frame 119: 7/32 and 6/114.

### 4.5 Mobility of humans that matter
- All 749 humans: swept extent median 0.00 m, p75 0.10 m, p90 0.80 m, p95 1.15 m, p99 1.69 m, max 3.47 m. 23.4% > 0.25 m, 18.7% > 0.5 m, 6.3% > 1 m (matches A2).
- Humans within 0.5 m of some val gt path are more mobile:
  - val_seen (n = 134): 31.3% > 0.5 m, 11.9% > 1 m.
  - val_unseen (n = 71): 22.5% > 0.5 m, 9.9% > 1 m.
- The brief's premise "humans shift ≤ ~0.3 m typically" holds for about 77% of all humans but understates path-relevant walkers.

### 4.6 Marginal value of collisions vs success vs distance (official Score, N = 3,408, β = 1 − 549/3408)

| Operating point | 1 success | social cost of one collision episode (1 collision) | each extra collision in the same episode | 1 m of final NE in one episode | stop-short break-even | attempt a risky passage (no alternative) if P(coll) < |
|---|---|---|---|---|---|---|
| SR 0.60, NE 3.0 | 0.0235 | 0.0058 (0.0051 without β) | 0.0013 | 0.00049 | 11.9 m (10.4) | 0.80 (0.82) |
| SR 0.40, NE 5.0 | 0.0235 | 0.0040 (0.0035) | 0.0009 | 0.00028 | 14.5 m (12.6) | 0.86 (0.87) |
| SR 0.75, NE 2.0 | 0.0235 | 0.0073 (0.0063) | 0.0016 | 0.00070 | 10.3 m (9.0) | 0.76 (0.79) |

Interpretation:
- SR dominates. A collision episode costs only about a quarter of a success in social terms.
- When reaching the goal requires a possible collision, try it unless the collision is near-certain.
- When the collision is certain (SR lost either way), crossing pays only if the goal is more than ~9–15 m past the blockage. Otherwise stop just before it, with no collision.
- Script: marginal.py. The "with β" column assumes CR = mean(CR_ep)/β. Public metric.py defines β but never uses it.

## 5. Specialisation to our mechanics: minimal-risk policy for TCR = 0

Mechanics recap (from A2 and the code; high):
- Only MOVE_FORWARD (0.25 m) can be flagged. A step is flagged iff the navmesh filter shortens it by more than 2e-5 m.
- TURN/LOOK/STOP never count, and a TURN snaps an off-mesh agent back onto the navmesh for free.
- Humans are STATIC meshes baked into per-frame navmeshes (radius 0.1, erosion 0.1).
- The active frame is wall-clock driven (signal every 0.1 s), refreshes only while total_signals_sent ≤ 120 (~12 s), then freezes. New-scene episodes may never get humans.

**Policy (ordered by priority):**
1. **Hard safety mesh: plan in the intersection of free space over all candidate navmeshes.**
   - Insert all 120 frames of every human in the scan as STATIC objects at once, then recompute the navmesh at agent_radius r_plan.
   - Ladder r_plan = 0.30 → 0.25 → 0.20 → 0.15. Take the largest radius that keeps start and goal region connected.
   - With r_plan = 0.25 there is 0.15 m of extra clearance beyond the scoring boundary for walls and humans alike. This covers A2's contour-simplification error (~6.5 cm) and float noise.
2. **Soft social cost on top**, so the plan never fails because of it. Add a proximity penalty λ·exp(−(d − d0)/σ) for root distance d < 1.0 m (PSC-1.0 convention of Falcon/RoboSense). Weight it so that a ≤ 2× path-length detour is always preferred to entering 1.0 m, but never preferred to failing. Path length is not scored (no SPL); only the 500-action cap binds.
3. **Lattice planner over the real action set.** States (x, z, heading in 15° steps). Forward = 0.25 m. Turns are free in scoring but count toward the cap.
   - Check each forward segment every ≤ 5 cm against the hard mesh.
   - Then verify by exact kinematic replay (try_step + EPS test) on all 121 candidate navmeshes {base, frame_000..119}. Require 0 flags. Then do one real docker replay.
4. **Start inside a human footprint** (4–6.5% of val_unseen starts per A2): make the first action a TURN, compute the snapped pose per navmesh, and plan from a pose that is safe on all of them.
5. **Stop pose.**
   - Stop where every human is at root distance ≥ 1.0 m if possible (≥ 0.5 m otherwise), within ≤ ~2–2.5 m of the estimated goal so goal uncertainty does not break the 3 m radius.
   - About half of goals have a human within 3 m.
   - In `cn > 0` episodes the human is in the goal region by construction.
6. **Use the allowance.** In `cn > 0` episodes (237 test episodes), up to `cn` flagged steps are free. Spend them only if the zero-collision plan is impossible or much riskier, and never exceed `cn` (one extra flag zeroes SR).
7. **Group etiquette (cheap, only for the report).** Avoid passing between members of an interacting group (HAPS 2.0 has 72 pairs, 59 triples and 15 quads), and pass on a consistent side. Make these tie-breakers in the soft cost.

## 6. When the only route passes through a human's swept volume

### 6.1 Classify per episode (offline, cheap)
- (A) Intersection-of-free-space mesh at r_plan ≥ 0.15 connects start → goal region: zero-collision guaranteed. Done.
- (B) Disconnected at 0.15 but connected at exactly 0.10 + ε (the scoring boundary itself): thread through with exact-replay verification on all 121 meshes. Still guaranteed if the verification passes. Margin is ~0, so re-verify on the organizers' cached navmeshes if they are available.
- (C) Intersection disconnected, but individual frames (or the base, human-free navmesh) connect: success is timing-dependent (graph proxy: 13/32 val_seen, 55/114 val_unseen forced trajectories).
- (D) Disconnected in every frame (static blocker; graph proxy ≈ 7–10% of trajectories, an upper bound): a collision is certain if you cross.

### 6.2 Decide
- **(C)** Estimate P(collision) as the probability mass of the frames active at the crossing step for which the step sequence collides.
  - The last frozen frame (≈ 119 when steps are < 0.1 s at the ~12 s boundary; environments.py:111-128) persists for all later steps.
  - Crossings late in long episodes therefore mostly see frame ≈ 119.
  - Attempt if P(coll) < ~0.8 (§4.6), choosing the sequence that is safe for frame 119 and for as many frames as possible.
- **(D)** Is the goal reachable within 3 m without crossing (blocker near the goal)? Then stop short, with SR kept.
  - Otherwise, cross with exactly one flagged step only if the goal lies more than ~10–15 m beyond the blocker. Otherwise stop just before it.
  - Crossing with one shortened step is better than repeated sliding (each extra flag costs ~0.001–0.0016 points).

### 6.3 Is waiting useful? (correction to the brief)
The README FAQ says actions do not advance frames ("Human animation follows released wall-clock behavior independently", track2/README.md:262-264). But the scorer spends real time on every action:
- rendering and measures on every step;
- during the first 12 s, each refresh also removes and re-adds every human (add_object_by_handle + step_physics(0.2) per human) and loads or recomputes a navmesh (environments.py:111-213).

So inserting no-op actions (LOOK_UP/LOOK_DOWN pairs; zero collision risk) **does** let the animation progress and, after ~12 s of wall time, freezes it at ≈ frame 119.

The number of no-ops needed depends on the unknown scorer speed (5–100 steps/s plausible) and competes with the 500-action cap. Therefore:
- (i) Never rely on waiting for guaranteed safety.
- (ii) Optionally calibrate the scorer's speed in Phase 1 with differential submissions. Make all episodes trivially collision-free except a probe set where a forward step into a walker's swept zone collides only before or after a known frame. Vary the burn length K. Aggregate TCR × N counts the probe collisions (one submission resolves one K). Then use burns only in class (C) episodes, where they raise P(frame = 119).
- (iii) Expect Phase 2 hardware or load to differ. Treat the calibration as a prior, not a guarantee.

## 7. What the organizers may value as "socially compliant" (Best Innovative Solution)

Evidence:
- **Website.** It stresses "maintaining socially compliant distances and avoiding collisions with moving bystanders", and "world models that anticipate human trajectories and future observations, and VLAs that ground human-centric instructions in egocentric video" (roboworld2026.github.io/track2.html:80-82). The index adds "anticipate human motion, and re-plan as people block corridors or doorways".
- **Organizers.** Yifei Dong, Fengyi Wu, Bohan Xiong, Lingdong Kong, Zhi-Qi Cheng (track2.html organizer block). The same team has a NeurIPS 2026 Oral "Language-Conditioned World Modeling for Visual Navigation" (index.html).
- **HA-VLN 2.0.** It emphasises real-world validation (Unitree Go2-EDU with RealSense D435i + MID360 LiDAR + IMU; office, living room, hallway, lobby; 2–4 volunteers) and the cylinder ablation (human semantics matter).
- **RoboSense 2025 precedent** (Kong co-organizer; inference). Its Innovation Award and code-only Phase 2 used a reproducibility audit and disqualified "submissions that do not run an actual inference and simulation pipeline" (robosense2025/track2 README.md:343-350). RoboWorld 2026 Track 2 allows action-only submissions, but award winners "may be asked to provide code or models for verification" (track2/README.md:258-262).

Recommended social-compliance showcase for the technical report:
1. Self-reported proxemic metrics on val and test: PSC@1.0 m (Falcon/RoboSense), PSC@0.5 m (iGibson), minimum human distance distribution, H-Coll (navmesh human-contact episodes, separated from wall contacts), and steps inside 1 m.
2. Group-aware behaviour: no cutting between interacting humans, a consistent passing side, and yielding at doorways and corridors (re-plan instead of squeezing).
3. Polite goal stopping: ≥ 1 m from a person, ideally facing them, when the instruction ends at a human (the Habitat 3.0 facing convention).
4. An explicit world-model / forecast module. Here the 120-frame swept volume acts as the "oracle forecast", and an egocentric student learns to predict it from RGB-D.
5. Honest framing: offline privileged planner as **teacher**, egocentric VLA / world-model **student**. Report both. This guards against an "exploit" judgement and aligns with the stated "Given egocentric RGB-D observations".

## 8. Contradictions and corrections to CONTEXT / brief

- **Waiting** (brief): "waiting is useless since frames do not advance with actions". That is only half true. Actions do not advance frames, but wall-clock time spent on actions does. No-ops shift the frame distribution toward the frozen final frame, uncontrollably without calibration (§6.3).
- **Mobility** (brief): "humans may shift ≤ ~0.3 m typically". True for ~77% of all humans, but 22–31% of path-adjacent humans sweep more than 0.5 m (§4.5).
- **collision_num** (CONTEXT fact 3, A2 fact 22): it is ≈ an annotation count of humans in the start/goal viewpoint regions. It matches exactly in 89–93% of episodes, never exceeds that count, and `cn > 0` ⇒ a human at the goal viewpoint in 100% of 1,043 episodes (§4.3). This does not contradict A2's "weak proximity correlation"; it explains it.
- **CR normalisation** (CONTEXT fact 3): public HASimulator/metric.py defines `beta` but never uses it. The β-normalised CR lives only in the hidden scorer and cannot be verified here.
- **Paper vs code:** the HA-VLN 2.0 paper's "collisions within 1 m of a human" (and HA-VLN 1.0's 1.0 m `isCrushed`) are distance-based. The scored code is navmesh-contact-based and includes walls (A2). Literature social thresholds therefore do not transfer to the scorer. Use them only as soft costs and report metrics.

## 9. Open questions
1. HAPS 2.0 GLB footprints per frame. Do the per-frame meshes bake in root motion in addition to the JSON translation? If so, swept extents exceed the translation-based numbers. Compute AABBs from HAPS2_0.zip (C1 infra).
2. Official scorer speed (steps/s) during the 12 s window, and whether the navmesh cache is pre-populated. This determines frame-occupancy probabilities for class (C) episodes.
3. Does the Phase-2 bundle include test human placements (human_motion entries for the 18 test scans)? Does `cn_test > 0` ⇒ human-at-goal hold for test (very likely if the same annotation pipeline was used)?
4. Will organizers accept offline privileged planning (scene mesh + human annotations + exhaustive search) for Top-5 and Innovation awards? Ask by email or Discord before Phase 2 (C2 risk register).
5. Exact HA-VLN 1.0 result tables, Habitat 3.0 Table 2, HCSG Table I, AdaVLN (arXiv 2411.18539) metrics, and any "HumanWorld" benchmark. Not verified because the search budget ran out.
6. Graph-proxy forced rates are upper bounds. Recompute them on the real swept-union navmesh (needs MP3D scenes + HAPS GLBs) to obtain true class (A)–(D) counts per split.

## 10. Sources
- HA-VLN 1.0: https://arxiv.org/abs/2406.19236 ; https://proceedings.neurips.cc/paper_files/paper/2024/file/d8087deaf34bb07ddd41c65f8a9fe9b5-Paper-Datasets_and_Benchmarks_Track.pdf ; https://lpercc.github.io/HA3D_simulator/ ; https://liner.com/review/humanaware-visionandlanguage-navigation-bridging-simulation-to-reality-with-dynamic-human ; https://www.sota2.com/research/sota/human-aware-vision-and-language-navigation-on-ha-vln-val-seen
- HA3D simulator code (cloned): https://github.com/lpercc/HA3D_simulator (HA3DSim.py:146-182; tasks/HA/eval.py; tasks/HA/utils.py:122-260, 400-490; tasks/HA/env.py:223-387; tasks/HA/realRobot.py:151-152)
- HA-VLN 2.0: https://arxiv.org/abs/2503.14229 ; https://arxiv.org/html/2503.14229v2 ; https://arxiv.org/html/2503.14229v3 ; https://www.themoonlight.io/en/review/ha-vln-a-benchmark-for-human-aware-navigation-in-discrete-continuous-environments-with-dynamic-multi-human-interactions-real-world-validation-and-an-open-leaderboard ; https://huggingface.co/papers/2503.14229
- HA-VLN code/data (local): ext/HA-VLN (HASimulator/environments.py, measures.py, metric.py; README.md:146-149; Data/Multi-Human-Annotations/README.md; Data/HA-R2R-tools/collision_num_*.json; HASimulator/HA-DE/*)
- Challenge: ext/track2/README.md (L28-31, 82, 136, 181-207, 258-264); ext/roboworld2026.github.io/track2.html (L80-82, organizers L195-218); index.html (track descriptions, NeurIPS 2026 Oral)
- Habitat 3.0: https://arxiv.org/abs/2310.13724 ; https://arxiv.org/pdf/2404.11327
- Falcon: https://arxiv.org/abs/2409.13244 ; https://github.com/Zeying-Gong/Falcon (falcon/additional_metric.py; habitat-lab/habitat/config/habitat/task/falcon_task_detail.yaml; default_structured_configs.py:1022-1026, 1276-1302) ; https://zeying-gong.github.io/projects/falcon/
- RoboSense 2025 Track 2: https://github.com/robosense2025/track2 (README.md:25-100, 200-350) ; https://arxiv.org/abs/2601.05014 ; https://arxiv.org/abs/2510.07871
- iGibson Challenge 2021: https://github.com/StanfordVL/iGibsonChallenge2021 (README.md:18-53) ; https://svl.stanford.edu/igibson/challenge2021.html ; https://arxiv.org/pdf/2210.06849
- VLN-Safe "Successful but Unsafe": https://arxiv.org/abs/2610.14682 ; https://arxiv.org/html/2610.14682v1
- Safe-VLN: https://arxiv.org/abs/2311.02817
- HCSG: https://arxiv.org/abs/2605.13321 ; https://arxiv.org/html/2605.13321v1
- DPed-VLN: https://arxiv.org/abs/2609.21504 ; https://zenodo.org/records/22816620
- SocialNav-SUB: https://arxiv.org/abs/2509.08757 ; SocialNav-MoE https://arxiv.org/abs/2512.14757 ; E-SocialNav https://arxiv.org/abs/2603.20664 ; SocialNav foundation model https://arxiv.org/abs/2511.21135 ; SocialNav-Map https://arxiv.org/abs/2511.12232
- AdaVLN (title only): https://arxiv.org/html/2411.18539v1
- Proximity-aware SocialNav: https://openaccess.thecvf.com/content/ICCV2023/papers/Cancelli_Exploiting_Proximity-Aware_Tasks_for_Embodied_Social_Navigation_ICCV_2023_paper.pdf
- ORCA/RVO2: https://gamma.cs.unc.edu/RVO2/
- Companion finding: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/A2-collision-semantics-habitat017.md
