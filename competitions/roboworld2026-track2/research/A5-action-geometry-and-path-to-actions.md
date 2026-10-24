# A5 — Action geometry and path → discrete-action conversion (HA-VLN / Habitat 0.1.7)

Topic id: `A5-action-geometry-and-path-to-actions` · Date: 2026-10-24 · Author: research agent A5

Regime tags used below: **[BOTH]** applies to every approach; **[COMPLIANT]** = the primary track per the
organizer clarification (egocentric RGB-D + GPS/compass, closed loop, no privileged scene/human data at inference);
**[PRIVILEGED]** = offline full-map planning (secondary track, needs organizer permission) and all training-time /
local-evaluation uses of simulator ground truth (e.g. generating collision-free DAgger teachers).

---

## Summary (the five things that matter)

1. **Kinematics are fully pinned down [BOTH, high].** MOVE_FORWARD = 0.25 m along the body −Z axis, TURN_LEFT/RIGHT =
   ±15° about +Y (24 per revolution), LOOK_UP/DOWN rotate only the sensors (no position or collision effect; tilt angle is 15° by
   habitat-lab default, 30° in VLN-CE's six-action RxR config; the challenge value is hidden in the image), STOP is never
   flagged. Yaw: `start_rotation = [x,y,z,w]` with x = z = 0; θ = 2·atan2(q_y, q_w); forward = (−sin θ, 0, −cos θ); TURN_LEFT
   adds +15°. **I checked this against the R2R-CE oracle trajectories.** For 98.8 % of the 505,504 oracle forward steps
   (all splits), the recorded displacement is a full 0.25 m in exactly this direction (within 0.26°). The rest are wall slides
   or re-snaps onto the navmesh.
2. **A shortest-path follower given the perfect goal still collides [BOTH, high].** The R2R-CE oracle action sequences come
   from the VLN-CE compat follower with a 0.5 m goal radius, on human-free navmeshes. **18–26 % of those episodes contain at
   least one flagged (shortened) forward step.** Per split: val_seen 25.8 %, val_unseen 18.1 %, train 19.4 %; the mean is
   0.29–0.38 flagged steps per episode and the worst episode has 13. Under the challenge metric, one flagged step
   (above `collision_num`) sets SR_ep = 0. So a converter that is not clearance-aware loses about one success in five,
   even with the correct goal. The habitat-sim 0.1.7 GreedyGeodesicFollower is no fix: it only *penalises* collisions
   (cost 0.25) and still takes colliding steps when they score best. ETPNav's "tryout" control only reacts *after* a collision.
3. **Heading quantisation limits how tightly a path can be tracked [BOTH, high].** The 24 available headings are
   θ0 + k·15°, where θ0 is the arbitrary start yaw, so the angle error to a straight segment is uniform in [0°, 7.5°]
   (mean 3.7°). Simulated on 400 val_unseen reference polylines in free space:
   - **Holding the nearest heading** gives lateral drift per segment of median 0.11 m, p90 0.26 m, max 0.59 m; at
     worst 0.13 m per metre of corridor.
   - **ETPNav-style "rotate, then floor(d/0.25) forwards"** strays up to median 0.24 m / p90 0.37 m from the path.
   - **The compat follower** strays up to median 0.16 m / p90 0.25 m.
   - **An exact lattice A\*** over (x, z, heading) can hold a ±0.05 m corridor on 120/120 sampled paths, at about 63 actions
     instead of about 52 for ±0.20 m. A ±0.03 m corridor is infeasible on 117/120 paths, so about 4–5 cm is the floor this
     action set can achieve.
   - **Action budget is not a constraint.** Oracle sequences average 55–58 actions (p99 98–109, val max 123), so 500 leaves about 8× headroom.
4. **Recommended converter [BOTH]:** run a lattice (x, z, heading) search with exact Habitat step semantics, minimising
   (number of actions) + λ·(clearance penalty). Use hard per-step constraints: the 0.25 m target is unshortened and
   clearance is ≥ m at the step end-point and midpoint. In the PRIVILEGED regime, clearance comes from
   `distance_to_closest_obstacle` on the actual scoring navmesh(es), plus an inflated (r ≈ 0.25–0.30 m) navmesh only to
   choose the route. In the COMPLIANT regime, it comes from a depth-built map using exact GPS/compass pose. Never use a
   reactive collide-then-recover controller. Start with a TURN, which re-snaps the agent onto the navmesh for free.
   Stop within ≤ 0.2 m of the chosen stop point; this costs at most 2–3 extra actions.
5. **Choose the STOP point to cover the most likely goals, not one goal [BOTH, high for the maths, medium for the
   gain].** Success is a strict < 3.0 m in 3-D *Euclidean* distance, and walls do not matter. With Social ≈ 1, one
   success is worth 0.8/N of Nav, while one metre of final distance is worth only 0.6/(3+NE)²/N, about 2–4 % of a success.
   So put the STOP point where a 3 m ball covers the most goal probability. Against R2R nav-graph candidates (3–6 hops
   from the start), a random wrong candidate is within 3 m of the true goal 21 % of the time and within 6 m 49–53 % of the
   time. So when two candidates are 3–6 m apart (about 30 % of random confusion pairs), stopping between them turns a
   coin-flip into a near-certain success. Also, when the only route to the goal requires a collision, stop short: one
   collision episode costs about 0.006 Score points, more than the NE gain from getting about 5 m closer (about 0.003).

---

## 1. Verified action kinematics [BOTH]

| Action (id) | What it does in Habitat-Sim 0.1.7 | Can it be flagged as a collision? | Evidence |
|---|---|---|---|
| STOP (0) | sets `is_stop_called`, calls `get_observations_at()`; ends episode | never (clears `collided`) | habitat-lab `habitat/tasks/nav/nav.py:1022-1029`; A2 fact 6 |
| MOVE_FORWARD (1) | `_move_along(node, -0.25, Z)`: `translate_local(transformation[2].xyz * -0.25)`; scene node is TranslationRotationScaling ⇒ translateLocal == translate ⇒ displacement = 0.25·R·(0,0,−1) = 0.25·(−sin θ, 0, −cos θ); then navmesh `try_step` filter | yes, iff filtered 3-D displacement² + 1e-5 < 0.0625 (shortened by > 2e-5 m) | habitat-sim `habitat_sim/agent/controls/default_controls.py:31-33,76-79`; `src/esp/gfx/magnum.h:22`; `object_controls.py:68-89` (A2); FORWARD_STEP_SIZE 0.25 `HASimulator/config/HAVLNCE_R2R_task.yaml:12`, website `track2.html:81` |
| TURN_LEFT (2) | rotate_y_local(+15°), re-normalise quaternion | never (zero requested displacement), but the filter runs: an off-navmesh agent is silently snapped onto the navmesh | `default_controls.py:36-67,106-123`; TURN_ANGLE 15 `HAVLNCE_R2R_task.yaml:13`; A2 fact 5 |
| TURN_RIGHT (3) | rotate_y_local(−15°) | never (same) | same |
| LOOK_UP (4) / LOOK_DOWN (5) | rotate the sensor nodes about local X by TILT_ANGLE; `body_action=False`, no filter, no constraint | never; no effect on position | `default_controls.py:126-139`; habitat-lab `actions.py:114-133` (v1 space); `TILT_ANGLE=15` default `habitat/config/default.py:218`; VLN-CE RxR six-action config `TURN_ANGLE: 30, TILT_ANGLE: 30, ACTION_SPACE_CONFIG: v1` (`VLN-CE/habitat_extensions/config/rxr_vlnce_english_task.yaml:5-7`) |

Facts:
- **Action ids:** STOP 0, MOVE_FORWARD 1, TURN_LEFT 2, TURN_RIGHT 3, LOOK_UP 4, LOOK_DOWN 5
  (habitat-lab `habitat/sims/habitat_simulator/actions.py:19-24`). [high]
- **24 turns make exactly one revolution.** DiscretePathPlanner asserts that 2π is a multiple of the turn angle
  (`HA-VLN/agent/VLN-CE/habitat_extensions/discrete_planner.py:31`). The quaternion is re-normalised after every turn
  (`default_controls.py:67`), so float drift is negligible (~1e-7 rad per turn). [high]
- **Budget:** MAX_EPISODE_STEPS 500 (`HAVLNCE_R2R_task.yaml:2`). The episode ends once elapsed_steps reaches 500
  (habitat-lab `habitat/core/env.py:187-190,230-232`). Every action counts, including LOOK_* (track2 README:44, FAQ Q3).
  The organizers' clarification branch (JostarXiong/track2 `bohan/clarification-Oct14`, commit 8289590) allows a
  500-action sequence without STOP. **Success still requires `is_stop_called`** (`nav.py:528-535`), so always STOP within
  500 actions. [high]
- **Success threshold:** strictly `distance < 3.0` (`nav.py:535`). DistanceToGoal is the HASimulator override, which uses
  3-D Euclidean distance to `goals[*].position` (`HASimulator/measures.py:17-20,100-155`). It is registered last through
  `habitat_extensions/measures.py:28`; see A2 fact 24 and the CONTEXT update. [high for the code; medium that the hidden scorer is identical]
- **Start pose and yaw:**
  - `start_rotation` is `[x, y, z, w]`. It is applied via `merge_sim_episode_config` (`nav.py:51-66`), then
    `set_agent_state` (`habitat_simulator.py:485-521`, docstring 497-499), then `quat_from_coeffs`
    (habitat-sim `habitat_sim/utils/common.py:18-28`, `agent.py:232-233`).
  - All R2R-CE val quaternions are pure yaw: 0 of 2,617 have non-zero x or z (computed).
  - So θ = 2·atan2(q_y, q_w). Forward = (−sin θ, 0, −cos θ). Right of forward = (cos θ, 0, −sin θ). TURN_LEFT: θ += 15°. [high]
  - HeadingSensor returns φ = θ (`nav.py:356-367`); EpisodicCompass returns θ − θ_start (`nav.py:374-389`). This is what
    "compass" means in the compliant input set. [high, derived from the code]
- **Empirical check of the kinematics.** I replayed the oracle `{split}_gt.json.gz` action sequences: start yaw plus ±15°
  per TURN, and the direction of each forward step compared with the recorded location delta.
  - **Clean steps:** 65,961 / 66,768 (98.8 %) val_unseen forward steps are a full 0.25 m in the predicted direction
    (cos > 0.99999). The same holds for val_seen (30,079/30,442) and train (403,316/408,294).
  - **Flagged slides:** 567 val_unseen steps were shortened.
  - **Full-length but rotated steps:** 240 val_unseen steps moved 0.2500–0.2512 m, rotated 1–14°. These come from
    `tryStep` projecting the start point onto the navmesh. A step that moves the full length is never flagged.
  - Scripts: `scratchpad/a5_scripts/gt_analysis.py`, `gt_collide.py`, `gt_mism.py`. [high]
- **R2R heading h → Habitat yaw (inference, medium).** The MP3D heading is 0 when facing +y_mp3d and increases
  clockwise. Habitat coordinates are (x, z, −y)_mp3d. So θ_habitat = −h, i.e. quaternion = [0, −sin(h/2), 0, cos(h/2)].
  - VLN-CE **v1-2** files do *not* follow this: their yaw is unrelated to the R2R heading (|θ + h| median 94°, histogram
    flat; computed with `heading_check*.py`).
  - VLN-CE **v1-3** "modifies initial headings to match R2R" (A1). HA-R2R ships its own `start_rotation`, so use the
    file value, never a recomputation.
- **Initial alignment cost:** the start yaw differs from the first path segment's bearing by a median 87–96°
  (p10 16°, p90 166–170°). That is about 6 turns on average before the first useful forward step (v1-2 val; computed). [high for v1-2]

## 2. How a forward step can collide [BOTH]

A2 covers the per-step collision maths. The points that matter for designing the converter:
- **Accept rule** (Detour `moveAlongSurface`, recastnavigation-habitat@354591e `DetourNavMeshQuery.cpp:2109-2111,2135-2138`):
  - The search circle is centred at the step midpoint, with radius = step/2 + 1 mm.
  - The target is accepted unchanged if it lies inside a polygon reachable through portals inside that circle.
  - Otherwise, with sliding enabled, it moves to the closest boundary point, the step is shortened, and it is **flagged**.
  - So the exact test is "target point inside locally connected navmesh", not "whole segment inside navmesh". A planner
    should still demand the whole segment (end-point and midpoint) has clearance, because the extra conservatism costs
    nothing. [high]
- **Tolerance is effectively zero.** A shortening of more than 2e-5 m flags the step. Every step of a wall slide is
  flagged, which explains the CMA baseline's TCR of 14–18 (A2). [high]
- **Stairs:** forward motion is horizontal and y is then snapped to the polygon height, so the 3-D displacement is ≥ 0.25 m
  and stairs alone never flag a step.
  - Oracle stair steps (|dy| > 1 cm) have |dy| median 0.04–0.06 m, p90 0.16–0.20 m, max 0.42 m.
  - The flag rate on stair steps is 0.45–0.63 %, against 0.79–1.04 % on flat floor (`stairs.py`). [high]
- **PathFinder API in 0.1.7** (`src/esp/bindings/ShortestPathBindings.cpp:51-117`):
  - `find_path(ShortestPath)` and multi-goal `find_path(MultiGoalShortestPath)`.
  - `try_step` and `try_step_no_sliding`, `snap_point`.
  - `is_navigable(pt, max_y_delta=0.5)`: horizontal tolerance 1 cm (`PathFinder.cpp:1241-1260`).
  - `distance_to_closest_obstacle(pt, max_search_radius=2.0)`: distance to the navmesh **wall edge**, via
    `findDistanceToWall` (`PathFinder.cpp:1214-1239`). Because the navmesh is already eroded by 0.1 m, this is exactly
    the clearance that decides whether a step is flagged.
  - `closest_obstacle_surface_point`, `island_radius`, `get_topdown_view(mpp, height)`, `get_random_navigable_point`,
    `load_nav_mesh`, `save_nav_mesh`.
  - NavMeshSettings fields (defaults: cell 0.05, agent_radius 0.1, height 1.5, max_climb 0.2, slope 45°,
    edge_max_error 1.3) — `PathFinder.h:103-154`. [high]
- **find_path limits:** at most 256 polygons, and the status must be exactly DT_SUCCESS. A partial path returns no path,
  i.e. infinite geodesic distance (`PathFinder.cpp:996-1003`). Long paths on finely cut human-aware or inflated
  navmeshes can fail; fall back to waypoint chaining or the lattice search. [high for the code; medium for the practical impact]
- **Recomputing a navmesh needs a renderer:** `recompute_navmesh(pathfinder, settings, include_static_objects)` asserts
  `create_renderer=True` (`src/esp/sim/Simulator.cpp:643-652`; binding `SimBindings.cpp:284-287`), so it needs a GPU/EGL
  context. Every PathFinder query above is CPU-only, so exact kinematic verification can run headless at scale. [high]

## 3. Existing followers and controllers, and why they are not enough [BOTH]

| Follower | Decision rule | Goal / stop | Collision handling | Source |
|---|---|---|---|---|
| VLN-CE `ShortestPathFollowerCompat` (v0.1.4 logic; R2R-CE dataset-generation oracle) | target = points[1] of the straight shortest path. MOVE_FORWARD if angle(heading, target) ≤ 15° + 1e-6; otherwise one turn in the direction that shrinks the angle (found by a trial turn) | geodesic ≤ goal_radius (VLN-CE default 0.5) | none; no anti-thrash | `HA-VLN/agent/VLN-CE/habitat_extensions/shortest_path_follower.py:65-104` (threshold line 87), `115-176`; `sensors.py:125-153`; `config/default.py:35-41` |
| habitat-lab 0.1.7 `ShortestPathFollower` → habitat-sim `GreedyGeodesicFollower` (the default ShortestPathSensor, USE_ORIGINAL_FOLLOWER False) | primitives [L]^n F or [R]^n F, reward = Δgeodesic/0.25 − 0.0125·n − 0.25·collided − 0.05·[clearance < 0.2 m]. Takes the first primitive with reward > 0.99, i.e. heading error ≲ 8.1° | geodesic < goal_radius (default 0.75 × step) | collisions are only penalised; colliding moves are taken if best. Anti-thrash after 16 L/R alternations | habitat-lab `habitat/tasks/nav/shortest_path_follower.py:53-85`; habitat-sim `habitat_sim/nav/greedy_geodesic_follower.py:41-123`; `src/esp/nav/GreedyFollower.cpp:59-137,139-155`; `.h:129-130` |
| `DiscretePathPlanner` (VLN-CE waypoint env) | greedy Euclidean steps in obstacle-free space toward a polar waypoint | 0.13 m | none (assumes free space) | `discrete_planner.py:8-83`; `vlnce_baselines/common/environments.py:165-232` |
| ETPNav `single_step_control` | rotate by the angle rounded to 15°, then floor(d/0.25) forwards | under-shoots by up to 0.25 m per hop | "tryout" only after `previous_step_collided` (reactive) | `ETPNav/vlnce_baselines/common/environments.py:340-421` |

Measured on the R2R-CE v1-2 oracle `*_gt.json.gz` (compat follower, goal radius 0.5, human-free navmesh); script `gt_analysis.py`:

| Split | Actions mean / median / p90 / p99 / max | Forwards mean | Turns mean | Turns per geodesic m | Actions per geodesic m | Geodesic distance mean (min–max) | Final distance mean (max) | Episodes with ≥ 1 flagged step | Flagged steps per episode, mean (max) |
|---|---|---|---|---|---|---|---|---|---|
| val_seen (778) | 57.8 / 56 / 83 / 106 / 119 | 39.1 | 17.6 | 1.94 | 6.13 | 9.58 (4.4–17.9) | 0.37 (0.499) | **25.8 %** | 0.38 (5) |
| val_unseen (1,839) | 54.6 / 53 / 74 / 98 / 123 | 36.3 | 17.3 | 2.10 | 6.30 | 8.90 (3.8–21.0) | 0.37 (0.500) | **18.1 %** | 0.29 (6) |
| train (10,819) | 56.0 / 53 / 79 / 109 / 500* | 37.7 | 17.2 | 1.99 | 6.17 | 9.27 (3.2–25.2) | 0.38 (1.98) | **19.4 %** | 0.29 (13) |

\*One train episode reaches 500 actions with 409 turns: the compat follower thrashing L/R in place. A converter needs
an explicit anti-thrash rule.

Inferences:
- About 20 % of episodes would fail SR purely from wall clipping, even with the perfect goal. This is about 4× the
  social penalty per episode (§6).
- The cause: the straight shortest path on a radius-0.1 navmesh touches the navmesh boundary at every inner corner (zero
  clearance). Any heading error of up to 15° near a corner therefore clips it.
- HA-VLN's DAgger teacher is the same family of followers, run on human-aware navmeshes, so the released CMA was trained
  to imitate a colliding oracle. **A clearance-aware teacher is a cheap, legitimate training-time upgrade [COMPLIANT].** [medium-high]
- Caveat: these are v1-2 data generated with an older Habitat. HA-R2R uses v1-3 episodes; the start/goal geometry is the
  same, but the flag rates under the 0.1.7 runtime may differ slightly. [medium]

## 4. Heading quantisation and lateral drift: free-space study [BOTH]

Setup: 400 random val_unseen episodes (fixed seed), using the reference polyline in xz and the true start yaw. For each
controller, I measured the actions used and the maximum deviation of every visited point and step midpoint from the
polyline. Script: `scratchpad/a5_scripts/converters.py`; output: `converters_out.json`. As a calibration check, my
free-space compat emulation needs 53.0 actions, against 54.6 for the real oracle.

| Controller | Actions mean (p90) | Forwards / turns | Max deviation from path: median / p90 / max | Final error |
|---|---|---|---|---|
| ETPNav-style: rotate, then floor(d/0.25) forwards per vertex | 53.6 (71) | 38.2 / 14.4 | 0.237 / 0.374 / 0.579 m | 0.19 m |
| Same with round(d/0.25) | 55.2 (72) | 39.3 / 14.9 | 0.237 / 0.377 / 0.579 m | 0.15 m |
| Compat follower (±15° tolerance), goal radius 0.5 m | 53.0 (71) | 36.9 / 15.0 | 0.159 / 0.248 / 0.333 m | 0.38 m |
| **Lattice A\*, corridor ±0.05 m, goal tol 0.2 m** (120 episodes) | **63.3** | 38.6 / 23.7 | **≤ 0.05 m by construction** (120/120 feasible) | ≤ 0.2 m |
| Lattice A\*, ±0.10 m | 55.0 | 38.1 / 15.9 | ≤ 0.10 m (120/120) | ≤ 0.2 m |
| Lattice A\*, ±0.20 m | 51.6 | 37.2 / 13.5 | ≤ 0.20 m (120/120) | ≤ 0.2 m |
| Lattice A\*, ±0.03 m | — | — | infeasible or over budget on 117/120 | — |

Segment geometry over 1,960 segments:
- Segment length: median 1.84 m, p90 3.18 m, max 6.72 m.
- Heading quantisation error: mean 3.68°, roughly uniform on 0–7.5°.
- Lateral drift if the nearest heading is held for a whole segment: median 0.11 m, p90 0.26 m, max 0.59 m.
- Worst case: sin 7.5° = 0.13 m per metre, i.e. 1.3 m over a 10 m corridor.
- MP3D buildings are mostly axis-aligned and θ0 is arbitrary, so every parallel corridor in an episode tends to share the
  same offset. The drift is systematic, not random. [high for the numbers; medium for the Manhattan remark]

Inferences:
- (a) Tracking a path to within ±5 cm costs about 1 extra turn per metre: 63 against 52 actions, still ≪ 500.
  Spend those turns wherever clearance is below about 0.25 m.
- (b) About 4–5 cm is the tightest corridor this action set can hold at an arbitrary bearing.
  Doorways need centre-line clearance of at least about 0.05 m plus a safety margin; plan for ≥ 0.10 m.
- (c) "Rotate-then-go" per waypoint (ETPNav, CWP-style controllers) needs about 0.4 m of lateral clearance at p90.
  This alone explains much of the wall contact of waypoint-based VLN-CE agents.

## 5. Proposed path → actions converter

### 5.1 Core: a clearance-aware lattice search with exact step semantics [BOTH]

The search state is (position p ∈ R³, heading index k ∈ Z₂₄, step count). Successors:
- **L / R:** k ± 1. Position unchanged (in the PRIVILEGED regime, apply `try_step(p, p)` to mirror the turn re-snap).
- **F:** target t = p + 0.25·(−sin θk, 0, −cos θk).

Hard constraints on every F step:
1. **Not shortened.** PRIVILEGED: `try_step(p, t)` returns t (|Δ| ≥ 0.24998 m) on every candidate navmesh — the base
   navmesh plus 120 human frames, or the swept-human navmesh (A2 Rule 2/4). COMPLIANT: t and the step midpoint are free in
   the depth-built map, in cells that have actually been observed.
2. **Clearance.** clearance(t) ≥ m_hard and clearance(midpoint) ≥ m_hard, with m_hard = 0.05 m on the scoring navmesh
   (PRIVILEGED) or ≥ 0.15 m from depth-observed obstacles (COMPLIANT, absorbing the Recast 5 cm raster + 6.5 cm contour
   error); keep ≥ 1.0 m from observed humans (COMPLIANT) or the union of all frames (PRIVILEGED).

Cost and search:
- **Cost** = 1 per action + λ·Σ max(0, c_pref − clearance)² with c_pref ≈ 0.25–0.35 m. This centres the agent in
  corridors and doorways without forbidding them.
- **Heuristic:** remaining geodesic length on the planning mesh divided by 0.25, plus a turn lower bound.
  Precompute a geodesic distance field, or use the remaining length along the route polyline.
- **De-duplication:** round positions to 1–2 cm per heading. In my free-space prototype this needed a median of
  2.4k–41k expansions per episode. In C++, or through PathFinder via pybind, this takes milliseconds to seconds.
- **Route / homotopy:** the global route comes from `find_path` on an inflated navmesh
  (`recompute_navmesh(agent_radius = 0.25–0.30)`, with all human frames as STATIC objects in the PRIVILEGED regime), or
  from the agent's topological graph or waypoint predictor in the COMPLIANT regime. The lattice runs between gates every
  ~2 m along the route, so each search stays small. Fall back to r = 0.20, then 0.15, if the inflated mesh disconnects
  start and stop; narrow MP3D doors and stairs do this.
- **Anti-thrash:** never emit L then R in a row (the cost already forbids it). Cap the turns per decision.

### 5.2 Start and end [BOTH]
- **First action:** a TURN, toward the first route bearing. It costs nothing and re-snaps an agent that starts slightly
  off-mesh or inside a human footprint (A2: 4–6.5 % of val_unseen starts are within 0.3–0.5 m of a human).
  Never open with MOVE_FORWARD from a start with clearance below m_hard.
- **Stop:** when |p − stop_point| ≤ 0.2 m (lattice goal tolerance). Going from 1 m to 0.2 m costs at most about 3 more
  actions and lowers the expected NE. Do not finish with turns to "face" anything; heading is not scored.
- **Budget guard:** if the plan exceeds 499 non-STOP actions (never seen in R2R; max 123 in val), cut it at the last
  state within 3 m of the stop point and STOP. Expect about 55–65 actions on typical paths, plus about 6 to align with the
  start yaw (already included).

### 5.3 Verification and repair [PRIVILEGED; also for training data and val evaluation]
- **Exact replay:** run headless habitat-sim 0.1.7 in the challenge image (`create_renderer=False` is enough for a loaded
  navmesh). Use `agent.act` per action against each candidate navmesh (base + `<scan>_<fff>.navmesh` for fff = 0..119),
  so float32 Magnum arithmetic and `try_step` are bit-exact. Then do one real `HAVLNCEDaggerEnv` replay.
- **Repair:** on the first flagged step i, re-plan from state i−1 with m_hard + 5 cm locally. If that fails, switch to
  another homotopy (pass on the other side of the human). If it still fails, move the stop point to the best safe point
  that still covers the most goal probability (§6). Planning is offline, so "backtracking" means editing the sequence
  before submission, not executing reverse moves.
- **Cost:** about 3,408 episodes × 60 steps × 121 navmeshes ≈ 25 M `try_step` calls. That is minutes of CPU.

### 5.4 Compliant-regime specifics [COMPLIANT]
- **Map:** use depth with the exact pose (GPS + compass are explicitly allowed, clarification FAQ Q9).
  - Rasterise points at heights 0.2–1.6 m above the floor as obstacles, mirroring Recast's walkableClimb 0.2 m and
    walkableHeight 1.6 m (A2 fact 13).
  - Erode by 0.1 m for the agent radius and add ≥ 0.15 m margin.
  - Treat never-observed cells as blocked for F steps.
- **Near-field blind zone** (camera 1.25 m high, `habitat/config/default.py:227`; HFOV 90° so ±45° vertically for the
  square depth; inference):
  - The floor is visible only beyond about 1.25 m ahead.
  - LOOK_DOWN by 15° makes the floor visible from about 0.72 m; by 30°, from about 0.33 m.
  - After turning onto a new heading, the first ~1.2 m may never have been observed. Spend LOOK_DOWN/LOOK_UP (2 actions,
    zero collision risk) or approach from an already-observed direction.
- **Collision detection:** a forward step that moved < 0.24998 m (read from GPS) was flagged. Use this only to mark the
  map and re-plan; the penalty is already incurred.
- **Human timing:** humans animate on wall-clock time for ~12 s, and the official replay timing differs from the local
  closed-loop run (A2 facts 16–18; clarification Q4). Humans seen in the local run may stand elsewhere during replay.
  Keep about 1 m clearance from every person observed; motion extents are p90 0.8 m and max 3.5 m. Elongate the keep-out
  zone along any motion seen between frames.
- **Budget for active perception:**
  - A full 360° scan costs 24 turns. Four 90° views cost 18 turns.
  - Scanning at the start and every ~3 m adds about 100–150 actions to the ~60 for the path, still < 500.
- **Gray areas (ask the organizers):** re-running a test episode several times and keeping the best sequence, and
  repairing a test sequence with privileged replay. Both use information beyond a single compliant run. Do not rely on them.

## 6. STOP-point selection under goal uncertainty [BOTH]

**Score marginals** (derived from the README formula; with zero collisions, Social = 1):
- One success: ∂Score/∂SR_i = 100·0.8·(0.7 + 0.3·S)/N, about 0.0235 points at N = 3,408.
- One metre of final distance: ∂Score/∂d_i = −100·0.2·3/(3+NE)²·(0.7 + 0.3·S)/N, about 0.0006 points at NE = 2.5.
- So 1 m ≈ 2.5 % of a success (3.7 % at NE = 1.5, 2.1 % at NE = 3).
- A collision in a successful-looking episode costs the success (0.0235) plus Social (about 0.006). In an episode that
  fails anyway, it costs only about 0.006. [high for the maths]

**Decision rule:** pick x, navigable and reachable without collision, that maximises Σ_j p_j·1[‖x − g_j‖₃D < 3 m] − ε·Σ_j p_j·‖x − g_j‖ with ε ≈ 0.025.
- This is a maximum-coverage ball of radius 3 m, Euclidean in 3-D, so walls and doors do not matter. Use the 3 m margin
  minus about 0.3 m for safety.
- With two candidates a distance D apart:
  - D < 3 m: either point works.
  - 3 m ≤ D < ~5.5 m: stop near the midpoint (covers both).
  - D ≥ 6 m: commit to the more likely candidate.
- If no candidate is likely (low confidence), minimise expected distance instead (geometric median), since NE still counts.

**Geometry of R2R goals** (`goal_geom.py`; MP3D connectivity graphs, candidates = included nodes 3–6 hops from the start):

| | val_seen | val_unseen |
|---|---|---|
| Candidates per episode, mean (median) | 34.7 (31) | 31.8 (29) |
| Share of wrong candidates within 3 m of the goal | 21.1 % | 20.8 % |
| Share of wrong candidates within 6 m (midpoint-coverable) | 48.9 % | 52.6 % |
| Median distance from the goal to the nearest other candidate | 1.22 m | 1.40 m |
| Other candidates within 3 m of the goal, mean | 5.3 | 5.2 |

Inference [medium]: say the true goal is the model's #2 candidate in a fraction q₂ of episodes and the top-2 pairs follow
these statistics. Midpoint hedging then adds about q₂ × 0.28–0.32 to SR; with q₂ ≈ 0.15, that is about +4–5 SR points.
Each SR point is worth about 0.8 Score points. A1 independently finds about 8 three-metre clusters per test start, which
supports scoring STOP candidates cluster-by-cluster.

**Blocked goals.** If every route to the best stop region needs a flagged step, success is impossible, because TCR > 0
forces SR_ep = 0. The exception is when `collision_num[ep]` gives slack: 237 of 3,408 test episodes allow 1–3 free
flagged steps (A2 fact 22). Otherwise stop at the best safe point. A collision costs about 0.006 points; getting 5 m
closer gains only about 0.003.

## 7. Multi-floor, stairs and islands [BOTH]

- **How common multi-floor episodes are** (`gt_analysis.py`). "Multi-floor" means the goal–start |Δy| > 0.5 m, or the
  reference-path y-range > 0.5 m.

  | Split | Multi-floor episodes | Goal |Δy| > 1 m | Max |Δy| |
  |---|---|---|---|
  | val_seen | 102 / 778 (13 %) | 45 | 3.4 m |
  | val_unseen | 432 / 1,839 (23.5 %) | 261 | 4.27 m |
  | train | 1,760 / 10,819 (16 %) | 925 | 5.5 m |

  - 37–48 % of episodes contain at least one step with |dy| > 5 cm (ramps, thresholds, stairs). [high]
- **Implications:**
  - Plan and verify in 3-D on navmesh positions, using `try_step` output y and geodesic distance. Do not use a single 2-D
    top-down grid: floors overlap in xz.
  - `get_topdown_view(mpp, height)` gives one floor slice only.
  - Success distance is 3-D Euclidean, so a stop point on the wrong floor directly above or below the goal is about 3 m
    off vertically. Do not count on it; MP3D floor heights are typically ≥ 3 m (inference).
- **Islands:**
  - R2R-CE episodes were kept only when start and goal were connected on the base navmesh. 100 % of val oracle runs ended
    within 0.5 m of the goal; 3 train runs ended between 0.5 and 2.0 m. [high]
  - Disconnection can come from (a) an inflated planning navmesh: narrow doors and stairs, so use the radius fallback
    ladder 0.30 → 0.25 → 0.20 → 0.15 m; (b) human-aware frames: people in doorways, so plan on the union of frames and
    re-route; (c) a predicted goal point on another island: snap the stop point to the start's island with the
    max-coverage rule (§6).
  - `find_path` returns infinity across islands or for a path longer than 256 polygons (§2).

## 8. Contradictions and flags relative to CONTEXT and the topic brief

- **Brief: "LOOK_UP/DOWN = 30° pitch".** Not verified. The habitat-lab 0.1.7 default is 15° (`default.py:218`). VLN-CE's
  six-action RxR config uses 30° — and also TURN_ANGLE 30°. The challenge's `six_action_task.yaml` lives in the image and
  cannot be read here (the ghcr blob download was blocked by the proxy, 403). Look actions have no effect on position, so
  only compliant-regime perception depends on this. The website (`roboworld2026.github.io/track2.html:81`,
  `index.html:1562`) does confirm 0.25 m steps and 15° turns. **Verify in the image:** step one LOOK_DOWN and read the
  sensor rotation.
- **Brief: "ensure STOP within ≤ 1 m".** Fine, but ≤ 0.2 m is nearly free and lowers NE. Also, the STOP point should be
  chosen by probability coverage, not as "the goal".
- **Brief: "plan on an inflated navmesh (agent radius 0.3)".** Refined:
  - Use the inflated mesh only for the route.
  - Enforce safety per step on the real scoring navmesh(es): `try_step` plus `distance_to_closest_obstacle` ≥ about 0.05 m.
    This is exact, and it avoids cutting off narrow doors that a 0.3 m inflation would close (0.6 m of free width is lost).
  - For COMPLIANT depth maps, the larger ≥ 0.15 m margin is needed, because the map only approximates the Recast mesh.
- **CONTEXT fact 1 ("STOP once at end").** Consistent; the clarification branch adds that a 500-action sequence may omit
  STOP, but it cannot then succeed.
- **New observation (low-medium):** an older toolkit README (havln-challenge commit 395a016) reported CMA val_unseen
  SR 0.114 / TCR 22.35, against 0.129 / 17.54 now. Organizer replays of the same baseline differ noticeably, consistent
  with timing-dependent human frames or a pipeline change. Treat local metrics as estimates.

## 9. Open questions
- What is the challenge TILT_ANGLE (15° or 30°)? Does the hidden config enable the DISTANCE_TO_HUMAN measure, which
  resets the sensor tilt every step (A2 fact 25)?
- Does HA-R2R `start_rotation` equal VLN-CE v1-3, with θ = −h_R2R? Check against the HA-R2R val files.
- Are the scorer's base MP3D navmeshes identical to those used when the v1-2 oracle was generated? This affects how
  directly the 18–26 % flag rate transfers. Re-measure by running the 0.1.7 GreedyGeodesicFollower and the compat follower
  on HA-R2R val in the image.
- Is a GPU-free path to the per-frame navmeshes acceptable? They are cached under `recompute_navmesh/`, and generating
  them needs `create_renderer=True`.
- Will the organizers allow offline multi-run selection or privileged repair for test sequences? Assume no.

## 10. Reproducibility (scripts written for this topic; read-only on downloaded data, run with `python3 -I`)
All under `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a5_scripts/`:
- `gt_analysis.py`: oracle action, geodesic, stairs and final-distance statistics.
- `gt_collide.py`: exact flag test on oracle trajectories.
- `gt_mism.py`: full-length rotated steps.
- `heading_check.py`, `heading_check2.py`, `heading_check3.py`: yaw conventions.
- `stairs.py`: stair-step statistics.
- `converters.py` (output `converters_out.json`): free-space controller and lattice study.
- `goal_geom.py`: STOP-hedging geometry.

Data: `ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{split}/{split}{,_gt}.json.gz`,
`ext/HA-VLN/HASimulator/HA-DE/connectivity/*.json`, `ext/HA-VLN/HASimulator/HA-DE/tasks/R2R/data/R2R_val_unseen.json`.

## Sources
- habitat-sim v0.1.7 (856d4b0), local `ext/habitat-sim-0.1.7`:
  - `habitat_sim/agent/controls/default_controls.py`, `habitat_sim/agent/agent.py`, `habitat_sim/utils/common.py`,
    `habitat_sim/simulator.py`, `habitat_sim/nav/greedy_geodesic_follower.py`
  - `src/esp/nav/GreedyFollower.{h,cpp}`, `src/esp/nav/PathFinder.{h,cpp}`, `src/esp/bindings/ShortestPathBindings.cpp`,
    `src/esp/bindings/SimBindings.cpp`, `src/esp/sim/Simulator.cpp`, `src/esp/gfx/magnum.h`
- habitat-lab v0.1.7 (d6ed1c0), local `ext/habitat-lab-0.1.7`: `habitat/config/default.py`,
  `habitat/sims/habitat_simulator/{actions.py,habitat_simulator.py}`,
  `habitat/tasks/nav/{nav.py,shortest_path_follower.py}`, `habitat/core/env.py`, `habitat/tasks/utils.py`
- recastnavigation (habitat fork) 354591e: `Detour/Source/DetourNavMeshQuery.cpp` (moveAlongSurface)
- UWMILab/HA-VLN (local `ext/HA-VLN`):
  - `agent/VLN-CE/habitat_extensions/{discrete_planner.py,shortest_path_follower.py,utils.py,actions.py,sensors.py,measures.py,__init__.py,config/default.py,config/vlnce_task.yaml,config/rxr_vlnce_english_task.yaml}`
  - `agent/VLN-CE/vlnce_baselines/common/environments.py`
  - `HASimulator/{measures.py,metric.py,config/HAVLNCE_R2R_task.yaml}`, `HASimulator/HA-DE/connectivity/`,
    `HASimulator/HA-DE/tasks/R2R/data/`
- jacobkrantz/VLN-CE (local `ext/VLN-CE`): `habitat_extensions/config/rxr_vlnce_english_task.yaml`
- MarSaKi/ETPNav (local `ext/ETPNav`, 160e65f): `vlnce_baselines/common/environments.py`
- Sim2Sim-VLNCE (local `ext/Sim2Sim-VLNCE`): `sim2sim_vlnce/Sim2Sim/environments.py` (subgoal follower, 0.2 m radius, rotation plan)
- Official toolkit `ext/track2/README.md`, `scripts/export_cma_submission.py`; clarification branch
  `ext/jostar-track2` origin/bohan/clarification-Oct14 (0f944d3, 8289590); older README `ext/havln-challenge`@395a016
- Website `ext/roboworld2026.github.io/track2.html:81`, `index.html:1562`
- R2R-CE v1-2 data (`ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed`)
- Sibling findings: A1 (episode format, goal-candidate clusters), A2 (collision semantics, navmesh swap, human timing)
- Magnum SceneGraph TranslationRotationScalingTransformation3D docs: translateLocal is equivalent to translate, because
  translation is applied last (https://doc.magnum.graphics/magnum/classMagnum_1_1SceneGraph_1_1TranslationRotationScalingTransformation3D.html).
  Cited from prior knowledge; not re-fetched, because the shared WebSearch budget was exhausted. The behaviour is
  independently confirmed by the 98.8 % match of oracle forward steps (§1).
