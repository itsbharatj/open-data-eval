> Superseded by strategy v1.2/v1.3: NavGPT-3-first (W4-T01) → SimpleVLN first; HOLDOUT-v1/SMOKE-v1 → `data/val_unseen_splits.json` is canonical; K6 (camera height) fixed in W2. Schemas exported to `contracts/`.

# C5 — Multi-agent organization and hand-off (RoboWorld 2026 Track 2, HA-VLN 2.0)

Topic id: `C5-multi-agent-organization-and-handoff` · Date: 2026-10-24 (evening; rechecked against the repo at ~19:50 UTC) · Author: research agent C5.

Regime: organizational, so it applies to both tracks. Every interface is tagged either **Track A** (the compliant inference path, which is the submission of record) or **oracle / Track B** (privileged: training, evaluation and the shadow track only).

**What I read.**
- `CONTEXT.md` (including the UPDATE) and the topic brief.
- `competitions/roboworld2026-track2/01-strategy.md`. It went from v1.0 to v1.1 to **v1.2** while I worked; this report critiques **v1.2** and the briefs as committed at `01229bd`.
- `00-competition-facts.md`, `02-research-digest.md`, `03-organizer-questions.md`, `README.md`, `briefs/README.md`, `W0`–`W7`, `data/val_unseen_splits.json`, and `havln_tools/` with its tests.
- Findings: C1 and C2 in full. The recommendations of C3, C6, C10 and B7. The headline sections of A3, A4, A5, A6, A8, A12, B3, B4 and B12.
- Simulator configs: `habitat-lab-0.1.7/habitat/config/default.py` and `HA-VLN/HASimulator/config/*.yaml`.

**Work files** (scratchpad `c5work/`):
- `contracts.py`: 16 JSON Schemas (draft 2020-12), each with an example that validates and negative cases that are rejected.
- `contracts/<Name>/1.json` and `contracts/fixtures/<Name>.json`: the same schemas exported, ready to copy into `havln_tools/schemas/`.
- `evalsets.py`: an independent hold-out draw and the power table (superseded by the committed split, see §6).
- `build_c5.py` with `c5_body.md` and `c5_json.py`: generate this document and its JSON twin.

**Reading guide.**
- Plan only (≈ 75 KB): §0–§3 and §5–§11.
- §4.3 (≈ 30 KB of schemas) is reference material for INT-T00.

**Scope boundary with sibling reports.**
- C10 owns the test program: the repo layout, the ledger and the submission gates G1–G6.
- C6 owns the measurement ladder and the statistics.
- C3 owns the rules.

This report **adopts** those specs and adds the organizational layer: roles, ownership of every interface, the module contracts that C10 names but does not define, the cadence, the headcount, the brief template, and the critique.

The topic brief numbers the workstreams the way the plan stood before the Oct-14 rules pivot. **The draft briefs' W0–W7 are canonical**; the mapping is in §1.

---

## 0. Summary (decision-relevant)

1. **Write the contracts first, then fan out.**
   - Bootstrap with 3 sessions for about 8 hours:
     - INT-T00: team repo per C10's layout, CI, schemas, ledger, splits ratified;
     - W1-T01: image forensics on both digests;
     - W0: post `03-organizer-questions.md`, register, request MP3D.
   - Then scale to ~16 sessions by about Oct 25 18:00 UTC. Without frozen contracts, every pair of workstreams negotiates frames, units and STOP ownership ad hoc.
