# Exact collision semantics in Habitat-Sim/Lab 0.1.7 as used by HA-VLN replay scoring

Topic id: `A2-collision-semantics-habitat017`  
Date: 2026-10-24

## Summary

A step counts as a collision iff it is a BODY translation (MOVE_FORWARD; also move_backward/left/right if they existed) whose navmesh-filtered end point lies closer to the start than the requested end point by more than ~2e-5 m: habitat_sim/agent/controls/object_controls.py:80-87 computes collided = (|filter_end-start|^2 + 1e-5) < |end-start|^2 using Magnum's zero-arg Vector.dot() (squared length). With ALLOW_SLIDING=True (HA-VLN config) the filter is PathFinder.tryStep -> Detour moveAlongSurface(allowSliding=true), which returns the closest point on the reachable navmesh boundary to the requested target, so ANY step whose 0.25 m target lies outside the navmesh (walls, furniture, or human footprints) is shortened and flagged, including every step of a slide along a wall at any non-parallel angle. TURN_LEFT/RIGHT are body actions that pass through the filter but have zero displacement, so they can never be flagged (they can, however, silently teleport an off-navmesh agent onto the navmesh); LOOK_UP/LOOK_DOWN only rotate sensor nodes with apply_filter=False; STOP calls sim.get_observations_at(), which overwrites _prev_sim_obs without a 'collided' key, so previous_step_collided is False. The agent is a 0.1 m radius / 1.5 m tall cylinder; the navmesh is eroded by ceil(0.1/0.05)=2 cells = 0.10 m from geometry, with walkableHeight 1.6 m and walkableClimb 0.2 m. HA-VLN inserts each human GLB frame as a STATIC object and calls recompute_navmesh(include_static_objects=True, radius 0.1, height 1.5), which joins the human meshes into the stage collision mesh, so a 'human collision' is literally a navmesh collision with the human's body silhouette (parts 0.2-1.6 m above floor) inflated by 0.10 m; there is no separate human-proximity detector in the scoring chain (the paper's '1 m' definition is NOT what the code does, and the CMA baseline's TCR of 14-18 per episode proves wall collisions are counted). The per-frame navmesh <scan>_<fff>.navmesh is swapped into the pathfinder inside HAVLNCEDaggerEnv.step() BEFORE each sim step whenever >=1 wall-clock signal (every 0.1 s) is pending and total_signals_sent<=120; after ~12 s wall time it freezes at the last processed frame. Which frames are active is wall-clock dependent (nondeterministic for us), and in a new-scene episode whose reset+scene load exceeds 12 s humans are never injected at all (base human-free navmesh). The agent start is set unconditionally (no navigability check); 4-6.5% of val_unseen starts lie within 0.3-0.5 m of a human, where a first MOVE_FORWARD is almost surely flagged while a first TURN snaps the agent out for free. Guaranteeing collisions.count==0 therefore means: plan on a swept-volume navmesh (all 120 frames of every human loaded as static objects) recomputed at agent_radius 0.25-0.30, keep >=0.10 m extra margin, make the first action a TURN when the start is non-navigable, end with STOP, and verify every action sequence by exact kinematic try_step replay against all 121 candidate navmeshes (base + 120 frames) before submission.

## Facts (verified from code/data; confidence in brackets)

1. **[high]** The collided flag is computed in Python as collided = (dist_moved_after_filter + EPS) < dist_moved_before_filter with EPS = 1e-5, where both distances are SQUARED lengths ((end_pos-start_pos).dot(), (filter_end-start_pos).dot()).  
   *Evidence:* habitat-sim v0.1.7 habitat_sim/agent/controls/object_controls.py lines 19 (EPS = 1e-5) and 68-89 (ObjectControls.action). Magnum zero-arg Vector::dot() returns Math::dot(*this,*this): mosra/magnum@46f4518 src/Magnum/Math/Vector.h:496-505; Python binding mosra/magnum-bindings@52f2073 src/python/magnum/math.vector.h:316.

2. **[high]** For a 0.25 m MOVE_FORWARD the step is flagged iff the actual 3D displacement after filtering is < sqrt(0.0625-1e-5) = 0.249980 m, i.e. the filter shortened the move by more than 2.0e-5 m (0.02 mm). The test compares distances moved, not positions: a filtered end point that is displaced but equally far (e.g. vertical snapping on stairs) is not flagged, as the code comment at object_controls.py:83-86 states.  
   *Evidence:* Arithmetic on object_controls.py:80-87: (0.25-d)^2 + 1e-5 < 0.0625  <=>  d > 2e-5 (ignoring d^2).

