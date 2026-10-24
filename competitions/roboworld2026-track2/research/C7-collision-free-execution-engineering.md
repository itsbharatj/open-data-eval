# C7 — Collision-free execution engineering (compliant executor + privileged teacher/oracle)

Topic id: `C7-collision-free-execution-engineering` · Date: 2026-10-24 · Author: research agent C7
`$BASE` = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`

Regime tags used below: **[C]** = compliant (inference inputs = forward RGB-D 224²/256² HFOV 90 + simulator pose (GPS+compass) + instruction; no navmesh, no human_motion.json, no simulator branching); **[P]** = privileged (navmesh, per-frame human navmeshes, exact try_step; allowed only for training labels, local evaluation and diagnostics, never to choose test-time actions; see C3 legitimacy matrix T3/T4/T13).

---

## 0. Summary

Collision counting is a pure navmesh-geometry test (A2): a MOVE_FORWARD is a collision iff its navmesh-filtered 3-D displacement is shorter than the requested 0.25 m by more than 2e-5 m (`|f-s|^2 + 1e-5 < |e-s|^2`); turns/looks/STOP never count; walls, furniture, unseen navmesh edges and human footprints all count; sliding along a wall counts on every step. The executor's job is therefore to make every forward target land strictly inside the active navmesh, whatever human frame is active during the organisers' wall-clock replay.

**[C] Compliant executor.** Build a persistent 2.5-D elevation/occupancy map from the single forward depth camera using the exact simulator pose (noise-free; GPS+compass allowed by FAQ Q9), separate humans with an off-the-shelf person segmenter, and execute through a hard forward-safety predicate: every 2.5 cm sample of the 0.25 m segment must be ≥ 0.25 m from observed static geometry, ≥ 0.20 m from unknown/barrier cells (no stepping onto unobserved floor), and ≥ 0.40 m + motion margin from any observed human surface point or human *trail*. Plans are made optimistically (frontiers allowed) but executed pessimistically (LOOK_DOWN to observe the near field before stepping into it; the level camera cannot see the floor closer than 1.25 m, and with the reported 30° tilt it sees it from 0.335 m). Routes are grid plans with a clearance cost, simplified to waypoints and converted by a 24-heading lattice search anchored at the start yaw (lateral resolution 0.25·sin15° = 6.5 cm, enough to centre in 0.7 m doors). After each forward the exact engine predicate is re-evaluated from the pose delta (contact iff `|Δp_3D|^2 + 1e-5 < 0.0625`, i.e. Δ < 0.24998 m, NOT "did not move" — vln-safe shows the "moved < 1e-4 m" proxy misses 77.7–87.6 % of contact episodes); a contact triggers a stall memory (never repeat that forward), a boundary-normal escape rule, local +0.10 m inflation and re-plan. The largest residual risk is human-timing mismatch: displacement between the frame the local agent saw and the frame the scorer shows is up to the full swept extent (p90 0.8 m, max 3.47 m, measured here); it is reduced by running the local rollout with a deterministic step-indexed human clock calibrated to the scorer speed and by keeping the union of observed human footprints (a "trail") as obstacles.

**[P] Privileged executor.** Load the 121 navmeshes that can be active during scoring (base + `<scan>_000..119`), build their intersection as a 2.5 cm free grid with a clearance field, plan with a soft clearance preference (≥ 0.20 m beyond the r=0.1 boundary, hard ≥ 0.05 m — do NOT hard-recompute at r=0.3–0.4, which closes 0.7–0.8 m doors), convert to 15° primitives with the same lattice, then verify by exact float32 kinematic emulation (Magnum TRS semantics: `q ← normalize(q·q_y(±15°))`, `p ← p + q·(0,0,−0.25)`, `try_step`, EPS test, turn re-snap) against all 121 meshes, requiring zero flags and xz-identical trajectories (frame invariance ⇒ any wall-clock mixture of frames is also collision-free). This produces DAgger/IL teacher labels with no learned collision habits (the VLN-CE ShortestPathFollower moves forward whenever heading error ≤ 15°, hugging corners) and an oracle that classifies every collision of a compliant rollout (wall / invisible edge / human-frame / start-snap) for margin calibration.

Executing a known route costs few actions (val_unseen reference path median 9.2 m ⇒ ~37 forwards; estimated median 73 / max 132 actions including a 24-turn spin), so the 500 budget leaves ample room for look-downs, detours and a forced STOP reserve.

---

## 1. Facts (verified from code/data in this session unless noted)

| # | Claim | Evidence | Conf. |
|---|---|---|---|
| F1 | Collision predicate: `collided = (‖filter_end−start‖² + 1e-5) < ‖end−start‖²` (squared lengths); only body translations can trip it; turns pass through the filter with zero displacement (never flagged, but can re-snap an off-mesh agent); LOOK_* bypass the filter; STOP clears the flag. | `$BASE/habitat-sim-0.1.7/habitat_sim/agent/controls/object_controls.py:68-89`; A2 facts 1–7 | high |
| F2 | Filter = `pathfinder.try_step` (sliding) because `ALLOW_SLIDING: True`; sliding returns the closest reachable boundary point ⇒ every wall-slide step is flagged. | `simulator.py:451-464`; `HASimulator/config/HAVLNCE_R2R_task.yaml:16`; A2 facts 8–11 | high |
| F3 | Forward kinematics: `_move_along(node, −0.25, Z)` uses `ax = transformation[2].xyz` and `translate_local(ax·d)`; in Magnum's TranslationRotationScaling transform `translateLocal` ≡ `translate` (`setTranslation(_translation+vector)`), so `p ← p + R·(0,0,−0.25)` (no double rotation). Turns: `rotate_y_local(±15°)` ≡ `rotation ← rotation·q_y(±15°)`, then `normalized()`. | `default_controls.py:31-33,36-63,77-79`; Magnum `SceneGraph/TranslationRotationScalingTransformation3D.h:127-129,153-155` (raw.githubusercontent, commit 46f4518) | high |
| F4 | HA-VLN inserts each human frame GLB as a STATIC object and recomputes/loads `<scan>_<fff>.navmesh` (r 0.1, h 1.5, include_static_objects) on a 0.1 s wall-clock signal, max 120 signals; humans freeze after ~12 s; base navmesh possible for slow new-scene resets. Active-mesh set = {base, frame 000..119}. | `HASimulator/environments.py:49-58,96-147,171-213`; A2 facts 14–18; C1 §1.3 | high |
| F5 | Sensors: RGB 224², depth 256², HFOV 90, default POSITION [0,1.25,0], depth MIN 0 / MAX 10 / NORMALIZE True (z-depth); VLN-CE GlobalGPS default DIMENSIONALITY 2; habitat default TILT 15°, the challenge config reportedly uses TILT 30° (competitor measured in image). | `HAVLNCE_R2R_task.yaml:17-24`; `$BASE/habitat-lab-0.1.7/habitat/config/default.py:218,227,239-241`; `HA-VLN/agent/VLN-CE/habitat_extensions/config/default.py:16-18`, `sensors.py` GlobalGPSSensor; `$BASE/competitor-bingchengzhang/project/havln_agent/config.py:23,28` | high (TILT 30: medium) |
| F6 | Rules clarification: inputs = initial pose, instruction, ongoing pose (GPS+compass), sequential egocentric RGB-D from ONE forward camera; human_motion.json forbidden at inference; panoramas only by rotating (actions count). | `$BASE/jostar-track2` `git diff origin/main origin/bohan/clarification-Oct14` (Input row, Q8, Q9, Q11) | high (unmerged branch) |
| F7 | VLN-CE `ShortestPathFollowerCompat` (the standard IL/DAgger oracle) issues MOVE_FORWARD whenever the heading error to the next geodesic point is ≤ 15°+1e-6 and plans on the r=0.1 navmesh ⇒ it cuts corners and slides; its greedy mode probes with `sim.step` + `set_agent_state`. | `HA-VLN/agent/VLN-CE/habitat_extensions/shortest_path_follower.py:47,82-103,115-176` | high |
| F8 | `DiscretePathPlanner` converts an (r,θ) waypoint into turns+forwards greedily, goal radius 0.13 m, "assumes infinite space devoid of obstacles". | `habitat_extensions/discrete_planner.py:8-36,38-83` | high |
| F9 | vln-safe training-free guard (`stall-mem1`): veto a forward if depth clearance at the step end < τ = 0.05 m beyond agent radius 0.1; stall veto: a forward from a pose (≤1 cm, heading within half a turn) where an executed forward moved < 1 cm is vetoed; escape = smallest turn whose 2-step ray clears τ + one forward; livelock caps (3 consecutive / 12 per episode) then "yield" (let a risky forward through). | `$BASE/sota/vln-safe/vlnsafe/guard.py:1-60,135-205,318-345`; `configs/guard/stall-mem1.yaml` | high |
| F10 | vln-safe: a forward right after a stalled forward collided every time (CMA 543,935/543,935; ETP-R1 27,085/27,085); "contact against a navmesh edge with no rendered surface reads as clear" (N11 smoke: CMA pressed into it with 0.23 m apparent clearance). | `guard.py:36-47` | high |
| F11 | vln-safe: the displacement proxy (forward moved < 1e-4 m) misses 77.7–87.6 % of episodes that had engine contact; under sliding 38.5–56.8 % of successful R2R-CE episodes contain ≥1 collision. | `README.md:11,15`; `vlnsafe/rollout.py:130-132` | high |
| F12 | vln-safe sliding-regime results (R2R-CE val_unseen, 1,839 eps): collision-free episode fraction CMA 0.502→0.664 with guard, ETP-R1 0.526→0.723, ETPNav 0.551→0.735, StreamVLN 0.527→0.674; mean collisions/episode CMA 27.2→3.2, ETP-R1 3.94→1.41; SR unchanged. Even the navmesh-oracle guard (block regime) leaves 7.8 % (ETP-R1) / 5.9 % (StreamVLN) episodes with contact (residuals from caps/"yield" and escapes). | computed this session from `results/<agent>/r2r/<arm>/episodes.csv`; `results/summary/guard_effect.json` | high |
| F13 | vln-safe: single forward camera "cannot see a wall the agent hugs sideways" — they used a 12-camera clearance ring for T1 agents; 8-frame depth memory cut veto precision to .125/.351/.650 vs .925/.877/.992 single-frame. Their projector keeps any non-floor surface incl. ceilings (rows above the horizon get `z_floor = inf`), so remembered ceiling points re-expressed near the agent become phantom obstacles — the likely cause of the precision collapse. | `clearance_predictor.py:23-26`; `stall-mem1.yaml:1-6`; `geometry.py:220-241` (inference about cause: medium) | high / medium |
| F14 | Human motion (749 humans, 72 scans): max displacement from frame 0 within frames 0..10: p99 0.25 m, max 0.35; within 0..20: p95 0.30, p99 0.49, max 0.70; within 0..30: p99 0.68, max 1.05; within 0..119: p90 0.80, p95 1.15, p99 1.69, max 3.47; per-frame speed p99 0.020 m, max 0.035 m (0.35 m/s at 10 Hz); `max_{f≤20}‖t_f − t_119‖` p90 0.80, p99 1.69, max 3.47 (a slow local run that sees frozen frame-119 humans vs a fast scorer showing frames ≤20 mismatches by the full sweep). | computed this session with `python3 -I` from `HA-VLN/Data/Multi-Human-Annotations/human_motion.json` (script `scratchpad/c7work/human_disp.py`) | high |
| F15 | R2R-CE path stats: val_unseen reference xz length p50 9.19 / p90 13.39 / max 22.08 m; 14.2 % of val_unseen (5.8 % val_seen, 8.5 % train) episodes change height > 1 m; estimated actions for a known route incl. 24-turn spin p50 73, p99 108, max 132. | computed from `$BASE/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/*/*.json.gz` (`c7work/ep_stats.py`) | high (action estimate: medium) |
| F16 | Navmesh boundary offset from rendered geometry: erosion 2 cells = 0.10 m, conservative rasterisation ≤ +0.05 m, contour simplification edgeMaxError 1.3 voxels = ±0.065 m ⇒ boundary lies ~0.035–0.215 m from geometry; small regions < 1 m² (regionMinSize 20 → 400 cells) are pruned; ledges > 0.2 m are cut (filterLedgeSpans). | A2 fact 13 (PathFinder.cpp:357-374,414-455, PathFinder.h:103-154); derivation here | medium (derived) |
| F17 | A public competitor's mapper/executor (2.5-D elevation map per floor, step tolerance 0.20 m, gap-slope 38°, wall margin 0.12 + radius 0.10 = 0.22 m, human margin 0.25 m, body half-depth 0.15, unseen-human uncertainty growth 0.3 m/s cap 1.5 m, 24-step initial spin, look-down when the route crosses unobserved cells within 1 m, LOOK_DOWN/LOOK_UP pairs as "wait"); its slide detector uses displacement < 0.8·step (misses small slides). | `$BASE/competitor-bingchengzhang/project/havln_agent/config.py:56-104`, `executor.py`, `mapping/static_layer.py`, `mapping/costmap.py` | high |
| F18 | C3 legitimacy matrix: simulator branching/backtracking search and navmesh/pathfinder at inference are not to be used in the compliant track; collision flag as bump sensor is gray — derive contact from pose deltas instead; local replay of final Phase-2 sequences only for format/determinism validation. | `findings/C3-rules-ethics-and-defensibility.md:98` (T2b, T2d, T3, T4, T13) | high (as policy) |

---

## 2. Key numbers

| What | Value | Source |
|---|---|---|
| Collision tolerance for a 0.25 m step | flagged iff 3-D displacement < 0.249980 m | object_controls.py:80-87; A2 |
| Lateral offset of one forward at ±15° | 0.0647 m (forward progress 0.2415 m) | 0.25·sin15°, 0.25·cos15° |
| Level camera: nearest visible floor | 1.25 m (bottom ray −45°) | cam h 1.25, VFOV 90 |
| Visible floor with tilt 15° / 30° | from 0.72 m / 0.335 m | 1.25/tan60°, 1.25/tan75° |
| Lowest visible height at distance d (level) | 1.25 − d (e.g. 0.90 m at d = 0.35 m) | geometry |
| Depth angular resolution | 0.35°/px (1.8 cm at 3 m) | 90°/256 |
| Navmesh boundary distance from geometry | ≈0.035–0.215 m (0.10 erosion ±0.065 simplification +≤0.05 raster) | F16 |
| Hard static clearance [C] | 0.25 m from observed geometry (0.22 only in aligned narrow passages) | design |
| Hard human clearance [C] | 0.40 m + motion margin from observed human surface/trail | 0.10+0.05+0.065+0.15 body+0.035 |
| Unknown/barrier clearance [C] | 0.20 m | design (≥0.215 holes) |
| Intersection-grid hard / preferred clearance [P] | ≥0.05 m / ≥0.20 m beyond r=0.1 boundary | design |
| 0.8 m door: centre clearance (r=0.1 mesh / geometry) | 0.30 m / 0.40 m | (0.8−0.2)/2 |
| Radius-0.30 recompute on 0.7 m door | passage ≈0.1 m (fragile/closed); r=0.4 closes ≤0.8 m doors | 0.7−2·0.3 |
| Human max speed | 0.035 m/frame (0.35 m/s) | F14 |
| Human displacement from frame 0 within 0..20 frames | p99 0.49 m, max 0.70 m | F14 |
| Human swept extent (0..119) | p90 0.80, p95 1.15, p99 1.69, max 3.47 m | F14 |
| vln-safe guard collision-free fraction (slide) | 0.66–0.74 (from 0.50–0.55) | F12 |
| vln-safe oracle-guard collision-free fraction (block) | 0.922 / 0.941 | F12 |
| Proxy (moved<1e-4) miss rate | 77.7–87.6 % of contact episodes | F11 |
| Known-route action count (val_unseen, with 24-turn spin) | p50 73, p99 108, max 132 | F15 |
| Multi-floor episodes (> 1 m height change) | 14.2 % val_unseen | F15 |
| Verification cost [P] | 121 meshes × ~100 actions × ~20–50 µs ≈ 0.3–0.6 s/episode/core | C1 §4.1 estimate |
| CMA baseline TCR | 13.7 (val_seen) / 17.5 (val_unseen) collisions per episode | track2 README; CONTEXT |

---

## 3. Design principles (both regimes)

1. **Only MOVE_FORWARD can lose points.** Turns, LOOK_* and STOP are free of collision risk; spend them freely (budget is not binding: ~75 actions for a known route vs 500).
2. **Target-inside-navmesh with margin, every step.** Never rely on sliding; a slide is a counted collision and a source of trajectory divergence between the local run and the replay.
3. **Frame invariance.** The submitted open-loop sequence is replayed with unknown human frames. A plan is robust iff every forward lands exactly on its nominal target under every candidate navmesh; then any per-step mixture of frames is also collision-free and the trajectory is identical (induction over steps). [P] verifies this exactly; [C] approximates it with human margins/trails.
4. **Optimistic planning, pessimistic execution [C].** The planner may route through unknown cells (frontiers), but the executor only steps when the target neighbourhood is observed free; otherwise it looks (LOOK_DOWN / turn) first.
5. **Exact pose, persistent map [C].** Simulator pose is noise-free, so a global map accumulated over the whole episode is safe; filter points by height relative to the local ground (fixes the vln-safe memory failure).
6. **Never "yield".** vln-safe's caps let flagged forwards through and leave residual collisions; we re-plan, take a detour, or STOP instead.
7. **Contact = engine predicate from pose delta**, not "did not move".
8. **STOP always, within 500.** Success requires STOP; reserve actions to reach the chosen stop point.

---

## 4. [C] Compliant executor

### 4.1 Interfaces
- Input per step k: `rgb (224²)`, `depth (256², normalised ×10 m, z-depth)`, `pose = (p_xyz, yaw)` from simulator agent state (Q9), `tilt_steps` (own bookkeeping), `subgoal` from the VLN policy (waypoint `(x,z[,floor])`, or `STOP_REQUEST(goal_hyps)`), `steps_used`.
- Output: one action ∈ {MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, LOOK_UP, LOOK_DOWN, STOP} and an event (`SEGMENT_DONE`, `PATH_BLOCKED`, `CONTACT`, `NEED_POLICY`).
- Headings: `H = {yaw0 + 15°·k : k = 0..23}` anchored at the start yaw (start yaw is arbitrary, not a multiple of 15°).

### 4.2 Map layers
- **Static 2.5-D layer** (per floor, 5 cm cells, 48 m window centred at start): `ground[i,j]` = min height of points below camera−0.05 m seen from above; `top[i,j]` = max height in (ground, ground+1.75]; cell OCCUPIED iff `top−ground > 0.20` (vertical structure / table tops / overhangs below 1.6 m) or step barrier `|Δground| > 0.20 + tan38°·gap` (ledges, platform edges, cliffs) or `forced` (contact memory); FREE iff ground known and not occupied; UNKNOWN otherwise. Ceiling points (height > ground+1.75) ignored. Agent footprint cells are always FREE at the agent's foot height. (Reuse competitor `StaticLayer` logic, fix nothing but the thresholds.)
- **Human layer**: person instance masks from RGB (open-weight YOLO-seg / Mask2Former; allowed by Q10), resized 224→256 and dilated 3 px; back-projected human points with height in [0.1, 1.8] m. Per track: current points, centre, velocity, and a **trail** = list of `(local_frame_time τ, points)`. Human points are excluded from the static layer. Depth points that appear inside previously-FREE observed cells at body height are tagged *dynamic* (fallback detector when segmentation misses).
- **Contact memory**: list of `(p_start, k, target, normal)` for every forward that tripped the post-check.

### 4.3 Forward-safety predicate
```text
SAFE_FWD(p, k, step):                          # p: current position, k: heading index
    t = p + 0.25 * dir(k)
    if any |t - c.target| < 0.05 for c in contacts: return False          # vln-safe stall rule, generalised
    if any |p - c.p_start| < 0.01 and c.k == k for c in contacts: return False
    for s in (0.025, 0.050, ..., 0.250):                                 # 10 samples
        q = p + s * dir(k)
        if dist_static(q)   < R_STATIC(q):  return False                 # 0.25 m (0.22 in an aligned narrow passage)
        if dist_unknown(q)  < 0.20:          return False                 # unobserved floor or barrier
        if dist_human(q, window(step)) < 0.40 + motion_margin(q, step): return False
    if floor_changes_too_fast(p, t): return False                        # |ground(t)-ground(p)| > 0.20 per 0.25 m
    return True
```
`dist_*` come from EDTs of the local 8×8 m window, recomputed when the map version changes (≈1 ms at 5 cm). `window(step)` = human footprints observed at local frame times τ ∈ [F_lo(step), F_hi(step)] (default [0, min(119, 2·step)], see 4.6) plus extrapolated positions for unobserved τ (velocity × Δτ, growth 0.035 m/frame, cap 1.5 m).

### 4.4 Planning and primitive conversion
```text
PLAN(p, k, subgoal):
    G = classify(static layer)                               # FREE / OCC / UNKNOWN
    cost(cell) = 1 + 20*max(0, 0.40 - d_static)^2/0.15^2 + 2*[UNKNOWN] + 40*max(0, 0.8 - d_human)/0.4
    hard(cell) = d_static >= 0.25 and d_human >= 0.40       # unknown allowed in planning (frontier)
    path = Dijkstra/A*(G, cost, hard, p -> subgoal)
    if path is None: retry with R_STATIC = 0.22 for corridor cells whose axis is within 15 deg of a lattice heading
    if path is None: return PATH_BLOCKED                      # policy picks another subgoal; never relax humans below 0.30
    wps = simplify(path, max_dev = 0.05 m, keep d_static >= 0.25)     # Douglas-Peucker with clearance check
    return LATTICE(p, k, wps)

LATTICE(p, k, wps, horizon = 3 m):                          # A* over (x, z, k); actions are the cost unit
    open = [(h(p,k), 0, p, k, [])]; closed = {}
    while open:
        f, g, p, k, acts = pop(open)
        key = (round(p.x/0.03), round(p.z/0.03), k)
        if key in closed: continue; closed.add(key)
        if reached(p, wps, tol = 0.13) or progress(p) >= horizon: return acts
        for a in (FWD, LEFT, RIGHT):
            if a == FWD:
                if not SAFE_FWD_PLAN(p, k): continue           # same predicate, unknown treated as cost not veto beyond 1.25 m
                p2, k2, c = p + 0.25*dir(k), k, 1 + clearance_penalty(p, k)
            else:
                p2, k2, c = p, (k +/- 1) % 24, 1
            push(open, (g + c + h(p2, k2), g + c, p2, k2, acts + [a]))
    return None
h(p, k) = geodesic_on_grid(p, wps)/0.25 + min_turns(k, grad_dir(p))     # grid Dijkstra field as heuristic
```
Notes: positions are accumulated in float32 exactly like the simulator (F3) so the plan and the executed pose agree to ~1e-6 m. A straight corridor at angle α between two lattice headings is tracked by alternating headings every n steps with lateral error ≤ 0.25·n·sin(min(α,15°−α)); n is chosen so the error stays < 0.05 m (≈1 turn per 3–4 forwards in the worst case). Replan every 4 steps or on map change near the path.

### 4.5 Main loop (one action per call)
```text
ACT(obs, pose, subgoal):
    observe(obs, pose)                                         # update layers (uses tilt_steps)
    if pending_post is not None: POST_CHECK(pending_post, pose)
    if tilt_steps != 0: return LOOK_UP/LOOK_DOWN to level   # keep the level camera for the VLM except during looks
    reserve = len(PLAN(pose, stop_point_estimate)) + 1 + 5
    if steps_used >= 499 or 500 - steps_used <= reserve: return go_to_best_stop_then_STOP()
    if subgoal is STOP_REQUEST: return STOP_PLACEMENT(subgoal.goal_hyps)  # 4.9
    acts = cached_plan if still valid else PLAN(pose.p, pose.k, subgoal)
    if acts is None: return event NEED_POLICY (policy chooses a new subgoal; executor may turn to look)
    a = acts[0]
    if a == FWD:
        if near_field_unknown(pose, k):                       # target disc not yet observed
            return LOOK_DOWN                                   # LOOK_UP follows next call (2 actions)
        if not SAFE_FWD(pose.p, k, steps_used):
            invalidate plan; return ACT(...) with replanned acts (or a TURN toward the freest known heading)
        pending_post = (pose.p, pose.k, pose.p + 0.25*dir(k))
    return a

POST_CHECK((p0, k, target), pose):
    d2 = |pose.p - p0|^2  (3-D, from simulator state)
    if d2 + 1e-5 < 0.0625:                                     # exact engine predicate
        n = normalize_xz(pose.p - target)                      # boundary normal (slide lands at closest boundary point)
        contacts.append((p0, k, target, n))
        static.force_obstacle(disc(target, 0.10)); local_inflate(target, +0.10, radius 1.0 m)
        constraint: next forward heading must satisfy dir(k').n >= 0.5 (moves >= 0.125 m away from the boundary)
        invalidate plan; log CONTACT (episode SR is already lost unless collision_num>0; keep going for NE)
```
Start of episode: action 1 is always a TURN (free re-snap if the start lies in a human hole); default opening = "pitched panorama" `12 × (TURN, TURN, LOOK_DOWN, LOOK_UP)` = 48 actions (level views every 30° for the policy + near-floor coverage), or 24 TURNs + selective look-downs if budget is tight.

### 4.6 Human timing in the local rollout
- In the official replay the human frame at step k is ≈ 10·(wall time since reset) and freezes at 119; with scorer speed S steps/s, frames ≈ 10k/S. A slow VLM-in-the-loop local run under the real wall clock shows frozen frame-119 humans almost immediately, while a fast scorer shows frames ≤ 20 for most of a 100-step episode — mismatch = the full sweep (F14).
- Recommendation: run local closed-loop rollouts with a **deterministic step-indexed human clock** `frame(k) = min(119, ⌊r·k⌋)` (C1's `FrameScheduler` R3), r = 10/S_est, S_est measured (havln-score-phase1 in the image; Phase-1 genuine submissions compared against local replays at several r). This is a local-simulator configuration, the agent still consumes only RGB-D+pose — but **confirm with organisers** (open question). Then the agent observes each visible human at the frames the scorer will show (± timing error), and the trail window `[F_lo, F_hi]` stays narrow.
- Until S is known: r = 2 frames/step (covers scorers ≥ 5 steps/s), trail window [0, min(119, 2k)], plus extrapolation for unobserved frames. Humans first seen late (already frozen locally) get motion_margin = min(1.5, 0.035·frames_unobserved) on their unobserved history.
- Waiting (LOOK pairs) does not transfer: in the replay a LOOK pair takes tens of ms, not the local time. Never plan on a human "having moved away".

### 4.7 Narrow passages, stairs, start-in-human
- **Doors** (0.7–0.9 m): centre clearance from geometry 0.35–0.45 m ⇒ slack ±0.10–0.20 m with R_STATIC 0.25; approach so the last two forwards before the door are on one lattice heading within ±15° of the door normal; centre laterally using single ±15° forwards (6.5 cm per step). If the door is narrower than 0.70 m (centre clearance < 0.35 m) the 0.25 rule leaves < 0.1 m slack — use 0.22 only for aligned crossings ≤ 4 steps long, and log it.
- **Stairs** (14 % of val_unseen episodes): elevation layer treats risers ≤ 0.20 m as traversable; descending stairs are invisible from the level camera — LOOK_DOWN before every forward whose target is within 1.25 m beyond a downward height change; switch floor layer when |y − y_ref| > 1.0 m for 3 steps; the collided test is 3-D so stair steps never false-flag (filtered displacement ≥ 0.25 when going up/down).
- **Start overlapping a human** (A2: 75/1,833 val_unseen starts within 0.3 m of some human frame): first action TURN; if human points lie within 0.6 m in the first frames, add +0.35 m spread margin to static and human checks for the first 2 m (the replay may snap differently than the local run).

### 4.8 Stop placement [C]
```text
STOP_PLACEMENT(goal_hyps = [(g_i, w_i)]):                     # from the policy / VLM (landmark + depth, or waypoint belief)
    cand = FREE cells reachable on the map with d_static >= 0.25, d_human >= 0.40, plan_len + 1 <= 500 - steps_used
    s* = argmax_s  sum_i w_i * [ |s - g_i|_3D < 3.0 - 0.10 ]  - 0.02 * sum_i w_i |s - g_i|  - 0.002 * plan_len(s)
    (prefer, at equal coverage, s with geodesic-on-map(s, g_i) < 3 as well: robust if the scorer were geodesic)
    execute plan to s*, then STOP
```
3-D Euclidean distance (A2 fact 24, C1 flag 4) means the stop must be on the goal's floor; across a thin wall within 3 m counts.

### 4.9 Parameters (initial; tune with [P] diagnostics, §5.5)
`res 0.05 m · R_STATIC 0.25 (0.22 aligned narrow) · R_UNKNOWN 0.20 · R_HUMAN 0.40 + motion · soft static 0.40 · soft human 0.80 · step tolerance 0.20 m · gap slope 38° · look-down trigger: unknown target disc within 1.25 m · replan every 4 steps · reserve 5 actions · r = 2 frames/step until S measured`.

---

## 5. [P] Privileged executor (teacher labels, oracle diagnostics, upper bounds)

### 5.1 Navmesh set and intersection grid
```text
FRAMESET(scan):
    meshes = [PathFinder.load(scan.navmesh)] + [PathFinder.load(f"{scan}_{f:03d}.navmesh") for f in 0..119]
    # build the 120 files exactly as environments.py:129-144 (single writer, then read-only; C1 flag 5)
    floors = cluster_y(base.build_navmesh_vertices())
    for floor y in floors:
        G_y = AND_f  get_topdown_view(meshes[f], mpp = 0.025, height = y)       # or is_navigable on a 2.5 cm lattice
    C_y = EDT(G_y) * 0.025                                                     # clearance beyond the r=0.1 boundary
    stairs: sample is_navigable along base-mesh shortest-path polylines between floors, AND over meshes
```
Alternative (optional): one swept navmesh with all 120 frames of every human inserted as STATIC objects, `recompute_navmesh(r=0.1)` — useful for `get_straight_shortest_path_points`; slower (≈10 humans × 120 GLBs) and not needed for correctness because verification is exact. Do **not** use a hard r = 0.3–0.4 recompute as the planning mesh: it closes 0.7–0.8 m doors; use the clearance cost on the r = 0.1 intersection instead (equivalent soft inflation, adaptive by construction).

### 5.2 Exact kinematic emulator (float32, Magnum semantics)
```text
STEP(pf, p, q, a):                                    # p: float32[3], q: float32 quaternion (w,x,y,z)
    if a == MOVE_FORWARD:
        e = p + rotate(q, (0,0,-0.25))                # translate_local == translate (TRS)
        f = pf.try_step(p, e)                         # ALLOW_SLIDING
        return f, q, (dot(f-p,f-p) + 1e-5 < dot(e-p,e-p))
    if a in (TURN_LEFT, TURN_RIGHT):
        q = normalize(q * q_axis_angle(+-15deg, Y))   # rotate_y_local then normalized()
        f = pf.try_step(p, p)                         # filter still runs: re-snap if off-mesh
        return f, q, False
    return p, q, False                                # LOOK_*, STOP
```
Validate bit-equivalence against the simulator on ≥1,000 random sequences × 3 scans × frames {0,60,119} (C1 test T2).

### 5.3 Plan → verify → repair
```text
PLAN_P(scan, start_p, start_q, route):                # route = reference path (teacher) or goal (oracle)
    F = FRAMESET(scan); G, C = intersection grid
    snaps = {xz(meshes[f].try_step(start_p, start_p)) for f}       # start re-snap set
    path = Dijkstra(G, cost = 1 + 50*max(0, 0.20 - C)^2/0.15^2, hard C >= 0.05, start -> route end, via route corridor <= 1 m)
    acts = [TURN_LEFT, TURN_RIGHT] if len(snaps) > 1 or start not navigable in any mesh else []   # free re-snap, net 0 rotation
    acts += LATTICE_P(start, wps(path), seg_ok = all 2.5 cm samples have C >= 0.05) + [STOP]
    for attempt in 1..3:
        bad = VERIFY(F, start_p, start_q, acts)
        if not bad: return acts
        acts = local_repair(acts, bad.first_step, c_min += 0.05 around bad.cell)
    block corridor containing bad.cell; replan once; else return min_risk_plan (fewest failing frames) + log

VERIFY(F, p0, q0, acts):
    nominal = None
    for f, pf in enumerate(F.meshes):                 # 121 meshes
        p, q = p0, q0; traj = []
        for i, a in enumerate(acts):
            p, q, c = STEP(pf, p, q, a); traj.append(xz(p))
            if c: return Bad(f, i, 'collided')
        if nominal is None: nominal = traj
        elif max_i |traj[i] - nominal[i]| > 1e-4: return Bad(f, argmax, 'non-invariant')
    for s in snaps (if >1): repeat with p0 := s   # every start re-snap outcome must also be clean
    return None
```
Frame invariance + zero flags per mesh ⇒ zero collisions for any wall-clock frame schedule (principle 3). Cost ≈ 0.3–0.6 s per episode per core; the whole test split is ~0.5 core-hour.

### 5.4 DAgger / IL teacher API
`teacher_action(scan, pose, episode) → action`: if `C(pose) < 0.05` (student wandered close to an obstacle) return the turn/forward that maximises C after ≤ 2 steps (escape first); else the first action of `LATTICE_P(pose → next reference waypoint)` using a cached Dijkstra field per (episode, floor) as heuristic (~1–5 ms per query). Labels at the waypoint level for a waypoint policy: the next intersection-grid waypoint 1–3 m ahead along the reference path. Unlike `ShortestPathFollowerCompat` (F7) it never issues a forward that would slide.

### 5.5 Oracle diagnostics for compliant rollouts (val/train only)
For each [C] rollout replay its sequence through `VERIFY` and log per forward: true clearance `C(p)` on each mesh, estimated clearances `d_static/d_unknown/d_human`, flags per mesh. Classify each flagged step: **wall** (flagged on base), **human-frame** (flagged only on some frame meshes), **invisible-edge** (flagged on base while the map said FREE with d_static ≥ 0.25), **start-snap**, **post-contact cascade**. Fit margins so that the false-safe rate per executed forward is < 3e-4 (⇒ ≥ 99 % collision-free episodes at ~37 forwards). Also measure, per train scan, the empirical distribution of navmesh-boundary distance to rendered geometry (to set R_STATIC = p99.99 + 0.02).

---

## 6. What to reuse from vln-safe (and what not)

Reuse: (1) the exact engine test in `navmesh_oracle` for [P] (`guard.py:348-363`, identical to F1); (2) the stall rule (a forward from a stalled pose fails with certainty) — generalised to "never re-attempt a forward whose target is within 5 cm of a contact target"; (3) the veto-then-escape structure with a short lookahead ray (we replace the escape with a lattice re-plan, keep the 2-step ray as a fast fallback); (4) the clearance definition `min dist(points) − agent radius` on an ego cloud (`geometry.py:occupancy_min_clearance`), but with our larger margins; (5) their analysis tooling ideas: precision/recall of vetoes vs engine contacts, first-contact position, proxy-miss audit.
Do not reuse: (a) the "yield" caps (residual collisions in every arm; even the oracle guard keeps 6–8 % contact episodes); (b) depth memory without height filtering (ceiling phantoms); (c) the 0.05 m threshold (tuned for a policy-driven agent in a 12-camera ring, too small for a single forward camera and Recast's ±0.065 m simplification); (d) the displacement proxy (<1e-4 m) for contact detection.

---

## 7. Failure-mode table

| # | Failure mode | Regime | Cause | Detection | Mitigation |
|---|---|---|---|---|---|
| 1 | Corner cut / wall slide | C,P | heading error ≤15° accepted (VLN-CE follower), shortest paths touch the eroded boundary | engine flag; pose delta < 0.24998 | clearance-cost planning, segment samples, align before forward runs |
| 2 | Low obstacle in the near blind zone | C | level camera sees nothing below 1.25−d m within 1.25 m | map UNKNOWN near target | persistent map, unknown-as-obstacle within 0.20 m, LOOK_DOWN before stepping into unobserved cells, pitched panorama at start |
| 3 | Invisible navmesh edge (mesh hole, mirror/glass phantom floor, pruned < 1 m² region, steep slope, ledge) | C | navmesh boundary without rendered obstacle | contact on a step the map called safe | require observed floor; elevation barriers; learned navigability net trained on train scans vs true navmesh; contact memory; floor-continuity check near depth discontinuities |
| 4 | Recast raster/simplification offset | C | boundary 0.035–0.215 m from geometry | [P] diagnostics | R_STATIC 0.25; calibrate per §5.5 |
| 5 | Human frame mismatch local vs replay | C | wall-clock animation; scorer speed unknown | [P] VERIFY on all frames | step-indexed local clock calibrated to S; trail union; motion margin; social soft cost |
| 6 | Hidden human body extent / limbs | C | depth sees front surface only | — | +0.15 m body depth in R_HUMAN; mask dilation |
| 7 | Missed human detection | C | segmenter false negative | dynamic-point change detection | treat new points in previously free cells as dynamic; static margin 0.25 still applies |
| 8 | Start inside a human footprint | C,P | start set without navigability check | try_step(start,start) ≠ start [P]; human points < 0.6 m [C] | first action TURN; [P] verify all snap outcomes; [C] +0.35 m early spread margin |
| 9 | New-scene episode runs on base navmesh | P | scene load > 12 s | — | included as the 121st mesh |
| 10 | Narrow door/passage cannot meet margins | C,P | 0.7 m doors, 15°/0.25 m quantisation | planner returns None at 0.25 | aligned crossing with 0.22 m, lateral 6.5 cm adjustments; [P] grid clearance cost; else alternative route |
| 11 | Stairs misread as walls / descending into unseen | C | 2-D occupancy; level camera | barrier on stair cells | 2.5-D elevation map (0.20 m step, 38° gap slope), LOOK_DOWN before descending, per-floor layers |
| 12 | Slide cascade after one contact | C | agent sits exactly on the boundary | consecutive contacts | escape heading dir·n ≥ 0.5, contact memory, local +0.10 m inflation |
| 13 | Livelock / oscillating replans | C | plan flip-flop between homotopies | repeated poses | hysteresis (commit 4 steps), visited-pose penalty, budget reserve; never yield |
| 14 | Budget exhaustion without STOP | C,P | exploration/loops | steps_used | reserve = plan_len(stop)+6; forced STOP at action 500 |
| 15 | Wrong camera-tilt bookkeeping | C | DISTANCE_TO_HUMAN measure resets tilt via set_state (A2 fact 25); missed LOOK | floor-plane fit residual | exclude that measure locally; level camera before each map update; sanity check floor plane |
| 16 | Emulator ≠ simulator | P | float32 rotation accumulation, quaternion order | T2 equivalence test | Magnum-exact ops; ≥1e-4 invariance tolerance; margins ≥ 0.05 m |
| 17 | Navmesh cache race | P,C-local | non-atomic writes in _handle_signals | T5 cache integrity | pre-warm single writer, read-only mount (C1 flag 5) |
| 18 | Stop target inside obstacle / other floor | C,P | goal on furniture, multi-floor | 3-D distance check | stop placement on reachable cells maximising coverage within 2.9 m 3-D |
| 19 | Human trail blocks the only corridor | C | moving human in hallway | planner None with human constraints | choose crossing whose trail frames are least likely at the crossing step; accept & log; never wait |
| 20 | Simulator lookahead used at inference | C | "step + set_agent_state restore" probing | code audit | forbidden in [C] (C3 T3/T4); the brief's simulate-and-repair loop is [P]-only |

---

## 8. Tests

### Unit (no simulator)
- **U1 kinematics:** emulator turn/forward vs golden habitat poses (start yaw arbitrary, 1,000 random sequences): position error < 1e-5 m, yaw error < 1e-5 rad.
- **U2 predicate:** displacements 0.24997 → collided, 0.249985 → not; up-stairs move (xz 0.25, dy 0.1) → not collided.
- **U3 projection:** synthetic box scenes (reuse competitor `tests/fixtures/box_scene.py` idea): wall, table (0.75 m top), 0.18 m stair risers, 0.5 m ledge, ceiling 2.5 m → table/ledge/wall OCCUPIED, stairs FREE, ceiling ignored; pitch 0/−15/−30 consistent.
- **U4 SAFE_FWD:** obstacle at 0.24 m from a sample → reject; 0.26 → accept; unknown cell at 0.19 m → reject; contact target within 5 cm → reject.
- **U5 lattice:** corridor at 7.5° off-lattice, 0.75 m door, L-turn: all forwards satisfy hard clearances, ≤ 1 turn per 3 forwards on the straight, headings ∈ yaw0+15°·k.
- **U6 post-check:** pose delta 0.2499 → CONTACT with correct normal; next forward with dir·n < 0.5 vetoed.
- **U7 contract:** every emitted sequence has 1–500 actions, exactly one STOP and it is last; forced STOP at index 499.
- **U8 stop placement:** synthetic goal mixtures (two modes 4 m apart, different floors) → argmax coverage; respects budget.

### Integration ([P] tools on train/val scans; real HAVLNCEDaggerEnv)
- **I1 no-short-step:** for every final sequence and every mesh f ∈ {base, 000..119}: no MOVE_FORWARD changes position by < 0.24998 m (3-D).
- **I2 zero collisions under regimes:** `collisions.count == 0` in the official env with FrameScheduler regimes frozen(k) k ∈ {0,30,60,119}, schedule(S) S ∈ {5,10,20,50,200}, base mesh, and two wall-clock runs (C1 R0/R2/R3).
- **I3 invariance:** final position within 1e-3 m of the planned stop under all regimes (and within 0.5 m for [C] sequences — any larger divergence is a bug or a human-timing contact).
- **I4 teacher quality:** privileged executor on val_unseen with GT goals: 100 % zero-collision, SR ≥ 99 % (3 m), median actions ≤ 90.
- **I5 compliant executor isolation:** [C] executor with oracle subgoals (GT reference waypoints fed one by one, no navmesh) on val_unseen: collision-free episodes ≥ 98 % under I2 regimes, SR ≥ 95 %; report failure classes (§5.5).
- **I6 map calibration:** per train scan, false-FREE rate of the static layer vs intersection navmesh inside the 0.25 m band < 1e-4 per cell; boundary-offset distribution p99.99 < 0.23 m.
- **I7 official parity:** a 200-episode sample through `havln-score-phase1` in the image ×3 equals local R0 within run-to-run spread.
- **I8 determinism:** same seed/config ⇒ byte-identical action sequences (open-weight models, greedy decoding).
- **I9 start-in-human set:** the 75 val_unseen episodes starting < 0.3 m from a human: action 1 is a TURN; I1–I3 pass.

### Acceptance gate before any submission
I1 + I2 on a 500-episode val_unseen stratified sample (≥ 1/3 multi-floor or human-near); no collision class > 0.5 % of episodes; contract U7 on the full file.

---

## 9. Implications

- Zero collisions is an engineering property of the executor, not of the VLN policy; decouple them: the policy outputs subgoals/stop requests, the executor owns primitives. Learned low-level collision avoidance is unnecessary.
- In [C], a depth-only geometric executor with a persistent, height-filtered, exact-pose map should beat the vln-safe reactive guard (66–74 % collision-free) by a wide margin because it plans for clearance instead of vetoing at 5 cm, and never yields; the residual is human timing and invisible navmesh edges.
- The single biggest unknown for [C] is the scorer's step rate S (it decides which human frames the replay shows); knowing S shrinks human margins from the full sweep (p90 0.8 m) to a few centimetres.
- [P] gives exact zero-collision guarantees cheaply (CPU, ~0.5 s/episode) — use it for teacher labels, val diagnostics, and margin calibration; it must not feed test-time action choice in the compliant track.
- Budget is not binding (known route ≈ 75 actions), so look-downs, pitched panoramas and conservative detours are affordable.

## 10. Recommendations

1. **[C] Build the executor as a deterministic module** (map + SAFE_FWD + planner + post-check) shared by training rollouts and inference; the policy outputs waypoints/STOP.
2. **[C] Hard thresholds:** static 0.25 m, unknown 0.20 m, human 0.40 m + motion margin; soft 0.40 / 0.80 m; tune only via [P] diagnostics on train/val_seen.
3. **[C] Never step onto unobserved floor:** LOOK_DOWN (verify TILT 30°) before forwards into unknown near-field; open with a pitched panorama `12×(TURN,TURN,LOOK_DOWN,LOOK_UP)`.
4. **[C] Contact detection by the exact engine predicate on the pose delta** (Δ < 0.24998 m, 3-D), followed by stall memory, boundary-normal escape (dir·n ≥ 0.5), local inflation and re-plan; never yield.
5. **[C] Human timing:** run local rollouts with a step-indexed human clock calibrated to the measured scorer speed (ask organisers to confirm this is acceptable); keep trails of observed humans as obstacles; extrapolate unobserved history with 0.035 m/frame (cap 1.5 m).
6. **[C+P] Convert routes with a 24-heading lattice anchored at the start yaw**, float32 pose accumulation identical to Habitat; centre in doors with single ±15° steps; alternate headings for off-lattice corridors.
7. **[P] Plan on the AND of the 121 cached navmeshes with a clearance cost (hard 0.05 m, preferred 0.20 m beyond the r=0.1 boundary)**, not on a hard r=0.3–0.4 recompute.
8. **[P] Verify every teacher/oracle sequence against all 121 meshes with the exact emulator**, require zero flags and frame-invariant trajectories, plus all start re-snap outcomes.
9. **[P] Replace ShortestPathFollowerCompat as the DAgger teacher** with the clearance-aware lattice teacher (escape-first when the student is within 0.05 m of the boundary).
10. **[P] Run oracle diagnostics on every [C] val run**, classify collisions (wall / invisible edge / human-frame / start-snap / cascade) and fit margins to < 3e-4 false-safe forwards.
11. **[C] Train a depth→BEV navigability net on train scans with true-navmesh labels** (privileged supervision; check with organisers) and AND it with the geometric map to catch invisible edges (mirrors, holes, pruned regions).
12. **[C+P] Always STOP within 500 with a reserve; choose stop points maximising 3-D-Euclidean coverage of the goal belief within 2.9 m on reachable cells.**
13. **[C] Keep simulator lookahead (step + restore) out of the inference path**; it is [P]-only (C3 T3/T4).
14. **Measure S early:** time `havln-score-phase1` in the image and compare genuine Phase-1 submissions with local replays under several r.

## 11. Open questions

- Scorer step rate S (steps/s) on CodaBench and whether it renders RGB-D; this fixes the human-frame window.
- Is configuring the local rollout's human clock (step-indexed instead of raw wall clock) acceptable to the organisers?
- Exact challenge config values: TILT_ANGLE (30° reported), camera POSITION height, depth MIN/MAX/NORMALIZE, whether DISTANCE_TO_HUMAN is in the local env measurements (tilt reset side effect).
- Will the Phase-2 bundle include human_motion entries for the 18 test scans (needed to render humans in local test rollouts at all)?
- Is navmesh-derived supervision (train scans) for a learned navigability predictor acceptable under Q10/Q11?
- Empirical navmesh-boundary-to-geometry offset distribution on MP3D (to tighten R_STATIC); frequency of invisible edges (mirrors, holes, pruned regions) along R2R paths.
- Whether the shipped base `<scan>.navmesh` was built with the same Recast settings as the recomputed frames (differences matter only for the 121st mesh in new-scene episodes).

## 12. Sources

- `$BASE/HA-VLN/HASimulator/environments.py` (49-58, 96-147, 171-213); `HASimulator/config/HAVLNCE_R2R_task.yaml` (1-57); `HASimulator/measures.py` (via A2).
- `$BASE/HA-VLN/agent/VLN-CE/habitat_extensions/shortest_path_follower.py` (1-199), `discrete_planner.py` (1-111), `sensors.py` (GlobalGPSSensor), `actions.py` (GoTowardPoint), `config/default.py` (16-18).
- `$BASE/habitat-sim-0.1.7/habitat_sim/agent/controls/object_controls.py` (60-89), `default_controls.py` (20-91), `simulator.py` (451-464).
- `$BASE/habitat-lab-0.1.7/habitat/config/default.py` (218-261).
- Magnum `src/Magnum/SceneGraph/TranslationRotationScalingTransformation3D.h` @46f4518 (raw.githubusercontent.com/mosra/magnum), lines 117-155.
- `$BASE/sota/vln-safe` (README.md; vlnsafe/guard.py; vlnsafe/geometry.py; vlnsafe/clearance_predictor.py; vlnsafe/agents/tryout.py; vlnsafe/rollout.py; configs/guard/*.yaml; results/*/r2r/*/episodes.csv; results/summary/guard_effect.json, guard_mechanism.json, guard_memory.json).
- `$BASE/competitor-bingchengzhang/project` (README.md 150-180; havln_agent/config.py; executor.py; mapping/static_layer.py; mapping/costmap.py; mapping/human_layer.py).
- `$BASE/jostar-track2` branch `bohan/clarification-Oct14` (README Input row, Q4, Q8, Q9, Q11).
- `$BASE/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`; `$BASE/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/*` (statistics computed with scripts in `scratchpad/c7work/`).
- Findings: `A2-collision-semantics-habitat017.md`, `C1-infra-and-replay-farm.md`, `C3-rules-ethics-and-defensibility.md`.
