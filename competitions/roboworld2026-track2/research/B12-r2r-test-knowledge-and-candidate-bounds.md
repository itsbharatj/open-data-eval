# R2R/R2R-CE test-path knowledge, a public partial leak of R2R test goals, and nav-graph goal-candidate bounds

topic_id: `B12-r2r-test-knowledge-and-candidate-bounds`

## Summary
(1) LEAK FOUND. The original Matterport3D Simulator repo publishes web/app/sample_room_paths.json, the input file of the R2R AMT annotation HIT. It holds full nav-graph paths with start and goal for R2R path_ids 0-1999, 1,963 entries in total. 366 of them are R2R TEST paths: every test path_id below 2000. All 1,597 train/val entries match the released R2R paths exactly. All 366 test entries match R2R_test.json on scan and start viewpoint. Two more checks against the test instructions agree: 79/79 elevation-changing paths mention stairs (train/val control 323/327), and turn words agree with the first-edge side at 0.62 (control 0.64). 293 of the 1,136 ported R2R-CE/HA-R2R test trajectories are covered, which is 879 of 3,408 Phase-2 episodes (25.8%). Web search finds no public discussion of this file. Using it would be test-label exploitation. Quarantine it, and consider telling the organizers, because a rival who uses it gains about +0.26 SR. No other leak: HA-VLN con/heading_info.json, HA tasks/R2R/data/path.json, the VLN-CE v1-2 test split, the REVERIE test split and FGR2R test carry no test goals. The VLN-CE eval.ai server was sunset in Jan 2026 without a ground-truth release. (2) R2R construction (Anderson 2018): weighted shortest paths of at least 5 m with 4-6 edges, start and goal predominantly in different regions (91% in the HIT file). R2R-CE kept 77.2% of train/val paths and 81.7% of test paths. Dropped paths are mostly elevation-changing: 52-57% of dropped vs 7-14% of ported. 86-94% of ported goals lie on the start floor. R2R-CE goal = goal-viewpoint floor point (median offset 0.11 m). (3) Candidate bounds on the 1,136 ported test starts. Filter 3-6 hops & 5-25.5 m: 100% recall on all 5,798 train/val paths, mean 28.9 / median 25 / p90 54 candidates, about 8 three-metre clusters. Filter 4-6 hops & 5-20 m: 98.5% recall on val_unseen, median 20 candidates, about 7 clusters. A full grid for hops 3-7 and geodesic 5-25 m is below. (4) Base rates on val_unseen: a random candidate in the 3-6 hop/5-25.5 m set is within 3 m of the goal 26% of the time. A blind, instruction-free pick of the densest candidate gets SR 43.7% against the true R2R-CE goals (NE 5.1 m), which is Score ~42 with zero collisions vs CMA 12.9. Diverse top-3 / top-5 cluster recall is 83% / 93% (prior trained on ported train). (5) 908 distinct start viewpoints serve the 1,391 test paths. 797 paths (57%) sit in 314 shared-start groups with identical headings. Siblings never share a goal node, but 22% of sibling pairs have goals within 3 m.

## Candidate-bound grid (candidate = included nav-graph node reachable from start; hops = edges on weighted shortest path; 3 m = 3-D floor Euclidean)

