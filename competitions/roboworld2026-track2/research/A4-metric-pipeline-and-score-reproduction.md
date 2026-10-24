# A4 — Metric pipeline and score reproduction (RoboWorld 2026 Track 2, HA-VLN)

Topic id: `A4-metric-pipeline-and-score-reproduction` · Date: 2026-10-24 · Regime: the metric is the same for the
compliant (egocentric closed-loop) and the privileged/offline regime. Everything here is about how a submitted action
sequence is turned into a Score.

BASE = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext`
Work scripts: `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a4work/`
(`score.py`, `solve.py`, `solve2.py`, `solve3.py`, `sens.py`, `cn_map.py`, `cn_hyp.py`, `havln_score_ref.py`)

---

## 0. Summary: the five findings that matter most for decisions

1. **CR is divided by βL, the human-influenced episode count, and its numerator counts ALL episodes:**
   `CR = Σ_{i=1..L} min(e_i,1) / (βL)`, with βL = L − H, H = 96 / 246 / 549 (val_seen / val_unseen / test), so βL = 682 / 1,593 / 2,859.
   Two kinds of evidence support this. (a) The organizers' first toolkit README states it explicitly: track2 commit 2daf3dd, README L336-350, plus the βL table at L96-101. (b) An exact integer-arithmetic reconstruction of all four published full-precision CMA Scores is consistent **only** with SR/L and CR/(βL), on 4 of 4 reference points. The plain all-episode mean C/L fails on 4 of 4, and C/H fails on 4 of 4. **[high]**
   Consequence: CR can exceed 1. Its maximum is 1/β = 1.141 / 1.154 / **1.192 (test)**, so Social can be negative. The social multiplier `0.70+0.30·Social` ranges from 0.657 to 1.000.
2. **The published Scores are reproduced exactly from integer counts.** Two corrections to what the brief assumed:
   - Rounded inputs give 16.513612 / 12.954102. The exact integers give **16.5094500 / 12.9453870**.
   - The residual (−0.00416 / −0.00871) is entirely rounding. About 78–89% of it comes from SR (true SR = 140/778 = 0.179949 and 237/1839 = 0.128874). The rest comes from CR (425/682, 1090/1593) and NE (6.223225 / 6.387021).
   - Recovered CMA facts:
     - Only **54.6% (val_seen) / 59.3% (val_unseen)** of episodes have ≥1 adjusted collision.
     - The colliding episodes average **25.1 / 29.6 collision steps**.
     - 41–45% of CMA episodes have no adjusted collision at all. CONTEXT's "~15 collisions per episode" is a mean over a bimodal distribution. **[high]**
3. **With zero collisions, Score = 80·SR + 60/(3+NE).**
   - In absolute terms, a collision-free success is worth 80/L points (+0.0235 on test).
   - A first collision in an otherwise-successful episode costs about **1.25–1.33 successes** (−0.029 to −0.031 on test). Most of that loss is the SR it removes; CR and TCR add the rest.
   - A first collision in an already-failed episode costs only −0.006 to −0.008.
   - Lowering mean NE by 1 m is worth +1.7 to +3.75 points (+2.4 at NE = 2), about 3 pp of SR.
   - For a single episode, one success is worth about 33 m of final-distance improvement. The best stopping rule is therefore "maximise P(d<3 m)". NE only breaks ties.
   - **The Score has no path-length, SPL or step-count term.** Exploration, look-arounds and long routes cost nothing except collision risk and the 500-action budget. TURN and LOOK actions can never collide (A2). **[high]**
4. **The official scorer ships inside the public image.**
   - The early toolkit README documents an official local replay CLI, `havln-score-phase1 --submission … --output-dir … --gpu-ids …` (2daf3dd README L246, L296), and states "The public-test and final phases use the same task and scoring algorithm" (L256).
   - The exporter imports `havln_scoring` from `/opt/havln-challenge/scoring/` and the CodaBench reference manifest from `/opt/havln-challenge/codabench/phase1/reference/` (export_cma_submission.py L74, L188-189, L219).
   - Pulling the image and reading `/opt/havln-challenge` removes all remaining metric uncertainty: the Euclidean-vs-geodesic distance, measure list, 1 m human filter, no-STOP handling and test collision_num. I could not fetch the blobs: ghcr.io blob downloads redirect to pkg-containers.githubusercontent.com, which this sandbox blocks. **Doing this is P0 for the team.** **[high that the code is there; not inspected]**
   - Local trainer CR (base_il_trainer.py L473-481) is the all-episode mean C/L. **Official CR = trainer CR × L/(βL)**, i.e. ×1.141 / ×1.154 / ×1.192.
5. **collision_num is a per-trajectory "free collision" allowance that is public for test, but its generation method is not public.**
   - It is constant across all 259 / 613 / 1,136 val_seen / val_unseen / test trajectories (exactly 3 episodes each, except val_seen's single 4-instruction trajectory).
   - It is non-zero for 20 / 53 / 79 trajectories, with values 1–4.
   - It was added on 2025-02-21 (HA-VLN commit 5a58635), before human_motion.json was published (2025-02-28), and has never been modified.
   - It is not reproducible from the current human_motion.json. Neither viewpoint membership nor proximity to the reference path (0.3–2 m) matches better than 233/259.
   - The HA-VLN 1.0 analogue subtracted the number of humans located at the Beginning/End of the GT path, with no clipping (HA3D_simulator tasks/HA/eval.py L55-73, L96-98). That does not match the CE file either.
   - For a zero-collision agent it is irrelevant. **[high on structure; low on generation method]**

---

## 1. Verified pipeline, from simulator to Score

### 1.1 Per-step and per-episode measures (Habitat-Lab 0.1.7 plus HA-VLN overrides)

| Quantity | Code | Semantics |
|---|---|---|
| `collisions.count` | habitat-lab-0.1.7 `habitat/tasks/nav/nav.py` L653-672 (`Collisions`) | +1 for each `env.step()` in which `sim.previous_step_collided` is true. A2 covers the details: only sliding or blocked MOVE_FORWARD steps count, and walls, furniture and human meshes all count. |
| `distance_to_goal` | `HA-VLN/HASimulator/measures.py` L100-155 | Overrides habitat's geodesic DistanceToGoal (nav.py L930-976 uses `geodesic_distance`). The override is a **3-D Euclidean** `np.linalg.norm(goal − agent)` (L17-20, L140-144). It is registered under the same name and wins because the registry dict is overwritten (`habitat/core/registry.py` L57-59) when `habitat_extensions/measures.py` L28 runs `from HASimulator.measures import *`. |
| `success` | nav.py L500-539 | 1.0 iff `task.is_stop_called` **and** `distance_to_goal < SUCCESS_DISTANCE` (strict `<`, 3.0 m: `HASimulator/config/HAVLNCE_task.yaml` L27, L47-48). A 500-action sequence without STOP is ended by `_past_limit` (`habitat/core/env.py` L187-198, L229-233) **with success = 0**. |
| episode length | HAVLNCE_task.yaml L2 `MAX_EPISODE_STEPS: 500`; env.py L229-233 | Exactly 500 actions are allowed. A STOP as the 500th action still counts as STOP. |

### 1.2 Adjustment (`HASimulator/metric.py`, identical in havln2)

```python
# HA-VLN/HASimulator/metric.py
L10   self.num_collisions = json.load(open(f'Data/HA-R2R-tools/collision_num_{split}.json'))
L12   self.beta = {'train':1-1615/10819, 'val_seen':1-96/778, 'val_unseen':1-246/1839, 'test':1-549/3408}
L15   metric['TCR'] = max(0, metric['collisions']['count'] - self.num_collisions[str(ep_id)])
L16   metric['CR']  = min(metric['TCR'], 1)
L17   metric['SR']  = metric['success'] * int(metric['TCR']==0)
```
`beta` is defined but **never used** anywhere in the public code. The β division happens only in the organizer scorer.

### 1.3 Public trainer aggregation (`agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py`)
- L267: `new_metric = Calculate_Metric(split=split)`.
- L389-394: when an env reports `done`, `stats_episodes[ep_id] = infos[i]` and then `new_metric(stats_episodes[ep_id], ep_id)` mutates the info dict in place, adding TCR, CR and SR.
- L458-481: every key is averaged over `num_episodes = len(stats_episodes)`. `collisions` is averaged via `['count']`. **CR is therefore C/L in the trainer**, not C/(βL).
- L483-497: the averages are saved and logged (`stats_ckpt_{i}_{split}.json`).

### 1.4 Official aggregation (organizer scorer, `havln_scoring`, not public)
From the first toolkit README (BASE/track2-jostar, `git show 2daf3dd:README.md`, L336-350; identical in havln-challenge history from 8e36fa7 on 2026-09-28 until e83e355 on 2026-10-08):

> Let L be the number of episodes, s_i the navigation-success indicator, d_i the final goal distance, and e_i the adjusted
> human-collision count. The released human-influenced episode count is βL:
> SR = (1/L) Σ s_i·1[e_i=0], NE = (1/L) Σ d_i, CR = Σ_{i=1}^{L} min(e_i,1) / (βL), TCR = (1/L) Σ e_i.
> "In particular, CR divides by the released human-influenced episode count βL, while SR, NE, and TCR divide by all L episodes."

The same formula appears in `havln2/HASimulator/README.md` L102-103 (`CR = 1/(βN) Σ_{i=1}^N min(e_i,1)`). The βL table is in 2daf3dd README L96-101 (val_seen 682, val_unseen 1,593; train and test shown as "—"). The current README (`track2/README.md` L196) shortened this to "Collision-episode rate over human-influenced episodes". The website `roboworld2026.github.io/track2.html` L134 says "Fraction of human-influenced episodes with at least one collision". havln-challenge `index.html` L206 says "normalized by the human-influenced episode count".

### 1.5 Composite (track2/README.md L199-213; website track2.html L136-185)
```
Navigation = 0.80·SR + 0.20·3/(3+NE)
Social     = 0.75·(1−CR) + 0.25/(1+TCR)
Score      = 100·Navigation·(0.70 + 0.30·Social)
```
Full precision (float64). Ties are broken by higher SR, then lower NE, lower CR, lower TCR, then earlier submission. Phase 1 ranks by val_unseen Score. Phase 2 (test) alone decides the awards.

### 1.6 Constants

| split | L | H (not influenced) | βL | β | 1/β = max CR | non-zero collision_num episodes (trajectories) |
|---|---|---|---|---|---|---|
| train | 10,819 | 1,615 | 9,204 | 0.85073 | 1.1755 | 824 eps |
| val_seen | 778 | 96 | 682 | 0.87661 | 1.1408 | 60 (20) |
| val_unseen | 1,839 | 246 | 1,593 | 0.86623 | 1.1544 | 159 (53) |
| test | 3,408 | 549 | 2,859 | 0.83891 | 1.1920 | 237 (79) |

---

## 2. Reproducing the CMA Scores

### 2.1 Naive recomputation from the displayed (rounded) components (`a4work/score.py`)

| split | SR | NE | CR | TCR | Score from rounded values | Published | Residual | Range if every component is perturbed by ±0.0005 |
|---|---|---|---|---|---|---|---|---|
| val_seen | 0.180 | 6.223 | 0.623 | 13.726 | 16.513612 | 16.509450 | +0.004162 | [16.479386, 16.547847] contains the published value |
| val_unseen | 0.129 | 6.387 | 0.684 | 17.536 | 12.954102 | 12.945387 | +0.008715 | [12.920955, 12.987258] contains the published value |

### 2.2 Exact reconstruction (`a4work/solve3.py`)
- SR = k/L and TCR = m/L must have integer numerators.
- CR = C/D, where D is one of {L, βL, H}.
- Search all integers consistent with the displayed 3-decimal values, then solve for the NE that reproduces the 6-decimal Score.
- Check whether that NE rounds to the displayed NE.

| reference point | SR | CR | TCR | NE (pinned by Score) | consistent families |
|---|---|---|---|---|---|
| toolkit replay val_seen (Score 16.509450) | 140/778 | 425/682 | 10679/778 | 6.2232240–6.2232258 | **only SR/L, CR/(βL)** |
| toolkit replay val_unseen (12.945387) | 237/1839 | 1090/1593 | 32248 or 32249 /1839 | 6.387018–6.387024 | **only SR/L, CR/(βL)** |
| organizer re-eval val_seen (15.469585; HA-VLN README 0cb555a, havln-challenge before 5ad4380) | 128/778 | 435/682 | 10325/778 | 6.229562–6.229563 | **only SR/L, CR/(βL)** |
| organizer re-eval val_unseen (11.944822) | 210/1839 | 1098/1593 | 41105 or 41106 /1839 | 6.501767–6.501771 | **only SR/L, CR/(βL)** |

Families tested on all four points: SR/{L, βL} × CR/{L, βL, H} × TCR/{L, βL}. Results:
- SR/L with CR/(βL) is consistent on 4/4 points.
- SR/L with CR/L (the all-episode rate) is consistent on 0/4.
- CR/H (the 96/246 interpretation) has no integer solution at all: k/96 and k/246 cannot round to 0.623 or 0.684.
- SR/(βL) is consistent on 0/4.
- (C/L)·β is consistent on 1/4.
- The TCR denominator cannot be identified from the data (∂Score/∂TCR is about 0.007 per unit), so it is taken from the README: L.

How strong is this test? For a wrong CR formula, landing inside the 0.001 m NE window has probability of about 0.12 per point (0.24 where two SR or C candidates exist). Passing all four by chance is about 1e-3. **[high]**

### 2.3 Residual decomposition (val_seen; val_unseen in brackets)
Replacing each displayed value with the exact value in turn:
- SR −0.003249 (−0.007789)
- CR −0.000786 (−0.000915)
- NE −0.000125 (−0.000011)
- TCR −0.000002 (≈0)

Sum: −0.004162 (−0.008715), which equals the residual exactly.

### 2.4 About the brief's premise ("CR 0.623 with TCR 13.7 cannot be an all-episode rate")
That argument is not decisive on its own. An all-episode rate of 0.623 (485/778 colliding episodes) would be arithmetically possible with TCR 13.7. The real colliding-episode share is 425/778 = 54.6%, with heavy collision tails. The exclusion comes from the exact Score arithmetic and the explicit README formula, not from plausibility.

### 2.5 What the reconstruction tells us about CMA

| | val_seen | val_unseen |
|---|---|---|
| collision-free successes | 140 (18.0%) | 237 (12.9%) |
| episodes with ≥1 adjusted collision | 425 (54.6%) | 1,090 (59.3%) |
| adjusted collision steps | 10,679 (25.1 per colliding episode) | 32,248–32,249 (29.6 per colliding episode) |
| social multiplier (0.7+0.3·Social) | 0.7899 | 0.7751 |

Run-to-run variation is large. The organizer trainer-based run and the replay run of the same checkpoint differ by 1.04 / 1.00 Score points, by 12 / 27 successes, and by TCR 13.27 vs 13.73 and 22.35 vs 17.54. The README says "Humans move in real time, so repeat runs can differ" (2daf3dd L324). Part of this is closed-loop policy divergence; part is wall-clock human frames.

---

## 3. collision_num semantics

**Provenance (verified from git).**
- `metric.py` was first committed on 2025-01-16 (af69d83). It already loaded `./data/datasets/collision_num_{split}.json` and the beta table.
- The files were added on 2025-02-21 (5a58635, author lpercc) under `Data/HAR2R-CE/`.
- They were renamed to `Data/HA-R2R-tools/` on 2025-02-28 (660e568) with byte-identical content and have never been changed since.
- `human_motion.json` was added on 2025-02-28 16:25 (b7ebadd), after the collision_num files.
- The toolkit pins the val files by SHA-256 (`track2/scripts/resources.json`: val_seen 632b5a47…, val_unseen 2c9111b1…). Both match the local files.
- test (9069d5da…) is public in the repo, but the toolkit intentionally does not pin it. The README says "collision annotations remain withheld" for Phase 2.

**Structure (verified; `a4work/cn_map.py`, using the R2R-CE v1-2 episode→trajectory map from `BASE/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed`).**
- Values are integers 0–4.
- They are **constant within every trajectory**: 259/259 val_seen, 613/613 val_unseen. A1 found the same for 1,136/1,136 test blocks {3k+1..3k+3}.
- Histograms:
  - val_seen {0:718, 1:42, 2:9, 3:9}
  - val_unseen {0:1680, 1:75, 2:57, 3:6, 4:21}
  - test {0:3171, 1:213, 2:6, 3:18}
  - train {0:9995, 1:610, 2:100, 3:96, 4:18}
- Means are 0.112 / 0.158 / 0.082 per episode.

**Paper definition.** HA-VLN 2.0, arXiv 2503.14229, App. D.1, via WebSearch summary: `TCR = Σ(c_i − |A_i^c|)/L` and `CR = Σ min(c_i − |A_i^c|, 1)/(βL)`. Here A_i^c is "the set of critical human activities the agent will encounter in the ground-truth path", c_i counts collisions within 1 m of a human, and β is "the fraction of instructions influenced by humans". So collision_num should be |A_i^c|. As implemented it is a precomputed per-trajectory integer.

**HA-VLN 1.0 analogue.** In `BASE/HA3D_simulator/tasks/HA/eval.py` L55-73, `penalty = #humans with human_rel_pos ∈ {'Beginning','End'}` of the GT path, and L96-98 sets `total_hits = sum(hits) − penalty`. That value is **not clipped**; 2.0 adds `max(0,·)`.

