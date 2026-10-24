# B8 — World models, innovation angle, and organizer taste (RoboWorld 2026 Track 2, HA-VLN 2.0)

Research date: 2026-10-24. Agent B8. Note: the shared WebSearch budget (200 calls per turn, across all agents) ran out partway through this task. The rest of the work used local clones of public GitHub repos (git clone / git ls-remote / PR refs) and PDFs that were already in a cloned repo. Claims marked *(prior knowledge)* could not be re-checked against the web in this session.

---

## 0. TL;DR: the 5 most decision-relevant findings

1. **The organizers have written down an inference-input rule, and it contradicts the "plan everything offline" hypothesis (CONTEXT fact 8). (Confidence: HIGH on content, MEDIUM that it becomes final.)** Open PR #2 on the official `roboworld2026/track2` repo is unmerged as of 2026-10-24. It was authored on 2026-10-14 by challenge organizer Bohan Xiong (git name "JosephJostar"; branch `bohan/clarification-Oct14`, head `8289590`). It rewrites the task Input to *"Episode ID, initial pose, navigation instruction, ongoing agent pose (GPS+compass from simulator state), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference."* It adds these rules:
   - one forward RGB-D camera only, with no added cameras and panoramas taken by rotating (Q8);
   - pose may be read (Q9);
   - pretrained models and external data are allowed, but training on val/test is not (Q10);
   - no `human_motion.json` at inference, though it may be used as *privileged supervision during training* (Q11);
   - closed APIs are allowed but discouraged, and a "7B Qwen-VL"-scale open model is encouraged (Q12).

   A pipeline that renders from arbitrary viewpoints, reads human placements, or plans on the ground-truth navmesh at test time is therefore non-compliant with the stated intent.
2. **The organizers' previous social-navigation track banned exactly this, and it audited code.** RoboSense 2025 Track 2 was run by the same lead organizer, Lingdong Kong. Its rules: *"policies based solely on RGBD observations and odometry, without access to global maps or privileged information"*. Phase 2 accepted code submissions only. A reproducibility audit preceded any award, and teams were disqualified for "accessing extra environmental information … beyond the allowed observation keys". The Track 2 2026 FAQ says award winners "may be asked to provide code or models for verification". That audit covers the Top-5 certificates as well as the innovation award. (HIGH)
3. **In this organizer lineage, "innovation" means a theme-aligned, named module with ablations, usually from a top-2 team.** RoboSense 2025 innovation awards went to three teams:
   - 2nd place, social navigation: a "Proactive Risk Perception Module", i.e. an auxiliary human-collision-risk head on the Falcon baseline. It scored 0.6994 against 0.7022 for 1st place and 0.6248 for the baseline.
   - 2nd place, driving with language: a VLM "Mixture-of-Prompts" router.
   - 1st place, cross-platform 3D detection: "DataEngine".

   The 1st-place social-navigation team (a generic RL replay trick) did *not* get the innovation award. RoboDepth 2023 gave its innovation prizes to non-podium teams. The bar is modest and achievable: a clean idea that targets the track's theme (here, human anticipation and humans as landmarks) plus ablations. (HIGH)
4. **The organizers' own research says what they value: world models with foresight, egocentric-only grounding, and explicit human/social modeling. It also says what they dislike: reliance on maps.**
   - UniWM (ECCV 2026) "explicitly grounds action decisions in visually imagined outcomes".
   - LCVN (NeurIPS 2026 oral) treats "language as goal specification" in a world model trained on social-navigation video.
   - GoViG (ACL Findings 2026) states: "*Unlike previous methods that rely on semantic maps or structured annotations, GoViG operates purely on egocentric visual input*".
   - The Track 2 page says humans "serve as both semantic landmarks and dynamic obstacles", "without relying on static-world assumptions", "under partial observability".
   - The RoboPAD workshop topics are post-training, RL fine-tuning of VLAs, world models, test-time adaptation, agent harnesses, and evaluation & safety.

   (HIGH)
5. **The best route to the innovation award and an oral is a *compliant* closed-loop agent that uses privileged information only at training time.** The rules still allow strong levers:
   - ground-truth pose plus depth, which makes near-exact online mapping and near-zero wall collisions possible;
   - privileged ground-truth humans and navmesh as a *training teacher*;
   - external VLN data and pretrained VLAs.

   Package these as 3–4 named modules: a human-occupancy foresight world model, humans-as-landmarks VLM grounding, a shielded discrete-action executor, and privileged-teacher post-training with metric-aware stopping. Keep the full-information planner as (a) an expert-data generator on train scenes, (b) an oracle ceiling in the report, and (c) a local diagnostic tool. Score arithmetic: a compliant agent at SR 0.55 / NE 3.5 / CR 0.10 / TCR 0.2 scores about 51.4, against 12.9 for CMA and about 22.5 for an HCSG-level agent.

---

## 1. Who judges, and what they work on (organizer profile)

All entries below were verified from `roboworld2026.github.io/index.html` (commit 84d0bc2), the RoboPAD site source, and the repo READMEs, except where marked otherwise.

