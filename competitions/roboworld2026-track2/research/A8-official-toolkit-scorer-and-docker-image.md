# A8 — Official toolkit, scorer and Docker image: reverse-engineering + "first 2 hours inside the container"

Topic id: `A8-official-toolkit-scorer-and-docker-image` · Date: 2026-10-24 · Author: research agent A8
`$BASE` = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`
New material fetched by this agent: `$BASE/a8/havln-challenge-full` (full 34-commit history + PR refs of F1y1113/havln-challenge),
`$BASE/a8/jostar-track2-full` (JostarXiong/track2 incl. branch `bohan/clarification-Oct14` = open PR #2 on roboworld2026/track2),
`$BASE/a8/worldnav-challenge` (Track 1, irrelevant), registry manifests in
`/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a8dl/manifests/` (all 8 tags + both pinned digests).

---

## 0. TL;DR — the decision-relevant findings

1. **The image ships a full local replay scorer, `havln-score-phase1`, plus `havln-check-environment`.** Both were documented in the toolkit until 2026-10-08 (commit `f73011d` in F1y1113/havln-challenge; `git show 2daf3dd:README.md` L240-306 in roboworld2026/track2) and then removed from the README by "streamlining". The pinned image (`e1a0544f…`) was the same digest throughout (pinned since the Sep-28 initial commit), so the CLI is in the image. Usage (verbatim from the old README): `havln-score-phase1 --submission /workspace/submission.zip --output-dir /workspace/results --gpu-ids 0 1`, data mounted read-only at `/data/havln2` and a separately writable `/data/havln2/recompute_navmesh`. It "computes the challenge metrics and Score". **This is our official-mirror oracle for val.** (high)
2. **There are two live image builds and they differ by one 33 KB layer.** `ghcr.io/jostarxiong/havln-challenge-2026` has 8 tags. The toolkit pins `@sha256:e1a0544f…` (= tag `v0.1.0-test-5e9ec54a924c`, 11 layers: one 6,106,231,833-byte base layer + ten small layers totalling 49,335 B). The HA-VLN repo/README, havln2 and havln2-docs pin `@sha256:78a62cd1…` (= tag **`cr-domain-20261004`**), which is byte-identical layer-for-layer plus **one extra 33,116-byte layer** (`429a799f…`) — almost certainly a re-install of the ~33 KB challenge package (cf. layer `3b2b1979…`, 33,123 B) with a change to the **CR "domain"** (the denominator/numerator set of the Collision Rate). Which one CodaBench runs is unknown and directly affects CR. (manifest facts: high; interpretation: medium)
3. **The challenge code is tiny and sits in small layers that can be fetched without Docker.** The ten small layers + config blob are ~55 KB. From this sandbox the registry API (manifests, tags) works but blob downloads 307-redirect to `pkg-containers.githubusercontent.com`, which the egress policy blocks (403) — so they must be fetched from the team's own machine. **Fetching `config` (`a8a8eca0…`, 5,986 B; `c03da97b…`, 6,236 B → full Dockerfile history) and layers `3b2b1979…` / `429a799f…` (33 KB each) is the single highest-value 5-minute action for this topic.** (high that it is cheap; medium that the scorer source is in those layers rather than in the 6.1 GB base layer)
4. **Reconstructed scorer = replay inside `HAVLNCEDaggerEnv` with wall-clock humans.** Everything visible (exporter mirrors the scorer's harness: same `/app/config/challenge_submission.yaml`, same `six_action_task.yaml`, scan-sharded jobs, `SEED 0`, `SHUFFLE False`, `EPISODES_ALLOWED`) implies: per episode `reset()` → for each action `step(name)` with `_handle_signals()` swapping in the per-frame human navmesh before every step (frame = wall-clock 0.1 s ticks since reset, frozen after 120 ticks) → measures `distance_to_goal` (**3-D Euclidean**, HASimulator override), `success` (STOP called and d < 3.0 m), `collisions.count` (every navmesh-shortened MOVE_FORWARD: walls, furniture and humans) → `TCR_ep = max(0, count − collision_num[ep])`, `CR_ep = min(TCR_ep,1)`, `SR_ep = success·[TCR_ep==0]` → SR/NE/TCR mean over L, CR over βL → Score. The organizers themselves state "Humans move in real time, so repeat runs can differ" (old README L324) and, in the Oct-14 clarification, that per-action wall time "is affected by runtime performance and hardware … replayed in the standardized organizer-controlled CodaBench environment". (high for structure; medium for exact measure list until the source is read)
5. **Validation contract (from exporter `check_rows`, README, docs history, unit tests):** flat ZIP (no parent folder/nested paths, no unsafe members), files identified by their JSON `split` value (filenames free, harmless extra root files allowed), each required split exactly once (Phase 1: `val_seen` 778 + `val_unseen` 1,839; Phase 2: `test` only), `format_version: 1`, every official `episode_id` (string) exactly once, `1 ≤ len(actions) ≤ 500`, actions ∈ {STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, LOOK_UP, LOOK_DOWN}, `STOP` at most once and only last, mandatory if `len < 500` (500 actions without STOP is legal but can never succeed). Message classes: `SUBMISSION REJECTED:` / `PASS:` / `SCORING DATA ERROR (organizer):`. (high)

Additional flags: (a) the toolkit's own test suite is stale — `tests/test_onboarding.py` L146-151 requires `--episode-limit 2` and `not a submission ZIP` in the README quick-start, both deleted on Oct 8, so `test_readme_has_no_manual_trainer_patch_and_keeps_named_container` fails (static analysis; not executed per safety rules); (b) Phase 1 (closes **Oct 30**) is scored on val with ground truth → **use 2–3 of the remaining Phase-1 submissions as scorer probes** (STOP-only probe resolves Euclidean-vs-geodesic NE and success; a wall-bump probe resolves "walls count in TCR") — see §7; (c) CONTEXT says the image is a "6.1 GB single layer" — it is one 6.1 GB layer **plus 10 (or 11) tiny layers**; (d) the Oct-14 clarification PR (unmerged) changes the rules picture (RGB-D + pose inputs, `human_motion.json` banned at inference) — see §2.8.

---

## 1. What was examined (all read in full)

| Item | Path / URL | Notes |
|---|---|---|
| Toolkit (current) | `$BASE/track2` (roboworld2026/track2 @ `2d408b2`, 2026-10-09) | README 347 lines; scripts/*.py; cma/*; tests; examples |
| Toolkit history | `$BASE/track2-full` (`2c804bb`→`2daf3dd`→`d4baf9e`→`2d408b2`) | `git show 2daf3dd:README.md` = pre-streamline README (503 lines) |
| Older toolkit + website | `$BASE/havln-challenge` (shallow) and **`$BASE/a8/havln-challenge-full`** (34 commits, Sep 23→Oct 8, + PR refs 1-4) | initial README (`8e36fa7`), `index.html` |
| Organizer fork + clarification branch | **`$BASE/a8/jostar-track2-full`** branch `origin/bohan/clarification-Oct14` (commits `0f944d3`, `8289590`, 2026-10-14) | = open PR #2 on roboworld2026/track2 (`refs/pull/2/head` = `8289590`, `refs/pull/2/merge` exists) |
| Upstream code | `$BASE/HA-VLN` (UWMILab/HA-VLN @ `3967752`, 2026-10-24; toolkit pin `f46f936` 2026-03-30) | HASimulator/{environments,measures,metric}.py, configs, VLN-CE env wrappers, trainer eval |
| Upstream docs | `$BASE/a10/JostarXiong_havln2-docs` (commit `55c79eb` removed 5 challenge pages) | challenge/{overview,getting_started,integration_guide,submission_format}.md in history |
| habitat-lab 0.1.7 | `$BASE/habitat-lab-0.1.7` (`d6ed1c0`, = toolkit's pinned habitat-lab revision) | Success, Collisions, registry, Env.step, HabitatSim |
| Competitor | `$BASE/competitor-bingchengzhang/project` | `scripts/extract_image_files.py` (registry-pull extractor), in-image measurement TILT_ANGLE=30 |
| Registry | `https://ghcr.io/v2/jostarxiong/havln-challenge-2026/{tags/list,manifests/<ref>}` (anonymous token) | fetched; blobs blocked (pkg-containers.githubusercontent.com → proxy 403) |
| Website | `$BASE/roboworld2026.github.io/track2.html`, `leaderboard.html` | "Closed-loop RGB-D", leaderboard "coming soon" |

