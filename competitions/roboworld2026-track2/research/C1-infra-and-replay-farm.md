# C1 — Compute/Infra Plan: Replay Farm, Planning Service, Caches, Queue, Versioning

Topic id: `C1-infra-and-replay-farm` · Date: 2026-10-24 · Author: research agent C1
Base of cloned material: `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext` (abbreviated `$BASE` below).

---

## 0. TL;DR and critical flags

1. **The scorer is deterministic in everything except human timing.** Collision, sliding, success and NE are pure functions of (scene navmesh with humans baked in, start pose, action list). The only wall-clock dependence is *which human frame (0..119) is baked into the navmesh at each step*; a frame refresh happens on a `step()` only if ≥1 signal (one per 0.1 s wall-clock, max 120 per episode) is pending (`$BASE/HA-VLN/HASimulator/environments.py:111-144`). A deterministic local scorer is obtained by replacing the queue read with a `FrameScheduler` and keeping the rest of the official code path unchanged (Section 3.2).
2. **FLAG — rules clarification (unmerged, organizer fork, 2026-10-14) contradicts the "plan everything offline" hypothesis in CONTEXT fact 8.** Branch `bohan/clarification-Oct14` of `JostarXiong/track2` (commits 0f944d3, 8289590) rewrites the Input row to *"Episode ID, initial pose, navigation instruction, ongoing agent pose (GPS+compass from simulator state), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (human_motion.json) is strictly prohibited during inference"*, adds *"One forward-facing RGB-D camera; adding cameras is not permitted; panoramas must be acquired by rotating"* (Q8), allows reading pose (Q9), allows pretrained models/other datasets but forbids training on val/test (Q10), forbids reading `human_motion.json` at inference (Q11), allows closed-source APIs but discourages them (Q12). Not merged into `roboworld2026/track2` main (HEAD 2d408b2) as of today, but it is the organizers' stated intent; award winners can be asked for code. **Infra must therefore be dual-mode: a *privileged* tier (training data, local evaluation, oracle analysis) and a *compliant* tier (closed-loop RGB-D + pose agent) with an audit manifest recording exactly what each submission consumed.** Whether offline use of the MP3D mesh/navmesh (not humans) is allowed is an open question to put to the organizers.
3. **FLAG — `collision_num_test.json` (3,408 entries, 237 non-zero, mean 0.08) is public** in `$BASE/HA-VLN/Data/HA-R2R-tools/`, although the toolkit README says test collision annotations are withheld. The per-episode TCR baseline for test is therefore known locally.
4. **FLAG — NE/SR use 3-D *Euclidean* distance to goal, not geodesic.** `HASimulator/measures.py:100-155` re-registers `DistanceToGoal` (same registry key; habitat's registry silently overwrites, `$BASE/habitat-lab-0.1.7/habitat/core/registry.py` `_register_impl`), computing `np.linalg.norm` to the goal; `Success` reads that uuid. A competitor independently confirmed the Euclidean behaviour inside the image (`$BASE/competitor-bingchengzhang/project/havln_agent/adapters/habitat_env.py:182-186`). Consequence: stopping within 3 m straight-line of the goal on another floor counts as success; the planner should optimise Euclidean, not geodesic, distance at STOP.
5. **FLAG — navmesh cache race.** `_handle_signals` writes `recompute_navmesh/<scan>/<scan>_<fff>.navmesh` directly (non-atomic) and swallows all exceptions (`environments.py:134-147`). Parallel workers on the same scan can read a half-written file → silent fallback to a stale navmesh → wrong collisions. **Pre-warm the full 120×scan cache single-writer, then mount read-only.**
6. **The official image already ships a replay scorer CLI** (`havln-score-phase1 --submission … --output-dir … --gpu-ids …`, plus `havln-check-environment`, `havln-check-data`, `havln-validate`), documented in the toolkit's initial commit (`$BASE/track2-full`, `git show 2daf3dd:README.md` §"Validate, replay, and submit" and §"Local Docker Replay") and removed from the streamlined README. It uses wall-clock human timing ("Humans move in real time, so repeat runs can differ"). Use it as the *official-mirror oracle*; use our deterministic scorer for development and robustness sweeps.
7. **Sizing answer (Section 8):** replaying 3,408 × 500 steps in the official-mirror regime (RGB-D rendered) in < 30 min needs ~24 long-lived worker processes (18 scan shards + 6 splits of the four largest scans) on 3 GPUs (8 procs/GPU, ~2 GB VRAM each), 24 CPU cores, ~100 GB RAM: ≈ 10–12 min including start-up. The navmesh-only CPU stepper (no GPU) does the same 1.7 M steps in seconds per core and is what the planners should hammer.

---

## 1. Facts established from the code (with citations)

### 1.1 Container contract (official image `ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f…`)
- Image layers: one 6.1 GB base layer + ten tiny layers (33 KB, 2–5 KB, …) (`$BASE/image-manifest.json`) → the challenge-specific code (`havln_scoring`, configs) is a few tens of KB on top of a Habitat 0.1.7 / torch 2.0.1+cu118 / python 3.8 base.
- Paths inside the image (from `$BASE/track2/scripts/export_cma_submission.py`): `/app/config/challenge_submission.yaml` (L104), `/app/habitat-lab` (`setup_cma.sh`), `/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml` (L219), `/opt/havln-challenge/codabench/phase1/reference/public_reference_manifest.json` (L189), python package `havln_scoring` with `runtime.quiet_runtime` (L74) and `submission_contract.load_manifest` (L188). CLI entry points: `havln-validate`, `havln-check-data`, `havln-check-environment`, `havln-score-phase1`.
- Mounts: `/data/havln2` (read-only OK) with `HA-R2R/{split}/{split}.json.gz`, `HA-R2R-tools/collision_num_*.json`, `Multi-Human-Annotations/human_motion.json`, `HAPS2_0/<category>_<index>/{000..119}.glb + .object_config.json` (116,640 files = 486×120×2, verified count in `$BASE/HA-VLN/scripts/docker-quickstart-20261005.json`), `scene_datasets/mp3d/<scan>/<scan>.glb` (+ `.navmesh`, `.house`), `checkpoints/HA-VLN-CMA/ckpt.39.pth`; **separately writable** `/data/havln2/recompute_navmesh` (initial README L122: "writable replay cache"); `/workspace` (outputs); `/toolkit` (ro).
- Env construction exactly as the exporter (L104-125): `get_config('/app/config/challenge_submission.yaml')`, set `DATASET.{SPLIT,DATA_PATH,SCENES_DIR,EPISODES_ALLOWED}`, `SIMULATOR.HABITAT_SIM_V0.GPU_DEVICE_ID`, `SIMULATOR.{HUMAN_GLB_PATH,HUMAN_INFO_PATH,RECOMPUTE_NAVMESH_PATH}`, `TASK.SENSORS=['INSTRUCTION_SENSOR']`, `TASK.MEASUREMENTS=[]` (scorer: add `DISTANCE_TO_GOAL, SUCCESS, COLLISIONS, COLLISIONS_DETAIL`), `ITERATOR_OPTIONS.SHUFFLE=False, MAX_SCENE_REPEAT_STEPS=-1`, `SEED=0`, then `HAVLNCEDaggerEnv(config)`, `env.habitat_env.episode_iterator = iter(sorted(env.episodes, key=int))`.
- Sharding: one job per (split, scan); one worker **process** per GPU; shards persisted as `shards/<split>-<scan>.json` with a `fingerprint` (L95-101, L172); `torch.set_num_threads(1)`; seeds 0.
- Action vocabulary check `TASK.POSSIBLE_ACTIONS == [STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, LOOK_UP, LOOK_DOWN]` (L123); actuation 0.25 m / 15° (`HASimulator/config/*.yaml`), TILT 30° (measured in-image by competitor, `config.py` `tilt_deg: 30.0 # 比赛配置实测`), `ALLOW_SLIDING: True`; agent radius 0.1 m, height 1.5 m (habitat defaults, `habitat/config/default.py:251-252`), RGB 224×224 HFOV 90, depth 256×256 (challenge yaml unknown; HA-VLN yaml values).

### 1.2 Step → collision semantics (what the replay actually computes)
- `Env.step` → `task.step` → `MoveForwardAction.step` → `sim.step(MOVE_FORWARD)` → `agent.act` → `ObjectControls.action(apply_filter=True)`: moves the body node 0.25 m along local −Z, then `filter_end = pathfinder.try_step(start, end)` (sliding allowed), and **collided = ‖filter_end−start‖² + 1e-5 < ‖end−start‖²** (`$BASE/habitat-sim-0.1.7/habitat_sim/agent/controls/object_controls.py:68-89`; `simulator.py:step_filter`; `src/esp/nav/PathFinder.cpp:1114-1180` `moveAlongSurface`). Turns rotate the body by exactly 15° about +Y (`default_controls.py:122-123`), LOOK_UP/DOWN rotate only sensor nodes (`body_action=False`) and can never collide. `STOP` calls `get_observations_at()` (no action, `collided` False) and sets `is_stop_called` (`nav.py:1018-1029`).
- Collision count per episode = number of `step()` calls whose `previous_step_collided` is True (`Collisions`/`CollisionsDetail.update_metric`, `nav.py:653-672`, `HASimulator/measures.py:158-180`). Each wall-slide counts once per step, hence baseline TCR ≈ 14–18.
- Episode ends when `STOP` is executed (`is_episode_active` False) or after `MAX_EPISODE_STEPS = 500` (`env.py:187-233`). With 500 non-STOP actions, success is impossible (needs `is_stop_called`).
- `Success = is_stop_called and distance_to_goal < 3.0` (strict), with `distance_to_goal` the **Euclidean** HA-VLN measure (see flag 4).
- Metric assembly (`HASimulator/metric.py`): `TCR_ep = max(0, count − collision_num[ep])`, `CR_ep = min(TCR_ep,1)`, `SR_ep = success·[TCR_ep==0]`; aggregates: means over all episodes, CR divided by β·L (β_test = 1−549/3408 = 0.8389; toolkit initial README table: human-influenced val_seen 682, val_unseen 1,593 → test 2,859). Score as in CONTEXT.

### 1.3 Human timing — the only nondeterminism
- `HAVLNCE.__init__` loads **all** 486 HAPS category directories with `load_configs` (58,320 templates; `assert add_num == 120`) (`environments.py:215-233`) and starts a daemon thread that `put`s one signal every 0.1 s into a `Queue(maxsize=120)`, incrementing `total_signals_sent` only after a successful put (`:96-109`).
- `reset()` clears the queue, zeroes counters, removes humans, enqueues **one** signal (so `total_signals_sent=1`) and adds humans at frame 0 **without touching the navmesh** (`:49-58`). After a scene switch, `Env.reset → sim.reconfigure` closes the sim, so the frame-0 humans added before `super().reset()` vanish and the pathfinder is the scene's default navmesh until the first step.
- `step()` first calls `_handle_signals()` (`vlnce_baselines/common/environments.py:68-75`): drains the queue; if ≥1 signal and `total_signals_sent ≤ 120`: `frame_id=(total_signals_sent−1)%120`, remove+add all humans for that frame (one `step_physics(0.2)` per human — a no-op integrator without Bullet, `PhysicsManager.cpp:201`), then **load** `<scan>_<fff>.navmesh` from the cache or **recompute** (`recompute_navmesh(…, include_static_objects=True)`, agent_radius 0.1, height 1.5, Recast defaults cell 0.05 m / 0.2 m, `PathFinder.h:137-154`) and save it.
- Consequences: (a) the first `step()` of every episode always refreshes (a signal is always pending), with `frame ≈ floor(elapsed_since_reset/0.1)`; (b) subsequent refreshes happen only on steps separated by ≥0.1 s wall-clock; (c) after ~12 s wall-clock since reset the counter exceeds 120 and humans **freeze at the last refreshed frame**; (d) a scorer running at S steps/s sees frames `0 … min(119, 500/S/0.1)` — a 200 steps/s scorer never passes frame ~25; a 10 steps/s scorer runs frames 0..119 then freezes; (e) `recompute_navmesh` requires `create_renderer=True` (`Simulator.cpp:643-651` CORRADE_ASSERT) and objects require a physics manager that only exists with a renderer (`Simulator.cpp` reconfigure block) ⇒ **every official-mirror worker needs an EGL/GPU context and ≥1 visual sensor**; a 2×2 depth sensor suffices if rendering is not wanted.
- Human displacement is small (CONTEXT fact 4: median extent 0.03 m, p90 0.8 m, max 3.47 m), so a plan that is collision-free against the **intersection of all 120 navmeshes** costs little clearance and is immune to timing (Section 4.3).

### 1.4 Dataset shape relevant to sharding
- Test: 3,408 episodes over 18 scans; R2R test path counts per scan (`$BASE/HA-VLN/HASimulator/HA-DE/tasks/R2R/data/R2R_test.json`) range 7 (gYvKGZ5eRqb) to 100 (nine scans) paths ⇒ ≈ 3 instructions/path ⇒ largest shards ≈ 245 episodes (≈ 7 % of the split), smallest ≈ 17.
- Val_unseen: 1,839 episodes over 11 scans (max 100 paths/scan); val_seen 778 over 56 scans; train 10,819 over 61 scans. Humans per scan (72 public scans): 6–19, median 10 (`human_motion.json`).
- Episode ids are contiguous 1..N strings per split (`collision_num_*.json`); test ids 1..3408.

---

## 2. Architecture overview

```
                      ┌────────────────────────── control plane ───────────────────────────┐
  coding agents ───►  │  CLI/SDK  →  Redis (streams: jobs.replay, jobs.plan, jobs.render,  │
  (N≈10-60)           │              jobs.llm)  →  results index (Postgres or SQLite-WAL)   │
                      │              provenance/fingerprint registry, dashboards            │
                      └───────────────────────────────┬────────────────────────────────────┘
                                                      │ idempotent tasks (key = sha256(inputs))
        ┌─────────────────────────────┬───────────────┴──────────────┬──────────────────────────┐
        ▼                             ▼                              ▼                          ▼
 GPU tier A: Replay Scorer    GPU tier B: Planning/Render     CPU tier C: NavStepper      GPU tier D: models
 (official image, 1 proc per  Service (habitat_sim only,      (PathFinder-only kinematic   (VLM/LLM servers, feature
 scan shard, EGL ctx, RGB-D   get_observations_at, panoramas, stepper; all-frames sweeps;  extractors; vLLM/TGI;
 or 2x2 depth), regimes R0-R3 humans at frame k, topdown)     search/planning workers)     response cache)
        └─────────────────────────────┴───────────────┬──────────────┴──────────────────────────┘
                                                      ▼
                     data plane (shared POSIX FS, e.g. Lustre/NFS/Weka; optionally S3 mirror):
                     /havln2 (ro)  /navmesh_cache (ro after warm-up)  /renders  /features  /llm_cache
                     /submissions  /results/<fingerprint>/<regime>/<split>-<scan>.json  /registry
```

Design rules: (1) every artifact is addressed by a content hash and a runtime fingerprint; (2) workers are long-lived per scan to amortise scene load (5–30 s) and the 58k template parse (~10–30 s); (3) all writes are atomic (`.partial` + `os.replace`, as the exporter does); (4) the navmesh cache is warmed once by a single writer per scan and mounted read-only everywhere else; (5) privileged vs compliant data flows are separated by endpoint and recorded in the submission manifest.

---

## 3. Component 1 — Deterministic local REPLAY SCORER service

### 3.1 Responsibilities
Input: a submission JSON (`{format_version, split, episodes:[{episode_id, actions[]}]}`) or a subset; a **regime**; optional goal overrides (test split has no goals). Output: per-episode `success, NE, collisions.count, collision_steps, TCR, CR, SR, frames_seen, final_pose, steps_executed`, aggregate `SR, NE, CR, TCR, Score`, plus the exact runtime fingerprint. Runs **inside the official image** (same binaries) so collision/sliding semantics are bit-identical.

### 3.2 Human-timing regimes (the `FrameScheduler` patch)
Subclass/monkeypatch `HASimulator.environments.HAVLNCE` so that `_handle_signals()` consults a scheduler instead of the queue, leaving `refresh_human_model` + navmesh load/recompute code untouched:

```python
class ScheduledHAVLNCE(HAVLNCE):
    def __init__(self, config, sim, scheduler):           # scheduler: step_idx -> frame_id | None
        super().__init__(config, sim); self.sched = scheduler; self.k = 0
        self._signal_thread = None                         # do not start the wall-clock thread (regimes R2/R3)
    def reset(self):
        self._reset_signal_queue_and_counters(); self.k = 0
        self.add_new_human_model(frame_id=0)               # identical to official reset: NO navmesh reload here
    def _handle_signals(self):
        fid = self.sched(self.k); self.k += 1
        if fid is None: return                             # no signal pending → no refresh (official behaviour)
        self.refresh_human_model(fid); self.frame_id = fid
        self._load_or_build_navmesh(fid)                   # copy of environments.py:129-144, with atomic save
```
Regimes (all selectable per job):
- **R0 `wallclock`**: the unmodified official class (thread at 0.1 s). Nondeterministic; used only for cross-checking against `havln-score-phase1`.
- **R1 `wallclock_throttled(t_step)`**: official class + `time.sleep(max(0, t_step − dt))` per step to emulate slower graders (t_step ∈ {0.01, 0.02, 0.05, 0.1, 0.2} s). Nondeterministic but reproducible in distribution.
- **R2 `frozen(k)`**: `sched(0)=k`, `sched(i>0)=None` → humans at frame k for the whole episode (120 deterministic worlds). `frozen(0)` is the fastest-grader limit; sweeping k∈{0..119} gives the robustness envelope.
- **R3 `schedule(S)`**: deterministic emulation of a grader running at S steps/s: `sched(i) = min(119, floor(i/(0.1·S)))` if it differs from the previous value else None; after 120 refreshes return None (freeze). S∈{5,10,20,50,100,200,∞}.
- **R4 `all_frames`**: not a sim regime; the CPU NavStepper (Section 4.1) replays the action list against all 120 cached navmeshes and reports the union of collision steps and the set of final positions. Acceptance test for "zero collisions under any timing".
Scorer determinism check: R2/R3 runs must produce byte-identical per-episode outputs across two runs on different GPUs (Section 10 test T3).

### 3.3 Worker design (one long-lived process per (GPU, shard))
```python
def worker(gpu, shard):                                    # shard = (split, scan, [episode ids])
    env = build_env(gpu, shard, measurements=[DISTANCE_TO_GOAL, SUCCESS, COLLISIONS, COLLISIONS_DETAIL],
                    sensors=[DEPTH_2x2] if not shard.render else [RGB_224, DEPTH_256])
    env.havlnce_tool = ScheduledHAVLNCE(env.habitat_env._config, env.habitat_env._sim, regime.sched)
    for task in queue.claim_loop(shard):                   # BRPOPLPUSH jobs.replay:<scan> → processing:<worker>
        rows = []
        for ep in sorted(env.episodes, key=int):           # same order as exporter
            if ep.episode_id not in task.ids: continue
            obs = env.reset(); assert env.current_episode.episode_id == ep.episode_id
            frames, coll_steps, done = [], [], False
            for i, a in enumerate(task.actions[ep.episode_id]):
                obs, _, done, info = env.step(a)
                frames.append(env.havlnce_tool.frame_id)
                if info['collisions']['is_collision']: coll_steps.append(i)
                if done: break
            if not done: raise RuntimeError('neither STOP nor 500 steps')      # contract violation
            st = env.habitat_env.sim.get_agent_state()
            rows.append(dict(episode_id=ep.episode_id, scan=shard.scan, steps_executed=i+1,
                 stopped=(a=='STOP'), distance_to_goal=info['distance_to_goal'], success=info['success'],
                 collisions=info['collisions']['count'], collision_steps=coll_steps,
                 frames_seen=sorted(set(frames)), final_position=st.position.tolist(),
                 final_rotation=quat_to_coeffs(st.rotation).tolist()))
        write_atomic(result_path(task), dict(fingerprint=FP, regime=regime.id, rows=rows))
        queue.ack(task)
```
Notes: `info['distance_to_goal']` is `inf`-free (Euclidean). For the **test split** goals are absent → pass `goal_overrides` (our own goal hypotheses) by injecting `episode.goals=[NavigationGoal(position=…)]` before `reset()`; otherwise only collision metrics are produced. Keep `torch` out of the worker (not needed); set `OMP_NUM_THREADS=1`, `MAGNUM_LOG=quiet`, `HABITAT_SIM_LOG=quiet`.

Rendering choice: with `sensors=[DEPTH_2x2]` the renderer exists (needed for objects+navmesh) but costs ~nothing; use `[RGB_224, DEPTH_256]` only for the closed-loop *rollout* mode (Section 3.6) or when frame dumps are wanted.

### 3.4 Navmesh cache warm-up (mandatory before parallel replay)
- Job `navmesh.warm(scan)`: single process per scan, `frozen(k)` for k=0..119 with a 1-step episode each (any episode of that scan) → forces `recompute_navmesh` + `save_nav_mesh` for every frame; verify `load_nav_mesh` round-trip; write `navmesh_cache/<scan>/MANIFEST.json {frame: {sha256, bytes, navigable_area}}`. Patch the save to `.partial` + `os.replace`.
- Cost: Recast build over the joined MP3D stage mesh (0.2–2 M triangles) + ~10 human meshes (6,890 verts each) at 5 cm cells: **estimate 3–20 s per frame (low confidence; measure in bring-up step B2)** → 6–40 min per scan serial; 90 scans in parallel (8 procs/GPU → 12 GPUs, or fewer GPUs over a longer wall time) → **< 1 h total**. Only scans with humans need frames 1..119 (72 public + 18 test when the Phase-2 bundle lands); a scan without humans has one identical navmesh.
- Size: MP3D navmesh ≈ 0.5–5 MB → 10,800 files ≈ 10–50 GB.
- After warm-up: mount `recompute_navmesh` read-only into all replay/planning containers; the official code path then only `load_nav_mesh`s (5–20 ms each, ≤120 per episode).
- The Phase-2 bundle presumably adds `human_motion.json` entries for the 18 test scans (UNCONFIRMED); warm-up must be re-run for those scans the moment the bundle is published (≈ 30–40 min with 18 parallel processes) — schedule it as the first Phase-2 job.

### 3.5 Scoring and aggregation contract
Per-episode JSON row (above) → `aggregate(split, rows, collision_num, beta)`:
```
TCR_ep = max(0, collisions − collision_num[ep]); CR_ep = min(TCR_ep, 1); SR_ep = success·[TCR_ep==0]
SR = mean(SR_ep); NE = mean(distance_to_goal); TCR = mean(TCR_ep); CR = sum(CR_ep)/(beta·L)   (clip to 1)
Nav = 0.8·SR + 0.2·3/(3+NE); Social = 0.75·(1−CR) + 0.25/(1+TCR); Score = 100·Nav·(0.7+0.3·Social)
```
Also emit **per-episode marginal value** `ΔScore_ep` (Score with vs without that episode's SR/collision) so agents can rank which episodes to fix. Store `rows` keyed by `(fingerprint, regime, submission_sha256, split, scan)`.

### 3.6 Rollout mode (closed-loop agent runner, compliant tier)
Same worker, but actions come from a policy callback instead of a list: `action = policy(obs_rgb, obs_depth, pose, instruction, step)`; the executed trace becomes the submission row (exactly as the exporter does, L140-170). Only the forward camera, pose and instruction are exposed to the policy; the worker signs the row with `inputs_used=["rgb","depth","pose","instruction"]`. Policies run in a separate GPU process (vLLM/TGI/torch server) reached over ZeroMQ/HTTP to keep the Habitat process small; expect 1–3 s per VLM decision → use many parallel episode workers (the GPU renderer is idle most of the time, so 16–32 Habitat processes per GPU are fine when the policy is remote).

### 3.7 Official-mirror oracle
`docker run --rm --gpus … -v $DATA:/data/havln2:ro -v $NAVMESH:/data/havln2/recompute_navmesh -v $WORK:/workspace $IMAGE havln-score-phase1 --submission /workspace/sub.zip --output-dir /workspace/results --gpu-ids 0 1` (initial README). Run it (a) once per candidate submission on an *idle* machine to approximate the CodaBench grader, (b) 3× to measure run-to-run variance, (c) also under `nice`/CPU-throttling to emulate a slow grader. Compare with R0 and R3(S) to calibrate S for the official grader (expected 20–150 steps/s; unknown).

---

## 4. Component 2 — PLANNING service (navmesh / pathfinder / render out of the sim)

### 4.1 NavStepper (CPU, no GPU, exact kinematics on cached navmeshes)
`habitat_sim.nav.PathFinder` is standalone (`ShortestPathBindings.cpp:74-118`): `load_nav_mesh`, `find_path`, `try_step`, `try_step_no_sliding`, `snap_point`, `is_navigable`, `distance_to_closest_obstacle`, `closest_obstacle_surface_point`, `island_radius`, `get_random_navigable_point`, `build_navmesh_vertices/indices`, `get_topdown_view`, `navigable_area`. With the warmed cache we reproduce the agent kinematics without a Simulator:
```python
class NavStepper:                     # float32 throughout to track magnum
    def __init__(self, navmesh_path): self.pf = PathFinder(); self.pf.load_nav_mesh(navmesh_path)
    def step(self, p, q, action):     # p: np.float32[3], q: np.quaternion (body rotation)
        if action == 'MOVE_FORWARD':
            end = p + quat_rotate_vector(q, np.array([0,0,-0.25], np.float32))
            new = np.asarray(self.pf.try_step(p, end), np.float32)
            collided = (np.dot(new-p, new-p) + 1e-5) < np.dot(end-p, end-p)
            return new, q, collided
        if action in ('TURN_LEFT','TURN_RIGHT'):
            s = 1 if action == 'TURN_LEFT' else -1
            return p, (quat_from_angle_axis(s*np.deg2rad(15), np.array([0,1,0])) * q).normalized(), False
        return p, q, False            # LOOK_UP/LOOK_DOWN/STOP never move the body
```
(The sim rotates with `rotate_y_local` then normalises — mirror by right-multiplying a local-Y rotation and normalising.) Throughput: `try_step` is a Detour `moveAlongSurface` (tens of µs) → **≈ 20–60 k steps/s per core** (estimate). Validate bit-equivalence against the Simulator on ≥ 1,000 episodes (test T2); residual float drift is expected only at sliding contacts, so treat any trajectory with a NavStepper/Simulator mismatch as "fragile" and re-plan with more clearance.

Services built on it: `simulate(scan, start, actions, frames=[k…])` (all-frames sweep: 120 PathFinders ≈ 0.6 GB RAM per scan held in a per-scan worker), `union_navmesh(scan)` (0.05 m occupancy grid = AND over frames of `is_navigable`, plus `min_k distance_to_closest_obstacle`), `geodesic(scan, a, b, frame)`, `shortest_path_points`, `snap`, `clearance`, `island`.

### 4.2 Sim-backed renderer (GPU)
A per-scan `habitat_sim.Simulator` (not habitat-lab) with `enable_physics=False` (same as the challenge; objects still work), the HAPS templates loaded, `requires_textures=True`, sensors: RGB 224² HFOV 90 at [0,1.25,0] (habitat default camera height; confirm `POSITION` from `/app/config/challenge_submission.yaml` in bring-up B1), depth 256² (MIN 0, MAX 10, normalised), optional semantic and extra wide/high-res cameras for the **privileged tier only**. API: `render.at(scan, position, rotation, frame, sensors)` via `set_agent_state` + `get_sensor_observations` (`habitat_simulator.py:523-551 get_observations_at` semantics); `render.pano(scan, position, headings=24, pitches=[-30,0,30], frame)`; `humans.at(scan, frame)` → id, category, translation, rotation, AABB (from the object's scene node `cumulative_bb`); `topdown(scan, y, frame, mpp=0.05)` via `pathfinder.get_topdown_view`. Frame handling: `remove_object`/`add_object_by_handle` per frame, exactly the official code (`environments.py:171-213`), ≈ 10 objects × (1–5 ms) + first-time GLB loads (5–20 ms each, cached in-process).
Throughput: habitat-sim 0.1.7 README (Titan Xp): RGB+depth single process ≈ 1,000 FPS at 256² pure render; expect 300–800 renders/s per process on an A100/4090 including read-back; a full 24×3 panorama ≈ 0.1–0.25 s.

### 4.3 Robust-plan primitives the agents will want
- `clearance_cost(scan, grid)`: inflate obstacles of the **union navmesh** by r (0.05–0.15 m) → planning on the inflated grid yields trajectories whose `try_step` never slides in any frame (zero TCR regardless of grader speed). The planning-service `plan(scan, start_pose, goal, r, frames='all')` returns the discrete action list via a lattice search over (x,z,θ∈15° bins): node expansion uses `NavStepper.step` with the inflated-union PathFinder; cost = steps; constraints: ≤ 500 actions incl. STOP, STOP within 3 m Euclidean of the goal hypothesis, and optional "visit waypoints" for instruction following. Verify every emitted plan with `simulate(frames='all')` before it enters a submission.
- `goal_hypotheses(scan, instruction, …)` is out of scope here (other agents), but the service stores them under `/results/goals/<model>/<split>/<episode>.json` so the scorer can compute proxy NE/SR on test.

### 4.4 Compliance tags
Every endpoint is tagged `privileged` (navmesh, humans.at, pano at non-visited poses, goals from GT) or `compliant` (`render.at` only for poses on the executed trajectory; `pose`, `instruction`). A rollout started in compliant mode gets a token that the service enforces; the submission manifest records the mode. Until the organizers answer the open question on offline mesh use, treat all navmesh-derived planning at inference as *privileged*.

---

## 5. Component 3 — Storage layout and caching

```
/havln2/ (ro, official layout, ~45-70 GB)   mp3d habitat task data ≈ 15 GB; HAPS2_0 ≈ 116,640 files (est. 15-30 GB);
                                            HA-R2R json.gz, collision_num_*.json, human_motion.json, ckpt.39.pth
/navmesh_cache/<scan>/<scan>_<fff>.navmesh + MANIFEST.json      10,800 files, 10-50 GB, ro after warm-up
/renders/<scan>/<frame|static>/<pose_hash>/{rgb.jpg,depth.png16,meta.json}   viewpoints: 10,800 MP3D nodes ×
      24 headings × 3 pitches × ~80 KB ≈ 60 GB; arbitrary poses on demand (LRU, cap 500 GB)
/features/<extractor@version>/<scan>/<pose_hash>.npy (fp16)    e.g. 1024-d global: 0.26 GB per 10.8k×12 views;
      dense 16×16×1024: ~66 GB per extractor
/llm_cache/<provider>/<model>/<sha256(prompt+params+image_hashes)>.json   (also SQLite index; months-stable)
/submissions/<sha256>.json(.zip) + manifest.json (inputs_used, generator, parents)
/results/<fingerprint>/<regime>/<submission_sha>/<split>-<scan>.json  + aggregate.json
/registry/fingerprints/<fp>.json   /registry/jobs.sqlite (mirror of Redis state)
```
Keying rules: pose hash = sha1 of `(scan, frame, round(x,3), round(y,3), round(z,3), round(yaw_deg,1), pitch_deg, sensor_spec_hash)`; LLM key includes model id, system prompt hash, temperature/seed, tool schema hash and the sha256 of every image; features include extractor commit + weights sha. Content-addressed files are immutable; indexes (SQLite WAL or Postgres) map logical names → hashes.

---

## 6. Component 4 — Job queue for many agents (idempotent)

- **Redis** (single node, AOF) with one stream/list per queue: `jobs.replay`, `jobs.navwarm`, `jobs.plan`, `jobs.render`, `jobs.llm`, `jobs.rollout`; routing keys per scan so a worker pinned to scan X only claims `jobs.replay:X` (avoids scene reloads). Claim with `BRPOPLPUSH queue processing:<worker_id>`; ack = `LREM`; a reaper requeues tasks in `processing:*` whose heartbeat (`SET hb:<worker> EX 60`) expired.
- **Idempotency**: task id = sha256(canonical JSON of {kind, inputs by hash, regime, fingerprint}); result path derived from the id; before running, a worker checks the result path exists → ack immediately. Agents therefore can `submit()` the same job 50× safely. Partial results are written to `.partial` and renamed.
- **Priorities**: three queues per kind (`:p0` interactive, `:p1` batch, `:p2` sweeps); workers poll p0→p2.
- **Filesystem fallback** (if Redis is undesirable): `queue/<kind>/pending/<task_id>.json`, claim = `os.rename` into `processing/<worker>/`, which is atomic on POSIX/NFSv4; same reaper logic by mtime. Simpler but polling-based; fine for ≤ 1k tasks/min.
- **SDK** for agents (`havlnctl`): `havlnctl score sub.json --split val_unseen --regime frozen:0,frozen:60,frozen:119,schedule:20` → blocks until aggregate is ready; `havlnctl simulate --scan X --start … --actions …`; `havlnctl plan …`; `havlnctl render …`; `havlnctl llm …`; `havlnctl status <task_id>`; `havlnctl diff subA subB` (per-episode ΔScore).
- **Quotas**: per-agent concurrency caps (e.g. 64 replay shards in flight) and a GPU budget label per job so one agent cannot starve others.

---

## 7. Component 5 — Reproducibility and versioning

Runtime fingerprint (extends the exporter's `identity` L222-227): image digest; `habitat.__version__`/`habitat_sim.__version__`; sha256 of `habitat/sims/habitat_simulator/habitat_simulator.py`, `/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml`, `/app/config/challenge_submission.yaml`, our scorer package git sha; dataset hashes (`{split}.json.gz`, `human_motion.json`, `collision_num_{split}.json`); `navmesh_cache/<scan>/MANIFEST.json` sha for every scan touched; HAPS `haps-extracted.json` sha; regime id+params; goal-override set sha. Results from different fingerprints are never merged (mirror of exporter L99-101, L261-262). Submissions carry `manifest.json {generator, parents[], inputs_used[], fingerprint, created_at}`; a submission is "release-ready" only if (a) `havln-validate` PASS, (b) R4 all-frames TCR==0 for the episodes we claim collision-free, (c) R2 sweep success stable, (d) manifest compliance mode matches the intended claim.

Pin everything: the image by digest; HA-VLN source at `f46f93642d7ab96cc49611f8cfea09cecf2fa7f9` (toolkit `resources.json`); habitat-lab `d6ed1c0a…` for `habitat_baselines`; HF revision `c5f1cec1…` for data; MP3D files by sha256 list.

---

## 8. Throughput and capacity estimates (measure in B2; these are planning numbers)

| Item | Estimate | Basis |
|---|---|---|
| Max replay steps, test | 3,408 × 500 = 1,704,000 (realistic plans ≈ 100–200 actions → 0.35–0.7 M) | contract |
| Official-mirror worker, RGB 224 + depth 256 | 100–300 steps/s/process | habitat-sim 0.1.7 README ~1,000 render FPS at 256² RGB-D single process (Titan Xp) minus habitat-lab/measure/python overhead (~2–5 ms/step) |
| Official-mirror worker, 2×2 depth sensor | 300–800 steps/s/process | render cost ≈ 0; `try_step` + geodesic measure + python |
| NavStepper (CPU, PathFinder only) | 20–60 k steps/s/core | Detour `moveAlongSurface` µs-scale + python |
| Per-episode reset | 50–150 ms (humans frame 0 re-add ≈ 10 objects) | `environments.py:49-58`, `add_object` |
| Worker start-up | 15–60 s: 58,320 `load_configs` JSON (~10–30 s) + MP3D glb load (5–30 s) + EGL ctx | `environments.py:224-233` |
| Navmesh refresh (cache hit) | 10 obj remove/add + `load_nav_mesh` ≈ 20–80 ms | per refresh, ≤120/episode |
| Navmesh recompute (cache miss) | 3–20 s per frame (low confidence) | Recast at 5 cm over 0.2–2 M tri MP3D mesh |
| Cache warm-up, 90 scans × 120 | 9–60 CPU-hours; < 1 h wall with 90 parallel procs (needs GPU ctx: ~8 procs/GPU → 12 GPUs, or 4 GPUs for ~3 h) | above |
| GPU memory per Habitat process | 1–2.5 GB (MP3D + sensors; issue #681 reports 2.2 GB at 256² RGBD) | habitat-sim issue #681 |
| RAM per process | 2–4 GB | scene + 58k templates |
| **Full test replay, official-mirror, < 30 min** | 24 processes (18 scans; split the 4 largest scans into 2–3 chunks of ≤100 episodes), 3 GPUs × 8 procs, 24 cores, ~100 GB RAM → 1.7 M steps / (24 × 150 steps/s) ≈ 8 min + 1 min start-up | worst case 500 steps/episode |
| Full test replay, R3 `schedule(10)` wall-clock emulation (R1) | needs ≥ 95 procs to stay < 30 min (sleep-bound) → 12 GPUs × 8; or use R3 (deterministic, no sleeping) which runs at full speed | 1.7 M / (N × 10) |
| R4 all-frames sweep (CPU) | 3,408 × 150 × 120 ≈ 61 M steps → 20–50 core-minutes | NavStepper |
| Phase-1 val replay (2,617 eps) | ≈ 6 min on the same 24-process pool | |
| Render farm | 300–800 renders/s/process → the 10.8k-viewpoint × 72-view panorama set (0.78 M images) in ≈ 30 min on 4 GPUs × 8 procs | |

Recommended steady-state farm for a 10–60-agent team: **GPU tier A/B: 4 nodes × 8 GPUs (24 GB+)** running ~64 Habitat processes (replay + render), **GPU tier D: separate VLM/LLM serving pool**, **CPU tier C: 2 × 64-core nodes** for NavStepper sweeps and lattice planning, **1 Redis + 1 Postgres**, **shared FS ≥ 2 TB** (renders dominate). This is far below "unlimited"; the bottleneck is bring-up and correctness, not FLOPs.

---

## 9. Bring-up order and time estimates

| # | Step | Deliverable | Est. |
|---|---|---|---|
| B0 | Data: MP3D habitat task data (licence email → `download_mp.py --task_data habitat`, ~15 GB), `download_data.sh --target all` (HAPS2_0, val splits, annotations, ckpt), verify sha256s; `docker pull` image by digest; `havln-check-environment`, `havln-check-data` | `/havln2` populated, checks PASS | 0.5–1 day (MP3D approval latency dominates; start immediately) |
| B1 | Inspect the image: dump `/app/config/challenge_submission.yaml`, `/opt/havln-challenge/scoring/**` (read `havln_scoring` source: measurements, sensors, how `havln-score-phase1` seeds/threads/shards, whether it renders RGB-D, how frames are timed), `pip freeze`, patched `habitat_extensions`; record fingerprint v0 | `docs/image-contract.md` + diff vs public HA-VLN | 0.5 day |
| B2 | Micro-benchmarks inside the image: steps/s with RGB-D vs 2×2 depth; `recompute_navmesh` seconds per frame on 3 scans; `load_nav_mesh` ms; processes/GPU vs VRAM; NavStepper vs Simulator equivalence on 1,000 random action lists | `bench.json` feeding Section 8 | 0.5 day |
| B3 | Navmesh warm-up job (single writer per scan, atomic save, MANIFEST) for all 72 public scans; mount ro | complete cache | 0.5 day wall (parallel) |
| B4 | Deterministic Replay Scorer (regimes R0–R3), aggregate/Score, per-episode ΔScore, CLI; validate: CMA baseline submission (export via toolkit) scores ≈ 16.5/12.9 under R0 and under `havln-score-phase1`; T3 determinism | `havln-score` v1 | 1–1.5 days |
| B5 | Redis queue + result index + `havlnctl` SDK + heartbeats/reaper + per-agent quotas; worker pools as systemd/k8s DaemonSets pinned per scan | farm v1 | 1 day |
| B6 | NavStepper service (+ all-frames R4, union navmesh, clearance grids, geodesic, lattice planner) | planning v1 (CPU) | 1 day |
| B7 | Render/feature service (panoramas at MP3D viewpoints for 72 scans, arbitrary poses on demand, humans.at, topdown), caches | render v1 | 1 day |
| B8 | Rollout mode (policy callback over ZeroMQ), compliance tokens, submission manifests, `havln-validate` integration, oracle cross-check runner (3× `havln-score-phase1`, throttled variants) | end-to-end pipeline | 1 day |
| B9 | Phase-2 readiness: ingest bundle format (test episodes without goals; test-scan humans if provided), re-warm 18 test scans (< 1 h), goal-override plumbing for proxy NE/SR | ready on Oct 30 | 0.5 day on bundle release |
Total: ≈ 6–7 engineer-days of agent work, parallelisable to ~3 calendar days (B4/B6/B7 independent after B2).

---

## 10. Tests (all runnable in CI inside the image, GPU jobs nightly)

- **T1 contract**: `check_rows` rules (1–500 actions, STOP once at end, 500-step omission allowed per Q13), id coverage; property tests on random sequences.
- **T2 equivalence**: NavStepper vs Simulator (2×2 depth) on 1,000 random action lists × 3 scans × frames {0, 60, 119}: identical collision flags and final positions within 1e-4 m; report mismatch rate (expect 0; any >0.1 % blocks release).
- **T3 determinism**: R2/R3 replays byte-identical across 2 runs, 2 GPUs, 2 process counts.
- **T4 official parity**: CMA baseline → `havln-score-phase1` ×3 vs our R0 ×3 vs R3(S) sweep: Score within run-to-run spread; collision counts per episode compared under `frozen(k)` to locate timing-sensitive episodes.
- **T5 cache integrity**: every navmesh in MANIFEST loads, `navigable_area` within ±5 % of frame 0, sha stable; detect `.partial` leftovers.
- **T6 regression**: fixed 50-episode golden set with stored per-step poses/collisions per regime; any diff fails CI.
- **T7 queue**: idempotent resubmission, crash mid-shard → reaper requeue → identical result; fingerprint mismatch refuses merge.
- **T8 compliance**: a rollout in compliant mode cannot call privileged endpoints (token denied + logged); manifest lists only `rgb, depth, pose, instruction`.

---

## 11. Open questions and risks

1. Official grader speed S (determines which human frames matter). Mitigation: zero-collision plans under the all-frames union; T4 calibration; ask organizers whether `havln-score-phase1` on CodaBench renders RGB-D and on what hardware.
2. Will the Phase-2 bundle include test-scan human annotations? If not, local replay for test is navmesh-without-humans only; then the union-clearance margin must be raised (humans occupy ≤ ~0.6 m footprint).
3. Rules: is offline use of MP3D geometry/navmesh at inference permitted? The Oct-14 clarification lists inputs as pose + RGB-D only; ask explicitly on GitHub Issues/Discord; keep dual-mode infra.
4. Exact challenge yaml values (camera POSITION, depth MIN/MAX/NORMALIZE, TILT_ANGLE=30 reported by a competitor, which measurements/sensors the scorer enables) — read from the image in B1.
5. `recompute_navmesh` cost is unmeasured (3–20 s is an estimate); if ≫ 20 s, warm only frames {0..30} first (fast-grader range) and backfill.
6. Recast navmesh for humans standing on stairs/thin geometry may differ per frame in connectivity; the union grid handles this conservatively.
7. Redis as a single point of failure: AOF + the filesystem mirror of task state; results are on the FS anyway.

---

## 12. Appendix — JSON contracts

**ScoreRequest**
```json
{"kind":"replay","submission_sha256":"…","split":"val_unseen","scans":["2azQ1b91cZZ"],
 "episode_ids":null,"regime":{"type":"frozen","k":0}|{"type":"schedule","steps_per_s":20}|{"type":"wallclock_throttled","t_step":0.05},
 "sensors":"depth2x2","goal_overrides_sha256":null,"fingerprint_expected":"…","priority":"p1"}
```
**ScoreResult (per shard)**
```json
{"task_id":"…","fingerprint":"…","regime":{"type":"frozen","k":0},"split":"val_unseen","scan":"2azQ1b91cZZ",
 "rows":[{"episode_id":"17","steps_executed":143,"stopped":true,"distance_to_goal":1.82,"success":1,
          "collisions":0,"collision_steps":[],"frames_seen":[0],"final_position":[x,y,z],"final_rotation":[x,y,z,w],
          "TCR":0,"CR":0,"SR":1,"delta_score":0.0312}],
 "timing":{"steps_per_s":212.4,"reset_ms":71,"wall_s":338.1}}
```
**Aggregate**
```json
{"split":"val_unseen","n":1839,"beta":0.86623,"SR":0.129,"NE":6.387,"CR":0.684,"TCR":17.536,"Score":12.945387,
 "by_regime":{"frozen:0":{…},"frozen:119":{…},"schedule:20":{…}},"robust":{"all_frames_zero_tcr_episodes":1811}}
```
**Planning service**
```json
{"op":"simulate","scan":"…","start":{"position":[x,y,z],"rotation":[x,y,z,w]},"actions":["MOVE_FORWARD",…],
 "frames":"all"|[0,60,119],"navmesh":"official"|{"inflate_m":0.1,"union":true}}
→ {"per_frame":{"0":{"collision_steps":[],"final_position":[…],"path":[[x,y,z],…]},…},"any_collision":false}
{"op":"plan","scan":"…","start":{…},"goal":[x,y,z],"goal_radius":2.5,"inflate_m":0.1,"frames":"all","max_actions":480,
 "waypoints":[[x,y,z],…]} → {"actions":[…],"n":137,"verified":true,"clearance_min":0.21}
{"op":"render","scan":"…","frame":0,"poses":[{"position":[…],"yaw_deg":90,"pitch_deg":0}],"sensors":["rgb","depth"],
 "mode":"privileged"|"compliant","token":"…"} → {"items":[{"pose_hash":"…","rgb":"/renders/…/rgb.jpg","depth":"…"}]}
{"op":"humans_at","scan":"…","frame":k} → [{"id":"…","category":"…","translation":[…],"rotation_euler":[…],"aabb":[…]}]
{"op":"union_navmesh","scan":"…","mpp":0.05,"inflate_m":0.1} → {"grid":"/features/navgrid/<scan>/<hash>.npz","bounds":[…]}
```
**Submission manifest**
```json
{"submission_sha256":"…","generator":"planner-v3@git:abc123","parents":["…"],"mode":"privileged"|"compliant",
 "inputs_used":["rgb","depth","pose","instruction","navmesh","humans"],"fingerprint":"…","regimes_verified":["all_frames","frozen:0..119"],
 "havln_validate":"PASS","created_at":"2026-10-24T18:00:00Z"}
```

---

## 13. Sources (local paths and URLs)
- `$BASE/track2/README.md`, `$BASE/track2/scripts/export_cma_submission.py` (L48-173, L176-283), `$BASE/track2/scripts/{setup_cma.sh,resources.json,download_resources.py}`, `$BASE/track2-full` (`git show 2daf3dd:README.md` — initial README with `havln-score-phase1`, Local Docker Replay, data layout), `$BASE/track2-jostar` branch `origin/bohan/clarification-Oct14` (commits 0f944d3, 8289590: rules clarification diff).
- `$BASE/HA-VLN/HASimulator/{environments.py,measures.py,metric.py,config/*.yaml}`, `$BASE/HA-VLN/agent/VLN-CE/vlnce_baselines/common/{environments.py,base_il_trainer.py}`, `$BASE/HA-VLN/agent/VLN-CE/habitat_extensions/{task.py,measures.py,sensors.py,actions.py,discrete_planner.py,shortest_path_follower.py,config/default.py}`, `$BASE/HA-VLN/Data/HA-R2R-tools/collision_num_*.json`, `$BASE/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`, `$BASE/HA-VLN/scripts/{demo.py,human_scene_fusion.py,docker-quickstart-20261005.json}`.
- `$BASE/habitat-lab-0.1.7/habitat/{core/env.py,core/embodied_task.py,core/registry.py,core/dataset.py,config/default.py,tasks/nav/nav.py,tasks/vln/vln.py,sims/habitat_simulator/{habitat_simulator.py,actions.py}}`.
- `$BASE/habitat-sim-0.1.7/habitat_sim/{simulator.py,agent/agent.py,agent/controls/{object_controls.py,default_controls.py},nav/greedy_geodesic_follower.py}`, `src/esp/sim/Simulator.cpp` (reconfigure, addObject, recomputeNavMesh), `src/esp/nav/{PathFinder.h,PathFinder.cpp}`, `src/esp/bindings/{ShortestPathBindings.cpp,SimBindings.cpp,AttributesManagersBindings.cpp}`, `src/esp/physics/PhysicsManager.cpp`.
- `$BASE/competitor-bingchengzhang/project/havln_agent/{adapters/habitat_env.py,metrics.py,rollout.py,config.py}`.
- Web: https://github.com/roboworld2026/track2 ; https://github.com/JostarXiong/track2 ; https://github.com/facebookresearch/habitat-sim/tree/v0.1.7 (benchmark table) ; https://github.com/facebookresearch/habitat-sim/issues/681 (GPU memory per process) ; https://github.com/codalab/codabench/issues/2586 and https://docs.codabench.org/v1.23/codabench-docs.pdf (execution_time_limit default 600 s, public queue 20 min cap) ; https://arxiv.org/abs/2503.14229 (HA-VLN 2.0, Algorithm A2 dual-thread rendering).
