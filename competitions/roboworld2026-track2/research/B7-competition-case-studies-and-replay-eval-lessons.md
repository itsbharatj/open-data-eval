# B7: Competition case studies and lessons from replay/offline evaluation

Topic id: `B7-competition-case-studies-and-replay-eval-lessons`. Research agent B7. Date: 2026-10-24.

**How this was researched.** I ran about 20 WebSearch queries before the session-wide limit of 200 searches, shared by all ~35 agents, ran out. After that I used primary sources fetched with `git clone` of public repositories, which CONTEXT.md allows. Those repositories are the challenge toolkits, rules READMEs, the CodaBench wiki and the Embodied-AI workshop website source. They are cloned under `$BASE/b7/`, where `BASE=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`. A few well-known historical incidents (Baidu ILSVRC-2015, PetFinder 2020, DFDC 2020, Netflix Prize 2009, Roelofs et al. 2019) come from background knowledge and are marked **[bg]**. I could not re-verify them this session, so their confidence is medium. The information-theory numbers come from `scratchpad/b7_scripts/infotheory.py`.

---

## 0. Executive summary: the 5 most decision-relevant findings

1. **The organizers have already written down a strict input rule, but it is not merged yet. Every precedent says such rules are enforced at award time.**
   - **The pending rule.** Open PR #2 on `roboworld2026/track2` (`refs/pull/2/head` = 8289590, branch `bohan/clarification-Oct14`, 2026-10-14) says:
     - the inputs are the instruction, the start pose, the agent pose (GPS+compass) and **sequential egocentric RGB-D** from **one forward-facing camera**;
     - extra cameras are banned, and panoramas must be acquired by rotating, which counts toward the action budget;
     - `human_motion.json` is **prohibited at inference**;
     - val and test must **not be used for training**;
     - closed APIs are allowed but discouraged.
   - **Precedent with the same submission model.** RxR-Habitat (2021–2023) and VLN-CE also took offline-generated trajectories. They still declared panoramic waypoint models "not valid". ALFRED and AI2-THOR, which also run offline on public test scenes, explicitly ban privileged test-time information. RoboWorld Track 3 states that "the top teams must provide their code and checkpoints, and their results are reproduced before the awards."
   - **Implication.** "Offline replay, therefore anything goes" (CONTEXT hypothesis 8) is **not** a safe basis for an award-winning entry. Get a written ruling before Phase 2.
2. **This leaderboard leaks far more than any precedent did.**
   - **How the design compares.** Track 2 Phase 2 gives up to 100 submissions (5/day) **on the final ranking set**. Results are visible, the metrics are "full precision", and the best score is retained. There is no private split.
     - Habitat's Test-Challenge allowed **5 submissions in total**, with results hidden until the workshop.
     - ALFRED allowed 1 submission per 7 days, all made public.
     - Kaggle uses a public/private split.
   - **How much it leaks.** Information-theoretic bound with exact success counts (deliberate failures can switch individual episodes off):
     - ≤11.7 bits per submission, so ≤1,173 bits over 100 submissions. A 6-decimal Score display adds about 13–15 bits per submission through the NE term.
     - The residual goal uncertainty of a good model is about 1,000–1,700 bits, because 3,408 episodes are only 1,136 trajectories with shared goals and about 8 goal clusters each.
     - So probing could in principle recover a large share of the test goals. Whitehill (2017) recovered **all 512 test labels with 98 probe submissions** on a Kaggle full-precision log-loss oracle.
3. **Probing would pay off, but it is near-certain to be detected and cannot be defended.**
   - **Payoff.** Realistic gain from SR-only probing is about +2–8 SR points (+1.5–6 Score). The theoretical ceiling is +20 SR or more.
   - **Why it would be caught.**
     - Probing needs structured submissions in which thousands of episodes are deliberately failed or toggled. That pattern is obvious to organizers, who can download every submission on CodaBench.
     - The final answers could not be reproduced from code during award verification.
     - It directly violates PR #2 Q10 ("test splits must not be used for training"), Habitat's "Don't overfit to the test set" and ALFRED's "do not ... optimize on the test set".
     - Precedent: Baidu was barred from ILSVRC for 12 months in 2015 [bg].
   - **Recommendation: do not probe.** Use Phase 2 submissions only for whole-system variants that can be rebuilt from code.
