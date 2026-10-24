# Exact collision semantics of the HA-VLN 2.0 / Habitat 0.1.7 replay scorer, and rules for collisions.count == 0

Topic id: `A2-collision-semantics-habitat017`  
Date: 2026-10-24  
Status: verified from source code (habitat-sim/lab v0.1.7, Recast fork, HA-VLN, official toolkit) plus statistics computed this session from released data. No Habitat run was possible here (no GPU, no MP3D).

## Summary

A step counts as a collision only if it is MOVE_FORWARD and the navmesh filter shortens the 0.25 m move: collided = |filter_end-start|^2 + 1e-5 < |end-start|^2 (Magnum float32 squared lengths). So a forward step is flagged when its filtered displacement is under 0.249980 m, i.e. it was shortened by more than 0.02 mm. TURN_LEFT/RIGHT do pass through the filter, but they have zero requested displacement, so they can never be flagged. They can, however, silently snap an agent that is off the navmesh back onto it. LOOK_UP/DOWN skip the filter. STOP replaces the observation and removes the 'collided' key. With ALLOW_SLIDING=True (all HA-VLN configs, and the habitat-lab default), Detour moveAlongSurface returns the closest boundary point whenever the target leaves the reachable navmesh. That makes every step of a wall slide at any non-parallel angle a collision, and it explains the CMA baseline's ~14-18 counted collisions per episode. The check looks only at the endpoint (no swept test), with a search circle whose diameter is the step. HA-VLN turns humans into navmesh obstacles in four steps: it adds each human's per-frame GLB as a STATIC object, which is re-centred on its bounding-box centre; it calls recompute_navmesh(include_static_objects=True, radius 0.1, height 1.5), which joins the human meshes into the stage mesh; it rebuilds the whole Recast navmesh (cell 0.05 m, walkableHeight 1.6 m, climb 0.2 m, 0.10 m erosion, islands < 1 m^2 removed); and it caches the result per (scan, frame). A 'human collision' is therefore an ordinary navmesh collision with the human silhouette (body parts 0.2-1.6 m above the floor) inflated by about 0.10 m. No 1 m proximity logic exists anywhere in the public scoring chain. The navmesh is swapped before the sim step at every step that has a pending clock signal. The first step always refreshes, at frame 0..119. Refreshes continue until about 120 signals (~12 s of GIL-available wall time; the 0.1 s clock thread is starved while pybind11 C++ calls hold the GIL). After that the scene freezes at the last refreshed frame. A plan must therefore be collision-free on every one of the 120 per-frame navmeshes (their intersection, i.e. the union of human holes), plus the human-free one. The agent start is set unconditionally. If it lies inside a human hole, a first MOVE_FORWARD is flagged or not depending on direction, while a first TURN snaps the agent out for free. Released data shows human translations are the bodies' bbox centres (y = floor + 0.84 m). It also shows that collision_num>0 almost always means a human within 3 m of the goal: 98% of cn>0 train and val_unseen episodes, and P(cn>0) = 0.93-1.0 when a human stands on the goal. That is useful both as a collision allowance and as a goal prior for the 237 test episodes with cn>0. Guaranteeing count == 0 comes down to geometry. Rebuild the scorer's 120 per-frame navmeshes (plus the human-free ones) in the official image. Plan on their intersection with at least 0.15 m clearance (at least 0.05 m only where unavoidable). Keep every forward segment fully inside the navmesh. Start with a TURN when the start is off-mesh in any frame. Accept a sequence only if exact try_step replay on all candidate navmeshes gives 0 flagged steps and 0 snaps.

## Collision call chain (habitat-sim / habitat-lab 0.1.7 + HA-VLN)

```
HAVLNCEDaggerEnv.step(a)                         vlnce_baselines/common/environments.py:68-75
  havlnce_tool._handle_signals()                 HASimulator/environments.py:111-147
     if >=1 pending signal and total<=120: frame=(total-1)%120
        remove + add humans (STATIC) at frame     :149-213
        pathfinder <- <scan>_<fff>.navmesh (load) or recompute_navmesh(r=0.1,h=1.5,include_static_objects=True)+save
  habitat Env.step -> task.step -> MoveForwardAction -> HabitatSim.step   nav.py:990-996; habitat_simulator.py:333-337
     habitat_sim.Simulator.step -> Agent.act      simulator.py:393-423; agent.py:158-184
        ObjectControls.action(body, 'move_forward', 0.25, apply_filter=True)   object_controls.py:68-89
           end = start + R(yaw)*(0,0,-0.25)
           f = step_filter(start,end) = pathfinder.try_step(start,end)          simulator.py:451-464
               projectToPoly(start), projectToPoly(end) [+-2,+-4,+-2 m]; island check; Detour moveAlongSurface(sliding)
           node.translate(f-end); collided = |f-start|^2 + 1e-5 < |end-start|^2
     obs['collided'] = collided -> HabitatSim._prev_sim_obs                    simulator.py:420; habitat_simulator.py:335
  measurements.update_measures -> Collisions: count += previous_step_collided  nav.py:666-672; env.py:268-270
episode end: TCR = max(0, count - collision_num[ep]); CR = min(TCR,1); SR = success*(TCR==0)   HASimulator/metric.py:14-17
STOP -> get_observations_at() (no 'collided' key -> False)                   nav.py:1024-1029; habitat_simulator.py:523-551
```

## Facts (verified; confidence per item)

1. **[high]** Collision flag formula: in ObjectControls.action, start_pos = node.absolute_translation; move_fn moves the node; if apply_filter: filter_end = move_filter_fn(start_pos, end_pos); node.translate(filter_end - end_pos); collided = (filter_end-start_pos).dot() + EPS < (end_pos-start_pos).dot(), with EPS = 1e-5. Magnum's zero-argument Vector3.dot() is the squared length (float32).  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) habitat_sim/agent/controls/object_controls.py:19 (EPS), :68-89 (action), :80-87 (test); mosra/magnum 46f4518 src/Magnum/Math/Vector.h 'T dot() const { return Math::dot(*this, *this); }'; magnum-bindings 52f2073 src/python/magnum/math.vector.h:316 binds that zero-arg dot().

2. **[high]** Tolerance: a 0.25 m MOVE_FORWARD is flagged iff the filtered 3-D displacement is < sqrt(0.0625-1e-5) = 0.249980 m, i.e. it was shortened by more than 2.0e-5 m. The test compares distances, not positions. A filtered end point that moves vertically (stairs, navmesh height snapping) makes the displacement LONGER, so it is never flagged. A small horizontal shortening s can even be masked when dy^2 >= (0.25)^2-(0.25-s)^2-1e-5. Float32 rounding at |coords| < 100 m is ~1e-5 m per coordinate (squared-length error well under 1e-5), so there are no spurious flags.  
   *Evidence:* Arithmetic on object_controls.py:80-87; code comment :83-86 explicitly cites the stairs case.

