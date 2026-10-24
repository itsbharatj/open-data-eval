# LLM/VLM zero-shot VLN planners (2023-Oct 2026) and the 'frontier VLM as judge over candidate trajectories' plan for HA-VLN Track 2

**topic_id:** `B3-llm-vlm-zero-shot-planners`  |  date 2026-10-24  |  author: research agent B3

> Method note: about 45 WebSearch (extended) queries, then the shared per-turn WebSearch budget (200 for all agents) ran out mid-run. After that, evidence came from cloned GitHub repos (READMEs, configs, prompt code), the local `papers.db` of ser666/awesome-zero-shot-navigation (870 abstracts, updated 2026-10-19), and computations on the HA-VLN data in `ext/HA-VLN`. Items marked *(search summary)* rest on WebSearch page summaries only. Cloned repos are in `ext/B3/`.

## Summary

Zero-shot LLM/VLM navigators went from weak to near-human in about 30 months. On DISCRETE R2R val-unseen: NavGPT (GPT-4, text-only scene descriptions) 34 SR, DiscussNav (GPT-4 multi-expert, 5-sample self-consistency) 43, MapGPT (GPT-4V, text topological map + per-node images) 43.7 full split / 47.7 on its 72-scene, 216-case subset (GPT-4o 46.3), NavCoT (fine-tuned LLaMA2-7B) 40, MSNav (GPT-4o) about 46-51 on the subset. On CONTINUOUS R2R-CE, mostly on 100-episode subsets: InstructNav 31, Open-Nav 19, CA-Nav 25.3, SmartWay 29, Three-Step Nav 34. Mid-2026 agent harnesses reached about 61 (HAM-VLN, Uni-LaViRA, HarnessVLN). Sept-Oct 2026 frontier models jumped again: NavProbe (GPT-5.5 xhigh) 71.7; GPT-6-Astra on monocular RGB only 76-81 on R2R-CE-100. NavGPT-3 is the only full-split result: on all 1,839 val-unseen episodes in Habitat-Sim 0.1.7, with the challenge's own 0.25 m / 15 degree action space and agent radius 0.1 m, it scores 76.94 SR with its public 8B VLA alone, 79.01 with a Claude Opus 5 planner and 81.51 with a GPT-6-Astra planner. On RxR-CE it reaches 90.43, against 90.4 for humans. Neither B1 nor B2 records any of these 2026 frontier results. Planner prompts and reported failures agree on what is still hard: deciding where to stop (endpoint vs. landmark; overshoot and undershoot), picking the right instance when rooms repeat, keeping progress through long multi-clause instructions, and left/right/heading grounding. When the model is asked to COMPARE alternatives instead of giving absolute answers, accuracy rises sharply. In C2Nav, switching to absolute questions cuts SR from 31 to as low as 12. With the same interface, GPT-5.5 beats Qwen3-VL-8B by 13 SR points (44 vs 31). Ranking candidate trajectories is an established idea: speaker pragmatic reranking (35.5 to 54.6 val-unseen), VLN-BERT/Airbert path selection (73/78 test SR), Pathdreamer look-ahead ranking (40.6 to 50.4), TRAVEL (known map, top-k last-landmark retrieval, shortest-path hypotheses, VLM alignment), and the NavGPT-3 planner, whose whole job is to choose the endpoint among visited nodes. That planner adds 2-4.6 SR on top of an 8B VLA. I found no paper named 'InstructVerifier'. Computed on the public HA-VLN 1.0 discrete val data, the offline problem has strong structure: 99.3% of reference paths are exact nav-graph shortest paths with 4-6 edges and 5-22 m length, so the task reduces to picking a goal among a median of 20 candidates (p90 40). About 4 candidates lie within 3 m of the true goal. A random candidate scores 22.9%, and an instruction-blind 'max-coverage' stop scores 41.6%. Each test trajectory also carries 6 instructions (3 HA-R2R plus 3 recoverable original R2R, per A1). Recommendation: use frontier VLMs as comparative top-K judges over geometry-annotated renders, on top of trained proposers/scorers (ScaleVLN/SRDF follower and speaker likelihoods, a fine-tuned Qwen3-VL listwise ranker, NavGPT-3 stop votes). Fuse them with a calibrator fitted on val_unseen, then pick a Bayes-optimal stop point. My inferred target is 85-92% goal-within-3 m, i.e. Score about 81-87 with zero collisions, for about $1-2k per full test pass with Claude Opus 5.5 under batch pricing.

## 1. Survey: LLM/VLM zero-shot (and LLM-based) VLN planners

### 1a. Discrete R2R (MP3D nav-graph), val-unseen

| Method | Year/venue | Backbone | Observation input | Eval set | SR | SPL | Notes |
|---|---|---|---|---|---|---|---|
| NavGPT | AAAI'24 | GPT-4 (GPT-3.5 summariser) | TEXT: BLIP-2 captions of 8 dirs x 3 elev + detected objects with distances + navigable directions (deg, m) | full val-unseen (11 scenes, 783 traj) | 34 | 29 | TL 11.45, NE 6.46, OSR 42; ReAct loop with viewpoint-ID tool |
| DiscussNav | ICRA'24 | GPT-4 + InstructBLIP + RAM | text from per-direction perception experts | val-unseen | 43 | 40 | OSR 61; 5-sample self-consistency, fusion, 'decision testing'; fixed 5/7-step budget |
| MapGPT | ACL'24 | GPT-4V / GPT-4o | IMAGES per place + text topological map + planning memory | 72-scene/216 subset; full split | 47.7 (4V) / 46.3 (4o); ~43.7 full | 38.1 / 37.8 | no STOP before step 3; 15-step cap; 'low' image detail |
| NavCoT | TPAMI'25 | LLaMA2-7B PEFT (trained) | text captions + imagination | val-unseen | ~40 | ~37 | +2.4 SR over GPT-4 NavGPT |
| MSNav | 2025/26 | GPT-4o + fine-tuned Qwen3-4B | text + topological memory with pruning | 72-scene subset | 45.7-50.9 | 32.8-42.6 | versions disagree; GPT-4o re-runs: NavGPT 36.1, DiscussNav 37.5 |
| NavGPT-2 (reference, trained) | ECCV'24 | FlanT5-XXL + InstructBLIP | images (EVA-CLIP-g) | val-unseen / test | 73.8 / 71.8 | 61.1 / 60.3 | trained LLM backbone, from B1 |
| VerNav (trained verifier) | 2026 | Qwen2.5-3B | text | val-unseen | 37.25-39.63 | 34.1-34.4 | >10x lower decision latency |

### 1b. Continuous R2R-CE (Habitat), val-unseen

