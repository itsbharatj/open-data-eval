# A10: HA-VLN 2.0 paper deep read, metric lineage and the organizer leaderboard

Topic id: `A10-havln2-paper-deep-read-and-organizer-leaderboard`. Research agent A10, 2026-10-24.

Paths below use `EXT=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext` and `SP=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad`.

**Access limits.** arxiv.org, huggingface.co, alphaxiv, themoonlight and semanticscholar were all unreachable from WebFetch and curl (DNS failure or proxy 403). WebSearch worked for about 20 queries. After that, the 200-call search budget shared by all agents ran out, so further searches were impossible. Paper numbers below therefore come from three kinds of source:
- verbatim copies in local sources: the HCSG paper PDF from its GitHub page, organizer git histories, and paper figures checked into the repos;
- WebSearch snippet extractions, marked as such;
- other agents' findings (B1, B2), cross-checked against the above.

## 0. Summary of the most decision-relevant findings

1. **The only directly comparable numbers to beat are the challenge CMA baselines.**
   - val_unseen: Score **12.945** from the toolkit replay, or **11.945** from the organizer's trainer re-evaluation.
   - val_seen: **16.509** or **15.470**.
   - Both runs use the same released checkpoint. They differ by about 1 Score point and by about 5 TCR (17.5 vs 22.4) because humans animate on wall-clock time. The organizers say so themselves: "Humans move in real time, so repeat runs can differ" (havln-challenge commit 5ad4380).
   - No public RoboWorld Track 2 leaderboard entries exist. `roboworld2026.github.io/leaderboard.html` says "Coming soon", and CodaBench has been down since about Oct 21.
   - No results from the "small-scale internal competition (Aug 2025)" were found anywhere. That README line was only added on 2026-10-05 (HA-VLN commit f1ebc41).
2. **The best published HA-VLN-CE numbers are low.** On val unseen:
   - HCSG (arXiv 2605.13321, May 2026): SR 0.24 / CR 0.36 / TCR 5.02.
   - Retrained BEVBert: SR 0.21 / CR 0.55 / TCR 4.71 / NE 5.51.
   - ETPNav: 0.17 / 0.58 / 6.94.
   - Plugged into the challenge formula, these are about Score 22.5–22.9 (HCSG, NE assumed 5.0–5.5) and **19.4** (BEVBert).

   These numbers are NOT strictly comparable with the challenge:
   - The paper's TCR is described as human-proximity collisions, while the challenge counts all contact steps.
   - The paper's agents used a 12-view panoramic rig, which the Oct-14 clarification bans.

   Even so, **an agent with SR ≥ 0.30 and few collisions (Score ≥ 30) would beat every published HA-VLN-CE result.**
3. **The metric definitions differ between the paper and the code that scores us.**
   - **Paper and website:** TCR counts "collisions within 1 m of a human" ("frequency of collisions in human-occupied zones"). This comes straight from HA-VLN 1.0 / HA-DE, where a "crash" is `minDistance <= 1` m to any human (`HA3DSim.py:180`).
   - **Challenge code:** the count is Habitat's `previous_step_collided`, which covers walls AND humans with no 1 m proximity term. It is adjusted by the released per-episode allowance `collision_num` (= |A_i^c|, the "critical human activities on the ground-truth path").
   - **Implication:** wall contact is the dominant collision source and the 1 m personal-space rule is not scored. Keeping clear of humans is still cheap insurance.
4. **The CR denominator is βL = 682 / 1,593 / 2,859, not 96 / 246 / 549.** The organizer README history (`havln-challenge` commit 8e36fa7, README L87-91) has a table "Human-influenced episodes (βL): val_seen 682, val_unseen 1,593". The formula is CR = Σ min(e_i,1) / (βL), with β = 1 − 96/778 and so on.
   - **CONTRADICTION FLAG:** the user's project file `/home/user/open-data-eval/competitions/roboworld2026-track2/00-competition-facts.md` (about L49) and `havln_tools/score.py` (`HUMAN_INFLUENCED` about L44-50, default `cr_mode="human_influenced"`) divide by 96 / 246 / 549. This inflates CR 7.1x / 6.5x / 5.2x. Their baseline check only worked because it fed in the published CR rather than recomputing it.
   - Because the denominator is βL < L, CR can exceed 1 (upper bound 1.14–1.19). That makes the Social term negative, so even non-human episodes with wall contact hurt CR.
