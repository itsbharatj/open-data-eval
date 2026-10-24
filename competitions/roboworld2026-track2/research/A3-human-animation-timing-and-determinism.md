# A3 — Human animation timing and official-replay determinism (HA-VLN 2.0 / RoboWorld 2026 Track 2)

Topic id: `A3-human-animation-timing-and-determinism` · Date: 2026-10-24 · Author: research agent A3

Paths below: `EXT=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`,
`A3=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a3` (my analysis scripts).
WebSearch budget was exhausted mid-task, so I verified everything from code and data, not from new web sources.

## Summary (decision-relevant)

1. **The human frame follows a Python thread's tick count, not pure wall time.** The frame at step k is `total_signals_sent − 1`, read when `_handle_signals()` runs just before step k. `total_signals_sent` counts how many ticks the sender thread has completed since `HAVLNCE.reset()`. It goes up by about 1 every 0.1 s, but only while the sender thread can get the Python GIL. habitat-sim 0.1.7's pybind11 bindings never release the GIL (I grepped `src/esp/bindings`: no `gil_scoped_release`). So time the main thread spends inside heavy C++ calls (navmesh recompute, GLB loading, scene loading) does **not** advance the animation. Updates stop for good once the counter passes 120 (the 0..119 frames never loop). I verified this with a faithful re-implementation of the code (`$A3/clock_sim.py`).
2. **Under official fast replay, humans most likely sit in early frames.** With a warm cache at ~5 ms per step, a 500-action episode only reaches frame ~26 (measured), and typical 60–150-action episodes stay at frames ≤ ~10. Slow stepping (≥0.1 s per step, e.g. a VLM in the loop) runs through all frames and then freezes. The freeze frame is **not necessarily 119**: it is the last frame refreshed while the counter was ≤120. I measured 117 at 0.3 s/step and 110 at 1 s/step. A cold navmesh cache (each new frame triggers a GIL-holding `recompute_navmesh`) makes the animation **step-locked**: frame ≈ step index (measured 0,1,2,…,11 over 12 steps that took 25 s). The scorer's first episode per scan in a fresh process probably behaves the same way, because GLBs load lazily.
3. **The `maxsize=120` queue caps the counter at 120 when nothing drains it.** So the first step after a long stall (≥12 s with the GIL free) always shows **frame 119**. I measured this 6/6 times. This contradicts A2's claim that humans are "never injected" after a slow reset. Step 1 of every episode always refreshes the humans, because `reset()` enqueues one signal.
4. **Human motion is small, slow and simple.** 560/749 humans (75%) never move horizontally. 140 (18.7%) sweep >0.5 m and 47 (6.3%) sweep >1 m; the maximum is 3.47 m. Peak speed is 0.35 m/s. Rotation is constant for every human in every frame. Motion is piecewise-linear in ~20-frame segments. 74% of movers walk within 20° of their facing direction (yaw applied to local +Z). Translations sit at pelvis height (median 0.74 m above the local floor).
5. **Robustness is cheap.** Treating each human as the union of all 120 frames adds only about 29% to the blocked area (discs of r = 0.45 m), and all of that comes from the 189 humans that move. Against R2R-CE reference paths, 39% of val_unseen episodes pass within 0.45 m of a human root at some frame, but only **8.0% (147/1839) are timing-sensitive**. The rest conflict at every frame (static humans standing on the path) or never conflict.
6. **Recommendation.** Certify every action sequence as collision-free on **all 120 per-frame navmeshes plus the base navmesh, at every step** (the "all-frames certificate"). Passing it guarantees zero human-timing-induced collisions under any scorer speed or FPS setting, and it also makes the trajectory, NE and SR deterministic. Back it with an adversarial replay sweep (frozen-k, step-locked, fast/slow, stall, random monotone, real wall clock) in the official image. If the organizers' unmerged Oct-14 rule (no `human_motion.json` at inference) applies, a compliant RGB-D agent must also fix the timing mismatch between its own rollout and the replay. It should run its local rollouts on a virtual human clock that matches the fast replay, and keep two-sided motion envelopes around detected humans.

---

## 1. Code walk-through: `$EXT/HA-VLN/HASimulator/environments.py`

The file is identical in the organizer forks `$EXT/havln2` and `$EXT/a10/F1y1113_HAVLN-CE` (diff is empty).