**Hypotheses tested against the CE file (`a4work/cn_hyp.py`).** None reproduce it.

| hypothesis | val_seen exact match | val_unseen exact match |
|---|---|---|
| HA-1.0 Begin/End penalty | (0,0) on 204 trajectories, but 35 trajectories have penalty 1 with cn 0 | no better |
| #humans (human_motion.json) whose viewpoint is on the GT path | 173/259 | 379/613 |
| … at the path start or end | 233/259 | 546/613 |
| … at intermediate viewpoints | 177/259 | 398/613 |
| #humans within r of the reference polyline (r = 0.3 m) | 163/259 | 383/613 |
| same, r = 2 m | 89/259 | 180/613 |

A2 independently found only 96/159 cn>0 val_unseen episodes with a human within 0.3 m of the reference path.

**Best inference [low-medium].** collision_num is the collision count recorded when the oracle/GT trajectory was replayed in HA-VLN-CE with an early version of the human placements. That would explain the per-trajectory constancy, small integers, possible wall-collision contributions, and the poor match with the current placements.

**What this means in practice.** The allowance only matters for an agent that collides. It "excuses" up to cn collisions in 7–9% of trajectories. Treat it as a released constant, and use the public test file for local test-split estimates (assuming the scorer uses it; to be confirmed from the image).