3. **[high]** Only body actions reach the filter: Agent.act calls controls.action(scene_node, ..., apply_filter=True) iff is_body_action(action.name); otherwise it rotates the sensor nodes with apply_filter=False and returns did_collide=False.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) habitat_sim/agent/agent.py:158-184; object_controls.py:39-48 (is_body_action).

4. **[high]** move_forward/backward/left/right are registered body_action=True. turn_left/turn_right are re-registrations of LookLeft/LookRight with body_action=True, so they DO pass through the filter, but their requested displacement is 0 and (after+1e-5 < 0) is impossible, so a turn can never be flagged. look_up/look_down (and move_up/down) are body_action=False. The C++ Agent.cpp BodyActions set mirrors this.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) habitat_sim/agent/controls/default_controls.py:70-91, 106-123 (turn_* registration at 122-123), 126-139; src/esp/agent/Agent.cpp:19-21.

5. **[high]** Side effect of turns: because the filter still runs with start == end, node.translate(filter_end - end) is applied. If the agent is off the navmesh (e.g. inside a human-footprint hole after a navmesh swap), a TURN moves it to the nearest navmesh boundary point with collided=False. If the agent is on the navmesh, tryStep(s,s) returns the same x,z (only y is snapped to the polygon height).  
   *Evidence:* object_controls.py:75-78; PathFinder.cpp:1121-1124 (projectToPoly of start), 1136-1138 + DetourNavMeshQuery.cpp:2136-2141 (point-in-poly returns end unchanged), 1153 (getPolyHeight).

6. **[high]** STOP never counts and clears any stale flag: StopAction.step sets task.is_stop_called and returns sim.get_observations_at(), which stores raw sensor observations (no 'collided' key) in _prev_sim_obs. previous_step_collided = _prev_sim_obs.get('collided', False). reset() does the same.  
   *Evidence:* habitat-lab v0.1.7 (d6ed1c0) habitat/tasks/nav/nav.py:1017-1029; habitat/sims/habitat_simulator/habitat_simulator.py:325-331, 523-551 (540), 563-576.

7. **[high]** Counting: the Collisions measure (uuid 'collisions') adds exactly 1 per env.step() in which previous_step_collided is True. It is updated after every action (task.step then measurements.update_measures), including STOP/LOOK/turns, which add 0. reset_metric does not update. HA-VLN's CollisionsDetail is identical plus a per-step bool list. VLN-CE habitat_extensions defines no collision measure.  
   *Evidence:* habitat-lab v0.1.7 (d6ed1c0) habitat/tasks/nav/nav.py:652-672; habitat/core/env.py:240-274 (step), 205-227 (reset); UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) HASimulator/measures.py:158-181; agent/VLN-CE/habitat_extensions/measures.py (no Collisions class; grep).

8. **[high (public configs); medium that the image's /app/config/challenge_submission.yaml keeps it]** The move filter is Simulator.step_filter: if pathfinder.is_loaded, try_step(start,end) when sim_cfg.allow_sliding, else try_step_no_sliding. It is installed as every agent's move_filter_fn. All four HA-VLN task configs set ALLOW_SLIDING: True (also the habitat-lab default). If no navmesh is loaded the filter is a no-op, so there are no collisions at all.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) habitat_sim/simulator.py:451-464, 243-250; UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) HASimulator/config/HAVLNCE_task.yaml:14-16 (+ the 3 sibling yamls); habitat-lab v0.1.7 (d6ed1c0) habitat/config/default.py:277.

9. **[high]** PathFinder::Impl::tryStep: (1) projects start and end with findNearestPoly in a +-2 x +-4 x +-2 m box; on failure it returns start (agent does not move, so the step is flagged). (2) If startRef and endRef are on different islands it returns start (flagged). (3) It runs Detour moveAlongSurface(startRef, PROJECTED start, end, allowSliding). (4) numPolys==0 returns start. (5) y is taken from getPolyHeight. (6) If the result lands on an edge between components it is nudged 1e-4 m toward the polygon centre.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) src/esp/nav/PathFinder.cpp:64-87 (projectToPoly, polyPickExt {2,4,2} at :73), 1113-1186 (tryStep), 1362-1375 (wrappers).

10. **[high]** Detour moveAlongSurface (habitat fork): it searches polygons breadth-first from startRef, but only through portal edges within a circle centred at the midpoint of (projected start, end) with radius |start-end|/2 + 1 mm (MAX_STACK 48). If the end is inside a visited polygon (2-D test) it returns the end exactly. Otherwise, with allowSliding=true, it returns the closest point (2-D) on any visited wall edge to the end. With allowSliding=false it returns the start->end/wall intersection, and only traverses polygons the segment crosses.  
   *Evidence:* erikwijmans/recastnavigation 354591e (the habitat-sim v0.1.7 submodule pin, verified with git ls-tree) Detour/Source/DetourNavMeshQuery.cpp:2066-~2305 (moveAlongSurface); 2089 (MAX_STACK), 2110-2111 (search circle), 2136-2141 (end inside poly), 2190-2209 (no-sliding wall hit), 2210-2223 (sliding: closest point on wall edge), 2242-2256 (portal pruning).

11. **[high]** Endpoint-only semantics: there is no swept test. A step is not flagged if its target polygon is reachable inside the search circle, even if the straight segment clips a navmesh corner. Conversely, a target that is on the navmesh but on a different island, or not reachable within the circle, is flagged. With sliding, the agent ends on the boundary after the first contact (h = 0), so every later step whose target crosses the boundary is flagged.  
   *Evidence:* DetourNavMeshQuery.cpp:2110-2111, 2136-2141, 2242-2244; PathFinder.cpp:1130-1132.

12. **[high]** Sliding geometry: suppose the agent is at perpendicular distance h from a straight boundary and steps 0.25 m at angle theta to it. If 0.25*sin(theta) > h the result is the projection of the target onto the boundary, giving displacement sqrt((0.25 cos theta)^2 + h^2) < 0.25, so the step is flagged. If 0.25*sin(theta) <= h it is not flagged. Hitting a wall head-on moves only h. Exactly parallel motion with the target still inside is not flagged. In a concave corner the closest-wall-point rule always shortens the step.  
   *Evidence:* Derived from DetourNavMeshQuery.cpp:2210-2223 + object_controls.py:80-87.

