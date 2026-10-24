# A7-competitor-intelligence: Competitor intelligence: the visible field, likely strong entrants, and a threat matrix for Phase 2 (test)

_Date: 2026-10-24. Regimes: **compliant** = Oct-14 clarified rules (egocentric RGB-D + GPS/compass, no human_motion.json at inference); **privileged** = offline full-map planning (needs organizer permission)._

## Summary

Only ONE public RoboWorld-2026 Track-2 competitor repo exists as of 2026-10-24: bingchengzhang/HA-VLN (ZJU-affiliated, created 2026-10-21, 7 commits). It is a well-engineered but non-performing hierarchical agent (YOLOv8-seg humans + 2.5-D per-floor elevation map + 0.1 m Dijkstra candidates + Qwen2.5-VL-7B QLoRA 'multiple-choice' decider, DeepSeek text option). Its only reported closed-loop result is SR = 0 on 20 val_unseen episodes (r0 LoRA trained on expert labels from ~500 train episodes), it runs on 2-3 shared RTX 4090s with a slow HF backend, and it already obeys the organizers' Oct-14 rule clarification (no privileged info at inference). Estimated current Score ~5; ceiling by Nov 30 ~15-25. Its value to us is the list of simulator quirks it verified (TILT_ANGLE=30, wall-sliding counts as a collision, humans re-inserted every 0.1 s and frozen after ~12 s, 'waiting' via LOOK_UP/DOWN does nothing in fast replay, the official image contents) and its failure modes (stuck in wall-inflation zones, background-depth STOP rejection, 11/20 instruction decompositions truncated). No other team repo, blog, Zhihu/CSDN/bilibili post, or visible leaderboard entry was found (CodaBench down since ~Oct 21). The ecosystem signals instead point at three classes of stronger potential entrants: (1) the HCSG group (HKUST-GZ, Haoang Li) - the only third-party method published on HA-VLN-CE (val_unseen SR .24 / CR .36 / TCR 5.02 -> challenge Score ~22.6), with a ready pipeline; (2) VLA/VLN-CE SOTA users - public third-party ports of StreamVLN (KAIST, Habitat 0.2.4) and InternNav/DualVLN (HTTP bridge) to HA-VLN already exist; with HA-R2R fine-tuning plus a collision shield such a team could reach Score ~30-45; (3) frontier-API zero-shot agents - closed-source APIs are explicitly permitted, and a public harness cites a paper claiming GPT-6-Astra zero-shot R2R-CE SR 81.3% (monocular RGB, no depth/map); with a depth collision shield this class plausibly reaches Score ~45-56 and is the single most dangerous compliant threat. Privileged offline full-map planning would score 57-90+ but is outside the clarified rules unless organizers permit it. Score arithmetic: +0.01 SR = +0.74 Score; collision-free execution, not navigation skill, is where most published agents lose (literature SOTA SR .24). Our bar: a compliant entry at SR >= .55 with CR <= .1 (Score >= 52) beats the best rival with ~85% probability under our threat model (P(best rival >= 50) ~ 0.16; inference, low confidence).

## 1. The one visible competitor: bingchengzhang/HA-VLN ("ExcuseMeBro" hierarchical agent)

**Identity / timeline (FACT, high).** Repo created 2026-10-21, 7 commits all that day, author email on `zju.edu.cn`; artefacts reference runs on 2026-10-18 (`sensor_report.json`) and 2026-10-19 (`pilot-repair-v6-20261019`, `paired-repair-v6-20261019-052025`). Code is developed on WSL, executed on a senior labmate's shared server via an OpenAI-Codex operator (`docs/CODEX_TASK.md`). No newer commits as of 2026-10-24 (`git ls-remote`).

**Resources (FACT, high).** RTX 4090 24 GB cards, only GPUs 5/6/7 (or 4/6) usable, no Docker, server cannot reach HF/GitHub (`docs/TRAINING.md:3-9,45,201,322`). Inference via LLaMA-Factory HF backend in 4-bit: "seconds per decision"; a 20-episode paired run takes hours (`docs/CODEX_TASK.md:63`). Scaling to 3,408 test episodes is feasible only if they fix serving.

**Architecture (FACT, high)** (`project/README.md:7-53`, `havln_agent/agent.py:131-249`):
- Fast loop (every step, ~25-40 ms without seg/LLM): depth back-projection (pitch-aware) -> per-floor 2.5-D elevation map (5 cm cells; obstacle if vertical span > 0.20 m step; gap rule step + tan(38 deg) x unobserved gap) -> YOLOv8m-seg person masks -> human tracks (median centroid + 0.15 m half-depth, velocity, uncertainty growth 0.3 m/s capped 1.5 m, prediction only during first 12 s) -> wall/human costmaps inflated separately (wall 0.10+0.12 m, human 0.10+0.25 m, relaxed 0.08 m after waiting) in a 16 m window -> 0.05 m grid, single scipy Dijkstra.
- Candidates: 24 rays (15 deg), groups split at 45 deg, endpoints 1-3 m, annotated with distance, min clearance to humans, crosses_human_zone, blocked_by_human, leads_to_unknown, visited, tried_before, goes up/down/level (`planning/candidates.py:87-242`).
- Decision gating: SEGMENT_DONE (3 m), JUNCTION (new opening), PATH_INVALID, FALLBACK (40 steps), OVERRUN (1.6x a train-fit length prior a + b*n_words), START/FLOOR/OBSERVE; LLM skipped only when exactly one viable unvisited way (`planning/decision.py:272-405`).
- Slow loop: offline instruction compilation into subgoals (landmark, ref_human, done_when) + online multiple-choice JSON {choose, observe, subgoal_done, stop, goal_box} with strict boolean parsing, 1 retry, heading-keeping fallback (`slow/prompts.py`, `slow/slow_loop.py`).
- Executor: lookahead 0.5 m, 7.5 deg turn tolerance, corner-heading search, escape from inflation zones, WAIT emulated as LOOK_DOWN/LOOK_UP pairs, look-down before unknown cells within 1 m (`executor.py`, `agent.py:426-446`).