**β ("human-influenced").** H = 96, 246 and 549 are each divisible by 3 (32 / 82 / 183 trajectories), so β is a per-trajectory property. It does not equal "no human in HA-1.0 annotations" (50 / 231 trajectories) or "no human within r m of the path" for any r from 1 to 10 m. Because the numerator sums over all episodes, β only matters as a constant denominator. Its semantics are not decision-relevant.

---

## 4. Worked example

Per episode (toy split L = 6, H = 1, so βL = 5):

| ep | collisions.count | collision_num | STOP and d<3 (success) | final d (m) | e = max(0, count−cn) | CR_ep = min(e,1) | SR_ep = success·[e=0] |
|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 1 | 1.20 | 0 | 0 | 1 |
| B | 3 | 1 | 1 | 2.10 | 2 | 1 | **0** (collisions void the success) |
| C | 1 | 2 | 1 | 0.80 | 0 | 0 | 1 (excused by the allowance) |
| D | 0 | 0 | 0 | 5.00 | 0 | 0 | 0 |
| E | 0 | 0 | **0** (500 actions, no STOP) | 0.50 | 0 | 0 | 0 |
| F | 7 | 0 | 0 | 9.00 | 7 | 1 | 0 |

Aggregates:
- SR = 2/6 = 0.3333; NE = 18.6/6 = 3.1; TCR = 9/6 = 1.5; **CR = 2/5 = 0.4** (not 2/6).
- Navigation = 0.8·0.3333 + 0.2·3/6.1 = 0.365027.
- Social = 0.75·0.6 + 0.25/2.5 = 0.55, so the multiplier is 0.865.
- **Score = 31.5749.**