5. **What the organizers consider standard.**
   - Paper v5, as summarized in the organizer toolkit, benchmarks: HA-VLN-CMA (Base, +DA, and full CMA* = +DAgger +EnvDrop) and HA-VLN-VL (a Recurrent-VLN-BERT-style transformer with a state token, Fig. 13), both proposed in the paper; BEVBert and ETPNav as external comparisons (retrained and zero-shot); and NaVid and NaVILA as zero-shot comparisons.
   - On HA-VLN-DE: Speaker-Follower, Rec(PREVALENT) and Airbert.
   - HCSG's table adds LAW-VLNCE, DUET and GridMM on HA-VLN-CE.
   - The track page explicitly "encourages world models that anticipate human trajectories and future observations, and VLAs" (`track2.html` L82). The lead organizer's own line of work is world models (UniWM, LCVN NeurIPS 2026 oral).

## 1. Paper identity and version history

| Item | Value | Evidence | Conf. |
|---|---|---|---|
| arXiv id | 2503.14229 | all repos | high |
| v1 date | 2025-03-18 | WebSearch (arXiv listing "v1 submitted 18 March, 2025") | med-high |
| v1/v2 title | "HA-VLN: A Benchmark for Human-Aware Navigation in Discrete–Continuous Environments with Dynamic Multi-Human Interactions, Real-World Validation, and an Open Leaderboard" | HA-VLN README bibtex at commits 4e0169e (2025-03-19) through 724f487 (2025-07-13); arxiv.org/html/2503.14229v1 and v2 titles in search results | high |
| later title (≥ about Oct 2025) | "HA-VLN 2.0: An Open Benchmark and Leaderboard for Human-Aware Navigation in Discrete and Continuous Environments with Dynamic Multi-Human Interactions" | README title from commit 160becd (2025-12-16); HF "published Oct 9 2025"; arXiv search "latest submitted 9 October, 2025" | med |
| latest version | v5, 18 Aug 2026 (arXiv header "arXiv:2503.14229v5 [cs.AI] 18 Aug 2026") | WebSearch snippet; organizer commit ec8f682 (2026-09-28) "Align participant pages with HA-VLN 2.0 paper v5" | med-high |
| venue | IROS 2026 (accepted 2026-06) | `EXT/HA-VLN/README.md` L47; bibtex in `EXT/track2/README.md` L328-333 | high |
| authors (v5) | Yifei Dong*, Fengyi Wu*, Qi He, Lingdong Kong, Heng Li, Minghan Li, Zebang Cheng, Yuxuan Zhou, Jingdong Sun, Qi Dai, Alexander G. Hauptmann, Zhi-Qi Cheng† (UW, NUS, CMU, MSR). Bohan Xiong and Yetong Sha are on the webpage team list. | `EXT/HA-VLN/README.md` header; `EXT/a10/UWMILab_HA-VLN-webpage/src/pages/index.astro` authors list | high |
| organizers of Track 2 = paper authors | Yifei Dong's CV: "Competition Organizer: RoboWorld Challenge"; "HA-VLN 2.0 serves as the benchmark for the human-aware navigation track" | `EXT/a10/F1y1113_f1y1113.github.io/assets/documents/Yifei_Dong_CV.pdf` (pdftotext lines 37, 51-52) | high |

**How content changed across versions.** These are inferences from snippets and organizer commits, medium confidence.
- **v1/v2:** CE agents BEVBert and ETPNav (retrained and zero-shot), plus HA-VLN-CMA variants (Base, DA, CMA*) and HA-VLN-VL. DE agents Speaker-Follower, Rec(PREVALENT) and Airbert. Ablations (human→cylinder, enrichment on/off, step size). Real-world validation. "Open leaderboard" for HA-R2R-DE and HA-R2R-CE.
- **v3–v5:** Table 1 has HA-VLN-CE results with Retrained and Zero-shot sub-columns for val seen, val unseen **and test**. NaVid and NaVILA were added as zero-shot comparisons (organizer README at ec8f682 lists "NaVid | External zero-shot comparison; NaVILA | External zero-shot comparison"). Fig. 13 shows the network structures (checked into `havln-challenge` at 8e36fa7: `assets/media/model-architectures.webp`, viewed).

## 2. Dataset facts (paper + repos)

