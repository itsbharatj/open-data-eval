# A11: Data acquisition logistics (Matterport3D, HF fly1113/HA-VLN, auxiliary assets)

Agent: A11 · Date: 2026-10-24 (Sat) · Regime notes: everything here is needed for BOTH the compliant regime (closed-loop RGB-D + GPS/compass agent run locally) and the privileged/offline regime. Both regimes depend on running the 0.1.7 simulator locally, and that needs the MP3D meshes.

`BASE=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`. Downloaded reference copies are in `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/dl/a11/`.

---

## 0. TL;DR: the five decision-relevant findings

1. **MP3D is the only approval-gated item, and the official channel is slow or unmonitored.** The process is: sign the Terms of Use (TOS) PDF with an institutional email and send it to `matterport3d@googlegroups.com`. The approval reply contains `download_mp.py`.
   - Public evidence suggests the mailbox is effectively unattended. In niessner/Matterport #65 (Jan 2024 to Oct 2024) a user waited about a month with no reply, and the only workaround offered was "contact Anderson on his email … no one is using the official account email". Issue #74 (Jan 6, 2026: "sent the email, haven't received a reply") still has zero replies.
   - Send several requests today, from different academically affiliated members. Chase individual maintainers and the organizers in parallel. Check for existing institutional licences. (high)
2. **Only one 15 GB archive is needed: `mp3d_habitat.zip`** (`download_mp.py --task_data habitat`). It holds all 90 scans × {`.glb`, `.navmesh`, `.house`, `_semantic.ply`} plus a README.
   - The full 1.3 TB release (skyboxes, undistorted RGB-D, and so on) is not needed. It serves only the discrete HA-DE / MP3D-Sim stack, which this track does not use.
   - Habitat-sim 0.1.7 auto-loads the three sidecar files next to `<scan>.glb`. Keep all four files together. `_semantic.ply` + `.house` give the room/object labels that are valuable for privileged training-data generation. (high)
3. **Everything else downloads today with no approval**, sha256-pinned in `track2/scripts/resources.json`:
   - HF `fly1113/HA-VLN` @ `c5f1cec1…`: HAPS2_0.zip, 4 val files, ckpt.39.pth.
   - GitHub annotations: human_motion.json + 2 collision baselines. These are already in our clone and their hashes match.
   - HA-R2R **train**: deliberately not in the toolkit manifest. Get it from the same HF revision, `HA-R2R/train/train.json.gz`, sha256 `568f966e…`.
   - The 6.1 GB (compressed) docker image.
   - **The public Habitat example scene `17DRP5sb8fy` (dl.fbaipublicfiles.com `mp3d_example.zip`).** This scene has 10 annotated humans in `human_motion.json` and appears in R2R train (30 paths) and val_seen (2 paths). Full end-to-end bring-up (image, HAPS, navmesh cache, replay, rendering) can therefore run tomorrow, before MP3D approval arrives. (high)
4. **No HA-R2R `*_gt.json.gz` is released or needed.**
   - The toolkit manifest has no `_gt` files.
   - `HAVLNCE_task.yaml` points `NDTW.GT_PATH` at `HA-R2R/{split}/{split}_gt.json.gz`, but NDTW is commented out of MEASUREMENTS (L39, L52).
   - The exporter sets `TASK.MEASUREMENTS = []`.
   - The Score does not use nDTW. Val JSONs already carry `goals` and `reference_path`. Dense GT can be regenerated with the shortest-path follower, or borrowed from R2R-CE v1-3 preprocessed `_gt.json.gz` if episode IDs align (to verify). (medium-high)
5. **Storage and filesystem traps.**
   - HAPS2_0 extracts to **116,640 small files** (486 dirs × 120 frames × {.glb, .object_config.json}). Every simulator instance `load_configs`-es all of them and asserts exactly 120 per dir.
   - The directory names contain `:`. Put HAPS on **local ext4/xfs NVMe per node**: not NTFS/SMB/exFAT, and ideally not NFS.
   - The replay needs a **writable** `recompute_navmesh/` cache: up to 120 navmeshes per scan, 10,800 files in total, an estimated 10–50 GB.
   - Budget about 80–140 GB for the core data. Budget 1–3 TB for a full training/rendering program (the default DAgger LMDB map size is 1.2 TB).
   - HAPS2_0.zip size is **not publicly documented**. My estimate is 5–20 GB (low confidence). Measure it with the one-liner in §3.4. (high for the layout, low for the sizes)

---

## 1. Inventory: what exists, where, how big, how to verify

### 1.1 Pinned public resources (toolkit `scripts/resources.json`, identical in track2, track2-full, track2-jostar, track2-latest, havln-challenge and HA-VLN `scripts/hf_resources.json`)