| Lines | Behaviour | Timing consequence |
|---|---|---|
| 35–36 | `total_signals_sent = 0`, `previous_human_object_ids = []` | |
| 39 | `human_model_lock` | Only the main thread ever touches the simulator. The sender thread never does, so the lock is redundant and there is no sim data race. |
| 42 | `queue.Queue(maxsize=120)` | The cap equals the number of frames (see §4). |
| 45–47 | Sender thread started (daemon) at env construction, after `__init_manager__` | The thread is never stopped. Each new env, e.g. one per scan job in the exporter, adds another thread. |
| 49–58 `reset()` | clear queue + counters (52), `put(timeout=1)` (54), `total += 1` → 1 (55), `_handle_signals()` **commented out** (57), `add_new_human_model(frame_id=0)` (58) | Frame-0 humans are placed but the **navmesh is not swapped**. The clock origin is this call. |
| 62–80 | queue cleared via `with signal_queue.mutex: queue.clear()` (65–66). This does not notify `not_full`. Then `total = 0` (70), remove humans (78), `frame_id = 0` (80) | A sender blocked in `put` is released either by the first `get_nowait()` drain or by its own ≤1 s timeout. |
| 96–109 `_signal_sender` | loop: `put(timeout=1)` (102) → `total += 1` (103); on `queue.Full`, pass (105–107); `time.sleep(0.1)` (109) | Ticks every ~0.1 s plus GIL wait. The docstring (97) and comment (108) say "0.5 seconds", a stale leftover from an earlier, slower clock. |
| 111–147 `_handle_signals` | drain all (115–117). If any were drained: `frame_id = (total−1) % 120` (122). Only if `total <= 120` (124): `refresh_human_model(frame_id)` (127), then load `<RECOMPUTE_NAVMESH_PATH>/<scan>/<scan>_<fff>.navmesh` (133, 143–144), or recompute it with `agent_radius 0.1`, `height 1.5`, `include_static_objects=True` and save it (134–142). All exceptions are swallowed (146–147). | `% 120` is dead code because of the ≤120 guard: **no looping, freeze instead**. Recompute and load hold the GIL. |
| 149–154 | refresh = remove all + add all | |
| 156–169 | remove by stored ids; warns if an id is missing (new-scene case) | harmless |
| 171–213 `add_new_human_model` | for each human: `translation[frame]`, `rotation[frame]` (186–187), template `or_num + idx*120 + frame` (191–192), `add_object_by_handle` (201), set pose (203–204), `STATIC` (208), `step_physics(1/5)` (210), store `_sim._human_posisions` (213) | The first `add_object` of each template loads its GLB from disk (lazy `instantiateAssetsOnDemand`, `$EXT/habitat-sim-0.1.7/src/esp/physics/PhysicsManager.cpp:81`, `assets/ResourceManager.cpp:1773-1863`) while holding the GIL. `step_physics` is a no-op integrator because physics is disabled (`PhysicsManager.cpp:201-226`; `ENABLE_PHYSICS=False`, `habitat-lab-0.1.7/habitat/config/default.py:278`). |
| 215–233 | registers 120 templates per HAPS category (asserted at 232) | ~58k templates; configs only, no meshes |

`$EXT/HA-VLN/agent/VLN-CE/vlnce_baselines/common/environments.py`:
- `HAVLNCEDaggerEnv.reset()` (56–66) calls `havlnce_tool.reset()` **before** `super().reset()`. The clock origin therefore precedes habitat's `Env.reset`, which includes the scene load, task reset and initial render.
- `HAVLNCEDaggerEnv.step()` (68–75) calls `_handle_signals()` **before** `super().step()`. The navmesh used for step k's collision test is the one swapped in at the start of step k.
- `HAVLNCEInferenceEnv` (104–131) is identical.
- The official CMA exporter uses `HAVLNCEDaggerEnv` and builds one env per scan job (`$EXT/track2/scripts/export_cma_submission.py:78,95-129`).

## 2. (a) Human frame as a function of time since reset

Let `t_r` be the time of `HAVLNCE.reset()`. Sender ticks happen at times τ₁ < τ₂ < … where τ_{i+1} − τ_i = 0.1 s + ε_i. The extra ε_i ≥ 0 is sleep overshoot (~0.1–1 ms) plus the wait for the GIL. That wait can last as long as the main thread's current GIL-holding C call. The phase τ₁ − t_r is arbitrary in [0, 0.1 s]; it is near-immediate if a blocked sender is released by the first drain.

Then:
- `total(t) = min(120, 1 + #{i : τ_i ≤ t})` while no drain has happened since reset. The queue holds at most 120 items, so a failed `put` does not increment the counter.
- After drains, `total(t) = 1 + #{i : τ_i ≤ t}`, unbounded.