| Fact | Value | Evidence | Conf. |
|---|---|---|---|
| HA-R2R instructions | 16,844 = 10,819 train / 778 val_seen / 1,839 val_unseen / 3,408 test (same as R2R-CE) | `EXT/track2/README.md` L165-171 | high |
| test split | 3,408 instructions, 18 unseen buildings, "emphasis on multi-human routes"; "scored server-side on the withheld test split" | `EXT/roboworld2026.github.io/track2.html` L122, L127 | high |
| distinct trajectories | train 3,603 / val_seen 259 / val_unseen 613 (3 instructions per path) | havln-challenge README @8e36fa7 L87-91 | high |
| human-influenced episodes (βL) | val_seen 682 (β=0.8766), val_unseen 1,593 (β=0.8662). Implied: train 9,204 (β=0.8507), test 2,859 (β=0.8389) | havln-challenge README @8e36fa7 L90-91; `EXT/HA-VLN/HASimulator/metric.py` L12 (β = 1−1615/10819, 1−96/778, 1−246/1839, 1−549/3408) | high |
| instruction length | HA-R2R mode about 100–105 words, mass 60–250, mean about 112 (paper). R2R-CE mode about 20 words. Longer with more humans: modes about 97 (0–1 human), 107 (2), 117 (3), 125 (>3) | `EXT/HA-VLN/demo/figs/instruction_length_comparison_v2.png`, `human_group_count_vs_length.png` (viewed) | high (figure) / med (mean 112) |
| paths intersecting human motion | "35.5% of the 16,844 paths physically intersect with human motion" | WebSearch snippet only | low-med |
| HAPS 2.0 | 486 motions (MDM, SMPL, 120 frames each, so 58,320 frames), 172 activity categories, 26 region types, 90 scans | `EXT/HA-VLN/README.md` HAPS section; `EXT/track2/README.md` L174; webpage index.astro L71-77 | high |
| placed humans | 910 instances in 428 regions. Interaction groups: 72 two-human, 59 three-human, 15 four-human. Stage-2 fine annotation: 529 models in 374 regions | `EXT/HA-VLN/README.md` (Human Activities Annotation section) | high |
| motion vs static | 268 moving (242 indoor / 26 outdoor) vs 642 static (557 indoor / 85 outdoor). Group sizes: 1-human 58.1%, 2: 15.8%, 3: 19.4%, 4: 6.6%. Average movement distance (enriched) 0.37. Outdoor regions 44 → 111 with enrichment. Human models used 358 → 486 | `EXT/HA-VLN/demo/figs/dataset_analy.png` (paper figure, viewed) | high |
| public human placements | `human_motion.json`: 72 scans, 749 humans. So about **161 humans (17.7%) sit in the 18 withheld test scans** (910−749, if 910 covers all 90 scans) | python count of `EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json` | high (749) / med (161) |
| test scans have humans | The paper teaser shows RPmz2sHmrrY (a test scan) populated with humans | `EXT/HA-VLN/demo/figs/task_define_final-1.png` (viewed) | high |
| per-episode allowance `collision_num` | Values 0–4. Non-zero in train 824/10,819, val_seen 60/778, val_unseen 159/1,839, **test 237/3,408** (mean 0.082; 213×1, 6×2, 18×3) | python over `EXT/HA-VLN/Data/HA-R2R-tools/collision_num_*.json` | high |

**HA-VLN 1.0 data, for lineage** (`EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/data`, python count):
- Discrete HA-R2R uses the full R2R path set (4,675 + 340 + 783 train/val paths, plus 1,391 test paths, = 7,189 paths, about 21.5k instructions).
- Average 50–59 words.
- 65–79% of paths have a human annotated (val_unseen 509/783, val_seen 268/340, train 3,515/4,675).
- `human_rel_pos` ∈ {Beginning, Around, Obstacle, End}.
- HAPS 1.0 = 145 descriptions × 3 MDM samples = 435 motions (`EXT/a10/lpercc_HA3D_simulator/human-viewpoint_annotation/human_motion_model/README.md` L12: `--num_repetitions 3 --batch_size 145`).

## 3. Exact metric definitions: paper vs HA-VLN 1.0 code vs challenge code

### 3.1 Paper (HA-VLN 2.0), from WebSearch extractions of arxiv html v2/v5 (medium confidence)
- **TCR** = Σ_i (c_i − |A_i^c|) / L.
  - c_i = "the set of time steps with collisions that counts collisions within 1 m of a human".
  - A_i^c = "the set of critical human activities the agent will encounter in the ground-truth path" (unavoidable).
  - The paper says TCR measures "how often collisions occur in human-occupied zones".
- **CR** = "fraction of navigation instances incurring at least one collision, conditioned on the fraction β of instructions influenced by humans". The toolkit makes this CR = Σ min(e_i,1)/(βL).
- **SR** = the episode has zero collisions AND the agent stops within 3 m of the goal.
- **NE** = final distance to goal (m).
- "Personal-space adherence" in the abstract refers to this 1 m human-proximity notion. Website `track2.html` L133: TCR = "Frequency of collisions in human-occupied zones".
- I found no evidence that the composite Score is in the paper. It appears to be a challenge construct (HA-VLN commit f4d66a8 "remove challenge Score", later reverted). havln2-docs (`EXT/a10/JostarXiong_havln2-docs/docs/api/evaluation_metrics.md` L47-69) presents it as "HA-VLN adopts a multi-objective Composite Score". Medium confidence.