**LLM choices (FACT, high).** Qwen2.5-VL-7B-Instruct (AWQ for vLLM 0.8.5 serving; bf16 base for QLoRA), DeepSeek `deepseek-chat` text-only alternative, temperature 0 + request-hash disk cache. Training: QLoRA r16/alpha32, 4-bit nf4, vision frozen, lr 1e-4, 2 epochs, eff. batch 16, 336 px, <= 4 images; labels from a privileged oracle (reference-path +3 m target, stop within 2 m with projected 0.6 x 1.6 m goal box, observe if target out of view), 15 % perturbation, DAgger planned (`configs/train_decision_lora.yaml`, `havln_agent/oracle.py`). r0 collected on **500** train episodes (`docs/CODEX_TASK.md:71`), adapter published at huggingface.co/bingchengzhang/HA-VLN-nav-r0-lora.

**Reported numbers (FACT, high).** r0 closed loop: **20 val_unseen episodes, SR = 0** (`docs/CLOSED_LOOP.md:50`). No NE/CR/TCR published. Estimated Score at SR 0 ~ **4.7** (inference, assuming NE 8, CR .4, TCR 2).

**Self-imposed rule (FACT, high).** Privileged data (reference path, goal, navmesh, true human positions) only for labels/diagnostics; `make_submission.py:42-43` refuses oracle runs; val/test never used for training; pose read from simulator. This matches the organizers' Oct-14 clarification (GPS+compass allowed, human_motion.json forbidden at inference, panoramas by rotation only, APIs allowed but discouraged).

### 1.1 Simulator quirks they discovered (with our cross-check)

| Quirk | Their source | Our cross-check | Conf. |
|---|---|---|---|
| LOOK_UP/DOWN tilt = **30 deg** in challenge config (measured 2026-10-18) | `config.py:28` | HA-VLN RxR configs also use 30 (`rxr_vlnce_english_task.yaml:6`) | high |
| Collision = `previous_step_collided`; **wall sliding counts**; keep 0.22 m centre-to-wall; detect BUMP/SLIDE | `config.py:54-75`, `agent.py:448-465` | UWMILab issue #17 confirms code counts walls; organizer docs (`havln_docs/.../evaluation_metrics.md:27-33`) still say human-only within 1 m - docs are wrong | high |
| Humans removed/re-added every 0.1 s (new object ids), 120 frames then static (~12 s wall-clock) | `seg_gt_smoke.py:7`, `config.py:89` | `HASimulator/environments.py:96-213` | high |
| Local LLM latency lets humans move; official replay has no waits -> local vs official collision mismatch | `docs/TRAINING.md:529-530` | consistent with wall-clock thread | high |
| 'Waiting' for people via LOOK pairs is pointless after 12 s; relax margin after 24 steps | `config.py:66-70`, `executor.py:10` | in fast replay humans barely move -> waiting is useless (inference) | medium |
| Map frame (x,-z), yaw CCW from +x, forward = -z, quaternion [x,y,z,w]; success/NE 3-D Euclidean | `geometry.py`, `habitat_env.py:254-258` | matches HA-VLN measures override | high |
| Navmesh recomputed with set_defaults + radius 0.1 / height 1.5 -> max climb 0.2, slope 45 deg (VERIFY) | `check_env.py:110-116` | `environments.py:135-139` | medium |
| Camera height 1.25, MAX_DEPTH 10, normalized depth: still VERIFY | `config.py:23-25` | not verified by anyone yet | low |
| Image layout: /app/config/challenge_submission.yaml, /app/habitat-lab, /opt/havln-challenge/scoring (six_action_task.yaml, havln-validate), phase1 public_reference_manifest.json; pull without Docker via registry API | `docs/TRAINING.md:89-99`, `extract_image_files.py` | toolkit `export_cma_submission.py:189,214-224`; NOTE it only *hashes* habitat_simulator.py into a fingerprint, so 'patched' is their inference | high |
| `_human_posisions` (typo) attribute exposes all human positions | `habitat_env.py:250-252` | `environments.py:213`; forbidden at inference per Oct-14 FAQ Q11 | high |
| Train episode 7901 has an outdoor instruction vs indoor goal (quarantined) | `training_watch.py:20` | not checked | medium |

### 1.2 Their failure analysis (what broke)

- Stuck 67 steps in a wall-inflation zone (no candidates) -> `escape_mask` (`grid_search.py:61-75`, `CODEX_TASK.md:36`).
- STOP rejected because goal-box depth hit the background wall (5.4 m); STOP now accepted immediately (`agent.py:338-346`, `tests/test_stop_regressions.py:16-27`) - the README's depth-confirmation stop rule (`README.md:199-209`) is stale.
- 11/20 instruction decompositions truncated at 256 tokens -> 1024 (`config.py:136`).
- Stair-edge cells misread as walls; narrow alcoves gave no >= 1 m candidate (`tests/test_navigation_regressions.py:59-117`).
- Budget sinks: 24-turn spin at start and on every floor change; up to 6 observe turns of 6-12 steps (`config.py:104,123`).
- Never measured YOLO recall on SMPL-rendered humans (built a semantic-ID hook to measure it) (`seg_gt_smoke.py`).
- Their own diagnostic plan: oracle-vs-model paired runs with candidate_coverage, choice_agreement, false_stop_rate, wrong_floor_rate, stop_kinds (`README.md:96-117`, `rollout.py:146-170`).