Test-scale scenarios (L = 3,408, βL = 2,859, NE = 2.5):

| scenario | SR | CR | TCR | Score |
|---|---|---|---|---|
| T1 zero collisions | 2045/3408 = 0.6001 | 0 | 0 | **58.914** |
| T3 2% of episodes with one bump, half of them would-be successes | 2011/3408 | 68/2859 = 0.0238 | 0.020 | 57.719 (−1.19) |
| T2 10% of episodes slide 3 steps, half would-be successes | 1875/3408 | 341/2859 = 0.1193 | 0.300 | 52.498 (−6.42) |

---

## 5. Sensitivity analysis (`a4work/sens.py`)

Partial derivatives, writing f = 0.70 + 0.30·Social and Nav = 0.8·SR + 0.6/(3+NE):
- ∂S/∂SR = 80·f
- ∂S/∂NE = −60·f/(3+NE)²
- ∂S/∂CR = −22.5·Nav
- ∂S/∂TCR = −7.5·Nav/(1+TCR)²

At CR = TCR = 0 (f = 1), Score = 80·SR + 60/(3+NE).

| SR | NE | Score | ∂/∂SR | ∂/∂NE (per m) | ∂/∂CR | ∂/∂TCR | 1 pp SR ≡ NE (m) | 1 pp SR ≡ CR (pp) | 1 pp SR ≡ TCR |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 1 | 55.0 | 80 | −3.750 | −12.38 | −4.13 | 0.213 | 6.5 | 0.194 |
| 0.5 | 2 | 52.0 | 80 | −2.400 | −11.70 | −3.90 | 0.333 | 6.8 | 0.205 |
| 0.5 | 3 | 50.0 | 80 | −1.667 | −11.25 | −3.75 | 0.480 | 7.1 | 0.213 |
| 0.6 | 2 | 60.0 | 80 | −2.400 | −13.50 | −4.50 | 0.333 | 5.9 | 0.178 |
| 0.7 | 1 | 71.0 | 80 | −3.750 | −15.98 | −5.33 | 0.213 | 5.0 | 0.150 |
| 0.7 | 2 | 68.0 | 80 | −2.400 | −15.30 | −5.10 | 0.333 | 5.2 | 0.157 |
| 0.7 | 3 | 66.0 | 80 | −1.667 | −14.85 | −4.95 | 0.480 | 5.4 | 0.162 |
| 0.8 | 2 | 76.0 | 80 | −2.400 | −17.10 | −5.70 | 0.333 | 4.7 | 0.140 |
| 0.9 | 1 | 87.0 | 80 | −3.750 | −19.58 | −6.53 | 0.213 | 4.1 | 0.123 |
| 0.9 | 3 | 82.0 | 80 | −1.667 | −18.45 | −6.15 | 0.480 | 4.3 | 0.130 |

