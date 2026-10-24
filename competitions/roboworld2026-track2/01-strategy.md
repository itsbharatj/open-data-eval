# RoboWorld 2026 Track 2 (HA-VLN 2.0) — winning strategy

Version 1.1 · 2026-10-24 (evening) · 37 days to the Phase 2 deadline (Nov 30) · final ranking is decided ONLY by Phase 2 (test, 3,408 episodes).
Companion files: `00-competition-facts.md` (verified facts), `research/` (agent findings), `briefs/` (hand-off briefs per workstream),
`havln_tools/` (scorer, contract validator, grouping; 13 passing tests), `benchmarks/score_landscape.md`.

---

## 0. The thesis in one page

1. **The score is a product of two things we control separately.** `Score = 100 · Nav · (0.70 + 0.30 · Social)`.
   `Social = 1` exactly when the tape has **zero** navmesh contacts (walls *and* humans both count — verified in code; the CMA
   baseline loses ~15 steps per episode to wall-sliding and ends at Score 12.9). `Nav = 0.8·SR + 0.2·3/(3+NE)` and
   `SR` requires stopping within 3 m **Euclidean** *and* zero contacts. One SR percentage point is worth 0.8 Score; 0.1 m of NE
   is worth about 0.2–0.3; every 0.01 of collision rate costs about 0.2. **Collision-free execution is a 30 % multiplier and a
   precondition for every success**, so it is engineered first and verified exhaustively.

2. **Scoring is offline replay of an action tape, so all computation happens on our machines.** The agent can think for minutes
   per step, use frontier VLMs, run many rollouts, build maps from depth + GPS/compass, and rotate in place for panoramas. The
   only external constraints are the 500-action budget and the rules on *what information* the agent may read.

3. **The organizers have written (not yet merged) the rules they intend.** Branch `bohan/clarification-Oct14` of the toolkit
   (verified in git) defines the agent input as episode id, start pose, instruction, **ongoing pose (GPS+compass)** and
   **sequential egocentric RGB-D from one forward camera**; it **prohibits reading `human_motion.json` at inference**, forbids
   extra cameras (panoramas only by turning, which costs budget), **allows pretrained models, external datasets and closed-source
   APIs**, and forbids training on val/test. Top-5 teams must deliver a technical report and may be asked for code.
   => **Our submission of record must be a compliant closed-loop agent.** Privileged information (scene mesh, navmesh, human
   placements, GT goals) is used only for training data, local evaluation, and aggregate regression testing.

4. **Within the compliant regime we still hold three decisive advantages:**
   - *Unlimited test-time compute.* Many rollouts per episode (seeds, prompts, model variants), frontier-VLM reasoning per step,
     and selection by **self-consistency** of stop positions plus **GPS-detected contact** (position delta < 0.25 m after a
     MOVE_FORWARD means the step was filtered → a collision happened; GPS is explicitly allowed). No GT is needed for selection.
   - *A depth+pose occupancy map makes zero collisions achievable.* The agent is a 0.1 m cylinder; the navmesh is already eroded
     by 0.10 m; humans are static-ish meshes visible in depth (median movement 0.03 m, p90 0.8 m). A local 5 cm grid with
     0.25–0.35 m inflation (0.6 m around detected people), heading alignment before straight runs, and a per-step forward check
     removes the wall-hugging that destroys learned agents. Published analysis: 38–57 % of "successful" R2R-CE episodes contain
     wall contact; a training-free collision guard recovers 7–29 SR points under blocking.
   - *Structure of the test set.* Test episodes 3k+1..3k+3 are the three instructions of ONE trajectory (verified from the
     public collision baseline file: identical values in 1,136/1,136 blocks; same start pose). The discrete `R2R_test.json`
     (1,391 paths, start viewpoint + heading + 3 original 29-word instructions) is public and already in the HA-VLN repo.
     Using the sibling instructions jointly is a test-*input* trick, not a GT leak; we will ask the organizers and run it only
     if allowed (expected gain: several SR points).