**Assessment (inference, medium).** Threat level LOW: modular and careful, but SR 0, weak serving, ~500-episode SFT, single student operator. Plausible Nov-30 ceiling Score 15-25 if the geometric stack works and DAgger helps. Worth monitoring; worth copying several engineering details (Section 6).

## 2. Other participants and the ecosystem

- **No other participant repo, blog, Zhihu/CSDN/bilibili post or leaderboard entry was found** (FACT, medium: absence of evidence). GitHub repo/code searches for havln, HA-VLN, roboworld, RoboPAD, HA-R2R, havln-validate, export_cma_submission, public_reference_manifest, HAVLNCEDaggerEnv, havlnce_tool, Multi-Human-Annotations, HAPS2_0 return only organizer repos, the bingchengzhang repo and the research ports below (GitHub code search does not yet index the Oct-21 competitor repo, so newer repos can be invisible). Web search budget was exhausted mid-task (shared 200-call limit).
- **UWMILab/HA-VLN**: 520 stars / 37 forks; newest fork `phanhieeus/HA-VLN-blackwellARC` (2026-10-23, no own commits; name suggests Blackwell-GPU port). Issue #30 (2026-10-09, `kuylv`) reproduces CMA embeddings - likely another entrant. Issue #14: GLB frames load unsorted -> jerky human motion in some tools.
- **roboworld2026/track2**: 7 stars, 1 fork, 1 open issue (as indexed). Website has per-track WeChat groups (QR refreshed 2026-10-23) - the Chinese academic community is the main audience.
- **HCSG** (HKUST-GZ, Haoang Li; arXiv 2605.13321; github.com/HaoxuanXU1024/HCSG): only third-party HA-VLN-CE method; code "will be released soon". Ready pipeline -> most likely *trained-model* rival.
- **StreamVLN HA-VLN port** (`LeonGoretzkatju/Human-Dyanamic-StreamVLN`, KAIST email, 2026-04-05): Habitat 0.2.4 human-aware eval with official TCR/CR/strict-SR; loops human frames (not freeze) and agent radius 0.05 -> numbers would not transfer to 0.1.7 replay.
- **InternNav bridge** (`Bubblevan/HA-VLN-HTTP`, 2026-03): HTTP middleware to run InternNav/DualVLN on HA-VLN (640x480, HFOV 79); only toy agent stats committed (random SR 0, handcrafted SR .1 on 10 eps).
- **Frontier-API zero-shot signal**: `scott89/gpt6astra-r2rce` (2026-10-03) reproduces a paper it cites as arXiv:2609.29861 claiming GPT-6-Astra zero-shot R2R-CE SR 81.3 % (ultra) / 75.7 % (medium) from one 512x512 RGB with no depth/map/pose; the harness itself gets 27-35 % with glm-5.3-flash, ~55 API calls/episode, and observed 6/10 outcome flips across identical reruns. APIs are permitted in Track 2 (FAQ Q12). (medium confidence: third-party quote.)
- Organizer-side repos (`JosephJostar0/HAVLN_baseline` is empty; `havln_docs` API docs; organizer CMA numbers differ from README by ~1 Score point).

## 3. Literature on HA-VLN-CE converted to challenge Score

| Method (val_unseen) | SR | NE | CR | TCR | Score | Source |
|---|---|---|---|---|---|---|
| CMA baseline (toolkit, val_unseen) | 0.129 | 6.387 | 0.684 | 17.536 | **13.0** | track2 README |
| ETPNav retrained (HA-VLN 2.0) | 0.17 | 5.43 | 0.58 | 6.94 | **16.7** | HCSG table / HA-VLN 2.0 |
| BEVBert (HA-VLN 2.0) | 0.21 | 5.51 | 0.55 | 4.71 | **19.4** | HCSG table; NE from HA-VLN 2.0 step-size table |
| HCSG (NE assumed 5.3) | 0.24 | 5.3 | 0.36 | 5.02 | **22.6** | HCSG table |

Caveat: paper-protocol numbers; NE for HCSG assumed. Conversion uncertainty ~ +/-3 Score. The published SOTA is therefore Score ~22-23; ours must be far above.

## 4. Threat matrix (Phase 2 test; inference unless noted)