3. **[high]** Only body actions can set collided: Agent.act() sets did_collide = controls.action(scene_node, ..., apply_filter=True) iff controls.is_body_action(action.name); otherwise it moves the sensor nodes with apply_filter=False and returns False.  
   *Evidence:* habitat_sim/agent/agent.py:158-184; ObjectControls.is_body_action habitat_sim/agent/controls/object_controls.py:39-48.

4. **[high]** move_forward/move_backward/move_left/move_right are registered body_action=True; turn_left/turn_right are registered body_action=True (so they run through the move filter) but produce zero translation, hence dist_moved_before_filter=0 and collided (= after+1e-5 < 0) can never be True; look_up/look_down (and move_up/move_down) are body_action=False and never touch the filter.  
   *Evidence:* habitat_sim/agent/controls/default_controls.py:70-91 (moves), 106-123 (LookLeft/LookRight + registry.register_move_fn(..., name='turn_left'/'turn_right', body_action=True)), 126-139 (LookUp/LookDown body_action=False). C++ mirror: src/esp/agent/Agent.cpp:19-21 BodyActions = {moveRight, moveLeft, moveForward, moveBackward, turnLeft, turnRight}.

5. **[high]** Side effect of turns: because the filter still runs with start==end, obj.translate(filter_end - end_pos) is applied; if the agent is off the navmesh (e.g. inside a human footprint hole) a TURN teleports it to the nearest navmesh point with collided=False.  
   *Evidence:* object_controls.py:75-78 (translate applied before the distance test); PathFinder.cpp tryStep projects start via findNearestPoly with half-extents {2,4,2} (src/esp/nav/PathFinder.cpp:65-87, 1114-1187).

6. **[high]** STOP never counts and clears a stale flag: StopAction.step() sets task.is_stop_called and returns sim.get_observations_at(), which sets _prev_sim_obs to raw sensor observations lacking the 'collided' key; previous_step_collided returns _prev_sim_obs.get('collided', False). reset() behaves the same.  
   *Evidence:* habitat-lab v0.1.7 habitat/tasks/nav/nav.py:1018-1029; habitat/sims/habitat_simulator/habitat_simulator.py:325-331 (reset), 523-551 (get_observations_at, line 540 sets _prev_sim_obs), 564-576 (previous_step_collided).

7. **[high]** The Collisions measure increments count by exactly 1 per env.step() in which previous_step_collided is True; it is called once after every action, including STOP, LOOK_*, and turns (which contribute 0).  
   *Evidence:* habitat/tasks/nav/nav.py:653-672 (Collisions.update_metric); habitat/core/env.py:240-274 (task.step then measurements.update_measures). HA-VLN CollisionsDetail is identical plus a per-step bool list: HASimulator/measures.py:158-181. VLN-CE habitat_extensions/measures.py defines no Collisions override (grep).

8. **[high]** The move filter is Simulator.step_filter: if pathfinder.is_loaded, end = pathfinder.try_step(start,end) when sim_cfg.allow_sliding else try_step_no_sliding; HA-VLN runs with ALLOW_SLIDING: True (also the habitat-lab default).  
   *Evidence:* habitat_sim/simulator.py:451-461 (step_filter), 259 (installed as controls.move_filter_fn); HA-VLN HASimulator/config/HAVLNCE_R2R_task.yaml:14-16; habitat-lab habitat/config/default.py:277.

9. **[high]** PathFinder::Impl::tryStep: projects start and end onto the nearest navmesh polygon within a {2,4,2} m half-extent box (failure -> return start, i.e. no movement -> flagged); checks island connectivity (no connection -> return start); calls Detour moveAlongSurface(startRef, projectedStart, end, allowSliding); numPolys==0 -> return start; sets y via getPolyHeight; if the end lands on an edge between disconnected components, nudges it 1e-4 m toward the polygon center.  
   *Evidence:* habitat-sim src/esp/nav/PathFinder.cpp:1114-1187 (tryStep), 65-87 (projectToPoly, polyPickExt {2,4,2}), 1363-1375 (public tryStep / tryStepNoSliding wrappers).

10. **[high]** Detour moveAlongSurface with allowSliding=true returns the end position if it lies inside a reachable polygon; otherwise the closest point (2D) on a reachable 'wall' edge to the target. With allowSliding=false (habitat fork modification) the candidate end is the intersection of the start->end segment with the wall edge, and neighbour traversal is limited to polygons the segment actually crosses.  
   *Evidence:* erikwijmans/recastnavigation@354591e ('No sliding try step', Jan 21 2020) Detour/Source/DetourNavMeshQuery.cpp:2068-2270, specifically 2155-2162 (dtPointInPolygon early exit), 2190-2219 (wall-edge handling, allowSliding branch), 2246-2255 (neighbour pruning when !allowSliding).