**Per-episode marginal values on test (L = 3,408, βL = 2,859).**

| | SR 0.6 / NE 2.5 | SR 0.7 / NE 2.0 | SR 0.8 / NE 1.5 |
|---|---|---|---|
| +1 collision-free success | +0.02347 | +0.02347 | +0.02347 |
| −1 m final distance in one episode | +0.00058 | +0.00070 | +0.00087 |
| first collision in a failed episode | −0.00593 | −0.00685 | −0.00779 |
| first collision in a successful episode | −0.02941 (1.25× a success) | −0.03032 (1.29×) | −0.03126 (1.33×) |
| each further collision in the same episode | −0.0013 | −0.0015 | −0.0017 |

Phase 1 (val_unseen, L = 1,839, βL = 1,593): a success is worth +0.0435 and a colliding episode costs about −22.5·Nav/1593.

**Reference anchors.**
- Upper bound: SR = 1 with NE = 0.5 gives 97.1. The theoretical maximum is 100.
- STOP-only, using the R2R-CE v1-2 proxy for HA-R2R coordinates:
  - With Euclidean NE (val_seen SR .0039, NE 8.197; val_unseen SR .0343, NE 7.467): **5.667 / 8.473**.
  - If the scorer were geodesic: 4.769 / 5.042.
  - Under the Euclidean reading, STOP-only already reaches 65% of CMA's val_unseen Score (12.945).