| Approach | SR | NE | CR | TCR | Expected Score | P(someone fields it by Nov 30) | Regime | Likely who |
|---|---|---|---|---|---|---|---|---|
| T0 CMA baseline / exported toolkit tape | 0.129 | 6.387 | 0.684 | 17.536 | **13.0** | ~100% (many teams) | compliant | anyone |
| T1 Hierarchical VLM+mapping, early (bingchengzhang-like) | 0.05 | 7.0 | 0.35 | 1.5 | **8.8** | 60-80% that >=1 such team submits | compliant | ZJU team + similar student teams |
| T2 ETPNav/BEVBert/ETP-R1 ported, no collision shield | 0.19 | 5.5 | 0.56 | 5.5 | **18.0** | 40-60% | compliant (rotate-in-place panoramas) | VLN-CE groups, organizer-paper reproducers |
| T3 HCSG-class (published SOTA on HA-VLN-CE) | 0.24 | 5.3 | 0.36 | 5.02 | **22.6** | 15-30% (if HKUST-GZ group enters) | compliant | HCSG authors |
| T4 Graph agent (ETP-R1) + collision shield + HA-R2R fine-tune | 0.33 | 4.8 | 0.2 | 0.5 | **31.7** | 15-25% | compliant | strong VLN-CE lab |
| T5 VLA (SimpleVLN/StreamVLN/DualVLN) fine-tuned on HA-R2R + depth shield | 0.42 | 4.3 | 0.15 | 0.4 | **39.5** | 10-20% | compliant | VLA groups (Shanghai AI Lab ecosystem, PKU, UCSD, KAIST port) |
| T6 Frontier-API zero-shot agent (GPT-6-Astra-class) + depth shield | 0.5 | 3.5 | 0.15 | 0.3 | **46.7** | 15-30% | compliant (APIs permitted, discouraged) | well-funded academic/industry team |
| T6b Frontier-API agent without collision shield | 0.3 | 3.8 | 0.55 | 3.0 | **26.9** | 10-20% | compliant | teams unaware walls count |
| T7 Test-time multi-rollout / self-verification on local sim (gray) | 0.55 | 3.2 | 0.1 | 0.2 | **51.8** | 5-10% | gray (pre-exploration-like) | replay-aware teams |
| T8 Privileged offline planner (navmesh + graph prior + LLM goal grounding) | 0.7 | 2.5 | 0.02 | 0.02 | **66.5** | 3-8% (and disqualification risk) | non-compliant unless permitted | exploit-aware teams |

**Best-rival Score distribution (Monte Carlo over the matrix, low confidence):** median 30.1, p90 55.1; P(best rival >= X): >=20: 0.71, >=30: 0.5, >=40: 0.32, >=45: 0.24, >=50: 0.16, >=55: 0.1, >=60: 0.06.

Score sensitivity near SR .40: +0.01 SR = +0.74 Score; -0.1 m NE = +0.10; -0.01 CR = +0.09; -0.1 TCR = +0.14. SR (which already requires zero net collisions) dominates.

## 5. Implications

- The visible field is weak: the only public competitor is at SR 0 and compute-constrained; the public literature SOTA on HA-VLN-CE converts to Score ~22.6 (HCSG). A compliant entry at Score >= 35 would likely be top-3 unless a frontier-API or fine-tuned-VLA team with a collision shield appears.
- The main hidden threat in the compliant regime is a frontier VLM (GPT-6-Astra-class) zero-shot closed-loop agent: APIs are explicitly permitted (Oct-14 FAQ Q12) and a public reproduction harness exists. Its weakness is collisions (no depth, sliding counts), so a team that adds a depth/costmap shield could reach Score ~45-56.
- Most competitors will lose points to wall collisions: published HA-VLN-CE agents sit at CR .36-.77; the competitor itself lists 'does the scorer count only humans?' as an open VERIFY item and organizer docs still describe TCR as human-only. Teams that believe the docs will under-invest in wall clearance.
- Waiting for humans to move (WAIT emulated by LOOK_UP/LOOK_DOWN) is ineffective in fast official replay; routes must go around people. This affects every closed-loop competitor whose local runs are slow (LLM latency), creating local/official mismatch they may not diagnose.
- Literature numbers (HA-VLN 2.0 tables) come from the organizers' paper protocol (and possibly different checkpoints); organizer docs and README already disagree on CMA by ~1 Score point. Treat literature->challenge Score conversions as +/-3 points.
- Privileged offline planning (T8) is the only approach that beats a strong compliant entry, but under the Oct-14 clarification it needs explicit permission; the probability that a rival fields it AND keeps it is low (3-8%), and its use would be visible in the mandatory technical report.
- Phase 1 leaderboard intelligence is unavailable (CodaBench down since ~Oct 21; val goals are public so Phase-1 ranks are uninformative anyway). Competitor strength will only be revealed in Phase 2 (Oct 30-Nov 30) if the leaderboard is public.

## 6. Recommendations

- Set the internal bar at a compliant Score >= 50 on val_unseen (e.g. SR >= .55, NE <= 3.3, CR <= .10, TCR <= .2); that dominates every compliant threat class in the matrix except an optimistic frontier-API+shield entry.
- Do not rely on waiting for people: plan geometric detours with human-inflated costmaps, and verify every final tape by local replay at multiple replay speeds (human frame at freeze differs by speed).
- Borrow the competitor's verified engineering, not its policy: TILT 30 deg, wall margin >= 0.12 m + slide detection, per-floor elevation maps with 0.2 m step/38 deg gap-slope rules, look-down before unknown terrain ahead, escape-from-inflation-zone logic, strict JSON parsing of VLM outputs, request-hash caching for determinism, scene-held-out validation splits, oracle-vs-model paired diagnostics (candidate_coverage, choice_agreement, false_stop_rate, wrong_floor_rate).
- Benchmark a frontier-API zero-shot agent ourselves early (the user has unlimited API budget): it is both our strongest cheap baseline and the best proxy for the most dangerous rival; add our collision shield on top and measure the gap to our trained agent.
- Avoid the competitor's known budget sinks: full 24-step spins at start and every floor change, 6x observe turns; prefer partial scans and reuse of view memory.
- Monitor competitor signals weekly until Nov 30: bingchengzhang/HA-VLN commits (git ls-remote), HaoxuanXU1024/HCSG code release, new forks of UWMILab/HA-VLN and roboworld2026/track2, CodaBench Phase-2 leaderboard, the track WeChat group, and arXiv for 'HA-VLN' / 'RoboWorld 2026' technical reports.
- If we ever pursue privileged planning, obtain written organizer permission first and keep a compliant submission as the ranked entry; rivals' reports will be scrutinized by the same judges.

## 7. Open questions