| Person | Role | Research line (evidence) | Implied taste |
|---|---|---|---|
| **Lingdong Kong** (NUS) | Lead challenge organizer; ran RoboDepth'23, RoboDrive'24, RoboSense'25; co-author of HA-VLN 2.0, UniWM, LCVN | Robustness benchmarks (RoboDepth, RoboBEV), evaluation reliability (DriveBench), *3D and 4D World Modeling: A Survey* (arXiv 2509.07996). The survey calls for standardized evaluation of controllability, safety and generalization, and for reproducible code | Values rigorous evaluation, robustness analysis and reproducibility. Previous challenges: code audits, joint challenge summary papers, LaTeX report template |
| **Yifei Dong, Fengyi Wu** (UW MILab) | Track 2 owners (HA-VLN 2.0 first authors); also WorldNav | HA-VLN 1.0/2.0, UniWM (ECCV 2026), LCVN (NeurIPS 2026 oral), GoViG (ACL Findings 2026) | World models plus planning, unified autoregressive world-action models, language as goal, egocentric-only methods |
| **Bohan Xiong** (UW) | Organizer; maintains the toolkit (`JostarXiong` / `JosephJostar`) | Author of the Oct-14 rules clarification (PR #2) | Strict inference-input definition; privileged information allowed at training only |
| **Yetong Sha** (UW) | Organizer; LCVN co-author | — | — |
| **Zhi-Qi Cheng** (UW Tacoma, MILab director) | Program committee; senior author on all MILab papers | Multimodal foundation models, embodied AI | Same as MILab |
| **Shaoyuan Xie, Junhao Liu** (UCI) / **Qi Alfred Chen** (UCI, PC) | Track 3 (SafeDriveVLA, CoRL 2026) | Navigation-conditioned world-model "dreaming"; Strict/Cautious/Fallback driving modes; Chen's ASGuard lab works on autonomous-vehicle security | Safety-aware reasoning. *Inference:* security researchers are likely to spot evaluation-harness exploits |
| Henrik Christensen (UCSD), Ziwei Liu (NTU), Wei Tsang Ooi (NUS), Benoit Cottereau (CNRS), Shijie Li and Lai Xing Ng (A*STAR) | Program committee | Robotics systems; generative / world models; multimedia; perception | Broad; Christensen is classic map-based robotics *(prior knowledge)* |
| Wenhao Ding (NVIDIA), Xian Sun (Meta) | Industry mentors | Not verified this session (search budget exhausted) | Unknown |

**RoboPAD workshop** (verified from the cloned `robotpad2026.github.io` source, commit of 2026-10-09):
- **When and where:** Dec 12, 2026, Paris.
- **Topics:** VLA Models, World Models, World Action Models, RL, Learning from Human Feedback, Real-to-Sim-to-Real, Test-Time Adaptation, Continual Learning, Cross-Embodiment, Embodied Reasoning & Memory, **Agent Harnesses**, Self-Improvement, **Evaluation & Safety**.
- **Invited speakers:** Ivan Laptev (MBZUAI), Gim Hee Lee (NUS), Cordelia Schmid (Inria/Google), Soujanya Poria (NTU), Elliot Chane-Sane (Mistral AI).
- **Workshop organizers:** Shijie Li, Shizhe Chen (Inria), Ziwei Wang, Jiafei Duan, Sihao Lin, Changliu Liu (CMU, safe control), Gerhard Neumann.
- **The audience is VLN-literate.** Laptev, Schmid and Shizhe Chen wrote HAMT/DUET. Gim Hee Lee's group wrote HNR, g3D-LF, Dynam3D and Sim2Real-3DFF (all in the cloned `sota/`).
- **Schedule:** the "RoboWorld Challenge" session is **15:55–16:25: 30 minutes for all three tracks**, so roughly 1–2 short talks per track (inference).

---

## 2. Evidence on "innovative" vs "exploity"

### 2.1 The Oct-14 rules clarification (PR #2): verified text

Location: `ext/track2-jostar` branch `origin/bohan/clarification-Oct14` (commits `0f944d3`, `8289590`, 2026-10-14). `git ls-remote https://github.com/roboworld2026/track2` shows `refs/pull/2/head = 8289590` and `refs/pull/2/merge = d6155e0` (merge test ref by "Bohan Xiong", 2026-10-14 12:04 −0700). `main` is still `2d408b2` (2026-10-09), so the PR is **open and unmerged**.

Key added text:
- **Input:** "... ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference."
- **Sensor Setup:** "One forward-facing RGB-D camera. Adding additional cameras is not permitted; panoramic views must be acquired by rotating in place (rotation actions count toward the action budget)."
- **Q10:** "Publicly available pretrained models are allowed … Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training."
- **Q11:** "During validation and test inference, no: the agent must not directly read `human_motion.json` … During training, however, ground-truth human information from released training episodes may be used as privileged supervision."
- **Q12:** "commercial or closed-source model APIs are permitted. However, we encourage participants to develop their own methodological contributions and explore smaller, open-weight models (such as a 7B Qwen-VL model) … We discourage relying primarily on powerful closed-source models."
- **Q4 (revised):** human animation advances with wall-clock time, and "All official submissions are replayed in the standardized organizer-controlled CodaBench environment".

Not explicitly addressed (gray areas):
- reading the scene mesh or navmesh at inference;
- non-parametric memory carried across episodes in the same test building;
- running several local rollouts and picking one;
- pre-exploration tours of the test buildings.

The Input row lists *only* RGB-D plus pose. That is strong evidence the intended answer for mesh and navmesh use is "no".

### 2.2 Precedent: RoboSense 2025 Track 2 (social navigation, same lead organizer)

Source: `ext/B8-robosense2025-track2/README.md` lines 32 and 340–360, and the FAQ at 449–466.
- "Participants must design navigation policies based solely on RGBD observations and odometry, **without access to global maps or privileged information**."
- Phase 2 accepted **code submissions only**. "We may perform additional audits for the top-performing teams." "Awards will only be granted to submissions that have successfully passed the reproducibility audit."
- Disqualification for: not running real inference in the container; a fabricated result.json; "accessing extra environmental information or sensors beyond the allowed observation keys"; and *open-source models only* (no proprietary models).
- Community norm, stated in the 2nd-place report: hierarchical global-planner methods "inherently depend on comprehensive environmental knowledge, rendering them impractical for real-world deployment". Privileged human-agent information is acceptable as an *auxiliary training signal* (citing Falcon).

### 2.3 Award history in Kong's challenges

| Challenge | Innovation award winners | Their rank | What the idea was |
|---|---|---|---|
| RoboSense 2025, T2 Social Nav | Xiaomi EV-AD VLA | **2nd** (0.6994 vs 1st 0.7022, baseline 0.6248; 16 teams) | Proactive Risk Perception Module: auxiliary head predicting distance-graded collision risk per nearby human, on the Falcon baseline |
| RoboSense 2025, T1 Driving w/ Language | UCAS-CSU | **2nd** | Mixture-of-Prompts router, task-specific spatial-reasoning prompts, visual assembly; Qwen2.5-VL-72B; 70.87% / 72.85% |
| RoboSense 2025, T5 Cross-Platform 3D Det | Visionary | **1st** | "DataEngine": unified pre-training plus viewpoint normalization |
| RoboSense 2025, other | "Best Technical Report" awards went to T3 4th and 5th place and T4 2nd place | — | — |
| RoboDepth 2023 | Scent-Depth, Ensemble, AIIA-RDepth | **none on the podium** | Robust depth (normalization/augmentation etc.) |
| RoboDrive 2024 | "Solutions with excellent novelty", chosen by the program committee, "two per track" (site) vs "two teams" (agenda) | unknown | — |

The 1st-place RoboSense social-nav team (PER-Falcon: positive-episode replay, a generic RL training trick) was **not** the innovation winner. The innovation award went to the module that addressed the track's theme (anticipating human collisions).

Other patterns:
- Every RoboSense top-5 team built on the official baseline, Falcon. Gains were about +7.7 Total points, so the absolute novelty bar was modest.
- Kong's challenges always publish a joint summary paper: RoboDepth arXiv 2307.15061, RoboDrive 2405.08816, RoboSense 2601.05014. RoboSense drew 143 teams from 85 institutions in 16 countries, and its paper consolidates 23 winning solutions. The Top-5 reports become sections of that paper, so a crisp one-figure method with a clean ablation table gets the best write-up.

### 2.4 The organizers' own stated values (verified quotes)

- **Track 2 page** (`havln-challenge/index.html`, `track2.html`):
  - "real-world spaces are shared with moving people who serve as **both semantic landmarks and dynamic obstacles**";
  - "**without relying on static-world assumptions**";
  - "balance instruction following and social compliance **under partial observability** and real-time human interactions";
  - "encourages **world models that anticipate human trajectories and future observations**, and VLAs that ground human-centric instructions in egocentric video and output low-level actions";
  - "waypoint planners, and topological planners are welcome".
- **UniWM:** "explicitly grounds action decisions in visually imagined outcomes … hierarchical memory".
- **LCVN:** a diffusion world model (DFoT-based, `ldit_video_social`, trained on SCAND/HuRoN social-nav videos) plus a latent actor-critic with intrinsic rewards, or a unified autoregressive model. "Language guidance functions as the goal specification".
- **GoViG:** "Unlike previous methods that rely on semantic maps or structured annotations, GoViG operates purely on egocentric visual input."
- **SafeDriveVLA:** a frozen latent world model (V-JEPA 2 encoder plus action-conditioned predictor) "dreams" the outcome of following the instruction, then picks a Strict, Cautious or Fallback mode.
- **HA-VLN 2.0:** "explicit social modeling improves navigation robustness and reduces collisions", plus a sim-to-real robot demo.
- **HCSG** is the only third-party HA-VLN-CE method with results. It is human-centric (geometric forecasting plus VLM semantic interpretation of human activity, a Social Distance Loss, and a real robot), with val_unseen SR 0.24 / CR 0.36 / TCR 5.02. This is the style the benchmark community currently rewards.

### 2.5 Profile: what the committee will see as innovative and what it will see as exploity

| Likely seen as **innovative / principled** | Likely seen as **exploity / non-compliant** |
|---|---|
| World models that anticipate human motion or occupancy and future observations, used inside planning (imagine, then act) | Reading `human_motion.json` or simulator human states at test time (explicitly banned, Q11) |
| Humans treated as semantic landmarks *and* obstacles (VLM activity grounding) | Rendering from arbitrary or extra viewpoints at test time (counts as "additional cameras", Q8) |
| Privileged information as a *training-time teacher* or auxiliary label (Q11 allows it; "learning by cheating") | Planning on the ground-truth navmesh or mesh of test scans ("global maps / privileged information" in the RoboSense precedent; outside the Input row) |
| Post-training a VLA (DAgger → RL/GRPO) with safety-shaped rewards (the RoboPAD theme) | Using the simulator collision flag to retry or pick among many local rollouts on test episodes (an undisclosed "beam search" setting) |
| Safety shields / certified collision avoidance, metric-aware decision-making | Exploiting benchmark mechanics: wall-clock human freeze, the collision_num allowance, Euclidean NE quirks |
| Robustness analysis (replay timing, instruction paraphrase), honest failure analysis, reproducibility | Leaderboard probing (100 full-precision submissions could leak per-episode outcomes) |
| Small open-weight models (7B Qwen-VL) used cleverly | Relying mainly on frontier closed APIs (allowed but discouraged, Q12) |
| Real-robot or sim-to-real evidence (HA-VLN 2.0, HCSG) | Training on val (ground truth is released) or on test; using the 2 sibling instructions of the same trajectory, or the original R2R test instructions, at test time |

**Action-sequence forensics risk (inference, MEDIUM).** Submitted action tapes can reveal privileged planning on their own. Tell-tale signs:
- no look-around rotations;
- near-geodesic paths through areas the camera never observed;
- avoidance of humans who were never in view;
- zero collisions across 3,408 unseen episodes.

A Score of about 76–94 when the field sits around 20–50 would invite a code check.

---

## 3. Compliance tiers for candidate techniques (under PR #2)

| Tier | Techniques | Status |
|---|---|---|
| **T0 Compliant** | Closed-loop agent using one forward RGB-D camera plus ground-truth pose; panoramas by rotation; online mapping from depth plus pose; person detection and tracking; pretrained VLAs/VLMs; external VLN data (R2R/RxR/ScaleVLN/…); privileged ground-truth humans and navmesh **on train scenes only** for experts, auxiliary labels and RL; local replay on val for evaluation (not training) | Safe; aim the official entry here |
| **T1 Probably fine, disclose** | Closed APIs (discouraged); deterministic re-runs; using the agent's *own* confidence to choose among its own stochastic rollouts; replay-timing-robust margins | Disclose in the report |
| **T2 Gray: ask in writing** | Cross-episode memory within a test building (IVLN-style); pre-exploration tours with egocentric sensors; test-time self-training on test scenes (may break Q10, "test splits must not be used for training"); choosing among rollouts by the *simulator* collision flag; using sibling instructions of the same trajectory | Do not rely on these without an organizer answer |
| **T3 Non-compliant** | `human_motion.json` at inference; arbitrary-view rendering; ground-truth navmesh/mesh planning at inference (very likely); training on val/test; leaderboard probing | Do not submit. Use only as oracle and diagnostic analysis |

---

## 4. Framing the offline full-information planner

**Honest bottom line.** No wording turns a T3 pipeline into a compliant one once code is audited. Use the planner where it *is* legitimate and valuable:
1. **As a privileged teacher on the 61 train scans** (HA-R2R train = 10,819 episodes). It generates collision-free, human-aware expert trajectories under the HA-VLN collision semantics. Then DAgger: the expert relabels the student's states. Then RL with a reward shaped like the Score. Q11 explicitly allows this. Frame it as **"Learning-by-cheating for social VLN: privileged socially-safe teacher → egocentric student"**. This is the same pattern as Falcon/Xiaomi auxiliary privileged signals, and it reflects WNM-3D's finding that DAgger-SFT on planner-generated demos gives the largest SR gain.
2. **As an oracle ceiling in the report.** For example: "with oracle goal and privileged geometry, Score is about 94; with our VLM goal inference on privileged geometry, about 76; our compliant agent, X". This shows *where* the difficulty lies (goal inference vs. control vs. social safety). Kong-style evaluation insight is valued.
3. **As local diagnostics** (val-only): collision forensics, NE decomposition, timing-regime robustness.

**If organizers explicitly allow scene-geometry use in writing** (unlikely given PR #2), these framings are principled, with honest perception risk noted:

| Framing | Literature anchor | How organizers will likely see it |
|---|---|---|
| *Digital-twin / known-map VLN*: map-conditioned language grounding plus socially aware trajectory optimization | VLMaps, HOV-SG, LM-Nav, MapGPT *(prior knowledge)*; GSA-VLN (ICLR 2025, persistent environments, verified README) | Conflicts with "partial observability" and with GoViG's anti-map stance. HIGH risk for innovation, even if ranked |
| *Pre-exploration setting*: explore with egocentric RGB-D first, then follow instructions on a self-built map | R2R "pre-explore" leaderboard category (EnvDrop/RCM) is a recognized *separate* setting; IVLN; MemoryVLN cross-context memory reuse | Better: only egocentric sensors are used. Must be labeled as a different setting; test-time training may violate Q10 |
| *World-model-in-the-loop verification*: imagine or verify candidate plans before committing | NWM (CVPR 2025) ranks external-policy trajectories; UniWM/LCVN imagined rollouts; Real-to-Sim-to-Real is a RoboPAD topic | Legitimate only if the world model is *learned or reconstructed from the agent's own observations*. Using the ground-truth simulator as the "world model" is oracle rehearsal |

Mandatory in any case: an **information-use disclosure table** (train-time vs. test-time inputs) and an **audit manifest** listing every file the inference process read, with hashes.

---

## 5. Low-cost components that add genuine innovation (compliant, theme-aligned)

Ranked by value-per-cost. The names are suggestions for the report.

1. **Shielded Discrete Executor (SDE)**: certified collision avoidance for the 0.25 m / 15° action space. *Cost: low.*
   - Build an occupancy map from depth plus ground-truth pose (Q9 allows pose).
   - Use an exact kinematic model of Habitat's try_step/sliding semantics (see A2/C1 findings).
   - Inflate obstacles by agent radius 0.1 m plus a margin; add human swept-volume margins (module 2) with **conformal calibration** on train/val (calibration only).
   - Veto any action predicted to collide; plan escape turns.
   - *Why it matters:* SR requires zero (baseline-adjusted) collisions. The vln-safe guard alone raised SR by 6.9–29.3 points under blocking. 38.5–56.8% of "successful" R2R-CE episodes contain contact.
   - *Taste match:* Evaluation & Safety (RoboPAD); Changliu Liu's safe-control line.
2. **Human Occupancy Foresight (HOF)**: a small world model that predicts *phase-agnostic swept occupancy* (the union of a human's body over the 120-frame motion loop, plus short-horizon forecast) from a short egocentric RGB-D track plus an activity label. *Cost: low–moderate* (BEV ConvGRU/transformer; data rendered on 72 non-test scans).
   - Trained with ground-truth human motion from train episodes, which Q11 explicitly allows as privileged supervision.
   - *Why it matters:* official replay human pose depends on scorer wall-clock speed (frames advance ~12 s, then freeze). A margin covering the whole loop is the principled, replay-robust answer. Human motion extents are small (median 0.03 m, p90 0.8 m), so the model is learnable.
   - *Taste match:* "world models that anticipate human trajectories" (track page); Falcon precognition; UniWM/LCVN foresight.
3. **Humans-as-Landmarks grounding (HALo)**: detect people, caption their activity with an open 7B Qwen-VL (the scale the organizers recommend), and align captions to the instruction's human-activity clauses (HA-R2R instructions are 20–60% human-related content). The result is a progress estimate along the instruction and stop-condition evidence. *Cost: low* (zero-shot VLM plus text alignment; optionally a small learned progress head).
   - *Taste match:* "both semantic landmarks and dynamic obstacles"; HCSG's semantic stream.
   - Do NOT use the annotation text in `human_motion_text.json` at inference (metadata, T3).
4. **Score-aware stopping (SAS)**: Bayes-optimal stop decision under the composite Score. Choose the stop point that maximizes E[0.8·1(d<3 m) + 0.2·3/(3+d)], given a belief over goal location from the policy/VLM. *Cost: very low.*
   - *Why it matters:* dScore/dSR ≈ 77 points per unit SR (at SR 0.5).
5. **Privileged-teacher post-training (PTP)**: privileged expert on train scans → DAgger → GRPO-style RL with the reward = success × collision-free + social shaping, on a VLA (StreamVLN / SimpleVLN / InternVLA-N1 / NaVILA family; see B2). *Cost: moderate–high*, but compute is not a constraint here.
   - *Taste match:* RoboPAD's core theme (post-training adaptation, RL fine-tuning of VLAs); X-NavDP (CoRL 2026) and WNM-3D (DAgger then DanceGRPO) are 2026 precedents.
6. Optional: **latent foresight ranking**. Use a learned world model (UniWM/LCVN-style or NWM-style) to score a few candidate action chunks by imagined outcome vs. instruction. *Cost: high, uncertain gain.* Only worth doing as a small ablation that "connects to the organizers' world-model agenda". LCVN, UniWM and GoViG READMEs list datasets but no pretrained checkpoints (MEDIUM), so it would need training.
7. Optional: **real-robot clip** of HOF + SDE (HA-VLN 2.0 and HCSG both include sim-to-real). *Cost: high.* It has strong "wow" value for the oral but is not needed for the award.

---

## 6. World-model and VLA navigation landscape: what counts as "current" in 2026

- **Navigation World Models (NWM, CVPR 2025):** 1B-parameter Conditional Diffusion Transformer trained on egocentric human and robot video. It plans by CEM, or *ranks trajectories from an external policy* by imagining their video and scoring the final frame against the goal. The ranking mode is the cheapest way to "add a world model" to an existing policy.
- **UniWM (ECCV 2026, organizers):** a unified autoregressive backbone for visual foresight plus planning with hierarchical memory. Reports up to 30% SR gains on Go Stanford / ReCon / SCAND / HuRoN, and zero-shot transfer to TartanDrive.
- **LCVN (NeurIPS 2026 oral, organizers):** 39,016 trajectories and 117,048 human-verified instructions. LCVN-WM (DFoT diffusion) + LCVN-AC (latent actor-critic, intrinsic rewards) vs. LCVN-Uni (autoregressive). Latent imagination gives more coherent rollouts; the unified model generalizes better to unseen environments.
- **NavMorph (ICCV 2025):** self-evolving latent world model for VLN-CE. R2R-CE monocular val-unseen SR 47.9 / SPL 33.2 vs. VLN-3DFF 43.8; removing self-evolution drops SR from 47.91 to 45.08.
- **WNM-3D (arXiv 2608.07267, 2026):** block-causal DiT world-action model with frozen 3D geometry tokens. SFT on A* demos → DAgger → Counterfactual DanceGRPO; the DAgger stage gives the largest SR gain.
- Other 2026 world-action models seen in search results: UniNav (2608.03244), WAM-Nav (2606.04907), "Policy-Guided World Model Planning for LCVN" (2603.25981, Drexel; Feng Liu co-authored LCVN), "Visual Representation and History Modeling for NWM" (2609.29555).
- **VLA navigation:**
  - NaVILA (RSS'25): two-level VLA plus locomotion.
  - Uni-NaVid (RSS'25): video VLA unifying navigation tasks.
  - StreamVLN: R2R-CE SR 56.4 / SPL 50.2 with v1-3 data; Go2 real-robot code.
  - InternVLA-N1: dual-system; InternData-N1 has 830k VLN samples.
  - SimpleVLN: native MLLM, IL → DAgger → RL.
  - JanusVLN, MemoryVLN, Dynam3D (Gim Hee Lee's group).
  - X-NavDP: RL post-training of navigation diffusion policies (CoRL 2026).
  - Details are in B2. "GR00T navigation" was not verified this session; GR00T N1 is a humanoid manipulation VLA *(prior knowledge)*.
- **Social navigation:** Falcon (ICRA 2025, future-aware auxiliary tasks) and RoboSense 2025 winners (PER replay, proactive risk, IL→RL two-stage, cutout for occlusion, hybrid parameter tuning). HCSG (2026) is the first human-centric VLN-CE method on HA-VLN-CE. DPed-VLN (2026) is a Habitat-3.0 ORCA-pedestrian VLN benchmark.

**Implication.** The genuinely open slot on this benchmark is *a world model for humans* (occupancy/motion foresight) wired into a *safe executor*, plus *humans-as-landmarks* grounding. Pixel-level video world models are expensive and not needed to claim "world-model-based".

---

## 7. Score arithmetic (how outliers look; what matters)

Score = 100 · Nav · (0.7 + 0.3 · Social); Nav = 0.8 SR + 0.2 · 3/(3+NE); Social = 0.75(1−CR) + 0.25/(1+TCR).

| Scenario | SR | NE | CR | TCR | Score |
|---|---|---|---|---|---|
| CMA baseline val_unseen (README) | 0.129 | 6.387 | 0.684 | 17.536 | **12.95** |
| HCSG-like | 0.24 | ~5.5 | 0.36 | 5.0 | 22.49 |
| Strong compliant A | 0.40 | 4.5 | 0.20 | 0.5 | 37.20 |
| Strong compliant B | 0.55 | 3.5 | 0.10 | 0.2 | 51.37 |
| Same SR, zero collisions | 0.55 | 3.5 | 0 | 0 | 53.23 |
| Privileged + VLM goal | 0.80 | 2.0 | 0 | 0 | 76.00 |
| Privileged + oracle goal | 0.98 | 0.8 | 0 | 0 | 94.19 |

Sensitivity at SR 0.5, NE 3.5, CR 0.1, TCR 0.2: dScore/dSR ≈ +77.2 per unit SR; dScore/dCR ≈ −11.1 per unit CR. SR dominates, and collisions mostly hurt *through SR gating* (any collision voids success when collision_num = 0; 3,171 of 3,408 test baselines are 0, per C2).

---

## 8. Draft technical-report outline

The outline follows the organizers' RoboSense 2025 template (`RoboSense2025_Technical_Report.zip`):
- two-column CVPR-style LaTeX, no page limit;
- **required:** Abstract, Introduction, Method with **≥1 method figure**, Experiments (setups, implementation, comparative study, ablations) with **≥1 visualization**, Conclusion with limitations and future work;
- "final rank is subject to the successful submission of this report", "no extension";
- the RoboSense deadline was about 2 weeks before the workshop.

Expect the RoboWorld report to be due around early December. Phase 2 closes Nov 30 and awards are Dec 12 (inference, MEDIUM).

**Title (example):** *Foresee, Ground, Shield: Human-Occupancy World Models and Humans-as-Landmarks Grounding for Safe Human-Aware VLN*.

0. **Abstract.** Problem (success-but-unsafe; humans as landmarks and obstacles; partial observability) → 3 named modules → test Score / SR / CR / TCR and rank → one-line compliance statement ("egocentric RGB-D + pose at inference; privileged information only for training").
1. **Introduction.**
   - Gap: collision-gated SR; humans treated as static obstacles; 112-word human-centric instructions.
   - Contributions (3 bullets): HOF world model; HALo grounding; SDE plus privileged-teacher post-training.
   - Headline numbers.
2. **Related work.**
   - VLN-CE agents (graph/waypoint, VLA).
   - World models for navigation (NWM, UniWM, LCVN, NavMorph, WNM-3D).
   - Social navigation (Falcon, RoboSense winners, HCSG, HA-VLN 2.0).
   - Safety shields and conformal prediction.
   - Cite the organizers' work accurately and position ours as complementary.
3. **Setting and compliance** (keep it short but explicit).
   - Table: inputs at train vs. test; models used (open weights; sizes; any API calls).
   - Statement mapping each module to README FAQ Q8–Q12.
   - Audit manifest description.
4. **Method.** Figure 1 is a system overview.
   - 4.1 Perception and mapping: pose-registered depth fusion; person detection and tracking.
   - 4.2 HOF human-occupancy world model: architecture, privileged training targets, conformal calibration.
   - 4.3 HALo humans-as-landmarks grounding: VLM prompts, clause alignment, progress head.
   - 4.4 Policy and goal reasoning: base VLA/graph agent; privileged teacher; DAgger; RL reward.
   - 4.5 SDE shielded discrete execution: exact step model, veto/escape logic, guarantees and assumptions.
   - 4.6 Score-aware stopping.
5. **Experiments.**
   - 5.1 Setup: HA-R2R splits, metrics, official Score; local replay vs. CodaBench agreement.
   - 5.2 Implementation: models, compute, training time, inference cost per episode.
   - 5.3 Main results: test leaderboard; val_unseen table vs. CMA, BEVBert, ETPNav, HCSG.
   - 5.4 Ablations (one row per module).
   - 5.5 Robustness: replay-timing regimes (fast / throttled / frozen / all-frames), instruction paraphrase, human density.
   - 5.6 Oracle ceilings, clearly labeled as non-submitted analysis (privileged geometry ± oracle goal), to locate the bottleneck.
   - 5.7 Failure analysis with visualizations: top-down trajectories, HOF predictions, HALo alignments.
6. **Conclusion.** Limitations (static-human collision proxy, wall-clock animation, simulator-specific step semantics) and future work (real robot; learned video world models). Broader impact: safety around people.
- **Appendix.** Docker digest and seeds, exact commands, prompts, hyperparameters, per-scan results, released code/model links. A reproduction script that regenerates the submitted ZIP bit-for-bit (deterministic decoding; cached VLM outputs).

**Talk (oral):** 5–8 min, given the 30-min slot for three tracks. Structure:
1. the problem in one clip;
2. one overview slide;
3. three module slides, each with an ablation number;
4. robustness and safety;
5. the oracle-ceiling insight.

Prepare to present in person in Paris on Dec 12, with a recorded backup.

---

## 9. Contradictions with CONTEXT "Established facts"

- **Fact 6 / Fact 8** ("No explicit rule forbids using the simulator/scene geometry offline"; the strategic hypothesis that any offline computation is fine): **contradicted in intent** by organizer PR #2 (Input row; Q8 no extra cameras; Q11 no human ground truth at inference) and by the RoboSense 2025 precedent (no global maps or privileged information; code audit). The merged README is still permissive in wording, so the rule is not yet "official". Award verification makes the intended rule the operative risk.
- **Fact 5** (test human placements possibly in the Phase-2 bundle): even if shipped, PR #2 says they exist "to support simulator rendering" and must not be read for planning.
- Also noted: the website's old "Terms & Conditions" (no external datasets; mandatory code for manual verification) was a stale RoboDrive template. It was removed in commit 2e62d94 (2026-10-06) and does not apply. PR #2 Q10 explicitly allows external datasets.

---

## 10. Recommendations (actionable)

1. **Now (before Phase 2 investment):** open a public GitHub issue on `roboworld2026/track2` referencing PR #2. Ask for written answers on:
   - (a) is reading MP3D mesh/navmesh at inference allowed?
   - (b) cross-episode memory within a test building;
   - (c) running multiple local rollouts and choosing one (by agent confidence vs. simulator collision flag);
   - (d) pre-exploration tours;
   - (e) using sibling instructions of the same trajectory.

   Also email roboworld2026@gmail.com. Treat PR #2 as binding until told otherwise.
2. **Make the official Phase-2 entry T0-compliant:** a closed-loop egocentric RGB-D + pose agent with SDE + HOF + HALo + SAS on top of the best VLA/graph policy from B1/B2. Instrument the inference process with an **input firewall plus audit manifest** (the process cannot open `human_motion.json`, navmesh caches or extra sensors; log hashes).
3. **Redirect the privileged planner** into expert generation on train scans, DAgger/RL post-training, val-only diagnostics, and oracle-ceiling analysis for the report.
4. **Target the innovation award deliberately:** 3 named, theme-aligned modules, each with a clean ablation; at least 1 method figure and 1 visualization; robustness section; reproducible code. Cite and complement HA-VLN 2.0, UniWM, LCVN, GoViG and Falcon.
5. **Avoid exploit signals:** no leaderboard probing; no training on val; no sibling-instruction or original-R2R-instruction leakage; no metric-quirk exploitation (collision_num allowance, wall-clock freeze, Euclidean NE). If any T1/T2 technique is used, disclose it.
6. **Prefer open-weight 7B-class models** for core modules. Use closed APIs at most for offline data generation or analysis, and disclose them.
7. **Report logistics:** draft the skeleton by Nov 20; automate ablation tables from experiment logs; plan in-person attendance in Paris on Dec 12.

---

## 11. Open questions

- Will PR #2 be merged, and when? Does "sequential egocentric RGB-D observations" implicitly ban mesh/navmesh use at inference (very likely), or will the organizers allow geometry?
- Is "Best Innovative Solution" one per track or one overall? Track READMEs list it per track; RoboSense gave one per track for 3 of 5 tracks.
- The tech-report template and deadline for RoboWorld 2026. Will the organizers publish a joint challenge summary paper (as in all three previous Kong challenges)?
- How many orals per track within the 30-min challenge slot, and are remote presentations allowed?
- Whether cross-episode memory or pre-exploration counts as "training on test splits" (Q10).
- The research focus of industry mentors Wenhao Ding (NVIDIA) and Xian Sun (Meta). Not verified; search budget exhausted.

---

## 12. Sources

**Local (verified by reading files or git objects):**
- `ext/track2-jostar`: branch `origin/bohan/clarification-Oct14`, commits `0f944d3`, `8289590` (README diff, Q8–Q13). `git ls-remote https://github.com/roboworld2026/track2` gives `refs/pull/2/head = 8289590`, unmerged; `main = 2d408b2`.
- `ext/track2/README.md`, lines 19–31, 77–83, 258–277 (awards, Q2 verification).
- `ext/roboworld2026.github.io/index.html`, `track2.html`, `leaderboard.html`; history commits `1fdad87` (May 2026: 5 tracks, cash prizes, Rising Star award) and `2e62d94` (Oct 6 rewrite; stale T&C removed).
- `ext/havln-challenge/index.html` (track page values) and PR refs 1–3.
- `ext/B8-robotpad/index.html`, `call-for-papers.html` (RoboPAD topics, speakers, organizers, schedule 15:55–16:25).
- `ext/B8-robosense2025-toolkit/README.md` (awards, innovation winners, technical reports); `RoboSense2025_Technical_Report.zip` (template sections); `technical_reports/RoboSense2025_Track2_{AreIvan,XiaomiEV_AD_VLA}.pdf` (scores table).
- `ext/B8-robosense2025-track2/README.md` (no global maps or privileged information; audit; disqualification; open-source only).
- `ext/B8-robodrive-24-toolkit/README.md` (Innovative Award = "excellent novelty"); `ext/B8-worldbench-RoboDepth/README.md` (innovation prize teams).
- `ext/B8-LCVN/README.md` and `lcvn-wm/configurations/*social*`; `ext/B8-UniWM/README.md` ([ECCV 2026]); `ext/B8-GoViG/README.md` (egocentric-only stance).
- `ext/HA-VLN/README.md` (IROS 2026; organizer links).
- `ext/sota/{HCSG/index.html, vln-safe/README.md, StreamVLN, NaVILA, Uni-NaVid, NavMorph, InternNav, NavDP, Dynam3D, MemVLN, SimpleVLN}`; `ext/GSA-VLN/README.md`.
- Sibling findings: `findings/B1`, `B2`, `C1`, `C2`, `A1`, `A2`.

**Web (via WebSearch, extended):**
- https://arxiv.org/abs/2603.26741 ; https://github.com/UWMILab/LCVN (LCVN)
- https://arxiv.org/abs/2510.08713 ; https://github.com/F1y1113/UniWM (UniWM)
- https://aclanthology.org/2026.findings-acl.732/ ; https://arxiv.org/pdf/2508.09547 (GoViG)
- https://arxiv.org/abs/2503.14229 ; https://arxiv.org/html/2406.19236 (HA-VLN 2.0 / 1.0)
- https://arxiv.org/abs/2610.20609 ; https://safedrive-vla.github.io/SafeDriveVLA/ ; https://github.com/ASGuard-UCI/safedrive-vla (SafeDriveVLA)
- https://robotpad2026.github.io/ ; https://github.com/robotpad2026/robotpad2026.github.io
- https://arxiv.org/abs/2601.05014 (RoboSense challenge report) ; https://arxiv.org/abs/2510.07871 (Xiaomi report) ; https://arxiv.org/abs/2510.24152 (UCAS-CSU)
- https://github.com/robosense2025/toolkit ; https://github.com/robosense2025/track2
- https://arxiv.org/abs/2307.15061 (RoboDepth report) ; https://arxiv.org/abs/2405.08816 ; https://robodrive-24.github.io/ ; https://ldkong.com/robodrive2024_agenda.pdf (RoboDrive)
- https://arxiv.org/abs/2509.07996 (3D/4D world modeling survey, Kong)
- https://arxiv.org/abs/2412.03572 ; https://openaccess.thecvf.com/content/CVPR2025/html/Bar_Navigation_World_Models_CVPR_2025_paper.html (NWM)
- https://arxiv.org/abs/2506.23468 (NavMorph) ; https://arxiv.org/abs/2608.07267 ; https://github.com/TeleHuman/WNM-3D (WNM-3D)
- https://arxiv.org/pdf/2608.03244 (UniNav) ; https://arxiv.org/pdf/2606.04907 (WAM-Nav) ; https://arxiv.org/pdf/2603.25981 (Policy-guided WM planning)
- https://github.com/jacobkrantz/VLN-CE ; https://eval.ai/web/challenges/challenge-page/719/overview (VLN-CE challenge: local runs + trajectory JSON submission; sunsetting Jan 2026)
- https://aihabitat.org/challenge/2021/ ; https://aihabitat.org/challenge/2023/ (Habitat: "no ground-truth map; only sensory input")
- https://arxiv.org/pdf/1904.04195 ; https://arxiv.org/pdf/2307.15644 ; https://arxiv.org/pdf/2203.12667 (R2R single-run / pre-explore / beam-search settings)
- https://directory.tacoma.uw.edu/employee/zhiqics ; https://depts.washington.edu/uwmilab/publications (Zhi-Qi Cheng, MILab)
