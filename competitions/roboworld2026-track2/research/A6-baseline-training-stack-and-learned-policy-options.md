# A6 — Baseline training stack and learned-policy options (HA-VLN 2.0 / RoboWorld 2026 Track 2)

Topic id: `A6-baseline-training-stack-and-learned-policy-options` · Date: 2026-10-24 · Author: research agent A6

Method note: everything marked **[verified]** was read from local clones under
`/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/` (abbreviated `$EXT` below) or from
`git ls-remote`. The shared WebSearch budget ran out on my first query, so I did no new literature search. Literature
numbers come from the repo READMEs I read and from the B2 findings
(`.../findings/B2-vlnce-sota-2023-2026.md`), which I cross-checked against those READMEs where possible. GPU-hour and Score
projections are **[inference]** and are labelled as such.

---

## 0. Summary (decision-relevant)

1. **The learned/compliant route may become the main route, not a fallback.** Open PR #2 on `roboworld2026/track2`
   (`refs/pull/2/head = 8289590`, still unmerged; `main = 2d408b2`, checked by `git ls-remote` today) would add four rules:
   - inference inputs are limited to pose (GPS+compass) and sequential egocentric RGB-D;
   - **reading `human_motion.json` at inference is forbidden** (it is allowed as privileged supervision during training);
   - **only one forward camera is allowed; panoramas must come from in-place rotation, and those turns count toward the
     500-action budget**;
   - training on val or test is forbidden.

   If this is adopted, the "plan offline on privileged state" hypothesis (CONTEXT fact 8) is non-compliant for awards.
   The best achievable Score would then come from a learned, closed-loop, collision-shielded policy.
2. **The baseline stack is a plain VLN-CE CMA DAgger pipeline.** It has three latent issues that cap it:
   - **(a) Misplaced config keys.** In `cma_pm_da_aug_tune.yaml`, `load_from_ckpt` and `ckpt_to_load` sit under
     `IL.DAGGER`. Habitat's `Config` uses `new_allowed=True`, so these keys are silently ignored, and the documented
     training command **trains from scratch**: iteration 0 is pure teacher forcing on 5,000 unique episodes, then 9 DAgger
     rounds with β=0.5^k. The released `ckpt.39.pth` is exactly the final checkpoint of such a 10×4 run.
   - **(b) The expert collides.** The expert is habitat's GreedyGeodesicFollower on a navmesh eroded by only 0.1 m. Its
     collision cost is just 0.25 per step, so it accepts sliding steps.
   - **(c) Little data.** It trains only on HA-R2R train (10,819 episodes), with no EnvDrop augmentation, despite the
     "Aug" in the config name.
3. **CMA ceiling.** Retraining CMA costs about 15–40 A100-GPU-h per run (about 0.5–1.5 days on one GPU after a navmesh-cache
   warm-up) and about 0.3–0.7 TB of lmdb. CMA-class models top out around **SR 0.20–0.27 / Score ≈ 20–27**, even with a
   clean expert and a collision shield. That is useful for validating the pipeline, not for winning.
4. **Best learned candidates, ranked by expected test Score:**

   | Rank | Candidate | Expected test Score [inference] |
   |---|---|---|
   | 1 | **SimpleVLN** (Qwen3.5-9B / Qwen3-VL-8B RL weights, monocular RGB, 0.25 m / 15° action chunks, vLLM server) + depth shield + HA-R2R SFT/DAgger | ≈ 47 (≈ 53 with RL) |
   | 2 | **ETP-R1** (graph planner, Habitat 0.1.7, GRPO code included) with rotation-acquired panorama + collision-aware GRPO reward | ≈ 40–43 |
   | 3 | StreamVLN | ≈ 37 |
   | 4 | NaVILA | ≈ 34 |
   | 5 | Uni-NaVid / NaVid (the only VLA whose eval stack exactly matches the challenge image: py3.8 / torch 2.0.1 / habitat 0.1.7) | ≈ 26–31 |
   | 6 | CMA | ≈ 22 |

   For comparison, a privileged planner that infers the goal correctly in 80% of episodes would score ≈ 75. Every
   learned option needs MP3D scenes, and the test-scan human placements are needed for local closed-loop runs.
5. **Universal fixes, worth more than the backbone choice:**
   - **Clearance-aware expert:** plan on a navmesh rebuilt at radius 0.25–0.3 m over the union of all 120 human frames.
   - **Collision shield** on MOVE_FORWARD: a depth veto plus a learned predictor of "will this step be shortened?",
     trained on navmesh labels.
   - **RL reward = success AND zero collisions.** This is the challenge SR.
   - **Do not truncate instructions.** ETPNav and BEVBert cut at 80 BERT tokens, ETP-R1 at 150; HA-R2R averages about
     112 words, roughly 140–160 tokens.
   - **Panorama by rotation.** Rotating in place gives views identical to ETPNav's 12-camera rig at a cost of about
     22–24 TURNs per decision.

---

## 1. Rules context that changes this topic (verified, flagged)

- **Fact [verified, high].** PR #2 is open and unmerged. `git ls-remote https://github.com/roboworld2026/track2` shows
  `refs/heads/main 2d408b2`, `refs/pull/2/head 8289590`, `refs/pull/2/merge d6155e0`. The fork `JostarXiong/track2` has
  branch `bohan/clarification-Oct14 = 8289590`. Its README diff against main (`$EXT/track2-jostar`,
  `git diff origin/main origin/bohan/clarification-Oct14 -- README.md`) changes the following:
  - **Input:** "Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator
    state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories
    (`human_motion.json`) is strictly prohibited during inference."
  - **Sensor Setup:** "One forward-facing RGB-D camera. Adding additional cameras is not permitted; panoramic views must be
    acquired by rotating in place (rotation actions count toward the action budget)."
  - **Q9:** the agent may read pose throughout the episode.
  - **Q10:** public pretrained models, including VLN policies, waypoint predictors and depth encoders, and external
    datasets are allowed. "HA-R2R validation splits (val_seen, val_unseen) and test splits must not be used for training."
  - **Q11:** ground-truth human info from training episodes may be used as privileged supervision during training only.
  - **Q12:** closed-source APIs are allowed but discouraged; organizers encourage "smaller, open-weight models (such as a 7B
    Qwen-VL model)".
  - **Q13:** a 500-action sequence may omit STOP.
