# Rules, ethics and defensibility (v2): a compliance tier for every technique under organizer PR #2, what to disclose, and the single GitHub issue to post

**Topic:** `C3-rules-ethics-and-defensibility` · **Date:** 2026-10-24 · **Supersedes** the v1 written at 19:22 (backup: `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/c3_scripts/C3-v1-backup.md`)

> **Verification limits.**
> - The WebSearch budget was exhausted, so no web searches were run for this note.
> - GitHub MCP access to roboworld2026/track2 was denied.
> - PR and issue status was verified with `git ls-remote` and WebFetch of github.com pages.
> - The CodaBench Terms could not be read (site down).
> - Items marked [FROM MEMORY] are unverified.

## Summary

**Rule status.**
- Binding text: the published Track 2 rules (main `2d408b2`, website `84d0bc2`). They say only that any method that "outputs valid actions is welcome", that award teams "may be asked to provide code or models for verification", and that the CodaBench Terms (unseen; site down) govern.
- Intended rules: the organizers' open, unmerged **PR #2** (Oct 14, by organizer Bohan Xiong, no reviews or comments). Its inputs are episode ID, initial pose, instruction, GPS+compass, and sequential egocentric RGB-D from **one** forward camera. Rules:
  - `human_motion.json` is "strictly prohibited during inference";
  - no extra cameras, and rotations used for panoramas must be in the submitted sequence;
  - pretrained models and external data are allowed;
  - val/test must not be used for training;
  - ground-truth humans may be used for training;
  - closed APIs are allowed but discouraged.
- We treat PR #2 as binding. We read its rules through one **Information Locality** principle: an episode's actions may depend only on its own inputs, on observations bought by actions in its own submitted sequence, and on prior learning.

