# Research digest — one screen per topic

Each entry condenses the agent report in `research/<id>.md` (full evidence, numbers, sources there). Status 2026-10-24 evening;
entries marked *pending* are being written.

## Mechanics

**A1 Episode format & test split.** HA-R2R episode = VLN-CE `VLNExtendedEpisode`; the Phase-2 file will carry id, trajectory_id,
scene, start pose, instruction and no goals. Test ids 1..3408 are triples per trajectory (1,136 trajectories; 788 distinct starts, so
group by id triple, not pose). The public R2R-CE v1-2 test file (Discrete-Continuous-VLN repo) has the same ids, scene, start pose
and the original R2R instruction for every test episode; v1-3 yaw = round30(360° − R2R heading). Goal candidates: nav-graph nodes
3–6 hops / 5–25.5 m from the start contain the true goal in 5,798/5,798 train+val paths; median 25 candidates (~9 clusters at 3 m).
Asset: `data/test_episode_index.json`.

**A2 Collision semantics.** A step is flagged iff it is a MOVE_FORWARD whose navmesh-filtered displacement is < 0.24998 m
(`collided = |filt−start|² + 1e-5 < |end−start|²`). Sliding along a wall flags every step. Turns/looks/STOP never flag; a turn
re-snaps an off-navmesh agent for free. Agent 0.1 m radius / 1.5 m; navmesh eroded 0.10 m; humans are static objects baked into
per-frame navmeshes (0.2–1.6 m body band). 4–6 % of starts lie within 0.5 m of a human. Guarantee zero collisions by planning on
an inflated (0.25–0.30 m) swept-volume mesh and verifying kinematically against all 121 navmeshes; begin with a TURN at crowded starts.
v2 additions: step 1 always injects humans (the 120-slot queue caps the counter, so a slow reset never skips them); `collision_num`
leaks the goal — when non-zero, 98 % of train/val_unseen episodes have a human within 3 m of the goal (a prior for the 237 test
episodes, privileged under the Oct-14 rules); human positions in the data are body-box centres ~0.84 m above the floor; open risks:
the image's "patched Habitat core" is unknown and the organizers' navmesh cache is keyed only by scan and frame.

**A3 Human timing.** Frame at step k = thread ticks since reset − 1 (0.1 s ticks, only while the GIL is free; capped at 120 by the
queue; never loops; freezes at the last applied frame). Under fast official replay (~5 ms/step) humans stay at frames ≤ ~10–20
(a 500-action episode reaches ~26); a cold navmesh cache makes frames advance ~1 per action; any ≥ 12 s stall shows frame 119.
Slow local agents (VLMs, CMA) see frames 110–119 — for movers, frame-10 vs frame-119 positions differ by p90 0.74 m, max 3.1 m.
Horizontally 75 % of humans never move; 18.7 % sweep > 0.5 m, 6.3 % > 1 m; rotation never changes; blocking all 120 frames adds
~29 % blocked area. Only 8 % of val_unseen reference paths are timing-sensitive; 31 % cross a standing human at every frame.
Compliant consequence: run local rollouts on a **virtual human clock matched to fast replay** (early frames) and keep two-sided
motion margins around detected people; privileged tapes are certified against all 121 navmeshes.