**Strategic reading.**
- (i) Success is everything. 80 of the 100 points come from SR.
- (ii) Collisions mostly cost through the successes they void. A collision-avoiding manoeuvre is worth it whenever it does not reduce P(success) by more than about 1.3× the collision probability it removes.
- (iii) Avoiding collisions in failed episodes is worth only about a quarter of a success each. Even so, a 10% slide rate costs about 6.4 points (T2), so zero-collision locomotion is still a top-3 lever.
- (iv) NE is a weak but non-trivial global term. 1 m of mean NE is worth about 3 pp SR. Cheap NE wins: on uncertain episodes, stop at the most probable goal, and never wander off when lost.
- (v) Nothing penalises path length, so exploration is free (budget 500 actions vs about 55 actions for an average GT path).
- (vi) TURN, LOOK and STOP never increment collisions. A 500-action sequence without STOP can never succeed.

---

## 6. Spec for a local scorer that mirrors the official one

### Mode A — official code (P0)
1. `docker pull ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556`.
2. Copy out `/opt/havln-challenge/` (scoring/havln_scoring, codabench/phase1, including `public_reference_manifest.json`) and `/app/config/`.
3. Diff them against the public code. Specifically read:
   - the measure list in `six_action_task.yaml` and `challenge_submission.yaml`;
   - whether `habitat_extensions` (the Euclidean override) is imported;
   - the CR denominator and the source of collision_num;
   - how 500-action sequences without STOP are handled;
   - any human-proximity filter (paper: 1 m);
   - per-episode reset and human-thread handling.
4. Run `havln-score-phase1 --submission X.zip --output-dir R --gpu-ids 0 1 …` with `/data/havln2` (ro) and a writable `/data/havln2/recompute_navmesh` mount (2daf3dd README L290-301). For test or custom splits, wrap the same package APIs.
5. The image digests seen are `e1a0544f…` (toolkit) and `78a62cd1…` (HA-VLN README quickstart). Inspect both and confirm which one CodaBench uses.

### Mode B — our own mirror (for test, custom subsets and robustness sweeps; scales to many workers)
- **Validation:** identical to `havln-validate`/`check_rows` (export_cma_submission.py L36-45).
  - Exactly-once coverage of the split's episode ids.
  - 1 ≤ len ≤ 500.
  - Action names in {STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, LOOK_UP, LOOK_DOWN}.
  - STOP at most once and only last; mandatory if len < 500.
  - `split` field per JSON; flat ZIP.
