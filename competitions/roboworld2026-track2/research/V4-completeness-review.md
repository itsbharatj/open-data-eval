# V4 — Completeness review of the Track 2 hand-off package (strategy v1.2)

Reviewer: V4 completeness critic · 2026-10-24 (night) · no web searches used.

Read in full: `CONTEXT.md`; `competitions/roboworld2026-track2/{README.md, 00-competition-facts.md, 01-strategy.md, 02-research-digest.md,
03-organizer-questions.md}`; `briefs/README.md`, `briefs/W0`–`W7`; `havln_tools/*.py`; `tests/*.py` (ran: **20 tests, OK**);
`benchmarks/*`; the `data/` listing and the keys of every data file. Skimmed all 32 reports in `research/`: every "Open questions" and
"Recommendations" section was extracted and checked against the package. Also read the scratchpad findings `C4-*.md` and `C5-*.md`,
which are **not** in `research/`.

All paths below are relative to `/home/user/open-data-eval/competitions/roboworld2026-track2/` unless absolute.

Priority scale:
- **P0**: an agent will do the wrong thing in the first 72 h, or cannot start without asking a human.
- **P1**: wrong or missing before the first genuine Phase-2 upload (about Nov 6).
- **P2**: hygiene and drift.

---

## Summary of P0 items

| # | Gap | Files to change |
|---|---|---|
| P0-1 | The day-0 organizer package is inconsistent and incomplete. W0 says "file the five questions from §7". §7 has 7 questions and `03-organizer-questions.md` has 10 different items. The ready-to-post issue never asks whether the Phase-2 bundle ships test-scan human placements (raised in 12 reports), never asks about the schedule or close time, and never asks about contact-based selection. The private email omits the `sample_room_paths.json` leak, which the strategy says must be disclosed before Oct 30. | `03-organizer-questions.md`, `briefs/W0-*.md`, `01-strategy.md` §7 |
| P0-2 | The strategy and W5 still prescribe techniques that C3 classifies as gray or prohibited. In `01-strategy.md`, L31-36, L128, L169 and L190-192 present K = 8–32 rollouts with "contact-free selection" as "allowed". C3 T04(d) says selection by pose-contact is **prohibited**. W5 L11-12 uses the public R2R instruction (T10, prohibited) and, by default, "shares the executor's map" across siblings (T07/T09, gray, OFF). Meanwhile the levers that are actually allowed in the clean configuration (B10 P4–P7) have no brief, no contract and no DoD. | `01-strategy.md` §0.4, §3; `briefs/W5-*.md` (rewrite) |
| P0-3 | The compliant runtime has no owner and none of the inter-workstream interfaces has a contract. That runtime is the env-server `reset`/`step` API, the `Observation` schema, the agent sandbox with file-open audit, and the 3,408-episode production run. Briefs use prose (`program.json`, "goal belief (point or distribution)"). The 16 validated JSON Schemas, acceptance tests and starter backlog exist in `findings/C5-*.md` and `c5work/contracts.py`, but they were never copied into the package. The digest still says "C5 — pending". | `briefs/W1-*.md` (new section), new `contracts/`, every brief's I/O section, `research/` (add C4, C5), `02-research-digest.md` |
| P0-4 | Human-timing regimes and the release gate contradict each other. W1 lists 7 regimes, W2 says "9 regimes", W6 says "4 regimes", C6 uses R0…Rall and C10 uses R0–R4; "R0" means *frozen frame 0* in C6 and *official wall clock* in C10. Strategy §5's W6 DoD "PASS + TCR 0 on all regimes for every candidate ZIP" contradicts the ≤ 1 % contact DoD for W2 and C10's G3 thresholds (TCR max ≤ 0.02). Applied to test ZIPs, it also contradicts the rules assumption in issue item 8 (no test-replay outcomes used to pick or edit). | `briefs/W1`, `W2`, `W6`; `01-strategy.md` §5, §12 |
| P0-5 | There is no explicit dependency graph, although the user asked for "parallel with a clear sequence". §5 has a single sentence ("W1 unblocks W2/W4/W6 once MP3D arrives"). It does not list blocking edges, says nothing on what each workstream does on day 1 without MP3D, and never mentions the public scene `17DRP5sb8fy`, which A11, C9, C10 and C5 all name as the MP3D-free bring-up path. | `01-strategy.md` §5 (new table), every brief (new "Depends on / Unblocks" line) |

---

## P0 — details and proposed text

### P0-1 Organizer package: one question set, three missing questions, missing leak disclosure

**Evidence.**
- `briefs/W0-ops-and-organizer-liaison.md` L7: "File the five questions from `01-strategy.md` §7". This text descends from C2 §8, which predates the Oct-14 pivot.
- `01-strategy.md` §7 (L254-268) has 7 questions.
- `03-organizer-questions.md` has 10 issue items with different content (scene geometry, camera, bump, single run, episode independence, siblings, R2R text, local replay, training data, leaderboard/terms).
- Gray areas raised in research `Open questions` that the ready-to-post issue does **not** cover:

| Gray area | Raised by | In `03` issue? | In §7? |
|---|---|---|---|
| Phase-2 bundle ships test-scan human placements (rendering needs them, so every compliant team is human-blind locally without them); `trajectory_id`; ids stay 1..3408; file names | A1, A2, A3, A6, A8, A9, B2, B3, B5, B6, B9, B11, C1, C3, C6, C7, C8, C9, C10, C5 | **no** | Q3 |
| Public `collision_num_test.json` = scoring allowance, or regenerated? | A1, A4, A8, C3, B6 | no (the private email only says "we flag them") | Q3 |
| Schedule: shift because of the outage, exact Phase-2 close (UTC), alternate submission/bundle channel | A11, A12, C2 | no (10(b) asks only for the Terms text) | Q5 |
| Selection by pose-detected contact across runs; prefix truncation (`a[1..t]+STOP`) of a run; "re-drive" | C8 §8, B10 G2, B8 (c), C5 Q8 | partly: item 4 asks only about "agreement among the runs" | no |
| Which image digest CodaBench runs (`e1a0544f` vs `78a62cd1` cr-domain) and the CR definition | A8, A10, C10, C5 | no | no |
| Official replay step rate / motion FPS; whether driving the local renderer's human clock from a step-indexed schedule is acceptable | A3, A7, B6, B10, C1, C7 §11, C9 | no | no (the strategy *relies* on it, §3 "virtual human clock") |
| Whether failed/rejected uploads count; per-episode results visible | A8, A12, B7 | no | no |
| `sample_room_paths.json` leak (879 test episodes) | B12 | **not in the private email** | strategy §2 says "inform privately before Oct 30" |

**Fix 1 — `03-organizer-questions.md`.** Inside the issue body, add after item 10:

> **11. Phase-2 bundle and scoring files.** Will the Phase-2 bundle include the human placements the simulator needs to render humans in the 18 test buildings (the test-scan entries of `human_motion.json`, mounted only into the simulator, never read by the agent)? Will it include `trajectory_id`? Will episode ids stay `1`..`3408`, and will the file name and format match `val_unseen.json.gz`? Is the public `Data/HA-R2R-tools/collision_num_test.json` the allowance used for scoring, or will it be regenerated? Through which channel will the bundle be released if CodaBench is still down? Without test human placements, no team can render the humans that the official replay contains.
>
> **12. Schedule.** Please confirm the exact Phase-2 close timestamp in UTC. Will Phase 1 or Phase 2 be extended because of the CodaBench outage? Is there an alternate submission channel, and does it share the 5/day and 100/phase quota? Does a submission still being scored at the deadline count?
>
> **13. Evaluation environment.** Which image digest does CodaBench run (`…e1a0544f` or `…78a62cd1`, tag `cr-domain-20261004`), and what did the cr-domain change alter? Is CR normalised by the human-influenced episode count (682 / 1,593 / 2,859)? At roughly what step rate, and with what motion FPS, does the official replay run? Our agent computes slowly per step. When it runs locally, may we drive the simulator's human animation from a step-indexed clock that approximates the official replay speed, instead of from our agent's wall clock? We assume yes, because it changes only what our agent observes, not how sequences are scored.

Extend item 4 with:

> - (d) If several runs were allowed, could the choice use pose-derived contact information (a shortened `MOVE_FORWARD`) observed in runs that are not submitted?
> - (e) May a run's sequence be truncated after the fact at an earlier position (prefix + `STOP`)?
>
> Our assumption: no to both.

**Fix 2 — `03-organizer-questions.md`, private email.** After the bullet list of public files, add:

> - `web/app/sample_room_paths.json` in the original `peteanderson80/Matterport3DSimulator` repository (committed 2018, sha256 `d15fe5df194da4caab89deb277454aea647b45d5c5fd0ebf078b84d6e4987e4f`) contains full start→goal viewpoint paths for R2R path_ids 0–1999. These include 366 of the 1,391 R2R test paths, which we estimate correspond to 293 HA-R2R test trajectories, i.e. 879 of the 3,408 Phase-2 episodes. We block this file by hash in all our pipelines. You may want to exclude or re-weight those episodes, or state a rule.

**Fix 3 — `briefs/W0-ops-and-organizer-liaison.md` L7-9.** Replace with:

> - [HUMAN] Post the GitHub issue **verbatim** from `03-organizer-questions.md` (items 1–13) from the team's registered GitHub account. Mirror it on Discord, and send the private email in that file to roboworld2026@gmail.com. Do **not** use `01-strategy.md` §7 or C2 §8 (both superseded). Archive the links in `research/organizer-answers.md`.
> - Answer protocol: copy every answer verbatim within 2 h. Within 24 h, map it to an ADR in `DECISIONS.md` and to a flag value in `config/compliance_flags.yaml` (see P1-7). An answer never switches a flag ON without a human-approved ADR.

**Fix 4 — `01-strategy.md` §7.** Replace the list with a one-line pointer to `03-organizer-questions.md`, plus this mapping so that numbers cited elsewhere still resolve:

| Old §7 | 03 item |
|---|---|
| 1 | preamble |
| 2 | 6, 7 |
| 3 | 11 |
| 4 | 1 |
| 5 | 12 |
| 6 | 2, 5 |
| 7 | private email |

### P0-2 Rules contradictions in the strategy and W5; the allowed levers have no spec

**Evidence.**
- `01-strategy.md`:
  - L31-36 lists "Many rollouts per episode … selection by self-consistency of stop positions plus GPS-detected contact" as one of the "decisive advantages within the compliant regime".
  - L128 (architecture): "K rollouts per episode → self-consistency + contact-free selection → tape".
  - L169: "first contact-free run among three guarded agents gives 62.4 %".
  - L190: "Test-time compute (allowed): K = 8–32 rollouts per episode … prefer clusters with contact-free tapes".
- C3 T04 (in `03-organizer-questions.md` L87): "(d) Selection by collisions, pose-contact or local metrics = prohibited (T13)"; multi-rollout itself is "GRAY - ASK (leans prohibited)".
- `briefs/W5-*.md`:
  - L9: "discard tapes with any detected contact" (prohibited signal).
  - L11-12: "(and the public R2R instruction when matched by start pose + text)" (T10 PROHIBITED).
  - L12: "otherwise run per episode and only share the executor's map" (cross-episode memory T07 and sibling sharing T09, both default OFF). This makes a gray technique the **default** when the flag is off.
- C5 K4/K5 flagged this on v1.1; v1.2 added a compliance banner to W5, but these lines are unchanged.
- The allowed levers are specified only in research: B10 P4 stop verifier + return-to-best node (+2–4), P5 per-step ensemble (+1–3), P6 instruction TTA (+1–3), P7 uncertainty-gated in-budget look-ahead (+1–4), B5 §7.8 runner-up visit, C8 A-ST. Together they are worth +8–18 SR. W5's DoD ("+5 SR over single rollout") measures the gray lever, not these.

**Fix 1 — `01-strategy.md` L31-36.** Replace the first sub-bullet with:

> - *Unlimited per-step compute inside one run.* Frontier/open VLM reasoning per step, several model samples at the **same** state, per-step ensembles, a stop verifier that can send the agent back to a better visited node, and in-budget physical look-ahead to a runner-up endpoint. Every observation is paid for by actions in the submitted tape. Multi-rollout selection is a **gray lever** (OFF; issue item 4). Contact information from discarded runs is **never** a selection signal (C3 T04(d)).

**Fix 2 — `01-strategy.md`.**
- L128: replace with `W5-S lockstep ensemble + stop verifier (single run) → tape [W5-M multi-rollout: flag rollouts_k, OFF]`.
- L169: append "(this uses contact-based selection across runs, which is prohibited; it is quoted only as an upper bound)".
- L190-192: replace "Test-time compute (allowed): K = 8–32 rollouts …" with:

> Test-time compute (allowed, single run): stop verifier + return-to-best-visited-node; per-step logit/sub-goal ensemble of 3–5 snapshots; instruction-side TTA on the episode's own instruction; uncertainty-gated physical visit of the runner-up endpoint (≤ 15 m extra, ≥ 100 actions left). Gray (flag `rollouts_k`, OFF): K = 8–32 independent rollouts with stop-cluster + verifier selection. Contact information is never a feature.

**Fix 3 — `briefs/W5-test-time-compute-and-selection.md`.** Rewrite as two sub-workstreams:

```
# W5 — Test-time compute and selection

## W5-S (default; ships in the clean configuration)
Goal: turn per-step compute into SR inside ONE closed-loop run.
Levers (research/B10 §Recommendations P4–P7, B5 §7.8, C8 §7.1):
 1. Stop verifier + return-to-best-visited-node. A Qwen3-VL-8B judge P(goal within 3 m | instruction, own keyframes,
    policy stop logit), trained on rollouts of OUR policies on TRAIN scans in 4 scan-disjoint folds. At each STOP proposal,
    compare the current node with the visited nodes. If a visited node wins by margin τ, W2 drives back and stops there.
 2. Per-step ensemble. Average action/waypoint logits of 3–5 snapshots/seeds of the same architecture. Heterogeneous policies
    vote on the next sub-goal position (cluster medoid); the verifier breaks ties. No extra environment steps.
 3. Instruction TTA on the episode's own text: raw HA text + de-HA condensed paraphrase + ordered sub-instruction list; fuse per step.
 4. Uncertainty-gated look-ahead. If the verifier's top-2 margin < τ2 and ≥ 100 actions remain, physically visit the runner-up
    endpoint (≤ 15 m extra travel; skip within 1 m of detected people), then return. All of these actions are in the tape.
Consumes: Observation/1, InstructionProgram/1, SubgoalProposal/1 (from each W4 policy). Produces: one fused SubgoalProposal/1
(+ stop_belief) for W2, and a SelectionRecord/1 log.
Never: discarded rollouts; contact information from other runs; sibling instructions; original R2R text; trajectory_id;
simulator save/restore.
DoD: paired DEV SR ≥ +3 pp over the best single backbone (trajectory-cluster bootstrap, p < 0.05). Verifier ECE ≤ 0.05 on DEV,
with the manifest proving train-fold-only training. Contact-episode rate not worse by > 0.2 pp. 100 % of tapes ≤ 500 actions with STOP.
Tests: U18 (fusion maths) and U19 (stats) from research/C10; S14 rollout determinism with the LLM cache.

## W5-M (flag rollouts_k, default OFF; val ablation only until issue item 4 is answered YES in writing)
K = 8–32 rollouts per episode (seeds/policies/prompts). Selection features: stop-cluster support + verifier score over each run's
own observations. Pose-detected contacts are logged but are NOT a feature unless item 4(d) is answered yes. Always report K=1 next
to K>1.
## Sibling fusion (flag sibling_fusion, default OFF; issue item 6)
Joint conditioning on the 3 HA instructions only. Never the original R2R text (C3 T10). With the flag OFF nothing crosses
episodes, not even the executor's map (that would be cross-episode memory, T07).
```

**Fix 4 — `01-strategy.md` §5 W5 row.** Replace the DoD with "W5-S: ≥ +3 SR paired on DEV from single-run levers; W5-M gains reported separately and never shipped without a written YES".

### P0-3 Runtime owner, sandbox and JSON contracts are missing from the package

**Evidence.**
- No brief owns the closed-loop runner. W1 builds a replay scorer and a *privileged* planning/render service (L33-36). W4 L27 says the executor "is the only thing that emits MOVE_FORWARD" but owns no runtime.
- The C3 §10.3 "CLEAN-1 sandbox" (env server exposes only `reset`/`step`; agent container without data mounts; file-open audit) is assigned to no brief.
- `briefs/README.md` L6 relies on `grep -r "oracle" agent/` (C5 K3: false positives; it misses `sim.pathfinder`, env-var paths and subprocesses).
- The interfaces are prose:
  - W2: "goal belief (point or distribution from W4/W5)";
  - W3: `parse(instruction) -> program.json` and `perceive(frame, pose)`;
  - W5 and W7: no I/O at all.
- The red lines in strategy §2 (no simulator look-ahead/save-restore, no human in the loop on test, coding agents never inspect test episodes) appear in no brief.
- `findings/C5-multi-agent-organization-and-handoff.md` contains:
  - 16 JSON Schemas (EpisodeInput/1, Observation/1, InstructionProgram/1, Percept/1, SubgoalProposal/1, ExecutorReport/1, RolloutRecord/1, SelectionRecord/1, ScoreRequest/1, ScoreResult/1, PlanRequest/1, PlanResult/1, GoalCandidates/1, ExperimentRecord/1, SubmissionManifest/1, TaskBrief/1);
  - frames and units conventions;
  - acceptance tests AT-W0-1…AT-INT-3;
  - a 17-task starter backlog with dependencies.
- The code for those schemas is in `scratchpad/c5work/contracts.py` (`SCHEMAS`, `EXAMPLES`). Neither C5 nor C4 was copied into `research/`, so the README's "33 topics" is wrong: the folder holds 32 files and lacks C4/C5. The digest says "C5 Organization — *pending*" and "C4 — not run separately".

**Fix 1.** Copy `findings/C4-*.md` and `findings/C5-*.md` into `research/`. At the top of C5, add:

> Superseded by strategy v1.2:
> - NavGPT-3-first (W4-T01) → SimpleVLN first.
> - HOLDOUT-v1/SMOKE-v1 → `data/val_unseen_splits.json` (lockbox `8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX`, 426 eps) is canonical.
> - K6 (camera height) fixed in W2.

Export `contracts.py` to `contracts/<Name>/1.json` + `contracts/fixtures/<Name>.json`, and add `tests/test_contracts_fixtures.py`, which validates each fixture and rejects each negative case.

**Fix 2 — `briefs/W1-data-and-infra.md`.** Insert a new section before "Planning/render service":

> **Closed-loop runner + compliant sandbox (Track A; day 1; owner W1; bring-up on the public scene `17DRP5sb8fy` before MP3D).**
>
> API, and nothing else:
> - `reset(episode_id) -> EpisodeInput/1 {episode_id, split, instruction, start_pose{position, rotation_xyzw}, budget: 500}` plus the first `Observation/1`.
> - `step(action) -> Observation/1 {step_idx, rgb uint8[224,224,3], depth float32[256,256,1] (metres), gps, compass, done}`.
> - No `get_state`/`set_state`, no PathFinder, no `trajectory_id`, no `collided` flag (unless issue item 3 says yes), no sim handles.
>
> Isolation and audit:
> - The env-server process alone mounts scenes, episodes, `human_motion.json` and navmesh caches.
> - The agent runs in a separate container with no data mount. `sys.addaudithook` logs `open`/`listdir`/`connect`, and every `RolloutRecord/1` carries `inputs_used` and the audit hash.
> - Agent state is reset per episode, asserted in code.
> - The human clock is pluggable: `gen:wall`, `gen:sps:<S>`, `gen:static`; see P0-4.
>
> Production mode:
> - Runs a full split (3,408 test episodes) with fixed seeds and a content-addressed LLM/VLM response cache.
> - Writes per-episode observation logs, so any tape can be regenerated for verification.
> - Target: ≥ 2,000 resets/h/GPU with a stub agent; full K=1 test pass ≤ 24 h wall.
>
> DoD: C10 C2/C4/C5 and AT-W1-7 green. A red-team test (open `human_motion.json`, import `habitat_sim`, read `$PKG/data/test_*`) fails loudly.

**Fix 3 — every brief's I/O line.** Add "Consumes / Produces" with schema names:

| Brief | Consumes | Produces |
|---|---|---|
| W1 | — | `EpisodeInput/1`, `Observation/1`, `RolloutRecord/1`, `ScoreRequest/1`→`ScoreResult/1`, `PlanRequest/1`→`PlanResult/1` (privileged, token-gated) |
| W2 | `Observation/1`, `Percept/1`, `SubgoalProposal/1` | actions + `ExecutorReport/1`. **W2 owns MOVE_FORWARD, the exact stop point, STOP and the 500-action budget** (C5 K10/K11) |
| W3 | `EpisodeInput/1`, `Observation/1` | `InstructionProgram/1`, `Percept/1` (with track ids and `swept_radius_m`) |
| W4 | `InstructionProgram/1`, `Percept/1`, `ExecutorReport/1` | `SubgoalProposal/1`; the teacher uses `PlanRequest/1` only under `oracle/` |
| W5 | many `SubgoalProposal/1` | fused `SubgoalProposal/1`, `SelectionRecord/1` |
| W6 | `RolloutRecord/1`, `ScoreResult/1` | `SubmissionManifest/1`, ZIP |
| W7 | `ScoreResult/1`, `GoalCandidates/1` | taxonomy, report |

**Fix 4 — `briefs/README.md`.** Replace rule 1 with:

> 1. Red lines (C3 PROHIBITED; never in the inference path, never in a submitted tape):
>    - human placements or simulator human state;
>    - simulator save/restore, step-and-revert or rendering from unreached poses;
>    - navmesh, PathFinder, scene mesh, MP3D nav-graph or `.house` of test buildings;
>    - original R2R / R2R-CE / FGR2R test text;
>    - `collision_num_test.json` and HA-VLN-1.0 test humans;
>    - `sample_room_paths.json` (sha256 d15fe5df…);
>    - picking or editing test tapes by local replay outcomes;
>    - leaderboard probing;
>    - any human or coding agent inspecting individual test episodes.
>
>    Enforcement: import-linter (`agent` must not import `oracle`, `sim.privileged`, `habitat`, `habitat_sim`), the runtime audit hook, and the privileged-ablation invariance test (C10 C1–C3). `grep` is not a compliance check.

### P0-4 One regime vocabulary, one release gate, and a test-split rule

**Evidence.**

| Source | Regime set |
|---|---|
| `briefs/W1` L28-30 | `wallclock`, `frozen(k)` k∈{0,60,119}, `fast`, `slow`, `all-frames` (7) |
| `briefs/W2` L28 | "the 9 human-timing regimes of the W1 scorer (`research/C6-*`)", but W1 does not define 9 |
| `briefs/W6` L6 | "4 human-timing regimes" |
| `research/C6` §6 | R0 = frozen 0, R26, R119, Rstep, Rfast, Rslow, Rstall, Rbase, Rall, plus generation regimes G-wall/G-fast/G-none |
| `research/C10` §7 | R0 = official wall clock, R1 throttled, R2 frozen(k) ×5, R3 schedule(S) ×5, R4 all-frames |
| `findings/C5` §4.0 | `wall`, `wallx:s`, `frz:k`, `sps:S`, `allf`, `static`; CERT = {frz:0, frz:60, frz:119, sps:20, allf} |

Gate conflicts:
- Strategy §5 W6 DoD (L223): "Every candidate ZIP: PASS + TCR 0 on all regimes".
- W2 DoD: contact episodes ≤ 1 %.
- C10 G3 (compliant): TCR max ≤ 0.02, spread < 0.005, R4 flagged ≤ 0.5 %.
- C10 G3 is "applied … on the test split if test humans are shipped". Issue item 8, our own stated assumption, says local replay outcomes on test are not used "to pick, edit or regenerate sequences, or to choose between pipeline variants".

**Fix — add to `briefs/W1-data-and-infra.md`, and reference it from W2, W6 and strategy §12.**

> **Canonical timing ids** (C5 §4.0), with C6/C10 aliases:
>
> | Id | Meaning | C6 alias | C10 alias |
> |---|---|---|---|
> | `wall` | Official wall clock | — | R0 |
> | `wallx:<s>` | Throttled wall clock, s per step | — | R1 |
> | `frz:<k>` | Humans frozen at frame k | R0 = `frz:0`, R26 = `frz:26`, R119 = `frz:119` | R2 |
> | `step` | frame = step index | Rstep | — |
> | `sps:<S>` | Deterministic schedule at S steps/s | Rfast = `sps:200`, Rslow = `sps:3` | R3 |
> | `stall` | Frame 119 from step 1 | Rstall | — |
> | `static` | No humans | Rbase | — |
> | `allf` | Kinematic check against all 121 navmeshes; evaluator-only | Rall | R4 |
>
> Generation (local rollout) clocks: `gen:wall`, `gen:sps:<S_est>`, `gen:static`.
>
> **CERT-9** (the "9 regimes" of W2): `frz:0, frz:26, frz:119, step, sps:200, sps:3, stall, static, allf`.
>
> Release gate on val (DEV, then lockbox at gates):
> - contact episodes ≤ 1 % in the generation clock;
> - flips (clean in generation, colliding in any CERT-9 regime) ≤ 0.5 %;
> - TCR spread < 0.005;
> - worst-regime Score ≥ mean − 0.5;
> - privileged teacher: 0 flagged steps under `allf`.
>
> **Test ZIPs.** Allowed checks:
> - (a) `havln_tools` and in-image `havln-validate` PASS;
> - (b) the ZIP is regenerated from the RC tag with an identical sha256;
> - (c) the agent fingerprint equals the DEV-certified fingerprint;
> - (d) only if issue item 8 is answered yes, a pose-trajectory reproduction check, with collision columns suppressed in the output.
>
> No collision/TCR number computed on test is printed, logged or used for any decision.

In `01-strategy.md` L223, replace the W6 DoD with: "Every candidate: contract PASS, regenerable with identical sha256, and its DEV run passes the CERT-9 gate (W1). Test ZIPs are never gated on locally computed collisions."

In `briefs/W6` L6, replace "local replay under 4 human-timing regimes (W1 scorer)" with "for **val** RCs: CERT-9 replay (W1); for **test** ZIPs: checks (a)–(d) only".

### P0-5 Explicit dependency graph and day-1 parallel plan

**Evidence.** `01-strategy.md` L226-229 is the only sequencing text. C2 §3 has a critical path for the superseded privileged plan. C5 §2.5 has a dependency table, but it is not in the package. None of the strategy or briefs mentions `17DRP5sb8fy` (grep: 0 hits). Several dates silently assume MP3D by Oct 26–28: W2 first deliverable Oct 28, M3 Oct 29 ("Executor given the GT goal: SR ≥ 0.90").

**Fix — `01-strategy.md` §5.** Add after the workstream table:

> **Dependency graph.** "→" means "blocks". Every brief repeats its own row as `Depends on / Unblocks`.
>
> | Task | Needs | Unblocks | Day-1 start? |
> |---|---|---|---|
> | INT-T00 repo, CI, `contracts/`, eval sets, registry (0.5 d) | — | every cross-WS merge | yes, first |
> | W0 issue/email/Discord, MP3D ×3, registration [HUMAN] | — | flags; MP3D tasks | yes |
> | W1-T01 image forensics → `havln_tools/facts.yaml` (camera height, TILT, depth range, MEASUREMENTS incl. DISTANCE_TO_HUMAN, CR per digest, frame timing) | image pull | W2 mapper constants, W6 scorer parity | yes |
> | W1-T03 runner + sandbox on `17DRP5sb8fy` (public `mp3d_example`, 10 humans) | image, INT-T00 | W3-T02, W4-T01/T02, W2 closed-loop tests | yes |
> | W2-T01/T02 mapper, planner, guard on synthetic scenes (`synth/`, C10 U14–U16) | INT-T00 | W2 oracle-goal harness | yes |
> | W3-T01 parser on HA-R2R train/val text | HF data | W4 (program input) | yes |
> | W4 SimpleVLN vLLM server + client against the runner stub; ETP-R1 code port | weights; W1-T03 for real frames | bake-off (Nov 3) | yes |
> | W6-T01 STOP-only ZIPs + predicted Scores from HA-R2R `val_*.json.gz` | HF data | Phase-1 calibration (M3) | yes |
> | W7-T01 report skeleton; Track B candidate enumerator on public connectivity graphs (val only) | — | oracle analysis | yes |
> | W1-T04 navmesh cache, CMA reproduction (M2/M3), planning service | **MP3D** | W2 harness, W4 teacher, W1 CERT replay | no |
> | W2 oracle-goal harness on val_unseen (DoD SR ≥ 0.90) | MP3D, W1-T04 | W4 integration | no |
> | W3 detector training on train-scan renders; `.house` end-region eval | MP3D | W2 people layer quality | no |
> | W4-T03 privileged teacher + DAgger/SFT data; all fine-tuning | MP3D, W1-T04 | G6 | no |
> | W5-S verifier training | W4 policy rollouts on train | G7 | no |
> | Phase-2 bundle ingestion (A1 validation script; C10 S17) | bundle (Oct 30) | test navmesh cache, first genuine test run (G5) | no |
> | W5-M, sibling_fusion, camera_cfg, Track B submission | written organizer YES | — | no |
>
> **MP3D-late rule.**
> - Express all MP3D-dependent dates as `D_MP3D + n`, where M2 = +1 and M3 = +3 days.
> - Until MP3D arrives, every closed-loop task runs on `17DRP5sb8fy` and synthetic scenes.
> - If there is no MP3D by Nov 7, escalate to the organizers (every team needs it). Do **not** switch to graph-based planning: C2 §9's "mesh-free contingency" uses test connectivity graphs and HA-VLN-1.0 test humans, both prohibited under C3.

---

## P1 — fix before the first genuine Phase-2 upload

**P1-1 One target table (numbers disagree in five places).**
- `01-strategy.md` L45: clean configuration ≈ 40–50; compliant agent "SR 0.50–0.65 → 50–65".
- §6 G7: K=1 SR 0.50–0.60 → 46–55.
- §12 L5: clean SR 0.50–0.62.
- §5 W4: SR ≥ 0.40 by Nov 9, ≥ 0.46 by Nov 16, ≥ 0.50 at freeze.
- `briefs/W4` L22-23: Nov 3 SR ≥ 0.30 / TCR ≤ 0.05; Nov 13 SR ≥ 0.45 / TCR ≤ 0.02.
- C5 AT-W4-3: DEV SR 0.35 / 0.52 / 0.61.
- C6 §13.7: "healthy final dev Score 53–60 at K=1".
- §6 G5 says "… on **test** (SR 0.28–0.36)", although test SR is knowable only from the leaderboard.

Fix: add a single gate table to `01-strategy.md` §6 and delete the numbers elsewhere (W4 references it):

| Gate (Fri) | DEV SR (K=1, clean) | Contact-episode rate | Expected test Score | Decision |
|---|---|---|---|---|
| G5 Nov 6 | ≥ 0.35 | ≤ 5 % | 30–36 | bake-off winner fixed by ADR |
| G6 Nov 13 | ≥ 0.45 | ≤ 2 % | 40–46 | fine-tune vs RL budget |
| G7 Nov 20 | ≥ 0.52 | ≤ 1 % | 46–55 | freeze |

All gates are measured on DEV with lockbox confirmation. Test uploads at gates are genuine RCs used only for official-vs-local calibration, never for choosing between variants.

**P1-2 One safety-margin table.**
- W2 L20-22: walls 0.25–0.35 m (0.20 m at doors), people 0.6 m.
- Strategy §3 executor rules (L136-138): static ≥ 0.25 m, unseen ≥ 0.20 m, people ≥ 0.40 m + motion margin.
- Strategy design rules (L150-152): 0.15–0.20 m; people 0.6 m discs.
- B6: hard 0.25–0.35 m + soft 1 m.
- A3 R5: capsule + 0.35 m body + 0.10 m erosion.

Fix: in `briefs/W2-safety-executor.md`, add "Margins (single source; values live in `config/executor_margins.yaml`; others reference it)" with C7's set: static 0.25, unknown 0.20, people 0.40 + motion capsule (A3 R5), soft cost 0.40/0.80 m, door relaxation 0.20 m. Tuning happens only on train/val_seen diagnostics. Delete the margin numbers from strategy L150-152 and point to W2.

**P1-3 Teacher definition contradicts the strategy.**
- `briefs/W4` L13-14: "shortest path … on a navmesh inflated to radius 0.30 … converted to actions with the W2 executor logic".
- Strategy L141-145 and C7 rec. 7: plan on the **intersection of the 121 navmeshes with a clearance cost**, because a hard 0.3–0.4 m inflation closes 0.7–0.8 m doors. Also, W2 is a perceived-map executor, not the teacher (C5 K15).

Fix: replace W4 L13-14 with:

> privileged expert = `oracle/teacher`: 24-heading lattice planner on the AND of the 121 cached navmeshes (base + 120 frames) with a clearance cost (hard 0.05 m, preferred 0.20 m beyond the r = 0.1 boundary), escape-first when the student is within 0.05 m of the boundary (research/C7 §10.7–9). Every teacher tape has 0 flags under `allf`. Called through `PlanRequest/1` (purpose = teacher).

**P1-4 Contingency for a Phase-2 bundle without test-scan humans.** The strategy risk row (L276) proposes "HA-VLN-1.0 human priors (70 humans in test scans public)", which C3 T18 lists as PROHIBITED at inference, and the row ends in an unfinished sentence ("depth perception still sees them in official replay? No — …").

Fix: replace the mitigation cell with:

> If test humans are not shipped: generate under `gen:static` (humans absent locally) and measure the `gen:static`→CERT-9 Score loss on DEV now (C6 §6 "G-none"; C8 rec. 5). Raise the unknown-space and doorway margins by the amount that loss analysis selects on DEV. Never use HA-VLN-1.0 test annotations (T18). The penalty applies to every team.

Add the measurement as a W2 deliverable due at G5.

**P1-5 MP3D-never contingency.** C2 §9 and the digest ("Nov 7 mesh-free fallback trigger") would make a graph-based planner primary, but that planner uses prohibited inputs. Without MP3D no compliant agent can render observations.

Fix: in `01-strategy.md` §8, MP3D row, add "Without MP3D the only compliant tape is blind (instruction-only, no observations). Expected Score ≈ 8–15. No graph/mesh fallback is allowed." In `02-research-digest.md` C2, add "(the mesh-free plan uses test connectivity graphs: prohibited under C3; superseded)".

**P1-6 Quarantine the test-side assets now in `data/`.**
- `data/test_episode_index.json` rows carry `r2r_instruction_text`, `trajectory_id` and `collision_num_test_public` (verified).
- `test_trajectory_table.json` carries 3 original instructions and nav-graph candidates.
- `mp3d_test_scan_room_labels.json` and `collision_num_test.json` are test annotations.

All of these are readable by every agent (C5 K7). The README only *says* they are privileged.

Fix:
1. Move them to `data/privileged/`. Update `tests/test_score.py` L95 (`collision_num_{split}.json`) and the README paths.
2. Add `tests/test_quarantine.py`. It (a) fails if any file outside `oracle/` or `tests/` references `data/privileged`, `human_motion`, `.navmesh`, `.house`, `connectivity`, `R2R_test`, `collision_num_test` or `sample_room_paths`, and (b) fails if any file in the repo has sha256 `d15fe5df…` (B12 rec. 1).
3. Add a test-text guard: no 8-gram from `r2r_instruction_text`, or from the Phase-2 instructions once they arrive, may appear under `agent/`, `prompts/` or `configs/` (C10 C1).

**P1-7 Compliance feature flags are named nowhere.** C3 rec. 4 names `rollouts_k`, `scene_memory`, `preexplore`, `sibling_fusion`, `camera_cfg`.

Fix: add `config/compliance_flags.yaml` (specified in `briefs/README.md`). Each flag defaults OFF, maps to an issue item (4, 5a, 5b, 6, 2) and to an ADR id. The runner refuses to start in production mode if a flag is ON without an ADR reference. `SubmissionManifest/1` records every flag value.

**P1-8 Submission-policy ADR (four conflicts).**
- (a) Daily cap: W0 L18 "5 per UTC day … keep 30 slots" vs C3 rec. 6 and C5 §8.3 "≤ 2/day".
- (b) STOP-only in Phase 2: W0, W6 and strategy M4 make the STOP-only anchor upload #1 in Phase 2, but C3 T14 says "Calibration probes only in Phase 1".
- (c) A/B uploads: C4 allows "semantic-class A/B" uploads and "≤ 5 per-episode debugging submissions". C3, C6 §13.4 and strategy §6 reject disjoint-subset A/B.
- (d) Deadline: strategy "Nov 30 15:59 UTC", C2 "23:59 UTC", C3 "≥ 48 h before Nov 30 AoE", C9 "final by Nov 24–25".

Fix: add `DECISIONS.md` ADR-002 and replace W0's "Submission policy" paragraph with:

> - ≤ 2 uploads/UTC day; ≤ 30 genuine whole-pipeline RCs in Phase 2; ≥ 30 slots in reserve.
> - Phase-2 upload #1 = STOP-only pipeline check (no per-episode information; disclosed). This is the only non-RC upload.
> - No subset or class A/B uploads and no per-episode debugging uploads (C4's ≤ 5 allowance is rejected).
> - Every upload is approved by the human (Tier 3).
> - Deadline assumed Nov 30 15:59 UTC until item 12 is answered. Final RC uploaded by Nov 27 12:00 UTC.
> - Never cancel a running job.

**P1-9 Sensor and config facts that the strategy states without verification.**
- Strategy L304 states "Camera tilt for LOOK actions is 30° in the challenge config" as fact. A2 fact 29 and A5 say the habitat default is 15°; 30° comes from a competitor's report.
- A2 fact 30: the `DISTANCE_TO_HUMAN` measure resets the LOOK tilt on every update. This breaks C7's look-down-first rule if the local env enables it.

Fix:
- `01-strategy.md` L304: replace with "LOOK tilt: 15° habitat default; 30° reported by a competitor; W1-T01 records the image value in `facts.yaml`".
- `briefs/W1` forensics list: add "TILT_ANGLE; whether `DISTANCE_TO_HUMAN` is in MEASUREMENTS of the scorer and of our runner (it resets the tilt via `set_state`; our runner must exclude it); camera POSITION; depth MIN/MAX/NORMALIZE; GPS dimensionality".
- `briefs/W2`: add "read all sensor constants from `facts.yaml`; never hard-code them".

**P1-10 Phase-2 bundle intake and day-1 val verification have no owner.**
- A1 rec. 2 (bundle-day validation script) and C10 S17: assert ids 1..3408; scene/start pose vs the index to 1e-4; v1-3 vs v1-2 yaw; goals absent; `trajectory_id` present; human entries inventoried.
- A1 rec. 7 / B1 rec. 1: verify on HA-R2R `val_unseen.json.gz` today that ep 1 → trajectory 15 and eps 10–12 → 57, the rotation convention, token lengths and `info` contents.

Fix: add both to `briefs/W1` as deliverables, due D1 (val check) and Oct 30 + 4 h (bundle). Under quarantine rules, the bundle is written only to `/lake/test_bundle/`, which is mounted only into the production runner.

**P1-11 SimpleVLN must act inside the official 0.1.7 environment.** `briefs/W4` L8-9 says "Habitat 0.3.3 eval → build a side-environment or bridge to the 0.1.7 HA scenes". A side environment would produce tapes whose physics differ from the scorer's.

Fix: replace with:

> All test and val tapes are generated in the W1 runner (official image, Habitat 0.1.7, humans inserted). SimpleVLN runs only as a vLLM model server behind `AgentAPI/1`. Port its prompt and action-chunk parser from `eval.py`; Habitat 0.3.3 may be used only to reproduce its published numbers.

**P1-12 W3 DoD and dependencies are incomplete.**
- Add AT-W3-4: person detection recall ≥ 0.95 within 3 m (B11 rec. 3 targets ≥ 95 % within 6 m), median footprint error ≤ 0.2 m. Collision avoidance depends on it.
- Add AT-W3-2: end-region accuracy ≥ 0.70 on DEV.
- State that the (a) eval needs MP3D `.house` files (MP3D-blocked) and lives in `oracle/eval`.
- Add a per-instruction and per-frame latency/cost quota (C5 K17).
- Add the room classifier trained on train-scan renders and the `.house` parser (A9 rec. 2–3; room type is "the strongest semantic cue").
- Add `Percept/1` people tracks with persistent ids and `swept_radius_m` (W2 needs trails).

**P1-13 W4 is missing work items recommended in research.**
- HA-style long-instruction augmentation with the organizers' public prompt; fill human slots only from the 61 train scans (B10 P2, +2–6; A6 rec. 4).
- A frontier-API zero-shot agent + our shield as the early strong baseline and rival proxy (A7 rec. 4).
- Harness check: reproduce vln-safe's human-free ETP-R1 clean 37.7 / depth guard 50.1 before claiming gains (B10 measurement protocol; B2 rec. 1 suggests vln-safe as the integration backbone).
- Bake-off date and pre-registered criterion: Tue Nov 3 (C5 AT-W4-2); the C9 decision is Nov 9.
- SFT data format, and where HA-R2R train lives (`HA-R2R/train/train.json.gz` on HF, A11).
- Compliant stop priors and auxiliary heads: no stop before ~5 m, soft penalty beyond ~15 m, start-floor preference, "hops remaining" head (B12 rec. 4, A9 rec. 5).

**P1-14 W6 is missing the release procedure and ledger schema.**
- Release procedure: tag → clean regenerate → identical sha256 (C5 AT-W6-1, C10).
- Decision authority: the human approves every upload.
- `RESULTS.md` generated from `ExperimentRecord/1` JSONL, never hand-edited (C5 §5.4, C10 rec. 8, C5 K22). Each record carries the fingerprint, eval set, generation clock and integer counts (k, C, Σe, L, βL).
- Pre-registration of hypotheses before DEV runs (C5 §0.6: best-of-20 inflates DEV SR by 2.8 pp).
- Also run the starting-kit `check_submission.py` (A8 rec. 3).

**P1-15 W7 needs a time-box, the correct framing, and report milestones.**
- Add the kill criterion: without written permission by Fri Nov 6, Track B gets 0 agents (C5 AT-W7-2, K19). The oracle analysis and the teacher continue.
- `oracle/` must refuse `split=test` for Track B until permitted.
- Replace the framing "… and test-time self-consistency" (gray) with B8's named compliant modules: safety-shielded executor, human-occupancy foresight, humans-as-landmarks grounding, Score-aware stopping.
- Milestones: skeleton Nov 6, ablations Nov 20, draft Nov 25, final Dec 8.

**P1-16 MP3D licence and closed APIs.** The strategy allows closed APIs "for dev tooling and synthetic TRAIN data". Sending MP3D renders (train or test scenes) to third-party APIs may conflict with the MP3D Terms of Use (C5 Q4).

Fix: add to `briefs/README.md`: "MP3D-derived images go only to locally hosted models unless the team lead has confirmed the MP3D ToU permits it. Text-only API use (instruction augmentation) is unaffected."

**P1-17 Human-only steps are not marked.** W0 asks "an agent" to register, sign the MP3D ToU from an institutional address, email, and post from the team account.

Fix: prefix those bullets with `[HUMAN]`. Add `ops/accounts.md`, which names the single submitting CodaBench account (C5 AT-W0-1).

**P1-18 Tests and benchmarks the user asked for exist only as prose.**
- C10 specifies U14–U21, S1–S17 and C1–C7 with owners. None is assigned in the briefs; W6 L14 still cites "13 passing".
- Expected bands (L0 8.473053; L1 CMA 12.945 ± 1.0, but W1 says ± 0.5; L2 0.97–0.995; …) are not machine-readable.

Fix:
- Add a "Tests you own" line to each brief with the C10 ids: W1 S1–S9, S11, S13, S15, S17; W2 U14–U16, S10, S12; W3 U17; W5 U18, U19, S14; W6 U20, U21, S16, C7; W1 + red team C1–C6.
- Add `benchmarks/expected_bands.json` (L0–L8 from strategy §12, one tolerance per metric; pick ± 0.5 Score for CMA L1 and use it in W1, §12 and C10).
- Add pure-Python tests that can be written today without Habitat: `test_quarantine.py` (P1-6), `test_contracts_fixtures.py` (P0-3), `test_flags.py` (P1-7).

**P1-19 Research index and digest drift.**
- `README.md` L10 says "33 topics"; the folder has 32 (C4 and C5 missing).
- The digest says "C5 — *pending*" and "C4 — not run separately".
- The digest's B3 entry still says NavGPT-3 uses "our action space", which strategy L176-178 corrects ("4 cameras + teleport; not compliant").
- C2's STOP-only estimate (5.95) conflicts with A4's 8.473053.

Fix: copy C4/C5 (P0-3); rewrite the C4/C5 digest entries from their TL;DRs; append "(corrected in strategy v1.2: not compliant as published)" to B3; append "(C2 superseded: pre-pivot plan; A/B uploads, oracle Phase-1 uploads and the mesh-free fallback are withdrawn)" to the C2 entry.

---

## P2 — hygiene

1. **Test-count drift.** `01-strategy.md` L5 says "13 passing tests", §11 L332 says "15 tests", `briefs/W6` L14 says "13 passing" and `README.md` says 20. Actual: 20. Replace the counts with "see `python3 -m unittest discover -s tests`".
2. **Image tags.** `00-competition-facts.md` Docker row lists "tags v0.1.0-test-*, cr-domain-20261004" under digest `e1a0544f`, but cr-domain belongs to `78a62cd1` (strategy §1, A8). Split it into two rows.
3. **STOP-only prediction.** 8.473053 was computed from the R2R-CE geometry. Strategy M3/§12 calls it "exact". Add "recompute from HA-R2R `val_unseen.json.gz` on D1 (W6-T01)".
4. **Id types.** `data/val_unseen_splits.json` stores episode ids as ints, while the contract requires strings. Add a note, or a loader `havln_tools.load_eval_set(name) -> list[str]`.
5. **Missing helpers.** `havln_tools` has no `expected_ids(split)` loader and no CLI (`python -m havln_tools validate|score`). Add both, so W6 and W1 do not write their own.
6. **Hold-out pointer.** `briefs/README.md` rule 3 says "hold out 3 scans" without naming them. Point to `data/val_unseen_splits.json` (lockbox, ≤ 4 looks).
7. **Rules-gate dates.** "G-rules by Oct 28" (L100) and "freeze clean config if no answer by Nov 7" (L97) are both stated. Say: "Oct 28 = proceed with the clean configuration; Nov 7 = last date a YES can still be integrated".
8. **Sibling-voting gain.** Strategy §0.4 says "several SR points", C3 T09 says +6–7 SR, and B10 says +2–2.3 for modern continuous agents. Cite B10's number.
9. **W5 "world-model lookahead inside the agent".** Specify *learned* world models only. Simulator look-ahead is T05 (prohibited).
10. **CMA reproduction tolerance.** W1 says Score ± 0.5; strategy §12 and C10 say ± 1.0. Pick one (see P1-18).
11. **Brief template.** The briefs lack time boxes, escalation rules, non-goals and a resumable log (C5 K24). Adopt the C5 §10 template for new task briefs.
12. **Operations.** Weekly competitor and repo monitoring (A7 rec. 6; A8 rec. 6 hourly `ghcr` tag poll + `git ls-remote` on toolkit and HA-VLN) is unowned. Give it to W0 as a scheduled task.
13. **Per-step frame logging.** Log `frame_id` and `total_signals_sent` per step in every local replay (A3 R6). Add to W1.
14. **Phase-1 calibration.** Add C10's K2 one-wall-bump tape. It settles walls-count, allowance subtraction and the CR denominator in one submission (A4 rec. 6, A8 rec. 2).
15. **Agent count.** Strategy L229 says "beyond ~16 concurrent coding agents overhead dominates"; C5 says peak 18–20 with a hard cap of 24. Align.
16. **Public accusations.** "No public accusations; ask the organizers privately to verify uniformly" (C3 rec. 11). Add to W0.
17. **Awards logistics.** In-person attendance in Paris on Dec 12 for the oral (B8 rec. 7). Add to the timeline Dec row.

---

## Appendix A — per-brief completeness checklist (current state)

| Brief | Inputs | Outputs / JSON contract | Tests | DoD in brief | Pointers | Main gaps |
|---|---|---|---|---|---|---|
| W0 | implicit | log only | n/a | none (only in strategy) | wrong (§7 "five questions") | P0-1, P1-8, P1-17 |
| W1 | yes | prose CSV; no API schema | yes | CMA tolerance only | good | runner/sandbox (P0-3), regimes (P0-4), bundle intake (P1-10), forensics list (P1-9) |
| W2 | yes | none (goal belief undefined) | synthetic unit tests | yes | good (C7) | contract, margins (P1-2), STOP/budget ownership, no-humans measurement (P1-4) |
| W3 | yes | prose `program.json`, partial `perceive()` | none | (b) ≥ 0.8 only | good (B9, B11) | detector recall, MP3D dependency, latency budget (P1-12) |
| W4 | yes | none | none | milestones conflict (P1-1) | good (C9, B2) | teacher (P1-3), 0.1.7 runtime (P1-11), augmentation/baselines (P1-13) |
| W5 | yes | none | none | gray-lever DoD | C3 | rewrite (P0-2) |
| W6 | yes | ZIP via `havln_tools` | 20 unit tests (says 13) | TCR 0 all regimes (P0-4) | C6 | release procedure, ledger schema (P1-14), test-ZIP rule (P0-4) |
| W7 | yes | none | none | in strategy only | B-series | time-box, framing (P1-15) |

## Appendix B — research recommendations not carried into the strategy or briefs

| Recommendation | Source | Where it should land | Gap id |
|---|---|---|---|
| Compliant test-time levers P4–P7, runner-up visit | B10, B5, C8 | W5-S | P0-2 |
| CLEAN-1 sandbox, file audit, per-episode reset | C3 rec. 3, B8 rec. 2, C5 K1/K3 | W1 | P0-3 |
| 16 contracts, acceptance tests, starter backlog | C5 | `contracts/`, all briefs | P0-3 |
| Canonical regimes + CERT set | C5 §4.0, C6, C10 | W1 | P0-4 |
| `17DRP5sb8fy` bring-up | A11, C9 rec. 1, C10 rec. 3 | strategy §5, W1 | P0-5 |
| Leak disclosure + hash block in CI | B12 | 03 email, tests | P0-1, P1-6 |
| Quarantine list | C3 rec. 8, C5 K7 | `data/privileged/`, tests | P1-6 |
| Feature flags | C3 rec. 4 | `config/compliance_flags.yaml` | P1-7 |
| Bundle-day validation; val id check | A1, B1, C10 S17 | W1 | P1-10 |
| TILT / DISTANCE_TO_HUMAN check | A2, A5, C7 | W1 forensics | P1-9 |
| Detector ≥ 95 % recall | B11 | W3 DoD | P1-12 |
| Room classifier + `.house` parser | A9 | W3 | P1-12 |
| HA-style augmentation | B10 P2, A6 | W4 | P1-13 |
| Frontier-API baseline | A7 | W4 | P1-13 |
| Stop priors / aux heads | B12, A9 | W4/W2 | P1-13 |
| Release sha256 regeneration, generated ledger | C5, C10 | W6 | P1-14 |
| Track B kill date | C5 | W7 | P1-15 |
| Named innovation modules | B8 | W7 | P1-15 |
| Human-blind penalty measurement | C8 rec. 5, C6 G-none | W2 | P1-4 |
| `check_submission.py`, ghcr poll, competitor watch | A8, A7 | W6, W0 | P1-14, P2-12 |

## Appendix C — contradictions found (numbers, verdicts, thresholds)

| Topic | Values | Resolution proposed |
|---|---|---|
| Organizer questions | §7: 7 questions; 03: 10 items; W0: "five" | 03 is canonical; extend it to 13 (P0-1) |
| Multi-rollout / contact selection | strategy "allowed"; C3 gray / contact prohibited | C3 verdict (P0-2) |
| R2R test instructions | W5 uses them; C3 prohibited | delete from W5 (P0-2) |
| Regimes | 4 / 7 / 9 / R0–R4 / R0…Rall (R0 means two different things) | canonical ids + CERT-9 (P0-4) |
| W6 DoD | TCR 0 on all regimes vs ≤ 1 % contact episodes vs TCR ≤ 0.02 | CERT-9 gate on val; no test collision gating (P0-4) |
| SR targets | 5 different sets | one gate table (P1-1) |
| Teacher | r = 0.30 inflation vs 121-mesh AND + clearance cost | C7 (P1-3) |
| Margins | 5 different sets | `executor_margins.yaml` (P1-2) |
| Upload cadence | 5/day vs ≤ 2/day; STOP-only Phase 2 vs Phase-1-only probes; C4 A/B vs C3 none | ADR-002 (P1-8) |
| Deadline | 15:59 UTC / 23:59 UTC / AoE −48 h / Nov 24–25 | 15:59 UTC; final RC Nov 27 (P1-8) |
| TILT | "30° (fact)" vs default 15° | verify (P1-9) |
| Hold-out split | `data/val_unseen_splits.json` lockbox vs C5 HOLDOUT-v1 | data file canonical (P0-3) |
| HA-1.0 test humans | risk mitigation vs T18 prohibited | remove (P1-4) |
| Mesh-free fallback | C2 primary on Nov 7 vs prohibited inputs | withdraw (P1-5) |
| Test counts | 13 / 15 / 20 | 20 (P2-1) |
| CMA tolerance | ± 0.5 vs ± 1.0 | ± 0.5 (P2-10) |