### 3.2 HA-VLN 1.0 / HA-DE code (verified, high confidence)
- `EXT/a10/lpercc_HA3D_simulator/HA3DSim.py` L174-180: `state.isCrushed = int(minDistance <= 1)`, a proximity "crash" within 1 m of any human. The env comment at `EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/env.py` L377 reads "Threshold is 1.0m".
- `EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/eval.py` L55-73, L96-99, L135-174:
  - total_hits = Σ_steps crash − penalty, where penalty = number of annotated humans whose `human_rel_pos` ∈ {Beginning, End}, i.e. the unavoidable ones. This is the ancestor of |A_i^c| and `collision_num`.
  - `total_hits_rate` (TCR) = mean(total_hits). There is no max(0,·), so it can be negative.
  - `hits_rate` (CR in 1.0) = fraction of episodes with any crash, over ALL episodes, unadjusted.
  - `successes_nohits_rate` (SR) = NE < 3 m AND total_hits == 0.
  - It also reports `politeness_rate` = 0.8·SR + 0.2·(1−hits_rate)·SR. That is a precursor of the 0.8/0.2 weights in the challenge Navigation term.

### 3.3 Challenge, which is what actually scores us (high confidence)
- `EXT/HA-VLN/HASimulator/metric.py` L12-17:
  - TCR_ep = max(0, collisions.count − collision_num[ep])
  - CR_ep = min(TCR_ep, 1)
  - SR_ep = success × [TCR_ep == 0]
- `collisions.count` = steps with Habitat `previous_step_collided` (any obstacle, walls included). Humans are static objects in a navmesh recomputed with agent_radius 0.1 and height 1.5 (`EXT/HA-VLN/HASimulator/environments.py` L137-139; see A2).
- Aggregation (toolkit README @ec8f682 L338-350): SR, NE and TCR are means over L. **CR = Σ min(e_i,1) / (βL)** with βL = 682 / 1,593 / (2,859 test).
- The trainer's own aggregation (`EXT/HA-VLN/agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py` L473-481) averages CR over ALL episodes with no β. So "trainer" CR and "replay/CodaBench" CR are not the same statistic. The 0.165/…/0.638 trainer row may therefore be un-normalized (unverified).
- **Score** = 100 · (0.8·SR + 0.2·3/(3+NE)) · (0.7 + 0.3·(0.75(1−CR) + 0.25/(1+TCR))) (`EXT/track2/README.md` L203-209). Ties are broken by SR↑, NE↓, CR↓, TCR↓, then submission time.

### 3.4 Differences that matter

| Aspect | Paper text | Challenge code | Consequence |
|---|---|---|---|
| What is a collision | within 1 m of a human (1.0 heritage) | any Habitat contact step (walls + humans) | wall-scraping (sliding) dominates TCR; CMA TCR about 14–22 |
| allowance | \|A_i^c\| critical activities on GT path | released `collision_num` (0–4) | test allowances are public; 237 test episodes have ≥1 free contact |
| CR denominator | β-conditioned | βL (682 / 1,593 / 2,859) | CR can exceed 1; collisions in non-human episodes still count |
| SR | zero collisions + ≤3 m | success × (TCR_ep==0) | identical |
| Score | not in paper (probable) | composite above | SR dominates (weight about 56–80 Score per unit SR) |

## 4. Numbers to beat

### 4.1 Directly comparable: challenge CMA baseline (released `ckpt.39.pth`, `cma_pm_da_aug_tune`)

| Run | Split | SR | NE | CR | TCR | Score | Source |
|---|---|---|---|---|---|---|---|
| toolkit local replay of exported actions | val_seen | 0.180 | 6.223 | 0.623 | 13.726 | **16.509450** | `EXT/track2/README.md` L183-186; havln-challenge commit 5ad4380 |
| toolkit local replay | val_unseen | 0.129 | 6.387 | 0.684 | 17.536 | **12.945387** | same |
| organizer trainer re-eval | val_seen | 0.165 | 6.230 | 0.638 | 13.271 | 15.469585 | `EXT/HA-VLN/README.md` L143-148; havln2-docs evaluation_metrics.md L77-80; `EXT/havln2/agent/README.md` L95-98 ("published HA-VLN 2.0 evaluation results") |
| organizer trainer re-eval | val_unseen | 0.114 | 6.502 | 0.689 | 22.352 | 11.944822 | same |

The organizers swapped and then reverted these as the "Published Benchmark Reference" on 2026-10-13 (HA-VLN f4d66a8, reverted by 09b5234). The same checkpoint therefore spans about 1 Score point and about 5 TCR across runs.