At step k, `_handle_signals` runs at time s_k:
- `frame_k = total(s_k) − 1` if at least one signal arrived since s_{k−1} and `total(s_k) ≤ 120`.
- Otherwise `frame_k = frame_{k−1}`.
- At k = 1 a signal is always pending, so `frame_1 = min(total(s_1),120) − 1`.

**Ideal case (no GIL stalls):** `frame_k ≈ min(119, ⌊(s_k − t_r)/0.1⌋ + φ)` with φ ∈ {0, 1}. After roughly 12 s the frame freezes at the last refreshed value.

**With GIL-holding C++ work of duration X per tick,** the effective period is ≈ 0.1 s + E[residual X]. I measured ≈0.12 s per frame at 30 ms of GIL-holding work per step. If X ≫ 0.1 s, frames advance by **one per refresh** (step-locked).

Verified by `$A3/clock_sim.py`. It copies `environments.py:35-147` with the simulator calls replaced by GIL-releasing sleeps or GIL-holding C loops (`sum(range(n))`). Runs used Python 3.13; the image uses Python 3.8, which has the same GIL design and 5 ms switch interval.

| Scenario (per-step cost) | Steps | Wall time | Frames observed | Final / freeze frame |
|---|---|---|---|---|
| 5 ms, GIL released | 500 | 2.58 s | 0..26 (step 100 → 5) | 26 |
| 5 ms, GIL held | 500 | 2.48 s | 0..23 | 23 |
| 5 ms + 20 ms GIL-held refresh | 500 | 3.28 s | 0..30 | 30 |
| 30 ms, GIL held | 500 | 15.9 s | step 10 → 2, step 50 → 12, step 100 → 25 | 119 (counter ended at 130) |
| 100 ms, released | 200 | 20 s | frame ≈ step index | 119 |
| 300 ms, released | 60 | 17.7 s | 0, 3, 6, … | **117** |
| 1 s, released | 16 | 15 s | 0, 10, 20, … | **110** |
| Cold navmesh: 2 s GIL-held recompute per refresh | 12 | 25.2 s | 0, 1, 2, …, 11 (step-locked) | 11 |
| 13 s stall before step 1, GIL released | 5 | 13 s | 119 from step 1 | 119 (6/6 trials) |
| 13 s stall before step 1, GIL held (e.g. C++ scene load) | 5 | 13.7 s | 1 | 1 |

## 3. (b) Fast versus slow replay

Analytic approximation: frames seen by step N ≈ `min(119, N·Δ/0.1)`, where Δ is the per-step wall time seen by the sender thread.

| Δ per step | N=60 | N=100 | N=200 | N=500 | Freeze reached at step |
|---|---|---|---|---|---|
| 2 ms (no-render stepper) | 1 | 2 | 4 | 10 | never |
| 5 ms (warm GPU replay) | 3 | 5 | 10 | 25 (measured 26) | never |
| 10 ms | 6 | 10 | 20 | 50 | never |
| 20 ms | 12 | 20 | 40 | 100 | ~600 (beyond the 500-action budget) |
| 50 ms | 30 | 50 | 100 | 119 | ~240 |
| 100 ms (CMA-like closed loop) | 60 | 100 | 119 | 119 | ~120 |
| ≥ 1 s (VLM in the loop) | 119 | 119 | 119 | 119 | ~12; freeze frame ∈ [120 − Δ/0.1, 119] |

- **Official replay** has no network in the loop, a warm cache and GPU rendering. It most likely runs at Δ ≈ 3–20 ms per step (estimate, medium-low confidence; never measured), so humans stay in frames ≈ 0–20 for typical episodes. The brief's "tens of ms per step" case (≈20 ms) reaches frame ~100 by step 500.
- **Exceptions:**
  - First episode(s) per scan in a fresh scorer process: GLB lazy-load, and navmesh recompute if the cache is cold, make the animation quasi step-locked (frame ≈ k).
  - Any pre-step stall ≥12 s with the GIL released gives frame 119 from step 1.
  - A slow or contended CodaBench worker shifts frames later.
- **Closed-loop rollouts** (CMA export, VLM agents) see humans at much later frames than the official replay. Movers end up in different places: |p(frame 10) − p(frame 119)| has p90 = 0.74 m, max = 3.12 m, and is >0.5 m for 112/749 humans. A policy that reacts to what it saw during a slow local rollout is reacting to humans that are elsewhere during scoring. This mismatch probably contributes to CMA's high TCR, and to the run-to-run spread: the README's local replay gives val_unseen TCR 17.54 / SR 0.129, while `$EXT/a10/JostarXiong_havln2-docs/docs/api/evaluation_metrics.md:77-80` gives 22.35 / 0.114 for the same checkpoint.