WebSearch: three extended searches for `havln-score-phase1`, `havln_scoring`, CodaBench 18135 starting kit returned nothing beyond the GitHub READMEs (the CodaBench page itself is not indexed). The shared search budget was then exhausted.

---

## 2. Toolkit facts, file by file

### 2.1 README — current vs. history (what the organizers deleted)

Current README (`$BASE/track2/README.md`):
- L28-31: "Official scoring replays submitted action sequences in the released HA-VLN 2.0 Habitat 0.1.7 runtime"; L44 budget 1-500, all six actions count; L45 "Trusted simulator replay".
- L112: image `ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556`; L116-120 `docker run --name havln-cma --gpus all -it --shm-size 16g` with mounts `/data/havln2`, `/workspace`, `/toolkit:ro`.
- L126-127: `bash /toolkit/scripts/setup_cma.sh` then `havln-check-data`. L141-143 exporter. L154 `havln-validate …/submission.zip`.
- L241-250: STOP rules, split-by-`split`-value, "harmless extra root files", rejects "missing or duplicate required splits, invalid prediction content, unsafe ZIP members, and nested paths", Phase 2 "single required `test` split".
- L268-277: Q4 "Human animation follows released wall-clock behavior"; Q5 "`havln-validate` checks structure and coverage only. Local replay can compute metrics for development … Results from another machine are not accepted".
- L281-286: Q6 message classes `SUBMISSION REJECTED:` / `PASS:` / `SCORING DATA ERROR (organizer):`.

Pre-streamline README (`git -C $BASE/track2-full show 2daf3dd:README.md`), deleted on Oct 8 by `d4baf9e`:
- L96-102: table "Human-influenced episodes (βL)": val_seen **682**, val_unseen **1,593**; distinct trajectories 259 / 613 / train 3,603.
- L106-108: "Phase 2 provides test inputs for final evaluation, while reference trajectories and collision annotations remain withheld."
- L110-123: required data layout:
  ```
  /data/havln2/HA-R2R/{val_seen,val_unseen}/{split}_bertidx.json.gz   ("replay data", --target core)
  /data/havln2/HA-R2R-tools/collision_num_{val_seen,val_unseen}.json
  /data/havln2/Multi-Human-Annotations/human_motion.json
  /data/havln2/HAPS2_0/<released-human-assets>
  /data/havln2/scene_datasets/mp3d/<scan>/<scan>.glb
  /data/havln2/checkpoints/HA-VLN-CMA/ckpt.39.pth   # optional
  /data/havln2/recompute_navmesh/                   # writable replay cache
  ```
  L167-168: "`--target core` (the default) downloads replay data and human assets; `--target cma` downloads the checkpoint and its matching instruction-token inputs" ⇒ **the replay scorer reads `{split}_bertidx.json.gz`, the CMA exporter reads `{split}.json.gz`** (both pinned in `scripts/resources.json`).
- L210-217: `--episode-limit 2` diagnostic ("This writes diagnostic JSON files only, not a submission ZIP"); L228 `HAVLN_CMA_VERBOSE=1` for native simulator diagnostics.
- L240-257 **"Validate, replay, and submit"**: `havln-validate …` then `havln-score-phase1 --submission … --output-dir …/replay --gpu-ids 0`; "replay computes the challenge metrics and Score"; "The public-test and final phases use the same task and scoring algorithm".
- L259-306 **"Local Docker Replay"**: `docker run --rm "$IMAGE" havln-check-environment` (no GPU needed), `havln-check-data` with `-v $DATA_ROOT:/data/havln2:ro -v $NAVMESH_ROOT:/data/havln2/recompute_navmesh`, `havln-validate` with only `/workspace` mounted (⇒ the validator needs no data: it embeds the manifest), full replay with `--gpus '"device=0,1"' … havln-score-phase1 … --gpu-ids 0 1` ("GPU ordinals as seen inside the container"); "Local replay may generate navmeshes in the separately writable cache mount. Participant code may live anywhere … there is no required launcher".
- L316-325: CMA replay table (0.180/6.223/0.623/13.726/16.509450; 0.129/6.387/0.684/17.536/12.945387) and **"Humans move in real time, so repeat runs can differ."**
- L336-350: formal metric definitions; "CR divides by the released human-influenced episode count βL, while SR, NE, and TCR divide by all L episodes."

Initial README of the older repo (`git -C $BASE/a8/havln-challenge-full show 8e36fa7:README.md`, 2026-09-28):
- L15/L71-79: original prize pool **$2,800 (1st $1,500, 2nd $800, 3rd $500)** + Rising Star award — removed Oct 7 (`4a793d6`); current README: certificates + orals only.
- L51-57: original timeline Phase 1 Sep 30–Oct 31, Phase 2 deadline Nov 20 (superseded by Oct 15 / Oct 30 / Nov 30).
- L100: "Final-phase episode identities and submission coverage will be supplied with that phase's bundle."
- L180-192: **CodaBench "Phase 1 Starting Kit" contains a STOP-only `sample_submission.zip` with every required episode ID and a standard-library `check_submission.py`** ("verifies format and exact episode coverage, but computes no Score"). The website FAQ (`$BASE/havln-challenge/index.html` L253) still says "Use the format checker in the CodaBench starting kit".
- L198-242: the original "CMA action-export hook" for `base_il_trainer.py` (record `action_names[action_id]` before `envs.step`).
- L254-255: "The historical package name is only an image identifier".
- L310-314: "Organizer re-evaluation" table = paper numbers (0.165/6.230/0.638/13.271/15.469585; 0.114/6.502/0.689/22.352/11.944822), replaced Oct 2 (`5ad4380`) by the measured replay of exported actions.

### 2.2 `scripts/export_cma_submission.py` (306 lines) — what it reveals about the image