| Method | Date | Backbone | Input | Eval set | SR | SPL | Notes |
|---|---|---|---|---|---|---|---|
| InstructNav | CoRL'24 | GPT-4 + GPT-4V | RGB-D, value maps | 100-ep | 31.0 | 24.0 | first zero-shot R2R-CE |
| Open-Nav | ICRA'25 | open-source LLMs (Llama3.1/Qwen2 etc.) or GPT-4o | panorama + waypoint predictor + text | OpenNav-100 | 19.0 (open); ~23 (GPT-4o, search summary) | 16.1 | defines OpenNav-100 subset |
| CA-Nav | 2024/25 | GPT-4 family | constraint-aware | 100-ep | 25.3 | 10.8 |  |
| SmartWay | IROS'25 | MLLM (GPT-4o) | pano + improved waypoint predictor, backtracking | 100-ep | 29.0 | 22.5 |  |
| Three-Step Nav | 2026-04 | gpt-4o/gpt-5/qwen3-vl | look forward/now/backward | 100-ep | 34.0 | 29.1 |  |
| HSGM | CVPR'26 | GPT-5 (or Qwen3.6-27B) | semantic-geometric top-down map | val-unseen | 47.9 | 32.8 | from B2 |
| C2Nav | 2026-09 | Qwen3-VL-8B vs GPT-5.5 | comparative choices over vetted views | OpenNav-100 | 31.0 vs 44.0 | 16.7 vs 29.0 | absolute-question ablation: 12/28/21 |
| Uni-LaViRA | 2026-05 | gemini-3.5-flash + qwen3.5-27b | language action + pixel target; TODO memory | 100-ep | 60.7 | - | second-chance backtrack |
| HarnessVLN | 2026-09 | MLLM agent harness | tools + spatiotemporal graph | - | 60.8 | - |  |
| HAM-VLN | 2026-07 | MLLM | depth-grounded world graph; -67% tokens | 100-ep x3 runs | 61.0+/-1.7 | 48.1 | OSR 78.7 |
| SpatialAnt | 2026-03 | VLM + scene reconstruction | active reconstruction | - | 66 | - |  |
| NavProbe | 2026-09 | gpt-5.5 (xhigh) | subgoal agenda + evidence retrieval | 100-ep | 71.7 | 55.8 | RxR-CE 55.3 |
| GPT-6-Astra (Codex harness) | 2026-09 | GPT-6-Astra | monocular RGB 512 px, no waypoint predictor | R2R-CE-100 | 76.0 (medium) / 79.0-81.3 (ultra) | 65.6-67.9 / 71.5 | v1/v2 disagree |
| GPT-6-Astra (direct API workflow) | 2026-09 | GPT-6-Astra | selected obs + feedback | 50 of OpenNav-100 | 52.0 | 48.9 | 36% STOP-success; +16% in range but never stopped |
| NavGPT VLA 8B (trained) | 2026-10 | Qwen3-VL-8B VLA, 19.28M samples | multi-view RGB history | FULL 1,839 | 76.94 | 70.61 | Habitat-Sim 0.1.7; public weights |
| NavGPT-3 + Claude Opus 5 | 2026-10 | Opus 5 planner (high effort) + 8B VLA | 8 tools incl. map, node memory | FULL 1,839 | 79.01 | 70.16 | RxR-CE 84.80; $5/episode cap |
| NavGPT-3 + GPT-6-Astra | 2026-10 | Astra planner + 8B VLA | same | FULL 1,839 | 81.51 | 70.42 | RxR-CE 90.43 (human 90.4) |