13. **[high for the public code path; medium-high that the hidden havln_scoring package is identical (the image ships a 'patched Habitat core', export_cma_submission.py:49-50, whose diff is unknown)]** All collisions count, including walls and furniture. The HA-VLN trainer's TCR uses habitat-lab Collisions.count (all navmesh collisions) and reports val_seen 13.271 / val_unseen 22.352 (README). The toolkit's replay scorer reports 13.726 / 17.536 for CMA, the same magnitude. Counting only human contacts would need ~13-18 human hits per episode averaged over ALL episodes, which is implausible when only 11-38% of reference paths come near a human. The README/website/docs phrase TCR as a 'human-collision count' / '1.0 m proximity envelope', but no such filter exists in the public code.  
   *Evidence:* UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) HASimulator/metric.py:14-17 (TCR from metric['collisions']['count']); agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py:473-477 (collisions aggregated from count); README.md:145-148; roboworld2026/track2 toolkit @2d408b2 README.md:183-188, 192-197; JostarXiong/havln2-docs docs/api/evaluation_metrics.md:27-34 (line 30: '1.0-meter proximity envelope').

14. **[high]** Agent body is the habitat default: a cylinder, radius 0.1 m, height 1.5 m. HA-VLN only overrides SENSORS. habitat-sim recomputes the base navmesh at configure time only if radius/height differ from 0.1/1.5, so before humans are injected the shipped mp3d/<scan>/<scan>.navmesh is used. The agent is a point at navmesh level for collision purposes: height matters only through the navmesh build.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) habitat_sim/agent/agent.py:72-86; habitat_sim/simulator.py:199-234; habitat-lab v0.1.7 (d6ed1c0) habitat/config/default.py:250-262, habitat_simulator.py:245-257 (AGENT_0 copied into AgentConfiguration); HAVLNCE_task.yaml:10-11.

15. **[high]** Recast build used by recompute_navmesh: cellSize 0.05, cellHeight 0.2, walkableHeight ceil(1.5/0.2) = 8 cells = 1.6 m, walkableClimb floor(0.2/0.2) = 1 cell = 0.2 m, walkableRadius ceil(0.1/0.05) = 2 cells = 0.10 m (0.1f is exactly 2*0.05f), slope 45 deg, minRegionArea 20^2 = 400 cells = 1.0 m^2, maxEdgeLen 12/0.05 = 240 cells, maxSimplificationError 1.3 cells (6.5 cm), filterLowHangingObstacles/LedgeSpans/WalkableLowHeightSpans all on, then rcErodeWalkableArea.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) src/esp/nav/PathFinder.h:103-154 (setDefaults 137-154); src/esp/nav/PathFinder.cpp:342-455 (cfg 357-374, filters 429-434, erosion 455).

16. **[high]** How humans become obstacles. add_new_human_model adds the frame's GLB template with add_object_by_handle, sets translation and rotation (Euler X*Y*Z quaternion), then sets MotionType.STATIC (order matters: RigidBase ignores pose setters once STATIC). In _handle_signals HA-VLN then calls sim.recompute_navmesh(pathfinder, NavMeshSettings(defaults, radius 0.1, height 1.5), include_static_objects=True) and saves <RECOMPUTE_NAVMESH_PATH>/<scan>/<scan>_<fff>.navmesh, or loads that file if it already exists. C++ recomputeNavMesh joins the stage collision mesh with every STATIC object's collision (else render) mesh, transformed by its visual node's absolute transform x template scale, and rebuilds the navmesh from scratch.  
   *Evidence:* UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) HASimulator/environments.py:171-213 (STATIC at 208 after set_translation 203 / set_rotation 204), 111-147 (navmesh 129-144); habitat-sim v0.1.7 (856d4b0) src/esp/sim/Simulator.cpp:643-700 (STATIC loop 661-695); src/esp/physics/RigidBase.h:287-300; src/esp/physics/RigidObject.cpp:62-69.

17. **[high (mechanism); medium (exact footprint sizes, since HAPS GLBs were not inspected)]** Resulting human hole: floor cells under any body part between 0.2 m and 1.6 m above the floor become unwalkable (low-height-span filter). Parts <= 0.2 m (feet) are step-over-able. Body tops are removed as ledges. The footprint is then eroded outward by 0.10 m, with about +-1 raster cell and up to 6.5 cm contour simplification. Pockets that become isolated regions < 1 m^2 (e.g. between a human and a wall) vanish too. Effective 'collision radius' around the human silhouette is about 0.10 m, not 1 m.  
   *Evidence:* PathFinder.cpp:414-455 + Recast semantics of rcFilterWalkableLowHeightSpans/rcFilterLowHangingWalkableObstacles/rcFilterLedgeSpans/rcErodeWalkableArea/minRegionArea.

18. **[medium-high (template JSONs not inspected)]** Human translation = bounding-box centre of that frame's GLB. habitat-sim 0.1.7 shifts each object's visual origin to its bbox centre unless the template provides a COM (finalizeObject -> shiftOriginToBBCenter). Consistent with this, released human translations sit a median 0.842 m (p10 0.68, p90 0.96) above the floor of their keyed viewpoint, i.e. half a standing body height. Body footprints are therefore centred on the translation point, and any root motion baked into per-frame GLBs is cancelled.  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) src/esp/physics/RigidObject.cpp:30-54 (shiftOriginToBBCenter at :46; default KINEMATIC at :56-60); src/esp/physics/RigidBase.h:178-183 (shiftOrigin), :189 (shiftOriginToBBCenter); ObjectAttributes.cpp:52 (computeCOMFromShape default true); computed from human_motion.json vs HA-DE/connectivity viewpoint heights (scratchpad/a2_scripts/vp_offset2.py).

19. **[high]** Per-frame navmesh swap. HAVLNCEDaggerEnv.step (and HAVLNCEInferenceEnv.step) calls havlnce_tool._handle_signals() BEFORE habitat Env.step. If >= 1 signal is pending and total_signals_sent <= 120, it removes and re-adds all humans at frame (total_signals_sent-1) % 120 and swaps the pathfinder's navmesh to that frame's file. So the collision test of step k uses the navmesh swapped in at the start of step k. Exceptions in this block are logged and swallowed. The official CMA exporter uses HAVLNCEDaggerEnv.  
   *Evidence:* UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) agent/VLN-CE/vlnce_baselines/common/environments.py:48-75, 104-131; HASimulator/environments.py:111-147; roboworld2026/track2 toolkit @2d408b2 scripts/export_cma_submission.py:78, 125, 161.

20. **[high]** Step 1 of every episode ALWAYS refreshes humans and navmesh. reset() zeroes total_signals_sent and enqueues one signal (total = 1). The sender increments total only after a successful put into a maxsize-120 queue (a full queue raises queue.Full and does not count), and no drain happens before step 1. So total <= 120 at the first _handle_signals and frame f1 = total-1 is in [0,119]. This corrects the earlier claim (previous draft) that a slow scene reset leaves an episode human-free. The human-free base navmesh is active only between reset and the first step, or if _handle_signals throws.  
   *Evidence:* HASimulator/environments.py:41-42 (Queue(maxsize=120)), 49-58, 62-80, 96-109 (put(timeout=1) then +=1; Full -> pass), 111-128.