## 4. (c) Queue `maxsize=120` and `queue.Full` interactions

1. **Saturation.** With no drain for ~12 s, the queue fills (1 reset signal + 119 ticks). Further `put(timeout=1)` calls raise `Full`, so `total` stays at **120**, not more. The next `_handle_signals` drains 120 items, reads `total=120` and refreshes to **frame 119**. Its `get_nowait()` then wakes the blocked sender, `total` becomes 121, and no further refreshes happen. Net effect: any drain-free stall ≥12 s puts humans at frame 119 for the rest of the episode. (Verified 6/6; high confidence.)
2. **Race at that drain.** The sender, woken by `not_full.notify()`, could increment the counter to 121 before the main thread reads it, which would skip the refresh. The main thread finishes a 120-item drain in well under the 5 ms GIL switch interval, so this almost never happens (0/6 observed). Theoretical risk only; low.
3. **Lost update.** The non-atomic `total += 1` (lines 55, 103) can collide with `total = 0` (line 70). This needs a GIL switch inside a microsecond window, so it is practically never. If it happened, `total` would stay >120 for the episode and the humans would stay at reset's frame 0 with a stale navmesh. Covered by the all-frames certificate.
4. **Reset with a full queue.** The deque is cleared without notify. The blocked sender either resumes at its ≤1 s timeout or is woken immediately by the first drain at step 1. I measured that frame 1 appears 5 ms after reset when a drain happens. Effect: phase jitter only.
5. **While full,** the sender loops at 1.1 s (1 s timeout + 0.1 s sleep). Irrelevant, because the counter is frozen at 120 anyway.
6. **Step 1 always refreshes,** because reset's signal is pending and `total ≤ 120`. The base, human-free navmesh is therefore never active during a step. The exceptions are the race in item 2 or a swallowed exception (e.g. a corrupt cache file; see the C1 cache-write race).
7. **Correction to A2 (findings/A2…md fact 17 and Appendix B).** "If reset + scene load exceeds 12 s … humans are never injected" is incorrect:
   - If the GIL was free during the stall, humans are injected at frame 119 (queue cap).
   - If the load held the GIL, they are injected at a low frame.
   - A2's recommendation to also certify against the base navmesh remains sensible for items 2, 3 and 6.

## 5. (d) What the organizers' scorer may have changed, and what to inspect

**Evidence:**
- The image ships its own patched habitat and runtime packages. The exporter imports the image's `habitat`, `habitat_extensions` and `vlnce_baselines` first and only appends the public source to `__path__`. It also fingerprints `habitat/sims/habitat_simulator/habitat_simulator.py` and `/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml` (`$EXT/track2/scripts/export_cma_submission.py:48-62,104,189,216-219`).
- The initial README (commit 2daf3dd, `git -C $EXT/track2 show 2daf3dd:README.md`):
  - L246-249 and L259-306: a local replay CLI `havln-score-phase1` and a writable `recompute_navmesh` cache mount.
  - L323-325: "Humans move in real time, so repeat runs can differ."
- The organizer clarification branch `bohan/clarification-Oct14` (`git -C $EXT/track2-jostar diff d4baf9e 8289590`) rewrites Q4: "Human animations advance with wall-clock time according to the **configured motion FPS** … there is no single fixed wall-clock duration for each action … replayed in the standardized organizer-controlled CodaBench environment."
- So the official scoring is wall-clock and nondeterministic (high confidence), and the FPS may be configurable in the image (medium). The stale "0.5 s" comments (environments.py:97,108) show the FPS has changed before.
- I could not fetch the image layers. The ghcr token and manifest work, but the blob CDN `pkg-containers.githubusercontent.com` is blocked by the egress proxy (status endpoint: connect_rejected).