**Input representations, observed trend.** Text-only scene descriptions (NavGPT, DiscussNav) are at about 34-43 SR. Raw images plus a text map (MapGPT) were about 44-48 SR in the GPT-4V era. 2026 frontier agents perform best when geometry is computed outside the model and painted or written onto the inputs (NavGPT-3 panoramas with bearing rulers, walkable distances, MAP-UP; MapGPT's turn words; AgenticNav/O2C-Nav markers on RGB), and the model is asked to choose among vetted options (C2Nav). Long raw histories hurt; compact memory helps (HAM-VLN -67% tokens, MSNav node pruning).

### 1c. Failure modes (consolidated)

- **Stopping** is the dominant failure. Some agents stop too early (MapGPT disables STOP for 3 steps). Some never stop: 16% of GPT-6-Astra workflow episodes were in range at the step limit without stopping. Some walk past the endpoint toward the named object, which is why NavGPT-3 says the endpoint is a position on the route.
- **Wrong instance**: buildings repeat bedrooms, doors and halls. NavGPT-3 adds a 'COUNT WHAT THE INSTRUCTION COUNTS' block, triggered only when the last clause reuses a repeatable landmark word.
- **Progress tracking over long instructions**: sub-instruction decomposition and TODO lists (MapGPT 'New Planning', Three-Step Nav, Uni-LaViRA TDM). This matters more for 112-word HA-R2R instructions.
- **Spatial grounding**: left/right/heading, doors, room transitions (Spatial-VLN, HSGM). Fix by computing geometry outside the model and stating it in words or labels.
- **Loops and revisits** ('the single most common way this task is failed' per NavGPT-3). This does not apply offline, where we pick paths and do not explore.
- **Context and cost blow-up** with image histories: HAM-VLN, SFCo-Nav and O2C-Nav are all efficiency papers. The NavGPT-3 Claude run caps spend at $5 per episode.
- **Benchmark noise**: 100-episode subsets give about +/-4.6 pt standard error, and versions disagree (GPT-6-Astra 79.0 vs 81.3; MSNav 45.7 vs 50.9).

## 2. Prior work closest to 'LLM/VLM as judge over candidate trajectories'

| Work | What is ranked | Scorer | Gain / result |
|---|---|---|---|
| Speaker-Follower pragmatic inference (NeurIPS'18) | 40 beam candidates (full routes) | speaker p(instr|route) x follower | val-unseen 35.5 to 54.6; test 53.5 |
| VLN-BERT (ECCV'20) | beam-search candidate paths ('path selection', pre-explored) | instruction vs panorama-sequence compatibility transformer | val-unseen 59.26 (30.52 w/o pretraining); test SR 73 / NE 3.09 |
| Airbert (ICCV'21) | same setting | in-domain pretrained compatibility + shuffle loss | test SR 78 / NE 2.58 |
| Pathdreamer (ICCV'21) | 1-3-step look-ahead candidates | compatibility model on dreamed observations | 40.6 to 50.4 SR (GT look-ahead 59) |
| FAST / Tactical Rewind (CVPR'19) | frontier candidates | trained goal reranker | beam-era gains |
| LM-Nav (CoRL'22) | nodes of a pre-built topological graph | GPT-3 landmark parse + CLIP node match + graph search | outdoor robot; full map known |
| TRAVEL (CVPR'25 WS) | k shortest-path hypotheses to top-k last-landmark locations (known map) | DP alignment of landmark sequence to panoramas using VLM match scores (GPT-4o 1-5 rating per one summary) | beats VLMaps on R2R-Habitat; nDTW>0.87 success; numbers not retrieved |
| NavGPT-3 planner (Oct'26) | nodes/waypoints along the VLA's driven route | Claude Opus 5 / GPT-6-Astra comparative endpoint choice | +2.07 / +4.57 SR on full R2R-CE over the VLA; RxR +2.4 / +8.0 |
| C2Nav (Sep'26) | physically vetted candidate views, instruction-leg hypotheses, arrival | VLM ordinal comparison | comparative >> absolute (31 vs 12-28 SR) |
| VerNav / DV-VLN (2026) | candidate actions per step | yes/no verifier; TFV + masked-entity verification | competitive SR at >10x lower latency (VerNav) |
| Slow Brain, Fast Planner (2026, urban) | K candidate trajectories drawn on image | VLM index choice | social/goal compliance |

No work titled 'InstructVerifier' was found. Instruction-trajectory compatibility as an evaluation metric goes back to Zhao/Fried et al. (EACL 2021).

## 3. Structure of OUR offline problem (computed this session)

Computed on HA-VLN 1.0 discrete val (R2R paths; HA-R2R test paths are a subset of R2R test paths per A1). Distances are graph-geodesic over MP3D connectivity.

- 99.3% of reference paths (1,115/1,123) are exact shortest paths; 99.2% have 4-6 edges; length 5.04-22.1 m (mean 9.69). **Choosing the goal fixes the path.**
- Candidate goals per start (4-6-edge shortest path, at least 5 m): median 20, mean 23.1, p90 40; the true goal is in the set 98.9% of the time; about 4 candidates within 3 m of the goal.
- Instruction-blind baselines: random candidate 22.9% SR; **max-coverage candidate 41.6% SR** (val_unseen, 772 episodes). A posterior over candidates should be turned into a stop point by maximising expected success.
- Human mentions (673 in 783 paths): Around 65%, Obstacle 21%, Beginning 7%, End 6%. 17.5% are on the path, 59.9% within 3 m of a path node, 24.5% within 3 m of the goal. Use them as soft path constraints.
- HA-VLN 1.0 text annotations cover all 18 test scans (70 humans). On public scans, 83.6% of 1.0 human viewpoints also hold a 2.0 human (68% identical activity text). This gives partial test-scan human ground truth.
- Per A1: 3,408 test episodes = 1,136 trajectories x 3 HA-R2R instructions, plus 3 original R2R test instructions recoverable by matching, so **6 instructions per decision**.

## 4. Recommended judge design (inference, built from the evidence above)

**Pipeline:** candidates (graph) -> cheap calibrated scorers (follower LL, speaker LL, fine-tuned Qwen3-VL ranker, NavGPT-3 stop votes) -> top-K (4-6) -> frontier comparative judge with permutation self-consistency -> calibrated fusion on val_unseen -> Bayes-optimal stop point -> collision-free planner.

**Judge prompt skeleton (for Claude Opus 5.5 / Fable 5.1, structured output, no temperature):**

```text
SYSTEM: You judge where a route described by several independent instructions ENDS in a known building.
You are given K candidate routes (A..K). Each route is the shortest walk from the same start to a different endpoint.
For each route you see: forward photos at every waypoint facing the direction of travel (labels burned in: step, turn,
metres walked, floor change), four photos at the endpoint, a top-down map with the route drawn, and per-waypoint text
(room label, salient objects, people and their activity).
Rules: Execute the clauses of each instruction IN ORDER against each route. A route is right only if every clause comes true
in order. The endpoint is a position on the route from which the last-named landmark is near (1-2 m), not the landmark
itself. Buildings repeat rooms and doors: if the last clause reuses a landmark word, count instances in order. Not seeing a
small landmark is not evidence against a route. People are mentioned as context near the route, rarely as the goal.
The original instructions (1-3) are the most literal; rewritten ones (4-6) add human-activity context.
WHERE THE ROUTE ENDS DECIDES EVERYTHING: compare the candidates' endpoints against the last clause of every instruction.
USER: <instructions 1-6> <candidate blocks in a permuted order>
OUTPUT (JSON schema): {clause_alignment: {route: [...]}, ranking: [letters best->worst], best: letter, confidence: low|med|high}
```

**Calibration and aggregation:** (i) comparative over absolute (C2Nav); (ii) 4-8 candidate-order permutations aggregated by Borda count, because position bias is a known LLM-judge failure; (iii) diversity from instruction subsets (orig-only / HA-only / all), rendering variants and models rather than temperature, which Claude rejects since 2026-10-21; (iv) logprob-based likelihoods only from local open models; (v) a fused calibrator fitted on val_unseen 613 trajectories; (vi) entropy-gated escalation to Fable 5.1 or other frontier models; (vii) Bayes-optimal stop.

**Expected accuracy (inference).** Anchors: trained discrete SOTA 80-85 SR single-run (B1); path-ranking 73-78 (2020-21 models); frontier egocentric 79-81.5 (NavGPT-3, Astra); human R2R 86 / RxR 90.4. Our setting adds full observability, free candidate enumeration, 6 instructions and a Bayes stop, so 85-92% within 3 m is the target band. A frontier judge alone on top-K is likely +2-5 SR over the best fused open/trained scorers (NavGPT-3 planner analogue) and about +10-15 SR over a zero-shot 7-8B judge (C2Nav analogue). A fine-tuned 8B ranker should be competitive with zero-shot frontier models. With zero collisions, Score is about 75 at SR 0.80, 83 at 0.88 and 86.5 at 0.92.

**Cost model (inference; Opus 5.5 $4/$20 per MTok, batch -50%).** Shortlist stage: 25 candidates as text in one listwise call, 4 permutations, about 32k in / 8k out, about $0.29. Visual stage: top-6 x (about 7 forward views + 4 end views at 512 px, about 334 tokens each) plus text, about 23k in / 4k out per call, 8 calls (4 permutations x 2 instruction groupings), about $1.38. Total about $1.7 per trajectory standard, about $0.85 batch. Test pass (1,136 trajectories): about $1.0-1.9k. Val_unseen pass (613): about $0.5-1.0k. Fable 5.1 costs about 2.5x. For comparison, online NavGPT-3-style Claude navigation is capped at $5 per episode (about $5.7k per test pass at one run per trajectory).

## 5. Facts (verified) with confidence

1. **NavGPT (AAAI 2024, GPT-4, purely text): at each step GPT-4 receives LLM-summarised text of BLIP-2 captions plus detected objects with distances, navigation history, and navigable viewpoints with orientations in degrees and distances within 3 m. It outputs a viewpoint ID through a LangChain ReAct loop. R2R val-unseen: TL 11.45, NE 6.46, OSR 42, SR 34, SPL 29.**
   - Evidence: NavGPT prompts and observation summariser in ext/B3/NavGPT/nav_src/prompt/planner_prompt.py (VLN_GPT4_PROMPT) and nav_src/scripts/obs_summarizer.py (gpt-3.5-turbo summary). Numbers come from the DiscussNav/NavGPT-2 comparison tables as returned by WebSearch: 'NavGPT (GPT-4) ... 11.45 6.46 42 34 29'.
   - Confidence: high (method), medium-high (numbers)

2. **DiscussNav (ICRA 2024, GPT-4 with InstructBLIP and RAM experts): R2R val-unseen SR 43, SPL 40, OSR 61. It is very call-heavy: 12 per-direction perception summaries per step, 5 sampled decision CoTs (num_predictions=5, up to 5 retries), a thought-fusion call per distinct prediction, and a decision-testing call. The step budget is fixed at 5 or 7 by the number of parsed actions, which is an implicit R2R path-length prior.**
   - Evidence: ext/B3/DiscussNav/DiscussNav.py L293-295 (num_predictions=5, num_retry=5), L322-343 (sampling), L360-400 (fusion/testing), L506 (step_length = 5 if <=5 actions else 7). Numbers come from a WebSearch summary of the DiscussNav table ('DiscussNav (Ours) ... 61 ... 43 ... 40').
   - Confidence: high (code), medium (numbers)

3. **MapGPT (ACL 2024, GPT-4V) gives a text topological map ('Place i is connected with Places ...'), the trajectory, unvisited 'supplementary' places, per-place images, and multi-step 'New Planning'. Geometry is converted to words (turn left/right/around, go up/down), and STOP is forbidden for the first 3 steps (stop_after 3) with a 15-step cap. On its 72-scene, 216-case val-unseen subset: GPT-4V NE 5.62, OSR 57.9, SR 47.7, SPL 38.1; GPT-4o NE 5.11, OSR 56.9, SR 46.3, SPL 37.8. On the full val-unseen split the paper reports about 43.7 SR.**
   - Evidence: ext/B3/MapGPT/README.md (table and config), ext/B3/MapGPT/GPT/one_stage_prompt_manager.py (get_action_concept, make_map_prompt, stop_after logic), ext/B3/MapGPT/GPT/api.py (image detail 'low', temperature 0). The full-split 43.7 is from B1 fact 18.
   - Confidence: high (subset numbers and code), medium (full-split 43.7)

4. **The NavCoT 'world-model imagination then match then act' recipe, with a parameter-efficiently fine-tuned LLaMA2-7B, reaches about 40 SR / 37 SPL on R2R val-unseen, about 2.4 SR above GPT-4 NavGPT. MSNav (GPT-4o, plus a Qwen3-4B fine-tuned for object/space extraction that beats GPT-4o at F1 0.316 vs 0.270) reports SR 45.7-50.9 on the 72-scene subset (paper versions disagree). In MSNav's own GPT-4o re-run on that subset, NavGPT scores 36.1 SR and DiscussNav 37.5 SR.**
   - Evidence: NavCoT abstract and README (ext/B3/NavCoT/README.md); third-party table row 'NavCoT ... 40 37'. MSNav abstract in the local paper DB (ext/B3/awesome-zero-shot-navigation/data/papers.db) and WebSearch summaries of arXiv 2508.16654.
   - Confidence: medium

5. **Zero-shot R2R-CE val-unseen results, mostly on 100-episode subsets (HAM-VLN comparison table): InstructNav NE 6.89 / OSR 47 / SR 31 / SPL 24; Open-Nav 6.70 / 23 / 19 / 16.1; CA-Nav 7.58 / 48 / 25.3 / 10.8; SmartWay 7.01 / 51 / 29 / 22.5; GC-VLN 33.6 SR; LaViRA 38.3; Three-Step Nav 34.0; HiMemVLN 30.0; HAM-VLN 61.0 +/- 1.7 (3 runs). Other 2026 results: Uni-LaViRA 60.7, HarnessVLN 60.8, SpatialAnt 66, SparseNav 42.8, VLN-Zero 42.4, HSGM (GPT-5) 47.9, and the GPT-5-mini obstacle-map method 41.**
   - Evidence: ext/B3/an1iu_HAM-VLN/index.html (results table transcribed from the paper; 'All results are averaged over three runs on fixed 100-episode val-unseen subsets'). Abstracts in papers.db for 2605.27582, 2609.15195, 2603.26837, 2609.26408, 2509.18592, 2509.20499; HSGM from B2.
   - Confidence: high (HAM-VLN table and abstracts), medium (cross-protocol comparability)

6. **September-October 2026 frontier zero-shot results. NavProbe uses gpt-5.5 at xhigh reasoning effort for its executive and skill selector, and reaches 71.7 SR / 55.8 SPL on R2R-CE and 55.3 SR on RxR-CE (100-episode lists). GPT-6-Astra in a minimal Codex harness with monocular RGB (512x512), deciding itself when to observe, move and stop, reaches 75.7-76.0 SR (medium effort) and 79.0-81.3 SR (ultra effort) on R2R-CE-100 (v1 vs v2), with SPL 65.6-67.9 / 71.5. A separate direct-API GPT-6-Astra workflow on 50 episodes gets SR 52.0, SPL 48.9, nDTW 70.8.**
   - Evidence: ext/B3/NavProbe/README.md (model gpt-5.5 xhigh; 100-episode Uni-LaViRA lists) and navprobe/config/navprobe.yaml L95-96. arXiv 2609.29861 and 2609.20116 abstracts in papers.db, plus WebSearch summaries of both versions.
   - Confidence: high (NavProbe, workflow paper), medium (GPT-6-Astra numbers; versions disagree)

7. **NavGPT-3 (arXiv 2610.10787, Oct 2026) is the strongest FULL-split result and runs in the challenge's simulator version. Setup: Habitat-Sim 0.1.7, 0.25 m forward, 15 degree turns, allow_sliding, agent height 1.5 m, radius 0.1 m, 500-step cap, all 1,839 R2R-CE val-unseen episodes. R2R-CE (NE / OSR / SR / SPL): NavGPT VLA 4B 3.32 / 81.67 / 74.33 / 68.13; VLA 8B 2.97 / 82.49 / 76.94 / 70.61; with Claude Opus 5 planner 2.77 / 84.07 / 79.01 / 70.16; with GPT-6-Astra planner 2.18 / 86.99 / 81.51 / 70.42. RxR-CE SR: 81.41 / 82.39 / 84.80 / 90.43 (human 90.4). Weights are on HF (Metacognition-AI/NavGPT3-4B, -8B; Qwen3-VL based), code is Apache-2.0, there are Claude Agent SDK and Codex planner runtimes, the Claude per-episode budget cap is $5, and an RxR episode takes 1 min 22 s.**
   - Evidence: ext/B3/metacognitionai_NavGPT-3/README.md (main results table, Planner sign-in, Habitat 0.1.7); configs/experiments/vln/navgpt3_opus_r2r.yaml (claude-opus-5, effort high, max_budget_usd 5.0, step 0.25, turn 15, allow_sliding true); navgpt/environment/r2r.py L72-73, L877-878 (hfov 90, camera 1.25 m, agent_height 1.5, agent_radius 0.1). papers.db abstract for 2610.10787.
   - Confidence: high

8. **The NavGPT-3 planner works as a judge over candidates, which is our use case. Its prompt says the VLA 'drives better than you'; the planner's only scored job is to decide 'where along the route it drove the instruction actually ends', choosing among nodes the robot stood on. The authors note that most failures end FURTHER from the goal than a point already visited. With a judge, the OSR-SR gap stays about 5.5 points (VLA 82.49 / 76.94; Astra 86.99 / 81.51). Even frontier stop selection therefore loses about 5 points to mis-ranking.**
   - Evidence: ext/B3/metacognitionai_NavGPT-3/navgpt/planner/prompts.py VLA_MEMORY_SYSTEM_PROMPT (comment block above it, 'HOW THE WORK DIVIDES', steps 1-8); README results table.
   - Confidence: high

9. **Comparative ('ordinal') questions beat cardinal/absolute ones by a large margin, and a frontier model adds about 13 SR over an 8B open model under the same interface. In C2Nav (training-free, OpenNav R2R-CE-100), Qwen3-VL-8B-Instruct gets OSR 41 / SR 31 / SPL 16.7 and GPT-5.5 gets 54 / 44 / 29. Replacing the comparative answer form with cardinal/absolute questions in the spatial, transition and terminal slots cuts SR to 12, 28 and 21.**
   - Evidence: papers.db abstract for arXiv 2609.15142 (C2Nav: Compare Before You Commit).
   - Confidence: high (as reported; single 100-episode subset)

10. **Effort and model scaling on navigation. GPT-6-Astra ultra vs medium effort: about +5.6 SR (81.3 vs 75.7) on R2R-CE-100. In NVIDIA's 'Astranomy' robot-policy study, xhigh vs medium gives 74.5 vs 72.7 at 2.6x latency and 2.2x tokens. MapGPT with GPT-4o vs GPT-4V: -1.4 SR (46.3 vs 47.7). NavGPT-3 planner, GPT-6-Astra vs Claude Opus 5: +2.5 SR on R2R-CE and +5.6 on RxR-CE.**
   - Evidence: WebSearch summaries (aiagentstore/NVIDIA Astranomy page; arXiv 2609.29861v2), MapGPT README, NavGPT-3 README.
   - Confidence: medium (Astra/Astranomy), high (MapGPT, NavGPT-3)

11. **Documented failure modes of LLM/VLM navigators: (1) Stopping. Some episodes are early stops, which is why MapGPT forbids STOP for 3 steps. Others never stop: 16% of GPT-6-Astra workflow episodes were within 3 m at the step limit without STOP, versus 36% that succeeded with STOP. Others overshoot the endpoint; NavGPT-3 says 'the endpoint is a POSITION ON THE ROUTE, not the object the last clause names'. (2) Wrong instance among repeated rooms or doors; NavGPT-3 adds a gated 'COUNT WHAT THE INSTRUCTION COUNTS' block. (3) Losing progress over long multi-clause instructions, which MapGPT, Three-Step Nav and Uni-LaViRA's TODO-list memory address. (4) Spatial/left-right grounding: Spatial-VLN reports door interaction, multi-room transitions and ambiguous instructions as the top failure classes, and HSGM describes a 'semantic-geometric gap'. (5) Loops and revisits ('Going in circles is the single most common way this task is failed'). (6) Context overload from long visual histories: MSNav prunes nodes, and HAM-VLN uses 67% fewer tokens.**
   - Evidence: ext/B3/metacognitionai_NavGPT-3/navgpt/planner/prompts.py (_MOVE_RULES, _PLACE_ENDGAME, _COUNTING_BLOCK, WHAT IS AND IS NOT EVIDENCE). Abstracts in papers.db: 2609.20116, 2604.26946, 2605.27582, 2601.12766, 2606.00095, 2607.29600. MapGPT stop_after in one_stage_prompt_manager.py.
   - Confidence: high

12. **Path/trajectory ranking with learned compatibility or speaker models is well established and gives large gains when candidate generation is free. Speaker-Follower pragmatic inference (beam 40, state-factored search): val-unseen 54.6 vs 35.5 greedy, 53.5 on test. VLN-BERT path selection (scores instruction vs. a panorama sequence) on val-unseen: 30.52 without pretraining, 59.26 for the full model; on test in the beam setting, NE 3.09 and SR 73. Airbert test: NE 2.58, SR 78. Pathdreamer ranks beam candidates with a compatibility model: 40.6 to 50.4 SR at a 3-step horizon, and 59 with ground-truth look-ahead.**
   - Evidence: ext/B3/ronghanghu_speaker_follower/README.md L131-169; ext/B3/arjunmajum_vln-bert/README.md L11-17 (val-unseen SR per pretraining stage); WebSearch summary of arXiv 2312.00151 test table ('VLN-BERT 3.09 73 0.01; AirBert 2.58 78 0.01'); WebSearch summary of Pathdreamer arXiv 2105.08756.
   - Confidence: high (repo numbers), medium (test-table numbers)

13. **TRAVEL (Rajabi and Kosecka, CVPR 2025 workshop) is the closest prior work to our offline plan. It assumes a known topological map (built from train episodes). An LLM extracts the ordered landmarks, the system retrieves the top-k locations of the LAST landmark, generates k BFS shortest-path hypotheses from start to each, and scores each panorama sequence against the landmark sequence by dynamic programming over VLM match scores. In one description GPT-4o rates paths 1-5. Success is defined as nDTW > 0.87, measured over 21 episodes per environment. The authors note that hypothesis quality caps what any VLM ranker can achieve. Its SR tables could not be retrieved here.**
   - Evidence: WebSearch summaries of arXiv 2502.07306 (abstract, HTML snippets).
   - Confidence: medium (method), low (GPT-4o 1-5 rating detail)

14. **Other verifier/rerank designs. VerNav: a batched yes/no-style verifier over executable actions plus an entropy-triggered generator; Qwen2.5-3B reaches SR 37.25 (VPO) and 39.63 (with RFT) on R2R val-unseen with more than 10x lower decision latency. DV-VLN: sample K=4 candidate actions, then rerank by True-False Verification plus Masked-Entity Verification. FAST: a frontier-aware search with a trained goal reranker. LM-Nav: GPT-3 landmark parsing, CLIP node grounding, and graph search over a pre-built topological map. 'Slow Brain, Fast Planner': a VLM picks among K candidate trajectories drawn as polylines on the image. No paper named 'InstructVerifier' was found.**
   - Evidence: papers.db abstract 2609.00920 plus WebSearch summary of its Table 3; WebSearch summary of DV-VLN (arXiv 2601.18492, repo PlumJun/DV-VLN); ext/B3/Kelym_FAST/README.md L87-113; LM-Nav WebSearch summary; arXiv 2606.20458 WebSearch summary.
   - Confidence: medium

15. **Using several instructions for the same path helps. LEO (multi-view learning across the 3 R2R instructions of a path) raised a greedy agent's SPL from 25.3 to 41.4.**
   - Evidence: papers.db abstract for arXiv 2003.00857.
   - Confidence: medium

16. **COMPUTED: R2R reference paths are exact nav-graph shortest paths, so goal choice determines the whole path. On HA-VLN 1.0 discrete val_seen+val_unseen (1,123 episodes over the MP3D connectivity graphs), 1,115 (99.3%) are exact Dijkstra shortest paths. Edge counts are 3/4/5/6 = 9/378/342/394 (99.2% have 4-6 edges), and geodesic length runs 5.04-22.1 m (mean 9.69).**
   - Evidence: Script run in this session over ext/HA-VLN/HASimulator/HA-DE/tasks/HA/data/HA_val_{seen,unseen}.json with HA-DE/connectivity/*_connectivity.json (included and unobstructed edges, Euclidean edge weights).
   - Confidence: high (for R2R-discrete paths; HA-R2R-CE test paths are a subset of R2R test paths per A1)

17. **COMPUTED: the candidate goal set per start, defined as nodes whose shortest path has 4-6 edges and is at least 5 m long, has median 20, mean 23.1 and p90 40 nodes, and contains the true goal in 98.9% of episodes. On average 4.0 candidates (median 4) lie within 3 m graph-geodesic of the true goal. Uniform random choice among candidates gives 22.9% SR. An instruction-BLIND 'max-coverage' choice (the candidate within 3 m of the most other candidates) gives 41.6% SR on val_unseen (772 episodes), far above the CMA baseline's 12.9.**
   - Evidence: Same script as above; graph shortest-path distance is used as a proxy for Habitat geodesic distance.
   - Confidence: high (as computed), medium (transfer to the Habitat geodesic success test)

18. **COMPUTED: human mentions are weak, route-adjacent location cues. In HA-VLN 1.0 val_unseen, 673 human mentions over 783 paths carry relation labels Around 440, Obstacle 141, Beginning 50 and End 42. Only 17.5% of mentioned human viewpoints lie on the path. Median distance to the nearest path node is 2.41 m (59.9% within 3 m), and median distance to the goal is 5.15 m (24.5% within 3 m).**
   - Evidence: Script over HA_val_unseen.json 'human' fields plus connectivity poses.
   - Confidence: high (HA-VLN 1.0); medium as a proxy for HA-R2R 2.0

19. **COMPUTED: HA-VLN 1.0 human text annotations (human_motion_text.json) cover all 18 test scans with 70 humans (2-7 per scan). On the 72 public scans, 254 of 304 (83.6%) 1.0 human viewpoints also host a HA-VLN 2.0 human (human_motion.json), and 207 of 304 (68%) have identical activity text. HA-VLN 2.0 has about 2.5x more humans (749 vs 304 on those scans).**
   - Evidence: Script over ext/HA-VLN/HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json and ext/HA-VLN/Data/Multi-Human-Annotations/human_motion.json (keys are viewpoint IDs with an optional suffix digit; category 'room:activity').
   - Confidence: high (counts); inference that the 1.0 test annotations are a subset of the 2.0 test placements: medium

20. **Claude API constraints that matter for a judge pipeline (cached 2026-10-06). Prices per MTok input/output: Opus 5.5 $4/$20, Fable 5.1 $10/$50, Opus 5 $5/$25, Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50. Batch is 50% off all tokens. Cache reads cost 0.05x input on Opus 5.5. Images cost about 1 token per 28x28-pixel patch, so 512x512 is about 334 tokens and 1280x720 about 1,200, up to 2576 px on the long edge (about 4,784 tokens). temperature/top_p/top_k return HTTP 400 on every model from 2026-10-21, so self-consistency must come from prompt or permutation diversity, not sampling temperature. Opus 5.5 effort defaults to 'medium' and should be set explicitly. Prefill is not supported; use structured outputs via output_config.format.**
   - Evidence: claude-api skill SKILL.md (Current Models table; Thinking and Effort table and sampling note), shared/cost-optimization.md L124 and L151, shared/prompt-caching.md L144, shared/model-migration.md L707 and L1045.
   - Confidence: high

21. **Cost and latency indicators for LLM navigators. NavGPT-3 caps Claude Opus 5 at $5 per episode (max_turns 200, timeout 2,400 s), and its planner reacts in 3-19 s per language-model decision. O2C-Nav evaluates OpenNav-100 in about 1 h on an RTX 4090 with 6 processes, calling qwen3-vl-235b-a22b. HAM-VLN uses 67.2% fewer API tokens than a full-visual-history baseline. SFCo-Nav uses more than 50% fewer tokens per trajectory and runs 3.5x faster. MapGPT caps output at 1,000 tokens per step with 'low'-detail images. DACo and DiscussNav sample 200-instruction subsets of REVERIE/R4R 'due to the constraint of cost'.**
   - Evidence: NavGPT-3 docs/USAGE.md L134-136 and the opus config; NavGPT-3 abstract; ext/B3/kkpsq_O2C-Nav-Code/README.md L119-133; HAM-VLN index.html; SFCo-Nav abstract (2603.01477); MapGPT scripts/README; ext/B3/ChocoWu_DACo/README.md L44-47.
   - Confidence: high

22. **Statistical caveat: most frontier zero-shot VLN-CE numbers come from 100-episode subsets (OpenNav-100 or Uni-LaViRA lists), whose binomial standard error is about +/-4.6 points at 70% SR. Paper versions disagree for GPT-6-Astra (79.0 vs 81.3) and MSNav (45.7 vs 50.9). Only NavGPT-3 reports the full 1,839-episode split.**
   - Evidence: sqrt(0.7*0.3/100) = 0.046; the sources above.
   - Confidence: high

23. **Gemini/Claude-specific navigation evidence. NavGemini (Gemini-Pro-Vision) claims +5.7 SR over prior text-LLM agents. Uni-LaViRA's defaults are gemini-3.5-flash for language actions and qwen3.5-27b for visual actions. One comparison lists Open-Nav with Gemini-3-Flash at 32% SR on OpenNav-100. NavGPT-3 with Claude Opus 5 is the best published Claude result: 79.01 R2R-CE, 84.80 RxR-CE. No Claude Opus 5.5 or Fable 5.x VLN numbers were found.**
   - Evidence: papers.db NavGemini abstract; ext/B3/NJU-R-L-Group-Embodied-Lab_uni-lavira-code sim-code defaults (LA_MODEL_NAME gemini-3.5-flash, VA_MODEL_NAME qwen3.5-27b); WebSearch summary of the GPT-6-Astra paper tables; NavGPT-3 README.
   - Confidence: medium-high

## 6. Key numbers

| What | Value | Source |
|---|---|---|
| NavGPT (GPT-4) R2R val-unseen TL/NE/OSR/SR/SPL | 11.45 / 6.46 / 42 / 34 / 29 | DiscussNav / NavGPT-2 comparison tables (arXiv 2309.11382, 2407.12366) |
| DiscussNav (GPT-4) R2R val-unseen OSR/SR/SPL | 61 / 43 / 40 | arXiv 2309.11382 |
| MapGPT 72-scene, 216-case subset NE/OSR/SR/SPL, GPT-4V vs GPT-4o | 5.62/57.9/47.7/38.1 vs 5.11/56.9/46.3/37.8 | ext/B3/MapGPT/README.md |
| MapGPT full val-unseen SR (GPT-4V) | about 43.7 | B1 fact 18; arXiv 2401.07314 |
| NavCoT (LLaMA2-7B) R2R val-unseen SR/SPL | about 40 / 37 | arXiv 2403.07376; third-party table |
| MSNav (GPT-4o) 72-scene subset SR | 45.7-50.9 (versions differ) | arXiv 2508.16654 |
| GPT-4o re-run on the 72-scene subset: NavGPT SR/SPL; DiscussNav SR/SPL | 36.1/31.6; 37.5/33.3 | MSNav tables (WebSearch summary) |
| R2R-CE zero-shot SR (100-episode subsets): InstructNav/Open-Nav/CA-Nav/SmartWay/GC-VLN/LaViRA/Three-Step/HiMemVLN/HAM-VLN | 31.0/19.0/25.3/29.0/33.6/38.3/34.0/30.0/61.0 | ext/B3/an1iu_HAM-VLN/index.html |
| Uni-LaViRA / HarnessVLN / SpatialAnt R2R-CE SR (zero-shot) | 60.7 / 60.8 / 66 | papers.db abstracts 2605.27582, 2609.15195, 2603.26837 |
| NavProbe (gpt-5.5 xhigh) R2R-CE SR/SPL; RxR-CE SR/SPL | 71.7/55.8; 55.3/38.6 | ext/B3/NavProbe/README.md |
| GPT-6-Astra R2R-CE-100 SR medium / ultra effort | 75.7-76.0 / 79.0-81.3 (SPL 65.6 / 71.5) | arXiv 2609.29861 v1/v2 |
| GPT-6-Astra direct-API workflow, 50 episodes: SR/SPL/nDTW; % success with STOP; % in range at step limit | 52.0/48.9/70.8; 36%; 16% | arXiv 2609.20116 |
| NavGPT-3 full R2R-CE val-unseen SR: VLA-4B / VLA-8B / +Claude Opus 5 / +GPT-6-Astra | 74.33 / 76.94 / 79.01 / 81.51 (OSR 81.67/82.49/84.07/86.99) | ext/B3/metacognitionai_NavGPT-3/README.md |
| NavGPT-3 RxR-CE SR: VLA-4B / VLA-8B / +Opus 5 / +Astra / human | 81.41 / 82.39 / 84.80 / 90.43 / 90.4 | NavGPT-3 README |
| NavGPT-3 per-episode Claude budget cap; RxR wall time per episode | $5.0; 1 min 22 s | configs/experiments/vln/navgpt3_opus_r2r.yaml; arXiv 2610.10787 |
| C2Nav OpenNav-100 OSR/SR/SPL: Qwen3-VL-8B vs GPT-5.5 | 41/31/16.7 vs 54/44/29 | arXiv 2609.15142 |
| C2Nav SR when comparative answers are replaced by absolute ones (spatial/transition/terminal) | 12 / 28 / 21 (vs 31) | arXiv 2609.15142 |
| Speaker-Follower pragmatic reranking val-unseen SR (greedy vs reranked); test SR | 35.5 vs 54.6; 53.5 | ext/B3/ronghanghu_speaker_follower/README.md |
| VLN-BERT path-selection val-unseen SR (no pretrain to full) | 30.52 to 59.26 | ext/B3/arjunmajum_vln-bert/README.md |
| VLN-BERT / Airbert test SR (beam/path-ranking setting) | 73 (NE 3.09) / 78 (NE 2.58) | arXiv 2312.00151 table (WebSearch) |
| Pathdreamer ranking SR: baseline / dreamed look-ahead / GT look-ahead | 40.6 / 50.4 / 59 | arXiv 2105.08756 (WebSearch) |
| LEO multi-instruction learning, greedy-agent SPL | 25.3 to 41.4 | arXiv 2003.00857 |
| VerNav Qwen2.5-3B R2R val-unseen SR (VPO / +RFT) | 37.25 / 39.63 | arXiv 2609.00920 (WebSearch) |
| Share of R2R reference paths that are exact graph shortest paths (HA-VLN 1.0 val, 1,123 episodes) | 99.3% | computed this session |
| Edge-count distribution 3/4/5/6 | 9/378/342/394 | computed |
| Reference path geodesic length min/mean/max (m) | 5.04 / 9.69 / 22.1 | computed |
| Candidate goals per start (4-6 hops, >=5 m): median/mean/p90; goal coverage | 20 / 23.1 / 40; 98.9% | computed |
| Candidates within 3 m of the true goal (mean) | 4.0 | computed |
| Instruction-blind SR: random candidate / max-coverage candidate (val_unseen, graph geodesic) | 22.9% / 41.6% | computed |
| Human mentions (HA-VLN 1.0 val_unseen): on path / within 3 m of path / within 3 m of goal | 17.5% / 59.9% / 24.5% | computed |
| HA-VLN 1.0 humans on the 18 test scans; 1.0-to-2.0 viewpoint overlap on public scans | 70; 83.6% (identical text 68%) | computed |
| Claude Opus 5.5 / Fable 5.1 / Sonnet 5.5 / Haiku 5.5 price per MTok (in/out) | $4/$20; $10/$50; $2/$10; $0.10/$0.50 (batch -50%) | claude-api skill (cached 2026-10-06) |
| Claude image tokens | about (w*h)/784; 512x512 about 334; max 2576 px about 4,784 | claude-api skill shared/cost-optimization.md, model-migration.md |
| Estimated cost of the recommended judge stage per test pass (1,136 trajectories, Opus 5.5) | about $1.0k (batch) to $1.9k (standard); Fable 5.1 about 2.5x | inference (see the cost model in the md) |
| Score sensitivity with zero collisions (Social=1): SR 0.80 / 0.88 / 0.92 | about 75 / 83 / 86.5 | inference from the CONTEXT score formula, assuming NE of 1.2 m on successes and 7 m on failures |

## 7. Implications (inferences)

- Frontier VLMs now reach about 76-81% SR on R2R-CE using only EGOCENTRIC observation, and add 2-4.6 SR as endpoint judges on top of an 8B VLA. Our offline setting is easier: all viewpoints can be rendered, candidates enumerated, nothing is irreversible, and there are 6 instructions per path. So a goal-selection accuracy of 85-92% within 3 m is a plausible target (inference). This matches B2's estimate of about 0.75-0.90 SR for 'LLM/VLM goal inference on privileged renders', moved up because of the late-2026 results.
- The task is essentially a 1-of-about-20 classification per trajectory, with about 4 near-duplicates within 3 m of the goal. Only 1,136 independent test problems exist, since each trajectory's 3 episodes share a goal (A1). Heavy per-trajectory computation is affordable: about 50-100 frontier calls per trajectory is still only a few thousand dollars.
- A Bayes-optimal stop is worth a lot before any language understanding: instruction-blind max-coverage alone gives 41.6% vs 22.9% random. With a real posterior, the stop should be the point that maximises P(distance <= 3 m), which can lie between candidate nodes. NE is a secondary term.
- The judge should COMPARE (listwise or pairwise over a shortlist), not give an absolute yes/no or a 0-10 score. C2Nav shows absolute questions losing up to 19 SR points, and NavGPT-3's design is also comparative (pick the best node on the route).
- Frontier vs 7-8B open models: zero-shot, frontier models are about 13 SR (about 40% relative) better under the same interface (C2Nav), and GPT-6-Astra beats Claude Opus 5 by 2.5-5.6 SR as a NavGPT-3 planner. A FINE-TUNED 4-8B model matches or beats zero-shot frontier models on in-domain sub-tasks (NavGPT-3 VLA alone 76.9; MSNav Qwen3-4B beats GPT-4o on extraction; NavCoT 7B beats NavGPT GPT-4). The best system is a fine-tuned open ranker for calibrated scores plus frontier judges for hard cases (inference).
- The Claude API exposes no sampling temperature (400 from 2026-10-21) and, to my knowledge, no token logprobs. Calibrated likelihood scores (speaker p(instruction | path), follower p(path | instruction)) should therefore come from open-weight models run locally (vLLM prompt logprobs). Claude/GPT/Gemini judges give ordinal votes, diversified by permuting candidate order, rendering variant, instruction, and model.
- NavGPT-3 (public weights, Habitat-Sim 0.1.7, the same 0.25 m / 15 degree actions and 0.1 m radius as the challenge) is directly runnable on the HA scenes as a closed-loop goal PROPOSER. Its stop locations and visited-node sets are high-quality candidates or features. Its raw action logs should not be submitted, because it relies on sliding and the challenge counts every collision.
- Human-activity sentences in HA-R2R instructions are mostly 'around the route' (60% within 3 m of a path node, only 24.5% within 3 m of the goal). They should be soft path-level constraints, not goal detectors. The 1.0 test-scan human annotations (70 humans) give partial ground truth for matching them.
- Prompt-level priors that LLM navigators already exploit (MapGPT's no-stop-before-step-3, DiscussNav's 5-or-7-step budget) are subsumed by the R2R shortest-path, 4-6 edge, >=5 m candidate construction. Encode this in the candidate set, not in prompt text.

## 8. Recommendations

1. Candidate generation (no LLM): for each test trajectory, map the start to the R2R test viewpoint (A1 matcher) and enumerate all nodes with 4-6-edge shortest paths of length >=5 m (median 20, p90 40). Keep the full shortest path per candidate. Add off-node stop points (navmesh samples within 3 m of 2 or more candidates) for the Bayes-stop step. Validate on val_unseen that the goal lies within 3 m of the candidate set in at least 99% of cases, using the Habitat geodesic, not the graph distance.
2. Cheap, calibrated scorers first, all run locally and offline. (a) Teacher-forced follower log-likelihood of each candidate shortest path from ScaleVLN-H14 / SRDF / DUET (B1). (b) Speaker log-likelihood p(instruction | path) from the ScaleVLN/SRDF instruction generators and from an open MLLM (e.g. Qwen3-VL-32B/235B or Qwen3.5 via vLLM prompt_logprobs), summed over all 6 instructions. (c) NavGPT-3 8B VLA closed-loop rollouts in Habitat 0.1.7 on the HA scenes: stop point and visited-node votes, one rollout per instruction (6 per trajectory). (d) A fine-tuned Qwen3-VL-8B listwise ranker trained on HA-R2R train (10,819 episodes) plus R2R train, with hard negatives from the same candidate set and a pointwise softmax over candidates.
3. Frontier judge as the top-K comparative stage. For the top 4-6 candidates from the fused cheap scores, render per candidate: a forward view at every path node facing the next node (512x512, HFOV about 90), a 4-view panorama at the endpoint, and a top-down map with the path drawn. Burn in step index, turn angle, cumulative distance and floor change, and add text per node: MP3D region label, salient objects, and nearby human annotations. Give all 6 instructions with the original R2R ones first. Ask for clause-by-clause alignment in order, then a single letter choice, as structured output. Run 4-8 candidate-order permutations and aggregate Borda counts. Use Claude Opus 5.5 at effort high or xhigh via the Batch API. Escalate to Fable 5.1 and/or GPT-6-Astra / GPT-5.5 / Gemini only when the fused posterior is flat (top-1 vs top-2 margin small), i.e. entropy-gated as in VerNav.
4. Prompt rules to copy from NavGPT-3 (the SOTA practitioners' wording): the endpoint is a position on the route, not the object; buildings repeat rooms, so count instances in order when the last clause reuses a landmark word; not seeing a landmark is not evidence; a better-matching room elsewhere is not the room the route reached; justify both 'go back' and 'stay'; put the decisive stopping section at the END of the prompt; state principles with their mechanism instead of episode-fitted rules. From MapGPT/NavGPT: convert geometry to words and degrees yourself rather than asking the model to infer heading from pixels, give strict option IDs and validate them, never let parse failure default to STOP.
5. Fusion and stop. Fit a calibrator (logistic regression or GBDT over per-candidate features: follower LL, speaker LL, ranker score, NavGPT-3 vote, judge Borda, human-cue match, hop count, length) on val_unseen (613 trajectories) with val_seen as a check. Produce a posterior over candidates. Choose the stop point maximising sum over v of p(v) * 1[geodesic(x, v) <= 3 m], with a secondary term for expected NE. Hand x to the collision-free planner (A2/C1).
6. Measure before scaling, on val_unseen with ground-truth goals. Ablations: text-only vs images vs both; pointwise vs listwise vs pairwise; K = 3/5/8; with vs without the original R2R instructions; human cues on/off; Opus 5.5 vs Fable 5.1 vs GPT-5.5/6 vs Qwen3-VL-8B fine-tuned; effort medium/high/xhigh. Report SR within 3 m (Habitat geodesic), NE and Score. Use at least 2 reps per configuration (100-episode noise is about +/-4.6 pts; use the full 613 trajectories).
7. Budget: about 10 judged calls per trajectory at about 20-25k input and 3-5k output tokens on the top-K stage, plus a text-only shortlist, comes to about $1.5-2 per trajectory at Opus 5.5 standard rates and about half that with batch. That is about $1-2k per full test pass and about $0.6-1.2k per val_unseen pass, so 10 development iterations cost about $10-25k. Cache the shared prefix (system prompt plus instructions) per trajectory. Do NOT use online egocentric frontier navigation (NavGPT-3 Claude planner is capped at $5 per episode) as the main engine: it costs more, is less controllable, and still leaves a 5.5-pt OSR-SR gap.
8. Do not rely on zero-shot GPT-4-era designs (NavGPT text-only, DiscussNav multi-expert, MapGPT online exploration) as goal engines (34-48 SR). Their prompts and parsers are useful only as templates.

## 9. Open questions

- Actual top-1 within-3 m accuracy of a frontier comparative judge on HA-R2R val_unseen (both HA-R2R and original R2R instructions). This must be measured; no published number exists for this exact offline full-information setting.
- Does the Phase-2 test bundle keep trajectory_id and start poses that allow exact matching to R2R_test.json, which gives the 3 original instructions? This is the A1 open question and has a large effect on judge accuracy.
- Will the test bundle contain HA-VLN 2.0 human placements for the 18 test scans? If not, only the 70 HA-VLN 1.0 text annotations are available as cues.
- How much does NavGPT-3's 8B VLA degrade on 112-word HA-R2R instructions and with static humans inserted? Should it receive the original R2R instruction instead?
- Whether the Claude Messages API offers logprobs. To my knowledge it does not (not documented in the claude-api skill), so likelihood scoring is planned on open models.
- The TRAVEL SR/nDTW tables, the exact MSNav and GPT-6-Astra final versions, the Open-Nav per-model numbers (GPT-4o about 23 vs open-source about 16-19), and per-episode $ costs for NavGPT/MapGPT/DiscussNav were not retrievable: the shared WebSearch budget (200 per turn) ran out mid-research, and arxiv and other paper hosts are blocked.
- The gap between the graph-geodesic 3 m test used in my computations and the Habitat navmesh geodesic used by the scorer, which matters especially across stairs.
- The rate of instruction errors introduced by the LLM rewriting in HA-R2R (hallucinated landmarks or turns), which caps any judge's accuracy. It can be estimated on val by comparing HA-R2R and original-R2R judge agreement.

## 10. Flags vs. CONTEXT / sibling findings

- No contradiction with the CONTEXT established facts.
- **Update to B2**: the R2R-CE frontier is now NavGPT-3 (VLA-8B alone 76.94 full split; with GPT-6-Astra 81.51; public weights; Habitat-Sim 0.1.7), above SimpleVLN 76.7. Neither B1 nor B2 mentions NavGPT-3, NavProbe or GPT-6-Astra.
- **Refines B1 fact 18**: zero-shot LLM navigators are no longer limited to 44 SR. Late-2026 frontier models reach about 72-81 on R2R-CE (mostly 100-episode subsets), so frontier judges are credible rerankers, though still not the primary proposers for an offline pipeline.

## 11. Sources

- NavGPT: https://arxiv.org/abs/2305.16986 ; https://github.com/GengzeZhou/NavGPT (local ext/B3/NavGPT)
- NavGPT-2: https://arxiv.org/abs/2407.12366
- NavGPT-3: https://arxiv.org/abs/2610.10787 ; https://github.com/metacognitionai/NavGPT-3 (local ext/B3/metacognitionai_NavGPT-3)
- MapGPT: https://arxiv.org/abs/2401.07314 ; https://aclanthology.org/2024.acl-long.529/ ; https://github.com/chen-judge/MapGPT (local ext/B3/MapGPT)
- DiscussNav: https://arxiv.org/abs/2309.11382 ; https://github.com/LYX0501/DiscussNav (local ext/B3/DiscussNav)
- NavCoT: https://arxiv.org/abs/2403.07376 ; https://github.com/expectorlin/NavCoT
- MSNav: https://arxiv.org/abs/2508.16654
- InstructNav: https://arxiv.org/abs/2406.04882 ; https://github.com/LYX0501/InstructNav
- Open-Nav: https://github.com/YanyuanQiao/Open-Nav
- CA-Nav: https://arxiv.org/abs/2412.10137
- SmartWay: https://arxiv.org/abs/2503.10069 ; https://github.com/sxyxs/SmartWay-Code
- A2Nav: https://arxiv.org/abs/2308.07997
- HAM-VLN: https://arxiv.org/abs/2607.29600 ; https://github.com/an1iu/HAM-VLN (project page with results table)
- Uni-LaViRA: https://arxiv.org/abs/2605.27582 ; https://github.com/NJU-R-L-Group-Embodied-Lab/uni-lavira-code
- HarnessVLN: https://arxiv.org/abs/2609.15195
- NavProbe: https://arxiv.org/abs/2609.27526 ; https://github.com/liujy25/NavProbe
- GPT-6-Astra Lights Up Embodied Navigation: https://arxiv.org/abs/2609.29861 (v1/v2)
- How Far Can GPT-6-Astra Go?: https://arxiv.org/abs/2609.20116
- C2Nav: https://arxiv.org/abs/2609.15142
- Three-Step Nav: https://arxiv.org/abs/2604.26946 ; https://github.com/ZoeyZheng0/3-step-Nav
- O2C-Nav: https://arxiv.org/abs/2609.06476 ; https://github.com/kkpsq/O2C-Nav-Code
- HSGM: https://arxiv.org/abs/2606.00095 ; https://github.com/Teacher-Tom/HSGM_public
- SFCo-Nav: https://arxiv.org/abs/2603.01477
- DACo: https://arxiv.org/abs/2602.18941 ; https://github.com/ChocoWu/DACo
- Spatial-VLN: https://arxiv.org/abs/2601.12766
- SparseNav: https://arxiv.org/abs/2609.26408 ; VLN-Zero: https://arxiv.org/abs/2509.18592 ; SpatialAnt: https://arxiv.org/abs/2603.26837
- Boosting Zero-Shot VLN (GPT-5-mini): https://arxiv.org/abs/2509.20499
- VerNav: https://arxiv.org/abs/2609.00920 ; DV-VLN: https://arxiv.org/abs/2601.18492 , https://github.com/PlumJun/DV-VLN
- TRAVEL: https://arxiv.org/abs/2502.07306
- Speaker-Follower: https://arxiv.org/abs/1806.02724 ; https://github.com/ronghanghu/speaker_follower
- VLN-BERT (Majumdar et al. ECCV 2020): https://github.com/arjunmajum/vln-bert
- Airbert: https://arxiv.org/abs/2108.09105 ; https://github.com/airbert-vln/airbert
- Which way is 'right'? (path-ranking vs sequential, test table): https://arxiv.org/abs/2312.00151
- Pathdreamer: https://arxiv.org/abs/2105.08756
- FAST (Tactical Rewind): https://github.com/Kelym/FAST
- LM-Nav: https://arxiv.org/abs/2207.04429 ; https://github.com/blazejosinski/lm_nav
- LEO multi-view learning: https://arxiv.org/abs/2003.00857
- On the Evaluation of VLN Instructions (instruction-trajectory compatibility): https://aclanthology.org/2021.eacl-main.111.pdf
- Slow Brain, Fast Planner: https://arxiv.org/abs/2606.20458
- RankGPT (listwise, sliding window): https://github.com/sunnweiwei/RankGPT
- Successful but Unsafe (VLN-Safe collision analysis): https://arxiv.org/abs/2610.14682
- NavGemini (Gemini-Pro-Vision VLN agent): local papers.db entry 2026-01-06
- Awesome zero-shot navigation list and DB: https://github.com/ser666/awesome-zero-shot-navigation (local ext/B3/awesome-zero-shot-navigation/data/papers.db)
- NVIDIA Astranomy (effort vs cost): https://research.nvidia.com/labs/srl/projects/astranomy/
- Local data: ext/HA-VLN/HASimulator/HA-DE/tasks/HA/data/HA_val_{seen,unseen}.json ; HA-DE/connectivity/*.json ; HA-DE/human-viewpoint_annotation/human_motion_text.json ; Data/Multi-Human-Annotations/human_motion.json
- Claude API pricing and limits: claude-api skill (cached 2026-10-06)
- Sibling findings: findings/A1-episode-format-and-test-split.md, B1-discrete-r2r-sota-and-transfer.md, B2-vlnce-sota-2023-2026.md