11. **[high]** Consequence: with sliding, when an agent at perpendicular distance h from a straight boundary moves 0.25 m at angle phi to the boundary normal such that the target crosses the boundary, the filtered displacement is sqrt(h^2 + (0.25 sin phi)^2) < 0.25, so the step is flagged. Sliding along a wall is flagged on EVERY step unless the motion is exactly parallel to the boundary with the target still on the navmesh. Hitting a boundary head-on yields displacement h (<0.25) -> flagged; if already touching (h=0) the agent does not move at all.  
   *Evidence:* Derived from DetourNavMeshQuery.cpp:2190-2219 (closest boundary point to target) plus object_controls.py:80-87. Consistent with CMA baseline TCR 13.7/17.5 collisions per episode (track2/README.md:181-186), only explicable if wall slides count.

12. **[high]** Agent defaults are radius 0.1 m, height 1.5 m, body_type cylinder; HA-VLN does not override them. habitat_sim recomputes the navmesh at configure time only when radius/height differ from these defaults, so the shipped MP3D <scan>.navmesh is used as the base navmesh.  
   *Evidence:* habitat_sim/agent/agent.py:73-86 (AgentConfiguration); src/esp/agent/Agent.h:52-60; habitat-lab habitat/config/default.py:251-252 (AGENT_0.HEIGHT 1.5, RADIUS 0.1); HA-VLN HASimulator/config/HAVLNCE_R2R_task.yaml:10-11 sets only SENSORS; habitat_sim/simulator.py:199-234 (_config_pathfinder).

13. **[high]** NavMeshSettings defaults: cellSize 0.05, cellHeight 0.2, agentHeight 1.5, agentRadius 0.1, agentMaxClimb 0.2, agentMaxSlope 45 deg, regionMinSize 20 (minRegionArea 400 cells = 1 m^2), edgeMaxLen 12, edgeMaxError 1.3 voxels, filterLowHangingObstacles/LedgeSpans/WalkableLowHeightSpans all true. Build config: walkableRadius = ceil(0.1/0.05) = 2 cells (0.10 m erosion via rcErodeWalkableArea), walkableHeight = ceil(1.5/0.2) = 8 cells (1.6 m), walkableClimb = floor(0.2/0.2) = 1 cell (0.2 m).  
   *Evidence:* src/esp/nav/PathFinder.h:103-154 (NavMeshSettings::setDefaults); src/esp/nav/PathFinder.cpp:357-374 (rcConfig), 414-434 (rasterize + filters), 455 (rcErodeWalkableArea).

14. **[high]** HA-VLN turns humans into navmesh obstacles: add_new_human_model() adds the frame's GLB via add_object_by_handle, sets translation/rotation, sets MotionType.STATIC; _handle_signals() then calls sim.recompute_navmesh(pathfinder, NavMeshSettings(radius 0.1, height 1.5), include_static_objects=True) and caches the result as <RECOMPUTE_NAVMESH_PATH>/<scan>/<scan>_<frame:03d>.navmesh (or loads the cached file).  
   *Evidence:* HA-VLN HASimulator/environments.py:171-213 (add_new_human_model; STATIC at line 208), 111-147 (_handle_signals; navmesh lines 129-144). Identical in organizer fork havln2 (diff: IDENTICAL).

15. **[high]** C++ recomputeNavMesh joins the stage collision mesh with the collision (or render) mesh of every STATIC object, transformed by its scene-node transform and template scale, then rebuilds the navmesh from the joined triangle soup. Human bodies are therefore ordinary geometry: body parts between walkableClimb (0.2 m) and walkableHeight (1.6 m) above the floor make the floor cells beneath them unwalkable (rcFilterWalkableLowHeightSpans), parts <=0.2 m are step-over-able (rcFilterLowHangingWalkableObstacles), near-horizontal body tops are removed as ledges (rcFilterLedgeSpans), and the footprint is then eroded outward by 0.10 m (+<=0.05 m raster). A 'human collision' in scoring is exactly a navmesh collision; no human-proximity logic exists in Collisions/CollisionsDetail.  
   *Evidence:* habitat-sim src/esp/sim/Simulator.cpp:643-700 (recomputeNavMesh, includeStaticObjects loop 661-695); PathFinder.cpp:414-455; habitat-lab nav.py:666-672; HASimulator/measures.py:172-181.