**Verdicts.**
- **CLEARLY ALLOWED:**
  - the closed-loop RGB-D+GPS agent;
  - unlimited compute per step (including per-step sampling/voting and learned world models);
  - pose-delta bump detection within one run (it is mathematically identical to Habitat's collision flag);
  - privileged teacher data on the 61 train scans;
  - external pretrained models and data;
  - val for aggregate model selection;
  - genuine whole-pipeline A/B submissions;
  - local replay for format/determinism.
- **GRAY - ASK (default OFF):**
  - multiple local rollouts with self-consistency selection;
  - cross-episode memory in a building;
  - pre-exploration and test-time adaptation;
  - sibling-instruction sharing;
  - camera-parameter changes;
  - test-building renderings or test-exposed checkpoints.
- **PROHIBITED:**
  - human files or simulator human state at inference (text);
  - extra or virtual cameras and simulator look-ahead (text);
  - mesh/navmesh/nav-graph/MP3D annotations of test buildings at inference (intent plus precedent; confirm);
  - public original R2R test instructions (intent; confirm);
  - per-episode tape selection by ground truth or local replay;
  - engineered leaderboard probing and multiple accounts;
  - training on val/test;
  - human-in-the-loop on test.

**Why ask now.** The gray items are worth about +2 to +15 Score each (sibling fusion about +5, pre-exploration or memory about +8 to +14, multi-rollout about +9 to +15). We therefore post one public issue (section 5) plus a private note on public test-side files before Phase 2 opens on Oct 30. Defaults hold if there is no answer by Nov 7.

**Defensibility.** It comes from architecture, not promises:
- an env-server/agent split, so the agent process cannot read forbidden files;
- per-episode observation logs, so organizers can regenerate every tape;
- a disclosure checklist for the report.

## 1. Rule status: what binds, and what is only intended

- **Published (binding text):** `roboworld2026/track2` main `2d408b2` (Oct 9) and the website `84d0bc2` (Oct 23).
  - The only method rule is that any method that "outputs valid actions is welcome".
  - Enforcement is through award verification: "may be asked to provide code or models for verification".
  - Terms are "displayed on the official CodaBench competition". These are unseen; the old website T&C was a stale RoboDrive template, removed on Oct 6 (`2e62d94`).
- **Intended (unmerged): PR #2.**
  - Status: open since Oct 14 with no reviews or comments. Author JosephJostar0 (organizer Bohan Xiong); `refs/pull/2/head = 8289590`.
  - Its description says it "clarifies recent participant questions regarding allowed inputs, sensor configuration, and rules".
  - We treat it as binding.
- **Public discussion:** none. roboworld2026/track2 has 0 issues.

### 1.1 PR #2 diff, quoted (`git -C ext/jostar-track2 diff origin/main origin/bohan/clarification-Oct14`)

```diff
diff --git a/README.md b/README.md
index e9542c4..ef25e40 100644
--- a/README.md
+++ b/README.md
@@ -38,7 +38,8 @@ policy, planner, world model, or VLA method that outputs valid actions is welcom
 
 | Component | Description |
 |:--|:--|
-| Input | Episode ID, initial position and yaw, navigation instruction, and released human-aware episode inputs. |
+| Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference. |
+| Sensor Setup | One forward-facing RGB-D camera. Adding additional cameras is not permitted; panoramic views must be acquired by rotating in place (rotation actions count toward the action budget). |
 | Output | One sequence made from six discrete VLN-CE actions. |
 | Actions | `STOP`, `MOVE_FORWARD`, `TURN_LEFT`, `TURN_RIGHT`, `LOOK_UP`, `LOOK_DOWN`. |
 | Budget | 1–500 actions; all six actions count toward the limit. |
@@ -239,7 +240,8 @@ Each file follows this schema (the invented ID is only an illustration):
 ```
 
 Include every official episode ID exactly once. `STOP`, if present, occurs once
-at the end; sequences shorter than 500 actions require it. The examples in
+at the end; sequences shorter than 500 actions require it, while sequences of
+exactly 500 actions may omit it if terminated by the step limit. The examples in
 [`examples/submission`](examples/submission) demonstrate schema only and do not
 have complete manifest coverage.
 
@@ -267,7 +269,7 @@ Yes. Both actions are valid and count toward the 500 task steps.
 
 **Q4. Does an action advance a human animation frame?**
 
-No. Human animation follows released wall-clock behavior independently.
+No. Human animations advance with wall-clock time according to the configured motion FPS, rather than advancing one frame per action. Because execution time is affected by runtime performance and hardware, there is no single fixed wall-clock duration for each action (including `LOOK_UP` and `LOOK_DOWN`). All official submissions are replayed in the standardized organizer-controlled CodaBench environment, which determines competition scores.
 
 **Q5. Does local validation compute a Score?**
 
@@ -294,6 +296,30 @@ and place the licensed scenes under your host data root's
 `scene_datasets/mp3d/`. That root can be anywhere on your machine. When using
 the challenge Docker image, mount it at `/data/havln2` inside the container.
 
+**Q8. Can an agent add more cameras to obtain panoramic or 360-degree views?**
+
+No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget.
+
+**Q9. Can the agent read its position and heading during navigation?**
+
+Yes. The agent is permitted to read its position and heading from the simulator agent state (GPS + compass) throughout the episode. You are not required to estimate localization solely from actions and visual odometry.
+
+**Q10. Are pretrained models and external training datasets allowed?**
+
+Yes. Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects, general vision and language models, and off-the-shelf perception models such as person detectors. Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training.
+
+**Q11. Can an agent use `human_motion.json` or simulator ground-truth human states?**
+
+During validation and test inference, no: the agent must not directly read `human_motion.json` to obtain human positions or motion trajectories for planning. This file is provided to support simulator rendering; during inference, the agent should infer human positions and movements from its camera observations. During training, however, ground-truth human information from released training episodes may be used as privileged supervision, provided that it is not accessed during validation or test inference.
+
+**Q12. Are commercial or closed-source model APIs allowed?**
+
+There is no open-weights-only restriction, and commercial or closed-source model APIs are permitted. However, we encourage participants to develop their own methodological contributions and explore smaller, open-weight models (such as a 7B Qwen-VL model) as components of their approach. We discourage relying primarily on powerful closed-source models, although this is a recommendation rather than an eligibility restriction.
+
+**Q13. Does every action sequence need to end with `STOP`?**
+
+Sequences shorter than 500 actions must end with `STOP`. If an episode reaches the maximum budget of 500 actions, `STOP` may be omitted (the episode is terminated automatically by the evaluator's 500-step limit). In all cases, `STOP` may appear at most once and only as the final action.
+
 ## 🔗 Resources and Contact
 
 | Resource | Link |
@@ -305,7 +331,7 @@ the challenge Docker image, mount it at `/data/havln2` inside the container.
 | RoboPAD Workshop | [RoboPAD @ NeurIPS 2026](https://robotpad2026.github.io/) |
 
 For technical support, use [GitHub Issues](https://github.com/roboworld2026/track2/issues).
-For event and registration questions, email [roboworld2026@gmail.com](mailto:roboworld2026@gmail.com).
+For general inquiries, email [roboworld2026@gmail.com](mailto:roboworld2026@gmail.com).
 
 ### 💬 Community & Discussion
```

## 2. Unifying principle: Information Locality

An episode's submitted actions may depend only on three things:
- (i) that episode's own inputs: ID, start pose and **its own** instruction;
- (ii) observations acquired by actions **inside that episode's submitted sequence**: forward RGB-D plus GPS/compass (PR #2 Input row, Q8, Q9);
- (iii) knowledge learned beforehand from train or external data (Q10, Q11).

Each technique below is classified by whether it injects information from outside (i)-(iii).

## 3. Compliance-tier table

Verdicts are **CLEARLY ALLOWED**, **GRAY - ASK** or **PROHIBITED**.
- The *basis* column says whether a verdict rests on rule text, evident intent or precedent.
- *Default* is what we do if the organizers do not answer.
- *Item* is the number of the matching question in the GitHub issue (section 5).

| ID | Technique | Key rule touched | Verdict | Default if unanswered | Issue item |
|---|---|---|---|---|---|
| T01 | Closed-loop egocentric agent: one forward RGB-D camera (official config) + GPS/compass, run locally in the official simulator; panoramas only via TURN actions inside the submitted sequence; LOOK_UP/DOWN; STOP or 500-action cap | PR#2 Input row, Sensor Setup, Q8, Q9; README Q1 | **CLEARLY ALLOWED** | This is the submission regime (CLEAN-1). | - |
| T02 | Changing the single camera's resolution, HFOV or mounting height (e.g. higher-res RGB for a VLM, wider FOV to cut rotations) | PR#2 Sensor Setup, Q8 (silent on parameters) | **GRAY - ASK** | Keep the official task config (RGB 224x224 HFOV 90, depth 256x256, default height). | 2 |
| T03 | Unlimited compute per step: large open-weight VLM/LLM reasoning, model ensembles inside ONE run, K samples + majority vote at the same state (no extra environment steps), learned world-model imagination / look-ahead, dense 3-D mapping | README 'any method ... welcome'; no compute limit; Q12 | **CLEARLY ALLOWED** | Use it freely, with open-weight models in the inference path (Q12 discourages relying on closed APIs). | 4 |
| T04 | Multiple full local rollouts of the same test episode (different seeds/variants), then submit one chosen by self-consistency (endpoint agreement, agent confidence) | PR#2 Q8 (observations bought in-sequence); beam-search precedent | **GRAY - ASK (leans prohibited)** | OFF in submissions. Allowed only as a clearly labelled val ablation ('multi-rollout, not submitted'). | 4 |
| T05 | Simulator look-ahead: save/restore or clone the sim state, step-and-revert, render from poses the agent has not reached, or use the ground-truth simulator as the 'world model' | PR#2 Q8/Sensor Setup (no extra cameras); Track 1 rule | **PROHIBITED** | Never. The env server exposes reset/step only. | 4 |
| T06 | GPS-detected contact: infer a bump from a shortened MOVE_FORWARD displacement (pose allowed by Q9) and react within the same episode; reading Habitat's collided flag directly | PR#2 Q9 (pose allowed); collided flag not an input | **CLEARLY ALLOWED (pose-delta, within one run); collided flag read directly = GRAY - ASK** | Use pose-delta bump inference only to react (back off, re-plan) in the same run. Do not read the flag. Never use contacts to rewind or retry an episode. | 3 |
| T07 | Memory across episodes of the same building (maps/landmarks/human sightings from our own earlier test episodes, IVLN-style) | PR#2 Input row (unscoped); Q8; Q10; 'partial observability' | **GRAY - ASK** | OFF (fresh agent state per episode, asserted in code). | 5 |
| T08 | Pre-exploration tours of test buildings (instruction-free, egocentric sensors, actions not in any submitted sequence) and test-time adaptation of weights on unlabelled test observations | PR#2 Q8; Q10 (test not for training); pre-explore precedent | **GRAY - ASK (leans prohibited)** | OFF. | 5 |
| T09 | Sibling-instruction sharing: use the other instructions/outcomes of episodes with the same trajectory_id (IDs 3k+1..3k+3 share start and goal), e.g. goal voting across the 3 instructions | PR#2 Input row (own instruction); old README trajectory note | **GRAY - ASK (treat as prohibited by default)** | OFF. trajectory_id hidden from the agent process and used only for bookkeeping. | 6 |
| T10 | Public original R2R instructions or other external annotations of the same test paths (R2R_test.json 3 instr/path, FGR2R, VLN-CE test.json.gz text), joined via trajectory_id = R2R path_id | PR#2 Input row; Q10 (test splits); 'test GT not released' | **PROHIBITED (confirm)** | Never, in training or inference. Never placed in prompts. | 7 |
| T11 | Nav-graph / mesh use at inference: MP3D connectivity graphs, scene mesh, Habitat navmesh/PathFinder (navigability, geodesic distance), top-down maps, MP3D region/object annotations of test buildings | PR#2 Input row; website 'partial observability'; RoboSense/Habitat | **PROHIBITED (intent + precedent; confirm)** | Never at inference. Allowed: maps the agent builds from its own RGB-D + pose; waypoint predictors trained on train-scan graphs (Q10); navmesh/PathFinder for training teachers, val analysis and labelled oracle ceilings. | 1 |
| T12 | Local replay with ground truth for AGGREGATE metrics (val) and replay of final test tapes for FORMAT/DETERMINISM only | README Q5 (local replay for development); Q10 | **CLEARLY ALLOWED (val aggregate, model selection); test-tape validity replay = allowed, confirm** | Val: aggregate metrics for model/hyper-parameter selection. Test: validate the schema, and check that the replay reproduces the trajectory the agent recorded. Never look at per-episode collision outcomes. | 8 |
| T13 | Per-episode tape selection or editing using ground truth or local replay outcomes (val: pick the best tape per episode with GT and post it to Phase 1; test: pick/edit tapes by local collision counts against the simulator's human placements) | PR#2 Q11 (infer humans from camera); Q10 | **PROHIBITED** | Never. Phase 1 receives only genuine pipeline outputs. | 8 |
| T14 | Leaderboard probing: engineered or differential submissions (subset perturbations, masked or STOP-only test probes) to infer per-episode or per-building test information; multiple accounts | README limits; 'test GT not released'; Habitat/RoboDrive precedent | **PROHIBITED (genuine whole-pipeline A/B submissions are allowed)** | Phase 2: genuine variants only, <=2/day, logged. Calibration probes only in Phase 1 (val GT is public anyway). | 10 |
| T15 | Privileged teacher data for TRAINING: GT human trajectories/swept volumes, navmesh shortest paths, oracle actions, collision labels on the HA-R2R train split / 61 train scans (DAgger, distillation, RL rewards, detector fine-tuning) | PR#2 Q11 (privileged supervision in training); Q10 | **CLEARLY ALLOWED on train; PROHIBITED on val/test** | Use heavily, restricted to the 61 train scans and train episodes. | 9 |
| T16 | Training on renderings of the 18 test buildings (even unlabelled), or using public checkpoints whose data may include them (R2R 'pre-explore' checkpoints, MP3D models trained on all 90 scans) | PR#2 Q10 (test splits not for training) | **GRAY - ASK (leans prohibited for our own training; disclose for third-party checkpoints)** | No training on test-building renderings. Avoid checkpoints self-trained on R2R test environments. Record data provenance for every pretrained component. | 9 |
| T17 | human_motion.json or simulator human state at inference, including indirect routes (rendering swept volumes into observations, reading human object poses from the sim) | PR#2 Input row, Q11 ('strictly prohibited') | **PROHIBITED** | Never. The file is mounted only into the env-server process. | preamble |
| T18 | Other public test-side annotations: collision_num_test.json (237 non-zero test episodes), HA-VLN-1.0 human_motion_text.json and connectivity for the 18 test scans; designing tapes around the collision_num slack | Website 'collision annotations remain withheld'; Q11 | **PROHIBITED at inference** | Quarantine. Aim for zero collisions regardless of the allowance. | - |
| T19 | Closed-source model APIs in the inference path | PR#2 Q12 | **CLEARLY ALLOWED (discouraged)** | Open-weight models in the inference path. Closed models only for dev tooling and synthetic TRAIN data (allowed by Q10). | - |
| T20 | External datasets and pretrained models (R2R/RxR/ScaleVLN/HM3D data, VLN-CE waypoint predictors, depth encoders, VLMs, person detectors) | PR#2 Q10; README Terms clause | **CLEARLY ALLOWED** | Use. Screenshot the CodaBench Terms when the site is reachable. | 10 |
| T21 | Human-in-the-loop on test: manual goal labelling, steering, cherry-picking or hand-editing of tapes, human annotation of test buildings | README Q2 (verification); RoboSense audit precedent | **PROHIBITED** | Never. | preamble |
| T22 | Modifying the LOCAL simulator for development (throttling, deterministic frame stepping, logging) | PR#2 Q4; README Q5 | **CLEARLY ALLOWED if it adds no information to the agent's observations** | Test-time inference runs the unmodified official image as the env server. Dev-only modifications are flagged in logs. | - |

### 3.1 Per-technique detail (rule text, verdict basis, stakes, disclosure, question)

#### T01 - Closed-loop egocentric agent: one forward RGB-D camera (official config) + GPS/compass, run locally in the official simulator; panoramas only via TURN actions inside the submitted sequence; LOOK_UP/DOWN; STOP or 500-action cap

- **Regime:** compliant (PRIMARY)
- **Rule text it touches:**
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - "Sensor Setup | One forward-facing RGB-D camera. Adding additional cameras is not permitted; panoramic views must be acquired by rotating in place (rotation actions count toward the action budget)." (PR #2, README L42)
  - "No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget." (PR #2, FAQ Q8)
  - "Yes. The agent is permitted to read its position and heading from the simulator agent state (GPS + compass) throughout the episode." (PR #2, FAQ Q9)
  - "If an episode reaches the maximum budget of 500 actions, `STOP` may be omitted ... `STOP` may appear at most once and only as the final action." (PR #2, FAQ Q13)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
  - "Official scoring replays submitted action sequences ... and any policy, planner, world model, or VLA method that outputs valid actions is welcome." (roboworld2026/track2 main 2d408b2, README.md L28-31)
- **Verdict:** **CLEARLY ALLOWED**. Basis: text (PR #2 Input row, Sensor Setup, Q8, Q9; main README Q1)
- **Default if unanswered:** This is the submission regime (CLEAN-1).
- **Notes:** This is the task as defined. VLN-CE components built for 12 cameras (ETPNav, the Discrete-Continuous waypoint predictor) must get their panorama by rotating: 12 views at 30 deg = 22 TURN actions, or 24 to return to the start heading, out of the 500-action budget.
- **Stakes:** Baseline regime. B8 estimates a compliant agent at about 51 Score, vs 12.9 for CMA.
- **Disclose in technical report:** Exact sensor config (RGB 224x224, depth 256x256, HFOV 90). A statement that every observation the agent used came from an action in that episode's submitted sequence. Mean actions per episode spent on look-around. No other sensors.
- **Question to organizers:** No question needed; PR #2 is explicit. Camera parameters: see T02 / issue item 2.

#### T02 - Changing the single camera's resolution, HFOV or mounting height (e.g. higher-res RGB for a VLM, wider FOV to cut rotations)

- **Regime:** compliant
- **Rule text it touches:**
  - "Sensor Setup | One forward-facing RGB-D camera. Adding additional cameras is not permitted; panoramic views must be acquired by rotating in place (rotation actions count toward the action budget)." (PR #2, README L42)
  - "No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget." (PR #2, FAQ Q8)
- **Verdict:** **GRAY - ASK**. Basis: text silent (only 'one forward-facing RGB-D camera'). The scorer replays actions only, so camera parameters affect the agent's information but not the scoring.
- **Default if unanswered:** Keep the official task config (RGB 224x224 HFOV 90, depth 256x256, default height).
- **Notes:** A wider HFOV is functionally a partial panorama without paying TURN actions, which is the very thing Q8 prices. Higher resolution at the same HFOV is the most defensible change.
- **Stakes:** Small to moderate (fewer look-around actions; better VLM grounding of small landmarks and people).
- **Disclose in technical report:** Camera parameters used, and whether they differ from the official config.
- **Question to organizers:** Issue item 2.
  - Exact wording (issue item 2):
    > **2. Camera parameters.** Must the single forward camera keep the official task-config parameters (RGB 224x224, depth 256x256, HFOV 90, default mounting height)? Or may we change its resolution, field of view or height? We assume the official parameters.

#### T03 - Unlimited compute per step: large open-weight VLM/LLM reasoning, model ensembles inside ONE run, K samples + majority vote at the same state (no extra environment steps), learned world-model imagination / look-ahead, dense 3-D mapping

- **Regime:** compliant
- **Rule text it touches:**
  - "Official scoring replays submitted action sequences ... and any policy, planner, world model, or VLA method that outputs valid actions is welcome." (roboworld2026/track2 main 2d408b2, README.md L28-31)
  - "There is no open-weights-only restriction, and commercial or closed-source model APIs are permitted. However, we encourage participants to develop their own methodological contributions and explore smaller, open-weight models (such as a 7B Qwen-VL model) ... We discourage relying primarily on powerful closed-source models, although this is a recommendation rather than an eligibility restriction." (PR #2, FAQ Q12)
  - Precedent, Track 1 of the same challenge: "The agent may generate and use its own predicted future observations, but it cannot access intermediate observations from the environment." (ext/track1/README.md L266)
  - "Human animations advance with wall-clock time according to the configured motion FPS ... All official submissions are replayed in the standardized organizer-controlled CodaBench environment, which determines competition scores." (PR #2, FAQ Q4)
- **Verdict:** **CLEARLY ALLOWED**. Basis: text: no compute or time limit exists in the README, PR #2 or the website. Track 1 explicitly allows the agent's 'own predicted future observations'.
- **Default if unanswered:** Use it freely, with open-weight models in the inference path (Q12 discourages relying on closed APIs).
- **Notes:** Caveat (engineering, not rules): humans animate on wall-clock time and freeze ~12 s after reset (A3/A2), so with slow per-step compute the local run sees frozen humans while the scorer replays at its own speed. Use swept-volume safety margins; never try to exploit replay timing. The world model must be learned (from train data or the agent's own observations). The ground-truth simulator used as a 'world model' is T05.
- **Stakes:** Main legal lever for SR (goal inference).
- **Disclose in technical report:** GPU-seconds per step and total GPU-hours for 3,408 episodes. Models (name, size, licence, version, decoding settings, seeds). Count and model versions of any API calls. Cached outputs.
- **Question to organizers:** No question needed. The issue (item 4) states our assumption that sampling several model outputs at the same state is fine.
  - Exact wording (issue item 4):
    > **4. Single-run evaluation.** Must an episode's submitted sequence come from one run, so that every observation the agent used was acquired by actions in that submitted sequence (the principle stated in Q8)? Or may we run the agent several times on the same test episode locally and submit one run, picked by an agent-internal criterion such as agreement among the runs? Our assumptions:
    > - one run only;
    > - sampling several model outputs at the same state within that run is fine;
    > - simulator look-ahead (saving/restoring state, stepping and reverting) is not.

#### T04 - Multiple full local rollouts of the same test episode (different seeds/variants), then submit one chosen by self-consistency (endpoint agreement, agent confidence)

- **Regime:** compliant-gray
- **Rule text it touches:**
  - "No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget." (PR #2, FAQ Q8)
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - [FROM MEMORY, unverified this session] R2R-era leaderboards list "single run", "pre-explore" and "beam search" entries as separate settings (EnvDrop, RCM); B4 quantified their historical gains.
  - Precedent, Track 1 of the same challenge: "The agent may generate and use its own predicted future observations, but it cannot access intermediate observations from the environment." (ext/track1/README.md L266)
- **Verdict:** **GRAY - ASK (leans prohibited)**. Basis: intent: the Q8 principle that every observation used must be bought by actions in the submitted sequence is broken by discarded rollouts. Beam search is a separately flagged setting in the VLN literature.
- **Default if unanswered:** OFF in submissions. Allowed only as a clearly labelled val ablation ('multi-rollout, not submitted').
- **Notes:** Split the variants. (a) Per-step multi-sample voting without extra environment steps = T03, allowed. (b) A deterministic re-run used only to verify reproducibility, with no selection on outcome = allowed. (c) K environment rollouts, selected by an agent-internal signal = gray. (d) Selection by collisions, pose-contact or local metrics = prohibited (T13).
- **Stakes:** Historical R2R beam search gave +11 to +19 SR (B4), about +9 to +15 Score here (there is no path-length term).
- **Disclose in technical report:** If permitted: K, the selection rule, total environment steps executed vs submitted, and the single-run result alongside.
- **Question to organizers:** Issue item 4.
  - Exact wording (issue item 4):
    > **4. Single-run evaluation.** Must an episode's submitted sequence come from one run, so that every observation the agent used was acquired by actions in that submitted sequence (the principle stated in Q8)? Or may we run the agent several times on the same test episode locally and submit one run, picked by an agent-internal criterion such as agreement among the runs? Our assumptions:
    > - one run only;
    > - sampling several model outputs at the same state within that run is fine;
    > - simulator look-ahead (saving/restoring state, stepping and reverting) is not.

#### T05 - Simulator look-ahead: save/restore or clone the sim state, step-and-revert, render from poses the agent has not reached, or use the ground-truth simulator as the 'world model'

- **Regime:** privileged
- **Rule text it touches:**
  - "No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget." (PR #2, FAQ Q8)
  - "Sensor Setup | One forward-facing RGB-D camera. Adding additional cameras is not permitted; panoramic views must be acquired by rotating in place (rotation actions count toward the action budget)." (PR #2, README L42)
  - Precedent, Track 1 of the same challenge: "The agent may generate and use its own predicted future observations, but it cannot access intermediate observations from the environment." (ext/track1/README.md L266)
  - Precedent, RoboSense 2025 Track 2 (same lead organizer): "navigation policies based solely on RGBD observations and odometry, without access to global maps or privileged information" (L32); disqualification for "accessing extra environmental information or sensors beyond the allowed observation keys" and "No bypassing simulation" (L458-460); "Awards will only be granted to submissions that have successfully passed the reproducibility audit" (L322) (ext/B8-robosense2025-track2/README.md)
- **Verdict:** **PROHIBITED**. Basis: text by equivalence: an extra (virtual) camera, banned by Q8/Sensor Setup. Precedents: Track 1 'cannot access intermediate observations', RoboSense 'No bypassing simulation'.
- **Default if unanswered:** Never. The env server exposes reset/step only.
- **Notes:** Indistinguishable from oracle rehearsal. The tape would also show avoidance of things never in view (action-tape forensics, B8).
- **Stakes:** Large, but illegitimate.
- **Disclose in technical report:** Negative statement plus env-server API description.
- **Question to organizers:** Stated as an assumption in issue item 4 (no answer needed if correct).
  - Exact wording (issue item 4):
    > **4. Single-run evaluation.** Must an episode's submitted sequence come from one run, so that every observation the agent used was acquired by actions in that submitted sequence (the principle stated in Q8)? Or may we run the agent several times on the same test episode locally and submit one run, picked by an agent-internal criterion such as agreement among the runs? Our assumptions:
    > - one run only;
    > - sampling several model outputs at the same state within that run is fine;
    > - simulator look-ahead (saving/restoring state, stepping and reverting) is not.

#### T06 - GPS-detected contact: infer a bump from a shortened MOVE_FORWARD displacement (pose allowed by Q9) and react within the same episode; reading Habitat's collided flag directly

- **Regime:** compliant
- **Rule text it touches:**
  - "Yes. The agent is permitted to read its position and heading from the simulator agent state (GPS + compass) throughout the episode." (PR #2, FAQ Q9)
  - habitat-sim 0.1.7 object_controls.py L68-89: collided = (|filter_end - start|^2 + 1e-5) < |end - start|^2 (squared metres), i.e. a MOVE_FORWARD is flagged iff the agent moved less than ~0.24998 m (A2 finding).
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
- **Verdict:** **CLEARLY ALLOWED (pose-delta, within one run); collided flag read directly = GRAY - ASK**. Basis: text: Q9 allows pose, and the pose delta is mathematically equivalent to the flag. The flag itself is not in the enumerated inputs.
- **Default if unanswered:** Use pose-delta bump inference only to react (back off, re-plan) in the same run. Do not read the flag. Never use contacts to rewind or retry an episode.
- **Notes:** Physically this is a bump sensor, and the collision is already counted when detected. Using contacts across rollouts or episodes turns the ground-truth human/obstacle geometry into a probe: T04, T07, T13.
- **Stakes:** Small: fewer repeated slides (the baseline averages ~15 flagged steps/episode).
- **Disclose in technical report:** Bump-inference mechanism. Confirm no rewind/retry.
- **Question to organizers:** Issue item 3.
  - Exact wording (issue item 3):
    > **3. Bump signal.** Q9 allows reading the agent's pose, and a blocked `MOVE_FORWARD` shows up as a shortened displacement. May the agent use that, or Habitat's `collided` flag, as a bump sensor to react within the same episode? We assume the pose-derived signal is fine under Q9 and will not read the flag unless you allow it. We will not use either to restart or retry an episode.

#### T07 - Memory across episodes of the same building (maps/landmarks/human sightings from our own earlier test episodes, IVLN-style)

- **Regime:** compliant-gray
- **Rule text it touches:**
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - "No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget." (PR #2, FAQ Q8)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
  - Precedent, GSA-VLN (ICLR 2025): "VLN tasks mainly evaluate agents based on one-time execution of individual instructions across multiple environments" (persistent-environment adaptation is defined as a separate task) (ext/GSA-VLN/README.md L4)
- **Verdict:** **GRAY - ASK**. Basis: text silent. 'Sequential egocentric RGB-D observations' is not scoped to the episode. Standard VLN-CE evaluation and the website's 'partial observability' / 'unseen buildings' imply per-episode independence.
- **Default if unanswered:** OFF (fresh agent state per episode, asserted in code).
- **Notes:** Most defensible variant if allowed: memory only from observations acquired in our own submitted sequences, a fixed processing order (file order), and same-trajectory siblings excluded (otherwise it becomes T09). IVLN fixes tour order on the benchmark side; here we would choose the order, so it is not an established setting.
- **Stakes:** Comparable to pre-exploration: about +8 to +14 Score. 75-300 episodes per test building.
- **Disclose in technical report:** If permitted: processing order, what is carried over, and an ablation with memory reset.
- **Question to organizers:** Issue item 5(a).
  - Exact wording (issue item 5):
    > **5. Episode independence.** Must each test episode start from a fresh agent state? Specifically, may an agent:
    > - (a) keep maps or memory from its own earlier test episodes in the same building;
    > - (b) explore a test building without an instruction before its episodes, with actions that are not part of any submitted sequence;
    > - (c) adapt its weights on unlabelled observations from test buildings?
    >
    > We assume no to all three.

#### T08 - Pre-exploration tours of test buildings (instruction-free, egocentric sensors, actions not in any submitted sequence) and test-time adaptation of weights on unlabelled test observations

- **Regime:** compliant-gray
- **Rule text it touches:**
  - "No. Adding cameras to the agent is not allowed. You may obtain a panoramic view by rotating the agent using the provided forward-facing RGB-D camera. All rotation actions used to acquire this view must be included in the submitted action sequence and count toward the 500-action budget." (PR #2, FAQ Q8)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - [FROM MEMORY, unverified this session] R2R-era leaderboards list "single run", "pre-explore" and "beam search" entries as separate settings (EnvDrop, RCM); B4 quantified their historical gains.
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
- **Verdict:** **GRAY - ASK (leans prohibited)**. Basis: intent: breaks the Q8 'pay for every observation' principle. TTA arguably 'uses test splits for training' (Q10). R2R treats pre-explore as a separate setting.
- **Default if unanswered:** OFF.
- **Notes:** Do not use the public start poses and scenes of the test file (A1) to pre-build anything for test buildings.
- **Stakes:** Historical +10 to +18 SR (RCM/EnvDrop/AuxRN, B4), about +8 to +14 Score.
- **Disclose in technical report:** If permitted: label the setting 'pre-explore'/'TTA' and report single-run too.
- **Question to organizers:** Issue item 5(b), 5(c).
  - Exact wording (issue item 5):
    > **5. Episode independence.** Must each test episode start from a fresh agent state? Specifically, may an agent:
    > - (a) keep maps or memory from its own earlier test episodes in the same building;
    > - (b) explore a test building without an instruction before its episodes, with actions that are not part of any submitted sequence;
    > - (c) adapt its weights on unlabelled observations from test buildings?
    >
    > We assume no to all three.

#### T09 - Sibling-instruction sharing: use the other instructions/outcomes of episodes with the same trajectory_id (IDs 3k+1..3k+3 share start and goal), e.g. goal voting across the 3 instructions

- **Regime:** gray
- **Rule text it touches:**
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - "Distinct trajectories are counted by `trajectory_id` within each released split; each episode requires its own action sequence." (organizer toolkit README, F1y1113/havln-challenge commit f49fe00, 2026-09-28, L93-95; dropped from the current README)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
- **Verdict:** **GRAY - ASK (treat as prohibited by default)**. Basis: intent: the Input row gives each episode its own 'navigation instruction'. The organizers know the triples share trajectories (old README) but never offer them as inputs. Standard VLN scores each instruction independently.
- **Default if unanswered:** OFF. trajectory_id hidden from the agent process and used only for bookkeeping.
- **Notes:** It exploits dataset construction (3 annotations of one path), not the navigation skill. Agreement among siblings is also a calibrated confidence signal (89.7% accurate when all 3 agree, B4), and using it is the same sharing.
- **Stakes:** Measured +6 to +7 SR on val_unseen (B4, Airbert/VLN-BERT 3-instruction vote), about +5 Score.
- **Disclose in technical report:** If permitted: per-instruction and fused results. If not: 'each episode was solved from its own instruction only'.
- **Question to organizers:** Issue item 6.
  - Exact wording (issue item 6):
    > **6. Episodes sharing a `trajectory_id`.** These share a start and a goal. May one episode's agent use the instructions or outcomes of the other episodes with the same `trajectory_id`? Or must it use only its own instruction? We assume only its own instruction.

#### T10 - Public original R2R instructions or other external annotations of the same test paths (R2R_test.json 3 instr/path, FGR2R, VLN-CE test.json.gz text), joined via trajectory_id = R2R path_id

- **Regime:** privileged
- **Rule text it touches:**
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
- **Verdict:** **PROHIBITED (confirm)**. Basis: intent: an extra annotation of the withheld test sample, obtained outside the episode inputs. Q10's 'datasets from other sources are permitted' gives nominal ambiguity, hence confirm.
- **Default if unanswered:** Never, in training or inference. Never placed in prompts.
- **Notes:** HA-R2R test instruction k is an LLM rewrite of R2R instruction (k-1) mod 3 plus human annotations (A1, B4). LLM pretraining corpora may contain R2R_test.json (it is on GitHub). That contamination is unavoidable; disclose it.
- **Stakes:** About +3 points of top-1 goal accuracy (85 -> 88%, B4), about +2 to +3 Score. Tiny upside against disqualification-level downside.
- **Disclose in technical report:** Negative statement covering R2R/R2R-CE/FGR2R/RxR/REVERIE test-split annotations. A contamination note for pretrained LLMs/VLMs.
- **Question to organizers:** Issue item 7.
  - Exact wording (issue item 7):
    > **7. External annotations of the same test paths.** HA-R2R test episodes come from R2R / R2R-CE test paths, whose original R2R instructions are publicly available. May they be used at inference or in training? We assume not.

#### T11 - Nav-graph / mesh use at inference: MP3D connectivity graphs, scene mesh, Habitat navmesh/PathFinder (navigability, geodesic distance), top-down maps, MP3D region/object annotations of test buildings

- **Regime:** privileged
- **Rule text it touches:**
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
  - "Official scoring replays submitted action sequences ... and any policy, planner, world model, or VLA method that outputs valid actions is welcome." (roboworld2026/track2 main 2d408b2, README.md L28-31)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - Precedent, RoboSense 2025 Track 2 (same lead organizer): "navigation policies based solely on RGBD observations and odometry, without access to global maps or privileged information" (L32); disqualification for "accessing extra environmental information or sensors beyond the allowed observation keys" and "No bypassing simulation" (L458-460); "Awards will only be granted to submissions that have successfully passed the reproducibility audit" (L322) (ext/B8-robosense2025-track2/README.md)
  - Precedent, Habitat Challenge: "A map of the environment is not provided and the agent must only use its sensory input to navigate." (L27); "We will block and disqualify teams that spam our servers." (L227) (ext/prec_facebookresearch_habitat-challenge/README.md)
  - Precedent, Track 3 of the same challenge: "No route-planner information in any part of the model ... Compliance is checked when the results of the top teams are reproduced." (ext/track3/README.md L42-45)
- **Verdict:** **PROHIBITED (intent + precedent; confirm)**. Basis: intent: excluded from PR #2's enumerated inputs; 'partial observability'. RoboSense 2025 banned 'global maps or privileged information'; Habitat 'map not provided'. Not banned by literal text, and the main README welcomes 'any planner', hence confirm.
- **Default if unanswered:** Never at inference. Allowed: maps the agent builds from its own RGB-D + pose; waypoint predictors trained on train-scan graphs (Q10); navmesh/PathFinder for training teachers, val analysis and labelled oracle ceilings.
- **Notes:** 'Waypoint planners and topological planners are welcome' refers to agent-built graphs (ETPNav-style), not the MP3D graph.
- **Stakes:** Largest single item: B8 scenario of about 76 (privileged geometry + VLM goal) vs about 51 Score (compliant).
- **Disclose in technical report:** Negative statement plus the agent-process file-access log. Oracle-ceiling numbers labelled 'not submitted'.
- **Question to organizers:** Issue item 1.
  - Exact wording (issue item 1):
    > **1. Scene geometry at inference.** During test inference, may the agent query scene information it has not observed itself? Examples: the scene mesh, the Habitat navmesh / PathFinder (navigability, geodesic distance), top-down maps, the MP3D navigation graph, or MP3D region/object annotations of the test buildings. Our assumption: no. Only maps the agent builds from its own RGB-D + pose observations, plus waypoint predictors trained on training scenes.

#### T12 - Local replay with ground truth for AGGREGATE metrics (val) and replay of final test tapes for FORMAT/DETERMINISM only

- **Regime:** dev
- **Rule text it touches:**
  - "Local replay can compute metrics for development, but only the official replay result published on CodaBench for the submitted archive determines leaderboard scores and awards." (README.md L274-277)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - "During validation and test inference, no: the agent must not directly read `human_motion.json` to obtain human positions or motion trajectories for planning. This file is provided to support simulator rendering; during inference, the agent should infer human positions and movements from its camera observations. During training, however, ground-truth human information from released training episodes may be used as privileged supervision, provided that it is not accessed during validation or test inference." (PR #2, FAQ Q11)
- **Verdict:** **CLEARLY ALLOWED (val aggregate, model selection); test-tape validity replay = allowed, confirm**. Basis: text: Q5 'Local replay can compute metrics for development'. Q10 bans val only for training. Test GT is not shipped, so test replay yields collisions/validity only.
- **Default if unanswered:** Val: aggregate metrics for model/hyper-parameter selection. Test: validate the schema, and check that the replay reproduces the trajectory the agent recorded. Never look at per-episode collision outcomes.
- **Notes:** Tuning margins (e.g. 0.35 vs 0.50 m inflation) on aggregate TEST collision stats is test-set model selection. Do it on val.
- **Stakes:** Scorer parity and bug catching.
- **Disclose in technical report:** Val used for selection only; test replay used for validity only.
- **Question to organizers:** Issue item 8 and 9(a).
  - Exact wording (issue item 8):
    > **8. Local replay in Phase 2.** FAQ Q5 allows local replay for development. May we replay our final test sequences locally, only to check format and that replay reproduces our recorded trajectory? We assume we may not use local replay outcomes on test episodes to pick, edit or regenerate sequences, or to choose between pipeline variants. That includes collision counts computed with the simulator's human placements.

#### T13 - Per-episode tape selection or editing using ground truth or local replay outcomes (val: pick the best tape per episode with GT and post it to Phase 1; test: pick/edit tapes by local collision counts against the simulator's human placements)

- **Regime:** privileged
- **Rule text it touches:**
  - "During validation and test inference, no: the agent must not directly read `human_motion.json` to obtain human positions or motion trajectories for planning. This file is provided to support simulator rendering; during inference, the agent should infer human positions and movements from its camera observations. During training, however, ground-truth human information from released training episodes may be used as privileged supervision, provided that it is not accessed during validation or test inference." (PR #2, FAQ Q11)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - "Local replay can compute metrics for development, but only the official replay result published on CodaBench for the submitted archive determines leaderboard scores and awards." (README.md L274-277)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
- **Verdict:** **PROHIBITED**. Basis: text/intent: an indirect read of ground-truth human trajectories via the simulator (Q11 'should infer human positions and movements from its camera observations'). On val it is a fabricated oracle result on a public board and 'validation inference' with GT (Q11).
- **Default if unanswered:** Never. Phase 1 receives only genuine pipeline outputs.
- **Notes:** Phase 1 does not count toward ranking, so oracle Phase-1 entries buy nothing and invite scrutiny.
- **Stakes:** Could push test collisions toward 0, illegitimately.
- **Disclose in technical report:** Negative statement plus a submission log.
- **Question to organizers:** Stated as an assumption in issue item 8.
  - Exact wording (issue item 8):
    > **8. Local replay in Phase 2.** FAQ Q5 allows local replay for development. May we replay our final test sequences locally, only to check format and that replay reproduces our recorded trajectory? We assume we may not use local replay outcomes on test episodes to pick, edit or regenerate sequences, or to choose between pipeline variants. That includes collision counts computed with the simulator's human placements.

#### T14 - Leaderboard probing: engineered or differential submissions (subset perturbations, masked or STOP-only test probes) to infer per-episode or per-building test information; multiple accounts

- **Regime:** meta
- **Rule text it touches:**
  - "Submission limits: five per day and 100 per phase; the best score is retained." (README.md L53)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - Precedent, Habitat Challenge: "A map of the environment is not provided and the agent must only use its sensory input to navigate." (L27); "We will block and disqualify teams that spam our servers." (L227) (ext/prec_facebookresearch_habitat-challenge/README.md)
  - Precedent, RoboDrive 2024 FAQ A15 (same lead organizer): "One team is affiliated with one CodaLab account only. Please REFRAIN from having multiple accounts for the same team." (ext/prec_robodrive-24_toolkit/README.md L353)
- **Verdict:** **PROHIBITED (genuine whole-pipeline A/B submissions are allowed)**. Basis: intent: extracting withheld test labels through the scoring oracle ('Test-split ground truth is not released'). Precedents: Habitat 'block and disqualify'; RoboDrive one account per team. CodaBench shows each team its own scores at 10 dp (C4/A12), so the channel exists and self-policing is required.
- **Default if unanswered:** Phase 2: genuine variants only, <=2/day, logged. Calibration probes only in Phase 1 (val GT is public anyway).
- **Notes:** C4 deliberately did not design a probing scheme, and this note agrees.
- **Stakes:** <1% of episodes recoverable (prior C3 estimate). Reputational risk is total.
- **Disclose in technical report:** Submission log (date, config hash, intent, score).
- **Question to organizers:** Issue item 10(a).
  - Exact wording (issue item 10):
    > **10. Leaderboard, Terms and verification.**
    > - (a) We will submit only complete outputs of real agent variants. Could you confirm that submissions built to extract per-episode or per-building test information are not allowed, and that each team must use a single CodaBench account?
    > - (b) CodaBench has been unreachable for us since about Oct 21. Could you post the Terms text in the README?
    > - (c) For award verification, what should top teams prepare? We plan to keep code, weights, per-episode observation logs, and cached outputs of any nondeterministic model calls, so each submitted sequence can be regenerated.
    > - (d) Is there a technical-report template and deadline?

#### T15 - Privileged teacher data for TRAINING: GT human trajectories/swept volumes, navmesh shortest paths, oracle actions, collision labels on the HA-R2R train split / 61 train scans (DAgger, distillation, RL rewards, detector fine-tuning)

- **Regime:** training
- **Rule text it touches:**
  - "During validation and test inference, no: the agent must not directly read `human_motion.json` to obtain human positions or motion trajectories for planning. This file is provided to support simulator rendering; during inference, the agent should infer human positions and movements from its camera observations. During training, however, ground-truth human information from released training episodes may be used as privileged supervision, provided that it is not accessed during validation or test inference." (PR #2, FAQ Q11)
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
- **Verdict:** **CLEARLY ALLOWED on train; PROHIBITED on val/test**. Basis: text: Q11 'ground-truth human information from released training episodes may be used as privileged supervision'. The baseline's own DAgger expert is a shortest-path oracle.
- **Default if unanswered:** Use heavily, restricted to the 61 train scans and train episodes.
- **Notes:** human_motion.json also covers the 11 val_unseen scans. Training on those humans would contaminate val_unseen and break Q10/Q11 ('training episodes'). Filter by scan.
- **Stakes:** Main legal lever for collisions and policy quality (learning-by-cheating).
- **Disclose in technical report:** List of privileged signals, scans/splits used, and a statement that val/test were excluded.
- **Question to organizers:** No question needed (Q11 explicit). Edge cases: issue item 9.
  - Exact wording (issue item 9):
    > **9. Training and selection data.**
    > - (a) Is selecting models and hyper-parameters on aggregate `val_seen`/`val_unseen` metrics acceptable, provided there is no gradient training on val?
    > - (b) Is training on renderings of the 18 test buildings excluded, even without labels?
    > - (c) May we use public checkpoints whose training data may include the MP3D test buildings, such as models trained on all 90 MP3D scans, if we disclose them?
    >
    > We assume (a) yes, (b) excluded, and (c) acceptable with disclosure. We will still avoid checkpoints that were self-trained on R2R test environments.

#### T16 - Training on renderings of the 18 test buildings (even unlabelled), or using public checkpoints whose data may include them (R2R 'pre-explore' checkpoints, MP3D models trained on all 90 scans)

- **Regime:** training-gray
- **Rule text it touches:**
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
- **Verdict:** **GRAY - ASK (leans prohibited for our own training; disclose for third-party checkpoints)**. Basis: intent: Q10 'test splits must not be used for training'; 'unseen buildings'.
- **Default if unanswered:** No training on test-building renderings. Avoid checkpoints self-trained on R2R test environments. Record data provenance for every pretrained component.
- **Notes:** Check each model card for the MP3D scan split.
- **Stakes:** Small to moderate (domain adaptation).
- **Disclose in technical report:** Provenance table: component, training data, MP3D test-scene exposure yes/no/unknown.
- **Question to organizers:** Issue item 9(b), 9(c).
  - Exact wording (issue item 9):
    > **9. Training and selection data.**
    > - (a) Is selecting models and hyper-parameters on aggregate `val_seen`/`val_unseen` metrics acceptable, provided there is no gradient training on val?
    > - (b) Is training on renderings of the 18 test buildings excluded, even without labels?
    > - (c) May we use public checkpoints whose training data may include the MP3D test buildings, such as models trained on all 90 MP3D scans, if we disclose them?
    >
    > We assume (a) yes, (b) excluded, and (c) acceptable with disclosure. We will still avoid checkpoints that were self-trained on R2R test environments.

#### T17 - human_motion.json or simulator human state at inference, including indirect routes (rendering swept volumes into observations, reading human object poses from the sim)

- **Regime:** privileged
- **Rule text it touches:**
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
  - "During validation and test inference, no: the agent must not directly read `human_motion.json` to obtain human positions or motion trajectories for planning. This file is provided to support simulator rendering; during inference, the agent should infer human positions and movements from its camera observations. During training, however, ground-truth human information from released training episodes may be used as privileged supervision, provided that it is not accessed during validation or test inference." (PR #2, FAQ Q11)
- **Verdict:** **PROHIBITED**. Basis: text: 'strictly prohibited during inference' (PR #2 Input row, Q11).
- **Default if unanswered:** Never. The file is mounted only into the env-server process.
- **Notes:** The simulator needs the file for rendering. That is exactly why the agent process must not be able to open it.
- **Stakes:** Large, but illegitimate.
- **Disclose in technical report:** Negative statement plus the file-access log.
- **Question to organizers:** Stated as an assumption in the issue preamble.
  - Exact wording (issue preamble):
    > Some techniques are still unclear to us. A short answer per item, in this thread or in the README FAQ, would let every team work under the same rules. **Unless you tell us otherwise, we will follow the conservative assumption stated in each item.** We assume these are clearly not allowed:
    > - reading human annotations or simulator human states at inference;
    > - adding cameras or rendering from poses the agent has not reached;
    > - people labelling, steering or correcting test episodes;
    > - training on val/test.

#### T18 - Other public test-side annotations: collision_num_test.json (237 non-zero test episodes), HA-VLN-1.0 human_motion_text.json and connectivity for the 18 test scans; designing tapes around the collision_num slack

- **Regime:** privileged
- **Rule text it touches:**
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
  - "During validation and test inference, no: the agent must not directly read `human_motion.json` to obtain human positions or motion trajectories for planning. This file is provided to support simulator rendering; during inference, the agent should infer human positions and movements from its camera observations. During training, however, ground-truth human information from released training episodes may be used as privileged supervision, provided that it is not accessed during validation or test inference." (PR #2, FAQ Q11)
  - "Input | Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference." (PR #2, README L41)
- **Verdict:** **PROHIBITED at inference**. Basis: intent: ground-truth annotations of test episodes/buildings. The website says 'reference trajectories and collision annotations remain withheld' while the upstream repo publishes them.
- **Default if unanswered:** Quarantine. Aim for zero collisions regardless of the allowance.
- **Notes:** Report the discrepancy privately (draft email below). The Phase-2 scorer may use regenerated files.
- **Stakes:** Small (slack on 7% of episodes).
- **Disclose in technical report:** Negative statement.
- **Question to organizers:** Private email, not the public issue.

#### T19 - Closed-source model APIs in the inference path

- **Regime:** compliant
- **Rule text it touches:**
  - "There is no open-weights-only restriction, and commercial or closed-source model APIs are permitted. However, we encourage participants to develop their own methodological contributions and explore smaller, open-weight models (such as a 7B Qwen-VL model) ... We discourage relying primarily on powerful closed-source models, although this is a recommendation rather than an eligibility restriction." (PR #2, FAQ Q12)
- **Verdict:** **CLEARLY ALLOWED (discouraged)**. Basis: text: Q12.
- **Default if unanswered:** Open-weight models in the inference path. Closed models only for dev tooling and synthetic TRAIN data (allowed by Q10).
- **Notes:** Closed APIs also break bit-for-bit reproducibility at verification. Cache every call if used.
- **Stakes:** Innovation-award optics (B8: organizers favour 7B open models).
- **Disclose in technical report:** Every API used, version, call count, cached outputs.
- **Question to organizers:** No question needed.

#### T20 - External datasets and pretrained models (R2R/RxR/ScaleVLN/HM3D data, VLN-CE waypoint predictors, depth encoders, VLMs, person detectors)

- **Regime:** compliant
- **Rule text it touches:**
  - "Publicly available pretrained models are allowed, including navigation policies trained on other VLN datasets, depth encoders and waypoint predictors from open-source VLN-CE projects ... Datasets from other sources are permitted. The intended training restriction is that HA-R2R validation splits (`val_seen`, `val_unseen`) and test splits must not be used for training." (PR #2, FAQ Q10)
  - "Participation is governed by the Terms displayed on the official CodaBench competition." (README.md L320-321)
- **Verdict:** **CLEARLY ALLOWED**. Basis: text: Q10. The stale RoboDrive-style T&C ('do not use any public or private datasets other than those specified') was removed from the website on 2026-10-06 (2e62d94). The CodaBench Terms are unseen.
- **Default if unanswered:** Use. Screenshot the CodaBench Terms when the site is reachable.
- **Notes:** Exclusions: see T10 and T16.
- **Stakes:** High (most SR gains come from pretrained VLN/VLM components).
- **Disclose in technical report:** Provenance and licence table.
- **Question to organizers:** Issue item 10(b) (Terms text).
  - Exact wording (issue item 10):
    > **10. Leaderboard, Terms and verification.**
    > - (a) We will submit only complete outputs of real agent variants. Could you confirm that submissions built to extract per-episode or per-building test information are not allowed, and that each team must use a single CodaBench account?
    > - (b) CodaBench has been unreachable for us since about Oct 21. Could you post the Terms text in the README?
    > - (c) For award verification, what should top teams prepare? We plan to keep code, weights, per-episode observation logs, and cached outputs of any nondeterministic model calls, so each submitted sequence can be regenerated.
    > - (d) Is there a technical-report template and deadline?

#### T21 - Human-in-the-loop on test: manual goal labelling, steering, cherry-picking or hand-editing of tapes, human annotation of test buildings

- **Regime:** meta
- **Rule text it touches:**
  - "Teams qualifying for awards (Top 5, Best Innovative Solution, or RoboPAD presentation) will be expected to contribute to a technical report and may be asked to provide code or models for verification." (README.md L262)
  - Precedent, RoboSense 2025 Track 2 (same lead organizer): "navigation policies based solely on RGBD observations and odometry, without access to global maps or privileged information" (L32); disqualification for "accessing extra environmental information or sensors beyond the allowed observation keys" and "No bypassing simulation" (L458-460); "Awards will only be granted to submissions that have successfully passed the reproducibility audit" (L322) (ext/B8-robosense2025-track2/README.md)
  - Website track2.html (84d0bc2): "Given egocentric RGB-D observations and a natural-language instruction ..."; "Partial observability ... require real-time re-planning"; "Policy-based agents, imitation or reinforcement learning, waypoint planners, and topological planners are welcome."; "Test-split ground truth is not released."
- **Verdict:** **PROHIBITED**. Basis: intent: the task is for 'agents'. Verification requires regenerating results from code (Q2; RoboSense: awards only after a reproducibility audit). Humans studying VAL failures to improve the method is normal R&D.
- **Default if unanswered:** Never.
- **Notes:** Write it into the team charter. Coding agents may not inspect test episodes either.
- **Stakes:** Not applicable.
- **Disclose in technical report:** Negative statement.
- **Question to organizers:** Stated as an assumption in the issue preamble.
  - Exact wording (issue preamble):
    > Some techniques are still unclear to us. A short answer per item, in this thread or in the README FAQ, would let every team work under the same rules. **Unless you tell us otherwise, we will follow the conservative assumption stated in each item.** We assume these are clearly not allowed:
    > - reading human annotations or simulator human states at inference;
    > - adding cameras or rendering from poses the agent has not reached;
    > - people labelling, steering or correcting test episodes;
    > - training on val/test.

#### T22 - Modifying the LOCAL simulator for development (throttling, deterministic frame stepping, logging)

- **Regime:** dev
- **Rule text it touches:**
  - "Human animations advance with wall-clock time according to the configured motion FPS ... All official submissions are replayed in the standardized organizer-controlled CodaBench environment, which determines competition scores." (PR #2, FAQ Q4)
  - "Local replay can compute metrics for development, but only the official replay result published on CodaBench for the submitted archive determines leaderboard scores and awards." (README.md L274-277)
- **Verdict:** **CLEARLY ALLOWED if it adds no information to the agent's observations**. Basis: text: only the organizer replay scores (Q4/Q5). Adding GT human information to observations = T17 (prohibited).
- **Default if unanswered:** Test-time inference runs the unmodified official image as the env server. Dev-only modifications are flagged in logs.
- **Notes:** Human timing in our local run need not match the scorer. That is a robustness question for C7/A3.
- **Stakes:** Development speed.
- **Disclose in technical report:** Which simulator build produced the submitted tapes.
- **Question to organizers:** No question needed.

## 4. Technical-report disclosure checklist ('Setting and Compliance' section)

1. Information-use table: for each module, which inputs it reads at TRAIN time and at TEST time.
2. Sensors: one forward RGB-D camera at the official config (or the permitted variant), GPS+compass, instruction. Mean, p50 and p95 actions per episode, and actions spent on look-around.
3. Negative statements: no scene mesh/navmesh/PathFinder/nav-graph/MP3D annotations of test buildings; no human_motion.json or simulator human state; no extra or virtual cameras or simulator look-ahead; no cross-episode memory, pre-exploration or TTA; no sibling instructions; no external annotations of test paths; no per-episode selection by GT or local replay; no human-in-the-loop; no leaderboard probing; one account.
4. Provenance table for every pretrained component: training data, licence, MP3D test-scene exposure (yes/no/unknown), and an LLM-corpus contamination note.
5. Privileged training signals and the scans/splits used (61 train scans). Val used for model selection only.
6. Compute: per step, per episode, total. Every API call (model and version).
7. Submission log for Phase 1 and Phase 2 (date, config hash, intent, score).
8. Reproducibility: container digest, code commit, weight hashes, seeds, cached model outputs, the observation-log archive, and a script that regenerates the submitted ZIP from the logs.
9. Organizer rulings (link to the issue). For any permitted gray technique, single-run numbers alongside.
10. Oracle and privileged analyses (e.g. a known-geometry ceiling) clearly labelled 'analysis only - not submitted'.

## 5. The single GitHub issue to post (roboworld2026/track2)

**Title:** Rules clarification request: Track 2 inference inputs and evaluation protocol (follow-up to PR #2)

**Body** (copy verbatim):

````markdown
Hi organizers, thank you for running Track 2 and for the toolkit.

We read open PR #2 (`bohan/clarification-Oct14`). It covers inference inputs, the single forward RGB-D camera, GPS+compass, no `human_motion.json` at inference, external data allowed, and no training on val/test. It is not yet on `main` or on the website. Could you merge it, or confirm here that it applies to Phase 2? We are already following it.

Some techniques are still unclear to us. A short answer per item, in this thread or in the README FAQ, would let every team work under the same rules. **Unless you tell us otherwise, we will follow the conservative assumption stated in each item.** We assume these are clearly not allowed:
- reading human annotations or simulator human states at inference;
- adding cameras or rendering from poses the agent has not reached;
- people labelling, steering or correcting test episodes;
- training on val/test.

**1. Scene geometry at inference.** During test inference, may the agent query scene information it has not observed itself? Examples: the scene mesh, the Habitat navmesh / PathFinder (navigability, geodesic distance), top-down maps, the MP3D navigation graph, or MP3D region/object annotations of the test buildings. Our assumption: no. Only maps the agent builds from its own RGB-D + pose observations, plus waypoint predictors trained on training scenes.

**2. Camera parameters.** Must the single forward camera keep the official task-config parameters (RGB 224x224, depth 256x256, HFOV 90, default mounting height)? Or may we change its resolution, field of view or height? We assume the official parameters.

**3. Bump signal.** Q9 allows reading the agent's pose, and a blocked `MOVE_FORWARD` shows up as a shortened displacement. May the agent use that, or Habitat's `collided` flag, as a bump sensor to react within the same episode? We assume the pose-derived signal is fine under Q9 and will not read the flag unless you allow it. We will not use either to restart or retry an episode.

**4. Single-run evaluation.** Must an episode's submitted sequence come from one run, so that every observation the agent used was acquired by actions in that submitted sequence (the principle stated in Q8)? Or may we run the agent several times on the same test episode locally and submit one run, picked by an agent-internal criterion such as agreement among the runs? Our assumptions:
- one run only;
- sampling several model outputs at the same state within that run is fine;
- simulator look-ahead (saving/restoring state, stepping and reverting) is not.

**5. Episode independence.** Must each test episode start from a fresh agent state? Specifically, may an agent:
- (a) keep maps or memory from its own earlier test episodes in the same building;
- (b) explore a test building without an instruction before its episodes, with actions that are not part of any submitted sequence;
- (c) adapt its weights on unlabelled observations from test buildings?

We assume no to all three.

**6. Episodes sharing a `trajectory_id`.** These share a start and a goal. May one episode's agent use the instructions or outcomes of the other episodes with the same `trajectory_id`? Or must it use only its own instruction? We assume only its own instruction.

**7. External annotations of the same test paths.** HA-R2R test episodes come from R2R / R2R-CE test paths, whose original R2R instructions are publicly available. May they be used at inference or in training? We assume not.

**8. Local replay in Phase 2.** FAQ Q5 allows local replay for development. May we replay our final test sequences locally, only to check format and that replay reproduces our recorded trajectory? We assume we may not use local replay outcomes on test episodes to pick, edit or regenerate sequences, or to choose between pipeline variants. That includes collision counts computed with the simulator's human placements.

**9. Training and selection data.**
- (a) Is selecting models and hyper-parameters on aggregate `val_seen`/`val_unseen` metrics acceptable, provided there is no gradient training on val?
- (b) Is training on renderings of the 18 test buildings excluded, even without labels?
- (c) May we use public checkpoints whose training data may include the MP3D test buildings, such as models trained on all 90 MP3D scans, if we disclose them?

We assume (a) yes, (b) excluded, and (c) acceptable with disclosure. We will still avoid checkpoints that were self-trained on R2R test environments.

**10. Leaderboard, Terms and verification.**
- (a) We will submit only complete outputs of real agent variants. Could you confirm that submissions built to extract per-episode or per-building test information are not allowed, and that each team must use a single CodaBench account?
- (b) CodaBench has been unreachable for us since about Oct 21. Could you post the Terms text in the README?
- (c) For award verification, what should top teams prepare? We plan to keep code, weights, per-episode observation logs, and cached outputs of any nondeterministic model calls, so each submitted sequence can be regenerated.
- (d) Is there a technical-report template and deadline?

We will describe our full information-use setup in the technical report. Thank you!
````

How each issue item maps to table rows:
- 1 = T11; 2 = T02; 3 = T06; 4 = T03, T04 and T05;
- 5 = T07 and T08; 6 = T09; 7 = T10; 8 = T12 and T13;
- 9 = T15 and T16; 10 = T14, T20 and verification;
- the preamble covers T17 and T21.

T18 is not in the public issue on purpose. It goes in the private email below, so that we do not advertise test-side files.

### 5.1 Companion private email (responsible disclosure; do not post publicly)

```text
To: roboworld2026@gmail.com
Subject: Track 2: rules questions (GitHub issue link) + a note on public test-side files

Hi organizers,
We posted our rules questions publicly as a GitHub issue on roboworld2026/track2 (<link>), so all teams see the same answers. Separately, here is a note we did not want to post publicly.

The website says reference trajectories and collision annotations for the test split remain withheld. However, the public UWMILab/HA-VLN repository contains:
- Data/HA-R2R-tools/collision_num_test.json: per-episode baseline collision counts for all 3,408 test episodes;
- HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json: HA-VLN 1.0 human placements/activities for all 18 test buildings;
- MP3D connectivity graphs and the original R2R test instructions.

We do not use any of these, and we flag them in case you want to regenerate Phase-2 scoring files or state a rule.
Best regards,
<team name / registered contact>
```

## 6. CLEAN-1: the compliant configuration (primary and fallback)

- **Env server** (unmodified official image):
  - It alone mounts the scenes, episode file and human file.
  - API: `reset(episode_id) -> {rgb 224x224, depth 256x256, gps, compass, instruction}` and `step(action)`.
  - There is no state get/set, no pathfinder access, and no trajectory_id or goal fields.
- **Agent container:**
  - It has no data mount, only model weights.
  - Every file open is logged.
  - State is fresh per episode (asserted).
  - It uses deterministic decoding and caches model outputs.
- **Policy:**
  - Fuse depth + pose into an occupancy/semantic map.
  - Track people with a detector, keeping a swept envelope.
  - Parse the instruction and ground landmarks with an open-weight VLM.
  - Look around selectively: 6-12 turns per sweep, 24 only when lost.
  - Plan A* on the inflated self-built map.
  - Infer bumps from the pose delta and use them for in-run reaction only.
  - Stop with Score-aware stopping.
- **Logs:**
  - Per-step observations and actions, about 100 GB compressed for Phase 2.
  - Organizers can regenerate every tape by replaying the agent on the logs.
- **Optional modules** (config flags, default OFF): `rollouts_k`, `scene_memory`, `preexplore`, `sibling_fusion`, `camera_cfg`. Each is turned on only after a written organizer permission and is then disclosed.

## 7. Facts (verified unless marked)

1. **[high]** The binding published rules (roboworld2026/track2 main 2d408b2, website 84d0bc2) contain no restriction on sensors, simulator state, scene geometry, cross-episode memory, multiple rollouts, sibling instructions or leaderboard use. Method text: 'any policy, planner, world model, or VLA method that outputs valid actions is welcome' (L30-31), 'Any method is eligible if it exports legal official action sequences' (Q1). Enforcement: award teams 'may be asked to provide code or models for verification' (L262). 'Participation is governed by the Terms displayed on the official CodaBench competition' (L320-321).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2/README.md (347 lines; identical to JostarXiong/track2 origin/main d4baf9e); grep for rule/prohibit/privileg/terms

2. **[high]** Organizer PR #2 on roboworld2026/track2 is OPEN and unmerged as of 2026-10-24. Title 'docs: clarify observation inputs, sensor setup, and rules FAQ', author JosephJostar0 (organizer Bohan Xiong), created 2026-10-14. Its description says it 'clarifies recent participant questions regarding allowed inputs, sensor configuration, and rules'. It has no reviews or comments. git refs: refs/pull/2/head = 8289590 (= JostarXiong/track2 bohan/clarification-Oct14), refs/pull/2/merge = d6155e0. main is still 2d408b2 (the merge of PR #1 = d4baf9e, Oct 9).  
   _Evidence:_ git ls-remote https://github.com/roboworld2026/track2 (run 2026-10-24); WebFetch https://github.com/roboworld2026/track2/pull/2 (2026-10-24); /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/jostar-track2 git log (0f944d3 2026-10-14 11:31 -0700, 8289590 11:47 -0700)

3. **[high]** PR #2 diff (git diff origin/main origin/bohan/clarification-Oct14, README.md only, +30/-4). Input row: 'Episode ID, initial pose, navigation instruction, ongoing agent pose (position and heading from simulator state, GPS+compass), and sequential egocentric RGB-D observations. Direct access to ground-truth human trajectories (`human_motion.json`) is strictly prohibited during inference.' Other additions: a Sensor Setup row (one forward camera; panoramas by rotation that counts toward the budget), Q4 rewrite (wall-clock animation; organizer replay determines scores), Q8 (no extra cameras; rotations must be in the submitted sequence), Q9 (pose allowed), Q10 (pretrained models and external data allowed; HA-R2R val/test not for training), Q11 (no human_motion.json at val/test inference; GT humans from training episodes allowed as privileged supervision), Q12 (closed APIs permitted but discouraged; 7B Qwen-VL encouraged), Q13 (500-action sequences may omit STOP).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/jostar-track2: git diff origin/main origin/bohan/clarification-Oct14 (quoted in full in the markdown twin)

4. **[high]** PR #2 does NOT address: scene mesh/navmesh/nav-graph at inference, camera parameter changes, the collided flag, multiple rollouts, cross-episode memory, pre-exploration, test-time adaptation, sibling instructions, external annotations of the same test paths, local replay on test, leaderboard probing, or human-in-the-loop work.  
   _Evidence:_ Full read of the PR #2 diff

5. **[high]** No public rules discussion exists: roboworld2026/track2 has 0 issues, and UWMILab/HA-VLN's 21 issues contain none about challenge rules. PR #2's own description cites unnamed 'recent participant questions' (likely Discord/WeChat).  
   _Evidence:_ WebFetch https://github.com/roboworld2026/track2/issues?q=is%3Aissue ('0 results'); WebFetch https://github.com/UWMILab/HA-VLN/issues (2026-10-24)

6. **[high]** The website frames Track 2 as egocentric and partially observable ('Given egocentric RGB-D observations ...', 'Partial observability ... real-time re-planning'). It also welcomes 'waypoint planners, and topological planners' and states 'Test-split ground truth is not released.'  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/roboworld2026.github.io/track2.html (tag-stripped text; commit 84d0bc2, 2026-10-23)

7. **[high]** The website's old Terms & Conditions ('do not use any public or private datasets other than those specified for model training', non-commercial use) was a stale RoboDrive template. Lingdong Kong removed it in commit 2e62d94 on 2026-10-06. The CodaBench Terms text is unknown (site unreachable since ~Oct 21).  
   _Evidence:_ git -C /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/roboworld2026.github.io show 2e62d94 -- index.html (removed lines)

8. **[high]** The same organizers wrote explicit input rules elsewhere. Track 1 'cannot access intermediate observations from the environment' but 'may generate and use its own predicted future observations'. Track 3: 'No route-planner information in any part of the model ... Compliance is checked when the results of the top teams are reproduced'. RoboSense 2025 Track 2 (same lead organizer, social navigation): 'solely on RGBD observations and odometry, without access to global maps or privileged information'; disqualification for extra observation keys; awards only after a reproducibility audit.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track1/README.md L266; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track3/README.md L42-45; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/B8-robosense2025-track2/README.md L32, L322, L345-350, L458-460

9. **[high]** Habitat Challenge precedent: 'A map of the environment is not provided and the agent must only use its sensory input'; 'We will block and disqualify teams that spam our servers.' RoboDrive 2024 precedent: one team = one account.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/prec_facebookresearch_habitat-challenge/README.md L27, L227; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/prec_robodrive-24_toolkit/README.md L353

10. **[high]** Pose-derived bump detection is mathematically equivalent to Habitat's collision flag. collided = (|filter_end-start|^2 + 1e-5) < |end-start|^2, so a MOVE_FORWARD is flagged iff displacement < ~0.24998 m. Turns, looks and STOP can never be flagged. GPS-detected contact therefore reveals exactly what the flag reveals, from an input Q9 explicitly permits.  
   _Evidence:_ A2 finding (habitat-sim 0.1.7 habitat_sim/agent/controls/object_controls.py L19, L68-89)

11. **[high]** Test structure enables the gray techniques. 3,408 test episodes = 1,136 trajectories (IDs 3k+1..3k+3 share trajectory_id, start and goal). trajectory_id = R2R path_id. The 3 original R2R instructions of every test path are public (R2R_test.json, 1,391 paths). The public VLN-CE test.json.gz mirror already reveals the scene, start pose and original instruction of every test episode.  
   _Evidence:_ A1 finding; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/tasks/R2R/data/R2R_test.json; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/test/test.json.gz

12. **[high]** The organizers know triples share trajectories. An earlier toolkit README (2026-09-28) said 'Distinct trajectories are counted by `trajectory_id` ...; each episode requires its own action sequence.' The current README no longer has the sentence, and neither version offers other episodes' instructions as inputs.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/a1-havln-challenge-full: git show f49fe00:README.md L93-95; ec8f682 L99

13. **[high]** Test-side annotations are public despite the website's 'withheld' wording: collision_num_test.json (3,408 entries, 237 non-zero), HA-VLN-1.0 human_motion_text.json covering all 18 test scans (70 humans), and MP3D connectivity graphs for all 18 test scans. human_motion.json (HA-VLN 2.0) covers 72 scans, including the 11 val_unseen scans, and 0 test scans.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/Data/HA-R2R-tools/collision_num_test.json; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/connectivity/; A1 finding

14. **[high]** Official camera config: RGB 224x224 HFOV 90, depth 256x256. The organizer exporter sets TASK.SENSORS = ['INSTRUCTION_SENSOR'] plus simulator RGB-D, and mounts human_motion.json into the SIMULATOR for rendering. The scorer replays actions only, so camera parameters affect only what the agent sees.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/agent/VLN-CE/habitat_extensions/config/vlnce_task.yaml L12-19; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2/scripts/export_cma_submission.py L108-117

15. **[high]** Privileged training is organizer practice: the baseline DAgger trainer consumes a shortest-path expert, and PR #2 Q11 explicitly allows GT human information from training episodes as privileged supervision.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/agent/VLN-CE/vlnce_baselines/dagger_trainer.py L43, L254, L416-437; PR #2 Q11

16. **[high]** CodaBench shows each team the scores of all its own submissions at 10 decimal places (unless columns are hidden), so per-episode information leakage via engineered submissions is technically possible. That makes self-policing and a submission log necessary.  
   _Evidence:_ C4 and A12 findings (codabench src/apps/leaderboards/models.py, api/serializers/submissions.py)

17. **[medium]** Historical value of the gray settings (B4): R2R beam search +11 to +19 SR; pre-exploration +10 to +18 SR; 3-instruction fusion measured +6 to +7 SR on val_unseen (Airbert 68.7 -> 75.7, VLN-BERT 59.3 -> 65.1); original R2R instructions about +3 points of goal accuracy.  
   _Evidence:_ B4 finding (released Airbert/VLN-BERT predictions re-analysed; literature numbers partly from memory)

18. **[high]** Verification limits of this note. WebSearch budget exhausted, so no web searches were run. GitHub MCP access to roboworld2026/track2 was denied (session allows only itsbharatj/open-data-eval). PR/issue status came from git ls-remote plus WebFetch of github.com pages. CodaBench Terms unreadable. R2R leaderboard setting categories, IVLN details and the ImageNet-2015/Kaggle precedents are from memory.  
   _Evidence:_ Tool results in this session

## 8. Numbers

| What | Value | Source |
|---|---|---|
| PR #2 size and commits | 2 commits (0f944d3, 8289590; 2026-10-14), README.md +30/-4; head 8289590, merge ref d6155e0; unmerged (main 2d408b2) | git ls-remote; jostar-track2 git log/diff |
| Public issues on roboworld2026/track2 | 0 (2026-10-24) | WebFetch github.com/roboworld2026/track2/issues |
| Techniques classified | 22: 8 clearly allowed (some with gray sub-cases), 6 gray-ask, 8 prohibited (T10, T11 marked confirm) | this note, compliance table |
| Test episodes / trajectories / buildings | 3,408 / 1,136 (IDs 3k+1..3k+3) / 18 (75-300 episodes per building; gYvK 21) | A1 |
| Collision-flag threshold | flag iff \|dp\|^2 + 1e-5 < 0.0625 m^2, i.e. displacement < 0.24998 m | habitat-sim object_controls.py L68-89 (A2) |
| Panorama cost under Q8 | 24 TURN actions per 360 deg; 12-view (30 deg) emulation = 22 turns (+2 to restore heading) | 15 deg turn (README); computed |
| Official camera | RGB 224x224 HFOV 90; depth 256x256 | vlnce_task.yaml L12-19 |
| Score per SR point (Social ~1) | ~0.8 Score per +1 SR point (100 x 0.8 x 1.0), plus NE co-benefit | README Score formula |
| Stakes of gray items (inference) | sibling fusion +6-7 SR ~ +5 Score; multi-rollout +11-19 SR ~ +9-15; pre-explore/cross-episode memory +10-18 SR ~ +8-14; original R2R instr ~ +2-3; privileged geometry ~ +25 (B8 scenario 76 vs 51) | B4, B8; computed |
| Public test-side annotations | collision_num_test: 237/3,408 non-zero (79 trajectories); 70 HA-VLN-1.0 humans in 18 test scans; 18/18 connectivity graphs; R2R_test 1,391 paths x 3 instructions | A1; HA-VLN repo files |
| Scans covered by public human_motion.json | 72 = 61 train + 11 val_unseen; 0 test (restrict privileged training to the 61 train scans) | A1; CONTEXT fact 5 |
| Submission caps | 5/day, 100/phase; Phase 2 Oct 30 - Nov 30 (31 days x 5 = 155 > 100) | README L53 |
| Per-episode observation-log archive for verification | ~280 KB/step raw (RGB 224x224x3 + depth 256x256 uint16); at 200 steps/episode ~190 GB raw, ~100 GB lossless-compressed for 3,408 episodes | computed |
| Rules decision checkpoint | 2026-11-07 (8 days after Phase 2 opens, 23 days before close); unanswered gray items stay OFF | recommendation |

## 9. Implications (inferences)

1. OPERATIVE RULE. Treat PR #2 as binding now. It is the organizers' written intent and matches their RoboSense-2025 stance. Award verification ('may be asked to provide code or models') makes intent, not literal README text, the operative standard. Nothing in it costs us much Score: there is no path-length term, and goal inference is the bottleneck in every regime.
2. ONE UNIFYING PRINCIPLE explains every verdict and should be stated in the report (Information Locality). An episode's actions may depend only on (i) that episode's own inputs (id, start pose, its own instruction), (ii) observations acquired by actions inside that episode's submitted sequence (forward RGB-D + GPS/compass), and (iii) knowledge learned beforehand from train/external data. Anything that injects information outside (i)-(iii) is gray or prohibited: scene geometry, human files, other episodes' instructions, discarded rollouts, earlier episodes, the scoring oracle, humans.
3. The gray items are worth +2 to +15 Score each, so a written public answer is high-value. Permissive answers would favour compute-rich teams like us (multi-rollout, pre-exploration, cross-episode memory). Restrictive answers bind everyone and protect ranking integrity. Either outcome beats guessing.
4. Enforcement is verification-only (no code is submitted), so defensibility must be PROVABLE. An architecture in which the agent process physically cannot reach forbidden information, plus logs that let organizers regenerate every tape from logged observations, turns 'trust us' into an audit.
5. Action-tape forensics (B8): tapes reveal privileged planning (no look-around, near-geodesic paths through unobserved space, avoidance of unseen humans). A clean agent with logs is robust to the scrutiny a far-above-field score will attract.
6. Two gray items have tempting, measurable gains and a dataset-artifact flavour: sibling fusion (+5 Score) and original R2R instructions (+2-3). The second is near-certainly prohibited, and asking about it publicly at least closes the loophole for everyone.
7. Privileged-training hygiene. human_motion.json also covers the 11 val_unseen scans, so swept-volume or human-occupancy training sets must be filtered to the 61 train scans. Otherwise val_unseen is contaminated and Q10/Q11 are breached.
8. Q8 prices information in actions. Multi-camera VLN-CE components (12-view waypoint predictors) cost 22-24 actions per panorama, so the policy must look selectively. A wider-HFOV camera would sidestep that price, which is why it must be asked, not assumed.
9. Phase 1 has no ranking value. Its legitimate use is scorer parity and calibration with genuine outputs. Oracle Phase-1 entries buy nothing and invite scrutiny.

## 10. Recommendations

1. POST THE ISSUE TODAY (2026-10-24/25), verbatim from the draft below, from the team's registered GitHub account on roboworld2026/track2. Email the same text plus the private note to roboworld2026@gmail.com. Ask a teammate to drop the issue link in the Track 2 Discord/WeChat (blocked from this sandbox). Do not post the private-email content publicly.
2. ADOPT A TEAM CHARTER NOW: PR #2 plus the Information Locality principle. Every GRAY item defaults to OFF in submissions until a written organizer answer exists. PROHIBITED items are never built into the inference path.
3. BUILD THE CLEAN-1 SANDBOX (owners: C1 infra / C7 execution). (1) The env-server process runs the unmodified official image. It alone mounts scenes, episodes and the human file, and it exposes only reset(episode_id) -> {rgb, depth, gps, compass, instruction} and step(action): no state get/set, no pathfinder, no trajectory_id. (2) The agent process runs in a separate container without the data mount and logs every file open (strace/fanotify). (3) Agent state is reset per episode, asserted in code. (4) Every step's observations and actions are logged (~100 GB compressed for Phase 2). Decoding is deterministic and model outputs are cached, so replaying the agent on the logged observations regenerates each tape bit-for-bit.
4. DEVELOP GRAY TECHNIQUES ONLY AS VAL ABLATIONS behind config flags (rollouts_k, scene_memory, preexplore, sibling_fusion, camera_cfg). If the organizers permit one, enable it, re-validate on val_unseen, and report single-run numbers next to it.
5. DECISION CHECKPOINT 2026-11-07. If no answer by then, freeze the clean regime for Phase 2. Re-send the email once, and do not escalate publicly.
6. LEADERBOARD PROTOCOL. Phase 1: genuine CLEAN-1 outputs only, using the first 2-3 submissions for scorer parity. Phase 2: complete genuine pipeline variants only, <=2/day, one account. Keep a log (date, config hash, intent, score) and reserve >=30 submissions for the final week. Make the final upload >=48 h before Nov 30 AoE.
7. TRAINING HYGIENE. Privileged teachers (GT humans, navmesh shortest paths, oracle actions) on the 61 train scans only. Val is used for aggregate model selection only. No renderings of test buildings in training. Record a provenance table (component, data, MP3D-test exposure) for every pretrained checkpoint, and avoid checkpoints self-trained on R2R test environments.
8. QUARANTINE in the agent container: Multi-Human-Annotations/*, any Phase-2 human file, recompute_navmesh/*, HASimulator/HA-DE/** (connectivity, human_motion_text.json, R2R_*.json), Data/HA-R2R-tools/collision_num_*.json, the VLN-CE test.json.gz mirror, FGR2R/RxR/REVERIE test files, and all val/test GT fields (goals, reference_path, info).
9. TECHNICAL REPORT 'Setting and Compliance' section (use the disclosure checklist below). Include an information-use table (train vs test time per module), negative statements, provenance, compute, submission log, organizer rulings with a link to the issue, oracle ceilings labelled 'not submitted', and a reproducibility recipe.
10. MODEL CHOICE. Open-weight models in the inference path (Qwen-VL class; this aligns with Q12 and the innovation-award taste per B8). Closed models only for dev tooling and synthetic train data, all disclosed.
11. IF COMPETITORS POST IMPLAUSIBLE SCORES: no public accusations. Privately ask the organizers to apply verification uniformly to all award candidates.

## 11. Open questions

- Will PR #2 be merged (or confirmed in the issue) before Phase 2 opens on Oct 30, and in the same wording?
- Rulings on the 10 issue items, especially 1 (scene geometry), 4 (single run), 5 (episode independence) and 6 (siblings), which carry the largest Score stakes.
- What do the CodaBench Terms say (non-commercial use? data restrictions conflicting with Q10? mandatory code?)?
- Will verification cover all Top-5 teams or only some? How will nondeterministic models and wall-clock human animation be handled when regenerating tapes?
- Does the Phase-2 bundle ship test-scan human placements for rendering (implied by Q11), and does the scorer use regenerated collision_num/human files?
- Technical-report template and deadline (RoboSense used a CVPR-style LaTeX template, with the final rank 'subject to' report submission).
- Will the organizers react to the private note on public test-side files (e.g. regenerate the test collision baselines)?

## 12. Sources

- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2/README.md (roboworld2026/track2 main 2d408b2: L28-31, L41, L53, L256, L262, L274-277, L320-321)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/jostar-track2 (git diff origin/main origin/bohan/clarification-Oct14; commits 0f944d3, 8289590)
- git ls-remote https://github.com/roboworld2026/track2 (refs/pull/2/head 8289590, refs/pull/2/merge d6155e0, main 2d408b2), 2026-10-24
- https://github.com/roboworld2026/track2/pull/2 (WebFetch 2026-10-24: open, author JosephJostar0, no reviews/comments)
- https://github.com/roboworld2026/track2/issues (WebFetch 2026-10-24: 0 issues); https://github.com/UWMILab/HA-VLN/issues (21 issues, none on rules)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/roboworld2026.github.io/track2.html, index.html (84d0bc2); git show 2e62d94 (stale T&C removed 2026-10-06)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/a1-havln-challenge-full (git show f49fe00:README.md L93-95)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track1/README.md L266; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track3/README.md L42-45
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/B8-robosense2025-track2/README.md L32, L322, L345-350, L458-460
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/prec_facebookresearch_habitat-challenge/README.md L27, L227; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/prec_robodrive-24_toolkit/README.md L353
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/GSA-VLN/README.md L4
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/agent/VLN-CE/habitat_extensions/config/vlnce_task.yaml L12-19; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2/scripts/export_cma_submission.py L108-117
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/agent/VLN-CE/vlnce_baselines/dagger_trainer.py; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/Data/HA-R2R-tools/collision_num_test.json; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/{connectivity,human-viewpoint_annotation,tasks/R2R/data}
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/A1-episode-format-and-test-split.md (test triples, R2R_test join, public mirror)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/A2-collision-semantics-habitat017.md (collided flag formula)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/B4-pre-exploration-beam-search-path-ranking.md (gains of beam search / pre-explore / 3-instruction fusion)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/B8-world-models-innovation-angle-and-organizer-taste.md (RoboSense precedent, organizer taste, tape forensics)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/C4-leaderboard-feedback-group-testing-math.md and A12-codabench-platform-mechanics.md (10-dp own scores)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/c3_scripts/C3-v1-backup.md (superseded v1 of this note)
- [FROM MEMORY, unverified] R2R leaderboard single-run / pre-explore / beam-search categories; IVLN (Krantz et al., CVPR 2023); ImageNet-2015 multi-account disqualification; Kaggle hand-labelling rules