- Is the competitor's (or anyone's) Phase-1 entry on CodaBench, and at what Score? (leaderboard unreachable; CodaBench down since ~Oct 21).
- Will HCSG's authors (HKUST-GZ) enter, and will their code be released before Nov 30?
- Is the GPT-6-Astra 81.3% zero-shot R2R-CE claim real and reproducible on 3,408 episodes, and what is its collision profile under ALLOW_SLIDING? (third-party quote only; web search budget exhausted before verification).
- How many teams registered for Track 2 (Google Form; WeChat group size)?
- Are the bingchengzhang VERIFY items (camera height 1.25 m, MAX_DEPTH 10, normalized depth, navmesh climb/slope) correct in /app/config/challenge_submission.yaml? (other agents with image access should check).
- Does the official replay run fast enough that humans are still animating (frames < 120) for early steps, or are they effectively frozen at the last frame? This changes how much rivals' local collision estimates diverge from official ones.

## 8. Facts with evidence and confidence

1. **[high]** Exactly one public Track-2 competitor repository is findable: bingchengzhang/HA-VLN, created 2026-10-21 14:33Z, last update 2026-10-21 15:27Z, 7 commits all on Oct 21 (author email domain zju.edu.cn), 0 stars/forks, no branches/PRs beyond main.  
   _Evidence:_ git log in /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang; git ls-remote shows only refs/heads/main=f0a9e91; GitHub repo search 'HA-VLN' (sorted by updated) and 'roboworld' via GitHub MCP search_repositories