**Inspection checklist** (someone with docker: `docker run --rm --entrypoint bash $IMAGE -c '…'` or `docker export`):
1. `/opt/havln-challenge/scoring/havln_scoring/**`: the `havln-score-phase1` entry module, replay loop, per-episode env reuse vs per-scan processes, worker count per GPU. grep for: `sleep|Thread|signal_queue|_handle_signals|refresh_human_model|frame|fps|FPS|perf_counter|time\.|recompute|navmesh|setswitchinterval|multiprocessing`.
2. `havln_scoring/config/six_action_task.yaml` and `/app/config/challenge_submission.yaml`: `SIMULATOR.ADD_HUMAN`, `HUMAN_*` paths, `RECOMPUTE_NAVMESH_PATH`, any FPS or `MOTION_FPS` key, sensor list and resolution (rendering cost per step), `TASK.MEASUREMENTS` (`DISTANCE_TO_HUMAN` adds N filtered moves per step and resets camera tilt), `ENV_NAME`, `MAX_EPISODE_STEPS`.
3. The image's own `HASimulator/environments.py` and `vlnce_baselines/common/environments.py` (find them via `python -c 'import HASimulator.environments as m; print(m.__file__)'`). Diff against the public files: queue size, sleep period, the ≤120 guard, whether reset calls `_handle_signals`, any deterministic per-step frame advance.
4. Diff `/app/habitat-lab/habitat/sims/habitat_simulator/habitat_simulator.py` against habitat-lab v0.1.7 (`$EXT/habitat-lab-0.1.7`).
5. Whether `recompute_navmesh/` is prebuilt in the image or created at scoring time; what `havln-check-data` and `havln-check-environment` check; whether HAPS GLBs are pre-instantiated (warm-up).
6. Python version and any `sys.setswitchinterval`; episode ordering (sorted by id within scan, as in the exporter); new env per scan job.

## 6. Human motion quantification

Source: `$EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json` (72 scans, 749 humans, 120 frames each, no `None` frames). Scripts: `$A3/analyze_motion.py`, `$A3/linearity.py`, `$A3/windows.py`, `$A3/facing.py`, `$A3/episodes_vs_humans.py`.

**Horizontal swept extent** (max pairwise XZ distance over 120 frames):

| Statistic | Value |
|---|---|
| p50 / p75 / p90 / p95 / p99 / max | 0.00 / 0.10 / 0.80 / 1.15 / 1.69 / 3.47 m |
| mean | 0.20 m |
| > 0.05 m | 189 humans (25.2%) |
| > 0.25 m | 175 (23.4%) |
| **> 0.5 m** | **140 (18.7%)** |
| > 1 m | 47 (6.3%) |
| > 1.5 m | 11 (1.5%) |
| > 2 m | 4 (0.5%) |
| > 3 m | 2 (0.3%) |

The CONTEXT figure "median 0.03 m" is a 3-D extent. Horizontally the median is exactly 0, and 560/749 humans never move in XZ; 425 of those move only vertically (pelvis bob). 135 are fully static.

**Motion shape:**
- **Rotation is constant:** Euler ptp = 0 on all axes for all 749 humans. Rotation x is non-zero for 26 lying or tilted humans; z is always 0.
- **Piecewise-linear:** start and stop frames sit at multiples of ~20 (0, 19, 39, 59, 78/79, 98/99, 118). The most common patterns are (0→118) ×75, (19→118) ×18, (0→78) ×18, (0→38) ×13.
- 26 of the 189 movers have some backward steps (pacing).
- Max per-frame step 0.035 m, i.e. **0.35 m/s at 10 FPS**; the p99 of per-human max speed is 0.25 m/s.
- **Direction:** 74% of movers with displacement ≥0.3 m move within 20° of local +Z rotated by their yaw (86% within 45°; median 0°). Humans walk in the direction they face.
- **Height:** the translation y sits a median 0.74 m above the nearby floor (IQR 0.67–0.83 m). It is the pelvis/root, so the GLB meshes are probably root-centred (medium confidence; the HAPS GLBs were not available to inspect).

**Category keywords** (median extent / share moving >0.5 m):

| Keyword | n | Median extent | Share > 0.5 m |
|---|---|---|---|
| pacing | 85 | 0.59 m | 65% |
| talking | 79 | 0.59 m | 66% |
| phone | 96 | 0.59 m | 54% |
| running | 21 | 1.00 m | 71% |
| cleaning | 32 | 0.60 m | 56% |
| walking | 10 | 0.49 m | 50% |
| dancing / exercise / "rush" | — | 0 m | 0% |

**Per scan:** 6–19 humans (mean 10.4). 57/72 scans have at least one mover >0.5 m; 30 have one >1 m; 7 have no horizontal mover. Train scans: 19.3% of humans >0.5 m, 6.1% >1 m. Val_unseen scans: 15.2% and 7.1%.

**Extent within the first K frames** (what a fast scorer can show):

| Frames | ≈ wall time | Mean | p90 | Max | n > 0.5 m | n > 1 m |
|---|---|---|---|---|---|---|
| 0..10 | 1.1 s | 0.02 m | 0.10 m | 0.35 m | 0 | 0 |
| 0..25 | 2.6 s | 0.05 m | 0.25 m | 0.88 m | 11 | 0 |
| 0..50 | 5.1 s | 0.11 m | 0.47 m | 1.75 m | 59 | 7 |
| 0..119 | 12 s | 0.20 m | 0.80 m | 3.47 m | 140 | 47 |