5. **Expected outcome.** (Clean configuration ≈ Score 40–50; with the gray levers approved ≈ 50–65.) Published HA-VLN-CE state of the art is SR 0.17–0.24 (BEVBert/ETPNav retrained, HCSG May 2026); the
   baseline is 0.129 / Score 12.9. A compliant agent built as below targets **SR 0.50–0.65, NE 2–3 m, CR≈TCR≈0 → Score 50–65**,
   which would be first by a wide margin unless another team fields an offline privileged planner (Score 75–90). That risk is
   covered by (a) getting the clarification merged/confirmed publicly (we ask, in writing, today), and (b) keeping a privileged
   planner ready as the **only-if-explicitly-allowed** Track B. Headroom check: an oracle-goal, zero-collision tape scores ~95.

---

## 1. What is fixed and what is uncertain

| Fixed (verified) | Uncertain (ask organizers today; see §7) |
|---|---|
| Replay scoring in Habitat 0.1.7 image; six actions; 500 cap; STOP required (<500). Two image digests exist (toolkit `e1a0544f`, HA-VLN README `78a62cd1` = `cr-domain-20261004`, +33 KB layer) | Whether the Oct-14 clarification is binding (it is the organizers' written intent; assume **yes**) |
| Collisions = Habitat `previous_step_collided` per step = any navmesh-filtered MOVE_FORWARD (walls + humans) | Whether sibling-instruction sharing and public R2R test instructions are permitted |
| Humans = static objects per animation frame; frame advances by wall clock (0.1 s), freezes after ~12 s; order of frames in official replay is unknowable | Whether the Phase 2 bundle ships test-scan human placements (needed by **anyone** to simulate humans locally) and `trajectory_id` |
| TCR_ep = max(0, count − baseline); baseline file for test is public (93 % zeros) | Official scorer speed (which frames are active) — irrelevant if tapes are collision-free under all frames |
| Success/NE are 3-D Euclidean (override in `HASimulator/measures.py`) | Exact `/opt/havln-challenge/scoring` behaviour — read it on day 1 inside the image |
| Test = 1,136 trajectories × 3; 18 R2R test scans. The public R2R-CE v1-2 test file (YicongHong/Discrete-Continuous-VLN) carries the **same episode ids, scene, start pose and original 26-word instruction for all 3,408 test episodes** (ids match in all four splits incl. train's 18 gaps). Index shipped in `data/test_episode_index.json` | CodaBench outage (down since Oct 21) → Phase 1 calibration window may vanish; deadline boundary probably **Nov 30 15:59 UTC** (midnight UTC+8, per the toolkit's earlier README) |
| Val splits contain GT goals/paths → Phase 1 leaderboard is meaningless; use it only to calibrate our local scorer | Matterport3D approval latency (anecdotally weeks) — zero-float item |

---

## 2. Two tracks, one gate

**Track A — Compliant closed-loop agent (submission of record).** Inputs at inference: instruction, start pose, GPS+compass,
forward RGB-D. Everything else is forbidden *at inference* but allowed for training/eval.

**Track B — Privileged offline planner (shadow track).** Full scene mesh/navmesh, human placements, exhaustive candidate-goal
search over the MP3D connectivity graph with discrete-VLN proposers (ScaleVLN/SRDF reach 80–85 SR on R2R test), VLM reranking,
collision-free planning and kinematic verification. Expected Score 75–90. **Submit only if the organizers explicitly permit
map/human-privileged offline planning in writing.** Otherwise Track B is used as (i) the oracle upper bound and failure
analysis for Track A, (ii) the expert for DAgger data, (iii) the regression harness.

**Ground-truth leak policy.** `research/B12*` found that a public file in the original Matterport3DSimulator repository
(`web/app/sample_room_paths.json`) contains full paths for 366 R2R test path_ids, covering 879 of the 3,408 Phase-2 episodes. That is
test ground truth. We do not use it, every pipeline blocks it by hash, and we recommend informing the organizers privately before
Oct 30 so the leaderboard stays meaningful (and so no rival gains 25 % of the test set for free).

**Compliance tiers (`research/C3*`, principle "information locality": an episode's actions may depend only on its own inputs,
on observations bought by actions in its own submitted sequence, and on what was learned beforehand).**
*Clearly allowed:* the closed-loop RGB-D+GPS agent; unlimited compute per step (incl. sampling several model outputs at the same
state, world models); bump detection from a short GPS displacement within a run; privileged teacher data on the 61 train scans
(exclude the 11 val_unseen scans, whose humans are public); external models/data; closed-source APIs; val for aggregate model
selection; local replay of test tapes for format/determinism only.
*Gray — ask first, off by default:* several local rollouts per episode with self-consistency selection (≈ +9–15 Score); memory across
episodes of the same building / pre-exploration (≈ +8–14); sibling-instruction sharing (≈ +5); changing camera resolution/FOV/height;
training on renderings of test buildings.
*Prohibited:* human placements or simulator human state at inference; look-ahead or virtual cameras; nav-graph/mesh/navmesh/MP3D
annotations of test buildings at inference; the public original R2R test instructions (to confirm); picking or editing individual test
tapes using GT or local replay; leaderboard probing or multiple accounts; public test-side annotations (`collision_num_test.json`,
HA-VLN-1.0 test humans); any human in the loop on test episodes.
=> The **clean configuration** = single-rollout compliant agent with the safety executor and per-step compute. The gray levers are
engineered behind feature flags and switched on only with a written organizer answer; **if no answer by Nov 7, freeze the clean
configuration.** Ready-to-post question text: `03-organizer-questions.md`.

**Gate G-rules (by Oct 28):** written organizer answer. Default if silent: Track A, clean configuration.

Why the default is Track A even without an answer (from `research/B8-*`): the clarification is open **PR #2** on the official
toolkit, authored by organizer Bohan Xiong on Oct 14; the lead organizer's previous social-navigation track (RoboSense 2025)
banned global maps and privileged information, required code for final submissions, audited code before awards, and
disqualified teams that accessed extra environment information. A privileged tape set would also be statistically conspicuous
(Score 75–95 against a field at 20–50) and visible in the action sequences themselves. The innovation award in that track went
to a *named module* (collision-risk prediction with nearby humans) on the 2nd-place team, so a clearly named safety/foresight
module matters more than raw rank for the Best Innovative Solution certificate.

---

## 3. Track A architecture (what the agents build)

```
instruction ──► Instruction parser (LLM) ──► landmark/turn/stop program + human mentions
                                                          │
RGB-D + pose ──► Perception: depth → local occupancy (5 cm), person detector/segmenter (YOLO-seg / OWL-ViT / VLM),
                 room/object tags (VLM or CLIP) ──► Egocentric semantic map + topological memory (nodes = visited poses)
                                                          │
                 System 1 policy proposals: fine-tuned monocular VLA (SimpleVLN-Qwen3.5-9B or StreamVLN/NaVILA),
                 ETP-R1-style waypoint agent fed by in-place rotation panoramas at decision points
                                                          │
                 System 2 (frontier VLM, slow): choose among frontier waypoints, decide STOP, re-plan on blockage
                                                          │
                 Safety executor: plan on inflated occupancy grid → 15°-quantised headings → per-step forward check;
                 never issue a MOVE_FORWARD whose 0.25 m segment is within margin of an obstacle; GPS post-check
                                                          │
                 K rollouts per episode (seeds/prompts/models) → self-consistency + contact-free selection → tape
                                                          │
                 havln_tools contract validation → ZIP → (local replay for aggregate metrics only) → CodaBench
```

Design rules that fall straight out of the code reading (see `research/A2*`):
- Only MOVE_FORWARD can collide; turns/looks/STOP are free. If the start pose is inside an obstacle hole, **begin with a TURN**
  (free re-snap), never with a forward.
- Keep every 0.25 m forward segment ≥ 0.15–0.20 m from any perceived obstacle; stay centred in corridors; align heading before
  straight runs; treat detected people as 0.6 m radius discs (covers animation drift for >90 % of humans).
- Budget: typical paths need 40–80 forwards; one 360° sweep costs 24 turns; plan ≤ 6 sweeps per episode and reserve 60 actions.
- Human clock (`research/A3*`): the official fast replay most likely shows humans at early animation frames (≤ ~20), while a slow
  local agent sees frames 110–119 (movers differ by up to 3 m). Run local rollouts on a virtual human clock matched to fast replay
  and give detected people two-sided motion margins (0.6 m disc covers > 90 % of humans; only ~8 % of paths are timing-sensitive).
- STOP must be issued (success requires it); stop at the point that maximises P(within 3 m) given the agent's goal belief.

Backbone ranking for the compliant agent (evidence in `research/B2*`, `B3*`, `A6*`): (1) **NavGPT-3 8B** (Oct 2026; public
weights; Habitat 0.1.7; exactly our 0.25 m / 15° / 0.1 m-radius action space; SR 76.9 alone and 79–81.5 with a frontier
planner on the full R2R-CE val_unseen) — monocular, so no panorama budget; (2) **SimpleVLN Qwen3.5-9B RL** (76.7; single
camera; vLLM-served; Habitat 0.3.3 side-env needed); (3) **ETP-R1** (65.3; 0.1.7-native; needs 12 views → an in-place sweep
of ~28 turns per decision point, affordable ≤ 5 times per episode); (4) StreamVLN / NaVILA / OmniNav as ensemble diversity.
Measured on vln-safe's logs (same physics as our scorer, human-free R2R-CE val_unseen): collision-free success ETP-R1 37.7
(raw 64.6), StreamVLN 34.4, ETPNav 34.0, OmniNav 29.1, CMA 17.8; a training-free depth guard lifts ETP-R1 to 50.1 and a
navmesh-aware guard to 61.3. **At least one of ETP-R1 / StreamVLN / OmniNav stops within 3 m in 87 % of episodes** (91.5 % with
six agents) while the best single agent manages 67.5 % → rollout diversity plus good selection is where the SR comes from.
Instruction handling: HA-R2R text is ~140–170 word-pieces; ETPNav truncates at 80 and ETP-R1 at 150 (the stop clause is lost) —
raise limits or feed an LLM-condensed route-only paraphrase alongside the original.

Selection evidence (`research/B4*`, `B3*`): voting across the 3 instructions of a path gave +6–7 SR for Airbert/VLN-BERT; when
all three agree (51 % of paths) the answer is right 89.7 % of the time vs 34.8 % when none agree — agreement is the
calibration signal that tells us where to spend frontier-VLM calls. Comparative judging (pick among candidates) beats absolute
yes/no judging by a wide margin. A stop chosen as the most-covered candidate, without reading the instruction, already succeeds
41.6 % of the time on the HA-VLN-1.0 val proxy (CMA: 12.9).

Humans (`research/B6*`): the human-free shortest path passes within 0.5 m of a person in ~41 % of val episodes, so avoidance runs
every episode; a hard 1 m margin is infeasible on 25–32 % of trajectories → use a hard scoring-safe inflation (0.25–0.35 m walls,
0.6 m people) plus a *soft* 1 m proximity cost. One success is worth 0.0235 Score; an extra collision in an already-failed
episode costs only 0.004–0.007, so when the only route passes a person, attempt it if P(contact) < ~0.8 and the goal is beyond.

Training (allowed): DAgger/IL on the 10,819 HA-R2R train episodes with a **privileged collision-free expert** (planned on an
inflated navmesh with humans inserted) so the policy learns human avoidance from supervision; RL fine-tuning with reward
= success ∧ zero contacts (SimpleVLN showed +7–10 SR from RL on R2R-CE). Val splits are evaluation-only.

Test-time compute (allowed): K = 8–32 rollouts per episode; cluster stop positions; prefer clusters with contact-free tapes;
tie-break by a learned success verifier trained on train-split rollouts (inputs: the agent's own observations and the instruction).

---

## 4. Track B architecture (shadow / oracle / only-if-allowed)

1. Candidate goals = MP3D connectivity nodes 3–6 hops and 5–25 m from the start (median 24 nodes, ~8 three-metre clusters).
2. Proposers: ScaleVLN DUET CLIP-H/14 (80/70 test), SRDF (~85 SR), NavGPT-2 XXL, MAGIC-L — all public with precomputed features
   for the 18 test scans; run greedily, with beam search, and exhaustively over simple paths; instruction de-paraphrased to R2R
   style and/or original R2R instruction retrieved via start pose + text match.
3. Human anchors: instruction human-activity sentences paraphrase annotated category strings → direct spatial anchors.
4. VLM judge over rendered panoramas along top-k paths; fuse by rank voting; ensemble over the 3 (or 6) instructions per trajectory.
5. Planner: swept-volume navmesh (all 120 frames of every human inserted, agent radius 0.30) → waypoints → quantised actions →
   exact kinematic replay against all 121 navmeshes (base + 120 frames) → zero flagged steps → STOP.
Expected (`research/B4*`, `B3*`): goal top-1 within 3 m ≈ 85 % (78–90) from HA-R2R instructions, ≈ 88 % (83–92) if the original
R2R instructions may be added → Score ~80–87 with zero collisions. Room type is the strongest semantic cue (matching the goal's
room label cuts candidates ~6×; 59–71 % of paths name the goal room in at least one instruction); public room labels exist for 76 %
of test-scan viewpoints and REVERIE object boxes for all 1,971 test viewpoints (`research/A9*`), but **none of this test-scan
material is usable at inference under the Oct-14 rules** — it is for Track B and for training a room classifier on train scans.

---

## 5. Workstreams, owners, and definition of done (details in `briefs/`)

| WS | Name | First deliverable (date) | Done when |
|---|---|---|---|
| W0 | Ops & organizer liaison | Register; file the 5 questions (Oct 24); MP3D requests ×3 | Written rules answer; MP3D data on disk |
| W1 | Data & infra | Image pulled; `/opt/havln-challenge` dumped & diffed; navmesh cache; replay farm (Oct 26) | Local scorer reproduces CMA README numbers; 3,408-episode replay < 30 min |
| W2 | Safety executor | Depth+pose occupancy planner with per-step guard (Oct 28) | Oracle-goal run on val_unseen: SR ≥ 0.95, TCR = 0 under 4 human-timing regimes |
| W3 | Perception & grounding | Person/room/object tagging; instruction parser; landmark program (Oct 29) | Human-mention → detected-person matching ≥ 0.8 on val_unseen |
| W4 | Policies | ETP-R1 port (control mode, no teleport), SimpleVLN/StreamVLN side-env, DAgger data (Nov 3) | Closed-loop val_unseen SR ≥ 0.40 with TCR ≤ 0.02 |
| W5 | Test-time compute & selection | K-rollout harness, self-consistency, verifier (Nov 8) | +5 SR over single rollout on val_unseen |
| W6 | Verification & submission | Contract validator (done), 4-regime replay, submission ledger (Oct 27) | Every candidate ZIP: PASS + TCR 0 on all regimes |
| W7 | Track B shadow + report | Candidate-goal enumerator, proposers, oracle analysis; technical report skeleton (Nov 6) | Oracle numbers feed W4/W5 error analysis; report draft by Nov 25 |

Parallelism: W0–W3 and W7 start now (no MP3D needed for most of W3/W7 code); W1 unblocks W2/W4/W6 once MP3D arrives (fallback:
start the executor on the public connectivity graphs + synthetic box scenes). Suggested agent count: 2–3 per workstream, with one
integrator; beyond ~16 concurrent coding agents the merge/queue overhead dominates (see `research/C5*`).

---

## 6. Timeline and gates

| Date | Gate | Acceptance |
|---|---|---|
| Oct 24 | G0 | Registered; questions filed; MP3D requested; image pulling; repo scaffold pushed |
| Oct 26 | M1 | Container boots; `/opt/havln-challenge` read; `havln-validate` PASS on STOP-only ZIPs; scorer spec frozen |
| Oct 28 | M2 | (MP3D) val_unseen navmesh cache; STOP-only replay matches prediction; CMA export reproduces README |
| Oct 29 | M3 | Oracle-goal executor SR ≥ 0.90, TCR 0 on val_unseen; Phase 1 calibration submissions if CodaBench is up |
| Oct 30 | M4 | Phase 2 bundle inventoried (human placements? trajectory_id?); test navmesh cache built; submission #1 (STOP-only anchor) |
| Nov 6 | G5 | Closed-loop v1 on test (Score ≥ 35); Track B oracle numbers on val_unseen |
| Nov 13 | G6 | v2 with fine-tuned policy + guard (Score ≥ 50) |
| Nov 20 | G7 | Architecture freeze; test-time-compute scaling; Score ≥ 58 |
| Nov 27 | G8 | Final candidate uploaded and scored; 3-day buffer for CodaBench outages; no new experiments after. Treat the close as **Nov 30 15:59 UTC** until the live site says otherwise |
| Dec 1–8 | — | Technical report, reproducibility pack, code for verification |

Submission budget (`research/A12*`): 100 per phase and 5 per UTC day, counted **per user account** → one submitting account per
team; failed submissions are free, cancelled/stuck ones count (never cancel a slow job; escalate with the id); best score is
retained automatically, ties go to the earlier upload; our own scores are visible to 10 decimals through the API. Plan ~20–30
reproducible full-system uploads plus the STOP-only anchor; **no leaderboard probing** — it would be detectable, would break
PR #2's spirit and the technical report, and is worth only +2–8 SR (`research/B7*`).

---

## 7. Questions to the organizers (file today as one GitHub issue + Discord post + email)

1. Is the Oct-14 clarification (single forward RGB-D camera, GPS+compass allowed, no `human_motion.json` at inference) the
   binding rule set for Phase 2? Will it be merged into the README?
2. May an agent use the three instructions that share a start pose jointly, and the public R2R test instructions?
3. Will the Phase 2 bundle include human placements for the 18 test scans (required to simulate humans locally) and
   `trajectory_id`? Is `collision_num_test.json` the scoring baseline?
4. Is offline computation of tapes with full scene geometry (navmesh planning) permitted, or must planning use only perceived
   geometry? (This decides Track B.)
5. Given the CodaBench outage since Oct 21: will Phase 1/2 dates shift, and is there an alternate submission channel? Exact
   Phase 2 close time (UTC)?
6. May the single forward camera's resolution/FOV be changed, and may the agent keep memory across episodes of the same building?
7. May `collision_num_test.json` (public) be read at inference? (It encodes a human at the start/goal viewpoint for 237 episodes.)

---

## 8. Risk register (top 10; full list in `research/C2*`)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MP3D approval lags weeks | Med–High | Blocks sim work | 3 requests today incl. individual maintainers; lab licence; mesh-free dev on connectivity graphs + synthetic scenes |
| Bundle omits test-scan human placements | Med | No local humans → collisions | Conservative inflation; HA-VLN-1.0 human priors (70 humans in test scans public); depth perception still sees them in official replay? No — if not shipped, nobody can render them; ask Q3 now |
| Another team fields privileged offline planner | Med | They score 75–90 | Get rules confirmed publicly (Q1/Q4); keep Track B ready; report transparency |
| Official human frame ≠ local frame | High | Rare extra contacts | 0.6 m person margin; multi-regime replay; avoid passing within 1 m of people when possible |
| CodaBench down through deadline | Low–Med | No submissions | Email organizers; keep final ZIP ready by Nov 27; ask Q5 |
| Wall contacts from quantised headings | Med | SR→0 for episode | Per-step guard, centreline following, GPS post-check and re-plan |
| 500-action overrun from panorama sweeps | Med | Episode fails | Budget planner: ≤ 6 sweeps, reserve 60 actions, monocular policy as default |
| Instruction style (112-word LLM text) breaks pretrained policies | High | −10–30 SR | Fine-tune on HA-R2R train; LLM de-paraphrase to route-only text; ensemble both |
| Overfitting to val_unseen | Med | Test surprise | Val scenes ≠ test scenes; hold out 3 val scans; no prompt tuning on test text |
| Technical-report/code audit | Med | Award loss | Compliance manifest per submission; privileged tools isolated behind an `oracle` package never imported at inference |
| Public R2R test-path leak (879 episodes) used by rivals | Med | Contaminated leaderboard | Never use it (hash-blocked); disclose privately to organizers; our report states the policy |

---

## 9. Handing this to agents

Each brief in `briefs/` is self-contained: goal, inputs, pointers into `research/`, interfaces (JSON), tests to run, definition of
done, and what to report. Every agent must: (1) read `00-competition-facts.md`; (2) never import privileged data in inference
code paths (`oracle/` package only); (3) validate every ZIP with `havln_tools`; (4) log experiments in `RESULTS.md` with the
config fingerprint; (5) treat val_unseen as the only test proxy and never touch test instructions for prompt tuning.

---

## 10. Competitive landscape (from `research/A7-competitor-intelligence.md`, 2026-10-24)

Only one public Track-2 competitor exists (bingchengzhang/HA-VLN, ZJU, created Oct 21: YOLOv8-seg people, per-floor 2.5-D map,
grid-search candidate routes, Qwen2.5-VL-7B QLoRA chooser; reported SR 0 on 20 val_unseen episodes; already follows the Oct-14
rules). Published HA-VLN-CE state of the art: HCSG (May 2026) SR .24 / CR .36 / TCR 5.0 ≈ Score 23; BEVBert ≈ 19; ETPNav ≈ 17;
CMA baseline 12.95. Public ports of StreamVLN and InternNav/DualVLN to HA-VLN exist, so fine-tuned-VLA teams are plausible.
Camera tilt for LOOK actions is 30° in the challenge config; a maintainer confirmed in UWMILab issue #17 that wall sliding counts.

| Approach a rival might field | Estimated Score |
|---|---|
| CMA baseline / ported ETPNav-type agent | 13 / 18 |
| HCSG-class social agent | 23 |
| Graph agent + collision guard | 32 |
| Fine-tuned VLA + guard | 40 |
| Frontier-API agent + guard (allowed by FAQ Q12) | 47 |
| Multi-rollout test-time selection | 52 |
| Privileged offline planner (needs explicit permission) | 66–90 |

Rough simulation: best rival's median Score ≈ 30, P(best rival ≥ 50) ≈ 0.16. **A compliant entry at Score ≥ 52 (SR ≥ .55, CR ≤ .1)
wins about 85 % of the time; each +0.01 SR adds ≈ 0.74 Score.** Competitor failure modes to design out: getting stuck inside
inflation zones, STOP rejected because depth hit a background wall, instruction truncation at 256 tokens, 24-turn spins eating the budget.


---

## 11. Assets shipped in this folder (ready for the agents)

| File | What it is | Source |
|---|---|---|
| `data/test_episode_index.json` | 3,408 rows: episode → trajectory, scan, start pose (v1-2 rotation + predicted v1-3 yaw), R2R start viewpoint, original R2R instruction; plus the 255 dropped R2R test path ids | `research/A1*` (public R2R-CE v1-2 test file + R2R_test.json) |
| `data/test_trajectory_table.json` | per test trajectory: start viewpoint, 3 original instructions, nav-graph goal candidates (3–6 hops, 5–25.5 m) with room labels | `research/A9*` |
| `data/mp3d_test_scan_room_labels.json` | decoded room-type labels for 1,539 test-scan panoramas (public MP3D region-classification task data) | `research/A9*` |
| `data/collision_num_{val_seen,val_unseen,test}.json` | released per-episode collision allowances (= humans at start/goal viewpoint in 89–93 % of cases) | HA-VLN repo; `research/B6*` |
| `benchmarks/havln_score_ref.py` | reference aggregator reproducing 16.5094500 from integer counts | `research/A4*` |
| `havln_tools/` | Score (official CR formula), contract validator, path grouping; 15 tests | this repo |

Compliance note: the test-scan assets above are **privileged at inference** under the Oct-14 rules. They serve Track B,
oracle analysis, and the organizer questions — not the compliant agent's inference path.