| bound | recall train / val_seen / val_unseen | ported-test cands mean / median / p90 | all-1391 median | P(random cand ≤3 m) val_unseen | uniform blind SR val_unseen | 3 m clusters (ported test, mean/median) |
|---|---|---|---|---|---|---|
| hops<=3 | 0.002 / 0.003 / 0.014 | 15.14 / 13.0 / 26 | 13 | 0.117 | 0.086 | - |
| hops<=4 | 0.356 / 0.297 / 0.368 | 22.7 / 21.0 / 38 | 21 | 0.163 | 0.183 | - |
| hops<=5 | 0.639 / 0.626 / 0.662 | 31.09 / 29.0 / 52 | 29 | 0.196 | 0.275 | - |
| hops<=6 | 1.000 / 1.000 / 1.000 | 39.69 / 36.0 / 68 | 35 | 0.206 | 0.332 | 10.05 / 8.0 |
| hops<=7 | 1.000 / 1.000 / 1.000 | 48.27 / 44.0 / 83 | 43 | 0.197 | 0.342 | - |
| hops3-6 | 1.000 / 1.000 / 1.000 | 30.94 / 27.0 / 54 | 27 | 0.256 | 0.446 | - |
| hops4-6 | 0.998 / 0.997 / 0.986 | 24.55 / 21.0 / 43 | 21 | 0.281 | 0.492 | - |
| hops3-7 | 1.000 / 1.000 / 1.000 | 39.51 / 34.0 / 71 | 34 | 0.234 | 0.455 | - |
| geo<=5 | 0.000 / 0.000 / 0.000 | 8.86 / 8.0 / 14 | 9 | 0.093 | 0.069 | - |
| geo<=10 | 0.564 / 0.503 / 0.617 | 26.06 / 26.0 / 40 | 26 | 0.194 | 0.249 | - |
| geo<=15 | 0.928 / 0.926 / 0.954 | 46.06 / 44.0 / 69 | 45 | 0.187 | 0.337 | - |
| geo<=20 | 0.996 / 1.000 / 0.999 | 66.15 / 65.0 / 102 | 66 | 0.148 | 0.333 | - |
| geo<=25 | 1.000 / 1.000 / 1.000 | 83.33 / 82.0 / 131 | 78 | 0.125 | 0.312 | - |
| geo5-10 | 0.564 / 0.503 / 0.617 | 17.19 / 17.0 / 28 | 17 | 0.256 | 0.355 | - |
| geo5-15 | 0.928 / 0.926 / 0.954 | 37.2 / 35.0 / 58 | 36 | 0.214 | 0.415 | 9.35 / 9.0 |
| geo5-20 | 0.996 / 1.000 / 0.999 | 57.29 / 56.0 / 92 | 55 | 0.161 | 0.363 | 13.93 / 13.0 |
| geo5-25.5 | 1.000 / 1.000 / 1.000 | 76.02 / 72.0 / 124 | 69 | 0.131 | 0.300 | - |
| hops3-6&geo5-25.5 | 1.000 / 1.000 / 1.000 | 28.92 / 25.0 / 54 | 24 | 0.262 | 0.459 | 8.34 / 7.0 |
| hops4-6&geo5-20 | 0.994 / 0.997 / 0.985 | 23.54 / 20.0 / 42 | 20 | 0.282 | 0.487 | 7.04 / 6.0 |
| hops3-6&geo5-15 | 0.928 / 0.926 / 0.954 | 25.62 / 23.0 / 46 | 23 | 0.264 | 0.459 | 7.17 / 7.0 |
| hops3-7&geo5-25.5 | 1.000 / 1.000 / 1.000 | 37.33 / 32.0 / 70 | 32 | 0.237 | 0.467 | - |
| all_reachable | 1.000 / 1.000 / 1.000 | 122.1 / 101.0 / 168 | 101 | 0.101 | 0.257 | 29.25 / 24.0 |

## Facts
- **[high]** sample_room_paths.json in peteanderson80/Matterport3DSimulator (web/app) is the R2R AMT collection input. It has 1,963 entries keyed by path_id 0-1999 with fields scan, path (full viewpoint sequence), distance, start_region and goal_region. All 1,597 entries whose path_id is an R2R train/val path equal the released R2R path exactly (distance within 0.005 m).
  - evidence: https://github.com/peteanderson80/Matterport3DSimulator/blob/master/web/app/sample_room_paths.json (local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/prec_peteanderson80_Matterport3DSimulator/web/app/sample_room_paths.json, sha256 d15fe5df194da4caab89deb277454aea647b45d5c5fd0ebf078b84d6e4987e4f; added in commit 3711595, 2018-08-08, Peter Anderson, "Add javascript for ... collecting and evaluating navigation instructions with AMT"); web/README.md line 49: 'Trajectories are loaded from the file sample_room_paths.json'; collect-hit.html line 137; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/leak.py