21. **[high (no GIL release); medium (quantitative dilation)]** The 'wall-clock' human clock is GIL-starved. The sender thread sleeps 0.1 s (releasing the GIL) but needs the GIL to enqueue. habitat-sim 0.1.7 bindings never release the GIL (no gil_scoped_release anywhere in src/), so no signals are produced while the main thread runs long C++ calls: scene load, first-time GLB loads in add_object, load_nav_mesh, recompute_navmesh (seconds), rendering. Frame cadence is therefore <= 10 Hz, roughly wall-clock in light steps and dilated by heavy C++ calls. A refresh happens at most once per step and frames never go backwards.  
   *Evidence:* grep of habitat-sim v0.1.7 (856d4b0) src/ and habitat_sim/ for gil_scoped_release/call_guard: 0 hits; SimBindings.cpp:285-287 (recompute_navmesh binding); HASimulator/environments.py:96-109; CPython GIL semantics (time.sleep releases; C extension calls hold unless released).

22. **[high (logic); low (actual scorer speed, unknown)]** Freeze: once total_signals_sent > 120 at a drain, the episode never refreshes again. Humans and navmesh stay at the LAST REFRESHED frame, which is 119 if steps are faster than 0.1 s, and can be a few frames lower when a step spans the 12-s boundary. Frames in force across an episode of N actions at tau s/step run roughly 0..min(119, N*tau/0.1): 100 actions at 20 ms/step stay within frames 0-20, at 120 ms/step they reach 119 and freeze.  
   *Evidence:* HASimulator/environments.py:120-128; arithmetic.

23. **[high]** Scene-change resets. habitat Env.reset -> HabitatSim.reconfigure: a new scene triggers sim.close() (C++ close drops physicsManager_, i.e. all objects, and the pathfinder) then reconfigure, which loads the scene's shipped .navmesh into a NEW PathFinder. The same scene only resets agents (objects and the last navmesh persist). HAVLNCE.reset() runs BEFORE Env.reset, so its frame-0 humans go into the previous scene (destroyed on a scene change) and the navmesh is not swapped. The toolkit exporter builds one env per (split, scan), so every reset there is same-scene.  
   *Evidence:* habitat-lab v0.1.7 (d6ed1c0) habitat/core/env.py:205-227, 289-298; habitat_simulator.py:360-370; habitat-sim v0.1.7 (856d4b0) habitat_sim/simulator.py:117-133, 199-213, 236-241; src/esp/sim/Simulator.cpp:53-77, 286-298; roboworld2026/track2 toolkit @2d408b2 scripts/export_cma_submission.py:211-212, 125-129.

24. **[high]** The agent start is placed unconditionally: Env.reset -> overwrite_sim_config sets AGENT_0.START_POSITION/ROTATION, and set_agent_state calls agent.set_state and always returns True, with no navigability check or snap. An episode can therefore start inside a human hole (or a removed <1 m^2 pocket) of the navmesh active at step 1.  
   *Evidence:* habitat-lab v0.1.7 (d6ed1c0) habitat/tasks/nav/nav.py:51-66 (merge_sim_episode_config); habitat_simulator.py:311-323, 485-521; habitat-sim v0.1.7 (856d4b0) habitat_sim/simulator.py:300-314.

25. **[high (mechanism); medium (empirical cross-check: the oracle that produced collision_num is not documented)]** What happens from inside a hole. A MOVE_FORWARD projects the start to the nearest boundary point p and runs moveAlongSurface(p -> target) inside the circle around (p+target)/2. If the target lands outside the hole and is reachable it returns the target, so the displacement is exactly 0.25 m and the step is NOT flagged. If the target is still in the hole it returns the closest visited wall point to the target, flagged iff that point is < 0.24998 m from the true start. From the centre of a hole of radius > 0.25 m this LENGTHENS the move (not flagged); stepping inward from near the edge is typically flagged. A first TURN instead snaps to p with collided=False. Released-data check: in train, oracle trajectories starting within 5 cm of a human with MOVE_FORWARD as the first action had collision_num = 0 in 21/24 cases.  
   *Evidence:* PathFinder.cpp:1121-1153; DetourNavMeshQuery.cpp:2110-2141, 2210-2223; object_controls.py:75-87; cross-tab computed this session (R2R_VLNCE_v1-2 train_gt.json.gz first action x human_motion.json x collision_num_train.json).

26. **[high]** Human motion: 749 humans in 72 released scans, all with 120 frames, no None frames. 560/749 have constant translation (only limbs animate). Horizontal swept extent: median 0.00, mean 0.203, p90 0.80, p99 1.79, max 3.47 m; 18.7% > 0.5 m, 6.3% > 1 m. Per-frame translation step: max 0.035 m (<= 0.35 m/s at 10 frames/s). Euler rotation constant across frames for all 749. 6-19 humans per scan (median 10).  
   *Evidence:* Computed with python -I from HA-VLN/Data/Multi-Human-Annotations/human_motion.json (scratchpad/a2_scripts/human_stats.py).

27. **[high]** Episode-start proximity (start_position vs any human translation at any frame, same floor). val_unseen: 63/75/99/123/159/225 of 1,839 within 0.2/0.3/0.4/0.5/0.75/1.0 m (frame 0 only: 42/51/75/96/126/198). val_seen: 30/39/42/51/63/78 of 778. train: 345/408/486/603/831/1,086 of 10,819. Goals within 0.3 m of a human: val_unseen 54, val_seen 27, train 448. Reference paths (0.1 m sampled) within 0.3 m of a human: val_unseen 699 (38%), val_seen 261 (34%), train 3,246 (30%); passing exactly (<5 cm) over a human-occupied intermediate viewpoint: val_unseen 201, val_seen 87, train 1,130.  
   *Evidence:* Computed this session from Discrete-Continuous-VLN R2R_VLNCE_v1-2_preprocessed (same 10,819/778/1,839/3,408 ids as collision_num_*.json, verified) x human_motion.json (scratchpad/a2_scripts/human_stats.py, vp_offset2.py).

28. **[high (statistics); medium (interpretation of how cn was generated)]** collision_num is driven by humans at or near the GOAL. P(cn>0) is 0.93 (train n=300), 0.83 (val_seen n=18) and 1.00 (val_unseen n=21) when a human translation is within 5 cm of the goal, and 0.003 (train n=5,816) when no human is within 3 m of the goal. Conversely, 98% of cn>0 episodes (train 824, val_unseen 159) have a human within 3 m of the goal, versus 40-45% of cn=0 episodes. Humans on an intermediate viewpoint of the reference path give cn>0 in only 10-19%, and humans on the start in 0-9%. This matches the docs' 'Oracle baseline scene collisions / unavoidable collisions': a human-aware oracle detours around mid-path humans but must collide to reach a human-occupied goal. TCR = max(0, count - cn), so cn is a per-episode collision allowance (test: 237/3,408 episodes, max 3).  
   *Evidence:* Computed this session (scratchpad/a2_scripts/goal_dist_cn.py, vp_offset2.py); HA-VLN HASimulator/metric.py:15; havln2-docs docs/quick_start/integration.md:140 and docs/api/evaluation_metrics.md:30; A1 finding (cn identical within each 3-instruction trajectory block).