**Swept-footprint model** (union over 120 frames of discs around the root, rasterized at 1 cm):

| Disc radius r | Static disc area | Swept area mean / p90 / max | Extra blocked area, all humans |
|---|---|---|---|
| 0.35 m | 0.385 m² | 0.53 / 0.95 / 2.93 m² | +109 m² (+38%) |
| **0.45 m** | 0.636 m² | 0.82 / 1.36 / 3.90 m² | **+140 m² (+29%)** |
| 0.55 m | 0.95 m² | 1.18 / 1.83 / 4.93 m² | +169 m² (+24%) |

All of the extra area comes from the 189 movers. The disc model is for analytics only. The exact obstacle is the navmesh hole: body parts 0.2–1.6 m above the floor, eroded by 0.10 m (A2 facts 13–15). Use per-frame navmeshes for planning.

**Reference-path timing sensitivity** (R2R-CE v1-2 `_gt` locations densified to 5 cm, same-floor humans with dy ∈ (0.2, 1.6) m; HA-R2R reuses these episodes per CONTEXT fact 5). "Sensitive" means the path is within R of a root at some frames only; "always" means at every frame.

| Split | R | Clear | Always | **Sensitive** | Frame 0 conflicts | Any 0..25 | Any 0..119 | Clear at f0, conflict later |
|---|---|---|---|---|---|---|---|---|
| val_unseen (1839) | 0.30 | 1221 | 417 | 201 (10.9%) | 549 | 555 | 618 | 69 |
| val_unseen | **0.45** | 1116 | 576 | **147 (8.0%)** | 651 | 654 | 723 | 72 |
| val_unseen | 0.60 | 1059 | 663 | 117 (6.4%) | 714 | 741 | 780 | 66 |
| val_seen (778) | 0.45 | 468 | 244 | 66 (8.5%) | 277 | 286 | 310 | 33 |
| train (10819) | 0.45 | 7054 | 3035 | 730 (6.7%) | 3501 | 3588 | 3765 | 264 |

Implication: about 1/3 of episodes already require detouring around static humans standing on the R2R path, whatever the timing. Timing adds only ~7–9% more episodes in which the union-of-frames constraint bites.

## 7. Per-frame navmesh recompute cost and the first local run

- The cache is per (scan, frame): `<RECOMPUTE_NAVMESH_PATH>/<scan>/<scan>_<fff>.navmesh`. That is up to 120 builds per scan: 8,640 for the 72 public scans and 2,160 more for the 18 test scans (10,800 files). Each build joins the whole stage collision mesh with every STATIC human mesh and rebuilds Recast at 5 cm cells (`$EXT/habitat-sim-0.1.7/src/esp/sim/Simulator.cpp:643-700`).
- Cost per build has not been measured. Estimate 1–20 s (low confidence; C1 estimates 3–20 s), so 2–40 min per scan serially. Size about 0.5–5 MB each (C1), 5–50 GB total.
- **First-run implication:** with a cold cache, the first episode(s) of each scan recompute at every new frame while holding the GIL. The run is very slow and the clock becomes step-locked (frame ≈ step index; §2). Its collision results are **not comparable** with warm-cache runs. A fresh process also loads each HAPS GLB lazily on first use (the ResourceManager is rebuilt on every scene change or close, `Simulator.cpp:53-77`), so even with a warm navmesh cache the first pass in each scan is quasi step-locked.
- **Cache keys contain only scan and frame.** Any change to `human_motion.json`, the HAPS assets, the NavMeshSettings or the habitat-sim build silently reuses stale files. Writes are non-atomic and exceptions are swallowed, so parallel writers can corrupt files (C1 flag 5).
- Remedy: one writer per scan pre-warms all 120 frames with atomic saves, then the cache is mounted read-only. Record a manifest of hashes. Rebuild when any input hash changes.

## 8. Recommendations

**R1 — Timing-robust collision policy (privileged tier).** Plan and accept only action sequences whose visited positions and MOVE_FORWARD segments lie inside every navmesh in N = {base, frame 000..119} with margin m = 0.10–0.15 m. Equivalently, plan on the intersection: a "swept" navmesh built with all 120 frames of every human added as STATIC objects, recomputed at agent_radius 0.25–0.30 (A2 RULE 2). Also require that every turn is a no-op translation on every navmesh, i.e. the position is navigable everywhere. Starts inside a human footprint get special handling: TURN first (A2 RULE 5). This makes collisions, the trajectory, NE and SR **independent of scorer timing and FPS**. The expected price is small: it bites in ~8% of episodes and adds ~29% blocked area around movers.