2. **Three runtime components have no owner in any brief.** C10 names them but no brief assigns them: `agent/io.py` (C10's `AgentInput`), `sim/rollout_worker.py` (the agent in a separate process) and `sim/audit.py`. W1's brief mentions only a "rollout environment" (L27).
   - Fix: W1 owns the rollout worker, the sandbox and the audit.
   - A new **Integrator (INT)** role owns `agent/io.py`, the agent composition (`agent/navstack`) and the release candidate.
3. **The W4→W2 contract is `SubgoalProposal/1`.**
   - Policies propose a waypoint, heading, frontier, look-around, or stop together with their goal belief.
   - **Only the executor emits MOVE_FORWARD and STOP.** It owns the 500-action budget (≥ 60 in reserve; it can deny sweeps) and picks the exact stop point (max P(within 3 m)).
   - In Track B and for teachers, the topic brief's "goal point + optional waypoint hints → actions" is `PlanRequest/1 → PlanResult/1`. It is privileged and token-gated.
   - `GoalCandidates/1` (`episode → candidates[{goal_xyz, score, features}]`) is oracle-only.
   - All 16 contracts are mapped to C10's six named schema files and fill in the rest (§4).
4. **Golden set: ratify the committed split.** `data/val_unseen_splits.json` (seed 20261024; referenced by strategy v1.2 §12 and the README):

   | Set | Scans | Episodes | Trajectories |
   |---|---|---|---|
   | dev | 8 | 1,413 | 471 |
   | lockbox | 8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX | 426 | 142 |
   | quick | — | 306 | 102 |
   | smoke | — | 60 | 20 |

   - **Three different hold-out definitions were produced on the same day**: the committed file; C6's report (HOLD = oLBMNvg9in8, X7HyMhZNoso, x8F5xyUWy9e, 8194nk5LbLH); and my own independent draw. Look budgets also differ: ≤ 4 looks (strategy/README), ≤ 3 at G5–G7 (C6), only G7+G8 (C10).
   - ADR-003 should freeze the committed file by hash, with one look per gate G5–G8 (≤ 4 total), W6 only, one pre-registered champion per look.
   - Paired MDE (discordance .20, design effect 1.5):

     | Set | MDE |
     |---|---|
     | smoke | 19.8 pp (catches breakage only) |
     | quick | 8.8 pp |
     | dev | 4.1 pp |
     | lockbox | 7.4 pp |
5. **The limit is how many decisions the eval sets can support, not how many agents run.** Choosing the best of M equally good variants on dev inflates the measured SR by **2.3 / 2.7 / 3.7 pp for M = 10 / 20 / 100**. That is as large as the gains being chased (+3–5 SR). This supports C6's cap of ~10 promotion decisions per week, with pre-registration (the `hypothesis` field is mandatory in `LedgerResult/1`).
6. **Headcount.**
   - Strategy v1.2's ~16 concurrent sessions is the right steady state.
   - Peak at 20 only from Oct 31 to Nov 13, and only where independent seams exist. **Hard cap 24.**
   - Useful parallelism per workstream = its number of seams + 1 lead:

     | WS | W1 | W2 | W3 | W4 | W5 | W6 | W7 |
     |---|---|---|---|---|---|---|---|
     | Seams | 4–5 | 3 | 3 | 5 | 2–3 | 2 | 3 |

   - The binding limits are human attention (~2 h/day → ≤ ~8 lead touch-points), the number of seams, and dev statistics. Compute and the merge queue are not binding.
   - Total ≈ 600 agent-days.
7. **Shared state.** Adopt C10's `havln2026/` layout, ledger and generated `RESULTS.md`, with one change and additions:
   - **One file per ledger record** (`ledger/results/<ULID>.json`). If 15+ branches append to the same `results.jsonl`, they conflict at end-of-file on every merge; `results.jsonl` becomes a generated index.
   - Add a content-addressed data lake (C1), a `DECISIONS.md` ADR log, a machine-readable facts registry, generated `STATUS.md` and `DIGEST`, and the rule "no run_id, no claim".
8. **Compliance has to be built into the architecture.** Convention is not enough.
   - The agent process has no quarantined mounts. C10's `lint-imports`, audit hook and privileged-ablation invariance replace the brief's `grep -r "oracle" agent/`.
   - The runner signs `inputs_used` plus an audit hash into every `RolloutRecord/1`.
   - The test bundle is visible only to the release runner.
   - **The test-scan assets in `data/` (`test_episode_index.json`, `test_trajectory_table.json`, `mp3d_test_scan_room_labels.json`) are readable by every agent today**, while only `sample_room_paths.json` is hash-blocked. Quarantine them.
9. **Review and merge.**
   - Trunk-based with a merge queue; 4 risk tiers.
   - Tier 2 (schemas, scorer, splits, compliance, facts) needs the integrator **and** the human. Tier 3 (uploads, organizer messages) is human-only.
   - Contract changes merge only at 12:00 UTC.
   - Freezes at G7 (Fri Nov 20) and G8 (Fri Nov 27).
   - Submission gates are C10's G1–G6 plus **G7: bit-identical regeneration of the ZIP from the release tag** (B7).
10. **Cadence (UTC, because the CodaBench day is a UTC day).**
    - Nightly evaluation and certification: 22:00–05:00. Digest: 05:30.
    - The human's 45–60 min decision block: about 06:00.
    - Upload window: 08:00–14:00, at most 2 per day.
    - Friday gate reviews follow the v1.2 gates (G5 Nov 2–6, G6 Nov 9–13, G7 Nov 16–20 + freeze, G8 Nov 27). The close is assumed to be Nov 30 15:59 UTC.
11. **Critique: 27 open issues remain in the current drafts (§11)**, plus 5 resolved during the day. High severity:
    - **K1.** Runtime components unassigned.
    - **K2.** Prose interfaces.
    - **K4.** W5's body and strategy §3 still present K-rollout selection as *the* method and "(allowed)", while §2, §5 and W5's own header call it gray and default OFF.
    - **K5.** W5 L11-12 still prescribes the public original R2R instruction, which `03-organizer-questions.md` T10 classifies as privileged.
    - **K6.** Three conflicting hold-out definitions and look budgets.
    - **K7.** Test-scan assets readable in the shared repo.
12. **Deliverables.**
    - An agent-brief template (§10): YAML front matter validated by `TaskBrief/1`, 12 sections, an append-only log so a context-limited session can resume, and a REPORT block.
    - A starter backlog of 17 tasks (§2.5).
    - The exported schemas.

---

## 1. Reconciliation: topic-brief workstreams vs the canonical (post-pivot) briefs

| Topic brief (pre-pivot) | Canonical WS | What changes |
|---|---|---|
| W1 data + infra | **W1** Data, image forensics, replay farm | + rollout worker (separate process), compliant sandbox, audit, `Observation/1`, Phase-2 bundle intake |
| W2 executor (navmesh path → actions) | **W2** Safety executor (perceived map) | The navmesh-based planner becomes `oracle/teacher` (W4-d + W7) behind `PlanRequest/1` |
| W3 grounding | **W3** Perception & grounding | Outputs `InstructionProgram/1`, `Percept/1` |
| W4 goal inference (candidates + rankers) | split: **W3** (end-region / human anchors), **W4** (stop belief inside the policy), **W5** (selection). Track B goal inference → **W7** (`GoalCandidates/1`, oracle-only) | No goal-inference workstream in Track A: the compliant agent has no map-derived candidate set |
| W5 learned closed-loop fallback | **W4** Policies (**now the primary**) | v1.2: SimpleVLN first, ETP-R1 second; NavGPT-3 / OmniNav / Uni-NaVid not compliant as published |
| W6 verification + ops | **W6** Verification & submission + **W0** Ops & liaison | W6 = release, gates G1–G7, ledger; W0 = organizers, MP3D, CodaBench |
| W7 research / report | **W7** Track B shadow + oracle analysis + report | Time-box Track B (K18) |
| — | **INT** Integrator, **REV** reviewer / red team, **OPS** scribe (scheduled task) | New cross-cutting roles |

---

## 2. Operating model

### 2.1 Roles

| Role | Instances | Owns | Decides | Talks to |
|---|---|---|---|---|
| **Human orchestrator (H)** | 1, ~2 h/day | Strategy, organizer communication, uploads, rules stance | Accepting ADRs; Tier-2/3 approvals (G6 sign-off); kill/continue at gates | Leads, INT, W0 |
| **Integrator (INT)** | 1 role, re-instantiated daily from `STATUS.md` + `HANDOFF/INT.md` | `agent/io.py`, `agent/navstack`, `havln_tools/schemas/`, merge-queue health, nightly release candidate (RC), gate packets | Additive schema changes; RC content | H, all leads |
| **WS lead (LEAD-Wn)** | 1 per active WS (≤ 8); a fresh session each morning | WS backlog `briefs/Wn/*.md`, task split, first-line review, WS status | Priorities inside the WS | H (digest / DECISIONS), INT, own implementers |
| **Implementer** | One per seam (§3) | One TaskBrief, one branch, ≤ 3 agent-days | Implementation inside the contract | Its lead only (brief log + PR) |
| **Reviewer (REV)** | Ephemeral, one fresh session per PR or batch | Checklist review (§7.3) | Approve Tier 0–1 | PR thread |
| **Red team (REV-RT)** | Part-time: weekly + every RC | C10 compliance suite C1–C7, sandbox-escape attempts, split hygiene, hash blocklist | Can block an RC | INT, H |
| **Scribe (OPS)** | Scheduled task, 05:30 UTC | Generates `RESULTS.md` (from the ledger), `STATUS.md` (from brief front matter), `DIGEST/<date>.md`; flags stale tasks (> 24 h with no log entry) | Nothing | Posts the digest to H |

### 2.2 Communication rules

- **Files and PRs are the bus**, which keeps everything auditable for the technical report's correspondence appendix:
  - Briefs carry the spec plus an append-only log.
  - PRs carry the code plus a REPORT block.
  - The ledger holds the numbers.
  - `STATUS.md` (generated) holds state.
  - `DECISIONS.md` holds ADRs.
  - `DIGEST/` holds the daily summary.
- Direct session messages are allowed only from H to a lead or INT, and from a lead to its implementers. There is no implementer-to-implementer chat; interface disagreements become a schema PR.
- Every number cites a ledger `run_id`. Every rules claim cites `research/organizer-answers.md`, the `03-organizer-questions.md` compliance table, or an ADR.

### 2.3 Task lifecycle

`draft → ready` (lead; dependencies met) `→ in_progress` (session id) `→ review` (PR + REPORT) `→ done` (merged). Side exits: `blocked` (reason + escalation) or `killed` (kill criterion).

Rules:
- Time box ≤ 3 agent-days; split anything bigger.
- The implementer appends a checkpoint to the brief's `## Log` at least every ~2 h of work. A fresh session can then resume after context exhaustion.
- One task per session.

### 2.4 Session hygiene (context budget)

- Mandatory reading: `AGENTS.md` (≤ 8 KB: charter, C3 red lines, workflow), `00-competition-facts.md`, the brief, and the brief's *read-first* list. Total **≤ 60 KB ≈ 15k tokens**.
- `research/` is now **32 files and 1.40 MB (≈ 350k tokens)**; it grew from 9 files at midday. Never load it wholesale. Use `02-research-digest.md`, then line ranges.
- Leads are stateless: a new lead session every morning. Long-lived sessions accumulate stale context, as this report itself experienced when the strategy changed twice in four hours.

### 2.5 Day-0 bootstrap and starter backlog

**INT-T00, first and alone (≈ 0.5 agent-day):**
1. Create the team repo `havln2026/` with C10's layout (`havln_tools/`, `synth/`, `agent/`, `oracle/`, `sim/`, `benchmarks/`, `tests/`, `ledger/`, `docker/`, `.github/workflows`).
2. Add the organizational files: `AGENTS.md`, `DECISIONS.md`, `briefs/<WS>/`, `HANDOFF/`, `DIGEST/`.
3. Copy the §4 schemas into `havln_tools/schemas/`.
4. Freeze `data/val_unseen_splits.json` by hash (ADR-003).
5. Install `havln_tools.ledger` with one file per record; the `RESULTS.md` and `STATUS.md` generators; PR CI per C10 (`lint-imports`, ledger check, py3.8 + 3.11); CODEOWNERS; branch protection and a merge queue; a PR template with the REPORT block.
6. Add scheduled tasks: digest 05:30 UTC, nightly 22:30 UTC.
7. Re-cut the drafts into TaskBrief files.

Starter backlog. Regime A = the compliant inference path; B = oracle.

| ID | Task | Regime | Depends on | Time box |
|---|---|---|---|---|
| INT-T00 | Bootstrap repo, CI, schemas, ledger, generators, split ADR | — | — | 0.5 d |
| W0-T01 | Register; post `03-organizer-questions.md` (GitHub issue + Discord + private email incl. the B12 leak note); archive verbatim | — | — | today |
| W0-T02 | MP3D: ≥ 3 academic requests + individual maintainers; daily chase log | — | — | daily |
| W1-T01 | Pull **both** digests; C10 S1–S4 (fingerprint, env parity, sensor parity, measure registry); write constants into `agent/io.py` and facts | — | — | 0.5 d |
| W1-T02 | Deterministic replay scorer with all regime ids (§4.0) + `havlnctl score / cert` | B | W1-T01 | 1.5 d |
| W1-T03 | `sim/rollout_worker.py` (agent in a separate, quarantine-free process) + `sim/audit.py` + `EpisodeInput/1` / `Observation/1` / `RolloutRecord/1`; HA-mini (17DRP5sb8fy) bring-up before MP3D | A | W1-T01 | 2 d |
| W1-T04 | Navmesh cache warm-up (single writer) + NavStepper + planning service (`PlanRequest/1`, token-gated) | B | MP3D | 1.5 d |
| W2-T01 | Persistent per-floor height map + people layer (C7, strategy §3 executor rules); `synth/` tests first | A | INT-T00 | 1.5 d |
| W2-T02 | 24-heading lattice planner + hard per-step check + budget manager + exact pose-delta contact handling; synthetic tests | A | W2-T01 | 2 d |
| W3-T01 | Clause labelling + instruction parser → `InstructionProgram/1` (B9 P1–P4); eval harness (train for development; dev via `oracle/gt_eval`) | A | INT-T00 | 1.5 d |
| W3-T02 | Person detector/tracker (trained on train-scan semantic renders, B11) + swept envelope + 144-way activity matcher → `Percept/1` | A | W1-T03 | 2 d |
| W4-T01 | SimpleVLN client (vLLM) through `AgentAPI/1` on smoke, with W2 owning MOVE_FORWARD | A | W1-T03, W2-T02 | 2 d |
| W4-T02 | ETP-R1 port with 22-TURN rings, `back_algo: control`, budget-aware sweep/STOP | A | W1-T03 | 3 d |
| W4-T03 | `oracle/teacher`: lattice on the intersection of 121 navmeshes with clearance cost (replaces ShortestPathFollower) + DAgger dataset spec | B | W1-T04 | 2 d |
| W6-T01 | Phase-1 calibration ZIPs (C6 P1-a…e) + release script skeleton + `SubmissionRecord/1` | — | W1-T01 | 1 d |
| W7-T01 | Oracle-ladder runner (C6 L0–L8) + failure taxonomy + report skeleton (C3 disclosure template) | B | W1-T02 | 1.5 d |
| REV-T01 | Red-team baseline: C10 C1–C7, sandbox escape, test-text guard, hash blocklist | — | W1-T03 | 1 d |

---

## 3. Workstreams: seams, interfaces, acceptance tests

| WS | Independent seams (≈ one implementer each) | Consumes | Produces | Peak agents |
|---|---|---|---|---|
| W0 Ops | answers → ADR / flags; MP3D chase; CodaBench watch | — | `research/organizer-answers.md`, ADRs | 0–1 + H (scheduled) |
| W1 Infra | (a) forensics + scorer parity; (b) farm, queue, `havlnctl`; (c) **rollout worker + sandbox + audit**; (d) navmesh cache + planning/render (privileged); (e) Phase-2 bundle intake | image, data | `EpisodeInput/1`, `Observation/1`, `RolloutRecord/1`, `ScoreRequest/Result/1`, `PlanRequest/Result/1` | 4 → 2 |
| W2 Executor | (a) height map + people layer; (b) lattice / guard / budget / contact response; (c) stop placement, oracle-goal harness (C6 L3) + taxonomy | `Observation/1`, `Percept/1`, `SubgoalProposal/1` | actions, `ExecutorReport/1` | 3 |
| W3 Grounding | (a) clause labelling + parser; (b) people detect / track / match; (c) room/object tags + topological memory | `EpisodeInput/1`, `Observation/1` | `InstructionProgram/1`, `Percept/1` | 3 |
| W4 Policies | (a) SimpleVLN; (b) ETP-R1 rings; (c) StreamVLN / NaVILA diversity; (d) teacher + DAgger data; (e) Guard v2 learned step-collision predictor + RL | `InstructionProgram/1`, `Percept/1`, `ExecutorReport/1`, `PlanResult/1` (teacher) | `SubgoalProposal/1`, checkpoints | 5 |
| W5 Selection | (a) **W5-S** allowed levers: per-decision voting, multi-sample at the same state, stop check; (b) **W5-M** K-rollout selector (flag, default OFF); (c) verifier on scan-disjoint train folds | many `SubgoalProposal/1`, `RolloutRecord/1` | `SelectionRecord/1`, tapes | 2–3 |
| W6 Release | (a) gates G1–G7, ledger, uploads; (b) compliance audit + regeneration | `RolloutRecord/1`, `ScoreResult/1` | `SubmissionRecord/1`, ZIP | 1–2 |
| W7 Oracle + report | (a) oracle ladder + taxonomy; (b) teacher with W4-d / Track B shadow (time-boxed); (c) report | `ScoreResult/1`, `GoalCandidates/1`, `PlanResult/1` | taxonomy, report | 2–3 |
| INT | `agent/io.py`, navstack, schemas, RC, gate packets | all | RC tags | 1 |

### 3.1 Acceptance tests

Where a C10 (U/S/B/C) or C6 (L/P) test already exists, it is referenced instead of redefined.

Regime sets (§4.0):
- **RELEASE-SWEEP** = C6's sweep; it is the G3 gate.
- **NIGHTLY-4** = {`frz:0`, `frz:119`, `sps:20`, `allf`}.

All thresholds below follow strategy v1.2. Conflicting thresholds elsewhere are listed in K12.

**W0 Ops**
- AT-W0-1: one registered submitting account recorded in `ops/accounts.md` (A12: limits are per account).
- AT-W0-2: `03-organizer-questions.md` posted on all 3 channels and the links archived. Answers are copied verbatim within 2 h and mapped to an ADR + config flag within 24 h. The private B12 leak note is sent before Oct 30.
- AT-W0-3: ≥ 3 MP3D requests with timestamps, plus a daily chase entry; the Nov 7 mesh-free trigger (C2) is recorded.
- AT-W0-4: CodaBench status checked ≥ 2× per day, logged in `STATUS.md`.

**W1 Infra**
- AT-W1-1 (M1): C10 S1–S4 pass on ≥ 2 GPU hosts and for both digests (CR definition per digest recorded). The camera height, tilt, depth range and normalisation are written into `agent/io.py` and facts by a Tier-2 PR.
- AT-W1-2 (M2): STOP-only val_unseen replay = 8.473053 (C6 L0; NE to 1e-6); LOOK-only tape → no displacement; a designed wall-slide tape → count = NavStepper prediction.
- AT-W1-3 (M2/M3): CMA export replay = README within Score ±0.5, SR ±0.01, NE ±0.15, TCR ±1.0, under both `wall` and the in-image `havln-score-phase1` (C6 L1).
- AT-W1-4: `frz:k`, `sps:S`, `lock` and `rand:<seed>` replays are byte-identical across 2 runs, 2 GPUs and 2 process counts (C1 T3).
- AT-W1-5: NavStepper ≡ Simulator on 1,000 random tapes × 3 scans × frames {0, 60, 119}; mismatch ≤ 0.1 % (C1 T2).
- AT-W1-6: test-split replay (3,408 episodes) < 30 min. The rollout worker with a stub agent sustains ≥ 2,000 episodes per hour per GPU; measure and record in `bench.json`.
- AT-W1-7: C10 C2/C3/C5. The agent process cannot open quarantined or hash-blocked paths; `AgentInput` = exactly C10 C4's keys; `inputs_used` ⊆ {rgb, depth, pose, instruction, episode_id, start_pose}; tapes are byte-identical with privileged files removed.
- AT-W1-8: frame conventions. MOVE_FORWARD in free space → `position_ep ≈ (0.25, 0, 0)`; TURN_LEFT → `yaw_ep = +π/12`; depth in metres.
- AT-W1-9 (M4): the Phase-2 bundle is ingested within 4 h, with an inventory report. Test `EpisodeInput/1` is written **only** to `/lake/test_bundle/` (mounted only in the release runner).

**W2 Executor (Track A)**
- AT-W2-1 (no Habitat; `synth/`): 1,000 randomized corridors, 0.7–0.9 m doors, L-turns and clutter → 0 contacts. Lateral drift ≤ 0.1 m per 5 m. The budget guard never produces > 500 actions or a missing STOP.
- AT-W2-2 (C6 L3; GT goal point, perceived map, dev): clean SR ≥ 0.90 at M3, rising to ≥ 0.94; contact episodes ≤ 1 % under RELEASE-SWEEP.
- AT-W2-3 (C6 L2; privileged teacher): SR ≥ 0.97 with zero contacts on all 121 navmeshes. The gap to AT-W2-2 measures the cost of perception.
- AT-W2-4: failure taxonomy (door / stairs / human-at-start / map error / budget / near-field blind zone) with episode ids; > 90 % of failures classified.
- AT-W2-5 (property, every tape): no MOVE_FORWARD with replay displacement < 0.24998 m in any NIGHTLY-4 regime. If an obstacle is within 0.5 m at the start, the first action is a TURN.

**W3 Grounding**
- AT-W3-1: 100 % schema-valid `InstructionProgram/1` on 2,000 train/val instructions; deterministic via the gateway cache; cost and latency within quota.
- AT-W3-2: end-region accuracy vs the GT final region (`oracle/gt_eval` via `.house`) ≥ 0.70 on dev, with a CI.
- AT-W3-3: human-mention → detected-person matching precision and recall ≥ 0.80 on dev. Labels come from `human_motion.json` read only in `oracle/gt_eval`.
- AT-W3-4: person detection recall ≥ 0.95 within 3 m on train scenes; median footprint error ≤ 0.2 m.
- AT-W3-5: report the fraction of episodes whose end-slot human lies within 3 m of the GT goal (B9 expects ~41 %).

**W4 Policies**
- AT-W4-1: each backbone runs on smoke through `AgentAPI/1`, with the executor emitting every MOVE_FORWARD; 0 contract violations; 0 instruction truncations.
- AT-W4-2 (bake-off, Tue Nov 3): dev SR, contacts, actions and cost per backbone. The primary is chosen by ADR-008 using a pre-registered criterion.
- AT-W4-3 (strategy v1.2 W4 row): closed-loop K = 1 dev clean SR ≥ 0.40 by Nov 9, ≥ 0.46 by Nov 16, ≥ 0.50 at freeze.
- AT-W4-4 (C10 C6): training manifests contain no val/test episode ids and no val_unseen/test scans. Teacher tapes have 0 contacts under `allf`.
- AT-W4-5: GPU-hours and LLM spend per run are recorded in the ledger.

**W5 Selection**
- AT-W5-1 (W5-S, allowed): +3–5 SR over the best single configuration on dev (paired, McNemar p < 0.05; C6 rule ≥ +1.0 pp per adopted change).
- AT-W5-2 (W5-M, gray): enabled only after a written answer to issue item 4. SR(K=8) − SR(K=1) is reported separately (C6 L7) and never mixed into the default board.
- AT-W5-3: verifiers and calibrators are fitted only on scan-disjoint **train** folds (manifest check); ECE ≤ 0.05 on dev.
- AT-W5-4: a full test production run takes ≤ 24 h wall. Estimate at 64 workers, assuming ~60 decisions × 1.5 s per episode: K = 1 ≈ 1.3 h, K = 8 ≈ 10.7 h.

**W6 Release (C10 §10 gates + G7)**
- AT-W6-1: G1 contract (ours strict + `havln-validate`); G2 compliance C1–C7; G3 RELEASE-SWEEP (TCR spread < 0.005, fragile episodes ≤ 0.5 %); G4 ledger entry with the predicted envelope; G5 ZIP sha not uploaded before; G6 human sign-off.
- AT-W6-2: **G7**: regenerating from a clean checkout of the RC tag, the pinned image and the LLM cache yields an **identical ZIP sha256** (B7).
- AT-W6-3: test tapes are validity-checked only (issue item 8). They are never re-selected or edited per episode using local test replay outcomes (`03-organizer-questions.md` T13 = privileged).
- AT-W6-4: a `SubmissionRecord/1` exists within 1 h of the official result. |official − predicted| outside the envelope opens an incident.

**W7 Oracle analysis + report**
- AT-W7-1: weekly oracle ladder (C6 L0–L8) and a taxonomy of the current RC's dev failures (≤ 8 classes, ≥ 95 % auto-classified), delivered to W2–W5 leads by Monday 06:00.
- AT-W7-2 (Track B shadow): candidate coverage ≥ 98 % on dev; top-1 within 3 m reported. **Kill criterion:** without written permission (issue item 1) by Fri Nov 6, Track B gets 0 agents and its code is frozen.
- AT-W7-3: report milestones: skeleton by Nov 6, ablation table by Nov 20, draft Nov 25, final Dec 8. Every number links to a `run_id`.

**INT**
- AT-INT-1: the navstack runs a stub agent end-to-end on HA-mini and smoke; in debug mode every message is schema-validated at module boundaries.
- AT-INT-2: the nightly RC is evaluated on dev and replayed under NIGHTLY-4 by 05:00 UTC, with its `run_id` in the digest.
- AT-INT-3: schema versions used in code = `havln_tools/schemas/` (CI).

---

## 4. Contracts (JSON Schemas, draft 2020-12)

### 4.0 Conventions

- **Location and versioning.**
  - Schemas live in `havln_tools/schemas/<Name>/<MAJOR>.json` (C10 location), with fixtures in `tests/fixtures/schemas/`.
  - Every message carries `"contract": "Name/MAJOR"`.
  - Adding optional fields keeps the MAJOR version but needs a schema PR (`additionalProperties` is false) and INT approval.
  - A breaking change becomes `Name/2`. It needs an ADR, human approval, and a 48 h dual-acceptance window.
- **Mapping to C10's named files:**

  | C10 file | C5 contract |
  |---|---|
  | `program` | `InstructionProgram/1` |
  | `rollout` | `RolloutRecord/1` |
  | `candidates` | `GoalCandidates/1` |
  | `ledger_result` | `LedgerResult/1` (same field names + `task_id`, `hypothesis`, `agent_fp`, `fingerprint`, `k_rollouts`, `compliance`) |
  | `ledger_submission` + `manifest` | `SubmissionRecord/1` |

  New contracts not in C10: `EpisodeInput/1`, `Observation/1` (the logged form of C10's `AgentInput`), `Percept/1`, `SubgoalProposal/1`, `ExecutorReport/1`, `SelectionRecord/1`, `ScoreRequest/1`, `ScoreResult/1`, `PlanRequest/1`, `PlanResult/1`, `TaskBrief/1`.
- **Frames.**
  - *World* = Habitat: +Y up, forward = −Z at yaw 0, θ = 2·atan2(qy, qw), quaternions [x,y,z,w] (A5).
  - *Episode frame* (compliant): origin at the start; +x = start heading, +y = left, +z = up; `yaw_ep = θ − θ_start`, counter-clockwise positive (TURN_LEFT = +15°).
  - Units are metres and radians.
  - `Observation/1` carries only C10 C4's `AgentInput` information. `pose_delta_m`, `actions_used`, `last_action` and `camera.pitch_deg` are *derived inside* `agent/io.py` from GPS, compass and the agent's own actions; they add no information.
- **Sensor constants are never hard-coded in briefs or code.** `agent/io.py` and `facts.yaml` get them from W1-T01 (C10 S3).
- **Canonical regime ids** (C1 R0–R4 + C6 extras):

  | Id | Meaning |
  |---|---|
  | `wall` | Official wall-clock timing (R0) |
  | `wallx:<s/step>` | Throttled wall clock (R1) |
  | `frz:<k>` | Humans frozen at frame k (R2) |
  | `sps:<S>` | Deterministic schedule at S steps/s (R3). C6's virtual clock with d̂ = 5 / 20 ms equals `sps:200` / `sps:50` |
  | `allf` | All-frames kinematic certificate (R4) |
  | `lock` | Step-locked |
  | `stall:<k>` | Stall at frame k |
  | `rand:<seed>` | Random monotone schedule |
  | `static` | No humans |

  - **RELEASE-SWEEP** (gate G3) = `allf` + `frz:{0,10,…,110,119}` + `sps:{5,10,20,50,200}` + `lock` + `stall:119` + `rand:1..20` + `wall` × 3.
  - **NIGHTLY-4** = `frz:0`, `frz:119`, `sps:20`, `allf`.
  - **Rollout regimes** for closed-loop runs: `sps:200` and `sps:50`; a tape that passes under only one of them is fragile (C6).
- **Eval-set names** = the keys of `data/val_unseen_splits.json` (`smoke`, `quick`, `dev`, `lockbox`) plus `val_unseen`, `val_seen`, `trainho`, `g60`, `ha-mini`, `syn-*`, `test`.
- **Validation.** CI validates the fixtures. The navstack validates every message in debug mode; the runner always validates `RolloutRecord/1`.

Shared definitions (injected into every schema):

```json
{"$defs": {
  "vec3": {"type":"array","items":{"type":"number"},"minItems":3,"maxItems":3},
  "quat_xyzw": {"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4},
  "sha256": {"type":"string","pattern":"^[0-9a-f]{64}$"},
  "episode_id": {"type":"string","pattern":"^[0-9]+$"},
  "split": {"enum":["train","val_seen","val_unseen","test","synthetic"]},
  "action": {"enum":["STOP","MOVE_FORWARD","TURN_LEFT","TURN_RIGHT","LOOK_UP","LOOK_DOWN"]},
  "regime": {"type":"string","pattern":"^(wall|wallx:[0-9.]+|frz:([0-9]|[1-9][0-9]|1[01][0-9])|sps:[0-9]+|allf|lock|stall:([0-9]|[1-9][0-9]|1[01][0-9])|rand:[0-9]+|static)$","description":"C1 R0 wall=official wall-clock; R1 wallx:<s/step> throttled; R2 frz:<k> frozen at frame k; R3 sps:<S> deterministic schedule at S steps/s (C6 virtual clock dhat=5 ms == sps:200); R4 allf = all-frames kinematic certificate; C6 extras: lock (step-locked), stall:<k>, rand:<seed> (random monotone schedule); static = no humans"},
  "eval_set": {"type":"string","pattern":"^(smoke|quick|dev|lockbox|val_unseen|val_seen|trainho|g60|ha-mini|test|syn-[a-z0-9-]+)(@v[0-9]+)?$","description":"names = keys of data/val_unseen_splits.json (smoke 60, quick 306, dev 1,413, lockbox 426) + C10 fixtures (g60, ha-mini)"},
  "utc": {"type":"string","pattern":"^20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9](:[0-5][0-9](\\.[0-9]+)?)?Z$"},
  "mode": {"enum":["compliant","privileged"]},
  "input_kind": {"enum":["rgb","depth","pose","instruction","episode_id","start_pose","siblings","navmesh","humans_gt","goal_gt","scene_mesh","test_scan_assets","collision_flag"]},
  "prob": {"type":"number","minimum":0,"maximum":1},
  "task_id": {"type":"string","pattern":"^(W[0-8]|INT|REV|OPS)-T[0-9]{2,3}$"}
}}
```

### 4.1 Agent API (Python; INT owns `agent/io.py` and `agent/navstack/api.py`; Tier 2)

```python
from typing import Protocol, Literal, Mapping, Any, Tuple, List
Action = Literal["STOP", "MOVE_FORWARD", "TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN"]

class Agent(Protocol):                                   # AgentAPI/1 — what sim/rollout_worker.py drives (separate process)
    def reset(self, episode: Mapping[str, Any]) -> None: ...        # EpisodeInput/1  (C10 AgentInput: episode_id, instruction, start_pose)
    def act(self, obs: Mapping[str, Any]) -> Action: ...            # Observation/1   (C10 AgentInput: step_idx, rgb, depth, gps, compass)
    def trace(self) -> List[dict]: ...                              # proposals/reports log; never used for control

class Parser(Protocol):      # W3
    def parse(self, episode) -> dict: ...                           # InstructionProgram/1
class Perceiver(Protocol):   # W3
    def update(self, obs) -> dict: ...                              # Percept/1
class Mapper(Protocol):      # W2 (in-process MapState)
    def update(self, obs, percept) -> "MapState": ...
class Policy(Protocol):      # W4 (one per backbone)
    def propose(self, obs, program, percept, map_view, last_report) -> dict: ...   # SubgoalProposal/1
class Executor(Protocol):    # W2 — the ONLY emitter of MOVE_FORWARD and STOP; owns the 500-action budget
    def step(self, proposal, map_state, obs) -> Tuple[Action, dict]: ...          # (action, ExecutorReport/1)
class Selector(Protocol):    # W5
    def choose(self, proposals: List[dict]) -> dict: ...           # W5-S: per decision, same observation stream (allowed)
    def select(self, rollouts: List[dict]) -> dict: ...            # W5-M: per episode -> SelectionRecord/1 (flag, default OFF)
```

Runner guarantees (W1):
- The agent process receives only `EpisodeInput/1` and `Observation/1`, as numpy arrays and no sim handles (C10 C4).
- Goals, reference paths, `info`, `scene_id`, `trajectory_id`, human files, navmeshes and test-side files are not mounted in that process.
- `act` is called until STOP or 500 actions; invalid actions are rejected.
- Each episode yields a signed `RolloutRecord/1` (inputs_used + audit hash).
- Seeds are fixed, and every model call goes through the gateway (cache + quota).

### 4.2 W1 ↔ everyone: the simulator API

This is a CLI and SDK over `ScoreRequest/1` / `ScoreResult/1`. Calls are idempotent: `task_id = sha256(canonical request)` (C1 §6).

```
havlnctl rollout --agent <entrypoint|agent_fp> --set smoke --k 1 --mode compliant --regime sps:200   -> RolloutRecord/1 (+ ScoreResult/1 on val)
havlnctl score   <tapes|zip> --set dev --regimes NIGHTLY-4                                            -> ScoreResult/1 + aggregate -> LedgerResult/1
havlnctl cert    <zip|tapes> --set dev --regimes RELEASE-SWEEP                                        -> gate G3 report -> SubmissionRecord.gates
havlnctl plan    <PlanRequest.json> --token $ORACLE_TOKEN                                             -> PlanResult/1 (privileged; refused in compliant mode)
havlnctl render  ... --token $ORACLE_TOKEN                                                            -> privileged renders (oracle/ only)
python -m havln_tools.ledger append|check|render                                                      -> ledger/results/<ULID>.json, RESULTS.md (scribe)
```

### 4.3 Schemas

#### EpisodeInput/1  (W1 runner → agent; = C10 `AgentInput` episode fields)

```json
{
 "$id": "havln-team/contracts/EpisodeInput/1",
 "title": "EpisodeInput/1: the ONLY episode data a compliant agent receives. Runner strips goals, reference_path, info, scene_id, trajectory_id. Owner W1 (runner). Consumers: W3, W4, W5.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","episode_id","split","start","instruction","max_actions"],
 "properties": {
   "contract": {"const":"EpisodeInput/1"},
   "episode_id": {"$ref":"#/$defs/episode_id"},
   "split": {"$ref":"#/$defs/split"},
   "start": {"type":"object","additionalProperties":false,"required":["position_world","rotation_world_xyzw"],"properties":{"position_world":{"$ref":"#/$defs/vec3"},"rotation_world_xyzw":{"$ref":"#/$defs/quat_xyzw"}}},
   "instruction": {"type":"string","minLength":1},
   "max_actions": {"const":500},
   "siblings": {"description":"Present ONLY if flag allow_sibling_instructions=true (requires written organizer permission)","type":"array","maxItems":3,"items":{"type":"object","additionalProperties":false,"required":["episode_id","instruction"],"properties":{"episode_id":{"$ref":"#/$defs/episode_id"},"instruction":{"type":"string"}}}}
 }
}
```

#### Observation/1  (W1 runner → agent each step; = C10 `AgentInput` step fields)

```json
{
 "$id": "havln-team/contracts/Observation/1",
 "title": "Observation/1: per-step compliant observation (logged form; in-process the refs are numpy arrays). Owner W1. Episode frame: origin = start position, +x = start heading, +y = left, +z = up; yaw_ep = yaw - yaw_start, CCW+, TURN_LEFT = +15 deg. Sensor constants (camera height, HFOV, depth range/normalisation, tilt) MUST be copied from the image's /app/config/challenge_submission.yaml by W1 (habitat defaults: camera 1.25 m, HFOV 90, depth 0-10 m normalised).",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","episode_id","t","rgb","depth","pose","camera","actions_used","last_action"],
 "properties": {
   "contract": {"const":"Observation/1"},
   "episode_id": {"$ref":"#/$defs/episode_id"},
   "t": {"type":"integer","minimum":0,"maximum":500,"description":"0 = observation after reset"},
   "rgb": {"type":"object","required":["ref","shape"],"properties":{"ref":{"type":"string"},"shape":{"const":[224,224,3]}}},
   "depth": {"type":"object","required":["ref","shape","units"],"properties":{"ref":{"type":"string"},"shape":{"const":[256,256,1]},"units":{"const":"m"},"max_range_m":{"type":"number"},"min_range_m":{"type":"number"}}},
   "pose": {"type":"object","additionalProperties":false,"required":["source","position_ep","yaw_ep"],"properties":{"source":{"const":"gps_compass"},"position_ep":{"$ref":"#/$defs/vec3"},"yaw_ep":{"type":"number"},"position_world":{"$ref":"#/$defs/vec3"}}},
   "camera": {"type":"object","required":["height_m","hfov_deg","pitch_deg"],"properties":{"height_m":{"type":"number"},"hfov_deg":{"type":"number"},"pitch_deg":{"type":"number"},"tilt_step_deg":{"type":"number"}}},
   "actions_used": {"type":"integer","minimum":0,"maximum":500},
   "last_action": {"anyOf":[{"$ref":"#/$defs/action"},{"type":"null"}]},
   "pose_delta_m": {"anyOf":[{"type":"number","description":"planar displacement caused by last_action; < 0.249 after MOVE_FORWARD => contact suspected"},{"type":"null"}]}
 }
}
```

#### InstructionProgram/1  (W3 → W4/W5/W7; = C10 `program.schema.json`)

```json
{
 "$id": "havln-team/contracts/InstructionProgram/1",
 "title": "InstructionProgram/1: parse(instruction) output. Owner W3. Consumers: W4 policies, W5 selector, W7 analysis.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","episode_id","instruction_sha256","parser","steps","humans","stop","confidence"],
 "properties": {
   "contract": {"const":"InstructionProgram/1"},
   "episode_id": {"$ref":"#/$defs/episode_id"},
   "instruction_sha256": {"$ref":"#/$defs/sha256"},
   "parser": {"type":"object","required":["model","prompt_sha256","version"],"properties":{"model":{"type":"string"},"prompt_sha256":{"$ref":"#/$defs/sha256"},"version":{"type":"string"}}},
   "start_context": {"type":"object","properties":{"region":{"anyOf":[{"type":"string"},{"type":"null"}]},"facing":{"anyOf":[{"type":"string"},{"type":"null"}]},"objects":{"type":"array","items":{"type":"string"}}}},
   "steps": {"type":"array","minItems":1,"items":{"type":"object","required":["idx","verb"],"additionalProperties":false,"properties":{"idx":{"type":"integer","minimum":0},"verb":{"enum":["go","turn_left","turn_right","turn_around","go_up","go_down","enter","exit","pass","follow","wait","stop"]},"landmark":{"anyOf":[{"type":"object","properties":{"text":{"type":"string"},"category":{"type":"string"}}},{"type":"null"}]},"relation":{"anyOf":[{"enum":["past","through","into","until","toward","around","at","between","along","out_of"]},{"type":"null"}]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]},"human_ref":{"anyOf":[{"type":"string"},{"type":"null"}]},"distance_hint_m":{"anyOf":[{"type":"number"},{"type":"null"}]}}}},
   "humans": {"type":"array","items":{"type":"object","required":["mention_id","text","role"],"additionalProperties":false,"properties":{"mention_id":{"type":"string"},"text":{"type":"string"},"activity":{"anyOf":[{"type":"string"},{"type":"null"}]},"role":{"enum":["start","during","end","unknown"]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]}}}},
   "stop": {"type":"object","required":["text"],"properties":{"text":{"type":"string"},"region":{"anyOf":[{"type":"string"},{"type":"null"}]},"object":{"anyOf":[{"type":"string"},{"type":"null"}]},"human_ref":{"anyOf":[{"type":"string"},{"type":"null"}]},"relation":{"anyOf":[{"type":"string"},{"type":"null"}]}}},
   "route_only_paraphrase": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "confidence": {"$ref":"#/$defs/prob"}
 }
}
```

#### Percept/1  (W3 → W2/W4/W5)

```json
{
 "$id": "havln-team/contracts/Percept/1",
 "title": "Percept/1: perceive(obs) output, episode frame. Owner W3. Consumers: W2 mapper (people layer, swept envelopes), W4, W5.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","t","people","tags","models"],
 "properties": {
   "contract": {"const":"Percept/1"},
   "t": {"type":"integer","minimum":0},
   "people": {"type":"array","items":{"type":"object","required":["track_id","position_ep","radius_m","conf"],"additionalProperties":false,"properties":{"track_id":{"type":"string"},"position_ep":{"$ref":"#/$defs/vec3"},"radius_m":{"type":"number"},"swept_radius_m":{"anyOf":[{"type":"number"},{"type":"null"}]},"bbox_xyxy":{"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4},"caption":{"anyOf":[{"type":"string"},{"type":"null"}]},"matched_mention_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"conf":{"$ref":"#/$defs/prob"}}}},
   "tags": {"type":"array","items":{"type":"object","required":["label","kind","conf"],"properties":{"label":{"type":"string"},"kind":{"enum":["room","object","opening","stairs","door"]},"position_ep":{"anyOf":[{"$ref":"#/$defs/vec3"},{"type":"null"}]},"conf":{"$ref":"#/$defs/prob"}}}},
   "region_belief": {"type":"object","additionalProperties":{"$ref":"#/$defs/prob"}},
   "models": {"type":"object","additionalProperties":{"type":"string"},"description":"component -> model id@weights sha"}
 }
}
```

#### SubgoalProposal/1  (W4/W5 → W2; the Track-A W4→W2 contract)

```json
{
 "$id": "havln-team/contracts/SubgoalProposal/1",
 "title": "SubgoalProposal/1: what a policy asks the safety executor to do next (Track A). Owner W2 (consumer), producers W4/W5. Policies never emit MOVE_FORWARD directly. stop_* kinds hand the goal belief to the executor, which picks the exact STOP point (max P(within 3 m), reachable, clearance-safe) and issues STOP.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","t","source","kind","valid_for_steps","confidence"],
 "properties": {
   "contract": {"const":"SubgoalProposal/1"},
   "t": {"type":"integer","minimum":0},
   "source": {"type":"object","required":["policy","version"],"properties":{"policy":{"type":"string"},"version":{"type":"string"}}},
   "kind": {"enum":["waypoint","heading","explore_frontier","look_around","stop_here","stop_at"]},
   "target_ep": {"anyOf":[{"$ref":"#/$defs/vec3"},{"type":"null"}]},
   "heading_ep": {"anyOf":[{"type":"number"},{"type":"null"}]},
   "tolerance_m": {"type":"number","minimum":0},
   "waypoint_hints_ep": {"type":"array","items":{"$ref":"#/$defs/vec3"},"maxItems":16},
   "valid_for_steps": {"type":"integer","minimum":1,"maximum":500},
   "sweep": {"anyOf":[{"type":"object","required":["n_turns","direction"],"properties":{"n_turns":{"type":"integer","minimum":1,"maximum":24},"direction":{"enum":["left","right"]},"pitch_deg":{"anyOf":[{"type":"number"},{"type":"null"}]}}},{"type":"null"}]},
   "stop_belief": {"anyOf":[{"type":"object","properties":{"goal_ep":{"anyOf":[{"$ref":"#/$defs/vec3"},{"type":"null"}]},"cov_xy":{"anyOf":[{"type":"array","items":{"type":"array","items":{"type":"number"}}},{"type":"null"}]},"samples_ep":{"type":"array","items":{"$ref":"#/$defs/vec3"}},"p_within_3m_here":{"anyOf":[{"$ref":"#/$defs/prob"},{"type":"null"}]}}},{"type":"null"}]},
   "social": {"anyOf":[{"type":"object","properties":{"min_person_clearance_m":{"anyOf":[{"type":"number"},{"type":"null"}]},"prefer_side":{"anyOf":[{"enum":["left","right"]},{"type":"null"}]}}},{"type":"null"}]},
   "confidence": {"$ref":"#/$defs/prob"},
   "rationale": {"type":"string","maxLength":400}
 },
 "allOf": [{"if":{"properties":{"kind":{"enum":["waypoint","stop_at"]}}},"then":{"required":["target_ep"],"properties":{"target_ep":{"$ref":"#/$defs/vec3"}}}},{"if":{"properties":{"kind":{"const":"heading"}}},"then":{"required":["heading_ep"],"properties":{"heading_ep":{"type":"number"}}}},{"if":{"properties":{"kind":{"const":"look_around"}}},"then":{"required":["sweep"]}},{"if":{"properties":{"kind":{"enum":["stop_here","stop_at"]}}},"then":{"required":["stop_belief"]}}]
}
```

#### ExecutorReport/1  (W2 → W4/W5)

```json
{
 "$id": "havln-team/contracts/ExecutorReport/1",
 "title": "ExecutorReport/1: executor's answer to a proposal. Owner W2. Budget manager lives in the executor (reserve >= 60 actions).",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","t","proposal_t","status","actions_emitted","actions_used","actions_remaining","contacts_detected"],
 "properties": {
   "contract": {"const":"ExecutorReport/1"},
   "t": {"type":"integer","minimum":0},
   "proposal_t": {"type":"integer","minimum":0},
   "status": {"enum":["progressing","reached","blocked","unreachable_in_map","need_observation","budget_low","sweep_denied","stop_issued","contact_detected"]},
   "actions_emitted": {"type":"array","items":{"$ref":"#/$defs/action"}},
   "actions_used": {"type":"integer","minimum":0,"maximum":500},
   "actions_remaining": {"type":"integer","minimum":0,"maximum":500},
   "min_clearance_m": {"anyOf":[{"type":"number"},{"type":"null"}]},
   "contacts_detected": {"type":"integer","minimum":0},
   "stop_point_ep": {"anyOf":[{"$ref":"#/$defs/vec3"},{"type":"null"}]},
   "notes": {"type":"string","maxLength":400}
 }
}
```

#### RolloutRecord/1  (W1 runner (signed) → W5/W6/scorer; = C10 `rollout.schema.json`)

```json
{
 "$id": "havln-team/contracts/RolloutRecord/1",
 "title": "RolloutRecord/1: one executed episode = one candidate tape. Producer: W1 runner (signs inputs_used/audit). Consumers: W5 selector, W6 release, scorer. Contains NO ground-truth metrics (those live in ScoreResult/1).",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","episode_id","split","rollout_id","agent_fp","seed","mode","actions","stopped","contacts_detected","inputs_used","audit_sha256","created_utc"],
 "properties": {
   "contract": {"const":"RolloutRecord/1"},
   "episode_id": {"$ref":"#/$defs/episode_id"},
   "split": {"$ref":"#/$defs/split"},
   "rollout_id": {"type":"string"},
   "agent_fp": {"$ref":"#/$defs/sha256"},
   "seed": {"type":"integer","minimum":0},
   "mode": {"$ref":"#/$defs/mode"},
   "regime_during_rollout": {"$ref":"#/$defs/regime"},
   "actions": {"type":"array","items":{"$ref":"#/$defs/action"},"minItems":1,"maxItems":500},
   "stopped": {"type":"boolean"},
   "final_pose_ep": {"type":"object","properties":{"position_ep":{"$ref":"#/$defs/vec3"},"yaw_ep":{"type":"number"}}},
   "contacts_detected": {"type":"integer","minimum":0},
   "self_confidence": {"anyOf":[{"$ref":"#/$defs/prob"},{"type":"null"}]},
   "stop_belief": {"anyOf":[{"type":"object"},{"type":"null"}]},
   "model_calls": {"type":"object","properties":{"n":{"type":"integer","minimum":0},"cache_hits":{"type":"integer","minimum":0},"usd":{"type":"number"}}},
   "wall_s": {"type":"number"},
   "inputs_used": {"type":"array","items":{"$ref":"#/$defs/input_kind"},"uniqueItems":true},
   "audit_sha256": {"$ref":"#/$defs/sha256"},
   "created_utc": {"$ref":"#/$defs/utc"}
 }
}
```

#### SelectionRecord/1  (W5 → W6)

```json
{
 "$id": "havln-team/contracts/SelectionRecord/1",
 "title": "SelectionRecord/1: how the submitted tape for an episode was chosen. Owner W5. flags.multi_rollout=true is only legal after a written organizer ruling (see critique item K4).",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","episode_id","method","candidates","chosen_rollout_id"],
 "properties": {
   "contract": {"const":"SelectionRecord/1"},
   "episode_id": {"$ref":"#/$defs/episode_id"},
   "method": {"type":"object","required":["name","version","flags"],"properties":{"name":{"type":"string"},"version":{"type":"string"},"flags":{"type":"object","required":["multi_rollout","siblings"],"properties":{"multi_rollout":{"type":"boolean"},"siblings":{"type":"boolean"}}}}},
   "candidates": {"type":"array","minItems":1,"items":{"type":"object","required":["rollout_id","contacts_detected"],"properties":{"rollout_id":{"type":"string"},"stop_cluster":{"anyOf":[{"type":"string"},{"type":"null"}]},"contacts_detected":{"type":"integer","minimum":0},"verifier_score":{"anyOf":[{"type":"number"},{"type":"null"}]}}}},
   "chosen_rollout_id": {"type":"string"},
   "margin": {"anyOf":[{"type":"number"},{"type":"null"}]}
 }
}
```

#### ScoreRequest/1  (anyone → W1 farm)

```json
{
 "$id": "havln-team/contracts/ScoreRequest/1",
 "title": "ScoreRequest/1: ask the W1 farm to replay tapes (kind=replay|cert) or to run an agent closed-loop (kind=rollout). Idempotent: task_id = sha256(canonical request).",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","kind","split","eval_set","regimes","priority","requester"],
 "properties": {
   "contract": {"const":"ScoreRequest/1"},
   "kind": {"enum":["replay","cert","rollout"]},
   "tapes_ref": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "agent_ref": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "k_rollouts": {"type":"integer","minimum":1,"maximum":64},
   "split": {"$ref":"#/$defs/split"},
   "eval_set": {"$ref":"#/$defs/eval_set"},
   "episode_ids": {"anyOf":[{"type":"array","items":{"$ref":"#/$defs/episode_id"}},{"type":"null"}]},
   "regimes": {"type":"array","items":{"$ref":"#/$defs/regime"},"minItems":1},
   "sensors": {"enum":["depth2x2","rgbd"]},
   "mode": {"$ref":"#/$defs/mode"},
   "fingerprint_expected": {"anyOf":[{"$ref":"#/$defs/sha256"},{"type":"null"}]},
   "priority": {"enum":["p0","p1","p2"]},
   "requester": {"$ref":"#/$defs/task_id"}
 },
 "allOf": [{"if":{"properties":{"kind":{"const":"rollout"}}},"then":{"required":["agent_ref","k_rollouts","mode"]},"else":{"required":["tapes_ref"]}}]
}
```

#### ScoreResult/1  (W1 farm → anyone; rows = C10 per-episode columns)

```json
{
 "$id": "havln-team/contracts/ScoreResult/1",
 "title": "ScoreResult/1: per-regime, per-shard result. Owner W1. aggregate uses havln_tools.aggregate(cr_mode='human_influenced').",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","task_id","fingerprint","regime","split","eval_set","rows"],
 "properties": {
   "contract": {"const":"ScoreResult/1"},
   "task_id": {"$ref":"#/$defs/sha256"},
   "fingerprint": {"$ref":"#/$defs/sha256"},
   "regime": {"$ref":"#/$defs/regime"},
   "split": {"$ref":"#/$defs/split"},
   "eval_set": {"$ref":"#/$defs/eval_set"},
   "scan": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "rows": {"type":"array","items":{"type":"object","required":["episode_id","steps_executed","stopped","collisions","collision_steps"],"properties":{"episode_id":{"$ref":"#/$defs/episode_id"},"steps_executed":{"type":"integer","minimum":0},"stopped":{"type":"boolean"},"distance_to_goal":{"anyOf":[{"type":"number"},{"type":"null"}]},"success":{"anyOf":[{"type":"boolean"},{"type":"null"}]},"collisions":{"type":"integer","minimum":0},"collision_steps":{"type":"array","items":{"type":"integer","minimum":0}},"frames_seen":{"type":"array","items":{"type":"integer","minimum":0}},"final_position":{"$ref":"#/$defs/vec3"},"SR":{"anyOf":[{"enum":[0,1]},{"type":"null"}]},"CR":{"anyOf":[{"enum":[0,1]},{"type":"null"}]},"TCR":{"anyOf":[{"type":"integer","minimum":0},{"type":"null"}]}}}},
   "aggregate": {"anyOf":[{"type":"object","required":["n","SR","NE","CR","TCR","Score","cr_mode"],"properties":{"n":{"type":"integer","minimum":0},"SR":{"type":"number"},"NE":{"type":"number"},"CR":{"type":"number"},"TCR":{"type":"number"},"Score":{"type":"number"},"cr_mode":{"const":"human_influenced"}}},{"type":"null"}]},
   "timing": {"type":"object","properties":{"steps_per_s":{"type":"number"},"wall_s":{"type":"number"}}}
 }
}
```

#### PlanRequest/1  (oracle/ callers (W4 teacher, W7 Track B, W2 oracle eval) → W1 planning service)

```json
{
 "$id": "havln-team/contracts/PlanRequest/1",
 "title": "PlanRequest/1 (PRIVILEGED, oracle/ only): the Track-B 'goal point + optional waypoint hints -> actions' contract, also used by the DAgger/RL teacher (purpose=teacher) and oracle-goal evaluations. Served by W1 planning service; token-gated.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","mode","token","scan","start","goal_world","goal_radius_m","inflate_m","human_margin_m","frames","max_actions","purpose"],
 "properties": {
   "contract": {"const":"PlanRequest/1"},
   "mode": {"const":"privileged"},
   "token": {"type":"string"},
   "scan": {"type":"string"},
   "start": {"type":"object","required":["position_world","rotation_world_xyzw"],"properties":{"position_world":{"$ref":"#/$defs/vec3"},"rotation_world_xyzw":{"$ref":"#/$defs/quat_xyzw"}}},
   "goal_world": {"$ref":"#/$defs/vec3"},
   "goal_radius_m": {"type":"number","minimum":0,"maximum":3.0},
   "stop_target": {"enum":["goal","max_p_within_3m"]},
   "goal_samples_world": {"type":"array","items":{"$ref":"#/$defs/vec3"}},
   "waypoint_hints": {"type":"array","items":{"type":"object","required":["position_world"],"properties":{"position_world":{"$ref":"#/$defs/vec3"},"radius_m":{"type":"number"}}}},
   "inflate_m": {"type":"number","minimum":0,"maximum":0.6},
   "human_margin_m": {"type":"number","minimum":0},
   "frames": {"anyOf":[{"const":"all"},{"type":"array","items":{"type":"integer","minimum":0,"maximum":119}}]},
   "max_actions": {"type":"integer","minimum":1,"maximum":500},
   "purpose": {"enum":["teacher","trackB","oracle_eval"]}
 }
}
```

#### PlanResult/1  (W1 planning service → oracle/ callers)

```json
{
 "$id": "havln-team/contracts/PlanResult/1",
 "title": "PlanResult/1 (PRIVILEGED): verified action list.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","actions","stop_world","clearance_min_m","verified"],
 "properties": {
   "contract": {"const":"PlanResult/1"},
   "actions": {"type":"array","items":{"$ref":"#/$defs/action"},"minItems":1,"maxItems":500},
   "stop_world": {"$ref":"#/$defs/vec3"},
   "clearance_min_m": {"type":"number"},
   "verified": {"type":"object","required":["regimes","any_collision"],"properties":{"regimes":{"type":"array","items":{"$ref":"#/$defs/regime"}},"any_collision":{"type":"boolean"}}},
   "warnings": {"type":"array","items":{"type":"string"}}
 }
}
```

#### GoalCandidates/1  (W7 (oracle/); = C10 `candidates.schema.json`)

```json
{
 "$id": "havln-team/contracts/GoalCandidates/1",
 "title": "GoalCandidates/1 (PRIVILEGED, oracle/ only): episode -> ranked candidate goals for Track B / oracle analysis. Owner W7.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","episode_id","scan","candidates","fusion"],
 "properties": {
   "contract": {"const":"GoalCandidates/1"},
   "episode_id": {"$ref":"#/$defs/episode_id"},
   "trajectory_key": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "scan": {"type":"string"},
   "candidates": {"type":"array","minItems":1,"items":{"type":"object","required":["cand_id","goal_world","score","rank"],"properties":{"cand_id":{"type":"string"},"goal_world":{"$ref":"#/$defs/vec3"},"viewpoint_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"floor_index":{"anyOf":[{"type":"integer"},{"type":"null"}]},"geodesic_m":{"anyOf":[{"type":"number"},{"type":"null"}]},"euclid_m":{"anyOf":[{"type":"number"},{"type":"null"}]},"score":{"type":"number"},"rank":{"type":"integer","minimum":1},"features":{"type":"object","additionalProperties":{"type":["number","string","boolean","null"]}},"sources":{"type":"array","items":{"type":"string"}}}}},
   "fusion": {"type":"object","required":["method","version"],"properties":{"method":{"type":"string"},"version":{"type":"string"}}},
   "stop_point": {"anyOf":[{"type":"object","required":["position_world","p_within_3m"],"properties":{"position_world":{"$ref":"#/$defs/vec3"},"p_within_3m":{"$ref":"#/$defs/prob"}}},{"type":"null"}]}
 }
}
```

#### LedgerResult/1  (everyone → ledger via `havln_tools.ledger.append()`; = C10 `ledger_result` + C5 fields)

```json
{
 "$id": "havln-team/contracts/LedgerResult/1",
 "title": "LedgerResult/1: one record per (run, subset, regime) = C10 ledger_result.schema.json field names PLUS the C5 additions task_id, hypothesis (pre-registered), agent_fp, fingerprint, k_rollouts, compliance. Written only by havln_tools.ledger.append() as ONE FILE PER RECORD (ledger/results/<run_id>.json) to avoid append conflicts; results.jsonl and RESULTS.md are generated. Rule: no run_id, no claim.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","run_id","created_at","owner","task_id","hypothesis","benchmark","git_sha","dirty","config_hash","image_digest","data_fingerprint","mode","split","subset","rollout_regime","replay_regime","agent_fp","fingerprint","compliance"],
 "properties": {
   "contract": {"const":"LedgerResult/1"},
   "run_id": {"type":"string","pattern":"^[0-9A-HJKMNP-TV-Z]{26}$","description":"ULID (time-sortable)"},
   "created_at": {"$ref":"#/$defs/utc"},
   "owner": {"type":"string","description":"WS/session, e.g. W2/session_abc"},
   "task_id": {"$ref":"#/$defs/task_id"},
   "hypothesis": {"type":"string","minLength":10,"description":"pre-registered before the run: what should change and by how much"},
   "benchmark": {"type":"string","description":"C10 benchmark id (B0..B8) or ad-hoc experiment tag"},
   "git_sha": {"type":"string","pattern":"^[0-9a-f]{7,40}$"},
   "dirty": {"type":"boolean"},
   "config_hash": {"type":"string","pattern":"^sha256:[0-9a-f]{64}$"},
   "image_digest": {"type":"string","pattern":"^sha256:[0-9a-f]{64}$"},
   "data_fingerprint": {"type":"object","additionalProperties":{"type":"string"}},
   "mode": {"enum":["compliant","privileged","oracle_goal"]},
   "split": {"$ref":"#/$defs/split"},
   "subset": {"type":"object","required":["name","n","ids_sha"],"properties":{"name":{"$ref":"#/$defs/eval_set"},"n":{"type":"integer","minimum":0},"ids_sha":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"}}},
   "rollout_regime": {"$ref":"#/$defs/regime"},
   "replay_regime": {"$ref":"#/$defs/regime"},
   "k_rollouts": {"type":"integer","minimum":1},
   "agent_fp": {"$ref":"#/$defs/sha256"},
   "fingerprint": {"$ref":"#/$defs/sha256"},
   "metrics": {"anyOf":[{"type":"object","required":["SR","NE","CR","TCR","Score"],"properties":{"SR":{"type":"number"},"SR_ci95":{"type":"array","items":{"type":"number"},"minItems":2,"maxItems":2},"NE":{"type":"number"},"CR":{"type":"number"},"TCR":{"type":"number"},"Score":{"type":"number"},"contact_free_rate":{"type":"number"},"paired_vs":{"anyOf":[{"type":"string"},{"type":"null"}]},"paired_delta_SR":{"anyOf":[{"type":"number"},{"type":"null"}]},"paired_p":{"anyOf":[{"type":"number"},{"type":"null"}]},"cr_mode":{"enum":["human_influenced","human_influenced_scaled","all"]}}},{"type":"null"}]},
   "expected_band": {"type":"object"},
   "pass": {"anyOf":[{"type":"boolean"},{"type":"null"}]},
   "per_episode": {"anyOf":[{"type":"object","required":["path","sha256"],"properties":{"path":{"type":"string"},"sha256":{"type":"string"}}},{"type":"null"}]},
   "runtime": {"type":"object","properties":{"wall_s":{"type":"number"},"gpu_s":{"type":"number"},"steps_per_s":{"type":"number"},"episodes_per_h":{"type":"number"},"llm_usd":{"type":"number"}}},
   "parents": {"type":"array","items":{"type":"string"}},
   "compliance": {"type":"object","required":["inputs_used"],"properties":{"inputs_used":{"type":"array","items":{"$ref":"#/$defs/input_kind"}},"audit_sha256":{"anyOf":[{"$ref":"#/$defs/sha256"},{"type":"null"}]},"flags":{"type":"object","additionalProperties":{"type":"boolean"}}}},
   "notes": {"type":"string","maxLength":2000}
 }
}
```

#### SubmissionRecord/1  (W6 → human sign-off → CodaBench + report; = C10 `ledger_submission` + `manifest`)

```json
{
 "$id": "havln-team/contracts/SubmissionRecord/1",
 "title": "SubmissionRecord/1: one per upload (ledger/submissions/<zip_sha256>.json) = C10 ledger_submission + compliance manifest, with C10 gates G1-G6 plus C5's G7 (bit-reproducible regeneration from the RC tag). Owner W6; G6 = human sign-off.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","phase","zip_sha256","release_tag","run_ids","agent_fp","mode","inputs_used","flags","gates","predicted_envelope","approved_by"],
 "properties": {
   "contract": {"const":"SubmissionRecord/1"},
   "phase": {"enum":["phase1","phase2"]},
   "zip_sha256": {"$ref":"#/$defs/sha256"},
   "release_tag": {"type":"string","pattern":"^rc-20[0-9]{6}-[0-9]+$"},
   "run_ids": {"type":"array","items":{"type":"string"},"minItems":1},
   "agent_fp": {"$ref":"#/$defs/sha256"},
   "mode": {"$ref":"#/$defs/mode"},
   "inputs_used": {"type":"array","items":{"$ref":"#/$defs/input_kind"}},
   "flags": {"type":"object","required":["multi_rollout","siblings","cross_episode_memory"],"properties":{"multi_rollout":{"type":"boolean"},"siblings":{"type":"boolean"},"cross_episode_memory":{"type":"boolean"}}},
   "gates": {"type":"object","required":["G1_contract","G2_compliance","G3_timing","G4_ledger","G5_new_sha","G6_human","G7_regenerated"],"properties":{"G1_contract":{"type":"boolean"},"G2_compliance":{"type":"boolean"},"G3_timing":{"type":"boolean"},"G4_ledger":{"type":"boolean"},"G5_new_sha":{"type":"boolean"},"G6_human":{"type":"boolean"},"G7_regenerated":{"type":"boolean"}}},
   "predicted_envelope": {"type":"object","description":"min/max per metric over the release-gate regimes, from dev/lockbox calibration"},
   "approved_by": {"type":"string"},
   "uploaded_utc": {"anyOf":[{"$ref":"#/$defs/utc"},{"type":"null"}]},
   "codabench_submission_id": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "official": {"anyOf":[{"type":"object","properties":{"SR":{"type":"number"},"NE":{"type":"number"},"CR":{"type":"number"},"TCR":{"type":"number"},"Score":{"type":"number"}}},{"type":"null"}]},
   "delta_vs_predicted": {"anyOf":[{"type":"object"},{"type":"null"}]},
   "manifest_sha256": {"anyOf":[{"$ref":"#/$defs/sha256"},{"type":"null"}]},
   "rationale": {"type":"string","maxLength":1000}
 },
 "allOf": [{"if":{"properties":{"uploaded_utc":{"type":"string"}},"required":["uploaded_utc"]},"then":{"properties":{"gates":{"properties":{"G1_contract":{"const":true},"G2_compliance":{"const":true},"G3_timing":{"const":true},"G4_ledger":{"const":true},"G5_new_sha":{"const":true},"G6_human":{"const":true},"G7_regenerated":{"const":true}}}}}}]
}
```

#### TaskBrief/1  (lead/human → implementer (front matter of every brief))

```json
{
 "$id": "havln-team/contracts/TaskBrief/1",
 "title": "TaskBrief/1: YAML front matter of briefs/<WS>/<task-id>.md (validated in CI). Status is the single source for STATUS.md.",
 "type": "object",
 "additionalProperties": false,
 "required": ["contract","id","title","workstream","role","regime","status","created","timebox_agent_days","depends_on","contracts_in","contracts_out","eval_sets","compute_quota"],
 "properties": {
   "contract": {"const":"TaskBrief/1"},
   "id": {"$ref":"#/$defs/task_id"},
   "title": {"type":"string","maxLength":80},
   "workstream": {"enum":["W0","W1","W2","W3","W4","W5","W6","W7","INT","REV","OPS"]},
   "role": {"enum":["lead","implementer","reviewer","redteam","scribe"]},
   "regime": {"enum":["A","B","A+B"],"description":"A = code runs in the compliant inference path; B = oracle/ only"},
   "status": {"enum":["draft","ready","in_progress","blocked","review","done","killed"]},
   "owner_session": {"anyOf":[{"type":"string"},{"type":"null"}]},
   "created": {"type":"string","pattern":"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$"},
   "due": {"anyOf":[{"type":"string","pattern":"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$"},{"type":"null"}]},
   "timebox_agent_days": {"type":"number","exclusiveMinimum":0,"maximum":3},
   "depends_on": {"type":"array","items":{"$ref":"#/$defs/task_id"}},
   "blocks": {"type":"array","items":{"$ref":"#/$defs/task_id"}},
   "contracts_in": {"type":"array","items":{"type":"string","pattern":"^[A-Za-z]+/[0-9]+$"}},
   "contracts_out": {"type":"array","items":{"type":"string","pattern":"^[A-Za-z]+/[0-9]+$"}},
   "eval_sets": {"type":"array","items":{"$ref":"#/$defs/eval_set"}},
   "compute_quota": {"type":"object","required":["gpu_h","llm_usd"],"properties":{"gpu_h":{"type":"number"},"llm_usd":{"type":"number"},"replay_shards_in_flight":{"type":"integer","minimum":0}}},
   "kill_criterion": {"anyOf":[{"type":"string"},{"type":"null"}]}
 }
}
```


---

## 5. Shared-state conventions

### 5.1 Repository layout (C10's `havln2026/` + organizational files)

```
havln2026/
  AGENTS.md                 charter, C3 red lines, workflow, read-first list                 (Tier 2)
  DECISIONS.md              ADR log                                                          (Tier 2/3)
  RESULTS.md STATUS.md DIGEST/<date>.md   GENERATED (scribe) — never hand-edited
  briefs/<WS>/<task-id>.md  TaskBrief/1 front matter + spec + ## Log;  HANDOFF/<role>.md rolling notes (INT, leads)
  havln_tools/              C10: score contract grouping ledger manifest stats fusion facts.yaml;
    schemas/<Name>/<MAJOR>.json                                                              (Tier 2; CODEOWNERS = INT + human)
  synth/  agent/{io.py, navstack/, perception/, mapping/, executor/, policies/<backbone>/, selection/}   [A]
  oracle/{teacher/, navplan/, trackb/, gt_eval/, analysis/}                                  [P]
  sim/{envfactory, frame_scheduler, navstepper, replay_scorer, rollout_worker, audit}.py     [container]
  benchmarks/ (B-xx + expected bands generated from the §8.2 gate table)   tests/{unit,synth,compliance,sim,gpu,official,fixtures}
  ledger/results/<ULID>.json  ledger/submissions/<zip_sha256>.json   (one file per record; *.jsonl and RESULTS.md generated)
  data/val_unseen_splits.json (frozen, hash in facts)   report/   docker/   .github/workflows/{pr,nightly,weekly}.yml
```

- Branches are `ws<N>/<task-id>-<slug>`. Merges are squash merges through the merge queue. PR titles are `[W2-T03] …`.
- Release tags are `rc-YYYYMMDD-N`; nightly tags are `nightly-YYYYMMDD`.
- C10's import contracts apply: `agent` must not import `oracle`, `sim.privileged`, `habitat` or `habitat_sim`; it talks to the sim only through `agent/io.py`.

### 5.2 Data lake (shared POSIX; extends C1 §5)

```
/lake/raw/                 ro: official data (havln2 layout), MP3D (licensed storage only), HAPS2_0
/lake/quarantine/          NEVER mounted into agent processes: human_motion*.json, HA-DE/** (connectivity, human_motion_text.json,
                           R2R_test.json), collision_num_*.json, test_episode_index / test_trajectory_table / mp3d_test_scan_room_labels,
                           val GT fields; plus the hash blocklist (B12: Matterport3DSimulator web/app/sample_room_paths.json)
/lake/test_bundle/         Phase-2 bundle; mounted only into the release runner
/lake/navmesh_cache/<scan>/<scan>_<fff>.navmesh + MANIFEST.json   single writer, then ro
/lake/renders/ /lake/features/<extractor@ver>/ /lake/llm_cache/<provider>/<model>/<sha256(request)>.json (gateway-only writer)
/lake/models/<name>@<sha>/ /lake/datasets/<name>@<ver>/ (manifest lists episode ids + scans; C10 C6 check)
/lake/rollouts/<agent_fp>/<split>/<scan>/<episode>_<rollout>.json   /lake/tapes/<sha256>.json   /lake/submissions/<zip_sha256>.zip
/lake/results/<run_id>/<subset>.parquet (per-episode, C10 columns)   /lake/scratch/<session_id>/ (GC after 7 days)
```

Write rules:
- Content-addressed paths are immutable.
- All writes are atomic (`.partial` + `os.replace`).
- Each prefix has one writer.
- Agents delete only inside their own scratch.
- Results from different fingerprints are never merged (C1 §7).

### 5.3 Ledger, fingerprints, boards

- **agent_fp** = sha256 of {git_sha (clean tree), resolved config, model weight shas, LLM model ids + prompt-template shas}.
- **fingerprint** = sha256 of {agent_fp, image digest, data fingerprint, subset name + ids_sha, rollout + replay regime, K, seeds}.
- Records from a dirty tree are allowed but are excluded from boards and gates.
- **`hypothesis` is mandatory** in `LedgerResult/1`: pre-registration (C6 §5) makes the winner's curse visible.
- `RESULTS.md` (generated nightly and on each official result; extends C10 §10):
  1. The official submissions ledger: #, UTC time, phase, zip sha256[:12], RC tag, agent_fp[:12], predicted envelope, official 10-dp metrics, delta, gates G1–G7.
  2. The **dev champion board**: run_id, date, WS, SR ± CI, NE, CR, TCR, Score, worst-regime Score, contact-free rate, K, cost per episode.
  3. C6's dashboards: oracle ladder, goal/stop metrics per stratum, executor robustness, ablations, official parity, budget and audit.
  4. The **lockbox look log** (≤ 4).
  5. g60 regression status.
- Every brief, README rule and digest refers to the ledger. "Log in RESULTS.md" (briefs README L8, W0 L19, W6 L7) is replaced by "append through `havln_tools.ledger`".

### 5.4 `STATUS.md`, `DECISIONS.md`, facts registry, digest

- `STATUS.md` is generated from brief front matter: tasks by status per WS, blocked items with their reasons, stale tasks, and the next gate with its open criteria.
- `DECISIONS.md` ADR format: `ADR-NNN · date · status · context · decision · consequences · evidence (run_ids, files) · approver`. Seed it with:

  | ADR | Decision |
  |---|---|
  | ADR-001 | Track A only by default; gray levers OFF until answered (`03-organizer-questions.md`) |
  | ADR-002 | Submission policy (§8.3) |
  | ADR-003 | Freeze `data/val_unseen_splits.json` + lockbox rule (§6) |
  | ADR-004 | Regime ids, RELEASE-SWEEP, NIGHTLY-4 |
  | ADR-005 | One safety-margin table (K9) |
  | ADR-006 | Sensor constants (after W1-T01) |
  | ADR-007 | W5-S default / W5-M flag |
  | ADR-008 | Primary backbone (Nov 3) |
  | ADR-009 | Freeze rules |

- **Facts registry** `havln_tools/facts.yaml`: id, value, source (file:line or URL), confidence, and the test that pins it. Code imports constants from it (split sizes, CR denominators, camera height, regimes, split hash) and never hard-codes them. Changing a fact is Tier 2.
  - Evidence that this is needed, all from Oct 24 alone:
    - the CR denominator and the `aggregate()` default changed;
    - the strategy went v1.0 → v1.1 → v1.2;
    - W2's camera height was wrong and then fixed;
    - the strategy header says "13 passing tests" while §11 says 15 (and W6 L14 says 13, though C10 added more);
    - three hold-out definitions appeared.
- **Digest** (05:30 UTC), one screen:
  - yesterday's merges;
  - board deltas (run_ids);
  - failing nightly tests and NIGHTLY-4 status;
  - pending decisions for H (≤ 10, each with a recommended option);
  - blocked tasks;
  - CodaBench and organizer status;
  - compute and LLM spend vs quota.

### 5.5 Quotas, LLM gateway, secrets, licences

- Queues have priorities p0 (interactive / smoke), p1 (nightly / dev) and p2 (sweeps). Each brief carries a `compute_quota` that the farm enforces per session. 22:00–05:00 is reserved for the RC evaluation and the sweep.
- **One model gateway** handles every call: a request-hash cache (the reproducibility mechanism, because the Claude API rejects temperature since Oct 21 and has no logprobs; B3), multi-provider routing, back-off and per-task spend.
- Keys live only in the gateway's environment.
- MP3D stays on licensed storage (C2 R22). Whether test-scene renders may be sent to closed APIs is an open licence question (§13), so prefer local open-weight models for test imagery. Q12 of the clarification also prefers open models.

---

## 6. Golden-set protocol (val_unseen) and test hygiene

**Canonical sets** = the committed `data/val_unseen_splits.json` (seed 20261024; verified disjoint and nested: smoke ⊂ quick ⊂ dev, dev ∩ lockbox = ∅). Freeze it by sha256 in `facts.yaml` (ADR-003).

| Set | Content | Episodes / trajectories | Non-zero baseline share | Who may run it | Purpose |
|---|---|---|---|---|---|
| `syn-*`, `ha-mini`, `g60` | C10 fixtures (synthetic world, 17DRP5sb8fy, golden 60) | — | — | anyone, CI | unit / regression |
| `smoke` | 20 dev trajectories | 60 / 20 | 10.0 % | anyone, p0 | catch breakage; required for `agent/` PRs. **Never for selection** (MDE ≈ 20 pp) |
| `quick` | ~100 dev trajectories (scan × floor-change × length) | 306 / 102 | 6.9 % | anyone, p0/p1 | fast iteration; directional only (MDE 8.8 pp) |
| `dev` | 8 scans: 2azQ1b91cZZ, TbHJrupSAjP, X7HyMhZNoso, Z6MFQCViBuw, oLBMNvg9in8, pLe4wQe7qrG, x8F5xyUWy9e, zsNo4HB9uLZ | 1,413 / 471 | 8.9 % | anyone, p1 | development, selection, ablations |
| `lockbox` | 8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX | 426 / 142 | 7.7 % | **W6 only, at gates** | confirmation: ≤ 4 looks total, one per gate G5–G8, one pre-registered champion per look, every look logged |
| `val_seen` | scenes overlap train | 778 | — | anyone | optimistic sanity check; Phase-1 calibration |
| `trainho` | 6 scan-disjoint train folds (C6) | — | — | anyone | fitting and validating calibrators, verifiers and prompts (never val) |
| `test` | Phase-2 bundle | 3,408 / 1,136 | — | **release runner only** | production runs; validity checks only |

**Conflict to resolve today (K6).** C6's final report proposes different partitions: DEV = 7 scans / 1,380 episodes; HOLD = oLBMNvg9in8, X7HyMhZNoso, x8F5xyUWy9e, 8194nk5LbLH (459 episodes), with ≤ 3 looks at G5–G7. C10 says the hold-out is used "only at gates G7 and G8". My own independent seeded draw gave yet another set (EU6Fwq7SyZv, TbHJrupSAjP, X7HyMhZNoso; `c5work/evalsets.py`).

The committed file is the only one in shared state and the one strategy v1.2 §12 cites, so it should win. C6's text and C10's G7/G8 wording should be amended to match. This is exactly the drift the facts registry and Tier-2 rule are meant to stop.

**Statistical power** (paired McNemar-style MDE, α 0.05 two-sided, power 0.8). DE is the design effect for 3 instructions per trajectory; C6 measured ICC 0.26–0.35, i.e. DE 1.5–1.7. "disc" is the fraction of episodes where the two variants disagree.

| Set | n | MDE disc .10 DE 1.5 | MDE disc .20 DE 1.5 | MDE disc .20 DE 2.0 | ±95 % CI of SR at .5 (DE 1.5) |
|---|---|---|---|---|---|
| smoke | 60 | 14.0 pp | 19.8 pp | 22.9 pp | ±15.5 pp |
| quick | 306 | 6.2 pp | 8.8 pp | 10.1 pp | ±6.9 pp |
| dev | 1,413 | 2.9 pp | 4.1 pp | 4.7 pp | ±3.2 pp |
| lockbox | 426 | 5.3 pp | 7.4 pp | 8.6 pp | ±5.8 pp |
| val_unseen (all) | 1,839 | 2.5 pp | 3.6 pp | 4.1 pp | ±2.8 pp |
| test (reference) | 3,408 | 1.9 pp | 2.6 pp | 3.0 pp | ±2.1 pp |

These agree with C6, which reports 2.4 / 3.3 pp at 10 / 20 % discordance on 1,839 episodes. C6 also warns that predicting test from val carries ±8 pp from building variation.

**Winner's curse.** Pick the best of M variants with equal true SR on dev (paired SE 1.46 pp). The expected inflation is:

| M | 5 | 10 | 20 | 50 | 100 |
|---|---|---|---|---|---|
| Inflation (pp) | 1.7 | 2.3 | 2.7 | 3.3 | 3.7 |

With 16–20 agents, M reaches 50–100 per month unless the number of decisions is capped. Adopt C6's rule: a change is accepted only with ΔSR ≥ +1.0 pp and McNemar p < 0.05; about 10 decisions per week, with the threshold raised to +1.5 pp beyond that.

**Rules (enforced by tooling where possible):**
1. Agents never open test episodes. Only the release runner reads `/lake/test_bundle/`. CI fails if test-instruction text appears in any committed prompt or file (C10; salted 8-gram hashes held by the release runner). No human reads test instructions or overrides episodes (C6).
2. No training on val (clarification Q10). That includes verifiers, calibrators and few-shot examples, which are fitted on train folds; a prompt edit motivated by dev is first validated on `trainho` (C6).
3. Every comparison is **paired** on identical episode sets, reported with trajectory- and scan-bootstrap CIs, and pre-registered (`hypothesis`).
4. Lockbox: W6 only, at most 4 looks, a pre-registered champion only. A failed look is never tuned against; fixes are re-justified on dev.
5. With only 8 dev scans, report per-scan results and use a scan bootstrap for generalization claims (test has 18 different buildings; C2 R12).
6. Phase-1 uploads contain only genuine agent outputs or C6's disclosed calibration probes (P1-a…e), never GT-derived tapes.
7. A change to a split file creates a new version and invalidates board comparisons across versions.

---

## 7. Review and merge policy

### 7.1 Risk tiers

| Tier | Scope | Approval | Required checks |
|---|---|---|---|
| 0 | Docs, research notes, brief logs, own `oracle/analysis` notebooks | self-merge | PR CI |
| 1 | Code inside one WS package (`agent/<pkg>/`, `oracle/<pkg>/`, `train/`, non-scorer `sim/`) | 1 reviewer session (not the author) or the WS lead | PR CI (C10: unit, synth, compliance-static, `lint-imports`, ledger check, py3.8 + 3.11, ≤ 90 s) + test-text guard; **`agent/` PRs: a smoke run cited by run_id with 0 contacts and no SR drop > 10 pp vs the nightly RC** (smoke catches only gross breakage) |
| 2 | `havln_tools/schemas/`, `agent/io.py`, `agent/navstack/api.py`, `havln_tools/{score,contract,facts}`, `data/val_unseen_splits.json`, `sim/{replay_scorer,rollout_worker,audit,frame_scheduler}`, `tests/compliance`, `AGENTS.md`, accepted ADRs | INT **and** human (CODEOWNERS) | Tier-1 checks + nightly container tests + ADR link |
| 3 | CodaBench uploads, organizer communication, account/registration changes | human only | `SubmissionRecord/1` with G1–G7 all true |

### 7.2 Mechanics

- Trunk-based: `main` is always green. A merge queue re-runs the checks on the merged result.
- PRs stay under ~800 changed lines, excluding generated files and fixtures. Squash merges. The REPORT block (§10) is mandatory.
- **Schema changes** arrive in their own PR (schema + fixtures + ADR).
  - Additive: INT approval.
  - Breaking: human approval, a 24 h notice in `STATUS.md`, and a 48 h dual-acceptance window.
  - Schema PRs merge only in the 12:00 UTC window.
- **Claims policy:** reviewers reject numbers that do not cite a clean-tree `run_id`. Autonomous agents otherwise produce plausible but unsupported figures.
- **Freezes:**
  - After G7 (Fri Nov 20), `agent/` accepts only fixes that come with a failing test or a paired dev non-regression run (C6), plus human approval.
  - After G8 (Fri Nov 27), only W6 (release manager) and H.
  - Ablations for the report continue in `oracle/analysis`.

### 7.3 Reviewer checklist (the REV session runs it verbatim)

1. The code respects the schemas (fixtures updated; versions unchanged unless an ADR exists).
2. Compliance:
   - no `oracle/`, `habitat`, `habitat_sim` or `sim.privileged` imports in `agent/`;
   - no quarantined or blocklisted paths;
   - no use of `scene_id` / `trajectory_id` / goals;
   - no cross-episode or cross-rollout state, unless an ADR flag permits it.
3. Tests added (unit / synth / property); CI green; smoke run_id cited for `agent/` changes.
4. Every number has a run_id with a pre-registered hypothesis; the comparison is paired.
5. Determinism: seeds fixed; model calls go through the gateway; no wall-clock dependence in agent logic (the virtual clock is used for rollouts).
6. Budget: TURN/LOOK usage counted; executor reserve ≥ 60.
7. The REPORT lists failures with episode ids.

---

## 8. Cadence

### 8.1 Daily loop (UTC)

| Time (UTC) | What | Who |
|---|---|---|
| 22:00 | Code cut: INT tags `nightly-YYYYMMDD` | INT (scheduled) |
| 22:00–05:00 | `nightly.yml`:<br>• container tests and g60;<br>• dev evaluation of the RC (K = 1 + W5-S) under the rollout regimes, then NIGHTLY-4 replay;<br>• training jobs (p1/p2);<br>• weekly (Sun) oracle ladder + taxonomy | farm |
| 05:30 | Scribe regenerates `RESULTS.md` / `STATUS.md` and writes `DIGEST/<date>.md` (≤ 10 pending decisions, each with a recommendation) | OPS |
| ~06:00 (shift to the human's timezone) | **Human block, 45–60 min:**<br>• digest (10 min);<br>• ADRs and Tier-2/3 items (20 min);<br>• today's upload or none: G6 sign-off (10 min);<br>• re-prioritise and kill/spawn tasks (10–20 min) | H |
| 07:00 | Fresh lead sessions read the digest and their WS status, update the backlog, and spawn or steer implementers | leads |
| 08:00–14:00 | **Upload window**, ≤ 2 per day. Nothing in the last 2 h of a UTC day, and never cancel a running job: cancelled and stuck submissions count against the quota (A12) | W6 + H |
| 12:00 | Schema-change merge window | INT |
| 07:00–21:00 | Implementers work; merge queue runs continuously; smoke/quick at p0 | all |
| 20:00 | Leads update `HANDOFF/` notes and the next-day plan; implementers checkpoint their brief logs | leads, implementers |

### 8.2 Weekly loop and gates (strategy v1.2 §6, plus dev thresholds from the v1.2 W4 row)

- **Monday:** taxonomy → leads re-plan; brief refresh.
- **Friday:** gate review with INT's gate packet: dev board, RELEASE-SWEEP result, lockbox look (W6), risks, and go/no-go per criterion.

| Gate | Date | Engineering acceptance | Dev threshold (K = 1, clean) | Official (v1.2) |
|---|---|---|---|---|
| G0 | Sat Oct 24 | registered; `03-organizer-questions.md` posted; MP3D requested; INT-T00 started | — | — |
| M1 | Mon Oct 26 | C10 S1–S4 for both digests; STOP-only ZIPs validated; schemas + splits frozen (Tier 2) | — | — |
| M2 | Wed Oct 28 | (MP3D) val_unseen navmesh cache; STOP-only = 8.473053; CMA reproduces README; runner + stub on HA-mini/smoke | — | — |
| M3 | Thu Oct 29 | L3 executor with GT goal SR ≥ 0.90 on dev | — | Phase-1 calibration set (C6 P1-a…e) if CodaBench is up |
| M4 | Fri Oct 30 | bundle inventoried (AT-W1-9); test navmesh cache; STOP-only anchor | — | STOP-only matches prediction |
| G5 | Nov 2–6 | zero-shot SimpleVLN + training-free guard integrated; G3 passed | SR ≥ 0.30 | test SR 0.28–0.36, Score 25–32 |
| G6 | Nov 9–13 | + learned Guard v2 + HA-R2R fine-tune | SR ≥ 0.40 by Nov 9 | SR 0.40–0.47, Score 36–43 |
| G7 | Nov 16–20 | + DAgger, per-decision voting, stop check; **architecture freeze Nov 20** | SR ≥ 0.46 by Nov 16, ≥ 0.50 at freeze | SR 0.46–0.54, Score 42–50 |
| G8 | Fri Nov 27 | final RC uploaded and scored; archive (ZIP, SubmissionRecord, regeneration proof) | lockbox look #4 | final K = 1 target Score 46–55 (60–66 only if K > 1 is allowed) |
| Close | Mon Nov 30, assume 15:59 UTC | last planned upload Sun Nov 29 12:00 UTC; Nov 30 for emergencies | — | — |

The G5 dev threshold of 0.30 is my derivation: the low end of v1.2's test range plus a 2 pp dev→test allowance. The others are v1.2's W4 row.

### 8.3 Submission policy (ADR-002; reconciles W0, W6, C2, C3, C6, B7 and v1.2)

- Whole-pipeline uploads only. No disjoint-subset A/B or probing (v1.2 §6, W6 L9). C6's disclosed Phase-1 calibration probes are allowed.
- At most 2 uploads per UTC day.
- Phase 2: ~20–30 uploads plus the STOP-only anchor; ≥ 30 slots in reserve.
- Every upload has G1–G7 true and H's sign-off.
- Upload a strong candidate early, because ties break on time.

---

## 9. Headcount: how many agents, and when coordination overhead dominates

**Model.** Three constraints bind before compute does. C1 sizes the farm at ~64 Habitat processes; with ~60 decisions × 1.5 s per episode, a dev K = 1 closed-loop run is ≈ 33 min on 64 workers and K = 8 ≈ 4.4 h.

1. **Human attention.** About 2 h/day: ~45–60 min decision block, ~10 min per lead touch-point, ~10 min for uploads and organizers. That saturates at **≈ 8 lead-level contacts per day**. Implementers never need the human directly.
2. **Seams.** Two implementers on one seam edit the same files and argue the same interface; together they produce less than one. The seam counts in §3 sum to ~22–23.
3. **Decision statistics.** Dev supports about 10 promotion decisions per week (C6) before the winner's curse eats the gains. Agents beyond what feeds those decisions mostly add indistinguishable variants.

Ephemeral reviewer sessions and the merge queue are **not** binding: a smoke gate is ~1.5 min on 64 workers.

| Phase | Dates | W0 | W1 | W2 | W3 | W4 | W5 | W6 | W7 | INT | REV/RT | **Total** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bootstrap | Oct 24 (≈ 8 h) | 1 | 1 | – | – | – | – | – | – | 1 | – | **3** |
| Week 0 | Oct 25–30 | 1* | 4 | 2 | 2 | 3 | – | 1 | 1 | 1 | 1 | **16** |
| Weeks 1–2 | Oct 31–Nov 13 | * | 2 | 3 | 3 | 5 | 2 | 1 | 1–2 | 1 | 2 | **20 (peak; 16 if seams are not ready)** |
| Week 3 | Nov 14–20 | * | 1 | 2 | 2 | 3 | 2 | 1 | 2 | 1 | 1 | **15** |
| Weeks 4–5 | Nov 21–30 | * | 1 | 1 | – | 1 | 1 | 2 | 2 | 1 | 1 | **10** |
| Report | Dec 1–12 | – | – | – | – | – | – | 1 | 2 | – | – | **3** |

\* W0 = the human plus a scheduled ops task. Total ≈ 600 agent-days.

**Hard cap: 24 concurrent task sessions** (reviewers excluded). Signs that overhead dominates:
- more than 10 pending human decisions per day;
- more than 2 implementers on one seam;
- more than 20 % of PRs needing a second rebase;
- more than 3 schema changes per week;
- more than 10 promotion decisions per week.

When those signs appear, shrink by killing the lowest-value seam, not a random agent.

**Tournaments are the exception to "one agent per seam".** Where the approach is uncertain (backbone bake-off, parser prompting, verifier design), 2–3 isolated attempts in separate directories are cheap to coordinate. They are judged by a pre-registered dev criterion and confirmed by a lockbox look at the next gate.

---

## 10. Agent-brief template (copy into `briefs/<WS>/<task-id>.md`)

```markdown
---
contract: TaskBrief/1
id: W2-T03
title: Per-step forward guard with pose-delta contact response
workstream: W2
role: implementer            # lead | implementer | reviewer | redteam | scribe
regime: A                    # A = runs in the compliant inference path; B = oracle/ only; A+B
status: ready                # draft | ready | in_progress | blocked | review | done | killed
owner_session: null
created: 2026-10-25
due: 2026-10-27
timebox_agent_days: 1.5      # <= 3; split otherwise
depends_on: [W1-T03, W2-T01]
blocks: [W4-T05]
contracts_in: [Observation/1, SubgoalProposal/1]
contracts_out: [ExecutorReport/1]
eval_sets: [syn-corridors, smoke, dev]
compute_quota: {gpu_h: 50, llm_usd: 0, replay_shards_in_flight: 32}
kill_criterion: "contacts on smoke > 0 after 2 iterations -> escalate to W2 lead"
---
## 1. Goal
One sentence + the metric that proves it (e.g. "0 contacts on syn-* and smoke; dev L3 SR not below the nightly RC (paired)").
## 2. Why it matters
2-3 lines; link the strategy section / ADR / gate it serves.
## 3. Read first (<= 60 KB total; exact files + line ranges)
- AGENTS.md; 00-competition-facts.md; havln_tools/schemas/SubgoalProposal/1.json, ExecutorReport/1.json
- research/C7-collision-free-execution-engineering.md L<a>-L<b>; research/A5-... L<c>-L<d> (lattice, blind zone)
## 4. Inputs / outputs
Schemas (name/version), lake paths, packages you own (agent/executor/guard.py) and must not touch.
## 5. Constraints and red lines
Regime A: no oracle/habitat imports, no quarantined/blocklisted paths, no scene_id/goal use, no cross-episode or cross-rollout state;
never open test episodes; no training on val; model calls only via the gateway; stay within compute_quota.
## 6. Plan sketch (optional; you may change it — record why in the Log)
## 7. Definition of done (each item checkable)
- [ ] AT-W2-1 passes; [ ] AT-W2-5 property test added; [ ] smoke run_id with 0 contacts; [ ] dev paired run_id (hypothesis pre-registered)
- [ ] PR merged via queue with REPORT block; [ ] brief status = done; [ ] follow-up tasks proposed (ids) if any
## 8. Tests to run
pytest -m "not sim and not gpu and not official" tests/unit tests/synth -q ; lint-imports ; python -m havln_tools.ledger --check
havlnctl rollout --agent agent.navstack:default --set smoke --k 1 --mode compliant --regime sps:200 ; havlnctl score <tapes> --set smoke --regimes NIGHTLY-4
## 9. Report (PR body + handback, <= 15 lines)
REPORT <id> · status: done|partial|failed · branch · PR
Result: <one line, numbers with denominators, run_ids>
Evidence: run_ids; tests passed; regimes
Schemas: unchanged | <Name/1> additive change (ADR-xxx)
Compliance: regime A; lint-imports PASS; audit PASS
Failures: top-3 with episode ids
Next: 1-3 bullets; proposed tasks
Cost: agent-hours, GPU-h, LLM $
## 10. Escalate (stop and ask your lead) when
a schema change seems needed; a red-line ambiguity; quota would be exceeded 2x; blocked > 4 h; a result contradicts facts.yaml.
## 11. Non-goals
What NOT to do (e.g. "do not tune margins here — ADR-005 owns the margin table").
## 12. Log (append-only; one entry per checkpoint)
- 2026-10-26T10:40Z · tried X · run 01JB… · next: Y
```

---

## 11. Critique of the current drafts (strategy v1.2, briefs at 01229bd, sibling specs)

**Resolved during Oct 24.** These were found by this review or by others and fixed before this report. They are kept here as evidence of the drift rate.
1. W2's camera height of 1.5 m became "Habitat default 1.25 m — verify" (W2 L15). The defaults are `habitat/config/default.py:227` sensor y = 1.25 and `:251` agent height 1.5.
2. NavGPT-3 is now judged non-compliant (v1.2 §3, W4 L5).
3. The CR default is now `human_influenced` (`score.py` L118; it reproduces 16.5094500 / 12.9453870 to ≤ 1.6e-6).
4. Disjoint-subset A/B probing is now forbidden (v1.2 §6, W6 L9).
5. Multi-rollout is now flagged gray in W5 L3 and v1.2 §2 and §5 (but see K4).

| # | Sev | Where | Issue | Fix |
|---|---|---|---|---|
| K1 | **H** | W1 L27; C10 §2 | C10 specifies `agent/io.py` (AgentInput), `sim/rollout_worker.py` (agent in a separate process) and `sim/audit.py`, but no brief assigns them. W1 mentions only a "rollout environment". No owner exists for agent composition or the RC. | W1-T03 owns the rollout worker + sandbox + audit; INT owns `agent/io.py` + navstack + RC (§2, §4.1) |
| K2 | **H** | W3 L31 (`parse(instruction) -> program.json`, `perceive(frame, pose)`), W2 L3/L26 ("goal belief (point or distribution)"), W4 L19-20 | Interfaces are prose without frames, units, versions or STOP/budget semantics. C10 names six schema files but defines only the ledger record. | The 16 schemas in §4, mapped to C10's file names; debug-mode validation |
| K3 | M | briefs/README L7 | Still prescribes `grep -r "oracle" agent/`:<br>• false positives on comments and strings;<br>• misses `sim.pathfinder`, `habitat_sim.nav`, file reads, subprocesses.<br>C10 already specifies `lint-imports` + audit hook + privileged-ablation invariance. | Replace rule 1 with C10 C1–C7 |
| K4 | **H** | v1.2 §3 ("Test-time compute (allowed): K = 8–32 rollouts per episode"; diagram "K rollouts per episode → self-consistency"); W5 L5-9 (K-rollout selection as the method), L15 ("Target: +5 SR over single rollout") | The strategy contradicts itself: §2/§5 and W5 L3 call cross-rollout selection gray and default OFF (`03-organizer-questions.md` T04, issue item 4). An agent reading W5's body or §3 will build the gray lever as the default and measure the wrong target. | Rewrite W5 around W5-S (per-decision voting, multi-sample at the same state, stop check) with the v1.2 target "+3–5 SR from allowed levers"; move K-rollout to a flagged appendix (W5-M); change §3 "(allowed)" to "(gray, flag)" |
| K5 | **H** | W5 L11-12 | "(and the public R2R instruction when matched by start pose + text)" contradicts `03-organizer-questions.md` T10 (privileged), v1.2 §11 and C3's red lines. Sibling sharing (T09) is gray. | Delete the R2R clause; keep siblings behind the `siblings` flag (`EpisodeInput.siblings`, `SubmissionRecord.flags`) |
| K6 | **H** | `data/val_unseen_splits.json` vs C6 report (HOLD = oLBM/X7Hy/x8F5/8194, 459 episodes, ≤ 3 looks at G5–G7) vs C10 ("holdout only at G7 and G8") vs README/v1.2 ("≤ 4 looks"); briefs/README L10 still says "hold out 3 scans" without naming them | Three hold-out definitions and three look budgets on the same day | ADR-003: the committed file is canonical (hash in facts); ≤ 4 looks, one per gate G5–G8; amend C6/C10 text; README L10 → point at the file |
| K7 | **H** | `data/test_episode_index.json` (2.4 MB), `data/test_trajectory_table.json` (5.8 MB), `data/mp3d_test_scan_room_labels.json` | Test-side assets, privileged at inference (v1.2 §11), sit in the folder every agent reads; only B12's `sample_room_paths.json` is hash-blocked | Move them to `/lake/quarantine` + the hash blocklist; CI fails if `agent/` references them; release-runner-only mount |
| K8 | M | W1 L28-29 (6 schedulers), W2 L28 ("9 human-timing regimes", C6), W6 L6 and v1.2 §5 W6 row ("4 human-timing regimes"), C10 (R0–R4 × rollout regimes), C6 (~40-regime sweep) | Five different regime vocabularies | Canonical ids + RELEASE-SWEEP + NIGHTLY-4 (§4.0), ADR-004 |
| K9 | M | v1.2 §3 executor rules (≥ 0.25 m static, ≥ 0.20 m unseen, ≥ 0.40 m + motion margin people) vs §3 design rules (≥ 0.15–0.20 m; people 0.6 m disc) vs §3 humans paragraph and W2 L16-17 (hard 0.25–0.35 walls / 0.6 people + soft 1 m) vs C6 ablation (clearance 0.10/0.15/0.25) | Safety margins conflict, even within one section of the strategy | One margin table owned by W2 (config + ADR-005); the strategy and briefs reference it instead of restating numbers |
| K10 | M | W4 L19-20 ("Policies propose waypoints/sub-goals and STOP"), W2 L26 (executor picks the stop point), W5 L7-8 (clusters) | STOP ownership is ambiguous | Policies/W5 own the goal belief; W2 owns the exact stop point and issues STOP (`SubgoalProposal.stop_belief`) |
| K11 | M | v1.2 §3 (ETP-R1 with rings ≈ 225–270 actions, p90 420–470; "≤ 6 sweeps; reserve 60") | No owner for the 500-action budget shared by sweeps, policies and the executor | Budget manager inside the W2 executor; `look_around` can be answered `sweep_denied` |
| K12 | M | W4 L22-23 (Nov 3 SR ≥ 0.30 / TCR ≤ 0.05; Nov 13 ≥ 0.45 / ≤ 0.02) vs v1.2 W4 row (≥ 0.40 Nov 9, ≥ 0.46 Nov 16, ≥ 0.50 freeze); C10 L3 bands (single rollout ≥ 0.30 → 0.45; end-to-end ≥ 50/58, the v1.0 gates); executor thresholds: W2/v1.2 (≥ 0.90 → 0.94, ≤ 1 % contact episodes) vs C10 (≥ 0.92, TCR ≤ 0.005) vs C6 O2 (≥ 0.90, ≤ 5 %) | Milestones and benchmark bands disagree across 4 documents | One gate table (§8.2). Generate `benchmarks/expected/*.yaml` bands from it so the documents cannot drift |
| K13 | L | W0 L18-19 | Submission policy omits "no probing" and the ≤ 2/day cap (W6 L9 has the probing rule) | ADR-002 (§8.3); W0 references it |
| K14 | M | W4 L13-14 ("W1 planning service + W2 executor logic") vs v1.2 §3 (teacher on the intersection of 121 navmeshes with clearance cost, replacing ShortestPathFollower) | The teacher's owner and design are unclear; W2 is a perceived-map executor | `oracle/teacher` (W4-d + W7) behind `PlanRequest/1` (purpose = teacher) |
| K15 | M | W1 | Missing:<br>• a closed-loop throughput target (Track A's dominant cost);<br>• Phase-2 bundle intake and test-scan navmesh warm-up as tasks;<br>• HA-mini bring-up before MP3D (C10); the Nov 7 trigger | AT-W1-6, AT-W1-9; W1-T03 |
| K16 | M | W3 | No cost/latency budget for per-frame VLM perception (3,408 episodes × K × frames). People tracks have no frame or persistence (W2 needs swept envelopes). `.house` evaluation must live in `oracle/gt_eval`. | `Percept/1` (track_id, swept_radius_m); compute_quota; oracle eval package |
| K17 | M | W6 L6, L14 | Still says "4 human-timing regimes" and "13 passing" tests. No release regeneration (G7) and no explicit human sign-off (C10 G6). No statement that test tapes are never re-selected per episode from local replay (T13). | AT-W6-1…4 |
| K18 | M | W7 | Track B (enumeration, 4 proposers, VLM judge, planner) is large and contributes nothing at inference unless permitted, yet shares a WS with the report | Time-box to ≤ 1 agent; kill on Nov 6 without permission (issue item 1); prioritise the oracle ladder, the teacher and the report |
| K19 | M | W1 L33 | Planning/render service "for W2/W7", but W2's compliant path must never call it | Privileged endpoints + token (C1 §4.4); refused in compliant mode |
| K20 | M | W2 L23-24 | "After each forward, compare GPS delta … back off … allowed feedback" reads as if it prevents contacts. Once the delta is short the collision is already counted; v1.2 §3 states the exact test (< 0.24998 m) and the response. | Align W2 with v1.2 §3: the pre-step check is the safety mechanism, the post-check is damage control. Add near-field blind-zone tests (floor visible only beyond 1.25 m at pitch 0) |
| K21 | L | briefs/README L8, W0 L19, W6 L7 | "Log in RESULTS.md": hand edits by many agents conflict. C10 makes it generated, but its single `results.jsonl` also conflicts on concurrent appends. | `havln_tools.ledger.append()` writes one file per record; jsonl and RESULTS.md are generated |
| K22 | L | all briefs | Pointers to whole research files; `research/` is now 1.40 MB / 32 files ≈ 350k tokens | Read-first lists with line ranges + `02-research-digest.md` |
| K23 | L | all briefs | No time boxes, escalation rules, non-goals, kill criteria or resumable logs | Template §10 |
| K24 | L | briefs/README L10 | "never tune prompts on test text" is too weak | Agents never open test episodes; the C10 test-text CI guard |
| K25 | L | v1.2 header L5 ("13 passing tests") vs §11 ("15 tests"); W6 L14 | Stale counts | Generated status + facts registry |
| K26 | L | all briefs | No cadence or UTC conventions; the probable close is Nov 30 15:59 UTC | §8 |
| K27 | M | W0 L7 | "File the five questions from `01-strategy.md` §7". §7 now lists 7 questions, and the canonical post is `03-organizer-questions.md` (10 issue items + private B12 email). W0 would post the wrong text. | W0-T01: post `03-organizer-questions.md` verbatim |

---

## 12. Facts vs inferences; contradictions found

- FACT [high], measured with `du -cb`:
  - `research/` = 32 files, 1.40 MB at ~19:50 UTC; it was 9 files at ~19:15.
  - Briefs = 19.4 KB.
  - Strategy v1.2 = 33.5 KB.
- FACT [high]: `data/val_unseen_splits.json` (seed 20261024):
  - lockbox = 8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX (426 episodes, 142 trajectories);
  - dev = 8 scans (1,413 / 471);
  - quick = 306 / 102; smoke = 60 / 20;
  - smoke ⊂ quick ⊂ dev and dev ∩ lockbox = ∅ (checked).

  C6's report JSON names a different HOLD (oLBMNvg9in8, X7HyMhZNoso, x8F5xyUWy9e, 8194nk5LbLH; 459 episodes) and DEV (7 scans / 1,380).
- FACT [high]: `habitat-lab-0.1.7/habitat/config/default.py:227` sets `SIMULATOR_SENSOR.POSITION = [0, 1.25, 0]`, `:251` sets `AGENT_0.HEIGHT = 1.5`, and `:239-241` set the depth range to 0–10 m, normalised. `HASimulator/config/HAVLNCE_task.yaml` overrides only WIDTH/HEIGHT/HFOV. The challenge YAML in the image is unverified.
- FACT [high]: `havln_tools/score.py` L118 defaults to `cr_mode="human_influenced"`. An integer search reproduces the published Scores with CR = 425/682 (|Δ| 1.6e-6) and 1090/1593 (|Δ| 5.2e-7); the best all-episode-mean fit leaves |Δ| ≥ 6.6e-4.
- FACT [high]: W5 L11-12 still contains the original-R2R-instruction clause. `03-organizer-questions.md` T10 marks it privileged and T04 marks multi-rollout gray. v1.2 §3 still says "Test-time compute (allowed): K = 8–32 rollouts per episode".
- FACT [high]: `03-organizer-questions.md` already asks about single-run evaluation (item 4) and local replay in Phase 2 (item 8). W0 L7 points to the older 5-question list.
- FACT [high]: C10 specifies `agent/io.py`, `sim/rollout_worker.py`, `sim/audit.py` and `ledger/results.jsonl`, and names six schema files. No brief assigns these components.
- INFERENCE [medium]: whether W5-M is allowed depends on the answer to issue item 4. Under C3's information-locality reading, it is not.
- INFERENCE [medium]: the headcount limits (≈ 8 lead contacts per day for the human, 16–20 sessions) rest on assumed minutes per touch-point, not measurements. Re-estimate after week 1.
- INFERENCE [low–medium]: the throughput figures (dev K = 1 ≈ 33 min on 64 workers) assume ~60 decisions × 1.5 s per episode. Measure them (AT-W1-6, AT-W5-4).
- Contradictions with CONTEXT.md: none. The CR-denominator uncertainty in CONTEXT has since been resolved in favour of βL (A4; `havln_tools`).

---

## 13. Open questions

1. **Human: ratify ADR-003 today.** Which hold-out definition is canonical: the committed file (recommended), C6's 4-scan HOLD, or another? With what look budget (≤ 4 recommended)?
2. Organizers: issue items 4 (single-run evaluation / multi-rollout), 6 (sibling instructions) and 8 (local replay in Phase 2). Their answers switch the W5-M, siblings and test-replay flags.
3. Which image digest does CodaBench run (`e1a0544f` or `78a62cd1`, `cr-domain`)? What are the challenge's camera POSITION, depth normalisation and TILT (W1-T01; issue item 2)?
4. Does the MP3D Terms of Use permit sending renders of test scenes to third-party closed-model APIs?
5. Human logistics: timezone (to place the daily block), the number of academic members who can file MP3D requests (≥ 3 advised), and the API spend ceiling.
6. Platform: does the team's GitHub plan support merge queues and CODEOWNERS on a private repo? What is the maximum number of concurrent Claude Code sessions? (The cap of 24 assumes no lower platform limit.)
7. Will the Phase-2 bundle include `trajectory_id` and test-scan human placements (AT-W1-9; flags)?

---

## 14. Sources

- `/home/user/open-data-eval/competitions/roboworld2026-track2/01-strategy.md` v1.2 (L5; §2; §3 executor rules, backbones, "Test-time compute (allowed)"; §5 table L213-231; §6 gates L232-254; §11; §12 L340-360), `00-competition-facts.md`, `02-research-digest.md`, `03-organizer-questions.md` (issue items 1–10; compliance table T01–T22), `README.md`, `data/val_unseen_splits.json`, `data/` listing, git log 54998c2 → 01229bd.
- `/home/user/open-data-eval/competitions/roboworld2026-track2/briefs/README.md` (L7, L8, L10); `W0` (L7, L18-19); `W1` (L27-33); `W2` (L15-17, L23-28); `W3` (L31); `W4` (L5, L13-14, L19-23); `W5` (L3-15); `W6` (L6-14); `W7`.
- `/home/user/open-data-eval/competitions/roboworld2026-track2/havln_tools/score.py` (L118) and `tests/`.
- Scratchpad findings: `C1-infra-and-replay-farm.md` (§3.2, §4.4, §5–§7, §10, §12); `C2-timeline-critical-path-and-risk-register.md` (§6, §7, §10); `C3-rules-ethics-and-defensibility.json`; `C6-experiment-design-and-val-protocol.json` (partitions, sweep, decision cap, ladder); `C10-testing-and-benchmark-plan.md` (§2 layout and CI, §5 S1–S4, §9 C1–C7, §10 ledger and gates); `B7-competition-case-studies-and-replay-eval-lessons.json`; A3, A4, A5, A6, A8, A12, B3 (L194, L257), B4, B12 (digest).
- `…/scratchpad/ext/habitat-lab-0.1.7/habitat/config/default.py` L224-252; `…/ext/HA-VLN/HASimulator/config/HAVLNCE_task.yaml`; `…/ext/HA-VLN/agent/VLN-CE/habitat_extensions/sensors.py` L20-50; `…/ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/val_unseen/val_unseen.json.gz`.
- Work files: `…/scratchpad/c5work/{contracts.py, contracts/, evalsets.py, build_c5.py, c5_body.md, c5_json.py}`.