- **Fact [verified].** The merged README (`$EXT/track2/README.md`) still says only that any approach that outputs valid
  action sequences is welcome. `$EXT/track2-latest/README.md` is byte-identical to main.
- **Inference.** C1 already flagged this PR. For A6 it means the learned route is the most defensible path to an award if
  the PR is merged or enforced at award time (winners "may be asked for code"). Treat it as a peer of the offline
  planner, not just a fallback.

## 2. The baseline training stack (verified from code)

| Item | Value | Evidence |
|---|---|---|
| Entry point | `python run.py --exp-config config/cma_pm_da_aug_tune.yaml --run-type train` (cwd `agent/`) | `$EXT/HA-VLN/agent/README.md` L8-17; `$EXT/HA-VLN/agent/run.py` L83-92 |
| Trainer / env | `TRAINER_NAME=dagger`, `ENV_NAME=HAVLNCEDaggerEnv` | `agent/VLN-CE/vlnce_baselines/config/default.py` L20-21 |
| Task config | `../HASimulator/config/HAVLNCE_task.yaml`: ADD_HUMAN True; RGB 224×224 HFOV 90; depth 256×256; 0.25 m / 15°; ALLOW_SLIDING True; MAX_EPISODE_STEPS 500; policy actions [STOP, FORWARD, LEFT, RIGHT]; sensors INSTRUCTION, SHORTEST_PATH (expert), VLN_ORACLE_PROGRESS; HUMAN_COUNTING False | `HASimulator/config/HAVLNCE_task.yaml` L1-57 |
| Envs | `NUM_ENVIRONMENTS: 4` on GPU 0 | `agent/config/cma_pm_da_aug_tune.yaml` L2-4 |
| DAgger schedule | 10 iterations × `update_size` 5,000 episodes, p=0.5, β = p^(it + [load_from_ckpt]); iteration 0 (β=1) collects unique episodes only | yaml L27-34; `dagger_trainer.py` L288-292, L318-321, L513-518 |
| Aggregation | The lmdb is appended across iterations (`start_id = entries`), so iteration k trains on 5,000·k trajectories | `dagger_trainer.py` L325-331, L357-362 |
| Updates | `IL.epochs` 4 per iteration over the whole aggregated lmdb; batch 5 full trajectories (BPTT); Adam lr 2.5e-4; inflection-weighted CE (coef 3.2) + progress-monitor aux loss (α=1) | yaml L23-25; `config/default.py` L60-68; `base_il_trainer.py` L96-98, L181-198; `cma_policy.py` L296-303 |
| Checkpoints | `ckpt.{it*epochs+epoch}.pth`, so a 10×4 run ends at **ckpt.39.pth** (the released file's name) | `dagger_trainer.py` L607-609 |
| Features | RGB ResNet50 (ImageNet, frozen) and depth ResNet50 (DD-PPO Gibson-2plus, frozen); features precomputed by forward hooks and stored in lmdb; `lmdb_fp16` False; map size 1.2 TB | `dagger_trainer.py` L300-314, L346-351; `config/default.py` L107-117, L240-254 |
| Model | CMA: BiLSTM instruction encoder (50-d embeddings, hidden 128×2) + 2 GRUs (512) + RGB/depth spatial attention + prev-action embedding; progress monitor | `cma_policy.py` L52-185; `track2/cma/inference.yaml` L8-39 |
| Vocabulary | HA-R2R vocabulary has 5,079 words; the released ckpt has a 5,401×50 lookup (rows 5079..5400 unused); the loader rejects any dataset whose word list differs | `common/instruction_embeddings.py` L9-12, L65-83; `base_il_trainer.py` L80-94; `Data/HA-R2R-tools/README.md` |
| **Config bug [verified, medium-high impact]** | `load_from_ckpt: True` and `ckpt_to_load` sit under `IL.DAGGER`, but the trainer reads `IL.load_from_ckpt` (default False). Habitat `Config` has `new_allowed=True`, so the misplaced keys are silently accepted and ignored, and the documented command trains **from scratch**. The same bug exists upstream in VLN-CE. | yaml L33-34; `config/default.py` L70-71; `dagger_trainer.py` L501-506, L517; `$EXT/habitat-lab-0.1.7/habitat/config/default.py` L13-15; `$EXT/VLN-CE/vlnce_baselines/config/r2r_baselines/cma_pm_da_aug_tune.yaml` |
| No augmentation | BASE_TASK_CONFIG_PATH points to HA-R2R train only; VLN-CE's real "Aug" stage (`cma_pm_aug.yaml`, 157,232 EnvDrop episodes × 45 epochs of teacher forcing) is not used | `agent/config/cma_pm_da_aug_tune.yaml` L1; `$EXT/HA-VLN/agent/VLN-CE/vlnce_baselines/config/r2r_baselines/cma_pm_aug.yaml` |
| **Expert [verified]** | `ShortestPathSensor` → habitat `ShortestPathFollower` (GOAL_RADIUS 0.5) → habitat-sim `GreedyGeodesicFollower`. Reward = geodesic progress − 0.0125·primLen − **0.25 if the step collides** − 0.05 if within 0.2 m of an obstacle, so **a colliding (sliding) step that keeps ≈0.25 m of progress scores 0.75 and is accepted** whenever no turn+forward primitive scores higher | `habitat_extensions/sensors.py` L125-153; `habitat_extensions/config/default.py` L35-41; `$EXT/habitat-sim-0.1.7/src/esp/nav/GreedyFollower.cpp` L58-76, L91-93; `GreedyFollower.h` L129-130 |
| Human obstacles in training | The expert plans on the per-frame navmesh with humans baked in at agent_radius 0.1, so it passes within ≈0.1–0.2 m of humans | `HASimulator/environments.py` L131-144 |
| Env step cost | Every `step()` calls `_handle_signals()`. While total_signals ≤ 120 (≈12 s of wall time after reset) with ≥1 pending signal (one per 0.1 s), it removes and re-adds all humans and loads (cache hit) or **recomputes (cache miss)** `<scan>_<fff>.navmesh` | `vlnce_baselines/common/environments.py` L68-75; `HASimulator/environments.py` L96-147 |
| Env init cost | `HAVLNCE.__init__` registers all 486 HAPS dirs × 120 frames (58,320 templates) per env process; `_update_dataset` rebuilds the envs every DAgger iteration | `HASimulator/environments.py` L215-233; `dagger_trainer.py` L253, L461 |
| TensorFlow import | `dagger_trainer.py` L26-28 and `base_il_trainer.py` L39-41 import tensorflow. The challenge toolkit's `cma/requirements.txt` has no TF; HA-VLN's `scripts/setup_docker_cma.sh` installs `requirements-py38.txt` (TF 2.12.1, torch 2.0.1) into the image, so **training is feasible inside the challenge image after setup_docker_cma.sh** | files cited; `$EXT/HA-VLN/requirements-py38.txt` |
| Training data availability | HA-R2R `train.json.gz` exists: a public competitor documents sha256 `568f966e…cbf19` and 3,603 trajectories / 10,819 episodes; HF hosts the `HA-R2R/*` episodes per the HA-VLN README. Not fetchable here (HF blocked) | `$EXT/competitor-bingchengzhang/project/docs/TRAINING.md` L260-270; `$EXT/HA-VLN/README.md` L326-345 |

## 3. Compute and time profile to retrain CMA on HA-R2R [inference unless noted]

Assumptions: A100-class GPU; 4 env processes per GPU; average DAgger episode length ≈ 90 primitive steps (iteration 0 is
expert-length ≈ 55–60; later iterations are longer). Throughput: per C1, an official-mirror process does 100–300 steps/s
with RGB-D; the CMA forward pass on 4 envs takes ≈10 ms; navmesh refreshes (20–80 ms each, ≈ every 0.1 s during the first
12 s of an episode) cut that to ≈50–70 steps/s per env.

| Stage | Size | Time (1 GPU, 4 envs) | Notes |
|---|---|---|---|
| Navmesh cache warm-up (one-time) | 61 train scans (+11 val) × 120 frames ≈ 7.3k–8.6k Recast builds at 3–20 s each | 6–48 CPU-h; < 1 h wall in parallel | **Mandatory**: a cold cache turns every first visit of (scan, frame) into a multi-second stall; concurrent writers race (C1 §3.4) |
| Rollout collection | 10 × 5,000 episodes × ~90 steps ≈ 4.5 M steps | ≈ 6–12 h | Scales with envs/GPUs (16 envs on 4 GPUs → ≈ 2–3 h) |
| lmdb size | ≈141 KB/step fp32 (RGB 2048×4×4 floats = 131 KB, depth 32×8×8 = 8 KB, tokens) → ≈ 0.6 TB fp32 / 0.3 TB with `lmdb_fp16` | — | Shapes from `resnet_encoders.py` (spatial 4×4 avg-pool) and habitat ResNetEncoder (2048-float compression), `$EXT/habitat-lab-0.1.7/habitat_baselines/rl/ddppo/policy/resnet_policy.py` L119-129 |
| Gradient updates | Σ_k 4·(5000k/5) = **220,000 batches** (batch = 5 full trajectories) | ≈ 5–10 h (≈60–150 ms per batch, I/O bound at ≈63 MB per batch) | `dagger_trainer.py` L525-609 |
| **Total per full run** | — | **≈ 12–36 h wall ≈ 15–40 GPU-h** | DAgger iterations are sequential; parallelise across seeds/variants, not within a run |
| Eval / inference | val_unseen 1,839 episodes; test 3,408 episodes; the official exporter runs batch-1 per shard | < 1 h on 4 GPUs | `track2/scripts/export_cma_submission.py` L65-170 |

Variance note **[verified]**: the same checkpoint gives two published val_unseen references:
- HA-VLN README: SR .114, Score 11.94, TCR 22.35 (`$EXT/HA-VLN/README.md` L143-148);
- toolkit README: SR .129, Score 12.945, TCR 17.54 (`$EXT/track2/README.md` L181-186).

So run-to-run or hardware variance from human timing is about ±1 Score point. Learned-policy comparisons need several
seeds or replays.

## 4. Checkpoint inventory

| Checkpoint | Where | Notes |
|---|---|---|
| **HA-VLN-CMA `ckpt.39.pth`** | HF `fly1113/HA-VLN` `checkpoints/HA-VLN-CMA/ckpt.39.pth`, sha256 `e70dce94…52dc` | Inference-only `{'state_dict'}` with 521 tensors incl. frozen encoders and the 5,401×50 lookup (`track2/scripts/resources.json` L13; `export_cma_submission.py` L91-93; `scripts/docker-quickstart-20261005.json`). Architecture in `track2/cma/inference.yaml`. It is the final 10×4 DAgger checkpoint, not one selected on val |
| DD-PPO depth encoder `gibson-2plus-resnet50.pth` | `dl.fbaipublicfiles.com/habitat/data/baselines/v1/ddppo/ddppo-models.zip` (672 MB) | Needed only for training from scratch; already embedded in ckpt.39 (`HA-VLN/README.md` L338-345; `config/default.py` L251-253) |
| VLN-CE `CMA_PM_DA_Aug` (R2R-CE, 141 MB) | Google Drive (VLN-CE README) | Transferable with `checkpoint_embedding_mode transfer` (2,504-word R2R lookup is dropped); R2R-CE val_unseen SR 0.29 / SPL 0.27 (leaderboard) |
| ETPNav (R2R-CE / RxR-CE), CWP waypoint predictor `check_cwp_bestdist_hfov90`, pretrained LXMERT-style weights, DD-PPO depth | ModelScope `admagic/ETPNav` | `$EXT/sota/ETPNav/README.md` |
| ETP-R1 joint-pretrain, R2R SFT `ckpt.iter25000`, R2R RFT `ckpt.iter270` (final), RxR | HF `cepillarskeira/ETP-R1-extra-files` (`extra_files.zip`) | `$EXT/sota/ETP-R1/README.md` L100-135 |
| BEVBert-CE | Google Drive; grid features on ModelScope `admagic/BEVBert` | `$EXT/VLN-BEVBert/README.md` L69-91 |
| NaVid / Uni-NaVid (7B) | HF `Jzzhang/NaVid`, `Jzzhang/Uni-NaVid` (`uninavid-7b-full-224-video-fps-1-grid-2`) + EVA-ViT-G | `$EXT/sota/NaVid-VLN-CE/README.md` L88-100 |
| NaVILA (LLaMA3-8B, 8 frames) | HF `a8cheng/navila-llama3-8b-8f` | `$EXT/sota/NaVILA/README.md` L180 |
| StreamVLN (LLaVA-Video-7B / Qwen2) | HF `mengwei0427/StreamVLN_Video_qwen_1_5_r2r_rxr_envdrop_scalevln_v1_3` | `$EXT/sota/StreamVLN/README.md` L39, L242-248 |
| SimpleVLN (Qwen2.5-VL 3B/7B SFT; Qwen3-VL 4B/8B SFT+RL; Qwen3.5 4B/9B SFT+RL) | HF `honglyhly/SimpleVLN_*` | `$EXT/sota/SimpleVLN/README.md` L77-85 |
| Competitor LoRA (Qwen2.5-VL-7B nav r0) | HF `bingchengzhang/HA-VLN-nav-r0-lora` | Their own docs report closed-loop SR = 0 on 20 routes (`project/docs/CLOSED_LOOP.md` L50) |
| HA-VLN-VL (Recurrent-VLN-BERT variant) | **not released** for CE | Only described in `agent/README.md` L19-37 |
| HCSG (0.24 SR on HA-VLN-CE) | **code not released** ("We will release our code soon") | `$EXT/sota/HCSG/README.md` |

## 5. Realistic ceiling of CMA-class models

- R2R-CE: CMA_PM_DA_Aug val_unseen SR 0.29 / SPL 0.27, test SR 0.28 (VLN-CE leaderboard; `$EXT/VLN-CE/README.md` L211-219).
- HA-R2R: the released CMA gets SR 0.129 at TCR 17.5, CR 0.684. CR is normalised by β·N, so about 59% of episodes have
  extra collisions, mostly wall slides (A2).
- **[inference]** CMA's raw success (≤3 m at STOP, ignoring collisions) on HA-R2R val_unseen is probably 0.22–0.30, so its
  SR is mostly collision-limited. With a clean expert, a collision shield and some data augmentation, SR ≈ 0.20–0.27 and
  NE ≈ 6 give **Score ≈ 20–27**. CMA is therefore a pipeline-validation vehicle: shield testing, expert-relabeling and
  calibration of the local scorer against Phase 1.

## 6. Learned-policy candidates (per-method cards)

The challenge image stack is py3.8, torch 2.0.1+cu118, habitat-sim/lab 0.1.7 (patched core), numpy 1.23.5,
gym 0.17.3 (`track2/scripts/setup_cma.sh` L8-9; `HA-VLN/requirements-py38.txt`). Because scoring is replay of an action
tape, a policy may run in any environment. The local simulator must still be habitat 0.1.7 with the HA human and navmesh
code, so its dynamics match the scorer. In practice: **sim client in the challenge image, model server in its own env**,
connected over a socket or an OpenAI-compatible HTTP API.

### 6.1 SimpleVLN (Hong et al., arXiv 2610.23203)
- **R2R-CE val_unseen [verified, README]:**
  - after RL: Qwen3.5-9B 76.7 SR / 72.6 SPL; Qwen3.5-4B 76.3 / 72.3; Qwen3-VL-8B 74.4 / 69.5; Qwen3-VL-4B 73.8 / 66.7;
  - before RL: 9B 69.2 / 61.2; Qwen2.5-VL-7B 59.1 / 52.0;
  - RL adds +7.5 to +10.2 SR.
- **Interface [verified]:**
  - single forward RGB 640×480 HFOV 90; forward 0.25 m, turn 15° (exact match to the challenge's action geometry);
    max 400 steps;
  - single-turn prompt with 8 uniformly sampled history frames plus the current frame;
  - outputs action chunks ("forward 75", "turn left 30" …) parsed with regex;
  - sampling temperature 0.3;
  - served by vLLM 0.18.0 through the OpenAI API;
  - eval code targets habitat 0.3.3.

  Sources: `eval/config/vln_r2r.yaml` L19-35; `eval/vln/eval.py` L137-330; `eval/requirements*.txt`.
- **Compliance:** monocular, so it satisfies the one-camera rule; depth stays free for the shield.
- **Code:** eval and weights only; **training code not released**. It is a native Qwen checkpoint, so SFT/DAgger can use
  generic Qwen-VL SFT tooling (ms-swift, LLaMA-Factory, TRL) with the reconstructed prompt format.
- **Dependency fit:** port the about 300-line client (`SimpleVLN_Agent`) into the 0.1.7 image (needs `openai>=1`,
  `opencv`); the model runs in a separate vLLM env. Conflict risk is low.
- **GPU-hours [inference]:**
  - zero-shot inference on test: ≈ 25–35 decisions/episode × 0.3–0.5 s ≈ 10–15 s/episode → ≈ 10–14 h on one server,
    ≈ 1.5–2 h on 8;
  - HA-R2R SFT + 1–2 DAgger rounds: 100–250 GPU-h;
  - GRPO RL with simulator rollouts: 300–1,000+ GPU-h.
- **Social layer:** depth shield on every MOVE_FORWARD in a chunk (re-query on veto); DAgger with the clearance-aware
  expert; RL reward = success × 1[collisions = 0] − λ·collisions.
- **Expected HA test Score [inference]:** zero-shot + shield ≈ 35–40; + SFT/DAgger ≈ 45–50; + RL ≈ 50–56.
- **Risks:**
  - camera domain shift (224² official vs 640×480 trained): rendering the single camera at 640×480 locally is plausibly
    allowed, but confirm with the organizers;
  - long instructions are fine for the LLM;
  - human figures are out of distribution;
  - training recipe not public;
  - license of weights/data: VLN-CE data are CC BY-NC-SA.

### 6.2 ETP-R1 / ETPNav family (graph planner + CWP waypoint predictor; Habitat 0.1.7)
- **R2R-CE val_unseen:**
  - ETPNav 57 SR / 49 SPL (B2); ETP-R1 SFT 63.2 / 54.3, RFT 65.3 / 55.8 (B2; README claims SOTA);
  - HA-VLN-CE in the HA-VLN 2.0 paper: retrained ETPNav SR 0.17 val_unseen; BEVBert 0.21 (B2).
- **Code [verified]:** full training code (pretrain, online DAgger SFT, **GRPO RFT**) and all checkpoints. Trained on
  4×A6000; DAgger 30k iterations, 8 envs/GPU; GRPO 500 iterations with sample_num 8 (`ETP-R1/README.md` L27;
  `run_r2r/main_server.bash` L18-72).
- **Stack:** py3.6, torch 1.9.1+cu111, habitat 0.1.7 (`ETP-R1/README.md` L40-59; `ETPNav/environment.yaml` L87). Two
  options:
  - run it in its own 0.1.7 conda env with HASimulator copied in;
  - upgrade to py3.8 / torch 2.0.1 (expected to be mostly mechanical: same habitat; CLIP and torch.distributed.launch
    still work).

  Either way, final tapes must be verified in the official image.
- **Five HA-specific issues [verified]:**
  1. **Instruction truncation.** `extract_instruction_tokens(..., max_length=IL.max_text_len)` keeps the first N tokens.
     The default is 80 for ETPNav/BEVBert (`ETPNav/run_r2r/iter_train.yaml` L42; `ss_trainer_ETP.py` L774-777;
     `vlnce_baselines/common/utils.py` L24; `VLN-BEVBert/bevbert_ce/run_r2r/iter_train.yaml` L42) and 150 for ETP-R1
     (`ETP-R1/run_r2r/iter_train.yaml` L62). HA-R2R averages about 112 words, so the goal sentence at the end is often
     cut. Raise to 256–320; the BERT/XLM-R position tables have 512/514 entries.
  2. **12-camera rig.** The rig consists of deep copies of the single sensor with only ORIENTATION changed, so every view
     shares one optical centre (`ss_trainer_ETP.py` L97-111). Rotating the agent in 2×15° steps therefore reproduces the
     same 12 views, minus human-timing effects. Cost: ≈ 22 TURNs to capture headings 0..330°, then turns to the chosen
     heading, about 28 extra actions per decision. Typical ≈ 6–8 decisions/episode → ≈ 170–220 extra actions; the
     worst case at 15 decisions nears 500. A budget-aware STOP is needed.
  3. **Backtracking.** The default `back_algo: teleport` (`iter_train.yaml` L46) is used in training, but the official
     eval/infer commands set `IL.back_algo control` (`ETPNav/run_r2r/main.bash` L33, L46; `ETP-R1/run_r2r/main_server.bash`
     L82, L96). With control there is no teleport (`ss_trainer_ETP.py` L915-919, L957-961). **Correction to B2 fact 26:**
     the recommended eval is already teleport-free.
  4. **Blind forward steps.** The obstacle "tryout" is active only when ALLOW_SLIDING is False (`ss_trainer_ETP.py` L907).
     With sliding on (HA config), the controller issues int(d/0.25) blind MOVE_FORWARDs (`environments.py` L362-372), so
     it slides along walls and collides. It needs a collision-aware local controller.
  5. **Primitive-step limit.** MAX_EPISODE_STEPS is 5,000 primitive steps in ETPNav (`run_r2r/r2r_vlnce.yaml` L2) vs the
     challenge's 500.
- **GPU-hours [inference]:**
  - HA-R2R SFT from the R2R-CE checkpoint (5–15k iterations): 50–150 GPU-h;
  - collision-aware GRPO: 50–150 GPU-h;
  - test inference about 1 h on 8 GPUs.
- **Social layer:**
  - retrain CWP on human-inserted navmeshes so ghost nodes avoid humans;
  - person detection on the 12 rotation views to penalise ghost nodes within 1 m of people (HCSG-style);
  - local A* on an occupancy grid built from the 12 depth views + pose with ≥0.25 m inflation;
  - GRPO reward success ∧ 0 collisions (the GRPO trainer already exists).
- **Expected Score [inference]:** ETPNav ≈ 33–38; ETP-R1 ≈ 40–45.
- **Risk:** medium (action budget, controller rewrite, py3.6 env).

### 6.3 BEVBert-CE / HNR / g3D-LF
- BEVBert-CE: R2R-CE 59 SR; 4 GPUs, 10k iterations; same max_text_len 80 / back_algo / tryout issues
  (`VLN-BEVBert/bevbert_ce/run_r2r/main.bash`, `iter_train.yaml` L42-54); needs metric-map grid features → heavier.
- HNR: 61 SR, but its lookahead fine-tuning code was never released (B2).
- g3D-LF: 61 SR; needs torch_kdtree + tiny-cuda-nn.
- **Inference:** these are dominated by ETP-R1 (better SR, RL code, same stack). Not recommended as first choices;
  Score ≈ 33–40.

### 6.4 StreamVLN
- **R2R-CE val_unseen:** 56.9 / 51.9 (paper); v1-3 checkpoint 4.90 NE / 56.4 SR / 50.2 SPL (`StreamVLN/README.md` L39).
- **Interface [verified]:** habitat **0.2.4**, py3.9, torch 2.1.2; RGB-D 640×480 HFOV 79; 0.25 m / 15°; DAgger
  collection code released (`config/vln_r2r.yaml` L21-35; `config/vln_dagger.yaml`; README L51-62).
- **Compute:** stage-one training ran on 4 nodes × 8 GPUs with a 96 h limit (`scripts/streamvln_train_slurm.sh` L3-5).
- **HA fit:** needs a 0.2.4 model-side env + 0.1.7 sim bridge; HFOV 79 vs 90 shift.
- **GPU-hours (HA fine-tune):** 100–300 [inference].
- **Expected Score:** 34–40. **Risk:** medium-high.

### 6.5 NaVILA
- **R2R-CE val_unseen:** 54.0 / 49.0 (B2).
- **Eval stack:** habitat 0.1.7 **built from source under py3.10** + patched transformers 4.37.2 + flash-attn 2.5.8
  (`NaVILA/README.md` L110-145); ≈ 0.6 s/step.
- **Inference cost:** ≈ 7 h on 8 GPUs for test.
- **Training:** SFT script `scripts/train/sft_8frames.sh` (8B, zero3).
- **Expected Score:** 30–36 [inference]. **Risk:** medium.

### 6.6 Uni-NaVid / NaVid
- **R2R-CE val [verified README]:** NaVid 41.9 / 36.5 (test 45 / 39); Uni-NaVid 51.8 / 47.7.
- **Eval code `jzhzhang/NaVid-VLN-CE` targets py3.8 + habitat-sim 0.1.7 + torch 2.0.1 + numpy 1.23.5 + gym 0.17.3**
  (`NaVid-VLN-CE/requirements.txt` L4, L8-9, L13, L29; README L30-54). That **exactly matches the challenge image**, so it
  is the cheapest VLA to stand up in-image. Extra pins: transformers 4.31.0, peft 0.4, bitsandbytes 0.41.
- **Camera/action shift:** trained with TURN_ANGLE 30 (map to 2× TURN 15°) and RGB 640×480 HFOV 90 (NaVid) / HFOV 120
  (Uni-NaVid) (`VLN_CE/habitat_extensions/config/vlnce_task_navid_r2r.yaml` L6-17; `..._uninavid_r2r.yaml` L15).
- **Speed:** Uni-NaVid ≈ 5 Hz on an A100. NaVid: 1,839 episodes in 2.5 h on 8×A100.
- **Training:** Uni-NaVid stage-2 fine-tune scripts exist (py3.10 + flash-attn; `Uni-NaVid/scripts/uninavid_stage_2.sh`).
- **GPU-hours (HA fine-tune):** 40–150 [inference].
- **Expected Score:** NaVid 22–28, Uni-NaVid 28–34. **Risk:** low (integration) / medium (ceiling).

### 6.7 CMA (in-stack)
- See §§2–5. **Expected Score** 20–27 after fixes. **Effort** 2–4 person-days. **Risk** low.

## 7. Ranked list (as complement/fallback; primary if PR #2 governs awards)

Scores are [inference] computed with the official formula, with CR normalised by β_test = 1 − 549/3408 = 0.839. Effort is
in person-days of a strong engineer; with 5–10 parallel coding agents, divide calendar time by about 2–3. MP3D data and
test human placements are assumed to be available.

| Rank | Option | Expected test SR / NE | Expected Score | Effort (person-days) | GPU-h | Main risks |
|---|---|---|---|---|---|---|
| 1 | SimpleVLN-9B (or Qwen3-VL-8B RL) + depth/learned collision shield → HA-R2R SFT + DAgger with clearance expert → optional GRPO (success ∧ 0 coll) | 0.40 zero-shot → 0.52 SFT/DAgger → 0.58 RL; NE 4.6→3.6 | **37 → 48 → 53** | 3 (zero-shot) + 10 (SFT/DAgger) + 12 (RL) | 30 / 250 / 1,000 | Camera/res shift; no training code; RL infrastructure; vLLM ops |
| 2 | ETP-R1 + rotation pano + max_text_len 320 + collision-aware controller + HA SFT + GRPO(0-coll) | 0.42–0.48; NE ≈ 4.4 | **40–45** | 10–14 | 150–300 | Action budget (≈28 turns/decision); py3.6 env; controller rewrite |
| 3 | StreamVLN + shield + HA DAgger | 0.38–0.42 | 35–39 | 8–12 | 150–350 | 0.2.4↔0.1.7 bridge; HFOV 79 |
| 4 | NaVILA + shield + HA SFT | 0.34–0.38 | 32–36 | 6–9 | 80–180 | py3.10 source build; 0.6 s/step |
| 5 | Uni-NaVid (in-image) + shield + HA SFT | 0.30–0.35 | 29–33 | 4–7 | 50–150 | HFOV 120 / turn 30 shift; lower ceiling |
| 6 | BEVBert-CE / HNR / g3D-LF | 0.35–0.40 | 33–38 | 10–14 | 150–300 | Dominated by ETP-R1 |
| 7 | CMA retrain (clean expert + shield) | 0.20–0.27; NE ≈ 6 | 20–27 | 2–4 | 15–40 | Low ceiling |
| (ref) | Released CMA | 0.129; NE 6.39 | 12.9 (val_unseen) | 0 | — | — |
| (ref) | Privileged planner, 80% goal accuracy, 0 collisions | 0.80; NE 2.5 | ≈ 75 | — | — | **Possibly non-compliant under PR #2** |

Score sensitivity [computed, `.../scratchpad/a6tmp/score.py`]:
- ≈ +7.5 Score per +0.1 SR (at SR 0.4, NE 4.8);
- at fixed SR 0.40, raising the colliding-episode fraction from 0.15 to 0.40 (TCR 0.4→2) costs only ≈ 4 points through
  Social;
- but each colliding episode also loses its SR credit, so collisions are first-order through SR.
- Checks: the released CMA val_unseen reproduces Score 12.95; the ensemble stretch case (SR 0.65, NE 3.2) gives ≈ 60.

## 8. Shared social-avoidance / collision layer (applies to every learned option)

1. **Training-time privileged expert (allowed per PR #2 Q11).** Recompute each training scan's navmesh at agent_radius
   0.25–0.30 m over the union of all 120 human frames. Run `habitat_sim.GreedyGeodesicFollower` (or a lattice A*) on it
   to label IL/DAgger targets, with zero-collision verification on the official 0.1.7 navmesh. This removes the expert's
   own sliding (§2) and teaches clearance from humans.
2. **Inference shield (compliant).**
   - (a) Analytic depth veto: block MOVE_FORWARD if any depth pixel in a 0.35–0.4 m wide corridor between 0.2 and 1.6 m
     height lies within 0.25 + margin m ahead.
   - (b) A learned **step-collision predictor**: a small CNN on depth (+RGB) labelled by whether `try_step` shortens the
     0.25 m move on the official navmesh, trained on millions of samples from training scans. Tune for ≈0 false
     negatives, because a single slide fails the episode.
   - (c) Person detector (GroundingDINO already in `HASimulator/detector.py`, or YOLO-seg as the competitor uses) plus
     depth back-projection, giving a 0.6–1.0 m keep-out region in a local costmap.
   - On veto, re-query the policy or replan locally. 'Successful but Unsafe' (arXiv 2610.14682, via B2) reports such
     training-free guards cut collision steps 62–98% and raise SR by 6.9–29.3 pp under blocking.
3. **Self-built map executor.** Use an occupancy map from the agent's own depth + GPS (compliant), A* with ≥0.25 m
   inflation, and the VLA/graph policy choosing sub-goals. This matches the competitor's architecture (YOLO-seg + depth
   map + grid search + Qwen slow loop).
4. **RL objective = challenge SR.** Reward = 1[success] · 1[collisions = 0], with dense shaping −λ·collision_step and
   +progress. ETP-R1's GRPO trainer is directly adaptable.
5. **Replay-robustness.** Humans in the official replay may sit at different frames, so keep clearance from detected
   humans larger than their likely motion (p90 extent 0.8 m). Validate tapes under several frame schedules (A3/C1
   scheduler).
6. **Gray zone (ask the organizers before using).** A forward-step collision is observable from GPS (displacement < 0.25 m)
   using only allowed inputs. Locally one can rewind (reset + replay the prefix) and choose another action, which
   produces tapes with zero local collisions for any policy. It uses no forbidden input but exploits replay; treat it as
   non-compliant unless explicitly allowed.

## 9. Implications

- **Two route regimes.** If PR #2 is merged or enforced at award time, the win is decided among compliant agents, where
  public R2R-CE SOTA collapses to 0.17–0.24 SR on HA-VLN-CE. A learned agent at SR 0.45–0.58 (Score 43–53) would be
  far ahead of the published state of the art. If PR #2 is not adopted, the learned agent is a hedge and a goal
  proposer for the privileged planner.
- **The decisive engineering is shared:** a collision-free expert, a shield, uncut instructions and RL on the true SR.
  These matter more than the backbone choice; for example, ETPNav's 80-token truncation alone plausibly explains part
  of the paper's 0.17.
- **Rotation-acquired panoramas are a free compliance fix for graph agents.** The only cost is the action budget, which
  is not scored (no SPL in the Score) apart from the 500 cap.
- **Hard prerequisites for every learned option:**
  - MP3D scenes (critical path per C2);
  - HA-R2R train split (exists; competitor sha256 above);
  - test-scan human placements for local closed-loop runs. Without them, the local test sim is human-free while the
    replay has humans in 84% of episodes (β_test = 0.839), so the learned route degrades sharply.

## 10. Recommendations

1. **Today:** freeze CMA as the calibration anchor. Retrain once with `IL.load_from_ckpt` set at the correct level (or
   accept from-scratch training), `lmdb_fp16 True`, and a pre-warmed navmesh cache, to validate the training farm
   (≈ 1 day, 1 GPU).
2. **Stand up three closed-loop agents in parallel (day 1–4):**
   - Uni-NaVid in-image (lowest integration risk);
   - SimpleVLN-Qwen3-VL-8B-RL and Qwen3.5-9B-RL behind vLLM with a 0.1.7 client;
   - ETP-R1 with rotation-pano, back_algo control, max_text_len 320 and a budget-aware STOP.

   Evaluate on val_unseen with the challenge metric (several seeds).
3. **Build the shared collision layer (day 2–6):** union-of-frames inflated navmeshes for training scans; a clearance
   expert; a depth-based step-collision predictor with navmesh labels; person-keep-out costmap. Gate every MOVE_FORWARD
   through it.
4. **Fine-tune the top-2 by val_unseen Score (day 5–15):** HA-R2R train SFT/DAgger with the clearance expert, plus
   HA-style augmentation:
   - rewrite R2R-CE / EnvDrop / ScaleVLN instructions with the organizers' published LLM prompt
     (`Data/HA-R2R/README.md`);
   - insert HAPS humans into training scenes;
   - keep the CMA vocabulary if CMA is used.

   Then GRPO with reward success ∧ zero-collision (ETP-R1 trainer; SimpleVLN-style RL for the VLA).
5. **Ensembling.** Run 2–3 policies or seeds per test episode and pick by self-consistency or a learned success/collision
   critic. No GT is used, so this stays compliant.
6. **Ask the organizers (GitHub issue / Discord) explicitly:**
   - Will PR #2 be merged?
   - Is offline use of MP3D geometry/navmesh (without humans) at inference allowed?
   - Is changing the single camera's resolution allowed?
   - Is the GPS-rewind trick allowed?
   - Will the test-scan human placements be in the Phase 2 bundle?

## 11. Open questions

- Will PR #2 be merged, and from what date does it apply? Does it retroactively bind Phase 2 award eligibility?
- Will the Phase 2 bundle include human placements for the 18 test scans? Without them, local closed-loop runs on test
  cannot see the humans.
- Is single-camera resolution/HFOV free to change (SimpleVLN/StreamVLN were trained at 640×480; the official camera is
  224² HFOV 90)?
- What is CMA's raw (collision-agnostic) success on HA-R2R val_unseen? It is the true measure of the CMA language
  ceiling; measure in bring-up.
- How was the HA-VLN 2.0 paper's ETPNav/BEVBert retraining configured (instruction length 80? panorama? sliding?) and was
  their SR baseline-adjusted?
- What is the real HA-sim step throughput and `recompute_navmesh` time (C1 B2 bench)? These drive all GPU-hour estimates
  above.
- License terms for SimpleVLN/StreamVLN weights (code CC BY-NC-SA for some; VLN-CE data CC BY-NC-SA 3.0): acceptable for a
  non-commercial challenge, but check the technical-report obligations.

## 12. Sources

Local files (all under `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/`):

**HA-VLN agent stack**
- HA-VLN/agent/config/cma_pm_da_aug_tune.yaml
- HA-VLN/agent/README.md
- HA-VLN/agent/run.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/dagger_trainer.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/common/environments.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/common/instruction_embeddings.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/models/cma_policy.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/models/encoders/{instruction_encoder.py,resnet_encoders.py}
- HA-VLN/agent/VLN-CE/vlnce_baselines/config/default.py
- HA-VLN/agent/VLN-CE/vlnce_baselines/config/r2r_baselines/{README.md,cma_pm_aug.yaml,cma_pm_da_aug_tune.yaml}
- HA-VLN/agent/VLN-CE/habitat_extensions/{sensors.py,config/default.py}

**HA-VLN simulator, data and setup**
- HA-VLN/HASimulator/{environments.py,measures.py,metric.py,config/*.yaml}
- HA-VLN/Data/HA-R2R-tools/{README.md,collision_num_*.json}
- HA-VLN/README.md
- HA-VLN/requirements-py38.txt
- HA-VLN/scripts/{setup_docker_cma.sh,hf_resources.json,docker-quickstart-20261005.json}

**Challenge toolkit**
- track2/README.md
- track2/cma/{inference.yaml,requirements.txt}
- track2/scripts/{export_cma_submission.py,setup_cma.sh,resources.json}
- track2-jostar (branch bohan/clarification-Oct14, commits 0f944d3, 8289590)

**Habitat 0.1.7 and VLN-CE**
- habitat-lab-0.1.7/habitat/config/default.py
- habitat-lab-0.1.7/habitat_baselines/rl/ddppo/policy/resnet_policy.py
- habitat-sim-0.1.7/src/esp/nav/{GreedyFollower.cpp,GreedyFollower.h}
- VLN-CE/README.md
- VLN-CE/vlnce_baselines/config/r2r_baselines/cma_pm_da_aug_tune.yaml

**Learned-policy candidates**
- sota/ETPNav/{README.md,environment.yaml,run_r2r/*,vlnce_baselines/ss_trainer_ETP.py,vlnce_baselines/common/{environments.py,utils.py}}
- sota/ETP-R1/{README.md,run_r2r/*}
- VLN-BEVBert/{README.md,bevbert_ce/run_r2r/*}
- waypoint-predictor/README.md
- sota/NaVid-VLN-CE/{README.md,requirements.txt,agent_navid.py,agent_uninavid.py,VLN_CE/habitat_extensions/config/*}
- sota/Uni-NaVid/{README.md,scripts/*}
- sota/NaVILA/{README.md,scripts/train/sft_8frames.sh}
- sota/StreamVLN/{README.md,config/*,scripts/streamvln_train_slurm.sh}
- sota/SimpleVLN/{README.md,eval/config/vln_r2r.yaml,eval/vln/eval.py,eval/requirements*.txt}
- sota/InternNav/README.md
- sota/HCSG/README.md
- competitor-bingchengzhang/project/docs/{TRAINING.md,CLOSED_LOOP.md,ARCHITECTURE.md,MODELS.md}

Other findings used: `.../scratchpad/findings/{B2-vlnce-sota-2023-2026,C1-infra-and-replay-farm,A1-episode-format-and-test-split,A2-collision-semantics-habitat017,C2-timeline-critical-path-and-risk-register}.md`.

Remote (via git): https://github.com/roboworld2026/track2 (refs incl. pull/2), https://github.com/JostarXiong/track2.

URLs cited in repos: https://huggingface.co/datasets/fly1113/HA-VLN, https://dl.fbaipublicfiles.com/habitat/data/baselines/v1/ddppo/ddppo-models.zip,
https://modelscope.cn/models/admagic/ETPNav, https://huggingface.co/honglyhly (SimpleVLN), https://huggingface.co/Jzzhang/Uni-NaVid,
https://huggingface.co/a8cheng/navila-llama3-8b-8f, https://huggingface.co/mengwei0427/StreamVLN_Video_qwen_1_5_r2r_rxr_envdrop_scalevln_v1_3,
https://huggingface.co/bingchengzhang/HA-VLN-nav-r0-lora, arXiv 2610.23203 (SimpleVLN), 2512.20940 (ETP-R1), 2304.03047 (ETPNav),
2503.14229 (HA-VLN 2.0), 2610.14682 (Successful but Unsafe), 2605.13321 (HCSG).
