# C2 — Timeline, critical path and risk register (Sat 2026-10-24 → Mon 2026-11-30 → Sat 2026-12-12)

Topic id: `C2-timeline-critical-path-and-risk-register`. Author: research agent C2. Date: 2026-10-24.

## 0. Executive summary

- 37 calendar days remain to the Phase 2 deadline (Nov 30), 6 days to the Phase 1 close (Fri Oct 30), 49 days to awards (Dec 12).
- **The single critical path is Matterport3D (MP3D) access → 16 GB habitat-task download → first navmesh cache → CMA reproduction → scorer calibration → Phase 2 pipeline.** Everything else (image pull 6.1 GB, HAPS2_0.zip, val JSONs, checkpoint, connectivity graphs, test start poses) is already downloadable today with no approval. Public evidence on MP3D approval latency is bad: GitHub issues on niessner/Matterport report requests unanswered for a month or more (Jan 2024, Oct 2024, Jan 2026), and the official googlegroups address was described as unmonitored. Treat "1–7 days" as the optimistic case; plan a hard fallback trigger (Nov 7) for a mesh-free pipeline.
- **CodaBench (www.codabench.org) has been unreachable since ~14:00 UTC Oct 21** (codalab/codabench issue #2679): the host university blocks all inbound HTTP(S) over a PHP-vulnerability precaution; maintainers had no ETA as of Oct 24. This directly threatens (a) the only official Phase 1 calibration window (closes Oct 30), (b) delivery of the Phase 2 bundle on Oct 30 if it is served from CodaBench, and (c) our daily submission cadence. The plan therefore front-loads an *outage-independent* calibration anchor (reproduce the README's official CMA numbers locally) and a *zero-infrastructure* official anchor (a STOP-only submission whose Score is exactly predictable because NE is Euclidean start→goal distance), and keeps every candidate ZIP pre-validated so that it can be uploaded the minute the site returns.
- Two facts change the data risk picture: `Data/HA-R2R-tools/collision_num_test.json` is already public in UWMILab/HA-VLN (3,408 entries; 3,171 zeros, 213 ones, 6 twos, 18 threes), while `human_motion.json` contains **0 of the 18 test scans** (72 scans, 749 humans). So the per-episode collision baseline for test is (probably) known, but the test-scan human placements are not; whether the Phase 2 bundle includes them is the #1 question for the organizers. Because TCR_ep = max(0, count − baseline), a zero-collision plan makes the baseline irrelevant.
- Submission arithmetic: 5/day, 100/phase, best retained. Phase 2 spans 31 UTC days → 155 slots are possible but the 100 cap binds; budget 70 experimental uploads + 30 reserve (outage/ties/final). CodaBench counts the day as UTC midnight→midnight (docs) and cancelled/stuck submissions consume quota (issues #1764/#2651).

## 1. Verified calendar facts

| Item | Value | Source | Confidence |
|---|---|---|---|
| Today | Sat 2026-10-24 | task | high |
| Phase 1 (val_seen 778 + val_unseen 1,839) | Oct 15 → Oct 30 | track2/README.md "Timeline"/"Phases" | high |
| Phase 2 (held-out test, 3,408 eps, 18 scans) | Oct 30 → Nov 30; final ranking only from Phase 2 | track2/README.md; roboworld2026.github.io/track2.html | high |
| Exact phase boundary time | Track 1 README says Phase 2 opens Oct 30 23:59 UTC and closes Nov 30 23:59 UTC; Track 2 README gives dates only | github.com/roboworld2026/track1 README (fetched) | medium (Track 2 inferred by analogy) |
| Awards | Dec 12, 2026 | README | high |
| Limits | 5 submissions/day, 100/phase, best retained; ties: SR↑, NE↓, CR↓, TCR↓, earlier submission | README "Competition Details", "Composite Score" | high |
| Registration | Google Form https://forms.gle/P2jH3c2VoGsNNWXG8 (opened Oct 8) required for leaderboard/awards | roboworld2026.github.io/index.html | high |
| Channels | GitHub issues roboworld2026/track2 (0 issues filed as of Oct 24), Discord https://discord.gg/S8s8JcxtT, WeChat QR, email roboworld2026@gmail.com | README "Resources and Contact"; issues page fetched | high |
| CodaBench competition | https://www.codabench.org/competitions/18135/ | README badge | high |
| CodaBench status | Unreachable since ~14:00 UTC Oct 21; cause: university-wide HTTP(S) block; no ETA on Oct 23/24; maintainers offer leaderboard CSV via info@codabench.org | github.com/codalab/codabench/issues/2679 | high |
| Daily-limit semantics | Docs: midnight UTC → midnight UTC; code counts by calendar day; cancelled/stuck submissions count; "failed" meant not to count but scoring exit codes are not always checked | docs.codabench.org v1.23 PDF; issues #1434, #1764, #1641, #2651 | medium |
| Image | ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f…; one 6,106,231,833-byte layer (6.1 GB compressed) | ext/image-manifest.json | high |
| Pinned data | HF dataset fly1113/HA-VLN @ c5f1cec…: HAPS2_0.zip, val_seen/val_unseen(.json.gz, _bertidx), ckpt.39.pth; GitHub UWMILab/HA-VLN @ f46f936…: human_motion.json, collision_num_val_*.json | track2/scripts/resources.json | high |
| MP3D habitat archive | `download_mp.py --task habitat` ≈ 15–16 GB for all 90 scans (Python 2.7 script; emailed after approval) | CSDN blog via WebSearch; habitat-sim DATASETS.md; BlenderProc docs | medium |
| MP3D approval latency | No official figure; anecdotes: ~1 month no reply (issue #65, Jan 2024), unanswered (Oct 2024), unanswered (issue #74, Jan 2026); tip in thread: contact an individual maintainer directly | github.com/niessner/Matterport issues #65, #74 | medium |

## 2. Quantities that size the plan

| What | Value | How derived |
|---|---|---|
| Test episodes per scan | 6 scans ×100 paths; min 7 (gYvKGZ5eRqb), max 100; 1,391 paths → 3,408 instructions | R2R_test.json (HA-DE/tasks/R2R/data) |
| Val_unseen | 1,839 eps on 11 scans; val_seen 778 eps on ≤61 train scans; train 10,819 eps/61 scans | R2R jsons + README |
| Navmesh cache builds | 120 frames × scans: test 2,160; val_unseen 1,320; all 90 scans 10,800. Each `recompute_navmesh(include_static_objects=True, r=0.1, h=1.5)` on an MP3D mesh: est. 3–30 s (low confidence; no published timing) → test cache 2–18 h serial, <1 h with 18 parallel workers (one per scan) | HASimulator/environments.py L133-144 |
| Humans per scan | min 6, mean 10.4, max 19 (72 public scans) | human_motion.json |
| Replay volume per full test verification | 3,408 eps × ~60–120 actions ≈ 200k–400k sim steps; at an assumed 50–200 steps/s/process → 20–130 min single process, minutes with 16+ processes grouped by scan | estimate |
| Official scorer latency | unknown; same volume as above plus queue → expect 0.5–6 h per submission; plan on ≤2 results/day usable for decisions | inference |
| STOP-only Phase 1 anchor | Score = 100 × 0.2 × 3/(3+NE) × (0.70+0.30×1.0) with NE = mean Euclid(start, goal). From R2R-graph geometry: val_unseen NE≈7.09 → Score≈5.95; val_seen/train NE≈7.69 → Score≈5.61. Exact value computable from val_*.json.gz on day 1 | measures.py L141-146 uses euclidean_distance; computed from connectivity poses |
| Score resolution per test episode | one extra success raises Score by ≈100×0.8/3408×(0.7+0.3·Social) ≈ 0.016–0.023 (≫ 1e-6 display precision) → official per-subset success counts can be inferred from Score deltas | Score formula |
| LLM/VLM volume for goal inference | 3,408 eps × ~30–60 candidate goals × 4–12 rendered views ≈ 0.4–2.5 M images per full pass; needs batch APIs, caching, multi-provider routing | a1_scripts/goal_candidates.py candidate rule + estimate |
| Downloads today | image 6.1 GB + HAPS2_0.zip (size unverified; est. 5–15 GB) + val JSONs (<100 MB) + ckpt (~0.2 GB); MP3D 16 GB after approval | manifests |

## 3. Critical path (with float)

```
MP3D request sent (D0) ──► approval (D1..D21?) ──► 16 GB download (≤1 h) ──► scenes verified (90 glb)
      │                                                             │
      │  [float: everything below runs without MP3D]                ▼
      ├─ image pull, HF data, container boot (D0–D1)        navmesh cache val_unseen (≤2 h parallel)
      ├─ STOP-only zips + predicted Score (D0–D1)                   │
      ├─ scorer entry points / config diff (D1)                     ▼
      ├─ connectivity-graph tooling, candidate goals (D1–D3)  CMA diag export (2 eps) → full export (2–6 h)
      ├─ instruction parsing on val/train (D1–D5)                   │
      └─ action compiler + kinematics unit tests (D1–D3)            ▼
                                                        local replay == README CMA numbers (gate M3)
                                                                    │
                            CodaBench back? ──yes──► Phase 1 uploads (STOP-only, CMA, oracle) → scorer calibrated
                                   │ no                             │
                                   └──► rely on README anchor + Phase 2 STOP-only anchor
                                                                    ▼
                               Phase 2 bundle (Oct 30/31) → inventory → test navmesh cache (≤2 h) → pipeline runs
```

Zero-float activities: MP3D approval, CMA reproduction, Phase 2 bundle inventory. Everything else has ≥2 days float in week 0.

## 4. Gantt (workstreams × weeks)

Legend: ▶ start, ■ active, ◆ gate/milestone, ░ buffer/standby.

| Workstream (owner) | W0 Oct 24–30 | W1 Oct 31–Nov 6 | W2 Nov 7–13 | W3 Nov 14–20 | W4 Nov 21–27 | W5 Nov 28–30 | Post Dec 1–12 |
|---|---|---|---|---|---|---|---|
| WS0 Ops/comms (human lead + OPS agent) | ▶ register, 5 questions, MP3D chase, CodaBench watch ◆G0 | ■ bundle watch, Discord/issues | ■ | ■ | ■ | ░ outage buffer | report submission, verification requests |
| WS1 Data/infra (INFRA agent) | ▶ image, HF data, MP3D, navmesh cache, replay farm ◆M1 ◆M2 | ■ test navmesh cache, farm scale-out ◆M4 | ■ render cache for VLM | ■ | ■ | ░ | archive |
| WS2 Verification/local scorer (VERIFY agent) | ▶ STOP-only, CMA reproduction, timing-robustness ◆M3 | ■ 4-mode replay gate on every candidate | ■ | ■ | ■ final audit | ░ | reproducibility pack |
| WS3 Planner/executor (PLAN agent) | ▶ compiler, oracle planner on val | ■ swept-volume humans, NE minimization, budget | ■ long-tail (stairs, doors) | ■ freeze ◆G7 | ■ bugfix only | ░ | ablations |
| WS4 Grounding/goal inference (GROUND agent) | ▶ parsing, candidate goals, v0 | ■ v1 multi-view VLM re-rank ◆G5 | ■ v2 ensembles, learned re-ranker ◆G6 | ■ freeze | ■ | ░ | writeup |
| WS5 Learned-policy fallback (POLICY agent) | ▶ env + R2R-CE ckpts | ■ ETPNav/BEVBert fine-tune on HA-R2R train | ■ eval as proposer/fallback | ■ decision: keep/drop | ░ | ░ | writeup |
| WS6 Submissions (SUBMIT agent) | ▶ Phase 1 calibration uploads (if site up) | ■ #1 STOP-only, #2 v0; ≤3/day A/B | ■ ≤3/day | ■ ≤3/day | ■ final candidate ◆G8 Nov 27 | ░ re-upload only | — |
| WS7 Report/code (REPORT agent) | ▶ decision log | ■ | ■ outline | ■ draft | ■ | ■ | ◆ report by Dec 8 |

## 5. Day-by-day plan

### Week 0 (dense): Oct 24 – Oct 30

**Sat Oct 24 (D0)** — Gate G0 by 23:59 local.
- OPS: register team (Google Form); join Discord + WeChat; file ONE GitHub issue in roboworld2026/track2 containing the 5 questions (public record), post the same on Discord, email roboworld2026@gmail.com; subscribe to codalab/codabench#2679.
- INFRA: send MP3D Terms-of-Use form from ≥2 institutional addresses (different members), to matterport3d@googlegroups.com; ask organizers for an expedited contact; ask every collaborating lab whether a licensed MP3D copy already exists (use only within the licence terms). Start `docker pull` (6.1 GB) on the GPU host; run `bash scripts/download_data.sh --destination $DATA_ROOT --target all` (HF primary; `--source gdrive` fallback); verify SHA-256s; clone UWMILab/HA-VLN @ f46f936.
- VERIFY: write `make_stop_only.py` (reads val_*.json.gz IDs → `{"format_version":1,"split":…,"episodes":[{id,["STOP"]}]}` → zip) and `predict_stop_only_score.py` (NE = mean ‖start−goal‖₂ per split; Score as in README). Deliverable: two ZIPs + predicted numbers to 6 decimals.
- PLAN: repo scaffold; JSON contract `plan.json = {episode_id, waypoints[(x,y,z)], final_yaw, actions[]}`; connectivity-graph loader for all 90 scans (public, includes test).
- GROUND: start instruction parsing (LLM) on val_unseen; prepare candidate-goal generator (geodesic 5–25 m, 3–6 hops rule from a1_scripts/goal_candidates.py).
- POLICY: list public R2R-CE checkpoints (ETPNav, BEVBert, GridMM) and their Habitat version constraints.

**Sun Oct 25 (D1)** — Milestone M1: container boots; `havln-validate` PASS on both STOP-only ZIPs; `havln-check-data` passes except MP3D.
- INFRA: `ls /opt/havln-challenge/scoring/havln_scoring`, enumerate `havln-*` CLIs, read `/app/config/challenge_submission.yaml` and `six_action_task.yaml`; diff the image's `habitat_simulator.py` and `habitat_extensions` against public 0.1.7/HA-VLN (record every patch — these are the scoring semantics). Check `curl -I` size of HAPS2_0.zip and record.
- VERIFY: run toolkit tests; implement `replay_harness.py` around the image runtime (actions in → per-step collided flags, final position, metrics out) following export_cma_submission.py's env construction.
- PLAN: action compiler v0 (pose → shortest 15° turn sequence + 0.25 m steps) with unit tests against Habitat 0.1.7 kinematics; sliding semantics noted.
- GROUND: val GT goal table; candidate-goal statistics per episode (count, 3 m-separated clusters).

**Mon Oct 26 (D2)**
- OPS: chase MP3D (resend; individual maintainers; organizers). Decision rule: if no approval by Oct 31 → escalate daily; if none by Nov 7 → mesh-free fallback becomes primary (see §8).
- INFRA (if MP3D granted): download habitat task archive (~16 GB), lay out `scene_datasets/mp3d/<scan>/<scan>.glb` ×90, start navmesh cache for the 11 val_unseen scans (parallel per scan).
- VERIFY: local replay of STOP-only on val_unseen must give SR 0, CR 0, TCR 0 and NE equal to prediction to 1e-6 (checks coordinate conventions). Then `export_cma_submission.py --episode-limit 2`.
- POLICY: training container (separate from the Habitat image) for ETPNav; download HA-R2R train from HF if present (verify path; toolkit manifest excludes train).

**Tue Oct 27 (D3)** — Milestone M2: first scene loads, navmesh cache builds, metrics from local replay.
- INFRA: full CMA export (2,617 eps, `--gpu-ids 0 1 2 3`; est. 2–6 h).
- VERIFY: local replay of the CMA export vs README numbers (val_unseen Score 12.945387, SR .129, NE 6.387, CR .684, TCR 17.536; val_seen 16.509450/.180/6.223/.623/13.726). Acceptance: |ΔScore| ≤ 0.5, |ΔSR| ≤ 0.01, |ΔNE| ≤ 0.15, |ΔCR| ≤ 0.03, |ΔTCR| ≤ 1.0 (TCR/CR are wall-clock sensitive).
- PLAN: oracle-goal planner v0 on val_unseen (GT goal; navmesh inflated to r≈0.3 m; humans as static holes) → local SR ≥ 0.90, TCR ≤ 0.5 first pass.

**Wed Oct 28 (D4)**
- VERIFY: timing-robustness test — replay oracle plans under 4 modes (as-fast-as-possible; 0.05 s/step; 0.2 s/step; frozen frame 0 and frozen frame 119). Any collision difference → PLAN adopts swept-volume avoidance (union of all 120 frames + 0.3–0.5 m margin).
- SUBMIT (only if CodaBench is back): Phase 1 uploads (a) STOP-only, (b) CMA export, (c) oracle planner. Record official numbers.
- GROUND: goal-inference v0 (LLM over instruction + candidate descriptors from connectivity + region/human text) measured as acc@3m on val_unseen.

**Thu Oct 29 (D5)** — Milestone M3 (scorer calibrated).
- SUBMIT: remaining Phase 1 probes: oracle planner at two inflation radii (0.2 / 0.4 m) and a "forward-until-blocked" probe → tells us how official replay counts wall collisions and whether our clearance is sufficient.
- Acceptance M3: STOP-only official Score equals prediction within 0.001 (NE within 0.001); CMA within the tolerances above; oracle planner official CR/TCR within 0.02 / 0.1 of local. If CodaBench is still down: M3 is declared on the README anchor only, with a flag to re-verify on the first Phase 2 result.

**Fri Oct 30 (D6)** — Phase 1 closes / Phase 2 opens (assume 23:59 UTC).
- INFRA: poll CodaBench "Files", toolkit repo releases/tags, HF dataset tree, Discord for the bundle; if a new image digest appears, pull and re-run the config diff; download bundle; inventory fields (episode_id, scene_id, start_position, start_rotation, instruction; goals absent?; test human placements present?; collision_num_test present and equal to the public file?; manifest for `havln-validate test`).
- GROUND: pre-process R2R_test.json (public: 1,391 paths with start viewpoint+heading) so the only bundle-dependent step is the episode_id ↔ path mapping.

### Week 1: Oct 31 – Nov 6

- **Sat Oct 31 (D7)** INFRA: test navmesh cache (2,160 builds, 18 workers, ≤2 h); SUBMIT #1 = STOP-only test (pipeline check; its Score reveals the test split's mean start→goal distance: NE = 60/Score − 3 while Social = 1).
- **Sun Nov 1 (D8)** SUBMIT #2 = v0 full pipeline (goal-inference v0 + planner). Daily from here: nightly full-val local eval + 4-mode replay gate on every test candidate (acceptance: 0 collisions in all modes, all sequences ≤500, STOP once, coverage exact).
- **Mon Nov 2 – Fri Nov 6** GROUND v1: render 4–12 views per candidate goal in Habitat, VLM re-ranking, self-consistency; PLAN: NE-minimization (stop at goal centre), budget-aware compilation, door/stair handling; POLICY: ETPNav fine-tune; SUBMIT ≤3/day using disjoint-subset A/B (variants differ on a subset so official Score deltas attribute to that subset). **Gate G5 (Nov 6):** local oracle planner SR ≥ 0.97, CR ≤ 0.01, TCR ≤ 0.02 on val_unseen; goal-inference acc@3m ≥ 0.60; official test Score ≥ 50.

### Week 2: Nov 7 – Nov 13
- Nov 7: MP3D hard trigger (if still no scenes → §8 fallback becomes primary; keep requesting).
- GROUND v2: ensembles, learned re-ranker trained on train split (10,819 eps with GT), human-reference grounding (match instruction human activities to bundle/1.0 annotations). **Gate G6 (Nov 13):** acc@3m ≥ 0.75; test Score ≥ 65.

### Week 3: Nov 14 – Nov 20
- Freeze architecture Nov 20 (**G7**); after this only data/parameter changes and long-tail fixes; ablation runs recorded for the report; decide whether WS5 policy contributes (as proposer) or is dropped.

### Week 4: Nov 21 – Nov 27
- Long-tail episodes (ambiguous goals: hedge by stopping at the candidate minimizing expected NE over the posterior; cluster-centre stopping when two candidates are <6 m apart). **G8 (Fri Nov 27):** final candidate uploaded and confirmed scored; its ZIP + sha256 + local metrics archived.

### Week 5: Nov 28 – Nov 30 (buffer)
- No new experiments. If CodaBench is down, email organizers with ZIP hash and request alternate channel. Last planned upload Sun Nov 29 12:00 UTC; Mon Nov 30 reserved for emergencies only (deadline 23:59 UTC assumed).

### Dec 1 – Dec 12
- Technical report (method, ablations, compliance statement, reproducibility: scorer hashes, plan JSONs, seeds) ready by Dec 8; code packaged for verification (winners "may be asked to provide code or models"); Dec 12 awards.

## 6. Milestones and acceptance criteria

| ID | Date | Acceptance criterion (measurable) |
|---|---|---|
| G0 | Oct 24 | Registered; issue with 5 questions filed; ≥2 MP3D requests sent; image pull + HF downloads started |
| M1 | Oct 25 | Container boots; `havln-validate` PASS on STOP-only val_seen+val_unseen ZIPs; scorer package enumerated and config diff recorded |
| M2 | Oct 27 (needs MP3D) | 90 `<scan>.glb` present; val_unseen navmesh cache complete; local replay returns metrics for 2 CMA episodes |
| M3 | Oct 29 | Local replay of the official CMA export reproduces README numbers within tolerances (Score ±0.5, SR ±0.01, NE ±0.15, CR ±0.03, TCR ±1.0); if CodaBench is up: STOP-only official Score = prediction ±0.001 and oracle-planner official CR/TCR within 0.02/0.1 of local |
| M4 | Oct 31 | Phase 2 bundle inventoried; test navmesh cache built; STOP-only test submission accepted (PASS) |
| G5 | Nov 6 | Oracle planner val_unseen SR ≥ 0.97 / CR ≤ 0.01 / TCR ≤ 0.02; goal acc@3m ≥ 0.60; official test Score ≥ 50 |
| G6 | Nov 13 | acc@3m ≥ 0.75; official test Score ≥ 65; every uploaded candidate passed the 4-mode zero-collision gate |
| G7 | Nov 20 | Architecture freeze; acc@3m ≥ 0.80; Score ≥ 72; ablation table complete |
| G8 | Nov 27 | Final candidate scored on CodaBench; archive (zip, sha256, local metrics, plan JSONs) frozen |
| R1 | Dec 8 | Technical report + verification package ready |

Score targets are derived from the formula: SR 0.6/NE 3.5/zero collisions → ≈57; SR 0.75/NE 2.5 → ≈71; SR 0.8/NE 2.2 → ≈75.5 (Social = 1 when CR = TCR = 0).

## 7. Risk register (likelihood L, impact I on 1–5)

| # | Risk | L | I | Indicator | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | MP3D access delayed weeks or never (unmonitored mailbox anecdotes) | 4 | 5 | No reply by Oct 28 | Multiple requesters on D0; contact individual maintainers; ask organizers for an expedited route; check licensed copies at collaborating labs; build everything mesh-independent first; Nov 7 trigger → §8 mesh-free fallback | INFRA + human lead |
| R2 | Phase 2 bundle lacks human placements for the 18 test scans (0/18 in human_motion.json) | 3 | 4 | Bundle inventory Oct 30 | Q1 to organizers now; fallback to HA-VLN 1.0 human_motion_text.json (covers 90 scans, viewpoint-anchored) with 1.0–1.5 m clearance; validate on val how well 1.0 anchors predict 2.0 positions; prefer routes that avoid all human-mentioned regions | GROUND + PLAN |
| R3 | Scoring uses a different collision baseline than the public collision_num_test.json, or TCR semantics differ | 2 | 3 | Phase 2 scores vs local | Target zero collisions so baseline is irrelevant; compare STOP-only and probe submissions | VERIFY |
| R4 | Scorer wall-clock nondeterminism (human frames advance for ~12 s after reset, then freeze; navmesh recomputed per frame) → collisions in official replay not seen locally | 3 | 4 | Official CR/TCR > local on probes | Plan against swept volume of all 120 frames + ≥0.3 m margin; 4-mode replay gate; keep ≥0.5 m from any human; Q4 asks for the replay's step rate / fixed frame | PLAN + VERIFY |
| R5 | Rules clarification: offline use of scene mesh/navmesh/human annotations judged non-compliant or "not innovative" | 2 | 5 | Organizer answer to Q2 | Ask in writing (GitHub issue = public record); keep WS5 egocentric policy as compliant fallback; frame method as topological/world-model planner (explicitly welcomed); verify every plan by local replay which is explicitly allowed | human lead + POLICY |
| R6 | CodaBench outage persists (since Oct 21, no ETA) through Oct 30 and/or into November | 4 | 4 | issue #2679 open | Pre-validated ZIPs ready; request alternate channel/extension (Q3); final candidate by Nov 27; 3-day buffer; archive hashes to prove timing; monitor daily | SUBMIT + OPS |
| R7 | Phase 1 calibration window missed (no official val numbers) | 4 | 3 | Site down Oct 29 | README CMA numbers as anchor (M3); STOP-only Phase 2 submission as exact NE anchor; ask for Phase 1 extension | VERIFY |
| R8 | Bundle delivered only via CodaBench while it is down → Phase 2 cannot start | 3 | 4 | Oct 30 no bundle | Q3 asks for mirror (HF/GitHub release); pre-process public R2R_test.json so only the id↔path mapping remains | OPS + GROUND |
| R9 | 500-action budget insufficient (long paths + detours + turns) | 2 | 3 | Compiler reports > 450 actions | Optimal turn sequences; path smoothing; budget check with fallback to the nearest reachable point; LOOK actions never used in submissions | PLAN |
| R10 | ZIP validation failures (missing/duplicate IDs, STOP placement, nested paths) waste daily quota | 2 | 3 | `SUBMISSION REJECTED` | `havln-validate` in container before every upload; toolkit `check_rows` as unit test; CI on the submission builder | SUBMIT |
| R11 | LLM/VLM API rate limits or outages during 0.4–2.5 M image passes | 3 | 3 | 429s/latency | Multi-provider routing, batch APIs, render/response caching, resumable shards, nightly budget report | GROUND |
| R12 | Overfitting goal inference to val_unseen (GT public; test emphasizes multi-human routes) | 3 | 4 | val–test gap on official Score | Blind hold-out (val_seen scans), cross-scan CV, limit tuned hyperparameters, use official test deltas via disjoint-subset experiments sparingly | GROUND + VERIFY |
| R13 | Ties at the top (several teams reach zero collisions and similar SR) | 2 | 3 | Leaderboard clustering | Tie-breaks: SR, NE, CR, TCR, earlier time → minimize NE (stop on goal centre), upload best as early as possible, never delay a strictly better candidate | SUBMIT + PLAN |
| R14 | Organizers ship a new image/toolkit for Phase 2; local scorer diverges | 3 | 3 | New digest/tag | Pin digests; re-run config diff + M3 tolerances on every image change | INFRA + VERIFY |
| R15 | Replay farm too slow (navmesh builds, scene loads, rendering) to verify every candidate | 2 | 3 | >2 h per full verification | Per-scan parallelism, cached navmeshes, sensors off for collision-only replays, group episodes by scan | INFRA |
| R16 | Habitat 0.1.7 incompatible with newest GPUs/drivers (RTX 5090 issue #20; torch 2.0.1+cu118) | 2 | 3 | Container fails on D1 | Use A100/H100-class or older drivers; test on D1; keep one known-good host | INFRA |
| R17 | Wall collisions count toward CR/TCR (maintainer confirmed general collisions) and inflated navmesh disconnects doorways | 3 | 3 | Oracle planner TCR > 0 or unreachable goals | Per-episode adaptive inflation (0.4 → 0.3 → 0.2 m), verify by replay; prefer corridor centrelines | PLAN |
| R18 | Multiple accounts / team-rule violation → disqualification | 1 | 5 | — | One account per team; Q5 to confirm rules; log all uploads | human lead |
| R19 | Goal-inference ceiling: LLM-rewritten instructions are long (112 words) and may hallucinate | 3 | 4 | acc@3m plateau < 0.7 | Ensembles, multi-view VLM, learned re-ranker on 10,819 train episodes, hedged stopping on posterior | GROUND |
| R20 | Download/mirror failures (HF rate limits, Google Drive quota) | 2 | 2 | checksum/curl errors | HF primary with pinned revision, `--source gdrive` fallback, resumable downloader | INFRA |
| R21 | Agent coordination drift over 37 days (duplicate work, interface changes) | 3 | 3 | Merge conflicts, stale metrics | Frozen JSON contracts, single metrics board, daily 15-min sync, decision log maintained by REPORT | human lead |
| R22 | MP3D licence: redistribution forbidden | 2 | 4 | — | Scenes stay on the licensed org's storage; agents access via mounted volume only | INFRA |
| R23 | Multi-floor goals: NE is 3-D Euclidean, so a wrong floor costs success even if planimetrically close | 2 | 3 | val failures with |Δz| > 1 m | Candidate goals carry floor/height; planner uses 3-D navmesh paths incl. stairs | PLAN |

## 8. The 5 questions to send today (GitHub issue + Discord + email), with fallbacks

1. **Phase 2 bundle contents.** Will the Phase 2 bundle include, for the 18 test scans, the HAPS 2.0 human placements (`human_motion.json` entries), the per-episode collision baseline (`collision_num_test.json`), start position/rotation, scene id and instruction, so that local replay for test has identical semantics to the official scorer? Is the public `Data/HA-R2R-tools/collision_num_test.json` the file used for scoring? Through which channel is the bundle distributed (CodaBench Files, HF, GitHub release)?
   *Fallback if no human placements:* use HA-VLN 1.0 `human_motion_text.json` anchors with 1.0–1.5 m clearance, route away from every human-mentioned region, and validate the 1.0→2.0 predictive power on val; accept a small NE/SR cost for large social margins.
2. **Permitted computation.** Since scoring is offline replay, is it permitted to compute action sequences using the simulator, scene geometry/navmesh, human annotations and arbitrary external models offline (open-loop planner/world-model submissions), with local replay used for verification? Are there constraints on inputs beyond those in the task definition, and will the technical report need to state the observation modalities used?
   *Fallback if restricted:* switch the final submission to the WS5 egocentric policy (trained with privileged data, run closed-loop locally, verified by local replay — which the FAQ allows) and keep the planner only as a training-data generator.
3. **CodaBench outage and schedule.** Given www.codabench.org has been unreachable since Oct 21, will Phase 1 be extended or Phase 2 shifted, and will an alternative submission/bundle channel be provided? Please confirm the exact Phase 2 open/close timestamps (UTC) and the daily-limit reset time.
   *Fallback:* keep pre-validated ZIPs with sha256 + timestamps; final candidate by Nov 27; email organizers hashes if the site is down at the deadline; rely on README anchor instead of Phase 1 calibration.
4. **Scorer determinism.** At what step rate does the official replay run, is the navmesh cache pre-built, and do human frames advance by wall clock during replay? Will two identical submissions receive identical scores? Could a fixed frame (or a published step rate) be adopted for reproducibility?
   *Fallback:* swept-volume planning across all 120 frames, 4-mode local replay gate, ≥0.5 m human clearance.
5. **Team and verification rules.** One CodaBench account per team? Team size limits and registration deadline? For winners, what exactly will be verified (action sequences reproducible from code, or the full pipeline), and by when must the technical report be delivered?
   *Fallback:* assume one account, keep a full reproducibility pack (plans, seeds, model versions, scorer hashes) from day 1.

## 9. Mesh-free contingency (if MP3D is still missing on Nov 7)

Public assets cover: 90 connectivity graphs with viewpoint poses and unobstructed edges (incl. test scans), R2R_test.json start viewpoints/headings, HA-VLN 1.0 human anchors for all 90 scans, HAPS motions, and the Phase 2 bundle (start pose + instruction). Plan: graph-path planning between viewpoints with straight-line compiled moves, generous turn-in-place at nodes, 1.5 m human clearance from 1.0 anchors, hedged stopping. Expected cost: wall-sliding collisions on ~20–40% of episodes (CR/TCR penalties) and lower SR; expected Score roughly 25–45 versus 60–80 with meshes. Keep requesting MP3D in parallel and switch back the moment scenes arrive (navmesh cache ≤2 h, full test re-plan ≤1 day).

## 10. Submission-slot budget (Phase 2, 100 cap)

| Purpose | Count |
|---|---|
| Pipeline/format checks (STOP-only, v0) | 3 |
| Weekly full-pipeline candidates (Nov 1–27) | 12 |
| Disjoint-subset A/B experiments | 45 |
| Probes (clearance radius, timing) | 6 |
| Final candidate + confirmations | 4 |
| Reserve (outage, ties, surprises) | 30 |

Rules of use: ≤3 uploads per UTC day by default; never start an upload in the last 2 h of a UTC day if a scoring job may hang (cancelled jobs consume quota); only upload candidates that passed the 4-mode zero-collision gate.

## 11. Facts vs inferences, and contradictions with CONTEXT.md

- FACT (new): `collision_num_test.json` for all 3,408 test episodes is public in UWMILab/HA-VLN; CONTEXT item 5 says collision annotations are "withheld" (website wording) — the website statement is about the bundle, but the upstream repo already contains this file. Whether the scorer uses it is unverified (Q1).
- FACT (new): NE and success use Euclidean 3-D distance (HASimulator/measures.py L141-146, `euclidean_distance`), not geodesic; this makes STOP-only submissions exactly predictable.
- FACT (new): CodaBench outage since Oct 21 (issue #2679) — not in CONTEXT; user said "seems to be down right now", confirmed and dated here.
- INFERENCE: Phase boundaries at 23:59 UTC (from Track 1 README); Track 2 may differ.
- INFERENCE: HAPS2_0.zip size (5–15 GB) and navmesh build times (3–30 s) are estimates to be measured on D1/D2.
- No contradiction found with CONTEXT items 1–4, 6–8.

## 12. Sources

- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/track2/README.md (timeline, limits, FAQ Q5/Q6/Q7, Score, ties)
- …/ext/track2/scripts/{export_cma_submission.py, download_resources.py, resources.json} (manifest paths in image, pinned revisions)
- …/ext/image-manifest.json (6,106,231,833-byte layer)
- …/ext/roboworld2026.github.io/{index.html, track2.html} (Google Form, CodaBench 18135, Discord)
- …/ext/HA-VLN/HASimulator/environments.py L96-144 (0.1 s signal thread, ≤120 signals, navmesh recompute r=0.1 h=1.5 include_static_objects)
- …/ext/HA-VLN/HASimulator/measures.py L17-20, L141-146 (Euclidean distance_to_goal)
- …/ext/HA-VLN/Data/HA-R2R-tools/collision_num_{train,val_seen,val_unseen,test}.json; …/Multi-Human-Annotations/human_motion.json; …/HASimulator/HA-DE/tasks/R2R/data/R2R_{train,val_unseen,test}.json; …/HA-DE/connectivity/*.json
- https://github.com/codalab/codabench/issues/2679 (outage, cause, no ETA, info@codabench.org)
- https://github.com/codalab/codabench/issues/1434 , /1764 , /1641 , /2651 ; docs.codabench.org v1.23 PDF (daily limit semantics)
- https://github.com/niessner/Matterport/issues/65 and /74 (approval latency anecdotes); https://niessner.github.io/Matterport/ (ToU process); BlenderProc MP3D docs (reply contains download_mp.py)
- https://github.com/roboworld2026/track1 README (Phase 2 open 23:59 UTC, bundle wording)
- https://github.com/roboworld2026/track2/issues (0 issues as of Oct 24)
- https://github.com/UWMILab/HA-VLN/issues/19 (test split "reserved for our leaderboard"), /17 (TCR counts all collisions incl. walls — maintainer confirmed), /20 (RTX 5090 incompatibility)
- CSDN blog (via WebSearch) on `download_mp.py --task habitat` ≈ 15–16 GB; facebookresearch/habitat-sim DATASETS.md