- **Environment:** inside the image, `HAVLNCEDaggerEnv` (vlnce_baselines/common/environments.py L49-76) with `/app/config/challenge_submission.yaml` and the following settings (mirroring export_cma_submission.py L104-129):
  - `DATASET.SPLIT/DATA_PATH/SCENES_DIR`, `EPISODES_ALLOWED`;
  - `HUMAN_GLB_PATH=/data/havln2/HAPS2_0`, `HUMAN_INFO_PATH=…/human_motion.json`, `RECOMPUTE_NAVMESH_PATH=…/recompute_navmesh`;
  - `ITERATOR_OPTIONS.SHUFFLE=False`, `MAX_SCENE_REPEAT_STEPS=-1`, `SEED=0`;
  - episodes sorted by int(id);
  - `TASK.MEASUREMENTS=[DISTANCE_TO_GOAL, SUCCESS, COLLISIONS]`. Optionally add `COLLISIONS_DETAIL` for per-step flags. Do **not** add DISTANCE_TO_HUMAN: it executes and undoes a MOVE_FORWARD each step and resets sensor tilt (A2).
- **Loop per episode:**
  1. `obs = env.reset()`; assert `current_episode.episode_id == id`.
  2. For each action, `obs,_,done,info = env.step(name)`.
  3. Assert `done` occurs exactly at the last action (STOP, or the 500th action).
  4. Record `info['collisions']['count']`, `info['distance_to_goal']`, `info['success']`, the per-step collided flags, the active human `frame_id` per step (`havlnce_tool.frame_id`), the wall-clock per step, and the final pose.
- **Aggregation:** `a4work/havln_score_ref.py`, which self-tests against the CMA val_seen integers and reproduces 16.509450:
  - e = max(0, count − cn[ep]), CR_ep = min(e, 1), SR_ep = success·[e == 0];
  - SR, NE, TCR divided by L; CR divided by βL = L − H with H from metric.py L12;
  - Score in float64;
  - rank key (−Score, −SR, NE, CR, TCR).
  - Report Navigation, Social, the multiplier, counts (k, C, Σe), and the per-episode table.
- **Nondeterminism control.** HASimulator/environments.py L41-47 and L96-147 drive human frames from a 0.1 s wall-clock thread; frames freeze after 120 signals. Replay each candidate under several frame schedules by patching `_signal_sender` / `_handle_signals`:
  - (a) real wall-clock at the measured official speed;
  - (b) frame frozen at 0;
  - (c) frame frozen at 119;
  - (d) one frame per step;
  - (e) humans absent (base navmesh), the slow-scorer new-scene case (A2).
  
  Score each schedule. Use the **worst case** for go/no-go and the mean as the estimate. A candidate is "collision-robust" if count == 0 under all schedules.
- **Acceptance tests for the mirror:**
  - (1) STOP-only on val_seen and val_unseen gives CR = TCR = 0, SR = frac(‖start−goal‖₂ < 3), NE = mean Euclidean start–goal distance, to within 1e-6, computed directly from the HA-R2R json. This catches Euclidean vs geodesic and coordinate bugs.
  - (2) Replaying the released CMA export (export_cma_submission.py) reproduces SR ≈ 140/778 and 237/1839, CR ≈ 425/682 and 1090/1593, TCR ≈ 13.73 and 17.54. Allow small wall-clock deviations (±5 episodes, ±0.3 TCR).
  - (3) Mode A and Mode B agree exactly on the same per-episode info dicts.
  - (4) The trainer output (base_il_trainer) satisfies CR_trainer × L/(βL) = CR_official.

---

## 7. Facts, inferences, contradictions

**Verified facts:** sections 1 to 3 above, with file and line citations. In addition:
- The current track2 README (L183-188) and the earliest README carry the same CMA replay table.
- The earlier "organizer re-evaluation" table (15.469585 / 11.944822) was replaced on 2026-10-02 (havln-challenge commit 5ad4380, "Document measured full CMA submission replay results").

**Inferences:**
- collision_num came from a GT-path replay with earlier human placements [low-medium].
- β marks trajectories "influenced" by humans by some annotation-based criterion [medium].
- The hidden scorer uses the public metric.py semantics plus division by βL [high for CR; medium-high for Euclidean distance and all-collision counting, pending image inspection].
  - C2 cites UWMILab/HA-VLN issue #17, where a maintainer confirmed that TCR counts general collisions, walls included. I could not re-check it: the WebSearch budget was exhausted, and the GitHub MCP is scoped to another repo.