16. **[high]** Replay step order: HAVLNCEDaggerEnv.step() calls havlnce_tool._handle_signals() BEFORE habitat RLEnv.step(), so the navmesh in force for step k's collision test is the one swapped in at the start of step k. reset() calls havlnce_tool.reset() (remove old humans, add frame-0 humans into the CURRENT = previous scene, no navmesh swap) BEFORE super().reset(); a scene change closes and reconfigures the C++ simulator (dropping all objects) and reloads the base navmesh, so humans and the human-aware navmesh for a new scene first appear at step 1 via _handle_signals.  
   *Evidence:* HA-VLN agent/VLN-CE/vlnce_baselines/common/environments.py:48-74 (HAVLNCEDaggerEnv) and 104-130 (HAVLNCEInferenceEnv, same logic); HASimulator/environments.py:49-58 (reset), 57 (_handle_signals commented out in reset); habitat-lab habitat_simulator.py:360-370 (close + reconfigure when scene changes); habitat_sim/simulator.py:117-133 (close), 199-212 (base navmesh reload). The official CMA export uses HAVLNCEDaggerEnv: track2/scripts/export_cma_submission.py:78,125,161.

17. **[high]** Frame selection is wall-clock driven: a daemon thread enqueues a signal every 0.1 s (queue maxsize 120); _handle_signals drains the queue and, if >=1 signal was pending AND total_signals_sent <= 120, refreshes humans to frame_id=(total_signals_sent-1)%120 and swaps the navmesh; after 120 signals (~12 s since reset) no refresh ever happens again in that episode. If reset + scene load itself exceeds 12 s in a new-scene episode, humans are never injected and the whole episode runs on the base human-free navmesh.  
   *Evidence:* HASimulator/environments.py:41-47 (queue, thread), 96-109 (_signal_sender, sleep 0.1), 111-128 (frame_id and <=120 guard), 49-58 (reset puts one signal). README FAQ Q4: 'Human animation follows released wall-clock behavior' (track2/README.md:262-264).