Implied collision episodes for CMA, using the βL denominator: val_seen ≈ 425/778 (55%), val_unseen ≈ 1,090/1,839 (59%).

### 4.2 HA-VLN-CE literature (TCR / CR / SR). Val seen and val unseen are copied verbatim from the HA-VLN paper by HCSG Table I

Source: `SP/ext/a10/HaoxuanXU1024_HCSG/assets/paper/HCSG.pdf`, text at `SP/hcsg.txt` L407-423 and `index.html` L205-330. Rows marked [10] are cited to arXiv 2503.14229. LAW/DUET/GridMM are listed without [10], so their provenance (the paper's leaderboard or HCSG's own runs) is unknown.

| Model | Seen TCR | Seen CR | Seen SR | Unseen TCR | Unseen CR | Unseen SR |
|---|---|---|---|---|---|---|
| HA-VLN-CMA (Base) [10] | 63.09 | 0.77 | 0.05 | 47.06 | 0.77 | 0.07 |
| HA-VLN-CMA-DA [10] | 17.45 | 0.61 | 0.17 | 27.25 | 0.69 | 0.09 |
| HA-VLN-VL [10] | 4.44 | 0.52 | 0.20 | 6.63 | 0.59 | 0.14 |
| LAW-VLNCE | 4.31 | 0.54 | 0.21 | 5.88 | 0.65 | 0.15 |
| DUET | 4.18 | 0.48 | 0.22 | 5.74 | 0.63 | 0.16 |
| ETPNav [2] (retrained) | 4.07 | 0.43 | 0.24 | 6.94 | 0.58 | 0.17 |
| GridMM | 3.92 | 0.45 | 0.24 | 5.76 | 0.59 | 0.18 |
| BEVBert [1] (retrained) | 3.64 | 0.46 | 0.27 | 4.71 | 0.55 | 0.21 |
| **HCSG (May 2026)** | 3.63 | 0.34 | 0.29 | 5.02 | 0.36 | **0.24** |

The same values appear on `sota2.com` ("Vision-and-Language Navigation on HA-VLNCE (val seen)") and `vlaleaderboard` (`EXT/a10/k1000dai_vlaleaderboard`, commit 10a7c98).

### 4.3 Further paper rows from WebSearch extractions (medium unless noted)

| Model / setting | Split | NE | TCR | CR | SR | Conf. |
|---|---|---|---|---|---|---|
| BEVBert retrained (0.25 m "CE default" step) | val unseen | 5.51 | 4.71 | 0.55 | 0.21 | med-high (TCR/CR/SR match HCSG) |
| ETPNav retrained | val unseen | ≈5.43 | 6.94 | 0.58 | 0.17 | med (NE low) |
| BEVBert zero-shot (VLN-CE-trained) | val unseen | 6.10 | 5.72 | 0.56 | 0.15 | med-high (3 extractions agree) |
| ETPNav zero-shot | val unseen | 7.40 | 7.94 | 0.71 | 0.08 | med-high |
| BEVBert, humans replaced by cylinders | val unseen | 6.32 | 5.11 | 0.46 | 0.17 | med |
| BEVBert / ETPNav without human presence and enrichment | val unseen | 6.13 / 7.75 | – | – | 0.19 / 0.14 | low-med |
| HA-VLN-CMA-Base retrained | seen / unseen / **test** | 7.63 / 7.34 / 7.30 | 63.09 / 47.06 / 47.55 | 0.77 / 0.77 / 0.76 | 0.05 / 0.07 / 0.07 | med (seen and unseen match HCSG) |
| HA-VLN-CMA-Base zero-shot | test | 7.89 | 62.14 | 0.74 | 0.04 | low-med |
| HA-VLN-CMA-Base zero-shot (B2 extraction) | val unseen (?) | 7.88 | 63.84 | 0.75 | 0.04 | low |
| HA-VLN-CMA* (full = +DAgger +EnvDrop) retrained | val seen | 5.61 | 3.34 | 0.60 | 0.17 | low |
| HA-VLN-CMA* retrained | **test** | 6.64 | 9.23 | 0.72 | 0.09 | low-med |
| HA-VLN-VL retrained | **test** | 5.52 | 5.96 | 0.63 | 0.14 | low-med |
| HA-VLN-VL zero-shot | test | 7.41 | 3.38 | 0.58 | 0.07 | low-med |
| SR drop vs VLN-CE (v1 gap table) | – | – | – | – | ETPNav −70.2% retrained / −86.0% zero-shot; BEVBert −64.4% / −74.6% | med |
| training-grid row (HA-R2R-trained) | val unseen | 6.23 | – | – | 0.15 (text: "28.6% drop") | low |
| unlabeled snippet: HA-VLN-VL 0.42 (HA-VLN-trained) / 0.38 (VLN-CE-trained) vs CMA-Base 0.23 | ? | – | – | – | – | low; columns unknown |