**Corrections to CONTEXT.md:**
- (1) Fact 3 says "CR normalized by the human-influenced episode count", which is right. Spell it out: CR = (#episodes with e ≥ 1, over ALL episodes)/(L − H). It can exceed 1. The public trainer's CR is smaller by a factor of β.
- (2) "TCR ≈ 14–18 means the baseline collides on ~15 steps per episode": 41–45% of CMA episodes have no adjusted collision, and colliding episodes have about 25–30.
- (3) A 500-action sequence without STOP is legal (clarification branch Q13) but scores success = 0 under habitat Success semantics.

---

## 8. Recommendations
1. **P0:** pull both image digests and extract `/opt/havln-challenge` and `/app/config`. Treat `havln_scoring` and `havln-score-phase1` as ground truth, and diff them against this spec. This is the cheapest way to remove every remaining metric uncertainty.
2. Use `a4work/havln_score_ref.py` (or a port of it) as the single aggregation library for every agent and leaderboard internally. Always report k, C and Σe integers alongside the float metrics.
3. Use zero collisions as a hard constraint in both regimes: every collision in a success costs more than one success. Then maximise P(d < 3 m) per episode. Only then minimise NE, for example by falling back to the most-probable goal when the agent is uncertain.
4. Remove STOP-without-success failure modes: always end with STOP before step 500. A 500-action sequence never succeeds.
5. Use free exploration: the metric has no path-length or SPL term. Budget the 500 actions for look-arounds (TURN and LOOK never collide) and verification detours.
6. Calibrate the official scorer as soon as CodaBench is reachable. Run the STOP-only probe (expected about 8.47 on val_unseen if Euclidean, 5.04 if geodesic; compute the exact value from HA-R2R json), then a constructed wall-bump probe whose |S| is chosen so that C/L and C/(βL) differ in the third decimal of CR.
7. Model selection: a 1-point val_unseen Score difference corresponds to about 1.25 pp SR, which is within building-level noise across 11 val_unseen buildings. Prefer paired per-episode comparisons and the worst-case-over-frame-schedules Score.

## 9. Open questions
- Does `havln_scoring` subtract collision_num from the public `collision_num_test.json` (sha256 9069d5da…) or from a withheld file? Does it use βL = 2,859 for test?
- Does it count all collisions, or only those within 1 m of a human (paper)? Is distance Euclidean (HA override) or geodesic?
- Does it handle a 500-action no-STOP sequence as plain habitat does (success 0)?
- What exactly defines the 96 / 246 / 549 non-influenced trajectories, and how was collision_num generated?
- How large is the official scorer's wall-clock variance for a fixed action file?

## 10. Sources
- BASE/HA-VLN/HASimulator/metric.py L1-17; git history af69d83 (2025-01-16), 5a58635 (2025-02-21), 4a847fc (2025-03-02).
- BASE/HA-VLN/agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py L245-497.
- BASE/HA-VLN/HASimulator/measures.py L17-20, L100-180; BASE/HA-VLN/agent/VLN-CE/habitat_extensions/measures.py L16, L28; habitat_extensions/__init__.py L1.
- BASE/habitat-lab-0.1.7/habitat/tasks/nav/nav.py L500-539, L653-672, L930-976; habitat/core/env.py L187-198, L229-272; habitat/core/registry.py L43-60.
- BASE/HA-VLN/HASimulator/config/HAVLNCE_task.yaml L1-57.
- BASE/HA-VLN/agent/VLN-CE/vlnce_baselines/common/environments.py L49-76; BASE/HA-VLN/HASimulator/environments.py L25-215.
- BASE/track2/README.md L183-213; BASE/track2/scripts/export_cma_submission.py L36-45, L74, L104-129, L148-170, L188-189, L219; BASE/track2/scripts/resources.json.
- BASE/track2-jostar `git show 2daf3dd:README.md` L96-101, L246-256, L290-301, L316-325, L327-350.
- BASE/havln-challenge git history (8e36fa7 … 1155a52; 5ad4380; e83e355); index.html L206.
- BASE/havln2/HASimulator/README.md L94-106.
- BASE/HA-VLN/README.md L143-150 and git history 0cb555a / 51e0ed8.
- BASE/roboworld2026.github.io/track2.html L127-185.
- BASE/HA-VLN/Data/HA-R2R-tools/collision_num_{train,val_seen,val_unseen,test}.json; BASE/HA-VLN/Data/Multi-Human-Annotations/human_motion.json; BASE/HA-VLN/HASimulator/HA-DE/tasks/HA/data/HA_{val_seen,val_unseen}.json.
- BASE/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{val_seen,val_unseen}/*.json.gz (episode→trajectory map, Euclidean and geodesic start–goal proxy).
- BASE/HA3D_simulator/tasks/HA/eval.py L55-73, L96-100, L135-152 (HA-VLN 1.0 metric).
- BASE/jostar-track2 branch bohan/clarification-Oct14 (Q4 wall-clock FPS, Q13 STOP omission at 500).
- [HA-VLN 2.0 paper, arXiv 2503.14229 (App. D.1 metric definitions, via WebSearch summary)](https://arxiv.org/abs/2503.14229); [HA-VLN 1.0, arXiv 2406.19236](https://arxiv.org/pdf/2406.19236).
- Cross-references: findings A1 (trajectory triples), A2 (collision semantics), C2 (issue #17, CodaBench outage).