**R2 — When the intersection disconnects start and goal** (e.g. a pacing human sweeping a whole hallway):
- (a) Look for an alternative route on the intersection.
- (b) Otherwise use the "causal union". Under the plausible regime (per-step time ≤0.1 s, no pre-step stall), frame(k) ≤ k + 1, so at step k only frames 0..min(119, k + slack) need to be avoided (slack ≥ 10). This relaxation is assumption-dependent; mark such episodes as at-risk.
- (c) In the 237 test episodes with `collision_num ≥ 1`, up to `collision_num` collisions are free (`HASimulator/metric.py:15`), so accept the risk there first.
- Never "wait" with LOOK pairs: delay per action depends on scorer speed and is not a reliable clock.

**R3 — Adversarial replay certification protocol.** Run in the official image, same binaries. Patch only the clock with a FrameScheduler (C1 §3.2); keep the refresh and navmesh code. Certify on these regimes:
1. **ALL-FRAMES certificate** (strongest, CPU-only): kinematic `try_step` replay against all 121 navmeshes at every step, requiring identical positions and zero shortening greater than 2e-5 m. It covers every schedule, any FPS and any looping.
2. **FROZEN-k**, k ∈ {0, 10, …, 110, 119} (or all 120).
3. **STEP-LOCKED:** frame(k) = min(k−1, 119).
4. **FAST(Δ):** Δ ∈ {2, 5, 10, 20, 50 ms}.
5. **SLOW(Δ):** Δ ∈ {0.1, 0.3, 1 s} with random phase (freeze at 110–119).
6. **STALL:** frame 119 from step 1.
7. **RANDOM-MONOTONE:** about 1,000 random non-decreasing schedules per episode.
8. **FPS variants:** 0.5 s per frame (the stale comment), 0.04 s (25 FPS demo), looping.
9. **OFFICIAL wall clock:** `havln-score-phase1` (initial README L246-249), at least 3 runs each on an idle machine, a loaded machine (`nice`/cpulimit), a cold cache, and a fresh process per scan.

Release gate: collisions.count == 0, or ≤ `collision_num`, on 1–8. Identical final pose in all regimes. Bit-identical Score across 9's repetitions.

**R4 — Leaderboard determinism check.** Resubmit an identical certified archive once. If the Score differs, timing sensitivity remains. Optionally, during Phase 1 (only until Oct 30), spend 1–2 submissions on timing probes:
- Probe episodes have `collision_num = 0`. Each one MOVE_FORWARDs at step k into a cell that a mover occupies only for frames ≥ F, and collides at most once.
- Every other episode issues STOP immediately, so its NE is known and it contributes no collisions.
- Invert the printed Score for TCR and CR. That yields the official step-to-frame map, including whether step 1 sees frame 119 or step-locked behaviour.

**R5 — Compliant tier** (if Oct-14 Q11 is enforced: no `human_motion.json` at inference; `$EXT/track2-jostar`, branch `bohan/clarification-Oct14`).
- Decouple the local rollout's human clock from agent compute: run closed-loop rollouts with a virtual clock, frame(k) = ⌊k·Δ̂/0.1⌋ with Δ̂ ≈ 5–10 ms (from probes, if run). Otherwise a slow VLM agent sees humans frozen near frame 110–119 while the scorer shows frames 0–20.
- Inflate each detected human by a two-sided capsule along its facing axis. Length comes from train-scan priors (allowed as privileged supervision under Q11): p95 ≈ 1.15 m, max 3.5 m, speed ≤ 0.35 m/s. Add 0.35 m body radius, 0.10 m erosion and ≥0.10 m margin.
- Whether running the all-frames certificate on **test** episodes counts as "accessing human_motion.json during inference" is unclear. Ask the organizers before relying on it for Phase 2.

**R6 — Operations.**
- Pre-warm and freeze the navmesh cache per scan (single writer, atomic, hashed manifest), and invalidate it on any input-hash change.
- Never benchmark on a cold-cache first run.
- Pin one process per scan, as the official exporter does.
- Log `havlnce_tool.frame_id` and `total_signals_sent` per step in every local replay, to measure the regime actually experienced.

## 9. Contradictions and flags