| # | Path (HF rev `c5f1cec167964bda3ba343acc3a18e7aef8540dd` / GitHub UWMILab/HA-VLN `f46f93642d7a…`) | target | sha256 | Size | Notes |
|---|---|---|---|---|---|
| 1 | HF `HAPS2_0/HAPS2_0.zip` → `downloads/HAPS2_0.zip` | core | `c5bc75ffcec1b1b83b9ffc1f7177a02fabcdacbb6a0a7a02368afa5bbc209741` | **unknown**; est. 5–20 GB zipped, 15–20 GB extracted (low) | extracted to `HAPS2_0/` with top-level `human_motion_glbs_v3/` or `HAPS2_0/` prefix stripped; 116,640 files verified by organizers |
| 2 | HF `HA-R2R/val_seen/val_seen_bertidx.json.gz` | core | `2e4fc2305d25bca662780eb035afdf003eb38a0f799a34d32d5a6ccf2314aee7` | small (est. ≤ 5 MB) | BERT token ids; used by the replay/scorer layout |
| 3 | HF `HA-R2R/val_unseen/val_unseen_bertidx.json.gz` | core | `d1679b9f16c87012477fb15b5abaff4b20f8274a90912c5fdde5ef8a86c628aa` | small | |
| 4 | GitHub `Data/Multi-Human-Annotations/human_motion.json` | core | `21ef40ea91110eed5a7f41b59f1601122f2f4dc73e3a3e5a97fd203c8c9ff289` | **23,507,162 B** (measured) | already in `$BASE/HA-VLN`; sha verified identical today |
| 5 | GitHub `Data/HA-R2R-tools/collision_num_val_seen.json` | core | `632b5a47…70dc0` | 7,672 B (measured) | verified identical |
| 6 | GitHub `Data/HA-R2R-tools/collision_num_val_unseen.json` | core | `2c9111b1…6e5c0` | 19,122 B (measured) | verified identical |
| 7 | HF `HA-R2R/val_seen/val_seen.json.gz` | cma | `c10d20cb46f607c2c80c0f3f49b6e16c62caa6e8878d34a83533ec77d3f14f7c` | small | ordinary vocab tokens (CMA) + goals/reference_path |
| 8 | HF `HA-R2R/val_unseen/val_unseen.json.gz` | cma | `0c2260a4910ff1e81bc1eee28204bd7aedbc4ac26433d7268504ada20318b014` | small | |
| 9 | HF `checkpoints/HA-VLN-CMA/ckpt.39.pth` | cma | `e70dce940c6ae16aa63c41f3b2411884448a3ccd083b06da156d297b5f4a52dc` | est. 130–250 MB (521 tensors incl. ResNet50 RGB + depth encoder) | inference-only `{'state_dict'}` |

Sources: `$BASE/track2/scripts/resources.json` L1-15; `$BASE/track2/scripts/download_resources.py` L111-163; `$BASE/HA-VLN/scripts/hf_resources.json` L1-15; organizer verification `$BASE/HA-VLN/scripts/docker-quickstart-20261005.json` L26-30 (`"pinned_resources": 9, "haps_files_verified": 116640`). Local sha256 recomputed for #4-#6 (match).

### 1.2 Known extra HF files (not in the toolkit manifest)

- `HA-R2R/train/train.json.gz`, 10,819 episodes. The pinned-revision URL is `https://huggingface.co/datasets/fly1113/HA-VLN/resolve/c5f1cec167964bda3ba343acc3a18e7aef8540dd/HA-R2R/train/train.json.gz`, sha256 `568f966edab1fde96891b8c831bf5d1ba83f3658c4d868c8809cc779805cbf19`.
  - Source: competitor doc `$BASE/competitor-bingchengzhang/project/docs/TRAINING.md` L233-235 and `project/scripts/download_train.py` L1-18. Their note says "the official toolkit only downloads val, the train set must be pulled separately". There is also an `HF_ENDPOINT=https://hf-mirror.com` option for teams in China.
  - Confidence: medium-high. This is a third-party hash, so recompute it after download.