4. **Across VLN-CE competitions, the winners were modular systems with explicit collision handling, data scaling and ensembles.**
   - **2022 RxR-Habitat winner (Dong An et al., the later ETPNav team).** Its modules were a candidate waypoint predictor, a history-enhanced planner and a heuristic "tryout" controller. It added in-domain synthetic pretraining, environment-level augmentation and a snapshot ensemble.
     - NDTW went from 37.39 to 55.43 and SR from 24.85 to 45.82 (+48% / +90% relative).
     - With sliding disabled, SR fell from 51.98% to 20.93%. The tryout controller brought it back to 48.6%.
   - **Later winners.** GridMM (grid memory map) won RxR-Habitat 2023. SkillFusion (AIRI), which mixes classical and learned skills, won Habitat ObjectNav 2023.
   - **Relevance here.** HA-VLN counts any excess collision as failure, so the "tryout" lesson (collision handling is worth about 28 SR points) applies directly.
5. **First-edition margins are large. Mature-benchmark margins are inside noise.**
   - **Large margins.** Habitat ObjectNav 2021 was won with 0.13 SPL against 0.06 for second place. RxR-Habitat 2022 beat the previous best by +18 NDTW.
   - **Small margins.** In Habitat ObjectNav 2023 the top two tied at 0.28 SPL with third at 0.26; Habitat "reserve[s] the right to use additional metrics ... in case of statistically insignificant SPL differences".
   - **Noise level of this test set.** It has about 0.9–1.5 SR points of noise (1,136 correlated trajectories). Best-of-N selection among near-equal variants adds about +0.5–1.4 SR legitimately.
   - **Implication.** Approach class decides first place (privileged-compliant planner vs. closed-loop learner). Leaderboard micro-optimization does not.

---

## 1. Case studies