**A4 Metrics.** CR = (#episodes with ≥1 adjusted collision over all episodes) / human-influenced count (682 / 1,593 / 2,859); SR, NE,
TCR over all episodes. Only this formula rebuilds all four published Scores from integer counts (val_seen SR 140/778, CR 425/682,
TCR 10679/778 → 16.5094500). With zero collisions Score = 80·SR + 60/(3+NE). STOP-only probe predicts ≈ 8.47 (Euclidean) vs ≈ 5.04
(geodesic) on val_unseen. `collision_num` is a 0–4 per-trajectory allowance, unreproducible from public data.

**A5 Action geometry.** MOVE_FORWARD = 0.25 m along body −Z; yaw θ = 2·atan2(q_y, q_w), forward = (−sin θ, 0, −cos θ) (98.8 % of
505k oracle steps match exactly). LOOK angle is 15° by Habitat default, 30° in the VLN-CE six-action RxR config — read the image's
config. **The perfect-goal shortest-path follower itself collides in 18–26 % of episodes** (corner touching at zero clearance), so a
clearance-aware teacher is a legitimate training upgrade. Heading quantisation limits tracking to a ±5 cm corridor (lattice A* over
(position, heading), ~63 actions) — budget is not a constraint (oracle sequences average 55–58 actions, p99 ≈ 100). Plan in 3-D
(13–24 % of episodes change floor). Stop by goal coverage, not commitment: stopping between two candidates 3–5.5 m apart adds
≈ 4–5 SR; if every route needs a collision, stop short (a collision costs ≈ 0.006 Score, 5 m of distance ≈ 0.003).

**A6 Learned-policy options.** The CMA config silently ignores `ckpt_to_load`; the baseline is a from-scratch 10×4 DAgger run with a
sliding-tolerant expert; CMA-class caps at Score 20–27. Ranked options: SimpleVLN (≈37 untuned → 48 fine-tuned → 53 with RL),
ETP-R1 (40–45), StreamVLN (37), NaVILA (34), Uni-NaVid (29–33). Shared fixes dominate: clearance-aware expert, per-step
collision check, RL reward = success ∧ zero collisions, no instruction truncation, rotation-acquired panoramas (~28 turns/decision).

**A7 Competitors.** One public entrant (bingchengzhang, ZJU, SR 0 on 20 eps, compliant hierarchical Qwen2.5-VL agent). Published
HA-VLN-CE SOTA ≈ Score 23 (HCSG). Best rival median ≈ 30, P(≥50) ≈ 0.16; a compliant Score ≥ 52 wins ~85 % of the time.

**A8 Toolkit / scorer / image.** Image ships `havln-score-phase1` and `havln-check-environment` (removed from README on Oct 8).
Two digests: `e1a0544f` (toolkit) and `78a62cd1` (`cr-domain-20261004`, +33 KB layer, probably the CR change). Pull both, diff the
small layers, ask which one CodaBench runs. 20-item verification checklist and first-2-hours plan in the report.

**A9 Test-scan knowledge.** Public room labels for 76 % of test-scan viewpoints (MP3D region-classification task data), REVERIE
object boxes for all 1,971 test viewpoints, `.house` room/door records (custom parser needed). Room type cuts goal candidates ~6×;
59–71 % of paths name the goal room. All of it is privileged at inference under the Oct-14 rules; use for Track B and for a
room classifier trained on train scans. HA-VLN-1.0 humans are a weak prior (35 % overlap, ~1 m offset).

**A10 Paper deep read.** Only the CMA checkpoint is directly comparable (Score 12.9 replay / 11.9 trainer; ±1 Score run-to-run
from wall-clock humans). Published HA-VLN-CE: HCSG .24, BEVBert .21, ETPNav .17, HA-VLN-VL .14 (all with a 12-view rig the rules
now ban). The paper's "within 1 m of a human" TCR is not what the code scores. Cash prize dropped Oct 7; certificates only.

**A11 Data acquisition.** MP3D (academic-only, signed ToU, mailbox anecdotally unattended for weeks) is the only blocker; request
from ≥3 academically affiliated members and chase individual maintainers. Only `mp3d_habitat.zip` (~15 GB, .glb/.navmesh/.house/
_semantic.ply per scan) is needed; press Ctrl-C at the main-dataset prompt. HA-R2R train exists on HF (`HA-R2R/train/train.json.gz`).
Public example scene 17DRP5sb8fy (10 humans) allows bring-up before approval. Local NVMe for the 116,640 HAPS files.

**A12 CodaBench.** Down since Oct 21 (host-university HTTP block, no ETA). Limits per account: 5/UTC day, 100/phase; failed
submissions free, cancelled ones count; best retained automatically, ties to earlier upload; API shows our scores to 10 decimals.
Plan the close as Nov 30 15:59 UTC until confirmed. One account per team; no probing.

## Literature & methods

**B1 Discrete R2R SOTA.** ScaleVLN CLIP-H/14 80/70, SRDF ~85/78 (needs ~1–2 A100-day fine-tune), MAGIC-L 77/69, NavGPT-2 XXL
71.8/60.3 on R2R test; all public with features for the 18 test scans. R2R-CE goals sit on R2R viewpoints (offset p99 0.02 m);
Euclidean 3 m makes ~8 nodes count as success. Projected Track-B Score 76.5 / 81.6 / 86.8 at 80 / 85 / 90 % goal accuracy.

**B2 VLN-CE SOTA.** 2026 native-MLLM policies reach 70–77 SR on R2R-CE val_unseen (SimpleVLN 76.7, Nav-R1, Qwen-RobotNav…);
collision-free success on vln-safe logs: ETP-R1 37.7, StreamVLN 34.4, ETPNav 34.0, OmniNav 29.1, CMA 17.8; depth guard → 50.1,
navmesh guard → 61.3. Union of three agents within 3 m: 87 %. ETPNav/ETP-R1 eval uses `back_algo control` (replayable).

**B3 LLM/VLM planners.** NavGPT-3 (Oct 2026): 8B public weights, Habitat 0.1.7, our action space, SR 76.9 alone / 79.0 with
Claude Opus 5 / 81.5 with GPT-6-Astra as planner on the full val_unseen. Comparative judging ≫ absolute. Most-covered-candidate
stop prior alone succeeds 41.6 %. Human mentions: 60 % within 3 m of the path, 24.5 % within 3 m of the goal. Claude API: no
temperature (since Oct 21) and no logprobs → calibrated scores from local open models; frontier judge for the top 4–6 with shuffles.

**B4 Pre-exploration & ranking.** ~22 candidates per episode, 98.6 % coverage, random pick 22.8 %. Beam search historically +10–19 SR;
rerankers 73–78 test SR; instruction voting +6–7 SR; agreement of all 3 instructions → 89.7 % correct vs 34.8 % when none agree.
Learned rankers are near chance on left/right swaps → add explicit turn-geometry features. Estimated Track-B top-1: 85 % (88 % with
original R2R text).

**B5 Compatibility models.** Goal inference offline is a ~20-way choice (median 19–20 candidates, true goal in the set 98.6 %);
the most central candidate alone gives 48.4 % SR under the 3-D Euclidean test. Perfect reading of single cues would give: first-move
direction 63.7 %, which HA-2.0 humans the path passes 71.7 %, both 77.7 %, room-type sequence 83–85 % (one scan). Compliant agents
cannot tour all candidates (median 792 actions; only 16.5 % of episodes fit in 500) — they can only verify the stop among nodes in
their own map plus 1–3 physically checked alternatives, recovering the 6–8 point "passed near vs stopped at" gap per policy.
VLN-BERT/Airbert rankers (59 % / 69 % val path selection; 60-wordpiece cut) are cheap offline votes only. Invest first in a
DUET-family goal/stop scorer (exposes stop score and forced-path likelihood; fine-tune with graph hard negatives, 256-wordpiece
text and human tokens; retrain on in-sim egocentric renders for the compliant head). 68 % of GT paths pass within one node of an
HA-2.0 human; HA-1.0 test-scan humans (4.2/scan vs 10.4) drop that oracle to 55 %. Fit fusion weights on held-out train scans only.

**B6 Social navigation.** Human-free shortest paths pass within 0.5 m of a person in ~41 % of val episodes; `collision_num` = humans
annotated at the start/goal viewpoint (89–93 %), never more; hard 1 m margins infeasible on 25–32 % of trajectories → hard
scoring-safe inflation + soft 1 m cost. One success = 0.0235 Score; an extra collision in a failed episode ≈ 0.004–0.007.
Waiting (no-op actions) does advance animation via scorer wall-clock, but unreliably.

**B7 Competition case studies.** Offline-submission challenges (RxR-Habitat, ALFRED, AI2-THOR) enforced input rules; Track 3
reproduces winners' code. Phase 2 leaks ~11.7 bits/submission via exact counts (1,173 bits over 100) — enough in principle to
decode much of the goal uncertainty, which is exactly why probing would be detected and indefensible (+2–8 SR realistic). 2022
RxR-Habitat winner (ETPNav team): waypoint predictor + history planner + "tryout" controller (SR 20.9 → 48.6 without sliding),
synthetic pretraining, environment augmentation, snapshot ensembles. Test noise ≈ 0.9–1.5 SR; approach type decides the ranking.

**B8 Innovation angle.** Clarification = open PR #2 (Oct 14). RoboSense 2025 (same lead organizer) banned global maps/privileged
info, audited code, disqualified violators; its innovation award went to a named human-collision-risk module on the 2nd-place
team. Organizers value world-model foresight, egocentric grounding, explicit human modelling. Named modules to build: safety-shielded
executor, human-occupancy foresight model, humans-as-landmarks grounding, Score-aware stopping. Report template needs a method
figure, ablations, a visualization; final rank depends on submitting it.

**B12 R2R test knowledge — INTEGRITY FINDING.** `web/app/sample_room_paths.json` in the original `peteanderson80/Matterport3DSimulator`
repo (the crowd-annotation tool's input, committed 2018) contains full start→goal paths for R2R path_ids 0–1999, i.e. **366 of the
1,391 R2R test paths = 293 ported HA-R2R test trajectories = 879 of 3,408 Phase-2 episodes (25.8 %)**; the test instructions agree
with those paths. Using it would be test ground truth: **we do not use it, we block the file by hash in every pipeline, and the team
lead should tell the organizers privately before Oct 30** (it also protects us from rivals who might use it). Everything else is
clean (heading_info.json, path.json, REVERIE/VLN-CE/FGR2R test). Other results: R2R paths are weighted shortest paths ≥ 5 m with
4–6 edges; R2R-CE kept 81.7 % of test paths, dropping mostly floor-changing ones; goals sit at the viewpoint's floor point (median
offset 0.11 m). Candidate filter 3–6 hops & 5–25.5 m: 100 % recall, median 25 candidates / 7 clusters; 4–6 hops & 5–20 m: 98.5 %,
20 / 6. Instruction-free densest-candidate baseline on val_unseen: SR 0.437, NE 5.1 m (≈ Score 42 with zero collisions) — offline-only.
1,391 test paths have 908 distinct starts; shared-start paths never share a goal.

**B11 Human-landmark grounding.** The activity vocabulary is closed: 749 public humans use 331 category strings and 115 distinct
activities, all verbatim in HA-VLN 1.0's 144-sentence motion-prompt list → matching an instruction mention is a 144-way choice. A
training-free word-overlap + GloVe matcher picks a correct activity for 88–90 % of human-mentioning instructions (96–97 % when
restricted to the scan's annotated humans) and false-fires on only 0.9–2.1 % of human-free ones. In 44–47 % of episodes a human on
the same floor stands within 3 m of the goal; HA-1.0 "End" humans are always within 3 m (median 0.3–0.9 m). The meshes are identical
grey untextured bodies without props ("a couple" is usually one body), so visual activity recognition is unreliable (≈30–43 % top-1);
weight presence, room type and position along the route, use the activity guess as a tiebreaker. Compliant grounding channel = a
person detector on the agent's own frames (exact per-pixel human labels for training via `set_object_semantic_id`). If the Phase-2
bundle omits test-scan human positions, local runs show no humans at all → ask the organizers now.

**B9 Instruction linguistics**, **B10 Augmentation/ensembling** — *pending*.

## Strategy & ops

**C1 Infra.** Deterministic replay scorer = official code with the signal queue swapped for a FrameScheduler (wallclock / throttled /
frozen(k) / all-frames); CPU PathFinder stepper (20–60k steps/s/core) for planning and verification; navmesh cache 10,800 files
(10–50 GB) pre-warmed single-writer and mounted read-only; 24 Habitat processes on 3 GPUs replay 3,408 × 500 steps in ~10 min;
content-addressed caches; Redis job queue; exporter-style fingerprints; dual-mode (privileged/compliant) with an audit manifest.

**C2 Timeline & risks.** Zero-float chain: MP3D → download → navmesh cache → CMA reproduction → scorer calibration → Phase 2.
Outage-independent anchors: reproduce README CMA numbers locally; STOP-only submission with an exactly predictable Score. Gates G0–G8
with acceptance criteria; 23-item risk register; Nov 7 mesh-free fallback trigger; freeze Nov 20; final upload Nov 27.

**C3 Rules**, **C5 Organization**, **C6 Experiments**, **C7 Executor**, **C8 Goal inference**, **C9 Closed-loop plan**, **C10 Tests** — *pending*.
**C4 Leaderboard-feedback math** — not run separately; B7 covers the information-theoretic estimate and the recommendation (no probing).