2. **[high]** Their only reported closed-loop number: r0 LoRA model, 20 val_unseen episodes, SR = 0. They explicitly state offline-accuracy gains must not be presented as navigation success and that control/terrain fixes since then need re-evaluation.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/docs/CLOSED_LOOP.md:50
3. **[high]** Architecture: 'LLM only answers multiple-choice'. Fast loop every step: depth back-projection -> per-floor 2.5-D elevation map (ground/top per 5 cm cell, step 0.20 m, gap slope 38 deg) + YOLOv8m-seg person masks -> human tracks with uncertainty discs -> separately inflated wall/human costmap in a 16 m window -> 0.05 m plan grid, one Dijkstra -> 24-direction candidates with risk summary (distance, clearance to humans, crosses_human_zone, blocked_by_human, leads_to_unknown, visited, goes up/down/level). Slow loop only at decision points (SEGMENT_DONE<=3 m, JUNCTION, PATH_INVALID, FALLBACK 40 steps, OVERRUN 1.6x expected length) asks the VLM to choose a candidate / observe left-right-behind / mark subgoal done / stop with goal_box.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/README.md:7-53; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/agent.py:131-249; planning/candidates.py:87-170; planning/decision.py:272-405; config.py:31-123
4. **[high]** LLM choices: Qwen2.5-VL-7B-Instruct (AWQ 4-bit for serving via vLLM 0.8.5, or bf16 + LLaMA-Factory HF backend 4-bit on the shared server); optional DeepSeek 'deepseek-chat' text-only via API; temperature 0, disk cache keyed on full request for reproducibility; 336x336 images, <=4 images/decision (current view with numbered candidate lines + remembered frames for out-of-view candidates).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:126-141; configs/deepseek_text.json; scripts/serve_vlm.sh:65-85; slow/llm_client.py:251-335; slow/view_memory.py:250-266
5. **[high]** Training: SFT + QLoRA (4-bit nf4 double-quant, LoRA r16 alpha32 all linear layers, vision tower frozen, lr 1e-4 cosine, 2 epochs, eff. batch 16, cutoff 4096) on expert labels produced by a privileged oracle (reference path +3 m look-ahead, stop within 2 m with projected goal_box) with 15% deliberate wrong-candidate perturbation; DAgger rounds planned. r0 collection actually configured for 500 train episodes (README suggests 2000). Published adapter: huggingface.co/bingchengzhang/HA-VLN-nav-r0-lora (~154 MiB).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/configs/train_decision_lora.yaml; docs/TRAINING.md:25-27,444-482; docs/CODEX_TASK.md:71; scripts/stage.py:10; havln_agent/oracle.py:204-327; docs/MODELS.md:7-16
6. **[high]** Compute/infra of this competitor is modest: shared lab server with RTX 4090 (24 GB) cards, only GPUs 5,6,7 (or 4,6) allowed, no Docker, server cannot reach HuggingFace/GitHub, LLaMA-Factory HF backend 'seconds per decision', a 20-episode paired run takes 'hours'. They drive the work with OpenAI Codex as an executor (docs/CODEX_TASK.md).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/docs/TRAINING.md:3-9,45,201,322-332; docs/CODEX_TASK.md:1-14,63; scripts/stage.py:42
7. **[high]** Self-imposed rule: privileged info (reference path, goal, navmesh, ground-truth human positions) is used only for labels/diagnostics; make_submission.py refuses oracle-decision runs; val/test never used for training; path-length prior fit on train only. Pose is read from the simulator ('pending organizer confirmation').  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/agent.py:6; adapters/habitat_env.py:73-83,225-258; scripts/make_submission.py:42-43; scripts/compile_instructions.py:7-8; havln_agent/config.py:155
8. **[high]** Their self-imposed regime matches the organizers' (unmerged, Oct-14) clarification: inputs = episode id, initial pose, instruction, ongoing GPS+compass pose, sequential egocentric RGB-D from one forward camera; human_motion.json forbidden at inference; panoramas only by rotating; pretrained models/external data allowed; closed-source APIs permitted but discouraged.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/jostar-track2: git diff origin/main origin/bohan/clarification-Oct14 -- README.md (task table + FAQ Q8, Q10-Q13)
9. **[high]** Quirk verified by competitor in the live challenge image: LOOK_UP/LOOK_DOWN tilt is 30 deg (sensor_report.json, 2026-10-18), not habitat's 15 deg default.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:28; docs/CODEX_TASK.md:33; HA-VLN rxr configs also use TILT_ANGLE 30 (/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/agent/VLN-CE/habitat_extensions/config/rxr_vlnce_english_task.yaml:6)
10. **[high]** Quirk: collision count = sim.previous_step_collided, so wall sliding counts; they keep a 0.12 m wall margin (0.22 m centre-to-wall) to avoid sliding, and log BUMP (<5 cm progress) / SLIDE (<80% of 0.25 m on flat floor). They flagged 'does the official scorer count only humans?' as unverified (VERIFY). Independent confirmation: UWMILab/HA-VLN issue #17 (Dec 2025) reports the code counts walls as well; organizer docs still describe TCR as human-only within 1 m.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:54-75; agent.py:448-465; README.md:159-161; https://github.com/UWMILab/HA-VLN/issues/17; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/havln_docs/docs/api/evaluation_metrics.md:27-33
11. **[high]** Quirk: humans are removed and re-added as new objects every 0.1 s wall-clock (new object ids each time) and stop updating after 120 signals (~12 s); per-frame navmeshes are cached to RECOMPUTE_NAVMESH_PATH/<scan>/<scan>_<fff>.navmesh. The competitor notes local LLM latency lets humans move during thinking, whereas the official fast replay has no such waits, so local collision counts can differ from official.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/scripts/seg_gt_smoke.py:7; config.py:89; docs/TRAINING.md:529-530; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/environments.py:96-145,150-213
12. **[medium (inference about replay speed; replay timing not observable)]** Implication of the same quirk that the competitor only half-exploits: 'waiting for a person to move' (they emulate WAIT with LOOK_DOWN/LOOK_UP pairs) is useless in the official replay because replay runs fast and humans freeze after ~12 s wall-clock; they relax the human margin after 24 steps for this reason.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/executor.py:10,54-58; config.py:66-70; agent.py:190-208
13. **[high]** Coordinate conventions they use: map (x, y) = (habitat x, -habitat z), yaw from +x CCW, agent forward = -z in body frame, habitat quaternion coeffs [x,y,z,w]; TURN_LEFT increases yaw by 15 deg; success/NE are 3-D Euclidean (wrong floor adds height difference).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/geometry.py:1-72; adapters/habitat_env.py:254-258; README.md:162
14. **[high (that these are their assumptions); medium (values)]** Sensor params they assume: depth 256x256, RGB 224x224, HFOV 90, forward 0.25 m, turn 15 deg; still UNVERIFIED (VERIFY): camera height 1.25 m, MAX_DEPTH 10, depth normalized, navmesh max climb 0.2 / slope 45 deg.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:15-28,39-45; scripts/check_env.py:110-127
15. **[high]** Official image contents they mapped (consistent with toolkit): /app/config/challenge_submission.yaml, /app/habitat-lab (possibly patched), /opt/havln-challenge/scoring/havln_scoring (six_action_task.yaml, havln-validate), /opt/havln-challenge/codabench/phase1/reference/public_reference_manifest.json. They pull it without Docker via anonymous registry-v2 layer download. Correction: the toolkit export script only hashes habitat_simulator.py into its receipt fingerprint; it does not validate it against a constant, so 'it is patched' is their inference.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/docs/TRAINING.md:89-99; scripts/extract_image_files.py:146-214; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2/scripts/export_cma_submission.py:189,214-224
16. **[high]** Submission format they produce: zip with root-level {split}.json = {format_version:1, split, episodes:[{episode_id, actions}]}, ids complete/unique, 1-500 actions, STOP only last, <500 must end with STOP.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/scripts/make_submission.py:21-70
17. **[high]** Competitor failure modes documented in code/tests: (a) agent stuck 67 steps inside a wall-inflation zone with zero candidates -> escape_mask added; (b) VLM STOP rejected because goal_box depth hit a background wall (5.4 m) -> now STOP accepted immediately (README's depth-confirmation rule is stale); (c) 11/20 instruction decompositions truncated at 256 tokens -> raised to 1024; (d) boundary stair cells misclassified as walls; (e) narrow alcoves yielding no >=1 m candidate; (f) 24-step initial spin + re-spin on every floor change consumes budget; (g) YOLO recall on SMPL-rendered humans never measured (semantic-ID ground-truth hook built to test it).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/planning/grid_search.py:61-75; docs/CODEX_TASK.md:33-37; agent.py:338-346; tests/test_stop_regressions.py:16-27; config.py:136; tests/test_navigation_regressions.py:59-117; config.py:104; agent.py:125-129; scripts/seg_gt_smoke.py:1-13
18. **[high (that they quarantined it); medium (that the episode is wrong)]** Data-quality note from competitor: HA-R2R train episode 7901 quarantined ('Outdoor instruction conflicts with verified indoor official goal').  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/scripts/training_watch.py:20
19. **[medium (absence of evidence; code search index incomplete and web search budget was exhausted mid-task)]** No other participant repos/blogs found. GitHub repo searches for havln / HA-VLN / roboworld / RoboPAD / HA-R2R return only organizer repos, the bingchengzhang repo, research forks, and unrelated projects; code search for 'havln-validate', 'export_cma_submission', 'public_reference_manifest' in non-organizer repos returns nothing (index lags for new repos). Web searches (English + Chinese, Zhihu/CSDN/bilibili) found no write-ups.  
   _Evidence:_ GitHub MCP search_repositories/search_code results (2026-10-24); WebSearch results listed in sources
20. **[high]** HCSG (HKUST-Guangzhou, Haoang Li group; arXiv 2605.13321) is the only third-party method published on HA-VLN-CE; its project page table (val_unseen TCR/CR/SR): HA-VLN-CMA 47.06/.77/.07, CMA-DA 27.25/.69/.09, HA-VLN-VL 6.63/.59/.14, LAW 5.88/.65/.15, DUET 5.74/.63/.16, ETPNav 6.94/.58/.17, GridMM 5.76/.59/.18, BEVBert 4.71/.55/.21, HCSG 5.02/.36/.24. Code 'will be released soon' (not released).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HCSG/index.html (cloned from github.com/HaoxuanXU1024/HCSG); /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HCSG/README.md:3
21. **[high (existence); low (that these authors are challenge entrants)]** Public third-party ports of strong VLA stacks onto HA-VLN already exist: (a) LeonGoretzkatju/Human-Dyanamic-StreamVLN (KAIST author, 2026-04-05) adds Habitat-0.2.4 human-aware evaluation of StreamVLN on HA-R2R with official TCR/CR/strict-SR; it loops human frames (frame % count) rather than freezing and uses agent radius 0.05, so its numbers would not transfer to the 0.1.7 replay. (b) Bubblevan/HA-VLN-HTTP (2026-03) is an HTTP bridge to run InternNav (InternVLA-N1/DualVLN) on the HA-VLN bench (640x480, HFOV 79).  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/Human-Dyanamic-StreamVLN/config/vln_havlnce_r2r.yaml; streamvln/habitat_compat/{metrics.py,human_controller.py:82-85}; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HA-VLN-HTTP/HASimulator/config/HAVLNCE_task_internnav.yaml; git log of both
22. **[medium (third-party quote of the paper; paper not read directly)]** A public harness (scott89/gpt6astra-r2rce, 2026-10-03) reproduces the protocol of a paper it cites as arXiv:2609.29861 claiming GPT-6-Astra (ultra) zero-shot R2R-CE SR 81.3% / SPL 71.5% (medium 75.7%) with single 512x512 RGB, no depth/map/pose; the harness itself gets 27-35% with glm-5.3-flash at ~55 API calls/episode and reports run-to-run flips on 6/10 episodes at temperature 0.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/gpt6astra-r2rce/README.md:1-30, Results section
23. **[high]** UWMILab/HA-VLN activity: 520 stars, 55 forks/derivatives in search; most recent fork phanhieeus/HA-VLN-blackwellARC (2026-10-23, no own commits yet); issue #30 (2026-10-09, user kuylv) about CMA vocabulary/embeddings suggests at least one more team reproducing the baseline; issue #14 reports unsorted GLB frame loading producing jerky human motion.  
   _Evidence:_ GitHub MCP search_repositories 'HA-VLN fork:only' and search_issues repo:UWMILab/HA-VLN; https://github.com/UWMILab/HA-VLN/issues/30, /issues/14
24. **[high]** Organizer docs report a different CMA validation result than the toolkit README (val_seen SR .165 Score 15.47; val_unseen SR .114 TCR 22.35 Score 11.94 vs README 16.509/12.945), attributing differences to checkpoint/runtime.  
   _Evidence:_ /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/havln_docs/docs/api/evaluation_metrics.md:73-82

## 9. Key numbers

| What | Value | Source |
|---|---|---|
| Competitor reported closed-loop result | SR 0 on 20 val_unseen episodes (r0 LoRA) | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/docs/CLOSED_LOOP.md:50 |
| Competitor estimated current Score (assumed NE~8, CR .4, TCR 2) | 4.7 | computed with official formula (inference) |
| Competitor r0 training data | expert labels from 500 train episodes (5-15 decisions/episode), 15% perturbation | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/docs/CODEX_TASK.md:71; docs/TRAINING.md:415 |
| Competitor LoRA config | r16, alpha 32, 4-bit nf4, lr 1e-4, 2 epochs, eff batch 16, 336px, <=4 images | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/configs/train_decision_lora.yaml |
| Competitor safety margins | agent_radius 0.10, wall_margin 0.12, human_margin 0.25 (relaxed 0.08 after waiting), unseen-body radius 0.35 | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:62-73 |
| TILT_ANGLE measured in challenge config | 30 deg | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:28 |
| Initial spin cost | 24 TURN_LEFT actions per episode start and per floor change | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:104; agent.py:74,128 |
| Instruction-decomposition truncation at 256 tokens | 11 of 20 failed | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/havln_agent/config.py:136 |
| Score formula check: CMA val_unseen reproduced | 13.0 | computed; README says 12.945 |
| Score sensitivity at SR .40/NE 4.5/CR .2/TCR .5 | +0.01 SR = +0.74; -0.1 m NE = +0.10; -0.01 CR = +0.09; -0.1 TCR = +0.14 | computed |
| HCSG val_unseen (TCR/CR/SR) | 5.02 / 0.36 / 0.24 | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HCSG/index.html |
| BEVBert val_unseen (TCR/CR/SR, NE) | 4.71 / 0.55 / 0.21, NE 5.51 | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HCSG/index.html; HA-VLN 2.0 (arXiv 2503.14229) step-size table via WebSearch |
| ETPNav val_unseen (TCR/CR/SR, NE) | 6.94 / 0.58 / 0.17, NE 5.43 | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HCSG/index.html; HA-VLN 2.0 via WebSearch |
| GPT-6-Astra zero-shot R2R-CE (as quoted) | SR 81.3% (ultra) / 75.7% (medium); reproduction with glm-5.3-flash 27.0-34.7% at ~55 API calls/episode | /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/gpt6astra-r2rce/README.md |
| UWMILab/HA-VLN popularity | 520 stars, 37 forks (repo), 55 fork-type results in search | GitHub MCP search (2026-10-24) |
| roboworld2026/track2 popularity | 7 stars, 1 fork, 1 open issue (as indexed) | GitHub MCP search_repositories 'roboworld' |
| Challenge Score equivalent: CMA baseline (toolkit, val_unseen) | 13.0 | computed from SR 0.129, NE 6.387, CR 0.684, TCR 17.536 (track2 README) |
| Challenge Score equivalent: ETPNav retrained (HA-VLN 2.0) | 16.7 | computed from SR 0.17, NE 5.43, CR 0.58, TCR 6.94 (HCSG table / HA-VLN 2.0) |
| Challenge Score equivalent: BEVBert (HA-VLN 2.0) | 19.4 | computed from SR 0.21, NE 5.51, CR 0.55, TCR 4.71 (HCSG table; NE from HA-VLN 2.0 step-size table) |
| Challenge Score equivalent: HCSG (NE assumed 5.3) | 22.6 | computed from SR 0.24, NE 5.3, CR 0.36, TCR 5.02 (HCSG table) |
| Threat-matrix Score: T0 CMA baseline / exported toolkit tape | 13.0 | assumed SR 0.129, NE 6.387, CR 0.684, TCR 17.536 (inference) |
| Threat-matrix Score: T1 Hierarchical VLM+mapping, early (bingchengzhang-like) | 8.8 | assumed SR 0.05, NE 7.0, CR 0.35, TCR 1.5 (inference) |
| Threat-matrix Score: T2 ETPNav/BEVBert/ETP-R1 ported, no collision shield | 18.0 | assumed SR 0.19, NE 5.5, CR 0.56, TCR 5.5 (inference) |
| Threat-matrix Score: T3 HCSG-class (published SOTA on HA-VLN-CE) | 22.6 | assumed SR 0.24, NE 5.3, CR 0.36, TCR 5.02 (inference) |
| Threat-matrix Score: T4 Graph agent (ETP-R1) + collision shield + HA-R2R fine-tune | 31.7 | assumed SR 0.33, NE 4.8, CR 0.2, TCR 0.5 (inference) |
| Threat-matrix Score: T5 VLA (SimpleVLN/StreamVLN/DualVLN) fine-tuned on HA-R2R + depth shield | 39.5 | assumed SR 0.42, NE 4.3, CR 0.15, TCR 0.4 (inference) |
| Threat-matrix Score: T6 Frontier-API zero-shot agent (GPT-6-Astra-class) + depth shield | 46.7 | assumed SR 0.5, NE 3.5, CR 0.15, TCR 0.3 (inference) |
| Threat-matrix Score: T6b Frontier-API agent without collision shield | 26.9 | assumed SR 0.3, NE 3.8, CR 0.55, TCR 3.0 (inference) |
| Threat-matrix Score: T7 Test-time multi-rollout / self-verification on local sim (gray) | 51.8 | assumed SR 0.55, NE 3.2, CR 0.1, TCR 0.2 (inference) |
| Threat-matrix Score: T8 Privileged offline planner (navmesh + graph prior + LLM goal grounding) | 66.5 | assumed SR 0.7, NE 2.5, CR 0.02, TCR 0.02 (inference) |
| Estimated P(best rival Score >= X) | {20: 0.71, 30: 0.5, 40: 0.32, 45: 0.24, 50: 0.16, 55: 0.1, 60: 0.06} | Monte Carlo over threat matrix (inference, low confidence) |

## 10. Sources

- https://github.com/bingchengzhang/HA-VLN (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang)
- https://huggingface.co/bingchengzhang/HA-VLN-nav-r0-lora (cited in competitor README; not fetched)
- https://github.com/roboworld2026/track2 (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2)
- https://github.com/JostarXiong/track2 branch bohan/clarification-Oct14 (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/jostar-track2)
- https://github.com/UWMILab/HA-VLN (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN); issues #14, #17, #30
- https://github.com/JosephJostar0/havln_docs (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/havln_docs)
- https://github.com/JosephJostar0/HAVLN_baseline (empty, local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HAVLN_baseline)
- https://github.com/HaoxuanXU1024/HCSG (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HCSG); https://arxiv.org/abs/2605.13321
- https://github.com/LeonGoretzkatju/Human-Dyanamic-StreamVLN (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/Human-Dyanamic-StreamVLN)
- https://github.com/Bubblevan/HA-VLN-HTTP (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HA-VLN-HTTP)
- https://github.com/phanhieeus/HA-VLN-blackwellARC (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/HA-VLN-blackwellARC)
- https://github.com/scott89/gpt6astra-r2rce (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/gpt6astra-r2rce); cites arXiv:2609.29861
- https://github.com/TingdeLiu/R2R-Eval-Ladder (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/A7/R2R-Eval-Ladder)
- https://arxiv.org/abs/2503.14229 / https://arxiv.org/html/2503.14229v2 (HA-VLN 2.0; numbers via WebSearch summaries)
- https://roboworld2026.github.io/ (local source: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/roboworld2026.github.io, commit 84d0bc2 2026-10-23)
- https://github.com/F1y1113/havln-challenge/pull/4 (timeline PR, via WebSearch)
- Peer findings cross-checked: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/findings/B2-vlnce-sota-2023-2026.md, A2-collision-semantics-habitat017.md