- **[high]** The same file contains the full ground-truth path and goal of 366 of the 1,391 R2R TEST paths, i.e. every R2R test path_id below 2000. Scan and start viewpoint match R2R_test.json for 366/366. Instruction checks agree: elevation-changing paths mention stairs in 79/79 cases (train/val control 323/327), and the first turn word matches the first-edge side at 0.616 (control 0.643). 362/366 are graph shortest paths, 365/366 fall in the 3-6 hop/5-25.5 m filter, and edges split 4:130 / 5:91 / 6:145.
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/leak.py output; ids in /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/leak_ids.json
- **[high (conditional on A1's HA==R2R-CE id mapping, itself high)]** 293 of the 1,136 R2R-CE test trajectories (= HA-R2R Phase-2 trajectories under A1's verified id mapping) are among the leaked 366. That is 879 of 3,408 test episodes (25.8%). They span 17 of 18 test scans; gYvKGZ5eRqb has none.
  - evidence: leak.py join of leak ids with /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a1v2/A1-test-episode-index.json trajectory_id
- **[medium (absence of evidence)]** The leak is not publicly discussed. A web search for 'sample_room_paths.json' returns nothing relevant. The file has sat in the public repo since 2018-08-08 (commit 3711595), and a second local copy exists at ext/Matterport3DSimulator.
  - evidence: WebSearch 2026-10-24; git log of blobless clone /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/b12/m3dsim-hist
- **[high]** HA-VLN's con/heading_info.json does NOT leak test paths. Its entries at start viewpoints are the R2R start headings (one per path). Every non-start entry is a viewpoint that sees an annotated human: 137/137 in val_unseen scans and 419/419 in test scans. In val_unseen these non-start viewpoints are goals at the base rate (30/137 = 22% vs 97/477 = 20%). In test scans they never coincide with test path nodes, because only starts are known there.
  - evidence: HA-VLN/HASimulator/HA-DE/con/heading_info.json; HA3D_simulator src/fusion.py lines 26-95 and fine_tune_heading/GUI.py lines 245-311 (headings for human-visible agent viewpoints)
- **[high]** HA-DE tasks/R2R/data/path.json (5,798 entries) is exactly R2R train+val_seen+val_unseen, with 0 test path_ids and 0 entries in test scans. REVERIE_test.json (v1 2,304 / v2 2,244 entries, all in test scans) contains start viewpoints only. The VLN-CE v1-2 test split has no goals (A1).
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12 inline checks; ext/REVERIE/tasks/REVERIE/data*/REVERIE_test.json
- **[medium-high]** The VLN-CE eval.ai test server was sunset in January 2026 (challenge end Jan 31 2026). The organizers recommend reporting val_unseen and follow the RxR precedent. No test ground truth was released, and the VLN-CE repo HEAD 729d141 (2025-01-07) ships no test gt.
  - evidence: https://eval.ai/web/challenges/challenge-page/719/overview ; ext/VLN-CE README
- **[high]** R2R construction: start/goal pairs are sampled with Matterport3D region annotations, predominantly in different rooms. Each path is the shortest path in the weighted nav graph, and paths under 5 m or with fewer than 4 or more than 6 edges are discarded. 7,189 paths, average about 10 m. The data agrees: edges 4/5/6 = 1,655/1,325/1,687 in train, plus 8 three-edge outliers. start_region differs from goal_region in 1,458/1,597 (91.3%) train/val HIT entries and 332/366 (90.7%) leaked test entries.
  - evidence: Anderson et al. 2018 https://arxiv.org/pdf/1711.07280 ; R2R_train.json; sample_room_paths.json
- **[high]** R2R-CE porting: 3,603/4,675 train, 259/340 val_seen, 613/783 val_unseen (4,475/5,798 = 77.2%, matching the '4475 trajectories' cited for VLN-CE) and 1,136/1,391 test (81.7%). Dropped paths are dominated by elevation change: 57%/47%/52% of dropped train/val_seen/val_unseen paths change floor height by more than 1 m, vs 9%/7%/14% of ported paths. Lengths are similar (9.6-10.2 m). Ported goals lie on the start floor (|dz| <= 1 m) in 91.2%/93.8%/86.1% of cases.
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/vlnce_check.py, shared_ported.py over ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/*
- **[high]** R2R-CE goal positions are the goal viewpoint's floor point: habitat (x, z_cam - height, -y). Offset median 0.11 m, p90 0.19 m, max 1.37 m (val_unseen). Discrete nav-graph candidates are therefore near-exact continuous goal hypotheses. The VLN-CE navmesh geodesic is shorter than the graph path: ratio median 0.94 (val_unseen 0.935, p10 0.81).
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/vlnce_check.py
- **[high]** Candidate-set recall and size (candidate = included node reachable from the start, hop = edges on the weighted shortest path). 3-6 hops & 5-25.5 m: recall 100% on train, val_seen and val_unseen; ported-test mean 28.9, median 25, p90 54; greedy 3-m cover mean 8.3, median 7, p90 16. 4-6 hops & 5-20 m: recall 99.4/99.7/98.5%; ported-test mean 23.5, median 20, p90 42; cover median 6. 'hops<=6' alone: recall 100%, median 36. Geodesic alone is weaker: 5-15 m has 95.4% recall with median 35; 5-20 m has 99.9% with median 56. Full grid in numbers/markdown.
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/cands.py -> cands_out.json
- **[high]** Random-candidate base rate (val_unseen, mean over paths) of being within 3 m (3-D floor Euclidean) of the true goal: 26.2% in the 3-6 hop/5-25.5 m set, 28.2% in 4-6 hop/5-20 m, 20.6% for hops<=6, 13.1% for 5-25.5 m geodesic only, and 10.1% for all reachable nodes. val_seen is 2-3 pp lower. Expected uniform-random SR on test is ~1/#clusters, about 0.19 for the 3-6 hop/5-25.5 m set.
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/cands.py
- **[high (for the nav-graph abstraction; ignores execution error and humans)]** Instruction-free 'blind' goal choice using only the nav graph and R2R construction priors (3-6 hops, 5-25.5 m; pick the candidate with the most candidates or prior mass within 3 m). Against the real R2R-CE goal on 613 ported val_unseen trajectories: SR@1 = 43.7%, NE 5.13 m, so Nav 0.424 and Score 42.4 if collision-free (val_seen: 38.6%, NE 6.31, Score 37.3). A hop/distance/floor prior trained on ported train gives SR@1 44.7%, diverse cluster recall@2/3/5 = 68.7/82.7/92.7%, and prior entropy ~4.3 bits (calibrated: predicted top-1 mass 0.41). Measured instead with discrete graph-geodesic success, the uniform blind SR is 34.4%.
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/prior.py, prior_ported.py, vlnce_check.py, blind_ne.py
- **[high]** Mean R2R instruction length correlates with path length at r = 0.46 (train) / 0.42 (val_unseen), and with edge count at r = 0.31. Conditioning the prior on word-length tercile adds 0.3-1.5 pp SR@1.
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/prior.py
- **[high]** The 1,391 R2R test paths use 908 distinct start viewpoints. 797 paths (57.3%) are in 314 shared-start groups with sizes 2:192, 3:86, 4:27, 5:8, 7:1, and every group has an identical heading. Train shows 2,560/4,675 in shared groups and val_unseen 510/783. Sibling paths never share an identical goal (0/2,270 train pairs, 0/452 val_unseen), but 21.8% (train) / 24.3% (val_unseen) of sibling pairs have goals within 3 m; median sibling-goal distance is 5.9 m (train).
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/shared_ported.py
- **[high]** The 18 test scans have 2,014 nav-graph viewpoints, 1,971 included. Mean candidates per ported start (3-6 hop/5-25.5 m) range from 11.4 (RPmz2sHmrrY) to 48.0 (gxdoqLR6rwA).
  - evidence: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12/perscan.py -> perscan_out.json

## Numbers
- R2R test paths whose full GT path is in sample_room_paths.json: **366 / 1,391 (26.3%)** (source: leak.py)
- Leaked & ported HA-R2R test trajectories / episodes: **293 / 1,136 trajectories; 879 / 3,408 episodes (25.8%)** (source: leak.py + A1 index)
- Leaked-path validation (stairs mention when |dz|>1 m; turn-word agreement): **79/79 (control 323/327); 0.616 (control 0.643)** (source: leak.py)
- R2R-CE ported fraction: **train 3,603/4,675; val_seen 259/340; val_unseen 613/783; test 1,136/1,391** (source: vlnce_check.py, A1)
- Share of dropped vs ported paths with >1 m height change: **train 57% vs 9%; val_seen 47% vs 7%; val_unseen 52% vs 14%** (source: vlnce_check.py)
- Ported goals on start floor: **train 91.2%, val_seen 93.8%, val_unseen 86.1%** (source: shared_ported.py)
- R2R-CE goal vs goal-viewpoint floor point offset: **median 0.11 m, p90 0.19 m** (source: vlnce_check.py)
- Navmesh geodesic / nav-graph distance: **median 0.94 (val_unseen 0.935, p10 0.81)** (source: vlnce_check.py)
- Candidates per ported test start, 3-6 hops & 5-25.5 m (recall 100% train/val): **mean 28.9, median 25, p10 11, p90 54, max 89; 3 m clusters mean 8.3, median 7, p90 16** (source: cands.py)
- Candidates per ported test start, 4-6 hops & 5-20 m (recall val_unseen 98.5%): **mean 23.5, median 20, p90 42; clusters median 6, p90 13** (source: cands.py)
- Candidates per ported test start, hops<=3/4/5/6/7 (val_unseen recall): **median 13/21/29/36/44 (recall 1.4%/36.8%/66.2%/100%/100%)** (source: cands.py)
- Candidates per ported test start, geodesic <=5/10/15/20/25 m (val_unseen recall): **median 8/26/44/65/82 (recall 0/61.7/95.4/99.9/100%)** (source: cands.py)
- Candidates per ported test start, geodesic 5-10/5-15/5-20/5-25.5 m: **median 17/35/56/72 (recall 61.7/95.4/99.9/100%)** (source: cands.py)
- P(random candidate within 3 m of goal), val_unseen: **3-6 hop/5-25.5 m: 0.262; 4-6 hop/5-20 m: 0.282; hops<=6: 0.206; 5-25.5 m: 0.131; all reachable: 0.101** (source: cands.py)
- Instruction-free blind SR@1 vs true R2R-CE goal (ported val_unseen / val_seen): **0.437 / 0.386 (NE 5.13 / 6.31 m; Score if collision-free 42.4 / 37.3)** (source: vlnce_check.py, blind_ne.py)
- Blind prior diverse-cluster recall@1/2/3/5 (ported val_unseen): **0.447 / 0.687 / 0.827 / 0.927** (source: prior_ported.py)
- Test start viewpoints: **908 distinct for 1,391 paths; 797 paths in 314 shared groups (2:192, 3:86, 4:27, 5:8, 7:1); ported: 788 distinct, 580 in shared groups** (source: shared_ported.py)
- Sibling (same-start) goal pairs within 3 m: **train 495/2,270 (21.8%); val_unseen 110/452 (24.3%); identical goal 0** (source: shared_ported.py)
- corr(mean instruction words, path length): **train 0.457, val_seen 0.382, val_unseen 0.423** (source: prior.py)
- Test-scan nav-graph viewpoints: **2,014 total, 1,971 included** (source: perscan.py)

## Implications
- [integrity, both regimes] About a quarter of Phase-2 episodes (879/3,408) have publicly recoverable goals. A team that exploits them gains roughly +0.26 SR, about +20 Score points, enough to decide the podium. Our own pipelines must never load this file. Organizer awareness is the main protection against a rival using it.
- [privileged/offline regime, needs organizer permission] Goal inference on test is a small discrete choice. 100%-recall filters leave a median of 20-25 nav-graph nodes, about 6-7 three-metre clusters, and blind priors alone reach SR 44% with top-5 cluster recall 93%. A VLM/LLM reranker that grounds the instruction only has to separate 3-5 well-spread clusters. Score 60-75 looks plausible if reranking adds +20-30 pp SR over blind and execution is collision-free (inference).
- [compliant regime] The same structure exists in the training data and can be learned legitimately. Goals are 5-25 m by graph and 4-6 waypoint hops away, sit on the start floor 86-94% of the time, and lie in a different region about 91% of the time. A learned stop prior and waypoint-hop budget (e.g. CWP-style waypoint predictor + a 'hops so far' feature) should cut premature stops and over-runs. Using the test-scene MP3D nav graph at inference is gray under the Oct-14 clarification.
- [evaluation] Local val_unseen evaluation should use only the 613 ported trajectories. Elevation-changing paths are under-represented in ported test (expect about 10-14%), so do not over-invest in stairs handling.
- [evaluation] Siblings sharing a start never share a goal node, but 22-24% have goals within 3 m. A cache keyed by start must not reuse a plan across sibling trajectories, which confirms A1.

## Recommendations
- [both] Quarantine: add sample_room_paths.json (sha256 d15fe5df194da4caab89deb277454aea647b45d5c5fd0ebf078b84d6e4987e4f) and any file containing these 366 path_id->goal pairs to a blocklist. Assert in CI that no training, eval or selection script reads web/app/ of any Matterport3DSimulator copy. Never use the file for model selection, 'sanity checks' on test, or submission.
- [both, team-lead decision] Disclose the leak privately to the organizers (email listed on roboworld2026.github.io) before Phase 2 opens on Oct 30. That protects the ranking against rivals and documents good faith for the 'may be asked for code' audit. C3 (rules/ethics) should own the wording.
- [privileged] If organizers permit offline map use, use the filter 3-6 hops & 5-25.5 m (100% recall), then score clusters with prior x instruction-grounding (VLM over rendered views + LLM over the instruction). Fall back to the hop/distance/floor prior when grounding is uncertain, because the prior alone is worth SR 0.44. Validate on the 613 ported val_unseen trajectories only.
- [compliant] Train the closed-loop agent with auxiliary heads for 'hops remaining' and 'distance travelled'. Add a stop-gating prior: no stop before ~5 m of travel, soft penalty beyond ~15 m, and a strong preference for staying on the start floor. Calibrate on ported val_unseen.
- [both] Report local metrics per trajectory (1,136 test, 613 val_unseen) and stratify by shared-start and elevation-change. Use the blind-prior SR (0.44 privileged nav-graph; ~0.03 stay-at-start) as the sanity floor for any goal-classification module.

## Open questions
- Will organizers treat the 18 test scans' MP3D connectivity graphs as permitted scene knowledge at inference? This decides whether the 0.44 blind floor is usable.
- Do the organizers know about sample_room_paths.json? Will they drop or reweight the 879 affected episodes if told?
- HA-R2R test goals are assumed identical to R2R-CE test goals. HA-VLN 2.0 could have re-generated or filtered goals; this is unverified until the Phase-2 bundle.
- How does the blind/candidate approach degrade with execution error in Habitat 0.1.7 (navmesh snapping, ~0.94 geodesic ratio) and with humans standing on goal nodes?
- Exact R2R-CE drop criterion: the data shows elevation change dominates, but the exact thresholds in Krantz et al. 2020 Sec. 'Transferring Nav-Graph Trajectories' were not retrieved (ar5iv blocked).

## Sources
- https://github.com/peteanderson80/Matterport3DSimulator/blob/master/web/app/sample_room_paths.json
- https://github.com/peteanderson80/Matterport3DSimulator/blob/master/web/README.md
- https://arxiv.org/pdf/1711.07280 (Anderson et al. 2018, R2R)
- https://arxiv.org/abs/2004.02857 (Krantz et al. 2020, VLN-CE)
- https://github.com/jacobkrantz/VLN-CE
- https://github.com/jacobkrantz/VLN-CE/issues/7
- https://eval.ai/web/challenges/challenge-page/719/overview (VLN-CE test server sunset Jan 2026)
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/tasks/R2R/data/R2R_{train,val_seen,val_unseen,test}.json, path.json
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/connectivity/*_connectivity.json
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/con/heading_info.json; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA3D_simulator/src/fusion.py
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{train,val_seen,val_unseen}
- /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/a1v2/A1-test-episode-index.json
- scripts in /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b12 (common.py, leak.py, cands.py, prior.py, prior_ported.py, vlnce_check.py, shared_ported.py, perscan.py, blind_ne.py; run with python3 -I)

Note: WebSearch was available (3 searches used); arxiv/ar5iv pages not directly fetchable.