29. **[high]** Look actions use habitat-lab action-space v1 semantics (look_up/look_down, TILT_ANGLE default 15 deg, no pitch constraint). The public HA-VLN configs use v0 with 4 actions; the six-action vocabulary comes from the image's six_action_task.yaml. In either case they are not body actions and cannot collide.  
   *Evidence:* habitat-lab v0.1.7 (d6ed1c0) habitat/sims/habitat_simulator/actions.py:19-24, 92-133; habitat/tasks/nav/nav.py:1032-1047; habitat/config/default.py:218; roboworld2026/track2 toolkit @2d408b2 scripts/export_cma_submission.py:14, 123-124, 219.

30. **[high]** The DISTANCE_TO_HUMAN measure (in HA-VLN's eval MEASUREMENTS, not in the exporter, which sets MEASUREMENTS = []) executes a filtered MOVE_FORWARD on the agent for every human at every update and restores it with agent.set_state(state). That reset_sensors=True undoes LOOK tilts, but it never touches _prev_sim_obs, so it cannot change collisions.count.  
   *Evidence:* UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) HASimulator/measures.py:49-97; habitat-sim v0.1.7 (856d4b0) habitat_sim/agent/agent.py:203-242; roboworld2026/track2 toolkit @2d408b2 scripts/export_cma_submission.py:118.

31. **[high]** PathFinder.is_navigable accepts points within 1 cm (XZ) of the navmesh and +-0.5 m in y, so it is too lax to verify the 0.02 mm collision tolerance. distance_to_closest_obstacle is the distance to the nearest navmesh wall edge (findDistanceToWall), i.e. clearance relative to the scoring boundary, not to geometry. load_nav_mesh returns False on failure before replacing the current mesh (HA-VLN ignores the return value).  
   *Evidence:* habitat-sim v0.1.7 (856d4b0) src/esp/nav/PathFinder.cpp:1241-1258, 1214-1239, 793-830.