- Why train is excluded from the manifest: the toolkit test asserts `'/train/' not in path` and `'val_test' not in path` for every manifest entry (`$BASE/track2/tests/test_onboarding.py` L26-35). So train is excluded on purpose (the onboarding is inference-only). The `val_test` guard hints at a private test-input path name.
- The HA-VLN README (L326-345) says: "For the complete HA-R2R training inputs … `hf download fly1113/HA-VLN --repo-type dataset --local-dir Data`" and "HF hosts HA-R2R episodes, the HAPS archive, and the CMA checkpoint".
- Unknown: whether `train_bertidx.json.gz` exists, and whether any test file is present. Test is "reserved for our leaderboard, which we will release later" (F1y1113, HA-VLN issue #19, Dec 28 2025).

### 1.3 `*_gt.json.gz` (dense ground truth for nDTW)

**Verdict: not in the released HA-R2R set, and not needed for the Score.** (medium-high)

Evidence:
- The 9-file manifest has no `_gt` file.
- `$BASE/HA-VLN/HASimulator/config/HAVLNCE_task.yaml` L35-46 lists MEASUREMENTS with `# NDTW,` commented out (L39), while L51-52 keep `GT_PATH: ../Data/HA-R2R/{split}/{split}_gt.json.gz`.
- The challenge exporter sets `cfg.TASK.MEASUREMENTS = []` (`$BASE/track2/scripts/export_cma_submission.py` L118).
- The HA-VLN README dataset tree (L363-378) lists only train/val_seen/val_unseen folders.

Substitutes:
- (a) Use `goals` + `reference_path` from the val JSON (A1).
- (b) Use R2R-CE `R2R_VLNCE_v1-3_preprocessed/{split}/{split}_gt.json.gz` (Google Drive id `1fo8F4NKgZDH-bPSdVU3cONAkt5EW-tyr`, 250 MB, `$BASE/HA-VLN/agent/VLN-CE/README.md` L68-79). Only valid if HA-R2R episode IDs equal R2R-CE IDs; check by start_position/trajectory_id equality.
- (c) Regenerate dense GT with `ShortestPathFollower` along `reference_path` on the 0.1.7 navmesh, which is how VLN-CE built its own.

### 1.4 Google Drive legacy mirrors

- `HAR2R-CE.zip` id `1_-5StHsRP6REKrANMxKIscPtEP7sx-q0` and `HAPS2_0.zip` id `1gNdA4_mDAhW6g6Yedq2ypOR1N1sFpARB`. Sources: `$BASE/track2/scripts/download_resources.py` L130-138 and `$BASE/HA-VLN/scripts/download_data.sh` L41-51.
- The toolkit's `--source gdrive` path re-verifies that the Drive HAPS archive and the extracted val files carry the **same sha256** as the HF pins (L132-133, L153-154). So the Drive copies are byte-identical fallbacks.
- Folder links: top-level `1WrdsRSPp-xJkImZ3CnI7Ho90lnhzp5GR`, HA-R2R `1ci6Fwxa86uBbcVQy8qJlJRhgLjj12d1u`, HAPS `1y40El1gDpvBbooFRBbhMCQSPbcDNebHR`.
- Caveat: Google Drive enforces download quotas on popular large files ("too many users"). Use HF as the primary source.

### 1.5 Matterport3D (approval-gated)

| Item | Fact | Evidence | Conf. |
|---|---|---|---|
| Process | Sign the TOS PDF "using your institutional email addresses" and send it to `matterport3d@googlegroups.com`; "We will then provide download access" | `niessner/Matterport` README L30 (fetched raw), toolkit README Q7 L288-295 | high |
| TOS URL | `http://kaldir.vc.cit.tum.de/matterport/MP_TOS.pdf` (newer `vc.cit` host) or `kaldir.vc.in.tum.de/matterport/MP_TOS.pdf` | niessner README L30 vs L44; toolkit initial README L126 | high |
| What you get | Reply email contains `download_mp.py` (and `scans.txt` per BlenderProc docs); "once you receive access (with download links to download_mp.py …)" | allenai/embodied-clip `readme_files/baselines_habitat.md` L31; WebSearch summary of BlenderProc MP3D docs | high |
| License | Matterport EULA for Academic Use: non-commercial academic only; licensee = "you or the entity that you represent"; provide name, email and **academic institution** (2.4(c)); derived information incl. trained models also academic-only (2.4(a)(ii)); publishing derived info requires including or linking the agreement (2.4(b)); distributing a "substantial portion" requires each recipient to accept the terms via a signed document or click-wrap with records (2.4(b)); the licence auto-terminates on breach, after which all copies must be destroyed (§3) | full text at `crockwell/pixelsynth docs/LICENSE.md` L1-200 (copy saved at `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/dl/a11/pixelsynth_LICENSE.md`) | high |
| Turnaround | No official SLA. #65 (Jan 30 2024): "emailing for about a month … no one is replying"; Oct 22 2024: "You need to contact anderson on his email … no one using the official account email"; #74 (Jan 6 2026): no reply, 0 comments | github.com/niessner/Matterport/issues/65, /74 (WebFetch) | high (anecdotes), medium (generalisation) |
| Archive | `--task_data habitat` (argparse also accepts the `--task habitat` prefix) → `<out>/v1/tasks/mp3d_habitat.zip`; zip root = `mp3d/<scan>/{<scan>.glb,.navmesh,.house,_semantic.ply}` + `README.txt` | `download_mp.py` public copy L35-50, L93-105, L139-142; embodied-clip L36-39; CMU-VLA-Challenge README; AgentCanvas `fetch_data_vlnce.sh` L194-196; HA-VLN README L106-111 | high |
| Size | ≈ 15 GB (download ~30 min) | habitat-lab-0.1.7 README L163 ("MatterPort3D … 15 GB"); AgentCanvas script L175; real-stanford/cow README L95 ("~30min") | high |
| Full release | 1.3 TB (`RELEASE_SIZE`). Not needed. After the task download the script prompts "Press any key to continue on to main dataset download". Press Ctrl-C there: never pipe `yes` into it, or it starts the 1.3 TB download (`--id ALL` default) | `download_mp.py` L14, L146, L162-172; HA-VLN README L109 | high |
| Per-scan subset | Not possible for habitat task data: it is one zip covering all 90 scans (`--id` filters raw scan types only) | `download_mp.py` L93-105, L155-161 | high |
| Python | Original is Python 2 (`print '\t'…`, `urllib.urlretrieve`, no resume). The organizers "locally verified" a Python 3 helper | `download_mp.py` L70-80; `docker-quickstart-20261005.json` L39-53 | high |
| 90 scenes | 61 train (val_seen ⊂ train scans, 56) + 11 val_unseen + 18 test = 90; matches `connectivity/` (90) | computed from `$BASE/HA-VLN/HASimulator/HA-DE/tasks/R2R/data/R2R_*.json` + connectivity dir | high |

**Not needed: full MP3D (skyboxes, undistorted color/depth, camera params).** These feed the discrete MP3D-Sim / HA3D (HA-DE) stack only. HA-DE README: `--type matterport_skybox_images undistorted_camera_parameters undistorted_depth_images`. MP3D-Sim README: "At minimum you must download the matterport_skybox_images".

Track 2 is continuous (Habitat VLN-CE), and every view can be rendered from the habitat `.glb`. Discrete-VLN transfer models (DUET/ScaleVLN/HAMT) ship precomputed features (Dropbox/HF), and those features are also MP3D-licensed. If a photoreal-pano experiment is ever wanted, it can be fetched later per scan with `--id <scan> --type matterport_skybox_images`. (high)

**Habitat-sim 0.1.7 sidecar behaviour.** The stage manager derives `<scan>.navmesh`, `<scan>.house` and `<scan>_semantic.ply` from the `.glb` path (`$BASE/habitat-sim-0.1.7/src/esp/metadata/managers/StageAttributesManager.cpp` L205-219). The navmesh is loaded at init if present (`src/esp/sim/Simulator.cpp` L147-161; otherwise only "Navmesh file not found" is logged). HA-VLN then recomputes it with humans as static objects. Keep `.navmesh` (episode reset/oracle sensors use the pathfinder before humans are added) and the semantic files (privileged labels). `mp3d.scene_dataset_config.json` is **only** needed for Habitat ≥ 0.2 stacks (StreamVLN/JanusVLN 0.2.4, SimpleVLN 0.3.3). Get it from `http://dl.fbaipublicfiles.com/habitat/mp3d/config_v1/mp3d.scene_dataset_config.json` (habitat-sim main `DATASETS.md` L177).

### 1.6 Public MP3D example scene (no approval): bring-up accelerator

- `http://dl.fbaipublicfiles.com/habitat/mp3d_example.zip` unzips (`-d data/scene_datasets/mp3d/`) to `17DRP5sb8fy/17DRP5sb8fy.glb` (+ sidecars). Evidence: `$BASE/habitat-sim-0.1.7/examples/tutorials/nb_python/ECCV_2020_Navigation.py` L42 and L161, and habitat-lab 0.1.7 tests.
- The newer `mp3d_example_v1.1.zip` is listed in habitat-sim main `datasets_download.py` L135-140 (uid `mp3d_example_scene`).
- `17DRP5sb8fy` has **10 humans** in `human_motion.json` (verified). It appears in R2R train (30 paths) and val_seen (2 paths → ~6 HA-R2R val_seen episodes, inferred).
- This is enough to bring up the challenge image end to end, with HAPS loading, navmesh cache, replay and RGB-D rendering with humans, before MP3D approval. It is not enough for submissions.
- Caveat: the toolkit exporter checks scene files for every episode it will run (`export_cma_submission.py` L206-209). Use a custom runner with `DATASET.EPISODES_ALLOWED` set to the 17DRP5sb8fy ids.

### 1.7 Auxiliary assets (all public, no approval; licence notes)

| Asset | Where | Size | Needed for |
|---|---|---|---|
| Challenge image `ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66be…` | GHCR | 6,106,231,833 B base layer + ~50 KB of small layers (compressed); est. 15–20 GB on disk | official-mirror replay; `havln-validate`, `havln-check-data`, `havln-score-phase1` |
| NB: the HA-VLN README quick-start uses a **different** digest `…@sha256:78a62cd176d2…` | HA-VLN README L126 | | use the toolkit digest for anything score-related |
| DD-PPO depth encoders `ddppo-models.zip` | `https://dl.fbaipublicfiles.com/habitat/data/baselines/v1/ddppo/ddppo-models.zip` (or the single file `…/ddppo-models/gibson-2plus-resnet50.pth`) | 672 MB zip (contains `data/ddppo-models/*.pth`) | only to train CMA-style depth encoders from scratch; CMA inference uses `ddppo_checkpoint: NONE` (`$BASE/track2/cma/inference.yaml` L32); default path `../Data/ddppo-models/gibson-2plus-resnet50.pth` (`default.py` L251-253). **Avoid the `*mp3d-train-val-test*` variants**: they were trained on MP3D val/test scenes, which is a contamination risk under the "no val/test training" rule (habitat-lab ddppo README L33-41) |
| R2R-CE `R2R_VLNCE_v1-3.zip` / `_preprocessed.zip` | GDrive `1T9SjqZWyR2PCLSXYkFckfDeIs6Un0Rjm` / `1fo8F4NKgZDH-bPSdVU3cONAkt5EW-tyr` | 3 MB / 250 MB | original R2R-CE instructions (test start poses), `_gt` files, `joint_train_envdrop` aug |
| RxR-CE `RxR_VLNCE_v0.zip` | `https://storage.googleapis.com/rxr-habitat/RxR_VLNCE_v0.zip` (+ optional 142 GB BERT features) | GBs | extra training data (allowed: "Datasets from other sources are permitted", clarification Q10) |
| ScaleVLN data/features/models | HF `OpenGVLab/ScaleVLN` (`r2r_preprocess_data.zip`, `features.zip`, `r2r_trained_models.zip`) | GBs | discrete-VLN transfer (B1) |
| SOTA VLN-CE weights | per B2: SimpleVLN (HF `honglyhly/SimpleVLN_*`, Habitat 0.3.3), ETP-R1, InternVLA-N1 (HF `InternRobotics/*`), CWP waypoint predictor `check_cwp_bestdist_hfov90` | ~20 GB per 8–9B VLM | closed-loop policy track |
| GloVe 6B 50d | nlp.stanford.edu | 822 MB zip | only to rebuild `embeddings_glove_50d.json.gz` (already shipped, `$BASE/HA-VLN/Data/HA-R2R-tools/README.md`) |

---

## 2. Layout the image expects (mount contract)

```
$DATA_ROOT  (mount at /data/havln2; may be :ro)
├── HA-R2R/{train,val_seen,val_unseen}/{split}.json.gz + {split}_bertidx.json.gz   (test/ arrives in Phase 2)
├── HA-R2R-tools/collision_num_{val_seen,val_unseen}.json   (+train/test from the GitHub repo)
├── Multi-Human-Annotations/human_motion.json   (72 scans now; expect 90 in Phase 2: clarification Q11 says the file "is provided to support simulator rendering")
├── HAPS2_0/<region:activity>_<idx>/{0..119}.glb + .object_config.json   (486 dirs, 116,640 files)
├── scene_datasets/mp3d/<scan>/<scan>.{glb,navmesh,house} + <scan>_semantic.ply   (90 dirs)
├── checkpoints/HA-VLN-CMA/ckpt.39.pth
├── downloads/{HAPS2_0.zip, haps-extracted.json}
└── recompute_navmesh/<scan>/<scan>_<fff>.navmesh   ← must be WRITABLE (separate mount OK)
```

Sources:
- `$BASE/track2/scripts/export_cma_submission.py` L110-116, L184-186, L206-209.
- Initial toolkit README (`git -C $BASE/jostar-track2 show 2daf3dd:README.md`) L111-123 ("recompute_navmesh/ # writable replay cache") and L274-302 (`-v $NAVMESH_ROOT:/data/havln2/recompute_navmesh`).
- Same README L203-206: "For scenes stored elsewhere, bind-mount them into a real `/data/havln2/scene_datasets/mp3d` directory rather than a nested directory symlink" (symlink targets must also be mounted).
- HAPS loader `$BASE/HA-VLN/HASimulator/environments.py` L215-233: `load_configs(dir)` on every dir, then `assert add_num == 120`. A single partially extracted directory crashes the simulator.
- Template suffix: `object_config.json` (`$BASE/habitat-sim-0.1.7/src/esp/metadata/managers/ObjectAttributesManager.h` L26).
- Navmesh cache: `environments.py` L131-144. The cache is created on first use per (scan, frame) and loaded afterwards. Concurrent writers to the same file are a race (inference), so pre-warm with one process per scan.

Filesystem rules:
- HAPS dir names contain `:` (e.g. `bedroom:Walking_0`). The toolkit insists on a Linux/WSL filesystem (README L103) and tests colon names explicitly (`test_onboarding.py` L94-105). Use ext4/xfs; avoid NTFS, exFAT and SMB.
- 116,640 small files are read at every environment construction. Use a local NVMe copy per node (inference: NFS metadata latency would multiply the 10–30 s start-up estimated by C1).

---

## 3. Day-by-day acquisition plan (critical path = MP3D)

### D0: Sat Oct 24 (TODAY). Send everything gated, start everything ungated.

**A. MP3D requests (human lead + every academically affiliated member, 30 min):**
1. Download the TOS PDF (link on https://niessner.github.io/Matterport/; hosts `kaldir.vc.cit.tum.de` or `kaldir.vc.in.tum.de`). Fill in the signature fields (name, institution, email, date, signature).
2. Email it **from an institutional address** to `matterport3d@googlegroups.com`.
3. **Send ≥ 3 independent requests from different members/institutions.** Each approved person is individually licensed, which also legally covers intra-team access (EULA 2.4(b)/(c)).
4. Template:
   > Subject: Matterport3D Terms of Use – request for download access (Habitat task data) – <Name>, <Institution>
   > Body: "Please find attached the signed Matterport3D Terms of Use. I request access to the Matterport3D dataset (specifically the Habitat task data, mp3d_habitat.zip) for non-commercial academic research: the RoboWorld 2026 / NeurIPS RoboPAD HA-VLN challenge (deadline Nov 30). Name / Institution / Position / Supervisor / institutional email."
5. Log the send timestamps in the ops tracker.

**B. Existing-licence sweep (same hour).** Ask lab-mates, the institution's HPC/shared-datasets team and collaborators whether a licensed `mp3d_habitat` copy already exists. Habitat/VLN-CE groups almost always have one. Use it only if the licence covers you:
- the licensee is your institution/entity, or you sign it yourself;
- the use is non-commercial academic;
- the data stays on licensed infrastructure.
For cross-institution sharing, each recipient must accept the EULA in writing (2.4(b)) and their name/email/institution goes to Matterport (2.4(c)). Ask the research office if unsure.

**C. Organizer and maintainer pings (15 min).**
- GitHub issue on `roboworld2026/track2` (0 issues today) plus email to `roboworld2026@gmail.com`:
  - (1) Is there an expedited MP3D channel? Many participants will hit #65/#74.
  - (2) Phase-2 bundle contents: test `{split}.json.gz`/`_bertidx`, test-scan human_motion (90-scan file?), HF revision, and delivery channel while CodaBench is down.
- Optionally cc the HA-VLN maintainers (`yfeidong@uw.edu`, `fyiwu@uw.edu`, `bohanx2@uw.edu`, HA-VLN README L598).
- MP3D maintainers: issue #65 indicates the group account is unmonitored and suggests emailing an individual ("Anderson", presumably Peter Anderson, not confirmed). Use publicly listed academic addresses of the Matterport3D paper authors (Chang, Dai, Funkhouser, Halber, Niessner, Savva, Song, Zeng, Zhang, niessner README L20). Do not guess addresses.

**D. Ungated downloads (infra agent; start immediately, in parallel; ~1–3 h wall):**

```bash
DATA_ROOT=/nvme/havln2            # ext4/xfs, local NVMe
IMAGE=ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556
# 1) image (6.1 GB compressed)
docker pull "$IMAGE" &
# 2) pinned public resources (9 files, sha256-verified, resumable, HAPS auto-extract → 116,640 files)
git clone https://github.com/roboworld2026/track2 && bash track2/scripts/download_data.sh --destination "$DATA_ROOT" --target all --dry-run
bash track2/scripts/download_data.sh --destination "$DATA_ROOT" --target all &
# 3) HA-R2R train (not in manifest) at the SAME pinned revision
REV=c5f1cec167964bda3ba343acc3a18e7aef8540dd
mkdir -p "$DATA_ROOT/HA-R2R/train"
curl -fL --retry 5 -C - -o "$DATA_ROOT/HA-R2R/train/train.json.gz" \
  "https://huggingface.co/datasets/fly1113/HA-VLN/resolve/$REV/HA-R2R/train/train.json.gz"
echo "568f966edab1fde96891b8c831bf5d1ba83f3658c4d868c8809cc779805cbf19  $DATA_ROOT/HA-R2R/train/train.json.gz" | sha256sum -c -
# 4) full HF inventory with sizes (answers the HAPS-size and train_bertidx/test questions in one call)
python - <<'PY'
from huggingface_hub import HfApi
api = HfApi()
for rev in ("c5f1cec167964bda3ba343acc3a18e7aef8540dd", "main"):
    for f in api.list_repo_tree("fly1113/HA-VLN", repo_type="dataset", recursive=True, revision=rev):
        print(rev[:7], f.path, getattr(f, "size", None), getattr(getattr(f, "lfs", None), "sha256", None))
print([ (c.commit_id[:7], c.created_at, c.title) for c in api.list_repo_commits("fly1113/HA-VLN", repo_type="dataset")][:10])
PY
#    (quick alternative for one file: curl -sIL <resolve-url> | grep -i -E 'x-linked-size|content-length')
# 5) mirror the rest of the pinned HF revision (e.g. train_bertidx if present) into a side dir
hf download fly1113/HA-VLN --repo-type dataset --revision "$REV" --local-dir "$DATA_ROOT/_hf_snapshot" &
# 6) public MP3D example scene for bring-up (NOT a substitute for the licensed data)
mkdir -p /nvme/mp3d_example && curl -fL -o /nvme/mp3d_example/mp3d_example.zip http://dl.fbaipublicfiles.com/habitat/mp3d_example.zip
# 7) code at pinned revisions (setup_cma.sh / prepare_cma_sources.py pin HA-VLN f46f936… and habitat-lab d6ed1c0a…)
# 8) optional, parallel: R2R-CE v1-3 (+preprocessed) via gdown; ddppo gibson-2plus-resnet50.pth; mp3d.scene_dataset_config.json;
#    RxR-CE; SOTA policy weights chosen by B2 (SimpleVLN / ETP-R1 / InternVLA-N1 / CWP)
```

**E. Verification (same day).**
- `download_resources.py` aborts on any sha256 mismatch and refuses to overwrite mismatching files (L31-43). HAPS is CRC-checked per member, with `downloads/haps-extracted.json` written with `{"files": 116640}`.
- Record `sha256sum` of every non-manifest file (train, R2R-CE, ddppo, example scene) in `$DATA_ROOT/SHA256SUMS`, and store the HF `list_repo_tree` output.
- In the image: `docker run --rm "$IMAGE" havln-check-environment`, then `havln-check-data` with `-v $DATA_ROOT:/data/havln2:ro -v $NAVMESH:/data/havln2/recompute_navmesh`. It is expected to fail only on the missing MP3D scans.

### D1: Sun Oct 25. Bring-up on 17DRP5sb8fy; chase MP3D.
- Place the example scene at `scene_datasets/mp3d/17DRP5sb8fy/`.
- Run a custom runner (EPISODES_ALLOWED = HA-R2R train/val_seen ids in that scan) inside the image. Measure:
  - HAPS template-load time on local NVMe vs NFS;
  - `recompute_navmesh` seconds per frame and the `.navmesh` size (this turns the 10–50 GB cache estimate into a number);
  - steps/s with RGB-D.
- Confirm humans render, and confirm that `previous_step_collided` fires on human contact.
- If there is no MP3D reply yet, the second member resends with a different subject line.

### D2–D3: Mon Oct 26 – Tue Oct 27. MP3D download (if approved).
1. Read the URL in the emailed `download_mp.py` (task file `v1/tasks/mp3d_habitat.zip`). Download it with that script, or, being authorized, with a resumable client: `curl -C - -o mp3d_habitat.zip <url>`. Run `curl -sI <url> | grep -i accept-ranges` first. If Range is supported, `aria2c -x4 -s4` is fine.
2. Expect ~15 GB in ~30 min.
3. Answer Ctrl-C at the "main dataset" prompt.
4. Run `unzip -t`, then `unzip mp3d_habitat.zip -d $DATA_ROOT/scene_datasets`. Then verify:

```bash
cd $DATA_ROOT/scene_datasets/mp3d && ls | wc -l          # expect 90
for s in */; do s=${s%/}; for f in $s.glb $s.navmesh $s.house ${s}_semantic.ply; do [ -s "$s/$f" ] || echo "MISSING $s/$f"; done; done
comm -3 <(ls | sort) <(ls $BASE/HA-VLN/HASimulator/HA-DE/connectivity | sed 's/_connectivity.json//' | sort)   # expect empty
find . -type f -print0 | sort -z | xargs -0 sha256sum > ../MP3D_SHA256SUMS   # team-internal integrity list (hashes only, never files)
```

5. If two members download independently, compare the SHA256SUMS. MP3D publishes no official hashes, so cross-copy agreement is the integrity check.
6. Copy the data to local NVMe on each licensed compute node.
7. Warm the navmesh cache: val_unseen 11 scans × 120 frames = 1,320 files first, then the 61 train scans.

### D4–D5: Wed Oct 28 – Thu Oct 29.
- CMA reproduction on val (needs the 67 val scans).
- Phase-1 pipeline test submission if CodaBench is reachable.
- Write and test the **Phase-2 ingest script**: poll every 15 min for new HF commits (`list_repo_commits`), toolkit/HA-VLN GitHub commits, and the CodaBench/Discord announcements.
- On a new bundle: download, sha256, diff `human_motion.json` (expect 72 → 90 scans), add `HA-R2R/test/`, run `havln-check-data`, warm the test navmesh cache (18 × 120 = 2,160 files), and run a STOP-only `havln-validate`.

### D6: Fri Oct 30 (Phase 2 opens).
- Ingest the bundle within about 2 h.
- If MP3D is still missing, escalate daily (organizers, other maintainers, more requesters).

### Nov 7: hard trigger (from C2).
- With no MP3D by Nov 7, the mesh-free fallback becomes primary (C2 §9). It is weak:
  - In the compliant regime, a closed-loop RGB-D agent cannot be run at all without meshes, because there is nothing to render.
  - Only open-loop heuristics from public assets remain: nav-graph connectivity for all 90 scans, R2R test start viewpoints, HA-VLN 1.0 human anchors for the test scans.
- Keep requesting MP3D in parallel. Switching back costs about 1 h of download plus about 1–2 h of navmesh warm-up.

---

## 4. Storage budget

| Item | Size | Confidence |
|---|---|---|
| Docker image | 6.1 GB pull (compressed), est. 15–20 GB on disk | high / low |
| `mp3d_habitat.zip` (keep a cold copy) | ~15 GB | high |
| Extracted MP3D (90 × 4 files) | est. 15–20 GB (textures are already compressed) | medium-low |
| `HAPS2_0.zip` (kept: the downloader re-verifies or re-downloads it if missing) | unknown; est. 5–20 GB | low |
| Extracted HAPS2_0 (116,640 files; SMPL mesh 6,890 verts / 13,776 faces ≈ 0.25–0.33 MB per GLB × 58,320) | est. 15–20 GB | low-medium |
| `recompute_navmesh/` (≤ 120 frames × 90 scans = 10,800 files) | est. 10–50 GB (measure on D1) | low |
| HA-R2R json.gz (all splits), annotations, ckpt | < 1 GB | high |
| R2R-CE preprocessed + ddppo zip | 0.25 + 0.67 GB | high |
| **Core subtotal** | **≈ 80–140 GB** | |
| Render/feature caches (C1) | 60–500 GB | low |
| DAgger feature LMDB (`IL.DAGGER.lmdb_map_size = 1.2e12` default, `default.py` L107) | 0.2–1.2 TB if training CMA/ETPNav-style | medium |
| VLM/VLA weights (8–9B bf16 ≈ 16–20 GB each; 72B ≈ 145 GB) | 50–300 GB | medium |
| **Program total (recommended provisioning)** | **2–4 TB shared NVMe + ≥ 150 GB local NVMe per compute node** | |

---

## 5. Legal and compliance notes (MP3D EULA + challenge rules)

**Facts:**
- Matterport3D is under the Matterport EULA for Academic Use of Model Data. The licence is non-commercial academic only and revocable. Derived information (models, renders, features) is also academic-only.
- Publishing derived information requires including or linking the agreement. Put the TOS link in the technical report.
- Distributing a substantial portion requires each recipient to accept the terms with records kept, and their details must be provided to Matterport. The licence terminates automatically on breach, and all copies must then be destroyed (EULA 2.2, 2.4, 3; `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/dl/a11/pixelsynth_LICENSE.md` L1-114).
- Downstream projects state "we are not legally allowed to re-distribute the MP3D scene assets" (real-stanford/cow README L90). The toolkit says: "Matterport3D requires separate authorized access" and "is not included in this repository, helper script, image, or submission kit" (toolkit README L317-321; initial README L143-144).

**Rules for the team:**
1. Never redistribute scene files, renders in bulk, or features outside licensed members.
2. Do not use unofficial mirrors (third-party HF/GDrive/Baidu copies). Also do not use the `kaldir…/v1/tasks/mp3d_habitat.zip` URL visible in public copies of `download_mp.py` before your own approval. That is unlicensed use, and award winners must publish a technical report and may be asked for code, so it is a real disqualification and reputational risk.
3. Only academically affiliated members can sign. The user's own email is a gmail address. If the team has no academic affiliation, partner with an academic co-author whose institution signs, and keep MP3D on that institution's infrastructure. (inference)
4. Grey area (inference, low confidence): sending MP3D-rendered images to closed third-party APIs. It is not "publishing", but it ships derived data off-premises. Prefer open-weight local VLMs, which the organizers also encourage.
5. Do not train on DD-PPO checkpoints trained on MP3D val/test, given the "HA-R2R val/test must not be used for training" rule (clarification Q10). Use `gibson-2plus-resnet50.pth`.

---

## 6. Facts vs inferences (summary)

**Verified facts:**
- The pinned manifest: 9 files, revisions and hashes.
- Local annotation hashes match.
- Train is excluded from the manifest on purpose.
- The train URL/hash is recorded by a third party (recompute it).
- The HAPS layout is 486 × 120 × 2 = 116,640 files, with an assert of 120 per dir and the object_config.json suffix.
- The MP3D process, the archive name and contents, ~15 GB, and the 1.3 TB full release.
- The prompt trap in `download_mp.py`.
- The sidecar auto-loading in habitat-sim 0.1.7.
- The example scene `17DRP5sb8fy` is public and has 10 humans.
- ddppo is 672 MB and is not needed for CMA inference.
- NDTW is disabled and no `_gt` is in the manifest.
- The test split is reserved for the leaderboard (issue #19).
- MP3D approval anecdotes (#65, #74).
- The writable navmesh cache.
- The image layer size.

**Inferences / estimates:**
- HAPS2_0.zip size (5–20 GB).
- Extracted MP3D size (15–20 GB).
- Navmesh cache size (10–50 GB).
- ckpt size (130–250 MB).
- That HA-R2R `_gt` files do not exist on HF at all (we cannot list the HF tree from this sandbox).
- That the example-scene glb is coordinate-identical to the habitat-task version.
- That the Phase-2 bundle will include test-scan human annotations (strongly implied by Q11, "provided to support simulator rendering").
- The identity of "Anderson".

**No contradictions with CONTEXT.md facts found.** One refinement: the CONTEXT says HF hosts "val_seen.json.gz, val_unseen.json.gz, *_bertidx.json.gz, HAPS2_0.zip, ckpt.39.pth". HF also hosts `HA-R2R/train/train.json.gz` at the same pinned revision.

## 7. Open questions
1. Exact sizes of HAPS2_0.zip and ckpt.39.pth, and the full HF file tree (does `train_bertidx.json.gz` exist? any `_gt`? any test file already?). Run the §3 D0 step 4 snippet on a machine with HF access.
2. Phase-2 bundle: file names, whether `human_motion.json` will cover all 90 scans, the HF revision bump, and the delivery channel if CodaBench is still down.
3. Do HA-R2R episode IDs equal R2R-CE v1-3 IDs, so that R2R-CE `_gt.json.gz` and test start poses can be joined directly?
4. Does the TUM server support HTTP Range (parallel/resumable download)?
5. Is the current emailed `download_mp.py` Python 3? The organizers mention a "locally verified Python 3 helper".
6. Does the official CodaBench scorer use `{split}_bertidx.json.gz` (the initial README layout lists only bertidx under HA-R2R) or `{split}.json.gz`? Ship both.
7. Actual per-frame navmesh size and recompute time (measure on D1 with 17DRP5sb8fy).

## 8. Sources
- `$BASE/track2/README.md` L91-104, L159-175, L288-295, L317-321; `$BASE/track2/scripts/resources.json` L1-15; `$BASE/track2/scripts/download_resources.py` L24-163; `$BASE/track2/scripts/export_cma_submission.py` L104-131, L176-209; `$BASE/track2/cma/inference.yaml` L1-39; `$BASE/track2/tests/test_onboarding.py` L26-35, L94-105
- `$BASE/jostar-track2` `git show 2daf3dd:README.md` L90-146, L196-206, L255-302; branch `bohan/clarification-Oct14` README Q10/Q11
- `$BASE/HA-VLN/README.md` L101-119, L121-139, L300-378, L598; `$BASE/HA-VLN/scripts/{hf_resources.json,download_hf.py,download_data.sh,docker-quickstart-20261005.json,test_quickstart.py}`; `$BASE/HA-VLN/Data/*/README.md`; `$BASE/HA-VLN/Data/HA-R2R-tools/README.md`
- `$BASE/HA-VLN/HASimulator/environments.py` L83-144, L171-233; `$BASE/HA-VLN/HASimulator/config/HAVLNCE_task.yaml` L1-57; `$BASE/HA-VLN/agent/config/cma_pm_da_aug_tune.yaml`; `$BASE/HA-VLN/agent/VLN-CE/vlnce_baselines/config/default.py` L107, L251-253; `$BASE/HA-VLN/agent/VLN-CE/README.md` L53-92
- `$BASE/habitat-sim-0.1.7/src/esp/sim/Simulator.cpp` L135-161; `$BASE/habitat-sim-0.1.7/src/esp/metadata/managers/StageAttributesManager.cpp` L205-219; `$BASE/habitat-sim-0.1.7/src/esp/metadata/managers/ObjectAttributesManager.h` L22-26; `$BASE/habitat-sim-0.1.7/examples/tutorials/nb_python/ECCV_2020_Navigation.py` L42, L161; `$BASE/habitat-lab-0.1.7/README.md` L162-166; `$BASE/habitat-lab-0.1.7/habitat_baselines/rl/ddppo/README.md` L25-60
- `$BASE/HA-VLN/HASimulator/HA-DE/README.md`; `$BASE/Matterport3DSimulator/README.md` L40-140; `$BASE/competitor-bingchengzhang/project/docs/TRAINING.md` L49, L181, L228-292; `$BASE/competitor-bingchengzhang/project/scripts/download_train.py`; `$BASE/image-manifest.json`
- Downloaded copies in `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/dl/a11/`: `niessner_Matterport_master_README.md` (L20, L30, L44), `pixelsynth_LICENSE.md` (EULA L1-200), `download_mp_dynalang.py.txt` (L11-172), `fetch_data_vlnce.sh.txt` (L160-245), `cow_README.md` (L88-100), `embodied_clip.md` (L31-45), `vlmaps_vlmaps_master_README.md` (L61-90), `facebookresearch_habitat-sim_main_DATASETS.md` (L161-177), `datasets_download.py.txt` (L112-140)
- https://github.com/niessner/Matterport/issues/65 ; https://github.com/niessner/Matterport/issues/74 ; https://github.com/niessner/Matterport/issues ; https://github.com/UWMILab/HA-VLN/issues/19 ; https://github.com/UWMILab/HA-VLN/issues/9 ; https://github.com/UWMILab/HA-VLN/issues/3 ; https://github.com/roboworld2026/track2/issues (0 issues)
- https://niessner.github.io/Matterport/ ; http://kaldir.vc.cit.tum.de/matterport/MP_TOS.pdf ; https://huggingface.co/datasets/fly1113/HA-VLN ; https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md ; https://dl.fbaipublicfiles.com/habitat/data/baselines/v1/ddppo/ddppo-models.zip ; http://dl.fbaipublicfiles.com/habitat/mp3d_example.zip ; https://github.com/matterport/habitat-matterport-3dresearch/issues/52 (HM3D access form unavailable since Oct 8 2026 per WebSearch summary: HM3D is not an MP3D substitute anyway)
- WebSearch session limit was reached mid-task (shared 200-call budget). Remaining checks used WebFetch on github.com and raw.githubusercontent.com only.