| Lines | Fact | Inference about the image / scorer |
|---|---|---|
| 13-16 | `SPLITS=('val_seen','val_unseen')`; 6-action tuple; ckpt sha `e70dce94…`; HA-VLN source revision `f46f936…` | |
| 36-45 | `check_rows`: exact ID set, no duplicates, `1≤len≤500`, all in vocab, `len<500 ⇒ last=='STOP'`, `'STOP' not in actions[:-1]` | identical to the validator's per-episode rule (and README L241-243) |
| 48-62 | imports image `habitat`, `habitat_sim` (asserts 0.1.7), then `habitat_extensions`, `vlnce_baselines`, `vlnce_baselines.common` **from the image**, then appends public-source dirs to `__path__` | the image contains *curated* copies of `habitat_extensions` and `vlnce_baselines` (env/config side), a "patched Habitat" core at `/app/habitat-lab`, and no policy code |
| 74 | `from havln_scoring.runtime import quiet_runtime` | scorer package `havln_scoring` exists; `quiet_runtime` silences native logs (`HAVLN_CMA_VERBOSE=1` disables) |
| 103-125 | env built from `get_config('/app/config/challenge_submission.yaml')`; overrides `EVAL.SPLIT`, `DATASET.{SPLIT,DATA_PATH,SCENES_DIR,EPISODES_ALLOWED}`, `HABITAT_SIM_V0.GPU_DEVICE_ID`, `SIMULATOR.{HUMAN_GLB_PATH,HUMAN_INFO_PATH,RECOMPUTE_NAVMESH_PATH}`, `TASK.SENSORS=[INSTRUCTION_SENSOR]`, **`TASK.MEASUREMENTS=[]`**, `SHUFFLE False`, `MAX_SCENE_REPEAT_STEPS -1`, `SEED 0`; asserts `POSSIBLE_ACTIONS == 6-tuple` | challenge config sets `ADD_HUMAN` (humans load from `human_motion.json`), six actions (⇒ `ACTION_SPACE_CONFIG v1`, `TILT_ANGLE 30` like VLN-CE RxR configs; competitor measured TILT 30 in-image, `config.py` L28). Measurements are disabled here *only* because the exporter does not score; the scorer must enable distance/success/collision measures. Test inputs lack goals, so the exporter also drops goal-dependent sensors (SHORTEST_PATH, VLN_ORACLE_PROGRESS) |
| 125-129 | `HAVLNCEDaggerEnv(config)`; episodes sorted by `int(episode_id)`; iterator replaced | env constructed per (split, scan) job ⇒ scene loaded at construction, never switched inside a job |
| 140-170 | per episode: `reset()`, up to 500 `step(name)`; **`if done and name!='STOP' and _elapsed_steps!=500: raise 'Unexpected early termination'`**; `if not done: raise` | the image's env ends an episode only on STOP or the 500-step limit (no early termination on collision) — the replay will consume every submitted action |
| 176-212 | `load_manifest('/opt/havln-challenge/codabench/phase1/reference/public_reference_manifest.json')` → `.splits[*].split/.episode_ids`; dataset IDs must equal manifest; jobs = one per (split, scan), sorted | image contains the CodaBench phase-1 bundle tree; the manifest is the source of truth for IDs; scan sharding is the organizers' standard pattern |
| 213-227 | fingerprint includes sha256 of `habitat/sims/habitat_simulator/habitat_simulator.py` ("simulator") and of `/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml` ("task") | the organizers consider the simulator wrapper and the six-action task file the two scoring-critical runtime files. Upstream habitat-lab v0.1.7 `habitat_simulator.py` sha256 = `d764666aafc437e381dc2d3e3567efe097ebf75fb5576470be16a7180cc5370c` → compare in-image to detect a patch |
| 232-253 | one subprocess per GPU, `jobs[i::n]` | multi-GPU pattern the scorer most likely shares (`--gpu-ids`) |
| 269-279 | full coverage ⇒ ZIP_DEFLATED flat zip `val_seen.json`,`val_unseen.json`, then `havln-validate` on it; `--episode-limit` ⇒ `*.diagnostic.json`, no ZIP | recommended packaging |

### 2.3 `tests/test_onboarding.py` (156 lines) — stale
- L26-35: manifest must be pinned (40-hex revisions, 64-hex sha) and **contain no `val_test` path and no `/train/` path** → the organizers' private test inputs are apparently named `val_test` somewhere (HF private path?) — the submission split value is nevertheless `test` (README L249-250).
- L130-136: `['LOOK_UP','LOOK_DOWN','STOP']` and `['MOVE_FORWARD']*500` legal; `[]`, `['MOVE_FORWARD']`, `['STOP','STOP']`, `['STOP']*501`, `['WAIT']` illegal.
- L138-142: missing / extra / duplicate IDs illegal.
- L144-152: README quick-start (text between `## 🚀 Getting Started` and `## 🐳`) must contain `--name havln-cma`, `havln-validate`, **`--episode-limit 2`** and **`not a submission ZIP`**, and must not contain `--rm` or `base_il_trainer.py`. The current README has no `## 🐳` heading and neither required string (`grep` returns nothing) ⇒ **this test fails on `main`**; the suite was not updated with the Oct-8 README rewrite. (Not executed — CONTEXT forbids running downloaded code; conclusion is from static reading, confidence high.)

### 2.4 Pins (`scripts/resources.json`, `prepare_cma_sources.py`, `setup_cma.sh`)
- HF dataset `fly1113/HA-VLN` revision `c5f1cec167964bda3ba343acc3a18e7aef8540dd`; GitHub `UWMILab/HA-VLN` revision `f46f93642d7ab96cc49611f8cfea09cecf2fa7f9` (2026-03-30; `HASimulator/{environments,measures,metric}.py` unchanged from that revision to HEAD — verified with `git diff --stat f46f936 HEAD`).
- 9 files: core = `HAPS2_0/HAPS2_0.zip` (`c5bc75ff…`), `val_{seen,unseen}_bertidx.json.gz` (`2e4fc230…`, `d1679b9f…`), `human_motion.json` (`21ef40ea…`), `collision_num_val_{seen,unseen}.json` (`632b5a47…`, `2c9111b1…`); cma = `val_{seen,unseen}.json.gz` (`c10d20cb…`, `0c2260a4…`), `ckpt.39.pth` (`e70dce94…`). The local HA-VLN clone's `human_motion.json` and `collision_num_val_seen.json` hashes match the pins (verified with sha256sum).
- `prepare_cma_sources.py` L11-16: HA-VLN tarball sha `2ea43d01…`, habitat-lab `d6ed1c0a0e786f16f261de2beafe347f4186d0d8` (the v0.1.7 version-bump commit, 2021-02-22) tarball sha `eb9a121a…`.
- `setup_cma.sh` L8-9: image python has `habitat` 0.1.7 importable with `PYTHONPATH=/app/habitat-lab`, **torch `2.0.1+cu118`**; L13-25: the image **lacks `habitat_baselines`** (restored by symlink + `.pth`); L28: refuses if the Habitat core path changes. Python is 3.8 (`HA-VLN/scripts/setup_docker_cma.sh` L5).
- `HA-VLN/scripts/docker-quickstart-20261005.json`: organizer smoke test on image `78a62cd1…` — HAPS files verified **116,640** (= 486×120×2), checkpoint 521 tensors, 1-episode/20-step pilots on both val splits, `"full_split_benchmark_reproduced": false`.

### 2.5 `cma/inference.yaml`
Four-action head `POLICY_ACTIONS: [STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT]`, vocab 5,401, ResNet50 RGB 256-d, depth ResNet50 128-d, GRU 512, progress monitor on. Only relevant here as proof that a 4-action subset is legal.

### 2.6 `havln-challenge` (older copy) + `index.html`
`$BASE/havln-challenge` scripts/cma/tests are byte-identical to the current toolkit (`diff` empty); README is the streamlined text. `index.html` adds: "Final rankings and awards are determined entirely by Phase 2 test evaluation"; "Only the CodaBench replay of the submitted ZIP determines the official score"; link "Docker runtime → Image and replay instructions" (`#-local-docker-replay`, now dead); FAQ 6 "format checker in the CodaBench starting kit … Submission & Evaluation page for validation and scoring-log explanations".

### 2.7 Website `track2.html` (current)
"Closed-loop RGB-D navigation"; "All submissions are scored server-side on the withheld test split. Test-split ground truth is not released."; TCR described as "Frequency of collisions in human-occupied zones" (wording ≠ code, see §4); leaderboard page "Coming soon".

