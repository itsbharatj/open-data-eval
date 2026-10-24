# V3 — Adversarial feasibility review of the Track 2 plan (strategy v1.2 + briefs W0–W7)

Reviewer: V3 (project-feasibility lens) · Sat 2026-10-24, evening UTC · Phase 2 opens Oct 30, closes Nov 30 (assume **15:59 UTC**).
No web searches. Evidence comes from the repo (`competitions/roboworld2026-track2/`), `research/`, `findings/` and the local clones under
`scratchpad/ext/`. Probabilities are my judgement and marked (low/med/high confidence); everything marked *verified* was read from a file
cited in §6.

Read: CONTEXT.md; 00-competition-facts.md; 01-strategy.md v1.2; 02-research-digest.md; briefs/README + W0–W7; 03-organizer-questions.md;
research C2, C1, C9, A11, A12 in full; C5 §0–§1; C6 regime section; C10 fixture lines; `ext/sota/SimpleVLN` (README, eval/README,
eval.py, requirements, eval.sh); `ext/sota/vln-safe` (README, docs/agent_notes/etpr1.md, environment/*.yml); `ext/HA-VLN/HASimulator/
environments.py` and task configs; `data/val_unseen_splits.json`; `havln_tools` (ran the 20 tests: pass).

---

## 0. Verdict (12 points)

1. **The plan is technically sound but is scheduled as if Matterport3D (MP3D) is on disk by Oct 26–27.** Without a known existing
   licence, P(MP3D by Oct 28) ≈ 0.38 (low confidence). Every milestone from M2 on is MP3D-gated: risk-adjusted M2 is P50 ≈ Nov 1,
   P80 ≈ Nov 11. The headline "Score 46–55" is the best-case scenario; the probability-weighted expectation is ≈ 34 (§2.1).
2. **The first P0 is in no brief: who can legally sign the MP3D Terms of Use?** The ToU requires an academic institution and an
   institutional address; the team's contact address on record is not institutional (A11 §5 rule 3). If no academically affiliated
   member and no existing institutional licence exist, the compliant track is infeasible: observations must be rendered from the meshes
   (C9 §8: "No MP3D at all: the compliant track is impossible"). This must be answered within hours, not days.
3. **The ready-to-post organizer issue is missing the questions that matter most for feasibility.** `03-organizer-questions.md`
   (10 items, verified) does not ask whether the Phase-2 bundle contains test-scan human placements, through which channel it ships,
   the exact close timestamp, or for an expedited MP3D route. Strategy §7 had those (Q3, Q5); they were lost when C3's draft replaced
   it. The private email omits the B12 leak (`sample_room_paths.json`, 879 test episodes) that strategy §2 says to disclose before
   Oct 30 (grep: 0 mentions in 03 and in all briefs). W0 says "the five questions from §7" (§7 has seven; 03 has ten).
4. **SimpleVLN's port is cheap, but nobody plans to check it.** The policy is one ~250-line agent class plus a separate vLLM 0.18
   server (verified). Its 76.7 SR was measured in Habitat 0.3.3 at 640×480, a 4:3 image, while the official camera is 224×224 square at
   the same 90° HFOV. That is a different image geometry, not just a lower resolution. No brief has a port-parity test, so a weak
   zero-shot number cannot be attributed to a port bug, the camera, the HA text or the humans. I would plan on zero-shot test SR of
   0.15–0.30, not 0.28–0.36.
5. **ETP-R1 is the most expensive port and pays least in the clean configuration.** It needs its own py3.6 / torch 1.10.2+cu113 worker
   env, 22-TURN sweeps and a budget rule. Its value is diversity, and the 87 % "union" gain needs K>1 selection, which is gray. Defer it
   until after the minimum viable submission (MVS), or drop it unless K>1 is approved. That frees 2 agents.
6. **Fan-out before MP3D and frozen contracts wastes agents.** Without MP3D only ~7 seams are executable. Cap the team at 7–8 coding
   sessions for the first 72 h and scale to 12–14 only after gate R72 (Oct 27) passes and MP3D is on disk. Otherwise agents write
   sim-dependent code that first runs a week later.
7. **The constraint is the serial chain, not GPU-hours.** The 5–10k GPU-h estimate overstates the need (§1 P1-8). The serial chain
   is: MP3D → navmesh cache for 61 train scans (7,320 builds, cost unmeasured) → teacher → renders → SFT round 0 → DAgger rounds
   (≈ 1 day each). From MP3D-day to the first fine-tuned model takes ≥ 7–9 days even with no bugs.
8. **The human clock probably cannot be calibrated officially.** That needs MP3D, a working CodaBench and Phase-1 uploads by Oct 30
   (P ≈ 0.25). Plan to the two-sided envelope (frames ≤ 26 and frame 119) and do not spend Phase-2 uploads on timing probes.
9. **The documents contradict each other, so agents will chase different targets:**
   - three different SR schedules for W4 (§5 table, §6 gates, W4 brief);
   - three sets of human-timing regimes (W1: 6 modes; W6: 4; W2 and C6: 9);
   - two val_unseen lockboxes (`data/val_unseen_splits.json` vs C5 HOLDOUT-v1);
   - W6/§5 "TCR 0 on all regimes" for *test* ZIPs vs the issue's Q8 promise not to use test local-replay outcomes to choose between
     variants;
   - test counts of 13 / 15 / 20 across documents.
10. **Ownership holes:** the closed-loop runner and sandbox; Guard v2 (W2 or W4); the privileged teacher (W2, W4 or W7); the person
    detector (W3 or W4); the vLLM serving pool; the stop verifier; Phase-2 bundle ingest; the B12 disclosure; the integrator/release
    role.
11. **An MVS must exist by Nov 10 whatever happens (§4).** If MP3D is on disk by Nov 6:
    - SimpleVLN zero-shot, or SFT round 0 if it is ready;
    - Guard v1 plus GPS contact escape, and a hard STOP at ≤ 490 actions;
    - K=1, official camera, full test run, validated and uploaded.

    Expected Score ≈ 19–28, already at or above published HA-VLN-CE SOTA (~22–23). Otherwise the MVS is the STOP-only anchor plus
    escalation.
12. **Move the final upload to Nov 25 and keep a recent scored entry.** From the MVS on, upload the best-known ZIP at least every 5
    days. The best score is retained automatically and ties go to the earlier upload (A12), so early uploads are free insurance against
    a late outage or queue congestion.

---

## 1. Critical-path items the plan under-weights

Severity: P0 = can end the effort or silently invalidate a submission; P1 = shifts the schedule by days; P2 = degrades the result.

### P0-1 MP3D eligibility and approval latency
- **Facts:**
  - The ToU requires an institutional email and an academic institution (A11 §1.5, §5).
  - The mailbox has gone unanswered for about a month in niessner/Matterport #65 and #74.
  - The habitat data is one 15 GB zip for all 90 scans.
  - Unofficial mirrors, and the public `download_mp.py` URL used before your own approval, are licence breaches. Award winners may be
    asked for code, so this is a disqualification risk (A11 §5 rule 2).
- **Under-weighted because:**
  - W0 assumes affiliated signers exist and has no decision rule if they don't.
  - Strategy §8 lists "MP3D approval lags", not "we may not be eligible".
  - There is no compliant fallback. The mesh-free C2 §9 fallback uses test-scan nav-graphs, which are prohibited at inference under
    the Oct-14 rules.
- **Scenario prior (low confidence):**

  | Scenario | P | Data on disk |
  |---|---|---|
  | A: existing usable licence | 0.35 | by Oct 26 |
  | B: fresh request answered | 0.20 | Oct 28–31 |
  | C: slow answer | 0.20 | Nov 1–10 |
  | D: later or never | 0.25 | after Nov 10 or never |

- **Fix (human, within 4 h):**
  - (a) Does any member hold, or belong to an institution with, a licence that covers this work and the compute it will run on?
  - (b) Who are the ≥ 3 academically affiliated signers, at different institutions if possible?
  - (c) If (a) and (b) are both empty: recruit an academic collaborator to join the team and host the MP3D-dependent compute on
    licensed infrastructure. Decide by Oct 26 12:00 UTC.
  - Also ask the organizers for an expedited route (issue item 13, §5 W0).

### P0-2 The organizer communication as drafted misses the bundle, the close time, MP3D and the B12 disclosure
- **Verified:** issue items 1–10 cover rules only. 10(b) only asks for the Terms text. No item asks:
  - whether `human_motion.json` will cover the 18 test scans;
  - for the delivery channel, or a mirror while CodaBench is down;
  - whether `collision_num_test.json` is the scoring baseline;
  - for the UTC open and close timestamps or the grader time limit;
  - for MP3D access.

  The private email lists `collision_num_test.json`, the HA-1.0 test humans, the connectivity graphs and the R2R instructions, but not
  `sample_room_paths.json`.
- **Consequence:**
  - We learn the bundle contents only on Oct 30, with no time to react.
  - The B12 disclosure, which protects the leaderboard and us, never happens.
- **Fix:** add items 11–13 and the B12 paragraph (exact text in §5 W0). Post today.

### P0-3 The Phase-2 bundle may lack test-scan human placements
- **Verified:**
  - `human_motion.json` covers 72 scans and none of the 18 test scans.
  - `HASimulator/environments.py` L175 does `self.human_motion_data.get(scan, {})`: a missing scan silently gives **no humans and no
    error**.
  - Local test rollouts would therefore be human-free while the official replay contains humans. The agent cannot see or avoid them.
  - The clarification's Q11 wording ("provided to support simulator rendering") suggests the organizers intend to ship them.
- **P(missing on Oct 30) ≈ 0.25** (low–medium confidence).
- **Consequence (my calculation with the official formula):** at the plan's operating point, SR 0.50 → ~0.40, CR 0.05 → ~0.30 and
  TCR 0.08 → ~0.5 take the **Score from 48.4 to ~37**. The same handicap hits every compliant team, so rank suffers less than Score.
- **Fix:**
  - Ask now (P0-2).
  - W1's ingest script must assert that all 18 test scans are present and raise an alarm otherwise.
  - Keep measuring C6's G-none regime (generate without humans, replay with humans) on val so the penalty is known.
  - Do **not** try to compensate with prohibited test-side data (HA-1.0 test humans, `collision_num_test.json`).

### P1-4 The CodaBench outage, and grader throughput
- **Facts (A12):**
  - The site has been unreachable since Oct 21 with no ETA.
  - Limits apply per account. Failed submissions are free; cancelled or stuck ones count.
  - Force_Best (best score retained) is automatic.
  - The phase boundary is probably 15:59 UTC.
  - The default public-queue time limit is 600 s; the organizer worker is probably custom.
  - In v1.34, a stuck submission can keep a better one off the leaderboard (#2557).
- **Probabilities (low confidence):**

  | Event | P |
  |---|---|
  | Still down on Oct 30 | 0.4 |
  | Still down on Nov 10 | 0.2 |
  | Down at Nov 27–30 with no organizer extension | 0.05 |
  | No Phase-1 calibration happens at all (it also needs MP3D by ~Oct 28) | ≈ 0.65 |

- **Under-weighted:** the grader's **execution-time limit vs tape length**. ETP-R1 with sweeps averages ~225–270 actions, more than
  CMA-length tapes. A timeout is a free "Failed", but it costs a day of turnaround. Nobody owns measuring grader throughput.
- **Fix:**
  - Prefer the monocular policy (no sweeps) for the MVS.
  - Upload the STOP-only val ZIP the moment CodaBench returns in Phase 1. It needs no MP3D and checks Euclidean NE exactly (predicted
    8.473053).
  - Final upload by Nov 25.
  - If the site is down, email the organizers the ZIP's sha256 and a link as timestamp evidence.

### P1-5 Porting SimpleVLN across Habitat versions
- **Verified:**
  - SimpleVLN's evaluator is Python 3.10 with habitat-sim/lab 0.3.3 (`eval/README.md` L12–27). The model is served from a separate
    vLLM 0.18 environment (`requirements-vllm.txt`). The 0.3.3 dependence is only in `Env`, the config and the measures
    (`eval.py` L1–30, L450–493).
  - The agent logic is portable:
    - system prompt;
    - ≤ 8 uniformly sampled history frames plus the current frame;
    - temperature 0.3, top-p 0.95;
    - a regex chunk parser.
  - The headline SR is `sucs_all`, the mean over trials. pass@k is reported separately (`eval/README.md` L257–269), so 76.7 is a
    single-run mean. Good news. The launcher's `PASS_K=4` default does not change the headline.
- **Under-weighted:**
  - (a) **Camera geometry.** 640×480 at HFOV 90 gives a ≈ 74° vertical FOV, while 224×224 at HFOV 90 gives 90°. The zero-shot drop is
    unknown, and whether a different resolution is allowed is gray (issue Q2).
  - (b) **No parity test anywhere** (fix in §5 W4).
  - (c) The challenge image is py3.8. Call the OpenAI-compatible endpoint with plain `requests`, not `openai>=1.0`.
  - (d) The SimpleVLN weight licence is unknown (C9 §15). Check the HF model cards before relying on them for an award.
- **P(> 3-day slip to a *trustworthy* zero-shot DEV number after MP3D-day) ≈ 0.3.**

### P1-6 Serving vLLM next to the Habitat 0.1.7 / torch 2.0.1 container, and the GPU fleet
- **Verified:**
  - The challenge image is py3.8, Habitat 0.1.7, torch 2.0.1+cu118 (C1 §1.1).
  - vln-safe already runs habitat 0.1.7 with the VLAs as subprocess workers in their own envs (vln-safe README). The sidecar pattern is
    proven.
  - The ETP-R1 worker env is Python 3.6.13 with torch 1.10.2+cu113 (`worker_etpnav.yml` L95, L216). It has no native Hopper or
    Blackwell kernels and depends on PTX JIT (inference: verify before investing).
- **Under-weighted:**
  - (a) **EGL in containers.** Habitat needs `NVIDIA_DRIVER_CAPABILITIES` to include `graphics`. The mapping between habitat-sim's
    `gpu_device_id` and `CUDA_VISIBLE_DEVICES` is a classic day-1 blocker on k8s and cloud.
  - (b) **GPU SKU.** HA-VLN #20 reports the RTX 5090 is incompatible. If the "unlimited compute" is Blackwell, keep an Ampere/Hopper pool
    for Habitat.
  - (c) **Co-location.** vLLM's default `gpu_memory_utilization` of 0.9 plus 8–16 Habitat processes at 1–2.5 GB each will OOM. Use
    separate pools (as in C9 §7) or cap utilization at ≤ 0.5.
  - (d) **Reproducibility.** Log a per-request seed for every sampled call (report and verification).
- **Fix:** a day-1 SKU/EGL smoke matrix (§3, block 1).

### P1-7 Calibrating the human-frame clock
- **Facts (A3, C6):**
  - Slow local agents see frames 110–119; fast replay sees frames ≤ ~26.
  - Official calibration needs moving tapes uploaded in Phase 1 (C6's four-submission set), i.e. MP3D, CodaBench and the CMA export all
    before Oct 30 (P ≈ 0.25).
- **Fix:**
  - Roll out on `schedule(S_fast)`.
  - Certify on DEV under R0, R26, R119, Rstall, Rbase and Rall with two-sided person margins.
  - Do not spend Phase-2 uploads on timing.

### P1-8 Data volumes and compute (sized, so the plan stops over- or under-estimating)

| Item | Volume | Risk | Note |
|---|---|---|---|
| Navmesh cache | val_unseen 1,320, test 2,160, train 7,320 builds | cost per build unmeasured (C1: "3–20 s", low confidence); at 60 s the train cache is ~120 GPU-context-hours, ~4 h on 32 procs | Launch the hour MP3D lands, one writer per scan (C1 flag 5: write race). **The cache key is only scan + frame** (C1), so a teacher cache built at r = 0.3 written into the official directory silently corrupts scoring. Use separate directories. |
| HAPS | 116,640 small files; every process parses 58,320 configs (10–30 s) | NFS start-up blow-up | Local NVMe copy on each node (A11 §0.5). |
| Guard v2 labels | C9: 10–50 M states × 24 headings, label = flagged on the base navmesh or any of 120 frame navmeshes → up to ≈ 1.5e11 `try_step` calls ≈ 1,000+ core-hours | CPU tier saturation | Prune: test the 120 frame navmeshes only when a human lies within 2 m of the swept segment (≈ 10–30× fewer calls). |
| Renders | ≈ 2.5 M frames per expert pass ≈ 40 GB at 224² (RGB JPEG + 16-bit depth); DAgger + RFT ×5 → ~0.2 TB; with RxR-CE ≤ ~1 TB | none on a 2–4 TB volume | — |
| SFT tokens | at 224²: 9 images × ~64 tokens + ~150 text ≈ 0.75k tokens/sample → 325k samples ≈ 0.25 B tokens/round (C9's 1–3 B assumes 640×480) | none | ≈ 10–20 H100-h per 9B round |
| Rollouts | val_unseen K=1 < 30 min; test K=5 3–6 h (C9) | env steps dominate, not GPUs | — |

**Conclusion:** GPU-hours are not a risk. The risk is the serial chain. Even in scenario A it is MP3D → caches (≈ ½ day) → teacher and
renders (≈ 1 day) → SFT r0 (≈ ½–1 day) → evaluation (≈ ½ day) → DAgger rounds (≈ 1 day each, including evaluation). The first
fine-tuned model lands ≥ 7–9 days after MP3D-day.

### P1-9 12–14 (really ~20) parallel coding agents merging into one repo
- C9 staffs 12–14 sessions for the compliant track alone (env 2, VLA 2, guard 3, expert 2, train 2, ETP 2, eval 1). W0, W3, W5, W6 and
  W7 come on top, giving ≈ 20 (C5: peak 18–20, hard cap 24).
- **Feasibility problem:** before MP3D only these seams are *executable*:
  - forensics;
  - the HA-mini env and runner;
  - vLLM serving;
  - the synthetic executor and guard;
  - instruction text;
  - submission tooling;
  - the SFT round-trip.

  Extra agents would write the DAgger driver, the ETP sweep adapter or the Guard v2 trainer blind, and integration would fail a week
  later.
- **Merge mechanics to make it work:**
  - an INT owner;
  - trunk plus a merge queue;
  - CODEOWNERS per package;
  - frozen, versioned `contracts/`;
  - CPU-only CI under 10 min (C10's F-SYN), with GPU tests nightly;
  - generated `RESULTS.md` and `STATUS.md` (C5);
  - read-only shared configs (`regimes.yaml`, splits);
  - cross-package edits only through INT.
- **Human bandwidth:** Tier-2/3 actions (uploads, organizer messages, contract changes) need the human for about 2 h/day (C5). Name a
  deputy, or uploads slip whenever the lead is offline.

### P2-10 MP3D licence vs closed-source APIs
- The architecture's System 2 is a "frontier VLM". Shipping MP3D renders to third-party APIs is a gray area under the EULA, since
  derived data leaves the licensed premises (A11 §5 rule 4). The organizers also encourage open 7B models.
- **Default System 2 to a local open-weight VLM.** Use closed APIs only for text, such as instruction parsing, unless the licence
  holder's institution approves in writing.

### P2-11 Report and award logistics
- Top-5 teams must contribute a technical report and may be asked for code.
- The W7 draft is due Nov 25, before the final numbers exist. Start a stub at the MVS (Nov 10) and insert the numbers after the final
  upload.

---

## 2. Risk-adjusted timeline

### 2.1 MP3D scenarios drive everything (probabilities low confidence; durations medium)

| Scenario | P | MP3D on disk | M2: val cache + CMA reproduction | First trustworthy compliant DEV number | First compliant test upload | SFT-r0 model | DAgger rounds before the Nov 20 freeze | Expected final K=1 test Score |
|---|---|---|---|---|---|---|---|---|
| A existing licence | 0.35 | Oct 25–26 | Oct 27–28 | Oct 29–30 | Oct 31–Nov 2 | Nov 5–7 | 2–3 | 42–52 |
| B fast approval | 0.20 | Oct 28–31 | Nov 1–2 | Nov 3–4 | Nov 4–6 | Nov 9–11 | 1–2 | 36–46 |
| C slow approval | 0.20 | Nov 1–10 | Nov 4–12 | Nov 6–14 | Nov 7–15 | Nov 14–20 | 0–1 | 25–38 |
| D late or never | 0.25 | after Nov 10 / never | — | — | MVS-0 only, or zero-shot if MP3D arrives by ~Nov 22 | — | 0 | 6–28 |

Probability-weighted expected Score ≈ 0.35·47 + 0.20·41 + 0.20·31 + 0.25·12 ≈ **34**. The plan's 46–55 is scenario A.

### 2.2 Slip probability and consequence for every milestone in strategy §6

| Milestone (plan date) | Plan acceptance | P(slip > 3 d) | Drivers | Consequence | Risk-adjusted P50 / P80 | Mitigation / trigger |
|---|---|---|---|---|---|---|
| G0 (Oct 24) | registered, questions filed, MP3D requested, image pulling, scaffold | 0.15 | no academic signer; incomplete issue text | MP3D clock starts late; if no signer at all, Track A is infeasible | Oct 25 / Oct 26 | 4-h licence triage; post the amended issue today |
| M1 (Oct 26) | container boots, `/opt/havln-challenge` read, `havln-validate` PASS on STOP-only, scorer spec frozen | 0.20 | EGL/graphics capability, Blackwell SKU, HAPS size/HF throttling, scorer shipped as bytecode | scorer facts (camera height, LOOK angle, CR build, frame timing) stay unknown; executor design guesses | Oct 26 / Oct 28 | forensics with `docker cp` needs no GPU; SKU matrix on day 1 |
| M2 (Oct 28) | val_unseen navmesh cache, STOP-only replay = prediction, CMA reproduces README | 0.60 | MP3D | every sim-dependent date moves 1:1 | Nov 1 / Nov 11 | HA-mini bring-up; MP3D-day runbook ready by Oct 27 |
| M3 (Oct 29), executor | executor given the GT goal: SR ≥ 0.90 on val_unseen | 0.75 | MP3D + FrameScheduler + executor maturity | W2's DoD fails on paper; no real harm if decoupled | Nov 5 / Nov 15 | split the DoD: HA-mini + SYN-HA by Oct 29; val_unseen at MP3D+5 d |
| M3 (Oct 29), calibration | Phase-1 calibration set | 0.65 (never happens) | CodaBench + MP3D (the CMA export needs the sim) | grader speed and CR build uncalibrated; rely on the README anchor + test STOP-only | — | upload STOP-only val as soon as CodaBench is up (MP3D-free) |
| M4 (Oct 30) | bundle inventoried, test navmesh cache, STOP-only anchor uploaded | 0.40 | bundle channel; test humans present?; MP3D for the test cache; CodaBench | late leaderboard presence; test runs without humans | Nov 1 / Nov 6 | ingest poller; test STOP-only ZIP pre-built from ids 1..3408 |
| G5 (Nov 2–6) | zero-shot SimpleVLN + guard on test: SR .28–.36, Score 25–32 | 0.55 (date); P(SR ≥ .28 on arrival) ≈ 0.35 | MP3D; port parity; 224² camera gap; humans; CodaBench | MVS at risk | Nov 6 / Nov 15 | MVS gate Nov 10 with a realistic bar (§4) |
| W4 brief, Nov 3 | SR ≥ 0.30, TCR ≤ 0.05 | 0.60 | as G5 | — | — | restate relative to MP3D-day (§5 W4) |
| G6 (Nov 9–13) | Guard v2 + HA SFT: SR .40–.47, Score 36–43 | 0.65 | train-scan cache, teacher, render pipeline, Qwen3.5 SFT toolchain, output-format reconstruction, label volume | fewer DAgger rounds: −5…−10 SR at freeze | Nov 15 / Nov 21 | SFT round-trip dry run in the first 72 h; Guard v1 stays the fallback |
| W4 brief, Nov 13 | SR ≥ 0.45, TCR ≤ 0.02 | 0.65 | as G6 | — | — | restate |
| G7 (Nov 16–20) | + DAgger, voting, stop check, SR .46–.54; freeze Nov 20 | 0.50 if not enforced | ≈ 1 day per DAgger round + bug cycles | final K≥1 test inference (3–6 h), validation and ablations squeezed | the freeze does **not** move; cut scope (§2.4) | cut ladder |
| G8 (Nov 27) | final candidate scored | 0.10 (slip = miss the deadline) | CodaBench outage/congestion, execution limit, stuck jobs | catastrophic | — | **final upload Nov 25**; best-known ZIP uploaded every ≤ 5 d from Nov 10 |
| Report (Dec 1–8) | report + verification pack | 0.30 | numbers late; attention | award forfeit | — | stub on Nov 10; INT co-owns |

### 2.3 Revised gates (UTC)

| Gate | Date | Acceptance (measurable) | Needs MP3D |
|---|---|---|---|
| G0' | Oct 24 24:00 | licence triage answered in writing; amended issue posted (items 1–13); private email with the B12 paragraph sent; ≥ 3 MP3D requests or a licensed copy located; team registered | no |
| **R72** | Oct 27 20:00 | the MP3D-less readiness criteria in §3 (10 items) | no |
| D+1 (MP3D-day + 1) | — | 90 scans × 4 files verified; HA-mini + val_unseen caches warm; STOP-only val replay = prediction to 1e-6; CMA 2-episode export | yes |
| D+3 | — | SimpleVLN port parity (§5 W4); zero-shot DEV clean SR at 224² with Guard v1 reported with denominators | yes |
| T-escalate | Oct 31 | no MP3D → daily escalation; academic-partner decision taken | — |
| T-cut-1 | Nov 3 | no MP3D → stop ETP-R1 and Track B; everyone on the MVS path and the HA-mini SFT pipeline | — |
| **MVS** | Nov 10 | §4 | MVS-1 yes; MVS-0 no |
| G6' | Nov 15 | SFT-r0 (or DAgger-r1) uploaded if it beats the MVS on DEV (paired CI); Guard v2 promoted only if it beats Guard v1 on DEV | yes |
| G7 | Nov 20 (fixed) | architecture freeze; after it, only thresholds and data | yes |
| Final | Nov 25 | final candidate scored; Nov 26 → Nov 30 15:59 reserved for re-uploading the same ZIP after platform failures | — |

### 2.4 Scope-cut ladder (apply in order whenever a gate slips)

Cut in this order:
1. ETP-R1 port.
2. Track B beyond oracle failure analysis.
3. GRPO.
4. RFT.
5. Third DAgger round.
6. The learned predictor in Guard v2 (keep the map-based person keep-out).
7. Per-decision K-sample voting (keep K=1 greedy).

**Never cut:**
- Guard v1;
- exact pose-delta contact detection and escape;
- the STOP and budget rules;
- validation and the ledger;
- the report stub.

---

## 3. The first 72 hours, assuming MP3D is NOT approved (T0 = Sat Oct 24 20:00 UTC → Tue Oct 27 20:00 UTC)

### 3.1 What can be exercised without MP3D
- **HA-mini = `17DRP5sb8fy`.** Source: the public `mp3d_example.zip`, distributed by habitat-sim 0.1.7 CI (`.circleci/config.yml`
  L325). It has 10 humans in `human_motion.json` and 75 HA-R2R train episodes in 25 trajectories, 6 of them with `collision_num` > 0
  (C10 F12; A11 §1.6).
  - It exercises the real image, real HAPS assets, real per-frame navmesh recompute, real collisions and real RGB-D with humans.
  - **Caveats:** it is a TRAIN scan that SimpleVLN probably saw in R2R training, so numbers are optimistic. It is a single building, so
    there are no statistics.
- **SYN-HA (new; not in the plan).** These are public non-MP3D Habitat scenes from `habitat-test-scenes.zip` (habitat-sim 0.1.7
  README L195): `apartment_1`, `van-gogh-room`, `skokloster-castle`.
  - Lay them out as `<name>/<name>.glb`. Add a **private** human-annotation file that places HAPS humans by script; HASimulator keys
    humans by the scene directory name (`environments.py` L174–175).
  - Use them for point-goal executor and guard tests in buildings other than HA-mini.
  - Never place this file in the scorer's data root. Replica is a further candidate; check its licence first.
- **F-SYN.** C10's pure-Python synthetic world (polygons, Habitat-exact kinematics, a 2.5-D depth raycaster) for CPU CI on every PR.
- **Text-only work:**
  - the HA-R2R train and val instructions (parser, 144-way human-mention matcher);
  - reconstructing the SimpleVLN prompt and output format from `eval.py`.
- **Submission side:**
  - STOP-only ZIPs for val_seen, val_unseen and test (test ids 1..3408 are public);
  - a Phase-1 STOP-only upload the moment CodaBench returns.

### 3.2 Staffing for the 72 h: 7 coding sessions plus the human

| Seat | Owner of |
|---|---|
| INT | repo, contracts, CI, regimes, splits, quarantine |
| W1-a | image, forensics, data, SKU matrix, runbook, SYN-HA |
| W1-b | HA-mini env, FrameScheduler, closed-loop runner |
| W4-a | vLLM pool + SimpleVLN client |
| W2 | executor + Guard v1 + contact detector + teacher on HA-mini |
| W4-b | from h24: SFT toolchain round-trip; W3 text components if idle |
| W6 | submission tooling, STOP-only ZIPs, Phase-2 ingest |
| Human (W0) | licence, organizers, registration, uploads |

ETP-R1, W5, W7 and Track B are **deliberately not staffed**.

### 3.3 Plan by block

| Block | Who | Work | Deliverable |
|---|---|---|---|
| **h0–4** (Sat 20:00–24:00) | Human | MP3D licence triage (3 questions, P0-1); post the amended issue (items 1–13); private email with the B12 paragraph; Google-Form registration; ≥ 3 MP3D requests or locate the licensed copy; maintainer pings to public academic addresses | G0' log with timestamps |
| | W1-a | `docker pull` both digests (`e1a0544f…`, `78a62cd1…`). Start downloads: `download_data.sh --target all`, HA-R2R `train.json.gz` (pinned rev, sha256), `mp3d_example.zip`, `habitat-test-scenes.zip`, SimpleVLN weights (Qwen3.5-4B-RL, Qwen3.5-9B-RL, Qwen3-VL-8B-RL, ≈ 50 GB). Local NVMe layout | downloads running, SHA256SUMS |
| | INT | Repo scaffold; `contracts/` v1 from C5 §4.3 (EpisodeInput/1, Observation/1, PrimitiveProposal/1, SubgoalProposal/1, RolloutRecord/1, ExperimentRecord/1); CODEOWNERS; CPU CI; move test-side assets to `quarantine/`; `configs/regimes.yaml` (C6's nine); splits = `data/val_unseen_splits.json` | scaffold commit |
| **h4–24** (Sun) | W1-a | Forensics via `docker create` + `docker cp` (no GPU): `/opt/havln-challenge/**`, `/app/config/challenge_submission.yaml`, CLIs. Answer camera POSITION, LOOK angle, the sensors enabled in replay, the CR formula in each digest, frame advance, cache path. **SKU/EGL matrix:** `havln-check-environment` + 100 rendered frames + 1 `recompute_navmesh` on each GPU type | `research/image-forensics.md` (file:line); SKU table |
| | W1-b | HA-mini fixture (scene, 10 humans, HAPS, 75 episodes); warm 120 navmeshes and **measure s/frame and MB/frame**, extrapolate to 90 scans; FrameScheduler regimes `frozen(k)`, `schedule(S)`, `wallclock`. Tests: determinism ×3, STOP-only, LOOK no-move, wall-slide count = prediction | cache metrics; 4 tests green |
| | W4-a | vLLM 0.18 sidecar for Qwen3.5-4B-RL on a GPU **separate** from Habitat; latency p50/p95 at 224² and 640×480. Extract SimpleVLN's agent logic into `agent/simplevln/` (py3.8, `requests`) with unit tests on saved frames: same prompt bytes, same parse results as the upstream code | client + tests |
| | W2 | F-SYN executor (24-heading lattice, float32 pose emulation); Guard v1 = vln-safe stall-mem1 port (pure numpy); exact contact detector (moved < 0.24998 m); C10 U3/U5/U8/U14/U15 | CPU-CI green |
| | W6 | STOP-only ZIPs (val_seen, val_unseen, test); predicted val Scores (val_unseen 8.473053); in-container `havln-validate` for val; Phase-2 ingest poller (HF commits, toolkit/HA-VLN repos) that asserts the 18 test scans are in `human_motion.json` | ZIPs + sha256; poller running |
| **h24–48** (Mon) | W1-b + W4-a | Closed-loop runner. The agent runs in a separate process with no navmesh, human file or GT mounted; Observation/1 hides `frame_id`, the collided flag and distance-to-goal. Run SimpleVLN-4B-RL + Guard v1 on the 75 HA-mini episodes at 224² (and 640×480, marked experimental) under `frozen(0)` and `frozen(119)` | 75 RolloutRecords; valid tapes |
| | W2 | Privileged teacher (intersection of 121 navmeshes + clearance cost; `oracle/`) on HA-mini; executor point-goal on SYN-HA | teacher flags = 0 on ≥ 74/75; SYN-HA clean SR |
| | W4-b | **SFT round-trip:** 2k SimpleVLN-format samples from HA-mini teacher rollouts → 100 steps on Qwen3.5-4B with ms-swift or LLaMA-Factory → serve with vLLM 0.18 → outputs parse. If Qwen3.5 tooling fails, retarget to Qwen3-VL-8B-RL and record an ADR | round-trip report |
| | W1-a | SYN-HA scene pack + private human file; **MP3D-day runbook**: download → `unzip -t` → 90 × {glb, navmesh, house, semantic.ply} check → hash list → cache warm order val_unseen 11 → test 18 (if humans are present) → train 61, single writer per scan, separate dirs for non-official radii | runbook reviewed by INT |
| **h48–72** (Tue) | INT | RC0 on HA-mini; nightly regime replay (R0, R26, R119, Rstall, Rbase, Rall) of the 75 tapes; R72 review | R72 report |
| | W4-b / W3 | Instruction clause labelling + route-only paraphrase + 144-way matcher on val_unseen text (GT region scoring waits for MP3D `.house`) | text metrics |
| | All | If MP3D is still absent: escalate (organizers, academic partner) and keep the 7 seats on MP3D-independent work (SFT pipeline, Guard v2 trainer on HA-mini/SYN-HA labels, detector training on HA-mini renders). **Do not scale up** | — |

### 3.4 R72 exit criteria (all must hold to scale beyond 8 sessions)
1. `havln-check-environment` passes on the production SKU, and the forensics doc answers ≥ 8 of the 10 W1 questions with file:line.
2. HA-mini has 120 navmeshes cached. The 20-episode determinism test is identical 3/3 under `frozen(0)`, `frozen(119)` and
   `schedule(S)`. LOOK actions do not move the agent. The wall-slide tape gives the predicted count.
3. The runner turns 75/75 HA-mini episodes into valid tapes (≤ 500 actions, STOP last) with SimpleVLN + Guard v1. Decision latency
   p50/p95 is recorded. The file-open audit of the agent process shows no privileged paths.
4. Replaying those tapes reproduces the recorded final poses to ≤ 1e-4 m under the same regime.
5. F-SYN tests U3/U5/U8/U14/U15 pass in CPU CI in under 10 min.
6. The teacher on HA-mini has zero flagged steps on all 121 navmeshes for ≥ 74/75 episodes; the rest are logged.
7. The SFT round-trip has passed on one backbone: the loss falls, the model reloads in vLLM 0.18, and ≥ 99 % of outputs parse.
8. STOP-only ZIPs (val ×2, test) pass `havln_tools.validate_submission_zip`; the val ZIPs also pass in-container `havln-validate`.
9. The MP3D-day runbook is reviewed and the Phase-2 ingest poller is running.
10. The organizer issue and email are sent (links logged), and the MP3D request log has timestamps.

### 3.5 What must wait for MP3D (do not staff it before)
- val_unseen numbers of any kind;
- CMA reproduction;
- DAgger and RFT at scale;
- Guard v2 and person-detector training at scale;
- ETP-R1 sweeps;
- Track B shadow numbers on val;
- test-split rollouts.

---

## 4. Minimum viable submission: must exist by Tue Nov 10, 23:59 UTC

An MVS is a ZIP that is valid, compliant, produced by a real agent, uploaded (or upload-ready with timestamp evidence), reproducible
and documented. There are two tiers.

### 4.1 MVS-0: independent of MP3D, due Oct 31 (or when Phase 2 opens)
- **Content:** a STOP-only test ZIP: 3,408 episodes, each `["STOP"]`.
- **Validation:** `havln_tools` contract; in-container `havln-validate` once the Phase-2 manifest exists.
- **Upload:** as Phase-2 submission #1.
- **Value:**
  - puts us on the leaderboard;
  - measures the test split's mean start→goal distance (NE = 60/Score − 3);
  - exercises the platform end to end.
- **Expected Score:** ≈ 5–6.

### 4.2 MVS-1: due Nov 10 if MP3D is on disk by Nov 6 (otherwise MP3D-day + 4)

| Component | Requirement |
|---|---|
| Policy | SimpleVLN: the best on DEV of {Qwen3.5-4B-RL, Qwen3.5-9B-RL, Qwen3-VL-8B-RL}, zero-shot, or SFT-r0 only if it wins a paired DEV comparison. Official camera 224² (640×480 only with a written organizer answer). Fixed temperature, per-request seed logged. **K = 1.** |
| Safety | Guard v1 (depth veto + stall memory + escape) on **every primitive, including those inside chunks**. Exact pose-delta contact detection (moved < 0.24998 m) → no-repeat memory + escape. First action is a TURN when the start is within 0.5 m of a perceived obstacle. 0.6 m person keep-out from depth blobs or the W3 detector, if ready (not required). |
| Budget | Hard STOP at ≤ 490 actions; never end without STOP. |
| Environment | Official image; virtual human clock `schedule(S_fast)`; agent isolated from navmesh, human files, MP3D annotations and GT. |
| Outputs | Full test inference (3,408 episodes); `validate_submission_zip` PASS; in-container `havln-validate` PASS; a 300-episode replay reproduces the recorded final poses (determinism only, no test collision counting); compliance manifest (`inputs_used = rgb, depth, pose, instruction`); ledger entry with git SHA, data fingerprint and sha256. |
| Evidence | DEV (1,413 episodes) SR / NE / CR / TCR / Score with denominators under R0 and R119; LOCKBOX untouched. |
| Acceptance bar | DEV clean SR ≥ 0.18 (CMA val_unseen: 0.129) and contact episodes ≤ 30 %. Expected Score 19–28 by the official formula: SR .20 / NE 6 / CR .25 / TCR .5 → 20.8; SR .28 / NE 5 / CR .15 / TCR .3 → 28.4. Published HA-VLN-CE SOTA ≈ 22–23. |
| Delivery | Uploaded by Nov 10. If CodaBench is down: the ZIP sha256 and a download link emailed to the organizers, logged. |
| Report stub | 2 pages: method, inputs used, DEV numbers, compliance statement, licences. |

- **Dependencies (only four):**
  - W1-b runner + clock;
  - W4-a client + serving;
  - W2 Guard v1 + contact detector;
  - W6 packaging.
- **Explicitly not dependencies:** W3, W5, ETP-R1, Guard v2, DAgger/RFT, Track B, frontier APIs, the Phase-1 calibration.
- **If MP3D is absent on Nov 10:** only MVS-0 exists. Hold a go/no-go review: no compliant alternative exists without meshes. Continue
  only if a licence route is in motion.

### 4.3 Upload policy after the MVS
- Upload the best-known ZIP at least every 5 days.
- At most 3 uploads per UTC day, none in the last 2 h of a UTC day.
- Never cancel a stuck job; escalate it with its id.
- Final upload Nov 25.

---

## 5. Brief-by-brief gaps, with proposed text

### 5.0 Ownership matrix (proposed; resolves the holes listed in §0.10)

| Item | Owner today | Proposed owner | Interface |
|---|---|---|---|
| Closed-loop runner + agent sandbox | none (C5 K1) | **W1-b** | EpisodeInput/1 → Observation/1 → action; RolloutRecord/1 |
| Agent composition, release candidates | none | **INT** (new brief) | `agent/navstack`, RC tags |
| Guard v1/v2 (step veto, escape, keep-out) | W4 (Guard v2) and W2 | **W2** | PrimitiveProposal/1 in, primitives out |
| Waypoint executor + STOP placement | W2 (and W4 "policies propose STOP") | **W2** issues STOP; policies request it | SubgoalProposal/1 |
| Privileged teacher planner (`oracle/teacher`) | W2 harness, W4 data, W7 swept-volume planner | **W2** library; W4 and W7 consume it | PlanRequest/1 → PlanResult/1 (oracle) |
| Render service + training-data writer | W1 (render) and W4 (data) | W1-c renders; **W4** builds datasets | render API (C1 §12) |
| Person detector model | W3 and W4 (Guard v2) | **W3** model; W2 keep-out logic | Percept/1 `people[]` |
| vLLM serving pool | none | **W1-c** | `configs/serving.yaml` |
| Stop verifier (T1d) | W5 / W3 | **W5** | stop request → verdict |
| Human-timing regime registry | W1 (6), W6 (4), W2/C6 (9) | **INT**, from C6's nine | `configs/regimes.yaml` |
| Val splits / lockbox | README (unnamed); `data/val_unseen_splits.json`; C5 HOLDOUT-v1 | **W6** custodian of `data/val_unseen_splits.json` | file + seed |
| Organizer issue + private email | W0 ("five questions from §7") | **W0** posts 03 items 1–10 + new 11–13 + the B12 paragraph | — |
| Phase-2 bundle ingest | not in any brief (C1 B9) | **W1-a** | ingest report |
| STOP-only anchors | W0 / W6 | **W6** builds; the human uploads | ZIP + sha256 |
| Technical report | W7 | **W7** + INT | — |

### 5.1 `briefs/README.md`
**Gaps:**
- Rule 1's `grep` check is weak (C5 K3).
- Rule 3's lockbox is unnamed and conflicts with C5 HOLDOUT-v1.
- Test-side assets in `data/` are readable by every agent (C5 K7).
- There is no cache-directory rule, no contracts reference, no regime registry, no MP3D licence rule, and no "no exp_id, no claim" rule.

**Add:**
```
5. Splits are fixed by data/val_unseen_splits.json (seed 20261024): DEV = 8 scans / 1,413 eps; LOCKBOX = 8194nk5LbLH, EU6Fwq7SyZv,
   QUCTc6BB5sX (426 eps; W6 only; ≤ 4 looks); QUICK 306; SMOKE 60. C5's HOLDOUT-v1 is superseded.
6. Test-side files (test_episode_index.json, test_trajectory_table.json, mp3d_test_scan_room_labels.json, collision_num_test.json,
   R2R_test.json, HA-1.0 test humans) live in quarantine/ and are not mounted in agent containers. Only W6 reads test episode ids.
7. Inference code runs in the runner's agent process, which has no navmesh, human file, MP3D annotation or GT mounted. CI enforces an
   AST import firewall plus a file-open audit; this replaces the grep.
8. Interfaces are the versioned JSON Schemas in contracts/ (EpisodeInput/1, Observation/1, PrimitiveProposal/1, SubgoalProposal/1,
   RolloutRecord/1, ExperimentRecord/1; PlanRequest/1 is oracle-only). Changes need INT + human approval and land at 12:00 UTC.
9. Human-timing regimes are defined once in configs/regimes.yaml (R0, R26, R119, Rstep, Rfast, Rslow, Rstall, Rbase, Rall; C6).
   Refer to them by name.
10. Only W1's single-writer warm-up writes the official recompute_navmesh/ directory. Every other radius/union/inflated cache uses
    navmesh_cache/<variant>/ (the official cache is keyed only by scan + frame).
11. MP3D data stays on licensed infrastructure. No unofficial mirrors. No MP3D renders to third-party APIs without the licence
    holder's written OK.
12. No exp_id, no claim: every number in a PR, report or digest cites an ExperimentRecord.
```

### 5.2 W0 — Ops and organizer liaison
**Gaps:**
- It assumes affiliated signers exist and has no decision rule if they don't.
- It posts "five questions from §7", but §7 has 7 and 03 has 10, and none of the ready text covers the bundle, the close time or MP3D.
- The B12 disclosure is unassigned.
- There is no deputy for uploads and no dated escalation triggers.

**Replace the second and third task bullets with:**
```
- Within 4 h: MP3D licence triage. Answer and log: (a) does any member hold, or belong to an institution with, an MP3D licence whose
  terms cover this work and the compute it will run on? (b) which ≥ 3 academically affiliated members (different institutions if
  possible) sign fresh ToU requests today? (c) if (a) and (b) are both empty: contact an academic collaborator to join the team and
  host the MP3D-dependent compute on licensed infrastructure; decide by Oct 26 12:00 UTC. Never use unofficial mirrors or the public
  download_mp.py URLs.
- Post the GitHub issue in 03-organizer-questions.md with items 11–13 appended, mirror it on Discord, and send the private email with
  the B12 paragraph appended. Log all links.
  11. Phase-2 bundle: will it include human_motion.json entries for the 18 test scans (local rendering needs them; without them local
      runs show no humans), the test episode file with trajectory_id, and is collision_num_test.json (public in UWMILab/HA-VLN) the
      scoring baseline? Which channel (HF revision, GitHub release, CodaBench), and will it be mirrored off CodaBench while it is down?
  12. Exact Phase-2 open/close timestamps in UTC, the daily-limit reset, the grader's execution time limit, and the fallback channel
      if CodaBench is unreachable near the deadline.
  13. Is there an expedited Matterport3D access route for registered teams (niessner/Matterport #65 and #74 report the mailbox
      unanswered for weeks)?
  B12 paragraph for the email: "The original Matterport3DSimulator repository (peteanderson80/Matterport3DSimulator,
  web/app/sample_room_paths.json, committed 2018) contains full start→goal paths for R2R path_ids 0–1999, i.e. 366 of the 1,391 R2R
  test paths; we estimate this covers 879 of the 3,408 Phase-2 episodes. We do not use it and block it by hash; you may want to
  account for it."
- Name a deputy who can upload and answer the organizers when the lead is unavailable. Upload window 08:00–14:00 UTC.
- Treat the Phase-2 close as Nov 30 15:59 UTC until the organizers say otherwise; the final upload is Nov 25.
Triggers: no MP3D by Oct 31 → daily escalation + academic-partner path; Nov 3 → T-cut-1 (stop ETP-R1/Track B); Nov 10 → MVS review.
Report adds: licence-triage outcome; request timestamps; bundle inventory incl. "18 test scans present in human_motion.json: yes/no".
```

### 5.3 W1 — Data, image forensics, replay farm
**Gaps:**
- Five or more seams sit in one brief: forensics, two digests, caches, CMA reproduction, FrameScheduler, replay farm, render/plan
  service, and now the runner.
- The **closed-loop runner and sandbox are unowned**.
- There is no day-1 HA-mini or SYN-HA fixture and no SKU/EGL matrix.
- There is no Phase-2 ingest, and the vLLM pool is unassigned.
- The cache-key collision is not addressed.
- Its 6 timing modes differ from C6's 9 regimes.

**Split into W1-a (image and data), W1-b (env, clock, runner) and W1-c (farm, render, serving). Add:**
```
Day 1 (no MP3D):
- SKU/EGL matrix: on every GPU type we own, inside the image, run havln-check-environment, render 100 RGB-D frames and one
  recompute_navmesh on 17DRP5sb8fy. Containers need NVIDIA_DRIVER_CAPABILITIES incl. graphics. Blackwell may fail (HA-VLN #20):
  keep an Ampere/Hopper pool for Habitat.
- HA-mini: mp3d_example.zip (17DRP5sb8fy) + its 10 humans + 75 HA-R2R train episodes; warm 120 navmeshes; record seconds and MB per
  frame and extrapolate to 90 scans.
- SYN-HA: habitat-test-scenes (apartment_1, van-gogh-room, skokloster-castle) laid out as <name>/<name>.glb with a PRIVATE
  human-annotation file placing HAPS humans; point-goal episodes for W2. Never mounted in the scorer's data root.
Closed-loop runner (W1-b; contract Observation/1):
- The agent runs in a separate process/container with no navmesh, human file, MP3D annotation or GT mounted, over a socket.
- Observation/1 = {rgb uint8 224×224×3; depth float32 256×256 as configured (verify normalisation and range in forensics); gps (x, z)
  and compass yaw in the episode-start frame; step_index; actions_left; instruction; episode_id}. Never expose frame_id, the collided
  flag, distance_to_goal or other simulator state.
- Human clock from configs/regimes.yaml; rollouts default to schedule(S_fast).
- Every rollout writes RolloutRecord/1 with inputs_used, a file-open audit hash, and model ids + seeds.
Phase-2 ingest (W1-a): from Oct 30 00:00 UTC, poll the HF dataset, the toolkit/HA-VLN repos and Discord every 15 min. On release:
sha256; diff human_motion.json and ALARM if any of the 18 test scans is missing; havln-check-data; warm the 2,160 test navmeshes
(one writer per scan).
Serving (W1-c): vLLM 0.18 on GPUs separate from the Habitat processes (or gpu_memory_utilization ≤ 0.5 if shared), health checks,
per-request seeds, endpoint list in configs/serving.yaml.
Cache rule: only the warm-up job writes the official recompute_navmesh/ directory; teacher/union/inflated caches use
navmesh_cache/<variant>/.
DoD adds: R72 exit criteria 1–4 and 8–9 (V3 review §3.4).
```

### 5.4 W2 — Safety executor
**Gaps:**
- The DoD is unrealistic for its date: val_unseen clean SR ≥ 0.90 → 0.94 under 9 regimes by Oct 28/29 needs MP3D and the scheduler.
- It is written for **waypoint following**, but the primary policy (SimpleVLN) emits **primitive chunks**, so a guard mode is needed.
- Guard v2 is listed under W4.
- The teacher has three owners.
- There is no schema for the goal belief.
- The teacher DoD has no clause for infeasible cases (C7 row 19).
- The STOP authority conflicts with W4.

**Replace the "Goal" line and the DoD with:**
```
Scope: package safety/ with two modes and one oracle library.
- Guard mode (the MVS default): input PrimitiveProposal/1 (a policy chunk of ≤ 6 primitives). Veto any MOVE_FORWARD that fails the
  hard clearance check. On a veto, escape (smallest clear turn ≤ 90°, then a replan on the own map) and return control. Guard v1 =
  vln-safe stall-mem1 port (MVS). Guard v2 = own occupancy map + learned step-collision predictor + person keep-out (owned here,
  not by W4).
- Waypoint mode: input SubgoalProposal/1 (waypoint | heading | frontier | look_around | stop, with a goal belief as [{xyz, p}]);
  emits primitives; chooses the stop point maximising P(within 3 m). Only the executor issues STOP; policies request it.
- oracle/teacher (privileged; single owner = W2): a clearance planner on the intersection of the 121 navmeshes, consumed by W4
  (expert data) and W7 (analysis).
DoD (D = MP3D-day):
- By Oct 29 (no MP3D): F-SYN U3/U5/U8/U14/U15 green; HA-mini teacher with zero flags on all 121 navmeshes for ≥ 74/75 episodes;
  SYN-HA point-goal clean SR ≥ 0.90.
- D+5: compliant executor given the GT goal point on val_unseen DEV: clean SR ≥ 0.90, contact episodes ≤ 2 % under R0/R119/Rstall.
- D+12: clean SR ≥ 0.94 and contact episodes ≤ 1 % under all nine regimes.
- Teacher: zero flags on all 121 navmeshes for ≥ 99.5 % of train episodes. The rest emit the minimum-risk plan, are logged, and are
  excluded from SFT data.
```

### 5.5 W3 — Perception and grounding
**Gaps:**
- Target (b) needs renders, i.e. MP3D.
- **No consumer of `program.json` exists in the SimpleVLN-first plan**, because SimpleVLN reads the raw instruction.
- The person detector is shared with Guard v2's keep-out.
- Visual activity recognition is unreliable (B11: 30–43 % top-1), yet (b) is phrased around it.
- There are no dates.

**Replace "Goal" through "Evaluation" with:**
```
Priorities, in order:
(1) Person detector/segmenter for the forward camera, trained on exact masks rendered with set_object_semantic_id on TRAIN scans
    (HA-mini first). Consumed by W2's keep-out. DoD D+7: person recall ≥ 0.95 within 5 m and precision ≥ 0.90 on DEV renders.
(2) Clause labelling + route-only paraphrase (text only; start now). Consumed as an optional second instruction by W4 and by W5's
    stop verifier.
(3) program.json, for waypoint mode / System 2 only.
If no consumer has integrated an output by Nov 13, stop work on it.
Target (b) means "a mentioned human (start/during/end) is matched to a detected person at that stage within 3 m along the path".
It does not mean activity recognition, which stays a tie-breaker.
```

### 5.6 W4 — Closed-loop policies
**Gaps:**
- Three inconsistent SR schedules: §5 (≥ .40 Nov 9, ≥ .46 Nov 16, ≥ .50 at freeze), §6 (.28–.36 Nov 2–6, .40–.47 Nov 9–13) and the
  brief (≥ .30 Nov 3, ≥ .45 Nov 13).
- "Habitat 0.3.3 eval → build a side-environment or bridge" is left undecided.
- **No port-parity test**, and the camera-resolution decision is open.
- ETP-R1 runs in parallel.
- Guard v2 is listed here.
- The SFT-toolchain risk for Qwen3.5 is not front-loaded.
- The SimpleVLN weight licence is unchecked.

**Replace the second paragraph and the milestones with:**
```
Decision: do not run Habitat 0.3.3. Port SimpleVLN's agent logic (eval.py: system prompt, 8 uniformly sampled history frames + the
current frame, temperature 0.3 / top-p 0.95, chunk parser) into agent/simplevln/ as a pure-Python client (py3.8, requests) for the
W1 runner. Weights are served by the W1 vLLM pool.
Port parity (D+3; blocks any HA claim): human-free R2R-CE val_unseen using SimpleVLN's bundled annotations, in our 0.1.7 runner at
640×480 HFOV 90, on a 300-episode stratified subset. SR must be within 6 pp of the published value for that checkpoint. Then repeat
at 224² (the camera gap), then with HA-R2R text, then with humans, and report the 4-step ladder.
Order: SimpleVLN zero-shot (the MVS) → SFT-r0 on W2 teacher data rendered at 224² with humans (train scans only) → DAgger r1–r2 →
RFT if time allows. ETP-R1 starts only after the MVS ships, and only if K>1 is permitted or SimpleVLN DEV clean SR is < 0.30 after
SFT-r0.
De-risk now (no MP3D): SFT round-trip on HA-mini samples with ms-swift or LLaMA-Factory for Qwen3.5-4B. If unsupported, retarget to
Qwen3-VL-8B-RL (an ADR). Check the HF model-card licences of the SimpleVLN weights.
Guard v2 moves to W2. Data: W1-c renders, W2 teacher, W4 builds datasets.
Milestones (single source; D = MP3D-day; the calendar dates assume D = Oct 28):
D+3 zero-shot DEV clean SR reported (expect 0.15–0.30); Nov 10 MVS; D+10 SFT-r0 DEV clean SR ≥ 0.35; Nov 20 freeze: DEV clean
SR ≥ 0.45 (stretch 0.50).
```

### 5.7 W5 — Test-time compute and selection
**Gaps:**
- The brief is organized around the gray K-rollout selection.
- It still suggests "the public R2R instruction when matched by start pose + text", which strategy §2 and issue Q7 prohibit.
- The "+5 SR" DoD relies on gray levers.
- The allowed levers (C9 T1a–T1d) are not the default.

**Replace the body with:**
```
Default deliverables (compliant, single run): T1a per-decision K-sample vote; T1c STOP supermajority; T1d rotation-based stop
verifier (≤ 2 sweeps per episode; turns counted). DoD: +2–4 DEV clean SR, paired against the same policy without them, with
action-budget p99 ≤ 480.
Behind a flag, OFF until a written organizer answer: K full rollouts with resets + selection; sibling-instruction sharing.
Delete: any use of the original R2R test instructions (prohibited).
Interfaces: consumes RolloutRecord/1; the stop verifier answers W2's STOP requests.
```

### 5.8 W6 — Verification and submission
**Gaps:**
- The test count is stale (13; the suite now has 20).
- In-container `havln-validate` on *test* needs the Phase-2 manifest.
- "4 regimes" conflicts with C6's 9.
- **"TCR 0 on all regimes" for test ZIPs (strategy §5) contradicts the issue's Q8 promise** not to use test local-replay outcomes to
  choose between variants.
- "Aggregate metrics only from GT-based replay" is impossible on test, which has no GT.
- There is no STOP-only test task and no evidence protocol for an outage.

**Replace "Pipeline" and "Policies" with:**
```
Selection uses val DEV (and LOCKBOX at gates) only. A test ZIP is released if:
(1) the havln_tools contract passes;
(2) in-container havln-validate passes, once the Phase-2 manifest exists;
(3) local replay of a 300-episode sample reproduces the recorded final poses (determinism only: no collision counts or success
    computed on test);
(4) the producing config passed the regime gate on DEV (R0, R26, R119, Rstall, Rbase, Rall; flips ≤ 0.5 %).
Never edit, select or regenerate test tapes from test replay outcomes.
Pre-build now: STOP-only ZIPs for val_seen, val_unseen and test (ids 1..3408).
Outage protocol: if CodaBench is unreachable, email the organizers the ZIP sha256 + a download link before the deadline; log it.
Final upload Nov 25; Nov 26–30 only for re-uploading the same ZIP after a platform failure.
Tests: the tests/ suite (20 passing) + nightly container tests.
```

### 5.9 W7 — Track B shadow, oracle analysis, report
**Gaps:**
- The Track B planner is large for a shadow track (C5 K19).
- It uses test-scan assets, which must stay in quarantine.
- The report draft is due before the final numbers exist.
- The oracle analysis needs Track A rollouts (D+3).

**Add:**
```
Time-box: 1 agent until an organizer answer permits Track B.
Priorities: (1) oracle failure taxonomy of Track A DEV failures, weekly from D+3; (2) report: stub on Nov 10 (MVS), full draft
Nov 25, final numbers inserted after the Nov 25 upload; (3) Track B on val_unseen only. No test-scan assets outside quarantine/.
```

### 5.10 New brief: INT — Integrator and release (missing)
```
INT — Integrator & release (1 agent + the human)
Owns: contracts/, CI (CPU < 10 min on every PR; GPU nightly), the merge queue, CODEOWNERS, release candidates (agent/navstack),
configs/regimes.yaml, the splits pointer, the ADR log, generated RESULTS.md and STATUS.md.
Daily RC at 04:00 UTC on SMOKE + QUICK; promotes to W6 only with an ExperimentRecord.
Scaling rule: ≤ 8 concurrent coding sessions until R72 passes and MP3D is on disk; ≤ 14 after that; a new seat needs a named
contract and a test it must turn green.
```

---

## 6. Facts vs inferences, and sources

### 6.1 Verified in this review (file:line)
- **SimpleVLN environment.** The evaluator is Python 3.10 with Habitat 0.3.3; vLLM 0.18 runs in a separate env. Sources:
  `ext/sota/SimpleVLN/eval/README.md` L12–37; `eval/requirements.txt`; `eval/requirements-vllm.txt`.
- **SimpleVLN camera.** 640×480 at HFOV 90; max 400 steps; temperature 0.3, top-p 0.95. Sources: `eval/config/vln_r2r.yaml`;
  `eval/README.md` L225–244.
- **SimpleVLN headline metric.** It is `sucs_all`, the mean over trials; `pass@k` is reported separately. Sources: `eval/README.md`
  L257–269; `eval/vln/eval.py` L572–660. The launcher defaults to `PASS_K=4` (`eval/scripts/eval.sh`); the README example uses
  `PASS_K=1`.
- **SimpleVLN's Habitat 0.3.3 coupling** is limited to `Env`, the config and the measures (`eval.py` L1–30, L450–493).
- **vln-safe.** The harness is py3.6 with habitat 0.1.7, and VLAs run as subprocess workers (vln-safe `README.md`, "Setup"). The
  ETP-R1 worker env is Python 3.6.13 with torch 1.10.2+cu113 (`environment/worker_etpnav.yml` L95, L216).
- **Missing scan → no humans.** `ext/HA-VLN/HASimulator/environments.py` L174–175 (`human_motion_data.get(scan, {})`).
- **HA task camera.** RGB 224², depth 256², HFOV 90 (`HAVLNCE_R2R_task.yaml` L11–24).
- **Public non-MP3D scenes.** `ext/habitat-sim-0.1.7/README.md` L195; `.circleci/config.yml` L305, L325.
- **Organizer drafts.** `03-organizer-questions.md`: the issue has items 1–10, with no bundle-content, close-time or MP3D item. The
  string `sample_room_paths` occurs 0 times in 03 and in every brief, and once in `01-strategy.md`.
- **Lockbox conflict.** `data/val_unseen_splits.json` has lockbox {8194nk5LbLH, EU6Fwq7SyZv, QUCTc6BB5sX} = 426 episodes. C5
  HOLDOUT-v1 is {EU6Fwq7SyZv, TbHJrupSAjP, X7HyMhZNoso} = 537 episodes (`findings/C5…md` §0.5).
- **Test counts.** `python3 -m unittest discover -s tests` runs 20 tests, all OK. The strategy header and W6 say 13; strategy §11
  says 15.
- **Score points** in §0, §1 and §4 were computed with the official formula
  (`Score = 100 · Nav · (0.7 + 0.3 · Social)`).

### 6.2 Inferences (confidence)
| Inference | Confidence |
|---|---|
| MP3D scenario probabilities and the probability-weighted Score of 34 | low |
| CodaBench outage probabilities | low |
| P(test humans missing) = 0.25 | low–medium |
| Zero-shot SimpleVLN at 224² SR 0.15–0.30 | low |
| Milestone slip probabilities | low–medium |
| Serial-chain durations | medium |
| Compute and volume sizing | medium |
| torch 1.10.2+cu113 on Hopper/Blackwell relies on PTX JIT | low–medium |
| The habitat-test-scenes layout trick for SYN-HA works unchanged in the image | medium; verify on day 1 |

### 6.3 Contradictions
- **With CONTEXT.md:** none.
- **Internal to the package:** the W4 SR schedules, the regime sets, the lockbox, the test counts, and W6's test gate vs issue Q8 (see
  §0.9 and §5).

### 6.4 Sources
- Repo: `competitions/roboworld2026-track2/{00-competition-facts.md, 01-strategy.md, 02-research-digest.md, 03-organizer-questions.md,
  briefs/*.md, data/val_unseen_splits.json, havln_tools/, tests/}`.
- research/ (same text as findings/):
  - C1-infra-and-replay-farm.md: §0, §1, §3.4, §8, §9.
  - C2-timeline-critical-path-and-risk-register.md: §0, §2, §3, §6–§9.
  - C9-learned-closed-loop-fallback-track.md: §1, §2, §3, §7, §8, §9, §15.
  - A11-data-acquisition-logistics-mp3d-hf.md: §0, §1.5, §1.6, §3, §5.
  - A12-codabench-platform-mechanics.md: §0, §1, §2, §5.
  - C6-experiment-design-and-val-protocol.md: generation/replay regimes, L301–322, and point 5 at L549.
  - C10-testing-and-benchmark-plan.md: F12 and HA-mini, L33, L65, L178, L375.
- findings/:
  - C5-multi-agent-organization-and-handoff.md: §0, §1.
- Clones under `scratchpad/ext/`: `sota/SimpleVLN`, `sota/vln-safe`, `HA-VLN/HASimulator`, `habitat-sim-0.1.7`.