| Competition | Evaluation mode | Submission limits / feedback | Information-leak controls | Winner / margin | Lesson for HA-VLN | Conf. |
|---|---|---|---|---|---|---|
| **RxR-Habitat 2021** (CVPR'21 EAI), Habitat 0.1.7, MP3D | Agent runs **locally**; teams submit a jsonlines file of **trajectories** (`BaseVLNCETrainer.inference()`) | Leaderboard Mar 1 – May 31 2021 | Rules on the action/observation spec; MP3D test scenes are public | Winner not found (search budget ran out) | Same offline model as HA-VLN | high (mode), n/a (winner) |
| **RxR-Habitat 2022** | Same | — | Required config: 30° turns, 0.25 m steps, 30° look up/down, 480×640 RGB-D. The README states "Existing waypoint models are not valid due to their panoramic observation space ... would need to be adapted" (this text is in the 2023-era README) | **1st: Dong An et al.** (CWP + history planner + tryout; synthetic pretraining, environment augmentation, snapshot ensemble). NDTW 55.43 / SR 45.82 vs 37.39 / 24.85 previously; tryout restores no-sliding SR from 20.93% to 48.6% | Collision/stuck handling is worth ~+28 SR. Observation-spec rules are applied to offline submissions too | high (method), medium (numbers via ResearchGate/Lacuna summary) |
| **RxR-Habitat 2023** | Same | Leaderboard Mar 20 – May 15 2023 | Same | **The GridMM Team** (embodied-ai.org/cvpr2023) | Map-memory planners keep winning | high |
| **VLN-CE (R2R-CE) eval.ai #719**, rolling | Local inference; the JSON contains a per-step `{position, heading, stop}` pose list. **The server scores the submitted poses; it does not replay them** | — | Honor system plus papers | ETPNav test SR 55; leaderboard re-evaluated the CMA baseline at **0.27 SPL vs 0.30 in the paper** ("hardware + Habitat build" differences) | Calibrate on the official scorer. HA-VLN's action replay is stricter than VLN-CE (physically consistent), but privileged information is still unenforceable technically | high |
| **R2R discrete leaderboard** (EvalAI #97) | Upload viewpoint trajectories | — | Community norm: report single-run, pre-explore and beam search **separately**; SPL/TL expose exploration cost | Beam search: EnvDrop 69 SR (single-run 51), AuxRN 71, Airbert/Lily 78 SR with SPL ≈ 0.01; pre-explore (Active Exploration) 70 (B1 findings, ScaleVLN appendix) | Using test-environment information is tolerated **only when declared as a separate setting**. HA-VLN has a single leaderboard, so a privileged entry must be pre-cleared and disclosed | medium-high |
| **Habitat Challenge 2019–2023** (PointNav/ObjectNav/ImageNav/Rearrange) | **Docker** agents run remotely on AWS. In 2019 Gibson was chosen **because "unlike Matterport3D Gibson's raw meshes are not publicly available allowing us to sequester a test set"** | Minival 30–100/day; Test-Standard 10/day ("Don't overfit to the test set"); **Test-Challenge 5 in total, best of 5 chosen automatically, results hidden until the workshop**; "We will block and disqualify teams that spam our servers" | Sequestered scenes, remote execution, hidden final results | ObjectNav 2021: Red Rabbit 6-Act Tether 0.13 SPL / 0.30 SR vs 2nd Habitat-Web 0.06 / 0.16. PointNav: 2020 winner 0.21 SPL, 2021 winner 0.74 SPL / 0.96 SR. ObjectNav 2023: SkillFusion (AIRI), tied with SkillTron at 0.28 SPL; ICanFly 0.26 | The organizers knew public MP3D meshes break test sequestration. HA-VLN uses public MP3D test scans and offline replay, so only rules and verification protect it | high (rules), medium (scores) |
| **ALFRED leaderboard** | Run locally on test seen/unseen, **dump action sequences**; the server replays them (closest analogue to HA-VLN) | **1 submission per 7 days**; all submissions public | Rules: "only RGB and language ... cannot use additional depth, mask, metadata ... on Test"; "Do not spam the leaderboard with repeated submissions (under different email accounts) in order to optimize on the test set"; mandatory disclosure questions on extra sensors | — | The same replay design was paired with explicit input rules, disclosure and very low submission counts | high |
| **RoboTHOR ObjectNav 2021 / AI2-THOR Rearrangement 2021–23** | Local runs; teams upload metrics plus trajectories, which the server validates | — | "never train your agent within any of the test scenes"; extra sensor information "should not be used at inference time"; "a winning submission must be materially different from the baseline models ... and from submissions made to prior years' challenges" | Rearrangement 2022: 1-phase ProcTHOR+FT 24.47% FixedStrict; 2-phase MaSS 16.56% (later SoTA TIDEE 28.94%) | Offline evaluation plus written rules plus a novelty clause | high |
| **IROS 2025 InternUtopia VLN (physical)** | Docker image run on the organizers' AliCloud; EvalAI | — | Fixed robot USD, controller and **monocular RGB-D** observation space; "use of large-scale model APIs (GPT, Claude, Gemini) is **not** permitted"; test server has no internet; onsite real-robot phase (Final = 40% online SR + 60% onsite SR) | Champion write-up on Zhihu (not read) | Recent VLN challenges restrict observations and APIs. RoboWorld PR #2 is milder: APIs allowed but discouraged | high |
| **RoboWorld 2026 Track 3** (sibling track, same umbrella) | Teams upload CARLA results | 3/day/participant; best kept | "Navigation Signal Rule": no route-planner information anywhere; "**Compliance is checked when the results of the top teams are reproduced**"; "The top teams must provide their code and checkpoints, and their results are reproduced before the awards" | — | Expect the same reproduction regime for Track 2 (README Q2: winners "may be asked to provide code or models for verification") | high |
| **RoboWorld 2026 Track 1** | Offline submissions | Phase 1 "does not determine shortlisting, final rankings, or awards" | Phase 2 gives test inference inputs only | — | Phase 1 is for development only | high |
| **Kaggle Intel-MobileODT 2017** (Whitehill) | CSV predictions; public LB on all 512 stage-1 test images, unrounded log-loss, 5/day | — | Two-stage design: stage 2 used 4,018 test images, including the original 512 | Attack: **all 512 labels inferred in 98 probe rounds**, stage-1 rank #4/848 with zero modelling; stage-2 rank 225/884 | A full-precision oracle on the final set leaks labels. A private split neutralises it; Track 2 has no private split | medium-high |
| **Blum & Hardt "Ladder" (ICML 2015); Hardt 2017** | Theory | — | Boosting attack shows that Kaggle-style leaderboards with 1e-5 rounding (< 1/√n) allow overfitting; Ladder only releases a new score when it beats the best by a margin; shaky-ladder lower bound ~(log(kn))^(1/3)/n^(1/3) | — | Organizer remedies: coarsen precision, release only significant improvements, hide the board | medium-high |
| **Aggarwal et al., ICML 2021** | Theory | — | **One** carefully built prediction vector can reveal all labels from a log-loss score under arbitrary precision; attacks still work with noise and bounded precision | — | Real-valued aggregate metrics (here NE and Score) are high-capacity channels | medium-high |
| **ILSVRC 2015 Baidu** [bg] | Server-scored predictions, 2 submissions per week | — | About 30 accounts and about 200 submissions in roughly 6 months; Baidu was barred for 12 months and withdrew its claim | — | Multiple-account or excess submission is the canonical disqualifying offence. CodaBench limits are **per participant**, so use one submitting account per team | medium (bg) |
| **Kaggle PetFinder 2019–20** [bg] | Code competition | — | The first-place team was disqualified after post-competition code review found hidden scraped test answers | — | Code verification catches test-label exploitation after the fact | medium (bg) |
| **Facebook DFDC 2020** [bg] | Code competition | — | The top private-LB team was disqualified for external data that did not meet the rules' consent/licence requirement | — | Document data provenance and licences (MP3D!) in the report | medium (bg) |
| **Netflix Prize 2009** [bg] | Quiz/test split | 1/day | Hidden test half | BellKor's Pragmatic Chaos won on an identical test RMSE because it **submitted 20 minutes earlier** | Tie-breaks on submission time are real. Track 2 breaks exact ties by SR, NE, CR, TCR, then earlier time; CodaBench sorts ties by `submitted_at` | medium (bg) |

---

## 2. Winning tactics (ranked by evidence and relevance)

1. **Modular plan-and-control with a robust low-level controller and stuck/collision recovery.**
   - Evidence: the 2022 RxR-Habitat winner (tryout recovered 27.7 SR in the no-sliding setting); ETPNav's obstacle-avoiding trial-and-error controller (ETPNav README); Safe-VLN (2023), which filters waypoints with a simulated LiDAR and re-selects after a collision.
   - The VLN-Safe benchmark (arXiv 2610.14682) finds that 38.5–56.8% of "successful" R2R-CE episodes involve contact under sliding, and that blocking lowers SR by 11.7–36.1 points.
   - For HA-VLN, where any excess collision means failure, this is first-order.
2. **Scale in-domain data.** Synthetic instruction pretraining, environment-level augmentation and large step counts. The Retrospectives paper reports winners training for hundreds of millions to billions of steps, for example Habitat-Web with 400M steps of behaviour cloning.
3. **Map or topological memory in the planner.** CWP/ETPNav topological maps (2022) and the GridMM grid map (2023).
4. **Ensembles.** The 2022 winner used a snapshot ensemble. Ensembling over goal-inference models is the natural analogue here.
5. **Hybrid classical + learned components.** The 2019 PointNav winner and SkillFusion (ObjectNav 2023) both combined them. BARN reports that classical planners led the field [bg].
6. **Exact matching of the evaluation configuration.** Sliding vs. no sliding swung SR by 31 points in 2022. The leaderboard and local runs differ: VLN-CE CMA scored 0.27 SPL on the leaderboard vs 0.30 locally. Habitat runs a minival phase "to confirm that our remote evaluation reports the same result as the one you're seeing locally".
7. **Test-time exploration or pre-exploration** gives +15–20 SR on R2R, but organizers and the community require it to be reported as a separate setting.

## 3. Margins between places

**Verified data points:**
- Habitat ObjectNav 2021 (Test-Challenge): 1st 0.13 SPL / 0.30 SR vs 2nd 0.06 SPL / 0.16 SR, roughly 2×.
- Habitat ObjectNav 2023: SkillFusion = SkillTron 0.28 SPL, ICanFly 0.26, host baseline 0.05 (table in IPPON arXiv 2410.19697; official winner SkillFusion per embodied-ai.org/cvpr2023).
- PointNav: 2020 winner 0.21 SPL, 2021 winner 0.74 SPL.
- RxR-Habitat 2022: winner +18 NDTW / +21 SR over the previous best.

I found no verified 5th-place numbers before the search budget ran out.

**Inference (medium confidence).** In first-edition challenges, 1st place typically leads 2nd by 1.5–2× in the primary metric, and 1st to 5th spans 2–5×. In mature challenges the top 3 are within statistical noise. For HA-VLN 2026 (baseline Score 12.9) I expect a bimodal field: a few systems that use test-scene geometry, legitimately or not, against closed-loop learners. The gap between those groups could be 30–60 Score points; within a group it could be a few points.

**Noise level of this test set.**
- The SR standard error is 0.86 points at p = 0.5 if all 3,408 episodes were independent. It is 1.48 points if the three instructions of each of the 1,136 trajectories are fully correlated. In Score terms that is about 0.7–1.2 points.
- Best-of-N selection over variants that disagree on 10–20% of episodes inflates the retained score by about +0.5 SR (N = 5) to +1.0–1.35 SR (N = 20–100).

---

## (a) Ten actionable lessons

1. **Get the input rules in writing before Phase 2 (Oct 30), and design every Phase-2 submission to the strictest plausible reading.**
   - PR #2 lists the allowed inputs and is open but not merged. Track 3 reproduces top teams. RxR-Habitat, ALFRED and AI2-THOR all banned privileged test-time inputs despite offline submission.
   - File a GitHub issue and send an email asking specifically about:
     - the MP3D mesh/navmesh and connectivity graphs at inference;
     - the public R2R test instructions;
     - the HA-VLN 1.0 human annotations;
     - the 12-camera rig in the task config vs PR #2 Q8;
     - LLM/VLM APIs.
   - **Because the best submission is retained automatically, one non-compliant upload can become your official entry.** Do not upload privileged-mode outputs to Phase 2 unless they are explicitly allowed.
2. **Treat zero-collision control as the first-order problem.** HA-VLN SR requires TCR_ep = 0. Precedent: sliding vs. no sliding was worth 31 SR, and the tryout controller recovered 28. Verify every action sequence by local replay against all 120 human frames (see A2/C1).
3. **Build a modular system:** goal grounding (VLM/LLM plus waypoint/topological memory) → planner → certified collision-free controller. Every VLN-CE challenge winner was modular.
4. **Invest in data and ensembles over tricks.** Use synthetic in-domain instructions and environment augmentation (the 2022 winner's +48% NDTW came from this), plus multi-model ensembling for goal inference, scored on val_unseen only.
5. **Use Phase 1 (val ground truth is public) as the "minival" calibration phase.** Submit:
   - the official CMA export, to reproduce 12.945;
   - an identical file twice, to measure scorer nondeterminism from wall-clock humans;
   - a wall-sliding but human-free set, to confirm wall collisions count;
   - a known-NE set, to confirm Euclidean vs. geodesic NE.

   None of this extracts hidden information, so it is fully legitimate. **Do not post GT-derived perfect val scores**: they look like cheating and carry no ranking value.
6. **Budget the 100 Phase-2 submissions.**
   - Day 1: a smoke test with a known-good pipeline, to catch episode-ID or coordinate bugs.
   - Then at most 1–2 per day of genuinely different full-system variants.
   - Keep a reserve of at least 20 for outages (CodaBench was down from Oct 21 to at least Oct 24 per C2) and for the final week.
   - Submit the strong entry early, because exact ties are broken by submission time.
7. **Never probe the test leaderboard** (subset toggling, kill switches, per-scan splicing, or resubmitting identical files to farm scorer randomness). See (b).
8. **Make the final submission bit-reproducible from code:**
   - pinned docker digest;
   - temperature-0 or cached LLM responses with stored prompt and response hashes;
   - seeds;
   - content-addressed per-episode logs;
   - one command that regenerates `submission.zip` with an identical SHA-256.

   This is exactly what award verification (Track 3 style) will test.
9. **Submit from one team account only.** CodaBench `max_submissions` and `max_submissions_per_day` apply **per participant**, so several team accounts multiply the cap. That is the Baidu-2015 offence and ALFRED's "different email accounts" rule.
10. **Plan for awards beyond rank.**
    - "Best Innovative Solution" and the oral talks are judged by humans. PR #2 Q12 encourages open-weight ~7B models and discourages heavy reliance on closed APIs.
    - Keep a compliant closed-loop pipeline based on open-weight models, both as the fallback entry and as the innovation story.
    - Report any privileged-information setting separately, as R2R separates beam search and pre-exploration.

---

## (b) Risk assessment: exploiting leaderboard feedback (3,408 episodes, ≤100 submissions, full-precision SR/NE/CR/TCR)

### b.1 Channel model

- **Per-episode controls.** For each episode we control the final position and whether to induce a known failure (a "kill switch"). The kill switch can be deliberate wall bumps, which push the count above the public `collision_num_test` baseline so SR_ep = 0 deterministically, or stopping short of the candidate.
- **No noise on live episodes.** Live episodes use collision-free plans, so success is deterministic: SR_ep = success AND TCR_ep == 0 (HASimulator/metric.py L15–17).
- **Trajectory structure.** Test episodes are 1,136 trajectories × 3 instructions with a shared goal (A1, high confidence). Each start has a median of 24 nav-graph goal candidates, which form about 8 clusters of 3 m.
- **Exact counts are recoverable.** If the final position is kept at the candidate for both live and killed copies, NE is constant across queries. Score then changes only through SR and the known CR/TCR terms, so the 6-decimal Score display recovers **exact** success counts. Each success moves the Score by about 0.016–0.023 points, far above the 1e-6 display resolution.

### b.2 Capacity

| Quantity | Value |
|---|---|
| SR exact-count channel | log2(3,409) = **11.7 bits/submission**, so **≤1,173 bits / 100 submissions** |
| Coin-weighing (exact subset sums): binary items fully resolved with 100 queries | **~440** constructive non-adaptive (Lindström / Erdős–Rényi 2n/log2 n); ≤~1,000 by the information bound |
| Queries needed to resolve top-1 correctness for all 1,136 trajectories | 112 (information bound) to 224 (constructive) |
| Bits needed to locate the wrong trajectories when top-1 accuracy is 0.6 / 0.7 / 0.8 / 0.9 | 1,097 / 996 / 815 / 529 bits (108 / 98 / 80 / 52 queries at the information bound) |
| NE channel through the 6-decimal Score | ∂Score/∂(Σd) ≈ 7.0e-4 per metre at NE = 2, so a resolution of **~1.4 mm** on the summed distance and **~14–15 bits/submission** over a 40 m range. With float64 `scores.json` it is limited only by how exactly we can model the goal coordinates (val ground truth allows calibration): **≥~23 bits/submission** |
| Goal entropy of the test set | Prior: about 3,400 bits (8 clusters) to 5,200 bits (24 nodes). Residual for a good model: about 1,000–1,700 bits |

**Conclusion (high confidence on the arithmetic, medium on the assumptions).** The Phase-2 oracle's capacity, about 1,200 bits from SR alone and 2,600–3,500 bits with the NE/Score channel, is the same order as the residual goal uncertainty of a competent model. In principle, a determined prober could approach oracle goal knowledge on a large part of the test set. Whitehill did exactly this: 512 labels in 98 queries.

### b.3 Expected gain

Assumptions: top-1 trajectory accuracy 0.75, so 284 wrong trajectories; P(top-2 correct | top-1 wrong) = 0.5; Social ≈ 1; one success = +0.0235 Score.

- **Theoretical ceiling (SR channel, perfectly efficient):** about 85% of wrong trajectories corrected, which is about 720 episodes: **+21 SR, about +17 Score**.
- **Constructive coin-weighing on the 440 least-confident trajectories:** about 85 trajectories fixed, which is about 255 episodes: **+7.5 SR, about +6 Score**.
- **Realistic** (half the budget, 5/day adaptivity, modelling error, possible scorer noise): **+2–4 SR, about +1.5–3 Score**.
- **Grey-zone per-scan splicing** (choose one of M models per test scan from leaderboard deltas; needs 18×(M−1) submissions): about +1–3 SR.
- **Legitimate best-of-N over full variants:** about +0.5–1.4 SR, an artefact of selection.

### b.4 How detectable it is

**Near-certain detection** for anyone who looks, and award winners will be looked at.

1. CodaBench admins and collaborators see and can download every submission and the leaderboard CSV. Hidden leaderboards and `hide_score_output` exist and can be switched on mid-competition.
2. Probing submissions have an unmistakable signature:
   - thousands of episodes that STOP early or deliberately collide (TCR and CR spike far above the baseline's 13–17 per episode);
   - SR jumping between very low and high values with no change in method;
   - per-episode endpoints toggling according to a balanced design matrix while the other episodes stay byte-identical.
3. The final best submission cannot be regenerated from the claimed code and model. Award verification (README Q2; Track 3 practice) fails.
4. Statistical test: compare per-episode endpoint changes between consecutive submissions. Genuine model iterations change many episodes in correlated, model-explainable ways; probes do not.

### b.5 Defensibility

**None.**
- It violates PR #2 Q10 ("test splits must not be used for training"; selecting per-episode answers with test feedback is training on test).
- Every precedent forbids it: Habitat "Don't overfit to the test set" and "block and disqualify teams that spam our servers"; ALFRED "Do not spam ... in order to optimize on the test set"; Baidu ILSVRC-2015 ban [bg].
- The winners present at a NeurIPS workshop, so a disqualification would be public.
- With no private split, the organizers' only defence is post-hoc review, and they will apply it to the top 5.

### b.6 Leaderboard hygiene policy (recommended)

1. One submitting account.
2. Every Phase-2 upload is a complete, reproducible system output, logged with git commit, config hash and ZIP SHA-256.
3. No submission whose per-episode content was chosen using earlier test scores.
4. No identical resubmissions to sample scorer randomness. Aim instead for zero variance by being robust to all animation frames.
5. At most about 20–30 Phase-2 uploads in total.
6. Disclose the full submission log in the technical report.

---

## (c) What to put in the technical report so top-5 awards are not contested

1. **Compliance matrix.** List every rule (README Q1–Q7 plus PR #2 Q8–Q13 if merged) and how the system complies: single forward RGB-D camera; panoramas only by counted rotations; pose from GPS+compass; no `human_motion.json` or ground-truth human states at inference; no training on val/test; APIs used, if any.
2. **Inference-time input firewall.** State exactly which files and fields the inference process could read (an allow-list), how this was enforced (separate process or container, read-only mounts) and the audit log hashes. If any privileged offline information was used (meshes, navmeshes, connectivity graphs, R2R test instructions, HA-VLN 1.0 human annotations), say so, quote the organizers' written permission, and give an **ablation without it**.
3. **Data provenance and licences.** List MP3D licence compliance, every external dataset and pretrained model with its licence, and a statement that no test labels and no Phase-2 feedback were used for training or per-episode selection (DFDC precedent [bg]).
4. **Reproducibility package.** Code, weights, docker digest, seeds, cached LLM/VLM responses, one-command regeneration of the final ZIP (with SHA-256 match), runtime and compute. Show local replay metrics on val_unseen matching the official Phase-1 numbers.
5. **Submission log.** Every Phase-2 submission with timestamp, the change from the previous one, and Score, SR, NE, CR and TCR. Explain how the final entry came about: the best of K full-system variants, and why K is small.
6. **Results beyond the headline.** Report val_seen and val_unseen (official Phase 1) and test. Break collisions down into human vs. wall. Show robustness to human animation timing (all 120 frames) and failure analysis by instruction type and scene.
7. **Method and novelty section** aimed at "Best Innovative Solution": what is new, ablations, use of small open models (PR #2 Q12 preference).
8. **Team and account declaration.** Members, one submitting account, and confirmation that daily and phase limits were respected (Baidu/ALFRED precedent).
9. **Organizer correspondence appendix.** Copies of the rule clarifications received, with dates.

---

## 4. Contradictions and flags vs CONTEXT.md and other agents

- **CONTEXT facts 6/8 ("no explicit rule forbids using the simulator/scene geometry offline").** Literally true of merged `main` (2d408b2). However, open PR #2 (8289590) restricts inputs to pose plus sequential egocentric RGB-D and bans `human_motion.json` at inference, and the website says "Given egocentric RGB-D observations". Precedents show such rules are enforced at award time. **High-severity risk** for the "plan everything offline" strategy (agrees with C1's flag).
- **Submission caps are per participant on CodaBench** (`max_submissions` and `max_submissions_per_day` are "per participant" in the YAML spec). The README's "five per day and 100 per phase" does not say "per team". Multiple accounts would multiply the cap, but the precedents treat that as disqualifying. Use one account.
- **B2 says ETPNav's "default eval teleports on backtracking (back_algo: teleport)".** The YAML default is `teleport`, but the released `run_r2r/main.bash` sets `IL.back_algo control` for **both eval and inference** (lines 33, 46); only training uses teleport. Minor correction.
- **RxR-Habitat rule vs winners.** The README says panoramic waypoint models "are not valid ... would need to be adapted", yet the 2022 and 2023 winners used waypoint-predictor (multi-view depth) architectures. The most plausible reconciliation, which I could not verify, is that the panoramas were acquired by in-place rotation, which is exactly PR #2 Q8's prescription.
- **Display precision.** The README shows Score to 6 decimals and components "rounded for display". CodaBench defaults to 2 decimals per column. Whether participants can download the full-precision `scores.json` (`hide_score_output`) is unknown. It determines the NE-channel leakage, but not the SR-channel leakage, which is recoverable from the 6-decimal Score.

## 5. Open questions

1. Will PR #2 be merged, and will the organizers rule on offline use of MP3D meshes, navmeshes and connectivity graphs, the public R2R test instructions and the HA-VLN 1.0 human annotations?
2. Are the submission limits per team or per account? Can a participant delete or deselect a submission under the Track 2 `submission_rule`, or is Force_Best automatic?
3. Can participants download the full-precision scoring output (`scores.json`, stdout) for Phase 2? Will the Phase-2 leaderboard stay visible?
4. What do the CodaBench competition Terms (competition 18135) say about multiple accounts, probing and code verification? I could not fetch them from here (codabench.org is blocked).
5. Who won RxR-Habitat 2021, what was the full 2022 leaderboard, and what are the 5th-place numbers? (Search budget ran out.)
6. Does the scorer show per-episode results (CodaBench `detailed_results.html`)? If so, leakage is total and organizers may disable it.

## 6. Sources

**Primary sources read locally** (BASE = `scratchpad/ext`):
- `track2/README.md` (roboworld2026/track2 @2d408b2)
- `track2-jostar` branch `bohan/clarification-Oct14` @8289590 (= roboworld2026/track2 `refs/pull/2/head`, open)
- `track3/README.md` @b695738; `track1/README.md` @a52e43f
- `roboworld2026.github.io/track2.html`, `track3.html`
- `HA-VLN/HASimulator/metric.py`
- `VLN-CE/README.md` (master + `rxr-habitat-challenge` branch); `VLN-CE/vlnce_baselines/common/base_il_trainer.py` (inference); `environments.py` `get_info`
- `ETPNav/README.md`, `ETPNav/run_r2r/main.bash`
- `Discrete-Continuous-VLN/README.md`
- `b7/habitat-challenge` README (branches challenge-2019 … navigation-challenge-2023, main)
- `b7/alfred/README.md`
- `b7/robothor-challenge/README.md`
- `b7/ai2thor-rearrangement/README.md`
- `b7/codabench.wiki/Yaml-Structure.md`, `Leaderboard-Functionality.md`
- `b7/eai/src/pages/cvpr2021.tsx`, `cvpr2023.tsx`, `cvpr2024.tsx`, `cvpr2026.tsx`
- `sota/InternNav/scripts/iros_challenge/README.md`

**Web sources:**
- https://arxiv.org/abs/2206.11610 (1st Place RxR-Habitat 2022); https://www.researchgate.net/publication/361500506 ; https://lacuna.tiptreesystems.com/work/1st-place-solutions-for-rxr-habitat-vision-and-language-navigation-competition/wrk_3f0ba748c640c1a4eac1f392a08167d7
- https://github.com/jacobkrantz/VLN-CE/tree/rxr-habitat-challenge
- https://embodied-ai.org/cvpr2023/
- https://aihabitat.org/challenge/2021/ ; https://eval.ai/web/challenges/challenge-page/802/leaderboard/2195
- https://arxiv.org/abs/2210.06849 (Retrospectives on the Embodied AI Workshop)
- https://arxiv.org/pdf/2410.19697 (IPPON; ObjectNav 2023 table)
- https://arxiv.org/abs/1707.01825 and https://users.wpi.edu/~jrwhitehill/AAAI2018WorkshopTalk.pdf (Whitehill)
- https://arxiv.org/abs/1502.04585 (Ladder); https://arxiv.org/pdf/1706.02733 (Shaky ladder)
- https://arxiv.org/abs/2105.08266 (Label inference from log-loss)
- https://arxiv.org/abs/2311.02817 (Safe-VLN); https://arxiv.org/html/2610.14682 (VLN-Safe)
- https://www.codabench.org/competitions/18135/ (not reachable from here)

**Background, not re-verified this session:** ILSVRC-2015 Baidu ban; PetFinder.my 2020 disqualification; DFDC 2020 disqualification; Netflix Prize 2009 tie-break; Roelofs et al. NeurIPS 2019 meta-analysis (little adaptive overfitting across 120 Kaggle competitions when a private split exists); Dwork et al. 2015 reusable holdout; Erdős–Rényi 1963 and Lindström 1964 coin weighing; BARN Challenge (ICRA 2022/23) reports.