On test, the paper's CMA-Base and VL rows have the same SR as val unseen (0.07, 0.14). **Expect Phase 2 test difficulty ≈ val_unseen**, so the CMA checkpoint should land around Score 12–13 on test. This is an inference.

**HA-VLN-DE**, paper Table 2, val unseen, discrete, with B1 cross-check:

| Agent | SR (VLN → HA-VLN-DE) | NE | TCR | CR |
|---|---|---|---|---|
| Speaker-Follower | 0.35 → 0.21 | – | – | 0.72 |
| Rec(PREVALENT) | 0.63 → 0.33 | 6.12 | 0.29 | 0.81 |
| Airbert | 0.62 → 0.36 | 5.54 | 0.30 | 0.83 |

The paper lists four agents; the fourth was not recovered. Medium confidence.

**HA-VLN 1.0 (NeurIPS 2024 D&B):** the best retrained agent reached ≤40% SR on unseen, and human presence cut SR by up to 65%. Agents were VLN-CM and VLN-DT (decision transformer). Source: B2 finding 30, medium.

### 4.4 Challenge Score equivalents for literature rows

Computed by `SP/a10_scripts/score_rows.py`. These are only indicative, because metric semantics differ.

| Row | Score |
|---|---|
| CMA toolkit replay, val_unseen | 12.95 |
| CMA trainer re-eval, val_unseen | 11.93 |
| BEVBert retrained, val_unseen (5.51/4.71/0.55/0.21) | **19.42** |
| ETPNav retrained, val_unseen (NE 5.43 assumed) | 16.66 |
| BEVBert zero-shot, val_unseen | 15.06 |
| ETPNav zero-shot, val_unseen | 9.41 |
| HA-VLN-VL retrained, test | 14.48 |
| HA-VLN-CMA* retrained, test | 10.34 |
| HA-VLN-CMA-Base retrained, test | 8.63 |
| HCSG val_unseen (NE assumed 5.0 / 5.5) | **22.87 / 22.49** |
| BEVBert retrained, val_seen (NE 5.51 assumed) | 24.00 |

Targets for reference:

| SR | NE | CR | TCR | Score |
|---|---|---|---|---|
| 0.3 | 3 | 0.2 | 0.3 | 31.9 |
| 0.5 | 3 | 0.2 | 0.3 | 46.9 |
| 0.5 | 2 | 0.1 | 0.1 | 50.5 |
| 0.7 | 2 | 0.1 | 0.1 | 66.0 |
| 0.9 | 2 | 0.1 | 0.1 | 81.5 |

## 5. Methods the organizers benchmarked ("what they consider standard")

| Method | Role in paper / challenge | Notes | Evidence |
|---|---|---|---|
| HA-VLN-CMA (Base / -DA / * = +DA +EV) | paper-proposed; challenge reference (released ckpt `cma_pm_da_aug_tune`) | ResNet-50 RGB + ResNet-50 depth → cross-modal attention with BERT-embedded instruction → GRU → MLP. "Training uses environmental dropout and DAgger" | Fig. 13(b) (`SP/a10img/model-architectures.png`); `track2.html` L189-190 |
| HA-VLN-VL | paper-proposed baseline | BERT-like multi-layer transformer with a recurrent state token (Recurrent-VLN-BERT style); RGB+depth via ResNet-50; per-step action probabilities | Fig. 13(a); havln-challenge README @ec8f682 |
| BEVBert | external comparison (retrained and zero-shot) | strongest paper baseline (val unseen SR 0.21) | §4 |
| ETPNav | external comparison (retrained and zero-shot) | val unseen SR 0.17 | §4 |
| NaVid | external zero-shot comparison (v3+) | numbers not recovered | havln-challenge README @ec8f682 and @5ad4380 |
| NaVILA | external zero-shot comparison (v3+) | numbers not recovered | same |
| Speaker-Follower, Rec(PREVALENT), Airbert (+1 more) | HA-VLN-DE comparisons | discrete | §4.3 |
| LAW-VLNCE, DUET, GridMM | listed on HA-VLN-CE in HCSG Table I | provenance unclear | HCSG |
| VLN-CM, VLN-DT | HA-VLN 1.0 agents | discrete | HA-VLN 1.0 / HA3D repo |

**Real-world validation (paper).**
- Robot: Unitree GO2-EDU quadruped, Intel RealSense D435i, Jetson NX for inference, Raspberry Pi 4B for motion control. Reported failure: a hallway volunteer's sudden move.
- This is irrelevant to scoring but signals what the organizers value.
- HCSG's real-world: NXROBO Leo, 5 scenarios × 10 trials; BEVBert 19/50 vs HCSG 41/50 (`SP/hcsg.txt` Table VIII).