32. **[high]** Template and frame ordering is deterministic across machines: HA-VLN sorts category directories (os.listdir + sorted), and habitat-sim loads each category's per-frame JSON configs with Directory::list(SortAscending), asserting 120 templates per category. Per-frame navmeshes are deterministic functions of (scene GLB, HAPS GLBs/configs, human_motion.json, Recast settings), so participants can regenerate them exactly in the official image.  
   *Evidence:* UWMILab/HA-VLN (HEAD 3967752; HASimulator/* and vlnce_baselines/common/environments.py are unchanged vs the toolkit-pinned f46f936, verified with git diff) HASimulator/environments.py:215-233; habitat-sim v0.1.7 (856d4b0) src/esp/metadata/managers/AttributesManagerBase.h:204-243 (216).

## Key numbers

| What | Value | Source |
|---|---|---|
| EPS in collided test (squared metres) | 1e-5 | habitat_sim/agent/controls/object_controls.py:19 |
| Min filtered displacement for a 0.25 m step to NOT be flagged | 0.249980 m (shortening tolerance 2.0e-5 m) | sqrt(0.0625-1e-5); object_controls.py:80-87 |
| Forward step / turn / tilt | 0.25 m / 15 deg / 15 deg (TILT_ANGLE default) | HAVLNCE_task.yaml:12-13; habitat-lab default.py:218 |
| Agent radius / height | 0.1 m / 1.5 m (cylinder) | habitat_sim/agent/agent.py:74-75,86; habitat-lab default.py:251-252 |
| Navmesh erosion from geometry | 2 cells = 0.10 m | PathFinder.cpp:364,455; PathFinder.h:138,141 |
| walkableHeight / walkableClimb | 8 cells = 1.6 m / 1 cell = 0.2 m | PathFinder.cpp:362-363 |
| Contour simplification max error | 1.3 cells = 6.5 cm | PathFinder.h:147; PathFinder.cpp:366 |
| Minimum island/region area kept | 400 cells = 1.0 m^2 | PathFinder.h:144; PathFinder.cpp:367-368 |
| findNearestPoly half-extents in tryStep | {2, 4, 2} m | PathFinder.cpp:73 |
| moveAlongSurface search circle radius | |start-end|/2 + 0.001 m (= 0.126 m for a full step) | DetourNavMeshQuery.cpp:2110-2111 |
| Thin-wall nudge | 1e-4 m | PathFinder.cpp:1179 |
| is_navigable XZ tolerance | 1e-2 m | PathFinder.cpp:1252-1255 |
| Human clock period / queue size / refresh horizon | 0.1 s sleep / maxsize 120 / total_signals_sent <= 120 (~12 s of GIL-available time) | HASimulator/environments.py:42,109,124 |
| Frame in force at step 1 | (signals since reset) - 1, always in [0,119]; refresh guaranteed | HASimulator/environments.py:49-58,96-128 |
| Humans / scans / frames (released) | 749 / 72 / 120 | human_motion.json (this session) |
| Humans with constant translation | 560 of 749 (74.8%) | human_motion.json (this session) |
| Human horizontal swept extent over 120 frames | median 0.00, mean 0.203, p90 0.80, p99 1.79, max 3.47 m; 18.7% > 0.5 m; 6.3% > 1 m | human_motion.json (this session) |
| Max per-frame human translation step | 0.035 m | human_motion.json (this session) |
| Human translation height above floor | median 0.842 m (p10 0.68, p90 0.96): bbox centre | human_motion.json x HA-DE connectivity (this session) |
| Humans within 5 cm of their keyed viewpoint | 25.0% (median offset 1.06 m) | human_motion.json x connectivity (this session) |
| val_unseen starts within 0.3 / 0.5 / 1.0 m of a human (any frame) | 75 / 123 / 225 of 1,839 | this session |
| val_seen starts within 0.3 / 0.5 / 1.0 m of a human (any frame) | 39 / 51 / 78 of 778 | this session |
| val_unseen reference paths within 0.3 m of a human | 699 of 1,839 (38%) | this session |
| val_unseen reference paths over a human-occupied intermediate viewpoint (<5 cm) | 201 (cn>0 in 19.4%) | this session |
| P(cn>0 | human within 5 cm of goal) | train 0.93 (n=300), val_seen 0.83 (n=18), val_unseen 1.00 (n=21) | this session |
| P(cn>0 | nearest human > 3 m from goal) | train 0.003 (n=5,816) | this session |
| Fraction of cn>0 episodes with a human within 3 m of the goal | train 0.98, val_seen 0.80, val_unseen 0.98 | this session |
| collision_num nonzero episodes | train 824/10,819; val_seen 60/778; val_unseen 159/1,839; test 237/3,408; max 4 | Data/HA-R2R-tools/collision_num_*.json |
| CMA replay TCR (collisions above cn per episode) | 13.726 val_seen, 17.536 val_unseen | track2 README.md:183-186 |
| CMA trainer-reported TCR (habitat Collisions.count based) | 13.271 val_seen, 22.352 val_unseen | HA-VLN README.md:145-148 |
| Success distance | 3.0 m (Euclidean DistanceToGoal override registered by HASimulator.measures) | HAVLNCE_task.yaml:27,47-48; HASimulator/measures.py:100-155; habitat-lab registry.py:50-60 |

## Answers to the six brief questions

1. **collided iff the navmesh-filtered end differs from the requested one?** Not exactly. It is a *distance* test: flagged iff |f-start|^2 + 1e-5 < |end-start|^2. For a 0.25 m step that means displacement < 0.249980 m (shortened by more than 0.02 mm). A displaced but equally long or longer end (vertical snapping, the 1e-4 nudge sideways, an off-mesh start projected outward) is not flagged. [high]
2. **TURN/LOOK/STOP never set collided?** Correct. Turns run the filter with zero requested displacement, so the test is impossible (but they can snap an off-mesh agent onto the navmesh). LOOK_* skip the filter. STOP drops the key. [high]
3. **Sliding along a wall at an angle counts every step?** Yes. Whenever the 0.25 m target crosses the boundary, the result is the closest boundary point, which is strictly shorter. Only exactly parallel motion with the target still inside escapes. [high]
4. **Radius/height and human obstacles?** 0.1 m / 1.5 m cylinder. HA-VLN's per-frame recompute joins STATIC human meshes into the stage mesh, so a human collision is literally a navmesh collision with the human silhouette (0.2-1.6 m above the floor) inflated by about 0.10 m. [high]
5. **Navmesh swapped per animation frame?** Yes: at every step with a pending clock signal while total_signals_sent <= 120, before the sim step. Step 1 always refreshes, frames are monotone in 0..119 and GIL-dilated, and the episode freezes at the last refreshed frame. Paths planned on the human-free navmesh hit human holes, and may also differ near walls because the whole navmesh is rebuilt. [high]
6. **Collisions when starting inside a human?** Possible but direction dependent: a first MOVE_FORWARD is flagged iff its filtered point lands < 0.24998 m from the true start. A first TURN always escapes for free (snap to nearest boundary). Starts within 0.3 m of a human: val_unseen 75/1,839, val_seen 39/778. [high mechanism / medium empirics]

## Implications (inferences)

- Zero collisions is a pure geometry problem. Only MOVE_FORWARD steps can count; each is judged solely on whether its 0.25 m target is reachable inside the navmesh in force at that step. Turns, looks, STOP, standing still while a human walks 'through' the agent, and the number of steps are all free.
- Wall/furniture contact is penalised exactly like human contact (it is the same navmesh test), so human avoidance alone is not enough. The CMA baseline's TCR of ~14-18 is mostly wall sliding.
- Planning on the shipped human-free MP3D navmesh is unsafe. 38% of val_unseen reference paths pass within 0.3 m of a human and 11% pass straight over a human-occupied viewpoint. In addition, every per-frame navmesh is a full Recast rebuild with 0.1.7 defaults, so boundaries can differ from the shipped navmesh even far from humans. Plan on the scorer's own recomputed navmeshes.
- The frame in force at each step is unknowable for us (scorer speed, GIL dilation). It is monotone non-decreasing and anywhere in 0..119, so the only robust target is the intersection of all 120 per-frame navmeshes, plus the human-free recompute and the shipped navmesh for safety.
- With 560/749 humans translation-static, the union-of-frames hole is barely larger than a single-frame hole for most humans. The 47 humans that sweep more than 1 m are the ones that may close corridors; check those episodes explicitly.
- Because human translations are bbox centres, distance-to-translation is a meaningful proxy where exact meshes are unavailable. A standing body half-width (~0.25-0.3 m) + 0.10 m erosion + raster/contour slack means a ~0.45 m radius is the nominal hole. Keeping >= 0.75 m from every translation (and from the swept segment of moving humans) is a conservative proxy; 1.0 m (the paper's envelope) is very safe.
- collision_num leaks goal information. A test episode with cn>0 (237 episodes = 79 trajectories) has a human within 3 m of its goal with ~98% probability, and a human standing ON a candidate goal viewpoint almost implies cn>0 (P(cn=0 | human on goal) ~ 0.2% in train). Feed this to the goal-inference team (A1/goal topics). It also grants an allowance: SR needs count <= cn, so those episodes tolerate cn collisions, but plan for 0 anyway.
- Verification must be exact (0.02 mm tolerance), but it is cheap: PathFinder.try_step needs no rendering, and the scorer's x,z trajectory is deterministic when no step is filtered. 121-122 navmeshes x 3,408 episodes x ~100 steps is ~4e7 try_step calls, i.e. CPU-minutes on a farm.
- If the Phase-2 bundle does not release the 18 test scans' human_motion entries, test collisions cannot be verified locally. Clearance from walls is still fully controllable; human avoidance would have to rely on priors: the HA-VLN 1.0 annotations (70 humans across all 18 test scans; only 248/749 = 33% of 2.0 humans sit on 1.0-annotated viewpoints in released scans), instruction mentions, cn>0-goal proximity, and maximal-clearance routing.

## Engineering rules for guaranteeing collisions.count == 0 (and Phase-1 probes)

- RULE 0 (what counts): count += 1 iff a MOVE_FORWARD's filtered displacement < 0.249980 m on the navmesh active at that step. Design everything around keeping each forward TARGET strictly inside the active navmesh, and the WHOLE 0.25 m segment inside (this also keeps you robust if the image used ALLOW_SLIDING=False). Never use sliding or corner cutting.
- RULE 1 (exact replica navmeshes): inside the official image (ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f...), for every scan use the scorer's own code path (HAVLNCE.refresh_human_model(f) then recompute_navmesh(pathfinder, defaults + radius 0.1 + height 1.5, include_static_objects=True)) to build <scan>_000..119.navmesh. Also build a human-free recompute and keep the shipped <scan>.navmesh: 122 candidates per scan. Record sha256s, and check that the image's /app/config/challenge_submission.yaml has ALLOW_SLIDING True, FORWARD_STEP_SIZE 0.25, TURN_ANGLE 15 and agent radius/height 0.1/1.5.
- RULE 2 (planning map = intersection): rasterise 'inside navmesh' on a <= 2.5 cm grid for all 122 candidates, using an exact test (snap_point XZ distance < 1e-4 m, or a polygon point-in-poly, NOT is_navigable's 1 cm tolerance). AND them together and compute clearance = distance to the union boundary. Equivalent shortcut: add all 120 frames of every human as STATIC objects at once and recompute at agent_radius 0.25 (fallback 0.20, 0.15) to get a swept-volume navmesh with 0.15/0.10/0.05 m clearance beyond the scoring boundary.
- RULE 3 (clearance policy): require clearance >= 0.15 m for every rest position and every point of every forward segment (sampled every <= 2.5 cm). Relax to >= 0.05 m only where the 0.15 m map is disconnected (narrow doors: a 0.7 m door leaves only a 0.5 m navmesh corridor at r = 0.1). Never go below 0.05 m, which covers float/structure drift and unknown scorer-side differences. Add a clearance-weighted cost so routes stay centred; path length is unscored apart from the 500-action cap.
- RULE 4 (lattice realities): headings are quantised to 15 deg relative to the start yaw, so a corridor whose direction is between headings drifts by up to 0.25*sin(7.5 deg) = 3.3 cm per step. Plan in (x, z, theta) with exact float32 kinematics, and zig-zag (turn, forward, turn) in long narrow corridors rather than assuming ideal alignment.
- RULE 5 (verification gate): accept an action sequence only if kinematic replay with habitat_sim.nav.PathFinder.try_step against ALL 122 candidates gives (a) 0 flagged steps, (b) 0 position changes on TURN/LOOK steps (no snaps), and (c) an identical final x,z. Emulate object_controls.py:68-89 exactly: start = position; end = start + R(yaw)*(0,0,-0.25) in float32; f = try_step(start,end); position = end + (f - end); flag if |f-start|^2 + 1e-5 < |end-start|^2; turns: yaw += -15 deg, f = try_step(p,p). Then run 2-3 end-to-end replays in the official HAVLNCEDaggerEnv with the real wall-clock thread under different CPU loads (or the image's havln-score-phase1) as an integration check.
- RULE 6 (starts inside or near holes): for each episode test whether the start is off-mesh, or within the clearance margin, on ANY candidate. If so, make action 1 a TURN (it cannot be flagged and it snaps the agent onto the frame-specific boundary). Compute the snapped start for every candidate, pick headings whose first forward targets land outside all holes, and verify the remaining sequence from every snapped start (branching per candidate). Never begin with an inward MOVE_FORWARD. Expect this for ~4-7% of episodes (val_unseen: 75 starts within 0.3 m, 123 within 0.5 m of a human).
- RULE 7 (goals near humans): stop >= 0.5 m outside any hole on any frame. Success is < 3 m Euclidean at STOP, so there is no need to approach human-occupied goals. Always end with STOP within 500 actions.
- RULE 8 (no timing exploits): do not depend on which frame is active, on the scorer's speed, or on 'waiting' with LOOK/TURN padding. Frames come from GIL-dilated wall-clock time, and padding cannot reliably reach the freeze within 500 actions. Treat frames as adversarial within [0,119].
- RULE 9 (moving humans): for the ~19% of humans that sweep > 0.5 m, inspect the intersection map for corridor closures. If a route is closed in the intersection but open in most frames, prefer a detour. If no detour exists, minimise the number of forward steps inside the swept band and count the episode as at-risk (and check whether its cn > 0 allowance covers it).
- RULE 10 (test-human uncertainty): if test human_motion is withheld, (i) still enforce rules 2-5 against walls on the human-free recompute; (ii) keep >= 1.0 m from every viewpoint that hosts a human in HA-VLN 1.0 annotations (human_motion_text.json; 70 humans in test scans) and from humans implied by the instruction near the predicted route; (iii) prefer maximum-clearance routes. Re-run everything the moment the Phase-2 bundle provides test human placements.
- PHASE-1 PROBE A (confirm wall counting): on val_seen, submit sequences verified locally to produce exactly ONE wall bump >= 3 m from any human, then STOP. Predicted official TCR ~ mean(max(0, 1 - cn)) ~ 0.92 and CR ~ 1.0 if walls count. TCR ~ 0 would mean the hidden scorer filters to human contacts, in which case relax wall margins.
- PHASE-1 PROBE B (optional, frame timing): pick val episodes where a walking human crosses an otherwise clear corridor and schedule the crossing at different step indices across episodes. Which episodes collide reveals the scorer's step-to-frame rate. Use it only for risk estimates, never to exploit.

## Corrections to earlier claims

- Previous draft of this file: 'in a new-scene episode whose reset+scene load exceeds 12 s humans are never injected'. Wrong. The queue (maxsize 120) caps total_signals_sent at 120 until the first drain, so step 1 always refreshes at frame <= 119. GIL starvation during the C++ scene load means even fewer signals accumulate.
- Previous draft: 'a first MOVE_FORWARD from inside a hole is almost surely flagged'. Too strong. It is flagged only if the filtered point lands < 0.24998 m from the true start, which depends on direction. Outward steps whose target leaves the hole, and steps from the centre of a large hole, are not flagged. Empirically, 21/24 oracle trajectories starting on a human with a forward first action have cn = 0.
- Previous draft: 'collision_num correlates only weakly with human proximity'. Refined: it is dominated by humans at or near the GOAL (P(cn>0) = 0.93-1.0 for human-on-goal; 98% of cn>0 episodes have a human within 3 m of the goal). Path proximity is a weak predictor because the oracle detours.
- CONTEXT fact 4 nuance: the 'wall-clock' clock only ticks when the GIL is free (habitat-sim never releases it), and the freeze is at the LAST REFRESHED frame (<= 119, may be lower). Otherwise CONTEXT facts 3-4 are confirmed.
- Toolkit README line numbers moved: the CMA table is now README.md:183-188, the metric table 192-197, FAQ Q4 268-270, Q5 274-277.

## Open questions

- Does the hidden havln_scoring replay count habitat-lab Collisions.count (all navmesh contacts) exactly as HASimulator/metric.py does? Evidence strongly says yes (trainer and replay TCR magnitudes agree); confirm with Probe A.
- What does the image's 'patched Habitat core' change? (export_cma_submission.py:49-50 and the fingerprint of habitat_simulator.py at :218.) Diff it against habitat-lab v0.1.7 in bring-up; collision semantics are assumed unchanged.
- Contents of /app/config/challenge_submission.yaml and six_action_task.yaml: ALLOW_SLIDING, step sizes, MEASUREMENTS (is DISTANCE_TO_HUMAN included?), sensor resolution (affects per-step time and hence frames).
- Official scorer per-step time and whether one env serves several scans (scene-change resets): this determines which frames are active. Irrelevant if Rule 2 holds, but it matters for risk estimates on at-risk episodes.
- Is the organisers' recompute_navmesh cache built from the same HAPS2_0 assets / human_motion.json we have (the cache key is only scan + frame)? A stale cache would desynchronise holes from rendered humans; margins of >= 0.05 m do not cover gross mismatches.
- Do the shipped MP3D <scan>.navmesh files match a 0.1.7-default recompute without humans? Measure the symmetric difference per scan; it only matters for the brief window before step 1 or if _handle_signals fails.
- Exact HAPS 2.0 footprints (bbox per frame, template COM/scale): compute from the GLBs to calibrate the distance proxy of Rule 10.
- Phase-2 bundle: will test human placements (human_motion entries for the 18 test scans) be released? Without them, test human collisions cannot be verified offline.
- How exactly was collision_num generated (oracle type, frame timing)? The goal-proximity signal is strong, but the generating process is undocumented.

## Sources

- https://github.com/facebookresearch/habitat-sim (tag v0.1.7, 856d4b0): habitat_sim/agent/controls/object_controls.py, default_controls.py, habitat_sim/agent/agent.py, habitat_sim/simulator.py, src/esp/agent/Agent.cpp, src/esp/nav/PathFinder.{h,cpp}, src/esp/sim/Simulator.cpp, src/esp/physics/{RigidBase.h,RigidObject.cpp,PhysicsManager.cpp}, src/esp/assets/ResourceManager.cpp, src/esp/metadata/managers/AttributesManagerBase.h, src/esp/bindings/{SimBindings,ShortestPathBindings}.cpp
- https://github.com/facebookresearch/habitat-lab (tag v0.1.7, d6ed1c0): habitat/sims/habitat_simulator/{habitat_simulator,actions}.py, habitat/tasks/nav/nav.py, habitat/core/{env,embodied_task,registry}.py, habitat/config/default.py
- https://github.com/erikwijmans/recastnavigation commit 354591e10a772b8057e42a4f9de701155b9aaa02: Detour/Source/DetourNavMeshQuery.cpp (moveAlongSurface)
- https://raw.githubusercontent.com/mosra/magnum/46f4518eb6ca121dfa3da2884dc5c8ad5417e97b/src/Magnum/Math/Vector.h; https://raw.githubusercontent.com/mosra/magnum-bindings/52f2073ff9c399ad2120085c9ca6f6a021fdafc1/src/python/magnum/math.vector.h
- https://github.com/UWMILab/HA-VLN (HEAD 3967752; pinned f46f936): HASimulator/{environments,measures,metric}.py, HASimulator/config/*.yaml, agent/VLN-CE/vlnce_baselines/common/{environments,base_il_trainer}.py, agent/VLN-CE/habitat_extensions/{__init__,measures}.py, README.md, Data/Multi-Human-Annotations/human_motion.json, Data/HA-R2R-tools/collision_num_*.json, HASimulator/HA-DE/{connectivity,human-viewpoint_annotation/human_motion_text.json}
- https://github.com/roboworld2026/track2 (@2d408b2, and initial commit 2daf3dd README: havln-score-phase1, 'Humans move in real time, so repeat runs can differ', writable recompute_navmesh cache): README.md, scripts/export_cma_submission.py, scripts/resources.json, tests/test_onboarding.py
- https://github.com/JostarXiong/havln2-docs (@55c79eb): docs/api/{evaluation_metrics,collision_checks,scene_updates}.md, docs/quick_start/integration.md
- https://github.com/roboworld2026/roboworld2026.github.io track2.html:128-134 (success requires no collisions; TCR 'in human-occupied zones')
- Local episodes: Discrete-Continuous-VLN data/datasets/R2R_VLNCE_v1-2_preprocessed/{train,val_seen,val_unseen,test}/*.json.gz (+ *_gt.json.gz); the ids match HA-R2R collision_num files 1:1
- Analysis scripts (this session): /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a2_scripts/{human_stats.py,cn_vs_gt.py,vp_offset2.py,goal_dist_cn.py}
- Note: the WebSearch budget for this run was exhausted (shared limit), so no new web lookups were made; all claims rest on code and data read locally.

## Appendix A: exact kinematic emulator (for the verification gate)

```python
# inputs: pf = habitat_sim.nav.PathFinder(); pf.load_nav_mesh(path)   (one per candidate navmesh)
import numpy as np, magnum as mn
def replay(pf, start_pos, start_quat_xyzw, actions, step=0.25, turn=15.0):
    p = mn.Vector3(*start_pos)                       # float32, exactly like the scene node
    yaw_q = mn.Quaternion(mn.Vector3(*start_quat_xyzw[:3]), start_quat_xyzw[3])
    flags, snaps = [], []
    for a in actions:
        if a == 'STOP': break
        if a in ('LOOK_UP', 'LOOK_DOWN'): flags.append(False); continue      # sensors only
        if a in ('TURN_LEFT', 'TURN_RIGHT'):
            yaw_q = (yaw_q * mn.Quaternion.rotation(mn.Deg(turn if a == 'TURN_LEFT' else -turn), mn.Vector3.y_axis())).normalized()
            end = p
        else:  # MOVE_FORWARD: translate along the body's -Z axis
            end = p + yaw_q.transform_vector(mn.Vector3(0, 0, -step))
        f = pf.try_step(p, end)                      # sliding version (ALLOW_SLIDING=True)
        new_p = end + (f - end)
        collided = ((f - p).dot() + 1e-5) < (end - p).dot()
        snaps.append(a.startswith('TURN') and (abs(new_p.x - p.x) > 1e-6 or abs(new_p.z - p.z) > 1e-6))
        flags.append(collided); p = new_p
    return p, flags, snaps   # accept iff no flags and no snaps on every candidate navmesh
```
Kinematics note: habitat-sim SceneNode = Magnum Object<TranslationRotationScalingTransformation3D> (src/esp/gfx/magnum.h:21-25); _move_along takes the world-space local-Z column of the node transform times -0.25 and translates in parent space (default_controls.py:31-33), i.e. a horizontal 0.25 m move along the current heading (the body node only carries yaw; LOOK tilts rotate sensor nodes). Validate this emulator against the real Simulator (same image) on >= 1,000 random sequences before trusting it; any mismatch marks the trajectory fragile.

## Appendix B: frame timing model (HASimulator/environments.py)

```
reset(): clear queue; total=0; remove humans; put() -> total=1; add frame-0 humans into CURRENT scene (no navmesh swap)
thread : loop { put(timeout=1) -> total+=1 (only on success; queue maxsize 120); sleep(0.1) }   # needs the GIL to run
step k : drain queue; if drained>0 and total<=120: frame=(total-1)%120; re-add humans; swap navmesh   # before sim.step
=> step 1 always refreshes (total<=120 guaranteed); frames monotone; once total>120 at a drain -> frozen at last refreshed frame
=> GIL held by every habitat-sim C++ call (no gil_scoped_release in 0.1.7) -> clock pauses during scene load / GLB load / navmesh recompute
```
