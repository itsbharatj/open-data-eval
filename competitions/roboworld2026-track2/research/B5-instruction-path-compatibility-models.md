# B5: Instruction–path compatibility models (rankers) for HA-VLN Track 2

**topic_id:** `B5-instruction-path-compatibility-models` · research agent B5 · 2026-10-24

Abbreviations: `S` = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad`, `EXT` = `S/ext`. All scripts are in `S/b5_scripts/`, and every number computed here is also saved in `S/b5_scripts/b5_results.json`.

## Access note
The WebSearch budget shared by all agents ran out after my 2nd query. The material below comes from three kinds of source:
- **Cloned repos and project-page repos.** vln-bert, airbert, airbert-vln.github.io (this holds the Airbert paper HTML with its tables), model-zoos, bnb-dataset, LANA-VLN, HOP-VLN, Probes-VLN, YouTube-VLN (Lily), valan, glgp, speaker_follower, R2R-EnvDrop, PREVALENT_R2R, NavGPT, MapGPT, LangNav, NavCoT, VELMA, C-Instructor, plus the earlier clones ScaleVLN, VLN-SRDF, VLN-HAMT, NaviLLM and lm_nav.
- **Local computation.** I used the public R2R splits and the MP3D connectivity graphs.
- **Recall.** Paper numbers I could not re-read are tagged "(recall)" and given medium or low confidence.

## Regime framing (READ FIRST)
The organizer clarification is on branch `bohan/clarification-Oct14`, file `EXT/jostar-track2` README, lines 41-42 and 299-313. It sets the following:
- The agent at inference may use only:
  - the episode ID;
  - the initial pose;
  - the instruction;
  - GPS and compass;
  - one forward-facing RGB-D camera.
- Panoramas may only be built by rotating, and those rotations count toward the 500-action budget.
- `human_motion.json` is banned at inference.
- HA-R2R val and test must not be used for training.
- Pretrained models and external datasets are allowed.

Each recommendation is therefore tagged with the regime it assumes:
- **[COMPLIANT]** is the primary track. Rankers must work from the agent's own egocentric observations and the agent's own map.
- **[OFFLINE-ONLY]** needs explicit organizer permission. It allows the test-scan nav graph, MP3D `.house`, REVERIE boxes, released MP3D features, HA 1.0 human placements, original R2R test instructions, and cross-episode consensus.

Most of the quantitative analysis below is computed on the nav graph. It is an exact description of the offline regime. For the compliant regime it is an *upper bound* on what any cue can deliver.

## Summary (most decision-relevant first)
1. **Goal inference reduces to ranking ~20 candidates, and geometry alone already gets 48%.**
   - R2R/HA-R2R goals are endpoints of nav-graph shortest paths with 4–6 edges and ≥5 m length: 99.8% of paths have 4–6 hops, 100% of train paths are shortest paths, and the minimum geodesic length is 5.0 m.
   - For a start node, the set {nodes 4–6 hops away and ≥5 m away} has a median of 19 (val_unseen) or 20 (test) candidates. That is about 7–8 clusters at 3 m, and the set contains the goal 98.6% of the time (99.5% within 3 m).
   - The "central node" pick (the candidate with the most other candidates within 3 m) uses no language and scores **48.4% SR** with the challenge's 3-D Euclidean success test (41.9% geodesic). Random scores 28.0%. The CMA baseline scores 12.9%.
   - If the cues below were extracted from the text perfectly:
     - first-move direction: 63.7%
     - HA 2.0 human signature: 71.7%
     - both: 77.7%
     - MP3D region sequence (one scan): 83–85%
2. **Exhaustive candidate exploration is impossible in the compliant regime, so a ranker can only re-rank the agent's own map.** Touring the union of all candidate paths costs a median of **792 actions**. Only 16.5% of episodes fit in 500, and 2% fit if a 24-action 360° sweep is added at each node (224×224 camera, HFOV 90, 15° turns). The compliant ranker is therefore a stop/goal verifier over the agent's own topological map plus 1–3 locally explored alternatives. The room it can recover is the OSR–SR gap: 6–8 points for ETP-R1 / ScaleVLN, and up to ~15–25 points over the union of several policies' stop points (B2: union recall 82.7–91.5% vs 67.5% for the best single agent).
3. **Classic rankers have public weights and features but are dated.**
   - VLN-BERT scores 59.26% val-unseen path selection on its own, and 73% on test when fused with the speaker and follower.
   - Airbert scores 68.67% val-unseen as a single model and 77% on test. It picks the right instruction among 1 correct + 10 corrupted ones 66.6/61.1/49.8% of the time on val-unseen (VLN-BERT: 58.7/52.3/45.3; random 9.1%).
   - Both use ViLBERT over Faster R-CNN regions from MatterSim skyboxes (≤8 viewpoints × 101 regions), with the instruction **truncated at 60 wordpieces**. HA-R2R averages 112 words, about 140–170 wordpieces.
   - Speaker reranking (Speaker-Follower pragmatic inference) takes val-unseen SR from 35.5 to 54.6.
   - The strongest compatibility signal available today is a DUET-family model's own stop/teacher-forced log-likelihood. These models reach 72–81% single-run SR on R2R val unseen, and features for all 90 scans are released.
4. **Invest first in a DUET-family goal/stop scorer.**
   - Fine-tune it with listwise graph hard negatives on train scans.
   - Re-train it on Habitat egocentric renders (with humans) for the compliant regime.
   - It is the same module the compliant planner needs (the ETPNav/ETP-R1 global planner), so the investment pays twice.
   - In parallel, build a prompt-only LLM verifier as the cheap hedge against the 112-word LLM-style instructions and as the natural consumer of human-activity text:
     - [OFFLINE]: `.house` regions, REVERIE objects and HA 1.0 humans.
     - [COMPLIANT]: VLM captions of the agent's own frames, plus person detection.
   - The decision rule in §8 compares the two on 120 val_unseen trajectories (360 instructions), at a cost of a few hours.
5. **Human-activity text is a large, cheap cue, but only if humans can be perceived or looked up.** 68% of val_unseen GT paths pass within 1 hop of a HA 2.0 human, and 26% end within 1 hop of one. Knowing exactly which humans the path passes takes the central-node pick from 48.4% to 71.7%. With the sparser HA 1.0 placements (4.2 humans/scan vs 10.4) the oracle drops to 55.4%. In the compliant regime this cue must come from detecting and captioning the rendered humans. `human_motion.json` may only supervise training on train scans (README Q11).

## 1. Task structure analysis (local computation; regime: OFFLINE exact, COMPLIANT upper bound)

| Quantity (R2R discrete; HA-R2R = R2R-CE subset) | val_seen | val_unseen | test |
|---|---|---|---|
| paths | 340 | 783 | 1,391 (1,136 ported to CE) |
| hops of GT path (3/4/5/6) | 1/100/112/127 | 8/278/230/267 | n/a |
| GT path is a graph shortest path | 100% | 99.0% | n/a |
| geodesic length min/median/p95/max (m) | 5.09/9.91/15.7/19.0 | 5.04/9.13/14.7/22.1 | n/a |
| candidates (4–6 hops, ≥5 m): mean/median/p10/p90 | 25.4/24/10/44 | 22.0/19/9/38 | 23.4/20/9/42 |
| greedy 3-m clusters (mean/median) | 8.1/7 | 7.2/6 | 8.0/7 |
| GT goal in candidate set / within 3 m of a candidate | 99.7%/99.7% | 98.6%/99.5% | n/a |
| random candidate SR (geodesic / Euclidean) | 22.9% / – | 22.8% / 28.0% | n/a |
| language-free central-node SR (geodesic / Euclidean) | 40.0% / – | 41.9% / **48.4%** | n/a |
| central over ANY graph node (Bayes stop, uniform prior) | – | 43.0% / 49.8% | n/a |
| + instruction-length distance prior (corr r=0.31, resid sd 3.0 m) | – | 43.6% (geodesic) | n/a |

The train split has 4,675 paths: hops 3/4/5/6 = 8/1,655/1,325/1,687, 100% are shortest paths, and the median length is 9.45 m.

Scripts: `S/b5_scripts/r2r_candidates.py`, `cand_sets.py`, `bayes_stop.py`, `len_prior.py`, `eucl.py`. Outputs are in `r2r_path_stats.json` and `cand_stats.json`.

**Oracle-cue upper bounds (val_unseen, 783 paths).** Each row filters candidates to those whose cue value equals the GT path's, then takes the central pick. These numbers measure how *discriminative* a cue is if the ranker extracts it perfectly from the instruction. They are not ranker accuracies.

| Cue (perfect extraction assumed) | SR geodesic | SR Euclidean (challenge) | median filtered set |
|---|---|---|---|
| none (central only) | 41.9% | 48.4% | 19 |
| first move direction (F/L/R/B relative to start heading) | 56.5% | 63.7% | 14 |
| HA 2.0 humans within 1 hop of path + of goal (`human_motion.json`, 10.4/scan) | 64.1% | 71.7% | 7 |
| HA 1.0 humans only (`human_motion_text.json`, 4.2/scan, the only public test-scan humans) | 55.4% | – | 12 |
| direction + HA 2.0 humans | 70.2% | 77.7% | 6 |
| one scan p5wJjkQkbXX (89 train/val_seen paths, full `.house` in VALAN testdata; central baseline only 39.3% Eucl.): GT end-region label | 70.8% | 75.3% | 4 |
| same scan: compressed region sequence | 78.7% | 83.1% | 3 |
| same scan: region sequence + direction | 80.9% | 85.4% | 3 |

Scripts for this table: `dir_disc.py`, `human_disc.py`, `human_disc_v1.py`, `eucl2.py` and `region_disc.py`.

**Compliant exploration cost.** Visiting every candidate means a DFS over the union of candidate shortest paths. On val_unseen that tree has a median of 29 nodes and the tour costs about 2 × length / 0.25 m plus 6 turns per edge traversal:

| Tour | Median actions | Quartiles / p90 | Fraction ≤ 500 |
|---|---|---|---|
| No panoramas | 792 | p25 600, p75 1,147, p90 1,508 | 16.5% |
| 24-action 360° sweep at every tree node | 1,447 | – | 2% |

Script: `tour.py`. The sensor used for these costs:
- RGB 224×224 at HFOV 90, and depth 256×256 (`EXT/HA-VLN/HASimulator/config/HAVLNCE_task.yaml` L12-24).
- TURN 15°.
- TILT 15° by default and RGB at 1.25 m (`EXT/habitat-lab-0.1.7/habitat/config/default.py` L218, L226-227).

**Human proximity in HA 1.0 (HA_val_unseen.json, 783 eps).**
- 509/783 (65%) of episodes list at least one human.
- Hop distance from human to path: 0: 118, 1: 271, 2: 127, 3: 87, ≥4: 70. Median 2.64 m, p90 7.5 m.
- Relative position: Around 440, Obstacle 141, Beginning 50, End 42.

HA 2.0 overlap on the 72 public scans: 248 of the 304 HA 1.0 viewpoints (82%) also anchor a 2.0 human, and 206 (68%) carry the same activity text. Script: `human_rel.py`.

## 2. Facts (verified unless marked)

1. **[high] VLN-BERT (Majumdar et al., ECCV 2020) inputs and training.**
   - Architecture: ViLBERT co-attention transformer (config `bert_base_6_layer_6_connect.json`).
   - Path: ≤8 viewpoints × ≤101 visual tokens per viewpoint. The 101 tokens are 100 bottom-up-attention Faster R-CNN (ResNet-101, Visual Genome) regions per panorama plus 1 mean "global" token. Regions come from 36 views (3 sweeps × 12) at 600×600, VFOV 80, with 5–20 boxes per view, then redundancy-pruned to 100. Each is a 2048-d feature with 1601-class probabilities and 11-d location (box, area, sin/cos of heading relative to current and next heading, elevation).
   - Instruction: truncated at **60 wordpieces**.
   - Pretraining stages: 1 = BERT language, 2 = Conceptual Captions, 3 = R2R masked path/instruction modelling.
   - Fine-tuning: candidates are 30 beams from the Speaker-Follower; each training item is 1 positive (≤3 m from goal) plus 3 negatives, with cross-entropy over 4. An alternative 'sampled' mode builds easy negatives (shortest path to a random node 4–6 hops away and >3 m from the goal), hard negatives (GT prefix, then divergence to a 4–6-hop node), and backup negatives (one viewpoint swapped).
   - Val-unseen path-selection SR by pretraining stage: none 30.52, stage 1 45.17, 1+2 49.64, 1+3 50.02, **all three 59.26**.
   - Final scores are fused as `alpha*scale*vlnbert + (1-alpha)*(beta*speaker + (1-beta)*follower)` with alpha 0.63, beta 0.94, scale 1e-2.
   - Weights are on Dropbox (`run_220825_pytorch_model_10.bin`). Features: `matterport-ResNet-101-faster-rcnn-genome.lmdb` (13.8 GB). Beam files are released for train/val/test.

   Evidence: `EXT/rk_arjunmajum_vln-bert/README.md` (model zoo); `utils/cli.py` L56-69, L97-98; `utils/dataset/beam_dataset.py` L68, L139-152, L217-223; `utils/dataset/trajectory_dataset.py` L184-226; `utils/dataset/pano_features_reader.py`; `scripts/matterport3D-updown-features/precompute_updown_img_features.py` L49-80; `scripts/combine-models.py` L25-34, L80-83; `INSTALL.md`.
2. **[high] Airbert (Guhur et al., ICCV 2021).**
   - Backbone: same as VLN-BERT (built on its codebase), pretrained on BnB: 140K Airbnb listings, 1.4M images, 0.7M captions, US only.
   - Path–instruction pair generation: concatenation, instruction rephrasing (fill-in-the-blank templates), instruction generation, image merging, captionless insertion.
   - A **shuffling loss** treats temporally shuffled path–instruction pairs as negatives.
   - Fine-tuning: 1 positive (≤3 m) vs 3 beam negatives, plus 2 shuffled negatives.
   - Val-unseen path-selection SR (VLN-BERT = 59.26):
     - adding more wrong-trajectory negatives: 59.11 (no gain)
     - keyword highlighting: 61.37
     - VLP-generated hard negatives: 61.63
     - shuffling: 61.98
     - BnB pretraining with masking + shuffling: 66.52–66.90
     - best single model (+speaker-augmented 178K pairs + shuffling in every stage): **68.67** (val seen 73.83)
   - Discrimination of 1 correct vs 10 corrupted instructions (noun-phrase replace / swap / left↔right; random = 9.1%), unseen: VLN-BERT 58.7/52.3/45.3, Airbert 66.6/61.1/49.8.
   - R2R test leaderboard SR in the pre-explored setting, with OSR 99 because the exploration path is counted:
     - EnvDrop 69
     - AuxRN 71
     - VLN-BERT 73 (NE 3.09)
     - **Airbert 77 (NE 2.69)**
     - (also listed: PREVALENT 59, Speaker-Follower 53)
   - BnB pretraining ran on 64 V100-32G with a 20 h slurm limit.
   - Weights (airbert, airbert-r2rRS, airbert-r2rRSA) are on Google Drive.

   Evidence: `EXT/rk_airbert-vln_airbert-vln.github.io/index.html` and `paper.html` (Tables 2–5, 8; Sec. 4.2–4.3, 5.1); `EXT/rk_airbert-vln_airbert/README.md`, `utils/dataset/beam_dataset.py` L32-61, L143-148; `EXT/rk_airbert-vln_model-zoos/Makefile`; `EXT/rk_airbert-vln_airbert/slurm/train-bnb-8.slurm`.
3. **[high] Lily / YouTube-VLN (ICCV 2023)** is an Airbert-style ViLBERT ranker pretrained on YouTube house-tour video frames (MRT: masking, ranking, trajectory judgement), then fine-tuned with ranking + shuffling (+speaker aug) on 8 GPUs. The trained ranker is released on Google Drive. (Recall, medium: path-selection val-unseen ≈71%, test 78% in the pre-explored setting; B1 also lists beam 78.) It is relevant to the compliant regime because it consumes egocentric *video* frames rather than panoramas. Evidence: `EXT/rk_JeremyLinky_YouTube-VLN/README.md` (training commands, "trained model" link).
4. **[high] Speaker reranking works.**
   - Speaker-Follower pragmatic inference (beam 40, state-factored search): val seen/unseen SR 70.1/54.6, test 53.5. The follower alone, greedy, scores 66.4/35.5.
   - Speaker and follower weights are downloadable.
   - EnvDrop and PREVALENT_R2R also ship a speaker. EnvDrop single-run val-unseen is 53.5 (EnvDrop README); its beam search with speaker scores 69 on test (Airbert table).
   - Evidence: `EXT/rk_ronghanghu_speaker_follower/README.md` L131-169; `EXT/rk_airsplay_R2R-EnvDrop/README.md` L12-14; `EXT/rk_weituo12321_PREVALENT_R2R/README.md`.
5. **[high] HAMT and HOP pretrained checkpoints already contain an instruction–trajectory-matching (ITM) head.**
   - HAMT ITM: negatives per positive are num_neg_trajs=4, i.e. K=2 random in-batch trajectories plus K=2 temporally shuffled copies of the positive history, with cross-entropy over 1+4. ITM has mix ratio 2 of 12 in R2R pretraining, max_txt_len 100.
   - HOP tasks: mlm, itm, order (trajectory order), 3class (group order), action.
   - In-batch negatives are easy (other scans and starts), so these heads need same-start hard negatives before they can rank candidates.
   - Evidence: `EXT/VLN-HAMT/pretrain_src/model/vilmodel.py` L640-720; `pretrain_src/model/pretrain_cmt.py` L245-262; `pretrain_src/config/pretrain_r2r.json`; `EXT/rk_YanyuanQiao_HOP-VLN/tasks/pretrain/main.py` L176-269.
6. **[high] Lana (CVPR 2023)** is a single model that both follows and generates instructions, so it could score P(instr|path). It is built on HAMT with CLIP-ViT-B/16 features and fine-tuned with max_instr_len 100. **No checkpoint is released** and pretraining code is listed as TODO. Evidence: `EXT/rk_wxh1996_LANA-VLN/README.md` (Progress list) and `finetune_src/scripts/run_r2r_clip.sh` (needs `bert_ckpt_file`).
7. **[high] SRDF and ScaleVLN filter their own data with a navigator compatibility score, but their speakers are not released.**
   - SRDF filters generated data by navigator nDTW ≥ 0.9 (and ROUGE ≤ 0.85), as the file name `mantis.hm3d_round3_greedy_ndtw0.9_ranked_414k_rouge0.85.json` shows. The generator (Mantis-based) is not released. Only the pretrained navigator `model_step_170000.pt` and partial data are.
   - ScaleVLN lists 'Speaker Training Code' as TODO.
   - Evidence: `EXT/VLN-SRDF/README.md`; `EXT/ScaleVLN/README.md` L26.
8. **[high] NaviLLM can act as a speaker.** Its schema includes trajectory summarization (= instruction generation) and checkpoints are on HF (`zd11024/NaviLLM`), so it can compute P(instruction | trajectory) by teacher forcing. Evidence: `EXT/NaviLLM/README.md` L52, L68, L154-171.
9. **[high] DUET/ScaleVLN already compute a compatibility signal.**
   - During rollout the model records a stop probability for every visited node and finally stops at the argmax over visited nodes.
   - With `feedback='teacher'` it follows `gt_path` exactly (`_teacher_action_r4r`). Replacing `gt_path` with any candidate shortest path therefore gives that path's teacher-forced log-likelihood plus its stop probability, with no architectural change.
   - Evidence: `EXT/ScaleVLN/VLN-DUET/map_nav_src/r2r/agent.py` L207-252, L316-482.
10. **[medium-high] ScaleVLN's released features are CLIP joint-space embeddings.** They are 512-d for CLIP ViT-B/16 and 1024-d for ViT-H/14, which match the CLIP *projected* embedding widths (the vision widths are 768/1280). The hdf5 files can therefore be compared directly with CLIP text embeddings of instruction landmarks for zero-shot scoring, without re-rendering. Evidence: feature dims from B1 and the ScaleVLN parser; the equivalence is an inference from the CLIP architecture.
11. **[high] LM-Nav-style CLIP path scoring needs only a graph and per-node image embeddings.**
    - An LLM extracts an ordered landmark list.
    - CLIP gives a similarity per (node, landmark), as the max over views.
    - Repeated "Dijkstra transforms" find the walk that maximises Σ similarity − α·distance with the landmarks visited in order.
    - Evidence: `EXT/B3/blazejosinski_lm_nav/lm_nav/optimal_route.py` L16-90.
12. **[high] Text-only / LLM VLN systems verbalize observations, but all are zero-shot sequential navigators, not full-candidate rankers.**
    - NavGPT feeds GPT-4 per-viewpoint 'detail', 'summary' and 'objects' fields (`EXT/rk_GengzeZhou_NavGPT/nav_src/env.py` L209-232).
    - LangNav ships pre-extracted BLIP captions plus Deformable-DETR objects for every view (`r2r_blip_DETR_vis2text`, 113 MB) and a LLaMA2-7B model (`bpan/LangNav-Sim2k-Llama2`).
    - MapGPT uses a map-to-text prompt with images. It scores GPT-4V SR 47.7 / GPT-4o 46.3 on a 72-scene, 216-case val-unseen subset (README).
    - (Recall, medium: NavGPT GPT-4 is about 34% SR on val unseen, and full-split MapGPT is about 44%; B1.)
13. **[medium] 'Rethinking the Spatial Route Prior' (Zhou, Liu, Mu, arXiv 2110.05728)** makes the same observation as §1. With a known map and the shortest-path prior, VLN becomes classification over destination nodes. It reports 73% val-unseen SR for a single model (~40 explored nodes) and 78% with a Speaker ensemble. Evidence: WebSearch summary of the arXiv abstract; I could not read the tables.
14. **[high] HA-R2R instructions are LLM rewrites built from the R2R-CE instruction plus `[start]/[during]/[end]` "region: activity" strings.** The region names are MP3D region categories: entryway/foyer/lobby, laundryroom/mudroom, meetingroom/conferenceroom, porch/terrace/deck/driveway, tv, dining booth, classroom, other room, … The human-activity sentences therefore carry room-type and human-landmark information about the GT path's start, middle and end. Evidence: `EXT/HA-VLN/Data/HA-R2R/README.md` (prompt + example); `EXT/HA-VLN/HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json` (format `[region:activity, model_id, heading]`; A9 decoded the fields).
15. **[high] Human annotation inventory.**
    - HA 1.0 `human_motion_text.json`: 374 humans on 90 scans, **70 on the 18 test scans** (4.16 per scan), keyed by MP3D viewpoint.
    - HA 2.0 `human_motion.json`: 749 humans on 72 scans (10.4 per scan; test scans withheld), keyed by viewpoint id, with 120-frame translation/rotation.
    - Of the 304 HA 1.0 viewpoints on the 72 shared scans, 248 (82%) also anchor a 2.0 human and 206 (68%) keep the same activity.
    - At inference both files are prohibited in the compliant regime. They are allowed as training supervision on train scans (README Q11).
16. **[high] MP3D `.house` files give region labels and objects for every panorama.**
    - Each panorama line (P) carries a region index; region lines (R) carry a label code (a=bathroom, b=bedroom, h=hallway, k=kitchen, l=living room, …); object lines (O) link to category lines (C) that map to mpcat40.
    - VALAN's parser returns the objects in the same region with their distance to the pano.
    - habitat-sim 0.1.7 auto-loads `{scan}.house` into `sim.semantic_scene`.
    - Evidence: `EXT/rk_google-research_valan/r2r/house_parser.py` L40-120, L244-390; `EXT/habitat-sim-0.1.7/src/esp/sim/Simulator.cpp` L265-271; full house file `EXT/rk_google-research_valan/r2r/testdata/scans/p5wJjkQkbXX/house_segmentations/p5wJjkQkbXX.house` (37 regions, 155 panos, 728 objects; 150/152 graph nodes labelled).
    - A9 additionally found public room labels for 76% of test viewpoints (niessner/Matterport region_classification) and REVERIE BBox files for 100% of test viewpoints. Both count as [OFFLINE-ONLY] at inference.
17. **[high] VALAN (Google) contains an R2R instruction–path discriminator agent** (TF2, LSTM encoders with attention pooling; from the Huang et al. 2019 data-filtering work, recall). There are no public weights. It is mainly a design reference. Evidence: `EXT/rk_google-research_valan/r2r/discriminator_agent.py`, `discriminator_problem.py`.
18. **[high] Instruction-length limits.**
    - VLN-BERT and Airbert: 60 wordpieces.
    - HAMT pretraining and Lana: 100.
    - DUET, ScaleVLN, GOAT, MAGIC, NavGPT-2: 200 (B1).
    - HA-R2R averages 112 words, about 140–170 wordpieces (B1 estimate, medium).
    - So VLN-BERT/Airbert would see roughly the first third of each HA-R2R instruction. The R2R-derived route text and the final stop sentence are often the parts cut off.
19. **[high] Rules relevant to rankers (clarification branch README).**
    - Q10: pretrained models and external datasets (R2R, BnB, YouTube-VLN, HM3D aug) are allowed. Training on HA-R2R val_seen/val_unseen/test is forbidden.
    - Q11: GT human info only as training supervision.
    - Q8: panoramas only by rotating, and the rotations count toward the budget.
    - Implication: any *learned* fusion weights or calibration should be fit on held-out TRAIN scans, not on val.

## 3. Model catalogue (inputs, data, negatives, reported accuracy, weights, HA adaptation)

| Model | Inputs | Train data & negatives | Reported ranking accuracy | Weights public? | Regime fit |
|---|---|---|---|---|---|
| VLN-BERT (ECCV20) | ≤8 vps × 101 Faster R-CNN regions (36-view pano, VFOV 80) + heading feats; ≤60 wp text | CC 3.3M → R2R masked; R2R 14k instr × 30 Speaker-Follower beams; 1 pos (≤3 m) + 3 neg; optional graph negatives (4–6 hop, >3 m) | val-unseen path selection 59.26 alone; test 73 fused with speaker+follower | yes (Dropbox ckpt, 13.8 GB lmdb incl. test scans, beams) | OFFLINE ensemble member; COMPLIANT needs retraining on renders |
| Airbert (ICCV21) | same as VLN-BERT | BnB 1.4M img / 0.7M captions → R2R; shuffling negatives (+2 per item), speaker-aug 178K | 68.67 val unseen (single); 77 test fused; 1-of-11 corruption: 66.6/61.1/49.8 | yes (GDrive: airbert, r2rRS, r2rRSA) | as above; best of the ViLBERT family |
| Lily (ICCV23) | ViLBERT; YouTube house-tour frames | YouTube-VLN pretrain (masking+ranking+trajectory judge) → R2R rank+shuffle | (recall) ≈71 val unseen; 78 test | yes (GDrive) | video-frame pretraining suits egocentric COMPLIANT paths |
| PREVALENT (CVPR20) | ResNet-152 views + text | 6.58M (recall) speaker-aug triplets; image-attended MLM + action prediction (no ranking head) | n/a as ranker (test SR 59 as agent) | yes | encoder only |
| HAMT ITM / HOP ITM | ViT-B/16 36-view hist + text (100) | in-batch random + shuffled negatives | not reported for candidate ranking | yes (HAMT Dropbox; HOP data) | needs hard-negative fine-tune |
| Lana (CVPR23) | CLIP-B/16 pano hist; joint follower + speaker | R2R + aug | speaker + follower; no ranking eval | **no** | skip |
| Speaker-Follower / EnvDrop / PREVALENT speakers | ResNet views → LSTM speaker P(instr\|path) | R2R | pragmatic rerank 35.5→54.6 val unseen; EnvDrop beam 69 test | yes | cheap fusion term (OFFLINE), retrain on renders (COMPLIANT) |
| NaviLLM (CVPR24) speaker mode | EVA02-CLIP-L views + Vicuna-7B | multi-task incl. trajectory summarization | n/a | yes (HF) | strong long-text speaker term |
| DUET / ScaleVLN / SRDF as scorer | 36-view CLIP/InternViT feats per node + graph; 200 wp | R2R + PREVALENT + HM3D/Gibson aug (4.9M / 19.5M) | navigator SR 72 / 81 / ~85 val unseen; stop-score over visited nodes; SRDF uses nDTW≥0.9 as data filter | yes (HF/Dropbox, feats incl. test scans) | **first investment**; COMPLIANT = ETPNav/ETP-R1 planner head |
| LM-Nav-style CLIP DP | LLM landmarks + CLIP node sims | zero-shot | (not on R2R) | code yes | zero-shot feature; works on ScaleVLN CLIP hdf5 |
| NavGPT / MapGPT / LangNav / NavCoT | verbalized views (captions+objects) or images → LLM | zero-shot / small FT | 34 / 44–48 SR sequential (not ranking) | code yes; LangNav model on HF | template for the text-only verifier |
| Route-prior classification (2110.05728) | known graph, destination classification | R2R | 73 val unseen (≈40 explored nodes), 78 + speaker | ? (not checked) | conceptual match to OFFLINE setting |

## 4. Adapting compatibility models to HA-R2R

### 4.1 Visual features for the 18 test scans
- **[OFFLINE-ONLY] No extraction is needed.**
  - The VLN-BERT/Airbert/Lily lmdb (13.8 GB) and the DUET-family hdf5 (HAMT ViT-B/16, ScaleVLN CLIP-B/16 and H/14, SRDF InternViT-6B) cover all 90 scans. They had to, because each method was submitted to the R2R test server.
  - To re-extract (new backbone):
    - DUET-family: MatterSim skybox, 36 views (12 headings × elevations −30/0/+30), 640×480, VFOV 60.
    - VLN-BERT-family: 600×600, VFOV 80, bottom-up Faster R-CNN, 5–20 boxes per view, ≤100 per pano.
  - Alternatively, render the `.glb` in Habitat at viewpoint poses:
    - convert MP3D (x,y,z) to Habitat (x, z, −y) (A1);
    - set the camera at the MP3D pose height;
    - HFOV = 2·atan(tan 30°·4/3) = 75.2° to mimic 640×480 VFOV 60.
  - The test scans have 1,971 viewpoints × 36 = 70,956 images: minutes for CLIP, about 1 GPU-hour for InternViT-6B (B1 estimate).
  - Habitat-render features carry a sim-to-sim gap. B1 cites ~20 SR points for 2021 models; ScaleVLN/SRDF should be less sensitive because they were pretrained partly on Habitat renders.
- **[COMPLIANT] Test-scan MP3D features are privileged.** Features must come from the agent's own frames: forward RGB-D, 224×224, HFOV 90, sensor at 1.25 m. Practical recipe:
  1. A 360° sweep is 24 TURN actions. Keep every 2nd frame to get 12 views at 30°, which matches ETPNav-style 12-view inputs. Elevation views cost 2 LOOK actions per 30° and are not worth it.
  2. Train the ranker on exactly this sensor. Render train-scan viewpoints and paths (about 7.8k R2R train-scan panoramas × 12–24 frames, with HA humans inserted via the HA-VLN simulator) and HM3D for augmentation. Rendering plus CLIP-H/14 encoding of ~0.3M frames takes about 10–30 GPU-min.
  3. Encode path nodes as the frames actually collected. Video-style rankers (Lily) and sequence rankers fit better than 36-view panorama rankers.

### 4.2 Long (≈3.5–3.9× R2R: 112 vs 29–32 words) instructions with human mentions
- **Text length.** Raise max text to 256 wordpieces. VLN-BERT/Airbert must then be re-fine-tuned: positions >60 were never trained and BERT allows 512. DUET-family models are already at 200.
- **Instruction-side structure.** Split sentences, then flag human-activity sentences (person/individual/someone/couple/group/child + activity verbs) with a segment embedding. This lets the model learn to treat them as landmarks without drowning out the route text.
- **Human-landmark tokens on the path side.**
  - [OFFLINE] For each node, append one token per HA human within 1 hop: [HUMAN] + CLIP-text(activity) + region embedding + relative heading/distance.
    - Training: from 2.0 annotations on train scans.
    - Test: from 1.0 annotations, or from the Phase-2 bundle if it is published and allowed.
    - Use token dropout p≈0.5 so the model tolerates missing humans. That matters because test scans have only 4.2 humans/scan in 1.0 vs 10.4 in 2.0.
  - [COMPLIANT] Build the same tokens from a person detector plus a VLM caption ("a person brushing teeth at a sink") on egocentric frames, placed at the node where they were seen. Train the detector/captioner alignment with GT 2.0 humans on train scans (allowed by Q11).
- **Optional text normalisation.** Add a de-paraphrased R2R-style rewrite (B1) as a second view of the instruction, and score both. [OFFLINE-ONLY]: also look up the original R2R test instructions (A9 mapping) and use them as extra views.

### 4.3 Negatives from the connectivity graph (train scans only)
1. **Exhaustive same-start candidates.** Every node 4–6 hops and ≥5 m from the start whose position is >3 m (Euclidean) from the GT goal; median ~19 per episode. This is exactly the test-time distribution, so use a listwise softmax over the full set. Candidates within 3 m become positives with soft targets ∝ 1, or ∝ exp(−d/1 m) for calibration.
2. **VLN-BERT hard negatives.** Take a GT prefix, then diverge to another 4–6-hop node.
3. **Airbert temporal shuffles.** Reorder visual nodes (`shuffle_different` / `shuffle_non_adjacent`).
4. **Instruction-side perturbations.** Swap left↔right, swap room names using MP3D region vocabulary, swap human activities across episodes in the same scan, drop or replace the final stop sentence, truncate.
5. **Cross-instruction negatives.** Other trajectories' instructions from the same scan and start, which force grounding.

Airbert found extra random wrong trajectories add nothing (59.11 vs 59.26). Most of the value is in hard and structured negatives (+2.4 to +2.7 each).

### 4.4 Training-time estimates (8 GPUs; estimates, low-medium confidence)
Data:
- HA-R2R train: 10,819 instructions on 3,603 trajectories.
- R2R train: 14,025 instructions on 4,675 paths. These are the same paths in a different style.
- Augmentation: EnvDrop/Airbert speaker aug (178K), and/or 100–200K HA-style rewrites. Make the rewrites by running the public HA-R2R prompt with GPT-class or open LLMs over aug paths on train scans, inserting train-scan humans.

| Ranker | Unit cost assumption | Data per epoch | Time on 8×A100/H100 |
|---|---|---|---|
| VLN-BERT/Airbert re-fine-tune at 256 wp | ~0.15–0.4 s per instruction (1 pos + 3–9 neg, 808 visual tokens per path) | 25k | 1–3 h per 10 epochs; +aug 178K: 8–20 h for 5 epochs (original V100 runs ≈2–3× slower) |
| DUET/ScaleVLN teacher-forced listwise ranker (K=8 sampled candidates × ~5 steps) | ~0.4 s per instruction fwd+bwd | 25k | ~20 min/epoch → 3–4 h for 10 epochs; +200K aug × 3 epochs: ~8 h |
| Light path-encoder cross-attention ranker (pooled 12–36-view CLIP per node + human tokens, all K≈20 candidates) | ~0.1 s per instruction | 25k (+1M HM3D aug) | ~5 min/epoch; 1M aug ≈ 3.5 h/epoch |
| Text-only cross-encoder (7–8B LLM + LoRA, instruction + one verbalized candidate, 8 candidates per instruction, ~600 tokens) | ~80k tok/s aggregate | 120M tokens | ~25 min/epoch |
| Verbalized speaker LM (LoRA 8B, P(instr \| path text)) | positives only, ~1.5k tokens | 25k–125k pairs (37–190M tokens) | 10–40 min/epoch |

Inference is cheap. 3,408 test episodes × ~20 candidates ≈ 70k pairs, which is minutes on one GPU for any of the discriminative models.

## 5. Proposed cheap text-only baseline: LLM-verbalized candidate paths

### 5.1 [OFFLINE-ONLY] variant (graph + `.house` + REVERIE + HA 1.0)
1. Build candidates: shortest paths from the start node to every node 4–6 hops and ≥5 m away (median 20). Cluster them at 3 m (≈7–8 clusters). Show the LLM one representative per cluster, plus its member variants as sub-options.
2. Verbalize each candidate path as compact structured text (~80–150 tokens). Example:

   `P3: start in bedroom facing door → turn right 90° → 2.1 m → hallway (pictures, doorway) → straight 3.4 m → stairs down 1 floor → living room (sofa, tv, fireplace) → 2.0 m → stop in living room near sofa; humans: person watching TV in tv room (left, 1.5 m) at step 4; end-room=living room`.

   Each part comes from:
   - turn angles: from start heading and node positions;
   - floor changes: from z;
   - region labels: from `.house` (or A9's public labels);
   - top 3–5 visible objects per node: from REVERIE BBoxes or `.house` mpcat40 objects within 3 m, ranked by size/rarity;
   - humans and activities: from HA 1.0.
3. Prompt a frontier LLM with the instruction and K candidates in shuffled order. Ask for a probability for each candidate, with a short justification. Repeat 3–5 times with different orders (RankGPT-style permutation self-consistency) and average log-probabilities. Then apply the Bayes-optimal stop: pick the node (or navmesh point) that maximises posterior mass within 3 m Euclidean. That adds +1.4 points even under a uniform prior.
4. Cheaper two-stage variant:
   - The LLM parses the instruction ONCE into a structured plan: first turn, ordered room sequence, landmarks, humans with activities, end room and end landmark.
   - A deterministic matcher scores all candidates.
   - The LLM reranks only the top 3–5.

   §1 shows that perfectly extracted direction + humans + rooms reach 78–85%, so the parse-and-match core alone should be strong.
5. Cost: ~1.5–3k input tokens per episode per permutation. That is ~0.5–1.1M tokens for a 360-instruction val subset and ~5–10M per full test pass per permutation.

### 5.2 [COMPLIANT] variant
- Candidate nodes are the nodes of the agent's own topological map: visited nodes plus ghost nodes from the waypoint predictor.
- Verbalizations come from a VLM. Qwen2.5-VL-7B is encouraged by the organizers; closed APIs are allowed but discouraged. The VLM captions the agent's own keyframes: room type, salient objects, people and their activities, doorways, stairs.
- The LLM/VLM acts as a stop verifier among the top 2–4 nodes whenever the planner's stop-score margin is small, and decides whether to spend actions exploring an alternative branch. At ~0.3 s per frame for 20–40 frames per episode, VLM cost is ≈10 GPU-hours for the test split.

### 5.3 Fast val_unseen evaluation protocol (GT goals available; evaluation only, never training)
1. Map each HA-R2R val_unseen episode to its R2R path. Use `trajectory_id` = R2R `path_id` (A9); the GT goal viewpoint is `path[-1]`. val_unseen has 613 trajectories and 1,839 instructions.
2. Sample 120 trajectories stratified over the 11 val_unseen scans. Score all 3 HA-R2R instructions of each (360 instructions).
3. Report:
   - top-1 acc@3m Euclidean (the challenge success test, using positions converted to Habitat);
   - top-3 recall;
   - MRR;
   - NLL/ECE of the posterior;
   - mean NE of the chosen node.

   Use bootstrap CIs at trajectory level: the 3 instructions per trajectory are correlated. At n=360 the binomial SE is ~2.5–2.8 points, so differences of ≥6 points are meaningful.
4. Always compare against:
   - central-node: 48.4% Euclidean;
   - random: 28%;
   - ScaleVLN teacher-forced scorer: zero-shot first, then fine-tuned.
5. Required ablations:
   - (a) humans removed, i.e. test-parity for COMPLIANT or for the 1.0-only setting;
   - (b) objects removed;
   - (c) region labels removed;
   - (d) R2R-original vs HA text;
   - (e) number of permutations 1 vs 5.
6. Turnaround: a few hours per configuration with parallel API calls; ~1M tokens.

## 6. Implications
- Under the offline regime, goal inference is a ~20-way choice with a 48% language-free floor and 78–85% oracle-cue ceilings. Every 1 point of SR is worth ~0.8 Score points at zero collisions (Score = 100 × (0.8·SR + 0.2·3/(3+NE)) when Social = 1). The ranker is therefore the main lever once execution is collision-free.
- Under the compliant regime, the candidate set comes from the agent's own exploration and exhaustive search is unaffordable (median 792 actions). The value of a ranker is bounded by policy OSR / proposal recall:
  - single-agent OSR–SR gap: ~6–8 points;
  - multi-policy union recall: up to 82–91% vs 67.5% (B2).

  The ranker should drive *where to spend the remaining action budget* (verify 1–3 alternative endpoints near the policy path), not just the final argmax.
- VLN-BERT/Airbert are designed for exactly this path-selection problem and ship weights. Their 60-token limit, 2020-era features and 59–69% val-unseen accuracy (on 29-word R2R text) make them secondary. In the offline regime they are a cheap ensemble member; in the compliant regime they would need full retraining on renders, which is not worth it.
- DUET-family navigators are already better rankers than the dedicated rankers: 72–81% single-run SR vs 59–69% path selection. Their stop and teacher-forced scores can be read out with a few lines of code. The same architecture is the compliant planner's global head, so fine-tuning it with hard listwise negatives improves both regimes at once.
- Human-activity sentences are an unusually informative cue: oracle +23 points over central. Humans are invisible in MP3D skybox features, so any ranker built on released MP3D features ignores them unless human tokens are added. The text-only verifier exploits them for free.
- The rules forbid training on HA-R2R val. Learned fusion weights, temperature calibration and threshold tuning should use a held-out set of ~6 train scans, with val_unseen kept for final evaluation only.

## 7. Recommendations (ordered)
1. **[BOTH] Day 0–1: build the candidate/eval harness.**
   - Graph candidates (4–6 hops, ≥5 m) with Euclidean 3-m success.
   - Implement the central-node and Bayes-stop baselines.
   - Use it for offline ranking and for open-loop evaluation of compliant verifiers on val_unseen (offline candidates rendered as the agent would see them).
2. **[BOTH] First investment: DUET-family scorer.**
   - Day 1: zero-shot ScaleVLN-H14 teacher-forced log-likelihood plus stop-prob on every candidate. [OFFLINE]: released features. Run on both HA-R2R text and de-paraphrased text.
   - Days 2–5: fine-tune with listwise hard negatives (§4.3) on HA-R2R train + R2R train (+HA-style aug), with human tokens and 256-wp text.
   - [COMPLIANT]: re-train the same head on 12-view egocentric Habitat renders (with humans) and plug it into the ETPNav/ETP-R1 planner as the stop/goal selector over visited + ghost nodes.
3. **[BOTH] Parallel hedge: prompt-only LLM verifier (§5)**, evaluated on 360 val_unseen instructions. [OFFLINE]: `.house`/REVERIE/HA-1.0 verbalizations. [COMPLIANT]: VLM captions of own frames plus person detection.
4. **[BOTH] Speaker term.** Add a speaker term (NaviLLM trajectory-summarization log P(instr|path), or a LoRA-fine-tuned verbalized-path speaker trained on HA-R2R train) to the fusion. Speaker reranking historically adds about 15–20 SR over a follower alone (35.5→54.6).
5. **[OFFLINE-ONLY] Cheap extra voters.** VLN-BERT (Dropbox) and Airbert-r2rRSA (GDrive) on the original R2R instructions (A9 lookup) and on truncated HA text. Keep them only if they add ≥2 points in fusion on the train-holdout dev set.
6. **[OFFLINE-ONLY, rules-risk] Cross-episode consensus.**
   - Each test trajectory has 3 HA instructions (+3 original R2R ones). Product-of-experts across them should cut ranking errors substantially. This is an inference: errors are partly independent.
   - Do not use this without organizer permission. It is transductive use of other episodes' inputs.
7. **[BOTH] Final decision.** Stop at the Bayes-optimal point: maximise posterior mass within the 3-m Euclidean sphere, not the argmax node. When the posterior is flat, prefer nodes that also minimise expected NE.
8. **[COMPLIANT] Budget allocation.** When the verifier's top-2 margin is small and ≥100 actions remain, physically visit the runner-up endpoint (~40–60 actions round-trip for a sibling branch). Capture a partial sweep there, then re-score and return to the winner. This replaces the pre-explored setting that VLN-BERT/Airbert assumed.

## 8. Decision rule: which ranker to invest in first
Measure on the val_unseen 360-instruction subset (§5.3) after 2–3 days:
- **R_duet**: zero-shot ScaleVLN teacher-forced/stop scorer on HA text.
- **R_llm**: prompt-only verifier.
- **R_oracle2**: the fraction of episodes where at least one of the two is right.

Then apply:
- **Rule A, default and expected.** If R_duet ≥ R_llm − 3 points, put the fine-tuning budget into the DUET-family ranker. Use the LLM only as a low-margin tie-breaker (when the DUET top-2 posterior gap is <0.15) and for human-mention episodes. Reason: the DUET scorer is also the compliant planner head.
- **Rule B.** If R_llm ≥ R_duet + 3, or on the subset of instructions with human sentences R_llm ≥ R_duet + 8, the instruction-style shift dominates. Invest first in verbalization quality and prompting. Fine-tune DUET on HA-R2R train in the background.
- **Rule C, fusion trigger.** If R_oracle2 − max(R_duet, R_llm) ≥ 6 points, build a calibrated log-linear fusion. Fit it on a train-holdout of ~6 scans, never on val. Add the speaker term.
- **Rule D, legacy rankers.** Include VLN-BERT/Airbert/Lily only if each adds ≥2 points to the fused dev score. Never invest training compute in them for the compliant regime.
- **Exit criterion.** If any configuration reaches top-1 acc@3m ≥ 0.75 on val_unseen with HA text and test-parity inputs, freeze the ranker work and move the budget to execution/collision safety (C2 Gate G6 uses the same 0.75).
- **Kill criterion for [COMPLIANT] text-only.** If VLM room-type captions agree with `.house` labels <60% of the time on train-holdout renders, drop region cues from the compliant verifier and keep only humans and objects.

## 9. Open questions
- Does the Phase-2 bundle ship test-scan human placements for local simulation? If it does, is reading them at inference prohibited like `human_motion.json`? Q11 suggests yes.
- How exactly does HA-R2R 2.0 map humans to [start]/[during]/[end], in terms of distance and hop thresholds? Measure it on HA-R2R train by matching instruction activity phrases to 2.0 humans near GT paths. This sets the right 'within k hops' for human tokens.
- How much SR do DUET/ScaleVLN lose on 112-word HA-R2R text vs original R2R text when scoring the same candidates (no published number)? How much does the ±30° elevation loss of 12-view egocentric panoramas cost?
- What are the true per-split numbers of 'Rethinking the Spatial Route Prior' and Lily? The search budget was exhausted, so the tables were not read.
- Will organizers permit the OFFLINE regime for a separate 'innovation' submission? It changes which rankers are usable.
- Does the HAMT/HOP ITM head, after hard-negative fine-tuning, beat DUET teacher-forced scoring? It is cheaper because it is a single forward pass per candidate.

## 10. Sources
Local repos and files:
- `EXT/rk_arjunmajum_vln-bert/{README.md,INSTALL.md,utils/cli.py,utils/dataset/beam_dataset.py,utils/dataset/trajectory_dataset.py,utils/dataset/pano_features_reader.py,scripts/combine-models.py,scripts/download-auxiliary-data.py,scripts/matterport3D-updown-features/precompute_updown_img_features.py}`
- `EXT/rk_airbert-vln_airbert/{README.md,Makefile,utils/cli.py,utils/dataset/beam_dataset.py,slurm/train-bnb-8.slurm}`; `EXT/rk_airbert-vln_airbert-vln.github.io/{index.html,paper.html}`; `EXT/rk_airbert-vln_model-zoos/{README.md,Makefile}`
- `EXT/rk_JeremyLinky_YouTube-VLN/README.md`; `EXT/rk_wxh1996_LANA-VLN/{README.md,finetune_src/scripts/run_r2r_clip.sh}`; `EXT/rk_YanyuanQiao_HOP-VLN/tasks/pretrain/main.py`; `EXT/rk_liangcici_Probes-VLN/README.md`
- `EXT/VLN-HAMT/pretrain_src/{model/vilmodel.py,model/pretrain_cmt.py,config/pretrain_r2r.json}`; `EXT/ScaleVLN/{README.md,VLN-DUET/map_nav_src/r2r/agent.py}`; `EXT/VLN-SRDF/README.md`; `EXT/NaviLLM/README.md`
- `EXT/rk_ronghanghu_speaker_follower/README.md`; `EXT/rk_airsplay_R2R-EnvDrop/README.md`; `EXT/rk_weituo12321_PREVALENT_R2R/README.md`; `EXT/rk_shuheikurita_glgp/README.md`
- `EXT/rk_google-research_valan/r2r/{house_parser.py,discriminator_agent.py,discriminator_problem.py,testdata/scans/p5wJjkQkbXX/house_segmentations/p5wJjkQkbXX.house}`
- `EXT/rk_GengzeZhou_NavGPT/nav_src/env.py`; `EXT/rk_chen-judge_MapGPT/README.md`; `EXT/rk_pbw-Berwin_LangNav/README.md`; `EXT/rk_expectorlin_NavCoT/README.md`; `EXT/rk_raphael-sch_VELMA/README.md`; `EXT/B3/blazejosinski_lm_nav/lm_nav/optimal_route.py`
- `EXT/HA-VLN/{Data/HA-R2R/README.md,Data/Multi-Human-Annotations/human_motion.json,HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json,HASimulator/HA-DE/tasks/HA/data/HA_val_unseen.json,HASimulator/HA-DE/tasks/R2R/data/R2R_{train,val_seen,val_unseen,test}.json,HASimulator/HA-DE/connectivity/*,HASimulator/config/HAVLNCE_task.yaml}`
- `EXT/habitat-lab-0.1.7/habitat/config/default.py`; `EXT/habitat-sim-0.1.7/src/esp/sim/Simulator.cpp`; `EXT/jostar-track2` branch `origin/bohan/clarification-Oct14` README L41-42, L299-313
- Other agents: `S/findings/{A1,A9,A10,B1,B2,C2}*.md`

Papers and URLs (not re-fetched here except via repo copies):
- https://arxiv.org/abs/2004.14973 (VLN-BERT); https://github.com/arjunmajum/vln-bert
- https://arxiv.org/abs/2108.09105 (Airbert); https://airbert-vln.github.io; https://github.com/airbert-vln/airbert; https://github.com/airbert-vln/model-zoos
- https://arxiv.org/abs/2307.11984 (Lily/YouTube-VLN); https://github.com/JeremyLinky/YouTube-VLN
- https://arxiv.org/abs/2303.08409 (Lana); https://github.com/wxh1996/LANA-VLN
- https://arxiv.org/abs/2002.10638 (PREVALENT); https://github.com/weituo12321/PREVALENT_R2R
- https://arxiv.org/abs/2203.11591 (HOP); https://arxiv.org/abs/2110.13309 (HAMT); https://arxiv.org/abs/2203.04006 (ProbES)
- https://arxiv.org/abs/1806.02724 (Speaker-Follower); https://arxiv.org/abs/1904.04195 (EnvDrop); https://openreview.net/pdf?id=45uOPa46Kh (GLGP)
- https://arxiv.org/abs/2110.05728 (Rethinking the Spatial Route Prior; via WebSearch summary)
- https://arxiv.org/pdf/2111.07228 (Curriculum Learning for VLN, notes the VLN-BERT beam size of 30; via WebSearch summary)
- https://arxiv.org/abs/2308.03244 (Mind the Gap: revisiting oracle success routes)
- https://arxiv.org/abs/2305.16986 (NavGPT); https://arxiv.org/abs/2401.07314 (MapGPT); https://arxiv.org/abs/2310.07889 (LangNav); https://arxiv.org/abs/2403.07376 (NavCoT); https://arxiv.org/abs/2307.06082 (VELMA); https://arxiv.org/abs/2207.04429 (LM-Nav)
- https://arxiv.org/abs/2312.02010 (NaviLLM); https://arxiv.org/abs/2307.15644 (ScaleVLN); https://arxiv.org/abs/2412.08467 (SRDF); https://github.com/google-research/valan