**Third-party HA-VLN-CE work (potential competitor profile).** HCSG, from HKUST(GZ) / SJTU / Haoang Li's group:
- pretrains in static VLN-CE for 100k iterations (batch 64, lr 5e-5), then fine-tunes online in Habitat for 15k iterations (batch 8, lr 1e-5) on 2× A6000;
- uses YOLO-Pose and Qwen3-VL-2B-Instruct;
- code status: "We will release our code soon" (`EXT/a10/HaoxuanXU1024_HCSG/README.md`).

HCSG's paper misstates HA-R2R as "averaging 15 words" (`SP/hcsg.txt` about L392), which raises a quality flag on their setup. Leads that I could not verify because the search budget ran out: Rule-VLN 2604.16993, TIC-VLA 2602.02459, HAM-VLN 2607.29600, LG-VLN 2609.15098, Goal2Pixel 2606.01621, survey 2512.00027, DPed-VLN (Habitat 3.0, separate benchmark), VLN-Safe "Successful but Unsafe".

## 6. Organizer leaderboard status

- **HA-VLN "Open Leaderboard" (paper).** The paper says the authors "host leaderboards for HA-R2R-DE and HA-R2R-CE" with "agent code or trajectories" and server-side evaluation (WebSearch snippet). No public entries were found:
  - the UWMILab webpage source (15 commits) has no leaderboard table;
  - the old `ha-vln-project.vercel.app` repo is not public.
- **RoboWorld leaderboard.html.** Track 2 says "Leaderboard: Coming soon" in every revision (`EXT/roboworld2026.github.io/leaderboard.html`, 4 commits checked).
- **CodaBench 18135.** Unreachable (also reported down since about Oct 21 per CONTEXT update).
- **Internal competition, Aug 2025.** Only the one-line news item exists (`EXT/HA-VLN/README.md` L48, added 2026-10-05 by f1ebc41). The Aug 2025 commits changed only README styling and title. There are no results, team names or numbers.
- **Prize history.** Until 2026-10-07 the toolkit README advertised "Prize Pool: $2,800 (1st $1,500, 2nd $800, 3rd $500) + Rising Star Award". It was replaced by certificates, Best Innovative Solution and RoboPAD orals (havln-challenge commit 4a793d6 and 719a80c).

## 7. Implications

