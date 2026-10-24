# W2 — Safety executor (zero-collision motion from perceived geometry)

Goal: given a target waypoint/goal belief and the agent's own depth+pose history, emit MOVE_FORWARD/TURN actions that never
trigger a navmesh collision, within budget, ending with STOP.

Facts to design against (see `research/A2-collision-semantics-habitat017.md`):
- Only MOVE_FORWARD collides; a step is flagged if the filtered displacement is shorter than 0.24998 m. Sliding along a wall
  flags EVERY step. Turns, looks, STOP are free. A turn re-snaps an off-navmesh agent for free → first action at a crowded start
  should be a TURN.
- Agent radius 0.1 m, height 1.5 m; the scoring navmesh is already eroded 0.10 m; doors are 0.7–0.9 m wide.
- Humans are static meshes per frame; horizontal drift median 0.0 m, p90 0.8 m, max 3.5 m; 0 rotation change; 4–6 % of starts
  are within 0.5 m of a human.

Compliant inputs only: depth (256×256, HFOV 90), RGB, GPS+compass. Build a local 2-D occupancy grid (5 cm cells) by projecting
depth to the floor plane using the known camera height (1.5 m) and pose; mark cells with surfaces between 0.2 m and 1.6 m above
floor as blocked; inflate by 0.25–0.35 m (adaptive: relax to 0.20 m only when a doorway is otherwise closed); people (from W3
segmentation or depth blobs) get a 0.6 m radius. Unknown space is blocked until observed; use TURNs to observe before moving.

Motion (see `research/A5-*`): lattice A* over (position, heading) with exact step semantics (0.25 m along −Z of the quantised
heading; θ = 2·atan2(q_y, q_w)), cost = actions + clearance penalty, every forward target checked at midpoint and endpoint; plan in
3-D (13–24 % of episodes change floor). Even the perfect-goal shortest-path follower collides in 18–26 % of episodes by touching
corners, so clearance is the whole game. Legacy alternative: plan on the grid (A*/Theta*), simplify to waypoints, quantise headings to 15° multiples, align before straight runs, and
before each MOVE_FORWARD check that the full 0.25 m segment stays ≥ margin from blocked cells. After each forward, compare GPS
delta with 0.25 m: if shorter, record a contact, back off (TURN, re-plan) — this is allowed feedback. Keep ≥ 60 actions in reserve.

Stop logic: given a goal belief (point or distribution from W4/W5), stop at the reachable point maximising P(Euclidean ≤ 3 m); stopping between two candidates 3–5.5 m apart is worth ≈ 4–5 SR (A5). First action at a crowded start is a TURN (free re-snap); stop within 0.2 m of the chosen point.

Oracle harness (eval only, in `oracle/`): run the executor towards the GT goal on val_unseen with humans rendered; target SR ≥ 0.95,
TCR = 0 under the 4 human-timing regimes of the W1 scorer. Report failures by category (door, stairs, human-at-start, map error).

Unit tests (no Habitat): synthetic box/corridor scenes; heading quantisation drift; door-passing with 0.8 m gaps; budget guard.
Report: SR/TCR table per regime; failure taxonomy with episode ids; action-count histogram.