### 2.8 Oct-14 clarification (open PR #2, `8289590`, not merged into `main` as of 2026-10-24)
Diff vs main (`git -C $BASE/a8/jostar-track2-full diff main origin/bohan/clarification-Oct14`):
- Input row → "Episode ID, initial pose, navigation instruction, ongoing agent pose (… GPS+compass), and sequential egocentric RGB-D observations. **Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference.**"; new row "Sensor Setup: One forward-facing RGB-D camera … panoramic views must be acquired by rotating in place (rotation actions count toward the action budget)."
- Sequences of exactly 500 actions may omit STOP.
- **Q4 rewritten: "Human animations advance with wall-clock time according to the configured motion FPS … there is no single fixed wall-clock duration for each action (including LOOK_UP and LOOK_DOWN). All official submissions are replayed in the standardized organizer-controlled CodaBench environment"** → confirms wall-clock humans in the official scorer and hints at a *configurable* FPS in the image's human module (upstream hard-codes `time.sleep(0.1)`).
- Q8 no extra cameras; Q9 pose readable; Q10 pretrained models/other datasets OK, val/test must not be used for training; Q11 no `human_motion.json` at val/test inference (train-time privileged use OK); Q12 closed APIs allowed but discouraged; Q13 STOP optional only at 500.

(Rules implications belong to C3; for this topic the point is that the scorer cannot detect any of this — it only replays actions — but award winners "may be asked to provide code".)

---

## 3. Image facts from the registry (verified 2026-10-24)

Anonymous token `https://ghcr.io/token?scope=repository:jostarxiong/havln-challenge-2026:pull` works; `tags/list` and `manifests/<ref>` work from this sandbox; `blobs/<digest>` returns 307 → `pkg-containers.githubusercontent.com` → **blocked by egress policy (proxy 403)**. Raw manifests saved under `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a8dl/manifests/`.

| Tag | Manifest digest | Config digest (size) | Layers | Layer-2 size |
|---|---|---|---|---|
| `v0.1.0-test-5e9ec54a924c` | **`e1a0544f66be…6556`** (toolkit pin) | `a8a8eca09a94…` (5,986) | 11 | 33,123 |
| `cr-domain-20261004` | **`78a62cd176d2…54f4`** (HA-VLN/havln2/havln2-docs pin) | `c03da97b6af7…` (6,236) | **12** = the 11 above + `429a799fdbf2…` (33,116) | 33,123 |
| `v0.1.0-test-39f161523ff1` | `243bb660d00b…` | `0751d75ff222…` (5,990) | 11 | 33,118 |
| `v0.1.0-test-9369033f32f8` | `4b2f417e2894…` | `4ac8167892e9…` (5,990) | 11 | 33,119 |
| `v0.1.0-test-764fce512e1d` | `74f1f037c278…` | `b50beef2ec93…` (5,987) | 11 | 30,947 |
| `v0.1.0-test-2dce90254f79` | `a25e5e49f652…` | `7da558378573…` (5,990) | 11 | 30,947 |
| `v0.1.0-test-4fbb6f95dd86` | `d9e718363daa…` | `8410e18d598b…` (5,988) | 11 | 30,945 |
| `v0.1.0-test-76ff69cde32a` | `00a8f71f3dcc…` | `216d01ade42e…` (5,987) | 11 | 31,139 |

Layer list of `e1a0544f` (all shared by `78a62cd1`): `708371e76802…` 6,106,231,833 B · `3b2b1979cbee…` 33,123 · `2084429b54a0…` 2,138 · `2f6f022707fb…` 5,102 · `c4e93db92bc7…` 2,505 · `8b720e9ef8c3…` 428 · `26e00dd060c7…` 658 · `f6326ac4f635…` 342 · `3ebcc8758cbe…` 4,245 · `344cb5e11e57…` 762 · `4f4fb700ef54…` 32 (the canonical empty layer). Total compressed 6,106,281,168 B (78a62cd1: 6,106,314,284 B). Full digests are in the JSON twin.

Inferences (medium): every build has a different 6.1 GB base digest with sizes differing by only hundreds of bytes ⇒ non-reproducible rebuild of a squashed base (OS + CUDA 11.8 + Python 3.8 + torch 2.0.1 + habitat-sim/lab 0.1.7); the 10 small layers are separate `COPY`/`RUN` steps for the challenge payload (`/opt/havln-challenge`, `/app/config`, console scripts, entrypoint); the ~33 KB layer is the `havln_scoring`/`codabench` payload (it grows from ~30.9 KB in four older test builds to ~33.1 KB in the three newest); `cr-domain-20261004` re-copies that payload with a CR-related change on Oct 4. The toolkit (Oct 8/9) never moved off `e1a0544f`, while the HA-VLN quick-start (Oct 5) uses `cr-domain`.

---

## 4. Reconstructed official scoring pipeline

```
CodaBench submission.zip ─► [validate]  (havln_scoring.submission_contract + manifest)
   │  flat zip, split-by-'split', format_version 1, exact IDs, 6-action vocab, 1..500, STOP rule
   │  → "SUBMISSION REJECTED: …" | continue
   ▼
[jobs] one job per (split, scan); episodes sorted by int(id); 1 process per GPU (--gpu-ids)
   ▼
env = HAVLNCEDaggerEnv(get_config('/app/config/challenge_submission.yaml') + overrides)
   TASK_CONFIG ← /opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml
   ADD_HUMAN True · HUMAN_INFO_PATH=/data/havln2/Multi-Human-Annotations/human_motion.json
   HUMAN_GLB_PATH=/data/havln2/HAPS2_0 · RECOMPUTE_NAVMESH_PATH=/data/havln2/recompute_navmesh
   DATA_PATH {split}_bertidx.json.gz (goals/start pose)  · MAX_EPISODE_STEPS 500 · SUCCESS_DISTANCE 3.0
   MEASUREMENTS ⊇ {DISTANCE_TO_GOAL (HASimulator Euclidean override), SUCCESS, COLLISIONS[_DETAIL]}
   HAVLNCE tool: loads 486×120 human templates, daemon thread puts a signal every 0.1 s (Queue max 120)
   ▼
for episode: env.reset()  → humans frame 0 (navmesh untouched), counters reset, timer starts
   for a in actions: env.step(a):
        _handle_signals(): if ≥1 pending signal and total_signals ≤ 120:
              frame=(total_signals−1)%120 → remove/add all humans at frame,
              load <scan>_<fff>.navmesh from cache (or recompute r=0.1 h=1.5 incl. static objects, save)
        habitat Env.step → MOVE_FORWARD: try_step on current navmesh (sliding) → collided flag
                           TURN/LOOK: no translation → never collide;  STOP: is_stop_called, no move
        measures update: distance_to_goal (3-D L2), success (STOP ∧ d<3.0), collisions.count += collided
   episode ends at STOP or 500 steps (exporter proves no other termination)
   ▼
per episode: TCR=max(0,count−collision_num[id]); CR=min(TCR,1); SR=success·[TCR==0]; NE=d_final
aggregate: SR=mean, NE=mean, TCR=mean over L; CR=ΣCR_ep/(βL)  [βL 682 / 1,593 / 2,859 — 'cr-domain' may change this]
Score=100·(0.8SR+0.2·3/(3+NE))·(0.7+0.3·(0.75(1−CR)+0.25/(1+TCR)))  full precision; ties SR↑ NE↓ CR↓ TCR↓ time↑
→ "PASS: …" (leaderboard: both val splits in Phase 1, ranked by val_unseen; test in Phase 2) | "SCORING DATA ERROR (organizer): …"
```