1. Treat the challenge CMA replay (val_unseen 12.95) as the official floor and HCSG/BEVBert (about 19–23 Score-equivalent) as the published literature ceiling. Any credible compliant agent at SR 0.35–0.5 with near-zero wall contact (Score 35–50) would very likely win.
2. Because the scorer counts every contact step, a collision-free controller (inflated-clearance local planning, stop-before-contact, no sliding) is worth more than anything human-specific. Under the Oct-14 rules this has to come from egocentric depth plus GPS/compass, not the navmesh, at inference time.
3. Most agents reported in the paper used panoramic 12-view rigs (BEVBert/ETPNav), which the Oct-14 clarification bans. Re-implementing them under the single-forward-camera + rotate-to-scan rule will lower their numbers further, so the literature numbers overstate what "standard" methods can reach in this challenge.
4. The CR denominator βL means CR rises even when collisions happen in non-human-influenced episodes. A CR above 1 makes Social negative, so wall contact is doubly penalized.
5. The test `collision_num` allowances are public. 237 test episodes tolerate 1–3 contact steps without penalty. Use this only as a safety margin, never as a plan.
6. Run-to-run noise in the official scorer is about ±1 Score for a collision-heavy agent, from wall-clock human animation. Agents with large clearance margins are insensitive to it.
7. For "Best Innovative Solution" and the technical report, position the method in the organizers' lineage:
   - human-trajectory and world-model anticipation (the organizers' UniWM/LCVN line);
   - socially compliant distance (the 1 m personal space from HA-VLN 1.0);
   - comparisons against HA-VLN-CMA, HA-VLN-VL, BEVBert, ETPNav and HCSG on val_unseen with the same metrics.

## 8. Recommendations

- **Fix the CR denominator now** in `/home/user/open-data-eval/competitions/roboworld2026-track2/havln_tools/score.py` (`HUMAN_INFLUENCED` → train 9,204, val_seen 682, val_unseen 1,593, test 2,859) and in `00-competition-facts.md`. Re-check that the baseline recomputes CR consistently from per-episode outputs.
- Mirror `metric.py` exactly in all local evaluation: all-contact count, minus `collision_num`, max(0,·); SR requires TCR_ep == 0; CR over βL. Also log a human-only ≤1 m proximity count as a secondary diagnostic, in case organizers change semantics (low probability, since the image is digest-pinned).
- Use the paper-standard comparison set for the technical report: CMA (released ckpt), HA-VLN-VL, BEVBert, ETPNav, HCSG (as reported), plus NaVid/NaVILA zero-shot if cheap.
- Expect test ≈ val_unseen difficulty. Calibrate on val_unseen with several replays per configuration to average out wall-clock noise.
- Monitor HCSG's code release and arXiv for any HA-VLN Track 2 tech reports. HCSG-level teams (val unseen SR 0.24) are the visible competition.
- When search budget is available, re-run targeted WebSearches for the v5 Table 1 test-split rows (BEVBert/ETPNav/NaVid/NaVILA) and the real-world table.

## 9. Open questions

- Exact v5 Table 1 rows for BEVBert/ETPNav/NaVid/NaVILA (retrained/zero-shot) on val seen, val unseen and **test**. The arXiv block and exhausted search budget prevented this.
- Did the paper's CE TCR use Habitat contact (as in `metric.py`) or a 1 m proximity count (as the text says)? The CMA-DA TCR of 17–27 resembles the contact-count scale; BEVBert's 4.7 is plausible either way.
- Is the released `ckpt.39.pth` the paper's CMA* or CMA-DA? Val_seen SR 0.165–0.180 matches both CMA-DA (0.17) and the CMA* extraction (0.17).
- Are the trainer-reported CR values (0.638/0.689) β-normalized? The trainer code averages over all episodes.
- Provenance of the LAW-VLNCE / DUET / GridMM HA-VLN-CE rows.
- Results and participants of the Aug 2025 internal competition.
- Whether Phase 2 uses β_test = 1−549/3408 (βL = 2,859) as `metric.py` implies.

## 10. Sources

Local (all verified by reading):
- `EXT/track2/README.md` (L165-209, L183-188)
- `EXT/HA-VLN/README.md` (L46-50, L143-148), full git history (219 commits, incl. f1ebc41, f4d66a8, 09b5234)
- `EXT/HA-VLN/HASimulator/metric.py` L12-17; `EXT/HA-VLN/HASimulator/measures.py` L159-180; `EXT/HA-VLN/HASimulator/environments.py` L137-139
- `EXT/HA-VLN/agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py` L267, L473-481
- `EXT/HA-VLN/Data/HA-R2R-tools/collision_num_*.json`; `EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`
- `EXT/HA-VLN/demo/figs/*.png`
- `EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/{eval.py,env.py,data/*.json}`
- `EXT/havln-challenge` git history (8e36fa7, ec8f682, 5ad4380, 4a793d6, 719a80c)
- `EXT/havln2/HASimulator/README.md` §4, `EXT/havln2/agent/README.md` L95-100
- `EXT/jostar-track2` branch `bohan/clarification-Oct14`
- `EXT/roboworld2026.github.io/{track2.html L80-82,L120-133,L188-190; leaderboard.html}`
- `EXT/a10/UWMILab_HA-VLN-webpage/src/pages/index.astro`
- `EXT/a10/JostarXiong_havln2-docs/docs/api/{evaluation_metrics.md,collision_checks.md}`
- `EXT/a10/lpercc_HA3D_simulator/HA3DSim.py` L174-180
- `EXT/a10/HaoxuanXU1024_HCSG/{README.md,index.html,assets/paper/HCSG.pdf}` → `SP/hcsg.txt`
- `EXT/a10/k1000dai_vlaleaderboard` commit 10a7c98
- `EXT/a10/F1y1113_f1y1113.github.io/assets/documents/Yifei_Dong_CV.pdf`
- `/home/user/open-data-eval/competitions/roboworld2026-track2/{00-competition-facts.md,havln_tools/score.py}` (read-only)

Web (via WebSearch summaries only):
- https://arxiv.org/abs/2503.14229
- https://arxiv.org/html/2503.14229v1
- https://arxiv.org/html/2503.14229v2
- https://arxiv.org/html/2503.14229v3
- https://arxiv.org/html/2503.14229
- https://arxiv.org/pdf/2503.14229
- https://www.alphaxiv.org/abs/2503.14229
- https://www.researchgate.net/publication/398407476
- https://arxiv.org/abs/2605.13321 (HCSG)
- https://www.sota2.com/research/sota/vision-and-language-navigation-on-ha-vlnce-val-seen
- https://github.com/k1000dai/vlaleaderboard/pull/34
- https://arxiv.org/abs/2406.19236 (HA-VLN 1.0)
- https://proceedings.neurips.cc/paper_files/paper/2024/file/d8087deaf34bb07ddd41c65f8a9fe9b5-Paper-Datasets_and_Benchmarks_Track.pdf