- **A2 (fact 17, Appendix B, "humans never injected" after slow resets):** refuted by the queue cap (§4 items 1 and 7; simulation 6/6).
- **CONTEXT fact 4 "median extent 0.03 m":** that is a 3-D number. The horizontal median is 0.00 m, 75% of humans never move in XZ, and the freeze frame is not always 119.
- **CONTEXT fact 8 / strategic hypothesis:** the unmerged organizer clarification forbids `human_motion.json` at inference (C1 flag 2). The timing-robust certificate needs per-test-scan human data, so its admissibility for Phase 2 is an open rules question.
- **Effective clock:** C1's statement that "12 s wall-clock" is the cutoff needs a caveat. GIL-held C++ time does not count, so the cutoff is ≥12 s of wall time and can be much longer (step-locked regime).

## 10. Open questions

1. What exactly does the image's havln_scoring replay do: FPS, sensors, measurements, process layout, cache state, GLB warm-up? See the §5 checklist; the image could not be pulled here.
2. What is the actual official per-step wall time? Measure locally with `havln-score-phase1` on comparable GPUs. Optionally measure on the leaderboard with R4 probes.
3. Will the Phase-2 bundle include `human_motion.json` entries for the 18 test scans (needed to build test navmeshes), and does Q11 make using them for offline certification illegal?
4. What are the HAPS2_0 per-frame mesh footprints? Is the root motion only in `translation`, or also baked into the GLBs? Compute AABBs from the GLBs.
5. What does one MP3D-scale `recompute_navmesh` cost, and is Recast output bit-identical across CPUs? Measure during bring-up; margins ≥0.10 m make the second point mostly moot.

## Sources

- `$EXT/HA-VLN/HASimulator/environments.py` (lines cited); identical copies in `$EXT/havln2` and `$EXT/a10/F1y1113_HAVLN-CE`.
- `$EXT/HA-VLN/agent/VLN-CE/vlnce_baselines/common/environments.py:48-131`
- `$EXT/HA-VLN/HASimulator/measures.py:23-181`, `$EXT/HA-VLN/HASimulator/metric.py:12-17`, `$EXT/HA-VLN/Data/HA-R2R-tools/collision_num_*.json`
- `$EXT/HA-VLN/README.md:382-396` (real-time human rendering; navmesh computed on first use)
- `$EXT/HA-VLN/scripts/demo.py:98-277` (25 FPS looping demo variant); `$EXT/HA-VLN/scripts/docker-quickstart-20261005.json` (earlier image digest 78a62cd…)
- `$EXT/track2/README.md` (current; FAQ Q4 lines 268-270); `git -C $EXT/track2 show 2daf3dd:README.md` (lines 47-48, 99-123, 246-306, 323-325)
- `$EXT/track2/scripts/export_cma_submission.py:48-129,189,216-219`
- `$EXT/track2-jostar`, branch `origin/bohan/clarification-Oct14`, commits 0f944d3 and 8289590 (Q4 rewrite, Q8–Q13)
- `$EXT/a10/JostarXiong_havln2-docs/docs/api/scene_updates.md`, `docs/quick_start/integration.md`, `docs/api/evaluation_metrics.md:73-82`
- habitat-sim v0.1.7 (`$EXT/habitat-sim-0.1.7`): `src/esp/bindings/*.cpp` (no `gil_scoped_release`), `SimBindings.cpp:152,186-192,284-287`, `src/esp/sim/Simulator.cpp:53-130,615-700`, `src/esp/physics/PhysicsManager.cpp:81,201-226`, `src/esp/assets/ResourceManager.cpp:1773-1863`, `habitat_sim/simulator.py:117-262,469-470`
- habitat-lab v0.1.7 (`$EXT/habitat-lab-0.1.7`): `habitat/sims/habitat_simulator/habitat_simulator.py:360-370`, `habitat/config/default.py:32-33,278`, `habitat/core/env.py:178-195`
- `$EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`; `$EXT/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{train,val_seen,val_unseen,test}`
- `$EXT/HA3D_simulator/src/render/renderer.py:128-164` (HA-VLN 1.0 baked root motion in meshes)
- My scripts: `$A3/clock_sim.py`, `$A3/clock_sim2.py`, `$A3/analyze_motion.py`, `$A3/linearity.py`, `$A3/windows.py`, `$A3/facing.py`, `$A3/episodes_vs_humans.py`
- Other findings cross-checked: `findings/A2-collision-semantics-habitat017.md`, `findings/C1-infra-and-replay-farm.md`
- https://arxiv.org/abs/2503.14229 (HA-VLN 2.0 paper; from one WebSearch result summary, which did not describe the signal thread)
- https://github.com/UWMILab/HA-VLN