Evidence per stage: exporter L103-170 (harness); `HA-VLN/agent/VLN-CE/vlnce_baselines/common/environments.py` L48-75 (`HAVLNCEDaggerEnv.reset/step` call `havlnce_tool.reset()` before `super().reset()` and `_handle_signals()` before `super().step()`); `HA-VLN/HASimulator/environments.py` L49-58 (reset), L96-109 (0.1 s thread, increments only on successful put), L111-147 (frame selection, ≤120 cap, navmesh cache load/recompute with `agent_radius 0.1`, `agent_height 1.5`, `include_static_objects=True`, exceptions swallowed), L171-213 (STATIC human objects); `HA-VLN/agent/VLN-CE/habitat_extensions/measures.py` L16 + L28 (`from habitat.tasks.nav.nav import DistanceToGoal, Success` then `from HASimulator.measures import *` re-registers `DistanceToGoal`); `HA-VLN/HASimulator/measures.py` L100-155 (Euclidean `DistanceToGoal`), L158-180 (`CollisionsDetail`); `habitat-lab-0.1.7/habitat/tasks/nav/nav.py` L525-539 (`Success`: `is_stop_called and distance < SUCCESS_DISTANCE`), L653-672 (`Collisions`), `habitat/core/env.py` L187-233 (500-step limit), `habitat/sims/habitat_simulator/habitat_simulator.py` L360-370 (same-scene `reconfigure` is a no-op, so human objects and the last navmesh persist across episodes of a scan); `HA-VLN/HASimulator/metric.py` L12-17 (β constants, TCR/CR/SR); upstream trainer `base_il_trainer.py` L267, L393-394, L473-481 (per-episode `Calculate_Metric`, but **plain mean over episodes for CR — β unused**; the challenge README L336-350 explicitly divides CR by βL, so the challenge scorer is new code in `havln_scoring`, not the trainer).

Consequences that matter for us (all follow from the code; A2/A3/C1 agree):
- Frames seen by step t depend on the organizers' step rate: frame(t) ≈ min(119, ⌊elapsed(t)/0.1 s⌋), frozen at the last refresh once 120 ticks (~12 s) have elapsed. A fast scorer (e.g. 50 steps/s) never shows frames beyond ~50 over a 250-step episode; a slow one shows all 120 within the first ~12 s. ⇒ **plan against the union of all 120 frames** (swept volume) — timing cannot be exploited or reproduced exactly.
- The first step of every episode refreshes humans (a signal is always pending after reset). Because jobs are per scan and the scene is loaded at env construction, the "scene load > 12 s ⇒ no humans" edge case should not occur in the official scorer *if* it mirrors the exporter (verify).
- Navmesh cache cold vs warm changes the step rate (a recompute takes seconds and makes frames jump) ⇒ our local replays must use a pre-warmed cache, and still can't match the organizers' timing.
- The STOP step never collides; turns and looks never collide but cost budget and (wall-clock) time.

---

## 5. Validation rules (consolidated)