18. **[medium]** Set of navmeshes that can be active during an episode: {frame_000..frame_119 of the episode's scan} plus the base MP3D navmesh (new-scene episode when the scorer is slow) — the previous episode's last frame navmesh (same scene) is only resident before step 1 and is replaced by _handle_signals at step 1. Per-frame navmesh files are deterministic functions of (scene mesh, human_motion.json, HAPS2_0 GLBs, recast settings), so they can be regenerated locally.  
   *Evidence:* Derived from environments.py:111-147 and the reset/step ordering above; Recast/Detour build is deterministic for identical input (standard Recast behaviour).

19. **[high]** Human motion is small and rotation is constant: 749 humans across 72 released scans, no None frames; horizontal swept extent (max pairwise XZ distance over 120 frames) median 0.00 m, mean 0.20 m, p90 0.80 m, p99 1.79 m, max 3.47 m; 18.7% exceed 0.5 m, 6.3% exceed 1 m; 0 humans change their Euler rotation across frames.  
   *Evidence:* Computed with python -I from HA-VLN/Data/Multi-Human-Annotations/human_motion.json (this session).

20. **[high]** Episode starts can overlap humans: set_agent_state() places the agent unconditionally (always returns True, no navigability check). In val_unseen 75/1833 episodes start within 0.3 m (XZ, |dy|<1.5) of some human's translation point at some frame, 120 within 0.5 m, 156 within 0.75 m; val_seen 39/51/63 of 772; train 408/603/828 of 10663. Goals within 0.3 m of a human: val_unseen 54/1818, val_seen 27/775.  
   *Evidence:* habitat-lab habitat_simulator.py:485-521 (set_agent_state), 311-323 (_update_agents_state), env.py:205-227; statistics computed from Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{split}/{split}.json.gz (same episodes as HA-R2R) joined with human_motion.json.

21. **[high]** Behaviour when the start is inside a human-footprint hole of the active navmesh: a first MOVE_FORWARD projects the start to the nearest boundary point (<=2 m box), slides toward the target and almost always travels < 0.25 m -> flagged; a first TURN_LEFT/RIGHT relocates the agent to the nearest navmesh point with collided=False. The relocation depends on which frame's navmesh is active.  
   *Evidence:* PathFinder.cpp:1114-1150 (projectToPoly on start, moveAlongSurface from the projected point), object_controls.py:75-87 (translate then distance test; turns have dist_before=0).

22. **[high]** Score plumbing: TCR_ep = max(0, collisions.count - collision_num[ep]); CR_ep = min(TCR_ep, 1); SR_ep = success * [TCR_ep == 0]. collision_num nonzero in val_seen 60/778 (mean .112, max 3), val_unseen 159/1839 (mean .158, max 4), test 237/3408 (mean .082, max 3), train 824/10819. collision_num correlates only weakly with human proximity to the reference path (val_unseen: only 96/159 cn>0 episodes have a human within 0.3 m of the ref path, while 603/1680 cn==0 episodes do), so it is not a simple geometric count — treat it as a released per-episode constant.  
   *Evidence:* HA-VLN HASimulator/metric.py:14-17; Data/HA-R2R-tools/collision_num_*.json statistics and proximity analysis computed this session.

23. **[high for the public code; medium that the hidden havln_scoring package behaves identically]** The paper defines TCR over collisions 'within 1 m of a human', but the released scoring code counts ALL navmesh collisions (walls, furniture, humans) via habitat-lab's Collisions measure; the CMA baseline's TCR of 13.7 (val_seen) / 17.5 (val_unseen) collisions per episode is only consistent with wall collisions being counted (only ~8% of episodes even have a nonzero human baseline).  
   *Evidence:* WebSearch summary of arXiv 2503.14229 (TCR = sum(c_i - |A_i^c|)/L, c_i = steps with collisions within 1 m of a human); code: HASimulator/metric.py:15 uses metric['collisions']['count']; README metric table track2/README.md:181-186.

24. **[medium-high (depends on the hidden scorer importing habitat_extensions, which it must to load the VLN-CE-v1 dataset class)]** Success/NE use STRAIGHT-LINE distance and require STOP: habitat_extensions/__init__.py imports measures, which does `from HASimulator.measures import *`, registering a class named DistanceToGoal (uuid 'distance_to_goal') that uses euclidean_distance; the registry keeps the last registration, overriding habitat-lab's geodesic DistanceToGoal. habitat-lab Success requires task.is_stop_called AND distance_to_goal < SUCCESS_DISTANCE (3.0). A 500-action sequence without STOP cannot succeed.  
   *Evidence:* HA-VLN agent/VLN-CE/habitat_extensions/__init__.py:1; habitat_extensions/measures.py:28; HASimulator/measures.py:100-155 (euclidean); habitat-lab habitat/core/registry.py:43-63 (mapping[_type][name] = cls, last wins); habitat/tasks/nav/nav.py:500-539 (Success), 929-985 (geodesic DistanceToGoal being overridden); HAVLNCE_R2R_task.yaml:27,47-50 (SUCCESS_DISTANCE 3.0). track2/scripts/export_cma_submission.py:55 shows the runtime imports habitat_extensions.

25. **[high]** Side effect of the DISTANCE_TO_HUMAN measure (in HA-VLN's own eval MEASUREMENTS, not in the CMA export which sets MEASUREMENTS=[]): each update executes a filtered MOVE_FORWARD on the agent and restores it with agent.set_state(state) whose default reset_sensors=True resets camera tilt, so LOOK_UP/LOOK_DOWN effects are undone every step in that configuration. It does not touch _prev_sim_obs, so it cannot change collisions.count.  
   *Evidence:* HASimulator/measures.py:49-97 (lines 64-70 execute controls.action with apply_filter=True; line 89 set_state); habitat_sim/agent/agent.py:203-242 (set_state defaults); HAVLNCE_R2R_task.yaml:35-46 (MEASUREMENTS incl. DISTANCE_TO_HUMAN); track2/scripts/export_cma_submission.py:118 (MEASUREMENTS=[]).

26. **[high]** The six-action vocabulary (incl. LOOK_UP/LOOK_DOWN) is provided by the image's patched task config (/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml, /app/config/challenge_submission.yaml), not by the public HAVLNCE_R2R_task.yaml (which lists POSSIBLE_ACTIONS [STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT] with ACTION_SPACE_CONFIG v0, which has no look actions). In habitat-lab, look actions need action-space config v1, which uses TILT_ANGLE (default 15 deg) and no pitch constraint.  
   *Evidence:* track2/scripts/export_cma_submission.py:14,104,123-124,219; HA-VLN HASimulator/config/HAVLNCE_R2R_task.yaml:9,34; habitat-lab habitat/sims/habitat_simulator/actions.py:92-133; habitat/config/default.py:218 (TILT_ANGLE 15).

## Key numbers

| What | Value | Source |
|---|---|---|
| EPS in collided test (squared metres) | 1e-5 | habitat_sim/agent/controls/object_controls.py:19 |
| Minimum filtered displacement for a 0.25 m step to NOT be flagged | 0.249980 m (shortening tolerance 2.0e-5 m) | sqrt(0.0625 - 1e-5), object_controls.py:80-87 |
| Agent radius / height defaults | 0.1 m / 1.5 m | habitat_sim/agent/agent.py:74-75; habitat-lab default.py:251-252 |
| Navmesh erosion from geometry | 2 cells = 0.10 m (cellSize 0.05) | PathFinder.cpp:364,455; PathFinder.h:138-141 |
| Navmesh walkableHeight / walkableClimb | 8 cells = 1.6 m / 1 cell = 0.2 m | PathFinder.cpp:362-363 |
| findNearestPoly search half-extents in tryStep | {2, 4, 2} m | PathFinder.cpp:73 |
| Thin-wall nudge | 1e-4 m | PathFinder.cpp:1179 |
| Human animation signal period / freeze horizon | 0.1 s / 120 signals (~12 s) | HASimulator/environments.py:109,124 |
| Human horizontal swept extent over 120 frames | median 0.00, mean 0.20, p90 0.80, p99 1.79, max 3.47 m; 18.7% > 0.5 m, 6.3% > 1 m | human_motion.json analysis (this session) |
| val_unseen starts within 0.3 / 0.5 / 0.75 m of a human (any frame) | 75 / 120 / 156 of 1833 | R2R-CE v1-2 val_unseen episodes x human_motion.json |
| val_seen starts within 0.3 / 0.5 / 0.75 m of a human | 39 / 51 / 63 of 772 | same |
| collision_num baseline nonzero episodes | val_seen 60/778, val_unseen 159/1839, test 237/3408, train 824/10819; max 4 | Data/HA-R2R-tools/collision_num_*.json |
| CMA baseline TCR (collisions per episode above baseline) | 13.726 val_seen, 17.536 val_unseen | track2/README.md:181-186 |
| Success distance | 3.0 m (Euclidean if HASimulator override active) | HAVLNCE_R2R_task.yaml:27; HASimulator/measures.py:100-155 |

## Implications (inferences)

- Zero collisions is a pure geometry problem: every MOVE_FORWARD target point (exactly 0.25 m ahead along the quantized 15-degree heading) must lie inside the ACTIVE navmesh with margin; turns, looks and STOP are free. No perception is needed to avoid collisions once scene mesh + human placements are known.
- Because the scoring navmesh is already eroded by 0.10 m, a planning navmesh recomputed at agent_radius 0.25-0.30 m gives 0.15-0.20 m of guaranteed clearance beyond the scoring boundary; combine with the swept-volume trick (load all 120 frames of each human as STATIC objects before recompute_navmesh(include_static_objects=True)) so one planning mesh covers every possible animation frame.
- Wall-hugging and door thresholds are the dominant collision source for learned agents (baseline ~15 flagged steps/episode); a planner that stays centred in corridors and aligns heading before forward runs eliminates them.
- Human animation frames during official scoring are wall-clock dependent and the scorer may even skip human injection in slow new-scene resets, so robustness must be over the UNION of all 120 per-frame navmeshes plus the base navmesh; never optimise for a specific frame.
- Because collided is a per-step distance test with a 0.02 mm tolerance, verification must be an exact kinematic replay (same float32 Magnum ops, same try_step) rather than a coarse geometric check; the PathFinder python binding needs no GPU/renderer, so all 3,408 test episodes x 121 navmeshes can be verified cheaply on CPU.
- If the start is inside a human footprint on the human-aware navmesh, begin with a TURN (free re-snap) and never with MOVE_FORWARD; account for the resulting re-snapped position in the plan.
- Success is Euclidean (<3 m straight-line at STOP) if the Euclidean DistanceToGoal override is active, which relaxes goal placement (stopping across a thin wall within 3 m counts); plan for geodesic <3 m anyway so the result is robust either way. STOP is mandatory.
- The paper's '1 m of a human' TCR definition does not match the code: wall collisions count, so human-avoidance alone is insufficient; total navmesh contact must be zero.

## Engineering rules for guaranteeing collisions.count == 0

- RULE 1 (what counts): treat any MOVE_FORWARD whose 0.25 m target leaves the active navmesh as a collision; turns/looks/STOP never count. Plan so that the entire 0.25 m segment stays inside the navmesh with margin (sample every <=5 cm; check is_navigable and distance_to_closest_obstacle >= margin).
- RULE 2 (planning mesh): for each scan, add ALL 120 frames of every human as STATIC objects, then sim.recompute_navmesh(pathfinder, NavMeshSettings(agent_radius=0.30, agent_height=1.5), include_static_objects=True) to obtain a swept-volume navmesh with 0.20 m clearance beyond the scoring boundary; keep a 0.25 m variant for narrow doorways (fall back only when the 0.30 m mesh is disconnected) and add >=0.10 m extra margin to absorb Recast contour simplification (edgeMaxError 1.3 voxels ~ 6.5 cm).
- RULE 3 (human clearance heuristic): keep the agent centre >= footprint_half_width + 0.10 (erosion) + 0.05 (raster) + 0.10 (safety) from every human translation over all 120 frames; use per-frame AABBs from the loaded GLBs (standing ~0.5-0.6 m total, sitting/lying up to ~1.2 m) rather than a constant; remember 19% of humans sweep >0.5 m and 6% >1 m.
- RULE 4 (verify): before submission, replay every action sequence kinematically (no rendering) against all 121 candidate navmeshes {base, frame_000..119}: load with habitat_sim.nav.PathFinder().load_nav_mesh(), emulate _move_along (translate_local along -Z by 0.25), try_step, obj.translate(filter_end-end), and the squared-distance EPS test exactly as object_controls.py:68-89, including turn re-snapping; require 0 flagged steps on all of them. Then run the real HAVLNCEDaggerEnv docker replay once as a final check.
- RULE 5 (start inside a human): if the start is non-navigable on any candidate navmesh, make action 1 a TURN (free re-snap), compute the re-snapped position per navmesh with try_step(start,start), and plan from a position that is safe for all; never start with MOVE_FORWARD.
- RULE 6 (path style): stay centred in corridors; align heading with turns before each straight run; avoid gaps narrower than 0.6 m on the planning mesh; prefer longer wide routes over short tight ones (path length is not scored beyond the 500-step cap).
- RULE 7 (termination): always end with STOP within 500 actions (success requires is_stop_called); aim for geodesic distance to goal < 3.0 m even though the active DistanceToGoal is likely Euclidean.
- RULE 8 (robustness): design for the union of all animation frames and the human-free base navmesh; do not exploit a particular frame or scorer speed.
- Phase-1 probes (cheap, 5 submissions/day): (a) a human-free, wall-sliding sequence set to confirm wall collisions count; (b) an Euclidean-vs-geodesic goal probe; (c) a sequence set that is collision-free on the swept mesh to confirm TCR==0 is reachable on the official scorer.

## Open questions

- Does the hidden havln_scoring package compute TCR from habitat-lab's Collisions.count exactly as the public metric.py does, or does it apply a human-proximity filter as in the paper? (Evidence strongly favours the public code; confirm on Phase-1 leaderboard by submitting a deliberately wall-sliding but human-free sequence set.)
- Does the official scorer import habitat_extensions (activating the Euclidean DistanceToGoal override)? Test with a Phase-1 submission that stops within 3 m Euclidean but >3 m geodesic of a goal.
- How fast is the official scorer per step and per scene load? This determines which animation frames are active and whether new-scene episodes ever get humans (12 s budget).
- Are the recompute_navmesh cache files shipped inside the image/data bundle or regenerated during scoring; is Recast output bit-identical across CPUs (affects the 0.02 mm-tolerance verification; margins of >=0.10 m make this moot).
- Exact HAPS2_0 mesh footprints and object-origin convention per category (needed to convert human translation points into clearance distances); compute AABBs from the GLBs locally.
- Whether the Phase-2 bundle provides the 18 test scans' human_motion entries (required to build human-aware navmeshes for test episodes); if withheld, plan with a conservative human-free base navmesh plus the released HA-VLN 1.0 human_motion_text.json placements as proxies.

## Sources

- https://github.com/facebookresearch/habitat-sim tag v0.1.7 (856d4b0): habitat_sim/agent/controls/object_controls.py, habitat_sim/agent/controls/default_controls.py, habitat_sim/agent/agent.py, habitat_sim/simulator.py, src/esp/agent/Agent.cpp, src/esp/agent/Agent.h, src/esp/nav/PathFinder.cpp, src/esp/nav/PathFinder.h, src/esp/sim/Simulator.cpp, src/esp/bindings/ShortestPathBindings.cpp, tests/test_simulator.py
- https://github.com/facebookresearch/habitat-lab tag v0.1.7 (d6ed1c0): habitat/sims/habitat_simulator/habitat_simulator.py, habitat/sims/habitat_simulator/actions.py, habitat/tasks/nav/nav.py, habitat/core/env.py, habitat/core/embodied_task.py, habitat/core/registry.py, habitat/config/default.py, habitat/tasks/vln/vln.py
- https://github.com/erikwijmans/recastnavigation commit 354591e10a772b8057e42a4f9de701155b9aaa02 (habitat-sim submodule): Detour/Source/DetourNavMeshQuery.cpp moveAlongSurface, findNearestPoly
- https://raw.githubusercontent.com/mosra/magnum/46f4518eb6ca121dfa3da2884dc5c8ad5417e97b/src/Magnum/Math/Vector.h (dot() = Math::dot(*this,*this)); https://raw.githubusercontent.com/mosra/magnum-bindings/52f2073ff9c399ad2120085c9ca6f6a021fdafc1/src/python/magnum/math.vector.h
- Local: ext/HA-VLN (UWMILab/HA-VLN main): HASimulator/environments.py, HASimulator/measures.py, HASimulator/metric.py, HASimulator/config/HAVLNCE_R2R_task.yaml, agent/VLN-CE/vlnce_baselines/common/environments.py, agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py, agent/VLN-CE/habitat_extensions/{__init__,measures,actions,task}.py, Data/Multi-Human-Annotations/human_motion.json, Data/HA-R2R-tools/collision_num_*.json; ext/havln2 (identical files)
- Local: ext/track2 README.md and scripts/export_cma_submission.py (official toolkit); ext/Discrete-Continuous-VLN R2R_VLNCE_v1-2_preprocessed episodes (start/goal/reference paths)
- https://arxiv.org/abs/2503.14229 HA-VLN 2.0 paper (TCR/CR definitions, via WebSearch summary)
- https://arxiv.org/html/2610.14682 'Successful but Unsafe' (VLN-Safe): independent description of Habitat flagging a translation as collision when the navmesh filter shortens it
- https://doc.magnum.graphics/python/magnum/Vector3/ (dot(self) -> float)

## Appendix A: exact collided computation (habitat-sim v0.1.7, habitat_sim/agent/controls/object_controls.py:68-89)

```
start_pos = obj.absolute_translation
move_fn(obj, actuation_spec)              # MOVE_FORWARD: translate_local(-Z * 0.25); turns: rotate only
end_pos   = obj.absolute_translation
if apply_filter:                          # True for body actions (move_*, turn_*), False for look_*
    filter_end = move_filter_fn(start_pos, end_pos)      # Simulator.step_filter -> pathfinder.try_step (ALLOW_SLIDING=True)
    obj.translate(filter_end - end_pos)                  # agent is moved to the filtered point (also for turns!)
    dist_moved_before_filter = (end_pos - start_pos).dot()        # SQUARED length (Magnum Vector.dot())
    dist_moved_after_filter  = (filter_end - start_pos).dot()
    collided = (dist_moved_after_filter + 1e-5) < dist_moved_before_filter
```
Flag propagation: Agent.act (agent.py:158-184) -> Simulator.step sets obs["collided"] (simulator.py:407-420) -> HabitatSim.step stores _prev_sim_obs (habitat_simulator.py:333-337) -> previous_step_collided = _prev_sim_obs.get("collided", False) (:564-576) -> Collisions.update_metric count += 1 (nav.py:666-672). STOP -> get_observations_at() drops the key (:523-551). HA-VLN metric: TCR = max(0, count - collision_num[ep]) (HASimulator/metric.py:15).

## Appendix B: per-step navmesh in force during replay (HA-VLN)

```
HAVLNCEDaggerEnv.step(a):                      # vlnce_baselines/common/environments.py:66-74
    havlnce_tool._handle_signals()             # drains 0.1 s wall-clock signals; if any and total<=120:
                                               #   frame=(total-1)%120; remove+add humans at frame (STATIC);
                                               #   load <scan>_<frame:03d>.navmesh or recompute_navmesh(r=0.1,h=1.5,include_static_objects=True)
    habitat Env.step(a):                       # task.step -> sim.step(a) -> collided vs CURRENT pathfinder navmesh
        measurements.update_measures()         # Collisions counts previous_step_collided
```
Reset: havlnce_tool.reset() (frame-0 humans into the *previous* scene, no navmesh swap) then Env.reset() (scene change => sim.close()+reconfigure => objects dropped, base navmesh reloaded). Humans/navmesh for a new scene appear at step 1 — unless >12 s elapsed (total_signals_sent>120), in which case the episode has no humans at all.