| # | Rule | Source | Conf. |
|---|---|---|---|
| Z1 | Upload one ZIP; predictions at ZIP root — no parent folder, no nested paths | README L248-249; Q6 L281-283 | high |
| Z2 | Unsafe members rejected (by analogy with the same authors' `safe_members`: absolute paths, `..`, backslashes, drive letters `C:`, duplicate names, symlinks) | README L248; `download_resources.py` L47-57 | high (that unsafe = rejected) / med (exact list) |
| Z3 | Files identified by JSON `split` value; names free; "harmless extra root files" allowed | README L246-248 | high |
| Z4 | Phase 1: exactly one JSON for each of `val_seen`, `val_unseen` (missing or duplicate required split ⇒ reject). Phase 2: single required `test` split | README L248-250 | high |
| J1 | `format_version == 1`, `split`, `episodes` list of `{episode_id, actions}` | README L228-239; docs history `submission_format.md` | high |
| J2 | Every official episode ID exactly once (val_seen 778, val_unseen 1,839, test presumably 3,408 = '1'..'3408'); no extras, no duplicates; IDs are strings | README L241, L282-283; exporter L36-39, L170; `collision_num_test.json` keys | high (strings safest; int IDs untested) |
| A1 | Each action ∈ {STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, LOOK_UP, LOOK_DOWN} (exact upper-case strings) | README L43; exporter L42; tests L130-136 | high |
| A2 | 1 ≤ len ≤ 500 (all six count) | README L44; Q3 | high |
| A3 | STOP at most once and only last; required when len < 500; optional at exactly 500 | README L241-243; exporter L43-44; PR #2 Q13 | high |
| A4 | A 500-action sequence without STOP is legal but `success` is impossible (`is_stop_called` False) | `nav.py` L532-536 | high |
| S1 | Validator checks structure + coverage only; never a Score | Q5 | high |
| S2 | Messages: `SUBMISSION REJECTED:` (fix ZIP) / `PASS:` (validation or replay succeeded) / `SCORING DATA ERROR (organizer):` (report submission id) | Q6 | high |

Packaging recommendation: Python `zipfile` with flat `arcname`, `ZIP_DEFLATED`, no directory entries, no `__MACOSX`, compact UTF-8 JSON without BOM, `allow_nan=False`, string IDs sorted numerically; run the CodaBench-image `havln-validate` **and** the starting-kit `check_submission.py` before every upload (rejections probably still consume one of the 5 daily slots — unverified).

---

## 6. Hypothesis table (claim → how to verify in the container → why it matters)

| ID | Claim (current belief, confidence) | How to verify in the container | Why it matters |
|---|---|---|---|
| H1 | `havln-score-phase1`, `havln-check-environment`, `havln-check-data`, `havln-validate` are console scripts of the `havln_scoring` package in `e1a0544f` (high) | `ls $(dirname $(which python)) \| grep havln`; `cat` each; `pip show -f` the owning dist; `entry_points.txt` | Local official-mirror scorer for val |
| H2 | The official replay harness = `HAVLNCEDaggerEnv` + `challenge_submission.yaml` + `six_action_task.yaml`, scan-sharded, sorted IDs (high) | read `havln_scoring` replay module; `grep -rn "HAVLNCEDaggerEnv\|get_config\|EPISODES_ALLOWED"` | Collision/timing semantics identical to upstream |
| H3 | Human frames are wall-clock (0.1 s/frame, freeze after 120 signals); possibly a configurable FPS key (high / med) | `grep -rn "sleep\|FPS\|fps\|monotonic\|time.time\|signal_queue"` over `/opt/havln-challenge /app` and the image's `HASimulator`; diff vs upstream `environments.py` | Swept-volume planning; no timing exploit; local vs official mismatch |
| H4 | Collision count = every navmesh-shortened MOVE_FORWARD, incl. walls/furniture (high) | grep `previous_step_collided`, `collisions`; replay `[MOVE_FORWARD]*20+[STOP]` into a wall far from humans → count ≈ 19-20 | Wall margin as important as human margin; TCR 14-18 baseline |
| H5 | `distance_to_goal` is 3-D Euclidean (HASimulator override), used by NE and Success (high from code) | `python -c "import habitat_extensions; from habitat.core.registry import registry; print(registry.mapping['measure']['DistanceToGoal'].__module__)"`; Phase-1 STOP-only probe (§7.3) | STOP-point optimisation; cross-floor/through-wall success |
| H6 | SR gate is `count ≤ collision_num[ep]` (allowance), not `count == 0` (high from code) | read metric code; replay an episode with collision_num=1 that bumps once and succeeds | Free collision budget in 60/159/237 episodes |
| H7 | CR = Σ_all-episodes min(TCR,1) / βL with β hard-coded (high for `e1a0544f`; the `cr-domain` image may restrict the numerator to human-influenced episodes or change βL) | grep `beta\|682\|1593\|2859\|549\|246` in both images; `diff -r` of `/opt/havln-challenge` between `e1a0544f` and `78a62cd1` | CR weight 0.75×0.3; CR can exceed 1 under the all-episode numerator |
| H8 | Phase-2 TCR baseline = public `collision_num_test.json` (sha256 `9069d5da…`, 3,408 keys, 237 non-zero) — or a withheld file (open) | look for `collision_num_test` / phase-2 references in image; Phase-2 bundle; ask organizers | Knowing per-episode allowances on test |
| H9 | Phase-2 bundle includes test `human_motion` entries for the 18 test scans (needed for anyone's local RGB-D rollouts; PR #2 Q11 says the file "is provided to support simulator rendering") (med) | inspect bundle; `python -c` count scans in the new `human_motion.json` | Local collision verification on test |
| H10 | The test reference (goals) is not in the image; CodaBench mounts private reference data; `codabench/phase2/` may exist without data (med) | `find /opt/havln-challenge -path "*phase2*"`; `grep -rn "reference" codabench/` | Whether any test GT leaks; how Phase-2 scoring is wired |
| H11 | The validator embeds the phase-1 manifest and needs no data/GPU (high) | run `havln-validate` with only `/workspace` mounted; read `submission_contract.py` | CI-able; Phase 2 needs an updated image/manifest → watch tags |
| H12 | Episodes end only on STOP or step 500 (high) | `MAX_EPISODE_STEPS` in `six_action_task.yaml`; replay 500 non-STOP actions | Every action is replayed; budget planning |
| H13 | `six_action_task.yaml`: `ACTION_SPACE_CONFIG v1`, `TILT_ANGLE 30`, `FORWARD_STEP_SIZE 0.25`, `TURN_ANGLE 15`, `ALLOW_SLIDING True`, `SUCCESS_DISTANCE 3.0`, RGB 224² / depth 256² HFOV 90 (high/med) | `cat` the file and `challenge_submission.yaml` | Exact kinematics for our offline stepper |
| H14 | Image `habitat_simulator.py` is patched vs upstream (sha ≠ `d764666a…`) (med) | `sha256sum`; `diff -ru` upstream `d6ed1c0` vs `/app/habitat-lab/habitat` | Any change to step/collision/reset semantics |
| H15 | Image `habitat_extensions` / `vlnce_baselines` / `HASimulator` are curated copies that differ from upstream (med) | `python -c "import X; print(X.__file__)"`; `diff -ru` vs `$BASE/HA-VLN` @ `f46f936` | Our stepper must replicate the image, not GitHub |
| H16 | `havln-score-phase1` writes per-episode results (success, distance, collision count, TCR) plus aggregates (med) | run on STOP-only sample; `ls -R` output dir | Per-episode local diagnostics; calibrate vs CodaBench |
| H17 | Navmesh cache is written lazily and non-atomically; cold runs are much slower (high from code) | time cold vs warm replay of one scan; `ls recompute_navmesh/<scan> \| wc -l` (expect 120 per scan) | Pre-warm cache; reproducibility |
| H18 | Repeated replays of the same ZIP differ (CMA: "repeat runs can differ") but a swept-volume-safe plan gives identical results (high) | replay same ZIP 3×, diff per-episode counts | Quantify nondeterminism; verify our robustness claim |
| H19 | CodaBench runs `e1a0544f` (toolkit pin) — or `78a62cd1` (cr-domain) (open) | ask organizers; compare Phase-1 probe CR with both local images | Which CR definition is official |
| H20 | The CodaBench starting kit has `check_submission.py` + STOP-only `sample_submission.zip` with all IDs (Phase 2 likewise) (med) | download from CodaBench Files tab | Fast ID manifest for Phase 2 |

---

## 7. "First 2 hours inside the container" checklist

### 7.0 Before docker (T−10 min, any internet-connected host, no Docker needed)
```bash
REPO=jostarxiong/havln-challenge-2026
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:$REPO:pull" | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s -H "Authorization: Bearer $TOKEN" https://ghcr.io/v2/$REPO/tags/list          # watch for new (phase-2) tags
mkdir -p blobs && cd blobs
for d in a8a8eca09a94f525e2b9d8be55e988190cfcd0145024f29accd7a2c6bbcadad1 \
         c03da97b6af72a40ab53ebc0a72cf9613e3fc6781fda395731ece84e45dea6b4 \
         3b2b1979cbee7da831e7a233f87c29eb0581d3e6ed9f6495a0f5c9f6e2de7844 \
         2084429b54a0a98608d19e55a66ebbbec55411ab9791046e3e8bb6b7e60e8527 \
         2f6f022707fbb2955f7a3a651b4cc62ac4aaab8cd21e87975884eb039a59636f \
         c4e93db92bc73758102495cd707c6d22e612ecaa2773355d53683cece4608a68 \
         8b720e9ef8c3261599dee91fd6f4faa5be422db850e6a0be70fda346ded4e543 \
         26e00dd060c795b282aa04d8835c281594a2e56ef5c5443e0e5c2a19a8c3573d \
         f6326ac4f635d1a45777436ab9935392c33e239fd100407c8ccfaf8aa8dbfa89 \
         3ebcc8758cbe993e3ee66ba74f604e59af958831a89b5658e2149cdac766c0c4 \
         344cb5e11e57ebe0e32b9486e6c14e4df2cdec96a6b582cd93d70e253e9ace69 \
         429a799fdbf23b7237d7bc93b6a311a21b1a31c2f7f89407592bb915979d7e1d; do
  curl -sL -H "Authorization: Bearer $TOKEN" "https://ghcr.io/v2/$REPO/blobs/sha256:$d" -o $d   # curl drops auth on the cross-host redirect
  echo "$d  $d" | sha256sum -c -
done
python3 -m json.tool a8a8eca0* | grep -A2 created_by    # Dockerfile history (COPY targets, ENV, ENTRYPOINT)
for d in 3b2b* 2084* 2f6f* c4e9* 8b72* 26e0* f632* 3ebc* 344c* 429a*; do echo "== $d"; tar -tzvf $d; done
mkdir L_3b2b L_429a && tar -xzf 3b2b* -C L_3b2b --no-same-owner && tar -xzf 429a* -C L_429a --no-same-owner
diff -ru L_3b2b L_429a          # = the "cr-domain" change
```
If the scorer is not in a small layer, it is in the 6.1 GB base layer → go to 7.1.

### 7.1 T+0–15 min: pull, inspect, dump (no data, no GPU)
```bash
A=ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556
B=ghcr.io/jostarxiong/havln-challenge-2026@sha256:78a62cd176d2fd7d0e2825f4cb5be2488ebc5f1a354649b7b4f536a98f1054f4
docker pull $A; docker pull $B
for X in A B; do I=${!X}; mkdir -p dump_$X
  docker image inspect $I > dump_$X/inspect.json            # Env, Entrypoint, Cmd, WorkingDir, Labels
  docker history --no-trunc --format '{{.CreatedAt}}\t{{.Size}}\t{{.CreatedBy}}' $I > dump_$X/history.tsv
  docker run --rm --entrypoint bash -v $PWD/dump_$X:/out $I -lc '
    env | sort > /out/env.txt; cat /etc/os-release > /out/os.txt; nvidia-smi -L 2>&1 | head -2 > /out/gpu.txt
    python -V > /out/python.txt 2>&1; which -a python python3 >> /out/python.txt
    python -m pip list --format=freeze > /out/pip_freeze.txt
    python - > /out/modules.txt 2>&1 <<EOF
import importlib
for m in ["habitat","habitat_sim","habitat_extensions","vlnce_baselines","vlnce_baselines.common.environments","HASimulator","HASimulator.environments","havln_scoring","habitat_baselines","torch","magnum"]:
    try:
        x=importlib.import_module(m); print(m, getattr(x,"__version__",None), getattr(x,"__file__",None), list(getattr(x,"__path__",[])))
    except Exception as e: print(m, "IMPORT-ERROR", repr(e))
import habitat_sim; print("bullet", getattr(habitat_sim,"built_with_bullet",None))
from habitat.core.registry import registry
import habitat_extensions
for k in ["DistanceToGoal","Success","Collisions","CollisionsDetail","DistanceToHuman"]:
    c=registry.mapping["measure"].get(k); print("measure",k,c and c.__module__)
EOF
    B=$(dirname $(which python)); ls -la $B | grep -i havln > /out/console_scripts.txt
    for s in $(ls $B | grep -i havln); do echo "=== $s"; cat $B/$s; done >> /out/console_scripts.txt
    find / -xdev -path "*site-packages*" \( -name entry_points.txt -o -name "*.pth" -o -name "*.egg-link" -o -name RECORD \) 2>/dev/null | xargs grep -il havln > /out/dist_files.txt
    find /opt/havln-challenge /app -xdev -type f | sort > /out/files.txt
    tar czf /out/opt_havln.tgz /opt/havln-challenge /app/config 2>/dev/null
    tar czf /out/app_py.tgz --exclude="*.so" --exclude="*.glb" /app 2>/dev/null
    for m in habitat_extensions vlnce_baselines HASimulator havln_scoring; do d=$(python -c "import $m,os;print(os.path.dirname($m.__file__))" 2>/dev/null) && tar czf /out/pkg_$m.tgz "$d"; done
    sha256sum /app/habitat-lab/habitat/sims/habitat_simulator/habitat_simulator.py \
      /opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml /app/config/challenge_submission.yaml > /out/sha.txt'
done
for X in A B; do mkdir -p dump_$X/x && tar xzf dump_$X/opt_havln.tgz -C dump_$X/x; done
diff -ru dump_A/x dump_B/x > cr_domain.diff; diff dump_A/sha.txt dump_B/sha.txt; diff dump_A/pip_freeze.txt dump_B/pip_freeze.txt
```

### 7.2 T+15–40 min: read the scorer (files to dump/read, in priority order)
1. `/opt/havln-challenge/scoring/havln_scoring/**/*.py` — especially `submission_contract.py` (`load_manifest`, ZIP/JSON rules), `runtime.py` (`quiet_runtime`), the replay/score module behind `havln-score-phase1`, check-data/check-environment modules.
2. `/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml` and `/app/config/challenge_submission.yaml` (BASE_TASK_CONFIG_PATH, ADD_HUMAN, MEASUREMENTS, MAX_EPISODE_STEPS, TILT, SUCCESS_DISTANCE, sensor sizes, any FPS key).
3. `/opt/havln-challenge/codabench/**` — `phase1/reference/public_reference_manifest.json` (fields: episode_ids, counts, file hashes, β/human-influenced lists?), scoring/ingestion programs, `metadata.yaml`, any `phase2`/`test` folder.
4. The image's `HASimulator/{environments,measures,metric}.py` (wherever they live) — diff vs `$BASE/HA-VLN` @ `f46f936`.
5. `/app/habitat-lab/habitat/**` — `diff -ru` vs habitat-lab `d6ed1c0` (sha `d764666a…` for `habitat_simulator.py`); also `nav.py`, `env.py`, `registry.py`.
6. Image `habitat_extensions/` and `vlnce_baselines/` (curated) — diff vs upstream.
7. `docker image inspect` → `Config.Env` (PYTHONPATH, EGL vars), `Entrypoint`.
Greps to run on the dump:
```bash
grep -rnE "sleep|FPS|fps|monotonic|time\.time|perf_counter|signal_queue|total_signals" .
grep -rnE "previous_step_collided|collisions|COLLISIONS|collision_num|is_collision" .
grep -rnE "beta|682|1593|1,593|2859|549\.0|246\.0|96\.0|human.?influenced|domain" .
grep -rnE "DistanceToGoal|geodesic|euclid|SUCCESS_DISTANCE|is_stop_called" .
grep -rnE "SUBMISSION REJECTED|SCORING DATA ERROR|PASS:|format_version|episode_ids|zipfile|is_symlink|S_ISLNK" .
grep -rnE "\btest\b|val_test|phase2|3408" .
grep -rnE "recompute_navmesh|load_nav_mesh|save_nav_mesh|include_static_objects" .
```

### 7.3 T+40–60 min: environment/data checks and validator fuzzing
- `docker run --rm $A havln-check-environment`; mount data (`-v $DATA:/data/havln2:ro -v $NAVCACHE:/data/havln2/recompute_navmesh`) and run `havln-check-data` (note exactly which files/hashes it demands — this is the Phase-2 data contract preview).
- Validator matrix (expected per §5; record actual): V1 STOP-only full coverage → PASS · V2 files in a folder → REJECT · V3 missing `val_unseen` → REJECT · V4 two files with `split: val_seen` → REJECT · V5 extra `README.txt` → PASS? · V6 renamed `a.json`/`b.json` → PASS · V7 integer `episode_id` → ? · V8 `MOVE_FORWARD`×500 → PASS · V9 501 actions → REJECT · V10 STOP mid-sequence → REJECT · V11 `stop` lower-case → REJECT · V12 extra ID → REJECT · V13 `format_version: 2` / missing → REJECT · V14 extra keys per episode → ? · V15 UTF-8 BOM / NaN → ? · V16 extra `test` JSON in Phase-1 zip → ? · V17 directory entries in zip → ? · V18 symlink member → REJECT · V19 `actions: []` → REJECT · V20 ZIP_STORED vs ZIP_DEFLATED vs LZMA → ? · V21 duplicate episode IDs → REJECT · V22 `"STOP "` with whitespace → REJECT.

### 7.4 T+60–90 min: replay calibration (val)
- R1 STOP-only full ZIP → `havln-score-phase1` → inspect output tree (per-episode fields?), runtime per scan, navmesh cache growth. Expect CR=TCR=0, NE = mean start→goal distance (compute Euclidean and geodesic ourselves from the episodes → which one matches?), SR = share of starts within 3 m.
- R2 CMA: `export_cma_submission.py --episode-limit 2`, then full export (≈2.6k episodes) → replay → compare to README (SR .180/.129, Score 16.51/12.95).
- R3 Replay the R2 ZIP three times (warm cache) → per-episode collision-count variance; one more with a cold cache.

### 7.5 T+90–120 min: decisive semantic probes (local) + plan official probes
- R4 wall probe: 20 episodes whose start faces a wall (pick from geometry) `[MOVE_FORWARD]*20+[STOP]` → count ≈ 19-20 ⇒ walls count (H4).
- R5 allowance probe: an episode with `collision_num ≥ 1`: oracle path + 1 deliberate wall bump → SR still 1 ⇒ H6.
- R6 Euclidean probe: stop ≤ 3 m straight-line but on the wrong side of a wall/floor → success? ⇒ H5.
- R7 timing probe: wrap `HAVLNCE._handle_signals` via a local `sitecustomize.py` on `PYTHONPATH` (inside our container only) to log `(episode, step, time, total_signals_sent, frame_id)`; measure our steps/s; repeat with CPU throttling (`--cpus 1`) to see the frame/step relation shift.
- R8 cr-domain: run R2 scoring under `$B` too; compare CR.
- Plan **official Phase-1 probes before Oct 30** (each costs 1 of 5 daily slots): P1 STOP-only (resolves NE metric and Euclidean success on the real worker, plus runtime/log format); P2 wall-bump on all episodes (resolves walls-in-TCR and allowance subtraction on the real worker; compare with local R4 counts); optionally P3 = the R2 CMA ZIP (calibrates local vs official, and e1a0544f vs cr-domain CR). Leaderboard rank in Phase 1 is irrelevant for awards (index.html: "Final rankings and awards are determined entirely by Phase 2").
- Write up: actual validator table, scorer source excerpts, diff A↔B, H1-H20 verdicts → update this file.

---

## 8. Implications

1. A faithful local scorer already exists (H1). Our deterministic stepper (C1) should be validated against `havln-score-phase1` per episode on val, and both against 2-3 official Phase-1 probes.
2. Official human timing is uncontrollable; only swept-volume-safe plans (all 120 frames) give reproducible zero collisions. Never tune margins to the frames seen in a local run.
3. Walls count (code-level certainty, to be confirmed by P2) ⇒ collision-free execution is mostly a wall-margin problem; success is gated by `count ≤ collision_num[ep]`.
4. Success/NE use straight-line 3-D distance (code-level; confirm by P1) ⇒ STOP placement should maximise P(‖stop−goal‖₂ < 3).
5. CR definition may differ between the two live images (`cr-domain`); since CR carries 0.225×Nav of the Score, the team must know which image CodaBench runs.
6. Phase 2 will need a new manifest (and probably a new image or bundle) — watch `tags/list` (works even from this sandbox) and the toolkit repo.
7. The toolkit is not a reliable spec by itself: README text was trimmed (scorer CLI, data layout, βL counts), tests are stale, and an open PR changes the rules text. Keep reading git history and PR refs, not just `main`.

## 9. Recommendations

1. Today: fetch config blobs + small layers (§7.0) on a team machine; diff `3b2b1979` vs `429a799f`. Then pull both images and run §7.1-7.2.
2. Before Oct 30: spend 2-3 Phase-1 submissions on probes P1 (STOP-only) and P2 (wall bump) (+P3 CMA) to pin NE metric, wall counting, allowance subtraction and CR definition on the real worker.
3. Build `submit.py` that (a) writes flat zips exactly like the exporter, (b) runs our strict validator (rules §5, rejecting anything with `?` in the fuzz table), (c) runs the image `havln-validate` and the starting-kit `check_submission.py`, (d) for val runs `havln-score-phase1` 2× and stores per-episode results with image digest + fingerprint.
4. Pre-warm `recompute_navmesh` (120 navmeshes × scan) once with a single writer, mount read-only for parallel replays (race noted in C1).
5. Ask organizers (GitHub issue / email): which image digest CodaBench uses; what `cr-domain` changed; whether the Phase-2 TCR baseline is the public `collision_num_test.json`; whether test `human_motion` is in the Phase-2 bundle; whether rejected submissions count toward 5/day; whether PR #2 rules are in force.
6. Add a cron (hourly) that polls `ghcr.io/v2/jostarxiong/havln-challenge-2026/tags/list` and the toolkit/HA-VLN repos (`git ls-remote`) and alerts on change.

## 10. Open questions
- Which image does CodaBench run (`e1a0544f` vs `78a62cd1`), and what exactly is the "cr-domain" change?
- Is `havln-score-phase1` byte-identical to the CodaBench scoring program, and does it print per-episode results?
- Is the image's human module the upstream one (0.1 s sleep) or a configurable-FPS variant ("configured motion FPS")? What FPS?
- Phase 2: file names (`test` vs `val_test`), episode IDs ('1'..'3408'?), test human placements in bundle, TCR baseline file.
- Is the image's `habitat_simulator.py` patched, and how?
- Does CodaBench count failed/rejected submissions toward the 5/day and 100/phase limits?
- Will PR #2 (rules clarification) be merged; does the "no human_motion.json at inference" rule extend to scene geometry/navmesh?

## 11. Corrections / flags vs CONTEXT.md
- CONTEXT fact 1/"Image facts": the image is **not** a single layer — 1 × 6.1 GB + 10 small layers (`e1a0544f`), 11 small layers for `78a62cd1`.
- CONTEXT fact 3 matches code; note the upstream trainer does **not** apply β (plain mean) — the β-normalised CR is challenge-scorer behaviour described only in README text (and possibly what `cr-domain` changes).
- CONTEXT fact 5 ("test collision annotations withheld"): `collision_num_test.json` (3,408 ids '1'..'3408', 237 non-zero, max 3, mean 0.082) has been public in UWMILab/HA-VLN since 2025-02-28 (`660e568`); whether the scorer uses it is unknown.
- CONTEXT fact 6/8: the open PR #2 (Oct 14) states RGB-D + pose inputs and forbids `human_motion.json` at inference — relevant to the "offline everything" hypothesis (C3 owns this).

## 12. Sources
- `$BASE/track2/README.md` (L28-31, 43-45, 112-157, 241-250, 264-286); `$BASE/track2/scripts/export_cma_submission.py` (L13-16, 36-45, 48-62, 74, 103-170, 176-227, 232-282); `$BASE/track2/tests/test_onboarding.py` (L26-35, 130-152); `$BASE/track2/scripts/{resources.json, download_resources.py L47-57, prepare_cma_sources.py L11-16, setup_cma.sh L8-29}`; `$BASE/track2/cma/inference.yaml`.
- `git -C $BASE/track2-full show 2daf3dd:README.md` (L96-123, 167-168, 210-257, 259-306, 316-350).
- `git -C $BASE/a8/havln-challenge-full show 8e36fa7:README.md` (L15, 51-57, 71-79, 100, 180-192, 254-255, 310-314); commits `1eecb7a`, `5ad4380`, `4a793d6`, `e83e355`, `f73011d`, `2bc1a92`; `$BASE/havln-challenge/index.html` (L230-253).
- `git -C $BASE/a8/jostar-track2-full diff main origin/bohan/clarification-Oct14` (commits `0f944d3`, `8289590`); `git ls-remote https://github.com/roboworld2026/track2` (refs/pull/2/head, refs/pull/2/merge).
- `$BASE/a10/JostarXiong_havln2-docs` commit `55c79eb` (removed challenge pages), `docs/api/evaluation_metrics.md` L13-43, `docs/api/collision_checks.md`.
- `$BASE/HA-VLN/HASimulator/environments.py` (L49-58, 96-147, 171-233), `measures.py` (L100-180), `metric.py` (L12-17), `config/HAVLNCE_task.yaml`; `agent/VLN-CE/vlnce_baselines/common/environments.py` (L48-75); `agent/VLN-CE/habitat_extensions/measures.py` (L16, L28); `agent/VLN-CE/habitat_extensions/task.py` (L62-90); `agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py` (L267, 393-394, 458-481); `README.md` L120-140; `scripts/{setup_docker_cma.sh, docker-quickstart-20261005.json, hf_resources.json}`; `Data/HA-R2R-tools/collision_num_*.json`.
- `$BASE/habitat-lab-0.1.7/habitat/tasks/nav/nav.py` (L500-539, 653-672), `habitat/core/env.py` (L187-233), `habitat/core/registry.py` (L43-60), `habitat/sims/habitat_simulator/habitat_simulator.py` (L222, 333-370, 564), `habitat/config/default.py` (L32, 54, 211, 218).
- `$BASE/competitor-bingchengzhang/project/{scripts/extract_image_files.py, havln_agent/config.py L28, havln_agent/adapters/habitat_env.py, docs/TRAINING.md L91-136}`.
- Registry: `https://ghcr.io/v2/jostarxiong/havln-challenge-2026/tags/list`, `…/manifests/{sha256:e1a0544f…,sha256:78a62cd1…, each tag}` (saved in `scratchpad/a8dl/manifests/`); blob host `pkg-containers.githubusercontent.com` blocked (proxy status log).
- Web: https://github.com/roboworld2026/track2 · https://github.com/JostarXiong/track2 · https://github.com/F1y1113/havln-challenge · https://www.codabench.org/competitions/18135/ (not fetchable here) · https://roboworld2026.github.io/track2
- Cross-checked with sibling findings `findings/A2-collision-semantics-habitat017.md`, `findings/C1-infra-and-replay-farm.md` (agree on harness, Euclidean distance, wall counting, public test collision_num, PR #2).
